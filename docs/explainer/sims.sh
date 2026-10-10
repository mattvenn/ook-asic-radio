#!/bin/bash
# Re-run the RX sims whose traces the explainer embeds (raws land in build/, gitignored).
# From the repo root:  tools/osic-mac docs/explainer/sims.sh   (tools/osic on Linux)
# TX traces come from the tile run already in build/ (tb_tile_rc_tx.raw) or sim/tx.
set -e
xschem -n -s -q -o build xschem/tb_logdet.sch
xschem -n -s -q -o build xschem/tb_rx_bb.sch
# bench/scope.py imports pyvisa (instrument driver), not needed here: stub it
mkdir -p build/explainer_stub && touch build/explainer_stub/pyvisa.py
PYTHONPATH=build/explainer_stub python3 sim/rx/gen_det.py -110 -100 -94 -90 -86 -82 -78 -74 -70
cd build
../sim/rx/rf.sh
(cd .. && docs/explainer/rf_levels.sh rx_rf_tone -110 -100 -90 -80 -70 -50 -40 -30)   # stage-by-stage tone at more levels
(cd .. && docs/explainer/rf_levels.sh rx_rf_key -110 -100 -90 -80 -70 -50 -40 -30)    # keyed detector at more levels; ~20 min
../sim/rx/bb.sh -110 -100 -94 -90 -86 -82 -78 -74 -70
# TX chain (ring, level-shifter latch a/b, drivers, dipole): build/tb_tx_ab.raw
cd ..
xschem -n -s -q -o build xschem/tb_tx.sch
cd build && ngspice -b tb_tx.spice > tb_tx.log 2>&1
