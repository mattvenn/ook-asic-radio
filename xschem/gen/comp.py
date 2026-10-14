"""
Generate the RX comparator, the switched-cap averaging reference, and their
testbenches.

  comp_ct : continuous-time comparator (the digital's 2-flop synchroniser
            samples it, so no strobe, no kickback onto the ~1 mV LPF node).
            out = 1 when inp > inn + trim offset.
            - stage 1: low-Vt NMOS pair (W 20, L 1, weak inversion), tail
              10 x ibias, low-Vt PMOS mirror load (W 8 L 2: 4x the area of the
              W 4 L 1 before 2026-10-13, for offset; docs/verify_supply_mc.md 2.2). Low Vt stretches the input
              CM range (det runs ~0.6 V at -20 dBm to ~1.52 V idle).
            - trim: low-Vt NMOS pair (W 8) with split tails and rdeg (0.85 M) between
              its sources, on the same loads: offset ~ (trim - vref) * (1/rdeg) / gm1;
              trim from the R2R DAC, vref = 0.75 VDD (1.35 V) from an on-chip xhigh-poly
              divider (lref1 / lref2 = 68 / 204: a tap 8 of 32 segments down the layout's
              string). Raising 'trim' acts like raising inn. Candidate H135 of
              docs/verify_supply_mc.md 2.2 (2026-10-13): the nominal chip balances near
              code 179, mid-way along the linear part of the trim (step ~0.127 mV/LSB),
              so offsets of either sign trim finely. Before: W 2, rdeg 2 M, vref VDD/2,
              balance at code 112 on the knee (steep step below it).
            - Cl (wcl x wcl um MIM, ~1 pF) on the stage-1 output sets a
              ~100 kHz dominant pole: limits the noise bandwidth.
            - stage 2: PMOS common source (matched to the load, so the
              balanced point sits mid-rail), NMOS current sink, inverter out.
  avg_sc  : out = slow average of in. Cs (phi1: in, phi2: out) into cavg;
            tau = cavg / (Cs * f_sample) ~ 3.7 p / (0.1 p * 77 kHz) ~ 0.48 ms
            (was 9.1 p / 0.25 p; shrunk 2026-10-08 for area).
            Transmission-gate switches with local phi inverters.
  tb_comp : DC threshold vs input CM, trim transfer, input-referred noise,
            1 mV overdrive transient.
  tb_avg  : averager step response with the digital's sc_phi timing.

    python xschem/gen/comp.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from xsch import Sch, mos, ports, write_symbol

XDIR = os.path.normpath(os.path.join(HERE, '..'))
COMP_PARAMS = {'w1': 20, 'l1': 1, 'mt1': 10, 'rdeg': '0.85Meg', 'mta': 2, 'lref1': 68, 'lref2': 204, 'wcl': 22}


def comp_ct():
    s = Sch()
    s.pin_order = ['VDD', 'VSS', 'ibias', 'inp', 'inn', 'trim', 'out']
    s.text(-1000, -560, 'comp_ct: continuous comparator, out = 1 when inp > inn + trim offset\n'
           'lvt NMOS pair + lvt PMOS mirror; degenerated trim pair (trim vs vref); PMOS CS; inverter', 0.4)
    XL, XR, YV, YS = -1000, 1150, -400, 200
    # bias: ibias into a diode (unit W 2, L 2); tails are multiples of it (gates labelled ibias)
    md = mos(s, 'n', -880, 100, W=2, L=2, name='Mb', body='VSS')
    s.route(md.pin('D'), (-860, 40))
    s.bus((XL, 40), (-860, 40), [(-900, 40)])
    s.route((-900, 40), (-900, 100))
    s.port((XL, 40), 'ibias')
    # Mt1 / Mn3 are 4.55 um fingers (the layout's row height) instead of 2 um units: that W
    # bin gives ~12 % more current per um than Mb's, so the total W is 0.91 x the units'
    # (10 / 5 units within +1.4 / -1 % over tt/ss/ff/sf/fs). Written as W per finger x mult,
    # as magic extracts them: with .spiceinit's skywaterpdk mode, W/nf bins differently.
    mt = mos(s, 'n', 80, 100, W="'0.455*mt1'", L=2, mult=4, name='Mt1', body='VSS')
    s.label(mt.pin('G'), 'ibias')
    # main pair: inp -> d1 (diode side), inn -> d2 (output side)
    m1 = mos(s, 'n', -20, -100, W="'w1'", L="'l1'", nf=4, name='M1', vt='lvt', body='VSS')
    m2 = mos(s, 'n', 220, -100, W="'w1'", L="'l1'", nf=4, name='M2', vt='lvt', body='VSS', flip=1)
    s.route(m1.pin('G'), (-100, -100))
    s.port((-100, -100), 'inp')
    s.route(m2.pin('G'), (300, -100))
    s.port((300, -100), 'inn', right=True)
    s.route(m1.pin('S'), (0, -20))
    s.route(m2.pin('S'), (200, -20))
    s.bus((0, -20), (200, -20), [(100, -20)])
    s.route((100, -20), mt.pin('D'))
    s.label((100, -20), 'tail', right=True)
    s.text(95, 145, f"W = 0.455 x mt1 = {0.455 * COMP_PARAMS['mt1']:.2f} um\n(mt1 = {COMP_PARAMS['mt1']})", 0.25)
    s.text(15, -195, f"M1/M2: W = w1 = {COMP_PARAMS['w1']} um\nL = l1 = {COMP_PARAMS['l1']} um, nf = 4", 0.25)
    # PMOS mirror load (lvt, L 1): diode on d1
    mp1 = mos(s, 'p', 20, -300, W=8, L=2, name='Mp1', vt='lvt', body='VDD', flip=1)
    mp2 = mos(s, 'p', 180, -300, W=8, L=2, name='Mp2', vt='lvt', body='VDD')
    s.bus(mp1.pin('G'), mp2.pin('G'), [(100, -300)])
    s.route((0, -240), (100, -240), (100, -300))
    s.bus(mp1.pin('D'), m1.pin('D'), [(0, -240), (0, -200)])
    s.bus(mp2.pin('D'), m2.pin('D'), [(200, -240), (200, -200)])
    s.label((0, -200), 'd1')
    s.label((200, -200), 'd2', right=True)
    # trim pair, outside the main pair so its drains join d1 / d2 without crossing:
    # vref -> d1, trim -> d2 (acts like inn), split tails + rdeg between the sources
    ta = []
    for nm, x, g, sn, fl in (('M3', -250, 'vref', 'sa', 0), ('M4', 450, 'trim', 'sb', 1)):
        m = mos(s, 'n', x + (20 if fl else -20), -100, W=8, L=1, name=nm, vt='lvt', body='VSS', flip=fl)
        s.route(m.pin('D'), (x, -200), (0 if x < 0 else 200, -200), vfirst=True)
        t = mos(s, 'n', x + (20 if fl else -20), 100, W=2, L=2, mult="'mta'", name=f'Mta_{sn}', body='VSS',
                flip=fl)
        s.label(t.pin('G'), 'ibias', right=bool(fl))
        s.text(330 if fl else -230, 145, f"mult = mta = {COMP_PARAMS['mta']}", 0.25)
        s.bus(m.pin('S'), t.pin('D'), [(x, 30)])
        s.label((x, 30), sn, right=bool(fl))
        ta.append((m, t))
    s.route(ta[1][0].pin('G'), (550, -100))
    s.port((550, -100), 'trim', right=True)
    r = s.place('sky130_fd_pr/res_xhigh_po_0p35.sym', -100, 30, rot=1, name='Rdeg',
                L="'rdeg/7.37k'", model='res_xhigh_po_0p35', mult='1', spiceprefix='X')
    s.connect(r, B='VSS')
    s.route((-250, 30), r.pin('M'))
    s.route(r.pin('P'), (450, 30))
    rd = float(COMP_PARAMS['rdeg'].replace('Meg', 'e6'))
    s.text(-235, -22, f"Rdeg = {COMP_PARAMS['rdeg']}\nL = {rd / 7.37e3:.1f} um", 0.3)
    # vref for the trim pair (xhigh poly divider + MIM decoupling)
    rr = []
    for nm, y, lr in (('Rr1', -250, "'lref1'"), ('Rr2', -40, "'lref2'")):
        rr.append(s.place('sky130_fd_pr/res_xhigh_po_0p35.sym', -700, y, name=nm, L=lr,
                          model='res_xhigh_po_0p35', mult='1', spiceprefix='X'))
        s.connect(rr[-1], B='VSS')
    l1, l2 = COMP_PARAMS['lref1'], COMP_PARAMS['lref2']
    s.text(-1000, -350, f'vref divider (defaults):\nRr1 L = lref1 = {l1} um\nRr2 L = lref2 = {l2} um\n'
           f'vref = VDD x {l2}/{l1 + l2} = {1.8 * l2 / (l1 + l2):.2f} V', 0.3)
    cr = s.place('sky130_fd_pr/cap_mim_m3_1.sym', -800, -40, name='Cref', model='cap_mim_m3_1',
                 W='10', L='10', MF='1', spiceprefix='X')
    s.bus(rr[0].pin('M'), rr[1].pin('P'), [(-700, -100)])
    s.route(cr.pin('c0'), (-800, -100))
    s.bus((-800, -100), ta[0][0].pin('G'), [(-700, -100)])
    s.label((-700, -100), 'vref')
    # band-limit stage 1 (dominant pole ~100 kHz): cuts the integrated noise;
    # a decision only has to settle within one 13 us sample
    cl = s.place('sky130_fd_pr/cap_mim_m3_1.sym', 600, -210, name='Cl', model='cap_mim_m3_1',
                 W="'wcl'", L="'wcl/2'", MF='2', spiceprefix='X')   # 2 x (wcl x wcl/2): fits the layout's band
    s.connect(cl, c1='VSS')
    w = COMP_PARAMS['wcl']
    s.text(572, -167, f"Cl = 2 x {w} x {w / 2:g} um\n(wcl = {w}): {2 * (w * w / 2 * 2e-15 + 1.5 * w * 0.38e-15) * 1e12:.2f} pF",
           0.25)
    # stage 2: PMOS CS (same W/L as the load) + NMOS sink (5 x unit); out2 low when inp > inn
    mp = mos(s, 'p', 830, -300, W=4, L=1, name='Mp3', vt='lvt', body='VDD')
    s.bus((200, -240), (810, -240), [cl.pin('c0')])
    s.route((810, -240), mp.pin('G'))
    mn = mos(s, 'n', 830, 100, W=4.55, L=2, mult=2, name='Mn3', body='VSS')
    s.label(mn.pin('G'), 'ibias')
    s.bus(mp.pin('D'), mn.pin('D'), [(850, -100)])
    s.label((850, -100), 'o2')
    # output inverter
    ip = mos(s, 'p', 1030, -300, W=2, L=0.15, name='Mip', body='VDD')
    i_n = mos(s, 'n', 1030, 100, W=1, L=0.15, name='Min', body='VSS')
    s.bus(ip.pin('G'), i_n.pin('G'), [(1010, -100)])
    s.bus((850, -100), (1010, -100))
    s.bus(ip.pin('D'), i_n.pin('D'), [(1050, -100)])
    s.route((1050, -100), (XR, -100))
    s.port((XR, -100), 'out', right=True)
    s.rail(YV, XL, 1050, [rr[0].pin('P'), mp1.pin('S'), mp2.pin('S'), mp.pin('S'), ip.pin('S')], 'VDD', port=True)
    s.rail(YS, XL, 1050, [md.pin('S'), cr.pin('c1'), rr[1].pin('M'), ta[0][1].pin('S'), mt.pin('S'),
                         ta[1][1].pin('S'), mn.pin('S'), i_n.pin('S')], 'VSS', port=True)
    # layout matching dummies (layout/gen/comp_ct.py: rail-tied dummies either side of the
    # ABBA pairs and the bias units): all terminals on the rail, no electrical effect; drawn
    # here so LVS sees the same devices (IIC etiquette: dummies belong in the schematic)
    s.text(-200, 300, 'layout matching dummies (all terminals on the rail)', 0.4)
    taps = {'n': [], 'p': []}
    for nm, x, kind, W, L, vt, m in (('Mdn1', -100, 'n', 5, 1, 'lvt', 2), ('Mdn2', 100, 'n', 4, 1, 'lvt', 2),
                                     ('Mdn3', 300, 'n', 2, 2, '', 1), ('Mdp1', 500, 'p', 4, 1, 'lvt', 2),
                                     ('Mdp2', 700, 'p', 4, 1, 'lvt', 1)):
        rail = 'VSS' if kind == 'n' else 'VDD'
        d = mos(s, kind, x, 450, W=W, L=L, mult=m, name=nm, vt=vt, body=rail)
        ry = 530 if kind == 'n' else 370
        far = d.pin('D')                     # D is on the far side from the rail for both kinds
        s.route(far, (x + 60, far[1]), (x + 60, ry))
        s.route(d.pin('G'), (x - 20, ry))
        taps[kind] += [(x - 20, ry), d.pin('S'), (x + 60, ry)]
    s.bus((-160, 530), (360, 530), [(t[0], 530) for t in taps['n']])
    for t in taps['n']:
        if t[1] != 530:
            s.wire(t, (t[0], 530))
    s.label((-160, 530), 'VSS')
    s.bus((440, 370), (760, 370), [(t[0], 370) for t in taps['p']])
    for t in taps['p']:
        if t[1] != 370:
            s.wire(t, (t[0], 370))
    s.label((440, 370), 'VDD')
    s.write(os.path.join(XDIR, 'comp_ct.sch'))
    write_symbol(os.path.join(XDIR, 'comp_ct.sym'), left=['inp', 'inn', 'trim', 'ibias'],
                 right=['out'], top=['VDD'], bottom=['VSS'], params=COMP_PARAMS)


def tgate(s, x, y, a, b, phi, phib, name, a_top=True):
    """Transmission gate centred on (x, y): PMOS (gate phib, out to the left)
    and NMOS (gate phi, out to the right) upright side by side, a joining one
    end of both, b the other (a on top, or at the bottom with a_top=False).
    Returns the a and b junctions (left end of the a line, right end of b)."""
    # (rot, flip) giving the drain (= a) on the wanted side with the gate outward
    n = mos(s, 'n', x + 110, y, W=0.5, L=0.15, name=f'{name}n', body='VSS',
            rot=0 if a_top else 2, flip=1 if a_top else 0)
    p = mos(s, 'p', x - 110, y, W=1, L=0.15, name=f'{name}p', body='VDD',
            rot=2 if a_top else 0, flip=1 if a_top else 0)
    s.bus(p.pin('D'), n.pin('D'))
    s.bus(p.pin('S'), n.pin('S'))
    s.label(p.pin('G'), phib)
    s.label(n.pin('G'), phi, right=True)
    return p.pin('D'), n.pin('S')


def avg_sc():
    s = Sch()
    s.pin_order = ['VDD', 'VSS', 'in', 'out', 'phi1', 'phi2']
    s.text(-600, -300, 'avg_sc: switched-cap average, tau = cavg / (cs * f_phi)\n'
           'phi1: cs <- in, phi2: cs -> out (cavg). cs = ncs x wcs x wcs um, cavg = nca x 30x30 um MIM', 0.4)
    XL = -600
    # local clock inverters: phib for the PMOS halves of the switches
    tops, bots = [], []
    for ph in ('phi1', 'phi2'):
        x = -300 if ph == 'phi1' else 300
        p = mos(s, 'p', x - 20, 330, W=1, L=0.15, name=f'Mi{ph}p', body='VDD')
        n = mos(s, 'n', x - 20, 480, W=0.5, L=0.15, name=f'Mi{ph}n', body='VSS')
        s.bus(p.pin('G'), n.pin('G'), [(x - 40, 405)])
        s.bus(p.pin('D'), n.pin('D'), [(x, 405)])
        s.route((x, 405), (x + 80, 405))
        s.label((x + 80, 405), f'{ph}b', right=True)
        s.route((x - 40, 405), (x - 200, 405))
        s.port((x - 200, 405), ph)
        tops.append(p.pin('S'))
        bots.append(n.pin('S'))
    s.rail(260, XL, 300, tops, 'VDD', port=True)
    s.rail(560, XL, 300, bots, 'VSS', port=True)
    # in -S1(phi1)- cs -S2(phi2)- out
    # S1 drawn a-on-top, S2 a-at-the-bottom: in -> S1 -> cs -> S2 -> out zig-zags through
    a1, b1 = tgate(s, -250, 0, 'in', 'cs', 'phi1', 'phi1b', 'S1')
    a2, b2 = tgate(s, 350, 0, 'cs', 'out', 'phi2', 'phi2b', 'S2', a_top=False)
    cs = s.place('sky130_fd_pr/cap_mim_m3_1.sym', 50, 100, name='Cs', model='cap_mim_m3_1',
                 W="'wcs'", L="'wcs'", MF="'ncs'", spiceprefix='X')
    ca = s.place('sky130_fd_pr/cap_mim_m3_1.sym', 650, 100, name='Cavg', model='cap_mim_m3_1',
                 W='30', L='30', MF="'nca'", spiceprefix='X')
    s.route((XL, a1[1]), a1)
    s.port((XL, a1[1]), 'in')
    s.bus(b1, a2, [(50, 30)])
    s.route((50, 30), cs.pin('c0'))
    s.label((50, 30), 'cs')
    s.bus(b2, (850, -30), [(650, -30)])
    s.route((650, -30), ca.pin('c0'))
    s.port((850, -30), 'out', right=True)
    s.rail(190, -50, 650, [cs.pin('c1'), ca.pin('c1')], 'VSS')
    s.write(os.path.join(XDIR, 'avg_sc.sch'))
    write_symbol(os.path.join(XDIR, 'avg_sc.sym'), left=['in', 'phi1', 'phi2'], right=['out'],
                 top=['VDD'], bottom=['VSS'], params={'ncs': 1, 'nca': 2, 'wcs': 7})


COMP_CODE = """
.param vcm=1.0 vd=0 vtrim=0.9
.options method=GEAR
.control
* threshold (offset) vs input CM, trim at mid
echo cm_V offset_mV
foreach cm 0.55 0.6 0.7 0.8 1.0 1.2 1.4 1.5 1.55 1.6
  alterparam vcm = $cm
  reset
  dc vdiff -20m 20m 0.05m
  meas dc vth when v(out)=0.9 cross=1
  let off = vth * 1e3
  echo $cm $&off
  destroy all
