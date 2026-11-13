# chain_in_t: the input section of the tall straight chain (docs/tall_stages_2026-11.md),
# drawn in the stages' frame (63.5 um tall) to abut amp_dp_t's left edge. Same devices as
# today's lna_chain input (layout/gen/lna_chain.py; xschem/gen/chain.py):
#   Cin_p / Cin_n  2 pF MIMs (top plate g1p / g1n, bottom plate on the pad side), tall rectangles
#                  with today's C (the model's (w + 0.15)(l + 0.15) kept)
#   Rb_p / Rb_n    20k high_po_0p35 (one segment each, L 19.13 um, side by side so the rpm merges)
#                  from vcm to g1p / g1n
#   Mref           nfet W 6 nf 2 / L 0.5, the reference diode (ibias = every stage's nb)
# Left to right: Cin_p | Cin_n (side by side, so each pad reaches its own cap from the bottom
# edge, as today) | a zone with Rb pair + Mref in a p-tap ring | (amp_dp_t).
#   g1n: Cin_n's top plate on a met4 strip straight right at amp_dp_t's inn height, a met3
#        landing 1.2 um clear of the plate, met2 into amp_dp_t's inn pin.
#   g1p: Cin_p's top plate up on met4 above both plates (clear of Cin_n's), right into the zone,
#        down a met4 column to amp_dp_t's inp height, the same way in.
#   Rb_p's top head -> g1p, Rb_n's bottom head -> g1n (each next to its own input line); the other
#        heads (vcm) are joined on met3 and go to a met4 column to the bottom edge (pin vcm).
#   Mref above the VSS line (sources down into it, as the stages' tails), drain + gate -> nb on
#        met2 at amp_dp_t's nb height (pin ibias at the bottom edge on met4).
#   VSS: amp_dp_t's centre rail continues on met1 to the ring. Pads: met3 tabs on each plate's
#        bottom edge (pins inp / inn).
# Run: tools/osic klayout -b -r layout/gen/chain_in_tall.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pya   # noqa: E402
from lay import Block, Fet, REPO, box, ring, snap, L   # noqa: E402
from passives import PolyRes, CAPM, CAPM_ENC_V3, BOT_PLATE_SPACE   # noqa: E402
from chain_strip_tall import pins   # noqa: E402

CINW = snap((2e-12 / 2.06e-15) ** 0.5)            # today's square side, 31.16 um
AREA = (CINW + 0.15) ** 2
LRB = (20e3 - 963) / 995
GRW = 0.4
RPM = (86, 20)


