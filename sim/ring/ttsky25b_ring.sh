#!/bin/bash
# Re-simulate the measured ttsky25b/tt08 ring 1 (18 x inv_2 + nand2_2, extracted
# layout ring.sim.spice + its driver + pad_model) across corner, VDD and
# temperature, to explain 600 MHz predicted vs 518 MHz measured. (VDD is
# good on the demoboards, so 1.8 V; the loop can take more values.)
# Run in the osic image from build/:  ../sim/ring/ttsky25b_ring.sh
SRC=/foss/designs/shuttle-tt08/tt08-analog-ring-osc
# the original deck: keep the extracted ring (x4), its driver (x5) and pad (x3)
deck() {
  sed -n '1,/^\.lib/p' $SRC/xschem/simulation/tb_ring.spice | grep -v '^\.lib' \
    | grep -E '^(\*\*|V10|V1 |x3 |x4 |x5 |\.subckt|\.ends)' > /dev/null
  echo "* ttsky25b ring 1, extracted: corner $1"
  echo "V10 vdd GND 'vdd'"
  echo "V1 enable GND 'vdd'"
  echo "x3 GND out_parax ring_out_parax pad_model"
  echo "x4 enable pre_drive_parax vdd GND ring_parax"
  echo "x5 vdd GND pre_drive_parax ring_out_parax driver"
  echo ".lib /foss/pdks/sky130A/libs.tech/combined/sky130.lib.spice $1"
  echo ".include /foss/pdks/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice"
  echo ".include $SRC/mag/ring.sim.spice"
  # driver + pad_model subckts from the original netlist
  awk '/^\.subckt (driver|pad_model)/,/^\.ends/' $SRC/xschem/simulation/tb_ring.spice
  echo ".param vdd=1.8"
  echo ".save v(pre_drive_parax) v(out_parax)"
  echo ".options method=GEAR"
  echo ".control"
  echo "echo corner VDD temp f_MHz"
  echo "foreach t 27 45 60"
  echo "  foreach v 1.8"
  echo "    alterparam vdd = \$v"
  echo "    reset"
  echo "    option temp = \$t"
  echo "    tran 2p 40n 10n uic"
  echo "    meas tran t1 when v(pre_drive_parax)=0.9 rise=3"
  echo "    meas tran t2 when v(pre_drive_parax)=0.9 rise=13"
  echo "    let f = 10 / (t2 - t1) / 1e6"
  echo "    echo $1 \$v \$t \$&f"
  echo "    destroy all"
  echo "  end"
  echo "end"
  echo ".endc"
  echo ".end"
}
for c in ${CORNERS:-tt ss ff sf fs}; do deck $c > ring_$c.spice; done
printf '%s\n' ${CORNERS:-tt ss ff sf fs} | xargs -P 1 -I{} sh -c 'ngspice -b ring_{}.spice > ring_{}.log 2>&1; grep -E "^(tt|ss|ff|sf|fs) " ring_{}.log'
