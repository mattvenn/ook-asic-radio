"""The gen_det.py --gain that puts its noise-only detector level at a transistor-level one.

gen_det maps the RF power (signal + noise at NF over B_RF) through the CW detector curve shifted by
SHIFT_DB, calibrated so the noise alone gives the full-gain noise_tran.sh level (1.439 V). With the
LNA low-gain strap on, signal and noise both arrive lower at the detector: --gain is that shift,
found here from noise_tran.sh's noise-only det with the strap on (VGLO=0).

    python3 sim/rx/lo_gain.py <det noise-only V> [nf_dB]      or     python3 sim/rx/lo_gain.py <nt_none*.log> [nf_dB]

Prints the gain (dB). Self-check: the full-gain level (1.43904 V) at NF 11 gives ~0.
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


if __name__ == '__main__':
    x = sys.argv[1]
    if os.path.exists(x):
        x = re.search(r'^RESULT none (\S+)', open(x).read(), re.M).group(1)
    nf = float(sys.argv[2]) if len(sys.argv) > 2 else G.NF_DB
    print(f'{gain_for(float(x), nf):.2f}')
