# amp_dpc_t: chain stages 2..6 as a tall, thin cell, for a straight chain (Harald Pretl's
# review, action 8; docs/handoff_tall_stages.md). Same circuit, PARAMS and reference as
# amp_dpc (layout/gen/amp_dpc.py; xschem/gen/chain.py:amp_dpc):
#   Mp / Mn   nfet W 20 nf 4 L 0.15: D outn / outp, G inp / inn, S sp / sn
#   Mtail_p/n nfet 3 x (W 6 nf 2) L 0.5 per side (drawn as one nf 6, W 18): D sp / sn, G nb
#   Rl_p / Rl_n res_high_po_0p69 L 7.38 um: VDD -> outn / outp
#   Cs_a (top sn, bottom sp), Cs_b (top sp, bottom sn): 0.3 pF MIMs, now tall rectangles
#
# Halves stacked: the p half above the cell's horizontal centre line, the n half its mirror
# image below (one half cell, placed twice). Across the cell, edge to edge:
#   centre: VSS rail (met1 + met3, met2 strips at its top and bottom edges with via1 / via2),
#           and nb on met2 sandwiched in the middle of it (both on the centre line, so a
#           flipped (MX) cell lines up with an unflipped one);
#   top and bottom edges: VDD rails (met1-met3), joined by a met4 column at the left edge.
# VSS in the centre because it is where the circuit starts: in each half, going out from the
# centre, tail (sources straight down into the ring and rail), nb strap, pair, load, VDD. nb
# drops to the centre strip from each tail's gate strap on a met2 riser at the left.
# One p-tap ring per half; its inner side sits on the rail.
# Signals on met2 at the height of the pair's gate strap (+/- Y_SIG): the input enters from
# the left edge straight onto the strap, the output (drain bar + load's bottom head, joined
# by a met2 spine right of the pair) leaves at the same height to the right edge. So a stage's
# outputs land on the next stage's inputs; flip every other stage (MX) and outn lands on inn.
# Each half's MIM bottom plate (its source node) covers the half; capm starts above the
# band where the tail-drain and pair-source bars via2 up into the plate (no via2 under
# capm). The top plates cross over on met4 strips: Cs_a's (left) down into plate B's band,
# Cs_b's (right) up into plate A's band.
# Taps to log_det: each output also runs on a met4 column the full height of the cell, at the
# right edge clear of the plates, so both outputs reach either long edge (TAPS=False drops them).
# Run: tools/osic klayout -b -r layout/gen/amp_dpc_tall.py
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pya   # noqa: E402
from lay import Block, Fet, REPO, box, ring, snap, write_ref, cuts_needed   # noqa: E402
from passives import PolyRes, CAPM, CAPM_ENC_V3, BOT_PLATE_SPACE   # noqa: E402

PARAMS = dict(w=20, l=0.15, rl=4e3, wt=6, mt=6, mm=0, cs=0.6e-12)
CAPW_SQ = math.sqrt(PARAMS['cs'] / 2 / 2.06e-15)       # today's square side (the schematic's)
MIM_DW = 0.15                                          # model: C = Ca (w + dw)(l + dw)
LRL = (PARAMS['rl'] - 526) / 470.9
RC = 1.0            # centre (VSS) rail: -RC .. RC
RV = 1.5            # VDD rail height
GRW = 0.4
VW = 0.3            # via landing width on a strip
BAR = 0.42          # met2 bar height
TRK = 0.4           # signal track height (met2)
W_CELL = float(os.environ.get('DPC_W', 11.7))
TAPS = os.environ.get('DPC_TAPS', '1') == '1'
SHIELD = os.environ.get('DPC_SHIELD', '1') == '1'
RPM = (86, 20)


