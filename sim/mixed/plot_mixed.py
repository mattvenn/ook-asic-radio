"""
Analyse a mixed-signal run (sim/mixed/gen_mixed.py + ngspice): the RTL's trim
servo driving the real r2r ladder into the real comparator.

Checks (pin order of the d_cosim .so, end to end):
  - rx_en = 1 (RX role);
  - the code starts at 128 after reset;
  - every settled change of v(trim) is exactly +-1 LSB (1.8/256 V), one per servo
    tick (13 us): a reversed or shifted trim bus would give other step sizes.
Prints the servo's convergence and dither statistics, the comparator's duty
cycle and the event / LED pins; plots det, lpf / avg, trim (code), comp.

    python sim/mixed/plot_mixed.py <level>[_pex]
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

LSB = 1.8 / 256
SAMPLE = 13e-6          # 130 clocks at 10 MHz


def main(level):
    v = read_raw(os.path.join(ROOT, 'build', 'mixed', f'mixed_{level}.raw'))[0]['vars']
    t = np.real(v['time'])
    g = lambda k: np.real(v[k])
    det, lpf, avg, comp, trim = g('v(det)'), g('v(lpf)'), g('v(avg)'), g('v(comp)'), g('v(trim)')
    # every settled change of the ladder code (value 1 us after the change, once the
    # ladder + 1 pF have settled): the servo steps on every tick, so these must all
    # be +-1 LSB, about one per 13 us sample
    code_all = np.round(trim / LSB)
    steps, last = [], code_all[np.searchsorted(t, 5e-6)]
    for i in np.nonzero(np.diff(code_all))[0]:
        j = np.searchsorted(t, t[i] + 1e-6)
        if t[i] < 4e-6 or j >= len(t):
            continue
        if code_all[j] != last:
            steps.append(code_all[j] - last)
            last = code_all[j]
    steps = np.array(steps)
    n_ticks = int((t[-1] - 2e-6) / SAMPLE)
    ts = np.arange(5e-6, t[-1], SAMPLE) + SAMPLE / 2          # for the plot / statistics
    code = np.interp(ts, t, trim) / LSB
    rx_en = np.interp(10e-6, t, g('v(rx_en_a)'))
    print(f'{level} dBm, {t[-1] * 1e3:.2f} ms simulated, {n_ticks} servo ticks')
    print(f'  pin-order checks: rx_en = {rx_en:.2f} V (expect 1.8); first code {np.round(code[0]):.0f} '
          f'(expect 128); {len(steps)} settled ladder steps (expect ~{n_ticks}), sizes '
          f'{sorted(set(steps.astype(int)))} (expect -1 / +1 only)')
    ok = (abs(rx_en - 1.8) < 0.1 and round(code[0]) == 128 and set(steps.astype(int)) <= {-1, 1}
          and abs(len(steps) - n_ticks) <= 3)
    print('  ->', 'PIN ORDER OK' if ok else 'PIN ORDER PROBLEM')
    c = np.round(code)
    settle = np.argmax(np.abs(np.diff(c[:200])) > 0) if len(c) > 1 else 0
    tail = c[len(c) // 2:]
    print(f'  servo: code {c[0]:.0f} -> mean {tail.mean():.1f} (last half: min {tail.min():.0f}, max {tail.max():.0f}, '
          f'std {tail.std():.2f} LSB)')
    duty = np.mean(np.interp(ts, t, comp) > 0.9)
    print(f'  comparator ones density over the run: {duty:.2f}')
    ev = g('v(uio_out_4_a)')
    led = g('v(uo_out_7_a)')
    opens = np.nonzero((ev[1:] > 0.9) & (ev[:-1] <= 0.9))[0]
    print(f'  event-open pin rises: {len(opens)} at ms {np.round(t[opens] * 1e3, 3).tolist()}; '
          f'LED (DP) at end {led[-1]:.1f} V')

    fig, ax = plt.subplots(4, 1, figsize=(11, 10), sharex=True)
    ms = t * 1e3
    ax[0].plot(ms, det, lw=0.3, color='C7', label='det (PWL, gen_det.py)')
    ax[0].set_ylabel('V')
    ax[1].plot(ms, lpf * 1e3, color='C0', label='lpf -> comp (-)')
    ax[1].plot(ms, avg * 1e3, color='C1', label='avg -> comp (+)')
    ax[1].set_ylabel('mV')
    ax[2].step(ts * 1e3, c, where='mid', color='C2', label='trim code (from v(trim))')
    ax[2].set_ylabel('code')
    a2 = ax[2].twinx()
    a2.plot(ms, trim, color='C2', lw=0.3, alpha=0.4)
    a2.set_ylabel('v(trim) V')
    ax[3].plot(ms, comp, color='C3', lw=0.5, label='comparator out (real comp_ct)')
    ax[3].plot(ms, ev / 1.8 * 1.6 + 0.1, color='k', lw=0.8, label='event open (uio_out[4])')
    ax[3].set_xlabel('ms')
    for a in ax:
        a.legend(fontsize=7, loc='upper right')
        a.grid(alpha=0.3)
    ax[0].set_title(f'mixed-signal: RTL trim servo -> r2r -> comp_ct, det {level} dBm', fontsize=10)
    fig.tight_layout()
    out = os.path.join(ROOT, 'sim', 'plots', f'mixed_{level}.png')
    fig.savefig(out, dpi=100)
    print('wrote', out)


if __name__ == '__main__':
    main(sys.argv[1])
