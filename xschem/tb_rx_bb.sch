v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {tb_rx_bb: det -> lpf_rc -> avg_sc -> comp_ct (one Gold burst)} -1000 -760 0 0 0.6 0.6 {}
T {det from sim/rx/gen_det.py; trim servo stand-in (B-source); plot: sim/rx/plot_rx.py} -1000 -710 0 0 0.3 0.3 {}
C {sky130_fd_pr/corner.sym} -1000 -620 0 0 {name=CORNER
only_toplevel=true
corner=tt}
C {devices/vsource.sym} -900 -450 0 0 {name=VDD
value=1.8}
C {devices/lab_pin.sym} -900 -480 0 1 {name=p1
sig_type=std_logic
lab=VDD}
C {devices/gnd.sym} -900 -420 0 0 {name=l1
lab=GND}
C {devices/vsource.sym} -700 -450 0 0 {name=Vphi1
value="pulse(0 1.8 0 10n 10n 6.09u 13u)"}
C {devices/lab_pin.sym} -700 -480 0 1 {name=p2
sig_type=std_logic
lab=phi1}
C {devices/gnd.sym} -700 -420 0 0 {name=l2
lab=GND}
C {devices/vsource.sym} -500 -450 0 0 {name=Vphi2
value="pulse(0 1.8 6.5u 10n 10n 6.09u 13u)"}
C {devices/lab_pin.sym} -500 -480 0 1 {name=p3
sig_type=std_logic
lab=phi2}
C {devices/gnd.sym} -500 -420 0 0 {name=l3
lab=GND}
C {devices/isource.sym} -300 -450 0 0 {name=Ib
value=1u}
C {devices/lab_pin.sym} -300 -480 0 1 {name=p4
sig_type=std_logic
lab=VDD}
C {devices/lab_pin.sym} -300 -420 0 1 {name=p5
sig_type=std_logic
lab=ibias}
C {lpf_rc.sym} -500 -100 0 0 {name=x1}
C {devices/lab_pin.sym} -600 -100 0 0 {name=p6
sig_type=std_logic
lab=det}
C {devices/lab_pin.sym} -400 -100 0 1 {name=p7
sig_type=std_logic
lab=lpf}
C {devices/gnd.sym} -550 -50 0 0 {name=l4
lab=GND}
C {avg_sc.sym} -100 0 0 0 {name=x2}
C {devices/lab_pin.sym} -200 -40 0 0 {name=p8
sig_type=std_logic
lab=lpf}
C {devices/lab_pin.sym} 0 -40 0 1 {name=p9
sig_type=std_logic
lab=avg}
C {devices/lab_pin.sym} -200 0 0 0 {name=p10
sig_type=std_logic
lab=phi1}
C {devices/lab_pin.sym} -200 40 0 0 {name=p11
sig_type=std_logic
lab=phi2}
C {devices/lab_pin.sym} -150 -90 0 0 {name=p12
sig_type=std_logic
lab=VDD}
C {devices/gnd.sym} -150 90 0 0 {name=l5
lab=GND}
C {comp_ct.sym} 300 -100 0 0 {name=x3}
C {devices/lab_pin.sym} 200 -160 0 0 {name=p13
sig_type=std_logic
lab=avg}
C {devices/lab_pin.sym} 200 -120 0 0 {name=p14
sig_type=std_logic
lab=lpf}
C {devices/lab_pin.sym} 200 -80 0 0 {name=p15
sig_type=std_logic
lab=trim}
C {devices/lab_pin.sym} 200 -40 0 0 {name=p16
sig_type=std_logic
lab=ibias}
C {devices/lab_pin.sym} 400 -160 0 1 {name=p17
sig_type=std_logic
lab=comp}
C {devices/lab_pin.sym} 250 -210 0 0 {name=p18
sig_type=std_logic
lab=VDD}
C {devices/gnd.sym} 250 10 0 0 {name=l6
lab=GND}
C {devices/code.sym} -1000 100 0 0 {name=SIMULATION
only_toplevel=false
value="
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
"
spice_ignore=false}
