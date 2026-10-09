#!/bin/bash
# Top-level checks of the tile GDS (layout/gen/top.py). Run inside the tools image from the repo root:
#   tools/osic-mac bash layout/check_top.sh [stage ...]     stages: klayout magic antenna lvs precheck
# (default: all). Results in build/lvs/top/.
set -u
REPO=$(pwd)
B=tt_um_mattvenn_radio
GDS=$REPO/build/top/$B.gds
OUT=$REPO/build/lvs/top
mkdir -p "$OUT"; cd "$OUT"
RC=$PDK_ROOT/$PDK/libs.tech/magic/sky130A.magicrc
STAGES=${*:-klayout magic antenna lvs precheck}
has() { [[ " $STAGES " == *" $1 "* ]]; }

if has precheck; then
  # TT analog rules we can check here: no met5; power pins met4, >= 1.2 um wide, within 10 um of
  # the bottom and the top edges, not touching each other
  cat > precheck.py <<'PYEOF'
import pya
ly = pya.Layout(); ly.read(gds); top = ly.top_cell(); H = top.dbbox().height()
bad = 0
for dt in (20, 16, 5, 44):
    li = ly.find_layer(72, dt)
    if li is not None and not pya.Region(top.begin_shapes_rec(li)).is_empty():
        print('FAIL met5 shapes on 72/%d' % dt); bad += 1
pins = {}
li, lt = ly.find_layer(71, 16), ly.find_layer(71, 5)
texts = [s.dtext for s in top.shapes(lt).each() if s.is_text()]
for s in top.shapes(li).each():
    b = s.dbbox()
    n = [t.string for t in texts if b.contains(t.trans.disp.to_p())]
    if n and n[0] in ('VDPWR', 'VGND', 'VAPWR'):
        ok = b.width() >= 1.2 - 1e-6 and b.bottom <= 10 and b.top >= H - 10
        print('%-5s %-6s x %.2f-%.2f y %.2f-%.2f' % ('ok' if ok else 'FAIL', n[0], b.left, b.right, b.bottom, b.top))
        bad += not ok
        pins.setdefault(n[0], []).append(b)
allp = [b for v in pins.values() for b in v]
for i in range(len(allp)):
    for j in range(i + 1, len(allp)):
        if allp[i].enlarged(0.001, 0.001).overlaps(allp[j]):
            print('FAIL power pins touch', allp[i], allp[j]); bad += 1
print('precheck', 'PASS' if not bad else 'FAIL %d' % bad)
PYEOF
  echo "== precheck"; klayout -b -rd gds=$GDS -r precheck.py 2>/dev/null | grep -v "^Loaded"
fi

if has klayout; then
  klayout -b -rd input=$GDS -rd topcell=$B -rd report=$OUT/klayout_drc.lyrdb -rd feol=true -rd beol=true \
    -rd thr=8 -r $PDK_ROOT/$PDK/libs.tech/klayout/drc/sky130A_mr.drc > klayout_drc.log 2>&1
  echo "== klayout DRC"
  python3 - <<EOF
import xml.etree.ElementTree as ET, collections
r = ET.parse('$OUT/klayout_drc.lyrdb').getroot()
c = collections.Counter(i.findtext('category') for i in r.iter('item'))
print('count', sum(c.values()))
for k, v in c.most_common(): print(v, k)
EOF
fi

if has magic || has lvs; then
  # magic: DRC (full) and the LVS extraction, from the GDS
  DO_DRC=0; has magic && DO_DRC=1
  DO_EXT=0; has lvs && DO_EXT=1
  cat > magic.tcl <<EOF
gds read $GDS
load $B
select top cell
if {$DO_DRC} {
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
}
if {$DO_EXT} {
  extract do local
  extract all
  ext2spice lvs
  ext2spice -o ${B}_lay.spice
}
quit -noprompt
EOF
  magic -dnull -noconsole -rcfile $RC magic.tcl > magic.log 2>&1
  has magic && { echo "== magic DRC"; cat magic_drc.txt; }
fi

if has antenna; then
  mkdir -p ant
  cat > ant/ant.tcl <<EOF
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
  sed -n '/ANTENNA_BEGIN/,/ANTENNA_END/p' antenna.log > antenna.txt
  echo "== antenna (magic): count $(grep -c 'Antenna violation' antenna.txt)"
  grep -A1 'Antenna violation' antenna.txt | head -12
fi

if has lvs; then
  (cd "$REPO" && xschem -n -s -q --tcl "set top_subckt 1; set lvs_netlist 1" -o "$OUT" xschem/$B.sch >/dev/null 2>&1)
  (cd "$REPO" && python3 layout/lvs_top_src.py)
  SETUP=$PDK_ROOT/$PDK/libs.tech/netgen/sky130A_setup.tcl
  cat > lvs.tcl <<EOF
set lay [readnet spice ${B}_lay.spice]
set sch [readnet spice $PDK_ROOT/$PDK/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice]
readnet verilog $REPO/macros/radio_digital/radio_digital.pnl.v \$sch
readnet spice ${B}_src.spice \$sch
lvs "\$lay $B" "\$sch $B" $SETUP lvs.report
EOF
  netgen -batch source lvs.tcl > netgen.log 2>&1
  echo "== LVS"; grep -E "Circuits match|do not match|Netlists match|Final result" lvs.report | tail -3
fi
