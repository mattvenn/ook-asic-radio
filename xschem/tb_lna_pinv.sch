v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
B 2 -200 250 700 600 {flags=graph
y1=-0.02
y2=0.02
ypos1=0
ypos2=2
divy=5
subdivy=1
unity=1
x1=0
x2=4e-07
divx=5
subdivx=1
xlabmag=1.0
ylabmag=1.0
node=""o1 diff; o1p o1n -""
color="4"
dataset=-1
unitx=1
logx=0
logy=0
}
T {tb_lna_pinv: first-stage LNA experiment (pinv), loaded by a copy of itself} -1400 -760 0 0 0.6 0.6 {}
T {dipole (36.5 ohm per side, common path through Vcmi) -> pad_model -> Cc -> x1 -> x2
analyse with: python sim/lna/analyse.py} -1400 -710 0 0 0.3 0.3 {}
T {tran: stage 1 differential output (V)} -200 220 0 0 0.4 0.4 {}
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
C {devices/capa.sym} -600 -360 1 0 {name=Cc_p
value='cc'
m=1}
C {devices/lab_pin.sym} -570 -360 0 1 {name=p9
sig_type=std_logic
lab=in_p}
C {devices/lab_pin.sym} -630 -360 0 0 {name=p10
sig_type=std_logic
lab=pad_p}
C {devices/vsource.sym} -1300 40 0 0 {name=Vant_n
value="dc 0 ac 0.5 180 sin(0 'vemf/2' 'f0' 0 0 180)"}
C {devices/lab_pin.sym} -1300 10 0 1 {name=p11
sig_type=std_logic
lab=emf_n}
C {devices/lab_pin.sym} -1300 70 0 1 {name=p12
sig_type=std_logic
lab=acm}
C {devices/res.sym} -1150 -20 1 0 {name=Rant_n
value=36.5
m=1}
C {devices/lab_pin.sym} -1120 -20 0 1 {name=p13
sig_type=std_logic
lab=ant_n}
C {devices/lab_pin.sym} -1180 -20 0 0 {name=p14
sig_type=std_logic
lab=emf_n}
C {pad_model.sym} -850 0 0 0 {name=xpad_n}
C {devices/lab_pin.sym} -1000 -20 0 0 {name=p15
sig_type=std_logic
lab=ant_n}
C {devices/lab_pin.sym} -700 -20 0 1 {name=p16
sig_type=std_logic
lab=pad_n}
C {devices/gnd.sym} -1000 20 0 0 {name=l4
lab=GND}
C {devices/capa.sym} -600 -20 1 0 {name=Cc_n
value='cc'
m=1}
C {devices/lab_pin.sym} -570 -20 0 1 {name=p17
sig_type=std_logic
lab=in_n}
C {devices/lab_pin.sym} -630 -20 0 0 {name=p18
sig_type=std_logic
lab=pad_n}
C {lna_pinv.sym} -200 -150 0 0 {name=x1}
C {devices/lab_pin.sym} -300 -170 0 0 {name=p19
sig_type=std_logic
lab=in_p}
C {devices/lab_pin.sym} -300 -130 0 0 {name=p20
sig_type=std_logic
lab=in_n}
C {devices/lab_pin.sym} -100 -170 0 1 {name=p21
sig_type=std_logic
lab=o1p}
C {devices/lab_pin.sym} -100 -130 0 1 {name=p22
sig_type=std_logic
lab=o1n}
C {devices/lab_pin.sym} -250 -220 0 0 {name=p23
sig_type=std_logic
lab=VDPWR}
C {devices/gnd.sym} -250 -80 0 0 {name=l5
lab=GND}
C {lna_pinv.sym} 300 -150 0 0 {name=x2}
C {devices/lab_pin.sym} 200 -170 0 0 {name=p24
sig_type=std_logic
lab=i2p}
C {devices/lab_pin.sym} 200 -130 0 0 {name=p25
sig_type=std_logic
lab=i2n}
C {devices/lab_pin.sym} 400 -170 0 1 {name=p26
sig_type=std_logic
lab=o2p}
C {devices/lab_pin.sym} 400 -130 0 1 {name=p27
sig_type=std_logic
lab=o2n}
C {devices/lab_pin.sym} 250 -220 0 0 {name=p28
sig_type=std_logic
lab=VDPWR}
C {devices/gnd.sym} 250 -80 0 0 {name=l6
lab=GND}
C {devices/capa.sym} 100 -350 1 0 {name=Cc2_p
value='cc'
m=1}
C {devices/lab_pin.sym} 130 -350 0 1 {name=p29
sig_type=std_logic
lab=i2p}
C {devices/lab_pin.sym} 70 -350 0 0 {name=p30
sig_type=std_logic
lab=o1p}
C {devices/capa.sym} 100 50 1 0 {name=Cc2_n
value='cc'
m=1}
C {devices/lab_pin.sym} 130 50 0 1 {name=p31
sig_type=std_logic
lab=i2n}
C {devices/lab_pin.sym} 70 50 0 0 {name=p32
sig_type=std_logic
lab=o1n}
C {devices/code.sym} -1400 450 0 0 {name=SIMULATION
only_toplevel=false
value="
.param f0=433.92e6
* vemf: differential EMF amplitude for the transient. -80 dBm from 73 ohm:
* vemf = sqrt(8 * 73 * 1e-11) = 76.4 uV
.param vemf=76.4e-6
* common-mode interferer: 20 mV at 10 MHz (our clock)
.param vcmi=20e-3 fcmi=10e6
* 1 % device mismatch between the p and n halves (so CM -> diff shows up)
.param mm=0.01
* lna_dp sizing
.param w_dp=20 l_dp=0.15 rl_dp=2k wt_dp=6 vcm_dp=1.2 ibias_dp=60u rb_dp=20k
* lna_dpp sizing (output CM = drop across rl to ground ~0.6 V; input CM to match)
.param w_dpp=80 l_dpp=0.15 rl_dpp=2k wt_dpp=12 vcm_dpp=0.6 ibias_dpp=60u rb_dpp=20k
* lna_pinv sizing
.param wn_inv=10 wp_inv=20 rf_inv=20k
.param cc=2p

.options method=GEAR
.control
op
let idd = -i(vdpwr)
print idd v(in_p) v(o1p) v(o1n) v(o2p)
write tb_lna_pinv_op.raw
* 1: differential input
ac dec 100 1meg 3g
write tb_lna_pinv_acdiff.raw
* 2: common-mode input (source in the antenna common path)
alter @vant_p[acmag]=0
alter @vant_n[acmag]=0
alter @vcmi[acmag]=1
ac dec 100 1meg 3g
write tb_lna_pinv_accm.raw
* 3: supply
alter @vcmi[acmag]=0
alter @vdpwr[acmag]=1
ac dec 100 1meg 3g
write tb_lna_pinv_acpsrr.raw
alter @vdpwr[acmag]=0
* noise at the first stage output, whole front end included
noise v(o1p,o1n) vant_p dec 100 10meg 3g
setplot previous
write tb_lna_pinv_noise.raw
* same at the stage 2 output: the cascade, stage 2 noise included
noise v(o2p,o2n) vant_p dec 100 10meg 3g
setplot previous
write tb_lna_pinv_noise2.raw
* weak -80 dBm signal + 20 mV 10 MHz common-mode interferer
tran 20p 400n
write tb_lna_pinv_tran.raw
.endc
"
spice_ignore=false}
C {devices/launcher.sym} -1400 900 0 0 {name=h1
descr="load tran"
tclcommand="xschem raw_read $netlist_dir/tb_lna_pinv_tran.raw tran"}
