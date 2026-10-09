# lna_chain layout (xschem/gen/chain.py:lna_chain), CHAIN_PARAMS w1=80 rl1=1k mt1=20 w2=20
# rl2=4k mt2=6 cs=0.6p cin=2p rb=20k: input coupling (Cin_p/n 2 pF MIM, ~31 um square,
# bottom plate on the pad side; Rb_p/n 20k high_po_0p35 from vcm to the gates), the
# reference diode Mref (W 6 nf 2 / L 0.5, ibias = every stage's nb), then amp_dp and
# 5 x amp_dpc (the finished cell layouts, read in as subcells).
#
# Folded in two (a U), for the tile floorplan (docs/floorplan_spec.md "Chosen floorplan").
# Own frame (placed R180 in the tile, so the front row is at the bottom over the RX pads):
#   front row (top): the input section (Cin_p, Cin_n side by side; Mref and the Rb pair in
#     a p-tap ring under them; the top plates drop on met3 just right of Cin_n to amp_dp's
#     inp / inn), amp_dp (st1), amp_dpc (st2), flowing east. The two stages are mirrored
#     top-bottom (MX), so their in / out wiring and VDD rail run along the moat: the o1 tap
#     and the start of the turn are short. Built in its own frame (front()), then placed at
#     Y_F and flattened one level.
#   turn (east edge): o2 from st2's outputs (moat side) down to st3's inputs (~35 um, met2);
#     nb beside it; the o1 tap comes along the moat and down the same channel. Then a VSS
#     column (met1) and a VDD column (met3): the only places the two rows' rails meet (the
#     tile's VDPWR / VGND straps are over this end).
#   moat (MOAT um): a p-tap ring tied to VSS at the VSS column only, with an n-well stripe
#     (n-tap ring to VDD) inside it. The rows' own rails don't touch it.
#   back row (bottom): st3..st6, amp_dpc rotated 180 (inputs east, VSS rail on the moat side),
#     flowing west, with the in / out wiring and the taps along the bottom edge (toward
#     log_det). st5 / st6 end up across the moat from the Cin plates (passives), st3 / st4
#     across from st2 / st1.
#   (Both rows' wiring on the moat side, v2, made the turn ~21 um but needed ~17 um met4 drops
#   for the back-row taps: worse overall. Both on the outer edges, v1, made the turn ~50 um.)
# Isolation rule (sim/chain/stability.sh): <= 0.1 fF asymmetric output -> input coupling at
# ss 10 C (aim <= 0.05 fF), where the input is the pads, Cin, g1, Rb, stage 1 and o1. The
# budget grows ~4.5x per stage back from the output (stages ~13 dB apart).
# Pins: inp / inn (the pad-side plates, met3, top edge, over ua[0] / ua[1] once placed with
# its tile-east edge at TILE_RIGHT), vcm and ibias (met2, west edge, toward bias_gen), taps
# o1..o5 (met2: o1 / o2 at the bottom of the turn channel, o3..o5 in the back-row gaps),
# outp / outn (met2, west end of the back row), VSS (met1) and VDD (met3) on the east columns.
# Rb_p / Rb_n are single segments (one segment = exactly the schematic's end resistance),
# side by side so their RPM regions merge (a lone 0.35 um segment fails magic rpm.1).
# Run: tools/osic klayout -b -r layout/gen/lna_chain.py
import math
import os
import re
import subprocess
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pya                                                          # noqa: E402
from lay import Block, Fet, REPO, box, ring, snap, _si             # noqa: E402
from passives import PolyRes, mim, CAPM_ENC_M3, BOT_PLATE_SPACE   # noqa: E402

PARAMS = dict(w1=80, rl1=1e3, mt1=20, w2=20, rl2=4e3, mt2=6, cs=0.6e-12, cin=2e-12, rb=20e3, mm=0)
CINW = snap(math.sqrt(PARAMS['cin'] / 2.06e-15))
LRB = (PARAMS['rb'] - 963) / 995
NST = 6
GAP = 2.0
RAIL_H = 1.5
GRW = 0.4
MOAT = 14.0
TILE_RIGHT = 158.5                     # the block's tile-east edge (its own x = 0) in the tile
UA = {'inp': 136.62, 'inn': 117.30}    # ua[0] / ua[1] pad centres, tile x


