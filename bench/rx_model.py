"""
Software model of the proof-of-concept OOK receiver, run on a recorded
packet:

    antenna -> LNA (noise figure NF, RF bandwidth B_RF, no selectivity)
            -> square-law envelope detector -> RC low-pass (B_V)
            -> slicer (oracle / fixed / peak-valley tracker) -> UART -> packet check

The 50 cm recording is used as the signal template (zeroed during "off"
bits so its recorded ambient isn't scaled with it), scaled to a received
power P_rx (dBm into 50R). Thermal noise kT*F*B_RF is added, plus
optionally a CW interferer standing in for the strong ~392 MHz signal
seen in the ambient spectra.
Monte-Carlo over noise seeds gives packet success rate vs P_rx.

    python bench/rx_model.py [template.npz]
"""
import glob
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from record import PACKET, BAUD, uart_decode

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
KT = 1.380649e-23 * 290
MATCH = PACKET[4:]                 # sync word + payload
OUT_RATE = 1e6                     # detector output sample rate

NF_DB = 10.0                       # inverter LNA + pad loss, a guess to refine in sim
# (label, B_RF, interferer dBm or None, interferer offset from carrier)
CASES = (('400 MHz LNA', 400e6, None, 0),
         ('400 MHz LNA + -62 dBm @ -126 MHz', 400e6, -62, -126e6),
         ('100 MHz selectivity', 100e6, None, 0))
B_V = 15e3                         # post-detection bandwidth (~1.5x bit rate)
LEVELS = np.arange(-50, -102, -2)  # dBm
TRIALS = 5
FIXED_SIGMA = 6                    # fixed slicer: noise-only mean + 6 sigma (calibrated squelch)
PATH_1M_DBM, PATH_N = -44.3, 1.89  # measured path-loss fit (ota.csv)


def load_template(path):
    d = np.load(path)
    bb, rate = d['bb'].astype(np.complex64), float(d['bb_rate'])
    # locate the packet in the clean recording and crop around it
    p = np.abs(bb) ** 2
    y = block_mean(p, int(rate / OUT_RATE))
    on = y > (np.percentile(y, 95) + np.percentile(y, 5)) / 2
    frames = uart_decode((~on).astype(np.uint8), OUT_RATE)
    got = bytes(b for _, b, _ in frames)
    pos = got.find(MATCH)
    if pos < 0:
        sys.exit(f'template does not decode: {got!r}')
    start = frames[max(0, pos - 4)][0]
    n_pkt = int(len(PACKET) * 10 / BAUD * OUT_RATE)
    a = max(0, start - 1000)
    b = start + n_pkt + 1000
    s = bb[int(a * rate / OUT_RATE): int(b * rate / OUT_RATE)]
    on_mask = np.repeat(on[a:b], int(rate / OUT_RATE))[: len(s)]
    p_on = np.median(np.abs(s[on_mask]) ** 2)
    s = np.where(on_mask, s, 0)             # drop the recorded ambient
    return s / np.sqrt(p_on), rate          # normalised: on-power = 1


