"""
End-to-end check of the bit-exact code-mode design through the channel model:
TX send (3 Gold bursts) -> wideband LNA noise (+fading / bursty interferer)
-> log detector -> analog comparator model (averaged reference, offset,
R2R trim) -> radio.RxDigital (bit-exact) -> LED toggle.

Success = exactly one LED toggle for a send. Also counts false toggles on a
wrong-code RX fed the same records, and on signal-free records.

    python model/e2e.py
"""
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


def main():
    rng = np.random.default_rng(21)
    on = send_onoff(CODE)
    res = {c: [] for c in CASES}
    false_wrong = 0
    for case in CASES:
        for lvl in LEVELS:
            ok = 0
            for _ in range(TRIALS):
                v = run_record(on, 10 ** ((lvl - 30) / 10), case, rng)
                rx, _, _ = radio.run_rx(v, CODE)
                ok += len(rx.toggles) == 1
                rxw, _, _ = radio.run_rx(v, WRONG)
                false_wrong += len(rxw.toggles)
            res[case].append(ok / TRIALS)
            print(f'  {case:7s} {lvl:4d} dBm  sends detected {ok}/{TRIALS}', flush=True)
    false_empty = 0
    for case in CASES:
        for _ in range(3):
            v = run_record(on, 0.0, case, rng)
            false_empty += len(radio.run_rx(v, CODE)[0].toggles)
    print(f'false toggles: wrong-code RX {false_wrong} (over {len(CASES)*len(LEVELS)*TRIALS} sends), '
          f'signal-free records {false_empty} (over {3*len(CASES)})')

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for case in CASES:
        ax.plot(LEVELS, np.array(res[case]) * 100, 'o-', label=case)
    ax.set_xlabel('received power (dBm)'); ax.set_ylabel('sends -> one LED toggle (%)')
    ax.set_title('bit-exact code-mode design, end to end (NF 10 dB, 400 MHz LNA)')
    ax.invert_xaxis(); ax.grid(); ax.legend()
    out = os.path.join(HERE, 'e2e.png')
    fig.tight_layout(); fig.savefig(out, dpi=110)
    print('saved', out)


if __name__ == '__main__':
    main()
