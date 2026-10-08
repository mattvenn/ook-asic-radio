# log_det layout: 6 det_cells summing into 'det' (xschem/gen/logdet.py:log_det).
#   vb replica: Mbias (nfet wd / 0.15, diode, ibias_det) + Rs_b (as the cells' Rs) to VSS;
#   Rdet (high_po 0.69, det -> VDD) and Cdet (MIM, top plate det, bottom plate VDD).
#
# One row: det_cell x6 at its pitch W (layout/gen/det_cell.py: VSS rail at the bottom,
# out / vb buses pinned on both edges, so cells abut; one cell per chain tap, so the row
# can sit under the chain later), then an end section in the same frame (rail, buses, its
# own p-tap ring): Mbias, Rs_b, Rdet. Rs_b is drawn exactly like the cells' Rs (high_po
# 0.35, 2 segments) so the vb replica matches them. Cdet (22x22) sits above the end
# section: its bottom plate abuts a VDD rail (met1-3, the VDD pin); its top plate drops to
# the det (out) bus on a met4 riser over the end section. Inputs t<k>p / t<k>n: the cells'
# bottom-plate pins (met3).
# Run: tools/osic klayout -b -r layout/gen/log_det.py   (writes layout/log_det.gds + ref)
import math
import os
import re
import sys
import pya
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, box, snap, ring, write_ref, LBL, PIN, REPO   # noqa: E402
from passives import PolyRes, mim, CAPM_ENC_M3                        # noqa: E402
import det_cell as dcm                                                 # noqa: E402

PARAMS = dict(dcm.PARAMS, rdet=8e3, cdet=1e-12)                        # radio_analog's xdet
NTAPS = 6
RPM = (86, 20)
GRW = dcm.GRW


