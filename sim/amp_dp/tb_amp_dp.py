"""Block testbench for amp_dp, chain stage 1 (schematic vs extracted layout).

As in lna_chain: nb from the reference diode (iref 60 uA into W 6 nf 2 / L 0.5: tail =
mt x 60 uA = 1.2 mA); inputs at the chain's input bias (vcm_dc 1.2 V), driven
differentially (1 V AC); outputs loaded by a schematic amp_dpc (stage 2). Measures, on the
differential output: gain at 434 MHz, peak gain and where, the -3 dB corner, the AC
imbalance |v(outp) + v(outn)| / |v(outp) - v(outn)| at 434 MHz; op: output CM, supply
current.
--pex swaps in layout/pex/amp_dp.spice (layout/pex.sh amp_dp).
--fingers writes the schematic's pair and tail as separate nf=1 fingers (as drawn and as
magic extracts them): the sky130 models give a 4-finger device as nf=4 noticeably less
gain than the same fingers listed separately, so this is the like-for-like reference.

    python sim/amp_dp/tb_amp_dp.py [--pex | --fingers] [corner]
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.path.join(ROOT, 'tools', 'osic')
PRM = 'w=80 l=0.15 rl=1k wt=6 mt=20 mm=0'
PRM_C = 'w=20 l=0.15 rl=4k wt=6 mt=6 mm=0 cs=0.6p'      # the stage-2 load
F = 433.92e6


def subckt(cell, name, prm, fingers=False):
    out = os.path.join(B, 'tb_amp_dp')
    os.makedirs(out, exist_ok=True)
    subprocess.run([OSIC, 'bash', '-c', f'xschem -n -s -q --tcl "set top_subckt 1" -o build/tb_amp_dp xschem/{cell}.sch'],
                   cwd=ROOT, capture_output=True)
    s = open(os.path.join(out, f'{cell}.spice')).read()
    s = re.search(rf'^\**\.subckt {cell} .*?^\**\.ends', s, re.S | re.M).group(0)
    s = re.sub(r'^\**\.(subckt|ends)', r'.\1', s, flags=re.M)
    s = re.sub(rf'^\.subckt {cell} ([^\n]*)', rf'.subckt {name} \1 {prm}', s, count=1, flags=re.M)
    if fingers:                       # pair: 16 x W/16 per side; tail: 40 x W 3 (as drawn)
        s = re.sub(r'\n\+', ' ', s)     # join continuation lines first (they carry m=...)
        lines = []
        for ln in s.splitlines():
            m = re.match(r'^(XM\w+) (\S+ \S+ \S+ \S+) (\S+) (.*)$', ln)
            if m and 'nfet' in ln:
                nm, pins, model, rest = m.groups()
                # keep the per-device extras (ad, as, ... evaluate per finger); drop L, W, nf, m
                keep = ' '.join(t for t in re.findall(r"\w+=(?:'[^']*'|\S+)", rest)
                                if t.split('=')[0].lower() not in ('l', 'w', 'nf', 'm', 'mult'))
                if 'tail' in nm:
                    lines += [f'{nm}_{k} {pins} {model} L=0.5 W=3 nf=1 {keep}' for k in range(40)]
                else:
                    sg = '+' if nm == 'XMp' else '-'
                    lines += [f"{nm}_{k} {pins} {model} L=0.15 W='w*(1{sg}mm/2)/16' nf=1 {keep}" for k in range(16)]
                continue
            lines.append(ln)
        s = '\n'.join(lines)
    return s


def deck(corner, mode):
    pex = mode == 'pex'
    dut = 'amp_dp' if pex else 'amp_dp_sch'
    return f"""* tb_amp_dp ({mode}), {corner}
.lib {os.environ.get('PDK_ROOT', '/foss/pdks')}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
{'' if pex else subckt('amp_dp', 'amp_dp_sch', PRM, mode == 'fingers')}
{subckt('amp_dpc', 'amp_dpc_sch', PRM_C)}
{'.include ../layout/pex/amp_dp.spice' if pex else ''}
VD VDD 0 1.8
Iref VDD nb 60u
XMref nb nb 0 0 sky130_fd_pr__nfet_01v8 L=0.5 W=6 nf=2
Vp inp 0 dc 1.2 ac 0.5
Vn inn 0 dc 1.2 ac 0.5 180
x1 inp inn nb outp outn VDD 0 {dut}
xload outp outn nb lp ln VDD 0 amp_dpc_sch
.options method=GEAR
.control
save v(outp) v(outn) i(VD)
op
let ocm = (v(outp) + v(outn)) / 2
let idd = -i(VD)
print ocm idd
ac dec 50 1e6 5e9
let gd = db(v(outp) - v(outn))
let imb = db(abs(v(outp) + v(outn)) / abs(v(outp) - v(outn)))
meas ac g434 find gd at={F:.6e}
meas ac imb434 find imb at={F:.6e}
meas ac gmax max gd
let gm3 = gmax - 3
meas ac fhi when gd=gm3 fall=last
echo RESULTS
.endc
.end
"""


def run(corner, mode):
    name = f'tb_amp_dp_{corner}' + ('' if mode == 'sch' else '_' + mode)
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(corner, mode))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    r = {k: float(x) for k, x in re.findall(r'^(\w+)\s+=\s+([-0-9.eE+]+)', log, re.M)}
    m = re.search(r'^gmax\s+=\s+\S+\s+at=\s+([-0-9.eE+]+)', log, re.M)
    if m:
        r['fpk'] = float(m.group(1))
    if 'g434' not in r or 'fhi' not in r:
        sys.exit(f'{name}: no results; see build/{name}.log')
    return r


if __name__ == '__main__':
    args = sys.argv[1:]
    mode = 'pex' if '--pex' in args else 'fingers' if '--fingers' in args else 'sch'
    corner = next((a for a in args if not a.startswith('-')), 'tt')
    r = run(corner, mode)
    print(f'amp_dp {corner} {mode}: gain at 434 MHz {r["g434"]:.2f} dB (peak {r["gmax"]:.2f} dB at '
          f'{r.get("fpk", 0) / 1e6:.0f} MHz), -3 dB up to {r["fhi"] / 1e6:.0f} MHz; imbalance at 434 MHz '
          f'{r["imb434"]:.1f} dB; out CM {r["ocm"]:.3f} V, I(VDD) {r["idd"] * 1e3:.3f} mA')
