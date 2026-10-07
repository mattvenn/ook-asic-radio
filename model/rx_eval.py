"""
Phase 1: soft vs hard (1-bit) code-mode correlator, on the same channel
model as bench/scheme_compare.py (wideband LNA, log detector, RC LPF).

Integer timing as in hardware: CLK 10 MHz, chip = 1040 clocks (9615 chip/s),
envelope sampled every 130 clocks (8 samples/chip), 4 chip-timing phases.
The log detector output is expressed in 8-bit DAC LSBs (0.44 dB/LSB).

  soft : chip value = sum of its 8 samples; Pearson correlation over 127 chips
         (reference only: needs ~4 x 127 x 11 bits of storage)
  hard : comparator vs DAC; DAC tracks the median (+/-1 LSB per sample);
         chip bit = majority of its 8 comparator decisions; score =
         popcount(XNOR(127-bit register, code)); ~4 x 127 flops

Both detect at the same z = 6 false-alarm point (rho >= 6/sqrt(127)).
A code-mode send is 3 bursts; the RX acts on 2 of 3, so per-send success
is 3p^2 - 2p^3 for per-burst detection probability p.

    python model/rx_eval.py
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'bench'))
import scheme_compare as ch          # channel: received_envelope(), cases
from gold import gold, LEN

CODE = 0x5A
SPC = 104                    # envelope samples (1 MSa/s) per chip: 1040 clk / 10
SAMP = 13                    # envelope samples per RX sample: 130 clk / 10
S = SPC // SAMP              # 8 RX samples per chip
PHASES = (0, 2, 4, 6)        # chip-timing phases, in RX samples
Z_T = 6.0
RHO_T = Z_T / np.sqrt(LEN)                       # 0.532
HARD_T = int(np.ceil(LEN / 2 + Z_T * np.sqrt(LEN) / 2))   # popcount threshold (97)
LSB_DB = 0.44
LEVELS = np.arange(-64, -108, -4)
TRIALS = 6
CASES = ('noise', 'fading', 'bursty')
ch.REC = 20e-3


def to_lsb(y_db):
    """log detector + 8-bit DAC scale: dB -> LSB (float, as the analog sees it)."""
    return np.clip((y_db + 140.0) / LSB_DB, 0, 255)


def chips_at_phase(x, p):
    n = (len(x) - p) // S
    return x[p:p + n * S].reshape(n, S)


def soft_detect(v, code_pm):
    best = -1.0
    for p in PHASES:
        c = chips_at_phase(v, p).sum(axis=1)
        if len(c) < LEN:
            continue
        w = np.lib.stride_tricks.sliding_window_view(c, LEN)
        wc = w - w.mean(axis=1, keepdims=True)
        rho = (wc @ code_pm) / (np.sqrt((wc ** 2).sum(axis=1)) * np.sqrt(LEN) + 1e-12)
        best = max(best, rho.max())
    return best >= RHO_T, best


def hard_frontend(v):
    """Bit-exact comparator + median-tracking DAC (integer DAC code)."""
    dac = int(round(v[0]))
    comp = np.empty(len(v), np.uint8)
    for i, x in enumerate(v):
        c = 1 if x > dac else 0
        comp[i] = c
        dac = min(255, dac + 1) if c else max(0, dac - 1)
    return comp


def hard_detect(comp, code_bits):
    best = 0
    for p in PHASES:
        m = chips_at_phase(comp, p).sum(axis=1)
        bits = (m >= S // 2 + 1) | ((m == S // 2) & chips_at_phase(comp, p)[:, -1].astype(bool))
        if len(bits) < LEN:
            continue
        w = np.lib.stride_tricks.sliding_window_view(bits.astype(np.uint8), LEN)
        score = (w == code_bits).sum(axis=1)
        best = max(best, int(score.max()))
    return best >= HARD_T, best


def main():
    code_bits = gold(CODE)
    code_pm = 2.0 * code_bits - 1
    on = np.repeat(code_bits.astype(bool), SPC)
    rng = np.random.default_rng(11)
    print(f'thresholds: soft rho >= {RHO_T:.3f}, hard popcount >= {HARD_T}/127')

    # false alarms on signal-free records (each record = ~1000 tests per phase)
    fa_s = fa_h = 0
    for case in CASES:
        for _ in range(3):
            y = ch.received_envelope(on, 0, 0.0, case, rng)
            v = to_lsb(y[::SAMP])
            fa_s += soft_detect(v, code_pm)[0]
            fa_h += hard_detect(hard_frontend(v), code_bits)[0]
    print(f'false alarms on 9 signal-free records: soft {fa_s}, hard {fa_h}')

    res = {(c, k): [] for c in CASES for k in ('soft', 'hard')}
    for case in CASES:
        for lvl in LEVELS:
            ok = {'soft': 0, 'hard': 0}
            for _ in range(TRIALS):
                st = int(rng.uniform(1e-3, ch.REC - 14.5e-3) * 1e6)
                y = ch.received_envelope(on, st, 10 ** ((lvl - 30) / 10), case, rng)
                v = to_lsb(y[::SAMP])
                ok['soft'] += soft_detect(v, code_pm)[0]
                ok['hard'] += hard_detect(hard_frontend(v), code_bits)[0]
            for k in ok:
                res[(case, k)].append(ok[k] / TRIALS)
            print(f'  {case:7s} {lvl:4d} dBm  soft {ok["soft"]}/{TRIALS}  hard {ok["hard"]}/{TRIALS}', flush=True)

    print('\nper-send success (2 of 3 bursts) >= 90%, lowest level:')
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.5), sharey=True)
    for ax, case in zip(axs, CASES):
        for k, mk in (('soft', 'o'), ('hard', 's')):
            p = np.array(res[(case, k)])
            send = 3 * p ** 2 - 2 * p ** 3
            good = [l for l, s in zip(LEVELS, send) if s >= 0.9]
            print(f'  {case:7s} {k:4s}  {min(good) if good else None} dBm')
            ax.plot(LEVELS, p * 100, marker=mk, ls=':', label=f'{k}: per burst')
            ax.plot(LEVELS, send * 100, marker=mk, label=f'{k}: per send (2 of 3)')
        ax.set_title(case); ax.set_xlabel('received power (dBm)'); ax.grid(); ax.invert_xaxis()
    axs[0].set_ylabel('detected (%)'); axs[0].legend(fontsize=8)
    fig.suptitle('Gold-127 code detection: soft (multi-bit) vs hard (1-bit, median-tracking DAC)')
    out = os.path.join(HERE, 'rx_eval.png')
    fig.tight_layout(); fig.savefig(out, dpi=110)
    print('saved', out)


if __name__ == '__main__':
    main()
