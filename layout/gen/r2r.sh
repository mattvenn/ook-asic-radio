#!/bin/bash
# r2r: the 8-bit R-2R trim DAC, reused from tt08-analog-r2r-dac-3v3 (its measured layout).
# The magic sources are copied unchanged into layout/src/r2r/ (r2r.mag + start/bit/end
# modules + the res_high_po_1p41 L 45 unit); this writes layout/r2r.gds from them.
# xschem/r2r.sch matches the layout device for device (STATUS, "Trim DAC").
# Run: tools/osic bash layout/gen/r2r.sh
set -eu
REPO=$(pwd)
cd layout/src/r2r
magic -dnull -noconsole -rcfile $PDK_ROOT/$PDK/libs.tech/magic/sky130A.magicrc > "$REPO/build/r2r_gds.log" 2>&1 <<EOF2
load r2r
select top cell
gds write $REPO/layout/r2r.gds
quit -noprompt
EOF2
echo "wrote layout/r2r.gds"
