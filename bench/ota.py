"""
Over-the-air level: averaged spectrum of the RX antenna on CH1 (50R).

    python bench/ota.py [--no-board] <distance_cm> [note]

Measures with the ring on, then off (noise floor), then turns the ring
back on. With --no-board (TX on a phone/battery running autorun.py) the
ring is left alone and the floor comes from bins next to the carrier. Appends to bench/data/ota.csv and saves the spectra.
"""
import csv
import os
import sys
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import board
import rf
from scope import Scope

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
BAND = (450e6, 600e6)       # where to look for the ring
DURATION = 10e-6            # per capture -> ~100 kHz resolution
N_AVG = 8


def avg_spectrum(sc):
    acc = None
    for _ in range(N_AVG):
        _, v, fs = sc.capture(1, duration=DURATION)
        f, dbm = rf.spectrum_dbm(v, fs)
        p = 10 ** (dbm / 10)
        acc = p if acc is None else acc + p
    return f, 10 * np.log10(acc / N_AVG), fs


def band_stats(f, dbm, f0=None):
    if f0 is None:
        f0, _ = rf.peak(f, dbm, *BAND)
    _, p0 = rf.peak(f, dbm, f0 - 2e6, f0 + 2e6)
    m = (f > BAND[0]) & (f < BAND[1]) & (np.abs(f - f0) > 3e6)
    return f0, p0, float(np.median(dbm[m]))


def main(dist_cm, note='', control=True):
    os.makedirs(DATA, exist_ok=True)
    sc = Scope()
    if sc.probe_atten(1) != 1:
        sys.exit('CH1 reports a probe attached; remove it before using 50 ohm')
    sc.setup_channel(1, scale=0.005, fifty=True)

    if control:
        board.run('on')
    f, on, fs = avg_spectrum(sc)
    f0, p_on, floor_on = band_stats(f, on)
    if control:
        board.run('off')
        _, off, _ = avg_spectrum(sc)
        _, p_off, floor_off = band_stats(f, off, f0)
        board.run('on')
    else:
        off, p_off, floor_off = np.full_like(on, np.nan), float('nan'), floor_on

    snr = p_on - floor_off
    print(f'{dist_cm} cm: ring {f0/1e6:.2f} MHz  on {p_on:.1f} dBm  '
          f'off(same bin) {p_off:.1f} dBm  floor {floor_off:.1f} dBm  '
          f'=> {snr:.1f} dB above floor (RBW ~{fs/len(f)/2/1e3:.0f} kHz)')

    stamp = time.strftime('%Y%m%d_%H%M%S')
    log = os.path.join(DATA, 'ota.csv')
    new = not os.path.exists(log)
    with open(log, 'a', newline='') as fh:
        wr = csv.writer(fh)
        if new:
            wr.writerow(['time', 'dist_cm', 'note', 'f_mhz', 'p_on_dbm',
                         'p_off_dbm', 'floor_dbm', 'snr_db'])
        wr.writerow([stamp, dist_cm, note, f'{f0/1e6:.3f}', f'{p_on:.1f}',
                     f'{p_off:.1f}', f'{floor_off:.1f}', f'{snr:.1f}'])

    base = os.path.join(DATA, f'ota_{dist_cm}cm_{stamp}')
    np.savez(base + '.npz', f=f, on=on, off=off, dist_cm=dist_cm, note=note)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(f / 1e6, off, label='ring off', alpha=0.7)
    ax.plot(f / 1e6, on, label='ring on', alpha=0.7)
    ax.set_xlim(0, 1000); ax.set_xlabel('MHz'); ax.set_ylabel('dBm (50R)')
    ax.set_title(f'OTA {dist_cm} cm {note}: {p_on:.1f} dBm @ {f0/1e6:.1f} MHz, {snr:.0f} dB above floor')
    ax.grid(); ax.legend(); fig.tight_layout(); fig.savefig(base + '.png', dpi=110)
    sc.close()


if __name__ == '__main__':
    args = sys.argv[1:]
    control = '--no-board' not in args
    args = [a for a in args if a != '--no-board']
    if not args:
        sys.exit(__doc__)
    main(args[0], ' '.join(args[1:]), control)
