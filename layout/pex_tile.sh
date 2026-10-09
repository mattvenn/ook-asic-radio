#!/bin/bash
# Extract the analog part of the tile (build/top/tt_um_mattvenn_radio.gds without the digital macro)
# as a drop-in for the schematic's radio_analog subckt, for the end-to-end decks.
# Run inside the tools image from the repo root:
#   tools/osic-mac bash layout/pex_tile.sh [lvs|c|rc]      (default lvs)
#     lvs: devices + connectivity only     c: + coupling / ground C     rc: + R (slow)
# Writes layout/pex/radio_analog_<mode>.spice: the extracted cell (radio_analog_lay) and a wrapper
# .subckt radio_analog with the schematic's port order. Work files in build/pex/tile_<mode>/.
set -eu
MODE=${1:-lvs}
REPO=$(pwd)
OUT=$REPO/build/pex/tile_$MODE
mkdir -p "$OUT" "$REPO/layout/pex"; cd "$OUT"
RC=$PDK_ROOT/$PDK/libs.tech/magic/sky130A.magicrc

# 1. the tile without the macro; the wires that ended on its pins get pins named as the
#    radio_analog ports
cat > strip.py <<'PYEOF'
import json, pya
ly = pya.Layout(); ly.read(src)
top = ly.top_cell()
for inst in list(top.each_inst()):
    if inst.cell.name == 'radio_digital':
        inst.delete()
P = json.load(open(pins))
NAME = {'comp_in': 'comp_out', 'rx_en': 'rx_en', 'sc_phi1': 'sc_phi1', 'sc_phi2': 'sc_phi2',
        'dbg_en': 'dbg_en', 'tx_en': 'tx_en', 'tx_en_n': 'tx_en_n'}
NAME.update({f'trim_out[{i}]': f'trim[{i}]' for i in range(8)})
lm, lp, lt = ly.layer(70, 20), ly.layer(70, 16), ly.layer(70, 5)
for pn, net in NAME.items():
    for lay, b in P['pins']['macro'][pn]:
        bx = pya.DBox(b[0] - 0.3, b[1], b[0] + 0.2, b[3])     # the wire end just west of the macro
        top.shapes(lm).insert(bx); top.shapes(lp).insert(bx)
        top.shapes(lt).insert(pya.DText(net, pya.DTrans(bx.center().x, bx.center().y)))
top.name = 'radio_analog_lay'
ly.cleanup()
ly.write(dst)
PYEOF
klayout -b -rd src=$REPO/build/top/tt_um_mattvenn_radio.gds -rd pins=$REPO/build/top/pins.json \
  -rd dst=$OUT/radio_analog_lay.gds -r strip.py > strip.log 2>&1

# 2. magic extraction
case $MODE in
  lvs) EXT="ext2spice lvs" ;;
  c)   EXT="ext2spice lvs
ext2spice cthresh 0" ;;
  rc)  EXT="extresist tolerance 10
extresist
ext2spice lvs
ext2spice cthresh 0
ext2spice extresist on" ;;
esac
cat > ext.tcl <<EOF
gds read $OUT/radio_analog_lay.gds
load radio_analog_lay
select top cell
extract do local
extract all
ext2sim labels on
ext2sim
$EXT
ext2spice -o radio_analog_lay_raw.spice
quit -noprompt
EOF
magic -dnull -noconsole -rcfile $RC ext.tcl > magic.log 2>&1

# 3. wrapper with the schematic's port order
python3 - <<PYEOF
import re
raw = open('radio_analog_lay_raw.spice').read()
lines = []
for ln in raw.splitlines():
    if ln.startswith('+') and lines:
        lines[-1] += ' ' + ln[1:].strip()
    else:
        lines.append(ln)
ports = None
for ln in lines:
    if ln.lower().startswith('.subckt radio_analog_lay'):
        ports = ln.split()[2:]
assert ports, 'no radio_analog_lay subckt'
sch = ['rx_en', 'tx_en', 'tx_en_n', 'dbg_en', 'sc_phi1', 'sc_phi2'] + [f'trim[{i}]' for i in range(7, -1, -1)] + \
      ['comp_out', 'tx_p', 'tx_n', 'rx_p', 'rx_n', 'dbg', 'VDPWR', 'VAPWR', 'VGND']
tile = {'tx_p': 'ua[3]', 'tx_n': 'ua[4]', 'rx_p': 'ua[0]', 'rx_n': 'ua[1]', 'dbg': 'ua[2]'}
conn = []
for p in ports:
    s = {v: k for k, v in tile.items()}.get(p, p)
    if s in sch:
        conn.append(s)
    elif p in ('VSUBS', 'VSUB') or p.startswith('VGND'):
        conn.append('VGND')
    elif p.startswith('VDPWR'):
        conn.append('VDPWR')
    elif p.startswith('VAPWR'):
        conn.append('VAPWR')
    else:
        conn.append(f'nc_{re.sub(r"[^A-Za-z0-9_]", "_", p)}')     # TT bus stubs etc.
missing = [s for s in sch if s not in conn]
with open('$REPO/layout/pex/radio_analog_$MODE.spice', 'w') as f:
    f.write('* radio_analog from the extracted tile (layout/pex_tile.sh $MODE)\n')
    f.write('\n'.join(lines) + '\n\n')
    f.write('.subckt radio_analog ' + ' '.join(sch) + '\n')
    f.write('X1 ' + ' '.join(conn) + ' radio_analog_lay\n.ends\n')
nd = sum(1 for l in lines if l[:1] in 'XxMm')
nc = sum(1 for l in lines if l[:1] in 'Cc')
nr = sum(1 for l in lines if l[:1] in 'Rr')
print(f'radio_analog_$MODE: {len(ports)} ports, {nd} X/M, {nc} C, {nr} R; missing ports: {missing}')
PYEOF
