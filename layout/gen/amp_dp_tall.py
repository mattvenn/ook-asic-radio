# amp_dp_t: chain stage 1 as a tall, thin cell that abuts amp_dpc_t (layout/gen/amp_dpc_tall.py;
# docs/handoff_tall_stages.md). Same circuit, PARAMS and reference as amp_dp
# (layout/gen/amp_dp.py; xschem/gen/chain.py:amp_dp):
#   Mp / Mn  nfet W 80 L 0.15: D outn / outp, G inp / inn, S tail (16 x 5 um fingers each)
#   Mtail    nfet 20 x (W 6 nf 2) L 0.5: D tail, G nb, S VSS (2 x nf 20, 3 um fingers)
#   Rl_p / Rl_n res_high_po_1p41 L 3.14 um: VDD -> outn / outp
# 1.2 mA tail, 0.6 mA per side.
#
# The frame is amp_dpc_t's: VSS + nb on the centre line, VDD rails at the top and bottom edges,
# the same height, and the outputs on met2 at amp_dpc_t's input height, so its right edge lands
# on amp_dpc_t's left edge (outn on the top, outp on the bottom; the next stage is flipped).
# Each half (one half cell, placed twice, the second mirrored): ring; going out from the centre,
# a tail (nf 20: sources down into the ring and rail, drains to a met2 bar, nb strap over its
# gate pads, riser to the centre strip as in amp_dpc_t), then one pair row, its load to the
# right, VDD.
# Matching (stage 1 has DC gain): each pair row is four groups of 4 fingers, the outer two
# the half's own device and the inner two the other half's: top row A B B A, bottom row B A A B
# (A = Mp, B = Mn). Each device has half its fingers in each row, and its centroid is the cell
# centre in x and y. One orientation per row, sources all on the tail.
# The price is four crossings of the centre, all on met4 (no MIM here): each row's inner-group
# drains (other-out bar) to the other half's output, and its inner gate strap to the other
# half's input. The output crossings are full-height columns at the right edge (also the taps
# to log_det, as in amp_dpc_t, with a VDD shield column between them); the input crossings are
# two columns left of the pair rows. The two halves' tail nodes join on a short met4 column.
# Run: tools/osic klayout -b -r layout/gen/amp_dp_tall.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pya   # noqa: E402
from lay import Block, Fet, REPO, box, ring, snap, write_ref, cuts_needed   # noqa: E402
from passives import PolyRes   # noqa: E402
import amp_dpc_tall as dpc   # noqa: E402

PARAMS = dict(w=80, l=0.15, rl=1e3, wt=6, mt=20, mm=0)
LRL = (PARAMS['rl'] - 278) / 230.3
NG, NFG = 4, 4                     # per row: 4 groups of 4 fingers
WF = PARAMS['w'] / 16              # 5 um fingers
RC, RV, GRW, VW, TRK = dpc.RC, dpc.RV, dpc.GRW, dpc.VW, dpc.TRK


