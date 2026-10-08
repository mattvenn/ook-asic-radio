"""
TX picture from the keyed full-chain run (sim/tx/tx_explore.py ring tt):
ring -> W9/3 -> skewed level shifter -> thick buffers -> antiphase drivers ->
pad_model x2 -> dipole (73 ohm, DC-blocked). Writes sim/plots/tx.png.

    python sim/tx/plot_tx.py [corner]
"""
import os
import sys

import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from rawread import read_raw

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

corner = sys.argv[1] if len(sys.argv) > 1 else 'tt'
v = read_raw(os.path.join(ROOT, 'build', 'tx', f'txr_{corner}_22.raw'))[0]['vars']
t = np.real(v['time']) * 1e9
g = lambda k: np.real(v[k])
fig, ax = plt.subplots(4, 2, figsize=(15, 10), gridspec_kw={'width_ratios': [2.2, 1]})
zoom = (t > 40) & (t < 46)
rows = [('ring output (1.8 V)', ['v(ring)'], 'V'),
        ('level-shifter latch nodes A, B (3.3 V)', ['v(a)', 'v(b)'], 'V'),
        ('driver outputs, one per dipole arm (antiphase)', ['v(drv_p)', 'v(drv_n)'], 'V'),
        ('dipole: arm-to-arm voltage (RF)', None, 'V')]
for i, (title, keys, unit) in enumerate(rows):
    for col, m in enumerate((np.ones_like(t, bool), zoom)):
        a = ax[i, col]
        if keys:
            for k in keys:
                a.plot(t[m], g(k)[m], lw=0.8 if col == 0 else 1.2, label=k.replace('v(', '').replace(')', ''))
        else:
            vd = g('v(ant_p)') - g('v(ant_n)')
            a.plot(t[m], vd[m], color='C3', lw=0.6 if col == 0 else 1.2)
        a.grid(alpha=0.3)
        a.set_title(title + (' (zoom)' if col else ''), fontsize=9)
        if keys and len(keys) > 1:
            a.legend(fontsize=7, loc='upper right')
        if col == 0:
            a.axvspan(5, 60, color='C2', alpha=0.06)
for a in ax[-1]:
    a.set_xlabel('ns')
ax[0, 0].text(6, 1.95, 'enable on 5-60 ns', fontsize=8, color='C2')
fig.suptitle(f'TX, transistor level ({corner}): 23-stage ring -> skewed level shifter -> thick buffers -> '
             'antiphase drivers -> pad x2 -> 73 ohm dipole', fontsize=11)
fig.tight_layout()
out = os.path.join(ROOT, 'sim', 'plots', 'tx.png')
fig.savefig(out, dpi=100)
print('wrote', out)
