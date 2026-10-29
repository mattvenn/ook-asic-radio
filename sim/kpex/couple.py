# Coupling tables from kpex 2.5D CSV netlists: python3 couple.py h8 h50 ...
import sys, csv, os
D = os.path.dirname(os.path.abspath(__file__))
VICT = ['inp', 'inn', 'g1p', 'g1n', 'o1p', 'o1n', 'st1_tail']
PAIRS_V = [('inp', 'inn'), ('g1p', 'g1n'), ('o1p', 'o1n')]
PAIRS_A = [('outp', 'outn'), ('o5p', 'o5n'), ('o4p', 'o4n'), ('o3p', 'o3n'), ('st6_sp', 'st6_sn'), ('st5_sp', 'st5_sn'), ('st4_sp', 'st4_sn'), ('st3_sp', 'st3_sn'), ('o2p', 'o2n')]
GROUND = ['VSS', 'VDD', 'VSUBS', 'sky130_gnd']
for run in sys.argv[1:]:
    f = f'{D}/{run}/lna_chain__lna_chain/lna_chain_k25d_pex_netlist.spice'
    C = {}; SI = {'a': 1e-3, 'f': 1, 'p': 1e3}   # -> aF after *1000
    for ln in open(f):
        if not ln.startswith('Cext_'): continue   # parasitics only (the MIM devices are plain 'C')
        _, a, b, v = ln.split()[:4]
        c = float(v[:-1]) * SI[v[-1]] * 1000
        C[frozenset((a, b))] = C.get(frozenset((a, b)), 0) + c
    g = lambda a, b: C.get(frozenset((a, b)), 0.0)
    nets = sorted({n for k in C for n in k})
    print(f'\n==== {run}  ({len(C)} caps, nets: {" ".join(nets)})')
    print('aF        ' + ''.join(f'{v:>9}' for v in VICT))
    for ap in PAIRS_A:
        for a in ap: print(f'{a:10}' + ''.join(f'{g(a, v):9.2f}' for v in VICT))
    print('asymmetric (aF): C(Xp,Vp)-C(Xp,Vn) | C(Xn,Vn)-C(Xn,Vp) | differential Cdm=[C(p,p)+C(n,n)-C(p,n)-C(n,p)]/2')
    for xp, xn in PAIRS_A:
        row = []
        for vp, vn in PAIRS_V:
            d1 = g(xp, vp) - g(xp, vn); d2 = g(xn, vn) - g(xn, vp)
            row.append(f'{vp[:-1]}: {d1:+7.2f} {d2:+7.2f} dm {(d1 + d2) / 2:+7.2f}')
        print(f'  {xp[:-1] if xp.endswith("p") else xp:8} ' + ' | '.join(row))
    print('victim to ground nets (aF):')
    for v in VICT: print(f'  {v:9}' + ''.join(f' {n}={g(v, n):9.1f}' for n in GROUND) + f'  total={sum(c for k, c in C.items() if v in k):9.1f}')
    print('largest couplings into victims from nets outside input zone / st1 (aF):')
    ext = sorted(((c, v, (set(k) - {v}).pop()) for k, c in C.items() for v in k
                  if v in VICT and not (set(k) - {v}) <= set(VICT) and len(k) == 2), reverse=True)
    for c, v, o in [e for e in ext if e[2] not in GROUND][:12]: print(f'  {o:10} -> {v:9} {c:10.1f}')
