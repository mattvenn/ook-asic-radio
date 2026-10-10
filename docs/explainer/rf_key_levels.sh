#!/bin/bash
# The keyed-carrier detector run (sim/rx/rf.sh rx_rf_key, -60 dBm) at more input levels, for the
# explainer's log_det page: build/rx_rf_key_<level>.raw. Needs build/rx_rf_key.spice from sim/rx/rf.sh.
# From the repo root:  tools/osic-mac docs/explainer/rf_key_levels.sh -100 -90 -80 -70 -50 -40 -30
cd build
for lvl in "$@"; do
  ve=$(python3 -c "import math; print(math.sqrt(8*73*1e-3*10**($lvl/10)))")   # same antenna EMF formula as rf.sh
  sed -e "s/^alterparam vemf=.*/alterparam vemf=$ve/" -e "s/^write rx_rf_key.raw/write rx_rf_key_$lvl.raw/" rx_rf_key.spice > rx_rf_key_$lvl.spice
  (ngspice -b rx_rf_key_$lvl.spice > rx_rf_key_$lvl.log 2>&1; echo "$lvl dBm: $(grep -ci error rx_rf_key_$lvl.log) errors") &
done
wait
