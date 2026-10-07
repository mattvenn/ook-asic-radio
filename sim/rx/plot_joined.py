"""
Plot the fully joined RX transient (sim/rx/joined.sh) and compare it with
what the split model (gen_det.py mapping) assumes.

Per level: key (TX on/off) + det, LPF out + SC average, comparator + trim.
Prints, for chips on vs off (settled part of each chip): the mean det and
LPF levels, the on-off swing, and the LPF noise rms, next to the split
model's predicted det levels (CW detector curve shifted -3.8 dB, noise floor
NF 11 dB over 450 MHz).

    python sim/rx/plot_joined.py [levels...]     (default -70 -90)
"""
import os
import sys

import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'bench'))
from rawread import read_raw
import rx_model as rxm

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

B = os.path.join(ROOT, 'build')
ON = [(60e-6, 164e-6), (268e-6, 372e-6)]      # chip-on intervals (joined.sh Vkey)
OFF = [(20e-6, 60e-6), (164e-6, 268e-6), (372e-6, 400e-6)]
SETTLE = 40e-6                                  # skip the LPF transition after each edge


def split_model_det(lvl):
    """det levels the split model (gen_det.py) uses for noise-only and chip-on."""
    rows = np.loadtxt(os.path.join(ROOT, 'sim', 'logdet', 'transfer_cw.txt'), skiprows=1)
    pn = rxm.KT * 10 ** (11 / 10) * 450e6
    ps = 10 ** ((lvl - 30) / 10)
    f = lambda p: np.interp(10 * np.log10(p) + 30 - 3.8, rows[:, 0], rows[:, 1])
    return f(pn), f(pn + ps)


def window_stats(t, y, spans):
    vals = []
    for a, b in spans:
        m = (t >= a + SETTLE) & (t < b)
        if m.any():
            vals.append(y[m])
    v = np.concatenate(vals) if vals else np.array([np.nan])
    return v.mean(), v.std()


def main(levels):
    fig, axs = plt.subplots(3, len(levels), figsize=(7.5 * len(levels), 9), sharex=True, squeeze=False)
    print(f'{"level":>6} {"":>14} {"det off":>9} {"det on":>9} {"swing mV":>9} {"LPF swing mV":>12} '
          f'{"LPF noise mV":>12}')
    for col, lvl in enumerate(levels):
        path = os.path.join(B, f'joined_{lvl}.raw')
        if not os.path.exists(path):
            print(f'{lvl}: {path} missing (still running?)')
            continue
        v = read_raw(path)[0]['vars']
        t = np.real(v['time'])
        det, lpf, avg = (np.real(v[k]) for k in ('v(det)', 'v(lpf)', 'v(avg)'))
        d_off, _ = window_stats(t, det, OFF)
        d_on, _ = window_stats(t, det, ON)
        l_off, n_off = window_stats(t, lpf, OFF)
        l_on, n_on = window_stats(t, lpf, ON)
        m_off, m_on = split_model_det(lvl)
        print(f'{lvl:6d} {"joined (sim)":>14} {d_off:9.4f} {d_on:9.4f} {(d_off - d_on) * 1e3:9.2f} '
              f'{(l_off - l_on) * 1e3:12.2f} {n_off * 1e3:6.2f}/{n_on * 1e3:.2f}')
        print(f'{"":6s} {"split model":>14} {m_off:9.4f} {m_on:9.4f} {(m_off - m_on) * 1e3:9.2f}')
        us = t * 1e6
        ax = axs[0, col]
        ax.plot(us, det, lw=0.3, color='C7', label='det (real log detector, with RF noise)')
        ax.set_ylabel('det (V)')
        a2 = ax.twinx()
        a2.plot(us, np.real(v['v(key)']), color='k', lw=1, label='TX on (key)')
        a2.set_ylim(-0.1, 4)
        a2.set_yticks([])
        ax.set_title(f'{lvl} dBm, fully joined transistor-level RX', fontsize=10)
        ax.legend(fontsize=7, loc='lower left')
        ax = axs[1, col]
        ax.plot(us, lpf * 1e3, color='C0', label='LPF out -> comparator (-)')
        ax.plot(us, avg * 1e3, color='C1', lw=2, label='SC average -> comparator (+)')
        ax.axhline(l_off * 1e3, color='C0', ls=':', lw=0.8)
        ax.axhline(l_on * 1e3, color='C0', ls=':', lw=0.8)
        ax.set_ylabel('mV')
        ax.set_title(f'LPF on/off swing {(l_off - l_on) * 1e3:.2f} mV '
                     f'(split model det swing {(m_off - m_on) * 1e3:.2f} mV), LPF noise {n_off * 1e3:.2f} mV rms',
                     fontsize=9)
        ax.legend(fontsize=7)
        ax = axs[2, col]
        ax.plot(us, np.real(v['v(comp)']), color='C3', lw=0.8, label='comparator out')
        ax.plot(us, np.real(v['v(trim)']), color='C2', label='trim (servo stand-in)')
        ax.set_xlabel('us')
        ax.legend(fontsize=7)
        for r in range(3):
            axs[r, col].grid(alpha=0.3)
    fig.tight_layout()
    out = os.path.join(ROOT, 'sim', 'plots', 'rx_joined.png')
    fig.savefig(out, dpi=100)
    print('wrote', out)


if __name__ == '__main__':
    main([int(a) for a in sys.argv[1:]] or [-70, -90])
