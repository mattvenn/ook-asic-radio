#!/usr/bin/env python3
"""Kick-test stability edge in Ccpl (or any swept value), with stability.sh's kick (stab_deck.kick_control).

"OSC": the output is still >= 1 mV p-p at 250-300 ns AND not decaying (late p-p >= 0.97 x the 150-200 ns p-p): a
sustained (limiting, ~1-2 V) or growing oscillation. Otherwise "ok". stability.sh's own criterion (late p-p alone)
calls a slow ring-down just inside the edge "OSC": at ss 10 C, 0.4625 fF is still at mV at 300 ns but has decayed
by 600 ns (a 1 pA kick decays there too), which put the stability.sh edge 1-3 % below the true one. The edge is found on a grid, then bisected between the last ok and the first OSC to
REL (default 3 %).

usage: python3 sim/chain/kick_edge.py [--chain sch|pex] [--jobs N] [--nodes pad_p,o1p] [--corners tt27,...]
writes build/stab_ac/kick_<chain>.json; prints one line per case.
"""
import argparse, json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
import stab_deck as sd

GRID = [0.01, 0.1, 0.2, 0.5, 0.75, 1, 1.5, 2, 3, 4]   # fF
CORNERS = {'tt27': ('tt', 27, 1.8), 'ss10': ('ss', 10, 1.8), 'sf27': ('sf', 27, 1.8), 'ff50': ('ff', 50, 1.8),
           'ss10v189': ('ss', 10, 1.89)}
OUT = os.path.join(sd.REPO, 'build/stab_ac')


def kick(deck):
    r = sd.results(sd.run(deck))
    k = [x for x in r if x['kind'] == 'kick']
    if not k or not isinstance(k[0].get('late_pp'), float):
        return None
    return k[0]


def is_osc(k):
    return k['late_pp'] >= 1e-3 and k['late_pp'] >= 0.97 * k['mid_pp']


def find_edge(make_deck, grid=GRID, rel=0.03, pool=None):
    """make_deck(x) -> deck text. Returns dict(grid=[(x, growth, late_pp)], ok=x_ok, osc=x_osc)."""
    m = pool.map if pool else map
    ks = list(m(lambda x: kick(make_deck(x)), grid))
    pts = [(x, k['growth'], k['late_pp']) for x, k in zip(grid, ks)]
    lo, hi = None, None
    for x, k in zip(grid, ks):
        if is_osc(k):
            hi = x
            break
        lo = x
    res = dict(grid=pts, ok=lo, osc=hi)
    if lo is not None and hi is not None:
        while (hi - lo) / hi > rel:
            mid = (lo + hi) / 2
            k = kick(make_deck(mid))
            res['grid'].append((mid, k['growth'], k['late_pp']))
            if is_osc(k):
                hi = mid
            else:
                lo = mid
        res['ok'], res['osc'] = lo, hi
    return res


def ccpl_case(chain, corner, temp, vsup, vglo, node, extra=''):
    def make(x):
        return (sd.base_deck(chain, corner, temp, vsup, vglo, keep_ac=True) + extra +
                f'Ccpl out_p {node} {x}f\n' + sd.kick_control(f'C {x}'))
    return make


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chain', default='sch')
    ap.add_argument('--jobs', type=int, default=20)
    ap.add_argument('--nodes', default='pad_p,o1p')
    ap.add_argument('--corners', default=','.join(CORNERS))
    ap.add_argument('--straps', default='1.8,0')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    cases = [(a.chain, *CORNERS[c], float(v), n) for c in a.corners.split(',') for v in a.straps.split(',')
             for n in a.nodes.split(',')]
    inner = ThreadPoolExecutor(a.jobs)
    with ThreadPoolExecutor(len(cases)) as ex:
        res = list(ex.map(lambda cs: (cs, find_edge(ccpl_case(*cs), pool=inner)), cases))
    out = [dict(chain=c[0], corner=c[1], temp=c[2], vsup=c[3], vglo=c[4], node=c[5], **r) for c, r in res]
    json.dump(out, open(os.path.join(OUT, f'kick_{a.chain}.json'), 'w'), indent=1)
    for r in out:
        print(f"{r['chain']} {r['corner']} {r['temp']} {r['vsup']} {'full' if r['vglo'] else 'low'} {r['node']}: "
              f"ok {r['ok']} fF, OSC {r['osc']} fF")


if __name__ == '__main__':
    main()
