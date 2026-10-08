#!/bin/bash
# AC check of the supply decap blocks (xschem/gen/decap.py): is decap_vapwr
# ~50 pF and decap_vdpwr ~30 pF, and what is their series R at 434 MHz?
# Takes the subcircuits from the tb_radio_analog netlist, drives each with
# a DC supply + 1 V AC and reports C = Im(I)/(2 pi f) and ESR = Re(1/Y) at
# 1 / 100 / 434 MHz, at the nominal supply and +-10 %, plus one 10 x 10 um
# MIM unit alone (so the MOS part is the rest).
# Run in the osic image from build/ (after netlisting tb_radio_analog):
#   ../sim/decap/decap_ac.sh   ->  RESULT lines in decap_ac.log
f=decap_ac.spice
{
  echo "* decap AC check"
  echo ".lib /foss/pdks/sky130A/libs.tech/combined/sky130.lib.spice tt"
  awk '/^\.subckt decap_v/,/^\.ends/' tb_radio_analog.spice
  echo ".param va=3.3 vd=1.8"
  echo "Va a 0 dc 'va' ac 1"
  echo "xa a 0 decap_vapwr n=100"
  echo "Vd d 0 dc 'vd' ac 1"
  echo "xd d 0 decap_vdpwr n=30"
  echo "* one MIM unit alone (10 x 10 um)"
  echo "Vm m 0 dc 1.8 ac 1"
  echo "XCm m 0 sky130_fd_pr__cap_mim_m3_1 W=10 L=10 MF=1 m=1"
  cat <<'CTL'
.control
foreach s 0.9 1.0 1.1
  alterparam va = 3.3 * $s
  alterparam vd = 1.8 * $s
  reset
  foreach fr 1e6 100e6 433.92e6
    ac lin 1 $fr $fr
    let ya = -i(va)
    let yd = -i(vd)
    let ym = -i(vm)
    let ca = imag(ya) / (2*pi*$fr) * 1e12
    let cd = imag(yd) / (2*pi*$fr) * 1e12
    let cm = imag(ym) / (2*pi*$fr) * 1e15
    let ra = real(1/ya)
    let rd = real(1/yd)
    echo RESULT scale $s f $fr vapwr_pF $&ca vapwr_esr $&ra vdpwr_pF $&cd vdpwr_esr $&rd mim_unit_fF $&cm
    destroy all
  end
end
.endc
.end
CTL
} > $f
ngspice -b $f > decap_ac.log 2>&1
grep RESULT decap_ac.log
