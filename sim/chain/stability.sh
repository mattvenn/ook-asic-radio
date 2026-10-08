#!/bin/bash
# Stability of the 80 dB gain chain with a real supply / ground and a little
# output -> input coupling (the RFIC-course point: at ~80 dB gain, ~0.04 fF of
# asymmetric coupling from the chain output back to its input is enough).
#
# From tb_chain (real passives):
#   - VDPWR: ideal 1.8 V -> 0.5 ohm -> L (bond wire + package + board) -> chip VDPWR;
#   - chip ground: the chain's VSS and the vcm source sit on 'gchip', returned to
#     the board ground (the antenna / pad reference) through the same L;
#   - Cdec (30 pF, the decap_vdpwr default) between chip VDPWR and gchip;
#   - Ccpl from out_p back to pad_p, or to CNODE (asymmetric, so it couples
#     differentially).
# Per case: a 1 ns, 1 uA current kick into pad_p, no signal; the output
# envelope in a late window vs an early one (growth > 1 = oscillating); and
# AC gain at 434 MHz and its peak, against the no-coupling case.
#
# Run in the osic image from build/real (after netlisting tb_chain there):
#   CASES="0:0 2n:0 5n:0 2n:0.01f 2n:0.1f 2n:1f 5n:0.1f 5n:1f" ../../sim/chain/stability.sh
# Results: RESULT lines in stab_<L>_<C>.log.
cases=${CASES:-"0:0 2n:0 5n:0 2n:0.01f 2n:0.1f 2n:1f 5n:0.1f 5n:1f"}
cdec=${CDEC:-30p}
cnode=${CNODE:-pad_p}   # where the coupling lands (e.g. o1p: stage 2 input)
corner=${CORNER:-tt}; temp=${TEMP:-27}   # e.g. CORNER=ss TEMP=10: the highest-gain case
for cs in $cases; do
  l=${cs%:*}; c=${cs#*:}
  tag=${l}_$c; [ "$cnode" != pad_p ] && tag=${tag}_$cnode
  [ "$corner/$temp" != tt/27 ] && tag=${tag}_${corner}_$temp
  f=stab_$tag.spice
  sed -e '/^\.control/,/^\.endc/d' -e '/^\.end$/d' \
      -e 's/^VDPWR VDPWR GND .*/Vsup vsup GND 1.8\nRsup vsup vs1 0.5/' \
      -e 's/^\(x1 .*\) VDPWR GND lna_chain/\1 VDPWR gchip lna_chain/' \
      -e 's/^Vcm vcm GND /Vcm vcm gchip /' \
      -e 's/^\.param vemf=.*/.param vemf=0/' \
      -e 's/^\.param vcmi=.*/.param vcmi=0 fcmi=10e6/' \
      -e "s/\(sky130\.lib\.spice\) tt/\1 $corner/" \
      tb_chain.spice > $f
  echo ".temp $temp" >> $f
  if [ "$l" = 0 ]; then
    echo "Lsup vs1 VDPWR 1p" >> $f; echo "Rgnd gchip GND 1m" >> $f
  else
    echo "Lsup vs1 VDPWR $l" >> $f; echo "Lgnd gchip GND $l" >> $f
  fi
  echo "Cdec VDPWR gchip $cdec" >> $f
  [ "$c" != 0 ] && echo "Ccpl out_p $cnode $c" >> $f
  cat >> $f <<CTL
Ikick GND pad_p pulse(0 1u 5n 0.1n 0.1n 1n 1)
.save v(out_p) v(out_n) v(pad_p) v(VDPWR) v(gchip)
.options method=GEAR
.control
tran 20p 300n 0
let d = v(out_p) - v(out_n)
meas tran early pp d from=5n to=25n
meas tran late pp d from=250n to=300n
let growth = late / early
meas tran vdd_pp pp v(VDPWR) from=20n to=300n
echo RESULT kick L $l C $c early_pp \$&early late_pp \$&late growth \$&growth vdd_pp \$&vdd_pp
destroy all
reset
ac dec 50 100meg 2g
let g = db(v(out_p) - v(out_n))
meas ac g434 find g at=433.92e6
meas ac gpk max g
meas ac fpk when g=gpk
echo RESULT ac L $l C $c gain434_dB \$&g434 peak_dB \$&gpk peak_at \$&fpk
.endc
.end
CTL
  ngspice -b $f > stab_$tag.log 2>&1
  echo "$cs $cnode: $(grep -c RESULT stab_$tag.log) results"
done
