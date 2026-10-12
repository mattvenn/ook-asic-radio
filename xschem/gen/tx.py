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
from xsch import Sch, inv, mos, ports, stdcell, write_symbol

XDIR = os.path.normpath(os.path.join(HERE, '..'))
NINV = 22
LS_PARAMS = {'kn': 14, 'kp': 8, 'wpi': 9, 'wni': 3}
DRV_N = [0.42, 1.68, 6.72, 26.88, 48]        # inverter taper after the NAND (x4, final N 48)


def nf_of(w):
    return max(1, int(round(w / 10)))


def tx_ring():
    s = Sch()
    s.pin_order = ['VDD', 'VSS', 'en', 'out']
    s.text(-500, -360, f'tx_ring: nand2_2 enable + {NINV} x inv_2 ({NINV + 1} stages), cw wiring C per stage\n'
           'cw 3.2 fF reproduces the ttsky25b ring extracted (598 MHz tt); en = 0 stops it with out = 1\n'
           'std cell supplies are instance properties (VDD / VSS)', 0.4)
    s.port((-500, -150), 'VDD')
    half = NINV // 2
    nd = stdcell(s, 'nand2_2', -300, 0, name='xr0')
    s.route((-500, -20), nd.pin('A'))
    s.port((-500, -20), 'en')
    c = s.place('devices/capa.sym', -190, 30, name='Cr0', value="'cw'", m='1')
    s.bus(nd.pin('Y'), (-140, 0), [(-210, 0), c.pin('p')])
    s.route((-210, 0), (-210, -80), (-120, -80))
    s.port((-120, -80), 'out', right=True)
    rails = {100: [c.pin('m')], 400: []}
    for i in range(1, NINV + 1):
        top = i <= half
        # row 1 runs left to right; row 2 (mirrored) runs back right to left
        x = -100 + (i - 1) * 200 if top else -100 + (NINV - i) * 200
        y = 0 if top else 300
        iv = stdcell(s, 'inv_2', x, y, name=f'xr{i}', flip=0 if top else 1)
        cx = x + 100 if top else x - 100
        c = s.place('devices/capa.sym', cx, y + 30, name=f'Cr{i}', value="'cw'", m='1')
        rails[100 if top else 400].append(c.pin('m'))
        y_pin = iv.pin('Y')
        if i == half:                                   # turn the corner down to row 2
            s.bus(y_pin, (x + 160, y), [(cx, y)])
            s.route((x + 160, y), (x + 160, 300), (x + 40, 300))
        elif i == NINV:                                 # back to the NAND's B input
            s.bus(y_pin, (-420, 300), [(cx, y)])
            s.route((-420, 300), (-420, 20), nd.pin('B'))
        else:
            s.bus(y_pin, (x + 160 if top else x - 160, y), [(cx, y)])
        s.label((cx, y), f'r{i}', right=not top)
    s.rail(100, -300, -100 + (half - 1) * 200 + 100, rails[100], 'VSS')
    s.rail(400, -500, -100 + (NINV - half - 1) * 200 - 100 + 200, rails[400], 'VSS', port=True)
    s.write(os.path.join(XDIR, 'tx_ring.sch'))
    write_symbol(os.path.join(XDIR, 'tx_ring.sym'), left=['en'], right=['out'], top=['VDD'],
                 bottom=['VSS'], params={'cw': '3.2f'})


