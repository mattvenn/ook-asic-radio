# log_det_t: log_det unwrapped into one row, to run along the tall chain's north edge
# (docs/tall_stages_2026-11.md, "Floorplan page"). Same circuit as log_det without Cdet, which
# is its own cell (cdet_t, below) placed where the floorplan has room.
#
#   | end section | t1 | t2 | t3 | t4 | t5 | t6 |     six det_cells (layout/det_cell.gds,
#   ---- VSS rail (met1-3) along the bottom ----        unchanged), abutted: their out / vb
#                                                       buses (met2) join through the edges
# Placed MY in the tile, t6 sits at the west end over stages 5-6 and the end section at the
# east end. Every cell's inputs (inp / inn: the Cc bottom plates' met3 pins) are labelled
# t<k>p / t<k>n where the cell has them.
# End section (own p-tap ring on the rail, psdm bridged to t1's): Mbias (diode, ibias_det),
# Rs_b drawn as the cells' Rs (the vb replica), Rdet (high_po 0.69, 3 segments, det -> VDD).
# The buses run on through it to the west edge: det (out bus) and ibias_det (vb bus) are pins
# there. Rdet's bottom end drops to the out bus in met1 (across the vb bus); its top end goes up
# to a met3 VDD pin on the north edge.
# Run: tools/osic klayout -b -r layout/gen/log_det_tall.py   (writes log_det_t / cdet_t gds + refs)
import math
import os
import re
import sys
import pya
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, box, snap, ring, write_ref, LBL, PIN, REPO   # noqa: E402
from passives import PolyRes, mim, CAPM_ENC_M3                          # noqa: E402
import det_cell as dcm                                                   # noqa: E402

PARAMS = dict(dcm.PARAMS, rdet=8e3, cdet=1e-12)                          # as log_det
N = 6
RPM = (86, 20)
GRW = dcm.GRW
RH = dcm.RAIL_H
VDDW = 1.0


def make():
    b = Block('log_det_t')
    src = dcm.make()
    cell = b.ly.create_cell('det_cell')
    cell.copy_tree(src.cell)
    bb = cell.dbbox()
    W, H = snap(bb.right), snap(bb.top)
    y_in = RH + GRW
    bus = {'out': (y_in + 0.3, y_in + 0.7), 'vb': (y_in + 1.0, y_in + 1.4)}   # det_cell's buses
    psdm = pya.Region(src.cell.begin_shapes_rec(src.ly.find_layer(94, 20))).bbox().to_dtype(src.ly.dbu)
    tap = pya.Region(src.cell.begin_shapes_rec(src.ly.find_layer(65, 44))).bbox().to_dtype(src.ly.dbu)

    # --- end section, from x = 0: Mbias | Rs_b | Rdet in a row on its own ring
    rs_l = (PARAMS['rs'] - 963) / 995
    rd_l = (PARAMS['rdet'] - 526) / 470.9
    rsb = PolyRes(b, rs_l, 2, typ='sky130_fd_pr__res_high_po_0p35')
    rdt = PolyRes(b, rd_l, 3, w=0.69, typ='sky130_fd_pr__res_high_po_0p69', pitch=1.5, pad_w=0.6)
    xin = 0.6 + GRW                                                    # ring hole left edge
    y_dev = bus['vb'][1] + 0.6
    f = Fet(b, 'n', PARAMS['wd'], 0.15, gate='top', vt='', bulk='None')
    f.place(xin + 0.8, y_dev + 0.2)
    f.commit()
    rsb.place(f.diff.right + 1.2 - (rsb._bbox.left - rsb._poly.left), y_dev - rsb._bbox.bottom + rsb._poly.bottom)
    rdt.place(rsb.bbox.right + 1.0 - (rdt._bbox.left - rdt._poly.left), y_dev - rdt._bbox.bottom + rdt._poly.bottom)
    b.rect(RPM, rdt.bbox)
    top = max(rsb.bbox.top, rdt.bbox.top, f.pads[0].top + 0.5)
    inner = box(xin, y_in, rdt.bbox.right + 0.6, top + 0.6)
    re_ = ring(b, inner, 'p', GRW)
    assert re_.top < H - 0.5, (re_, H)
    b.rect('m1', box(re_.left, RH - 0.01, re_.right, y_in))            # ring onto the rail

    # cells: t1 next to the end section, its ring abutting the end section's (both VSS; 0.2 apart is a tap.3 error)
    x0 = snap(re_.right - tap.left)
    for k in range(N):
        b.place(cell, x0 + k * W, 0)
    for k in range(N):                                                 # psdm slivers between rings
        xb = x0 + k * W
        left = (re_.right + (psdm.right - tap.right)) if k == 0 else xb - (W - psdm.right)
        b.rect('psdm', box(left - 0.1, psdm.bottom, xb + psdm.left + 0.1, psdm.top))
    b.stack(box(0, 0, x0, RH), 'm1', 'm3')                             # the rail on through the end section
    for net, (y0, y1) in bus.items():
        b.rect('m2', box(0, y0, x0, y1))

    # inputs: the cell's met3 pins (inp, inn), per tap
    pins = {}
    li_t, li_p = src.ly.find_layer(*LBL['m3']), src.ly.find_layer(*PIN['m3'])
    for t in src.cell.shapes(li_t).each():
        if t.is_text() and t.text_string in ('inp', 'inn'):
            p = pya.DPoint(t.dtext.x, t.dtext.y)
            for s in src.cell.shapes(li_p).each():
                if s.dbbox().contains(p):
                    pins[t.text_string] = s.dbbox()
    for k in range(N):
        for nm, sfx in (('inp', 'p'), ('inn', 'n')):
            pb = pins[nm]
            b.pin('m3', box(x0 + k * W + pb.left, pb.bottom, x0 + k * W + pb.right, pb.top), f't{k + 1}{sfx}')

    # Mbias: diode (gate pad over the drain, drain up to it, met2 down onto the vb bus)
    d, s = f.strips
    g = f.pads[0]
    gpad = box(d.left - 0.03, g.bottom, g.right, max(g.top, g.bottom + 0.32))
    b.rect('m1', gpad)
    b.rect('m1', box(d.left - 0.03, d.bottom, d.right + 0.03, gpad.top))
    dv = box(d.left - 0.03, gpad.bottom, d.right + 0.03, gpad.top)
    b.via('via1', dv, enc=(0.07, 0.085))
    b.rect('m2', box(dv.left, bus['vb'][0], dv.right, gpad.top))
    # source -> Rs_b's first end; its second end down to the ring (VSS), across the buses in met1
    h1, h2 = rsb.ends
    yl = s.center().y
    b.rect('m1', box(s.left, yl - 0.2, h1.right, yl + 0.2))
    b.rect('m1', box(h1.left, h1.bottom, h1.right, yl + 0.2))
    b.rect('m1', box(h2.left, y_in - 0.01, h2.right, h2.top))
    # Rdet: bottom end down to the out bus (met1 across vb, via1), top end up to the VDD pin
    hb, ht = rdt.ends
    b.rect('m1', box(hb.left, bus['out'][0], hb.right, hb.top))
    b.via('via1', box(hb.left, bus['out'][0], hb.right, bus['out'][1]), enc=(0.055, 0.085))
    b.via('via1', box(ht.left, ht.top - 0.4, ht.right, ht.top), enc=(0.12, 0.085))
    b.rect('m2', box(ht.left, ht.top - 0.4, ht.right, ht.top))
    b.via('via2', box(ht.left, ht.top - 0.4, ht.right, ht.top), enc=(0.085, 0.065))
    xv = ht.center().x
    vdd = box(xv - VDDW / 2, ht.top - 0.4, xv + VDDW / 2, H)
    b.rect('m3', vdd)
    b.pin('m3', box(vdd.left, H - 0.5, vdd.right, H), 'VDD')
    b.label('m2', box(0, bus['out'][0], 0.5, bus['out'][1]), 'det')
    b.pin('m2', box(0, bus['out'][0], 0.5, bus['out'][1]), 'det')
    b.pin('m2', box(0, bus['vb'][0], 0.5, bus['vb'][1]), 'ibias_det')
    b.pin('m3', box(0, 0, 1.0, RH), 'VSS')
    bbox = b.cell.dbbox()
    print(f'log_det_t: end section 0..{x0:.2f}, {N} cells of {W} x {H}; block {bbox.width():.2f} x {bbox.height():.2f} um '
          f'(bbox from {bbox.left:.2f}, {bbox.bottom:.2f})')
    return b


