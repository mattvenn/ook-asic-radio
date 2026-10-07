"""
Generate the post-detection low-pass filter and its testbench:

  lpf_rc : passive single-pole RC between the log detector and the
           comparator: xhigh poly R (res_xhigh_po_0p35, ~7.37 kOhm per um of
           length at 0.35 um wide) and MIM caps (cap_mim_m3_1, 30x30 um =
           1.82 pF each). Defaults: L = 136 um (~1.0 MOhm), 6 caps (~10.9 pF)
           -> ~14.6 kHz. The e2e model is insensitive to 10-20 kHz, so the
           +-20-30 % spread of an on-chip RC is fine. The cap is kept large
           to soak up comparator kickback on a node that carries ~1 mV of
           signal near sensitivity.
           Keep the ua[4] debug pin OFF this node (nA of pad/ESD leakage
           into 1 MOhm = mV of offset): tap 'det' instead.
  tb_lpf : AC response + step response, driven from an ideal source with the
           detector's 8 kOhm output resistance.

    python xschem/gen/lpf.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from xsch import Sch, ports, write_symbol

XDIR = os.path.normpath(os.path.join(HERE, '..'))
LPF_PARAMS = {'lr': 136, 'nc': 6}


def lpf_rc():
    s = Sch()
    s.text(-400, -460, 'lpf_rc: xhigh poly R (L=lr um, 0.35 um wide) + nc x 30x30 um MIM caps\n'
           'defaults ~1.0 MOhm, ~10.9 pF -> ~14.6 kHz', 0.4)
    ports(s, -400, -360, ['VSS', 'in', 'out'])
    r = s.place('sky130_fd_pr/res_xhigh_po_0p35.sym', 0, -150, rot=1, name='R1',
                L="'lr'", model='res_xhigh_po_0p35', mult='1', spiceprefix='X')
    s.connect(r, P='out', M='in', B='VSS')
    c = s.place('sky130_fd_pr/cap_mim_m3_1.sym', 200, -100, name='C1',
                model='cap_mim_m3_1', W='30', L='30', MF="'nc'", spiceprefix='X')
    s.connect(c, c0='out', c1='VSS')
    s.write(os.path.join(XDIR, 'lpf_rc.sch'))
    write_symbol(os.path.join(XDIR, 'lpf_rc.sym'), left=['in'], right=['out'], bottom=['VSS'],
                 params=LPF_PARAMS)


CODE = """
.param lr=136 nc=6
.options method=GEAR
.control
ac dec 50 100 10meg
let g = db(v(out)/v(src))
meas ac f3db when g=-3
write tb_lpf_ac.raw
tran 0.2u 200u
meas tran t10 when v(out)=1.401 rise=1
meas tran t90 when v(out)=1.409 rise=1
let trise = t90 - t10
print trise
write tb_lpf_tran.raw
.endc
"""


def tb_lpf():
    s = Sch()
    s.place('sky130_fd_pr/corner.sym', -900, -520, name='CORNER', only_toplevel='true', corner='tt')
    s.text(-900, -660, 'tb_lpf: lpf_rc driven like the detector output (8 kOhm source)', 0.6)
    s.text(-900, -610, '10 mV step at 1.40 V (detector-like level) at t=20 us', 0.3)
    v = s.place('devices/vsource.sym', -600, -150, name='Vsrc',
                value='"dc 1.4 ac 1 pwl(0 1.4 20u 1.4 20.01u 1.41)"')
    s.connect(v, p='src', m='GND')
    r = s.place('devices/res.sym', -450, -210, rot=1, name='Rdet', value='8k', m='1')
    s.connect(r, P='in', M='src')
    x = s.place('lpf_rc.sym', -150, -180, name='x1', lr="'lr'", nc="'nc'")
    s.connect(x, VSS='GND')
    s.connect(x, **{'in': 'in', 'out': 'out'})
    s.code(-900, 100, 'SIMULATION', CODE)
    s.write(os.path.join(XDIR, 'tb_lpf.sch'))


if __name__ == '__main__':
    lpf_rc()
    tb_lpf()
    print('wrote lpf_rc (.sch/.sym), tb_lpf.sch')
