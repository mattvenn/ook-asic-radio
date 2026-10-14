"""
Generate the RX bias generator and its testbench.

  bias_gen : I = V/R reference, everything referred to the high_po poly that
             also loads the chain:
             - divider VDD - vcm - vref - (en switch) - VSS, three equal xhigh
               poly sections (rdiv each): vref = VDD/3, vcm = 2 VDD/3 (1.2 V,
               the chain's input bias; MIM decoupled). Ratio only: no process
               or temperature dependence.
             - OTA (PMOS input, since vref is only 0.6 V; NMOS mirror load;
               tail from a resistor-biased PMOS diode, so it is biased
               whenever en = 1 and the loop has no zero-current state) forces
               x = vref across rref (high_po 0p69, 10 k) through Mn.
             - Mn's drain current I = vref / rref = 60 uA goes into the PMOS
               diode Mpr (60 units); output mirrors (units W wpu L 1):
               ib_chain 60 units (60 uA), ib_det 2 (2 uA), ib_comp 1 (1 uA).
             Since rref is the same poly as the chain loads, the stage drop
             I x RL (and so the DC-coupled chain's operating points and gain)
             is a resistor ratio, independent of the resistor corner.
             en = 0: OTA tail off, Mn gate pulled low, Mpr gate pulled to VDD,
             divider off: no current.
  tb_bias  : op: currents and vcm at tt / ss / ff / hh / ll, 10 / 27 / 50 C,
             VDD 1.7 / 1.8 / 1.9 V; tran: start-up from a VDD ramp and en
             toggling. Loads are diode-connected NMOS like the real ones.

    python xschem/gen/bias.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from xsch import Sch, inv, mim, mos, poly_r, ports, write_symbol, value_notes

XDIR = os.path.normpath(os.path.join(HERE, '..'))
BIAS_PARAMS = {'rref': '10k', 'rdiv': '200k', 'rtail': '250k', 'wpu': 2, 'cc': '1p'}
OUTS = (('ib_chain', 60), ('ib_det', 2), ('ib_comp', 1))
NREF = 60
NDUM = 5           # mirror-array dummies (layout/gen/bias_gen.py)


def bias_gen():
    s = Sch()
    s.pin_order = ['VDD', 'VSS', 'en', 'vcm', 'ib_chain', 'ib_det', 'ib_comp']
    s.text(-1300, -800, 'bias_gen: I = (VDD/3) / rref (high_po, same poly as the chain loads)\n'
           'OTA forces x = vref; PMOS diode Mpr -> mirrors ib_chain 60 uA, ib_det 2 uA, ib_comp 1 uA; '
           'vcm = 2 VDD/3. en = 0: all off', 0.4)
    XL, YV, YS = -1300, -600, 300
    vdd, vss = [], []
    # enable inverter
    p, n, g, d = inv(s, -1100, -150, dict(W=1, L=0.15, name='Meip', body='VDD'),
                     dict(W=0.5, L=0.15, name='Mein', body='VSS'))
    s.route(g, (XL, -150))
    s.port((XL, -150), 'en')
    s.route(d, (-1040, -150))
    s.label((-1040, -150), 'enb', right=True)
    vdd.append(p.pin('S')); vss.append(n.pin('S'))
    # divider: VDD - vcm - vref - dsw - (switch) - VSS
    rd = []
    for nm, y in (('Rd1', -500), ('Rd2', -350), ('Rd3', -200)):
        rd.append(poly_r(s, -850, y, 'rdiv', 'xhigh', '0p35', name=nm))
        s.connect(rd[-1], B='VSS')
    m = mos(s, 'n', -870, -50, W=1, L=0.15, name='Mdsw', body='VSS')
    s.label(m.pin('G'), 'en')
    vdd.append(rd[0].pin('P')); vss.append(m.pin('S'))
    cv = []
    for nm, y in (('Cvcm', -400), ('Cvref', -250)):
        cv.append(mim(s, -700, y, 2e-12, mf=2, name=nm))     # 2 x 22 um units (<= 30 um), like Cc
    s.bus(rd[0].pin('M'), rd[1].pin('P'), [(-850, -430)])
    s.bus((-850, -430), (-600, -430), [cv[0].pin('c0')])
    s.port((-600, -430), 'vcm', right=True)
    s.label(cv[0].pin('c1'), 'VSS', right=True)
    s.bus(rd[1].pin('M'), rd[2].pin('P'), [(-850, -280)])
    s.bus((-850, -280), (-480, -280), [cv[1].pin('c0')])
    s.label((-850, -280), 'vref')
    vss.append(cv[1].pin('c1'))
    s.bus(rd[2].pin('M'), m.pin('D'), [(-850, -120)])
    s.label((-850, -120), 'dsw')
    # OTA tail bias: PMOS diode Mpb fed through rtail (+ en switch) to VSS
    mpb = mos(s, 'p', 80, -500, W=4, L=1, name='Mpb', body='VDD')
    r = poly_r(s, 100, -350, 'rtail', 'xhigh', '0p35', name='Rtail')
    s.connect(r, B='VSS')
    m = mos(s, 'n', 80, -200, W=1, L=0.15, name='Mtsw', body='VSS')
    s.label(m.pin('G'), 'en')
    s.bus(mpb.pin('D'), r.pin('P'), [(100, -440)])
    s.label((100, -440), 'pb', right=True)
    s.bus(r.pin('M'), m.pin('D'), [(100, -270)])
    s.label((100, -270), 'tsw', right=True)
    vdd.append(mpb.pin('S')); vss.append(m.pin('S'))
    mpt = mos(s, 'p', -280, -500, W=4, L=1, name='Mpt', body='VDD', flip=1)
    s.bus(mpt.pin('G'), mpb.pin('G'), [(0, -500)])
    s.route((100, -440), (0, -440), (0, -500))
    vdd.append(mpt.pin('S'))
    # PMOS input pair: M1 gate vref (diode side), M2 gate x (output side)
    m1 = mos(s, 'p', -420, -350, W=4, L=1, name='M1', body='VDD')
    m2 = mos(s, 'p', -180, -350, W=4, L=1, name='M2', body='VDD', flip=1)
    s.route((-480, -280), m1.pin('G'), vfirst=True)
    s.label(m2.pin('G'), 'x', right=True)
    s.route(m1.pin('S'), (-400, -420))
    s.route(m2.pin('S'), (-200, -420))
    s.bus((-400, -420), (-200, -420), [(-300, -420)])
    s.route(mpt.pin('D'), (-300, -420))
    s.label((-300, -420), 'tail', right=True)
    m3 = mos(s, 'n', -380, -150, W=2, L=2, name='M3', body='VSS', flip=1)
    m4 = mos(s, 'n', -220, -150, W=2, L=2, name='M4', body='VSS')
    s.bus(m3.pin('G'), m4.pin('G'), [(-300, -150)])
    s.bus(m1.pin('D'), m3.pin('D'), [(-400, -250)])
    s.route((-400, -250), (-300, -250), (-300, -150))
    s.label((-400, -250), 'd1')
    s.bus(m2.pin('D'), m4.pin('D'), [(-200, -250)])
    vss += [m3.pin('S'), m4.pin('S')]
    c = mim(s, 200, -220, 'cc', name='Cc')
    s.label(c.pin('c1'), 'VSS', right=True)
    m = mos(s, 'n', 280, -150, W=1, L=0.15, name='Mpd', body='VSS')     # en = 0: pull Mn gate low
    # Mn + rref: I = vref / rref into the PMOS diode Mpr
    mn = mos(s, 'n', 480, -250, W=20, L=0.5, nf=2, name='Mn', body='VSS')
    s.bus((-200, -250), mn.pin('G'), [c.pin('c0'), (300, -250)])
    s.label((300, -250), 'ota', right=True)
    s.route((300, -250), m.pin('D'))
    s.label(m.pin('G'), 'enb')
    vss.append(m.pin('S'))
    # two halves in series, as laid out: each poly segment has its own contact heads (the
    # 526 ohm 'ends' of the fitted R(L)), so one 10 k device drawn as two segments is 5 % high
    rr = []
    for k in range(2):
        rr.append(poly_r(s, 500, -150 + 120 * k, 'rref/2', 'high', '0p69', name=f'Rref{k + 1}'))
        s.connect(rr[-1], B='VSS')
    s.bus(mn.pin('S'), rr[0].pin('P'), [(500, -200)])
    s.label((500, -200), 'x', right=True)
    s.bus(rr[0].pin('M'), rr[1].pin('P'), [(500, -90)])
    s.label((500, -90), 'xr', right=True)
    vss.append(rr[1].pin('M'))
    mpr = mos(s, 'p', 520, -500, W="'wpu'", L=1, mult=NREF, name='Mpr', body='VDD', flip=1)
    mpu = mos(s, 'p', 280, -450, W=1, L=0.15, name='Mpu', body='VDD')    # en = 0: mirror gate to VDD
    s.label(mpu.pin('G'), 'en')
    s.bus(mpr.pin('D'), mn.pin('D'), [(500, -400)])
    s.route(mpu.pin('D'), (300, -400), (500, -400))
    vdd += [mpr.pin('S'), mpu.pin('S')]
    s.route((500, -400), (600, -400), (600, -500))
    s.label((600, -400), 'pr', right=True)
    gates = [(600, -500)]
    for i, (out, k) in enumerate(OUTS):
        x = 700 + i * 200
        p = mos(s, 'p', x - 20, -500, W="'wpu'", L=1, mult=k, name=f'Mo_{out}', body='VDD')
        if i == 0:
            gates.append(p.pin('G'))
        else:
            s.label(p.pin('G'), 'pr')
        s.route(p.pin('D'), (x, -380))
        s.port((x, -380), out, right=True)
        vdd.append(p.pin('S'))
    s.bus(mpr.pin('G'), gates[-1], gates[:-1])
    # the layout's mirror array has dummy fingers at its row ends (all terminals on VDD)
    p = mos(s, 'p', 1280, -500, W="'wpu'", L=1, mult=NDUM, name='Mdum', body='VDD')
    s.connect(p, D='VDD', G='VDD')
    vdd.append(p.pin('S'))
    s.rail(YV, XL, 1300, vdd, 'VDD', port=True)
    s.rail(YS, XL, 500, vss, 'VSS', port=True)
    value_notes(s, BIAS_PARAMS, at={'Cc': (5, -50), 'Cvcm': (100, -14), 'Cvref': (100, -14), 'Mdum': (25, 55)})
    s.write(os.path.join(XDIR, 'bias_gen.sch'))
    write_symbol(os.path.join(XDIR, 'bias_gen.sym'), left=['en'], right=['vcm'] + [o for o, _ in OUTS],
                 top=['VDD'], bottom=['VSS'], params=BIAS_PARAMS)


TB_CODE = """
.param vdd=1.8 ven=1.8
.options method=GEAR
.control
foreach v 1.7 1.8 1.9
  foreach t 10 27 50
    alterparam vdd = $v
    reset
    option temp = $t
    op
    let ic = i(vmc) * 1e6
    let id = i(vmd) * 1e6
    let ip = i(vmp) * 1e6
    let itot = -i(vdd) * 1e6
    let vc = v(vcm)
    echo RESULT op vdd $v T $t ib_chain_uA $&ic ib_det_uA $&id ib_comp_uA $&ip vcm $&vc idd_uA $&itot
    destroy all
  end
