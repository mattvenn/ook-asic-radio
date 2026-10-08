"""Block testbench for tx_ring (schematic with cw vs extracted layout).

en steps high at 1 ns; out drives the main level shifter (schematic tx_ls, its input
inverter 9/3 is the ring's designed load). Measures the oscillation frequency over the
last 10 periods of 40 ns, out duty, and VDD current. --pex swaps in layout/pex/tx_ring.spice.
Silicon estimate: x0.866 (the ttsky25b ring's measured / extracted-tt ratio, STATUS).

    python sim/tx/tb_tx_ring.py [--pex] [corner] [cw=3.2f]
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.environ.get('OSIC', os.path.join(ROOT, 'tools', 'osic'))
TSTOP = 40e-9


def subckt(c, params=''):
    out = os.path.join(B, 'tb_tx_ring')
    os.makedirs(out, exist_ok=True)
    subprocess.run([OSIC, 'bash', '-c', f'xschem -n -s -q --tcl "set top_subckt 1" -o build/tb_tx_ring xschem/{c}.sch'],
                   cwd=ROOT, capture_output=True)
    s = open(os.path.join(out, f'{c}.spice')).read()
    s = re.search(rf'^\**\.subckt {c} .*?^\**\.ends', s, re.S | re.M).group(0)
    s = re.sub(r'^\**\.(subckt|ends)', r'.\1', s, flags=re.M)
    if params:          # the top-level netlist drops the parameter defaults
        s = re.sub(rf'^(\.subckt {c} [^\n]*)', rf'\1 {params}', s, count=1, flags=re.M)
    return s + '\n'


def deck(corner, pex, cw, name):
    pdk = os.environ.get('PDK_ROOT', '/foss/pdks')
    ring = '.include ../layout/pex/tx_ring.spice' if pex else subckt('tx_ring', f'cw={cw}')
    return f"""* tb_tx_ring ({'extracted' if pex else 'schematic cw=' + cw}), {corner}
.lib {pdk}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
.include {pdk}/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice
{ring}
{subckt('tx_ls', 'kn=10 kp=4 wpi=9 wni=3')}
VD VDD 0 1.8
VA VAPWR 0 3.3
Ven en 0 pwl(0 0 1n 0 1.05n 1.8)
x1 en out VDD 0 tx_ring
xls out a b VDD VAPWR 0 tx_ls
.options method=GEAR
.control
save v(out) i(VD)
tran 2p {TSTOP:.4e} 0
meas tran ivd avg i(VD) from=20n to={TSTOP:.4e}
write {name}.raw v(out)
echo RESULTS
.endc
.end
"""


def run(corner, pex, cw):
    name = f'tb_tx_ring_{corner}' + ('_pex' if pex else '')
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(corner, pex, cw, name))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    r = {k: float(x) for k, x in re.findall(r'^(\w+)\s+=\s+([-0-9.eE+]+)', log, re.M)}
    if 'ivd' not in r:
        sys.exit(f'{name}: no results; see build/{name}.log')
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    import numpy as np
    from rawread import read_raw
    v = read_raw(os.path.join(B, name + '.raw'))[0]['vars']
    t, y = np.real(v['time']), np.real(v['v(out)'])
    up = np.where((y[:-1] < 0.9) & (y[1:] >= 0.9))[0]
    tu = t[up] + (0.9 - y[up]) * (t[up + 1] - t[up]) / (y[up + 1] - y[up])
    tu = tu[tu > 20e-9][-11:]                    # last 10 full periods after settling
    per = (tu[-1] - tu[0]) / (len(tu) - 1)
    m = (t >= tu[0]) & (t <= tu[-1])
    duty = np.trapezoid((y[m] > 0.9).astype(float), t[m]) / (tu[-1] - tu[0])
    return dict(f=1 / per, duty=duty, ivd=-r['ivd'])


if __name__ == '__main__':
    args = sys.argv[1:]
    pex = '--pex' in args
    cw = next((a.split('=')[1] for a in args if a.startswith('cw=')), '3.2f')
    corner = next((a for a in args if not a.startswith('-') and '=' not in a), 'tt')
    r = run(corner, pex, cw)
    print(f'tx_ring {corner} {"pex" if pex else "sch cw=" + cw}: {r["f"] / 1e6:.1f} MHz '
          f'(x0.866 -> ~{r["f"] * 0.866 / 1e6:.0f} MHz on silicon), out duty {r["duty"] * 100:.1f} %, '
          f'I(VDD) {r["ivd"] * 1e3:.2f} mA (ring + level shifter)')