def make_cdet():
    """Cdet on its own: a square MIM (as log_det's), top plate det on a met4 pin over the plate,
    bottom plate VDD on a met3 pin at its edge."""
    b = Block('cdet_t')
    e = CAPM_ENC_M3
    cw = snap(math.sqrt(PARAMS['cdet'] / 2.06e-15))
    cap = box(e, e, e + cw, e + cw)
    strip = box(cap.left + 0.2, cap.bottom + 0.2, cap.left + 1.2, cap.top - 0.2)
    bot = mim(b, cap, strip)
    b.rect('m4', strip)
    b.pin('m4', box(strip.left, cap.center().y - 0.5, strip.right, cap.center().y + 0.5), 'det')
    b.pin('m3', box(bot.right - 1.0, bot.bottom, bot.right, bot.top), 'VDD')
    print(f'cdet_t: {bot.width():.2f} x {bot.height():.2f} um, W = L = {cw}')
    return b


if __name__ == '__main__':
    make().write(os.path.join(REPO, 'layout', 'log_det_t.gds'))
    write_ref('log_det_t', 'log_det', PARAMS, drop=r'XCdet$')
    ref = os.path.join(REPO, 'layout', 'ref', 'log_det_t.spice')
    txt = re.sub(r'(?m)^(x\w+ .* det_cell)(\s+\w+=\S+)+$', r'\1', open(ref).read())
    open(ref, 'w').write(txt)
    make_cdet().write(os.path.join(REPO, 'layout', 'cdet_t.gds'))
    cw = snap(math.sqrt(PARAMS['cdet'] / 2.06e-15))
    with open(os.path.join(REPO, 'layout', 'ref', 'cdet_t.spice'), 'w') as fh:
        fh.write(f'* cdet_t: log_det\'s Cdet on its own (layout/gen/log_det_tall.py)\n.subckt cdet_t det VDD\n'
                 f'XCdet det VDD sky130_fd_pr__cap_mim_m3_1 W={cw} L={cw}\n.ends\n')
