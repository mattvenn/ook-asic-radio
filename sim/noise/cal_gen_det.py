"""
Fit sim/rx/gen_det.py's detector model to a transistor-level noise run (sim/noise/devnoise_results.txt), so the
mixed bench can be rerun with device noise (Harald's review action 13 follow-up, 2026-11-22).

gen_det.py maps the block power of signal + noise (NF 11 dB over 450 MHz) to det through an old CW curve
(sim/logdet/transfer_cw.txt, 5 dB steps). With the det level fixed, the model has two knobs that matter:
  --shift   where the noise-only power sits on the curve: sets det with no signal (and the local slope);
  --sig     signal-only gain in dB: sets the signal-to-noise ratio, so the swings.
(NF and --sig are the same knob once det with no signal is fixed: the block-power statistics don't depend on NF.)
This fits --shift to the run's no-signal det, then --sig to its swings at -94 / -90 / -85 dBm (least squares,
weighted by 1 / seed scatter: +-0.3 mV at -94, +-0.2 at -90, +-0.15 at -85, docs/verify_tall.md section 5).

    python3 sim/noise/cal_gen_det.py            (prints the fit for A and Dth, ~2 min)
"""
import os
import sys

import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'sim', 'rx'))
sys.path.insert(0, os.path.join(ROOT, 'bench'))
sys.path.insert(0, os.path.join(ROOT, 'model'))
import gen_det as g      # noqa: E402
import rx_model as rxm   # noqa: E402

LEVELS = (-94, -90, -85)
SIGMA = np.array([0.3, 0.2, 0.15])     # mV, seed scatter of the transistor swings
# transistor-level runs (devnoise_results.txt, schematic chain + log_det, full gain, tt): det no signal V, swings mV
TARGETS = {'A': (1.44973, (-1.16, -2.44, -6.56)),       # injected NF 11.0: what gen_det.py was calibrated on
           'Dth': (1.43715, (-0.66, -1.55, -4.62)),     # device noise, thermal
           'Dall': (1.42679, (-0.55, -1.30, -3.90))}    # device noise, thermal + 1/f (upper bound)
N, SEED = 200000, 1
PIN, VDET = g.det_curve()
UP = int(g.B_RF / g.R)


def _noise():
    """Common random numbers: the same noise for every evaluation, in 1 us blocks."""
    rng = np.random.default_rng(SEED)
    n_var = rxm.KT * 10 ** (g.NF_DB / 10) * g.B_RF
    for _ in range(N // 500):
        yield (rng.standard_normal(500 * UP, dtype=np.float32) +
               1j * rng.standard_normal(500 * UP, dtype=np.float32)) * np.float32(np.sqrt(n_var / 2))


NOISE = list(_noise())


def det(lvl, shift, sig):
    a = 0.0 if lvl is None else np.sqrt(10 ** ((lvl + sig - 30) / 10))
    return np.mean([np.interp(10 * np.log10(rxm.block_mean(np.abs(a + x) ** 2, UP)) + 30 + shift, PIN, VDET).mean()
                    for x in NOISE])


def bisect(f, lo, hi, n=30):
    flo = f(lo)
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid)
        if np.sign(fm) == np.sign(flo):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def fit(d0, swings):
    shift = bisect(lambda s: det(None, s, 0) - d0, -9, -1, 22)
    base = det(None, shift, 0)
    sw = lambda sig: np.array([1e3 * (det(l, shift, sig) - base) for l in LEVELS])
    cost = lambda sig: np.sum(((sw(sig) - np.array(swings)) / SIGMA) ** 2)
    grid = np.arange(-6, 6.01, 0.5)
    c = [cost(s) for s in grid]
    k = int(np.argmin(c))
    lo, hi = grid[max(k - 1, 0)], grid[min(k + 1, len(grid) - 1)]
    for _ in range(14):                      # golden-section on the bracket
        m1, m2 = lo + 0.382 * (hi - lo), lo + 0.618 * (hi - lo)
        if cost(m1) < cost(m2):
            hi = m2
        else:
            lo = m1
    sig = (lo + hi) / 2
    return shift, base, sig, sw(sig), sw(0.0)


if __name__ == '__main__':
    for name in sys.argv[1:] or TARGETS:
        d0, swings = TARGETS[name]
        shift, base, sig, s, s0 = fit(d0, swings)
        print(f'{name:4s} target det {d0:.5f} V, swings {swings}; fit --shift={shift:.2f} (det {base:.5f}) '
              f'--sig={sig:+.2f}: swings {" ".join(f"{x:.2f}" for x in s)} (with --sig=0: '
              f'{" ".join(f"{x:.2f}" for x in s0)})', flush=True)
