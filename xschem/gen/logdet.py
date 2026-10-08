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
from xsch import Sch, mim, mos, poly_r, ports, write_symbol
from frontend import antenna_pad
import chain

XDIR = os.path.normpath(os.path.join(HERE, '..'))
NTAPS = chain.NSTAGES

CELL_PARAMS = {'wd': 1, 'rs': '10k', 'cc': '100f', 'rb': '200k'}
DET_PARAMS = {'wd': 1, 'rs': '10k', 'cc': '100f', 'rb': '200k', 'rdet': '8k', 'cdet': '5p'}


def det_cell():
    s = Sch()
    s.text(-400, -560, 'det_cell: full-wave rectifier, gates AC coupled and biased at ~Vth from vb\n'
           'params: wd (W, L=0.15), rs (source degeneration), cc/rb (coupling)', 0.4)
    ports(s, -400, -460, ['VSS', 'vb', 'inp', 'inn', 'out'])
    for side, x in (('p', 0), ('n', 400)):
        c = mim(s, x - 200, -200, 'cc', name=f'Cc_{side}')          # bottom plate on the chain tap
        s.connect(c, c0=f'g{side}', c1=f'in{side}')
        rb = poly_r(s, x - 100, -300, 'rb', 'xhigh', '0p35', name=f'Rb_{side}')
        s.connect(rb, P='vb', M=f'g{side}', B='VSS')
        m = mos(s, 'n', x, -200, W="'wd'", L=0.15, nf=1, name=f'M{side}')
        s.connect(m, D='out', G=f'g{side}', S=f's{side}', B='VSS')
        r = poly_r(s, x + 20, -50, 'rs', 'high', '0p35', name=f'Rs_{side}')
        s.connect(r, P=f's{side}', M='VSS', B='VSS')
    s.write(os.path.join(XDIR, 'det_cell.sch'))
    write_symbol(os.path.join(XDIR, 'det_cell.sym'), left=['inp', 'inn', 'vb'],
                 right=['out'], bottom=['VSS'], params=CELL_PARAMS)


def log_det(n=NTAPS):
    s = Sch()
    s.text(-600, -760, f'log_det: {n} det_cells summed into rdet || cdet; vb from a replica diode\n'
           'taps t<i>p/n: chain stage outputs, last = chain output', 0.4)
    taps = [f't{i}{sd}' for i in range(1, n + 1) for sd in 'pn']
    ports(s, -600, -660, ['VDD', 'VSS', 'ibias_det', 'det'] + taps)
    # replica: diode-connected cell device with the same degeneration
    mb = mos(s, 'n', -400, 200, W="'wd'", L=0.15, nf=1, name='Mbias')
    s.connect(mb, D='ibias_det', G='ibias_det', S='sb', B='VSS')
    rsb = poly_r(s, -380, 350, 'rs', 'high', '0p35', name='Rs_b')
    s.connect(rsb, P='sb', M='VSS', B='VSS')
    r = poly_r(s, -200, -500, 'rdet', 'high', '0p69', name='Rdet')
    s.connect(r, P='VDD', M='det', B='VSS')
    c = mim(s, -100, -500, 'cdet', mf=4, name='Cdet')               # 4 x ~25 um; bottom plate on VDD
    s.connect(c, c0='det', c1='VDD')
    for i in range(1, n + 1):
        x = (i - 1) * 400
        cell = s.place('det_cell.sym', x, -200, name=f'xd{i}', wd="'wd'", rs="'rs'", cc="'cc'", rb="'rb'")
        s.connect(cell, inp=f't{i}p', inn=f't{i}n', vb='ibias_det', out='det', VSS='VSS')
    s.write(os.path.join(XDIR, 'log_det.sch'))
    write_symbol(os.path.join(XDIR, 'log_det.sym'), left=taps + ['ibias_det'],
                 right=['det'], top=['VDD'], bottom=['VSS'], params=DET_PARAMS, width=200)


PARAMS = chain.PARAMS + """
* log detector
.param ibias_det=2u wd=1 rs=10k ccd=100f rbd=200k rdet=8k cdet=5p
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
                 w2="'w2'", rl2="'rl2'", mt2="'mt2'", cs="'cs'", cin="'cin'", rb="'rb'")
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
