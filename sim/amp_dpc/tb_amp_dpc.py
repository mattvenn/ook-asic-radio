"""Block testbench for amp_dpc (schematic vs extracted layout).

As in lna_chain: nb from the reference diode (iref 60 uA into W 6 nf 2 / L 0.5, so each
side's tail is mt/2 x 60 uA = 180 uA); inputs at the previous stage's output level
(1.8 V - 4k x 180 uA = 1.08 V), driven differentially (1 V AC); outputs loaded by a
schematic copy of the next stage. Measures, on the differential output:
  - gain at 434 MHz, peak gain and where, the low / high -3 dB corners (cap degeneration
    gives the low corner, the loads' and parasitics' C the high one);
  - op: output common mode, supply current;
  - the AC imbalance at 434 MHz, |v(outp) + v(outn)| / |v(outp) - v(outn)|, which shows
    asymmetric parasitics (inn / outn cross the cell).
--pex swaps in layout/pex/amp_dpc.spice (layout/pex.sh amp_dpc).

    python sim/amp_dpc/tb_amp_dpc.py [--pex] [corner]
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.path.join(ROOT, 'tools', 'osic')
PRM = 'w=20 l=0.15 rl=4k wt=6 mt=6 mm=0 cs=0.6p'
F = 433.92e6


def subckt(name):
    out = os.path.join(B, 'tb_amp_dpc')
    os.makedirs(out, exist_ok=True)
    subprocess.run([OSIC, 'bash', '-c', 'xschem -n -s -q --tcl "set top_subckt 1" -o build/tb_amp_dpc xschem/amp_dpc.sch'],
                   cwd=ROOT, capture_output=True)
    s = open(os.path.join(out, 'amp_dpc.spice')).read()
    s = re.search(r'^\**\.subckt amp_dpc .*?^\**\.ends', s, re.S | re.M).group(0)
    s = re.sub(r'^\**\.(subckt|ends)', r'.\1', s, flags=re.M)
    # the top-level netlist drops the parameter defaults; rename (the load copy stays schematic)
    return re.sub(r'^\.subckt amp_dpc ([^\n]*)', rf'.subckt {name} \1 {PRM}', s, count=1, flags=re.M)


def deck(corner, pex):
    dut = 'amp_dpc' if pex else 'amp_dpc_sch'
    return f"""* tb_amp_dpc ({'extracted' if pex else 'schematic'}), {corner}
.lib {os.environ.get('PDK_ROOT', '/foss/pdks')}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
{subckt('amp_dpc_sch')}
{'.include ../layout/pex/amp_dpc.spice' if pex else ''}
VD VDD 0 1.8
Iref VDD nb 60u
XMref nb nb 0 0 sky130_fd_pr__nfet_01v8 L=0.5 W=6 nf=2
Vp inp 0 dc 1.08 ac 0.5
Vn inn 0 dc 1.08 ac 0.5 180
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
meas ac flo when gd=gm3 rise=1
meas ac fhi when gd=gm3 fall=last
echo RESULTS
.endc
.end
"""


def run(corner, pex):
    name = f'tb_amp_dpc_{corner}' + ('_pex' if pex else '')
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(corner, pex))
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
    pex = '--pex' in args
    corner = next((a for a in args if not a.startswith('-')), 'tt')
    r = run(corner, pex)
    print(f'amp_dpc {corner} {"pex" if pex else "sch"}: gain at 434 MHz {r["g434"]:.2f} dB '
          f'(peak {r["gmax"]:.2f} dB at {r["fpk"] / 1e6:.0f} MHz), -3 dB {r["flo"] / 1e6:.1f} MHz .. '
          f'{r["fhi"] / 1e6:.0f} MHz; imbalance at 434 MHz {r["imb434"]:.1f} dB; '
          f'out CM {r["ocm"]:.3f} V, I(VDD) {r["idd"] * 1e3:.3f} mA')
