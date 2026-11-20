"""Table of build/r2r_curve_*.json (from sim/dac/tb_r2r.py): what the servo sees in the operating band.

  step x   median code-to-code step in codes 140..254, in ideal LSB (1.8/256): multiplies the comparator's trim step
  p90 x    90th percentile of the same
  carries  DNL at 127>128 / 159>160 / 191>192 / 223>224; overlap = codes above 128 still below V(127)

    python3 sim/dac/r2r_summary.py [pattern]       default build/r2r_curve_*.json
"""
import glob
import json
import os
import sys

import numpy as np

LSB = 1.8 / 256
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))


def stats(v):
    v = np.asarray(v)
    s = np.diff(v) / LSB
    band = s[140:255]
    over = int(np.argmax(v[128:] > v[127]))
    return dict(med=np.median(band), p90=np.percentile(band, 90), mx=band.max(), c=[s[c] - 1 for c in (127, 159, 191, 223)],
                over=over, v255=v[255], v180=v[180], mono=bool((s > 0).all()))


if __name__ == '__main__':
    pat = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build', 'r2r_curve_*.json')
    print(f'{"case":24s} step x  p90 x  max x   DNL 127  159   191   223  overlap  V255    V180 (ideal 1.2656)')
    for f in sorted(glob.glob(pat)):
        st = stats(json.load(open(f)))
        print(f'{os.path.basename(f)[10:-5]:24s} {st["med"]:.3f}  {st["p90"]:.3f}  {st["mx"]:.3f}  '
              + ' '.join(f'{x:+6.2f}' for x in st['c']) + f'  {st["over"]:4d}   {st["v255"]:.4f}  {st["v180"]:.4f}')
