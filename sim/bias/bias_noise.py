"""Analyse sim/bias/bias_noise.sh: rms noise at the comparator from each block, ideal vs real bias.

The comparator sees lpf_rc(det) - avg_sc(det): the 14 kHz envelope filter minus the slow average
(tau 0.45 ms), so drift below ~350 Hz is taken out. Each device's v(det) noise spectrum is
weighted by |H_lpf - H_avg|^2 and integrated (1 Hz-10 MHz); 'LPF only' is the same without
the average. The link model's budget (docs/history.md): <= 0.5 mV rms comparator noise is free.

    python sim/bias/bias_noise.py [corner ...]       (default tt)
"""
import math
import os
import re
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from rawread import read_raw  # noqa: E402

D = os.path.join(ROOT, 'build', 'biasnoise')
F_LPF, TAU_AVG = 14e3, 0.45e-3


def weights(f):
    s = 1j * f
    h_lpf = 1 / (1 + s / F_LPF)
    h_avg = 1 / (1 + s * 2 * math.pi * TAU_AVG)
    return np.abs(h_lpf - h_avg) ** 2, np.abs(h_lpf) ** 2


def rms_mv(f, psd, w):
    return 1e3 * math.sqrt(np.trapezoid(psd * w, f))


def block(dev):
    if '.xbias.' in dev or dev.endswith('.xbias'):
        return 'bias_gen'
    if '.x1.' in dev:
        return 'lna_chain'
    if '.x2.' in dev:
        return 'log_det'
    if 'xpad' in dev or 'rant' in dev:
        return 'antenna + pads'
    return 'other'


def load(path):
    v = read_raw(path)[0]['vars']
    f = np.real(v['frequency'])
    tot = np.real(v['onoise_spectrum']) ** 2
    devs = {}
    for k, a in v.items():
        m = re.match(r'onoise\.(.+)$', k)
        if not m:
            continue
        name = m.group(1)
        # mosfet totals end in the model name; drop their sub-terms (.id, .1overf, ...)
        if name.startswith('m.') and not re.search(r'\.m[^.]*$', name):
            continue
        if name.endswith(('_thermal', '_1overf')):
            continue
        devs[name] = np.nan_to_num(np.real(a)) ** 2
    return f, tot, devs


for c in sys.argv[1:] or ['tt']:
    print(f'=== {c}: rms at the comparator, mV (LPF - avg weighting; LPF only in brackets)')
    res = {}
    for b in ('ideal', 'real'):
        p = os.path.join(D, f'bn_{b}_{c}.raw')
        if not os.path.exists(p):
            print(f'  {b}: missing {p}')
            continue
        f, tot, devs = load(p)
        w, wl = weights(f)
        res[b] = (f, tot, devs, w, wl)
        acc = sum(devs.values())
        print(f'  {b:5s} total {rms_mv(f, tot, w):.3f}  ({rms_mv(f, tot, wl):.3f})'
              f'   [devices account for {100 * np.trapezoid(acc * w, f) / np.trapezoid(tot * w, f):.0f} %]')
        g = defaultdict(lambda: 0 * f)
        for d, a in devs.items():
            g[block(d)] += a
        for k, a in sorted(g.items(), key=lambda x: -np.trapezoid(x[1] * w, f)):
            print(f'      {k:15s} {rms_mv(f, a, w):.3f}  ({rms_mv(f, a, wl):.3f})')
    if 'real' in res:
        f, tot, devs, w, wl = res['real']
        bias = {d: a for d, a in devs.items() if block(d) == 'bias_gen'}
        print('  bias_gen devices (top 8):')
        for d, a in sorted(bias.items(), key=lambda x: -np.trapezoid(x[1] * w, f))[:8]:
            print(f'      {d:55s} {rms_mv(f, a, w):.3f}')
        if 'ideal' in res:
            fi, ti = res['ideal'][:2]
            add = np.trapezoid(tot * w, f) - np.trapezoid(ti * w, fi)
            print(f'  real - ideal (power difference): {1e3 * math.copysign(math.sqrt(abs(add)), add):.3f} mV rms')
        # spot densities at det
        for fx in (100, 1e3, 10e3):
            i = int(np.argmin(abs(f - fx)))
            bs = sum(bias.values())[i]
            print(f'  at {fx:>7.0f} Hz: total {1e9 * math.sqrt(tot[i]):7.1f} nV/rtHz, bias_gen {1e9 * math.sqrt(bs):7.1f} nV/rtHz')
