# log_det layout: 6 det_cells summing into 'det' (xschem/gen/logdet.py:log_det).
#   vb replica: Mbias (nfet wd / 0.15, diode, ibias_det) + Rs_b (as the cells' Rs) to VSS;
#   Rdet (high_po 0.69, det -> VDD) and Cdet (MIM, top plate det, bottom plate VDD).
#
# Two rows of three det_cells (layout/gen/det_cell.py, unchanged) and an end column:
#   top row    t1 t2 t3   det_cell as drawn (rail at its bottom)  | Cdet (22x22, bottom
#   ---- one VSS rail (met1-3), shared ----                       | plate VDD) over the
#   bottom row t4 t5 t6   mirrored in y (rail at its top)         | column; the end
#                                                                 | section under it
# The inputs (each cell's Cc bottom-plate pins, met3) face out: the top row's along the top
# edge, the bottom row's along the bottom. t1 and t6 sit on opposite corners. The out / vb
# buses (met2) of both rows run into the end column and are joined there: out by a met2
# riser, which carries on down to Rdet and the Cdet drop, and vb by a met1 riser (it crosses
# the out buses). End section (own p-tap ring, bridged to t6's ring): Mbias (diode; drain
# up to the bottom vb bus in met2), Rs_b drawn exactly like the cells' Rs (high_po 0.35,
# 2 segments) so the vb replica matches them, Rdet (0.69, 3 segments, one RPM). Cdet's top
# plate drops on a met4 strip to a met3 island 1.2 um below the bottom plate. The bottom
# plate's met3 runs on as a strip at the right edge: the VDD pin (via3 from the top level
# outside capm), which Rdet's top end reaches in met2.
# Run: tools/osic klayout -b -r layout/gen/log_det.py   (writes layout/log_det.gds + ref)
import math
import os
import re
import sys
import pya
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, box, snap, ring, write_ref, LBL, PIN, REPO   # noqa: E402
from passives import PolyRes, mim, CAPM_ENC_M3, BOT_PLATE_SPACE      # noqa: E402
import det_cell as dcm                                                 # noqa: E402

PARAMS = dict(dcm.PARAMS, rdet=8e3, cdet=1e-12)                        # radio_analog's xdet
NCOL = 3                                                               # cells per row (2 rows)
RPM = (86, 20)
GRW = dcm.GRW
VDDW = 1.2                                                             # VDD strip (met3) width


