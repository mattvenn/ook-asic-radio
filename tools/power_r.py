"""DC resistance of every block supply pin to the tile's power pins (the met4 straps).

Traces each supply net's metal in the tile GDS (li .. met4 + mcon / via1-3; via3 on a MIM is
not a met3-met4 contact), rasterizes it on a grid, builds a conductance mesh (sheet R per layer,
R per via cut) and solves with the straps / power-pin shapes held at 0 V: for each block pin,
R = V(pin) for 1 A injected over the pin shape.

    tools/osic-mac python3 tools/power_r.py [gds] [pitch_um]      (default the routed tile, 0.25)

Limits: the straps count as ideal (the TT met5 grid lands on them every 57 um; their own R,
~0.04 ohm/um for 1.2 um met4, comes on top); diffusion / substrate paths are not counted.
"""
import json
import os
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
import klayout.db as db

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
GDS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build/top/tt_um_mattvenn_radio.gds')
P = float(sys.argv[2]) if len(sys.argv) > 2 else 0.25
DBU = 0.001
# sheet R (ohm/sq) and per-cut R (ohm), sky130 typical
LAY = [('li', (67, 20), 12.8), ('m1', (68, 20), 0.125), ('m2', (69, 20), 0.125),
       ('m3', (70, 20), 0.047), ('m4', (71, 20), 0.047)]
CUT = [('mcon', (67, 44), 9.3, 0.17), ('v1', (68, 44), 4.5, 0.15), ('v2', (69, 44), 3.4, 0.2),
       ('v3', (70, 44), 3.4, 0.2)]
NETS = ('VDPWR', 'VAPWR', 'VGND')
PINS = {'VDD', 'VSS', 'VAPWR', 'VDPWR', 'VGND'}


