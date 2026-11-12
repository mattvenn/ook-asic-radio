"""Block testbench for the r2r trim DAC (schematic vs extracted layout, ideal vs real bit drivers).

Bits: ideal 1.8 V sources, or with --drv each b_i driven through one sky130_fd_sc_hd__clkdlybuf4s25_1 (the
macro's trim_out[7:0] output buffer) on the ladder's 1.8 V / 0 V rails, its input from the ideal bit.
DC: the full 256-code sweep (one op per code): INL / DNL against code/256 * 1.8 V, monotonicity, the DNL at every
carry in codes 120..255, the overlap at 127/128, V(255); Rout (1 uA into out at code 135). Transient: the major
carry 127 -> 128 (1 ns edges) into the real load, 1 pF (the trim filter cap at the comparator); 0.1 % settling.
The curve goes to build/r2r_curve_<name>.json (code -> V).

--pex       layout/pex/r2r.spice instead of the schematic
--drv       real bit drivers
--temp=T    temperature (default 27)
--mc=N      Monte Carlo (corner -> <corner>_mm: resistor and driver mismatch): N samples, one ngspice process
            each with its own .options seed (docs/sim_learnings.md), --jobs=J at once (default 8); DC sweep only

    python3 sim/dac/tb_r2r.py [--pex] [--drv] [--temp=T] [--mc=N] [corner]
"""
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.environ.get('OSIC', os.path.join(ROOT, 'tools', 'osic'))
CELL = 'sky130_fd_sc_hd__clkdlybuf4s25_1'
LSB = 1.8 / 256


def bits(code):
    return [1.8 * ((code >> i) & 1) for i in range(8)]


def ladder(pex):
    if pex:
        return '.include ../layout/pex/r2r.spice'
    d = f'tb_r2r_{os.getpid()}'     # per process: parallel runs sharing one netlist race (sim_learnings)
    out = os.path.join(B, d)
    os.makedirs(out, exist_ok=True)
    subprocess.run([OSIC, 'bash', '-c', f'xschem -n -s -q --tcl "set top_subckt 1" -o build/{d} xschem/r2r.sch'],
                   cwd=ROOT, capture_output=True)
    s = open(os.path.join(out, 'r2r.spice')).read()
    shutil.rmtree(out)
    s = re.search(r'^\**\.subckt r2r .*?^\**\.ends', s, re.S | re.M).group(0)
    return re.sub(r'^\**\.(subckt|ends)', r'.\1', s, flags=re.M)


def deck(corner, sub, drv, temp, mc_seed=None):
    pdk = os.environ.get('PDK_ROOT', '/foss/pdks')
    lo, hi = bits(127), bits(128)
    node = 'a' if drv else 'b'      # where the ideal sources connect
    vb = '\n'.join(f'Vb{i} {node}{i} 0 dc {lo[i]} pwl(0 {lo[i]} 10n {lo[i]} 11n {hi[i]})' for i in range(8))
    if drv:
        vb += f'\n.include {pdk}/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice\nVDD vdd 0 1.8\n'
        vb += '\n'.join(f'xd{i} a{i} 0 0 vdd vdd b{i} {CELL}' for i in range(8))
    sweep, prev = '', None
    for c in range(256):
        sweep += ''.join(f'alter Vb{i} dc = {v}\n' for i, v in enumerate(bits(c)) if prev is None or prev[i] != v)
        sweep += f'op\necho CODE {c} $&v(out)\n'
        prev = bits(c)
    extra = ''
    if mc_seed is None:
        extra = f"""{''.join(f'alter Vb{i} dc = {v}' + chr(10) for i, v in enumerate(bits(135)))}
alter Iout dc = 0
op
let v135 = v(out)
set s135 = $&v135
alter Iout dc = 1u
op
let rout = ($s135 - v(out)) / 1u
echo RES rout=$&rout
reset
alter Iout dc = 0
tran 10p 60n 0
meas tran vf find v(out) at=59n
meas tran tset WHEN v(out)=vf+0.0007 CROSS=LAST
"""
    return f"""* tb_r2r {corner} {temp} C{' drv' if drv else ''}{f' mc seed {mc_seed}' if mc_seed else ''}
.lib {pdk}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
{sub}
{vb}
x1 b0 b1 b2 b3 b4 b5 b6 b7 out 0 r2r
Cl out 0 1p
Iout 0 out 0
.temp {temp}
.options method=GEAR{f' seed={mc_seed}' if mc_seed else ''}
.save v(out)
.control
set num_threads=1
{sweep}{extra}.endc
.end
"""