def tx_ls():
    s = Sch()
    s.pin_order = ['VDD', 'VAPWR', 'VSS', 'in', 'A', 'B']
    s.text(-500, -460, 'tx_ls: 1.8 -> 3.3 V level shifter (R2R DAC dac_drive, skewed core)\n'
           'in -> thin inverter (wpi/wni) -> ctrl; core NMOS kn x 0.42, PMOS kp x 0.42, L 0.5 thick. '
           'A = in, B = not in', 0.4)
    XL = -500
    # input inverter (the ring's calibrated load when wpi/wni = 9/3)
    p1, n1, g1, d1 = inv(s, -300, 0, dict(W="'wpi'", L=0.15, name='Mi1p', body='VDD'),
                         dict(W="'wni'", L=0.15, name='Mi1n', body='VSS'))
    s.route((XL, 0), g1)
    s.port((XL, 0), 'in')
    # ctrl_n inverter: was dac_drive's hvt PMOS 1 / NMOS 0.42, too weak for M10's thick
    # gate + the ctrl_n wiring (extracted A duty 37 -> 28 %); now about as strong as the
    # input inverter, so both paths into the core are balanced (2026-10-08)
    p2, n2, g2, d2 = inv(s, 0, 0, dict(W=4, L=0.15, name='M8', vt='hvt', body='VDD'),
                         dict(W=1.68, L=0.15, name='M7', body='VSS'))
    s.bus(d1, g2, [(-200, 0)])
    s.label((-200, 0), 'ctrl')
    s.route(d2, (80, 0))
    s.label((80, 0), 'ctrl_n', right=True)
    # thick core: pull-downs kn x (gates labelled ctrl / ctrl_n), cross-coupled PMOS kp x
    m9 = mos(s, 'n', 380, 50, W="'0.42*kn'", L=0.5, name='M9', vt='g5', body='VSS')
    m10 = mos(s, 'n', 620, 50, W="'0.42*kn'", L=0.5, name='M10', vt='g5', body='VSS', flip=1)
    s.label(m9.pin('G'), 'ctrl')
    s.label(m10.pin('G'), 'ctrl_n', right=True)
    m11 = mos(s, 'p', 420, -150, W="'0.42*kp'", L=0.5, name='M11', vt='g5', body='VAPWR', flip=1)
    m12 = mos(s, 'p', 580, -150, W="'0.42*kp'", L=0.5, name='M12', vt='g5', body='VAPWR')
    s.bus(m11.pin('D'), m9.pin('D'), [(400, -60), (400, -20)])
    s.bus(m12.pin('D'), m10.pin('D'), [(600, -90), (600, -20)])
    s.route(m12.pin('G'), (530, -150), (530, -60), (400, -60))      # the cross: B's PMOS gate on A
    s.route(m11.pin('G'), (470, -150), (470, -90), (600, -90))      # and A's PMOS gate on B
    s.route((400, -20), (330, -20))
    s.port((330, -20), 'A')
    s.route((600, -20), (700, -20))
    s.port((700, -20), 'B', right=True)
    s.rail(-200, XL, 0, [p1.pin('S'), p2.pin('S')], 'VDD', port=True)
    s.rail(-260, XL, 600, [m11.pin('S'), m12.pin('S')], 'VAPWR', port=True)
    s.rail(180, XL, 600, [n1.pin('S'), n2.pin('S'), m9.pin('S'), m10.pin('S')], 'VSS', port=True)
    s.write(os.path.join(XDIR, 'tx_ls.sch'))
    write_symbol(os.path.join(XDIR, 'tx_ls.sym'), left=['in'], right=['A', 'B'], top=['VDD', 'VAPWR'],
                 bottom=['VSS'], params=LS_PARAMS)


