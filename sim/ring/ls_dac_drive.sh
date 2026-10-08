#!/bin/bash
# Can the R2R DAC's 1.8 -> 3.3 V level shifter (tt08-analog-r2r-dac-3v3
# dac_drive: thick-oxide cross-coupled core W 0.42 / L 0.5, buffers) pass a
# 433.92 MHz square wave? Core + buffers scaled by k; output loaded with
# 0.3 pF (~gate of the TX's big thick-oxide driver). tt, 1.8 / 3.3 V.
# Run in the osic image from build/tx/:  ../../sim/ring/ls_dac_drive.sh
for k in 1 4 10 20; do
cat > ls_$k.spice <<SP
* dac_drive scaled x$k at 433.92 MHz
.lib /foss/pdks/sky130A/libs.tech/combined/sky130.lib.spice tt
.param k=$k
VA VAPWR 0 3.3
VD VDPWR 0 1.8
Vin ctrl 0 pulse(0 1.8 0.5n 80p 80p 1.072n 2.3046n)
.subckt dac_drive VAPWR VDPWR ctrl out VGND
XM8 ctrl_n ctrl VDPWR VDPWR sky130_fd_pr__pfet_01v8_hvt L=0.15 W='1*k' nf=1
XM7 ctrl_n ctrl VGND VGND sky130_fd_pr__nfet_01v8 L=0.15 W='0.42*k' nf=1
XM11 m9m11 m10m12 VAPWR VAPWR sky130_fd_pr__pfet_g5v0d10v5 L=0.5 W='0.42*k' nf=1
XM9 m9m11 ctrl VGND VGND sky130_fd_pr__nfet_g5v0d10v5 L=0.5 W='0.42*k' nf=1
XM10 m10m12 ctrl_n VGND VGND sky130_fd_pr__nfet_g5v0d10v5 L=0.5 W='0.42*k' nf=1
XM12 m10m12 m9m11 VAPWR VAPWR sky130_fd_pr__pfet_g5v0d10v5 L=0.5 W='0.42*k' nf=1
XM1 out_drive m10m12 VAPWR VAPWR sky130_fd_pr__pfet_g5v0d10v5 L=0.5 W='0.84*k' nf=1
XM2 out_drive m10m12 VGND VGND sky130_fd_pr__nfet_g5v0d10v5 L=0.5 W='0.42*k' nf=1
XM3 out out_drive VAPWR VAPWR sky130_fd_pr__pfet_g5v0d10v5 L=0.5 W=9 nf=3
XM4 out out_drive VGND VGND sky130_fd_pr__nfet_g5v0d10v5 L=0.5 W=3 nf=1
.ends
x1 VAPWR VDPWR ctrl out 0 dac_drive
Cl out 0 0.3p
.save v(ctrl) v(out) v(x1.m10m12) v(x1.out_drive) i(VA)
.options method=GEAR
.control
tran 5p 30n
meas tran vmax max v(out) from=20n to=30n
meas tran vmin min v(out) from=20n to=30n
meas tran vcmax max v(x1.m10m12) from=20n to=30n
meas tran vcmin min v(x1.m10m12) from=20n to=30n
meas tran td trig v(ctrl) val=0.9 rise=10 targ v(out) val=1.65 rise=10
meas tran ia avg i(VA) from=20n to=30n
let iam = -ia*1e3
echo RESULT k $k core_swing \$&vcmin \$&vcmax out_swing \$&vmin \$&vmax delay_ns \$&td IA_mA \$&iam
write ls_$k.raw
.endc
.end
SP
ngspice -b ls_$k.spice > ls_$k.log 2>&1; grep RESULT ls_$k.log || grep -i error ls_$k.log | head -3
done
