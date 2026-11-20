#!/usr/bin/env python3
"""(A) Small-signal loop gain through the out_p -> node coupling capacitor Ccpl (docs/stability_ac_2026-11.md).

The loop break. In the closed loop Ccpl carries i = jwC (v(out_p) - v(X)) from out_p into X (pad_p or o1p).
Here Ccpl's out_p end is lifted onto an AC test source Vt (1 V) and out_p gets a C of the same value to ground:
  - X side: X sees jwC (v_t - v(X)), the closed-loop expression with v(out_p) replaced by v_t: exact.
  - out_p side: in the loop out_p's load is jwC (v(out_p) - v(X)); here jwC v(out_p). The two differ by
    v(X) / v(out_p) = 1 / (forward gain X -> out_p), so the break is accurate wherever the chain has gain, which is
    the only place |T| can approach 1.
So the return ratio is T = v(out_p) / v_t, and the loop oscillates when T = +1 (the coupling is positive feedback
when the phase of T is 0 mod 360). Both halves of the chain stay connected and only out_p is coupled, so T carries
the differential and the common-mode routes from X to out_p. T is linear in Ccpl to the extent that 1 fF loads
neither X nor out_p (pad_p ~5 pF, o1p 1 kOhm // ~0.1 pF), which the 0.1 / 1 fF pair checks.

Margins: gain margin GM = -20 log10 |T| at each frequency where the phase of T crosses 0 (Im T changes sign with
Re T > 0); the critical one is the smallest. Tolerable coupling: Ccpl_crit = Ccpl * 10^(GM/20). Phase margin:
at |T| = 1 (only reached above Ccpl_crit), the phase of T away from 0.

usage: python3 sim/chain/stability_ac.py [--chain sch|pex] [--jobs N] [--quick]
writes build/stab_ac/ac_<chain>.json and prints the table.
"""
import argparse, json, os, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import stab_deck as sd

CORNERS = [('tt', 27, 1.8), ('ss', 10, 1.8), ('sf', 27, 1.8), ('ff', 50, 1.8), ('ss', 10, 1.89)]
STRAPS = [1.8, 0]
NODES = ['pad_p', 'o1p']
CPLS = ['0.1f', '1f']
OUT = os.path.join(sd.REPO, 'build/stab_ac')


def fval(s):
    return float(s.replace('f', 'e-15').replace('p', 'e-12').replace('n', 'e-9'))


def loop_deck(chain, corner, temp, vsup, vglo, node, c, extra='', L='2n'):
    s = sd.base_deck(chain, corner, temp, vsup, vglo, L=L, keep_ac=True)
    s += extra
    s += f"""Vt tdrv GND dc 0 ac 0
Ccpl tdrv {node} {c}
Cret out_p GND {c}
.save v(out_p) v(out_n) v(o1p) v(o1n) v(o2p) v(o2n) v(o3p) v(o3n) v(o4p) v(o4n) v(o5p) v(o5n) v(pad_p) v(pad_n)
.options method=GEAR
.control
op
ac dec 100 10meg 5g
let gd = v(out_p) - v(out_n)
wrdata gain.txt gd
alter @vant_p[acmag]=0
alter @vant_n[acmag]=0
alter @vt[acmag]=1
ac dec 400 10meg 5g
wrdata loop.txt v(out_p)
.endc
.end
"""
    return s


def margins(f, T, c):
    """GM at phase-0 crossings, Ccpl_crit, PM at |T| = 1."""
    re_, im = T.real, T.imag
    cross = []
    for i in np.nonzero(np.sign(im[:-1]) != np.sign(im[1:]))[0]:
        a = im[i] / (im[i] - im[i + 1])                  # linear interpolation of Im T = 0
        fx = f[i] + a * (f[i + 1] - f[i])
        tx = T[i] + a * (T[i + 1] - T[i])
        if tx.real > 0:
            cross.append((fx, abs(tx)))
    r = {'crossings': [(float(fx), float(20 * np.log10(m))) for fx, m in cross]}
    if cross:
        fx, m = max(cross, key=lambda x: x[1])
        r['GM_dB'] = float(-20 * np.log10(m))
        r['f_GM'] = float(fx)
        r['Ccpl_crit_fF'] = float(fval(c) * 1e15 / m)
    mag = np.abs(T)
    r['Tmax_dB'] = float(20 * np.log10(mag.max()))
    r['f_Tmax'] = float(f[mag.argmax()])
    pm = []
    for i in np.nonzero((mag[:-1] - 1) * (mag[1:] - 1) < 0)[0]:
        a = (1 - mag[i]) / (mag[i + 1] - mag[i])
        tx = T[i] + a * (T[i + 1] - T[i])
        pm.append((float(f[i] + a * (f[i + 1] - f[i])), float(abs(np.degrees(np.angle(tx))))))
    if pm:
        r['PM_deg'], r['f_PM'] = min(pm, key=lambda x: x[1])[1], min(pm, key=lambda x: x[1])[0]
    return r


def one(chain, corner, temp, vsup, vglo, node, c):
    log = sd.run(loop_deck(chain, corner, temp, vsup, vglo, node, c))
    bad = sd.check_op(log)
    g = np.array(sd.wrfile(log, 'gain.txt'))
    lp = np.array(sd.wrfile(log, 'loop.txt'))
    f, T = lp[:, 0], lp[:, 1] + 1j * lp[:, 2]
    gd = np.abs(g[:, 1] + 1j * g[:, 2])
    r = dict(chain=chain, corner=corner, temp=temp, vsup=vsup, vglo=vglo, node=node, C=c, warn=bad,
             gain434_dB=float(20 * np.log10(np.interp(433.92e6, g[:, 0], gd))))
    r.update(margins(f, T, c))
    np.save(os.path.join(OUT, f'T_{chain}_{corner}{temp}_{vsup}_{vglo}_{node}_{c}.npy'), np.c_[f, T.real, T.imag])
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chain', default='sch')
    ap.add_argument('--jobs', type=int, default=16)
    ap.add_argument('--quick', action='store_true', help='ss 10 C, full gain, pad_p only')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    cases = [(a.chain, *k, v, n, c) for k in CORNERS for v in STRAPS for n in NODES for c in CPLS]
    if a.quick:
        cases = [x for x in cases if x[1:4] == ('ss', 10, 1.8) and x[4] == 1.8 and x[5] == 'pad_p']
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda x: one(*x), cases))
    json.dump(res, open(os.path.join(OUT, f'ac_{a.chain}.json'), 'w'), indent=1)
    print('chain corner T VSUP strap node C | gain434 | GM dB @ f | Ccpl_crit fF | |T|max dB @ f | PM | warn')
    for r in res:
        print(f"{r['chain']} {r['corner']} {r['temp']} {r['vsup']} {'full' if r['vglo'] else 'low'} {r['node']} "
              f"{r['C']} | {r['gain434_dB']:.2f} | {r.get('GM_dB', float('nan')):.2f} @ "
              f"{r.get('f_GM', float('nan')) / 1e6:.0f} MHz | {r.get('Ccpl_crit_fF', float('nan')):.3f} | "
              f"{r['Tmax_dB']:.1f} @ {r['f_Tmax'] / 1e6:.0f} | {r.get('PM_deg', '-')} | {r['warn']}")


if __name__ == '__main__':
    main()
