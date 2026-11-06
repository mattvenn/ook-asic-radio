#!/bin/bash
# KLayout LVS (kpex's sky130 deck) of the flattened lna_chain, with device combining
# (parallel fingers), so the extracted netlist matches the flat schematic. Run in osic.
W=$(cd "$(dirname "$0")" && pwd)
klayout -b -r /usr/local/lib/python3.12/dist-packages/klayout_pex/pdk/sky130A/libs.tech/kpex/sky130.lvs \
  -rd input=$W/lna_chain_flat.gds -rd report=$W/lvs/lna_chain.lvsdb.gz -rd schematic=$W/lna_chain_flat_ref.spice \
  -rd target_netlist=$W/lvs/lna_chain_extracted.cir -rd thr=6 -rd run_mode=deep -rd spice_net_names=true \
  -rd spice_comments=false -rd scale=false -rd verbose=false -rd schematic_simplify=true -rd net_only=false \
  -rd top_lvl_pins=true -rd combine=true -rd purge=${PURGE:-false} -rd purge_nets=false > $W/lvs/lvs.log 2>&1
tail -2 $W/lvs/lvs.log
