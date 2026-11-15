# amp_dpc_ts: stage 2 of the tall chain with the low-gain shunt (lna_shunt, xschem/gen/chain.py)
# built in: amp_dpc_t (layout/gen/amp_dpc_tall.py) plus, in the free space above each half's
# ring (under the Cs plates, as today's Rb / Mref sit under Cin):
#   top half:    Rh_a | Msw | Rh_b in a row. Msw (PMOS W 18 nf 6 / L 0.15, own n-tap ring on VDD)
#                sources -> sa bar -> Rh_a, drains -> sb bar -> Rh_b; Rh_b's free head lands on the
#                outn (o2n) tap column, Rh_a's on the outp (o2p) column, both on met2 / met3 islands;
#   bottom half: Mcap (PMOS W 5 / L 5, gi -> VDD) | Rg (xhigh 20k, gi <- lna_lo_n).
# gi crosses the centre on one more met4 column next to the outn column (the cell is 0.7 um
# wider than amp_dpc_t; the plates, caps and height are unchanged), and lna_lo_n comes in on
# the same column's lower segment from the cell's bottom edge (met4 pin). The loads' VDD
# risers jog to the left edge to free the space. Shunt values: lna_chain.py SHUNT (the same
# as today's chain).
# Run: tools/osic klayout -b -r layout/gen/amp_dpc_shunt_tall.py
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, REPO, box, snap, cuts_needed   # noqa: E402
from passives import PolyRes   # noqa: E402
import amp_dpc_tall as dpc   # noqa: E402

SHUNT = dict(rh_l=0.62, wsw=18, nf=6, rg=20e3)   # as layout/gen/lna_chain.py
BAR, VW, RV = dpc.BAR, dpc.VW, dpc.RV
GAP = float(os.environ.get('SH_GAP', 0.9))       # Msw's n-well box to each Rh


