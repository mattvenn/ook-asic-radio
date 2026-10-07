#!/bin/bash
# Fully joined RX transient, transistor level end to end:
#   antenna (keyed 434 MHz + trnoise at the receiver's NF) -> pad_model ->
#   6-stage lna_chain -> log_det -> lpf_rc -> avg_sc -> comp_ct (+ trim servo
#   stand-in, digital sc_phi timing).
# Keying with real chip timing: off 0-60 us, then chips on/off/on (104 us
# each), off to the end. Checks that the real detector feeds the baseband
# blocks the way the split model (gen_det.py + bb.sh) assumes.
#
# Slow: ~16 s of CPU per simulated us -> ~2 h per level for 400 us.
# Run in the osic image from build/:
#   LEVELS="-70 -90" TSTOP=400u ../sim/rx/joined.sh
# Progress: tr '\r' '\n' < build/joined_<lvl>.log | grep Reference | tail -1
# Output: build/joined_<lvl>.raw (10 ns grid via option interp), plot with
#   sim/rx/plot_joined.py
levels=${LEVELS:-"-70 -90"}
tstop=${TSTOP:-400u}
# noise: 2.76 nV/rtHz per arm (3.9 differential ~ NF 11 dB), white, 50 ps samples
nz=$(python3 -c "import math; print(2.76e-9*math.sqrt(1/(2*50e-12)))")
for lvl in $levels; do
  ve=$(python3 -c "import math; print(math.sqrt(8*73*1e-3*10**($lvl/10)))")
  f=joined_$lvl.spice
  sed -e '/^\.control/,/^\.endc/d' -e '/^\.end$/d' \
      -e 's/^Vant_p emf_p acm .*/Bant_p emf_p acm V = v(key) * vemf\/2 * sin(2*pi*f0*time)/' \
      -e 's/^Vant_n emf_n acm .*/Bant_n emf_n acm V = -v(key) * vemf\/2 * sin(2*pi*f0*time)/' \
      -e "s/^Rant_\([pn]\) ant_\([pn]\) emf_\([pn]\) 36.5/Rant_\1 an_\1 emf_\1 36.5\nVnz_\1 ant_\1 an_\1 dc 0 trnoise($nz 50p 0 0)/" \
      tb_logdet.spice > $f
  # baseband blocks: subcircuits from the tb_rx_bb netlist
  awk '/^\.subckt (lpf_rc|avg_sc|comp_ct)/,/^\.ends/' tb_rx_bb.spice >> $f
  cat >> $f <<CTL
* --- baseband half, joined to the real detector output 'det'
* NB all clock/key edges are offset by 25 ps: trnoise puts a breakpoint every
* 50 ps, and an edge landing on that grid (+- rounding) gives 'timestep too small'
x11 det lpf GND lpf_rc lr=136 nc=6
x12 lpf phi1 phi2 avg VDPWR GND avg_sc ncs=1 nca=5
x13 avg lpf trim ibc comp VDPWR GND comp_ct w1=20 l1=1 mt1=10 rdeg=1.4Meg mta=2 lref=136 wcl=22
Ibc VDPWR ibc 1u
Vphi1 phi1 GND pulse(0 1.8 25p 10n 10n 6.09u 13u)
Vphi2 phi2 GND pulse(0 1.8 6.500025u 10n 10n 6.09u 13u)
Ctrim trim 0 1n
Btrim 0 trim I = tanh((v(comp) - 0.9) * 20) * 1n * (1.8/256) / 13u
Vkey key 0 pwl(0 0 60.000025u 0 60.010025u 1 164.000025u 1 164.010025u 0 268.000025u 0 268.010025u 1 372.000025u 1 372.010025u 0)
.ic v(trim)=0.84 v(avg)=1.439 v(x12.cs)=1.439 v(lpf)=1.439
.save v(det) v(lpf) v(avg) v(comp) v(trim) v(key)
.options method=GEAR interp
.control
alterparam vemf=$ve
reset
tran 10n $tstop 0 50p
write joined_$lvl.raw
.endc
.end
CTL
  echo "start $lvl dBm: $(date)"
  ngspice -b $f > joined_$lvl.log 2>&1
  echo "done  $lvl dBm: $(date), $(grep -ci error joined_$lvl.log) errors"
done
