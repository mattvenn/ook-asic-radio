# amp_dpc layout: chain stages 2..6 (xschem/gen/chain.py:amp_dpc), lna_chain's sizing
# w=20 l=0.15 rl=4k wt=6 mt=6 cs=0.6p:
#   Mp / Mn   nfet W 20 nf 4 L 0.15: D outn / outp, G inp / inn, S sp / sn
#   Mtail_p/n nfet 3 x (W 6 nf 2) L 0.5 per side (drawn as one nf 6, W 18): D sp / sn, G nb
#   Rl_p / Rl_n res_high_po_0p69 L 7.38 um: VDD -> outn / outp
#   Cs_a (top sn, bottom sp), Cs_b (top sp, bottom sn): 0.3 pF MIMs, ~12.07 um square
# 0.18 mA per side (tail = mt x iref, iref 60 uA): minimum widths, >= 2 cuts.
#
# Mirrored about the centre (p half left, n half right), as STATUS asks for the chain:
#   VSS rail (met1+2+3) / one p-tap ring round all devices / VDD rail on top.
#   In the ring, per half from the outer edge: tail (gates 'bottom', on the nb strap,
#   which crosses the centre so both halves share it) with the pair above it (gates 'top',
#   the in strap); then the load resistors as an adjacent pair in the centre (adjacent so
#   their RPM regions merge: a lone 0.69 um segment fails magic rpm.1).
#   Over each strip pair, met2 bars: tail VSS (to the ring) and s (source), pair s and out.
#   Cs_a sits over the p half and Cs_b over the n half: each bottom plate is its half's
#   source node, so the s bars just via2 up into it. Each top plate is contacted by a met4
#   strip that runs over the other cap to the far outer edge and drops (met3 column, 1.2 um
#   from the plates) to that half's s bar: Cs_a's strip high, Cs_b's low, so they don't cross.
#   Above the ring, a channel of met1 tracks: inp, inn to the left edge, outp, outn to the
#   right edge; every vertical (in risers, out spines, VDD risers) is met2, so nothing
#   crosses on one layer. nb leaves on met2 at both edges.
# Run: tools/osic klayout -b -r layout/gen/amp_dpc.py
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, REPO, box, ring, snap, write_ref   # noqa: E402
from passives import PolyRes, mim, CAPM_ENC_M3, BOT_PLATE_SPACE   # noqa: E402

PARAMS = dict(w=20, l=0.15, rl=4e3, wt=6, mt=6, mm=0, cs=0.6e-12)
CAPW = snap(math.sqrt(PARAMS['cs'] / 2 / 2.06e-15))
LRL = (PARAMS['rl'] - 526) / 470.9
RAIL_H = 1.5
GRW = 0.4
VW = 0.3            # via landing width on a strip (via1 0.15 + 0.075)
BAR = 0.42          # met2 bar height


