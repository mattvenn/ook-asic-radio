# Layout helpers: sky130 pcells (Mabrains, via KLayout's python), vias, rails, pins.
# Run generators inside the tools image: tools/osic klayout -b -r layout/gen/<block>.py
# The pcells need gdsfactory 8.x (the image has 9.x): tools/kpcell_setup.sh installs
# it into build/pyold, which goes first on sys.path here.
import sys, os, warnings
import pya

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
PDKDIR = os.path.join(os.environ['PDK_ROOT'], os.environ.get('PDK', 'sky130A'))
sys.path.insert(0, os.path.join(REPO, 'build', 'pyold'))
sys.path.insert(0, os.path.join(PDKDIR, 'libs.tech', 'klayout', 'python'))
os.environ.pop('PDK', None)          # gdsfactory would try to import a PDK module of that name
warnings.filterwarnings('ignore')
import gdsfactory as _gf             # noqa: E402
_gf.logger.remove()                  # silence the gf 7->8 deprecation chatter
from cells import sky130             # noqa: E402
sky130()

L = {   # sky130 GDS layer/datatype
    'nwell': (64, 20), 'diff': (65, 20), 'tap': (65, 44), 'poly': (66, 20), 'licon': (66, 44),
    'li': (67, 20), 'mcon': (67, 44), 'm1': (68, 20), 'via1': (68, 44), 'm2': (69, 20),
    'via2': (69, 44), 'm3': (70, 20), 'via3': (70, 44), 'm4': (71, 20), 'hvi': (75, 20),
    'nsdm': (93, 44), 'psdm': (94, 20), 'hvntm': (125, 20), 'prb': (235, 4),
}
PIN = {'li': (67, 16), 'm1': (68, 16), 'm2': (69, 16), 'm3': (70, 16), 'm4': (71, 16)}
LBL = {'li': (67, 5), 'm1': (68, 5), 'm2': (69, 5), 'm3': (70, 5), 'm4': (71, 5)}

# cut size, cut space, enclosure below, enclosure above (conservative: the larger
# "one of two adjacent sides" value on all sides)
VIA = {
    'mcon': (0.17, 0.19, 'li', 0.0, 'm1', 0.06),
    'via1': (0.15, 0.17, 'm1', 0.085, 'm2', 0.085),
    'via2': (0.20, 0.20, 'm2', 0.085, 'm3', 0.065),
    'via3': (0.20, 0.20, 'm3', 0.09, 'm4', 0.065),
}
STACK = ['li', 'm1', 'm2', 'm3', 'm4']
CUT = {('li', 'm1'): 'mcon', ('m1', 'm2'): 'via1', ('m2', 'm3'): 'via2', ('m3', 'm4'): 'via3'}

# flare(): per-axis enclosure (small, big) below then above: sky130 allows the small value on one
# axis when the other has the big one (via.5a / m2.4 / via2 / via3 "one of two adjacent sides")
ENC = {'via1': (0.055, 0.085, 0.055, 0.085), 'via2': (0.04, 0.085, 0.065, 0.065),
       'via3': (0.06, 0.09, 0.065, 0.065)}

G = 0.005   # manufacturing grid


def snap(v):
    return round(round(v / G) * G, 3)


def box(x0, y0, x1, y1):
    return pya.DBox(snap(min(x0, x1)), snap(min(y0, y1)), snap(max(x0, x1)), snap(max(y0, y1)))


