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
DECA1_MIM_TOP = 160.0           # xdeca part 1: MIM below this, MOS only above
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
        self.out = top                   # the cell routed shapes go into (per net: net['cell'])

    # ---------- obstacle database ----------
    def add_cell_inst(self, cell, trans, pins, tag_prefix, solid=None):
        """Metal of one placed instance. pins: {name: [(L, [x0,y0,x1,y1])]} (tile um). Polygons
        touching a pin get tag prefix.pin, the rest '?' (foreign to everyone). solid: {L: Box}
        blocked as a whole (the macro's core; its pins are tagged outside it)."""
        own = {}                                          # L -> {tag: Region} of this instance
        for L in LAYERS:
            li = self.ly.find_layer(*GDSL[L])
            reg = db.Region()
            if li is not None:
                reg = db.Region(db.RecursiveShapeIterator(self.ly, cell, li)).transformed(trans).merged()
            core = db.Region(solid[L]) if solid and L in solid else db.Region()
            tagged = db.Region()
            own[L] = {}
            for pn, shp in pins.items():
                for pl, b in shp:
                    if pl != L:
                        continue
                    hit = (reg.interacting(db.Region(ibox(*b))) + db.Region(ibox(*b))) - core
                    self.S.add(L, f'{tag_prefix}.{pn}', hit)
                    own[L][f'{tag_prefix}.{pn}'] = hit
                    tagged += hit
            self.S.add(L, '?', ((reg - tagged) + core).merged())
        li = self.ly.find_layer(*CAPM)
        if li is None:
            return
        capm = db.Region(db.RecursiveShapeIterator(self.ly, cell, li)).transformed(trans).merged()
        if capm.is_empty():
            return
        # capm is a met4 obstacle (no other net's met4 over a MIM), except under its own top
        # plate's net; MIM bottom plates keep other met3 1.2 um away (capm.2b_a): a halo of
        # (1.2 - 0.3) um, tagged like the plate so the plate's own net may still reach it
        self.capm = (getattr(self, 'capm', db.Region()) + capm).merged()
        rest = capm.dup()
        for tag, reg in own['m4'].items():
            mine = capm.interacting(reg)
            if not mine.is_empty():
                # a keep-out every net but the top plate's own must respect; never a terminal
                self.S.add('m4', tag + '~cap', mine)
                rest -= mine
        self.S.add('m4', '?', rest)
        # capm.2b_a: met3 not touching a bottom plate (capm & met3, grown 0.14) stays 1.2 away
        # from it. The halo is foreign to every net, the plate's own too (a wire that runs near
        # its plate without touching it is a violation): a plate is reached by a via onto it.
        halo = int(round((1.2 + 0.14 - SPACE['m3']) / DBU))
        m3all = db.Region(db.RecursiveShapeIterator(self.ly, cell, self.ly.find_layer(*GDSL['m3']))).transformed(trans).merged()
        plates = m3all.interacting(capm)
        bot = (capm & m3all).sized(int(round(0.14 / DBU)))
        ring = bot.sized(halo) - plates
        # a pin that is itself a plate: its net may come in on met3 right at the pin (the wire
        # then touches the plate, which the rule allows)
        for tag, reg in own['m3'].items():
            if reg.interacting(plates).is_empty():
                continue
            for pn, shp in pins.items():
                if f'{tag_prefix}.{pn}' != tag:
                    continue
                for pl, b in shp:
                    if pl == 'm3':
                        near = ring & db.Region(ibox(*b)).sized(int(round(1.3 / DBU)))
                        self.S.add('m3', tag + '~near', near)      # passable, not a terminal
                        ring -= near
        self.S.add('m3', '?h', ring)                   # a keep-out, not metal

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
        w = net.get('w', 0.3)
        hw = w / 2
        layers = net.get('layers', ['m2', 'm3', 'm4'])
        own = set(net['own']) | {name}
        own |= {t + '~near' for t in own} | {t + '~cap' for t in own}
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
            # met3 / met4 pads are blocked at 0.5 um: the middle pad of a via stack is drawn that
            # big (min area 0.24 um2)
            pad[(a, b)] = (max(w, cs + 2 * ea, 0.5 if a in ('m3', 'm4') else 0),
                           max(w, cs + 2 * eb, 0.5 if b in ('m3', 'm4') else 0))
        ownpad = np.zeros((nl, ny, nx), bool)
        for k, L in enumerate(LAYERS):
            o, f = self.S.split(L, own, wbox)
            owncell[k] = self.raster(o, win)
            ownpad[k] = self.raster(o.merged().sized(-int(round(0.25 / DBU))), win)
            if L not in layers:
                continue
            sp = SPACE[L]
            if L in ('m3', 'm4') and (w > 3.0 or net.get('wide')):
                sp = 0.4                                     # m3.3cd / m4.5ab (> 3 um metal)
            blocked[k] = self.raster(f.sized(int(round((hw + sp) / DBU))), win)
            if L in ('m3', 'm4') and sp < 0.4:
                # metal wider than 3 um wants 0.4 (m3.3cd / m4.5ab)
                wide = f.merged().sized(-1500).sized(1500)
                if not wide.is_empty():
                    blocked[k] |= self.raster(wide.sized(int(round((hw + 0.4) / DBU))), win)
            hp = max([w] + [p[0] for (a, b), p in pad.items() if a == L] + [p[1] for (a, b), p in pad.items() if b == L]) / 2
            padblk[k] = self.raster(f.sized(int(round((hp + sp) / DBU))), win)
            for ti, t in enumerate(terms):
                tr = db.Region()
                for tag in t:
                    if tag in self.S.r[L]:
                        tr += self.S.r[L][tag] & db.Region(wbox)
                # end only where the whole wire end lies inside the terminal (no slivers); a
                # terminal too small for that takes any cell on it (and gets a patch)
                inside = self.raster(tr.merged().sized(-int(round(hw / DBU))), win)
                termcells[ti][k] = inside if inside.any() else self.raster(tr, win)
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
        # no via2 within 0.1 of a MIM (capm.8): no met2 <-> met3 (or met1 <-> met2) via there
        cap = getattr(self, 'capm', db.Region()) & db.Region(wbox)
        capmask = self.raster(cap.sized(int(round((0.1 + 0.2) / DBU))), win) if not cap.is_empty() else None
        if os.environ.get('RDEBUG') == name:
            np.savez(os.path.join(REPO, 'build/top/rdebug.npz'), free=free, own=owncell,
                     terms=np.array(termcells), win=np.array(win))
        viaok = ~padblk | (ownpad & free)          # (a pad on an own shape must fit inside it)
        if capmask is not None:
            viaok[1] &= ~capmask
            # via3 not on a MIM keeps 0.08 from it (capm.5): no via3 in a band round each capm edge
            band = cap.sized(int(round((0.08 + 0.1 + 0.02) / DBU))) - cap.sized(-int(round((0.1 + 0.02) / DBU)))
            viaok[3] &= ~self.raster(band, win)
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
        # 'late' terminals (a strap, for a net drawn inside a subcell) connect only after all the
        # others, so the subcell's wiring is connected on its own
        late = [ti for ti, t in enumerate(terms) if set(t) & set(net.get('late', []))]
        first = [ti for ti in range(len(terms)) if ti not in late]
        tree = set(tsets[first[0]])
        remaining = first[1:]
        if net.get('anchors'):
            # start from shared anchors (straps, bars) only; every terminal then connects to
            # the nearest point of the growing tree
            am = np.zeros((nl, ny, nx), bool)
            for k, L in enumerate(LAYERS):
                ar = db.Region()
                for tag in net['anchors']:
                    if tag in self.S.r[L]:
                        ar += self.S.r[L][tag] & db.Region(wbox)
                am[k] = self.raster(ar, win)
            tree = cells(am)
            remaining = [ti for ti, t in enumerate(terms) if not set(t) <= set(net['anchors'])]
            if not tree:
                return self.fail(name, 'no free anchor cell', t0)
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
        while remaining or late:
            if not remaining:
                remaining, late = late, []
            # nearest remaining terminal (by bbox centre distance to the tree)
            # nearest remaining terminal first (bbox distance to the tree's bbox: cheap)
            tk = np.array([c for c in tree])
            def dist(ti):
                a = np.array(list(tsets[ti]))
                return abs(a[:, 1].mean() - tk[:, 1]).min() + abs(a[:, 2].mean() - tk[:, 2]).min()
            ti = min(remaining, key=dist)
            p = self.astar(tree, tsets[ti], free, viaok, cost, pref, wrong, viacost, (ny, nx))
            if p is None:
                return self.fail(name, f'no path to terminal {terms[ti]}', t0)
            paths.append(p)
            tree |= set(p) | tsets[ti]
            remaining.remove(ti)
        # draw
        return self.draw(net, paths, win, w, t0)

    def fixed(self, net):
        """Pre-computed geometry (net['fixed']): ('wire', L, x0, y0, x1, y1) centre lines of
        width net['w'], ('via', lo, hi, x, y)."""
        w = net.get('w', 0.3)
        hw = w / 2
        length = 0.0
        for it in net['fixed']:
            if it[0] == 'wire':
                _, L, x0, y0, x1, y1 = it
                x0, x1 = sorted((x0, x1))
                y0, y1 = sorted((y0, y1))
                self.rect(L, [x0 - hw, y0 - hw, x1 + hw, y1 + hw], net['name'])
                length += (x1 - x0) + (y1 - y0)
            elif it[0] == 'pad':
                _, L, x, y, a = it
                self.rect(L, [x - a / 2, y - a / 2, x + a / 2, y + a / 2], net['name'])
            else:
                _, lo, hi, x, y = it
                self.via(lo, hi, x, y, w, net['name'])
        # check: no fixed shape within the spacing of foreign metal (they aren't maze-routed)
        bad = []
        own = {net['name']} | set(net.get('own', []))
        for L in LAYERS:
            if net['name'] not in self.S.r[L]:
                continue
            mine = self.S.r[L][net['name']]
            keep = {t for t in self.S.r[L] if t.startswith('macro.') or t in (net['name'].split('[')[0],)}
            _, f = self.S.split(L, own | {net['name']} | {'macro.' + net['name'], net['name']}, mine.bbox().enlarged(2000, 2000))
            hit = mine.sized(int(round(SPACE[L] / DBU)) - 1) & f
            if not hit.is_empty():
                bad.append(f'{L} {hit.bbox().to_s()}')
        if bad:
            print(f'  FIXED CLASH {net["name"]}: ' + '; '.join(bad))
        self.report[net['name']] = {'ok': not bad, 'len': round(length, 1), 'fixed': True, 'clash': bad}

    def fail(self, name, why, t0):
        if os.environ.get('RDEBUG') == name and getattr(self, 'explored', None) is not None:
            m = np.zeros(int(np.prod(self.explored_shape)), bool)
            m[self.explored] = True
            np.save(os.path.join(REPO, 'build/top/rdebug_explored.npy'), m.reshape(self.explored_shape))
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
        self.explored = np.array(list(gbest.keys()))
        self.explored_shape = (nl, ny, nx)
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
            for ri, r in enumerate(runs):
                if isinstance(r, tuple):
                    _, a, b = r
                    lo, hi = sorted((a[0], b[0]))
                    x = (gx + a[2] + 0.5) * G
                    y = (gy + a[1] + 0.5) * G
                    self.via(LAYERS[lo], LAYERS[hi], x, y, w, tag)
                    nvia += 1
                    # a one-cell run between two vias is the middle pad of a stack: min area
                    if ri + 2 < len(runs) and len(runs[ri + 1]) == 1 and isinstance(runs[ri + 2], tuple):
                        Lm = LAYERS[b[0]]
                        if Lm in ('m3', 'm4'):
                            self.rect(Lm, [x - 0.25, y - 0.25, x + 0.25, y + 0.25], tag)
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
        # where a path ends on a terminal shape, fill the step between the wire end and the
        # shape (an off-centre junction leaves a sliver: m3.1 / m4.1)
        own = set(net['own'])
        for p in paths:
            for c in (p[0], p[-1]):
                L = LAYERS[c[0]]
                x, y = (gx + c[2] + 0.5) * G, (gy + c[1] + 0.5) * G
                sq = ibox(x - hw, y - hw, x + hw, y + hw)
                near = db.Region(ibox(x - hw - 0.5, y - hw - 0.5, x + hw + 0.5, y + hw + 0.5))
                clip = db.Region()
                for t2 in own:
                    if t2 in self.S.r[L]:
                        clip += self.S.r[L][t2] & near
                clip = clip.merged()
                if not (db.Region(sq) - clip).is_empty() and not clip.is_empty() and (db.Region(sq) & clip).is_empty() is False:
                    pass
                else:
                    continue
                if not (db.Region(sq) - clip).is_empty():
                    pass
                for poly in clip.each():
                    if poly.bbox().contains(db.Point(int(round(x / DBU)), int(round(y / DBU)))) or poly.bbox().overlaps(sq):
                        bb = poly.bbox() + sq
                        self.safe_add(L, db.Region(bb), tag, own)
        self.close_notches(tag, own, win)
        self.min_area(tag)
        if net.get('label'):
            p = paths[0][len(paths[0]) // 2]
            L = LAYERS[p[0]]
            x, y = (gx + p[2] + 0.5) * G, (gy + p[1] + 0.5) * G
            self.out.shapes(self.ly.layer(*LBLL[L])).insert(db.DText(net['label'], db.DTrans(x, y)))
        self.report[name] = {'ok': True, 'len': round(length, 1), 'vias': nvia, 't': round(time.time() - t0, 1)}
        print(f'  {name}: {length:.0f} um, {nvia} vias, {time.time() - t0:.1f} s')
        return True

    def close_notches(self, tag, own, win):
        """Fill same-net gaps under the spacing (a via pad next to a wire, a wire beside its pin):
        closing (grow, shrink) of this net's new shapes together with its own terminal shapes;
        only the filled difference is added (a gap that narrow can't hold another net)."""
        gx, gy, nx, ny = win
        wbox = db.Region(ibox(gx * G, gy * G, (gx + nx) * G, (gy + ny) * G))
        for L in LAYERS:
            if tag not in self.S.r[L]:
                continue
            mine = self.S.r[L][tag] & wbox
            if mine.is_empty():
                continue
            ref = mine.dup()
            for t2 in own:
                if t2 != tag and t2 in self.S.r[L]:
                    ref += self.S.r[L][t2].interacting(mine.sized(int(round(0.35 / DBU))))
            ref.merge()
            d = int(round(SPACE[L] / 2 / DBU)) + 1
            self.safe_add(L, ref.sized(d).sized(-d) - ref, tag, own)

    def safe_add(self, L, reg, tag, own):
        """Add reg to net tag on layer L, minus anything within the spacing of a foreign shape."""
        if reg.is_empty():
            return
        win = reg.bbox().enlarged(2000, 2000)
        keepouts = {t for t in self.S.r[L] if t == '?h' or t.endswith('~near') or t.endswith('~cap')}
        _, f = self.S.split(L, set(own) | {tag} | keepouts, win)
        reg = reg - f.sized(int(round(SPACE[L] / DBU)))
        # drop thin protrusions the clip may leave: open the merged own metal + fill, keep only
        # fill that survives (a notch fill makes the merged shape wider, so it stays)
        mw = int(round((0.3 if L in ('m3', 'm4') else 0.14) / 2 / DBU))
        o, _ = self.S.split(L, set(own) | {tag}, win)
        merged = (o + reg).merged()
        reg = reg & merged.sized(-mw).sized(mw)
        if reg.is_empty():
            return
        for poly in reg.each():
            self.out.shapes(self.li[L]).insert(poly)
        self.S.add(L, tag, reg)

    def min_area(self, tag):
        """Isolated met3 / met4 pieces of this net under the min area (0.24 um2): a 0.5 square."""
        for L in ('m3', 'm4'):
            if tag not in self.S.r[L]:
                continue
            for poly in self.S.r[L][tag].merged().each():
                if poly.area() * DBU * DBU < 0.24:
                    c = poly.bbox().center()
                    x, y = c.x * DBU, c.y * DBU
                    self.rect(L, [x - 0.25, y - 0.25, x + 0.25, y + 0.25], tag)

    def rect(self, L, b, tag):
        b = [snap(v) for v in b]
        self.out.shapes(self.li[L]).insert(db.DBox(*b))
        self.S.add(L, tag, db.Region(ibox(*b)))

    def via(self, lo, hi, x, y, w, tag):
        cut, cs, sp, elo, ehi = VIA[(lo, hi)]
        plo, phi = max(w, cs + 2 * elo), max(w, cs + 2 * ehi)
        self.rect(lo, [x - plo / 2, y - plo / 2, x + plo / 2, y + plo / 2], tag)
        self.rect(hi, [x - phi / 2, y - phi / 2, x + phi / 2, y + phi / 2], tag)
        e = max(elo, ehi)
        li = self.ly.layer(*cut)
        pitch = cs + sp
        a0, a1 = x - w / 2 + e, x + w / 2 - e                   # where cuts may sit
        b0, b1 = y - w / 2 + e, y + w / 2 - e
        # multi-cut arrays on a global cut grid: overlapping arrays (a wide wire's vias at
        # neighbouring cells) then share cuts instead of merging into over-long ones
        xs = [k * pitch for k in range(math.ceil(a0 / pitch), math.floor((a1 - cs) / pitch) + 1)]
        ys = [k * pitch for k in range(math.ceil(b0 / pitch), math.floor((b1 - cs) / pitch) + 1)]
        if len(xs) < 2 or len(ys) < 2:
            xs, ys = [x - cs / 2], [y - cs / 2]                  # small via: one centred cut
        if not hasattr(self, 'cuts'):
            self.cuts = {}
        placed = self.cuts.setdefault(cut, db.Region())
        for cx in xs:
            for cy in ys:
                cx, cy = snap(cx), snap(cy)
                c = db.Region(ibox(cx, cy, cx + cs, cy + cs))
                hit = placed.interacting(c.sized(int(round(sp / DBU)) - 1))
                if not hit.is_empty():
                    if (hit & c).area() == c.area():
                        continue                                  # the same cut
                    continue                                      # too close: the pads overlap
                placed.insert(ibox(cx, cy, cx + cs, cy + cs))
                self.out.shapes(li).insert(db.DBox(cx, cy, snap(cx + cs), snap(cy + cs)))


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
            if tag in ('VDPWR', 'VGND', 'VAPWR'):          # straps: by side (w / m / e)
                x = b.center().x * DBU
                tag += '@' + ('w' if x < 100 else 'm' if x < 290 else 'e')
            R.S.add(L, tag, db.Region(b))
    # decap areas not laid out (none now): reserve met1, met3, met4 (MOS + MIM); met2 stays free
    for b in FP['blocks'] if False else []:
        if b['cell'].startswith('decap_') and not (b['inst'] == 'xdecd' and b['part'] == 4):
            # (xdecd part 4, x 0-51 y 216-222, sits in the TT pin channel: left free for now)
            bx = [b['x'], max(b['y'], 3.2), b['x'] + b['w'], b['y'] + b['h']]   # (clear of the VDPWR bar)
            if b['inst'] == 'xdeca' and b['part'] == 1:
                # the top of part 1 (above the macro's lowest TT pin) is MOS only: met3 / met4 stay
                # free there for the TT wires' staircase down to the macro pins
                R.add_box('m1', '?', bx)
                bx = [bx[0], bx[1], bx[2], DECA1_MIM_TOP]
                R.add_box('m3', '?', bx)
                R.add_box('m4', '?', bx)
                continue
            for L in (['m3', 'm4'] if b.get('mim') else ['m1', 'm3', 'm4']):
                R.add_box(L, '?', bx)
    return R


def clip_to_die(ly, top):
    """Clip the top cell's own shapes to its prBoundary (TT precheck: nothing outside the die).
    Pads at the bottom-edge pins hang below y = 0 otherwise."""
    die = db.Region(top.shapes(ly.layer(235, 4)))
    for li in ly.layer_indexes():
        sh = top.shapes(li)
        r = db.Region(sh)
        if r.is_empty() or (r - die).is_empty():
            continue
        keep = [s.dtext for s in sh.each() if s.is_text()]
        sh.clear()
        sh.insert(r & die)
        for t in keep:
            sh.insert(t)


def main():
    if sys.argv[1:2] == ['--clip']:          # clip an already routed tile, no re-route
        ly = db.Layout(); ly.read(sys.argv[2]); clip_to_die(ly, ly.top_cell()); ly.write(sys.argv[2])
        return
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import top_nets
    out = os.path.join(REPO, 'build/top')
    R = build(os.path.join(out, 'tt_um_mattvenn_radio_place.gds'), os.path.join(out, 'pins.json'),
              os.path.join(REPO, 'layout/floorplan/floorplan.json'))
    only = sys.argv[1:]
    for net in top_nets.nets():
        if only and net['name'] not in only:
            continue
        R.out = R.ly.cell(net['cell']) if net.get('cell') else R.top
        if 'fixed' in net:
            R.fixed(net)
        else:
            R.route(net)
    for q in os.environ.get('RWHO', '').split(';'):
        if q:
            L, *b = q.split(',')
            print('WHO', q, who(R, L, *map(float, b)))
    clip_to_die(R.ly, R.top)
    R.ly.write(os.path.join(out, 'tt_um_mattvenn_radio.gds'))
    json.dump(R.report, open(os.path.join(out, 'route_report.json'), 'w'), indent=1)
    bad = [n for n, r in R.report.items() if not r['ok']]
    print(f'routed {len(R.report) - len(bad)} / {len(R.report)}', 'FAILED: ' + ' '.join(bad) if bad else '')



def who(R, L, x0, y0, x1, y1):
    """Tags of shapes on layer L touching the box (debug)."""
    b = db.Region(ibox(x0, y0, x1, y1))
    return [t for t, r in R.S.r[L].items() if not r.interacting(b).is_empty()]


if __name__ == '__main__':
    main()
