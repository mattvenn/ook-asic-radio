#!/bin/bash
# All substrate solves (two streams, 3 threads each). Run: tools/osic-mac build/substrate/runall.sh
cd "$(dirname "$0")"
export OMP_NUM_THREADS=3 OPENBLAS_NUM_THREADS=3
S="venv/bin/python -u solve.py"
( $S --h 1 --out h1_n300 > h1_n300.log 2>&1
  $S --h 1 --back dirichlet --T 300 --out h1_d300 > h1_d300.log 2>&1
  $S --h 1 --back dirichlet --T 150 --out h1_d150 > h1_d150.log 2>&1
  $S --h 1 --rho 15 --out h1_n300_r15 > h1_n300_r15.log 2>&1
  $S --h 1 --rho 35 --out h1_n300_r35 > h1_n300_r35.log 2>&1
  $S --h 1 --drop_taps moat --out h1_n300_nomoat > h1_n300_nomoat.log 2>&1 ) &
( $S --h 0.5 --out h05_n300 > h05_n300.log 2>&1 ) &
wait
