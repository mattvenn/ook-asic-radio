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
    s.pin_order = ['VDD', 'VSS', 'ibias', 'inp', 'inn', 'outp', 'outn']
    s.text(-300, -560, 'lna_dp: NMOS diff pair, resistor loads, mirrored tail (x10 of ibias)', 0.5)
    XL, XR = -300, 600
    tops = []
    for side, x, gate, drain, sgn, fl in (('p', 0, 'inp', 'outn', '+', 0), ('n', 400, 'inn', 'outp', '-', 1)):
        r = s.place('devices/res.sym', x, -320, name=f'Rl_{side}', value="'rl_dp'", m='1')
        m = mos(s, 'n', x + (20 if fl else -20), -150, W=f"'w_dp*(1{sgn}mm/2)'", L="'l_dp'", nf=4,
                name=f'M{side}', flip=fl, body='VSS')
        tap, edge = (x, -240), XR if fl else XL
        s.bus(r.pin('M'), m.pin('D'), [tap])
        s.route(tap, (edge, -240))
        s.port((edge, -240), drain, right=bool(fl))
        s.route(m.pin('G'), (edge, -150))
        s.port((edge, -150), gate, right=bool(fl))
        s.route(m.pin('S'), (x, -80))
        tops.append(r.pin('P'))
    s.rail(-420, XL, 400, tops, 'VDD', port=True)
    s.bus((0, -80), (400, -80), [(200, -80)])
    s.label((200, -80), 'tail', right=True)
    mt = mos(s, 'n', 180, 10, W="'wt_dp'", L=0.5, nf=2, mult=10, name='Mtail', body='VSS')
    s.route((200, -80), mt.pin('D'))
    # reference diode, mirrored so its gate faces Mtail's: the classic 1:10 mirror
    md = mos(s, 'n', -80, 10, W="'wt_dp'", L=0.5, nf=2, mult=1, name='Mdiode', flip=1, body='VSS')
    s.route(md.pin('D'), (-100, -50))
    s.bus((-100, -50), (-40, -50))
    s.route((-40, -50), (-40, 10))
    s.bus(md.pin('G'), mt.pin('G'), [(-40, 10)])
    s.route((-100, -50), (XL, -50))
    s.port((XL, -50), 'ibias')
    s.rail(100, XL, 400, [md.pin('S'), mt.pin('S')], 'VSS', port=True)
    s.write(os.path.join(XDIR, 'lna_dp.sch'))
    write_symbol(os.path.join(XDIR, 'lna_dp.sym'), left=['inp', 'inn', 'ibias'],
                 right=['outp', 'outn'], top=['VDD'], bottom=['VSS'])


