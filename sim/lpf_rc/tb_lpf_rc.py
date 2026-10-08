"""Block testbench for lpf_rc (schematic vs extracted layout).

Driven like the detector output (as xschem/tb_lpf.sch): an ideal source with 8 kOhm
in series, unloaded output. Measures
  - AC: f-3dB, and the attenuation at 434 / 868 MHz (the detector's carrier ripple:
    coupling across the resistor in the layout would show up here);
  - step: 10 mV at 1.40 V, 10-90 % rise time.
--pex swaps in layout/pex/lpf_rc.spice (layout/pex.sh lpf_rc).

    python sim/lpf_rc/tb_lpf_rc.py [--pex] [corner]
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.path.join(ROOT, 'tools', 'osic')
PRM = 'lr=400 nc=2'


def subckt():
    out = os.path.join(B, 'tb_lpf_rc')
    os.makedirs(out, exist_ok=True)
    subprocess.run([OSIC, 'bash', '-c', 'xschem -n -s -q --tcl "set top_subckt 1" -o build/tb_lpf_rc xschem/lpf_rc.sch'],
                   cwd=ROOT, capture_output=True)
    s = open(os.path.join(out, 'lpf_rc.spice')).read()
    s = re.search(r'^\**\.subckt lpf_rc .*?^\**\.ends', s, re.S | re.M).group(0)
    s = re.sub(r'^\**\.(subckt|ends)', r'.\1', s, flags=re.M)
    # the top-level netlist drops the parameter defaults
    return re.sub(r'^(\.subckt lpf_rc [^\n]*)', rf'\1 {PRM}', s, count=1, flags=re.M)


def deck(corner, pex):
    src = f"""* tb_lpf_rc ({'extracted' if pex else 'schematic'}), {corner}
.lib {os.environ.get('PDK_ROOT', '/foss/pdks')}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
{'.include ../layout/pex/lpf_rc.spice' if pex else subckt()}
Vsrc src 0 dc 1.4 ac 1 pwl(0 1.4 20u 1.4 20.01u 1.41)
Rdet src in 8k
x1 in out 0 lpf_rc{'' if pex else ' ' + PRM}
.options method=GEAR
.control
save v(src) v(in) v(out)
ac dec 50 100 1g
let g = db(v(out)/v(src))
meas ac f3db when g=-3
meas ac g434 find g at=433.92e6
meas ac g868 find g at=867.84e6
tran 0.1u 200u
meas tran t10 when v(out)=1.401 rise=1
meas tran t90 when v(out)=1.409 rise=1
echo RESULTS
.endc
.end
"""
    return src


def run(corner, pex):
    name = f'tb_lpf_rc_{corner}' + ('_pex' if pex else '')
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(corner, pex))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    r = {k: float(x) for k, x in re.findall(r'^(\w+)\s+=\s+([-0-9.eE+]+)', log, re.M)}
    if 'f3db' not in r or 't90' not in r:
        sys.exit(f'{name}: no results; see build/{name}.log')
    return r


if __name__ == '__main__':
    args = sys.argv[1:]
    pex = '--pex' in args
    corner = next((a for a in args if not a.startswith('-')), 'tt')
    r = run(corner, pex)
    print(f'lpf_rc {corner} {"pex" if pex else "sch"}: f-3dB {r["f3db"] / 1e3:.2f} kHz, '
          f'rise 10-90 % {(r["t90"] - r["t10"]) * 1e6:.2f} us, '
          f'at 434 MHz {r["g434"]:.1f} dB, at 868 MHz {r["g868"]:.1f} dB')
