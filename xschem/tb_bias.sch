v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {tb_bias: bias_gen into diode loads like the chain / detector / comparator} -1000 -760 0 0 0.5 0.5 {}
T {RESULT lines: currents and vcm vs VDD and T; start-up and en toggling} -1000 -710 0 0 0.3 0.3 {}
C {sky130_fd_pr/corner.sym} -1000 -620 0 0 {name=CORNER
only_toplevel=true
corner=tt}
C {devices/vsource.sym} -900 -450 0 0 {name=Vdd
value="dc 'vdd' pwl(0 'vdd' 1 'vdd')"}
C {devices/lab_pin.sym} -900 -480 0 1 {name=p1
sig_type=std_logic
lab=VDD}
C {devices/gnd.sym} -900 -420 0 0 {name=l1
lab=GND}
C {devices/vsource.sym} -700 -450 0 0 {name=Ven
value="dc 'ven' pwl(0 'ven' 1 'ven')"}
C {devices/lab_pin.sym} -700 -480 0 1 {name=p2
sig_type=std_logic
lab=en}
C {devices/gnd.sym} -700 -420 0 0 {name=l2
lab=GND}
C {bias_gen.sym} -300 -150 0 0 {name=x1}
C {devices/lab_pin.sym} -400 -210 0 0 {name=p3
sig_type=std_logic
lab=en}
C {devices/lab_pin.sym} -200 -210 0 1 {name=p4
sig_type=std_logic
lab=vcm}
C {devices/lab_pin.sym} -200 -170 0 1 {name=p5
sig_type=std_logic
lab=ic}
C {devices/lab_pin.sym} -200 -130 0 1 {name=p6
sig_type=std_logic
lab=id}
C {devices/lab_pin.sym} -200 -90 0 1 {name=p7
sig_type=std_logic
lab=ip}
C {devices/lab_pin.sym} -350 -260 0 0 {name=p8
sig_type=std_logic
lab=VDD}
C {devices/gnd.sym} -350 -40 0 0 {name=l3
lab=GND}
C {devices/vsource.sym} 100 -250 0 0 {name=Vmc
value=0}
C {devices/lab_pin.sym} 100 -280 0 1 {name=p9
sig_type=std_logic
lab=ic}
C {devices/lab_pin.sym} 100 -220 0 1 {name=p10
sig_type=std_logic
lab=lc}
C {sky130_fd_pr/nfet_01v8.sym} 100 0 0 0 {name=Ml0
nf=2
mult=1
ad="'int((nf+1)/2) * W/nf * 0.29'"
pd="'2*int((nf+1)/2) * (W/nf + 0.29)'"
as="'int((nf+2)/2) * W/nf * 0.29'"
ps="'2*int((nf+2)/2) * (W/nf + 0.29)'"
nrd="'0.29 / W'"
nrs="'0.29 / W'"
sa=0
sb=0
sd=0
L=0.5
W=6
model=nfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 120 -30 0 1 {name=p11
sig_type=std_logic
lab=lc}
C {devices/lab_pin.sym} 80 0 0 0 {name=p12
sig_type=std_logic
lab=lc}
C {devices/gnd.sym} 120 30 0 0 {name=l4
lab=GND}
C {devices/gnd.sym} 120 0 0 0 {name=l5
lab=GND}
C {devices/vsource.sym} 400 -250 0 0 {name=Vmd
value=0}
C {devices/lab_pin.sym} 400 -280 0 1 {name=p13
sig_type=std_logic
lab=id}
C {devices/lab_pin.sym} 400 -220 0 1 {name=p14
sig_type=std_logic
lab=ld}
C {sky130_fd_pr/nfet_01v8.sym} 400 0 0 0 {name=Ml1
nf=1
mult=1
ad="'int((nf+1)/2) * W/nf * 0.29'"
pd="'2*int((nf+1)/2) * (W/nf + 0.29)'"
as="'int((nf+2)/2) * W/nf * 0.29'"
ps="'2*int((nf+2)/2) * (W/nf + 0.29)'"
nrd="'0.29 / W'"
nrs="'0.29 / W'"
sa=0
sb=0
sd=0
L=0.15
W=1
model=nfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 420 -30 0 1 {name=p15
sig_type=std_logic
lab=ld}
C {devices/lab_pin.sym} 380 0 0 0 {name=p16
sig_type=std_logic
lab=ld}
C {devices/lab_pin.sym} 420 30 0 1 {name=p17
sig_type=std_logic
lab=lds}
C {devices/gnd.sym} 420 0 0 0 {name=l6
lab=GND}
C {devices/vsource.sym} 700 -250 0 0 {name=Vmp
value=0}
C {devices/lab_pin.sym} 700 -280 0 1 {name=p18
sig_type=std_logic
lab=ip}
C {devices/lab_pin.sym} 700 -220 0 1 {name=p19
sig_type=std_logic
lab=lp}
C {sky130_fd_pr/nfet_01v8.sym} 700 0 0 0 {name=Ml2
nf=1
mult=1
ad="'int((nf+1)/2) * W/nf * 0.29'"
pd="'2*int((nf+1)/2) * (W/nf + 0.29)'"
as="'int((nf+2)/2) * W/nf * 0.29'"
ps="'2*int((nf+2)/2) * (W/nf + 0.29)'"
nrd="'0.29 / W'"
nrs="'0.29 / W'"
sa=0
sb=0
sd=0
L=2
W=2
model=nfet_01v8
spiceprefix=X}
C {devices/lab_pin.sym} 720 -30 0 1 {name=p20
sig_type=std_logic
lab=lp}
C {devices/lab_pin.sym} 680 0 0 0 {name=p21
sig_type=std_logic
lab=lp}
C {devices/gnd.sym} 720 30 0 0 {name=l7
lab=GND}
C {devices/gnd.sym} 720 0 0 0 {name=l8
lab=GND}
C {sky130_fd_pr/res_high_po_0p35.sym} 420 150 0 0 {name=Rlds
L='max((10000.0-963)/995,0.5)'
model=res_high_po_0p35
mult=1
spiceprefix=X}
C {devices/lab_pin.sym} 420 120 0 1 {name=p22
sig_type=std_logic
lab=lds}
C {devices/gnd.sym} 420 180 0 0 {name=l9
lab=GND}
C {devices/gnd.sym} 400 150 0 0 {name=l10
lab=GND}
C {devices/code.sym} -1000 100 0 0 {name=SIMULATION
only_toplevel=false
value="
.param vdd=1.8 ven=1.8
.options method=GEAR
.control
foreach v 1.7 1.8 1.9
  foreach t 10 27 50
    alterparam vdd = $v
    reset
    option temp = $t
    op
    let ic = i(vmc) * 1e6
    let id = i(vmd) * 1e6
    let ip = i(vmp) * 1e6
    let itot = -i(vdd) * 1e6
    let vc = v(vcm)
    echo RESULT op vdd $v T $t ib_chain_uA $&ic ib_det_uA $&id ib_comp_uA $&ip vcm $&vc idd_uA $&itot
    destroy all
  end
end
alterparam vdd = 1.8
alterparam ven = 0
reset
op
let itot = -i(vdd) * 1e6
let ic = i(vmc) * 1e6
echo RESULT off idd_uA $&itot ib_chain_uA $&ic
destroy all
alterparam ven = 1.8
reset
* start-up: VDD ramps 0 -> 1.8 V in 10 us; then en low at 40 us, high at 60 us
alter @vdd[pwl] = [ 0 0 10u 1.8 ]
alter @ven[pwl] = [ 0 0 1u 0 1.01u 1.8 40u 1.8 40.01u 0 60u 0 60.01u 1.8 ]
tran 20n 100u
meas tran ic30 find i(vmc) at=30u
meas tran ic50 find i(vmc) at=50u
meas tran ic99 find i(vmc) at=99u
let a = ic30 * 1e6
let b = ic50 * 1e6
let c = ic99 * 1e6
echo RESULT tran ib_chain_uA at_30u $&a at_50u_en0 $&b at_99u $&c
let ic = i(vmc) * 1e6
meas tran tset when ic=54 rise=last
echo RESULT tran last rise through 54 uA at $&tset
write tb_bias.raw
.endc
"
spice_ignore=false}
