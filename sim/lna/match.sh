#!/bin/bash
# Input matching experiment on a tb_lna variant (default dp_1m2). Adds, per run:
#   lser : off-chip series L in each antenna arm (Q = qoff)
#   lsh  : off-chip differential shunt L across the two pins (Q = qoff)
#   lchip: on-chip differential shunt L across the pad 'mod' nodes (Q = qon)
# and prints EMF->o1 gain at 330/434/560 MHz plus NF at 434 MHz.
# Run in the osic image from build/:  ../sim/lna/match.sh [variant] ["L list nH"] ["lser lsh lchip"]
v=${1:-dp_1m2}; ls_=${2:-0 10 20 30 40 60 80 120 160}; whats=${3:-lser lsh lchip}
sed -e '/^\.control/,/^\.endc/d' -e '/^\.end$/d' \
    -e 's/^Rant_\([pn]\) ant_\([pn]\) emf_\([pn]\) 36.5/Rant_\1 a0_\1 emf_\1 36.5\
Lser_\1 ant_\1 a1_\1 '"'"'lser'"'"'\
RLser_\1 a1_\1 a0_\1 '"'"'max(1m, 6.283*f0*lser\/qoff)'"'"'/' \
    tb_lna_$v.spice > /tmp/m_$v.spice
cat >> /tmp/m_$v.spice <<'CTL'
Lsh ant_p shx 'lsh'
RLsh shx ant_n 'max(1m, 6.283*f0*lsh/qoff)'
Lchip pad_p chx 'lchip'
RLchip chx pad_n 'max(1m, 6.283*f0*lchip/qon)'
.param lser=1p lsh=1 lchip=1 qoff=30 qon=5
.control
echo "what L_nH g330 g434 g560 NF434"
foreach what @WHATS@
  foreach l @LS@
    alterparam lser = 1e-12
    alterparam lsh = 1
    alterparam lchip = 1
    if $l > 0
      let lv = $l * 1e-9
      alterparam $what = $&lv
    end
    reset
    echo "$what $l" NOEOL
    foreach f 330e6 433.92e6 560e6
      ac lin 1 $f $f
      let gdb = db((v(o1p)-v(o1n))/(v(emf_p)-v(emf_n)))
      echo "$&gdb" NOEOL
      destroy all
    end
    noise v(o1p,o1n) vant_p lin 1 433.92e6 433.92e6
    let nf = 20*log10(inoise_spectrum / sqrt(4*1.380649e-23*300.15*73))
    echo "$&nf"
    destroy all
  end
end
.endc
.end
CTL
sed -i -e "s/@WHATS@/$whats/" -e "s/@LS@/$ls_/" /tmp/m_$v.spice
ngspice -b /tmp/m_$v.spice 2>&1 | grep -E "^(what|lser|lsh|lchip|[0-9-])" | sed -z "s/ NOEOL\n/ /g"
