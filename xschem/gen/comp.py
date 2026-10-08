"""
Generate the RX comparator, the switched-cap averaging reference, and their
testbenches.

  comp_ct : continuous-time comparator (the digital's 2-flop synchroniser
            samples it, so no strobe, no kickback onto the ~1 mV LPF node).
            out = 1 when inp > inn + trim offset.
            - stage 1: low-Vt NMOS pair (W 20, L 1, weak inversion), tail
              10 x ibias, low-Vt PMOS mirror load. Low Vt stretches the input
              CM range (det runs ~0.6 V at -20 dBm to ~1.52 V idle).
            - trim: small low-Vt NMOS pair with split tails and rdeg (2 M; was 1.4 M,
              raised 2026-10-08 so the step is ~0.075-0.107 mV/LSB over corners) between
              its sources, on the same loads: offset ~ (trim - VDD/2) *
              (1/rdeg) / gm1; trim from the R2R DAC, VDD/2 from an on-chip
              xhigh-poly divider. Raising 'trim' acts like raising inn.
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
COMP_PARAMS = {'w1': 20, 'l1': 1, 'mt1': 10, 'rdeg': '2Meg', 'mta': 2, 'lref': 136, 'wcl': 22}


def comp_ct():
    s = Sch()
    s.text(-700, -860, 'comp_ct: continuous comparator, out = 1 when inp > inn + trim offset\n'
           'lvt NMOS pair + lvt PMOS mirror; degenerated trim pair (trim vs VDD/2); PMOS CS; inverter', 0.4)
    ports(s, -700, -760, ['VDD', 'VSS', 'ibias', 'inp', 'inn', 'trim', 'out'])
    # bias: ibias into a diode (unit W 2, L 2); tails are multiples of it
    md = mos(s, 'n', -600, 300, W=2, L=2, name='Mb')
    s.connect(md, D='ibias', G='ibias', S='VSS', B='VSS')
    mt = mos(s, 'n', 0, 300, W=2, L=2, mult="'mt1'", name='Mt1')
    s.connect(mt, D='tail', G='ibias', S='VSS', B='VSS')
    # main pair: inp -> d1 (diode side), inn -> d2 (output side)
    for nm, x, g, d in (('M1', -100, 'inp', 'd1'), ('M2', 100, 'inn', 'd2')):
        m = mos(s, 'n', x, 100, W="'w1'", L="'l1'", nf=4, name=nm, vt='lvt')
        s.connect(m, D=d, G=g, S='tail', B='VSS')
    # PMOS mirror load (lvt, L 1): diode on d1
    for nm, x, d in (('Mp1', -100, 'd1'), ('Mp2', 100, 'd2')):
        m = mos(s, 'p', x, -150, W=4, L=1, name=nm, vt='lvt')
        s.connect(m, D=d, G='d1', S='VDD', B='VDD')
    # trim pair: vref -> d1, trim -> d2 (acts like inn), split tails + rdeg
    for nm, x, g, d, sn in (('M3', 300, 'vref', 'd1', 'sa'), ('M4', 500, 'trim', 'd2', 'sb')):
        m = mos(s, 'n', x, 100, W=2, L=1, name=nm, vt='lvt')
        s.connect(m, D=d, G=g, S=sn, B='VSS')
        t = mos(s, 'n', x, 300, W=2, L=2, mult="'mta'", name=f'Mta_{sn}')
        s.connect(t, D=sn, G='ibias', S='VSS', B='VSS')
    r = s.place('sky130_fd_pr/res_xhigh_po_0p35.sym', 400, 200, rot=1, name='Rdeg',
                L="'rdeg/7.37k'", model='res_xhigh_po_0p35', mult='1', spiceprefix='X')
    s.connect(r, P='sb', M='sa', B='VSS')
    # VDD/2 reference for the trim pair (xhigh poly divider + MIM decoupling)
    for nm, y, p, m_ in (('Rr1', -350, 'VDD', 'vref'), ('Rr2', -250, 'vref', 'VSS')):
        rr = s.place('sky130_fd_pr/res_xhigh_po_0p35.sym', 700, y, name=nm, L="'lref'",
                     model='res_xhigh_po_0p35', mult='1', spiceprefix='X')
        s.connect(rr, P=p, M=m_, B='VSS')
    cr = s.place('sky130_fd_pr/cap_mim_m3_1.sym', 800, -250, name='Cref', model='cap_mim_m3_1',
                 W='10', L='10', MF='1', spiceprefix='X')
    s.connect(cr, c0='vref', c1='VSS')
    # band-limit stage 1 (dominant pole ~100 kHz): cuts the integrated noise;
    # a decision only has to settle within one 13 us sample
    cl = s.place('sky130_fd_pr/cap_mim_m3_1.sym', 200, -50, name='Cl', model='cap_mim_m3_1',
                 W="'wcl'", L="'wcl'", MF='1', spiceprefix='X')
    s.connect(cl, c0='d2', c1='VSS')
    # stage 2: PMOS CS (same W/L as the load) + NMOS sink (5 x unit); out2 low when inp > inn
    mp = mos(s, 'p', 900, -150, W=4, L=1, name='Mp3', vt='lvt')
    s.connect(mp, D='o2', G='d2', S='VDD', B='VDD')
    mn = mos(s, 'n', 900, 100, W=2, L=2, mult=5, name='Mn3')
    s.connect(mn, D='o2', G='ibias', S='VSS', B='VSS')
    # output inverter
    ip = mos(s, 'p', 1200, -150, W=2, L=0.15, name='Mip')
    s.connect(ip, D='out', G='o2', S='VDD', B='VDD')
    i_n = mos(s, 'n', 1200, 100, W=1, L=0.15, name='Min')
    s.connect(i_n, D='out', G='o2', S='VSS', B='VSS')
    s.write(os.path.join(XDIR, 'comp_ct.sch'))
    write_symbol(os.path.join(XDIR, 'comp_ct.sym'), left=['inp', 'inn', 'trim', 'ibias'],
                 right=['out'], top=['VDD'], bottom=['VSS'], params=COMP_PARAMS)


def tgate(s, x, y, a, b, phi, phib, name):
    n = mos(s, 'n', x, y, W=0.5, L=0.15, name=f'{name}n')
    s.connect(n, D=a, G=phi, S=b, B='VSS')
    p = mos(s, 'p', x + 200, y, W=1, L=0.15, name=f'{name}p')
    s.connect(p, D=a, G=phib, S=b, B='VDD')


def avg_sc():
    s = Sch()
    s.text(-600, -660, 'avg_sc: switched-cap average, tau = cavg / (cs * f_phi)\n'
           'phi1: cs <- in, phi2: cs -> out (cavg). cs = ncs x wcs x wcs um, cavg = nca x 30x30 um MIM', 0.4)
    ports(s, -600, -560, ['VDD', 'VSS', 'in', 'out', 'phi1', 'phi2'])
    for ph in ('phi1', 'phi2'):
        x = -300 if ph == 'phi1' else 300
        p = mos(s, 'p', x, 300, W=1, L=0.15, name=f'Mi{ph}p')
        s.connect(p, D=f'{ph}b', G=ph, S='VDD', B='VDD')
        n = mos(s, 'n', x, 450, W=0.5, L=0.15, name=f'Mi{ph}n')
        s.connect(n, D=f'{ph}b', G=ph, S='VSS', B='VSS')
    tgate(s, -300, 0, 'in', 'cs', 'phi1', 'phi1b', 'S1')
    tgate(s, 300, 0, 'cs', 'out', 'phi2', 'phi2b', 'S2')
    cs = s.place('sky130_fd_pr/cap_mim_m3_1.sym', 100, 150, name='Cs', model='cap_mim_m3_1',
                 W="'wcs'", L="'wcs'", MF="'ncs'", spiceprefix='X')
    s.connect(cs, c0='cs', c1='VSS')
    ca = s.place('sky130_fd_pr/cap_mim_m3_1.sym', 700, 150, name='Cavg', model='cap_mim_m3_1',
                 W='30', L='30', MF="'nca'", spiceprefix='X')
    s.connect(ca, c0='out', c1='VSS')
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