def shunt(b0, c, flip=False):
    """Draws the shunt in its own cell, placed over the stage; flip: mirrored about the centre
    line (Msw and the Rh pair in the bottom half, Mcap / Rg in the top, the strap pin at the top
    edge), for a stage whose tap columns run to its bottom edge (lna_chain_tall.py)."""
    b = Block(b0.name + '_sh', ly=b0.ly)
    W, Hh, g = c['W'], c['Hh'], c['g']
    c1, c2, cg = c['c1'], c['c2'], c['cg']
    y0 = g['ring'].top + 0.6                          # free space above the half's ring
    y1 = Hh - RV - 0.3

    def island(col, yc, low='m2'):
        isl = b.rect('m3', box(col.left - 0.05, yc - 0.3, col.right + 0.05, yc + 0.3))
        if low == 'm2':
            b.via('via2', box(isl.left, yc - 0.2, isl.right, yc + 0.2), enc=(0.065, 0.085))
        b.via('via3', isl, enc=(0.09, 0.09))
        return isl

    def head_via(hd, top):
        xc = hd.center().x
        vb = (box(xc - 0.15, hd.top - 0.45, xc + 0.15, hd.top - 0.05) if top
              else box(xc - 0.15, hd.bottom + 0.05, xc + 0.15, hd.bottom + 0.45))
        b.via('via1', vb, enc=(0.075, 0.085))
        return vb

    # --- top half: Rh_a | Msw | Rh_b
    rh = {q: PolyRes(b, SHUNT['rh_l'], 1, w=1.41, typ='sky130_fd_pr__res_high_po_1p41', pad_w=1.41) for q in 'ab'}
    f = Fet(b, 'p', SHUNT['wsw'], 0.15, nf=SHUNT['nf'], vt='', bulk='guard ring')
    xa = 1.7                                          # Rh_a's box left (the VDD riser is at 1.0 .. 1.4)
    rh['a'].place(xa - rh['a']._bbox.left + rh['a']._poly.left, y0 + 0.2)
    f.place(rh['a'].bbox.right + GAP + (f.diff.left - f.bbox.left), y0 + (f.diff.bottom - f.bbox.bottom))
    f.commit()
    rh['b'].place(f.bbox.right + GAP - rh['b']._bbox.left + rh['b']._poly.left, y0 + 0.2)
    assert rh['b'].bbox.right <= W - 0.15, (rh['b'].bbox, W)
    s0, d0 = f.diff.bottom + 0.2, f.diff.top - 0.2 - BAR
    n = {'sa': 0, 'sb': 0}
    for k, st in enumerate(f.strips):
        yb = s0 if k % 2 == 0 else d0
        xc = st.center().x
        bb = box(xc - VW / 2, yb, xc + VW / 2, yb + BAR)
        b.rect('m1', bb)
        n['sa' if k % 2 == 0 else 'sb'] += b.via('via1', bb, enc=(0.075, 0.085))
    xl, xr = f.strips[0].center().x - VW / 2, f.strips[-1].center().x + VW / 2
    for q, yb in (('a', s0), ('b', d0)):
        hd = rh[q].ends[0]                            # bottom head
        vb = head_via(hd, False)
        xc = hd.center().x
        b.rect('m2', box(min(xc - 0.15, xl), yb, max(xc + 0.15, xr), yb + BAR))
        b.rect('m2', box(vb.left, vb.bottom, vb.right, yb + BAR))
    b.label('m2', box(xl, s0, xr, s0 + BAR), 'sa')
    # Msw's gate: met1 bar over the (staggered) pads, one via1 at its right end, met2 to the gi column
    gy0, gy1 = min(q.bottom for q in f.pads), max(max(q.top for q in f.pads), min(q.bottom for q in f.pads) + 0.32)
    gb = b.rect('m1', box(f.pads[0].left, gy0, f.pads[-1].right, gy1))
    ygt = snap((gy0 + gy1) / 2)
    gv = box(gb.right - 0.4, ygt - 0.2, gb.right, ygt + 0.2)
    b.via('via1', gv, enc=(0.085, 0.085))
    b.rect('m2', box(gv.left, ygt - 0.2, cg.right + 0.05, ygt + 0.2))
    island(cg, ygt)
    # free heads: Rh_b -> outn column (met2 0.9 above the gi line, so the met3 landings clear),
    # Rh_a -> outp column (met2 above that)
    tb_ = rh['b'].heads[0][1]
    vb = head_via(tb_, True)
    yb_ = max(vb.center().y, ygt + 0.9)
    b.rect('m2', box(vb.left, vb.bottom, vb.right, yb_ + 0.2))
    b.rect('m2', box(c1.left - 0.05, yb_ - 0.2, vb.right, yb_ + 0.2))
    island(c1, yb_)
    ta = rh['a'].heads[0][1]
    va = head_via(ta, True)
    yh = max(tb_.top + 0.6, yb_ + 0.6)
    b.rect('m2', box(va.left, va.bottom, va.right, yh + 0.2))
    b.rect('m2', box(va.left, yh - 0.2, c2.right + 0.05, yh + 0.2))
    island(c2, yh)
    # Msw's ring -> VDD: met1 + mcon on its top bar, met1 up into the top rail
    bar = box(f.ring.left + 0.3, f.hole.top, f.ring.right - 0.3, f.ring.top)
    top = b.rect('m1', box(bar.left, bar.bottom - 0.16, bar.right, bar.top + 0.06))
    b.via('mcon', bar, enc=(0.06, 0.0))
    xv = top.center().x
    b.rect('m1', box(xv - 0.4, top.bottom, xv + 0.4, Hh - RV + 0.01))

    # --- bottom half: Mcap | Rg (drawn the right way up, at y < 0)
    fc = Fet(b, 'p', 5, 5, nf=1, vt='', bulk='guard ring')
    fc.place(1.7 + (fc.diff.left - fc.bbox.left), -y1 + (fc.diff.bottom - fc.bbox.bottom))
    fc.commit()
    rg = PolyRes(b, SHUNT['rg'] / 7379.0, 1)          # xhigh 0.35: R = 7379 * L
    rg.place(fc.bbox.right + 0.8 - rg._bbox.left + rg._poly.left, -y1 + 0.2)
    assert rg.bbox.right <= W - 0.15 and rg.bbox.top <= -y0, (rg.bbox, W, y0)
    hg = rg.heads[0][1]                               # top head: gi
    hs = rg.heads[0][0]                               # bottom head: lna_lo_n
    pc = fc.pads[0]
    xg = hg.center().x
    b.rect('m1', box(pc.left, pc.bottom, xg + 0.15, pc.top))
    b.rect('m1', box(xg - 0.15, min(pc.bottom, hg.bottom), xg + 0.15, max(pc.top, hg.top)))
    vg = head_via(hg, True)
    ygb = vg.center().y
    b.rect('m2', box(cg.left - 0.05, ygb - 0.2, vg.right, ygb + 0.2))
    island(cg, ygb)
    b.rect('m4', box(cg.left, ygb - 0.3, cg.right, ygt + 0.3))       # gi across the centre
    b.label('m4', box(cg.left, ygb, cg.right, ygt), 'gi')
    # Mcap: S / D strips and its ring's bottom bar -> VDD, met1 down into the bottom rail
    cb = box(fc.ring.left + 0.3, fc.ring.bottom, fc.ring.right - 0.3, fc.hole.bottom)
    cm = b.rect('m1', box(cb.left, cb.bottom - 0.06, cb.right, cb.top + 0.16))
    b.via('mcon', cb, enc=(0.06, 0.0))
    for st in fc.strips:
        b.rect('m1', box(st.left, cm.bottom, st.right, st.bottom + 0.1))
    b.rect('m1', box(cm.center().x - 0.4, -(Hh - RV + 0.01), cm.center().x + 0.4, cm.top))
    # strap: Rg's bottom head -> met2 up to an island on the gi column's lower segment, met4 down
    # to the cell's bottom edge (pin lna_lo_n)
    vs = head_via(hs, False)
    ys_ = max(vs.center().y, -(Hh - RV) + 0.65)      # island 0.3 clear of the rail's met3
    b.rect('m2', box(cg.left - 0.05, ys_ - 0.2, vs.right, ys_ + 0.2))
    b.rect('m2', box(vs.left, vs.bottom, vs.right, ys_ + 0.2))
    island(cg, ys_)
    assert ys_ + 0.3 + 0.3 <= ygb - 0.3, (ys_, ygb)
    b.rect('m4', box(cg.left, -Hh, cg.right, ys_ + 0.3))
    b.pin('m4', box(cg.left, -Hh, cg.right, -Hh + 0.5), 'lna_lo_n')
    c['rep'] += [('sa/sb', 'Msw strips', min(n.values()), 1)]
    b0.place(b.cell, 0, 0, 0, flip)
    b0.flare(target=b, small=True, verbose=True)   # via arrays (docs/layout.md "Via arrays"), 1 x 2: RF


