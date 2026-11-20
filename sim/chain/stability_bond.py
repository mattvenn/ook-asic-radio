#!/usr/bin/env python3
"""(C) Bond-wire / package coupling: supply and ground bond wires mutually coupled to the input bond wires.

The model (on stab_deck.base_deck, i.e. stability.sh's bench):
  - an input bond wire Lb in series with each input between the antenna resistor (board side) and the pad model
    (Rant_x -> Lb_x -> ant_x). The pad model keeps its own 1 nH; Lb is on top of it;
  - Lsup (VDPWR) and Lgnd (chip ground) are the supply bond wires, value L (2 or 5 nH), as in stability.sh;
  - mutual coupling: the aggressor wire (VDPWR, VGND, or both with the same k) couples k to pad_p's wire and r*k to
    pad_n's (r = 0: only pad_p; 0.5: k/2 on pad_n; 1: symmetric, i.e. common mode). All wires are taken as running
    the same way (package -> die), so the currents' signs are 'into the die' on VDPWR and 'out of the die' on VGND;
    the sign of k (the dot orientation) isn't known, so both are reported.

AC stability margin (ac mode). The mutual inductance is bilateral: the input wires carry real RF current (the pad
model's 2 + 3 pF), which induces a voltage in the supply wires as well as the other way round, so breaking the loop
one way only is wrong (it predicted closed / open = 1.13 for a measured 3.9 at k = 0.9). Instead: series test
sources in the four wires (Vtp, Vtn, Visup, Vignd) give their 4 x 4 short-circuit admittance matrix Y(f) (four AC
runs). The K elements add series voltages e = jw M i with M = k M1 (M1: the coupling pattern at unit k, symmetric,
zero diagonal; the wires' self L stays in the circuit), so the coupled circuit has i = Y e = jw k Y M1 i, and a
pole sits on the jw axis where det(I - k jw Y M1) = 0, i.e. k = 1 / lambda for a real eigenvalue lambda of
jw Y M1. k_crit is the smallest such |k| (with its sign) over 10 MHz - 5 GHz. Checked: Y predicts the closed loop
with real K = +-0.9 elements to 1e-8 (sim/chain/stability_bond.py check), and kick mode runs the kick with real K.

usage: python3 sim/chain/stability_bond.py ac [--chain sch]      -> build/stab_ac/bond_ac_<chain>.json
       python3 sim/chain/stability_bond.py check                 -> Y model vs real K elements (closed loop)
       python3 sim/chain/stability_bond.py kick                  -> kick edges in k at a few cases
       python3 sim/chain/stability_bond.py combined              -> Ccpl_crit with the bond coupling present
       python3 sim/chain/stability_bond.py current               -> RF current in Lsup / Lgnd at -60 / -90 dBm
"""
import argparse, itertools, json, math, os, re, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import stab_deck as sd
import kick_edge as ke
from stability_ac import margins

OUT = os.path.join(sd.REPO, 'build/stab_ac')
CORNERS = [('tt', 27, 1.8), ('ss', 10, 1.8), ('sf', 27, 1.8), ('ff', 50, 1.8), ('ss', 10, 1.89)]


def fval(s):
    return float(str(s).replace('n', 'e-9').replace('p', 'e-12'))


def bond_deck(chain, corner, temp, vsup, vglo, L, Lb, vemf=0.0, keep_ac=False, test=False):
    """Bench with input bond wires and current sense on the supply wires. test: series AC test sources in the input
    wires (Vtp / Vtn, ac 0 to start)."""
    s = sd.base_deck(chain, corner, temp, vsup, vglo, L=L, vemf=vemf, keep_ac=keep_ac)
    for x in 'pn':
        if test:
            rep = f'Rant_{x} antb_{x} emf_{x} 36.5\nLb{x} antb_{x} antt_{x} {Lb}\nVt{x} antt_{x} ant_{x} dc 0 ac 0'
        else:
            rep = f'Rant_{x} antb_{x} emf_{x} 36.5\nLb{x} antb_{x} ant_{x} {Lb}'
        s, n = re.subn(rf'^Rant_{x} ant_{x} emf_{x} 36\.5$', rep, s, flags=re.M)
        assert n == 1
    s, n1 = re.subn(r'^Lsup vs1 VDPWR (.*)$', r'Visup vs1 vs1i 0\nLsup vs1i VDPWR \1', s, flags=re.M)
    s, n2 = re.subn(r'^Lgnd gchip GND (.*)$', r'Lgnd gchip gndi \1\nVignd gndi GND 0', s, flags=re.M)
    assert n1 == 1 and n2 == 1
    return s


