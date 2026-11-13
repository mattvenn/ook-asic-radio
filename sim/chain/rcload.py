#!/usr/bin/env python3
"""(B) RC loads: a capacitor Cl across each chosen stage's load R (both halves), as a netlist edit.

The load R of every stage runs from the chain's VDD (VDPWR in tb_chain) to each output net, so 'Cl across the
load R' is a capacitor from VDPWR to o<k>p and to o<k>n (out_p / out_n for stage 6). Cl = 1 / (2 pi R f_pole)
with the stage's R (1 kOhm stage 1, 4 kOhm stages 2-6): the pole the load R and Cl alone would set. Nothing in
xschem/ changes.

Per variant and corner, one deck: the differential gain (EMF -> out) and every stage's output, NF at 448 MHz
(noise analysis, NF = onoise^2 / (|G|^2 4kT 73 ohm) as analyse.py), and the loop gain T through a Ccpl to pad_p
and to o1p (stability_ac.py's break, each test source on in turn), giving Ccpl_crit for each node.

usage: python3 sim/chain/rcload.py rolloff            # (B1) today's roll-off per stage, tt / ss 10 C
       python3 sim/chain/rcload.py sweep [--chain sch] # (B2-4) the variant sweep -> build/stab_ac/rcload_<chain>.json
"""
import argparse, json, math, os, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import stab_deck as sd
from stability_ac import margins

OUT = os.path.join(sd.REPO, 'build/stab_ac')
KT4_ANT = 4 * 1.380649e-23 * 300.15 * 73
CORNERS = [('tt', 27, 1.8), ('ss', 10, 1.8)]
SETS = {'all': [1, 2, 3, 4, 5, 6], 'last3': [4, 5, 6], 'last2': [5, 6], 's1': [1]}
FPOLES = [0.6e9, 0.8e9, 1.0e9, 1.5e9, 2.0e9, 3.0e9, 5.0e9]
TAPS = ['o1', 'o2', 'o3', 'o4', 'o5', 'out_']


def cl_lines(stages, fpole):
    s = ''
    for k in stages:
        p, n, r = sd.STAGES[k - 1]
        c = 1 / (2 * math.pi * r * fpole)
        s += f'Clp{k} VDPWR {p} {c:.4e}\nCln{k} VDPWR {n} {c:.4e}\n'
    return s


def deck(chain, corner, temp, vsup, vglo, extra, ccpl='1f'):
    s = sd.base_deck(chain, corner, temp, vsup, vglo, keep_ac=True) + extra
    nodes = ' '.join(f'v({sd.STAGES[i][0]}) v({sd.STAGES[i][1]})' for i in range(6))
    s += f"""Vt1 tdrv1 GND dc 0 ac 0
Ccpl1 tdrv1 pad_p {ccpl}
Vt2 tdrv2 GND dc 0 ac 0
Ccpl2 tdrv2 o1p {ccpl}
Cret out_p GND {ccpl}
.options method=GEAR
.control
op
ac dec 100 10meg 5g
let gp = v(pad_p) - v(pad_n)
let g1 = v(o1p) - v(o1n)
let g2 = v(o2p) - v(o2n)
let g3 = v(o3p) - v(o3n)
let g4 = v(o4p) - v(o4n)
let g5 = v(o5p) - v(o5n)
let g6 = v(out_p) - v(out_n)
wrdata gain.txt gp g1 g2 g3 g4 g5 g6
noise v(out_p,out_n) vant_p lin 1 448e6 448e6
setplot noise1
wrdata noise.txt onoise_spectrum
setplot ac1
alter @vant_p[acmag]=0
alter @vant_n[acmag]=0
alter @vt1[acmag]=1
ac dec 400 10meg 5g
wrdata loop1.txt v(out_p)
alter @vt1[acmag]=0
alter @vt2[acmag]=1
ac dec 400 10meg 5g
wrdata loop2.txt v(out_p)
.endc
.end
"""
    return s


