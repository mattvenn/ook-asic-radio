"""The gen_det.py --gain that puts its noise-only detector level at a transistor-level one.

gen_det maps the RF power (signal + noise at NF over B_RF) through the CW detector curve shifted by
SHIFT_DB, calibrated so the noise alone gives the full-gain noise_tran.sh level (1.44973 V since 2026-11-20). With the
LNA low-gain strap on, signal and noise both arrive lower at the detector: --gain is that shift,
found here from noise_tran.sh's noise-only det with the strap on (VGLO=0).

    python3 sim/rx/lo_gain.py <det noise-only V> [nf_dB]      or     python3 sim/rx/lo_gain.py <nt_none*.log> [nf_dB]

Prints the gain (dB). Self-check: the full-gain level (1.44973 V) at NF 11 gives ~0. Fixed-noise levels (2026-11-17,
build_tall/rerun_tall_follow/logs/nt3_*): schematic noise-only 1.44973 V full gain, 1.51088 V low gain.

The extracted rx_t (chain + its own extracted detector) can't be calibrated this way: its detector sits at another
level (noise-only, low gain: 1.484 V against the schematic's 1.510 V), and mapping that through the schematic curve
read as +6.6 dB of gain (2026-11-16, the invalid 'lopex' runs). For it, keep the schematic's gain and raise the NF by
the measured signal loss instead: the extracted detector drops (noise-only level minus level with signal) are a
fixed fraction of the schematic's at every level (0.67 at low gain, 2026-11-17), i.e. the same signal-to-noise as
the schematic with the NF that much higher. That counts all of the loss as SNR (none as detector slope): pessimistic.

    python3 sim/rx/lo_gain.py --nf <sch TAG> <pex TAG> [nf_dB]     e.g. --nf _sch_glo0 _pex_glo0 11.7

reads build/nt_<level><TAG>.log for every level both have and prints the NF (dB).
"""
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_det as G  # noqa: E402


def gain_for(det_v, nf=G.NF_DB):
    pin, vdet = G.det_curve()
    o = np.argsort(vdet)                               # the curve falls with power: invert on sorted V
    p_eq = float(np.interp(det_v, vdet[o], pin[o]))   # curve input power that gives det_v
    pn = 10 * math.log10(G.rxm.KT * 10 ** (nf / 10) * G.B_RF) + 30
    return p_eq - pn - G.SHIFT_DB


def nf_for(sch_tag, pex_tag, nf, build=os.path.join(HERE, '..', '..', 'build')):
    def res(tag):
        out = {}
        for f in os.listdir(build):
            m = re.fullmatch(rf'nt_(\S+?){re.escape(tag)}\.log', f)
            r = m and re.search(r'^RESULT (\S+) (\S+)', open(os.path.join(build, f)).read(), re.M)
            if r:
                out[r.group(1)] = float(r.group(2))
        return out
    s, p = res(sch_tag), res(pex_tag)
    lv = sorted(k for k in s if k in p and k != 'none')
    assert 'none' in s and 'none' in p and lv, f'no common levels for {sch_tag} / {pex_tag}'
    ratio = float(np.median([(p['none'] - p[k]) / (s['none'] - s[k]) for k in lv]))
    return nf - 10 * math.log10(ratio), ratio, lv


if __name__ == '__main__':
    if sys.argv[1] == '--nf':
        nf, ratio, lv = nf_for(sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else G.NF_DB)
        print(f'{nf:.2f}')
        print(f'drop ratio {ratio:.3f} over {" ".join(lv)}', file=sys.stderr)
        sys.exit()
    x = sys.argv[1]
    if os.path.exists(x):
        x = re.search(r'^RESULT none (\S+)', open(x).read(), re.M).group(1)
    nf = float(sys.argv[2]) if len(sys.argv) > 2 else G.NF_DB
    print(f'{gain_for(float(x), nf):.2f}')
