"""Grid router for the top level (layout/gen/top.py places, this routes).

A* on a 0.2 um grid over met1..met4. Obstacles are the real geometry of the placed tile (every
block's metal, MIM top plates as met4 obstacles, the macro), bloated per net by half its width +
the layer spacing, so a route is DRC-clean by construction (vias: the pad size is checked on
both layers). Each shape carries a tag: a block pin's polygon is tagged 'inst.pin', the tile
pins / straps by their net, routed wires by their route net. A net may touch only shapes whose
tag is in its own set; everything else keeps its distance.

Per net: width, layers, step costs (preferred direction per layer, vias), keep-out boxes,
"avoid" (extra cost within a distance of other nets' shapes), "follow" (cheaper next to an
already routed net: differential pairs), and ordered waypoints.

    tools/osic-mac python3 layout/gen/route.py      (after layout/gen/top.py)
"""
import heapq
import json
import math
import os
import sys
import time

import numpy as np
import klayout.db as db

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
G = 0.2                                   # grid pitch (um); cell centres at (i + 0.5) * G
DBU = 0.001
LAYERS = ['m1', 'm2', 'm3', 'm4']
GDSL = {'m1': (68, 20), 'm2': (69, 20), 'm3': (70, 20), 'm4': (71, 20)}
PINL = {'m1': (68, 16), 'm2': (69, 16), 'm3': (70, 16), 'm4': (71, 16)}
LBLL = {'m1': (68, 5), 'm2': (69, 5), 'm3': (70, 5), 'm4': (71, 5)}
CAPM = (89, 44)
SPACE = {'m1': 0.14, 'm2': 0.14, 'm3': 0.3, 'm4': 0.3}
# cut: size, space, enclosure below, enclosure above (as lay.py: conservative all round)
VIA = {('m1', 'm2'): ((68, 44), 0.15, 0.17, 0.085, 0.085),
       ('m2', 'm3'): ((69, 44), 0.20, 0.20, 0.085, 0.065),
       ('m3', 'm4'): ((70, 44), 0.20, 0.20, 0.09, 0.065)}


def snap(v):
    return round(round(v / 0.005) * 0.005, 3)


def ibox(x0, y0, x1, y1):
    return db.Box(int(round(x0 / DBU)), int(round(y0 / DBU)), int(round(x1 / DBU)), int(round(y1 / DBU)))


class Shapes:
    """Per layer: one Region per tag."""

    def __init__(self):
        self.r = {L: {} for L in LAYERS}

    def add(self, L, tag, region):
        if tag in self.r[L]:
            self.r[L][tag] += region
        else:
            self.r[L][tag] = region.dup()

    def split(self, L, own, win):
        """(own, foreign) Regions on layer L inside window win (db.Box)."""
        o, f = db.Region(), db.Region()
        for tag, reg in self.r[L].items():
            part = reg & db.Region(win)
            if part.is_empty():
                continue
            if tag in own:
                o += part
            else:
                f += part
        return o, f


