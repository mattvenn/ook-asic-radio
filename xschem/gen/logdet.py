"""
Generate the successive-detection log detector and its testbench:

  det_cell : full-wave rectifier for one chain tap. Each side: AC coupling
             (cc + rb from vb) onto an NMOS gate biased at ~threshold, source
             degeneration rs to VSS, drain to the shared output. Idle current
             is small (set by vb); a tap that limits gives a fixed, clipped
             current, so each cell covers ~one stage gain (~13 dB) of range.
  log_det  : one det_cell per tap (o1..o<N-1>, out), drains summed into
             rdet || cdet from VDD (output 'det' falls with input power).
             vb comes from a replica: ibias_det into a diode-connected cell
             transistor with the same rs, so the idle current tracks Vth.
  tb_logdet: tb_chain front end -> lna_chain -> log_det.

    python xschem/gen/logdet.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from xsch import Sch, mim, mos, poly_r, ports, write_symbol, value_notes
from frontend import antenna_pad
import chain

XDIR = os.path.normpath(os.path.join(HERE, '..'))
NTAPS = chain.NSTAGES

CELL_PARAMS = {'wd': 1, 'rs': '10k', 'cc': '100f', 'rb': '200k'}
DET_PARAMS = {'wd': 1, 'rs': '10k', 'cc': '100f', 'rb': '200k', 'rdet': '8k', 'cdet': '1p'}


def det_cell():
    s = Sch()
    s.pin_order = ['VSS', 'vb', 'inp', 'inn', 'out']
    s.text(-300, -460, 'det_cell: full-wave rectifier, gates AC coupled and biased at ~Vth from vb\n'
           'params: wd (W, L=0.15), rs (source degeneration), cc/rb (coupling)', 0.4)
    XL, XR = -400, 800
    bots, vbs = [], []
    for side, x, fl in (('p', 0, 0), ('n', 400, 1)):
        o = 1 if not fl else -1                     # outward = -x for p, +x for n
        c = mim(s, x - 200 * o, -40, 'cc', flip=fl, name=f'Cc_{side}')  # bottom plate on the chain tap
        rb = poly_r(s, x - 80 * o, -200, 'rb', 'xhigh', '0p35', name=f'Rb_{side}')
        s.connect(rb, B='VSS')
        m = mos(s, 'n', x - 20 * o, -100, W="'wd'", L=0.15, nf=1, name=f'M{side}', body='VSS', flip=fl)
        r = poly_r(s, x, 20, 'rs', 'high', '0p35', name=f'Rs_{side}')
        s.connect(r, B='VSS')
        s.route(c.pin('c0'), (x - 200 * o, -100))
        s.bus((x - 200 * o, -100), m.pin('G'), [(x - 80 * o, -100)])
        s.route(rb.pin('M'), (x - 80 * o, -100))
        s.label((x - 80 * o, -100), f'g{side}', right=bool(fl))
        edge = XR if fl else XL
        s.route(c.pin('c1'), (x - 200 * o, 40), (edge, 40))
        s.port((edge, 40), f'in{side}', right=bool(fl))
        s.bus(m.pin('S'), r.pin('P'), [(x, -40)])
        s.label((x, -40), f's{side}', right=bool(fl))
        s.route(m.pin('D'), (x, -180))
        vbs.append(rb.pin('P'))
        bots.append(r.pin('M'))
    s.bus((0, -180), (400, -180), [(200, -180)])
    s.route((200, -180), (200, -220), (300, -220))
    s.port((300, -220), 'out', right=True)
    s.rail(-260, XL, 480, vbs, 'vb', port=True)
    s.rail(120, XL, 400, bots, 'VSS', port=True)
    value_notes(s, CELL_PARAMS, at={'Cc_p': (-185, 35), 'Cc_n': (12, 35)})
    s.write(os.path.join(XDIR, 'det_cell.sch'))
    write_symbol(os.path.join(XDIR, 'det_cell.sym'), left=['inp', 'inn', 'vb'],
                 right=['out'], bottom=['VSS'], params=CELL_PARAMS)


def log_det(n=NTAPS):
    s = Sch()
    taps = [f't{i}{sd}' for i in range(1, n + 1) for sd in 'pn']
    s.pin_order = ['VDD', 'VSS', 'ibias_det', 'det'] + taps
    s.text(-700, -460, f'log_det: {n} det_cells summed into rdet || cdet; vb from a replica diode\n'
           'taps t<i>p/n: chain stage outputs, last = chain output', 0.4)
    XL, XR, YV, YS, YD = -700, 400 * n + 200, -300, 200, -150
    # replica: diode-connected cell device with the same degeneration
    mb = mos(s, 'n', -400, 0, W="'wd'", L=0.15, nf=1, name='Mbias', body='VSS')
    rsb = poly_r(s, -380, 100, 'rs', 'high', '0p35', name='Rs_b')
    s.connect(rsb, B='VSS')
    s.bus((XL, -60), (-380, -60), [(-440, -60)])
    s.route((-440, -60), mb.pin('G'), vfirst=True)
    s.route((-380, -60), mb.pin('D'))
    s.port((XL, -60), 'ibias_det')
    s.bus(mb.pin('S'), rsb.pin('P'), [(-380, 50)])
    s.label((-380, 50), 'sb', right=True)
    r = poly_r(s, XR - 300, -220, 'rdet', 'high', '0p69', name='Rdet')
    s.connect(r, B='VSS')
    c = mim(s, XR, -220, 'cdet', rot=2, name='Cdet')                # ~22 um square; bottom plate on VDD
    s.route(r.pin('M'), (XR - 300, YD))
    s.route(c.pin('c0'), (XR, YD))
    vss, outs = [rsb.pin('M')], []
    for i in range(1, n + 1):
        x = (i - 1) * 400
        cell = s.place('det_cell.sym', x, 0, name=f'xd{i}', wd="'wd'", rs="'rs'", cc="'cc'", rb="'rb'")
        s.label(cell.pin('vb'), 'ibias_det')
        for pin, net in (('inp', f't{i}p'), ('inn', f't{i}n')):
            q = cell.pin(pin)
            s.route(q, (q[0] - 60, q[1]))
            s.port((q[0] - 60, q[1]), net)
        q = cell.pin('out')
        s.route(q, (q[0] + 40, q[1]), (q[0] + 40, YD))
        outs.append((q[0] + 40, YD))
        vss.append(cell.pin('VSS'))
    s.bus(outs[0], (XR + 100, YD), outs[1:] + [(XR - 300, YD), (XR, YD)])
    s.label(outs[-1], 'det')
    s.port((XR + 100, YD), 'det', right=True)
    s.rail(YV, XL, XR, [r.pin('P'), c.pin('c1')], 'VDD', port=True)
    s.rail(YS, XL, vss[-1][0], vss, 'VSS', port=True)
    value_notes(s, DET_PARAMS, at={'Mbias': (85, -37)})
    s.write(os.path.join(XDIR, 'log_det.sch'))
    write_symbol(os.path.join(XDIR, 'log_det.sym'), left=taps + ['ibias_det'],
                 right=['det'], top=['VDD'], bottom=['VSS'], params=DET_PARAMS, width=200)


PARAMS = chain.PARAMS + """
* log detector
.param ibias_det=2u wd=1 rs=10k ccd=100f rbd=200k rdet=8k cdet=1p
"""

CONTROL = """
.options method=GEAR
.control
op
let idd = -i(vdpwr)
print idd v(det) v(x2.ibias_det)
write tb_logdet_op.raw
* transfer: 434 MHz tone from -110 to -10 dBm available power
echo Pin_dBm det_avg_V det_pp_V
foreach p -110 -100 -95 -90 -85 -80 -75 -70 -65 -60 -55 -50 -45 -40 -35 -30 -25 -20 -15 -10
  let ve = sqrt(8 * 73 * 1e-3 * 10^($p/10))
  alterparam vemf = $&ve
  reset
  tran 50p 600n 400n
  meas tran detavg avg v(det) from=500n to=600n
  meas tran detpp pp v(det) from=500n to=600n
  echo $p $&detavg $&detpp
  destroy all
