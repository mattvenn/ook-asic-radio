#!/bin/bash
# Run sim/chain/stability.sh in build/substrate/sim/<variant> for tt 27 and ss 10.
#   tools/osic-mac build/substrate/stab.sh <variant> [CASES]
cd "$(dirname "$0")/sim/$1" || exit 1
C=${2:-2n:0}
time CASES="$C" bash ../../../../sim/chain/stability.sh
time CASES="$C" CORNER=ss TEMP=10 bash ../../../../sim/chain/stability.sh
grep -h RESULT stab_*.log
