#!/bin/bash
# Parasitic extraction (R + C) of one block's GDS with magic, for simulation.
# Run inside the tools image from the repo root:
#   tools/osic bash layout/pex.sh tx_drv
# Writes layout/pex/<block>.spice: .subckt <block> with the schematic's port
# order (instances connect by position), the substrate tied to VSS.
# Work files in build/pex/<block>/.
set -eu
B=$1
REPO=$(pwd)
GDS=$REPO/layout/$B.gds
OUT=$REPO/build/pex/$B
mkdir -p "$OUT" "$REPO/layout/pex"; cd "$OUT"
RC=$PDK_ROOT/$PDK/libs.tech/magic/sky130A.magicrc

# schematic netlist, for the port order
(cd "$REPO" && xschem -n -s -q --tcl "set top_subckt 1; set lvs_netlist 1" -o "$OUT" xschem/$B.sch >/dev/null 2>&1)

cat > pex.tcl <<EOF
gds read $GDS
load $B
flatten ${B}_flat
load ${B}_flat
cellname delete $B
cellname rename ${B}_flat $B
select top cell
extract do local
extract all
ext2sim labels on
ext2sim
extresist tolerance 10
extresist
ext2spice lvs
ext2spice cthresh 0
ext2spice extresist on
ext2spice -o ${B}_raw.spice
quit -noprompt
EOF
magic -dnull -noconsole -rcfile $RC pex.tcl > magic.log 2>&1
python3 "$REPO/layout/pexfix.py" ${B}_raw.spice $B.spice "$REPO/layout/pex/$B.spice"
