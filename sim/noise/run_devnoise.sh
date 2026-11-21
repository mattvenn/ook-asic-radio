#!/bin/bash
# Action 13: device noise in transient (sim/noise/dev_noise.py) against the workaround (one equivalent noise source per
# antenna arm, sim/logdet/gen_noise.py) at the same noise figure, on the schematic chain + log_det (tb_logdet), full gain.
# noise_tran.sh per case: det averaged over 0.5-3 us, chain output rms.
#   A    injected, 2.76 nV/rtHz per arm (NF 11.0, the workaround as used; seed 7 is the gen_det.py calibration run)
#   Bth  injected at the device sources' thermal NF   (2.943 nV/rtHz: dev_noise.py "NF +0.53 dB" over ngspice's 11.03)
#   Ball injected at the device sources' thermal + 1/f NF (3.267 nV/rtHz: "+1.44 dB")
#   Dth  device sources, thermal       Dall  device sources, thermal + 1/f
# Needs build/tb_logdet.spice and build/devnoise/dev_{thermal,all}_s{11,12,13}.inc (dev_noise.py ... 3e-6 <seed>).
#   bash sim/noise/run_devnoise.sh            (from the repo root; outputs build/devnoise/run/<set>_s<seed>/nt_<level>.log)
# Each run dir gets the repo .spiceinit with num_threads=1 (ngspice reads it from its cwd; without it ~/.spiceinit's
# ngbehavior=hsa applies), NPAR at once.
set -e
R=$(cd "$(dirname "$0")/../.." && pwd -P)
W=$R/build/devnoise/run
NPAR=${NPAR:-26}
LEVELS=${LEVELS:-none -94 -90 -85}
mkdir -p $W
jobs=()
mk() {   # set seed noise-include-text
  d=$W/$1_s$2; mkdir -p $d; cp $R/build/tb_logdet.spice $d/; printf '%s\n' "$3" > $d/noise_pwl.inc
  sed 's/^set num_threads=.*/set num_threads=1/' $R/.spiceinit > $d/.spiceinit
  for p in $LEVELS; do jobs+=("$d $p"); done
}
mk A 7 "$(cd $R && python3 -c "import sys; sys.path.insert(0, 'sim/logdet'); import gen_noise as g; g.main(3e-6, 7, '/dev/stdout')")"
for s in 11 12 13; do
  for x in Bth:2.943e-9 Ball:3.267e-9; do
    mk ${x%%:*} $s "$(cd $R && python3 -c "import sys; sys.path.insert(0, 'sim/logdet'); import gen_noise as g; g.D = ${x#*:}; g.main(3e-6, $s, '/dev/stdout')")"
  done
  for x in thermal all; do
    [ $x = thermal ] && n=Dth || n=Dall
    mk $n $s "Vnz_p ant_p an_p 0
Vnz_n ant_n an_n 0
.include $R/build/devnoise/dev_${x}_s$s.inc"
  done
done
printf '%s\n' "${jobs[@]}" | xargs -P $NPAR -L 1 sh -c \
  "cd \$0 && TB=tb_logdet.spice bash $R/sim/logdet/noise_tran.sh \$1 > /dev/null 2>&1; grep -h '^RESULT' nt_\$1.log | sed \"s|^|\$(basename \$0) |\""
