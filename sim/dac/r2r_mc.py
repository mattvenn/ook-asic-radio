"""Summary of build/r2r_mc_*.json (sim/dac/tb_r2r.py --mc): per sample, the DNL at the carries, gaps
(DNL > +0.5 LSB anywhere in codes 120..254) and the step factor (median code-to-code step in codes 140..254, ideal
LSB): the factor the comparator's trim step is multiplied by.

    python3 sim/dac/r2r_mc.py [build/r2r_mc_<tag>.json ...]
"""
import glob
import json
import os
import sys

import numpy as np

LSB = 1.8 / 256
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))


def pct(x):
    return '/'.join(f'{v:+.2f}' for v in np.percentile(x, [5, 50, 95]))


if __name__ == '__main__':
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, 'build', 'r2r_mc_*.json')))
    for f in files:
        c = np.array(json.load(open(f))['curves'])
        s = np.diff(c, axis=1) / LSB
        d = s - 1
        gap = (d[:, 120:255] > 0.5).any(1)
        fac = np.median(s[:, 140:255], axis=1)
        print(f'{os.path.basename(f)[7:-5]}: {len(c)} samples, unique {len({tuple(np.round(x, 9)) for x in c})}')
        print(f'   DNL 127>128 p5/50/95 {pct(d[:, 127])}   191>192 {pct(d[:, 191])}   159>160 {pct(d[:, 159])}')
        print(f'   max DNL in 120..254: p50 {np.median(d[:, 120:255].max(1)):+.2f}, worst {d[:, 120:255].max():+.2f}; '
              f'chips with a gap (> +0.5) {gap.mean() * 100:.1f} %;  chips with a downward step away from the '
              f'16-code carries {np.mean([(np.delete(x, np.arange(15, 255, 16)) < -1).any() for x in d]) * 100:.1f} %')
        print(f'   step factor (median step 140..254) p5/50/95 {"/".join(f"{v:.3f}" for v in np.percentile(fac, [5, 50, 95]))}'
              f';  V255 p5/50/95 {"/".join(f"{v:.4f}" for v in np.percentile(c[:, 255], [5, 50, 95]))}')
