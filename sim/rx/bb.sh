#!/bin/bash
# Baseband half of the whole-RX transient for each level (needs
# build/det_<level>.inc from sim/rx/gen_det.py). Run in the osic image from
# build/:  ../sim/rx/bb.sh -94 -70      -> build/rx_bb_<level>.raw, .log
for lvl in "$@"; do
  sed -e "s/^\.include det.inc/.include det_$lvl.inc/" -e "s/^write tb_rx_bb.raw/write rx_bb_$lvl.raw/" \
      tb_rx_bb.spice > rx_bb_$lvl.spice
  ngspice -b rx_bb_$lvl.spice > rx_bb_$lvl.log 2>&1
  echo "$lvl dBm: $(grep -ci error rx_bb_$lvl.log) errors"
done
