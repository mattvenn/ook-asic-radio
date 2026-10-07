"""
Compare OOK signalling schemes through the same envelope-detector receiver
model (rx_model.py): wideband LNA (NF, B_RF) -> log detector -> RC LPF.

  A  NRZ UART packet (9600 baud), peak/valley tracker + squelch slicer,
     sync-correlated bit check                                (current plan)
  B  Manchester, 4800 bit/s (9600 chips/s), sync by correlation, each bit
     decided by first-half vs second-half energy (no threshold)
  C  Code-mode detection: 127-chip Gold sequence per code at 9600 chips/s,
     correlate against the RX's own code; detect if z > Z_T and own code
     beats the other codes

Signal: synthetic OOK envelope with the measured turn-on amplitude bump
(+14% for ~16 us). Channel cases: noise only; slow fading +/-10 dB during
the packet; bursty CW interferer -60 dBm at -126 MHz (3.5 ms on / 14.17 ms).

    python bench/scheme_compare.py
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import rx_model as rxm

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
R = 1e6                      # envelope sample rate
B_RF = 400e6
REC = 30e-3                  # record length; packet placed at a random start
LEVELS = np.arange(-60, -104, -4)
TRIALS = 4
RHO_T = 0.4                  # scheme C: normalised-correlation threshold (wrong codes <~0.25, noise <~0.16)
N_OTHER = 16                 # other codes checked for confusion in C
CODE = 0x5A & 0x7F


# ---------------------------------------------------------------- patterns
def uart_bits(data):
    bits = []
    for b in data:
        bits += [0] + [(b >> i) & 1 for i in range(8)] + [1]
    return bits


def crc8(data, poly=0x07):
    c = 0
    for b in data:
        c ^= b
        for _ in range(8):
            c = ((c << 1) ^ poly) & 0xFF if c & 0x80 else (c << 1) & 0xFF
    return c


def packet_bytes(code, seq=1):
    body = bytes([0x2D, 0xD4, seq, code, (~code) & 0xFF])
    return bytes([0x55] * 4) + body + bytes([crc8(body)])


def scheme_a():
    """NRZ UART at 9600: carrier on = 0. Returns (on chips at R, info)."""
    bits = uart_bits(packet_bytes(CODE))
    spb = R / 9600
    on = np.repeat(np.array(bits) == 0, 1)[(np.arange(int(len(bits) * spb)) / spb).astype(int)]
    return on, bits


def manchester(bits):
    chips = []
    for b in bits:
        chips += [1, 0] if b else [0, 1]          # 1 = on->off, 0 = off->on
    return chips


def scheme_b_bits():
    pre = [1, 0] * 8
    body = packet_bytes(CODE)[4:]                 # sync, seq, code, ~code, crc
    payload = [(byte >> (7 - i)) & 1 for byte in body for i in range(8)]
    return pre, payload


def scheme_b():
    pre, payload = scheme_b_bits()
    chips = manchester(pre + payload)
    spc = R / 9600
    on = np.array(chips, bool)[(np.arange(int(len(chips) * spc)) / spc).astype(int)]
    return on, (pre, payload)


def mseq(taps, n=7):
    """Fibonacci LFSR m-sequence (taps of a primitive polynomial)."""
    st, out = [1] * n, []
    for _ in range((1 << n) - 1):
        out.append(st[-1])
        fb = 0
        for t in taps:
            fb ^= st[t - 1]
        st = [fb] + st[:-1]
    return np.array(out, np.uint8)


M1 = mseq([7, 3])                 # m-sequence, length 127
# preferred-pair partner: decimate M1 by q = 2^k + 1 = 3 (n = 7 odd, gcd(7,1) = 1)
M2 = M1[(3 * np.arange(127)) % 127]


def gold(k):
    return M1 ^ np.roll(M2, k)


def scheme_c(code=CODE):
    seq = gold(code)
    spc = R / 9600
    return seq.astype(bool)[(np.arange(int(len(seq) * spc)) / spc).astype(int)]


# ---------------------------------------------------------------- channel
def add_bump(on):
    """Measured turn-on amplitude bump: +14% decaying over ~16 us."""
    amp = on.astype(np.float32)
    rises = np.flatnonzero(np.diff(on.astype(int)) == 1) + 1
    bump = 1 + 0.14 * np.clip(np.arange(20) / 16.0, 0, 1) * (np.arange(20) < 17)
    for r in rises:
        seg = amp[r:r + 20]
        amp[r:r + 20] = seg * bump[: len(seg)]
    return amp


def received_envelope(on, start, p_w, case, rng):
    """log-detector output (dB, after RC LPF) at R for a record of REC."""
    n_out = int(REC * R)
    amp = np.zeros(n_out, np.float32)
    seg = add_bump(on)
    amp[start:start + len(seg)] = seg[: n_out - start]
    t_out = np.arange(n_out) / R
    if case == 'fading':
        ph = rng.uniform(0, 2 * np.pi)
        amp *= 10 ** ((10 * np.sin(2 * np.pi * t_out / 30e-3 + ph)) / 20)
    up = int(B_RF / R)
    fs = R * up
    s = np.repeat(amp * np.sqrt(p_w), up).astype(np.complex64)
    n_var = rxm.KT * 10 ** (rxm.NF_DB / 10) * fs
    x = s + (rng.standard_normal(len(s), dtype=np.float32) +
             1j * rng.standard_normal(len(s), dtype=np.float32)) * np.float32(np.sqrt(n_var / 2))
    if case == 'bursty':
        t = np.arange(len(x)) / fs
        off = rng.uniform(0, 14.17e-3)
        gate = ((t + off) % 14.17e-3) < 3.5e-3
        x += (gate * np.sqrt(10 ** ((-60 - 30) / 10)) *
              np.exp(2j * np.pi * (-126e6) * t + 1j * rng.uniform(0, 6.3))).astype(np.complex64)
    p = np.abs(x) ** 2
    y = 10 * np.log10(rxm.block_mean(p, up))
    return rxm.rc_lowpass(y, rxm.B_V, R)


# ---------------------------------------------------------------- receivers
def xcorr(y, tmpl):
    a = y - y.mean()
    n = 1 << int(np.ceil(np.log2(len(a) + len(tmpl))))
    c = np.fft.irfft(np.fft.rfft(a, n) * np.conj(np.fft.rfft(tmpl, n)), n)
    return c[: len(a) - len(tmpl)]


def rx_a(y, noise_stats):
    on_ref, bits = scheme_a()
    sliced = rxm.slice_tracker(y, squelch=noise_stats['lsq'])
    # sync-correlated bit check over everything after the preamble
    e = 2.0 * on_ref[int(40 * R / 9600):] - 1
    k = int(np.argmax(xcorr(2.0 * sliced - 1, e)))
    spb = R / 9600
    nb = len(bits) - 40
    centres = k + ((np.arange(nb) + 0.5) * spb).astype(int)
    if centres[-1] >= len(sliced):
        return False
    return bool(np.all(sliced[centres] == (np.array(bits[40:]) == 0)))


def rx_b(y):
    pre, payload = scheme_b_bits()
    on_ref, _ = scheme_b()
    spc = R / 9600
    # bit timing + sync from correlation with preamble + sync word (chips)
    nsync = len(pre) + 16
    tmpl = 2.0 * on_ref[: int(2 * nsync * spc)] - 1
    k = int(np.argmax(xcorr(y, tmpl)))
    got = []
    for i in range(len(pre), len(pre) + len(payload)):
        a0 = k + int(2 * i * spc)
        h = int(spc)
        g = max(1, h // 8)                      # guard at chip edges
        if a0 + 2 * h >= len(y):
            return False
        first = y[a0 + g:a0 + h - g].mean()
        second = y[a0 + h + g:a0 + 2 * h - g].mean()
        got.append(1 if first > second else 0)
    return got == payload


def norm_xcorr(y, tmpl):
    """Pearson correlation of tmpl against every window of y (scale and
    offset invariant): what a hardware correlator + energy normaliser does."""
    y = np.asarray(y, np.float64) - np.mean(y)    # centre: avoids cancellation
    t = tmpl - tmpl.mean()
    n = len(t)
    num = xcorr(y, t)                     # xcorr removes y's global mean; t is zero-mean
    cs = np.cumsum(np.r_[0.0, y])
    cs2 = np.cumsum(np.r_[0.0, y * y])
    m = len(num)
    s1 = cs[n:n + m] - cs[:m]
    s2 = cs2[n:n + m] - cs2[:m]
    var = np.maximum(s2 / n - (s1 / n) ** 2, 1e-30)
    return num / (n * np.sqrt(var) * t.std())


def rx_c(y, others):
    """The RX only knows its own code: detect if its rho > RHO_T. Also
    report the best other code's rho to check it would NOT trigger."""
    rs = norm_xcorr(y, scheme_c(CODE).astype(float)).max()
    ro = max(norm_xcorr(y, scheme_c(o).astype(float)).max() for o in others)
    return rs > RHO_T, rs, ro


