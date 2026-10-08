#!/bin/bash
# Build build/mixed/radio_digital.so (the RTL, verilated, for an XSPICE d_cosim
# instance in ngspice). This is ngspice's vlnggen script redone in bash: in the
# image's ngspice 46 the script's shell lines get lowercased ('-Mdir' ->
# '-mdir'), which Verilator 5.048 rejects.
# Run in the osic image from the repo root:  tools/osic bash sim/mixed/build_so.sh
set -e
SRC=/foss/tools/ngspice/share/ngspice/scripts/src
OUT=build/mixed
OBJ=$OUT/radio_digital_obj_dir
RTL="sim/mixed/radio_digital_sim.v verilog/rtl/radio_digital.v verilog/rtl/rd_corr.v verilog/rtl/rd_gold.v
     verilog/rtl/rd_rx.v verilog/rtl/rd_tx.v verilog/rtl/rd_cg.v"
mkdir -p $OUT
rm -rf $OBJ $OUT/radio_digital.so
# 1. Verilog -> C++ (prefix Vlng, as the shim expects)
verilator -Wno-fatal -Mdir $OBJ --prefix Vlng --CFLAGS -fpic --cc --top-module radio_digital $RTL
# 2. port tables for the shim: VL_IN8(&clk,0,0); -> VL_DATA(8,clk,0,0)
for kind in INOUT IN OUT; do
  f=$(echo $kind | tr A-Z a-z); [ $f = inout ] && f=inouts || f=${f}puts
  echo "/* Generated code: do not edit. */" > $OBJ/$f.h
  sed -n -e "s/.*VL_${kind}\([0-9]*\)(&\([^;]*\);.*/VL_DATA(\1,\2/p" $OBJ/Vlng.h >> $OBJ/$f.h
done
# 3. compile with the ngspice shim + main, then link the shared library
verilator -Wno-fatal -Mdir $OBJ --prefix Vlng --CFLAGS -fpic --CFLAGS -I$SRC --cc --build --exe \
  --top-module radio_digital $SRC/verilator_main.cpp $SRC/verilator_shim.cpp $RTL
g++ --shared $OBJ/verilator_shim.o $OBJ/verilated.o $OBJ/verilated_threads.o $OBJ/Vlng__ALL.a \
  -pthread -lpthread -o $OUT/radio_digital.so
echo "built $OUT/radio_digital.so"
echo "inputs:";  grep VL_DATA $OBJ/inputs.h
echo "outputs:"; grep VL_DATA $OBJ/outputs.h