def main():
    ly = db.Layout()
    ly.read(GDS)
    top = ly.top_cell()
    for inst in list(top.each_inst()):            # the digital macro is not part of this
        if inst.cell.name == 'radio_digital':
            inst.delete()
    l2n = db.LayoutToNetlist(db.RecursiveShapeIterator(ly, top, []))
    L = {n: l2n.make_layer(ly.layer(*d), n) for n, d, _ in LAY}
    C = {n: l2n.make_layer(ly.layer(*d), n) for n, d, _, _ in CUT}
    capm = l2n.make_layer(ly.layer(89, 44), 'capm')
    C['v3'] = C['v3'] - capm
    for n, d in (('m3', (70, 5)), ('m4', (71, 5)), ('m3', (70, 16)), ('m4', (71, 16)), ('m1', (68, 5)),
                 ('m2', (69, 5)), ('m1', (68, 16))):
        l2n.connect(L[n], l2n.make_text_layer(ly.layer(*d), f'{n}t{d[1]}'))
    seq = ['li', 'mcon', 'm1', 'v1', 'm2', 'v2', 'm3', 'v3', 'm4']
    allL = {**L, **C}
    for n in seq:
        l2n.connect(allL[n])
    for a, b in zip(seq, seq[1:]):
        l2n.connect(allL[a], allL[b])
    l2n.extract_netlist()
    circ = l2n.netlist().circuit_by_name(top.name)
    P_ = json.load(open(os.path.join(ROOT, 'build/top/pins.json')))
    bb = top.dbbox()
    nx, ny = int(bb.width() / P) + 1, int(bb.height() / P) + 1

    def raster(reg, full=True):
        if reg.is_empty():
            return np.zeros((ny, nx))
        o = db.Point(0, 0)
        px = int(round(P / DBU))
        a = reg.rasterize(o, db.Vector(px, px), db.Vector(px, px), nx, ny)
        return np.array(a) * (DBU * DBU) / (P * P)      # coverage 0..1

    results = []
    for netname in NETS:
        nets = [n for n in circ.each_net() if netname in n.expanded_name().split(',')]
        if not nets:
            print(netname, 'not found')
            continue
        net = nets[0]
        cov = [raster(l2n.shapes_of_net(net, L[n], True).merged()) for n, _, _ in LAY]
        cut = [raster(l2n.shapes_of_net(net, C[n], True).merged()) for n, _, _, _ in CUT]
        # node index per (layer, cell) where coverage > 0
        idx = -np.ones((len(LAY), ny, nx), np.int64)
        cnt = 0
        for k in range(len(LAY)):
            m = cov[k] > 0.02
            idx[k][m] = np.arange(cnt, cnt + m.sum())
            cnt += int(m.sum())
        A_, B_, G_ = [], [], []
        for k, (_, _, rs) in enumerate(LAY):
            c, ix = cov[k], idx[k]
            for dy, dx in ((0, 1), (1, 0)):
                a = ix[:ny - dy, :nx - dx]; b = ix[dy:, dx:]
                ca = c[:ny - dy, :nx - dx]; cb = c[dy:, dx:]
                m = (a >= 0) & (b >= 0)
                A_.append(a[m]); B_.append(b[m]); G_.append(np.minimum(ca[m], cb[m]) / rs)  # R = rs / f
        for k, (_, _, rc, cs) in enumerate(CUT):       # cut k joins layer k and k+1
            m = (cut[k] > 0) & (idx[k] >= 0) & (idx[k + 1] >= 0)
            A_.append(idx[k][m]); B_.append(idx[k + 1][m]); G_.append(cut[k][m] * (P * P) / (cs * cs) / rc)
        a = np.concatenate(A_); b = np.concatenate(B_); g = np.concatenate(G_)
        rows = np.concatenate([a, b, a, b]); cols = np.concatenate([a, b, b, a])
        vals = np.concatenate([g, g, -g, -g])
        G = sp.csr_matrix((vals, (rows, cols)), shape=(cnt, cnt))
        # ties: the straps / power-pin shapes (met4 pin purpose with this net's label)
        tie = np.zeros(cnt, bool)
        lp, lt = ly.find_layer(71, 16), ly.find_layer(71, 5)
        texts = [s.text for s in top.shapes(lt).each() if s.is_text()]
        for s in top.shapes(lp).each():
            b = s.bbox()
            if any(t.string == netname and b.contains(t.trans.disp.to_p()) for t in texts):
                r = raster(db.Region(b))
                tie[idx[4][(r > 0.5) & (idx[4] >= 0)]] = True
        free = ~tie
        A = G[free][:, free].tocsc()
        lu = spl.splu(A)
        fmap = -np.ones(cnt, np.int64)
        fmap[free] = np.arange(free.sum())
        # sources: block supply pins on this net
        for inst, pins in P_['pins'].items():
            if inst == 'macro':
                continue
            for pn, shp in pins.items():
                if pn not in PINS:
                    continue
                for lay, bx in shp:
                    k = [n for n, _, _ in LAY].index({'li': 'li', 'm1': 'm1', 'm2': 'm2', 'm3': 'm3', 'm4': 'm4'}[lay])
                    r = raster(db.Region(db.DBox(*bx).to_itype(DBU)))
                    nodes = idx[k][(r > 0.3) & (idx[k] >= 0)]
                    if len(nodes) == 0:
                        continue
                    if tie[nodes].any():
                        results.append((netname, inst, pn, 0.0))
                        break
                    rhs = np.zeros(free.sum())
                    rhs[fmap[nodes]] = 1.0 / len(nodes)
                    try:
                        v = lu.solve(rhs)
                    except Exception:
                        continue
                    R = float(np.mean(v[fmap[nodes]]))
                    results.append((netname, inst, pn, R))
                    break
        print(f'{netname}: {cnt} nodes, {int(tie.sum())} tied', flush=True)
    out = os.path.join(ROOT, 'build/top/power_r.json')
    json.dump(results, open(out, 'w'), indent=0)
    for net, inst, pn, R in sorted(results, key=lambda r: (r[0], -r[3])):
        flag = '  (not connected to a strap?)' if R > 1e3 else ''
        print(f'{net:6s} {inst:12s} {pn:6s} {R:9.3f} ohm{flag}')


main()
