"""Block testbench for comp_ct (schematic vs extracted layout).

VDD 1.8, ibias 1 uA (as bias_gen), inp = 1.0 V + vd, inn = 1.0 V, Cl load on out 10 fF.
  offset: DC sweep of vd at trim 0.9 V (mid code) -> vd where out crosses 0.9 V;
  trim gain: the same at trim 0.9 + 64 LSB (1.8 / 256 per LSB) -> mV per LSB;
  response: vd steps -1 mV -> +1 mV at 20 us, back at 60 us -> out delays (0.9 V).
(xschem tb_comp, schematic: offset +0.5..+1.8 mV over CM, trim ~0.07-0.1 mV/LSB, 0.36 us at 1 mV.)
--pex swaps in layout/pex/comp_ct.spice.

    python sim/comp_ct/tb_comp_ct.py [--pex] [corner]
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.path.join(ROOT, 'tools', 'osic')
PRM = 'w1=20 l1=1 mt1=10 rdeg=2Meg mta=2 lref=136 wcl=22'
LSB = 1.8 / 256


def subckt():
    out = os.path.join(B, 'tb_comp_ct')
    os.makedirs(out, exist_ok=True)
    subprocess.run([OSIC, 'bash', '-c', 'xschem -n -s -q --tcl "set top_subckt 1" -o build/tb_comp_ct xschem/comp_ct.sch'],
                   cwd=ROOT, capture_output=True)
    s = open(os.path.join(out, 'comp_ct.spice')).read()
    s = re.search(r'^\**\.subckt comp_ct .*?^\**\.ends', s, re.S | re.M).group(0)
    s = re.sub(r'^\**\.(subckt|ends)', r'.\1', s, flags=re.M)
    return s.replace('.subckt comp_ct inp inn trim ibias out VDD VSS', '.subckt comp_ct inp inn trim ibias out VDD VSS ' + PRM, 1)


def deck(corner, pex):
    pdk = os.environ.get('PDK_ROOT', '/foss/pdks')
    sub = '.include ../layout/pex/comp_ct.spice' if pex else subckt()
    inst = 'x1 inp inn trim ibias out VDD 0 comp_ct' + ('' if pex else ' ' + PRM)
    t1 = 0.9 + 64 * LSB
    return f"""* tb_comp_ct ({'extracted' if pex else 'schematic'}), {corner}
.lib {pdk}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
{sub}
VD VDD 0 1.8
Ib VDD ibias 1u
Vcm inn 0 1.0
Vdif inp inn dc 0 pwl(0 -1m 20u -1m 20.01u 1m 60u 1m 60.01u -1m)
Vt trim 0 0.9
{inst}
Co out 0 10f
.options method=GEAR
.control
dc Vdif -20m 20m 0.02m
meas dc off0 when v(out)=0.9 cross=1
echo RES off0=$&off0
reset
alter Vt dc = {t1:.5f}
dc Vdif -40m 40m 0.02m
meas dc off1 when v(out)=0.9 cross=1
echo RES off1=$&off1
reset
alter Vt dc = 0.9
tran 20n 100u 0
meas tran tup TRIG v(inp) VAL=1.0 RISE=1 TARG v(out) VAL=0.9 CROSS=1 TD=19u
meas tran tdn TRIG v(inp) VAL=1.0 FALL=1 TD=50u TARG v(out) VAL=0.9 CROSS=1 TD=59u
echo RES tup=$&tup tdn=$&tdn
.endc
.end
"""


def run(corner, pex):
    name = f'tb_comp_ct_{corner}' + ('_pex' if pex else '')
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(corner, pex))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    r = {k: float(v) for k, v in re.findall(r'(\w+)=([-0-9.eE+]+)', ' '.join(re.findall(r'^RES (.*)$', log, re.M)))}
    if 'off0' not in r:
        sys.exit(f'{name}: no results; see build/{name}.log')
    return r


if __name__ == '__main__':
    args = sys.argv[1:]
    pex = '--pex' in args
    corner = next((a for a in args if not a.startswith('-')), 'tt')
    r = run(corner, pex)
    gain = (r['off1'] - r['off0']) / 64
    print(f'comp_ct {corner} {"pex" if pex else "sch"}: offset {r["off0"] * 1e3:+.3f} mV (trim mid), '
          f'trim {gain * 1e3:+.4f} mV/LSB, +-1 mV response up/down '
          f'{r.get("tup", float("nan")) * 1e6:.2f}/{r.get("tdn", float("nan")) * 1e6:.2f} us')
