#!/bin/bash
# New TX ring sizing with the calibrated schematic model: nand2_2 enable + N
# sky130_fd_sc_hd__inv_2, 3.2 fF wiring per stage (matches the ttsky25b ring's
# extracted 598 MHz at N=18), loaded by the ttsky25b driver + pad_model.
# Target: ~500 MHz here (= extracted tt) -> ~433 MHz on silicon (x0.866).
# Run in the osic image from build/tx/:  ../../sim/ring/ring_stages.sh
SRC=/foss/designs/shuttle-tt08/tt08-analog-ring-osc
for n in 18 20 22 24; do
{
  echo "* ring: nand2 + $n inv_2, cw = 3.2 fF"
  echo "V10 vdd GND 1.8"
  echo "V1 enable GND 1.8"
  echo "x10 GND out ring_out pad_model"
  echo "x1 vdd GND enable pre_drive ringn"
  echo "x2 vdd GND pre_drive ring_out driver"
  echo ".lib /foss/pdks/sky130A/libs.tech/combined/sky130.lib.spice tt"
  echo ".include /foss/pdks/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice"
  awk '/^\.subckt (driver|pad_model|inverter) /,/^\.ends/' $SRC/xschem/simulation/tb_ring.spice \
    | sed "s/^C6 in VSS 10fF m=1/C6 in VSS 3.2f m=1/"
  echo ".subckt ringn VDD VSS enable out"
  echo "x0 enable n$n VSS VSS VDD VDD out sky130_fd_sc_hd__nand2_2"
  prev=out
  for i in $(seq 1 $n); do echo "xi$i VDD VSS $prev n$i inverter"; prev=n$i; done
  echo ".ends"
  echo ".save v(pre_drive)"
  echo ".options method=GEAR"
  echo ".control"
  echo "tran 2p 80n 10n uic"
  echo "meas tran t1 when v(pre_drive)=0.9 rise=3"
  echo "meas tran t2 when v(pre_drive)=0.9 rise=13"
  echo "let f = 10 / (t2 - t1) / 1e6"
  echo "echo RESULT inverters $n stages $((n+1)) f_MHz \$&f"
  echo ".endc"
  echo ".end"
} > ringn_$n.spice
ngspice -b ringn_$n.spice > ringn_$n.log 2>&1; grep RESULT ringn_$n.log || grep -i error ringn_$n.log | head -3
done