class Router:
    def __init__(self, ly, top, W, H):
        self.ly, self.top, self.W, self.H = ly, top, W, H
        self.S = Shapes()
        self.li = {L: ly.layer(*GDSL[L]) for L in LAYERS}
        self.report = {}

    # ---------- obstacle database ----------
    def add_cell_inst(self, cell, trans, pins, tag_prefix, solid=None):
        """Metal of one placed instance. pins: {name: [(L, [x0,y0,x1,y1])]} (tile um). Polygons
        touching a pin get tag prefix.pin, the rest '?' (foreign to everyone). solid: {L: Box}
        to block as a whole instead (the macro's core)."""
        for L in LAYERS:
            li = self.ly.find_layer(*GDSL[L])
            reg = db.Region()
            if li is not None:
                it = db.RecursiveShapeIterator(self.ly, cell, li)
                reg = db.Region(it).transformed(trans).merged()
            if solid and L in solid:
                reg = (reg - db.Region(solid[L])) + db.Region(solid[L])
                reg.merge()
            tagged = db.Region()
            for pn, shp in pins.items():
                for pl, b in shp:
                    if pl != L:
                        continue
                    hit = reg.interacting(db.Region(ibox(*b)))
                    hit += db.Region(ibox(*b))
                    self.S.add(L, f'{tag_prefix}.{pn}', hit)
                    tagged += hit
            self.S.add(L, '?', reg - tagged)
        li = self.ly.find_layer(*CAPM)
        if li is not None:
            capm = db.Region(db.RecursiveShapeIterator(self.ly, cell, li)).transformed(trans).merged()
            if not capm.is_empty():
                self.S.add('m4', '?', capm)
                # MIM bottom plates keep other met3 1.2 um away (capm.2b_a): a halo of
                # (1.2 - 0.3) um, tagged like the plate so the plate's own net may still reach it
                halo = int(round((1.2 - SPACE['m3']) / DBU))
                for tag, reg in list(self.S.r['m3'].items()):
                    if not (tag == '?' or tag.startswith(tag_prefix + '.')):
                        continue
                    plates = reg.interacting(capm)
                    if not plates.is_empty():
                        self.S.add('m3', tag, plates.sized(halo) - plates)

    def add_box(self, L, tag, b):
        self.S.add(L, tag, db.Region(ibox(*b)))

    # ---------- grid ----------
    def window(self, boxes, margin):
        x0 = min(b[0] for b in boxes) - margin
        y0 = min(b[1] for b in boxes) - margin
        x1 = max(b[2] for b in boxes) + margin
        y1 = max(b[3] for b in boxes) + margin
        x0, y0 = max(0, math.floor(x0 / G)), max(0, math.floor(y0 / G))
        x1, y1 = min(int(self.W / G), math.ceil(x1 / G)), min(int(self.H / G), math.ceil(y1 / G))
        return x0, y0, x1 - x0, y1 - y0           # in cells

    def raster(self, reg, win):
        gx, gy, nx, ny = win
        if reg.is_empty():
            return np.zeros((ny, nx), bool)
        o = db.Point(int(round((gx + 0.5) * G / DBU)) - 1, int(round((gy + 0.5) * G / DBU)) - 1)
        a = reg.rasterize(o, db.Vector(int(G / DBU), int(G / DBU)), db.Vector(2, 2), nx, ny)
        return np.array(a) > 0

    # ---------- one net ----------
    def route(self, net):
        t0 = time.time()
        name = net['name']
        w = net.get('w', 0.4)
        hw = w / 2
        layers = net.get('layers', ['m2', 'm3', 'm4'])
        own = set(net['own']) | {name}
        terms = net['terms']                              # list of lists of tags (each one terminal)
        # terminal boxes, for the window
        tb = []
        for t in terms:
            for tag in t:
                for L in LAYERS:
                    if tag in self.S.r[L]:
                        bb = self.S.r[L][tag].bbox()
                        tb.append([bb.left * DBU, bb.bottom * DBU, bb.right * DBU, bb.top * DBU])
        for wp in net.get('via', []):
            tb.append([wp[0], wp[1], wp[0], wp[1]])
        if not tb:
            raise ValueError(f'{name}: no terminal shapes')
        win = self.window(tb, net.get('margin', 25))
        gx, gy, nx, ny = win
        wbox = ibox(gx * G - 5, gy * G - 5, (gx + nx) * G + 5, (gy + ny) * G + 5)
        nl = len(LAYERS)
        blocked = np.ones((nl, ny, nx), bool)
        padblk = np.ones((nl, ny, nx), bool)
        owncell = np.zeros((nl, ny, nx), bool)
        termcells = [np.zeros((nl, ny, nx), bool) for _ in terms]
        pad = {}
        for (a, b), (_, cs, _, ea, eb) in VIA.items():
            pad[(a, b)] = (max(w, cs + 2 * ea), max(w, cs + 2 * eb))
        for k, L in enumerate(LAYERS):
            o, f = self.S.split(L, own, wbox)
            owncell[k] = self.raster(o, win)
            if L not in layers:
                continue
            blocked[k] = self.raster(f.sized(int(round((hw + SPACE[L]) / DBU))), win)
            hp = max([w] + [p[0] for (a, b), p in pad.items() if a == L] + [p[1] for (a, b), p in pad.items() if b == L]) / 2
            padblk[k] = self.raster(f.sized(int(round((hp + SPACE[L]) / DBU))), win)
            for ti, t in enumerate(terms):
                tr = db.Region()
                for tag in t:
                    if tag in self.S.r[L]:
                        tr += self.S.r[L][tag] & db.Region(wbox)
                termcells[ti][k] = self.raster(tr, win)
        # cost map
        cost = np.ones((nl, ny, nx), float)
        pref = net.get('pref', {'m1': 'x', 'm2': 'y', 'm3': 'x', 'm4': 'y'})
        layer_cost = net.get('layer_cost', {'m1': 4.0, 'm2': 1.0, 'm3': 1.0, 'm4': 1.0})
        wrong = net.get('wrong', 3.0)
        for k, L in enumerate(LAYERS):
            cost[k] *= layer_cost.get(L, 1.0)
        for z in net.get('zones', []):                   # (x0, y0, x1, y1, [layers] or None, cost)
            x0, y0, x1, y1, zl, c = z
            j0, j1 = max(0, int(x0 / G) - gx), min(nx, int(math.ceil(x1 / G)) - gx)
            i0, i1 = max(0, int(y0 / G) - gy), min(ny, int(math.ceil(y1 / G)) - gy)
            if j0 >= j1 or i0 >= i1:
                continue
            for k, L in enumerate(LAYERS):
                if zl is None or L in zl:
                    if c == 'block':
                        blocked[k, i0:i1, j0:j1] = True
                        padblk[k, i0:i1, j0:j1] = True
                    else:
                        cost[k, i0:i1, j0:j1] += c
        if net.get('avoid') or net.get('follow'):
            from scipy.ndimage import distance_transform_edt
            for tags, dist, c in net.get('avoid', []):
                m = np.zeros((ny, nx), bool)
                for L in LAYERS:
                    reg = db.Region()
                    for tag in tags:
                        if tag in self.S.r[L]:
                            reg += self.S.r[L][tag] & db.Region(wbox)
                    m |= self.raster(reg, win)
                if m.any():
                    d = distance_transform_edt(~m) * G
                    cost += np.where(d < dist, c * (1 - d / dist), 0)[None]
            for tag, pitch in net.get('follow', []):
                m = np.zeros((ny, nx), bool)
                for L in LAYERS:
                    if tag in self.S.r[L]:
                        m |= self.raster(self.S.r[L][tag] & db.Region(wbox), win)
                if m.any():
                    d = distance_transform_edt(~m) * G
                    cost *= np.where((d >= pitch - 0.25) & (d <= pitch + 0.25), 0.4, 1.0)[None]
        for k, L in enumerate(LAYERS):
            if L not in layers:
                blocked[k] = True
                padblk[k] = True
        free = ~blocked
        viaok = ~padblk | (owncell & free)
        viacost = net.get('viacost', 6.0)

        def cells(mask):
            ks, iis, jjs = np.nonzero(mask & free)
            return set(zip(ks.tolist(), iis.tolist(), jjs.tolist()))

        # targets in order; the tree starts at the net's existing own shapes (if any route-net
        # shapes or shared anchors exist) else at terminal 0
        anchor = owncell & free
        tsets = [cells(m) for m in termcells]
        for ti, s in enumerate(tsets):
            if not s:
                return self.fail(name, f'terminal {terms[ti]} has no free cell', t0)
        wps = [(net.get('via_layer', None), wp) for wp in net.get('via', [])]
        tree = set(tsets[0])
        if net.get('anchor_own', False):
            tree |= cells(anchor)
        remaining = list(range(1, len(tsets)))
        paths = []
        # waypoints: route terminal 0 -> wp1 -> wp2 ... -> terminal 1 (2-terminal nets)
        seq_targets = []
        for _, wp in wps:
            j, i = int(wp[0] / G) - gx, int(wp[1] / G) - gy
            lays = [LAYERS.index(wp[2])] if len(wp) > 2 else [k for k, L in enumerate(LAYERS) if L in layers]
            seq_targets.append(set((k, i, j) for k in lays if 0 <= i < ny and 0 <= j < nx and free[k, i, j]))
        for st in seq_targets:
            if not st:
                return self.fail(name, 'waypoint blocked', t0)
            p = self.astar(tree, st, free, viaok, cost, pref, wrong, viacost, (ny, nx))
            if p is None:
                return self.fail(name, f'no path to waypoint', t0)
            paths.append(p)
            tree = set(p)                               # continue from the waypoint path only
            tree = {p[-1]}
        while remaining:
            # nearest remaining terminal (by bbox centre distance to the tree)
            best = None
            for ti in remaining:
                p = self.astar(tree, tsets[ti], free, viaok, cost, pref, wrong, viacost, (ny, nx))
                if p is None:
                    return self.fail(name, f'no path to terminal {terms[ti]}', t0)
                best = (ti, p)
                break
            ti, p = best
            paths.append(p)
            tree |= set(p) | tsets[ti]
            remaining.remove(ti)
        # draw
        return self.draw(net, paths, win, w, t0)

    def fail(self, name, why, t0):
        self.report[name] = {'ok': False, 'why': why, 't': round(time.time() - t0, 1)}
        print(f'  FAIL {name}: {why}')
        return False

    def astar(self, src, dst, free, viaok, cost, pref, wrong, viacost, shape):
        ny, nx = shape
        nl = len(LAYERS)
        dk = np.array([d[0] for d in dst]); di = np.array([d[1] for d in dst]); dj = np.array([d[2] for d in dst])
        bi0, bi1, bj0, bj1 = di.min(), di.max(), dj.min(), dj.max()
        dset = dst

        def h(i, j):
            return (max(0, bi0 - i, i - bi1) + max(0, bj0 - j, j - bj1))

        N = nl * ny * nx
        gbest = {}
        prev = {}
        pq = []
        for s in src:
            k, i, j = s
            idx = (k * ny + i) * nx + j
            gbest[idx] = 0.0
            prev[idx] = -1
            heapq.heappush(pq, (h(i, j), 0.0, idx))
        prefx = [pref.get(L) == 'x' for L in LAYERS]
        prefy = [pref.get(L) == 'y' for L in LAYERS]
        while pq:
            f, g, idx = heapq.heappop(pq)
            if g > gbest.get(idx, 1e18):
                continue
            k, rem = divmod(idx, ny * nx)
            i, j = divmod(rem, nx)
            if (k, i, j) in dset:
                path = []
                while idx != -1:
                    k2, r2 = divmod(idx, ny * nx)
                    path.append((k2, r2 // nx, r2 % nx))
                    idx = prev[idx]
                return path[::-1]
            c0 = cost[k, i, j]
            for dk_, di_, dj_ in ((0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0)):
                k2, i2, j2 = k + dk_, i + di_, j + dj_
                if not (0 <= k2 < nl and 0 <= i2 < ny and 0 <= j2 < nx):
                    continue
                if dk_:
                    if not (viaok[k, i, j] and viaok[k2, i, j]):
                        continue
                    step = viacost
                else:
                    if not free[k2, i2, j2]:
                        continue
                    step = 0.5 * (c0 + cost[k2, i2, j2])
                    if dj_ and prefy[k] or di_ and prefx[k]:
                        step *= wrong
                g2 = g + step
                idx2 = (k2 * ny + i2) * nx + j2
                if g2 < gbest.get(idx2, 1e18):
                    gbest[idx2] = g2
                    prev[idx2] = idx
                    heapq.heappush(pq, (g2 + h(i2, j2), g2, idx2))
        return None

    def draw(self, net, paths, win, w, t0):
        gx, gy, nx, ny = win
        name = net['name']
        hw = w / 2
        tag = name
        length, nvia = 0.0, 0
        cell = self.top
        for p in paths:
            # split into same-layer runs
            runs, cur = [], [p[0]]
            for a, b in zip(p, p[1:]):
                if a[0] == b[0]:
                    cur.append(b)
                else:
                    runs.append(cur)
                    runs.append(('via', a, b))
                    cur = [b]
            runs.append(cur)
            for r in runs:
                if isinstance(r, tuple):
                    _, a, b = r
                    lo, hi = sorted((a[0], b[0]))
                    x = (gx + a[2] + 0.5) * G
                    y = (gy + a[1] + 0.5) * G
                    self.via(LAYERS[lo], LAYERS[hi], x, y, w, tag)
                    nvia += 1
                    continue
                L = LAYERS[r[0][0]]
                # straight segments
                seg = [r[0]]
                for a, b, c in zip(r, r[1:], r[2:]):
                    if (b[1] - a[1], b[2] - a[2]) != (c[1] - b[1], c[2] - b[2]):
                        seg.append(b)
                seg.append(r[-1])
                for a, b in zip(seg, seg[1:]):
                    x0, x1 = sorted(((gx + a[2] + 0.5) * G, (gx + b[2] + 0.5) * G))
                    y0, y1 = sorted(((gy + a[1] + 0.5) * G, (gy + b[1] + 0.5) * G))
                    self.rect(L, [x0 - hw, y0 - hw, x1 + hw, y1 + hw], tag)
                    length += (x1 - x0) + (y1 - y0)
                if len(seg) == 1:
                    x, y = (gx + seg[0][2] + 0.5) * G, (gy + seg[0][1] + 0.5) * G
                    self.rect(L, [x - hw, y - hw, x + hw, y + hw], tag)
        if net.get('label'):
            p = paths[0][len(paths[0]) // 2]
            L = LAYERS[p[0]]
            x, y = (gx + p[2] + 0.5) * G, (gy + p[1] + 0.5) * G
            self.top.shapes(self.ly.layer(*LBLL[L])).insert(db.DText(net['label'], db.DTrans(x, y)))
        self.report[name] = {'ok': True, 'len': round(length, 1), 'vias': nvia, 't': round(time.time() - t0, 1)}
        print(f'  {name}: {length:.0f} um, {nvia} vias, {time.time() - t0:.1f} s')
        return True

    def rect(self, L, b, tag):
        b = [snap(v) for v in b]
        self.top.shapes(self.li[L]).insert(db.DBox(*b))
        self.S.add(L, tag, db.Region(ibox(*b)))

    def via(self, lo, hi, x, y, w, tag):
        cut, cs, sp, elo, ehi = VIA[(lo, hi)]
        plo, phi = max(w, cs + 2 * elo), max(w, cs + 2 * ehi)
        self.rect(lo, [x - plo / 2, y - plo / 2, x + plo / 2, y + plo / 2], tag)
        self.rect(hi, [x - phi / 2, y - phi / 2, x + phi / 2, y + phi / 2], tag)
        e = max(elo, ehi)
        n = max(1, int((w - 2 * e + sp + 1e-9) // (cs + sp)))
        span = n * cs + (n - 1) * sp
        li = self.ly.layer(*cut)
        for a in range(n):
            for b in range(n):
                cx = snap(x - span / 2 + a * (cs + sp))
                cy = snap(y - span / 2 + b * (cs + sp))
                self.top.shapes(li).insert(db.DBox(cx, cy, snap(cx + cs), snap(cy + cs)))


def build(place_gds, pins_json, fp_json):
    ly = db.Layout()
    ly.read(place_gds)
    top = ly.top_cell()
    P = json.load(open(pins_json))
    FP = json.load(open(fp_json))
    W, H = FP['tile']['w'], FP['tile']['h']
    R = Router(ly, top, W, H)
    # placed instances (tx_top's children in tile coordinates: tx_top sits at the origin)
    insts = []
    for inst in top.each_inst():
        if inst.cell.name == 'tx_top':
            for i2 in inst.cell.each_inst():
                insts.append((i2.cell, inst.dcplx_trans * i2.dcplx_trans))
        else:
            insts.append((inst.cell, inst.dcplx_trans))
    for name, bb in P['insts'].items():
        m = [(c, t) for c, t in insts if abs(c.dbbox().transformed(t).left - bb[0]) < 0.01
             and abs(c.dbbox().transformed(t).bottom - bb[1]) < 0.01 and abs(c.dbbox().transformed(t).right - bb[2]) < 0.01]
        assert len(m) == 1, (name, len(m))
        c, t = m[0]
        solid = None
        if name == 'macro':
            core = ibox(bb[0] + 2.0, bb[1], bb[2], bb[3])           # pins on its west edge
            solid = {L: core for L in LAYERS}
        R.add_cell_inst(c, t.to_itrans(DBU), P['pins'][name], name, solid)
    # top-cell shapes: template pins and straps, tagged by their label
    for L in LAYERS:
        li = ly.find_layer(*GDSL[L])
        lt = ly.find_layer(*LBLL[L])
        if li is None:
            continue
        texts = [s.text for s in top.shapes(lt).each() if s.is_text()] if lt is not None else []
        for s in top.shapes(li).each():
            b = s.bbox()
            tag = '?'
            for t in texts:
                if b.contains(t.trans.disp.to_p()):
                    tag = t.string
                    break
            R.S.add(L, tag, db.Region(b))
    # decap areas (not laid out yet): reserve met1, met3, met4 (MOS + MIM); met2 stays free
    for b in FP['blocks']:
        if b['cell'].startswith('decap_'):
            bx = [b['x'], b['y'], b['x'] + b['w'], b['y'] + b['h']]
            for L in (['m3', 'm4'] if b.get('mim') else ['m1', 'm3', 'm4']):
                R.add_box(L, '?', bx)
    return R


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import top_nets
    out = os.path.join(REPO, 'build/top')
    R = build(os.path.join(out, 'tt_um_mattvenn_radio_place.gds'), os.path.join(out, 'pins.json'),
              os.path.join(REPO, 'layout/floorplan/floorplan.json'))
    only = sys.argv[1:]
    for net in top_nets.nets():
        if only and net['name'] not in only:
            continue
        R.route(net)
    R.ly.write(os.path.join(out, 'tt_um_mattvenn_radio.gds'))
    json.dump(R.report, open(os.path.join(out, 'route_report.json'), 'w'), indent=1)
    bad = [n for n, r in R.report.items() if not r['ok']]
    print(f'routed {len(R.report) - len(bad)} / {len(R.report)}', 'FAILED: ' + ' '.join(bad) if bad else '')


if __name__ == '__main__':
    main()
