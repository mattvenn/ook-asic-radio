#!/bin/bash
# Large-signal check of tb_chain: 434 MHz tone from -100 to -10 dBm (available
# from the 73 ohm dipole), differential amplitude (pp/2) at every stage tap.
# Run in the osic image from build/:  ../sim/chain/levels.sh [netlist]
src=${1:-tb_chain.spice}
sed -e '/^\.control/,/^\.endc/d' -e '/^\.end$/d' $src > /tmp/lv.spice
cat >> /tmp/lv.spice <<'CTL'
.options method=GEAR
.control
echo "Pin_dBm o1_mV o2_mV o3_mV o4_mV out_mV"
foreach p -100 -90 -80 -70 -60 -50 -40 -30 -20 -10
  let ve = sqrt(8 * 73 * 1e-3 * 10^($p/10))
  alterparam vemf = $&ve
  reset
  tran 20p 120n 60n
  echo "$p" NOEOL
  foreach t o1 o2 o3 o4
    let d = v(x1.{$t}p) - v(x1.{$t}n)
    meas tran pp pp d from=80n to=120n
    let a = pp / 2 * 1e3
    echo "$&a" NOEOL
  end
  let d = v(out_p) - v(out_n)
  meas tran pp pp d from=80n to=120n
  let a = pp / 2 * 1e3
  echo "$&a"
  destroy all
end
.endc
.end
CTL
ngspice -b /tmp/lv.spice 2>&1 | grep -E "^(Pin|-?[0-9])" | sed -z "s/ NOEOL\n/ /g"
