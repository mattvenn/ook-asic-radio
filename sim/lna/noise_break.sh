#!/bin/bash
# Per-device noise at 433.92 MHz at the stage-1 diff output of tb_lna_<kind>.
# Run inside the osic image from build/; prints raw onoise_* lines (V/rtHz).
for k in "$@"; do
  sed -e '/^\.control/,/^\.endc/c\
.control\
noise v(o1p,o1n) vant_p lin 1 433.92e6 433.92e6 1\
print all\
.endc' tb_lna_$k.spice > /tmp/nb_$k.spice
  echo "=== $k"
  ngspice -b /tmp/nb_$k.spice 2>&1 | grep -E "^onoise"
done