def make():
    b = Block('log_det')
    src = dcm.make()                                                   # det_cell in its own layout
    cell = b.ly.create_cell('det_cell')
    cell.copy_tree(src.cell)
    bb = cell.dbbox()
    W, H = snap(bb.right), snap(bb.top)                                # pitch and height (rail at y 0..RAIL_H)
    RH = dcm.RAIL_H
    yt = snap(H - RH)                                                  # top row origin: its rail on the bottom row's
    ytop = snap(yt + H)
    y_in = RH + GRW
    cbus = {'out': (y_in + 0.3, y_in + 0.7), 'vb': (y_in + 1.0, y_in + 1.4)}   # det_cell's buses

    def up(y0, y1):                                                    # cell y range -> top row
        return (snap(yt + y0), snap(yt + y1))

    def dn(y0, y1):                                                    # cell y range -> bottom row (mirrored)
        return (snap(H - y1), snap(H - y0))
    bus = {(n, r): f(*cbus[n]) for n in cbus for r, f in (('t', up), ('b', dn))}

    # cells: top row t1..t3 as drawn, bottom row t4..t6 mirrored about the shared rail
    for k in range(NCOL):
        b.place(cell, k * W, yt)
        b.cell.insert(pya.DCellInstArray(cell.cell_index(), pya.DTrans(pya.DTrans.M0, pya.DVector(k * W, H))))
    x0 = NCOL * W                                                      # end column's left edge

    # ring implants (psdm) of neighbouring cells end 0.2 um apart (a psdm.1 sliver in
    # KLayout): bridge them in both rows (p+ taps either side)
    psdm = pya.Region(src.cell.begin_shapes_rec(src.ly.find_layer(94, 20))).bbox().to_dtype(src.ly.dbu)
    for k in range(1, NCOL):
        xb = k * W
        for f in (up, dn):
            b.rect('psdm', box(xb - (W - psdm.right) - 0.1, f(psdm.bottom, psdm.top)[0],
                               xb + psdm.left + 0.1, f(psdm.bottom, psdm.top)[1]))

    # inputs: the cell's met3 pins (inp, inn) per tap
    pins = {}
    li_t = src.ly.find_layer(*LBL['m3'])
    li_p = src.ly.find_layer(*PIN['m3'])
    for t in src.cell.shapes(li_t).each():
        if t.is_text() and t.text_string in ('inp', 'inn'):
            p = pya.DPoint(t.dtext.x, t.dtext.y)
            for s in src.cell.shapes(li_p).each():
                if s.dbbox().contains(p):
                    pins[t.text_string] = s.dbbox()
    for k in range(NCOL):
        for nm, sfx in (('inp', 'p'), ('inn', 'n')):
            pb = pins[nm]
            b.pin('m3', box(k * W + pb.left, yt + pb.bottom, k * W + pb.right, yt + pb.top), f't{k + 1}{sfx}')
            b.pin('m3', box(k * W + pb.left, H - pb.top, k * W + pb.right, H - pb.bottom), f't{k + NCOL + 1}{sfx}')

    # --- end section (bottom of the end column): own ring, devices in a row
    rs_l = (PARAMS['rs'] - 963) / 995                                  # as the cells' Rs
    rd_l = (PARAMS['rdet'] - 526) / 470.9
    rsb = PolyRes(b, rs_l, 2, typ='sky130_fd_pr__res_high_po_0p35')
    rdt = PolyRes(b, rd_l, 3, w=0.69, typ='sky130_fd_pr__res_high_po_0p69', pitch=1.5, pad_w=0.6)
    xin = x0 + 0.1 + GRW                                               # ring hole left edge (0.2 from t6's ring)
    yh = snap(GRW + 0.13)                                              # ring hole bottom (its psdm from y 0)
    y_dev = yh + 0.6
    f = Fet(b, 'n', PARAMS['wd'], 0.15, gate='top', vt='', bulk='None')
    f.place(xin + 0.8, y_dev + 0.2)
    f.commit()
    rsb.place(f.diff.right + 1.2 - (rsb._bbox.left - rsb._poly.left), y_dev - rsb._bbox.bottom + rsb._poly.bottom)
    rdt.place(rsb.bbox.right + 1.0 - (rdt._bbox.left - rdt._poly.left), y_dev - rdt._bbox.bottom + rdt._poly.bottom)
    b.rect(RPM, rdt.bbox)                     # one RPM over the 0.69 array (per-segment RPMs leave gaps: rpm.2)
    top = max(rsb.bbox.top, rdt.bbox.top, f.pads[0].top + 0.5)
    inner = box(xin, yh, rdt.bbox.right + 0.6, top + 0.6)
    re_ = ring(b, inner, 'p', GRW)
    assert re_.top < bus['vb', 'b'][0] - 1.0, (re_, bus)
    # VSS: the ring onto t6's ring (met1 across the 0.2 um gap), psdm bridged likewise
    b.rect('m1', box(x0 - 0.3, re_.bottom + 0.5, x0 + 0.3, re_.top - 0.5))
    pe = pya.Region(b.cell.begin_shapes_rec(b.li((94, 20)))) & pya.Region(box(x0, 0, re_.right + 1, re_.top + 1).to_itype(b.ly.dbu))
    pe = pe.bbox().to_dtype(b.ly.dbu)
    pd = dn(psdm.bottom, psdm.top)
    b.rect('psdm', box(x0 - (W - psdm.right) - 0.1, max(pe.bottom, pd[0]), pe.left + 0.1, min(pe.top, pd[1])))

    d, s = f.strips                       # drain left (gate tie, vb), source right (Rs_b)
    g = f.pads[0]
    # diode: gate pad extended left over the drain; drain up to it; met2 from there up to the vb bus
    gpad = box(d.left - 0.03, g.bottom, g.right, max(g.top, g.bottom + 0.32))
    b.rect('m1', gpad)
    b.rect('m1', box(d.left - 0.03, d.bottom, d.right + 0.03, gpad.top))
    dv = box(d.left - 0.03, gpad.bottom, d.right + 0.03, gpad.top)
    b.via('via1', dv, enc=(0.07, 0.085))
    b.rect('m2', box(dv.left, dv.bottom, dv.right, bus['vb', 'b'][1]))
    # source -> Rs_b's first end (both ends at the bottom: 2 segments); second end -> the ring (VSS)
    h1, h2 = rsb.ends
    yl = s.center().y
    b.rect('m1', box(s.left, yl - 0.2, h1.right, yl + 0.2))
    b.rect('m1', box(h1.left, h1.bottom, h1.right, yl + 0.2))
    b.rect('m1', box(h2.left, yh - 0.01, h2.right, h2.top))

    # --- bus joins. vb: buses on to a met1 riser (crosses the out buses); out (det): buses on
    # to a met2 riser over Rdet's bottom end, which runs down to it
    hb, ht = rdt.ends
    xv = snap(max(dv.right + 0.6, x0 + 1.2))
    for r in 'tb':
        b.rect('m2', box(x0, bus['vb', r][0], xv + 0.5, bus['vb', r][1]))
        b.rect('m2', box(x0, bus['out', r][0], hb.right, bus['out', r][1]))
        b.via('via1', box(xv, bus['vb', r][0], xv + 0.5, bus['vb', r][1]), enc=(0.085, 0.085))
    assert xv + 0.5 + 0.3 < hb.left, (xv, hb)
    b.rect('m1', box(xv, bus['vb', 'b'][0], xv + 0.5, bus['vb', 't'][1]))
    b.label('m1', box(xv, bus['vb', 'b'][0], xv + 0.5, bus['vb', 't'][1]), 'ibias_det')
    b.via('via1', box(hb.left, hb.bottom, hb.right, hb.bottom + 0.6), enc=(0.12, 0.085))
    b.rect('m2', box(hb.left, hb.bottom, hb.right, bus['out', 't'][1]))
    b.label('m2', box(hb.left, bus['out', 'b'][1], hb.right, bus['out', 't'][0]), 'det')

    # --- Cdet over the column, top-aligned with the block; bottom plate 1.2 um clear of the
    # cells' met3 (their rail ends at x0)
    e = CAPM_ENC_M3
    cw = snap(math.sqrt(PARAMS['cdet'] / 2.06e-15))
    cap = box(x0 + BOT_PLATE_SPACE + e, ytop - e - cw, x0 + BOT_PLATE_SPACE + e + cw, ytop - e)
    xc = hb.center().x
    assert cap.left + 0.6 < xc - 0.5, (cap, xc)
    yi = snap(cap.bottom - e - BOT_PLATE_SPACE)                        # island top: 1.2 below the plate
    plate = mim(b, cap, box(xc - 0.5, cap.bottom + 0.2, xc + 0.5, cap.top - 0.2))
    island = box(xc - 0.5, yi - 1.0, xc + 0.5, yi)
    b.rect('m4', box(xc - 0.5, island.bottom, xc + 0.5, cap.top - 0.2))
    b.stack(island, 'm2', 'm4')
    # VDD: the bottom plate's met3 on as a strip down the right edge; Rdet's top end to it in met2
    strip = box(plate.right, 0, plate.right + VDDW, ytop)
    b.rect('m3', strip)
    b.via('via1', box(ht.left, ht.top - 0.4, ht.right, ht.top), enc=(0.12, 0.085))
    yv = (ht.top - 0.4, ht.top)
    b.rect('m2', box(ht.left, yv[0], strip.right, yv[1]))
    b.via('via2', box(strip.left, yv[0], strip.right, yv[1]), enc=(0.085, 0.065))
    b.pin('m3', strip, 'VDD')

    # pins (det / ibias_det on the top row's buses at the left edge, VSS on the shared rail)
    b.pin('m2', box(0, bus['out', 't'][0], 0.5, bus['out', 't'][1]), 'det')
    b.pin('m2', box(0, bus['vb', 't'][0], 0.5, bus['vb', 't'][1]), 'ibias_det')
    b.pin('m3', box(0, yt, 1.0, H), 'VSS')
    bbox = b.cell.dbbox()
    print(f'log_det: 2 x {NCOL} cells ({W} x {H}), end column {x0:.2f}..{strip.right:.2f}, '
          f'Cdet {cw}^2; block {bbox.width():.2f} x {bbox.height():.2f} um')
    return b


if __name__ == '__main__':
    make().write(os.path.join(REPO, 'layout', 'log_det.gds'))
    write_ref('log_det', 'log_det', PARAMS)
    # det_cell instances: drop their parameters (already substituted inside the subckt);
    # netgen compares instance properties against the layout's parameterless instances
    ref = os.path.join(REPO, 'layout', 'ref', 'log_det.spice')
    txt = re.sub(r'(?m)^(x\w+ .* det_cell)(\s+\w+=\S+)+$', r'\1', open(ref).read())
    open(ref, 'w').write(txt)
