"""Block testbench for dbg_tg (schematic vs extracted layout).

a = det side, b = ua[2] pad side, VDD 1.8 V.
  - on (en = 1.8): switch resistance at a = 0.2 / 0.9 / 1.6 V (b held 1 mV above a,
    Ron = 1 mV / I);
  - off (en = 0): isolation from the pad into det: b driven by a 50 Ohm source, a loaded
    like det (8 kOhm || 5 pF, as tb_dbg); |v(a)/v(src)| at 1 / 100 / 434 MHz. Coupling
    across the switch in the layout shows up here.
--pex swaps in layout/pex/dbg_tg.spice (layout/pex.sh dbg_tg).

    python sim/dbg_tg/tb_dbg_tg.py [--pex] [corner]
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.path.join(ROOT, 'tools', 'osic')
PRM = 'wn=2 wp=4'
VA = (0.2, 0.9, 1.6)


def subckt():
    out = os.path.join(B, 'tb_dbg_tg')
    os.makedirs(out, exist_ok=True)
    subprocess.run([OSIC, 'bash', '-c', 'xschem -n -s -q --tcl "set top_subckt 1" -o build/tb_dbg_tg xschem/dbg_tg.sch'],
                   cwd=ROOT, capture_output=True)
    s = open(os.path.join(out, 'dbg_tg.spice')).read()
    s = re.search(r'^\**\.subckt dbg_tg .*?^\**\.ends', s, re.S | re.M).group(0)
    s = re.sub(r'^\**\.(subckt|ends)', r'.\1', s, flags=re.M)
    # the top-level netlist drops the parameter defaults
    return re.sub(r'^(\.subckt dbg_tg [^\n]*)', rf'\1 {PRM}', s, count=1, flags=re.M)


def deck(corner, pex):
    x = '' if pex else ' ' + PRM
    ron = '\n'.join(f'Va{k} a{k} 0 {v}\nVb{k} b{k} 0 {v + 1e-3:.4f}\nxon{k} a{k} von b{k} VD 0 dbg_tg{x}'
                    for k, v in enumerate(VA))
    meas = '\n'.join(f'let ron{k} = 1e-3 / abs(i(Va{k}))\nprint ron{k}' for k in range(len(VA)))
    return f"""* tb_dbg_tg ({'extracted' if pex else 'schematic'}), {corner}
.lib {os.environ.get('PDK_ROOT', '/foss/pdks')}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
{'.include ../layout/pex/dbg_tg.spice' if pex else subckt()}
VD VD 0 1.8
Von von 0 1.8
* on: Ron at three levels
{ron}
* off: pad (b, 50 Ohm source) -> det (a, 8k || 5p)
Vsrc src 0 dc 0.9 ac 1
Rsrc src boff 50
xoff aoff 0 boff VD 0 dbg_tg{x}
Rdet aoff dcm 8k
Cdet aoff 0 5p
Vdcm dcm 0 1.44
.control
op
{meas}
ac dec 20 1e6 1e9
let g = db(v(aoff)/v(src))
meas ac g1m find g at=1e6
meas ac g100m find g at=100e6
meas ac g434m find g at=433.92e6
echo RESULTS
.endc
.end
"""


def run(corner, pex):
    name = f'tb_dbg_tg_{corner}' + ('_pex' if pex else '')
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(corner, pex))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    r = {k: float(x) for k, x in re.findall(r'^(\w+)\s+=\s+([-0-9.eE+]+)', log, re.M)}
    if 'g434m' not in r or 'ron0' not in r:
        sys.exit(f'{name}: no results; see build/{name}.log')
    return r


if __name__ == '__main__':
    args = sys.argv[1:]
    pex = '--pex' in args
    corner = next((a for a in args if not a.startswith('-')), 'tt')
    r = run(corner, pex)
    ron = ', '.join(f'{v} V {r[f"ron{k}"] / 1e3:.2f} k' for k, v in enumerate(VA))
    print(f'dbg_tg {corner} {"pex" if pex else "sch"}: Ron {ron}; off pad->det '
          f'{r["g1m"]:.1f} / {r["g100m"]:.1f} / {r["g434m"]:.1f} dB at 1 / 100 / 434 MHz')
