v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {tb_dac: r2r driven by ideal 1.8 V bits (B-sources from code)} -1000 -760 0 0 0.5 0.5 {}
C {sky130_fd_pr/corner.sym} -1000 -620 0 0 {name=CORNER
only_toplevel=true
corner=tt}
C {devices/vsource.sym} -900 -400 0 0 {name=Vb0
value='vdd*(floor(code/1)-2*floor(code/2))'}
C {devices/lab_pin.sym} -900 -430 0 1 {name=p1
sig_type=std_logic
lab=b0}
C {devices/gnd.sym} -900 -370 0 0 {name=l1
lab=GND}
C {devices/vsource.sym} -780 -400 0 0 {name=Vb1
value='vdd*(floor(code/2)-2*floor(code/4))'}
C {devices/lab_pin.sym} -780 -430 0 1 {name=p2
sig_type=std_logic
lab=b1}
C {devices/gnd.sym} -780 -370 0 0 {name=l2
lab=GND}
C {devices/vsource.sym} -660 -400 0 0 {name=Vb2
value='vdd*(floor(code/4)-2*floor(code/8))'}
C {devices/lab_pin.sym} -660 -430 0 1 {name=p3
sig_type=std_logic
lab=b2}
C {devices/gnd.sym} -660 -370 0 0 {name=l3
lab=GND}
C {devices/vsource.sym} -540 -400 0 0 {name=Vb3
value='vdd*(floor(code/8)-2*floor(code/16))'}
C {devices/lab_pin.sym} -540 -430 0 1 {name=p4
sig_type=std_logic
lab=b3}
C {devices/gnd.sym} -540 -370 0 0 {name=l4
lab=GND}
C {devices/vsource.sym} -420 -400 0 0 {name=Vb4
value='vdd*(floor(code/16)-2*floor(code/32))'}
C {devices/lab_pin.sym} -420 -430 0 1 {name=p5
sig_type=std_logic
lab=b4}
C {devices/gnd.sym} -420 -370 0 0 {name=l5
lab=GND}
C {devices/vsource.sym} -300 -400 0 0 {name=Vb5
value='vdd*(floor(code/32)-2*floor(code/64))'}
C {devices/lab_pin.sym} -300 -430 0 1 {name=p6
sig_type=std_logic
lab=b5}
C {devices/gnd.sym} -300 -370 0 0 {name=l6
lab=GND}
C {devices/vsource.sym} -180 -400 0 0 {name=Vb6
value='vdd*(floor(code/64)-2*floor(code/128))'}
C {devices/lab_pin.sym} -180 -430 0 1 {name=p7
sig_type=std_logic
lab=b6}
C {devices/gnd.sym} -180 -370 0 0 {name=l7
lab=GND}
C {devices/vsource.sym} -60 -400 0 0 {name=Vb7
value='vdd*(floor(code/128)-2*floor(code/256))'}
C {devices/lab_pin.sym} -60 -430 0 1 {name=p8
sig_type=std_logic
lab=b7}
C {devices/gnd.sym} -60 -370 0 0 {name=l8
lab=GND}
C {r2r.sym} -300 -100 0 0 {name=x1}
C {devices/lab_pin.sym} -200 -240 0 1 {name=p9
sig_type=std_logic
lab=out}
C {devices/gnd.sym} -350 90 0 0 {name=l9
lab=GND}
C {devices/lab_pin.sym} -400 -240 0 0 {name=p10
sig_type=std_logic
lab=b0}
C {devices/lab_pin.sym} -400 -200 0 0 {name=p11
sig_type=std_logic
lab=b1}
C {devices/lab_pin.sym} -400 -160 0 0 {name=p12
sig_type=std_logic
lab=b2}
C {devices/lab_pin.sym} -400 -120 0 0 {name=p13
sig_type=std_logic
lab=b3}
C {devices/lab_pin.sym} -400 -80 0 0 {name=p14
sig_type=std_logic
lab=b4}
C {devices/lab_pin.sym} -400 -40 0 0 {name=p15
sig_type=std_logic
lab=b5}
C {devices/lab_pin.sym} -400 0 0 0 {name=p16
sig_type=std_logic
lab=b6}
C {devices/lab_pin.sym} -400 40 0 0 {name=p17
sig_type=std_logic
lab=b7}
C {devices/isource.sym} 0 -100 0 0 {name=Iout
value=0}
C {devices/gnd.sym} 0 -130 0 0 {name=l10
lab=GND}
C {devices/lab_pin.sym} 0 -70 0 1 {name=p18
sig_type=std_logic
lab=out}
C {devices/code.sym} -1000 100 0 0 {name=SIMULATION
only_toplevel=false
value="
.param code=0 vdd=1.8
.control
echo code out_V ideal_V
foreach c 0 1 85 128 135 255
  alterparam code = $c
  reset
  op
  let ideal = $c / 256 * 1.8
  echo RESULT code $c out $&v(out) ideal $&ideal
  destroy all
end
* output resistance at code 135: 1 uA into out
alterparam code = 135
reset
op
let v0 = v(out)
set v0s = $&v0
destroy all
alter @iout[dc] = 1u
op
let rout = (v(out) - $v0s) / 1u
echo RESULT rout_ohm $&rout
destroy all
alter @iout[dc] = 0
* VDD sensitivity at code 135, relative to VDD/2 (what the trim pair sees)
alterparam vdd = 1.81
reset
op
let d = (v(out) - 0.905) - ($v0s - 0.9)
let s = d / 0.01
echo RESULT dtrim_minus_dvdd2_per_dvdd $&s
.endc
"
spice_ignore=false}
