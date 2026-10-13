"""Bin comp_ct Monte Carlo --step results (build/mc/comp_*_step*.txt) as in verify_supply_mc.md 2.2.

Per file: samples, duplicate rows (the seed trap: must be 0), offset mean / sigma, median step, the
fraction of chips by trim step (<= 0.19 mV/LSB: -92 dBm; 0.19-0.43: about -90; > 0.43: about -88),
no switching point (NaN: can't trim), switching code > 242 (near the top end), and the 95th / 99th
percentile step.

    python3 sim/comp_ct/mc_bins.py [--vdd 1.8] build/mc/comp_tt_27_cm1.5_step_<tag>.txt ...

--vdd: the bench supply; a DAC code is VDD / 256 (the R2R ladder runs off VDPWR).
"""
import sys

import numpy as np


def bins(path, vdd=1.8):
    a = np.loadtxt(path, ndmin=2)
    n = len(a)
    if a.shape[1] < 3:
        return None
    _, cnt = np.unique(a[~np.isnan(a).any(axis=1)], axis=0, return_counts=True)
    dup = int(np.sum(cnt - 1))
    nan = np.isnan(a[:, 2])
    g = a[~nan]
    st = g[:, 2] * 1e3
    code = g[:, 1] / (vdd / 256)
    return dict(n=n, dup=dup, off_mean=g[:, 0].mean() * 1e3, off_sig=g[:, 0].std(ddof=1) * 1e3,
                med=np.median(st), p95=np.percentile(st, 95), p99=np.percentile(st, 99),
                b92=100 * np.sum(st <= 0.19) / n, b90=100 * np.sum((st > 0.19) & (st <= 0.43)) / n,
                b88=100 * np.sum(st > 0.43) / n, nan=int(nan.sum()), hi=int(np.sum(code > 242)),
                code_mean=code.mean(), code_sig=code.std(ddof=1), code_max=code.max(), code_min=code.min())


if __name__ == '__main__':
    args = sys.argv[1:]
    vdd = 1.8
    if '--vdd' in args:
        i = args.index('--vdd')
        vdd = float(args[i + 1])
        del args[i:i + 2]
    print('file | n | dup | offset mV | step med / p95 / p99 | <=0.19 | 0.19-0.43 | >0.43 | NaN | code>242 | '
          'code mean ± sig (min..max)')
    for p in args:
        r = bins(p, vdd)
        if r is None:
            print(f"{p.split('/')[-1]} | no rows (no comparator threshold at this point)")
            continue
        print(f"{p.split('/')[-1]} | {r['n']} | {r['dup']} | {r['off_mean']:+.2f} ± {r['off_sig']:.2f} | "
              f"{r['med']:.3f} / {r['p95']:.3f} / {r['p99']:.3f} | {r['b92']:.1f} % | {r['b90']:.1f} % | "
              f"{r['b88']:.1f} % | {r['nan']} | {r['hi']} | {r['code_mean']:.0f} ± {r['code_sig']:.0f} "
              f"({r['code_min']:.0f}..{r['code_max']:.0f})")
