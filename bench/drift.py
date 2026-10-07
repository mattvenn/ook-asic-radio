"""
Log the ring oscillator frequency and level over time (TX left running).

    python bench/drift.py [minutes] [interval_s] [note]

Writes bench/data/drift_<time>.csv as it goes and a plot at the end.
Ctrl-C stops early and still plots.
"""
import csv
import os
import sys
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import rf
from scope import Scope

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
BAND = (400e6, 650e6)
DURATION = 20e-6        # 50 kHz bins; interpolation gets a few kHz


def plot(path, rows, note):
    t = np.array([r[0] for r in rows]) / 60
    f = np.array([r[1] for r in rows]) / 1e6
    p = np.array([r[2] for r in rows])
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    a1.plot(t, f, '.-'); a1.set_ylabel('MHz'); a1.grid()
    a1.set_title(f'ring osc drift {note}: {f.min():.2f}..{f.max():.2f} MHz '
                 f'(span {(f.max()-f.min())*1e3:.0f} kHz, {(f.max()-f.min())/f.mean()*1e6:.0f} ppm)')
    a2.plot(t, p, '.-'); a2.set_ylabel('dBm'); a2.set_xlabel('minutes'); a2.grid()
    fig.tight_layout(); fig.savefig(path, dpi=110)
    print('saved', path)


def main(minutes=15, interval=5, note=''):
    os.makedirs(DATA, exist_ok=True)
    sc = Scope()
    sc.setup_channel(1, scale=0.01, fifty=True)
    stamp = time.strftime('%Y%m%d_%H%M%S')
    base = os.path.join(DATA, f'drift_{stamp}')
    rows = []
    t0 = time.time()
    with open(base + '.csv', 'w', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['t_s', 'f_hz', 'p_dbm'])
        try:
            while time.time() - t0 < minutes * 60:
                tn = time.time()
                _, v, fs = sc.capture(1, duration=DURATION)
                f, dbm = rf.spectrum_dbm(v, fs)
                f0, p0 = rf.peak(f, dbm, *BAND)
                rows.append((tn - t0, f0, p0))
                wr.writerow([f'{tn - t0:.1f}', f'{f0:.0f}', f'{p0:.1f}'])
                fh.flush()
                print(f'{(tn - t0)/60:6.2f} min  {f0/1e6:9.4f} MHz  {p0:6.1f} dBm', flush=True)
                time.sleep(max(0, interval - (time.time() - tn)))
        except KeyboardInterrupt:
            pass
    if rows:
        plot(base + '.png', rows, note)
    sc.close()


if __name__ == '__main__':
    a = sys.argv[1:]
    main(float(a[0]) if a else 15, float(a[1]) if len(a) > 1 else 5,
         ' '.join(a[2:]))
