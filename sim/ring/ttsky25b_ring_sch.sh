#!/bin/bash
# Old ring 1 at schematic level (ring subckt: nand2_2 + 18 inverters of the
# 'inverter' subckt) with its driver + pad_model, tt, 1.8 V: gives the
# schematic -> extracted ratio for the new ring (extracted tt = 598 MHz).
# Sweeps the per-stage wiring cap 'cw' (the original schematic used 10 fF).
# Run in the osic image from build/tx/:  ../../sim/ring/ttsky25b_ring_sch.sh
SRC=/foss/designs/shuttle-tt08/tt08-analog-ring-osc
{
  echo "* ttsky25b ring 1, schematic"
  echo "V10 vdd GND 1.8"
  echo "V1 enable GND 1.8"
  echo "x10 GND out ring_out pad_model"
  echo "x1 vdd GND enable pre_drive ring"
  echo "x2 vdd GND pre_drive ring_out driver"
  echo ".lib /foss/pdks/sky130A/libs.tech/combined/sky130.lib.spice tt"
  echo ".include /foss/pdks/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice"
  awk '/^\.subckt (driver|pad_model|ring|inverter) /,/^\.ends/' $SRC/xschem/simulation/tb_ring.spice \
    | sed "s/^C6 in VSS 10fF m=1/C6 in VSS 'cw' m=1/"
  echo ".param cw=10f"
  echo ".save v(pre_drive)"
  echo ".options method=GEAR"
  echo ".control"
  echo "foreach c 10f 4f 2f 1f 0.5f 0"
  echo "  alterparam cw = \$c"
  echo "  reset"
  echo "  tran 2p 120n 10n uic"
  echo "  meas tran t1 when v(pre_drive)=0.9 rise=3"
  echo "  meas tran t2 when v(pre_drive)=0.9 rise=13"
  echo "  let f = 10 / (t2 - t1) / 1e6"
  echo "  echo RESULT schematic tt cw \$c f_MHz \$&f"
  echo "  destroy all"
  echo "end"
  echo ".endc"
  echo ".end"
} > ring_sch.spice
ngspice -b ring_sch.spice > ring_sch.log 2>&1; grep RESULT ring_sch.log || tail -20 ring_sch.log
