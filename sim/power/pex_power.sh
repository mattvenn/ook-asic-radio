#!/bin/bash
# RC extraction of the analog part of the tile with the TT PDN drawn in, for the power study.
# Run inside the tools image from the repo root:
#   tools/osic-mac bash -c 'CASE=A bash sim/power/pex_power.sh'      (CASE A or B: sim/power/pdn.py)
# sim/power/pdn_gds.py makes the extraction copy (the tile minus the macro, as layout/pex_tile.sh,
# plus the power gates' output columns, the met5 stripes, via4s, one port per supply); then magic
# extracts it like layout/pex_tile.sh rc. Writes build/power/ext_<case>/: radio_analog_lay_raw.spice,
# .res.ext (node coordinates), ties.json (every via4 landing).
set -eu
REPO=$(pwd)
CASE=${CASE:-A}
OUT=$REPO/build/power/ext_$CASE${TOL:+_t$TOL}${NOTAP:+_n$NOTAP}${SIMP:+_s$SIMP}${THR:+_r$THR}
mkdir -p "$OUT"; cd "$OUT"
RC=$PDK_ROOT/$PDK/libs.tech/magic/sky130A.magicrc

klayout -b -rd src=$REPO/build/top/tt_um_mattvenn_radio.gds -rd pins=$REPO/build/top/pins.json \
  -rd repo=$REPO -rd case=$CASE -rd notap=${NOTAP:-1} -rd dst=$OUT/radio_analog_lay.gds -r $REPO/sim/power/pdn_gds.py > strip.log 2>&1

cat > ext.tcl <<EOF
gds read $OUT/radio_analog_lay.gds
load radio_analog_lay
flatten radio_analog_flat
load radio_analog_flat
cellname delete radio_analog_lay
cellname rename radio_analog_flat radio_analog_lay
select top cell
extract do local
extract all
ext2sim labels on
ext2sim
extresist tolerance ${TOL:-10}
extresist simplify ${SIMP:-on}
extresist threshold ${THR:-0.01}
extresist
ext2spice lvs
ext2spice cthresh 0
ext2spice extresist on
ext2spice -o radio_analog_lay_raw.spice
quit -noprompt
EOF
magic -dnull -noconsole -rcfile $RC ext.tcl > magic.log 2>&1
echo "case $CASE: landings $(grep -c '"net"' ties.json); R $(grep -c '^R' radio_analog_lay_raw.spice); ports: $(grep -i -A40 '^.subckt radio_analog_lay' radio_analog_lay_raw.spice | grep -o 'V[A-Z]*PWR\|VGND' | sort -u | tr '\n' ' ')"
