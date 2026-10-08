"""
Analyse sim/tx/vapwr.sh: per supply case, TX power into the dipole, VAPWR
droop at turn-on (minimum in the first 20 ns after the key), the mean level
and peak-to-peak ripple while on (25..60 ns), and the frequency.

    python sim/tx/vapwr.py
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from rawread import read_raw
from tx_explore import ring_metrics

import numpy as np

B = os.path.join(HERE, '..', '..', 'build')


def key(p):
    l, c = os.path.basename(p)[len('vapwr_'):-len('.raw')].split('_')
    unit = lambda s: float(s.rstrip('npf') or 0) * {'n': 1e-9, 'p': 1e-12, 'f': 1e-15}.get(s[-1:], 1)
    return unit(l), unit(c)


if __name__ == '__main__':
    print(f'{"L":>6} {"Cdec":>6} {"P73 dBm":>8} {"f MHz":>7} {"VAPWR min":>9} {"mean on":>8} {"ripple pp":>9}')
    for p in sorted(glob.glob(os.path.join(B, 'vapwr_*.raw')), key=key):
        v = read_raw(p)[0]['vars']
        m = ring_metrics(v, 5e-9, 60e-9, drv=('out_p', 'out_n'))
        t = np.real(v['time'])
        va = np.real(v['v(vapwr)'])
        on = (t > 25e-9) & (t < 60e-9)
        early = (t > 5e-9) & (t < 25e-9)
        l, c = key(p)
        print(f'{l * 1e9:5.0f}n {c * 1e12:5.0f}p {m["pdbm"]:8.2f} {m["f"] / 1e6:7.1f} {va[early].min():9.3f} '
              f'{va[on].mean():8.3f} {np.ptp(va[on]):9.3f}')
