"""
Generate the two candidate LNA first stages (schematic + symbol each):

  lna_dp   : NMOS differential pair, resistor loads, tail mirrored from an
             external bias current (ibias pin sinks into a diode NMOS, x10).
  lna_dpp  : PMOS differential pair (n-well tied to tail), resistor loads to
             ground, tail mirrored x10 from ibias (ibias pin sources current
             out of a diode PMOS: the testbench sinks it to ground).
  lna_pinv : pseudo-differential: two self-biased inverters (Rf out->in).

Sizes come from global spice params set by the testbench, so they can be
swept without regenerating:
  lna_dp   : w_dp (pair W, total), l_dp (pair L), rl_dp (load R), wt_dp (tail/diode unit W)
  lna_dpp  : w_dpp, l_dpp, rl_dpp, wt_dpp (same roles as lna_dp)
  lna_pinv : wn_inv, wp_inv, rf_inv
  both     : mm = fractional mismatch, applied +mm/2 to the p side and -mm/2
             to the n side (pair W / inverter W), so common-mode -> diff
             conversion shows up in simulation.

    python xschem/gen/lna_blocks.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from xsch import Sch, mos, ports, write_symbol

XDIR = os.path.normpath(os.path.join(HERE, '..'))


def lna_dp():
    s = Sch()
    s.text(-400, -560, 'lna_dp: NMOS diff pair, resistor loads, mirrored tail (x10 of ibias)', 0.5)
    ports(s, -400, -480, ['VDD', 'VSS', 'ibias', 'inp', 'inn', 'outp', 'outn'])
    for side, x, gate, drain, sgn in (('p', 0, 'inp', 'outn', '+'), ('n', 300, 'inn', 'outp', '-')):
        r = s.place('devices/res.sym', x + 20, -300, name=f'Rl_{side}', value="'rl_dp'", m='1')
        s.connect(r, P='VDD', M=drain)
        m = mos(s, 'n', x, -150, W=f"'w_dp*(1{sgn}mm/2)'", L="'l_dp'", nf=4, name=f'M{side}')
        s.connect(m, D=drain, G=gate, S='tail', B='VSS')
    mt = mos(s, 'n', 150, 50, W="'wt_dp'", L=0.5, nf=2, mult=10, name='Mtail')
    s.connect(mt, D='tail', G='ibias', S='VSS', B='VSS')
    md = mos(s, 'n', -150, 50, W="'wt_dp'", L=0.5, nf=2, mult=1, name='Mdiode')
    s.connect(md, D='ibias', G='ibias', S='VSS', B='VSS')
    s.write(os.path.join(XDIR, 'lna_dp.sch'))
    write_symbol(os.path.join(XDIR, 'lna_dp.sym'), left=['inp', 'inn', 'ibias'],
                 right=['outp', 'outn'], top=['VDD'], bottom=['VSS'])


def lna_dpp():
    s = Sch()
    s.text(-400, -560, 'lna_dpp: PMOS diff pair, resistor loads to ground, mirrored tail (x10 of ibias)', 0.5)
    ports(s, -400, -480, ['VDD', 'VSS', 'ibias', 'inp', 'inn', 'outp', 'outn'])
    mt = mos(s, 'p', 150, -300, W="'wt_dpp'", L=0.5, nf=2, mult=10, name='Mtail')
    s.connect(mt, D='tail', G='ibias', S='VDD', B='VDD')
    md = mos(s, 'p', -150, -300, W="'wt_dpp'", L=0.5, nf=2, mult=1, name='Mdiode')
    s.connect(md, D='ibias', G='ibias', S='VDD', B='VDD')
    for side, x, gate, drain, sgn in (('p', 0, 'inp', 'outn', '+'), ('n', 300, 'inn', 'outp', '-')):
        m = mos(s, 'p', x, -150, W=f"'w_dpp*(1{sgn}mm/2)'", L="'l_dpp'", nf=8, name=f'M{side}')
        s.connect(m, D=drain, G=gate, S='tail', B='tail')
        r = s.place('devices/res.sym', x + 20, 0, name=f'Rl_{side}', value="'rl_dpp'", m='1')
        s.connect(r, P=drain, M='VSS')
    s.write(os.path.join(XDIR, 'lna_dpp.sch'))
    write_symbol(os.path.join(XDIR, 'lna_dpp.sym'), left=['inp', 'inn', 'ibias'],
                 right=['outp', 'outn'], top=['VDD'], bottom=['VSS'])


def lna_pinv():
    s = Sch()
    s.text(-400, -560, 'lna_pinv: pseudo-differential self-biased inverters (Rf out->in)', 0.5)
    ports(s, -400, -480, ['VDD', 'VSS', 'inp', 'inn', 'outp', 'outn'])
    for side, x, gate, drain, sgn in (('p', 0, 'inp', 'outn', '+'), ('n', 400, 'inn', 'outp', '-')):
        mp = mos(s, 'p', x, -200, W=f"'wp_inv*(1{sgn}mm/2)'", L=0.15, nf=8, name=f'Mp_{side}')
        s.connect(mp, D=drain, G=gate, S='VDD', B='VDD')
        mn = mos(s, 'n', x, -50, W=f"'wn_inv*(1{sgn}mm/2)'", L=0.15, nf=4, name=f'Mn_{side}')
        s.connect(mn, D=drain, G=gate, S='VSS', B='VSS')
        r = s.place('devices/res.sym', x - 120, -120, rot=1, name=f'Rf_{side}', value="'rf_inv'", m='1')
        s.connect(r, P=drain, M=gate)
    s.write(os.path.join(XDIR, 'lna_pinv.sch'))
    write_symbol(os.path.join(XDIR, 'lna_pinv.sym'), left=['inp', 'inn'],
                 right=['outp', 'outn'], top=['VDD'], bottom=['VSS'])


lna_dp()
lna_dpp()
lna_pinv()
print('wrote lna_dp, lna_dpp, lna_pinv (.sch/.sym)')