class Block:
    """One cell being built: shapes by layer name, pcell instances, pins."""

    def __init__(self, name, ly=None):
        self.ly = ly or pya.Layout()
        self.ly.dbu = 0.001
        self.cell = self.ly.create_cell(name)
        self.name = name

    def li(self, lay):
        return self.ly.layer(*L[lay]) if lay in L else self.ly.layer(*lay)

    def rect(self, lay, b):
        if b.width() <= 0 or b.height() <= 0:
            return b
        self.cell.shapes(self.li(lay)).insert(b)
        return b

    def via(self, cut, b, enc=None):
        """Fill box b (the overlap of the two metals) with cuts of type cut, centred.
        Draws the cut layer only; the caller draws the metals. enc = (x, y)
        enclosure, for narrow strips (default: the conservative value all round)."""
        size, space, lo, elo, hi, ehi = VIA[cut]
        ex, ey = enc or (max(elo, ehi),) * 2
        w, h = b.width() - 2 * ex, b.height() - 2 * ey
        nx = max(0, int((w + space + 1e-9) // (size + space)))
        ny = max(0, int((h + space + 1e-9) // (size + space)))
        if nx == 0 or ny == 0:
            raise ValueError(f'{cut} does not fit in {b}')
        # snap the origin once, then step by the (on-grid) pitch: equal spacing
        x0 = snap(b.left + (b.width() - (nx * size + (nx - 1) * space)) / 2)
        y0 = snap(b.bottom + (b.height() - (ny * size + (ny - 1) * space)) / 2)
        for i in range(nx):
            for j in range(ny):
                x, y = snap(x0 + i * (size + space)), snap(y0 + j * (size + space))
                self.rect(cut, pya.DBox(x, y, snap(x + size), snap(y + size)))
        return nx * ny

    def stack(self, b, lo, hi):
        """Metal on every layer from lo to hi over box b, with cut arrays between."""
        i0, i1 = STACK.index(lo), STACK.index(hi)
        for k in range(i0, i1 + 1):
            self.rect(STACK[k], b)
        for k in range(i0, i1):
            self.via(CUT[(STACK[k], STACK[k + 1])], b)

    def clear(self, lays, b):
        """Cut box b out of the top cell's own shapes on each layer in lays (a gap in a
        rail for a pin to drop through: clear the metal and the cuts that land on it).
        Cut layers lose whole cuts within 0.1 of b (so what's left keeps its enclosure).
        A metal's pin shapes are cut too: magic reads them as metal."""
        dbu = self.ly.dbu
        for lay in list(lays) + [PIN[m] for m in lays if m in PIN]:
            sh = self.cell.shapes(self.li(lay))
            if lay in VIA:
                gone = pya.Region(b.enlarged(0.1, 0.1).to_itype(dbu))
                r = pya.Region(sh).select_not_interacting(gone)
            else:
                r = pya.Region(sh) - pya.Region(b.to_itype(dbu))
            sh.clear()
            sh.insert(r)

    def flare(self, cuts=('via1', 'via2', 'via3'), maxrow=3, keep=(), only=None, small=False, small_nets=None,
              skip_nets=None, target=None, netof=None, outline=None, verbose=False):
        """Via arrays at every junction (Harald Pretl's review point 11, docs/layout.md "Checklist").
        Every single cut and every 1 x n row (n <= maxrow) drawn in this cell becomes an array: >= 2 x 2
        where one fits, else 1 x 2. The array grows from the existing cut(s) on their pitch; both metals
        get a local pad (the array plus its enclosure), so the wires keep their width away from the
        junction. A candidate is drawn only if both pads keep the layer's spacing to every other metal
        shape (child cells included: the shapes not touching the cut), the new cuts keep the cut spacing
        to every other cut, stay 0.2 um clear of MIM (capm / cap2m; a met3 pad 1.4 um unless it is that
        MIM's bottom plate), and the pads stay inside the cell's outline (inset by half the spacing)
        wherever the metal isn't already outside it. Of the candidates, the one adding the least metal
        wins (least C).
        small=True (RF and sensitive nets): a single cut becomes 1 x 2 rather than 2 x 2, rows are left.
        small_nets / skip_nets: regexes on net names (from the cell's labels, KLayout connectivity): the
        junctions of matching nets get the small treatment / are left alone.
        keep: boxes whose cuts are left alone; only: if given, flare only cuts inside these boxes.
        target: a child Block placed in this cell (e.g. a half placed twice, mirrored): flare the child's
        own cuts instead, checked in every placement against this whole cell, drawn into the child (so
        the placements stay identical / symmetric). keep / only are in this cell's coordinates.
        outline: a pya.DBox to keep the pads inside instead of the cell's bounding box (inset by
        the layer's spacing / 2 all the same), e.g. the die minus a margin at the tile level.
        netof: callable(cut, box) -> net name (box in this cell's dbu coordinates), instead of the
        labels (e.g. the top-level router's own net tags).
        Adds shapes only; nothing drawn before is moved or removed.
        Returns [(cut, x, y, n, net)] for the junctions left as they were (no room)."""
        import re as _re
        dbu = self.ly.dbu
        I = lambda v: int(round(v / dbu))                       # noqa: E731
        SP = {'li': 0.17, 'm1': 0.14, 'm2': 0.14, 'm3': 0.3, 'm4': 0.3}
        top = self.cell
        tc = target.cell if target is not None else top
        Ts = [inst.cplx_trans for inst in top.each_inst() if inst.cell_index == tc.cell_index()] \
            if target is not None else [pya.ICplxTrans()]
        if not Ts:
            raise ValueError(f'{target.name} is not placed in {self.name}')

        def rec(lay):
            li = self.ly.find_layer(*lay)
            return pya.Region(top.begin_shapes_rec(li)) if li is not None else pya.Region()

        def tr(reg, T):
            return reg.transformed(T)

        outline = outline.to_itype(dbu) if outline is not None else top.bbox()
        cap = rec((89, 44)) + rec((97, 44))
        metal = {m: (rec(L[m]) + rec(PIN[m])).merged() for m in SP}
        kbox = pya.Region([b.to_itype(dbu) for b in keep])
        obox = pya.Region([b.to_itype(dbu) for b in only]) if only else None
        left = []
        if netof is None:
            netof = self._netof() if (small_nets or skip_nets or verbose) else (lambda cut, b: '?')
        for cut in cuts:
            size, space, lo, elo, hi, ehi = VIA[cut]
            cs, p = I(size), I(size + space)
            mine = pya.Region(tc.shapes(self.li(cut)))
            mine.merged_semantics = False
            allc = rec(L[cut])
            allc.merged_semantics = False
            for grp in mine.sized(I(0.125)).merged().each():
                gr = pya.Region(grp)
                cl = [c.bbox() for c in mine.interacting(gr).each()]
                n = len(cl)
                xs, ys = {c.left for c in cl}, {c.bottom for c in cl}
                old = pya.Region(cl)
                olds = [tr(old, T) for T in Ts]                  # the cluster in each placement
                net = netof(cut, olds[0].bbox())
                names = net.split(',')                          # a net with several labels
                sm = small or bool(small_nets and any(_re.fullmatch(small_nets, q) for q in names))
                if skip_nets and any(_re.fullmatch(skip_nets, q) for q in names):
                    continue
                if n > maxrow or (len(xs) > 1 and len(ys) > 1) or (sm and n > 1):
                    continue                                    # already an array (or a long row)
                if not kbox.is_empty() and any(not kbox.interacting(o).is_empty() for o in olds):
                    continue
                if obox is not None and all(obox.interacting(o).is_empty() for o in olds):
                    continue
                cc = olds[0].bbox().center()
                x0, y0 = min(xs), min(ys)
                cands = []                                       # (rank, new cut origins)
                if n == 1:
                    for dx in (-1, 1):
                        for dy in (-1, 1):
                            cands.append((0, [(x0 + dx * p, y0), (x0, y0 + dy * p), (x0 + dx * p, y0 + dy * p)]))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        cands.append((1, [(x0 + dx * p, y0 + dy * p)]))
                    if sm:
                        cands = [(1 - r, c) for r, c in cands]
                elif len(ys) == 1:                               # a row along x: a second row
                    for dy in (1, -1):
                        cands.append((0, [(x, y0 + dy * p) for x in sorted(xs)]))
                else:                                            # a column: a second column
                    for dx in (1, -1):
                        cands.append((0, [(x0 + dx * p, y) for y in sorted(ys)]))
                allold = pya.Region()
                for o in olds:
                    allold += o
                others = allc - allc.interacting(allold)
                owns = [{m: metal[m].interacting(o) for m in (lo, hi)} for o in olds]
                foreigns = [{m: metal[m] - ow[m] for m in (lo, hi)} for ow in owns]
                best = None
                for rank, new in cands:
                    nb = pya.Region([pya.Box(x, y, x + cs, y + cs) for x, y in new])
                    arr = (old + nb).bbox()
                    for ori in (0, 1):
                        pads = {}
                        for m, (es, eb) in ((lo, ENC[cut][:2]), (hi, ENC[cut][2:])):
                            ex, ey = (eb, es) if ori else (es, eb)
                            pads[m] = pya.Region(arr.enlarged(I(ex), I(ey)))
                        ok, cost = True, 0
                        padsT = []
                        for T, ow, fo in zip(Ts, owns, foreigns):
                            pT = {m: tr(pd, T) for m, pd in pads.items()}
                            r = self._flare_try(None, rank, tr(nb, T), pT, ow, fo, others, cap, outline, cut, space, SP, I)
                            if r is None:
                                ok = False
                                break
                            cost += r[0][1]
                            padsT.append((pT, ow))
                        # two placements' pads: apart by the spacing unless they are the same net
                        for a in range(len(padsT)):
                            for c in range(a + 1, len(padsT)):
                                for m in pads:
                                    if not ok:
                                        break
                                    if padsT[a][1][m].interacting(padsT[c][1][m]).is_empty() and \
                                            not (padsT[a][0][m] & padsT[c][0][m].sized(I(SP[m]) - 1)).is_empty():
                                        ok = False
                        if ok and (best is None or (rank, cost) < best[0]):
                            best = ((rank, cost), nb, pads)
                if best is None:
                    left.append((cut, round(cc.x * dbu, 3), round(cc.y * dbu, 3), n, net))
                    continue
                _, nb, pads = best
                for c in nb.each():
                    tc.shapes(self.li(cut)).insert(c)
                for T in Ts:
                    allc += tr(nb, T)
                for m, pd in pads.items():
                    # the pad, plus whatever closes a notch between it and the metal it joins (same net,
                    # under the spacing): only fill that is clear in every placement
                    d = I(SP[m] / 2) + 1
                    fill = None
                    for T, ow, fo in zip(Ts, owns, foreigns):
                        pT = tr(pd, T)
                        loc = (ow[m] + pT).merged()
                        f = ((loc.sized(d).sized(-d) - loc) & pT.sized(I(SP[m]))) - fo[m].sized(I(SP[m]))
                        f = tr(f, T.inverted())
                        fill = f if fill is None else fill & f
                    add = (pd + fill).merged()
                    for poly in add.each():
                        tc.shapes(self.li(m)).insert(poly)
                    for T in Ts:
                        metal[m] = (metal[m] + tr(add, T)).merged()
                if verbose:
                    print(f'  flare {cut} {net} ({cc.x * dbu:.2f}, {cc.y * dbu:.2f}): {n} -> {n + nb.count()}')
        if left:
            print(f'{self.name}: flare left {len(left)} junction(s) as they were:',
                  ', '.join(f'{c} {net} ({x}, {y}) n={n}' for c, x, y, n, net in left[:12]) + (' ...' if len(left) > 12 else ''))
        return left

    def _netof(self):
        """flare(): net name at a cut, from KLayout's connectivity (li .. met4, pins and labels as
        texts); '?' when no label names it."""
        ly, top = self.ly, self.cell
        l2n = pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly, top, []))
        lay, prev = {}, None
        capm = l2n.make_layer(ly.layer(89, 44), 'capm')
        for m in ('li', 'mcon', 'm1', 'via1', 'm2', 'via2', 'm3', 'via3', 'm4'):
            lay[m] = l2n.make_layer(ly.layer(*L[m]), m)
            l2n.connect(lay[m])
            if m == 'm4':                       # a via3 on a MIM lands on capm (the top plate), not met3
                v3 = lay['via3'] - capm
                l2n.register(v3, 'via3_m3')
                l2n.connect(lay['m3'], v3)
                l2n.connect(v3, lay['via3'])
                l2n.connect(lay['via3'], lay['m4'])
            elif prev and m != 'via3':
                l2n.connect(lay[prev], lay[m])
            prev = m
            if m in PIN:
                pn = l2n.make_layer(ly.layer(*PIN[m]), m + 'p')
                l2n.connect(pn)
                l2n.connect(lay[m], pn)
                for tl in (LBL[m], PIN[m]):
                    t = l2n.make_text_layer(ly.layer(*tl), m + 't%d' % tl[1])
                    l2n.connect(lay[m], t)
        l2n.extract_netlist()

        def netof(cut, b):
            n = l2n.probe_net(lay[cut], b.center())
            return n.expanded_name() if n is not None and n.name else '?'
        return netof

    def _flare_try(self, best, rank, nb, pads, own, foreign, others, cap, outline, cut, space, SP, I):
        """flare(): one candidate (new cuts nb, pads per metal): the better of it and best, or best."""
        for m, pd in pads.items():
            inner = pya.Region(outline.enlarged(-I(SP[m] / 2), -I(SP[m] / 2)))
            if not (pd - own[m] - inner).is_empty() or not (foreign[m] & pd.sized(I(SP[m]) - 1)).is_empty():
                return best
        if not (others & nb.sized(I(space) - 1)).is_empty():
            return best
        # capm.11: MIM 1.34 um from met3 that isn't its bottom plate
        if 'm3' in pads and own['m3'].interacting(cap).is_empty() and \
                not (cap & (pads['m3'] - own['m3']).sized(I(1.4))).is_empty():
            return best
        if cut in ('via2', 'via3') and not (cap & nb.sized(I(0.2))).is_empty():
            return best
        cost = sum((pd - own[m]).area() for m, pd in pads.items())
        if best is None or (rank, cost) < best[0]:
            return ((rank, cost), nb, pads)
        return best

    def pin(self, lay, b, name):
        """Pin shape + label on a metal (the metal itself must be drawn too)."""
        self.cell.shapes(self.li(PIN[lay])).insert(b)
        self.cell.shapes(self.li(LBL[lay])).insert(pya.DText(name, pya.DTrans(b.center().x, b.center().y)))

    def label(self, lay, b, name):
        """Net name on a metal (text only, no pin shape): names internal nets in the
        extracted netlist and the LVS report instead of magic's a_123_456#."""
        self.cell.shapes(self.li(LBL[lay])).insert(pya.DText(name, pya.DTrans(b.center().x, b.center().y)))

    def place(self, cell, x, y, rot=0, mirror=False):
        """Instance of cell, rotated by rot degrees (mirror about x first), then moved by (x, y)."""
        if rot == 0 and not mirror:
            return self.cell.insert(pya.DCellInstArray(cell.cell_index(), pya.DTrans(pya.DVector(snap(x), snap(y)))))
        return self.cell.insert(pya.DCellInstArray(cell.cell_index(), pya.DCplxTrans(1, rot, mirror, snap(x), snap(y))))

    def write(self, path, flatten=False):
        """flatten: pcells into the block, so their markers merge with the block's own (the TT precheck
        reads the GDS with magic 'gds maskhints yes': per-device hvi 0.16 um apart fails hvi.5 even under
        a covering hvi drawn in the parent)."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if flatten:
            self.cell.flatten(-1, True)
        self.ly.write(path)
        print('wrote', path, self.cell.dbbox())


class Fet:
    """A thick- or thin-oxide FET pcell with guard ring, plus where its terminals are.

    W is the total width (as in the schematic), split over nf fingers.
    gate: 'top' or 'bottom' (side of the gate contact pads).
    After placing at (x, y) (the origin is the diffusion's lower left), the
    attributes are absolute: strips[k] (met1 S/D strip boxes, left to right),
    pads[k] (met1 gate pads per finger), ring (outer box), hole (inner box), diff."""

    def __init__(self, blk, kind, W, l, nf=1, gate='top', vt='g5', bulk='guard ring', nfmax=None):
        typ = {('n', 'g5'): 'sky130_fd_pr__nfet_g5v0d10v5', ('p', 'g5'): 'sky130_fd_pr__pfet_g5v0d10v5',
               ('n', ''): 'sky130_fd_pr__nfet_01v8', ('p', ''): 'sky130_fd_pr__pfet_01v8',
               ('p', 'hvt'): 'sky130_fd_pr__pfet_01v8_hvt', ('n', 'lvt'): 'sky130_fd_pr__nfet_01v8_lvt',
               ('p', 'lvt'): 'sky130_fd_pr__pfet_01v8_lvt'}[(kind, vt)]
        if nfmax:                      # fold: fingers no taller than nfmax um
            nf = max(nf, -(-W // nfmax))
            nf = int(nf)
        self.blk, self.kind, self.nf, self.vt = blk, kind, nf, vt
        self.W, self.w = W, snap(W / nf)
        self.cell = blk.ly.create_cell('pfet' if kind == 'p' else 'nfet', 'skywater130',
                                       dict(type=typ, w=self.w, l=l, nf=nf, bulk=bulk,
                                            gate_con_pos=gate))
        ly = blk.ly

        def boxes(lay):
            li = ly.find_layer(*L[lay])
            return [] if li is None else [p for p in pya.Region(self.cell.begin_shapes_rec(li)).each()]
        dbu = ly.dbu
        self._diff = boxes('diff')[0].to_dtype(dbu).bbox()
        m1 = [p.to_dtype(dbu).bbox() for p in boxes('m1')]
        self._strips = sorted([b for b in m1 if b.bottom >= self._diff.bottom - 0.01 and b.top <= self._diff.top + 0.01],
                              key=lambda b: b.left)
        self._pads = sorted([b for b in m1 if b not in self._strips], key=lambda b: b.left)
        rings = [p for p in boxes('tap') if p.holes()]
        if rings:
            ring = rings[0].to_dtype(dbu)
            self._ring = ring.bbox()
            self._hole = pya.DPolygon(list(ring.each_point_hole(0))).bbox()
        else:
            self._ring = self._hole = self._diff
        self._bbox = self.cell.dbbox()
        assert len(self._strips) == nf + 1 and len(self._pads) == nf, (self._strips, self._pads)
        self.place(0, 0)

    def place(self, x, y):
        self.x, self.y = snap(x), snap(y)
        v = pya.DVector(self.x, self.y)
        self.diff = self._diff.moved(v)
        self.strips = [b.moved(v) for b in self._strips]
        self.pads = [b.moved(v) for b in self._pads]
        self.ring = self._ring.moved(v)
        self.hole = self._hole.moved(v)
        self.bbox = self._bbox.moved(v)
        return self

    def commit(self):
        self.blk.place(self.cell, self.x, self.y)
        return self

    @property
    def ringw(self):
        return self.hole.left - self.ring.left


def ring(blk, inner, kind, grw=0.4):
    """Guard ring (PDK guard_ring_gen pcell, tap + li + met1) around box inner.
    kind 'n': n+ tap (nsdm), for a PMOS row in nwell; 'p': p+ tap (psdm).
    Returns the outer box of the tap ring."""
    c = blk.ly.create_cell('guard_ring_gen', 'skywater130',
                           dict(in_w=snap(inner.width()), in_l=snap(inner.height()), grw=grw, con_lev='metal1',
                                implant_type='nsdm' if kind == 'n' else 'psdm'))
    # flattened: magic interprets each GDS cell on its own, so the tap only becomes an
    # HV (nwell, hvi) tap when it shares a cell with the nwell/hvi drawn by the caller
    blk.place(c, inner.left, inner.bottom).flatten()
    return box(inner.left - grw, inner.bottom - grw, inner.right + grw, inner.top + grw)


def cuts_needed(i_ma, cut):
    """Cuts for i_ma (RMS or avg) at 2x margin on the tech-LEF per-cut limit."""
    lim = {'mcon': 0.36, 'via1': 0.29, 'via2': 0.48, 'via3': 0.48}[cut]
    return max(1, int(-(-2 * i_ma // lim)))


def _si(expr):
    """SPICE number suffixes to Python (7.37k -> 7.37e3, 2Meg -> 2e6) for eval."""
    import re
    mult = {'t': 'e12', 'g': 'e9', 'meg': 'e6', 'k': 'e3', 'm': 'e-3', 'u': 'e-6', 'n': 'e-9', 'p': 'e-12', 'f': 'e-15'}
    return re.sub(r'(?<![\w.])(\d+\.?\d*)(meg|[tgkmunpf])(?![a-z])',
                  lambda m: m.group(1) + mult[m.group(2).lower()], expr, flags=re.I)


def write_ref(name, sch, params, drop=None):
    """LVS/PEX reference layout/ref/<name>.spice: the xschem netlist of xschem/<sch>.sch
    (LVS mode, top as a subckt) with the parameters substituted into quoted expressions
    (netgen can't evaluate W='0.42*kn'), the subckt renamed to name, and the lines whose
    instance name matches the regex drop removed (e.g. wiring-estimate caps)."""
    import math
    import re
    import subprocess
    tmp = os.path.join(REPO, 'build', 'lay', 'ref')
    os.makedirs(tmp, exist_ok=True)
    subprocess.run(['xschem', '-n', '-s', '-q', '--tcl', 'set top_subckt 1; set lvs_netlist 1', '-o', tmp,
                    f'xschem/{sch}.sch'], cwd=REPO, capture_output=True)
    src = open(os.path.join(tmp, f'{sch}.spice')).read()
    out = []
    for ln in src.splitlines():
        if ln.startswith(f'.subckt {sch}'):
            ln = re.sub(r'\s+\w+=\S+', '', ln).replace(f'.subckt {sch}', f'.subckt {name}')
        if drop and re.match(drop, ln.split()[0] if ln.split() else ''):
            continue
        ln = re.sub(r"(\w+)='([^']+)'", lambda m: f'{m.group(1)}={eval(_si(m.group(2)), {"sqrt": math.sqrt}, dict(params)):g}', ln)
        out.append(ln)
    os.makedirs(os.path.join(REPO, 'layout', 'ref'), exist_ok=True)
    with open(os.path.join(REPO, 'layout', 'ref', name + '.spice'), 'w') as fh:
        fh.write(f'* {name}: xschem/{sch}.sch with {params} (lay.write_ref)\n' + '\n'.join(out) + '\n')