def k_lines(agg, k, r):
    """K elements: aggressor 'sup', 'gnd' or 'both' to Lbp (k) and Lbn (r k). VGND's current runs die -> package
    for a positive i(Lgnd) (gchip -> GND), so its k takes the opposite sign for the same wire orientation."""
    s = ''
    for a, sg in (('sup', 1), ('gnd', -1)):
        if agg in (a, 'both'):
            L = 'Lsup' if a == 'sup' else 'Lgnd'
            s += f'K{a}p {L} Lbp {sg * k:.6g}\n'
            if r:
                s += f'K{a}n {L} Lbn {sg * k * r:.6g}\n'
    return s


PORTS = ['vtp', 'vtn', 'visup', 'vignd']   # input wire p, n, VDPWR wire, VGND wire (series sources)
LIDX = {'Lbp': 0, 'Lbn': 1, 'Lsup': 2, 'Lgnd': 3}


def ymatrix(chain, corner, temp, vsup, vglo, L, Lb, sweep='dec 400 10meg 5g'):
    s = bond_deck(chain, corner, temp, vsup, vglo, L, Lb, test=True)
    s = s.replace('Visup vs1 vs1i 0', 'Visup vs1 vs1i dc 0 ac 0').replace('Vignd gndi GND 0', 'Vignd gndi GND dc 0 ac 0')
    s += '.options method=GEAR\n.control\nop\n'
    for j, p in enumerate(PORTS):
        s += ''.join(f'alter @{q}[acmag]={1 if q == p else 0}\n' for q in PORTS)
        s += f'ac {sweep}\nwrdata y{j}.txt ' + ' '.join(f'i({q})' for q in PORTS) + '\n'
    s += '.endc\n.end\n'
    log = sd.run(s)
    Y = None
    for j in range(4):
        a = np.array(sd.wrfile(log, f'y{j}.txt'))
        f = a[:, 0]
        if Y is None:
            Y = np.zeros((len(f), 4, 4), complex)
        for i in range(4):
            Y[:, i, j] = a[:, 1 + 3 * i] + 1j * a[:, 2 + 3 * i]
    return f, Y, sd.check_op(log)


def m1(agg, r, L, Lb):
    """Unit-k mutual matrix from the K lines k_lines() writes (so the sign conventions are the same)."""
    M = np.zeros((4, 4))
    for line in k_lines(agg, 1.0, r).splitlines():
        _, a, b, k = line.split()
        la = fval(L) if a in ('Lsup', 'Lgnd') else fval(Lb)
        lb = fval(L) if b in ('Lsup', 'Lgnd') else fval(Lb)
        M[LIDX[a], LIDX[b]] = M[LIDX[b], LIDX[a]] = float(k) * math.sqrt(la * lb)
    return M


def k_crit(f, Y, M):
    """Smallest |k| (signed) where det(I - k jw Y M) = 0 on the jw axis, and its frequency."""
    lam = np.array([np.linalg.eigvals(2j * np.pi * fi * Yi @ M) for fi, Yi in zip(f, Y)])
    for i in range(1, len(f)):                 # follow the eigenvalue branches (nearest match)
        prev, cur = lam[i - 1], lam[i]
        best = min(itertools.permutations(range(4)), key=lambda p: sum(abs(cur[list(p)] - prev)))
        lam[i] = cur[list(best)]
    best = (None, None)
    for b in range(4):
        x = lam[:, b]
        for i in np.nonzero(np.sign(x.imag[:-1]) != np.sign(x.imag[1:]))[0]:
            a = x.imag[i] / (x.imag[i] - x.imag[i + 1])
            lr = x.real[i] + a * (x.real[i + 1] - x.real[i])
            if abs(lr) < 1e-12:
                continue
            k = 1 / lr
            if best[0] is None or abs(k) < abs(best[0]):
                best = (float(k), float(f[i] + a * (f[i + 1] - f[i])))
    return best


