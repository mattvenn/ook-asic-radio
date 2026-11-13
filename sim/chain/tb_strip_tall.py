"""Stage gain of the tall-stage strip (layout/gen/chain_strip_tall.py) against today's chain.

All three are driven differentially at stage 1's gates (1.2 V DC, the chain's vcm; 1 V AC
differential), biased as in the chain (60 uA into a W 6 nf 2 / L 0.5 diode on nb), outputs and
taps unloaded:
  strip : layout/pex/chain_strip_t.spice (amp_dp_t + 5 x amp_dpc_t, abutted, taps included);
  u     : layout/pex/lna_chain.spice, today's extracted U chain, driven at its g1p / g1n nodes
          (the input section is then out of the way; lna_lo_n 1.8 V = full gain);
  blocks: today's block extractions in series (layout/pex/amp_dp.spice + 5 x amp_dpc.spice),
          no wiring between them and no taps.
Measures the differential gain at 434 MHz to each tap and to the output, the peak and the
-3 dB edges, and the AC imbalance at the output.

    python sim/chain/tb_strip_tall.py <strip|u|blocks> [corner] [--temp=C] [--lo]
--lo: lna_lo_n = 0, the low-gain shunt on (strip with amp_dpc_ts as stage 2, and u).
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.path.join(ROOT, 'tools', 'osic')
PEX = os.path.join(ROOT, 'layout', 'pex')
F = 433.92e6
TAPS = ['o1', 'o2', 'o3', 'o4', 'o5', 'out']
VLO = 1.8        # lna_lo_n: 1.8 full gain, --lo: 0 (the shunt on)


def dut(kind):
    if kind == 'strip':
        # with the shunt built into stage 2 (amp_dpc_ts) the strip has an lna_lo_n port
        hdr = re.search(r'^\.subckt chain_strip_t ([^\n]*)', open(os.path.join(PEX, 'chain_strip_t.spice')).read(), re.M).group(1)
        lo = ' lo' if 'lna_lo_n' in hdr.split() else ''
        return (f'.include {PEX}/chain_strip_t.spice\n'
                f'Vgp g1p inp 0\nVgn g1n inn 0\nVlo lo 0 {VLO}\n'
                f'x1 g1p g1n nb outp outn o1p o1n o2p o2n o3p o3n o4p o4n o5p o5n VDD 0{lo} chain_strip_t\n')
    if kind == 'u':
        # a copy with g1p / g1n (stage 1's gate nodes, internal) brought out as ports
        src = open(os.path.join(PEX, 'lna_chain.spice')).read()
        src = re.sub(r'^(\.subckt lna_chain [^\n]*)', r'\1 g1p g1n', src, count=1, flags=re.M)
        open(os.path.join(B, 'lna_chain_g1.spice'), 'w').write(src)
        return (f'.include {B}/lna_chain_g1.spice\n'
                f'Vpad_p padp 0 0\nVpad_n padn 0 0\nVcm vcm 0 1.2\nVlo lo 0 {VLO}\n'
                'Vgp g1p inp 0\nVgn g1n inn 0\n'
                # the chain's own reference diode takes ibias; its nb is internal
                'x1 padp padn ibias vcm lo outp outn o1p o1n o2p o2n o3p o3n o4p o4n o5p o5n VDD 0 g1p g1n lna_chain\n')
    s = f'.include {PEX}/amp_dp.spice\n.include {PEX}/amp_dpc.spice\nVgp g1p inp 0\nVgn g1n inn 0\n'
    s += 'x1 g1p g1n nb o1p o1n VDD 0 amp_dp\n'
    for i in range(2, 7):
        a = f'o{i - 1}'
        o = 'out' if i == 6 else f'o{i}'
        s += f'x{i} {a}p {a}n nb {o}p {o}n VDD 0 amp_dpc\n'
    return s


def deck(kind, corner, temp):
    # the U chain has its own reference diode on ibias; the others get one on nb
    bias = 'Iref VDD ibias 60u\n' if kind == 'u' else 'Iref VDD nb 60u\nXMref nb nb 0 0 sky130_fd_pr__nfet_01v8 L=0.5 W=6 nf=2\n'
    meas = '\n'.join(f'let g_{t} = db(v({t}p) - v({t}n))\nmeas ac a_{t} find g_{t} at={F:.6e}' for t in TAPS)
    return f"""* tb_strip_tall {kind} {corner} {temp}
.lib {os.environ.get('PDK_ROOT', '/foss/pdks')}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
.temp {temp}
{dut(kind)}
VD VDD 0 1.8
{bias}
Vp inp 0 dc 1.2 ac 0.5
Vn inn 0 dc 1.2 ac 0.5 180
.options method=GEAR
.control
save {' '.join(f'v({t}p) v({t}n)' for t in TAPS)}
op
ac dec 40 1e6 5e9
{meas}
let imb = db(abs(v(outp) + v(outn)) / abs(v(outp) - v(outn)))
meas ac imb434 find imb at={F:.6e}
meas ac gmax max g_out
let gm3 = gmax - 3
meas ac flo when g_out=gm3 rise=1
meas ac fhi when g_out=gm3 fall=last
echo RESULTS
.endc
.end
"""


def run(kind, corner, temp):
    name = f'tb_strip_tall_{kind}_{corner}_{temp:g}' + ('_lo' if VLO == 0 else '')
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(kind, corner, temp))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    r = {k: float(x) for k, x in re.findall(r'^(\w+)\s+=\s+([-0-9.eE+]+)', log, re.M)}
    m = re.search(r'^gmax\s+=\s+\S+\s+at=\s+([-0-9.eE+]+)', log, re.M)
    if m:
        r['fpk'] = float(m.group(1))
    if 'a_out' not in r or 'fhi' not in r:
        sys.exit(f'{name}: no results; see build/{name}.log')
    return r


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    temp = next((float(a.split('=')[1]) for a in sys.argv[1:] if a.startswith('--temp=')), 27.0)
    if '--lo' in sys.argv:
        VLO = 0
    kind = args[0]
    corner = args[1] if len(args) > 1 else 'tt'
    r = run(kind, corner, temp)
    st = [r['a_o1']] + [r[f'a_{TAPS[i]}'] - r[f'a_{TAPS[i - 1]}'] for i in range(1, 6)]
    print(f'{kind}{" low gain" if VLO == 0 else ""} {corner} {temp:g} C: gain at 434 MHz {r["a_out"]:.2f} dB (peak {r["gmax"]:.2f} dB at '
          f'{r["fpk"] / 1e6:.0f} MHz), -3 dB {r["flo"] / 1e6:.0f} .. {r["fhi"] / 1e6:.0f} MHz; imbalance '
          f'{r["imb434"]:.1f} dB; per stage {" ".join(f"{g:.2f}" for g in st)}')