def pins_of(cell, ly):
    """{name: [boxes]} from a cell's pin shapes (xx/16) and labels (xx/5)."""
    out = {}
    for lay in (68, 69, 70, 71):
        li, pi = ly.find_layer(lay, 5), ly.find_layer(lay, 16)
        if li is None or pi is None:
            continue
        boxes = [s.dbbox() for s in cell.shapes(pi).each()]
        for s in cell.shapes(li).each():
            if s.is_text():
                p = s.dtext.position()
                for bb in boxes:
                    if bb.contains(p):
                        out.setdefault(s.dtext.string, []).append((lay, bb))
    return out


def front(b, cells, pin):
    """The front row (input section, st1, st2) in its own frame. The stages are mirrored
    top-bottom (MX), so their in / out wiring and VDD rail are along the bottom (the moat)."""
    W1, H1 = cells['amp_dp'].dbbox().width(), cells['amp_dp'].dbbox().height()
    Hc = cells['amp_dpc'].dbbox().height()
    T = {}

    def pb(cell, net, side=None):
        """pin box of the placed cell's net (side 'L' / 'R': the one at that edge)."""
        cands = sorted((bb.transformed(T[cell]) for _, bb in pin[cell][net]), key=lambda q: q.left)
        return cands[0] if side in (None, 'L') else cands[-1]

    # ---- input section
    e = CAPM_ENC_M3
    plate = CINW + 2 * e
    xc0 = 0.6                                           # Cin_p plate left
    cp = box(xc0 + e, RAIL_H + BOT_PLATE_SPACE + e, xc0 + e + CINW, RAIL_H + BOT_PLATE_SPACE + e + CINW)
    cn = cp.moved(pya.DVector(plate + 1.6, 0))
    pl_n_right = cn.right + e
    x_a = pl_n_right + BOT_PLATE_SPACE                  # drop column to amp_dp's lower input
    x_b = x_a + 0.5 + 0.3                               # drop column to its upper input
    x_dp = x_b + 0.5 + 1.2                              # amp_dp origin
    xs = [x_dp, x_dp + W1 + GAP]
    T['amp_dp'] = pya.DCplxTrans(1, 0, True, x_dp, H1)
    T['amp_dpc'] = pya.DCplxTrans(1, 0, True, xs[1], Hc)
    b.place(cells['amp_dp'], x_dp, H1, mirror=True)
    b.place(cells['amp_dpc'], xs[1], Hc, mirror=True)
    # VSS rail along the input section; it stops short of amp_dp's VDD rail (now at the
    # bottom) and a met1 link takes it up to amp_dp's VSS rail (now at the top)
    b.stack(box(0, 0, x_dp - 0.6, RAIL_H), 'm1', 'm3')
    vs1 = pb('amp_dp', 'VSS')
    b.rect('m1', box(x_dp - 1.0, 0, x_dp - 0.6, vs1.top))
    b.rect('m1', box(x_dp - 1.0, vs1.bottom, x_dp + 0.5, vs1.top))

    # Mref + Rb pair in a p-tap ring under the caps
    y_in = RAIL_H + GRW
    mref = Fet(b, 'n', 6.0, 0.5, nf=2, gate='top', vt='', bulk='None')
    mref.place(1.5, y_in + 0.47).commit()
    rbs = [PolyRes(b, LRB, 1, typ='sky130_fd_pr__res_high_po_0p35') for _ in range(2)]
    xr = mref.diff.right + 2.0
    for k, r in enumerate(rbs):
        r.place(xr + k * r.pitch - (r._bbox.left - r._poly.left), y_in + 0.6 - r._bbox.bottom + r._poly.bottom)
    inner = box(0.6 + GRW, y_in, rbs[-1].bbox.right + 0.6, max(rbs[0].bbox.top, mref.diff.top + 1.5) + 0.6)
    ring(b, inner, 'p', GRW)
    b.rect('m1', box(inner.left - GRW, RAIL_H - 0.01, inner.right + GRW, y_in))
    # Mref: sources down into the ring; gate strap + drain (via1, met2) = ibias
    s0, sd, s2 = mref.strips
    for s in (s0, s2):
        b.rect('m1', box(s.center().x - 0.15, y_in - 0.01, s.center().x + 0.15, s.top))
    gy0 = min(q.bottom for q in mref.pads)
    gy1 = max(max(q.top for q in mref.pads), gy0 + 0.32)
    b.rect('m1', box(mref.pads[0].left, gy0, mref.pads[-1].right, gy1))
    # ibias at amp_dp's nb height
    nb_dp = pb('amp_dp', 'nb', 'L')
    yi0, yi1 = nb_dp.bottom, nb_dp.top
    dx = sd.center().x
    dv = box(dx - 0.15, mref.diff.top - 1.0, dx + 0.15, mref.diff.top - 0.2)
    b.rect('m1', dv)
    b.via('via1', dv, enc=(0.075, 0.085))
    gv = box(mref.pads[0].left, gy0, mref.pads[0].left + 0.5, gy1)
    b.via('via1', gv, enc=(0.085, 0.085))
    b.rect('m2', box(dv.left, dv.bottom, dv.right, yi1))
    b.rect('m2', box(gv.left, min(gv.bottom, yi0), gv.right, max(gv.top, yi1)))
    b.rect('m2', box(0, yi0, x_dp + 0.5, yi1))
    b.pin('m2', box(0, yi0, 0.5, yi1), 'ibias')
    # Rb: bottom heads joined (vcm, met2 to the left edge, below ibias); top heads -> g1p / g1n
    (bp, tp), (bn, tn) = rbs[0].heads[0], rbs[1].heads[0]
    b.rect('m1', box(bp.left, bp.bottom, bn.right, bp.bottom + 0.4))
    vv = box(bp.left, bp.bottom, bp.right, bp.bottom + 0.4)
    b.via('via1', vv, enc=(0.055, 0.085))
    yv0, yv1 = vv.bottom, vv.top
    assert yv1 + 0.3 <= yi0, (yv1, yi0)
    b.rect('m2', box(0, yv0, vv.right, yv1))
    b.pin('m2', box(0, yv0, 0.5, yv1), 'vcm')
    # the drop columns: x_a (nearer the caps) to amp_dp's lower input pin, x_b to the upper
    # one, so the lower pin's met3 run passes under the end of the other column
    in_dp, inn_dp = pb('amp_dp', 'inp', 'L'), pb('amp_dp', 'inn', 'L')
    col = {'p': x_a, 'n': x_b} if in_dp.bottom < inn_dp.bottom else {'p': x_b, 'n': x_a}
    # g1p from Rb_p: up 1 um above the heads, then right to its column; g1n from Rb_n at head level
    hp = box(tp.left, tp.top - 0.45, tp.right, tp.top - 0.05)
    hn = box(tn.left, tn.top - 0.45, tn.right, tn.top - 0.05)
    for h in (hp, hn):
        b.via('via1', h, enc=(0.055, 0.085))
    yg_p = (hp.top + 0.6, hp.top + 1.0)
    b.rect('m2', box(hp.left, hp.bottom, hp.right, yg_p[1]))
    b.rect('m2', box(hp.left, yg_p[0], col['p'] + 0.5, yg_p[1]))
    b.rect('m2', box(hn.left, hn.bottom, col['n'] + 0.5, hn.top))
    b.label('m2', hp, 'g1p')
    b.label('m2', hn, 'g1n')
    # the caps, top plates by met4 strips to the drop columns
    st_p = (cp.top - 1.3, cp.top - 0.15)                 # Cin_p's strip high
    st_n = (cp.top - 2.9, cp.top - 1.75)                 # Cin_n's strip lower
    for c, (s0_, s1_), xcol, pinb, via_y in ((cp, st_p, col['p'], in_dp, yg_p),
                                             (cn, st_n, col['n'], inn_dp, (hn.bottom, hn.top))):
        ylo, yhi = pinb.bottom, pinb.top
        strip = box(c.left, s0_, xcol + 0.5, s1_)
        bot = mim(b, c, strip)
        b.rect('m4', strip)
        b.rect('m3', box(xcol, min(ylo, via_y[0]), xcol + 0.5, s1_))
        b.via('via3', box(xcol, s0_, xcol + 0.5, s1_))
        b.via('via2', box(xcol, via_y[0], xcol + 0.5, via_y[1]), enc=(0.065, 0.065))
        b.rect('m3', box(xcol, ylo, x_dp + 0.5, yhi))      # into amp_dp's pin (met3)
        # pad-side plate: a met3 tab up to the top edge (the pin), over its ua pad once placed
        name = 'inp' if c is cp else 'inn'
        xt = TILE_RIGHT - UA[name]
        assert bot.left + 1.5 <= xt <= bot.right - 1.5, (name, xt, bot)
        tab = box(xt - 1.0, bot.top - 0.5, xt + 1.0, bot.top + 1.0)
        b.rect('m3', tab)
        b.pin('m3', box(tab.left, tab.top - 0.5, tab.right, tab.top), name)

    # ---- st1 -> st2 (amp_dp: met3 out; amp_dpc: met2 in)
    xl, xr_ = xs[0] + W1, xs[1]
    for net in ('VDD', 'VSS'):                          # bridge the rails where the cells' bands overlap
        ql, qr = pb('amp_dp', net), pb('amp_dpc', net)
        y0, y1 = max(ql.bottom, qr.bottom), min(ql.top, qr.top)
        for lay in ('m1', 'm2', 'm3'):
            b.rect(lay, box(xl - 0.5, y0, xr_ + 0.5, y1))
    nl, nr = pb('amp_dp', 'nb', 'R'), pb('amp_dpc', 'nb', 'L')
    xm = (xl + xr_) / 2
    b.rect('m2', box(nl.left, nl.bottom, xm + 0.2, nl.top))
    b.rect('m2', box(xm - 0.2, min(nl.bottom, nr.bottom), xm + 0.2, max(nl.top, nr.top)))
    b.rect('m2', box(xm - 0.2, nr.bottom, nr.right, nr.top))
    # outputs: met3 to a via2 column each (p nearer st1), met2 to st2's input; after MX
    # outp sits above outn, so p's met2 runs above n's column and n's met2 starts right of p's
    o1 = {}
    for o, inn_, xv in (('outp', 'inp', xl + 0.6), ('outn', 'inn', xl + 1.4)):
        ob, ib = pb('amp_dp', o, 'R'), pb('amp_dpc', inn_, 'L')
        w = 0.3 if o == 'outp' else 0.2
        b.rect('m3', box(ob.left, ob.bottom, xv + w, ob.top))
        vb = box(xv - w, ob.bottom, xv + w, ob.top)
        b.rect('m2', vb)
        b.via('via2', vb, enc=(0.085 if w < 0.3 else 0.065, 0.065))
        b.rect('m2', box(xv - w, min(ob.bottom, ib.bottom), xv + w, max(ob.top, ib.top)))
        b.rect('m2', box(xv - w, ib.bottom, ib.right, ib.top))
        # the o1 tap: via3 up from amp_dp's met3 output track (it runs to the cell's right
        # edge, and amp_dp has no met4), a short met4 drop into the moat
        xd = xl - (1.35 if o == 'outp' else 0.55)
        d = box(xd - 0.25, ob.bottom, xd + 0.25, ob.top)
        b.rect('m3', d)
        b.via('via3', d)
        o1[o[-1]] = d
    return dict(x_dp=x_dp, xs=xs, W=xs[1] + cells['amp_dpc'].dbbox().width(), o1=o1, T2=T['amp_dpc'])


