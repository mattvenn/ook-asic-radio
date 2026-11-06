# Asymmetric coupling (aF) from a kpex FasterCap result matrix, as couple.py does for the 2.5D runs:
#   python3 build/kpex/fcsum.py build/kpex/fc/run/cut__lna_chain_cut/lna_chain_cut_FasterCap_Result_Matrix_Avg.csv
import sys, csv
rows = list(csv.reader(open(sys.argv[1]), delimiter=';'))
names = [h.split('_', 1)[1] for h in rows[0] if h]
M = [[float(x) for x in r if x] for r in rows[1:] if r and r[0]]
ix = {n: i for i, n in enumerate(names)}
C = lambda a, b: -M[ix[a]][ix[b]] * 1e18                 # aF (off-diagonal Maxwell terms are negative)
print('aF        ' + ''.join(f'{v:>9}' for v in ('g1p', 'g1n', 'inp', 'inn')))
for a in ('st6_sp', 'st6_sn', 'st5_sp', 'st5_sn'):
    print(f'{a:10}' + ''.join(f'{C(a, v):9.2f}' for v in ('g1p', 'g1n', 'inp', 'inn')))
print('asymmetric: C(Xp,Vp)-C(Xp,Vn) | C(Xn,Vn)-C(Xn,Vp) | dm')
for x in ('st6', 'st5'):
    for vp, vn in (('g1p', 'g1n'), ('inp', 'inn')):
        d1 = C(f'{x}_sp', vp) - C(f'{x}_sp', vn); d2 = C(f'{x}_sn', vn) - C(f'{x}_sn', vp)
        print(f'  {x} -> {vp[:-1]}: {d1:+8.2f} {d2:+8.2f} dm {(d1 + d2) / 2:+8.2f}')