def half(b):
    """The p half (y >= 0, centre line at y = 0) as its own cell. Returns the cell and the
    geometry the top cell needs."""
    h = Block(b.name + '_half', ly=b.ly)
    tail = Fet(h, 'n', PARAMS['wt'] * PARAMS['mt'] / 2, 0.5, nf=PARAMS['mt'], gate='top', vt='', bulk='None')
    pair = Fet(h, 'n', PARAMS['w'], PARAMS['l'], nf=4, gate='top', vt='', bulk='None')
    rl = PolyRes(h, LRL, 1, w=0.69, typ='sky130_fd_pr__res_high_po_0p69', pad_w=0.5)
    x_ri = 0.7                                       # ring hole left (ring 0.3 .. 0.7)
    y_in = RC + GRW                                  # ring hole bottom
    nbx = (x_ri + 0.15, x_ri + 0.45)                 # nb riser (met2)
    # tail: D bar (from strip 1) clear of the nb riser
    off1 = tail.strips[1].center().x - tail.diff.left
    x_t = max(x_ri + 0.45, nbx[1] + 0.2 + VW / 2 - off1)
    tail.place(x_t, y_in + 0.47).commit()

    def land(s, y0, y1):
        xc = s.center().x
        bb = box(xc - VW / 2, y0, xc + VW / 2, y1)
        h.rect('m1', bb)
        return h.via('via1', bb, enc=(0.075, 0.085))

    def span(f, k0, k1):
        return f.strips[k0].center().x - VW / 2, f.strips[k1].center().x + VW / 2

    rep = []
    # tail: sources (even strips) down into the ring / rail on met1, drains (odd) -> sp bar
    tb = (tail.diff.top - 0.15 - BAR, tail.diff.top - 0.15)
    n = 0
    for k, s in enumerate(tail.strips):
        if k % 2 == 0:
            h.rect('m1', box(s.center().x - VW / 2, y_in - 0.01, s.center().x + VW / 2, s.top))
        else:
            n += land(s, *tb)
    sbar_t = h.rect('m2', box(*span(tail, 1, len(tail.strips) - 2)[:1], tb[0], span(tail, 1, len(tail.strips) - 2)[1], tb[1]))
    rep.append(('sp', 'tail drains', n, cuts_needed(0.18, 'via1')))
    # nb: met1 strap over the tail's gate pads, out left to the riser, riser down to y = 0
    ny0 = min(q.bottom for q in tail.pads)
    ny1 = max(max(q.top for q in tail.pads), ny0 + 0.32)
    h.rect('m1', box(nbx[0], ny0, tail.pads[-1].right, ny1))
    h.via('via1', box(nbx[0], ny0, nbx[1], ny1), enc=(0.075, 0.085))
    h.rect('m2', box(nbx[0], 0, nbx[1], ny1))
    # pair: above the nb strap, left-aligned with the tail
    pair.place(tail.diff.left, ny1 + 0.6).commit()
    ps = (pair.diff.bottom + 0.2, pair.diff.bottom + 0.2 + BAR)
    po = (pair.diff.top - 0.2 - BAR, pair.diff.top - 0.2)
    cnt = {'s': 0, 'o': 0}
    for k, s in enumerate(pair.strips):
        cnt['s' if k % 2 == 0 else 'o'] += land(s, *(ps if k % 2 == 0 else po))
    sbar_p = h.rect('m2', box(span(pair, 0, 4)[0], ps[0], span(pair, 0, 4)[1], ps[1]))
    rep.append(('sp', 'pair sources', cnt['s'], cuts_needed(0.18, 'via1')))
    rep.append(('outn', 'pair drains', cnt['o'], cuts_needed(0.18, 'via1')))
    xs = pair.diff.right + 0.6                        # out spine (met2) centre
    h.rect('m2', box(span(pair, 1, 3)[0], po[0], xs + 0.15, po[1]))
    # load: right of the spine, bottom head about level with the pair's bottom
    x_rl = xs + 0.8
    y_rl = max(pair.diff.bottom - 0.3, ny1 + 0.6 - (rl._poly.bottom - rl._bbox.bottom))   # poly 0.48 from the tail's pads (poly.9)
    rl.place(x_rl - (rl._bbox.left - rl._poly.left), y_rl - rl._bbox.bottom + rl._poly.bottom)
    # a lone 0p69 segment's rpm / psdm are too narrow (rpm.1, psdm.1): widen them to 1.3 um
    rr = pya.Region(rl.cell.begin_shapes_rec(b.ly.layer(*RPM))).bbox().to_dtype(b.ly.dbu)
    cx = rl.poly.center().x
    rpm = box(cx - 0.65, rl.poly.bottom + (rr.bottom - rl._poly.bottom), cx + 0.65, rl.poly.top + (rr.top - rl._poly.top))
    h.rect(RPM, rpm)
    h.rect('psdm', box(cx - 0.65, rl.psdm.bottom, cx + 0.65, rl.psdm.top))
    bot, top_ = rl.heads[0]
    nv = h.via('via1', bot, enc=(0.085, 0.085))
    h.rect('m2', box(xs - 0.15, bot.bottom, bot.right, bot.top))       # jog to the spine
    nv2 = h.via('via1', top_, enc=(0.085, 0.085))
    rep.append(('outn', 'Rl heads', min(nv, nv2), cuts_needed(0.18, 'via1')))
    # gate strap and the signal height
    gy0 = min(q.bottom for q in pair.pads)
    gy1 = max(max(q.top for q in pair.pads), gy0 + 0.32)
    h.rect('m1', box(pair.pads[0].left, gy0, pair.pads[-1].right, gy1))
    y_sig = snap((gy0 + gy1) / 2)
    t0, t1 = y_sig - TRK / 2, y_sig + TRK / 2
    gv = box(pair.pads[0].left, max(gy0, t0), pair.pads[0].left + 0.5, min(gy1, t1))
    rep.append(('inp', 'gate strap', h.via('via1', gv, enc=(0.085, 0.085)), 1))
    h.rect('m2', box(0, t0, gv.right, t1))                             # in track from the left edge
    h.rect('m2', box(xs - 0.15, bot.bottom, xs + 0.15, t1))            # out spine
    assert gv.right + 0.3 < xs - 0.15
    # ring round the half
    x_ri_r = max(tail.diff.right + 0.45, rl.bbox.right + 0.6, rpm.right + 0.3)
    ring_top = max(rl.bbox.top + 0.6, gy1 + 0.45)
    inner = box(x_ri, y_in, x_ri_r, ring_top)
    ring(h, inner, 'p', GRW)
    return h, dict(y_sig=y_sig, trk=(t0, t1), xs=xs, rl_top=top_, sbars=(sbar_t, sbar_p), nbx=nbx,
                   ring=box(inner.left - GRW, inner.bottom - GRW, inner.right + GRW, inner.top + GRW),
                   rep=rep, tail=tail, pair=pair)