def make():
    b = Block('amp_dpc')
    e = CAPM_ENC_M3
    plate = CAPW + 2 * e
    drop_w = 0.5
    edge = 0.3                                          # drop column to cell edge
    # devices (placed at 0,0 first to measure)
    tl = {s: Fet(b, 'n', PARAMS['wt'] * PARAMS['mt'] / 2, 0.5, nf=PARAMS['mt'], gate='bottom', vt='', bulk='None')
          for s in 'pn'}
    pr = {s: Fet(b, 'n', PARAMS['w'], PARAMS['l'], nf=4, gate='top', vt='', bulk='None') for s in 'pn'}
    rl = {s: PolyRes(b, LRL, 1, w=0.69, typ='sky130_fd_pr__res_high_po_0p69', pad_w=0.5) for s in 'pn'}
    rpitch = rl['p']._bbox.width() - 0.01                # adjacent: markers overlap, merge
    # x: half width from the outer device edge to the centre
    x_dev = edge + drop_w + BOT_PLATE_SPACE              # devices start under the plate
    half_dev = max(tl['p'].diff.width(), pr['p'].diff.width())
    x_spine = x_dev + 0.45 + half_dev + 0.6              # out spine (met2), inner side of the half
    x_rl = x_spine + 0.8                                 # Rl_p marker left
    cx = x_rl + rpitch                                   # centre: between Rl_p and Rl_n
    cx = max(cx, x_dev + plate + 0.8)                    # the plate (one per half, from x_dev) must fit
    x_rl = cx - rpitch                                   # the Rl pair centred on the mirror line
    W = 2 * cx

    def mx(x):                                           # mirror an x coordinate
        return W - x

    # y: rail, ring bottom, nb strap, tail, pair
    y_in = RAIL_H + GRW                                  # ring hole bottom
    t = tl['p']
    pad_drop = t.diff.bottom - min(p.bottom for p in t.pads)          # pads below the diff
    y_tail = y_in + 0.45 + pad_drop + 0.2
    p_ = pr['p']
    pad_rise = max(p.top for p in p_.pads) - p_.diff.top
    y_pair = y_tail + t.diff.height() + 1.2
    for s, sgn in (('p', 1), ('n', -1)):
        for f, y in ((tl[s], y_tail), (pr[s], y_pair)):
            x = x_dev + 0.45 if sgn > 0 else mx(x_dev + 0.45) - f.diff.width()
            f.place(x, y).commit()
    y_dev_top = y_pair + p_.diff.height() + pad_rise
    # load resistors: centre, from just above the nb strap's level up
    y_rl = y_tail + 0.3                                  # clear of the nb strap (met1) under it
    rl['p'].place(x_rl - (rl['p']._bbox.left - rl['p']._poly.left), y_rl - rl['p']._bbox.bottom + rl['p']._poly.bottom)
    rl['n'].place(x_rl + rpitch - (rl['n']._bbox.left - rl['n']._poly.left),
                  y_rl - rl['n']._bbox.bottom + rl['n']._poly.bottom)
    # one psdm over both loads: theirs end up 0.35 apart (psdm.2 0.38) and the 0.69 pcell
    # leaves a thin psdm notch at its heads (psdm.1)
    b.rect((94, 20), rl['p'].psdm + rl['n'].psdm)
    ring_top = max(y_dev_top + 0.45, rl['p'].bbox.top + 0.6)       # ring's psdm 0.38 from the loads'
    inner = box(x_dev, y_in, mx(x_dev), ring_top)
    ring(b, inner, 'p', GRW)
    b.stack(box(0, 0, W, RAIL_H), 'm1', 'm3')
    b.rect('m1', box(inner.left - GRW, RAIL_H - 0.01, inner.right + GRW, y_in))     # ring onto VSS
    b.pin('m1', box(0, 0, 1.0, RAIL_H), 'VSS')

    def via_strip(s, y0, y1):
        """met1 landing on a S/D strip (widened to VW) + via1, from y0 to y1."""
        xc = s.center().x
        bb = box(xc - VW / 2, y0, xc + VW / 2, y1)
        b.rect('m1', bb)
        b.via('via1', bb, enc=(0.075, 0.085))
        return bb

    # nb: one met1 strap under both tails (their pads), across the centre; met2 out at both edges
    pads = [q for s in 'pn' for q in tl[s].pads]
    ny0, ny1 = min(q.bottom for q in pads), max(q.top for q in pads)
    ny1 = max(ny1, ny0 + 0.32)
    b.rect('m1', box(min(q.left for q in pads), ny0, max(q.right for q in pads), ny1))
    for xa, xb in ((min(q.left for q in pads), min(q.left for q in pads) + 0.5),
                   (max(q.right for q in pads) - 0.5, max(q.right for q in pads))):
        b.via('via1', box(xa, ny0, xb, ny1), enc=(0.085, 0.055))
    b.rect('m2', box(0, ny0, W, ny1))
    b.pin('m2', box(0, ny0, 0.5, ny1), 'nb')
    b.pin('m2', box(W - 0.5, ny0, W, ny1), 'nb')

    out = {}
    for s, sgn in (('p', 1), ('n', -1)):
        t, p, r = tl[s], pr[s], rl[s]
        src, onet = ('sp', 'outn') if s == 'p' else ('sn', 'outp')
        # tail: S strips (even) -> VSS bar (low), D strips (odd) -> s bar (high)
        tb0 = t.diff.bottom + 0.2
        ts0 = t.diff.top - 0.2 - BAR
        for k, st in enumerate(t.strips):
            if k % 2 == 0:
                via_strip(st, tb0, tb0 + BAR)
            else:
                via_strip(st, ts0, ts0 + BAR)
        # VSS bar out over the ring's side (met1, VSS), via1 onto it
        side = (box(inner.left - GRW, tb0, inner.left, tb0 + BAR) if sgn > 0
                else box(inner.right, tb0, inner.right + GRW, tb0 + BAR))
        b.rect('m2', box(min(side.left, (t.strips[0].center().x - VW / 2)), tb0, max(side.right, (t.strips[-1].center().x + VW / 2)), tb0 + BAR))
        b.via('via1', side, enc=(0.085, 0.085))
        b.rect('m2', box((t.strips[0].center().x - VW / 2), ts0, (t.strips[-1].center().x + VW / 2), ts0 + BAR))
        # pair: S strips (even) -> s bar (low), D strips (odd) -> out bar (high)
        ps0 = p.diff.bottom + 0.2
        po0 = p.diff.top - 0.2 - BAR
        for k, st in enumerate(p.strips):
            if k % 2 == 0:
                via_strip(st, ps0, ps0 + BAR)
            else:
                via_strip(st, po0, po0 + BAR)
        b.rect('m2', box((p.strips[0].center().x - VW / 2), ps0, (p.strips[-1].center().x + VW / 2), ps0 + BAR))
        xs = x_spine if sgn > 0 else mx(x_spine)
        b.rect('m2', box(min((p.strips[0].center().x - VW / 2), xs), po0, max((p.strips[-1].center().x + VW / 2), xs), po0 + BAR))
        b.label('m2', box((p.strips[0].center().x - VW / 2), ps0, (p.strips[-1].center().x + VW / 2), ps0 + BAR), src)
        out[s] = dict(xs=xs, po0=po0, ts0=ts0, ps0=ps0, t=t, p=p, r=r, src=src, onet=onet, sgn=sgn)

    # load resistors: top head -> VDD (met2 riser), bottom head -> out spine (met2 jog)
    y_ch = inner.top + GRW + 0.4                         # channel bottom (met1 tracks)
    trk = [y_ch + k * 0.7 for k in range(3)]             # 0.4 tall tracks at 0.7 pitch
    plate_top = RAIL_H + BOT_PLATE_SPACE + CAPW + 2 * e  # plates start 1.2 um above the VSS rail
    y_vdd = max(trk[-1] + 0.4 + 0.5, plate_top + BOT_PLATE_SPACE)
    b.stack(box(0, y_vdd, W, y_vdd + RAIL_H), 'm1', 'm3')
    b.pin('m1', box(0, y_vdd, 1.0, y_vdd + RAIL_H), 'VDD')
    for s in 'pn':
        o = out[s]
        r = o['r']
        bot, top_ = r.heads[0][0], r.heads[0][1]
        xc = top_.center().x
        vb = box(xc - 0.15, top_.top - 0.45, xc + 0.15, top_.top - 0.05)
        b.via('via1', vb, enc=(0.075, 0.085))
        b.rect('m2', box(vb.left, vb.bottom, vb.right, y_vdd + 0.01))
        xb = bot.center().x
        vo = box(xb - 0.15, bot.bottom + 0.05, xb + 0.15, bot.bottom + 0.45)
        b.via('via1', vo, enc=(0.075, 0.085))
        xs = o['xs']
        b.rect('m2', box(min(vo.left, xs - 0.15), vo.bottom, max(vo.right, xs + 0.15), vo.top))
        # out spine: from the Rl jog up past the pair's out bar to its channel track
        o['spine'] = (vo.bottom, xs)
    # channel tracks (met1): 0 = inp (left) + outp (right), 1 = inn (to the left edge), 2 = outn (to the right)
    def track(k, xa, xb, net):
        bb = b.rect('m1', box(xa, trk[k], xb, trk[k] + 0.4))
        b.label('m1', bb, net)
        return bb

    def riser(x, y0, k):
        """met2 riser at x from y0 up to track k, with via1 onto the track."""
        b.rect('m2', box(x - 0.15, y0, x + 0.15, trk[k] + 0.4))
        b.via('via1', box(x - 0.15, trk[k], x + 0.15, trk[k] + 0.4), enc=(0.075, 0.085))

    def edge_pin(k, x0, x1, net):
        pb = box(x0, trk[k], x1, trk[k] + 0.4)
        b.rect('m2', pb)
        b.via('via1', pb, enc=(0.085, 0.085))
        b.pin('m2', pb, net)

    # gates: met1 strap over the pair's pads, a met2 riser up to its track
    for s, k in (('p', 0), ('n', 1)):
        p = out[s]['p']
        gy0, gy1 = min(q.bottom for q in p.pads), max(q.top for q in p.pads)
        gy1 = max(gy1, gy0 + 0.32)
        b.rect('m1', box(p.pads[0].left, gy0, p.pads[-1].right, gy1))
        xr = p.pads[0].left + 0.15 if s == 'p' else p.pads[-1].right - 0.15
        b.via('via1', box(xr - 0.15, gy0, xr + 0.15, gy1), enc=(0.075, 0.085))
        riser(xr, gy0, k)
        out[s]['gx'] = xr
    track(0, 0, out['p']['gx'] + 0.15, 'inp')
    track(1, 0, out['n']['gx'] + 0.15, 'inn')
    edge_pin(0, 0, 0.6, 'inp')
    edge_pin(1, 0, 0.6, 'inn')
    # outputs: spine from the Rl jog up to the track
    for s, k in (('p', 2), ('n', 0)):
        y0, xs = out[s]['spine']
        riser(xs, y0, k)
    track(2, out['p']['xs'] - 0.15, W, 'outn')
    track(0, out['n']['xs'] - 0.15, W, 'outp')
    edge_pin(2, W - 0.6, W, 'outn')
    edge_pin(0, W - 0.6, W, 'outp')

    # MIMs: Cs_a over the p half (bottom sp), Cs_b over the n half (bottom sn)
    cy0 = RAIL_H + BOT_PLATE_SPACE                       # plate bottom: 1.2 um above the VSS rail's met3
    caps = {'p': box(x_dev + e, cy0 + e, x_dev + e + CAPW, cy0 + e + CAPW)}
    caps['n'] = box(mx(caps['p'].right), caps['p'].bottom, mx(caps['p'].left), caps['p'].top)
    for s in 'pn':
        o = out[s]
        c = caps[s]
        bot = box(c.left - e, c.bottom - e, c.right + e, c.top + e)
        o['plate'] = bot
        # the plate reaches its half's s through a met3 tab out to the drop column (same net;
        # no via2 may sit under capm, capm.8)
        o['tab'] = bot
    # top plates: met4 strips across to the far edge, drop columns (met3) to that half's s bar
    hi = (caps['p'].top - 1.3, caps['p'].top - 0.15)
    lo = (caps['p'].bottom + 0.15, caps['p'].bottom + 1.3)
    for s, other, (sy0, sy1) in (('p', 'n', hi), ('n', 'p', lo)):
        c = caps[s]
        o = out[other]                                  # the plate's top is the other half's s
        xd0 = edge if o['sgn'] > 0 else W - edge - drop_w
        strip = box(min(c.left, xd0), sy0, max(c.right, xd0 + drop_w), sy1)
        mim(b, c, strip)
        b.rect('m4', strip)
        # drop column: met3 from the strip down to the s bar's level (tail's), via3 at the top
        ybar = o['ts0']
        col = box(xd0, min(ybar, sy0), xd0 + drop_w, max(ybar + BAR, sy1))
        b.rect('m3', col)
        b.via('via3', box(xd0, sy0, xd0 + drop_w, sy1))
        b.via('via2', box(xd0, ybar, xd0 + drop_w, ybar + BAR), enc=(0.085, 0.04))
        # the tail's and the pair's s bars (met2) out to the column, via2 there
        t, p = o['t'], o['p']
        for yb_, f in ((ybar, t), (o['ps0'], p)):
            b.rect('m2', box(min((f.strips[0].center().x - VW / 2), xd0), yb_, max((f.strips[-1].center().x + VW / 2), xd0 + drop_w), yb_ + BAR))
            b.via('via2', box(xd0, yb_, xd0 + drop_w, yb_ + BAR), enc=(0.085, 0.04))
        col = box(xd0, min(col.bottom, o['ps0']), xd0 + drop_w, max(col.top, o['ps0'] + BAR))
        b.rect('m3', col)
        # this half's own plate: a met3 tab from its outer edge to the column (same net)
        pl = o['plate']
        ty0, ty1 = pl.bottom + 2.0, pl.bottom + 3.0
        b.rect('m3', box(xd0, ty0, pl.left, ty1) if o['sgn'] > 0 else box(pl.right, ty0, xd0 + drop_w, ty1))
        col = box(xd0, min(col.bottom, ty0), xd0 + drop_w, max(col.top, ty1))
        b.rect('m3', col)
    print(f'amp_dpc: {W:.2f} x {y_vdd + RAIL_H:.2f} um; cap {CAPW} um, Rl {LRL:.3f} um')
    return b


if __name__ == '__main__':
    make().write(os.path.join(REPO, 'layout', 'amp_dpc.gds'))
    write_ref('amp_dpc', 'amp_dpc', dict(PARAMS, sqrt=math.sqrt))     # sqrt: the MIM side expression
    ref = os.path.join(REPO, 'layout', 'ref', 'amp_dpc.spice')
    lines = open(ref).read().split('\n')
    lines[0] = f'* amp_dpc: xschem/amp_dpc.sch with {PARAMS} (lay.write_ref)'
    open(ref, 'w').write('\n'.join(lines))