def lna_dpp():
    s = Sch()
    s.pin_order = ['VDD', 'VSS', 'ibias', 'inp', 'inn', 'outp', 'outn']
    s.text(-300, -620, 'lna_dpp: PMOS diff pair, resistor loads to ground, mirrored tail (x10 of ibias)', 0.5)
    XL, XR = -300, 600
    # tail mirror on top: diode Mdiode (fed by ibias, sunk by the testbench) -> Mtail x10
    mt = mos(s, 'p', 180, -330, W="'wt_dpp'", L=0.5, nf=2, mult=10, name='Mtail', body='VDD')
    md = mos(s, 'p', -80, -330, W="'wt_dpp'", L=0.5, nf=2, mult=1, name='Mdiode', flip=1, body='VDD')
    s.rail(-420, XL, 400, [md.pin('S'), mt.pin('S')], 'VDD', port=True)
    s.route(md.pin('D'), (-100, -270))
    s.bus((-100, -270), (-40, -270))
    s.route((-40, -270), (-40, -330))
    s.bus(md.pin('G'), mt.pin('G'), [(-40, -330)])
    s.route((-100, -270), (XL, -270))
    s.port((XL, -270), 'ibias')
    s.route(mt.pin('D'), (200, -240))
    s.bus((0, -240), (400, -240), [(200, -240)])
    s.label((200, -240), 'tail', right=True)
    bots = []
    for side, x, gate, drain, sgn, fl in (('p', 0, 'inp', 'outn', '+', 0), ('n', 400, 'inn', 'outp', '-', 1)):
        # n-well tied to the tail (source)
        m = mos(s, 'p', x + (20 if fl else -20), -150, W=f"'w_dpp*(1{sgn}mm/2)'", L="'l_dpp'", nf=8,
                name=f'M{side}', flip=fl, body='tail')
        r = s.place('devices/res.sym', x, 30, name=f'Rl_{side}', value="'rl_dpp'", m='1')
        s.route(m.pin('S'), (x, -240))
        tap, edge = (x, -60), XR if fl else XL
        s.bus(m.pin('D'), r.pin('P'), [tap])
        s.route(tap, (edge, -60))
        s.port((edge, -60), drain, right=bool(fl))
        s.route(m.pin('G'), (edge, -150))
        s.port((edge, -150), gate, right=bool(fl))
        bots.append(r.pin('M'))
    s.rail(120, XL, 400, bots, 'VSS', port=True)
    s.write(os.path.join(XDIR, 'lna_dpp.sch'))
    write_symbol(os.path.join(XDIR, 'lna_dpp.sym'), left=['inp', 'inn', 'ibias'],
                 right=['outp', 'outn'], top=['VDD'], bottom=['VSS'])


def lna_pinv():
    s = Sch()
    s.pin_order = ['VDD', 'VSS', 'inp', 'inn', 'outp', 'outn']
    s.text(-300, -560, 'lna_pinv: pseudo-differential self-biased inverters (Rf out->in)', 0.5)
    XL = -300
    tops, bots = [], []
    for side, x, gate, drain, sgn in (('p', 0, 'inp', 'outn', '+'), ('n', 500, 'inn', 'outp', '-')):
        # inverter: PMOS over NMOS, gates and drains joined; Rf from out back to in, drawn over the top
        mp = mos(s, 'p', x - 20, -230, W=f"'wp_inv*(1{sgn}mm/2)'", L=0.15, nf=8, name=f'Mp_{side}', body='VDD')
        mn = mos(s, 'n', x - 20, -80, W=f"'wn_inv*(1{sgn}mm/2)'", L=0.15, nf=4, name=f'Mn_{side}', body='VSS')
        r = s.place('devices/res.sym', x - 90, -330, rot=1, name=f'Rf_{side}', value="'rf_inv'", m='1')
        s.bus(mp.pin('D'), mn.pin('D'), [(x, -150)])
        s.bus(mp.pin('G'), mn.pin('G'), [(x - 40, -150)])
        s.bus((x - 120, -150), (x - 40, -150))
        s.route(r.pin('M'), (x - 120, -330), (x - 120, -150))
        s.bus((x, -150), (x + 120, -150), [(x + 60, -150)])
        s.route((x + 60, -150), (x + 60, -330), r.pin('P'))
        if x == 0:
            s.bus((XL, -150), (x - 120, -150))
            s.port((XL, -150), gate)
        else:
            s.port((x - 120, -150), gate)
        s.port((x + 120, -150), drain, right=True)
        tops.append(mp.pin('S'))
        bots.append(mn.pin('S'))
    s.rail(-400, XL, 500, tops, 'VDD', port=True)
    s.rail(50, XL, 500, bots, 'VSS', port=True)
    s.write(os.path.join(XDIR, 'lna_pinv.sch'))
    write_symbol(os.path.join(XDIR, 'lna_pinv.sym'), left=['inp', 'inn'],
                 right=['outp', 'outn'], top=['VDD'], bottom=['VSS'])


lna_dp()
lna_dpp()
lna_pinv()
print('wrote lna_dp, lna_dpp, lna_pinv (.sch/.sym)')