def make():
    ly = pya.Layout()
    ly.read(os.path.join(REPO, 'layout', 'amp_dp_t.gds'))
    dp = ly.cell('amp_dp_t')
    H = dp.dbbox().height()
    p = pins(dp, ly)
    y_inp, y_inn, y_nb = p['inp'][0][1], p['inn'][0][1], p['nb'][0][1]
    y_vss = p['VSS'][0][1]
    b = Block('chain_in_t')
    # caps: capm 0.5 .. 61.5 um tall, plates 0.2 round; Cin_p left, Cin_n right, 1.2 apart
    cy0, cy1 = 0.5, 61.5
    cl = cy1 - cy0
    cw = snap(AREA / (cl + 0.15) - 0.15)
    x0 = 0.5
    caps = {}
    for s in ('p', 'n'):
        caps[s] = b.rect(CAPM, box(x0 + 0.2, cy0, x0 + 0.2 + cw, cy1))
        pl = b.rect('m3', box(x0, cy0 - 0.2, x0 + cw + 0.4, cy1 + 0.2))
        xc = pl.center().x                            # pad tab on the bottom edge
        tab = b.rect('m3', box(xc - 1.0, 0, xc + 1.0, pl.bottom + 0.01))
        b.pin('m3', box(tab.left, 0, tab.right, 0.4), 'inp' if s == 'p' else 'inn')
        x0 = pl.right + BOT_PLATE_SPACE
    xz = caps['n'].right + 0.2                       # Cin_n's plate right edge
    # zone: landings 1.2 clear of the plate
    col = box(xz + 1.25, 0, xz + 1.65, 0)            # g1p column / both landings
    # Rb pair + Mref in a p-tap ring
    rbs = [PolyRes(b, LRB, 1, typ='sky130_fd_pr__res_high_po_0p35') for _ in range(2)]
    mref = Fet(b, 'n', 6.0, 0.5, nf=2, gate='top', vt='', bulk='None')
    xin = xz + 2.4                                   # ring hole left
    yc = (y_vss.bottom + y_vss.top) / 2
    r0 = rbs[0]
    rh = r0._bbox.height()
    xr = xin + 0.6
    for k, r in enumerate(rbs):                      # centred on the centre line
        r.place(xr + k * r.pitch - (r._bbox.left - r._poly.left), yc - rh / 2 - r._bbox.bottom + r._poly.bottom)
    # rpm over the pair (they merge, as today), wide enough
    mref.place(rbs[-1].bbox.right + 1.6, y_vss.top + 0.5).commit()
    inner = box(xin, min(r.bbox.bottom for r in rbs) - 0.6, mref.diff.right + 0.6,
                max(max(r.bbox.top for r in rbs) + 0.6, mref.diff.top + 1.4))
    ring(b, inner, 'p', GRW)
    Win = snap(inner.right + GRW + 0.4)               # ring psdm 0.45 from amp_dp_t's (psdm.2 0.38)
    # VSS: met1 from the right edge (amp_dp_t's rail) to the ring; Mref's sources down into it
    b.rect('m1', box(mref.strips[0].center().x - 0.15, y_vss.bottom, Win, y_vss.top))
    s0, sd, s2 = mref.strips
    for s in (s0, s2):
        b.rect('m1', box(s.center().x - 0.15, y_vss.top - 0.01, s.center().x + 0.15, s.top))
    b.pin('m1', box(Win - 0.5, y_vss.bottom, Win, y_vss.top), 'VSS')
    # Mref: gate strap + drain -> nb (met2 at amp_dp_t's nb height, under the VSS met1)
    gy0 = min(q.bottom for q in mref.pads)
    gy1 = max(max(q.top for q in mref.pads), gy0 + 0.32)
    b.rect('m1', box(mref.pads[0].left, gy0, mref.pads[-1].right, gy1))
    dx = sd.center().x
    dv = b.rect('m1', box(dx - 0.15, mref.diff.top - 1.0, dx + 0.15, mref.diff.top - 0.2))
    b.via('via1', dv, enc=(0.075, 0.085))
    gv = box(mref.pads[-1].right - 0.5, gy0, mref.pads[-1].right, gy1)
    b.via('via1', gv, enc=(0.085, 0.085))
    b.rect('m2', box(dv.left, y_nb.bottom, dv.right, dv.top))
    b.rect('m2', box(gv.left, y_nb.bottom, gv.right, gv.top))
    b.rect('m2', box(dv.left, y_nb.bottom, Win, y_nb.top))
    b.pin('m2', box(Win - 0.5, y_nb.bottom, Win, y_nb.top), 'ibias')
    # ibias also to the bottom edge: met4 column right of the ring's left part, over Mref's side
    xi = mref.diff.right - 0.2
    ci = box(xi - 0.2, 0, xi + 0.2, 0)
    isl = b.rect('m3', box(ci.left - 0.05, y_nb.center().y - 0.3, ci.right + 0.05, y_nb.center().y + 0.3))
    b.rect('m2', box(isl.left, y_nb.bottom, isl.right, y_nb.top))
    b.via('via2', box(isl.left, y_nb.bottom, isl.right, y_nb.top), enc=(0.065, 0.085))
    b.via('via3', isl, enc=(0.09, 0.09))
    b.rect('m4', box(ci.left, 0, ci.right, isl.top))
    b.pin('m4', box(ci.left, 0, ci.right, 0.5), 'ibias')
    # Rb heads: Rb_p top -> g1p, Rb_n bottom -> g1n; Rb_p bottom + Rb_n top = vcm (met3 between)
    (bp, tp), (bn, tn) = rbs[0].heads[0], rbs[1].heads[0]

    def hv(hd, top):
        xc = hd.center().x
        v = (box(xc - 0.15, hd.top - 0.45, xc + 0.15, hd.top - 0.05) if top
             else box(xc - 0.15, hd.bottom + 0.05, xc + 0.15, hd.bottom + 0.45))
        b.via('via1', v, enc=(0.075, 0.085))
        return v
    vp, vn = hv(tp, True), hv(bn, False)
    for v, y in ((vp, y_inp), (vn, y_inn)):
        b.rect('m2', box(v.left, min(v.bottom, y.bottom), v.right, max(v.top, y.top)))
        b.rect('m2', box(col.left - 0.05, y.bottom, Win, y.top))          # the input line into amp_dp_t
    b.pin('m2', box(Win - 0.5, y_inp.bottom, Win, y_inp.top), 'g1p')
    b.pin('m2', box(Win - 0.5, y_inn.bottom, Win, y_inn.top), 'g1n')
    # vcm: Rb_p's bottom head jogs left (xv1), Rb_n's top head right (xv2), each to a met3
    # riser; the two meet on met3 across the centre (over the pair, the VSS met1 and nb met2)
    va, vb_ = hv(bp, False), hv(tn, True)
    xv1 = rbs[0].bbox.left - 0.5
    xv2 = rbs[1].bbox.right + 0.45
    assert xv2 + 0.25 + 0.3 <= mref.diff.left, (xv2, mref.diff.left)
    for v, xv in ((va, xv1), (vb_, xv2)):
        b.rect('m2', box(min(xv - 0.25, v.left), v.bottom - 0.05, max(xv + 0.25, v.right), v.top + 0.05))
        b.via('via2', box(xv - 0.25, v.bottom - 0.05, xv + 0.25, v.top + 0.05), enc=(0.065, 0.065))
    b.rect('m3', box(xv1 - 0.25, va.bottom - 0.1, xv1 + 0.25, yc + 0.25))
    b.rect('m3', box(xv1 - 0.25, yc - 0.25, xv2 + 0.25, yc + 0.25))
    b.rect('m3', box(xv2 - 0.25, yc - 0.25, xv2 + 0.25, vb_.top + 0.1))
    assert xv1 - 0.25 >= xz + BOT_PLATE_SPACE, (xv1, xz)
    # vcm to the bottom edge: via3 at the left riser's bottom end, met4 column down
    vb3 = box(xv1 - 0.25, va.bottom - 0.1, xv1 + 0.25, va.bottom + 0.5)
    b.via('via3', vb3, enc=(0.09, 0.09))
    b.rect('m4', box(xv1 - 0.25, 0, xv1 + 0.25, vb3.top))
    b.pin('m4', box(xv1 - 0.25, 0, xv1 + 0.25, 0.5), 'vcm')
    # top plates: Cin_n on a met4 strip right at the inn height; Cin_p up and over, down the column
    for s, y in (('n', y_inn), ('p', y_inp)):
        yl = y.center().y
        isl = b.rect('m3', box(col.left - 0.05, yl - 0.3, col.right + 0.05, yl + 0.3))
        b.via('via2', box(isl.left, y.bottom, isl.right, y.top), enc=(0.065, 0.085))
        b.via('via3', isl, enc=(0.09, 0.09))
        c = caps[s]
        if s == 'n':
            st = b.rect('m4', box(c.right - 4.0, yl - 0.6, col.right, yl + 0.6))
            b.via('via3', st & c, enc=(CAPM_ENC_V3, CAPM_ENC_V3))
        else:
            yt = (cy1 + 0.2 + 0.6, cy1 + 0.2 + 1.4)   # above both plates
            st = b.rect('m4', box(c.right - 4.0, c.top - 3.0, c.right - 0.5, yt[1]))
            b.via('via3', st & c, enc=(CAPM_ENC_V3, CAPM_ENC_V3))
            b.rect('m4', box(c.right - 4.0, yt[0], col.right, yt[1]))
            b.rect('m4', box(col.left, isl.bottom, col.right, yt[1]))
    assert yt[1] <= H - 0.3
    print(f'chain_in_t: {Win:.2f} x {H:.2f} um; Cin {cw} x {cl} um each (was {CINW} square)')
    return b, dict(W=Win, H=H, cinw=cw, cinl=cl)


