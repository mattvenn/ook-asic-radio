#!/bin/bash
# Equivalence check of the digital macro: RTL vs the shipped netlist (eqy).
#   tools/osic bash formal/eqy/run.sh            the check on nl.v, then the planted-bug self-test
#   tools/osic bash formal/eqy/run.sh check      only the check
# Work dirs and logs in build/eqy/. docs/verification.md "Equivalence (eqy)".
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
HERE=$ROOT/formal/eqy
B=$ROOT/build/eqy
CELLS=$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/verilog
# the image's /foss/tools/bin/eqy is a symlink, and eqy looks for its Yosys plugins
# (eqy_combine.so, ...) relative to its own path: call it by its real path
EQY=${EQY:-$(readlink -f "$(command -v eqy)")}

mkdir -p "$B/in"
cd "$B"
ln -sfn "$ROOT/verilog/rtl" rtl
cp "$CELLS/sky130_fd_sc_hd.v" "$HERE"/{udp.v,icg_bb.v,gold.ys,gate.ys} in/

# match only ports, flop outputs and the clock gates (match.py)
# one eqy run: name, gate netlist
run() {
    local name=$1 net=$2
    cp "$net" gate.v
    yosys -q -l "$name.prepass.log" -p "script in/gold.ys; write_json gold.json; design -reset; script in/gate.ys; write_json gate.json"
    { cat "$HERE/radio_digital.eqy"; echo; python3 "$HERE/match.py" gold.json gate.json; } > radio_digital.eqy
    local t0=$(date +%s)
    "$EQY" -f -j "${JOBS:-4}" -d "$name" radio_digital.eqy > "$name.log" 2>&1 || true
    local r=$(grep -o "DONE ([A-Z]*" "$name.log" | tail -1 | cut -c7-)
    local np=$(grep -c "" "$name/partition.list" 2>/dev/null || echo 0)
    local nf=$(grep -c "Failed to prove equivalence of partition" "$name.log" || true)
    echo "$name: ${r:-ERROR}, $((np - nf))/$np partitions proven, $(( $(date +%s) - t0 )) s ($B/$name.log)"
    grep "Failed to prove equivalence of partition" "$name.log" | sed 's/.*partition /  not proven: /' || true
}

run nl "$ROOT/macros/radio_digital/radio_digital.nl.v"
