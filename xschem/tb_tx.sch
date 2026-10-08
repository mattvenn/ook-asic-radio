v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {tb_tx: tx_top -> pad_model per arm -> dipole (73 ohm + 100 pF series)} -1000 -760 0 0 0.6 0.6 {}
T {key on 5..60 ns; en_p follows the key, en_n = key * ven_n/1.8; analyse: sim/tx/tb_tx.py} -1000 -710 0 0 0.3 0.3 {}
C {sky130_fd_pr/corner.sym} -1000 -620 0 0 {name=CORNER
only_toplevel=true
corner=tt}
C {devices/code.sym} -800 -620 0 0 {name=STDCELLS
only_toplevel=true
format="tcleval( @value )"
value=".include $::SKYWATER_STDCELLS/sky130_fd_sc_hd.spice"
spice_ignore=false}
C {devices/vsource.sym} -900 -450 0 0 {name=VA
value=3.3}
C {devices/lab_pin.sym} -900 -480 0 1 {name=p1
sig_type=std_logic
lab=VAPWR}
C {devices/gnd.sym} -900 -420 0 0 {name=l1
lab=GND}
C {devices/vsource.sym} -700 -450 0 0 {name=VD
value=1.8}
C {devices/lab_pin.sym} -700 -480 0 1 {name=p2
sig_type=std_logic
lab=VDPWR}
C {devices/gnd.sym} -700 -420 0 0 {name=l2
lab=GND}
C {devices/vsource.sym} -900 -100 0 0 {name=Vkey
value="pwl(0 0 5n 0 5.05n 1.8 60n 1.8 60.05n 0)"}
C {devices/lab_pin.sym} -900 -130 0 1 {name=p3
sig_type=std_logic
lab=key}
C {devices/gnd.sym} -900 -70 0 0 {name=l3
lab=GND}
C {devices/vsource.sym} -700 -100 0 0 {name=Ven_p
value="pwl(0 0 5n 0 5.05n 1.8 60n 1.8 60.05n 0)"}
C {devices/lab_pin.sym} -700 -130 0 1 {name=p4
sig_type=std_logic
lab=en_p}
C {devices/gnd.sym} -700 -70 0 0 {name=l4
lab=GND}
C {devices/vsource.sym} -500 -100 0 0 {name=Ven_n
value="pwl(0 0 5n 0 5.05n 'ven_n' 60n 'ven_n' 60.05n 0)"}
C {devices/lab_pin.sym} -500 -130 0 1 {name=p5
sig_type=std_logic
lab=en_n}
C {devices/gnd.sym} -500 -70 0 0 {name=l5
lab=GND}
C {tx_top.sym} -100 -100 0 0 {name=xtx}
C {devices/lab_pin.sym} -200 -140 0 0 {name=p6
sig_type=std_logic
lab=key}
C {devices/lab_pin.sym} -200 -100 0 0 {name=p7
sig_type=std_logic
lab=en_p}
C {devices/lab_pin.sym} -200 -60 0 0 {name=p8
sig_type=std_logic
lab=en_n}
C {devices/lab_pin.sym} 0 -140 0 1 {name=p9
sig_type=std_logic
lab=out_p}
C {devices/lab_pin.sym} 0 -100 0 1 {name=p10
sig_type=std_logic
lab=out_n}
C {devices/lab_pin.sym} -150 -190 0 0 {name=p11
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} -110 -190 0 0 {name=p12
sig_type=std_logic
lab=VAPWR}
C {devices/gnd.sym} -150 -10 0 0 {name=l6
lab=GND}
C {pad_model.sym} 300 -150 0 1 {name=xpad_p}
C {devices/lab_pin.sym} 450 -170 0 1 {name=p13
sig_type=std_logic
lab=ant_p}
C {devices/lab_pin.sym} 150 -170 0 0 {name=p14
sig_type=std_logic
lab=out_p}
C {devices/gnd.sym} 450 -130 0 0 {name=l7
lab=GND}
C {pad_model.sym} 300 50 0 1 {name=xpad_n}
C {devices/lab_pin.sym} 450 30 0 1 {name=p15
sig_type=std_logic
lab=ant_n}
C {devices/lab_pin.sym} 150 30 0 0 {name=p16
sig_type=std_logic
lab=out_n}
C {devices/gnd.sym} 450 70 0 0 {name=l8
lab=GND}
C {devices/res.sym} 650 -150 0 0 {name=Rdip
value=73
m=1}
C {devices/lab_pin.sym} 650 -180 0 1 {name=p17
sig_type=std_logic
lab=ant_p}
C {devices/lab_pin.sym} 650 -120 0 1 {name=p18
sig_type=std_logic
lab=dmid}
C {devices/capa.sym} 650 50 0 0 {name=Cdip
value=100p
m=1}
C {devices/lab_pin.sym} 650 20 0 1 {name=p19
sig_type=std_logic
lab=dmid}
C {devices/lab_pin.sym} 650 80 0 1 {name=p20
sig_type=std_logic
lab=ant_n}
C {devices/code.sym} -1000 100 0 0 {name=SIMULATION
only_toplevel=false
value="
.param ven_n=1.8
.save v(xtx.ring) v(xtx.a) v(xtx.b) v(out_p) v(out_n) v(ant_p) v(ant_n) i(VA) i(VD) v(key)
.options method=GEAR
.control
alterparam ven_n = 1.8
reset
tran 2p 80n 0
meas tran pa avg i(VA) from=25n to=60n
meas tran pd avg i(VD) from=25n to=60n
let ia = -pa * 1e3
let id = -pd * 1e3
echo RESULT ab IA_mA $&ia ID_mA $&id
write tb_tx_ab.raw
destroy all

alterparam ven_n = 0
reset
tran 2p 80n 0
meas tran pa avg i(VA) from=25n to=60n
meas tran pd avg i(VD) from=25n to=60n
let ia = -pa * 1e3
let id = -pd * 1e3
echo RESULT se IA_mA $&ia ID_mA $&id
write tb_tx_se.raw
destroy all
.endc
"
spice_ignore=false}
