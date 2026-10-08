"""Block testbench for the r2r trim DAC (schematic vs extracted layout).

Ideal 1.8 V bits. DC: out at codes 0, 1, 85, 128, 135 (the servo's operating point),
255 against code/256 * 1.8 V, and Rout (1 uA into out at code 135). Transient: the
major carry 127 -> 128 (all bits switch, 1 ns edges) into the real load, 1 pF MIM
(the trim filter cap at the comparator); 0.1 % settling time.
--pex swaps in layout/pex/r2r.spice.

    python sim/dac/tb_r2r.py [--pex] [corner]
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.path.join(ROOT, 'tools', 'osic')
CODES = [0, 1, 85, 128, 135, 255]


def bits(code):
    return [1.8 * ((code >> i) & 1) for i in range(8)]


def deck(corner, pex, name):
    pdk = os.environ.get('PDK_ROOT', '/foss/pdks')
    if pex:
        sub = '.include ../layout/pex/r2r.spice'
    else:
        out = os.path.join(B, 'tb_r2r')
        os.makedirs(out, exist_ok=True)
        subprocess.run([OSIC, 'bash', '-c', 'xschem -n -s -q --tcl "set top_subckt 1" -o build/tb_r2r xschem/r2r.sch'],
                       cwd=ROOT, capture_output=True)
        s = open(os.path.join(out, 'r2r.spice')).read()
        s = re.search(r'^\**\.subckt r2r .*?^\**\.ends', s, re.S | re.M).group(0)
        sub = re.sub(r'^\**\.(subckt|ends)', r'.\1', s, flags=re.M)
    lo, hi = bits(127), bits(128)
    vb = '\n'.join(f'Vb{i} b{i} 0 pwl(0 {lo[i]} 10n {lo[i]} 11n {hi[i]})' for i in range(8))
    dc = ''
    for c in CODES:
        dc += ''.join(f'alter Vb{i} dc = {v}\n' for i, v in enumerate(bits(c)))
        dc += f'op\nlet v{c} = v(out)\necho RES v{c}=$&v{c}\nset s{c} = $&v{c}\nreset\n'
    return f"""* tb_r2r ({'extracted' if pex else 'schematic'}), {corner}
.lib {pdk}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
{sub}
{vb}
x1 b0 b1 b2 b3 b4 b5 b6 b7 out 0 r2r
Cl out 0 1p
Iout 0 out 0
.options method=GEAR
.control
{dc}
{''.join(f'alter Vb{i} dc = {v}' + chr(10) for i, v in enumerate(bits(135)))}
alter Iout dc = 1u
op
let rout = ($s135 - v(out)) / 1u
echo RES rout=$&rout
reset
alter Iout dc = 0
tran 10p 60n 0
meas tran vf find v(out) at=59n
meas tran tset WHEN v(out)=vf+0.0007 CROSS=LAST
.endc
.end
"""


def run(corner, pex):
    name = f'tb_r2r_{corner}' + ('_pex' if pex else '')
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(corner, pex, name))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    r = {k: float(v) for k, v in re.findall(r'^RES (\w+)=([-0-9.eE+]+)', log, re.M)}
    if 'rout' not in r:
        sys.exit(f'{name}: no results; see build/{name}.log')
    r.update({k: float(x) for k, x in re.findall(r'^(tset|vf)\s+=\s+([-0-9.eE+]+)', log, re.M)})
    return r


if __name__ == '__main__':
    args = sys.argv[1:]
    pex = '--pex' in args
    corner = next((a for a in args if not a.startswith('-')), 'tt')
    r = run(corner, pex)
    lsb = 1.8 / 256
    err = ', '.join(f'{c}: {(r[f"v{c}"] - c * lsb) / lsb:+.3f}' for c in CODES)
    print(f'r2r {corner} {"pex" if pex else "sch"}: error vs code/256*1.8 (LSB) {err}; '
          f'Rout {abs(r["rout"]) / 1e3:.2f} kOhm; 127->128 settles (0.1 LSB) at {(r["tset"] - 10e-9) * 1e9:.2f} ns after the edge')
