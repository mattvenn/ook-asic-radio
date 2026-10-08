v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {tb_lpf: lpf_rc driven like the detector output (8 kOhm source)} -900 -660 0 0 0.6 0.6 {}
T {10 mV step at 1.40 V (detector-like level) at t=20 us} -900 -610 0 0 0.3 0.3 {}
C {sky130_fd_pr/corner.sym} -900 -520 0 0 {name=CORNER
only_toplevel=true
corner=tt}
C {devices/vsource.sym} -600 -150 0 0 {name=Vsrc
value="dc 1.4 ac 1 pwl(0 1.4 20u 1.4 20.01u 1.41)"}
C {devices/lab_pin.sym} -600 -180 0 1 {name=p1
sig_type=std_logic
lab=src}
C {devices/gnd.sym} -600 -120 0 0 {name=l1
lab=GND}
C {devices/res.sym} -450 -210 1 0 {name=Rdet
value=8k
m=1}
C {devices/lab_pin.sym} -420 -210 0 1 {name=p2
sig_type=std_logic
lab=in}
C {devices/lab_pin.sym} -480 -210 0 0 {name=p3
sig_type=std_logic
lab=src}
C {lpf_rc.sym} -150 -180 0 0 {name=x1
lr='lr'
nc='nc'}
C {devices/gnd.sym} -200 -130 0 0 {name=l2
lab=GND}
C {devices/lab_pin.sym} -250 -180 0 0 {name=p4
sig_type=std_logic
lab=in}
C {devices/lab_pin.sym} -50 -180 0 1 {name=p5
sig_type=std_logic
lab=out}
C {devices/code.sym} -900 100 0 0 {name=SIMULATION
only_toplevel=false
value="
.param lr=400 nc=2
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
"
spice_ignore=false}
