# Key resistances from solved port networks: venv/bin/python report.py h1_n300 h05_n300 ...
import sys, json, os, numpy as np
D = os.path.dirname(os.path.abspath(__file__))
PAIRS = [('st6_mn', 'st1_mp'), ('st6_mn', 'st1_mn'), ('st6_mp', 'st1_mp'), ('st6_mp', 'st1_mn'), ('st6_mtail_n', 'st1_mtail'),
         ('st5_mp', 'st1_mn'), ('st6_mn', 'cin_p_11'), ('st6_mp', 'cin_p_20'), ('st5_mp', 'cin_n_10'), ('st6_mn', 'rb_p'),
         ('st2_mn', 'st1_mn'), ('st3_mn', 'st1_mp'), ('st6_mn', 'st6_mp'), ('st1_mp', 'st1_mn')]
SELF = ['st1_mp', 'st1_mn', 'st1_mtail', 'st2_mn', 'st4_mn', 'st4_mtail_n', 'st6_mn', 'st6_mp', 'st6_mtail_n', 'mref', 'rb_p', 'cin_p_11', 'cin_n_11']
for run in sys.argv[1:]:
    Y = np.load(f'{D}/{run}/Y.npy'); info = json.load(open(f'{D}/{run}/info.json')); names = info['names']
    Z = np.linalg.inv(Y); ix = names.index
    a = info['args']
    print(f'\n== {run}: h {a["h"]} rho {a["rho"]} back {a["back"]} T {a["T"]} drop {a["drop_taps"] or "-"}; grid {info["grid"]}, {info["unknowns"]} unknowns, {info["time_s"]:.0f} s')
    print('  self: R to taps with the other ports shorted (1/Ykk) | floating (Zkk), ohm')
    print('   ' + '  '.join(f'{n} {1 / Y[ix(n), ix(n)]:.0f}|{Z[ix(n), ix(n)]:.0f}' for n in SELF))
    print('  transfer: Z_ij (V at j per A into i, others floating) ohm | direct link R_ij = -1/Y_ij ohm | Z_ij/Z_ii (voltage ratio)')
    for p, q in PAIRS:
        i, j = ix(p), ix(q)
        print(f'   {p:12} -> {q:10} Z {Z[i, j]:10.4g}   R_link {(-1 / Y[i, j]) if Y[i, j] < 0 else float("inf"):10.4g}   ratio {Z[i, j] / Z[i, i]:9.3g}')
