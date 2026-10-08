"""Block testbench for det_cell (schematic vs extracted layout).

As in log_det: vb from the replica (ibias_det = 2 uA into a diode-connected W 1 / L 0.15
NMOS with the same rs to VSS); out into rdet 8 kOhm || cdet 5 pF from VDD 1.8 V.
inp / inn: a 434 MHz differential sine at DC 1.2 V (the chain's output CM), amplitudes
0 / 20 / 100 / 400 mV peak per side, one cell each (all share the replica's vb).
Measures:
  - the idle out level and the rectified drop (out average over the last 100 ns of 400 ns);
  - the input capacitance on inp (Im(Y) / w at 434 MHz, inn at AC ground): the load the
    cell puts on its chain tap, where bottom-plate parasitics show.
--pex swaps in layout/pex/det_cell.spice (layout/pex.sh det_cell).

    python sim/det_cell/tb_det_cell.py [--pex] [corner]
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.path.join(ROOT, 'tools', 'osic')
PRM = 'wd=1 rs=10k cc=100f rb=200k'
AMPS = (0, 0.02, 0.1, 0.4)
F = 433.92e6


def subckt():
    out = os.path.join(B, 'tb_det_cell')
    os.makedirs(out, exist_ok=True)
    subprocess.run([OSIC, 'bash', '-c', 'xschem -n -s -q --tcl "set top_subckt 1" -o build/tb_det_cell xschem/det_cell.sch'],
                   cwd=ROOT, capture_output=True)
    s = open(os.path.join(out, 'det_cell.spice')).read()
    s = re.search(r'^\**\.subckt det_cell .*?^\**\.ends', s, re.S | re.M).group(0)
    s = re.sub(r'^\**\.(subckt|ends)', r'.\1', s, flags=re.M)
    # the top-level netlist drops the parameter defaults
    return re.sub(r'^(\.subckt det_cell [^\n]*)', rf'\1 {PRM}', s, count=1, flags=re.M)


def deck(corner, pex):
    x = '' if pex else ' ' + PRM
    cells = []
    for k, a in enumerate(AMPS):
        cells.append(f'Vp{k} p{k} 0 sin(1.2 {a} {F:.6e})\nVn{k} n{k} 0 sin(1.2 {-a} {F:.6e})\n'
                     f'x{k} p{k} n{k} vb o{k} 0 det_cell{x}\nRd{k} VD o{k} 8k\nCd{k} o{k} 0 5p')
    meas = '\n'.join(f'meas tran out{k} avg v(o{k}) from=300n to=400n' for k in range(len(AMPS)))
    save = ' '.join(f'v(o{k})' for k in range(len(AMPS)))
    return f"""* tb_det_cell ({'extracted' if pex else 'schematic'}), {corner}
.lib {os.environ.get('PDK_ROOT', '/foss/pdks')}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
{'.include ../layout/pex/det_cell.spice' if pex else subckt()}
VD VD 0 1.8
* vb replica (as log_det)
Ib VD vb 2u
XMb vb vb sb 0 sky130_fd_pr__nfet_01v8 L=0.15 W=1 nf=1
XRsb 0 sb 0 sky130_fd_pr__res_high_po_0p35 L=9.0824 mult=1
{chr(10).join(cells)}
* input C: an AC copy with its own output load
Vac pa 0 dc 1.2 ac 1
xac pa 0 vb oac 0 det_cell{x}
Rdac VD oac 8k
.options method=GEAR
.control
save vb {save} i(Vac)
op
let vbop = v(vb)
print vbop
ac lin 1 {F:.6e} {F:.6e}
let cin = imag(-i(Vac)) / (2 * pi * {F:.6e}) * 1e15
print cin
tran 20p 400n
{meas}
echo RESULTS
.endc
.end
"""


def run(corner, pex):
    name = f'tb_det_cell_{corner}' + ('_pex' if pex else '')
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(corner, pex))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    r = {k: float(x) for k, x in re.findall(r'^(\w+)\s+=\s+([-0-9.eE+]+)', log, re.M)}
    if f'out{len(AMPS) - 1}' not in r or 'cin' not in r:
        sys.exit(f'{name}: no results; see build/{name}.log')
    return r


if __name__ == '__main__':
    args = sys.argv[1:]
    pex = '--pex' in args
    corner = next((a for a in args if not a.startswith('-')), 'tt')
    r = run(corner, pex)
    o0 = r['out0']
    drops = ', '.join(f'{a * 1e3:.0f} mV {(o0 - r[f"out{k}"]) * 1e3:.2f}' for k, a in enumerate(AMPS) if k)
    print(f'det_cell {corner} {"pex" if pex else "sch"}: vb {r["vbop"]:.4f} V, idle out {o0:.4f} V; '
          f'drop (mV) at {drops}; Cin(inp) {r["cin"]:.1f} fF')