def analyse(log, ccpl='1f'):
    g = np.array(sd.wrfile(log, 'gain.txt'))
    f = g[:, 0]
    v = [g[:, 1 + 3 * i] + 1j * g[:, 2 + 3 * i] for i in range(7)]   # pad, o1..o5, out
    gd = np.abs(v[6])
    gi = lambda x: float(20 * np.log10(np.interp(x, f, gd)))
    nz = np.array(sd.wrfile(log, 'noise.txt'))
    on = nz[0, 1]
    nf = float(10 * np.log10(on ** 2 / (np.interp(448e6, f, gd) ** 2 * KT4_ANT)))
    r = dict(g330=gi(330e6), g434=gi(433.92e6), g448=gi(448e6), g560=gi(560e6), nf448=nf, warn=sd.check_op(log))
    for node, fn in (('pad_p', 'loop1.txt'), ('o1p', 'loop2.txt')):
        lp = np.array(sd.wrfile(log, fn))
        m = margins(lp[:, 0], lp[:, 1] + 1j * lp[:, 2], ccpl)
        r[f'crit_{node}'] = m.get('Ccpl_crit_fF')
        r[f'fGM_{node}'] = m.get('f_GM')
    # roll-off: chain gain 20 / 40 dB below its 434 MHz value (above 434); each stage's upper -3 dB edge
    g434 = np.interp(433.92e6, f, gd)
    up = f > 433.92e6
    for d in (20, 40):
        idx = np.nonzero(up & (gd < g434 * 10 ** (-d / 20)))[0]
        r[f'f_minus{d}'] = float(f[idx[0]]) if len(idx) else None
    st = []
    for i in range(1, 7):
        a = np.abs(v[i] / v[i - 1])
        pk = a.argmax()
        idx = np.nonzero((np.arange(len(f)) > pk) & (a < a[pk] / math.sqrt(2)))[0]
        st.append(dict(peak_dB=float(20 * np.log10(a[pk])), f_peak=float(f[pk]),
                       f3dB_up=float(f[idx[0]]) if len(idx) else None,
                       g434_dB=float(20 * np.log10(np.interp(433.92e6, f, a)))))
    r['stages'] = st
    return r


def run_case(chain, corner, temp, vsup, vglo, name, stages, fpole):
    extra = cl_lines(stages, fpole) if stages else ''
    r = analyse(sd.run(deck(chain, corner, temp, vsup, vglo, extra)))
    r.update(chain=chain, corner=corner, temp=temp, vsup=vsup, vglo=vglo, variant=name, fpole=fpole)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['rolloff', 'sweep'])
    ap.add_argument('--chain', default='sch')
    ap.add_argument('--jobs', type=int, default=20)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    cases = [(a.chain, *c, v, 'none', [], 0) for c in CORNERS for v in (1.8, 0)]
    if a.mode == 'sweep':
        cases += [(a.chain, *c, 1.8, n, s, fp) for c in CORNERS for n, s in SETS.items() for fp in FPOLES]
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda x: run_case(*x), cases))
    json.dump(res, open(os.path.join(OUT, f'rcload_{a.mode}_{a.chain}.json'), 'w'), indent=1)
    base = {(r['corner'], r['vglo']): r for r in res if r['variant'] == 'none'}
    if a.mode == 'rolloff':
        for r in res:
            print(f"{r['corner']} {r['temp']} {'full' if r['vglo'] else 'low'}: G434 {r['g434']:.2f} dB, -20 dB at "
                  f"{r['f_minus20'] / 1e6:.0f} MHz, -40 dB at {(r['f_minus40'] or 0) / 1e6:.0f} MHz, NF448 {r['nf448']:.2f}, "
                  f"crit pad {r['crit_pad_p']:.3f} fF @ {r['fGM_pad_p'] / 1e6:.0f}, o1p {r['crit_o1p']:.3f} @ "
                  f"{r['fGM_o1p'] / 1e6:.0f} {r['warn']}")
            for i, s in enumerate(r['stages']):
                print(f"   stage {i + 1}: peak {s['peak_dB']:.2f} dB @ {s['f_peak'] / 1e6:.0f} MHz, "
                      f"434 {s['g434_dB']:.2f} dB, -3 dB upper edge {(s['f3dB_up'] or 0) / 1e6:.0f} MHz")
        return
    print('corner variant fpole | dG448 dG560 dB | NF448 (dNF) | crit pad_p fF (x) | crit o1p fF (x)')
    for r in res:
        b = base[(r['corner'], 1.8)] if r['vglo'] else base[(r['corner'], 0)]
        print(f"{r['corner']}{r['temp']} {'full' if r['vglo'] else 'low'} {r['variant']} {r['fpole'] / 1e9:.1f}G | "
              f"{r['g448'] - b['g448']:+.2f} {r['g560'] - b['g560']:+.2f} | {r['nf448']:.2f} ({r['nf448'] - b['nf448']:+.2f}) | "
              f"{r['crit_pad_p']:.3f} (x{r['crit_pad_p'] / b['crit_pad_p']:.2f}) | {r['crit_o1p']:.3f} "
              f"(x{r['crit_o1p'] / b['crit_o1p']:.2f}) {r['warn']}")


if __name__ == '__main__':
    main()
