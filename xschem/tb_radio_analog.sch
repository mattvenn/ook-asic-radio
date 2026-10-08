v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {tb_radio_analog: radio_analog with pad models, both dipoles, debug probe, digital interface from sources} -1400 -760 0 0 0.5 0.5 {}
T {RESULT lines: RX op, all-off current, det at -60 dBm; TX raw for sim/tx/tb_tx.py-style analysis} -1400 -710 0 0 0.3 0.3 {}
C {sky130_fd_pr/corner.sym} -1400 -620 0 0 {name=CORNER
only_toplevel=true
corner=tt}
C {devices/code.sym} -1200 -620 0 0 {name=STDCELLS
only_toplevel=true
format="tcleval( @value )"
value=".include $::SKYWATER_STDCELLS/sky130_fd_sc_hd.spice"
spice_ignore=false}
C {devices/vsource.sym} -1300 -420 0 0 {name=VDPWR
value="dc 1.8 ac 0"}
C {devices/lab_pin.sym} -1300 -450 0 1 {name=p1
sig_type=std_logic
lab=VDPWR}
C {devices/gnd.sym} -1300 -390 0 0 {name=l1
lab=GND}
C {devices/vsource.sym} -1300 300 0 0 {name=Vcmi
value="dc 0 ac 0 sin(0 'vcmi' 'fcmi')"}
C {devices/lab_pin.sym} -1300 270 0 1 {name=p2
sig_type=std_logic
lab=acm}
C {devices/gnd.sym} -1300 330 0 0 {name=l2
lab=GND}
C {devices/vsource.sym} -1300 -300 0 0 {name=Vant_p
value="dc 0 ac 0.5 0 sin(0 'vemf/2' 'f0' 0 0 0)"}
C {devices/lab_pin.sym} -1300 -330 0 1 {name=p3
sig_type=std_logic
lab=emf_p}
C {devices/lab_pin.sym} -1300 -270 0 1 {name=p4
sig_type=std_logic
lab=acm}
C {devices/res.sym} -1150 -360 1 0 {name=Rant_p
value=36.5
m=1}
C {devices/lab_pin.sym} -1120 -360 0 1 {name=p5
sig_type=std_logic
lab=ant_p}
C {devices/lab_pin.sym} -1180 -360 0 0 {name=p6
sig_type=std_logic
lab=emf_p}
C {pad_model.sym} -850 -340 0 0 {name=xpad_p}
C {devices/lab_pin.sym} -1000 -360 0 0 {name=p7
sig_type=std_logic
lab=ant_p}
C {devices/lab_pin.sym} -700 -360 0 1 {name=p8
sig_type=std_logic
lab=pad_p}
C {devices/gnd.sym} -1000 -320 0 0 {name=l3
lab=GND}
C {devices/vsource.sym} -1300 40 0 0 {name=Vant_n
value="dc 0 ac 0.5 180 sin(0 'vemf/2' 'f0' 0 0 180)"}
C {devices/lab_pin.sym} -1300 10 0 1 {name=p9
sig_type=std_logic
lab=emf_n}
C {devices/lab_pin.sym} -1300 70 0 1 {name=p10
sig_type=std_logic
lab=acm}
C {devices/res.sym} -1150 -20 1 0 {name=Rant_n
value=36.5
m=1}
C {devices/lab_pin.sym} -1120 -20 0 1 {name=p11
sig_type=std_logic
lab=ant_n}
C {devices/lab_pin.sym} -1180 -20 0 0 {name=p12
sig_type=std_logic
lab=emf_n}
C {pad_model.sym} -850 0 0 0 {name=xpad_n}
C {devices/lab_pin.sym} -1000 -20 0 0 {name=p13
sig_type=std_logic
lab=ant_n}
C {devices/lab_pin.sym} -700 -20 0 1 {name=p14
sig_type=std_logic
lab=pad_n}
C {devices/gnd.sym} -1000 20 0 0 {name=l4
lab=GND}
C {devices/vsource.sym} -1100 -420 0 0 {name=VA
value=3.3}
C {devices/lab_pin.sym} -1100 -450 0 1 {name=p15
sig_type=std_logic
lab=VAPWR}
C {devices/gnd.sym} -1100 -390 0 0 {name=l5
lab=GND}
C {devices/vsource.sym} -807 600 0 0 {name=Vrx
value='ven_rx'}
C {devices/lab_pin.sym} -807 570 0 1 {name=p16
sig_type=std_logic
lab=rx_en}
C {devices/gnd.sym} -807 630 0 0 {name=l6
lab=GND}
C {devices/vsource.sym} -798 600 0 0 {name=Vdbg
value='vdbg'}
C {devices/lab_pin.sym} -798 570 0 1 {name=p17
sig_type=std_logic
lab=dbg_en}
C {devices/gnd.sym} -798 630 0 0 {name=l7
lab=GND}
C {devices/vsource.sym} -789 600 0 0 {name=Vtx
value="pwl(0 0 5n 0 5.05n 'ven_tx' 60n 'ven_tx' 60.05n 0)"}
C {devices/lab_pin.sym} -789 570 0 1 {name=p18
sig_type=std_logic
lab=tx_en}
C {devices/gnd.sym} -789 630 0 0 {name=l8
lab=GND}
C {devices/vsource.sym} -780 600 0 0 {name=Vtxn
value="pwl(0 0 5n 0 5.05n 'ven_tx' 60n 'ven_tx' 60.05n 0)"}
C {devices/lab_pin.sym} -780 570 0 1 {name=p19
sig_type=std_logic
lab=tx_en_n}
C {devices/gnd.sym} -780 630 0 0 {name=l9
lab=GND}
C {devices/vsource.sym} -771 600 0 0 {name=Vphi1
value="pulse(0 1.8 0 10n 10n 6.09u 13u)"}
C {devices/lab_pin.sym} -771 570 0 1 {name=p20
sig_type=std_logic
lab=sc_phi1}
C {devices/gnd.sym} -771 630 0 0 {name=l10
lab=GND}
C {devices/vsource.sym} -762 600 0 0 {name=Vphi2
value="pulse(0 1.8 6.5u 10n 10n 6.09u 13u)"}
C {devices/lab_pin.sym} -762 570 0 1 {name=p21
sig_type=std_logic
lab=sc_phi2}
C {devices/gnd.sym} -762 630 0 0 {name=l11
lab=GND}
C {devices/vsource.sym} -300 700 0 0 {name=Vt0
value=1.8}
C {devices/lab_pin.sym} -300 670 0 1 {name=p22
sig_type=std_logic
lab=trim[0]}
C {devices/gnd.sym} -300 730 0 0 {name=l12
lab=GND}
C {devices/vsource.sym} -200 700 0 0 {name=Vt1
value=1.8}
C {devices/lab_pin.sym} -200 670 0 1 {name=p23
sig_type=std_logic
lab=trim[1]}
C {devices/gnd.sym} -200 730 0 0 {name=l13
lab=GND}
C {devices/vsource.sym} -100 700 0 0 {name=Vt2
value=1.8}
C {devices/lab_pin.sym} -100 670 0 1 {name=p24
sig_type=std_logic
lab=trim[2]}
C {devices/gnd.sym} -100 730 0 0 {name=l14
lab=GND}
C {devices/vsource.sym} 0 700 0 0 {name=Vt3
value=0}
C {devices/lab_pin.sym} 0 670 0 1 {name=p25
sig_type=std_logic
lab=trim[3]}
C {devices/gnd.sym} 0 730 0 0 {name=l15
lab=GND}
C {devices/vsource.sym} 100 700 0 0 {name=Vt4
value=0}
C {devices/lab_pin.sym} 100 670 0 1 {name=p26
sig_type=std_logic
lab=trim[4]}
C {devices/gnd.sym} 100 730 0 0 {name=l16
lab=GND}
C {devices/vsource.sym} 200 700 0 0 {name=Vt5
value=0}
C {devices/lab_pin.sym} 200 670 0 1 {name=p27
sig_type=std_logic
lab=trim[5]}
C {devices/gnd.sym} 200 730 0 0 {name=l17
lab=GND}
C {devices/vsource.sym} 300 700 0 0 {name=Vt6
value=0}
C {devices/lab_pin.sym} 300 670 0 1 {name=p28
sig_type=std_logic
lab=trim[6]}
C {devices/gnd.sym} 300 730 0 0 {name=l18
lab=GND}
C {devices/vsource.sym} 400 700 0 0 {name=Vt7
value=1.8}
C {devices/lab_pin.sym} 400 670 0 1 {name=p29
sig_type=std_logic
lab=trim[7]}
C {devices/gnd.sym} 400 730 0 0 {name=l19
lab=GND}
C {radio_analog.sym} 0 0 0 0 {name=xana}
C {devices/lab_pin.sym} -140 -120 0 0 {name=p30
sig_type=std_logic
lab=rx_en}
C {devices/lab_pin.sym} -140 -80 0 0 {name=p31
sig_type=std_logic
lab=tx_en}
C {devices/lab_pin.sym} -140 -40 0 0 {name=p32
sig_type=std_logic
lab=tx_en_n}
C {devices/lab_pin.sym} -140 0 0 0 {name=p33
sig_type=std_logic
lab=dbg_en}
C {devices/lab_pin.sym} -140 40 0 0 {name=p34
sig_type=std_logic
lab=sc_phi1}
C {devices/lab_pin.sym} -140 80 0 0 {name=p35
sig_type=std_logic
lab=sc_phi2}
C {devices/lab_pin.sym} 140 -120 0 1 {name=p36
sig_type=std_logic
lab=comp}
C {devices/lab_pin.sym} -90 -170 0 0 {name=p37
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} -50 -170 0 0 {name=p38
sig_type=std_logic
lab=VAPWR}
C {devices/gnd.sym} -90 170 0 0 {name=l20
lab=GND}
C {devices/lab_pin.sym} 140 -80 0 1 {name=p39
sig_type=std_logic
lab=tx_p}
C {devices/lab_pin.sym} 140 -40 0 1 {name=p40
sig_type=std_logic
lab=tx_n}
C {devices/lab_pin.sym} 140 0 0 1 {name=p41
sig_type=std_logic
lab=pad_p}
C {devices/lab_pin.sym} 140 40 0 1 {name=p42
sig_type=std_logic
lab=pad_n}
C {devices/lab_pin.sym} 140 80 0 1 {name=p43
sig_type=std_logic
lab=dbg}
C {devices/lab_pin.sym} -140 120 0 0 {name=p44
sig_type=std_logic
lab=trim[7:0]}
C {pad_model.sym} 700 -150 0 1 {name=xpadtx_p}
C {devices/lab_pin.sym} 850 -170 0 1 {name=p45
sig_type=std_logic
lab=ant_tx_p}
C {devices/lab_pin.sym} 550 -170 0 0 {name=p46
sig_type=std_logic
lab=tx_p}
C {devices/gnd.sym} 850 -130 0 0 {name=l21
lab=GND}
C {pad_model.sym} 700 50 0 1 {name=xpadtx_n}
C {devices/lab_pin.sym} 850 30 0 1 {name=p47
sig_type=std_logic
lab=ant_tx_n}
C {devices/lab_pin.sym} 550 30 0 0 {name=p48
sig_type=std_logic
lab=tx_n}
C {devices/gnd.sym} 850 70 0 0 {name=l22
lab=GND}
C {devices/res.sym} 1000 -150 0 0 {name=Rdip
value=73
m=1}
C {devices/lab_pin.sym} 1000 -180 0 1 {name=p49
sig_type=std_logic
lab=ant_tx_p}
C {devices/lab_pin.sym} 1000 -120 0 1 {name=p50
sig_type=std_logic
lab=dmid}
C {devices/capa.sym} 1000 50 0 0 {name=Cdip
value=100p
m=1}
C {devices/lab_pin.sym} 1000 20 0 1 {name=p51
sig_type=std_logic
lab=dmid}
C {devices/lab_pin.sym} 1000 80 0 1 {name=p52
sig_type=std_logic
lab=ant_tx_n}
C {pad_model.sym} 700 300 0 1 {name=xpaddbg}
C {devices/lab_pin.sym} 850 280 0 1 {name=p53
sig_type=std_logic
lab=dbg_pin}
C {devices/lab_pin.sym} 550 280 0 0 {name=p54
sig_type=std_logic
lab=dbg}
C {devices/gnd.sym} 850 320 0 0 {name=l23
lab=GND}
C {devices/res.sym} 1000 300 0 0 {name=Rprobe
value=1Meg
m=1}
C {devices/lab_pin.sym} 1000 270 0 1 {name=p55
sig_type=std_logic
lab=dbg_pin}
C {devices/gnd.sym} 1000 330 0 0 {name=l24
lab=GND}
C {devices/code.sym} -1400 900 0 0 {name=SIMULATION
only_toplevel=false
value="
.param f0=433.92e6
* transient EMF (differential amplitude); -80 dBm from 73 ohm = 76.4 uV
.param vemf=76.4e-6
.param vcmi=20e-3 fcmi=10e6
.param mm=0.01
* reference current (stage tail = mt x iref) and gate bias
.param iref=60u vcm_dc=1.2
* chain sizing (passed to x1; sweep these)
.param w1=80 rl1=1k mt1=20 w2=20 rl2=4k mt2=6 cs=0.6p cin=2p rb=20k

.param ven_rx=1.8 ven_tx=0 vdbg=0
.options method=GEAR
.control
* 1: RX on, TX off, no signal: operating point
op
let idp = -i(vdpwr) * 1e3
let iap = -i(va) * 1e3
echo RESULT op_rx IDPWR_mA $&idp IAPWR_mA $&iap vcm $&v(xana.vcm) det $&v(xana.det) lpf $&v(xana.lpf) trim $&v(xana.trim) tx_p $&v(tx_p) tx_n $&v(tx_n)
destroy all
* 2: everything off (rx_en = 0, tx_en = 0)
alterparam ven_rx = 0
reset
op
let idp = -i(vdpwr) * 1e6
let iap = -i(va) * 1e6
echo RESULT op_off IDPWR_uA $&idp IAPWR_uA $&iap
destroy all
* 3: RX on, -60 dBm tone at 434 MHz (EMF 0.764 mV): det level (vs op_rx)
alterparam ven_rx = 1.8
alterparam vemf = 7.64e-4
reset
tran 50p 600n 400n
meas tran detavg avg v(xana.det) from=500n to=600n
echo RESULT rx_m60dBm det $&detavg
destroy all
* 4: TX keyed 5..60 ns, RX off
alterparam vemf = 0
alterparam ven_rx = 0
alterparam ven_tx = 1.8
reset
tran 2p 80n 0
write tb_radio_analog_tx.raw
.endc
"
spice_ignore=false}
