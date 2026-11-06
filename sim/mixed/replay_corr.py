"""Replay the RTL's detection on a finished mixed run, at all 8 sample alignments of the chip slicer.

The comparator samples are recovered from the trim servo's steps (rd_rx.v: up when the sampled comparator
bit is 1, down when 0). Then, as rd_corr.v, an 8-sample majority slicer and the 127-chip XNOR score against
gold(0x5A), threshold 97, the max over the window where the burst has fully arrived. The RTL scores 4 of the
8 alignments (window ends on odd k): with the mixed bench's fixed burst start these are the even offsets here
(checked: the even-offset replay matches the simulated event pin 60/60 at -86 / -88 / -90 dBm low gain). The
odd offsets are what the RTL would score for a burst one sample (13 us) later, so the average over both is
the detection rate for a burst arriving at a random time.

    python3 sim/mixed/replay_corr.py <tag> <level> [<level> ...]     e.g.  lo -88 -90   (mixed_<lvl>_s<1..20>_<tag>.raw)
"""
import os
import sys

import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'model'))
from rawread import read_raw    # noqa: E402
from gold import gold           # noqa: E402

LSB = 1.8 / 256
TH = 97
TMPL = gold(0x5A).astype(int)
WIN = (13.5e-3, 15.5e-3)        # window ends where the burst (1.5 ms + 127 x 104 us) has fully arrived


def samples(path):
    """Comparator samples (from the servo's settled steps), their times, and whether the event pin opened."""
    v = read_raw(path)[0]['vars']
    t, trim, ev = (np.real(v[k]) for k in ('time', 'v(trim)', 'v(uio_out_4_a)'))
    code = np.round(trim / LSB)
    seq, tt, last = [], [], code[np.searchsorted(t, 5e-6)]
    for i in np.nonzero(np.diff(code))[0]:
        j = np.searchsorted(t, t[i] + 1e-6)          # the value once the ladder has settled
        if t[i] < 4e-6 or j >= len(t) or code[j] == last:
            continue
        seq.append(1 if code[j] > last else 0)
        tt.append(t[i])
        last = code[j]
    return np.array(seq), np.array(tt), bool(np.any((ev[1:] > 0.9) & (ev[:-1] <= 0.9)))


def scores(seq, tt):
    """Max score at each of the 8 alignments."""
    out = []
    for ph in range(8):
        n = (len(seq) - ph) // 8
        w = seq[ph:ph + 8 * n].reshape(n, 8)
        c7 = w[:, :7].sum(1)
        bits = ((c7 >= 5) | ((w[:, 7] == 1) & (c7 >= 3))).astype(int)   # rd_corr.v majority
        tend = tt[ph + 8 * np.arange(1, n + 1) - 1]
        out.append(max(int(np.sum(bits[e - 127:e] == TMPL)) for e in range(127, n + 1)
                       if WIN[0] < tend[e - 1] < WIN[1]))
    return out


def main(tag, levels):
    for lvl in levels:
        n = agree = d_even = d_odd = 0
        print(f'{lvl} dBm ({tag}): seed, sim event | max score at offsets 0..7 | RTL phases (even) / 1 sample later (odd)')
        for s in range(1, 21):
            path = os.path.join(ROOT, 'build', 'mixed', f'mixed_{lvl}_s{s}_{tag}.raw')
            if not os.path.exists(path):
                continue
            seq, tt, det = samples(path)
            sc = scores(seq, tt)
            ev, od = max(sc[0::2]) >= TH, max(sc[1::2]) >= TH
            n += 1
            agree += ev == det
            d_even += ev
            d_odd += od
            print(f'  s{s:<2} {"DET " if det else "miss"} | ' + ' '.join(f'{x:3d}' for x in sc) +
                  f' | {"det" if ev else "-"} / {"det" if od else "-"}')
        print(f'  -> replay at the RTL phases agrees with the sim {agree}/{n}; detects {d_even}/{n} as simulated, '
              f'{d_odd}/{n} one sample later: {100 * (d_even + d_odd) / (2 * n):.0f} % over burst timing')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