def mode_check(a):
    f, Y, _ = ymatrix(a.chain, 'ss', 10, 1.89, 1.8, '5n', '5n', sweep='dec 50 100meg 2g')
    for agg, r in (('sup', 0), ('gnd', 0.5), ('both', 1)):
        for k in (0.9, -0.9):
            s = bond_deck(a.chain, 'ss', 10, 1.89, 1.8, '5n', '5n', test=True) + k_lines(agg, k, r)
            s += ('.options method=GEAR\n.control\nop\nalter @vtp[acmag]=1\nac dec 50 100meg 2g\n'
                  'wrdata c.txt i(vtp) i(visup)\n.endc\n.end\n')
            c = np.array(sd.wrfile(sd.run(s), 'c.txt'))
            sim = np.c_[c[:, 1] + 1j * c[:, 2], c[:, 4] + 1j * c[:, 5]]
            M = k * m1(agg, r, '5n', '5n')
            pred = np.array([np.linalg.solve(np.eye(4) - 2j * np.pi * fi * Yi @ M, Yi[:, 0]) for fi, Yi in zip(f, Y)])
            err = np.abs(pred[:, [0, 2]] / sim - 1).max()
            print(f'ss10 1.89 V L 5n {agg} r {r} k {k:+}: max |Y model / sim - 1| = {err:.1e}, '
                  f'|i_sup| closed / open up to {np.abs(sim[:, 1] / Y[:, 2, 0]).max():.2f}')


def ac_case(chain, corner, temp, vsup, vglo, L, Lb):
    f, Y, warn = ymatrix(chain, corner, temp, vsup, vglo, L, Lb)
    np.save(os.path.join(OUT, f'Y_{chain}_{corner}{temp}_{vsup}_{vglo}_{L}.npy'), np.c_[f, Y.reshape(len(f), 16)])
    res = []
    for r in (0, 0.5, 1):
        for agg in ('sup', 'gnd', 'both'):
            k, fk = k_crit(f, Y, m1(agg, r, L, Lb))
            res.append(dict(chain=chain, corner=corner, temp=temp, vsup=vsup, vglo=vglo, L=L, Lb=Lb, r=r, agg=agg,
                            k_crit=k, f_crit=fk, warn=warn))
    return res


def mode_ac(a):
    cases = [(a.chain, *c, v, L, L) for c in CORNERS for v in (1.8, 0) for L in ('2n', '5n')]
    with ThreadPoolExecutor(a.jobs) as ex:
        res = sum(ex.map(lambda x: ac_case(*x), cases), [])
    json.dump(res, open(os.path.join(OUT, f'bond_ac_{a.chain}.json'), 'w'), indent=1)
    print('corner strap L=Lb r(pad_n / pad_p coupling) aggressor: k_crit @ f')
    for r in res:
        kc = f"{r['k_crit']:+.3g} @ {r['f_crit'] / 1e6:.0f} MHz" if r['k_crit'] else 'none'
        print(f"{r['corner']}{r['temp']} {r['vsup']} {'full' if r['vglo'] else 'low'} L {r['L']} r {r['r']} "
              f"{r['agg']}: {kc} {r['warn'] or ''}")


def mode_kick(a):
    """Kick edge in k (real K elements) at the cases asked, to check the AC k_crit."""
    cases = [('ss', 10, 1.8, 1.8, '2n', 'sup', 0, s) for s in (1, -1)] + \
            [('ss', 10, 1.8, 1.8, '2n', 'gnd', 0, s) for s in (1, -1)] + \
            [('ss', 10, 1.8, 1.8, '5n', 'sup', 0, s) for s in (1, -1)] + \
            [('tt', 27, 1.8, 1.8, '2n', 'sup', 0, s) for s in (1, -1)]
    inner = ThreadPoolExecutor(a.jobs)

    def make(c):
        corner, temp, vsup, vglo, L, agg, r, sgn = c

        def mk(k):
            return (bond_deck(a.chain, corner, temp, vsup, vglo, L, L, keep_ac=True) + k_lines(agg, sgn * k, r) +
                    sd.kick_control(f'k {k}'))
        return mk

    def go(c):
        return c, ke.find_edge(make(c), grid=[0.01, 0.03, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 0.99], pool=inner)
    with ThreadPoolExecutor(len(cases)) as ex:
        res = list(ex.map(go, cases))
    json.dump([dict(case=c, **r) for c, r in res], open(os.path.join(OUT, f'bond_kick_{a.chain}.json'), 'w'), indent=1)
    for c, r in res:
        print(c, 'ok', r['ok'], 'OSC', r['osc'])


