#!/bin/bash
# Complex differential AC gain (out_p - out_n per unit differential EMF) from a stability.sh deck,
# written by wrdata at 200 points per decade, 100 MHz - 2 GHz: <deck>.ac.txt (freq, re, im).
#   tools/osic-mac build/substrate/acx.sh build/substrate/sim/<v>/stab_2n_0.spice ...
for f in "$@"; do
  d=$(dirname "$f"); b=$(basename "$f" .spice)
  sed '/^\.control/,$d' "$f" > "$d/${b}_acx.spice"
  cat >> "$d/${b}_acx.spice" <<CTL
.control
set wr_singlescale
set numdgt=12
ac dec 200 100meg 2g
let gd = v(out_p) - v(out_n)
wrdata ${b}.ac.txt real(gd) imag(gd)
.endc
.end
CTL
  (cd "$d" && ngspice -b ${b}_acx.spice > ${b}_acx.log 2>&1; echo "$f: $(wc -l < ${b}.ac.txt) points")
done
