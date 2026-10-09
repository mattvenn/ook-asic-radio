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
# (a parameter variant has its reference in layout/ref/<block>.spice, written by its generator)
if [ -f "$REPO/layout/ref/$B.spice" ]; then cp "$REPO/layout/ref/$B.spice" $B.spice
else (cd "$REPO" && xschem -n -s -q --tcl "set top_subckt 1; set lvs_netlist 1" -o "$OUT" xschem/$B.sch >/dev/null 2>&1); fi
[ -s $B.spice ] || echo "(no schematic xschem/$B.sch: LVS skipped)"

# magic: DRC (full) and LVS extraction, from the GDS
cat > magic.tcl <<EOF
gds maskhints yes
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

# antenna check: its own magic session, on a flattened copy. On the hierarchy it misses
# gates inside subcells (pcells) driven by metal in the parent, and in the same session
# as the LVS extraction above it found nothing either. This setup catches a deliberate
# violation (a 0.5 x 0.42 um g5 gate on 300 um^2 of met1: ratio 1033 > 400).
mkdir -p ant
cat > ant/ant.tcl <<EOF
gds maskhints yes
gds read $GDS
load $B
flatten ${B}_flat
load ${B}_flat
select top cell
extract do local
extract all
puts "ANTENNA_BEGIN"
antennacheck debug
antennacheck
puts "FEEDBACK [feedback count]"
puts "ANTENNA_END"
quit -noprompt
EOF
(cd ant && magic -dnull -noconsole -rcfile $RC ant.tcl > ../antenna.log 2>&1)
echo "== antenna (magic)"
sed -n '/ANTENNA_BEGIN/,/ANTENNA_END/p' antenna.log > antenna.txt
# violations print only with 'debug'; each also leaves magic feedback entries
echo "count $(grep -c 'Antenna violation' antenna.txt) (feedback $(grep FEEDBACK antenna.txt | cut -d' ' -f2))"
grep -A1 'Antenna violation' antenna.txt | head -12

# metal density over the block (good neighbour: stay well under the 60 % implied by the
# PDK's 40 % min clear-area rule; TT adds fill after submission)
cat > dens.py <<'PYEOF'
import pya
ly = pya.Layout(); ly.read(gds)
top = ly.top_cell(); A = top.bbox().area()
out = []
for n, l in [('li', (67, 20)), ('m1', (68, 20)), ('m2', (69, 20)), ('m3', (70, 20)), ('m4', (71, 20))]:
    li = ly.find_layer(*l)
    a = pya.Region(top.begin_shapes_rec(li)).merged().area() if li is not None else 0
    out.append(f'{n} {100 * a / A:.0f}%' + (' <-- heavy' if a / A > 0.5 else ''))
print('== density: ' + ', '.join(out))
PYEOF
klayout -b -rd gds=$GDS -r dens.py 2>/dev/null | grep "^=="

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

# netgen LVS (blocks with std cells: the hd library goes on the schematic side)
SETUP=$PDK_ROOT/$PDK/libs.tech/netgen/sky130A_setup.tcl
if [ -s $B.spice ] && grep -q sky130_fd_sc_hd__ $B.spice; then
  cat > lvs.tcl <<EOF
set lay [readnet spice ${B}_lay.spice]
set sch [readnet spice $PDK_ROOT/$PDK/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice]
readnet spice $B.spice \$sch
lvs "\$lay $B" "\$sch $B" $SETUP lvs.report
EOF
  netgen -batch source lvs.tcl > netgen.log 2>&1
elif [ -s $B.spice ]; then
  netgen -batch lvs "${B}_lay.spice $B" "$B.spice $B" $SETUP lvs.report > netgen.log 2>&1
fi
[ -s $B.spice ] && echo "== LVS" && grep -E "Circuits match|do not match|Netlists match|Final result" lvs.report | tail -3
