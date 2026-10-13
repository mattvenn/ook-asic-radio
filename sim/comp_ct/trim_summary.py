"""Summarise trim_curve.py results: vref, balance point (nominal code), flat step and fine-trim window.

Flat step: the median of the steps within 1.3x the smallest step (0.4-1.7 V). Two windows, each quoted as the
threshold (mV) at its ends, i.e. the input offsets a chip can cancel there (a chip with offset x needs threshold
-x, so the window's negative end serves positive-offset chips):
  fine: the contiguous run of 50 mV points around the balance point whose step (from the previous point) is
        within 0.95-1.25x the flat step;
  -92:  from the lowest point with step <= 0.19 mV/LSB (e2e holds -92 dBm) up to the threshold at code 242
        (the top end: past it a chip may not trim at all).

    python3 sim/comp_ct/trim_summary.py [--vdd 1.8] <tag> ...      (reads build/trim/<tag>.json)
"""
import json
import os
import sys

import numpy as np

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build', 'trim')


def summary(tag, vdd=1.8):
    r = np.array(json.load(open(os.path.join(B, tag + '.json'))))
    lsb = vdd / 256
    vt, th = r[:, 0], r[:, 1] * 1e3
    st = np.full(len(vt), np.nan)
    st[1:] = np.abs(np.diff(th)) / (np.diff(vt) / lsb)
    mid = (vt >= 0.4) & (vt <= 1.7) & ~np.isnan(st)
    flat = np.median(st[mid][st[mid] <= 1.3 * np.nanmin(st[mid])])
    k = np.where(np.diff(np.sign(th)) > 0)[0][0]              # th crosses 0 between k and k+1
    v0 = vt[k] - th[k] * (vt[k + 1] - vt[k]) / (th[k + 1] - th[k])
    ok = (st >= 0.95 * flat) & (st <= 1.25 * flat)
    lo, hi = k + 1, k + 1
    while lo - 1 >= 0 and ok[lo - 1] and ok[lo]:
        lo -= 1
    if not ok[lo]:
        lo += 1
    while hi + 1 < len(vt) and ok[hi + 1]:
        hi += 1
    j = k + 1
    while j - 1 >= 0 and st[j] <= 0.19:
        j -= 1
    top = np.interp(242 * lsb, vt, th)
    return dict(vref=r[0, 4], code=v0 / lsb, flat=flat, wlo=th[lo], whi=th[hi], vlo=vt[lo], vhi=vt[hi],
                w92=th[j], top=top)


if __name__ == '__main__':
    args = sys.argv[1:]
    vdd = 1.8
    if '--vdd' in args:
        i = args.index('--vdd')
        vdd = float(args[i + 1])
        del args[i:i + 2]
    print('tag | vref V | nominal code | flat step mV/LSB | fine window mV (trim V) | -92 window mV')
    for t in args:
        s = summary(t, vdd)
        print(f"{t} | {s['vref']:.3f} | {s['code']:.0f} | {s['flat']:.3f} | "
              f"{s['wlo']:+.1f} / {s['whi']:+.1f} ({s['vlo']:.2f}..{s['vhi']:.2f}) | {s['w92']:+.1f} / {s['top']:+.1f}")