def write_ref(meta):
    src = open(os.path.join(REPO, 'layout', 'ref', 'amp_dpc_t.spice')).read()
    body = re.search(r'^\.subckt amp_dpc_t [^\n]*\n(.*?)^\.ends', src, re.S | re.M).group(1)
    rh_l = SHUNT['rh_l']
    out = ['* amp_dpc_ts: amp_dpc_t (layout/ref/amp_dpc_t.spice) + lna_shunt (a = outp, b = outn, g = lna_lo_n), '
           'the shunt as layout/gen/lna_chain.py writes it (amp_dpc_shunt_tall.py)',
           '.subckt amp_dpc_ts inp inn nb outp outn VDD VSS lna_lo_n',
           body.rstrip('\n'),
           f'XRh_a sa outp VSS sky130_fd_pr__res_high_po_1p41 L={rh_l:.6g} mult=1',
           f'XRh_b outn sb VSS sky130_fd_pr__res_high_po_1p41 L={rh_l:.6g} mult=1',
           f"XMsw sb gi sa VDD sky130_fd_pr__pfet_01v8 L=0.15 W={SHUNT['wsw']} nf={SHUNT['nf']}",
           f"XRg lna_lo_n gi VSS sky130_fd_pr__res_xhigh_po_0p35 L={SHUNT['rg'] / 7379.0:.6g} mult=1",
           'XMcap VDD gi VDD VDD sky130_fd_pr__pfet_01v8 L=5 W=5 nf=1',
           '.ends']
    with open(os.path.join(REPO, 'layout', 'ref', 'amp_dpc_ts.spice'), 'w') as fh:
        fh.write('\n'.join(out) + '\n')


if __name__ == '__main__':
    b, meta = dpc.make(name='amp_dpc_ts', extra=0.7, riser_left=True, hook=shunt)
    b.write(os.path.join(REPO, 'layout', 'amp_dpc_ts.gds'))
    write_ref(meta)
