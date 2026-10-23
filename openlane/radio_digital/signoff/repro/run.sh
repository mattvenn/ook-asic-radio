#!/bin/bash
# Signoff of the shipped macro (macros/radio_digital/) with LibreLane's own steps,
# without re-hardening (a re-harden doesn't reproduce the same layout, see ../README.md).
# From the repo root:  tools/osic bash openlane/radio_digital/signoff/repro/run.sh
# Work dir: openlane/radio_digital/runs/signoff_check (git-ignored). ~1 min.
set -e
REPO=$(cd "$(dirname "$0")/../../../.." && pwd)
HERE=$REPO/openlane/radio_digital/signoff/repro
MAC=$REPO/macros/radio_digital
W=$REPO/openlane/radio_digital/runs/signoff_check
rm -rf "$W" && mkdir -p "$W" && cd "$W"

# OpenROAD database from the shipped DEF
MAC=$MAC openroad -exit -no_splash "$HERE/mkodb.tcl"

# input states: the shipped views, LibreLane's SDC from the harden
python3 - "$MAC" "$W" "$HERE" <<'E'
import json, sys
mac, w, here = sys.argv[1:]
base = {'odb': f'{w}/radio_digital.odb', 'def': f'{mac}/radio_digital.def',
        'nl': f'{mac}/radio_digital.nl.v', 'pnl': f'{mac}/radio_digital.pnl.v',
        'sdc': f'{here}/radio_digital.sdc', 'metrics': {}}
json.dump(base, open('state_sta.json', 'w'), indent=1)
g = f'{mac}/radio_digital.gds'
json.dump(dict(base, gds=g, mag_gds=g, klayout_gds=g), open('state_sign.json', 'w'), indent=1)
E

run() { python3 -m librelane.steps run --condensed --hide-progress-bar "$@"; }
run -o rcx -c "$HERE/rcx.json" -i state_sta.json
run -o sta -c "$HERE/sta.json" -i rcx/state_out.json
run -o drc -c "$HERE/drc.json" -i state_sign.json
run -o ext -c "$HERE/ext.json" -i state_sign.json      # MAGIC_EXT_USE_GDS: extract the GDS, not the DEF
run -o lvs -c "$HERE/lvs.json" -i ext/state_out.json

echo; cat sta/summary.rpt
grep COUNT drc/reports/drc.magic.rpt
grep 'Final result' lvs/reports/lvs.netgen.rpt