def make(W=W_CELL, taps=TAPS, name='amp_dpc_t', extra=0.0, riser_left=False, hook=None):
    """extra: width added at the right edge (the plates stay where they are, the tap columns
    move right, leaving one more column position next to the outn column); riser_left: the
    loads' VDD risers jog to the left edge (frees the space above each ring); hook(b, ctx):
    draws more before the cell is flattened (amp_dpc_shunt_tall.py)."""
    b = Block(name)
    h, g = half(b)
    W = max(W, g['ring'].right + 0.3)
    W0, W = W, W + extra
    ys = g['y_sig']
    t0, t1 = g['trk']
    # x plan, right edge: tap columns (met4) and their met3 landings, 1.2 clear of the plates
    # outp column at the edge, outn column 1.4 in, a VDD column between them as a shield
    # (unshielded, 0.3 apart, the two columns coupled 6.9 fF outn-outp, x2 for the signal)
    c2 = box(W - 0.55, 0, W - 0.15, 0)                 # outp column
    sh = box(W - 1.25, 0, W - 0.85, 0)                 # VDD shield column
    c1 = box(W - 1.95, 0, W - 1.55, 0) if SHIELD else sh   # outn column
    isl_l = c1.left - extra - 0.05                    # (the plates as for width W0)
    pl0, pl1 = 1.3, isl_l - BOT_PLATE_SPACE            # plate x (left: 1.2 from the left neighbour's landings)
    cw = snap(pl1 - pl0 - 0.4)                         # capm width
    area = (CAPW_SQ + MIM_DW) ** 2                     # same C as today's square
    ch = snap(area / (cw + MIM_DW) - MIM_DW)
    sbar_t, sbar_p = g['sbars']
    capm0 = snap(sbar_p.top + 0.25)                    # capm above the band with the via2s
    py0 = RC + BOT_PLATE_SPACE                         # plate bottom: 1.2 above the rail's met3
    ptop = capm0 + ch + 0.2
    Hh = snap(ptop + BOT_PLATE_SPACE + RV)             # half height
    H = 2 * Hh

    # the two halves
    b.place(h.cell, 0, 0)
    b.place(h.cell, 0, 0, 0, True)
    # rails: VSS + nb in the centre, VDD at the top and bottom edges
    b.rect('m1', box(0, -RC, W, RC))
    b.rect('m3', box(0, -RC, W, RC))
    b.rect('m2', box(0, -0.2, W, 0.2))
    gap = (g['nbx'][0] - 0.3, g['nbx'][1] + 0.3)      # the nb risers come through here
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
        # load's top head: met2 riser up into the rail
        top_ = g['rl_top']
        if riser_left:                                 # jog left to x 1.0 .. 1.4, then up
            b.rect('m2', box(1.0, sg * top_.bottom, top_.right, sg * top_.top))
            b.rect('m2', box(1.0, sg * top_.bottom, 1.4, sg * (Hh - RV + 0.01)))
        else:
            b.rect('m2', box(top_.left, sg * top_.bottom, top_.right, sg * (Hh - RV + 0.01)))
    vc = b.rect('m4', box(0.3, -Hh, 0.8, Hh))         # VDD rails joined (left edge)
    for sg in (1, -1):
        b.via('via3', box(0.3, sg * (Hh - RV), 0.8, sg * Hh))
    # signals: pins at the edges, labels on the internal nets
    for sg, i, o, s in ((1, 'inp', 'outn', 'sp'), (-1, 'inn', 'outp', 'sn')):
        b.pin('m2', box(0, min(sg * t0, sg * t1), 0.5, max(sg * t0, sg * t1)), i)
        b.rect('m2', box(g['xs'] - 0.15, sg * t0, W, sg * t1))          # out track to the right edge
        b.pin('m2', box(W - 0.5, min(sg * t0, sg * t1), W, max(sg * t0, sg * t1)), o)
        b.label('m2', box(sbar_t.left, sg * sbar_t.bottom, sbar_t.right, sg * sbar_t.top), s)
    rep = list(g['rep'])
    # MIMs: plates over each half, capm above the via2 band
    caps, plates = {}, {}
    for sg, s in ((1, 'p'), (-1, 'n')):
        plates[s] = b.rect('m3', box(pl0, sg * py0, pl1, sg * ptop))
        caps[s] = b.rect(CAPM, box(pl0 + 0.2, sg * capm0, pl1 - 0.2, sg * (capm0 + ch)))
        nv = 0
        for bar in (sbar_t, sbar_p):
            bb = box(max(bar.left, pl0 + 0.1), sg * bar.bottom, min(bar.right, pl1 - 0.1), sg * bar.top)
            nv += b.via('via2', bb, enc=(0.085, 0.085))
        rep.append(('s' + s, 'bars to plate', nv, cuts_needed(0.18, 'via2')))
    # top plates: Cs_a (over the p half, top sn) on a met4 strip down into plate B's band (left);
    # Cs_b (top sp) up into plate A's band (right)
    land = (py0 + 0.25, sbar_t.bottom - 0.3)          # band below the tail-drain bar
    for s, sg, xa in (('p', 1, pl0 + 0.4), ('n', -1, pl1 - 1.2)):
        st = box(xa, -sg * land[1], xa + 0.8, sg * (capm0 + 1.6))
        b.rect('m4', st)
        b.via('via3', st & caps[s], enc=(CAPM_ENC_V3, CAPM_ENC_V3))
        b.via('via3', box(xa, -sg * land[0], xa + 0.8, -sg * land[1]))
    assert vc.right + 0.3 <= pl0 + 0.4
    # taps: each output up a met4 column the full height, landed from its track on met3
    if taps:
        for sg, c, net in ((1, c1, 'outn'), (-1, c2, 'outp')):
            col = b.rect('m4', box(c.left, -Hh, c.right, Hh))
            isl = b.rect('m3', box(c.left - 0.05, sg * ys - 0.3, c.right + 0.05, sg * ys + 0.3))
            b.via('via2', box(isl.left, sg * t0, isl.right, sg * t1) if sg > 0 else box(isl.left, -t1, isl.right, -t0),
                  enc=(0.065, 0.085))
            b.via('via3', isl, enc=(0.09, 0.09))
            b.pin('m4', box(c.left, Hh - 0.5, c.right, Hh), net)
            b.pin('m4', box(c.left, -Hh, c.right, -Hh + 0.5), net)
        if SHIELD:
            b.rect('m4', box(sh.left, -Hh, sh.right, Hh))
            for sg in (1, -1):
                b.via('via3', box(sh.left, sg * (Hh - RV), sh.right, sg * Hh))
    if hook:
        hook(b, dict(W=W, Hh=Hh, ys=ys, trk=(t0, t1), g=g, c1=c1, c2=c2, sh=sh, cg=box(c1.left - 0.7, 0, c1.right - 0.7, 0),
                     plate=(pl0, pl1), rep=rep))
    # everything up so the cell's lower left is (0, 0)
    b.cell.flatten(-1, True)
    for li in b.ly.layer_indexes():
        b.cell.shapes(li).transform(pya.DTrans(0, Hh))
    meta = dict(W=W, H=H, y_sig=ys, trk=(t0, t1), capw=cw, capl=ch, Hh=Hh)
    print(f'{name}: {W:.2f} x {H:.2f} um; cap {cw} x {ch} um (was {CAPW_SQ:.2f} square), '
          f'signals at {Hh - ys:.2f} / {Hh + ys:.2f} um, taps {"on" if taps else "off"}')
    print('  net    where           cuts  need (2x margin)')
    for net, where, nc, need in rep:
        print(f'  {net:6s} {where:15s} {nc:4d}  {need}{"   <-- short" if nc < need else ""}')
    return b, meta


def write(b, meta, name='amp_dpc_t'):
    b.write(os.path.join(REPO, 'layout', name + '.gds'))
    write_ref(name, 'amp_dpc', dict(PARAMS, sqrt=math.sqrt))
    ref = os.path.join(REPO, 'layout', 'ref', name + '.spice')
    s = open(ref).read()
    s = s.replace('W=12.0678 L=12.0678', f'W={meta["capw"]:g} L={meta["capl"]:g}')
    s = s.split('\n', 1)
    s[0] = f'* {name}: xschem/amp_dpc.sch with {PARAMS}, Cs drawn {meta["capw"]:g} x {meta["capl"]:g} um (amp_dpc_tall.py)'
    open(ref, 'w').write('\n'.join(s))


if __name__ == '__main__':
    write(*make())
