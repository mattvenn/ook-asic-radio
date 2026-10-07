"""
Whole-RX pictures from the transistor-level runs:

  sim/plots/rx_rf.png : RF half (antenna -> pad -> 6 stages -> log detector)
      a) signal amplitude at each point of the chain for a -60 dBm tone
      b) the 434 MHz waveform at each point (same few ns)
      c) detector output when the carrier is keyed on and off
  sim/plots/rx_bb.png : baseband half (det -> LPF -> SC average -> comparator)
      for -70 and -94 dBm, one Gold burst: detector / LPF / reference,
      TX chips vs sampled comparator bits, trim servo, and the bit-exact
      digital correlator fed with the sampled comparator bits.

Needs: build/rx_rf_tone.raw, rx_rf_key.raw (sim/rx/rf.sh),
       build/rx_bb_<lvl>.raw (sim/rx/bb.sh), build/det_<lvl>.npz (gen_det.py)

    python sim/rx/plot_rx.py
"""
import os
import sys

import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'model'))
from rawread import read_raw
import radio

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

B = os.path.join(ROOT, 'build')
F0 = 433.92e6
NODES = [('antenna EMF', 'emf'), ('pad (chip side)', 'pad'), ('stage 1', 'o1'), ('stage 2', 'o2'),
         ('stage 3', 'o3'), ('stage 4', 'o4'), ('stage 5', 'o5'), ('stage 6 (out)', 'out')]


def diff(v, n):
    if n == 'out':
        return np.real(v['v(out_p)'] - v['v(out_n)'])
    return np.real(v[f'v({n}_p)'] - v[f'v({n}_n)']) if f'v({n}_p)' in v else \
        np.real(v[f'v({n}p)'] - v[f'v({n}n)'])


def amp434(t, y):
    """Amplitude of the 434 MHz component (least squares, uniform resample)."""
    g = np.arange(t[0], t[-1], 20e-12)
    yy = np.interp(g, t, y)
    m = np.array([np.ones_like(g), np.sin(2 * np.pi * F0 * g), np.cos(2 * np.pi * F0 * g)]).T
    c, *_ = np.linalg.lstsq(m, yy, rcond=None)
    return np.hypot(c[1], c[2])


