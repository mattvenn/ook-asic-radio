#!/bin/bash
# sim/rx/rf.sh's runs (rx_rf_tone: steady tone; rx_rf_key: keyed carrier), both at -60 dBm, repeated at more input
# levels for the explainer's lna_chain / log_det pages: build/<run>_<level>.raw. Needs build/<run>.spice from sim/rx/rf.sh.
# From the repo root:  tools/osic-mac docs/explainer/rf_levels.sh rx_rf_tone -100 -90 -80 -70 -50 -40 -30
run=$1; shift
cd build
for lvl in "$@"; do
  ve=$(python3 -c "import math; print(math.sqrt(8*73*1e-3*10**($lvl/10)))")   # same antenna EMF formula as rf.sh
  sed -e "s/^alterparam vemf=.*/alterparam vemf=$ve/" -e "s/^write $run.raw/write ${run}_$lvl.raw/" $run.spice > ${run}_$lvl.spice
  (ngspice -b ${run}_$lvl.spice > ${run}_$lvl.log 2>&1; echo "$run $lvl dBm: $(grep -ci error ${run}_$lvl.log) errors") &
done
wait