def make():
    b = Block('lna_chain')
    ly = b.ly
    opts = pya.LoadLayoutOptions()
    opts.cell_conflict_resolution = pya.LoadLayoutOptions.RenameCell
    cells = {}
    for name in ('amp_dp', 'amp_dpc'):
        ly.read(os.path.join(REPO, 'layout', name + '.gds'), opts)
        cells[name] = ly.cell(name)
        assert cells[name] is not None, name
    pin = {n: pins_of(c, ly) for n, c in cells.items()}
    Wc, Hc = cells['amp_dpc'].dbbox().width(), cells['amp_dpc'].dbbox().height()

    def pt(cell, net, trans, side=None):
        """pin box of cell's net through an instance transform (side: the left- / right-most)."""
        cands = sorted((bb.transformed(trans) for _, bb in pin[cell][net]), key=lambda q: q.left)
        return cands[0] if side in (None, 'L') else cands[-1]

    # ---- front row, built in its own frame and flattened in at Y_F
    Y_F = snap(Hc + MOAT)
    fb = Block('lna_front', ly)
    f = front(fb, cells, pin)
    inst = b.cell.insert(pya.DCellInstArray(fb.cell.cell_index(), pya.DTrans(pya.DVector(0, Y_F))))
    inst.flatten(1)
    ly.delete_cell(fb.cell.cell_index())
    Xe = f['W']                                          # east edge of st2 and st3
    T2 = pya.DCplxTrans(pya.DVector(0, Y_F)) * f['T2']   # st2

    # ---- back row: st3 (east) .. st6 (west), amp_dpc rotated 180: inputs east, VSS rail on
    # the moat side, in / out wiring and the taps along the bottom edge (toward log_det)
    Tb = []
    for k in range(4):
        xr = Xe - k * (Wc + GAP)
        b.place(cells['amp_dpc'], xr, Hc, rot=180)
        Tb.append(pya.DCplxTrans(1, 180, False, xr, Hc))
    x_west = Xe - 4 * Wc - 3 * GAP
    vss_b = (Hc - RAIL_H, Hc)
    vdd_b = (0, RAIL_H)
    for k in range(3):                                   # gap between stage 3+k (east) and 4+k (west)
        xl = Xe - k * (Wc + GAP) - Wc - GAP              # west cell's right edge
        xr = xl + GAP                                    # east cell's left edge
        xm = (xl + xr) / 2
        for lay in ('m1', 'm2', 'm3'):
            b.rect(lay, box(xl - 0.5, vss_b[0], xr + 0.5, vss_b[1]))
            b.rect(lay, box(xl - 0.5, vdd_b[0], xr + 0.5, vdd_b[1]))
        nl = pt('amp_dpc', 'nb', Tb[k + 1], 'R')
        nr = pt('amp_dpc', 'nb', Tb[k], 'L')
        b.rect('m2', box(nl.left, min(nl.bottom, nr.bottom), nr.right, max(nl.top, nr.top)))
        s = 3 + k
        for o, inn_ in (('outp', 'inp'), ('outn', 'inn')):
            ob = pt('amp_dpc', o, Tb[k], 'L')            # east cell's output, at its left edge
            ib = pt('amp_dpc', inn_, Tb[k + 1], 'R')     # west cell's input, at its right edge
            b.rect('m2', box(xm - 0.2, ob.bottom, ob.right, ob.top))
            b.rect('m2', box(xm - 0.2, min(ob.bottom, ib.bottom), xm + 0.2, max(ob.top, ib.top)))
            b.rect('m2', box(ib.left, ib.bottom, xm + 0.2, ib.top))
            b.pin('m2', box(xm - 0.2, ib.bottom, xm + 0.2, ib.top), f'o{s}{o[-1]}')
    # last stage outputs: short stubs west, the pins
    for o in ('outp', 'outn'):
        ob = pt('amp_dpc', o, Tb[3], 'L')
        stub = box(ob.left - 1.0, ob.bottom, ob.right, ob.top)
        b.rect('m2', stub)
        b.pin('m2', box(stub.left, stub.bottom, stub.left + 0.5, stub.top), o)

    # ---- the turn channel, east of Xe (met2 verticals; rails cross it on met1 / met3).
    # st2's outn is below its outp (front row mirrored) and st3's inn below its inp: n takes
    # the inner column, and p's bottom run crosses it on met3, from a via just outside st3.
    c_o2 = {'n': (Xe + 0.9, Xe + 1.3), 'p': (Xe + 1.9, Xe + 2.3)}
    c_nb = (Xe + 2.8, Xe + 3.2)
    c_o1 = {'p': (Xe + 3.6, Xe + 4.0), 'n': (Xe + 4.3, Xe + 4.7)}
    c_vss, c_vdd = (Xe + 5.1, Xe + 6.1), (Xe + 6.4, Xe + 7.4)
    W = c_vdd[1]

    def cross_m3(pinb, cx):
        """met2 stub out of a st3 pin, via2 just outside the cell, met3 east to column cx, via2."""
        vin = box(Xe + 0.0, pinb.bottom, Xe + 0.5, pinb.top)
        b.rect('m2', box(pinb.left, pinb.bottom, vin.right, pinb.top))
        b.rect('m3', box(vin.left, pinb.bottom, cx[1], pinb.top))
        for v in (vin, box(cx[0], pinb.bottom, cx[1], pinb.top)):
            b.rect('m2', v)
            b.via('via2', v, enc=(0.085, 0.065))

    for o, inn_ in (('outp', 'inp'), ('outn', 'inn')):
        q = o[-1]
        ob, ib = pt('amp_dpc', o, T2, 'R'), pt('amp_dpc', inn_, Tb[0], 'R')
        cx = c_o2[q]
        b.rect('m2', box(ob.left, ob.bottom, cx[1], ob.top))
        b.rect('m2', box(cx[0], ib.bottom, cx[1], ob.top))
        if q == 'n':
            b.rect('m2', box(ib.left, ib.bottom, cx[1], ib.top))
        else:
            cross_m3(ib, cx)
        b.pin('m2', box(cx[0], ib.bottom, cx[1], ib.top), 'o2' + q)
    # nb: st2's right nb (top of the front row) -> st3's right nb (top of the back row), outside o2
    nt, nbk = pt('amp_dpc', 'nb', T2, 'R'), pt('amp_dpc', 'nb', Tb[0], 'R')
    b.rect('m2', box(nt.left, nt.bottom, c_nb[1], nt.top))
    b.rect('m2', box(c_nb[0], nbk.bottom, c_nb[1], nt.top))
    cross_m3(nbk, c_nb)
    # o1: short met4 drops from the front gap into the moat, met3 east along it, a met2 column
    # down to the back row's tap level
    y_o1 = {'p': Y_F - 3.0, 'n': Y_F - 4.5}
    for q, d in f['o1'].items():
        d = d.moved(pya.DVector(0, Y_F))
        y0 = y_o1[q]
        b.rect('m4', box(d.left, y0 - 0.3, d.right, d.top))
        pad = box(d.left, y0 - 0.3, d.right, y0 + 0.3)
        b.rect('m3', pad)
        b.via('via3', pad)
        cx = c_o1[q]
        b.rect('m3', box(d.left, y0 - 0.3, cx[1], y0 + 0.3))
        vb = box(cx[0], y0 - 0.3, cx[1], y0 + 0.3)
        b.rect('m2', vb)
        b.via('via2', vb, enc=(0.065, 0.04))
        yb = pt('amp_dpc', 'inp' if q == 'p' else 'inn', Tb[0], 'R').bottom
        b.rect('m2', box(cx[0], yb, cx[1], y0 + 0.3))
        b.pin('m2', box(cx[0], yb, cx[1], yb + 0.4), 'o1' + q)

    # ---- moat: p-tap ring (VSS, at the VSS column only) with an n-well / n-tap stripe (VDD)
    mo = box(0.125 + GRW, Hc + 0.4 + GRW, c_vss[1] - GRW, Y_F - 0.4 - GRW)   # ring inner (its psdm reaches x = 0)
    ring(b, mo, 'p', GRW)
    ni = box(mo.left + 1.1, mo.center().y - 1.4, Xe - 1.5, mo.center().y + 1.4)
    ring(b, ni, 'n', GRW)
    b.rect('nwell', box(ni.left - GRW - 0.4, ni.bottom - GRW - 0.4, ni.right + GRW + 0.4, ni.top + GRW + 0.4))
    yv = (ni.center().y - 0.5, ni.center().y + 0.5)
    tie = box(ni.right - 0.2, yv[0], ni.right + GRW + 0.2, yv[1])
    b.rect('m1', tie)
    b.rect('m2', tie)
    b.via('via1', tie)
    b.via('via2', tie, enc=(0.085, 0.065))
    b.rect('m3', box(tie.left, yv[0], c_vdd[1], yv[1]))

    # ---- supplies: each row's rails run to the east columns and meet only there
    fr_vss, fr_vdd = pt('amp_dpc', 'VSS', T2), pt('amp_dpc', 'VDD', T2)
    b.rect('m1', box(Xe - 0.5, fr_vss.bottom, c_vss[1], fr_vss.top))
    b.rect('m1', box(Xe - 0.5, vss_b[0], c_vss[1], vss_b[1]))
    b.rect('m1', box(c_vss[0], vss_b[0], c_vss[1], fr_vss.top))
    b.rect('m3', box(Xe - 0.5, fr_vdd.bottom, c_vdd[1], fr_vdd.top))
    b.rect('m3', box(Xe - 0.5, vdd_b[0], c_vdd[1], vdd_b[1]))
    b.rect('m3', box(c_vdd[0], vdd_b[0], c_vdd[1], fr_vdd.top))
    b.pin('m1', box(c_vss[0], vss_b[0], c_vss[1], vss_b[1]), 'VSS')
    b.pin('m3', box(c_vdd[0], fr_vdd.bottom, c_vdd[1], fr_vdd.top), 'VDD')

    H = b.cell.dbbox().height()
    print(f'lna_chain: {W:.2f} x {H:.2f} um (moat {MOAT}); front x_dp {f["x_dp"]:.2f}, st2 east edge {Xe:.2f}, '
          f'back row west end {x_west:.2f}; in the tile (R180): x {TILE_RIGHT - W:.2f}..{TILE_RIGHT}')
    return b