def block_mean(x, n):
    return x[: len(x) // n * n].reshape(-1, n).mean(axis=1)


def rc_lowpass(x, fc, rate):
    a = 1 - np.exp(-2 * np.pi * fc / rate)
    y = np.empty_like(x)
    acc = x[0]
    for i, v in enumerate(x):
        acc += a * (v - acc)
        y[i] = acc
    return y


def detector(s_norm, rate, p_rx_w, b_rf, rng, intf_dbm=None, intf_off=0.0, log=False):
    """Received complex baseband (power units: |x|^2 in W) -> RC-filtered
    square-law detector output at OUT_RATE."""
    up = int(round(b_rf / rate))
    if up >= 1:
        s = np.repeat(s_norm, up)          # narrowband signal: hold is fine
        fs = rate * up
    else:
        dn = int(round(rate / b_rf))
        s = block_mean(s_norm, dn)
        fs = rate / dn
    s = s * np.sqrt(p_rx_w)
    n_var = KT * 10 ** (NF_DB / 10) * fs     # complex white noise at fs = B_RF
    noise = (rng.standard_normal(len(s), dtype=np.float32) +
             1j * rng.standard_normal(len(s), dtype=np.float32)) * np.sqrt(n_var / 2)
    x = s + noise
    if intf_dbm is not None and abs(intf_off) < fs / 2:
        t = np.arange(len(x)) / fs
        x = x + np.sqrt(10 ** ((intf_dbm - 30) / 10)) * np.exp(2j * np.pi * intf_off * t).astype(np.complex64)
    p = np.abs(x) ** 2
    y = block_mean(p, int(round(fs / OUT_RATE)))
    if log:
        # log-response detector (e.g. successive-detection limiter chain):
        # output in dB, ~1 us video bandwidth before the RC filter
        y = 10 * np.log10(y)
    return rc_lowpass(y, B_V, OUT_RATE), n_var


def slice_oracle(y, truth_on):
    thr = (y[truth_on].mean() + y[~truth_on].mean()) / 2
    return y > thr


def slice_fixed(y, thr):
    return y > thr


def slice_tracker(y, squelch=0.0, tau_attack=20e-6, tau_decay=3e-3, hyst=0.15):
    """Peak/valley tracking data slicer with hysteresis. With squelch > 0
    the output is held idle (carrier off) unless peak - valley > squelch."""
    af = 1 - np.exp(-1 / (tau_attack * OUT_RATE))
    ad = 1 - np.exp(-1 / (tau_decay * OUT_RATE))
    pk = vl = y[0]
    out = np.zeros(len(y), dtype=bool)
    state = False
    for i, v in enumerate(y):
        pk += (af if v > pk else ad) * (v - pk)
        vl += (af if v < vl else ad) * (v - vl)
        mid, h = (pk + vl) / 2, hyst * (pk - vl)
        if pk - vl < squelch:
            state = False
        elif state and v < mid - h:
            state = False
        elif not state and v > mid + h:
            state = True
        out[i] = state
    return out


def expected_onoff(data, rate=OUT_RATE, baud=BAUD):
    """Carrier on/off per sample for UART-framed `data` (carrier on = 0)."""
    bits = []
    for b in data:
        bits += [0] + [(b >> i) & 1 for i in range(8)] + [1]
    spb = rate / baud
    n = int(len(bits) * spb)
    idx = (np.arange(n) / spb).astype(int)
    return np.array(bits)[idx] == 0, np.array(bits), spb


EXP_ON, EXP_BITS, SPB = expected_onoff(MATCH)


def decodes(on):
    """Sync-word correlator back end: find the best alignment of the framed
    sync word + payload in the sliced stream, then require every bit
    (sampled at its centre) to match. Equivalent to a correct packet."""
    a = 2.0 * on - 1
    e = 2.0 * EXP_ON - 1
    n = 1 << int(np.ceil(np.log2(len(a) + len(e))))
    corr = np.fft.irfft(np.fft.rfft(a, n) * np.conj(np.fft.rfft(e, n)), n)[: len(a) - len(e)]
    k = int(np.argmax(corr))
    centres = k + ((np.arange(len(EXP_BITS)) + 0.5) * SPB).astype(int)
    got_on = on[centres]
    return bool(np.all(got_on == (EXP_BITS == 0)))


def main(template):
    s_norm, rate = load_template(template)
    print(f'template {os.path.basename(template)}: {len(s_norm)/rate*1e3:.1f} ms; '
          f'NF {NF_DB} dB, B_V {B_V/1e3:g} kHz')
    # ground-truth on/off from the clean template
    truth = block_mean(np.abs(s_norm) ** 2, int(rate / OUT_RATE)) > 0.5
    rng = np.random.default_rng(1)
    slicers = ('oracle', 'fixed', 'tracker+squelch', 'log+fixed', 'log+tracker+squelch')
    res = {(c[0], sl): [] for c in CASES for sl in slicers}
    for label, b_rf, i_dbm, i_off in CASES:
        n_dbm = 10 * np.log10(KT * 10 ** (NF_DB / 10) * b_rf) + 30
        # calibrate the fixed threshold on a noise(+interferer)-only run
        y0, _ = detector(s_norm, rate, 0.0, b_rf, rng, i_dbm, i_off)
        y0 = y0[len(y0) // 10:]
        thr = y0.mean() + FIXED_SIGMA * y0.std()
        sq = FIXED_SIGMA * y0.std()
        l0, _ = detector(s_norm, rate, 0.0, b_rf, rng, i_dbm, i_off, log=True)
        l0 = l0[len(l0) // 10:]
        lthr = l0.mean() + FIXED_SIGMA * l0.std()
        lsq = FIXED_SIGMA * l0.std()
        print(f'{label}: thermal noise {n_dbm:.1f} dBm in B_RF', flush=True)
        for lvl in LEVELS:
            ok = dict.fromkeys(slicers, 0)
            for _ in range(TRIALS):
                seed = rng.integers(1 << 31)
                y, _ = detector(s_norm, rate, 10 ** ((lvl - 30) / 10), b_rf,
                                np.random.default_rng(seed), i_dbm, i_off)
                ly, _ = detector(s_norm, rate, 10 ** ((lvl - 30) / 10), b_rf,
                                 np.random.default_rng(seed), i_dbm, i_off, log=True)
                m = min(len(y), len(truth))
                y, ly, tr = y[:m], ly[:m], truth[:m]
                ok['oracle'] += decodes(slice_oracle(y, tr))
                ok['fixed'] += decodes(slice_fixed(y, thr))
                ok['tracker+squelch'] += decodes(slice_tracker(y, sq))
                ok['log+fixed'] += decodes(slice_fixed(ly, lthr))
                ok['log+tracker+squelch'] += decodes(slice_tracker(ly, lsq))
            for sl in slicers:
                res[(label, sl)].append(ok[sl] / TRIALS)
            print(f'  {lvl:4d} dBm  ' + '  '.join(f'{sl} {ok[sl]}/{TRIALS}' for sl in slicers),
                  flush=True)
            if all(ok[sl] == 0 for sl in slicers):
                for sl in slicers:     # pad the rest of the sweep with zeros
                    res[(label, sl)] += [0.0] * (len(LEVELS) - len(res[(label, sl)]))
                break

    def sens(rates):
        good = [l for l, r in zip(LEVELS, rates) if r >= 0.9]
        return min(good) if good else None

    print('\nsensitivity (>=90% packets) and range from the measured path-loss fit:')
    fig, ax = plt.subplots(figsize=(9, 5))
    styles = ('-', '--', ':')
    for (label, sl), rates in res.items():
        p = sens(rates)
        rng_m = 10 ** ((PATH_1M_DBM - p) / (10 * PATH_N)) if p is not None else None
        lab = f'{label}, {sl}'
        print(f'  {lab:48s} {p} dBm' + (f'  -> ~{rng_m:.1f} m (no fade margin), '
                                       f'~{rng_m/10**(15/(10*PATH_N)):.1f} m with 15 dB margin'
                                       if p is not None else ''))
        ci = [c[0] for c in CASES].index(label)
        mk = 'osv^d'[slicers.index(sl)]
        ax.plot(LEVELS, np.array(rates) * 100, styles[ci], marker=mk, ms=3, label=lab)
    ax.set_xlabel('received power (dBm)'); ax.set_ylabel('packets decoded (%)')
    ax.set_title(f'envelope-detector RX model on real 518 MHz OOK recording (NF {NF_DB:g} dB)')
    ax.grid(); ax.legend(fontsize=8); ax.invert_xaxis()
    out = os.path.join(DATA, 'rx_model.png')
    fig.tight_layout(); fig.savefig(out, dpi=110)
    print('saved', out)


if __name__ == '__main__':
    t = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob(os.path.join(DATA, 'packet_50cm_*.npz')))[-1]
    main(t)
