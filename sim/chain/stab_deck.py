"""Shared deck builder for the chain stability work (docs/stability_ac_2026-11.md).

base_deck() turns tb_chain.spice (schematic: build/real, extracted: build/pexsim) into the same circuit
sim/chain/stability.sh builds: board supply -> 0.5 ohm -> Lsup -> chip VDPWR, chip ground 'gchip' -> Lgnd -> GND,
the real decap_vdpwr between VDPWR and gchip, no signal, the corner / temperature / supply / strap set. The
caller appends its own elements and .control block. run() runs ngspice in a scratch directory (single thread,
the repo's .spiceinit) and returns the log text.

kick_control() is stability.sh's kick + AC measurement, so variants (RC loads, bond wires) can be kick-tested
with exactly the same criterion. check_kick.py compares it against stability.sh.
"""
import os, re, subprocess, tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
NETLISTS = {'sch': os.path.join(REPO, 'build/real/tb_chain.spice'),
            'pex': os.path.join(REPO, 'build/pexsim/tb_chain.spice')}
DECAP = os.path.join(REPO, 'build/real/decap_vdpwr.spice')   # netlisted by stability.sh on its first run
SPICEINIT = os.path.join(REPO, '.spiceinit')

# stage outputs (top-level nets of tb_chain) and their load R
STAGES = [('o1p', 'o1n', 1e3), ('o2p', 'o2n', 4e3), ('o3p', 'o3n', 4e3), ('o4p', 'o4n', 4e3),
          ('o5p', 'o5n', 4e3), ('out_p', 'out_n', 4e3)]


def base_deck(chain='sch', corner='tt', temp=27, vsup=1.8, vglo=1.8, L='2n', cdec='real', vemf=0.0,
              keep_ac=False):
    s = open(NETLISTS[chain]).read()
    s = re.sub(r'^\.control.*?^\.endc\n', '', s, flags=re.S | re.M)
    s = re.sub(r'^\.end\s*$', '', s, flags=re.M)
    s = re.sub(r'^VDPWR VDPWR GND .*$', f'Vsup vsup GND {vsup}\nRsup vsup vs1 0.5', s, flags=re.M)
    s = re.sub(r'^(x1 .*) VDPWR GND lna_chain', r'\1 VDPWR gchip lna_chain', s, flags=re.M)
    s = re.sub(r'^Vcm vcm GND ', 'Vcm vcm gchip ', s, flags=re.M)
    s = re.sub(r'^\.param vemf=.*$', f'.param vemf={vemf}', s, flags=re.M)
    s = re.sub(r'^\.param vcmi=.*$', '.param vcmi=0 fcmi=10e6', s, flags=re.M)
    s = re.sub(r'(sky130\.lib\.spice) tt', rf'\1 {corner}', s)
    s = re.sub(r'^\.param vglo=.*$', f'.param vglo={vglo}', s, flags=re.M)
    if not keep_ac:       # the antenna sources' AC drive (differential 1 V EMF) off unless asked for
        s = re.sub(r'^(Vant_[pn] \S+ \S+ dc 0) ac 0\.5', r'\1 ac 0', s, flags=re.M)
    s += f'\n.temp {temp}\n'
    if L in ('0', 0):
        s += 'Lsup vs1 VDPWR 1p\nRgnd gchip GND 1m\n'
    else:
        s += f'Lsup vs1 VDPWR {L}\nLgnd gchip GND {L}\n'
    if cdec == 'real':
        d = open(DECAP).read()
        s += re.search(r'^\.subckt decap_vdpwr.*?^\.ends', d, flags=re.S | re.M).group(0) + '\n'
        s += 'Xdec VDPWR gchip decap_vdpwr\n'
    else:
        s += f'Cdec VDPWR gchip {cdec}\n'
    return s


def kick_control(tag="case x"):
    """stability.sh's kick (1 uA, 1 ns into pad_p) + AC gain. tag: 'key value' pairs for the RESULT lines."""
    return f"""Ikick GND pad_p pulse(0 1u 5n 0.1n 0.1n 1n 1)
.save v(out_p) v(out_n) v(pad_p) v(VDPWR) v(gchip)
.options method=GEAR
.control
tran 20p 300n 0
let d = v(out_p) - v(out_n)
meas tran early pp d from=5n to=25n
meas tran mid pp d from=150n to=200n
meas tran late pp d from=250n to=300n
let growth = late / early
echo RESULT kick {tag} early_pp $&early late_pp $&late growth $&growth mid_pp $&mid
destroy all
reset
ac dec 50 100meg 2g
let g = db(v(out_p) - v(out_n))
meas ac g434 find g at=433.92e6
meas ac gpk max g
meas ac fpk when g=gpk
echo RESULT ac {tag} gain434_dB $&g434 peak_dB $&gpk peak_at $&fpk
.endc
.end
"""


def run(deck, keep=None):
    """Run ngspice -b on a deck in a scratch dir; return the log. keep: also copy the deck there."""
    with tempfile.TemporaryDirectory(prefix='stab_') as d:
        init = open(SPICEINIT).read().replace('num_threads=8', 'num_threads=1')
        open(os.path.join(d, '.spiceinit'), 'w').write(init)
        open(os.path.join(d, 'deck.spice'), 'w').write(deck)
        p = subprocess.run(['ngspice', '-b', 'deck.spice'], cwd=d, capture_output=True, text=True)
        log = p.stdout + p.stderr
        if keep:
            open(keep, 'w').write(deck)
        for f in os.listdir(d):
            if f.endswith('.txt') or f.endswith('.csv'):
                log += f'\n#FILE {f}\n' + open(os.path.join(d, f)).read()
        return log


def results(log):
    """RESULT lines -> list of dicts (key value pairs after 'RESULT <kind>')."""
    out = []
    for line in log.splitlines():
        if line.startswith('RESULT'):
            w = line.split()
            d = {'kind': w[1]}
            for k, v in zip(w[2::2], w[3::2]):
                try:
                    d[k] = float(v)
                except ValueError:
                    d[k] = v
            out.append(d)
    return out


def wrfile(log, name):
    """Columns of a wrdata file captured by run() -> list of float rows."""
    m = re.search(rf'^#FILE {re.escape(name)}\n(.*?)(?=^#FILE |\Z)', log, flags=re.S | re.M)
    if not m:
        raise RuntimeError(f'{name} not written; log tail:\n' + log[-3000:])
    return [[float(x) for x in l.split()] for l in m.group(1).splitlines() if l.strip()]


def check_op(log):
    bad = [w for w in ('Transient op started', 'singular matrix', 'Timestep too small', 'ERROR', 'Error')
           if w in log]
    return bad
