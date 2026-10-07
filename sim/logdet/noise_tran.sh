#!/bin/bash
# Detector output with the receiver's noise present: a PWL noise source in each
# antenna arm carries the whole input-referred noise (NF ~11 dB at 434 MHz:
# 3.9 nV/rtHz differential = 2.76 nV/rtHz per arm, white to 10 GHz with 50 ps
# samples), written by gen_noise.py with a fixed seed, so every case sees the
# same noise and differences show the signal. (ngspice's trnoise ignores the
# seed options here, so it isn't repeatable.) Needs build/noise_pwl.inc:
#   python sim/logdet/gen_noise.py [tstop_s]
# Run in the osic image from build/:  ../sim/logdet/noise_tran.sh [levels...]
# Progress: each case logs to build/nt_<level>.log; ngspice writes
#   'Reference value : <sim time>' as it goes, so
#   tr '\r' '\n' < build/nt_-94.log | grep Reference | tail -1
# shows how far through the transient it is. TSTOP / TSTART env vars override
# the run length (default 3u / 0.5u). NPAR = parallel cases (default 1: each
# ngspice already uses num_threads from .spiceinit; running several at once
# oversubscribes the cores).
levels=${@:-none -100 -94 -90 -85 -80}
tstop=${TSTOP:-3u}; tstart=${TSTART:-0.5u}; npar=${NPAR:-1}
for p in $levels; do
  if [ "$p" = none ]; then ve=0; else ve=$(python3 -c "import math; print(math.sqrt(8*73*1e-3*10**($p/10)))"); fi
  sed -e '/^\.control/,/^\.endc/d' -e '/^\.end$/d' \
      -e "s/^Rant_\([pn]\) ant_\([pn]\) emf_\([pn]\) 36.5/Rant_\1 an_\1 emf_\1 36.5/" \
      tb_logdet.spice > nt_$p.spice
  cat >> nt_$p.spice <<CTL
.include noise_pwl.inc
* keep only what's measured: 60k time points x every node otherwise
.save v(det) v(out_p) v(out_n)
.options method=GEAR
.control
alterparam vemf=$ve
reset
tran 50p $tstop $tstart
meas tran detavg avg v(det) from=$tstart to=$tstop
let dout = v(out_p) - v(out_n)
meas tran outrms rms dout from=$tstart to=$tstop
echo RESULT $p \$&detavg \$&outrms
.endc
.end
CTL
done
printf '%s\n' $levels | xargs -P $npar -I{} sh -c 'ngspice -b nt_{}.spice > nt_{}.log 2>&1; grep "^RESULT" nt_{}.log; rm -f nt_{}.spice'
