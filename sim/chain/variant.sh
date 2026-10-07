#!/bin/bash
# Run tb_chain with some .params overridden, as a named variant whose raws
# sim/chain/analyse.py can read. Run in the osic image from build/:
#   ../sim/chain/variant.sh chain_rbc2k "rbc=2k"
name=$1; params=$2
sed -e "s/tb_chain_/tb_${name}_/g" -e "/^\.control/i .param $params" tb_chain.spice > tb_$name.spice
ngspice -b tb_$name.spice 2>&1 | grep -E "^idd|rror"