def write_ref():
    """LVS/PEX reference: xschem's lna_chain (LVS mode) with the chain parameters
    evaluated, its amp_dp / amp_dpc definitions replaced by layout/ref/amp_dp(c).spice
    (those carry the per-cell parameters) and the instances' parameters dropped."""
    tmp = os.path.join(REPO, 'build', 'lay', 'ref')
    os.makedirs(tmp, exist_ok=True)
    subprocess.run(['xschem', '-n', '-s', '-q', '--tcl', 'set top_subckt 1; set lvs_netlist 1', '-o', tmp,
                    'xschem/lna_chain.sch'], cwd=REPO, capture_output=True)
    src = open(os.path.join(tmp, 'lna_chain.spice')).read()
    src = re.sub(r'\n\+', ' ', src)
    for c in ('amp_dp', 'amp_dpc'):
        src = re.sub(rf'^\.subckt {c}\s.*?^\.ends[^\n]*\n', '', src, flags=re.S | re.M)
    env = dict(PARAMS, sqrt=math.sqrt, max=max)
    out = []
    for ln in src.splitlines():
        if ln.startswith('.subckt lna_chain'):
            ln = re.sub(r'\s+\w+=\S+', '', ln)
        if re.match(r'^xa\d', ln):
            ln = re.sub(r'\s+\w+=\S+', '', ln)
        ln = re.sub(r"(\w+)='([^']+)'", lambda m: f'{m.group(1)}={eval(_si(m.group(2)), {}, env):.6g}', ln)
        out.append(ln)
    for c in ('amp_dp', 'amp_dpc'):
        out.append(open(os.path.join(REPO, 'layout', 'ref', c + '.spice')).read())
    with open(os.path.join(REPO, 'layout', 'ref', 'lna_chain.spice'), 'w') as fh:
        fh.write(f'* lna_chain: xschem/lna_chain.sch with {PARAMS} (layout/gen/lna_chain.py)\n' + '\n'.join(out) + '\n')


if __name__ == '__main__':
    make().write(os.path.join(REPO, 'layout', 'lna_chain.gds'))
    write_ref()
