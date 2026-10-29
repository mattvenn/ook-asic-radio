#!/bin/bash
# AC-only comparison for one substrate network: full, cut (late<->input links removed), cutall.
#   tools/osic-mac build/substrate/acvar.sh <Y run> <gscale> <tag>
# Decks are case a's stability.sh decks (sim/a) with the lna_chain subckt swapped.
cd "$(dirname "$0")"; Y=$1; G=$2; T=$3
mkdir -p sim/v_$T
for k in full cut cutall; do
  opt=""; [ $k = cut ] && opt=--cut; [ $k = cutall ] && opt=--cutall
  venv/bin/python mknet.py --case b --Y $Y --gscale $G $opt --out sim/v_$T/net_$k.spice > /dev/null
  for c in "" _ss_10; do python3 swap.py sim/a/stab_2n_0$c.spice sim/v_$T/net_$k.spice sim/v_$T/${k}$c.spice; done
done
cp sim/a/decap_vdpwr.spice sim/v_$T/
for k in full cut cutall; do echo sim/v_$T/$k.spice sim/v_$T/${k}_ss_10.spice; done | xargs ./acx.sh > /dev/null
cd sim
for c in "" _ss_10; do
  for r in cut cutall; do
    echo "== $T ($Y x$G) corner ${c:-_tt} ref=$r"
    python3 ../cmp.py v_$T/$r$c.ac.txt a/stab_2n_0$c.ac.txt a/stab_2n_0.01f$c.ac.txt 0.01 v_$T/full$c.ac.txt | grep -v "\.ac\.txt"
  done
done
