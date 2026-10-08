#!/bin/bash
# dac_drive level shifter: max toggle rate vs scale k (sanity check at low f
# and the speed limit). Uses ls_<k>.spice from ls_dac_drive.sh as template.
# Run in the osic image from build/tx/:  ../../sim/ring/ls_fmax.sh
for k in 1 10; do
  for f in 10e6 50e6 100e6 200e6 300e6; do
    per=$(python3 -c "print(1/$f)"); pw=$(python3 -c "print(0.5/$f-80e-12)")
    sed -e "s/^Vin ctrl 0 pulse.*/Vin ctrl 0 pulse(0 1.8 0.5n 80p 80p $pw $per)/" \
        -e "s/^tran 5p 30n/tran 5p $(python3 -c "print(8/$f)")/" \
        -e "s/from=20n to=30n/from=$(python3 -c "print(4/$f)") to=$(python3 -c "print(8/$f)")/g" \
        -e "s/rise=10 targ v(out) val=1.65 rise=10/rise=4 targ v(out) val=1.65 rise=4/" \
        -e "s/^echo RESULT k $k/echo RESULT k $k f $f/" -e "/^write/d" ls_$k.spice > lsf.spice
    ngspice -b lsf.spice 2>&1 | grep RESULT
  done
done