def half(b, frame):
    h = Block(b.name + '_half', ly=b.ly)
    nt = PARAMS['mt']                                  # tail fingers per half
    tail = Fet(h, 'n', 3.0 * nt, 0.5, nf=nt, gate='top', vt='', bulk='None')
    grp = [Fet(h, 'n', WF * NFG, PARAMS['l'], nf=NFG, gate='top', vt='', bulk='None') for _ in range(NG)]
    rl = PolyRes(h, LRL, 1, w=1.41, typ='sky130_fd_pr__res_high_po_1p41', pad_w=1.2)
    x_ri = 0.7
    y_in = RC + GRW
    nbx = (x_ri + 0.15, x_ri + 0.45)
    cin = [box(1.25, 0, 1.65, 0), box(1.95, 0, 2.35, 0)]   # input crossing columns (met4), left of the rows
    off1 = tail.strips[1].center().x - tail.diff.left
    x_t = max(x_ri + 0.45, nbx[1] + 0.2 + VW / 2 - off1)
    tail.place(x_t, y_in + 0.47).commit()
    rep = []

    def land(s, y0, y1):
        xc = s.center().x
        bb = box(xc - VW / 2, y0, xc + VW / 2, y1)
        h.rect('m1', bb)
        return h.via('via1', bb, enc=(0.075, 0.085))

    def sx(f, k):
        return f.strips[k].center().x

    # tail: sources down into the ring, drains -> tail bar (met2, 0.6 tall)
    tb = (tail.diff.top - 0.15 - 0.6, tail.diff.top - 0.15)
    n = 0
    for k, s in enumerate(tail.strips):
        if k % 2 == 0:
            h.rect('m1', box(sx(tail, k) - VW / 2, y_in - 0.01, sx(tail, k) + VW / 2, s.top))
        else:
            n += land(s, *tb)
    tbar = h.rect('m2', box(sx(tail, 1) - VW / 2, tb[0], sx(tail, nt - 1) + VW / 2, tb[1]))
    rep.append(('tail', 'tail drains', n, cuts_needed(0.6, 'via1')))
    # nb strap and riser (as amp_dpc_t)
    ny0 = min(q.bottom for q in tail.pads)
    ny1 = max(max(q.top for q in tail.pads), ny0 + 0.32)
    h.rect('m1', box(nbx[0], ny0, tail.pads[-1].right, ny1))
    h.via('via1', box(nbx[0], ny0, nbx[1], ny1), enc=(0.075, 0.085))
    h.rect('m2', box(nbx[0], 0, nbx[1], ny1))
    # pair row: right of the input columns
    gw = grp[0].diff.width()
    xp = cin[1].right + 0.6
    yp = ny1 + 0.7
    for f in grp:
        f.place(xp, yp).commit()
        xp = f.diff.right + 0.9
    d0 = grp[0].diff.bottom
    yb = {'tail': (d0 + 0.15, d0 + 0.75), 'own': (d0 + 1.55, d0 + 1.97), 'oth': (d0 + 2.95, d0 + 3.37)}
    cnt = {'tail': 0, 'own': 0, 'oth': 0}
    for gi, f in enumerate(grp):
        dn = 'own' if gi in (0, 3) else 'oth'
        for k, s in enumerate(f.strips):
            net = 'tail' if k % 2 == 0 else dn
            cnt[net] += land(s, *yb[net])
    L, R = sx(grp[0], 0) - VW / 2, sx(grp[-1], NFG) + VW / 2
    h.rect('m2', box(L, yb['tail'][0], R, yb['tail'][1]))
    rep.append(('tail', 'pair sources', cnt['tail'], cuts_needed(0.6, 'via1')))
    rep.append(('own', 'outer drains', cnt['own'], cuts_needed(0.3, 'via1')))
    rep.append(('oth', 'inner drains', cnt['oth'], cuts_needed(0.3, 'via1')))
    # tail links: met2 from the tail's bar up to the row's tail bar (over the nb strap)
    for xc in (L + 0.4, (L + R) / 2, R - 0.4):
        h.rect('m2', box(xc - 0.25, tb[0], xc + 0.25, yb['tail'][1]))
    # load: right of the row, bottom head below the row's own bar
    xr = R + 1.0
    rl.place(xr - (rl._bbox.left - rl._poly.left), max(yp - 0.2, ny1 + 0.6) - rl._bbox.bottom + rl._poly.bottom)
    bot, top_ = rl.heads[0]
    nv = h.via('via1', bot, enc=(0.085, 0.085))
    h.rect('m2', box(bot.left, min(bot.bottom, yb['own'][0]), bot.right, max(bot.top, yb['own'][1])))
    nv2 = h.via('via1', top_, enc=(0.085, 0.085))
    rep.append(('own', 'Rl heads', min(nv, nv2), cuts_needed(0.6, 'via1')))
    # bars to the right edge region (the out columns are placed by the top cell)
    x_end = frame['W_req']
    own = h.rect('m2', box(sx(grp[0], 1) - VW / 2, yb['own'][0], x_end, yb['own'][1]))
    oth = h.rect('m2', box(sx(grp[1], 1) - VW / 2, yb['oth'][0], x_end, yb['oth'][1]))
    # gates: outer straps (own input) joined by a met2 jumper, out to the left edge;
    # the inner strap (other input): via1 + via2, met3 up over the jumper and left to the input columns
    gy0 = min(q.bottom for f in grp for q in f.pads)
    gy1 = max(max(q.top for f in grp for q in f.pads), gy0 + 0.32)
    straps = [h.rect('m1', box(grp[0].pads[0].left, gy0, grp[0].pads[-1].right, gy1)),
              h.rect('m1', box(grp[1].pads[0].left, gy0, grp[2].pads[-1].right, gy1)),
              h.rect('m1', box(grp[3].pads[0].left, gy0, grp[3].pads[-1].right, gy1))]
    yj = (gy1 + 0.35, gy1 + 0.85)                      # jumper (met2)
    for st in (straps[0], straps[2]):
        xc = st.center().x
        v = box(xc - 0.25, gy0, xc + 0.25, gy1)
        h.via('via1', v, enc=(0.085, 0.085))
        h.rect('m2', box(v.left, gy0, v.right, yj[1]))
    jump = h.rect('m2', box(0, yj[0], straps[2].center().x + 0.25, yj[1]))
    xc = straps[1].center().x
    v = box(xc - 0.25, gy0, xc + 0.25, gy1)
    h.via('via1', v, enc=(0.085, 0.085))
    h.rect('m2', v)
    h.via('via2', v, enc=(0.065, 0.06))
    yo = (yj[1] + 0.45, yj[1] + 0.95)                  # other-input line (met3)
    h.rect('m3', box(v.left, gy0, v.right, yo[1]))
    oline = h.rect('m3', box(cin[0].left - 0.05, yo[0], v.right, yo[1]))
    # ring
    inner = box(x_ri, y_in, max(tail.diff.right + 0.45, rl.bbox.right + 0.6), max(yo[1] + 0.45, rl.bbox.top + 0.6))
    ring(h, inner, 'p', GRW)
    return h, dict(rep=rep, tbar=tbar, own=own, oth=oth, jump=jump, oline=oline, cin=cin, nbx=nbx,
                   rl_top=top_, ring=box(inner.left - GRW, inner.bottom - GRW, inner.right + GRW, inner.top + GRW),
                   rl_right=rl.bbox.right, tail=tail)


