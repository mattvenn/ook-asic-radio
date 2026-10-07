"""
Generate xschem/tb_rx_bb.sch: the baseband half of the whole-RX transient,
transistor level: det (PWL from sim/rx/gen_det.py) -> lpf_rc -> avg_sc ->
comp_ct, with the digital's sc_phi timing and a stand-in for the trim servo.

Wiring (det falls with power): avg_sc.in = lpf, comp.inp = avg, comp.inn =
lpf, so comp = 1 when power is above its average.

Trim servo stand-in: the digital steps the 8-bit DAC by +-1 LSB (7.03 mV)
per sample (13 us) towards 50 % ones. Here a B-source ramps Ctrim at
+-7.03 mV / 13 us depending on comp (continuous version of the same loop).

The netlist includes 'det.inc'; sim/rx/bb.sh substitutes the case file.

    python xschem/gen/tb_rx_bb.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from xsch import Sch

XDIR = os.path.normpath(os.path.join(HERE, '..'))

CODE = """
.include det.inc
* trim servo stand-in: +-1 DAC LSB (1.8/256 V) per 13 us sample
Ctrim trim 0 1n
Btrim 0 trim I = (v(comp) > 0.9 ? 1 : -1) * 1n * (1.8/256) / 13u
.ic v(trim)=0.84 v(avg)=1.438 v(x2.cs)=1.438 v(lpf)=1.438
.save v(det) v(lpf) v(avg) v(comp) v(trim) v(phi1)
.options method=GEAR
.control
tran 0.1u 15.2m 0 0.2u
write tb_rx_bb.raw
.endc
"""


def tb():
    s = Sch()
    s.place('sky130_fd_pr/corner.sym', -1000, -620, name='CORNER', only_toplevel='true', corner='tt')
    s.text(-1000, -760, 'tb_rx_bb: det -> lpf_rc -> avg_sc -> comp_ct (one Gold burst)', 0.6)
    s.text(-1000, -710, 'det from sim/rx/gen_det.py; trim servo stand-in (B-source); plot: sim/rx/plot_rx.py', 0.3)
    vd = s.place('devices/vsource.sym', -900, -450, name='VDD', value='1.8')
    s.connect(vd, p='VDD', m='GND')
    p1 = s.place('devices/vsource.sym', -700, -450, name='Vphi1', value='"pulse(0 1.8 0 10n 10n 6.09u 13u)"')
    s.connect(p1, p='phi1', m='GND')
    p2 = s.place('devices/vsource.sym', -500, -450, name='Vphi2', value='"pulse(0 1.8 6.5u 10n 10n 6.09u 13u)"')
    s.connect(p2, p='phi2', m='GND')
    ib = s.place('devices/isource.sym', -300, -450, name='Ib', value='1u')
    s.connect(ib, p='VDD', m='ibias')
    f = s.place('lpf_rc.sym', -500, -100, name='x1')
    s.connect(f, **{'in': 'det'}, out='lpf', VSS='GND')
    a = s.place('avg_sc.sym', -100, 0, name='x2')
    s.connect(a, **{'in': 'lpf'}, out='avg', phi1='phi1', phi2='phi2', VDD='VDD', VSS='GND')
    c = s.place('comp_ct.sym', 300, -100, name='x3')
    s.connect(c, inp='avg', inn='lpf', trim='trim', ibias='ibias', out='comp', VDD='VDD', VSS='GND')
    s.code(-1000, 100, 'SIMULATION', CODE)
    s.write(os.path.join(XDIR, 'tb_rx_bb.sch'))


if __name__ == '__main__':
    tb()
    print('wrote tb_rx_bb.sch')
