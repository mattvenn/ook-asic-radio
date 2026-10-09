#!/bin/bash
# Copy the routed tile into gds/ and write its LEF into lef/ (the TT gds / precheck action reads both).
# Run inside the tools image from the repo root, after layout/gen/route.py:
#   tools/osic-mac bash layout/export_tt.sh
set -eu
B=tt_um_mattvenn_radio
mkdir -p gds lef
cp build/top/$B.gds gds/$B.gds
cat > build/top/lef.tcl <<TCL
gds read gds/$B.gds
load $B
lef write lef/$B.lef -pinonly -hide
quit -noprompt
TCL
magic -dnull -noconsole -rcfile $PDK_ROOT/$PDK/libs.tech/magic/sky130A.magicrc build/top/lef.tcl > build/top/lef.log 2>&1
# magic leaves USE off the supplies read from GDS; precheck wants USE POWER / GROUND
python3 - lef/$B.lef <<'PY'
import re, sys
p = sys.argv[1]; s = open(p).read()
for n, u in (('VDPWR', 'POWER'), ('VAPWR', 'POWER'), ('VGND', 'GROUND')):
    s = re.sub(r'(  PIN %s\n)(?!    USE)' % n, r'\1    USE %s ;\n' % u, s)
open(p, 'w').write(s)
PY
grep -A1 -E "PIN (VDPWR|VAPWR|VGND)$" lef/$B.lef
