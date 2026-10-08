#!/bin/bash
# Loop gain / phase margin of the bias_gen OTA loop (xschem/gen/bias.py).
# The loop: OTA out (ota, Cc) -> Mn gate -> Mn source x (across rref) -> M2
# gate (the OTA's inverting input) -> ota. It is broken at M2's gate with a
# series AC voltage source (Middlebrook voltage injection: M2's gate is a
# high impedance driven from Mn's low-impedance source, so this is accurate):
#   T = -v(x)/v(xb), PM = 180 + phase(T) at |T| = 1.
# From tb_bias (real diode loads on the three outputs). Per corner, 10/27/50 C.
# Run in the osic image from a dir holding the tb_bias netlist:
#   CORNERS="tt ss ff sf fs" ../../sim/bias/loop.sh  -> RESULT lines in bias_loop_<c>.log
corners=${CORNERS:-"tt ss ff sf fs"}
temps=${TEMPS:-"10 27 50"}
for c in $corners; do
  f=bias_loop_$c.spice
  sed -e '/^\.control/,/^\.endc/d' -e '/^\.end$/d' \
      -e "s/\(sky130\.lib\.spice\) tt/\1 $c/" \
      -e 's/^\(XM2 ota\) x \(tail .*\)/Vinj xb x dc 0 ac 1\n\1 xb \2/' tb_bias.spice > $f
  grep -q '^XM2 ota xb tail' $f || { echo "M2 gate not found"; exit 1; }
  cat >> $f <<CTL
.control
foreach t $temps
  reset
  option temp = \$t
  ac dec 50 1 10g
  let tl = -v(x1.x) / v(x1.xb)
  let tdb = db(tl)
  let tph = 180 / pi * cph(tl)
  meas ac dc_db find tdb at=10
  meas ac fu when tdb=0 fall=1
  meas ac phu find tph when tdb=0 fall=1
  let pm = 180 + phu
  meas ac gm_f when tph=-180 fall=1
  echo RESULT bias_loop $c \$t dc_dB \$&dc_db fu_Hz \$&fu pm_deg \$&pm
  destroy all
end
.endc
.end
CTL
  ngspice -b $f > bias_loop_$c.log 2>&1
  grep RESULT bias_loop_$c.log
done
