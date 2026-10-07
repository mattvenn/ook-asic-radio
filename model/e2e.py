"""
End-to-end check of the bit-exact code-mode design through the channel model:
TX send (3 Gold bursts) -> wideband LNA noise (+fading / bursty interferer)
-> log detector -> analog comparator model (averaged reference, offset,
R2R trim) -> radio.RxDigital (bit-exact) -> LED toggle.

Success = exactly one LED toggle for a send. Also counts false toggles on a
wrong-code RX fed the same records, and on signal-free records.

    python model/e2e.py                       # the original assumptions
    python model/e2e.py --nf 11 --brf 450e6 --slope 12 --comp-noise-mv 0.3

The analog errors are given in mV at the detector output and converted to dB
with the detector slope (mV/dB): offset (default 2 mV), trim step (0.08 mV),
comparator input noise per decision (default 0). Defaults reproduce the
original run (NF 10 dB, 400 MHz, 16 mV/dB, noiseless comparator).
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'bench'))
import scheme_compare as ch
import radio
import rx_eval as r

CODE, WRONG = 0x5A, 0x11
LEAD_CHIPS = 40
LEVELS = (-70, -86, -90, -94, -98)
TRIALS = 5
CASES = ('noise', 'fading', 'bursty')


def send_onoff(code):
    chips = radio.tx_chips(code)
    return np.repeat(chips.astype(bool), r.SPC)


def run_record(on, p_w, case, rng):
    ch.REC = (LEAD_CHIPS + len(on) // r.SPC + 120) * r.SPC * 1e-6
    st = LEAD_CHIPS * r.SPC + int(rng.integers(0, r.SPC))
    y = ch.received_envelope(on, st, p_w, case, rng)
    return r.to_lsb(y[::r.SAMP])


def parse_args():
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    p.add_argument('--nf', type=float, default=10.0, help='RX noise figure, dB')
    p.add_argument('--brf', type=float, default=400e6, help='RF noise bandwidth, Hz')
    p.add_argument('--slope', type=float, default=16.0, help='detector slope, mV/dB')
    p.add_argument('--offset-mv', type=float, default=2.0, help='comparator offset, mV')
    p.add_argument('--trim-mv', type=float, default=0.08, help='trim DAC step, mV')
    p.add_argument('--bv', type=float, default=15e3, help='post-detection RC LPF cutoff, Hz')
    p.add_argument('--comp-noise-mv', type=float, default=0.0,
                   help='comparator input noise per decision, mV rms')
    p.add_argument('--levels', type=float, nargs='+', default=list(LEVELS))
    p.add_argument('--trials', type=int, default=TRIALS)
    p.add_argument('--cases', nargs='+', default=list(CASES), choices=CASES)
    p.add_argument('--out', default='e2e.png')
    return p.parse_args()


def main():
    a = parse_args()
    ch.rxm.NF_DB = a.nf
    ch.B_RF = a.brf
    ch.rxm.B_V = a.bv
    levels, trials, cases = a.levels, a.trials, a.cases
    crng = np.random.default_rng(5)

    def afe():
        return radio.AfeModel(offset_db=a.offset_mv / a.slope, trim_lsb_db=a.trim_mv / a.slope,
                              noise_db=a.comp_noise_mv / a.slope, rng=crng)
    desc = (f'NF {a.nf:g} dB, {a.brf / 1e6:.0f} MHz, LPF {a.bv / 1e3:g} kHz, {a.slope:g} mV/dB, offset {a.offset_mv:g} mV, '
            f'trim {a.trim_mv:g} mV/LSB, comp noise {a.comp_noise_mv:g} mV')
    print(desc)
    rng = np.random.default_rng(21)
    on = send_onoff(CODE)
    res = {c: [] for c in cases}
    false_wrong = 0
    for case in cases:
        for lvl in levels:
            ok = 0
            for _ in range(trials):
                v = run_record(on, 10 ** ((lvl - 30) / 10), case, rng)
                rx, _, _ = radio.run_rx(v, CODE, afe())
                ok += len(rx.toggles) == 1
                rxw, _, _ = radio.run_rx(v, WRONG, afe())
                false_wrong += len(rxw.toggles)
            res[case].append(ok / trials)
            print(f'  {case:7s} {lvl:4.0f} dBm  sends detected {ok}/{trials}', flush=True)
    false_empty = 0
    for case in cases:
        for _ in range(3):
            v = run_record(on, 0.0, case, rng)
            false_empty += len(radio.run_rx(v, CODE, afe())[0].toggles)
    print(f'false toggles: wrong-code RX {false_wrong} (over {len(cases)*len(levels)*trials} sends), '
          f'signal-free records {false_empty} (over {3*len(cases)})')

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for case in cases:
        ax.plot(levels, np.array(res[case]) * 100, 'o-', label=case)
    ax.set_xlabel('received power (dBm)'); ax.set_ylabel('sends -> one LED toggle (%)')
    ax.set_title(f'code mode end to end\n{desc}', fontsize=9)
    ax.invert_xaxis(); ax.grid(); ax.legend()
    out = os.path.join(HERE, a.out)
    fig.tight_layout(); fig.savefig(out, dpi=110)
    print('saved', out)


if __name__ == '__main__':
    main()