end
* trim transfer at CM 1.0
alterparam vcm = 1.0
echo trim_V offset_mV
foreach t 0 0.2 0.4 0.6 0.8 0.9 1.0 1.2 1.4 1.6 1.8
  alterparam vtrim = $t
  reset
  dc vdiff -30m 30m 0.05m
  meas dc vth when v(out)=0.9 cross=1
  let off = vth * 1e3
  echo $t $&off
  destroy all
end
* input-referred noise at the balance point (CM 1.0, trim mid): find vth, sit there
alterparam vtrim = 0.9
reset
dc vdiff -5m 5m 0.01m
meas dc vth when v(out)=0.9 cross=1
* keep the threshold in control variables: 'destroy all' deletes vectors
let vlo = vth - 1m
let vhi = vth + 1m
set vthv = $&vth
set vlo = $&vlo
set vhi = $&vhi
alterparam vd = $vthv
reset
destroy all
op
print v(x1.o2) v(out)
ac dec 20 1 100meg
let g = abs(v(x1.o2))
meas ac g0 find g at=1
meas ac fp when g=g0/1.414 fall=1
let g0v = g0
set g0s = $&g0v
destroy all
* totals are in the current (integrated) plot right after noise.
* Decision noise = output noise / DC gain (inoise_total integrates the
* input-referred density where the gain is tiny, so it overstates).
noise v(x1.o2) vdiff dec 20 1 100meg
let vn_in_uV = onoise_total / $g0s * 1e6
print onoise_total vn_in_uV
destroy all
* speed: +-1 mV square around the threshold (vthv), 20 kHz
alter @vdiff[pulse] = [ $vlo $vhi 10u 10n 10n 25u 50u ]
tran 10n 120u
let vdf = v(inp) - v(inn)
meas tran trise trig vdf val=$vthv rise=2 targ v(out) val=0.9 rise=2
meas tran tfall trig vdf val=$vthv fall=2 targ v(out) val=0.9 fall=2
.endc
"""


def tb_comp():
    s = Sch()
    s.place('sky130_fd_pr/corner.sym', -1000, -620, name='CORNER', only_toplevel='true', corner='tt')
    s.text(-1000, -760, 'tb_comp: comp_ct threshold vs CM, trim transfer', 0.6)
    s.text(-1000, -710, 'inn = vcm, inp = vcm + vdiff; trim = vtrim (DAC stand-in)', 0.3)
    vd = s.place('devices/vsource.sym', -900, -450, name='VDD', value='1.8')
    s.connect(vd, p='VDD', m='GND')
    vc = s.place('devices/vsource.sym', -700, -100, name='Vcm', value="'vcm'")
    s.connect(vc, p='inn', m='GND')
    vdf = s.place('devices/vsource.sym', -500, -200, name='Vdiff', value='"dc \'vd\' ac 1 pulse(0 0 1 1n 1n 1 2)"')
    s.connect(vdf, p='inp', m='inn')
    vt = s.place('devices/vsource.sym', -300, -100, name='Vtrim', value="'vtrim'")
    s.connect(vt, p='trim', m='GND')
    ib = s.place('devices/isource.sym', -100, -300, name='Ib', value='1u')
    s.connect(ib, p='VDD', m='ibias')
    x = s.place('comp_ct.sym', 300, -150, name='x1')
    s.connect(x, inp='inp', inn='inn', trim='trim', ibias='ibias', out='out', VDD='VDD', VSS='GND')
    s.code(-1000, 100, 'SIMULATION', COMP_CODE)
    s.write(os.path.join(XDIR, 'tb_comp.sch'))


AVG_CODE = """
.param vin0=1.4
.save v(in) v(out)
.options method=GEAR
.control
echo vin_V tau_ms offset_mV
foreach v0 0.6 1.0 1.4 1.5
  alterparam vin0 = $v0
  reset
  tran 50n 2.5m
  * offset: out - in just before the step (settled from t=0 via the .ic below)
  meas tran vo0 avg v(out) from=0.15m to=0.2m
  meas tran vi0 avg v(in) from=0.15m to=0.2m
  let off = (vo0 - vi0) * 1e3
  * tau: time from the step (0.2 ms) to 63 % of the 10 mV step
  let v63 = vo0 + 6.32m
  set v63s = $&v63
  meas tran t63 when v(out)=$v63s rise=1
  let tau = (t63 - 0.2m) * 1e3
  echo $v0 $&tau $&off
  destroy all
