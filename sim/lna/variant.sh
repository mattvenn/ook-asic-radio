#!/bin/bash
# Run a testbench with some .params overridden, as a named variant whose raws
# analyse.py can read. Run in the osic image from build/:
#   ../sim/lna/variant.sh dp dp_1m2 "w_dp=80 rl_dp=1k ibias_dp=120u wt_dp=12"
base=$1; name=$2; params=$3
sed -e "s/tb_lna_${base}_/tb_lna_${name}_/g" -e "/^\.control/i .param $params" \
  tb_lna_$base.spice > tb_lna_$name.spice
ngspice -b tb_lna_$name.spice 2>&1 | grep -E "^(idd|v\()|rror"
