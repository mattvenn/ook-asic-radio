v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
B 2 -200 -700 700 -350 {flags=graph
y1=-30
y2=0
ypos1=0
ypos2=2
divy=5
subdivy=1
unity=1
x1=7
x2=9.48
divx=5
subdivx=1
xlabmag=1.0
ylabmag=1.0
node="gain_db"
color="4"
dataset=-1
unitx=1
logx=1
logy=0
}
B 2 -200 -250 700 100 {flags=graph
y1=-0.003
y2=0.003
ypos1=0
ypos2=2
divy=5
subdivy=1
unity=1
x1=2e-08
x2=3e-08
divx=5
subdivx=1
xlabmag=1.0
ylabmag=1.0
node="emf_diff
rf_diff"
color="4 10"
dataset=-1
unitx=1
logx=0
logy=0
}
T {tb_input: what reaches the chip core from the RX dipole} -1400 -760 0 0 0.6 0.6 {}
T {balanced 73 ohm dipole (36.5 ohm per side) -> pad_model (pad, ESD, TT mux) -> core
core load = 100 fF LNA gate + 1 Meg bias path (stand-in until the LNA exists)} -1400 -710 0 0 0.3 0.3 {}
T {AC: core differential voltage per volt of antenna EMF (dB)} -200 -730 0 0 0.4 0.4 {}
T {tran: -50 dBm at 433.92 MHz, antenna EMF vs core} -200 -280 0 0 0.4 0.4 {}
C {sky130_fd_pr/corner.sym} -1400 -620 0 0 {name=CORNER
only_toplevel=true
corner=tt}
C {devices/vsource.sym} -1300 -420 0 0 {name=VDPWR
value=1.8}
C {devices/lab_pin.sym} -1300 -450 0 1 {name=p1
sig_type=std_logic
lab=VDPWR}
C {devices/gnd.sym} -1300 -390 0 0 {name=l1
lab=GND}
C {devices/vsource.sym} -1300 -300 0 0 {name=Vant_p
value="dc 0 ac 0.5 0 sin(0 'vemf/2' 'f0' 0 0 0)"}
C {devices/lab_pin.sym} -1300 -330 0 1 {name=p2
sig_type=std_logic
lab=emf_p}
C {devices/gnd.sym} -1300 -270 0 0 {name=l2
lab=GND}
C {devices/res.sym} -1150 -360 1 0 {name=Rant_p
value=36.5
m=1}
C {devices/lab_pin.sym} -1120 -360 0 1 {name=p3
sig_type=std_logic
lab=ant_p}
C {devices/lab_pin.sym} -1180 -360 0 0 {name=p4
sig_type=std_logic
lab=emf_p}
C {pad_model.sym} -850 -340 0 0 {name=xpad_p}
C {devices/lab_pin.sym} -1000 -360 0 0 {name=p5
sig_type=std_logic
lab=ant_p}
C {devices/lab_pin.sym} -700 -360 0 1 {name=p6
sig_type=std_logic
lab=rf_p}
C {devices/gnd.sym} -1000 -320 0 0 {name=l3
lab=GND}
C {devices/capa.sym} -560 -300 0 0 {name=Cin_p
value=100f
m=1}
C {devices/lab_pin.sym} -560 -330 0 1 {name=p7
sig_type=std_logic
lab=rf_p}
C {devices/gnd.sym} -560 -270 0 0 {name=l4
lab=GND}
C {devices/res.sym} -460 -300 0 0 {name=Rbias_p
value=1Meg
m=1}
C {devices/lab_pin.sym} -460 -330 0 1 {name=p8
sig_type=std_logic
lab=rf_p}
C {devices/gnd.sym} -460 -270 0 0 {name=l5
lab=GND}
C {devices/vsource.sym} -1300 40 0 0 {name=Vant_n
value="dc 0 ac 0.5 180 sin(0 'vemf/2' 'f0' 0 0 180)"}
C {devices/lab_pin.sym} -1300 10 0 1 {name=p9
sig_type=std_logic
lab=emf_n}
C {devices/gnd.sym} -1300 70 0 0 {name=l6
lab=GND}
C {devices/res.sym} -1150 -20 1 0 {name=Rant_n
value=36.5
m=1}
C {devices/lab_pin.sym} -1120 -20 0 1 {name=p10
sig_type=std_logic
lab=ant_n}
C {devices/lab_pin.sym} -1180 -20 0 0 {name=p11
sig_type=std_logic
lab=emf_n}
C {pad_model.sym} -850 0 0 0 {name=xpad_n}
C {devices/lab_pin.sym} -1000 -20 0 0 {name=p12
sig_type=std_logic
lab=ant_n}
C {devices/lab_pin.sym} -700 -20 0 1 {name=p13
sig_type=std_logic
lab=rf_n}
C {devices/gnd.sym} -1000 20 0 0 {name=l7
lab=GND}
C {devices/capa.sym} -560 40 0 0 {name=Cin_n
value=100f
m=1}
C {devices/lab_pin.sym} -560 10 0 1 {name=p14
sig_type=std_logic
lab=rf_n}
C {devices/gnd.sym} -560 70 0 0 {name=l8
lab=GND}
C {devices/res.sym} -460 40 0 0 {name=Rbias_n
value=1Meg
m=1}
C {devices/lab_pin.sym} -460 10 0 1 {name=p15
sig_type=std_logic
lab=rf_n}
C {devices/gnd.sym} -460 70 0 0 {name=l9
lab=GND}
C {devices/code.sym} -1400 200 0 0 {name=SIMULATION
only_toplevel=false
value="
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
"
spice_ignore=false}
C {devices/launcher.sym} -1400 640 0 0 {name=h1
descr="load AC"
tclcommand="xschem raw_read $netlist_dir/tb_input_ac.raw ac"}
C {devices/launcher.sym} -1400 700 0 0 {name=h2
descr="load tran"
tclcommand="xschem raw_read $netlist_dir/tb_input_tran.raw tran"}
