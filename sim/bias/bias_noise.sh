#!/bin/bash
# Baseband noise at the detector output (v(det)) from the bias generator.
# tb_logdet (pad models, lna_chain, log_det) at idle (no signal), .noise 1 Hz-10 MHz,
# twice: ideal bias sources (noiseless) and the real bias_gen (from tb_radio_analog),
# which feeds the chain's ibias + vcm and the detector's ibias_det; ib_comp is loaded
# with 100 k as in rx_corners.sh. The difference is what bias_gen adds; the per-device
# spectra in the raw file split it further. Analyse: python sim/bias/bias_noise.py
# Netlist first (into build/biasnoise, so build/ isn't touched):
#   tools/osic-mac bash -c 'xschem -n -s -q -o build/biasnoise xschem/tb_logdet.sch;
#                           xschem -n -s -q -o build/biasnoise xschem/tb_radio_analog.sch'
# Run in the osic image from build/biasnoise:  ../../sim/bias/bias_noise.sh [corners...]
# One ngspice per case, NPAR at a time (default 2); NT threads each (default 2).
corners=${@:-tt}
npar=${NPAR:-2}; nt=${NT:-2}
strip() { sed -e '/^\.control/,/^\.endc/d' -e '/^\.end$/d' -e "s/\(sky130\.lib\.spice\) tt/\1 $2/" $1; }
for c in $corners; do
  for b in ideal real; do
    f=bn_${b}_$c.spice
    strip tb_logdet.spice $c > $f
    if [ $b = real ]; then
      sed -i -e '/^Iref VDPWR ibias /d' -e '/^Vcm vcm GND /d' -e '/^Ibd VDPWR ibias_det /d' $f
      {
        echo "xbias VDPWR vcm ibias ibias_det ib_comp_nc VDPWR GND bias_gen rref=10k rdiv=200k rtail=250k wpu=2 cc=1p"
        echo "Rib_comp_nc ib_comp_nc GND 100k"
        sed -n '/^\.subckt bias_gen /,/^\.ends/p' tb_radio_analog.spice
      } >> $f
    fi
    cat >> $f <<CTL
.options method=GEAR
.control
set num_threads=$nt
op
print v(det) v(vcm) v(ibias) v(ibias_det)
noise v(det) vant_p dec 20 1 10meg 1
setplot noise1
write bn_${b}_$c.raw all
.endc
.end
CTL
  done
done
jobs_list=$(for c in $corners; do for b in ideal real; do echo bn_${b}_$c; done; done)
echo "$jobs_list" | xargs -P $npar -I{} sh -c 'ngspice -b {}.spice > {}.log 2>&1; echo done {}'