end
alterparam vdd = 1.8
alterparam ven = 0
reset
op
let itot = -i(vdd) * 1e6
let ic = i(vmc) * 1e6
echo RESULT off idd_uA $&itot ib_chain_uA $&ic
destroy all
alterparam ven = 1.8
reset
* start-up: VDD ramps 0 -> 1.8 V in 10 us; then en low at 40 us, high at 60 us
alter @vdd[pwl] = [ 0 0 10u 1.8 ]
alter @ven[pwl] = [ 0 0 1u 0 1.01u 1.8 40u 1.8 40.01u 0 60u 0 60.01u 1.8 ]
tran 20n 100u
meas tran ic30 find i(vmc) at=30u
meas tran ic50 find i(vmc) at=50u
meas tran ic99 find i(vmc) at=99u
let a = ic30 * 1e6
let b = ic50 * 1e6
let c = ic99 * 1e6
echo RESULT tran ib_chain_uA at_30u $&a at_50u_en0 $&b at_99u $&c
let ic = i(vmc) * 1e6
meas tran tset when ic=54 rise=last
echo RESULT tran last rise through 54 uA at $&tset
write tb_bias.raw
.endc
"""


def tb_bias():
    s = Sch()
    s.place('sky130_fd_pr/corner.sym', -1000, -620, name='CORNER', only_toplevel='true', corner='tt')
    s.text(-1000, -760, 'tb_bias: bias_gen into diode loads like the chain / detector / comparator', 0.5)
    s.text(-1000, -710, 'RESULT lines: currents and vcm vs VDD and T; start-up and en toggling', 0.3)
    v = s.place('devices/vsource.sym', -900, -450, name='Vdd', value='"dc \'vdd\' pwl(0 \'vdd\' 1 \'vdd\')"')
    s.connect(v, p='VDD', m='GND')
    v = s.place('devices/vsource.sym', -700, -450, name='Ven', value='"dc \'ven\' pwl(0 \'ven\' 1 \'ven\')"')
    s.connect(v, p='en', m='GND')
    x = s.place('bias_gen.sym', -300, -150, name='x1')
    s.connect(x, en='en', vcm='vcm', ib_chain='ic', ib_det='id', ib_comp='ip', VDD='VDD', VSS='GND')
    # loads: the chain's Mref (W 6 L 0.5 nf 2), log_det's replica (W 1 L 0.15 + 10k), comp's Mb (W 2 L 2)
    for i, (src, node, W, L, nf) in enumerate((('ic', 'lc', 6, 0.5, 2), ('id', 'ld', 1, 0.15, 1),
                                               ('ip', 'lp', 2, 2, 1))):
        vm = s.place('devices/vsource.sym', 100 + i * 300, -250, name=f'Vm{"cdp"[i]}', value='0')
        s.connect(vm, p=src, m=node)
        m = mos(s, 'n', 100 + i * 300, 0, W=W, L=L, nf=nf, name=f'Ml{i}')
        s.connect(m, D=node, G=node, S='GND' if i != 1 else 'lds', B='GND')
    r = poly_r(s, 420, 150, 10e3, 'high', '0p35', name='Rlds')
    s.connect(r, P='lds', M='GND', B='GND')
    s.code(-1000, 100, 'SIMULATION', TB_CODE)
    s.write(os.path.join(XDIR, 'tb_bias.sch'))


if __name__ == '__main__':
    bias_gen()
    tb_bias()
    print('wrote bias_gen (.sch/.sym), tb_bias.sch')