def fig_rf():
    v = read_raw(os.path.join(B, 'rx_rf_tone.raw'))[0]['vars']
    t = np.real(v['time'])
    fig = plt.figure(figsize=(15, 10))
    gs = fig.add_gridspec(len(NODES), 3, width_ratios=[1.1, 1.2, 1.2])
    # a) level diagram
    ax = fig.add_subplot(gs[:, 0])
    amps = [amp434(t, diff(v, n)) for _, n in NODES]
    x = np.arange(len(NODES))
    ax.semilogy(x, np.array(amps) * 1e3, 'o-', color='C0')
    for xi, a in zip(x, amps):
        ax.annotate(f'{a * 1e3:.3g} mV', (xi, a * 1e3), textcoords='offset points', xytext=(6, -12), fontsize=8)
    ax.axhline(1350, color='C3', ls='--', lw=1)
    ax.text(0.1, 1500, 'stage limits (~1.35 V diff; a clipped wave fits a bit higher)', color='C3', fontsize=8)
    ax.set_xticks(x, [nm for nm, _ in NODES], rotation=35, ha='right', fontsize=8)
    ax.set_ylabel('434 MHz amplitude, differential (mV)')
    ax.set_title('a) -60 dBm tone: level along the chain', fontsize=10)
    ax.grid(True, which='both', alpha=0.3)
    # b) waveforms, same 6 ns
    w = (t > t[-1] - 6e-9)
    for i, (nm, n) in enumerate(NODES):
        a = fig.add_subplot(gs[i, 1])
        y = diff(v, n)[w]
        a.plot((t[w] - t[w][0]) * 1e9, (y - y.mean()) * 1e3, color=f'C{i % 10}', lw=1)
        a.set_ylabel(nm, fontsize=7, rotation=0, ha='right', va='center')
        a.tick_params(labelsize=7)
        a.grid(alpha=0.3)
        if i == 0:
            a.set_title('b) 434 MHz waveform at each point (mV, own scale per row)', fontsize=10)
        if i < len(NODES) - 1:
            a.set_xticklabels([])
        else:
            a.set_xlabel('ns', fontsize=8)
    # c) keyed carrier -> detector
    k = read_raw(os.path.join(B, 'rx_rf_key.raw'))[0]['vars']
    tk = np.real(k['time'])
    a1 = fig.add_subplot(gs[:4, 2])
    a1.plot(tk * 1e6, diff(k, 'out'), lw=0.3, color='C7')
    a1.set_ylabel('stage 6 output (V diff)', fontsize=8)
    a1.set_title('c) carrier keyed on 0.5-2.5 us (-60 dBm)', fontsize=10)
    a1.grid(alpha=0.3)
    a1.set_xticklabels([])
    a2 = fig.add_subplot(gs[4:, 2])
    a2.plot(tk * 1e6, np.real(k['v(det)']), color='C3')
    a2.set_ylabel('log detector output det (V)', fontsize=8)
    a2.set_xlabel('us')
    a2.grid(alpha=0.3)
    a2.text(0.02, 0.05, 'det falls when power rises (log of the power summed over 6 taps)',
            transform=a2.transAxes, fontsize=8)
    fig.suptitle('RX RF half, transistor level: antenna -> pad -> 6 gain stages -> log detector (tt)', fontsize=12)
    fig.tight_layout()
    out = os.path.join(ROOT, 'sim', 'plots', 'rx_rf.png')
    fig.savefig(out, dpi=100)
    print('wrote', out, ' amplitudes (mV):', ', '.join(f'{nm}={a * 1e3:.3g}' for (nm, _), a in zip(NODES, amps)))


def sample_bits(t, comp, n):
    """The digital samples comp once per 13 us (just before phi1 rises)."""
    ts = np.arange(1, n + 1) * 13e-6 - 50e-9
    return ts, (np.interp(ts, t, comp) > 0.9).astype(np.uint8)


