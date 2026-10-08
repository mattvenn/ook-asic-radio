# amp_dp layout: chain stage 1 (xschem/gen/chain.py:amp_dp), lna_chain's sizing
# w=80 l=0.15 rl=1k wt=6 mt=20:
#   Mp / Mn  nfet W 80 L 0.15 (schematic nf 4): D outn / outp, G inp / inn, S tail
#   Mtail    nfet 20 x (W 6 nf 2) L 0.5: D tail, G nb, S VSS (drawn as 2 x nf 20, 3 um fingers,
#            the reference diode's finger width, so the mirror ratio holds)
#   Rl_p / Rl_n res_high_po_1p41 L 3.14 um: VDD -> outn / outp
# 1.2 mA tail, 0.6 mA per side (tail = mt x iref, iref 60 uA). Sized at 2x the tech-LEF
# limits: tail net 1.2 mA (met2 bar 1.0 um, 3 x 0.4 um met2 links to the pair), each out
# 0.6 mA (>= 5 via1), VSS straight down the tail's source strips into the ring / rail.
#
# Gate fingers: the schematic's 4 x 20 um fingers would be ~530 Ohm of gate per finger
# (poly ~48 Ohm/sq, contacted one end), far above 1/gm (~110 Ohm per side): drawn as 16 x
# 5 um per side instead (same W and L; netgen adds parallel fingers).
# Matching (stage 1 has DC gain; its offset goes down the chain): the pair is 4 groups of
# 8 fingers, A B B A (A = Mp, B = Mn), one orientation, sources all on the tail.
#
# Floorplan: VSS rail (met1+2+3) / p-tap ring round everything / VDD rail.
#   In the ring: the tail row (2 x nf 20, gates up to the nb strap; source strips down
#   into the ring's bottom side); above it the pair row (A B B A, gates up), with Rl_p
#   left of it and Rl_n right of it (mirror pair). Over the pair, met2 bars: tail (low,
#   all source strips), outp (middle, B drains), outn (high, A drains). The A gate straps
#   join by a met2 jumper over the B strap; inp and inn leave left on met3.
#   Outputs: each bar out to its load's bottom head, via2 to met3, met3 tracks along the
#   top to the right edge. nb leaves on met2 at both edges.
# Run: tools/osic klayout -b -r layout/gen/amp_dp.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, REPO, box, ring, write_ref, cuts_needed   # noqa: E402
from passives import PolyRes   # noqa: E402

