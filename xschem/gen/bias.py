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
from xsch import Sch, mim, mos, poly_r, ports, write_symbol

XDIR = os.path.normpath(os.path.join(HERE, '..'))
BIAS_PARAMS = {'rref': '10k', 'rdiv': '200k', 'rtail': '250k', 'wpu': 2, 'cc': '1p'}
OUTS = (('ib_chain', 60), ('ib_det', 2), ('ib_comp', 1))
NREF = 60


def bias_gen():
    s = Sch()
    s.text(-800, -860, 'bias_gen: I = (VDD/3) / rref (high_po, same poly as the chain loads)\n'
           'OTA forces x = vref; PMOS diode Mpr -> mirrors ib_chain 60 uA, ib_det 2 uA, ib_comp 1 uA; '
           'vcm = 2 VDD/3. en = 0: all off', 0.4)
    ports(s, -800, -760, ['VDD', 'VSS', 'en', 'vcm', 'ib_chain', 'ib_det', 'ib_comp'])
    # enable inverter
    p = mos(s, 'p', -700, -350, W=1, L=0.15, name='Meip')
    s.connect(p, D='enb', G='en', S='VDD', B='VDD')
    n = mos(s, 'n', -700, -200, W=0.5, L=0.15, name='Mein')
    s.connect(n, D='enb', G='en', S='VSS', B='VSS')
    # divider: VDD - vcm - vref - dsw - (switch) - VSS
    for nm, y, a, b in (('Rd1', -500, 'VDD', 'vcm'), ('Rd2', -350, 'vcm', 'vref'), ('Rd3', -200, 'vref', 'dsw')):
        r = poly_r(s, -450, y, 'rdiv', 'xhigh', '0p35', name=nm)
        s.connect(r, P=a, M=b, B='VSS')
    m = mos(s, 'n', -470, -50, W=1, L=0.15, name='Mdsw')
    s.connect(m, D='dsw', G='en', S='VSS', B='VSS')
    for nm, nd, y in (('Cvcm', 'vcm', -450), ('Cvref', 'vref', -300)):
        c = mim(s, -300, y, '2p', mf=1, name=nm)
        s.connect(c, c0=nd, c1='VSS')
    # OTA tail bias: PMOS diode Mpb fed through rtail (+ en switch) to VSS
    p = mos(s, 'p', 0, -500, W=4, L=1, name='Mpb')
    s.connect(p, D='pb', G='pb', S='VDD', B='VDD')
    r = poly_r(s, 20, -350, 'rtail', 'xhigh', '0p35', name='Rtail')
    s.connect(r, P='pb', M='tsw', B='VSS')
    m = mos(s, 'n', 0, -200, W=1, L=0.15, name='Mtsw')
    s.connect(m, D='tsw', G='en', S='VSS', B='VSS')
    p = mos(s, 'p', 300, -500, W=4, L=1, name='Mpt')
    s.connect(p, D='tail', G='pb', S='VDD', B='VDD')
    # PMOS input pair: M1 gate vref (diode side), M2 gate x (output side)
    for nm, x, g, d in (('M1', 200, 'vref', 'd1'), ('M2', 400, 'x', 'ota')):
        m = mos(s, 'p', x, -350, W=4, L=1, name=nm)
        s.connect(m, D=d, G=g, S='tail', B='VDD')
    for nm, x, d in (('M3', 200, 'd1'), ('M4', 400, 'ota')):
        m = mos(s, 'n', x, -150, W=2, L=2, name=nm)
        s.connect(m, D=d, G='d1', S='VSS', B='VSS')
    c = mim(s, 550, -100, 'cc', name='Cc')
    s.connect(c, c0='ota', c1='VSS')
    m = mos(s, 'n', 650, -100, W=1, L=0.15, name='Mpd')                 # en = 0: pull Mn gate low
    s.connect(m, D='ota', G='enb', S='VSS', B='VSS')
    # Mn + rref: I = vref / rref into the PMOS diode Mpr
    m = mos(s, 'n', 900, -150, W=20, L=0.5, nf=2, name='Mn')
    s.connect(m, D='pr', G='ota', S='x', B='VSS')
    r = poly_r(s, 920, 0, 'rref', 'high', '0p69', name='Rref')
    s.connect(r, P='x', M='VSS', B='VSS')
    p = mos(s, 'p', 900, -450, W="'wpu'", L=1, mult=NREF, name='Mpr')
    s.connect(p, D='pr', G='pr', S='VDD', B='VDD')
    p = mos(s, 'p', 1100, -450, W=1, L=0.15, name='Mpu')                 # en = 0: mirror gate to VDD
    s.connect(p, D='pr', G='en', S='VDD', B='VDD')
    for i, (out, k) in enumerate(OUTS):
        p = mos(s, 'p', 1300 + i * 200, -450, W="'wpu'", L=1, mult=k, name=f'Mo_{out}')
        s.connect(p, D=out, G='pr', S='VDD', B='VDD')
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
