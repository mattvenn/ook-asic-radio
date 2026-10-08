v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {tb_logdet: dipole -> pad_model -> lna_chain -> log_det} -1400 -760 0 0 0.6 0.6 {}
T {analyse with: python sim/logdet/analyse.py} -1400 -710 0 0 0.3 0.3 {}
C {sky130_fd_pr/corner.sym} -1400 -620 0 0 {name=CORNER
only_toplevel=true
corner=tt}
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
C {lna_chain.sym} -300 -150 0 0 {name=x1
w1='w1'
rl1='rl1'
mt1='mt1'
w2='w2'
rl2='rl2'
mt2='mt2'
cs='cs'
cin='cin'
rb='rb'
mm='mm'}
C {devices/lab_pin.sym} -420 -370 0 0 {name=p15
sig_type=std_logic
lab=pad_p}
C {devices/lab_pin.sym} -420 -330 0 0 {name=p16
sig_type=std_logic
lab=pad_n}
C {devices/lab_pin.sym} -420 -290 0 0 {name=p17
sig_type=std_logic
lab=ibias}
C {devices/lab_pin.sym} -420 -250 0 0 {name=p18
sig_type=std_logic
lab=vcm}
C {devices/lab_pin.sym} -180 -370 0 1 {name=p19
sig_type=std_logic
lab=out_p}
C {devices/lab_pin.sym} -180 -330 0 1 {name=p20
sig_type=std_logic
lab=out_n}
C {devices/lab_pin.sym} -370 -420 0 0 {name=p21
sig_type=std_logic
lab=VDPWR}
C {devices/gnd.sym} -370 120 0 0 {name=l5
lab=GND}
C {devices/lab_pin.sym} -180 -290 0 1 {name=p22
sig_type=std_logic
lab=o1p}
C {devices/lab_pin.sym} -180 -250 0 1 {name=p23
sig_type=std_logic
lab=o1n}
C {devices/lab_pin.sym} -180 -210 0 1 {name=p24
sig_type=std_logic
lab=o2p}
C {devices/lab_pin.sym} -180 -170 0 1 {name=p25
sig_type=std_logic
lab=o2n}
C {devices/lab_pin.sym} -180 -130 0 1 {name=p26
sig_type=std_logic
lab=o3p}
C {devices/lab_pin.sym} -180 -90 0 1 {name=p27
sig_type=std_logic
lab=o3n}
C {devices/lab_pin.sym} -180 -50 0 1 {name=p28
sig_type=std_logic
lab=o4p}
C {devices/lab_pin.sym} -180 -10 0 1 {name=p29
sig_type=std_logic
lab=o4n}
C {devices/lab_pin.sym} -180 30 0 1 {name=p30
sig_type=std_logic
lab=o5p}
C {devices/lab_pin.sym} -180 70 0 1 {name=p31
sig_type=std_logic
lab=o5n}
C {devices/isource.sym} -500 250 0 0 {name=Iref
value='iref'}
C {devices/lab_pin.sym} -500 220 0 1 {name=p32
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} -500 280 0 1 {name=p33
sig_type=std_logic
lab=ibias}
C {devices/vsource.sym} -300 250 0 0 {name=Vcm
value='vcm_dc'}
C {devices/lab_pin.sym} -300 220 0 1 {name=p34
sig_type=std_logic
lab=vcm}
C {devices/gnd.sym} -300 280 0 0 {name=l6
lab=GND}
C {log_det.sym} 500 -150 0 0 {name=x2
wd='wd'
rs='rs'
cc='ccd'
rb='rbd'
rdet='rdet'
cdet='cdet'}
C {devices/lab_pin.sym} 380 90 0 0 {name=p35
sig_type=std_logic
lab=ibias_det}
C {devices/lab_pin.sym} 620 -390 0 1 {name=p36
sig_type=std_logic
lab=det}
C {devices/lab_pin.sym} 430 -440 0 0 {name=p37
sig_type=std_logic
lab=VDPWR}
C {devices/gnd.sym} 430 140 0 0 {name=l7
lab=GND}
C {devices/lab_pin.sym} 380 -390 0 0 {name=p38
sig_type=std_logic
lab=o1p}
C {devices/lab_pin.sym} 380 -350 0 0 {name=p39
sig_type=std_logic
lab=o1n}
C {devices/lab_pin.sym} 380 -310 0 0 {name=p40
sig_type=std_logic
lab=o2p}
C {devices/lab_pin.sym} 380 -270 0 0 {name=p41
sig_type=std_logic
lab=o2n}
C {devices/lab_pin.sym} 380 -230 0 0 {name=p42
sig_type=std_logic
lab=o3p}
C {devices/lab_pin.sym} 380 -190 0 0 {name=p43
sig_type=std_logic
lab=o3n}
C {devices/lab_pin.sym} 380 -150 0 0 {name=p44
sig_type=std_logic
lab=o4p}
C {devices/lab_pin.sym} 380 -110 0 0 {name=p45
sig_type=std_logic
lab=o4n}
C {devices/lab_pin.sym} 380 -70 0 0 {name=p46
sig_type=std_logic
lab=o5p}
C {devices/lab_pin.sym} 380 -30 0 0 {name=p47
sig_type=std_logic
lab=o5n}
C {devices/lab_pin.sym} 380 10 0 0 {name=p48
sig_type=std_logic
lab=out_p}
C {devices/lab_pin.sym} 380 50 0 0 {name=p49
sig_type=std_logic
lab=out_n}
C {devices/isource.sym} 300 250 0 0 {name=Ibd
value='ibias_det'}
C {devices/lab_pin.sym} 300 220 0 1 {name=p50
sig_type=std_logic
lab=VDPWR}
C {devices/lab_pin.sym} 300 280 0 1 {name=p51
sig_type=std_logic
lab=ibias_det}
C {devices/code.sym} -1400 450 0 0 {name=SIMULATION
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

* log detector
.param ibias_det=2u wd=1 rs=10k ccd=100f rbd=200k rdet=8k cdet=1p

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
"
spice_ignore=false}
