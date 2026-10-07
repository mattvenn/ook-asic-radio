"""
Plot received level vs distance from bench/data/ota.csv (or a given csv),
with free-space (1/d) and near-field (1/d^3) reference slopes.

    python bench/sweep_plot.py [csv]
"""
import csv
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DATA, 'ota.csv')
rows = [r for r in csv.DictReader(open(path)) if r['dist_cm'].replace('.', '').isdigit()]
d = np.array([float(r['dist_cm']) / 100 for r in rows])
p = np.array([float(r['p_on_dbm']) for r in rows])
floor = np.array([float(r['floor_dbm']) for r in rows])

# least-squares fit of p = a - 10*n*log10(d): n is the path-loss exponent
A = np.column_stack([np.ones_like(d), -10 * np.log10(d)])
(a, n), *_ = np.linalg.lstsq(A, p, rcond=None)
print(f'fit: {a:.1f} dBm at 1 m, path-loss exponent n = {n:.2f} '
      f'(free space 2, near-field E ~ 6)')

dd = np.logspace(np.log10(d.min() * 0.8), np.log10(max(d.max() * 3, 10)), 50)
fig, ax = plt.subplots(figsize=(8, 5))
ax.semilogx(d, p, 'o-', label='measured')
ax.semilogx(dd, a - 10 * n * np.log10(dd), '--', label=f'fit n={n:.2f}')
ax.semilogx(dd, p[0] - 20 * np.log10(dd / d[0]), ':', label='free space 1/d')
ax.semilogx(d, floor, 'x', label='scope floor (100 kHz)')
ax.set_xlabel('distance (m)'); ax.set_ylabel('received (dBm, 50R)')
ax.set_title('519 MHz ring osc, 14.5 cm wires')
ax.grid(which='both', alpha=0.4); ax.legend()
out = os.path.splitext(path)[0] + '_sweep.png'
fig.tight_layout(); fig.savefig(out, dpi=110)
print('saved', out)