end
.endc
"""


def tb_avg():
    s = Sch()
    s.place('sky130_fd_pr/corner.sym', -1000, -620, name='CORNER', only_toplevel='true', corner='tt')
    s.text(-1000, -760, 'tb_avg: avg_sc step response with the digital sc_phi timing', 0.6)
    s.text(-1000, -710, '13 us period (130 clk @ 10 MHz): phi1 6.1 us, 0.4 us gap, phi2 6.1 us; 10 mV step at 0.2 ms', 0.3)
    vd = s.place('devices/vsource.sym', -900, -450, name='VDD', value='1.8')
    s.connect(vd, p='VDD', m='GND')
    vi = s.place('devices/vsource.sym', -700, -100, name='Vin',
                 value='"pwl(0 \'vin0\' 0.2m \'vin0\' 0.2001m \'vin0+10m\')"')
    s.connect(vi, p='in', m='GND')
    p1 = s.place('devices/vsource.sym', -500, -100, name='Vphi1', value='"pulse(0 1.8 0 10n 10n 6.09u 13u)"')
    s.connect(p1, p='phi1', m='GND')
    p2 = s.place('devices/vsource.sym', -300, -100, name='Vphi2', value='"pulse(0 1.8 6.5u 10n 10n 6.09u 13u)"')
    s.connect(p2, p='phi2', m='GND')
    x = s.place('avg_sc.sym', 100, -150, name='x1')
    s.connect(x, **{'in': 'in'}, out='out', phi1='phi1', phi2='phi2', VDD='VDD', VSS='GND')
    s.code(-1000, 100, 'SIMULATION', AVG_CODE + '.ic v(out)=\'vin0\' v(x1.cs)=\'vin0\'\n')
    s.write(os.path.join(XDIR, 'tb_avg.sch'))


if __name__ == '__main__':
    comp_ct()
    avg_sc()
    tb_comp()
    tb_avg()
    print('wrote comp_ct, avg_sc (.sch/.sym), tb_comp.sch, tb_avg.sch')
