"""
Keying test: ring enable toggled at 1 kHz (board.py square 1000), capture
a few ms at full rate and measure turn-on/turn-off time and frequency
settling (chirp) after enable.

    python bench/keying.py [rate_hz]
"""
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
BW = 40e6       # envelope / frequency bandwidth around the carrier


def edges(env, fs, thresh):
    on = env > thresh
    d = np.diff(on.astype(int))
    return np.flatnonzero(d == 1), np.flatnonzero(d == -1)


def transition_time(env, i, fs, rising, win=2e-6):
    """10-90% time around edge index i."""
    n = int(win * fs)
    seg = env[max(0, i - n): i + n]
    hi = np.median(env[env > env.max() * 0.5])
    lo, hi10, hi90 = 0, 0.1 * hi, 0.9 * hi
    if rising:
        a = np.flatnonzero(seg > hi10); b = np.flatnonzero(seg > hi90)
    else:
        a = np.flatnonzero(seg < hi90); b = np.flatnonzero(seg < hi10)
    if len(a) == 0 or len(b) == 0:
        return float('nan')
    return (b[0] - a[0]) / fs


def main(rate=1000):
    os.makedirs(DATA, exist_ok=True)
    print(board.run('square', rate))
    time.sleep(4)   # board re-inits the SDK and loads the shuttle first
    sc = Scope()
    sc.setup_channel(1, scale=0.01, fifty=True)
    t, v, fs = sc.capture(1, duration=2.2 / rate)
    sc.close()
    print(f'captured {len(v)/1e6:.1f} Mpts at {fs/1e9:.2f} GSa/s')

    f, dbm = rf.spectrum_dbm(v, fs)
    fc, pc = rf.peak(f, dbm, 400e6, 650e6)
    bb = rf.envelope(v, fs, fc, BW)
    env = np.abs(bb)
    # smooth to ~20 ns for edge finding
    k = max(1, int(20e-9 * fs))
    env_s = np.convolve(env, np.ones(k) / k, mode='same')
    thresh = 0.5 * np.median(env_s[env_s > 0.5 * env_s.max()])
    rise, fall = edges(env_s, fs, thresh)
    print(f'carrier {fc/1e6:.2f} MHz; {len(rise)} rising, {len(fall)} falling edges')

    # instantaneous frequency (offset from fc), smoothed over 200 ns
    ph = np.unwrap(np.angle(bb))
    finst = np.gradient(ph) * fs / (2 * np.pi)
    m = max(1, int(200e-9 * fs))
    finst_s = np.convolve(finst, np.ones(m) / m, mode='same')

    results = []
    for r in rise:
        tr = transition_time(env_s, r, fs, True)
        # frequency vs time after turn-on, while carrier present
        def fat(dt):
            i = r + int(dt * fs)
            return fc + finst_s[i] if i < len(v) and env_s[i] > thresh else np.nan
        chirp = [(dt, fat(dt)) for dt in (0.5e-6, 1e-6, 2e-6, 5e-6, 10e-6, 50e-6, 200e-6, 400e-6)]
        results.append((tr, chirp))
        print(f'  turn-on 10-90% {tr*1e9:.0f} ns; freq after enable: ' +
              ', '.join(f'{dt*1e6:g}us {fr/1e6:.2f}' for dt, fr in chirp if not np.isnan(fr)))
    for fl in fall:
        n1, n5 = int(1e-6 * fs), int(5e-6 * fs)
        before = np.median(env_s[max(0, fl - n5): fl - n1])
        after = [np.median(env_s[fl + int(a * fs): fl + int(b * fs)])
                 for a, b in ((1e-6, 5e-6), (20e-6, 50e-6), (100e-6, 300e-6))
                 if fl + int(b * fs) < len(v)]
        print(f'  turn-off 10-90% {transition_time(env_s, fl, fs, False)*1e9:.0f} ns; '
              f'on {before*1e3:.2f} mV, off ' +
              ', '.join(f'{x*1e3:.3f} mV ({20*np.log10(x/before):.0f} dB)' for x in after))

    stamp = time.strftime('%Y%m%d_%H%M%S')
    base = os.path.join(DATA, f'keying_{rate}Hz_{stamp}')
    np.savez(base + '.npz', t=t, v=v, fs=fs, fc=fc)

    fig, ax = plt.subplots(3, 1, figsize=(11, 9))
    dec = max(1, len(v) // 20000)
    ax[0].plot(t[::dec] * 1e3, env_s[::dec] * 1e3)
    ax[0].set_xlabel('ms'); ax[0].set_ylabel('envelope mV'); ax[0].grid()
    ax[0].set_title(f'ring 1 OOK at {rate} Hz, carrier {fc/1e6:.2f} MHz')
    if len(rise):
        r = rise[0]
        a, b = max(0, r - int(1e-6 * fs)), min(len(v), r + int(20e-6 * fs))
        tt = (np.arange(a, b) - r) / fs * 1e6
        ax[1].plot(tt, env_s[a:b] * 1e3); ax[1].set_ylabel('envelope mV')
        ax[1].set_xlabel('us from enable'); ax[1].grid(); ax[1].set_title('turn-on detail')
        good = env_s[a:b] > thresh
        ax[2].plot(tt[good], (fc + finst_s[a:b][good]) / 1e6, '.', ms=1)
        ax[2].set_ylabel('inst. freq MHz'); ax[2].set_xlabel('us from enable'); ax[2].grid()
        ax[2].set_title('frequency settling after enable (200 ns smoothing)')
    fig.tight_layout(); fig.savefig(base + '.png', dpi=110)
    print('saved', base + '.{npz,png}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1000)
