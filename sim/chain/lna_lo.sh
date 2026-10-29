#!/bin/bash
# Low-gain strap sizing: a shunt across stage 1's outputs (o1p - o1n) in tb_chain,
# o1p - Rh - PMOS - Rh - o1n, gate at 0 (low gain, switch on) or VDPWR (full gain).
# Per case: AC gain at 434 MHz and its peak, and NF at 434 MHz (input-referred
# noise vs the 73 ohm source; relative numbers, same method for every case).
#
# Run in the osic image from build/real (after netlisting tb_chain there):
#   CASES="ideal:325:on dev:250:on dev:250:off" CORNER=ss TEMP=10 bash ../../sim/chain/lna_lo.sh
# Case = <kind>:<Rh ohms per half>:<on|off|none>[:<pmos W um>]
#   kind ideal: Rh are ideal resistors, the switch an ideal short (on) or open (off);
#   kind dev:   Rh drawn as res_high_po_5p73 (one segment per half), switch pfet_01v8 L 0.15, nf = W/5.
#   kind d141:  as dev, Rh drawn as res_high_po_1p41 (R = 278 + 230.3 * L, L >= 0.5: >= 393 ohm).
#   kind sw:    the switch alone (no Rh; <Rh> ignored).
#   none: no shunt at all (the reference).
# Results: RESULT lines in lnalo_<tag>.log.
cases=${CASES:-"x:0:none ideal:325:on"}
corner=${CORNER:-tt}; temp=${TEMP:-27}
vglo=${VGLO:-1.8}                         # the chain's own strap (lna_shunt): 1.8 off, 0 low gain
node=${NODE:-o1}                          # o1: stage 1 outputs; o2: stage 2's (what-if)
wsw_def=${WSW:-10}
for cs in $cases; do
  IFS=: read kind rh st wsw <<< "$cs"; wsw=${wsw:-$wsw_def}
  tag=${kind}_${rh}_${st}; [ "$kind" != ideal ] && tag=${tag}_w$wsw
  [ "$corner/$temp" != tt/27 ] && tag=${tag}_${corner}_$temp
  [ "$node" != o1 ] && tag=${tag}_$node
  [ "$vglo" != 1.8 ] && tag=${tag}_glo$vglo
  f=lnalo_$tag.spice
  sed -e '/^\.control/,/^\.endc/d' -e '/^\.end$/d' \
      -e "s/\(sky130\.lib\.spice\) tt/\1 $corner/" \
      -e "s/^\.param vglo=.*/.param vglo=$vglo/" \
      tb_chain.spice > $f
  echo ".temp $temp" >> $f
  if [ "$st" != none ]; then
    if [ "$st" = on ]; then gv=0; else gv=1.8; fi
    if [ "$kind" = ideal ]; then
      echo "Rh_p ${node}p shp $rh" >> $f; echo "Rh_n ${node}n shn $rh" >> $f
      if [ "$st" = on ]; then echo "Rsw shp shn 1m" >> $f; fi
    else
      # res_high_po_5p73: R = 72.8 + 56.6 * L (tt op fit, L 0.5-2)
      if [ "$kind" = d141 ]; then
        echo "XRh_p ${node}p shp GND sky130_fd_pr__res_high_po_1p41 L='max(($rh-278)/230.3,0.5)' mult=1" >> $f
        echo "XRh_n ${node}n shn GND sky130_fd_pr__res_high_po_1p41 L='max(($rh-278)/230.3,0.5)' mult=1" >> $f
      elif [ "$kind" = sw ]; then
        echo "Vsh_p ${node}p shp 0" >> $f; echo "Vsh_n ${node}n shn 0" >> $f
      else
        echo "XRh_p ${node}p shp GND sky130_fd_pr__res_high_po_5p73 L='max(($rh-72.8)/56.6,0.5)' mult=1" >> $f
        echo "XRh_n ${node}n shn GND sky130_fd_pr__res_high_po_5p73 L='max(($rh-72.8)/56.6,0.5)' mult=1" >> $f
      fi
      nf=$(( ${wsw%.*} / 5 )); [ $nf -lt 1 ] && nf=1
      echo "XMsw shp glo shn VDPWR sky130_fd_pr__pfet_01v8 L=0.15 W=$wsw nf=$nf ad='int(($nf+1)/2)*$wsw/$nf*0.29' as='int(($nf+2)/2)*$wsw/$nf*0.29' pd='2*int(($nf+1)/2)*($wsw/$nf+0.29)' ps='2*int(($nf+2)/2)*($wsw/$nf+0.29)' nrd='0.29/$wsw' nrs='0.29/$wsw' sa=0 sb=0 sd=0 mult=1 m=1" >> $f
      echo "Vglo glo GND $gv" >> $f
    fi
  fi
  cat >> $f <<CTL
.control
op
let o1cm = (v(o1p) + v(o1n)) / 2
let o2cm = (v(o2p) + v(o2n)) / 2
let idd = -i(vdpwr)
echo RESULT op o1cm \$&o1cm o2cm \$&o2cm idd \$&idd
ac dec 50 100meg 2g
let g = db(v(out_p) - v(out_n))
let g1 = db(v(o1p) - v(o1n)) - db(v(pad_p) - v(pad_n))
meas ac g434 find g at=433.92e6
meas ac g1_434 find g1 at=433.92e6
meas ac gpk max g
echo RESULT ac gain434_dB \$&g434 st1_dB \$&g1_434 peak_dB \$&gpk
noise v(out_p,out_n) vant_p lin 3 423.92e6 443.92e6
setplot previous
let nf = 10*log10(inoise_spectrum[1]^2 / (4*1.380649e-23*300*73))
echo RESULT noise nf434_dB \$&nf
.endc
.end
CTL
  ngspice -b $f > lnalo_$tag.log 2>&1
  echo "$cs $corner $temp: $(grep RESULT lnalo_$tag.log | tr '\n' ' ')"
done
