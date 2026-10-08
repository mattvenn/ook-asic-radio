#!/bin/bash
# Skewed version of the dac_drive level shifter: core NMOS x kn (W 0.42*kn),
# core PMOS kept minimum (W 0.42, L 0.5), buffers as dac_drive. 0.3 pF load.
# Pass/fail at 433.92 and 600 MHz, tt; then the best at ss.
# Run in the osic image from build/tx/:  ../../sim/ring/ls_skew.sh
run() { kn=$1; f=$2; corner=$3
  per=$(python3 -c "print(1/$f)"); pw=$(python3 -c "print(0.5/$f-80e-12)")
  sed -e "s/^Vin ctrl 0 pulse.*/Vin ctrl 0 pulse(0 1.8 0.5n 80p 80p $pw $per)/" \
      -e "s/^.param k=1/.param k=1 kn=$kn/" \
      -e "s/^XM9 m9m11 ctrl VGND VGND sky130_fd_pr__nfet_g5v0d10v5 L=0.5 W='0.42\*k'/XM9 m9m11 ctrl VGND VGND sky130_fd_pr__nfet_g5v0d10v5 L=0.5 W='0.42*kn'/" \
      -e "s/^XM10 m10m12 ctrl_n VGND VGND sky130_fd_pr__nfet_g5v0d10v5 L=0.5 W='0.42\*k'/XM10 m10m12 ctrl_n VGND VGND sky130_fd_pr__nfet_g5v0d10v5 L=0.5 W='0.42*kn'/" \
      -e "s/sky130.lib.spice tt/sky130.lib.spice $corner/" \
      -e "s/^echo RESULT k 1/echo RESULT kn $kn f $f $corner/" -e "/^write/d" ls_1.spice > lss.spice
  ngspice -b lss.spice 2>&1 | grep RESULT
}
for kn in 2 4 10; do for f in 433.92e6 600e6; do run $kn $f tt; done; done
for f in 433.92e6 600e6; do run 4 $f ss; run 10 $f ss; done
