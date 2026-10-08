# Passive primitives for the layout generators (on top of lay.py):
#   PolyRes : a precision poly resistor as nseg series segments of the PDK res_poly pcell
#             (LVS: netgen adds series L, so it matches one schematic device of the total L)
#   mim     : a cap_mim_m3_1 (capm over a met3 bottom plate), own geometry: the top plate
#             is contacted by a met4 strip only, not a full met4 plate as in the PDK pcell
#             (keeps met4 sparse for the top-level power straps)
import pya
from lay import Block, L, box, snap   # noqa: F401

CAPM = (89, 44)
# capm rules (sky130A_mr.drc): width 1.0, space 0.84, met3 enclosure 0.14, via3 enclosure
# 0.14; bottom plate (capm grown 0.14) to other met3 1.2
CAPM_ENC_M3 = 0.2      # met3 bottom plate past capm (rule 0.14)
CAPM_ENC_V3 = 0.14
BOT_PLATE_SPACE = 1.2  # bottom plate to unrelated met3


class PolyRes:
    """nseg vertical segments of res_poly (default xhigh 0.35 um), total length L_total,
    side by side at pitch, joined in series by met1 bridges at alternating ends
    (a serpentine of straight segments: each segment is one device for magic).
    Origin (x, y): lower left of the array's poly. After place():
      ends   = (first, last) met1 head pads (boxes): first = bottom of segment 0,
               last = segment nseg-1's free head (bottom if nseg is even);
      links  = [met1 bridge boxes], links[k] joins segment k and k+1;
      bbox   = the array's extent (all layers), poly = the array's poly extent.
    Head pads are widened to pad_w so a via1 fits."""

    def __init__(self, blk, L_total, nseg, w=0.35, typ='sky130_fd_pr__res_xhigh_po_0p35',
                 pitch=1.0, pad_w=0.4):
        self.blk, self.nseg, self.pitch, self.pad_w = blk, nseg, pitch, pad_w
        self.lseg = snap(L_total / nseg)
        # the pcell's poly.res (what magic measures) comes out 0.12 um longer than 'len'
        self.cell = blk.ly.create_cell('res_poly', 'skywater130',
                                       dict(type=typ, len=snap(self.lseg - 0.12), w=w, gr=False))
        ly = blk.ly
        m1 = [p.to_dtype(ly.dbu).bbox() for p in pya.Region(self.cell.begin_shapes_rec(ly.layer(*L['m1']))).each()]
        self._heads = sorted(m1, key=lambda b: b.bottom)            # bottom, top
        assert len(self._heads) == 2, m1
        self._poly = pya.Region(self.cell.begin_shapes_rec(ly.layer(*L['poly']))).bbox().to_dtype(ly.dbu)
        self._psdm = pya.Region(self.cell.begin_shapes_rec(ly.layer(94, 20))).bbox().to_dtype(ly.dbu)
        self._bbox = self.cell.dbbox()

    def place(self, x, y):
        """x, y: lower left of segment 0's poly."""
        blk = self.blk
        dx, dy = snap(x - self._poly.left), snap(y - self._poly.bottom)
        self.segs, heads = [], []
        for k in range(self.nseg):
            ox = snap(dx + k * self.pitch)
            blk.place(self.cell, ox, dy)
            v = pya.DVector(ox, dy)
            heads.append([h.moved(v) for h in self._heads])
            self.segs.append(self._bbox.moved(v))
        # widened head pads (met1), centred on each pcell head
        hw = self.pad_w / 2

        def pad(h):
            c = h.center().x
            return blk.rect('m1', box(c - hw, h.bottom, c + hw, h.top))
        self.heads = [[pad(h) for h in hh] for hh in heads]
        self.links = []
        for k in range(self.nseg - 1):
            side = 1 if k % 2 == 0 else 0           # 0-1 joined at the top, 1-2 at the bottom, ...
            a, b = self.heads[k][side], self.heads[k + 1][side]
            self.links.append(blk.rect('m1', box(a.left, a.bottom, b.right, a.top)))
        last_side = 0 if self.nseg % 2 == 0 else 1
        self.ends = (self.heads[0][0], self.heads[-1][last_side])
        self.bbox = self.segs[0] + self.segs[-1]
        self.psdm = (self._psdm.moved(pya.DVector(dx, dy)) +
                     self._psdm.moved(pya.DVector(dx + (self.nseg - 1) * self.pitch, dy)))
        self.poly = self._poly.moved(pya.DVector(dx, dy)) + self._poly.moved(pya.DVector(dx + (self.nseg - 1) * self.pitch, dy))
        return self


def mim(blk, capm, strip=None):
    """cap_mim_m3_1 on capm box: draws capm and its met3 bottom plate (capm + CAPM_ENC_M3).
    strip (a box): where the met4 top-plate contact runs; via3 fill its overlap with
    capm (shrunk by the capm via3 enclosure). The caller draws the met4 strip itself
    (it usually continues to a drop point). Returns the bottom plate box."""
    blk.rect(CAPM, capm)
    e = CAPM_ENC_M3
    bot = blk.rect('m3', box(capm.left - e, capm.bottom - e, capm.right + e, capm.top + e))
    if strip is not None:
        ov = strip & capm
        blk.via('via3', ov, enc=(CAPM_ENC_V3, CAPM_ENC_V3))
    return bot
