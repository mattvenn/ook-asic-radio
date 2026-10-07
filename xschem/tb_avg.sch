v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
T {tb_avg: avg_sc step response with the digital sc_phi timing} -1000 -760 0 0 0.6 0.6 {}
T {13 us period (130 clk @ 10 MHz): phi1 6.1 us, 0.4 us gap, phi2 6.1 us; 10 mV step at 0.2 ms} -1000 -710 0 0 0.3 0.3 {}
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
C {devices/vsource.sym} -700 -100 0 0 {name=Vin
value="pwl(0 'vin0' 0.2m 'vin0' 0.2001m 'vin0+10m')"}
C {devices/lab_pin.sym} -700 -130 0 1 {name=p2
sig_type=std_logic
lab=in}
C {devices/gnd.sym} -700 -70 0 0 {name=l2
lab=GND}
C {devices/vsource.sym} -500 -100 0 0 {name=Vphi1
value="pulse(0 1.8 0 10n 10n 6.09u 13u)"}
C {devices/lab_pin.sym} -500 -130 0 1 {name=p3
sig_type=std_logic
lab=phi1}
C {devices/gnd.sym} -500 -70 0 0 {name=l3
lab=GND}
C {devices/vsource.sym} -300 -100 0 0 {name=Vphi2
value="pulse(0 1.8 6.5u 10n 10n 6.09u 13u)"}
C {devices/lab_pin.sym} -300 -130 0 1 {name=p4
sig_type=std_logic
lab=phi2}
C {devices/gnd.sym} -300 -70 0 0 {name=l4
lab=GND}
C {avg_sc.sym} 100 -150 0 0 {name=x1}
C {devices/lab_pin.sym} 0 -190 0 0 {name=p5
sig_type=std_logic
lab=in}
C {devices/lab_pin.sym} 200 -190 0 1 {name=p6
sig_type=std_logic
lab=out}
C {devices/lab_pin.sym} 0 -150 0 0 {name=p7
sig_type=std_logic
lab=phi1}
C {devices/lab_pin.sym} 0 -110 0 0 {name=p8
sig_type=std_logic
lab=phi2}
C {devices/lab_pin.sym} 50 -240 0 0 {name=p9
sig_type=std_logic
lab=VDD}
C {devices/gnd.sym} 50 -60 0 0 {name=l5
lab=GND}
C {devices/code.sym} -1000 100 0 0 {name=SIMULATION
only_toplevel=false
value="
.param vin0=1.4
.save v(in) v(out)
.options method=GEAR
.control
echo vin_V tau_ms offset_mV
foreach v0 0.6 1.0 1.4 1.5
  alterparam vin0 = $v0
  reset
  tran 50n 2.5m
  * offset: out - in just before the step (settled from t=0 via the .ic below)
  meas tran vo0 avg v(out) from=0.15m to=0.2m
  meas tran vi0 avg v(in) from=0.15m to=0.2m
  let off = (vo0 - vi0) * 1e3
  * tau: time from the step (0.2 ms) to 63 % of the 10 mV step
  let v63 = vo0 + 6.32m
  set v63s = $&v63
  meas tran t63 when v(out)=$v63s rise=1
  let tau = (t63 - 0.2m) * 1e3
  echo $v0 $&tau $&off
  destroy all
end
.endc
.ic v(out)='vin0' v(x1.cs)='vin0'
"
spice_ignore=false}