def mode_combined(a):
    """Ccpl_crit (out_p -> pad_p / o1p) with the bond coupling present, both signs, sup and gnd aggressors."""
    sys.path.insert(0, os.path.dirname(__file__))
    cases = [(c, v, L, agg, k, sgn, node) for c in (('ss', 10, 1.8), ('tt', 27, 1.8)) for v in (1.8,)
             for L in ('2n', '5n') for agg in ('sup', 'gnd') for k in (0, 0.1, 0.3) for sgn in ((1, -1) if k else (1,))
             for node in ('pad_p', 'o1p')]

    def go(x):
        (corner, temp, vsup), v, L, agg, k, sgn, node = x
        s = bond_deck(a.chain, corner, temp, vsup, v, L, L) + k_lines(agg, sgn * k, 0)
        s += f"""Vt tdrv GND dc 0 ac 1
Ccpl tdrv {node} 1f
Cret out_p GND 1f
.options method=GEAR
.control
op
ac dec 400 10meg 5g
wrdata loop.txt v(out_p)
.endc
.end
"""
        lp = np.array(sd.wrfile(sd.run(s), 'loop.txt'))
        m = margins(lp[:, 0], lp[:, 1] + 1j * lp[:, 2], '1f')
        return dict(corner=corner, temp=temp, vglo=v, L=L, agg=agg, k=k, sign=sgn, node=node,
                    Ccpl_crit_fF=m.get('Ccpl_crit_fF'), f=m.get('f_GM'))
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(go, cases))
    json.dump(res, open(os.path.join(OUT, f'bond_combined_{a.chain}.json'), 'w'), indent=1)
    for r in res:
        print(f"{r['corner']}{r['temp']} L {r['L']} {r['agg']} k {r['sign'] * r['k']:+.2f} {r['node']}: Ccpl_crit "
              f"{r['Ccpl_crit_fF']:.3f} fF @ {r['f'] / 1e6:.0f} MHz")


def mode_current(a):
    """RF current in Lsup / Lgnd at 434 MHz (and 868 MHz) with a CW input at -60 and -90 dBm (from 73 ohm)."""
    f0 = 433.92e6
    cases = [(c, v, L, p) for c in (('tt', 27, 1.8), ('ss', 10, 1.8)) for v in (1.8, 0) for L in ('2n', '5n')
             for p in (-90, -60)]

    def go(x):
        (corner, temp, vsup), v, L, p = x
        vemf = 76.4e-6 * 10 ** ((p + 80) / 20)
        s = bond_deck(a.chain, corner, temp, vsup, v, L, L, vemf=vemf)
        s += """.save i(visup) i(vignd) v(out_p) v(out_n)
.options method=GEAR
.control
tran 20p 400n 0
linearize
let isup = i(visup)
let ignd = i(vignd)
let vod = v(out_p) - v(out_n)
wrdata tr.txt isup ignd vod
.endc
.end
"""
        t = np.array(sd.wrfile(sd.run(s), 'tr.txt'))
        tt_ = t[:, 0]
        ncyc = int(200e-9 * f0)
        sel = tt_ >= tt_[-1] - ncyc / f0
        out = dict(corner=corner, temp=temp, vglo=v, L=L, P_dBm=p)
        for name, col in (('isup', 1), ('ignd', 3), ('vod', 5)):
            y = t[sel, col]
            for h, fh in ((1, f0), (2, 2 * f0)):
                ph = np.exp(-2j * np.pi * fh * tt_[sel])
                out[f'{name}_h{h}'] = float(2 * abs(np.mean(y * ph)))
        return out
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(go, cases))
    json.dump(res, open(os.path.join(OUT, f'bond_current_{a.chain}.json'), 'w'), indent=1)
    for r in res:
        print(f"{r['corner']}{r['temp']} {'full' if r['vglo'] else 'low'} L {r['L']} {r['P_dBm']} dBm: "
              f"I(Lsup) 434 {r['isup_h1'] * 1e6:.3g} uA, 868 {r['isup_h2'] * 1e6:.3g} uA; "
              f"I(Lgnd) 434 {r['ignd_h1'] * 1e6:.3g} uA, 868 {r['ignd_h2'] * 1e6:.3g} uA; "
              f"out diff 434 {r['vod_h1'] * 1e3:.3g} mV")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['ac', 'check', 'kick', 'combined', 'current'])
    ap.add_argument('--chain', default='sch')
    ap.add_argument('--jobs', type=int, default=4)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    {'ac': mode_ac, 'check': mode_check, 'kick': mode_kick, 'combined': mode_combined, 'current': mode_current}[a.mode](a)


if __name__ == '__main__':
    main()
