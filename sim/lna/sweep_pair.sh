#!/bin/bash
# Diff-pair first stage (dp = NMOS pair, dpp = PMOS pair): gain EMF->o1 and NF
# at 433.92 MHz vs tail current and pair W, L = 0.15. The load R keeps a 0.6 V drop,
# and the mirror W scales with current. Run in the osic image from build/:
#   ../sim/lna/sweep_pair.sh dp "10 20 40 80 160"
#   ../sim/lna/sweep_pair.sh dpp "40 80 160 320"
k=$1; widths=$2; wt0=$([ "$k" = dp ] && echo 6 || echo 12)
sed -e '/^\.control/,/^\.endc/d' -e '/^\.end$/d' tb_lna_$k.spice > /tmp/sw_$k.spice
cat >> /tmp/sw_$k.spice <<CTL
.control
echo "pair itail_mA W gain_o1_dB NF_dB"
foreach it 0.6 1.2 2.4
  foreach w $widths
    let ib = \$it * 1e-4
    let rl = 1.2 / (\$it * 1e-3)
    let wt = $wt0 * \$it / 0.6
    alterparam ibias_$k = \$&ib
    alterparam rl_$k = \$&rl
    alterparam wt_$k = \$&wt
    alterparam w_$k = \$w
    reset
    ac lin 1 433.92e6 433.92e6
    let gdb = db((v(o1p)-v(o1n))/(v(emf_p)-v(emf_n)))
    echo "$k \$it \$w \$&gdb" NOEOL
    noise v(o1p,o1n) vant_p lin 1 433.92e6 433.92e6
    * inoise referred to vant_p alone = noise per volt of differential EMF (symmetric circuit)
    let nf = 20*log10(inoise_spectrum / sqrt(4*1.380649e-23*300.15*73))
    echo "\$&nf"
    destroy all
  end
end
.endc
.end
CTL
ngspice -b /tmp/sw_$k.spice 2>&1 | grep -E "^(pair|dp|[0-9-])" | sed -z "s/ NOEOL\n/ /g"