# ---------------------------------------------------------------- main
def main():
    rng = np.random.default_rng(7)
    others = [o for o in rng.choice(128, N_OTHER + 1, replace=False) if o != CODE][:N_OTHER]
    on_a, _ = scheme_a()
    on_b, _ = scheme_b()
    on_c = scheme_c()
    print(f'packet lengths: A {len(on_a)/R*1e3:.1f} ms, B {len(on_b)/R*1e3:.1f} ms, '
          f'C {len(on_c)/R*1e3:.1f} ms')
    cases = ('noise', 'fading', 'bursty')
    res = {(c, s): [] for c in cases for s in 'ABC'}
    wrong = {}
    for case in cases:
        # squelch / false-alarm calibration on a signal-free record
        y0 = received_envelope(on_a, 0, 0.0, case, rng)
        noise_stats = {'lsq': rxm.FIXED_SIGMA * y0[len(y0) // 10:].std()}
        fa = sum(rx_c(received_envelope(on_c, 0, 0.0, case, rng), others)[0] for _ in range(3))
        print(f'{case}: scheme C false alarms with no signal: {fa}/3', flush=True)
        for lvl in LEVELS:
            ok = {'A': 0, 'B': 0, 'C': 0}
            for _ in range(TRIALS):
                p = 10 ** ((lvl - 30) / 10)
                st = int(rng.uniform(2e-3, REC - 14e-3) * R)
                ok['A'] += rx_a(received_envelope(on_a, st, p, case, rng), noise_stats)
                ok['B'] += rx_b(received_envelope(on_b, st, p, case, rng))
                hit, rs, ro = rx_c(received_envelope(on_c, st, p, case, rng), others)
                ok['C'] += hit
                wrong[case] = max(wrong.get(case, 0), ro)
            for s in 'ABC':
                res[(case, s)].append(ok[s] / TRIALS)
            print(f'  {case:7s} {lvl:4d} dBm  A {ok["A"]}/{TRIALS}  B {ok["B"]}/{TRIALS}  '
                  f'C {ok["C"]}/{TRIALS}', flush=True)

    print('\nscheme C: highest rho seen for a WRONG code per case (must stay < '
          f'{RHO_T}):', {k: round(float(v), 3) for k, v in wrong.items()})
    print('\nsensitivity (>= 75% success, lowest level):')
    names = {'A': 'NRZ UART + tracker', 'B': 'Manchester half-bit', 'C': 'Gold-127 correlation'}
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.5), sharey=True)
    for ax, case in zip(axs, cases):
        for s, mk in zip('ABC', 'osd'):
            r = res[(case, s)]
            good = [l for l, v in zip(LEVELS, r) if v >= 0.75]
            print(f'  {case:7s} {names[s]:22s} {min(good) if good else None} dBm'
                  f'  (fails at {[int(l) for l, v in zip(LEVELS, r) if v < 0.75 and l > (min(good) if good else -999)]})')
            ax.plot(LEVELS, np.array(r) * 100, marker=mk, label=names[s])
        ax.set_title(case); ax.set_xlabel('received power (dBm)'); ax.grid(); ax.invert_xaxis()
    axs[0].set_ylabel('success (%)'); axs[0].legend(fontsize=8)
    fig.suptitle('OOK scheme comparison, envelope-detector RX model (NF 10 dB, 400 MHz LNA, log detector)')
    out = os.path.join(DATA, 'scheme_compare.png')
    fig.tight_layout(); fig.savefig(out, dpi=110)
    print('saved', out)


if __name__ == '__main__':
    main()
