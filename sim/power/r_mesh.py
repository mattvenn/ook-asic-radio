"""DC resistance from each block's devices to the PDN, ngspice on the supply meshes (sim/power/mesh.py).

Per supply net: the port (the gate's output column / the VGND frame) at 0 V, 1 A shared equally
between the block's current-carrying device terminals (positions from the magic extraction,
sim/power/common.py probes; each put on the mesh's li cell there, else met1, else the nearest li /
met1 cell within 1.5 um), mean and worst terminal voltage = the block's R to the port. Metal islands
not connected to the port are dropped first (listed). Add pdn.R_GATE for the R to the gate's input.

    python3 sim/power/r_mesh.py [A|B]
Writes build/power/r_mesh_<case>.json and prints the table.
"""
import collections
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import common  # noqa: E402
from rawread import read_raw  # noqa: E402


def load_mesh(case, net):
    d = os.path.join(common.B, f'mesh_{case}')
    meta = json.load(open(os.path.join(d, f'{net}.json')))
    lines = open(os.path.join(d, f'{net}.spice')).read().splitlines()
    return meta, lines


def connected(lines, port):
    """Keep only the R lines in the port's connected component."""
    par = {}

    def f(a):
        par.setdefault(a, a)
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for ln in lines:
        t = ln.split()
        if t and t[0][0] == 'R':
            a, b = f(t[1]), f(t[2])
            if a != b:
                par[a] = b
    root = f(port)
    keep = [ln for ln in lines if not ln.startswith('R') or f(ln.split()[1]) == root]
    comp = collections.Counter(f(n) for n in list(par))
    return keep, {n for n in par if f(n) == root}, len(comp) - 1


def place(meta, xy, alive):
    """Mesh node for a point: li cell, else met1, else nearest li / met1 cell within 1.5 um."""
    p, x0, y0 = meta['p'], meta['x0'], meta['y0']
    ix, iy = int((xy[0] - x0) / p), int((xy[1] - y0) / p)
    for k in (0, 1):
        n = f'm{k}_{ix}_{iy}'
        if n in alive:
            return n
    best = None
    r = int(1.5 / p) + 1
    for k in (0, 1):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                n = f'm{k}_{ix + dx}_{iy + dy}'
                if n in alive:
                    d = dx * dx + dy * dy
                    if best is None or d < best[0]:
                        best = (d, n)
    return best[1] if best else None


def main(case):
    pr = common.probes(case)
    xy = common.node_xy(case)
    res, miss = {}, collections.Counter()
    for net in common.SUP:
        meta, lines = load_mesh(case, net)
        lines, alive, nisl = connected(lines, net)
        blks = [b for b in sorted(pr) if net in pr[b]]
        pts = {}
        for b in blks:
            nodes = []
            for t in pr[b][net]:
                n = place(meta, xy[t], alive)
                if n:
                    nodes.append(n)
                else:
                    miss[(b, net)] += 1
            if nodes:
                pts[b] = nodes
        name = f'r_mesh_{case}_{net}'
        deck = [f'* {name}: R from each block to the {net} port (mesh)'] + lines + [f'Vport {net} 0 0']
        for b, nodes in pts.items():
            deck.append(f'.param ib_{b}=0')
            for k, n in enumerate(nodes):
                deck.append(f"I_{b}_{k} 0 {n} dc 'ib_{b}/{len(nodes)}'")
        deck.append('.save ' + ' '.join(sorted({f'v({n})' for v in pts.values() for n in v})))
        deck.append('.control')
        for b in pts:
            deck += [f'alterparam ib_{b2}={1 if b2 == b else 0}' for b2 in pts]
            deck += ['reset', 'op', f'write {name}_{b}.raw', 'destroy all']
        deck += ['.endc', '.end']
        open(os.path.join(common.B, name + '.spice'), 'w').write('\n'.join(deck) + '\n')
        print(f'{net}: {len(alive)} nodes on the port\'s mesh, {nisl} islands dropped; solving', flush=True)
        subprocess.run([common.OSIC, 'bash', '-c', f'cd build/power && ngspice -b {name}.spice > {name}.log 2>&1'],
                       cwd=common.ROOT)
        for b, nodes in pts.items():
            v = read_raw(os.path.join(common.B, f'{name}_{b}.raw'))[0]['vars']
            vs = np.array([float(v[f'v({n})'][0]) for n in nodes])
            res.setdefault(b, {})[net] = {'mean': float(vs.mean()), 'max': float(vs.max()), 'n': len(vs)}
    json.dump(res, open(os.path.join(common.B, f'r_mesh_{case}.json'), 'w'), indent=1)
    if miss:
        print('terminals not placed on the mesh:', dict(miss))
    print(f'case {case}: R (ohm) from each block\'s device terminals to the port (mesh), mean / worst')
    print(f'{"block":12s} {"VDPWR":>14s} {"VAPWR":>14s} {"VGND":>14s}')
    for b in sorted(res):
        row = [f"{res[b][n]['mean']:6.2f} / {res[b][n]['max']:5.2f}" if n in res[b] else '' for n in common.SUP]
        print(f'{b:12s} ' + ' '.join(f'{c:>14s}' for c in row))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'A')