def write_ref(meta):
    w, l = meta['cinw'], meta['cinl']
    lines = ['* chain_in_t: the input section of xschem/lna_chain.sch (Cin, Rb, Mref; values as layout/ref/lna_chain.spice),',
             f'* Cin drawn {w:g} x {l:g} um (chain_in_tall.py)',
             '.subckt chain_in_t inp inn ibias vcm g1p g1n VSS',
             'XMref ibias ibias VSS VSS sky130_fd_pr__nfet_01v8 L=0.5 W=6 nf=2',
             f'XCin_p g1p inp sky130_fd_pr__cap_mim_m3_1 W={w:g} L={l:g}',
             f'XRb_p g1p vcm VSS sky130_fd_pr__res_high_po_0p35 L={LRB:.6g} mult=1',
             f'XCin_n g1n inn sky130_fd_pr__cap_mim_m3_1 W={w:g} L={l:g}',
             f'XRb_n g1n vcm VSS sky130_fd_pr__res_high_po_0p35 L={LRB:.6g} mult=1',
             '.ends']
    open(os.path.join(REPO, 'layout', 'ref', 'chain_in_t.spice'), 'w').write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    b, meta = make()
    b.write(os.path.join(REPO, 'layout', 'chain_in_t.gds'))
    write_ref(meta)
