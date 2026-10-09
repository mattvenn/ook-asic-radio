"""Block testbench for the level shifters (schematic vs extracted layout).

tx_ls (main): in = ideal 1.8 V 434 MHz square (100 ps edges); A and B drive the
  'in' of a tx_drv arm each (schematic tx_drv, en high, out into 1 pF), as in tx_top.
tx_ls_en: in = one 1.8 V pulse (on at 2 ns, off at 12 ns); A drives a tx_drv 'en'.
Measures A/B 20-80 % edges, delay in -> A (rise/fall), A duty cycle (main),
and VDD / VAPWR average current. --pex swaps in layout/pex/<variant>.spice.

    python sim/tx/tb_tx_ls.py [--pex] [tx_ls|tx_ls_en] [corner]
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.path.join(ROOT, 'tools', 'osic')
T = 1 / 433.92e6
PRM = {'tx_ls': 'kn=14 kp=8 wpi=9 wni=3', 'tx_ls_en': 'kn=1 kp=1 wpi=1 wni=0.42'}


def subckts(cells=('tx_ls', 'tx_drv')):
    out = os.path.join(B, 'tb_tx_ls')
    os.makedirs(out, exist_ok=True)
    txt = ''
    for c in cells:
        subprocess.run([OSIC, 'bash', '-c', f'xschem -n -s -q --tcl "set top_subckt 1" -o build/tb_tx_ls xschem/{c}.sch'],
                       cwd=ROOT, capture_output=True)
        s = open(os.path.join(out, f'{c}.spice')).read()
        s = re.search(rf'^\**\.subckt {c} .*?^\**\.ends', s, re.S | re.M).group(0)
        s = re.sub(r'^\**\.(subckt|ends)', r'.\1', s, flags=re.M)
        if c == 'tx_ls':      # the top-level netlist drops the parameter defaults
            s = s.replace('.subckt tx_ls in A B VDD VAPWR VSS', '.subckt tx_ls in A B VDD VAPWR VSS ' + PRM['tx_ls'], 1)
        txt += s + '\n'
    return txt


def deck(v, corner, pex):
    if v != 'tx_ls_en':          # the ring -> arms shifter (and its variants)
        vin = f'pulse(0 1.8 0 100p 100p {T / 2 - 100e-12:.4e} {T:.4e})'
        loads = ('xdp A VA out_p VAPWR 0 tx_drv\nxdn B VA out_n VAPWR 0 tx_drv\n'
                 'Cop out_p 0 1p\nCon out_n 0 1p\n')
        t0, tstop, n = 8e-9, 8e-9 + 8 * T, 3
    else:
        vin = 'pwl(0 0 2n 0 2.1n 1.8 12n 1.8 12.1n 0)'
        loads = 'xdp VA A out_p VAPWR 0 tx_drv\nCop out_p 0 1p\n'
        t0, tstop, n = 0, 20e-9, 1
    inst = f'x1 in A B VDD VAPWR 0 {v}' if pex else f'x1 in A B VDD VAPWR 0 tx_ls {PRM[v]}'
    src = f"""* tb_tx_ls {v} ({'extracted' if pex else 'schematic'}), {corner}
.lib {os.environ.get('PDK_ROOT', '/foss/pdks')}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
{subckts(('tx_drv',) if pex else ('tx_ls', 'tx_drv'))}
{'.include ../layout/pex/' + v + '.spice' if pex else ''}
VD VDD 0 1.8
VA VAPWR 0 3.3
VH VA 0 3.3
Vin in 0 {vin}
{inst}
{loads}
.options method=GEAR
.control
save v(in) v(a) v(b) v(out_p) v(out_n) i(VD) i(VA)
tran 2p {tstop:.4e} 0
let t0 = {t0:.4e}
let t1 = {tstop:.4e}
meas tran ivd avg i(VD) from=$&t0 to=$&t1
meas tran iva avg i(VA) from=$&t0 to=$&t1
meas tran tr TRIG v(a) VAL=0.66 RISE={n} TARG v(a) VAL=2.64 RISE={n}
meas tran tf TRIG v(a) VAL=2.64 FALL={n} TARG v(a) VAL=0.66 FALL={n}
meas tran tdr TRIG v(in) VAL=0.9 RISE={n} TARG v(a) VAL=1.65 RISE={n}
meas tran tdf TRIG v(in) VAL=0.9 FALL={n} TARG v(a) VAL=1.65 FALL={n}
"""
    if v != 'tx_ls_en':
        src += """let ah = v(a) gt 1.65
meas tran duty avg ah from=$&t0 to=$&t1
meas tran tdbr TRIG v(in) VAL=0.9 FALL=3 TARG v(b) VAL=1.65 RISE=3
let oph = v(out_p) gt 1.65
let onh = v(out_n) gt 1.65
meas tran dutyp avg oph from=$&t0 to=$&t1
meas tran dutyn avg onh from=$&t0 to=$&t1
"""
    src += 'echo RESULTS\n.endc\n.end\n'
    return src


def run(v, corner, pex):
    name = f'tb_{v}_{corner}' + ('_pex' if pex else '')
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(v, corner, pex))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    r = {k: float(x) for k, x in re.findall(r'^(\w+)\s+=\s+([-0-9.eE+]+)', log, re.M)}
    if 'tdr' not in r:
        sys.exit(f'{name}: no results; see build/{name}.log')
    return r


if __name__ == '__main__':
    args = sys.argv[1:]
    pex = '--pex' in args
    v = next((a for a in args if a.startswith('tx_ls')), 'tx_ls')
    corner = next((a for a in args if not a.startswith('-') and not a.startswith('tx_ls')), 'tt')
    r = run(v, corner, pex)
    line = (f'{v} {corner} {"pex" if pex else "sch"}: A tr/tf {r["tr"] * 1e12:.0f}/{r["tf"] * 1e12:.0f} ps, '
            f'delay in->A r/f {r["tdr"] * 1e12:.0f}/{r["tdf"] * 1e12:.0f} ps')
    if 'duty' in r:
        line += (f', A duty {r["duty"] * 100:.1f} %, in->B {r["tdbr"] * 1e12:.0f} ps; '
                 f'arm out duty p/n {r["dutyp"] * 100:.1f}/{r["dutyn"] * 100:.1f} %')
    line += f'; I(VDD) {-r["ivd"] * 1e3:.3f} mA, I(VAPWR) {-r["iva"] * 1e3:.3f} mA'
    print(line)
