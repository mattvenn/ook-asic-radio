"""Block testbench for log_det (schematic vs extracted layout).

VDD 1.8, ibias_det 2 uA, taps t1..t5 quiet (inputs at 0 V: they're AC coupled), t6 driven
differentially at 433.92 MHz with amplitude a (peak, each side +-a/2). det averaged over
the last 100 ns of 600 ns, for a = 0 (idle), 1, 10, 100 mV.
--pex swaps in layout/pex/log_det.spice.

    python sim/logdet/tb_log_det.py [--pex] [corner]
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.path.join(ROOT, 'tools', 'osic')
PRM = 'wd=1 rs=10k cc=100f rb=200k rdet=8k cdet=1p'
AMPS = [0, 1e-3, 10e-3, 100e-3]


def subckts():
    out = os.path.join(B, 'tb_log_det')
    os.makedirs(out, exist_ok=True)
    txt = ''
    for c in ('log_det', 'det_cell'):
        subprocess.run([OSIC, 'bash', '-c', f'xschem -n -s -q --tcl "set top_subckt 1" -o build/tb_log_det xschem/{c}.sch'],
                       cwd=ROOT, capture_output=True)
        s = open(os.path.join(out, f'{c}.spice')).read()
        s = re.search(rf'^\**\.subckt {c} .*?^\**\.ends', s, re.S | re.M).group(0)
        s = re.sub(r'^\**\.(subckt|ends)', r'.\1', s, flags=re.M)
        if c == 'log_det':
            s = re.sub(r'^(\.subckt log_det [^\n]*)', r'\1 ' + PRM, s, count=1, flags=re.M)
        else:
            s = re.sub(r'^(\.subckt det_cell [^\n]*)', r'\1 wd=1 rs=10k cc=100f rb=200k', s, count=1, flags=re.M)
        txt += s + '\n'
    return txt


def deck(corner, pex):
    pdk = os.environ.get('PDK_ROOT', '/foss/pdks')
    sub = '.include ../layout/pex/log_det.spice' if pex else subckts()
    pins = ' '.join(f't{k}p t{k}n' for k in range(1, 7))
    inst = f'x1 {pins} ibias det VDD 0 log_det' + ('' if pex else ' ' + PRM)
    quiet = '\n'.join(f'Vq{k}p t{k}p 0 0\nVq{k}n t{k}n 0 0' for k in range(1, 6))
    runs = ''
    for a in AMPS:
        runs += f"""alter @V6p[sin] = [ 0 {a / 2:g} 433.92e6 ]
alter @V6n[sin] = [ 0 {-a / 2:g} 433.92e6 ]
tran 50p 600n 0
meas tran det_{int(a * 1e3)} avg v(det) from=500n to=600n
echo RES det_{int(a * 1e3)}=$&det_{int(a * 1e3)}
reset
"""
    return f"""* tb_log_det ({'extracted' if pex else 'schematic'}), {corner}
.lib {pdk}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
{sub}
VD VDD 0 1.8
Ib VDD ibias 2u
{quiet}
V6p t6p 0 sin(0 0 433.92e6)
V6n t6n 0 sin(0 0 433.92e6)
{inst}
.options method=GEAR
.control
save v(det)
{runs}.endc
.end
"""


def run(corner, pex):
    name = f'tb_log_det_{corner}' + ('_pex' if pex else '')
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(corner, pex))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    r = {k: float(v) for k, v in re.findall(r'^RES (\w+)=([-0-9.eE+]+)', log, re.M)}
    if len(r) < len(AMPS):
        sys.exit(f'{name}: no results; see build/{name}.log')
    return r


if __name__ == '__main__':
    args = sys.argv[1:]
    pex = '--pex' in args
    corner = next((a for a in args if not a.startswith('-')), 'tt')
    r = run(corner, pex)
    idle = r['det_0']
    print(f'log_det {corner} {"pex" if pex else "sch"}: det idle {idle:.4f} V; change at t6 = '
          + ', '.join(f'{int(a * 1e3)} mV: {(r[f"det_{int(a * 1e3)}"] - idle) * 1e3:+.2f} mV' for a in AMPS[1:]))
