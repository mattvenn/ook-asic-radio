v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {tb_dbg: det (8k || 5p source) -> dbg_tg -> pad_model -> ua[4] pin <- Vext (50 ohm)} -1000 -760 0 0 0.5 0.5 {}
T {ven = 0 (normal) / 1.8 (debug); results: RESULT lines in the log} -1000 -710 0 0 0.3 0.3 {}
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
C {devices/vsource.sym} -700 -450 0 0 {name=Ven
value='ven'}
C {devices/lab_pin.sym} -700 -480 0 1 {name=p2
sig_type=std_logic
lab=en}
C {devices/gnd.sym} -700 -420 0 0 {name=l2
lab=GND}
C {devices/vsource.sym} -900 -100 0 0 {name=Vdet
value="dc 'vdet' ac 0"}
C {devices/lab_pin.sym} -900 -130 0 1 {name=p3
sig_type=std_logic
lab=vd}
C {devices/gnd.sym} -900 -70 0 0 {name=l3
lab=GND}
C {devices/res.sym} -700 -150 0 0 {name=Rdet
value=8k
m=1}
C {devices/lab_pin.sym} -700 -180 0 1 {name=p4
sig_type=std_logic
lab=vd}
C {devices/lab_pin.sym} -700 -120 0 1 {name=p5
sig_type=std_logic
lab=det}
C {devices/capa.sym} -600 -50 0 0 {name=Cdet
value=5p
m=1}
C {devices/lab_pin.sym} -600 -80 0 1 {name=p6
sig_type=std_logic
lab=det}
C {devices/gnd.sym} -600 -20 0 0 {name=l4
lab=GND}
C {dbg_tg.sym} -300 -150 0 0 {name=x1}
C {devices/lab_pin.sym} -400 -170 0 0 {name=p7
sig_type=std_logic
lab=det}
C {devices/lab_pin.sym} -200 -170 0 1 {name=p8
sig_type=std_logic
lab=mod}
C {devices/lab_pin.sym} -400 -130 0 0 {name=p9
sig_type=std_logic
lab=en}
C {devices/lab_pin.sym} -350 -220 0 0 {name=p10
sig_type=std_logic
lab=VDD}
C {devices/gnd.sym} -350 -80 0 0 {name=l5
lab=GND}
C {pad_model.sym} 100 -150 0 1 {name=xpad}
C {devices/lab_pin.sym} 250 -170 0 1 {name=p11
sig_type=std_logic
lab=pin}
C {devices/lab_pin.sym} -50 -170 0 0 {name=p12
sig_type=std_logic
lab=mod}
C {devices/gnd.sym} 250 -130 0 0 {name=l6
lab=GND}
C {devices/res.sym} 400 -150 0 0 {name=Rext
value='rext'
m=1}
C {devices/lab_pin.sym} 400 -180 0 1 {name=p13
sig_type=std_logic
lab=ext}
C {devices/lab_pin.sym} 400 -120 0 1 {name=p14
sig_type=std_logic
lab=pin}
C {devices/capa.sym} 300 -50 0 0 {name=Cprobe
value=15p
m=1}
C {devices/lab_pin.sym} 300 -80 0 1 {name=p15
sig_type=std_logic
lab=pin}
C {devices/gnd.sym} 300 -20 0 0 {name=l7
lab=GND}
C {devices/vsource.sym} 500 -50 0 0 {name=Vext
value="dc 'vpin' ac 1"}
C {devices/lab_pin.sym} 500 -80 0 1 {name=p16
sig_type=std_logic
lab=ext}
C {devices/gnd.sym} 500 -20 0 0 {name=l8
lab=GND}
C {devices/code.sym} -1000 100 0 0 {name=SIMULATION
only_toplevel=false
value="
.param vdet=1.44 ven=0 vpin=0.9 rext=50
.options method=GEAR
.control
* AC from the pin source to det, switch off then on
foreach e 0 1.8
  alterparam ven = $e
  reset
  ac dec 20 1k 1g
  let g = db(v(det))
  meas ac g10k find g at=10e3
  meas ac g10m find g at=10e6
  meas ac g100m find g at=100e6
  echo RESULT ext_to_det en $e dB_10k $&g10k dB_10M $&g10m dB_100M $&g100m
  destroy all
end
* on: det -> pin bandwidth (source = Vdet) into a scope (1 Meg || 15 pF probe + cable)
alterparam ven = 1.8
alterparam rext = 1Meg
reset
alter @vext[acmag] = 0
alter @vdet[acmag] = 1
ac dec 20 1k 1g
let g = db(v(pin))
meas ac g0 find g at=1e3
let g3 = g0 - 3
meas ac f3db when g=g3 fall=1
echo RESULT det_to_pin_on dB_1k $&g0 f3dB $&f3db
destroy all
alter @vdet[acmag] = 0
alterparam rext = 50
* DC: det shift from the pad path (leakage, ESD) with the pin held at 0 / 1.8 V
foreach e 0 1.8
  foreach vp 0 1.8
    alterparam ven = $e
    alterparam vpin = $vp
    reset
    op
    let dv = (v(det) - 1.44) * 1e6
    echo RESULT dc en $e pin $vp det_shift_uV $&dv
    destroy all
  end
end
.endc
"
spice_ignore=false}
