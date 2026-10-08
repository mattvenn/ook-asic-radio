#!/bin/bash
# TX with a real VAPWR feed: ideal 3.3 V -> rsup 0.5 ohm -> lsup (bond wire +
# package + board) -> on-chip VAPWR, decap cdec to ground. The ~11 mA TX step
# and the 434 MHz driver current both come through it. Ground return is still
# ideal.
# Run in the osic image from build/ after netlisting tb_tx:
#   CASES="2n:0 5n:0 5n:20p 5n:50p 5n:100p 10n:50p" ../sim/tx/vapwr.sh
# Writes build/vapwr_<L>_<C>.raw; analyse: python sim/tx/vapwr.py
cases=${CASES:-"2n:0 5n:0 5n:20p 5n:50p 5n:100p 10n:0 10n:50p"}
for cs in $cases; do
  l=${cs%:*}; c=${cs#*:}
  f=vapwr_${l}_$c.spice
  sed -e '/^\.control/,/^\.endc/d' -e '/^\.end$/d' -e '/^\.save/d' \
      -e 's/^VA VAPWR GND 3.3/VA vsup GND 3.3\nRsup vsup vs2 0.5\nLsup vs2 VAPWR '"$l"'/' tb_tx.spice > $f
  [ "$c" != 0 ] && echo "Cdec VAPWR GND $c" >> $f
  cat >> $f <<CTL
.save v(VAPWR) v(out_p) v(out_n) v(ant_p) v(ant_n) i(VA) i(VD) v(key)
.options method=GEAR
.control
tran 2p 80n 0
write vapwr_${l}_$c.raw
.endc
.end
CTL
  ngspice -b $f > vapwr_${l}_$c.log 2>&1
  echo "$cs: $(grep -ci error vapwr_${l}_$c.log) errors"
done
