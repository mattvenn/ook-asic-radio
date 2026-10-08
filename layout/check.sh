#!/bin/bash
# DRC (magic + klayout) and LVS (magic extract + netgen vs the xschem netlist) of
# one block's GDS. Run inside the tools image from the repo root:
#   tools/osic bash layout/check.sh tx_drv
# Results in build/lvs/<block>/: magic_drc.txt, klayout_drc.lyrdb, lvs.report
set -u
B=$1
REPO=$(pwd)
GDS=$REPO/layout/$B.gds
OUT=$REPO/build/lvs/$B
mkdir -p "$OUT"; cd "$OUT"
RC=$PDK_ROOT/$PDK/libs.tech/magic/sky130A.magicrc

# schematic netlist (top as a subckt, LVS mode)
(cd "$REPO" && xschem -n -s -q --tcl "set top_subckt 1; set lvs_netlist 1" -o "$OUT" xschem/$B.sch >/dev/null 2>&1)
[ -s $B.spice ] || { echo "no schematic netlist"; exit 1; }

# magic: DRC (full) and LVS extraction, from the GDS
cat > magic.tcl <<EOF
gds read $GDS
load $B
select top cell
drc euclidean on
drc style drc(full)
drc check
drc catchup
set n [drc list count total]
set fp [open magic_drc.txt w]
puts \$fp "count \$n"
set sc [cif scale out]
foreach {why boxes} [drc listall why] {
  set loc {}
  foreach b [lrange \$boxes 0 2] { lappend loc [lmap v \$b {format %.2f [expr {\$v * \$sc}]}] }
  puts \$fp "[llength \$boxes]  \$why   at \$loc"
}
close \$fp
extract do local
extract all
ext2spice lvs
ext2spice -o ${B}_lay.spice
quit -noprompt
EOF
magic -dnull -noconsole -rcfile $RC magic.tcl > magic.log 2>&1
echo "== magic DRC"; cat magic_drc.txt

# klayout DRC (the TT precheck uses this deck too)
klayout -b -rd input=$GDS -rd topcell=$B -rd report=$OUT/klayout_drc.lyrdb -rd feol=true -rd beol=true \
  -r $PDK_ROOT/$PDK/libs.tech/klayout/drc/sky130A_mr.drc > klayout_drc.log 2>&1
echo "== klayout DRC"
python3 - <<EOF
import xml.etree.ElementTree as ET, collections
r = ET.parse('$OUT/klayout_drc.lyrdb').getroot()
c = collections.Counter(i.findtext('category') for i in r.iter('item'))
print('count', sum(c.values()))
for k, v in c.most_common(): print(v, k)
EOF

# netgen LVS
netgen -batch lvs "${B}_lay.spice $B" "$B.spice $B" $PDK_ROOT/$PDK/libs.tech/netgen/sky130A_setup.tcl lvs.report > netgen.log 2>&1
echo "== LVS"; grep -E "Circuits match|do not match|Netlists match|Final result" lvs.report | tail -3
