#!/bin/bash
# RF part of the whole-RX picture, transistor level (tb_logdet: antenna ->
# pad_model -> 6-stage lna_chain -> log_det). Two runs, raws for
# sim/rx/plot_rx.py:
#   rx_rf_tone : steady -60 dBm tone, 400 ns (stage-by-stage growth/limiting)
#   rx_rf_key  : -60 dBm tone keyed on at 0.5 us, off at 2.5 us (detector edge)
# Run in the osic image from build/:  ../sim/rx/rf.sh
ve=$(python3 -c "import math; print(math.sqrt(8*73*1e-3*10**(-60/10)))")
base() { sed -e '/^\.control/,/^\.endc/d' -e '/^\.end$/d' tb_logdet.spice; }
SAVE='.save v(emf_p) v(emf_n) v(pad_p) v(pad_n) v(o1p) v(o1n) v(o2p) v(o2n) v(o3p) v(o3n) v(o4p) v(o4n) v(o5p) v(o5n) v(out_p) v(out_n) v(det)'

base > rx_rf_tone.spice
cat >> rx_rf_tone.spice <<CTL
$SAVE
.options method=GEAR
.control
alterparam vemf=$ve
reset
tran 10p 400n 300n
write rx_rf_tone.raw
.endc
.end
CTL

# keyed: replace the antenna sources with a keyed sine (key: 0 -> 1 at 0.5 us, back at 2.5 us)
base | sed -e 's/^Vant_p emf_p acm .*/Bant_p emf_p acm V = v(key) * vemf\/2 * sin(2*pi*f0*time)/' \
           -e 's/^Vant_n emf_n acm .*/Bant_n emf_n acm V = -v(key) * vemf\/2 * sin(2*pi*f0*time)/' > rx_rf_key.spice
cat >> rx_rf_key.spice <<CTL
Vkey key 0 pwl(0 0 0.5u 0 0.502u 1 2.5u 1 2.502u 0)
$SAVE v(key)
.options method=GEAR
.control
alterparam vemf=$ve
reset
tran 20p 3.5u
write rx_rf_key.raw
.endc
.end
CTL
for r in rx_rf_tone rx_rf_key; do ngspice -b $r.spice > $r.log 2>&1; echo "$r: $(grep -ci error $r.log) errors"; done