def fig_bb(levels):
    fig = plt.figure(figsize=(7.5 * len(levels), 13))
    gs = fig.add_gridspec(5, len(levels), height_ratios=[3, 0.8, 0.8, 1.2, 1.6], hspace=0.75)
    axs = np.empty((5, len(levels)), dtype=object)
    for col in range(len(levels)):
        axs[0, col] = fig.add_subplot(gs[0, col])
        for r_ in (1, 2, 3):
            axs[r_, col] = fig.add_subplot(gs[r_, col], sharex=axs[0, col])
        axs[4, col] = fig.add_subplot(gs[4, col])
    for col, lvl in enumerate(levels):
        v = read_raw(os.path.join(B, f'rx_bb_{lvl}.raw'))[0]['vars']
        d = np.load(os.path.join(B, f'det_{lvl}.npz'))
        t = np.real(v['time'])
        n = int(t[-1] / 13e-6) - 1
        ts, bits = sample_bits(t, np.real(v['v(comp)']), n)
        # digital: bit-exact correlator on the sampled comparator bits
        rx = radio.RxDigital(0x5A)
        scores = np.empty(n)
        for i, c in enumerate(bits):
            rx.step(int(c))
            scores[i] = rx.last_score
        # truth: TX chip at each sample time
        lead, spc = int(d['lead']), int(d['spc'])
        on = d['on']
        truth = on[np.clip((ts * 1e6).astype(int), 0, len(on) - 1)]
        burst = (ts * 1e6 >= lead) & (ts * 1e6 < lead + 127 * spc)
        agree = np.mean(bits[burst] == truth[burst]) * 100
        base = np.median(np.real(v['v(lpf)'])[(t > 1.0e-3) & (t < 1.5e-3)])
        w = (t > 3.0e-3) & (t < 6.0e-3)
        ax = axs[0, col]
        ax.plot(t[w] * 1e3, (np.real(v['v(det)'])[w] - base) * 1e3, lw=0.4, color='C7', alpha=0.6,
                label='det: log detector output (1 us blocks)')
        ax.plot(t[w] * 1e3, (np.real(v['v(lpf)'])[w] - base) * 1e3, lw=1.2, color='C0',
                label='LPF out (14 kHz RC) -> comparator (-)')
        ax.plot(t[w] * 1e3, (np.real(v['v(avg)'])[w] - base) * 1e3, lw=2, color='C1',
                label='SC average (0.47 ms) -> comparator (+)')
        on_lvl = np.median(np.real(v['v(lpf)'])[w][np.interp(t[w] * 1e6, np.arange(len(on)), on) > 0.5])
        swing = (base - on_lvl) * 1e3
        ax.set_title(f'{lvl} dBm: chips "on" pull det down by ~{swing:.1f} mV', fontsize=10)
        ax.set_ylabel('mV (re noise-only level)')
        ax.legend(fontsize=7, loc='lower right')
        if lvl < -85:
            lim = np.percentile(np.abs((np.real(v['v(lpf)'])[w] - base) * 1e3), 99.5) * 2.5
            ax.set_ylim(-lim, lim)
        sw = (ts > 3.0e-3) & (ts < 6.0e-3)
        axs[1, col].step(ts[sw] * 1e3, truth[sw], where='post', color='k')
        axs[1, col].set_ylabel('TX chips\n(truth)', fontsize=8)
        axs[2, col].step(ts[sw] * 1e3, bits[sw], where='post', color='C3')
        axs[2, col].set_ylabel('comparator\n(sampled)', fontsize=8)
        axs[2, col].set_title(f'sampled comparator bit = TX chip {agree:.0f}% of the time (whole burst)',
                              fontsize=9)
        tw = (t > 3.0e-3) & (t < 6.0e-3)
        axs[3, col].plot(t[tw] * 1e3, np.real(v['v(trim)'])[tw], color='C2')
        axs[3, col].set_ylabel('trim DAC (V)\nservo stand-in', fontsize=8)
        # correlator over the whole run: the full 127-chip code is only in the
        # register at the end of the burst
        a = axs[4, col]
        a.plot(ts * 1e3, scores, color='C4', lw=1)
        a.axhline(radio.THRESH, color='C3', ls='--', lw=1)
        a.axvspan(lead / 1e3, (lead + 127 * spc) / 1e3, color='k', alpha=0.06)
        a.text(lead / 1e3 + 0.1, 52, 'burst being received', fontsize=8)
        a.set_ylabel('correlator\nscore /127', fontsize=8)
        a.set_xlabel('ms (whole run)')
        a.set_ylim(45, 130)
        peak = int(scores.max())
        tpk = ts[np.argmax(scores)] * 1e3
        verdict = 'DETECTED' if peak >= radio.THRESH else 'not detected'
        a.set_title(f'digital correlator: peak {peak}/127 at end of burst -> {verdict}\n'
                    f'(threshold {radio.THRESH}, chance ~64)', fontsize=9)
        for xx in (3.0, 6.0):
            a.axvline(xx, color='C0', lw=0.6, ls=':')
        for r_ in range(5):
            axs[r_, col].grid(alpha=0.3)
        for r_ in (0, 1, 2):
            plt.setp(axs[r_, col].get_xticklabels(), visible=False)
        axs[3, col].set_xlabel('ms (3 ms window, dotted lines below)', fontsize=8)
    fig.suptitle('RX baseband half, transistor level: det -> LPF -> SC average -> comparator -> '
                 'bit-exact digital (one Gold burst, 3 ms window shown)', fontsize=12)
    out = os.path.join(ROOT, 'sim', 'plots', 'rx_bb.png')
    fig.savefig(out, dpi=100, bbox_inches='tight')
    print('wrote', out)


if __name__ == '__main__':
    fig_rf()
    fig_bb([-70, -94])