def make():
    b = Block('log_det')
    src = dcm.make()                                                   # det_cell in its own layout
    cell = b.ly.create_cell('det_cell')
    cell.copy_tree(src.cell)
    bb = cell.dbbox()
    W = snap(bb.right)                                                 # the cell's pitch (x 0 .. W)
    y_in = dcm.RAIL_H + GRW
    out = (y_in + 0.3, y_in + 0.7)                                     # as det_cell's buses
    vb = (y_in + 1.0, y_in + 1.4)
    for k in range(NTAPS):
        b.place(cell, k * W, 0)
    # neighbouring cells' ring implants (psdm) end 0.2 um apart at each boundary (a psdm.1
    # sliver in KLayout): bridge them (p+ taps either side). The cell's ring psdm extent:
    psdm = pya.Region(src.cell.begin_shapes_rec(src.ly.find_layer(94, 20))).bbox().to_dtype(src.ly.dbu)
    for k in range(1, NTAPS + 1):
        xb = k * W
        b.rect('psdm', box(xb - (W - psdm.right) - 0.1, psdm.bottom, xb + psdm.left + 0.1 if k < NTAPS
                           else xb + 0.6 + GRW + 0.2, psdm.top))
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
    for k in range(NTAPS):
        for nm, sfx in (('inp', 'p'), ('inn', 'n')):
            b.pin('m3', pins[nm].moved(pya.DVector(k * W, 0)), f't{k + 1}{sfx}')

    # --- end section, same frame: rail 0..RAIL_H, ring hole from y_in, buses through
    x0 = NTAPS * W
    rs_l = (PARAMS['rs'] - 963) / 995                                  # as the cells' Rs
    rd_l = (PARAMS['rdet'] - 526) / 470.9
    rsb = PolyRes(b, rs_l, 2, typ='sky130_fd_pr__res_high_po_0p35')
    rdt = PolyRes(b, rd_l, 3, w=0.69, typ='sky130_fd_pr__res_high_po_0p69', pitch=1.5, pad_w=0.6)
    y_dev = vb[1] + 0.6
    xin = x0 + 0.6 + GRW                                               # ring hole left edge
    f = Fet(b, 'n', PARAMS['wd'], 0.15, gate='top', vt='', bulk='None')
    f.place(xin + 0.8, y_dev + 0.2)
    f.commit()
    rsb.place(f.diff.right + 1.2 - (rsb._bbox.left - rsb._poly.left), y_dev - rsb._bbox.bottom + rsb._poly.bottom)
    rdt.place(rsb.bbox.right + 1.0 - (rdt._bbox.left - rdt._poly.left), y_dev - rdt._bbox.bottom + rdt._poly.bottom)
    b.rect(RPM, rdt.bbox)                     # one RPM over the 0.69 array (per-segment RPMs leave gaps: rpm.2)
    top = max(rsb.bbox.top, rdt.bbox.top, f.pads[0].top + 0.5)
    inner = box(xin, y_in, rdt.bbox.right + 0.6, top + 0.6)
    re_ = ring(b, inner, 'p', GRW)
    xe1 = snap(re_.right + 0.1)
    b.stack(box(x0, 0, xe1, dcm.RAIL_H), 'm1', 'm3')                    # VSS rail on
    b.rect('m1', box(re_.left, dcm.RAIL_H - 0.01, re_.right, y_in))     # ring onto the rail
    for y0, y1 in (out, vb):
        b.rect('m2', box(x0, y0, xe1, y1))
    d, s = f.strips                       # drain left (gate tie, vb), source right (Rs_b)
    g = f.pads[0]
    # diode: drain up to the gate pad's level, pad extended left to meet it
    gpad = box(d.left - 0.03, g.bottom, g.right, max(g.top, g.bottom + 0.32))
    b.rect('m1', gpad)
    b.rect('m1', box(d.left - 0.03, vb[0], d.right + 0.03, gpad.top))   # and down to the vb bus
    b.via('via1', box(d.left - 0.03, vb[0], d.right + 0.03, vb[1]), enc=(0.07, 0.085))
    # source -> Rs_b's first end (both ends at the bottom: 2 segments); second end -> VSS
    h1, h2 = rsb.ends
    yl = s.center().y
    b.rect('m1', box(s.left, yl - 0.2, h1.right, yl + 0.2))
    b.rect('m1', box(h1.left, h1.bottom, h1.right, yl + 0.2))
    b.rect('m1', box(h2.left, dcm.RAIL_H - 0.01, h2.right, h2.top))     # crosses the buses in met1
    # Rdet: bottom end (segment 0) down to the out (det) bus; top end (segment 2) up to VDD
    hb, ht = rdt.ends
    b.rect('m1', box(hb.left, out[0], hb.right, hb.top))
    b.via('via1', box(hb.left, out[0], hb.right, out[1]), enc=(0.12, 0.085))
    yv = re_.top + 0.6
    rail = box(x0, yv, xe1, yv + 1.5)
    b.stack(rail, 'm1', 'm3')
    b.pin('m3', rail, 'VDD')
    b.via('via1', box(ht.left, ht.top - 0.4, ht.right, ht.top), enc=(0.12, 0.085))
    b.rect('m2', box(ht.left, ht.top - 0.4, ht.right, yv + 0.5))         # met2: crosses the ring's met1
    # Cdet above, bottom plate on the VDD rail; riser over the end section to the det bus
    e = CAPM_ENC_M3
    cw = snap(math.sqrt(PARAMS['cdet'] / 2.06e-15))
    cap = box(rail.right - e - cw, rail.top + e, rail.right - e, rail.top + e + cw)
    xr = cap.right - 1.0
    assert xr - 0.5 > re_.left + 0.5, 'Cdet riser must drop through the end section'
    mim(b, cap, box(xr - 0.5, cap.bottom + 0.2, xr + 0.5, cap.top - 0.2))
    b.rect('m4', box(xr - 0.5, out[0], xr + 0.5, cap.top - 0.2))
    b.stack(box(xr - 0.5, out[0], xr + 0.5, out[1]), 'm2', 'm4')
    # pins
    b.pin('m2', box(0, out[0], 0.5, out[1]), 'det')
    b.pin('m2', box(0, vb[0], 0.5, vb[1]), 'ibias_det')
    b.pin('m3', box(0, 0, 1.0, dcm.RAIL_H), 'VSS')
    print(f'log_det: {NTAPS} cells at pitch {W}, end section to {xe1:.2f}, Cdet {cw}^2')
    return b


if __name__ == '__main__':
    make().write(os.path.join(REPO, 'layout', 'log_det.gds'))
    write_ref('log_det', 'log_det', PARAMS)
    # det_cell instances: drop their parameters (already substituted inside the subckt);
    # netgen compares instance properties against the layout's parameterless instances
    ref = os.path.join(REPO, 'layout', 'ref', 'log_det.spice')
    txt = re.sub(r'(?m)^(x\w+ .* det_cell)(\s+\w+=\S+)+$', r'\1', open(ref).read())
    open(ref, 'w').write(txt)
