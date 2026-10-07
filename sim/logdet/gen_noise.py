"""
Write build/noise_pwl.inc: PWL noise sources Vnz_p / Vnz_n for the antenna
arms (nodes an_x -> ant_x), white Gaussian, fixed seed, so every case of
noise_tran.sh sees exactly the same noise. ngspice's own trnoise can't be
made repeatable here (seed options ignored).

Density per arm 2.76 nV/rtHz (= 3.9 nV/rtHz differential, the receiver's
input-referred noise at NF ~11 dB), sampled every 50 ps:
sigma = d / sqrt(2 T).

    python sim/logdet/gen_noise.py [tstop_s] [seed]
"""
import os
import sys

import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
T, D = 50e-12, 2.76e-9


def main(tstop=3e-6, seed=7):
    rng = np.random.default_rng(seed)
    n = int(round(tstop / T)) + 2
    t = np.arange(n) * T
    sigma = D / np.sqrt(2 * T)
    with open(os.path.join(ROOT, 'build', 'noise_pwl.inc'), 'w') as fh:
        fh.write(f'* white noise per arm, {D * 1e9:.2f} nV/rtHz, T={T * 1e12:.0f} ps, seed {seed}\n')
        for side in 'pn':
            v = rng.normal(0, sigma, n)
            fh.write(f'Vnz_{side} ant_{side} an_{side} pwl(\n')
            for i in range(0, n, 8):
                fh.write('+ ' + ' '.join(f'{t[j]:.4e} {v[j]:.4e}' for j in range(i, min(i + 8, n))) + '\n')
            fh.write('+ )\n')


if __name__ == '__main__':
    a = sys.argv[1:]
    main(float(a[0]) if a else 3e-6, int(a[1]) if len(a) > 1 else 7)
