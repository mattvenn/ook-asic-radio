#!/bin/bash
# RX process corners x temperature, transistor level, ideal bias sources
# (iref 60 uA, vcm 1.2 V, 2 uA detector, 1 uA comparator: the circuits' own
# spread; bias generation comes later).
#   chain   (tb_chain):  supply current; AC gain EMF -> out over 100 MHz-1 GHz
#                        (raw per case); spot noise at 434 MHz (raw per case)
#   logdet  (tb_logdet): CW det level at a few input levels (RESULT lines)
#   comp    (tb_comp):   offset vs input CM, trim transfer ends (RESULT lines)
# One ngspice per testbench per corner (the .lib line is rewritten), with the
# temperature loop inside (option temp after reset).
# Run in the osic image from build/ (after netlisting tb_chain, tb_logdet,
# tb_comp):  CORNERS="tt ss" TEMPS="-20 27 85" ../sim/corners/rx_corners.sh
# Output: build/corners/*.raw, build/corners/rx_<tb>_<corner>.log (RESULT
# lines). TBS="comp" runs only some testbenches. Analyse: python sim/corners/rx_corners.py
# Supply: VDD=1.71 sets VDPWR (default 1.8); OUT=corners_v171 writes there instead (analyse with
# CORNERS_DIR=build/corners_v171). NT=1 sets ngspice threads (default: .spiceinit's 8).
# Bias: BIAS=real replaces the ideal sources (iref, vcm, detector / comparator currents) with the real
# bias_gen (from real/tb_radio_analog.spice; netlist xschem/tb_radio_analog.sch into build/real first).
# Its outputs a bench doesn't use are loaded with 100 k. Default BIAS=ideal.
corners=${CORNERS:-"tt ss ff sf fs"}
temps=${TEMPS:-"-20 27 85"}
levels=${LEVELS:-"-110 -90 -80 -70 -60 -50 -40 -30"}
vdd=${VDD:-1.8}
out=${OUT:-corners}
nt=${NT:+set num_threads=$NT}
mkdir -p $out
bias=${BIAS:-ideal}
# realbias <deck> <vdd node>: ideal bias sources out, bias_gen in (enabled), unused outputs loaded
realbias() {
  [ "$bias" = real ] || return 0
  sed -i -e '/^Iref VDPWR ibias /d' -e '/^Vcm vcm GND /d' -e '/^Ibd VDPWR ibias_det /d' -e '/^Ib VDD ibias 1u$/d' $1
  local chain=ibias det=ibias_det comp=ib_comp_nc vcm=vcm
  if grep -q "comp_ct" $1; then chain=ib_chain_nc det=ib_det_nc comp=ibias vcm=vcm_nc; fi
  if ! grep -q "ibias_det" $1; then det=ib_det_nc; fi
  {
    echo "xbias $2 $vcm $chain $det $comp $2 GND bias_gen rref=10k rdiv=200k rtail=250k wpu=2 cc=1p"
    for n in $chain $det $comp; do case $n in *_nc) echo "R$n $n GND 100k";; esac; done
    sed -n '/^\.subckt bias_gen /,/^\.ends/p' real/tb_radio_analog.spice
  } >> $1
}
strip() { sed -e '/^\.control/,/^\.endc/d' -e '/^\.end$/d' -e "s/\(sky130\.lib\.spice\) tt/\1 $2/" \
  -e "s/^VDPWR VDPWR GND dc 1\.8 /VDPWR VDPWR GND dc $vdd /" -e "s/^VDD VDD GND 1\.8$/VDD VDD GND $vdd/" $1; }

for c in $corners; do
  # ---- chain
  f=$out/rx_chain_$c.spice
  strip tb_chain.spice $c > $f
  realbias $f VDPWR
  cat >> $f <<CTL
.options method=GEAR
.control
$nt
foreach t $temps
  reset
  option temp = \$t
  op
  let idd = -i(vdpwr) * 1e3
  echo RESULT chain $c \$t idd_mA \$&idd
  destroy all
  ac dec 50 100meg 1g
  write $out/chain_${c}_{\$t}_ac.raw
  destroy all
  noise v(out_p,out_n) vant_p lin 1 433.92e6 433.92e6
  write $out/chain_${c}_{\$t}_noise.raw
  destroy all
end
.endc
.end
CTL
  # ---- log detector CW transfer
  f=$out/rx_logdet_$c.spice
  strip tb_logdet.spice $c > $f
  realbias $f VDPWR
  cat >> $f <<CTL
.save v(det)
.options method=GEAR
.control
$nt
foreach t $temps
  foreach p $levels
    let ve = sqrt(8 * 73 * 1e-3 * 10^(\$p/10))
    alterparam vemf = \$&ve
    reset
    option temp = \$t
    tran 50p 600n 400n
    meas tran detavg avg v(det) from=500n to=600n
    echo RESULT logdet $c \$t \$p \$&detavg
    destroy all
  end
end
.endc
.end
CTL
  # ---- comparator: offset vs CM (trim mid), trim transfer ends (CM 1.0)
  f=$out/rx_comp_$c.spice
  strip tb_comp.spice $c > $f
  realbias $f VDD
  cat >> $f <<CTL
.options method=GEAR
.control
$nt
foreach t $temps
  foreach cm 0.6 1.0 1.4 1.55
    alterparam vcm = \$cm
    alterparam vtrim = 0.9
    reset
    option temp = \$t
    dc vdiff -30m 30m 0.05m
    meas dc vth when v(out)=0.9 cross=1
    let off = vth * 1e3
    echo RESULT comp_cm $c \$t \$cm \$&off
    destroy all
  end
  foreach tr 0.6 0.8 0.9 1.0 1.1 1.2 1.8
    alterparam vcm = 1.0
    alterparam vtrim = \$tr
    reset
    option temp = \$t
    dc vdiff -40m 40m 0.05m
    meas dc vth when v(out)=0.9 cross=1
    let off = vth * 1e3
    echo RESULT comp_trim $c \$t \$tr \$&off
    destroy all
  end
end
.endc
.end
CTL
  for tb in ${TBS:-chain logdet comp}; do
    echo "start $tb $c: $(date)"
    ngspice -b $out/rx_${tb}_$c.spice > $out/rx_${tb}_$c.log 2>&1
    echo "done  $tb $c: $(date), $(grep -c RESULT $out/rx_${tb}_$c.log) results, $(grep -ci error $out/rx_${tb}_$c.log) errors"
  done
done
