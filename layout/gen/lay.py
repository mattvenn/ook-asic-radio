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