PARAMS = dict(w=80, l=0.15, rl=1e3, wt=6, mt=20, mm=0)
LRL = (PARAMS['rl'] - 278) / 230.3
NG, NFG = 4, 8                     # pair: 4 groups of 8 fingers (A B B A)
WF = PARAMS['w'] / (NG // 2 * NFG)  # 5 um fingers
RAIL_H = 1.5
GRW = 0.4
VW = 0.3


def make():
    b = Block('amp_dp')
    nt = PARAMS['mt'] * 2 // 2                        # tail fingers per device (2 devices)
    tails = [Fet(b, 'n', 3.0 * nt, 0.5, nf=nt, gate='top', vt='', bulk='None') for _ in range(2)]
    groups = [Fet(b, 'n', WF * NFG, PARAMS['l'], nf=NFG, gate='top', vt='', bulk='None') for _ in range(NG)]
    side = ['A', 'B', 'B', 'A']
    rl = {s: PolyRes(b, LRL, 1, w=1.41, typ='sky130_fd_pr__res_high_po_1p41', pad_w=1.2) for s in 'pn'}
    rlw = rl['p']._bbox.width()

    x0 = GRW + 0.45 + 0.6                            # ring hole left = 0.6 + GRW
    y_in = RAIL_H + GRW                              # ring hole bottom
    # tail row
    t0 = tails[0]
    y_t = y_in + 0.47
    x = x0
    for f in tails:
        f.place(x, y_t).commit()
        x = f.diff.right + 0.9
    tail_r = tails[-1].diff.right
    # pair row: centred over the tail row, Rl either side
    gw = groups[0].diff.width()
    pw = NG * gw + (NG - 1) * 0.9
    pad_rise = max(q.top for q in t0.pads) - t0.diff.top
    y_p = y_t + t0.diff.height() + pad_rise + 1.6
    xp = (x0 + tail_r) / 2 - pw / 2
    for f in groups:
        f.place(xp, y_p).commit()
        xp = f.diff.right + 0.9
    pl, pr = groups[0].diff.left, groups[-1].diff.right
    # loads: beside the pair, bottom heads level with the pair's bottom
    yr = y_p - 0.2
    rl['p'].place(pl - 1.6 - rlw + (rl['p']._poly.left - rl['p']._bbox.left), yr - rl['p']._bbox.bottom + rl['p']._poly.bottom)
    rl['n'].place(pr + 1.6 + (rl['n']._poly.left - rl['n']._bbox.left), yr - rl['n']._bbox.bottom + rl['n']._poly.bottom)
    gp_top = max(q.top for f in groups for q in f.pads)
    inner = box(min(x0 - 0.45, rl['p'].bbox.left - 0.6), y_in,
                max(tail_r + 0.45, rl['n'].bbox.right + 0.6), max(gp_top + 2.2, rl['p'].bbox.top + 0.6))
    ring(b, inner, 'p', GRW)
    # channel above the ring: met3 out tracks, then the VDD rail
    y_ch = inner.top + GRW + 0.3
    trk = {'outp': (y_ch, y_ch + 0.6), 'outn': (y_ch + 0.9, y_ch + 1.5)}
    y_vdd = y_ch + 1.5 + 0.5
    W = inner.right + GRW + 0.6
    b.stack(box(0, 0, W, RAIL_H), 'm1', 'm3')
    b.stack(box(0, y_vdd, W, y_vdd + RAIL_H), 'm1', 'm3')
    b.rect('m1', box(inner.left - GRW, RAIL_H - 0.01, inner.right + GRW, y_in))       # ring onto VSS
    b.pin('m1', box(0, 0, 1.0, RAIL_H), 'VSS')
    b.pin('m1', box(0, y_vdd, 1.0, y_vdd + RAIL_H), 'VDD')

    def land(s, y0, y1):
        xc = s.center().x
        bb = box(xc - VW / 2, y0, xc + VW / 2, y1)
        b.rect('m1', bb)
        return b.via('via1', bb, enc=(0.075, 0.085))

    def span(f):
        return f.strips[0].center().x - VW / 2, f.strips[-1].center().x + VW / 2

    report = []
    # tail: source strips (even) down into the ring's bottom side; drains (odd) -> tail bar
    tb = (t0.diff.top - 0.15 - 1.0, t0.diff.top - 0.15)
    n_t = 0
    for f in tails:
        for k, s in enumerate(f.strips):
            if k % 2 == 0:
                b.rect('m1', box(s.center().x - 0.15, y_in - 0.01, s.center().x + 0.15, s.top))
            else:
                n_t += land(s, *tb)
    b.rect('m2', box(span(tails[0])[0], tb[0], span(tails[-1])[1], tb[1]))
    report.append(('tail', 'tail drains', n_t, cuts_needed(1.2, 'via1')))
    # nb: met1 strap over all tail pads, met2 out at both edges
    pads = [q for f in tails for q in f.pads]
    ny0, ny1 = min(q.bottom for q in pads), max(q.top for q in pads)
    ny1 = max(ny1, ny0 + 0.32)
    b.rect('m1', box(min(q.left for q in pads), ny0, max(q.right for q in pads), ny1))
    for xa in (min(q.left for q in pads), max(q.right for q in pads) - 0.5):
        b.via('via1', box(xa, ny0, xa + 0.5, ny1), enc=(0.085, 0.055))
    b.rect('m2', box(0, ny0, min(q.left for q in pads) + 0.5, ny1))
    b.rect('m2', box(max(q.right for q in pads) - 0.5, ny0, W, ny1))
    b.pin('m2', box(0, ny0, 0.5, ny1), 'nb')
    b.pin('m2', box(W - 0.5, ny0, W, ny1), 'nb')

    # pair: three bars over the fingers (5 um): tail (sources) low, outp middle, outn high
    g0 = groups[0]
    yb = {'tail': (g0.diff.bottom + 0.15, g0.diff.bottom + 0.15 + 1.0),
          'outp': (g0.diff.bottom + 1.55, g0.diff.bottom + 2.15),
          'outn': (g0.diff.bottom + 2.6, g0.diff.bottom + 3.2)}
    cnt = {'tail': 0, 'outp': 0, 'outn': 0}
    for f, sd in zip(groups, side):
        dnet = 'outn' if sd == 'A' else 'outp'
        for k, s in enumerate(f.strips):
            net = 'tail' if k % 2 == 0 else dnet
            cnt[net] += land(s, *yb[net])
    L, R = span(groups[0])[0], span(groups[-1])[1]
    b.rect('m2', box(L, yb['tail'][0], R, yb['tail'][1]))
    b.label('m2', box(L, yb['tail'][0], R, yb['tail'][1]), 'tail')
    # tail links: met2 from the tail row's bar up to the pair's tail bar (over the nb strap)
    for xc in (L + 1.0, (L + R) / 2, R - 1.0):
        b.rect('m2', box(xc - 0.2, tb[0], xc + 0.2, yb['tail'][1]))
    report.append(('tail', 'pair sources', cnt['tail'], cuts_needed(1.2, 'via1')))
    # out bars: outp over the B groups out to Rl_n (right), outn over everything out to Rl_p (left)
    bl = span(groups[1])[0]
    b.rect('m2', box(bl, yb['outp'][0], rl['n'].ends[0].right, yb['outp'][1]))
    b.rect('m2', box(rl['p'].ends[0].left, yb['outn'][0], R, yb['outn'][1]))
    report.append(('outp', 'B drains', cnt['outp'], cuts_needed(0.6, 'via1')))
    report.append(('outn', 'A drains', cnt['outn'], cuts_needed(0.6, 'via1')))
    # loads: bottom head (met1, widened) -> via1 to its bar; top head -> met2 riser to VDD
    for s_, net in (('p', 'outn'), ('n', 'outp')):
        r = rl[s_]
        bot, top_ = r.heads[0][0], r.heads[0][1]
        y0, y1 = yb[net]
        # via1 over the whole bottom head; met2 from it up to the bar
        nv = b.via('via1', bot, enc=(0.085, 0.085))
        b.rect('m2', box(bot.left, bot.bottom, bot.right, max(bot.top, y1)))
        nv2 = b.via('via1', top_, enc=(0.085, 0.085))
        b.rect('m2', box(top_.left, top_.bottom, top_.right, y_vdd + 0.01))
        report.append((net, f'Rl_{s_} heads', min(nv, nv2), cuts_needed(0.6, 'via1')))
    # outputs to met3 on the right of the pair only (the left stays free of met3 for inn):
    # outn's riser between the pair and Rl_n, outp's beyond Rl_n
    hp = rl['n'].ends[0]
    for net, xo in (('outn', (R + 0.4, R + 1.2)), ('outp', (hp.right + 0.3, hp.right + 1.1))):
        y0, y1 = yb[net]
        b.rect('m2', box(R if net == 'outn' else hp.left, y0, xo[1], y1))
        ob = box(xo[0], y0, xo[1], y1 + 0.8)             # taller landing: >= 3 via2
        b.rect('m2', ob)
        n2 = b.via('via2', ob, enc=(0.065, 0.065))
        ty = trk[net]
        b.rect('m3', box(ob.left, y0, ob.right, ty[1]))
        b.rect('m3', box(ob.left, ty[0], W, ty[1]))
        b.pin('m3', box(W - 0.5, ty[0], W, ty[1]), net)
        report.append((net, 'to met3', n2, cuts_needed(0.6, 'via2')))
    # gates: A straps (groups 0, 3) joined by a met2 jumper, out to the left (inp);
    # B strap (groups 1, 2): via1 + via2, met3 up over the jumper and out to the left (inn)
    gy0 = min(q.bottom for f in groups for q in f.pads)
    gy1 = max(max(q.top for f in groups for q in f.pads), gy0 + 0.32)
    straps = []
    for gi in ((0,), (1, 2), (3,)):
        fs = [groups[i] for i in gi]
        straps.append(b.rect('m1', box(fs[0].pads[0].left, gy0, fs[-1].pads[-1].right, gy1)))
    yj = (gy1 + 0.35, gy1 + 0.85)
    for st in (straps[0], straps[2]):
        xc = st.center().x
        v = box(xc - 0.25, gy0, xc + 0.25, gy1)
        b.via('via1', v, enc=(0.085, 0.085))
        b.rect('m2', box(v.left, gy0, v.right, yj[1]))
    # the jumper stays between the A straps (met2 further left would cross Rl_p's VDD riser);
    # inp leaves on met3 from the left strap's riser
    x0j = straps[0].center().x
    b.rect('m2', box(x0j - 0.25, yj[0], straps[2].center().x + 0.25, yj[1]))
    b.via('via2', box(x0j - 0.25, yj[0], x0j + 0.25, yj[1]), enc=(0.065, 0.065))
    b.rect('m3', box(0, yj[0], x0j + 0.25, yj[1]))
    b.pin('m3', box(0, yj[0], 0.5, yj[1]), 'inp')
    b.label('m1', straps[0], 'inp')
    xc = straps[1].center().x
    v = box(xc - 0.25, gy0, xc + 0.25, gy1)
    b.via('via1', v, enc=(0.085, 0.085))
    b.rect('m2', v)
    b.via('via2', v, enc=(0.065, 0.06))
    yi = (yj[1] + 0.4, yj[1] + 0.9)
    b.rect('m3', box(v.left, gy0, v.right, yi[1]))
    b.rect('m3', box(0, yi[0], v.right, yi[1]))
    b.pin('m3', box(0, yi[0], 0.5, yi[1]), 'inn')
    assert yi[1] + 0.3 <= inner.top + GRW, (yi, inner)          # stays inside / under the ring top
    print(f'amp_dp: {W:.2f} x {y_vdd + RAIL_H:.2f} um; fingers {WF} um x {NG * NFG} (pair), 3 um x {2 * nt} (tail)')
    print('  net    where          cuts  need (2x margin)')
    for net, where, n, need in report:
        print(f'  {net:6s} {where:14s} {n:4d}  {need}{"   <-- short" if n < need else ""}')
    return b


if __name__ == '__main__':
    make().write(os.path.join(REPO, 'layout', 'amp_dp.gds'))
    write_ref('amp_dp', 'amp_dp', PARAMS)
