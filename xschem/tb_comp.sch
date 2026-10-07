v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {tb_comp: comp_ct threshold vs CM, trim transfer} -1000 -760 0 0 0.6 0.6 {}
T {inn = vcm, inp = vcm + vdiff; trim = vtrim (DAC stand-in)} -1000 -710 0 0 0.3 0.3 {}
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
C {devices/vsource.sym} -700 -100 0 0 {name=Vcm
value='vcm'}
C {devices/lab_pin.sym} -700 -130 0 1 {name=p2
sig_type=std_logic
lab=inn}
C {devices/gnd.sym} -700 -70 0 0 {name=l2
lab=GND}
C {devices/vsource.sym} -500 -200 0 0 {name=Vdiff
value="dc 'vd' ac 1 pulse(0 0 1 1n 1n 1 2)"}
C {devices/lab_pin.sym} -500 -230 0 1 {name=p3
sig_type=std_logic
lab=inp}
C {devices/lab_pin.sym} -500 -170 0 1 {name=p4
sig_type=std_logic
lab=inn}
C {devices/vsource.sym} -300 -100 0 0 {name=Vtrim
value='vtrim'}
C {devices/lab_pin.sym} -300 -130 0 1 {name=p5
sig_type=std_logic
lab=trim}
C {devices/gnd.sym} -300 -70 0 0 {name=l3
lab=GND}
C {devices/isource.sym} -100 -300 0 0 {name=Ib
value=1u}
C {devices/lab_pin.sym} -100 -330 0 1 {name=p6
sig_type=std_logic
lab=VDD}
C {devices/lab_pin.sym} -100 -270 0 1 {name=p7
sig_type=std_logic
lab=ibias}
C {comp_ct.sym} 300 -150 0 0 {name=x1}
C {devices/lab_pin.sym} 200 -210 0 0 {name=p8
sig_type=std_logic
lab=inp}
C {devices/lab_pin.sym} 200 -170 0 0 {name=p9
sig_type=std_logic
lab=inn}
C {devices/lab_pin.sym} 200 -130 0 0 {name=p10
sig_type=std_logic
lab=trim}
C {devices/lab_pin.sym} 200 -90 0 0 {name=p11
sig_type=std_logic
lab=ibias}
C {devices/lab_pin.sym} 400 -210 0 1 {name=p12
sig_type=std_logic
lab=out}
C {devices/lab_pin.sym} 250 -260 0 0 {name=p13
sig_type=std_logic
lab=VDD}
C {devices/gnd.sym} 250 -40 0 0 {name=l4
lab=GND}
C {devices/code.sym} -1000 100 0 0 {name=SIMULATION
only_toplevel=false
value="
.param vcm=1.0 vd=0 vtrim=0.9
.options method=GEAR
.control
* threshold (offset) vs input CM, trim at mid
echo cm_V offset_mV
foreach cm 0.55 0.6 0.7 0.8 1.0 1.2 1.4 1.5 1.55 1.6
  alterparam vcm = $cm
  reset
  dc vdiff -20m 20m 0.05m
  meas dc vth when v(out)=0.9 cross=1
  let off = vth * 1e3
  echo $cm $&off
  destroy all
end
* trim transfer at CM 1.0
alterparam vcm = 1.0
echo trim_V offset_mV
foreach t 0 0.2 0.4 0.6 0.8 0.9 1.0 1.2 1.4 1.6 1.8
  alterparam vtrim = $t
  reset
  dc vdiff -30m 30m 0.05m
  meas dc vth when v(out)=0.9 cross=1
  let off = vth * 1e3
  echo $t $&off
  destroy all
end
* input-referred noise at the balance point (CM 1.0, trim mid): find vth, sit there
alterparam vtrim = 0.9
reset
dc vdiff -5m 5m 0.01m
meas dc vth when v(out)=0.9 cross=1
* keep the threshold in control variables: 'destroy all' deletes vectors
let vlo = vth - 1m
let vhi = vth + 1m
set vthv = $&vth
set vlo = $&vlo
set vhi = $&vhi
alterparam vd = $vthv
reset
destroy all
op
print v(x1.o2) v(out)
ac dec 20 1 100meg
let g = abs(v(x1.o2))
meas ac g0 find g at=1
meas ac fp when g=g0/1.414 fall=1
let g0v = g0
set g0s = $&g0v
destroy all
* totals are in the current (integrated) plot right after noise.
* Decision noise = output noise / DC gain (inoise_total integrates the
* input-referred density where the gain is tiny, so it overstates).
noise v(x1.o2) vdiff dec 20 1 100meg
let vn_in_uV = onoise_total / $g0s * 1e6
print onoise_total vn_in_uV
destroy all
* speed: +-1 mV square around the threshold (vthv), 20 kHz
alter @vdiff[pulse] = [ $vlo $vhi 10u 10n 10n 25u 50u ]
tran 10n 120u
let vdf = v(inp) - v(inn)
meas tran trise trig vdf val=$vthv rise=2 targ v(out) val=0.9 rise=2
meas tran tfall trig vdf val=$vthv fall=2 targ v(out) val=0.9 fall=2
.endc
"
spice_ignore=false}
