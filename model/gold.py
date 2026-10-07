"""
Bit-exact Gold-127 code generator, written the way the RTL will do it:
two 7-bit Fibonacci LFSRs of a preferred pair of primitive polynomials.
Code k (0..126) = M1 xor M2 delayed by k chips; code 127 = M1 alone.

The RTL loads both LFSRs with SEED, then clocks LFSR2 k extra times
before the burst (k <= 126 cycles), so no lookup table is needed.
"""
import numpy as np

N = 7
LEN = (1 << N) - 1          # 127
SEED = 0b1111111
TAPS1 = (7, 3)              # x^7 + x^3 + 1   (verified primitive below)
TAPS2 = None                # filled in by _find_partner(): decimation of M1 by 3


def lfsr(taps, seed=SEED, n=LEN):
    """Fibonacci LFSR: output = stage 7 (MSB), feedback = XOR of the tap
    stages, shifted in at stage 1. Returns (bits, list of states)."""
    st = [(seed >> (N - 1 - i)) & 1 for i in range(N)]   # st[0] = stage 1
    out, states = [], []
    for _ in range(n):
        states.append(int(''.join(map(str, st)), 2))
        out.append(st[-1])
        fb = 0
        for t in taps:
            fb ^= st[t - 1]
        st = [fb] + st[:-1]
    return np.array(out, np.uint8), states


def berlekamp_massey(s):
    """Shortest LFSR (connection polynomial coefficients c[0..L]) for bits s."""
    s = list(map(int, s))
    c, b = [1] + [0] * len(s), [1] + [0] * len(s)
    L, m = 0, -1
    for n in range(len(s)):
        d = s[n]
        for i in range(1, L + 1):
            d ^= c[i] & s[n - i]
        if d:
            t = c[:]
            for i in range(len(s) - n + m):
                c[n - m + i] ^= b[i]
            if 2 * L <= n:
                L, m, b = n + 1 - L, n, t
    return L, c[:L + 1]


def _find_partner():
    m1, _ = lfsr(TAPS1)
    m2 = m1[(3 * np.arange(LEN)) % LEN]                  # decimation by q = 3
    L, c = berlekamp_massey(np.tile(m2, 2))
    assert L == N, L
    # recurrence s[n] = XOR c[i] s[n-i]; for our output-from-stage-7 LFSR the
    # equivalent tap set is {N - i + 1 ... } -> find it by brute-force check
    for mask in range(1, 1 << (N - 1)):
        taps = (N,) + tuple(N - i for i in range(1, N) if mask >> (i - 1) & 1)
        seq, _ = lfsr(taps)
        for k in range(LEN):
            if np.array_equal(np.roll(seq, -k), m2):
                return tuple(sorted(set(taps), reverse=True)), k
    raise RuntimeError('no partner LFSR found')


TAPS2, M2_PHASE = _find_partner()
M1, _ = lfsr(TAPS1)
M2, _ = lfsr(TAPS2)


def gold(k):
    """Code k as a 127-chip 0/1 array (1 = carrier on)."""
    if k == 127:
        return M1.copy()
    return M1 ^ np.roll(M2, -k)


def check():
    b = lambda x: 2.0 * x - 1
    assert M1.sum() == 64 and M2.sum() == 64
    for m in (M1, M2):
        ac = {int(np.dot(b(m), np.roll(b(m), s))) for s in range(1, LEN)}
        assert ac == {-1}, ac
    worst = 0
    for k1 in range(0, 128, 9):
        for k2 in range(128):
            if k1 != k2:
                g1, g2 = b(gold(k1)), b(gold(k2))
                worst = max(worst, max(abs(np.dot(g1, np.roll(g2, s))) for s in range(LEN)))
    return worst


if __name__ == '__main__':
    print('LFSR1 taps', TAPS1, ' LFSR2 taps', TAPS2)
    print('worst periodic cross-correlation between codes:', check(), '(Gold bound 17)')
    print('code 0x5A:', ''.join(map(str, gold(0x5A)))[:40], '...', 'ones', gold(0x5A).sum())