def run_deck(name, text):
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(text)
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    # ngspice's stderr notes ("vbN: dc value used for op ...") land in the middle of echo lines
    log = re.sub(r'Note: \w+: dc value used for op instead of transient time=0 value\.\n?', '', log)
    v = dict((int(c), float(x)) for c, x in re.findall(r'^CODE (\d+) ([-0-9.eE+]+)', log, re.M))
    if len(v) != 256:
        sys.exit(f'{name}: {len(v)} codes; see build/{name}.log')
    r = {k: float(x) for k, x in re.findall(r'^RES (\w+)=([-0-9.eE+]+)', log, re.M)}
    r.update({k: float(x) for k, x in re.findall(r'^(tset|vf)\s+=\s+([-0-9.eE+]+)', log, re.M)})
    r['v'] = [v[c] for c in range(256)]
    return r


def analyse(v):
    """DNL / INL in ideal LSB (1.8/256) and the facts the servo cares about."""
    dnl = [(v[c + 1] - v[c]) / LSB - 1 for c in range(255)]
    inl = [(v[c] - c * LSB) / LSB for c in range(256)]
    over = next((k for k in range(256 - 128) if v[128 + k] > v[127]), None)
    return dict(dnl=dnl, inl=inl, mono=all(d > -1 for d in dnl), over128=over,
                carries={c: dnl[c] for c in range(127, 255, 16)},
                worst_dnl_hi=max(range(120, 255), key=lambda c: dnl[c]),
                gap=any(dnl[c] > 0.5 for c in range(120, 255)))


def report(tag, r):
    a = analyse(r['v'])
    car = ' '.join(f'{c}>{c + 1} {d:+.2f}' for c, d in a['carries'].items())
    w = a['worst_dnl_hi']
    print(f'{tag}: V255 {r["v"][255]:.4f}  V180 {r["v"][180]:.4f} (ideal {180 * LSB:.4f})  '
          f'monotonic {a["mono"]}  overlap@128 {a["over128"]} codes  63>64 {a["dnl"][63]:+.2f}')
    print(f'   carries (DNL, LSB): {car}')
    print(f'   max DNL in 120..255 {a["dnl"][w]:+.2f} at {w}>{w + 1};  max |INL| {max(abs(x) for x in a["inl"]):.2f}'
          + (f';  Rout {abs(r["rout"]) / 1e3:.2f} kOhm; 127->128 settles (0.1 LSB) {(r["tset"] - 10e-9) * 1e9:.2f} ns'
             if 'rout' in r and 'tset' in r else ''))
    return a


if __name__ == '__main__':
    args = sys.argv[1:]
    pex, drv = '--pex' in args, '--drv' in args
    opt = dict(a[2:].split('=', 1) for a in args if a.startswith('--') and '=' in a)
    temp = float(opt.get('temp', 27))
    corner = next((a for a in args if not a.startswith('-')), 'tt')
    tag = f'{corner}_{temp:g}C' + ('_pex' if pex else '') + ('_drv' if drv else '')
    sub = ladder(pex)
    if 'mc' not in opt:
        r = run_deck(f'tb_r2r_{tag}', deck(corner, sub, drv, temp))
        json.dump(r['v'], open(os.path.join(B, f'r2r_curve_{tag}.json'), 'w'))
        report(f'r2r {tag}', r)
        sys.exit()
    n, jobs = int(opt['mc']), int(opt.get('jobs', 8))
    mc_corner = corner if corner.endswith('_mm') else corner + '_mm'
    seed0 = int.from_bytes(os.urandom(3), 'little')
    os.makedirs(os.path.join(B, 'r2r_mc'), exist_ok=True)

    def one(j):
        return run_deck(f'r2r_mc/{tag}_{j}', deck(mc_corner, sub, drv, temp, seed0 + j))['v']

    with ThreadPoolExecutor(jobs) as ex:
        curves = list(ex.map(one, range(n)))
    json.dump(dict(seed0=seed0, curves=curves), open(os.path.join(B, f'r2r_mc_{tag}.json'), 'w'))
    dup = n - len({tuple(round(x, 9) for x in c) for c in curves})
    print(f'r2r MC {tag}: {n} samples, seed0 {seed0}, duplicate samples {dup}')