def tx_drv():
    s = Sch()
    s.pin_order = ['VAPWR', 'VSS', 'in', 'en', 'out']
    s.text(-600, -460, 'tx_drv: one antenna arm on VAPWR, out = in & en\n'
           'thick NAND2 then inverters x4 per stage: N ' + ' / '.join(f'{w:g}' for w in DRV_N) +
           ' um, P = 3 N, L 0.5', 0.4)
    XL = -600
    # NAND2: PMOS in parallel on top, NMOS in series below; 'in' on the NMOS next to the
    # output (the fast input), en below it.
    # Series NMOS 2 x 0.42, PMOS 1.26: same pull-up as the inverter it replaces.
    ps = []
    for nm, x, g in (('Mna', -400, 'in'), ('Mnb', -200, 'en')):
        ps.append(mos(s, 'p', x - 20, -150, W=1.26, L=0.5, name=nm + 'p', vt='g5', body='VAPWR'))
    ma = mos(s, 'n', -320, 0, W=0.84, L=0.5, name='Mnan', vt='g5', body='VSS')
    mb = mos(s, 'n', -320, 100, W=0.84, L=0.5, name='Mnbn', vt='g5', body='VSS')
    s.route(ps[0].pin('D'), (-400, -50))
    s.route(ps[1].pin('D'), (-200, -50))
    s.bus((-400, -50), (-200, -50), [(-300, -50)])
    s.route((-300, -50), ma.pin('D'))
    s.bus(ma.pin('S'), mb.pin('D'), [(-300, 50)])
    s.label((-300, 50), 'ns', right=True)
    s.route((XL, 0), ma.pin('G'))
    s.port((XL, 0), 'in')
    s.route(ps[0].pin('G'), (-460, -150), (-460, 0))
    s.route((XL, 100), mb.pin('G'))
    s.port((XL, 100), 'en')
    s.label(ps[1].pin('G'), 'en')
    s.label((-200, -50), 'y0', right=True)
    vap, vss = [p.pin('S') for p in ps], [mb.pin('S')]
    prev = (-200, -50)
    for i, wn in enumerate(DRV_N, 1):
        y = 'out' if i == len(DRV_N) else f'y{i}'
        x = -100 + i * 250
        p, n, g, d = inv(s, x, -50, dict(W=round(3 * wn, 3), L=0.5, nf=nf_of(3 * wn), name=f'M{i}p', vt='g5',
                                         body='VAPWR'),
                         dict(W=round(wn, 3), L=0.5, nf=nf_of(wn), name=f'M{i}n', vt='g5', body='VSS'), h=100)
        s.bus(prev, g)
        if i < len(DRV_N):
            s.label(d, y, right=True)
        prev = d
        vap.append(p.pin('S'))
        vss.append(n.pin('S'))
    s.route(prev, (prev[0] + 100, -50))
    s.port((prev[0] + 100, -50), 'out', right=True)
    s.rail(-260, XL, prev[0], vap, 'VAPWR', port=True)
    s.rail(200, XL, prev[0], vss, 'VSS', port=True)
    s.write(os.path.join(XDIR, 'tx_drv.sch'))
    write_symbol(os.path.join(XDIR, 'tx_drv.sym'), left=['in', 'en'], right=['out'], top=['VAPWR'],
                 bottom=['VSS'])


def tx_top():
    s = Sch()
    s.pin_order = ['VDPWR', 'VAPWR', 'VSS', 'key', 'en_p', 'en_n', 'out_p', 'out_n']
    s.text(-500, -460, 'tx_top: ring -> level shifter -> antiphase arms (A -> out_p, B -> out_n)\n'
           'en_p / en_n (1.8 V) gate each arm: both = key normally (off: both arms low); '
           'en_n = 0: single-ended fallback\nsupplies and the arm enables enh_p / enh_n are labelled', 0.4)
    ports(s, -500, -300, ['VDPWR', 'VAPWR', 'VSS'])
    sup = dict(VDD='VDPWR', VSS='VSS')

    def vapwr(inst):                     # right of its pin: VDD's label sits just left of it
        s.label(inst.pin('VAPWR'), 'VAPWR', right=True)
    r = s.place('tx_ring.sym', -400, 0, name='xring')
    s.connect(r, VDD='VDPWR', VSS='VSS')
    s.route((-600, 0), r.pin('en'))
    s.port((-600, 0), 'key')
    ls = s.place('tx_ls.sym', 0, 0, name='xls')
    s.connect(ls, **sup)
    vapwr(ls)
    s.route(r.pin('out'), (-200, 0), (-200, -20), ls.pin('in'))
    s.label((-200, 0), 'ring')
    s.route(ls.pin('A'), (250, -20), (250, -120), (400, -120))
    s.label(ls.pin('A'), 'a', right=True)
    s.route(ls.pin('B'), (300, 20), (300, 180), (400, 180))
    s.label(ls.pin('B'), 'b', right=True)
    for side, y in (('p', 300), ('n', 600)):
        e = s.place('tx_ls.sym', 0, y, name=f'xlse_{side}', kn=1, kp=1, wpi=1, wni=0.42)
        s.connect(e, **sup, A=f'enh_{side}', B=f'enhb_{side}')
        vapwr(e)
        s.route((-600, y - 20), e.pin('in'))
        s.port((-600, y - 20), f'en_{side}')
        d = s.place('tx_drv.sym', 500, -100 if side == 'p' else 200, name=f'xdrv_{side}')
        s.connect(d, en=f'enh_{side}', VAPWR='VAPWR', VSS='VSS')
        q = d.pin('out')
        s.route(q, (q[0] + 100, q[1]))
        s.port((q[0] + 100, q[1]), f'out_{side}', right=True)
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