end
.endc
"""


def tb_logdet():
    s = Sch()
    s.place('sky130_fd_pr/corner.sym', -1400, -620, name='CORNER', only_toplevel='true', corner='tt')
    s.text(-1400, -760, 'tb_logdet: dipole -> pad_model -> lna_chain -> log_det', 0.6)
    s.text(-1400, -710, 'analyse with: python sim/logdet/analyse.py', 0.3)
    antenna_pad(s)
    taps = {f'o{i}{sd}': f'o{i}{sd}' for i in range(1, NTAPS) for sd in 'pn'}
    x1 = s.place('lna_chain.sym', -300, -150, name='x1', w1="'w1'", rl1="'rl1'", mt1="'mt1'",
                 w2="'w2'", rl2="'rl2'", mt2="'mt2'", cs="'cs'", cin="'cin'", rb="'rb'", mm="'mm'")
    s.connect(x1, inp='pad_p', inn='pad_n', ibias='ibias', vcm='vcm', outp='out_p', outn='out_n',
              VDD='VDPWR', VSS='GND', **taps)
    ib = s.place('devices/isource.sym', -500, 250, name='Iref', value="'iref'")
    s.connect(ib, p='VDPWR', m='ibias')
    vcm = s.place('devices/vsource.sym', -300, 250, name='Vcm', value="'vcm_dc'")
    s.connect(vcm, p='vcm', m='GND')
    x2 = s.place('log_det.sym', 500, -150, name='x2', wd="'wd'", rs="'rs'", cc="'ccd'", rb="'rbd'",
                 rdet="'rdet'", cdet="'cdet'")
    nets = {f't{i}{sd}': f'o{i}{sd}' for i in range(1, NTAPS) for sd in 'pn'}
    nets.update({f't{NTAPS}p': 'out_p', f't{NTAPS}n': 'out_n'})
    s.connect(x2, ibias_det='ibias_det', det='det', VDD='VDPWR', VSS='GND', **nets)
    ibd = s.place('devices/isource.sym', 300, 250, name='Ibd', value="'ibias_det'")
    s.connect(ibd, p='VDPWR', m='ibias_det')
    s.code(-1400, 450, 'SIMULATION', PARAMS + CONTROL)
    s.write(os.path.join(XDIR, 'tb_logdet.sch'))


det_cell()
log_det()
tb_logdet()
print('wrote det_cell, log_det (.sch/.sym), tb_logdet.sch')
