"""
Generate the TX chain blocks and their testbench (first pass was raw spice in
sim/tx/tx_explore.py; sizes and results in STATUS "TX chain, first pass").

  tx_ring : nand2_2 enable + 22 x inv_2 (23 stages), cw (3.2 fF) wiring per
            stage: the stand-in for layout, calibrated against the ttsky25b
            ring's extracted netlist. en = 0 stops it with out = 1.
  tx_ls   : 1.8 -> 3.3 V level shifter, the R2R DAC's dac_drive with a skewed
            core: thin input inverter (wpi/wni; W 9/3 is the load the ring
            was calibrated with) -> hvt/thin ctrl_n inverter -> thick
            cross-coupled core, pull-down NMOS kn x 0.42 um, PMOS kp x 0.42,
            L 0.5. A follows in, B is its complement. kn 14 / kp 8 (was 10 / 4: the p arm's
            duty collapsed under the extracted a / b load; sim/top/tb_tile_tx.py) runs at
            433 and 600 MHz; kn 1 / kp 1 (the DAC's own sizing) is fine for
            the static enables.
  tx_drv  : one antenna arm on VAPWR: thick NAND2 (in, en) then an inverter
            taper (x4 per stage) to the final N wn / P 3 wn, L 0.5.
            out = in & en: en = 0 parks the arm low.
  tx_top  : ring -> tx_ls -> tx_drv on A (out_p) and on B (out_n): the latch's
            two nodes are inherently antiphase. Each arm has its own enable
            through a small tx_ls, so:
              en_p = en_n = key : both arms low when off (no DC across the
                                  dipole), the normal mode;
              en_n = 0          : single-ended (monopole) fallback on out_p.
  tb_tx   : VDPWR 1.8 V, VAPWR 3.3 V, key on 5..60 ns, both enables follow
            the key ('ven_n' = 0 for the single-ended case) -> pad_model per
            arm -> dipole (73 ohm + 100 pF series: open at DC).
            Analyse: sim/tx/tb_tx.py.

    python xschem/gen/tx.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from xsch import Sch, mos, ports, stdcell, write_symbol

XDIR = os.path.normpath(os.path.join(HERE, '..'))
NINV = 22
LS_PARAMS = {'kn': 14, 'kp': 8, 'wpi': 9, 'wni': 3}
DRV_N = [0.42, 1.68, 6.72, 26.88, 48]        # inverter taper after the NAND (x4, final N 48)


def nf_of(w):
    return max(1, int(round(w / 10)))


def tx_ring():
    s = Sch()
    s.text(-700, -560, f'tx_ring: nand2_2 enable + {NINV} x inv_2 ({NINV + 1} stages), cw wiring C per stage\n'
           'cw 3.2 fF reproduces the ttsky25b ring extracted (598 MHz tt); en = 0 stops it with out = 1', 0.4)
    ports(s, -700, -460, ['VDD', 'VSS', 'en', 'out'])
    nd = stdcell(s, 'nand2_2', -400, 0, name='xr0')
    s.connect(nd, A='en', B=f'r{NINV}', Y='out')
    c = s.place('devices/capa.sym', -300, 100, name='Cr0', value="'cw'", m='1')
    s.connect(c, p='out', m='VSS')
    prev = 'out'
    for i in range(1, NINV + 1):
        x = -200 + (i - 1) % 11 * 200
        y = (i - 1) // 11 * 300
        iv = stdcell(s, 'inv_2', x, y, name=f'xr{i}')
        s.connect(iv, A=prev, Y=f'r{i}')
        c = s.place('devices/capa.sym', x + 80, y + 100, name=f'Cr{i}', value="'cw'", m='1')
        s.connect(c, p=f'r{i}', m='VSS')
        prev = f'r{i}'
    s.write(os.path.join(XDIR, 'tx_ring.sch'))
    write_symbol(os.path.join(XDIR, 'tx_ring.sym'), left=['en'], right=['out'], top=['VDD'],
                 bottom=['VSS'], params={'cw': '3.2f'})


def tx_ls():
    s = Sch()
    s.text(-700, -560, 'tx_ls: 1.8 -> 3.3 V level shifter (R2R DAC dac_drive, skewed core)\n'
           'in -> thin inverter (wpi/wni) -> ctrl; core NMOS kn x 0.42, PMOS kp x 0.42, L 0.5 thick. '
           'A = in, B = not in', 0.4)
    ports(s, -700, -460, ['VDD', 'VAPWR', 'VSS', 'in', 'A', 'B'])
    # input inverter (the ring's calibrated load when wpi/wni = 9/3)
    p = mos(s, 'p', -400, -150, W="'wpi'", L=0.15, name='Mi1p')
    s.connect(p, D='ctrl', G='in', S='VDD', B='VDD')
    n = mos(s, 'n', -400, 100, W="'wni'", L=0.15, name='Mi1n')
    s.connect(n, D='ctrl', G='in', S='VSS', B='VSS')
    # ctrl_n inverter: was dac_drive's hvt PMOS 1 / NMOS 0.42, too weak for M10's thick
    # gate + the ctrl_n wiring (extracted A duty 37 -> 28 %); now about as strong as the
    # input inverter, so both paths into the core are balanced (2026-10-08)
    p = mos(s, 'p', -100, -150, W=4, L=0.15, name='M8', vt='hvt')
    s.connect(p, D='ctrl_n', G='ctrl', S='VDD', B='VDD')
    n = mos(s, 'n', -100, 100, W=1.68, L=0.15, name='M7')
    s.connect(n, D='ctrl_n', G='ctrl', S='VSS', B='VSS')
    # thick core: pull-downs kn x, cross-coupled PMOS kp x
    for nm, x, g, d in (('M9', 200, 'ctrl', 'A'), ('M10', 500, 'ctrl_n', 'B')):
        m = mos(s, 'n', x, 100, W="'0.42*kn'", L=0.5, name=nm, vt='g5')
        s.connect(m, D=d, G=g, S='VSS', B='VSS')
    for nm, x, g, d in (('M11', 200, 'B', 'A'), ('M12', 500, 'A', 'B')):
        m = mos(s, 'p', x, -150, W="'0.42*kp'", L=0.5, name=nm, vt='g5')
        s.connect(m, D=d, G=g, S='VAPWR', B='VAPWR')
    s.write(os.path.join(XDIR, 'tx_ls.sch'))
    write_symbol(os.path.join(XDIR, 'tx_ls.sym'), left=['in'], right=['A', 'B'], top=['VDD', 'VAPWR'],
                 bottom=['VSS'], params=LS_PARAMS)


def tx_drv():
    s = Sch()
    s.text(-700, -560, 'tx_drv: one antenna arm on VAPWR, out = in & en\n'
           'thick NAND2 then inverters x4 per stage: N ' + ' / '.join(f'{w:g}' for w in DRV_N) +
           ' um, P = 3 N, L 0.5', 0.4)
    ports(s, -700, -460, ['VAPWR', 'VSS', 'in', 'en', 'out'])
    # NAND2: 'in' on the NMOS next to the output (the fast input), en below it.
    # Series NMOS 2 x 0.42, PMOS 1.26: same pull-up as the inverter it replaces.
    for nm, x, g in (('Mna', -400, 'in'), ('Mnb', -200, 'en')):
        p = mos(s, 'p', x, -150, W=1.26, L=0.5, name=nm + 'p', vt='g5')
        s.connect(p, D='y0', G=g, S='VAPWR', B='VAPWR')
    m = mos(s, 'n', -400, 100, W=0.84, L=0.5, name='Mnan', vt='g5')
    s.connect(m, D='y0', G='in', S='ns', B='VSS')
    m = mos(s, 'n', -400, 250, W=0.84, L=0.5, name='Mnbn', vt='g5')
    s.connect(m, D='ns', G='en', S='VSS', B='VSS')
    prev = 'y0'
    for i, wn in enumerate(DRV_N, 1):
        y = 'out' if i == len(DRV_N) else f'y{i}'
        x = -100 + i * 250
        p = mos(s, 'p', x, -150, W=round(3 * wn, 3), L=0.5, nf=nf_of(3 * wn), name=f'M{i}p', vt='g5')
        s.connect(p, D=y, G=prev, S='VAPWR', B='VAPWR')
        n = mos(s, 'n', x, 100, W=round(wn, 3), L=0.5, nf=nf_of(wn), name=f'M{i}n', vt='g5')
        s.connect(n, D=y, G=prev, S='VSS', B='VSS')
        prev = y
    s.write(os.path.join(XDIR, 'tx_drv.sch'))
    write_symbol(os.path.join(XDIR, 'tx_drv.sym'), left=['in', 'en'], right=['out'], top=['VAPWR'],
                 bottom=['VSS'])


def tx_top():
    s = Sch()
    s.text(-700, -760, 'tx_top: ring -> level shifter -> antiphase arms (A -> out_p, B -> out_n)\n'
           'en_p / en_n (1.8 V) gate each arm: both = key normally (off: both arms low); '
           'en_n = 0: single-ended fallback', 0.4)
    ports(s, -700, -660, ['VDPWR', 'VAPWR', 'VSS', 'key', 'en_p', 'en_n', 'out_p', 'out_n'])
    r = s.place('tx_ring.sym', -400, 0, name='xring')
    s.connect(r, en='key', out='ring', VDD='VDPWR', VSS='VSS')
    ls = s.place('tx_ls.sym', 0, 0, name='xls')
    s.connect(ls, **{'in': 'ring'}, A='a', B='b', VDD='VDPWR', VAPWR='VAPWR', VSS='VSS')
    for side, y, src in (('p', 300, 'a'), ('n', 600, 'b')):
        e = s.place('tx_ls.sym', 0, y, name=f'xlse_{side}', kn=1, kp=1, wpi=1, wni=0.42)
        s.connect(e, **{'in': f'en_{side}'}, A=f'enh_{side}', B=f'enhb_{side}', VDD='VDPWR', VAPWR='VAPWR',
                  VSS='VSS')
        d = s.place('tx_drv.sym', 400, y - 150, name=f'xdrv_{side}')
        s.connect(d, **{'in': src}, en=f'enh_{side}', out=f'out_{side}', VAPWR='VAPWR', VSS='VSS')
    s.write(os.path.join(XDIR, 'tx_top.sch'))
    write_symbol(os.path.join(XDIR, 'tx_top.sym'), left=['key', 'en_p', 'en_n'], right=['out_p', 'out_n'],
                 top=['VDPWR', 'VAPWR'], bottom=['VSS'])


CASE = """
alterparam ven_n = {vn}
reset
tran 2p 80n 0
meas tran pa avg i(VA) from=25n to=60n
meas tran pd avg i(VD) from=25n to=60n
let ia = -pa * 1e3
let id = -pd * 1e3
echo RESULT {case} IA_mA $&ia ID_mA $&id
write tb_tx_{case}.raw
destroy all
"""
# both arms keyed (normal: 'ab'), then the single-ended fallback ('se', en_n held low).
# Unrolled: a loop variable in the file name needs {$v}, and braces break xschem properties.
TB_CODE = """
.param ven_n=1.8
.save v(xtx.ring) v(xtx.a) v(xtx.b) v(out_p) v(out_n) v(ant_p) v(ant_n) i(VA) i(VD) v(key)
.options method=GEAR
.control""" + CASE.format(vn=1.8, case='ab') + CASE.format(vn=0, case='se') + """.endc
"""


def tb_tx():
    s = Sch()
    s.place('sky130_fd_pr/corner.sym', -1000, -620, name='CORNER', only_toplevel='true', corner='tt')
    s.code(-800, -620, 'STDCELLS', '.include $::SKYWATER_STDCELLS/sky130_fd_sc_hd.spice',
           only_toplevel='true', tcleval=True)
    s.text(-1000, -760, 'tb_tx: tx_top -> pad_model per arm -> dipole (73 ohm + 100 pF series)', 0.6)
    s.text(-1000, -710, 'key on 5..60 ns; en_p follows the key, en_n = key * ven_n/1.8; '
           'analyse: sim/tx/tb_tx.py', 0.3)
    va = s.place('devices/vsource.sym', -900, -450, name='VA', value='3.3')
    s.connect(va, p='VAPWR', m='GND')
    vd = s.place('devices/vsource.sym', -700, -450, name='VD', value='1.8')
    s.connect(vd, p='VDPWR', m='GND')
    key = 'pwl(0 0 5n 0 5.05n 1.8 60n 1.8 60.05n 0)'
    vk = s.place('devices/vsource.sym', -900, -100, name='Vkey', value=f'"{key}"')
    s.connect(vk, p='key', m='GND')
    vk = s.place('devices/vsource.sym', -700, -100, name='Ven_p', value=f'"{key}"')
    s.connect(vk, p='en_p', m='GND')
    vk = s.place('devices/vsource.sym', -500, -100, name='Ven_n',
                 value='"pwl(0 0 5n 0 5.05n \'ven_n\' 60n \'ven_n\' 60.05n 0)"')
    s.connect(vk, p='en_n', m='GND')
    x = s.place('tx_top.sym', -100, -100, name='xtx')
    s.connect(x, key='key', en_p='en_p', en_n='en_n', out_p='out_p', out_n='out_n', VDPWR='VDPWR',
              VAPWR='VAPWR', VSS='GND')
    for side, y in (('p', -150), ('n', 50)):
        pad = s.place('pad_model.sym', 300, y, rot=0, flip=1, name=f'xpad_{side}')
        s.connect(pad, pin=f'ant_{side}', mod=f'out_{side}', VGND='GND')
    r = s.place('devices/res.sym', 650, -150, name='Rdip', value='73', m='1')
    s.connect(r, P='ant_p', M='dmid')
    c = s.place('devices/capa.sym', 650, 50, name='Cdip', value='100p', m='1')
    s.connect(c, p='dmid', m='ant_n')
    s.code(-1000, 100, 'SIMULATION', TB_CODE)
    s.write(os.path.join(XDIR, 'tb_tx.sch'))


if __name__ == '__main__':
    tx_ring()
    tx_ls()
    tx_drv()
    tx_top()
    tb_tx()
    print('wrote tx_ring, tx_ls, tx_drv, tx_top (.sch/.sym), tb_tx.sch')