def make():
    _, fr = dpc.make()                                 # the frame: height, signal heights
    Hh, ys, (t0, t1) = fr['Hh'], fr['y_sig'], fr['trk']
    b = Block('amp_dp_t')
    # pass 1 for the width: the out columns go right of the ring
    probe = Block('probe')
    _, g0 = half(probe, dict(W_req=50))
    W = snap(max(g0['ring'].right, g0['rl_right'] + 0.6) + 2.1)
    h, g = half(b, dict(W_req=W))
    c2 = box(W - 0.55, 0, W - 0.15, 0)                 # outp column
    sh = box(W - 1.25, 0, W - 0.85, 0)                 # VDD shield
    c1 = box(W - 1.95, 0, W - 1.55, 0)                 # outn column
    b.place(h.cell, 0, 0)
    b.place(h.cell, 0, 0, 0, True)
    # rails (as amp_dpc_t)
    b.rect('m1', box(0, -RC, W, RC))
    b.rect('m3', box(0, -RC, W, RC))
    b.rect('m2', box(0, -0.2, W, 0.2))
    gap = (g['nbx'][0] - 0.3, g['nbx'][1] + 0.3)
    for y0, y1 in ((0.34, RC), (-RC, -0.34)):
        for xa, xb in ((0, gap[0]), (gap[1], W)):
            if xb - xa < 0.5:
                continue
            bb = b.rect('m2', box(xa, y0, xb, y1))
            b.via('via1', bb, enc=(0.085, 0.085))
            b.via('via2', bb, enc=(0.085, 0.065))
    b.pin('m1', box(0, -RC, 1.0, RC), 'VSS')
    b.pin('m2', box(0, -0.2, 0.5, 0.2), 'nb')
    b.pin('m2', box(W - 0.5, -0.2, W, 0.2), 'nb')
    for sg in (1, -1):
        rv = box(0, sg * (Hh - RV), W, sg * Hh)
        b.stack(rv, 'm1', 'm3')
        b.pin('m1', box(0, rv.bottom, 1.0, rv.top), 'VDD')
        top_ = g['rl_top']
        b.rect('m2', box(top_.left, sg * top_.bottom, top_.right, sg * (Hh - RV + 0.01)))
    for c in (box(0.3, 0, 0.8, 0), sh):               # VDD columns: rails joined (left edge), shield
        b.rect('m4', box(c.left, -Hh, c.right, Hh))
        for sg in (1, -1):
            b.via('via3', box(c.left, sg * (Hh - RV), c.right, sg * Hh))
    rep = list(g['rep'])

    def stack(c, bb, low='m2', hh=0.45):
        """met4 column c down to a met2 bar (or a met3 line) bb: via2 + met3 island (0.9 tall,
        centred on bb) + via3."""
        yc = bb.center().y
        isl = b.rect('m3', box(c.left - 0.05, yc - hh, c.right + 0.05, yc + hh))    # hh 0.45: 2 cuts high
        if low == 'm2':
            b.rect('m2', isl)                          # the bar widened under it
        n2 = b.via('via2', isl, enc=(0.065, 0.065)) if low == 'm2' else 99
        n3 = b.via('via3', isl, enc=(0.09, 0.09))
        return min(n2, n3)

    def mir(bb, sg):
        return box(bb.left, sg * bb.bottom, bb.right, sg * bb.top)

    # outputs: own bar, the other half's other bar, the out track: all on the net's column
    for sg, c, net in ((1, c1, 'outn'), (-1, c2, 'outp')):
        b.rect('m4', box(c.left, -Hh, c.right, Hh))
        own, oth = mir(g['own'], sg), mir(g['oth'], -sg)
        n_own = stack(c, own)
        n_oth = stack(c, oth)
        tr = b.rect('m2', box(c.left - 0.05, min(sg * t0, sg * t1), W, max(sg * t0, sg * t1)))
        stack(c, tr)
        b.pin('m2', box(W - 0.5, tr.bottom, W, tr.top), net)
        b.pin('m4', box(c.left, Hh - 0.5, c.right, Hh), net)
        b.pin('m4', box(c.left, -Hh, c.right, -Hh + 0.5), net)
        rep.append((net, 'bars to column', min(n_own, n_oth), cuts_needed(0.3, 'via2')))
    # inputs: own jumper (met2, to the left edge: the pin) and the other half's met3 line
    cin = g['cin']
    for sg, c, net in ((1, cin[1], 'inp'), (-1, cin[0], 'inn')):
        j, o = mir(g['jump'], sg), mir(g['oline'], -sg)
        ia, ib = stack(c, j, hh=0.25), stack(c, o, low='m3', hh=0.25)
        b.rect('m4', box(c.left, min(j.center().y, o.center().y) - 0.25, c.right, max(j.center().y, o.center().y) + 0.25))
        b.pin('m2', box(0, j.bottom, 0.5, j.top), net)
    # the two halves' tail nodes: a short met4 column through the rail
    tb = g['tbar']
    ct = box(tb.center().x - 0.3, 0, tb.center().x + 0.3, 0)
    for sg in (1, -1):
        stack(ct, mir(tb, sg))
    b.rect('m4', box(ct.left, -tb.center().y - 0.45, ct.right, tb.center().y + 0.45))
    b.label('m2', tb, 'tail')
    b.cell.flatten(-1, True)
    for li in b.ly.layer_indexes():
        b.cell.shapes(li).transform(pya.DTrans(0, Hh))
    print(f'amp_dp_t: {W:.2f} x {2 * Hh:.2f} um; pair 2 rows x {NG} x {NFG} fingers of {WF} um per half, tail nf {PARAMS["mt"]} per half; '
          f'outputs at {Hh - ys:.2f} / {Hh + ys:.2f} um')
    print('  net    where           cuts  need (2x margin)')
    for net, where, nc, need in rep:
        print(f'  {net:6s} {where:15s} {nc:4d}  {need}{"   <-- short" if nc < need else ""}')
    return b, dict(W=W, H=2 * Hh)


if __name__ == '__main__':
    b, meta = make()
    b.write(os.path.join(REPO, 'layout', 'amp_dp_t.gds'))
    write_ref('amp_dp_t', 'amp_dp', PARAMS)
