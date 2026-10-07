"""
Generate xschem/tb_input.sch: antenna -> pad model (pad, ESD, TT analog mux)
-> chip core, for both sides of the RX dipole (ua[2], ua[3]).

    python xschem/gen/tb_input.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from xsch import Sch

OUT = os.path.join(HERE, '..', 'tb_input.sch')

s = Sch()
s.place('sky130_fd_pr/corner.sym', -1400, -620, name='CORNER', only_toplevel='true', corner='tt')
s.text(-1400, -760, 'tb_input: what reaches the chip core from the RX dipole', 0.6)
s.text(-1400, -710, 'balanced 73 ohm dipole (36.5 ohm per side) -> pad_model (pad, ESD, TT mux) -> core\n'
       'core load = 100 fF LNA gate + 1 Meg bias path (stand-in until the LNA exists)', 0.3)

# supplies (VAPWR is only used inside pad_model's ESD/mux, which has its own source)
vd = s.place('devices/vsource.sym', -1300, -420, name='VDPWR', value='1.8')
s.connect(vd, p='VDPWR', m='GND')

# antenna: two antiphase sources (EMF amplitude 'vemf' differential), 36.5 ohm each side
for side, y, phase in (('p', -300, 0), ('n', 40, 180)):
    v = s.place('devices/vsource.sym', -1300, y, name=f'Vant_{side}',
                value=f'"dc 0 ac 0.5 {phase} sin(0 \'vemf/2\' \'f0\' 0 0 {phase})"')
    s.connect(v, p=f'emf_{side}', m='GND')
    r = s.place('devices/res.sym', -1150, y - 60, rot=1, name=f'Rant_{side}', value='36.5', m='1')
    s.connect(r, P=f'ant_{side}', M=f'emf_{side}')
    pad = s.place('pad_model.sym', -850, y - 40, name=f'xpad_{side}')
    s.connect(pad, pin=f'ant_{side}', mod=f'rf_{side}', VGND='GND')
    c = s.place('devices/capa.sym', -560, y, name=f'Cin_{side}', value='100f', m='1')
    s.connect(c, p=f'rf_{side}', m='GND')
    rb = s.place('devices/res.sym', -460, y, name=f'Rbias_{side}', value='1Meg', m='1')
    s.connect(rb, P=f'rf_{side}', M='GND')

s.code(-1400, 200, 'SIMULATION', """
.param f0=433.92e6
* vemf: differential EMF amplitude. -50 dBm available from a 73 ohm dipole:
* P = vemf^2 / (8 * 73)  ->  vemf = sqrt(8 * 73 * 1e-8) = 2.42 mV
.param vemf=2.42e-3
.options method=GEAR
.control
ac dec 100 10meg 3g
let gain = (v(rf_p) - v(rf_n)) / (v(emf_p) - v(emf_n))
let gain_db = db(gain)
meas ac gain433 find gain_db at=433.92e6
meas ac gain100 find gain_db at=100e6
let zin_core = abs((v(rf_p) - v(rf_n)) / (i(Vant_p)))
write tb_input_ac.raw
tran 10p 30n
let rf_diff = v(rf_p) - v(rf_n)
let emf_diff = v(emf_p) - v(emf_n)
meas tran vrf_pp pp rf_diff from=20n to=30n
meas tran vemf_pp pp emf_diff from=20n to=30n
write tb_input_tran.raw
.endc
""")
s.launcher(-1400, 640, 'load AC', 'xschem raw_read $netlist_dir/tb_input_ac.raw ac')
s.launcher(-1400, 700, 'load tran', 'xschem raw_read $netlist_dir/tb_input_tran.raw tran')
s.graph(-200, -700, 700, -350, ['gain_db'], x_lo=7, x_hi=9.48, y_lo=-30, y_hi=0, logx=1,
        title='AC: core differential voltage per volt of antenna EMF (dB)')
s.graph(-200, -250, 700, 100, ['emf_diff', 'rf_diff'], x_lo=20e-9, x_hi=30e-9,
        y_lo=-3e-3, y_hi=3e-3, title='tran: -50 dBm at 433.92 MHz, antenna EMF vs core')
s.write(OUT)
print('wrote', os.path.normpath(OUT))
