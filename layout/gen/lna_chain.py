# lna_chain layout (xschem/gen/chain.py:lna_chain), CHAIN_PARAMS w1=80 rl1=1k mt1=20 w2=20
# rl2=4k mt2=6 cs=0.6p cin=2p rb=20k: input coupling (Cin_p/n 2 pF MIM, ~31 um square,
# bottom plate on the pad side; Rb_p/n 20k high_po_0p35 from vcm to the gates), the
# reference diode Mref (W 6 nf 2 / L 0.5, ibias = every stage's nb), then amp_dp and
# 5 x amp_dpc in a straight line (the finished cell layouts, read in as subcells).
#
# Floorplan, left to right: the input section (Cin_p, Cin_n side by side; Mref and the Rb
# pair in a p-tap ring under them; the top plates drop on met3 just right of Cin_n to
# amp_dp's inp / inn), then the stages with 2 um routing gaps. A straight line puts the
# chain's output as far as possible from its input (the stability limit is output ->
# input coupling). In each gap: out -> in on met3/met2 (amp_dp's outputs line up with
# amp_dpc's inputs; between amp_dpc stages outp runs straight and outn steps down to
# inn), nb on met2, the VSS rail and the overlapping band of the VDD rails bridged.
# Pins: inp / inn (the pad-side plates, met3, top edge), vcm and ibias (met2, left edge),
# outp / outn (met2, right edge), taps o1..o5 (met2, in the gaps), VDD, VSS.
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
    W1, Wc = cells['amp_dp'].dbbox().width(), cells['amp_dpc'].dbbox().width()

    def pb(cell, net, side=None, dx=0.0):
        """pin box of cell's net (side 'L' / 'R': the one at that edge), moved by dx."""
        cands = pin[cell][net]
        if side:
            cands = sorted(cands, key=lambda t: t[1].left)
            cands = [cands[0] if side == 'L' else cands[-1]]
        lay, bb = cands[0]
        return lay, bb.moved(pya.DVector(dx, 0))

    # ---- input section
    e = CAPM_ENC_M3
    plate = CINW + 2 * e
    xc0 = 0.6                                           # Cin_p plate left
    cp = box(xc0 + e, RAIL_H + BOT_PLATE_SPACE + e, xc0 + e + CINW, RAIL_H + BOT_PLATE_SPACE + e + CINW)
    cn = cp.moved(pya.DVector(plate + 1.6, 0))
    pl_n_right = cn.right + e
    x_a = pl_n_right + BOT_PLATE_SPACE                  # g1p drop column
    x_b = x_a + 0.5 + 0.3                               # g1n drop column
    x_dp = x_b + 0.5 + 1.2                              # amp_dp origin
    xs = [x_dp]
    for i in range(1, NST):
        xs.append(xs[-1] + (W1 if i == 1 else Wc) + GAP)
    W = xs[-1] + Wc
    for i, x in enumerate(xs):
        b.place(cells['amp_dp' if i == 0 else 'amp_dpc'], x, 0)
    # VSS rail along the whole input section + the gaps (stage cells carry their own)
    b.stack(box(0, 0, x_dp - 0.3, RAIL_H), 'm1', 'm3')
    for lay in ('m1', 'm2', 'm3'):                      # metal only at the joint: abutting via
        b.rect(lay, box(x_dp - 0.5, 0, x_dp + 0.5, RAIL_H))   # arrays would break via spacing
    b.pin('m1', box(0, 0, 1.0, RAIL_H), 'VSS')

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
    _, nb_dp = pb('amp_dp', 'nb', 'L', x_dp)
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
    # g1p from Rb_p: up 1 um above the heads, then right to column x_a; g1n from Rb_n at head level to x_b
    hp = box(tp.left, tp.top - 0.45, tp.right, tp.top - 0.05)
    hn = box(tn.left, tn.top - 0.45, tn.right, tn.top - 0.05)
    for h in (hp, hn):
        b.via('via1', h, enc=(0.055, 0.085))
    yg_p = (hp.top + 0.6, hp.top + 1.0)
    b.rect('m2', box(hp.left, hp.bottom, hp.right, yg_p[1]))
    b.rect('m2', box(hp.left, yg_p[0], x_a + 0.5, yg_p[1]))
    b.rect('m2', box(hn.left, hn.bottom, x_b + 0.5, hn.top))
    b.label('m2', hp, 'g1p')
    b.label('m2', hn, 'g1n')
    # the caps, top plates by met4 strips to the drop columns
    _, in_dp = pb('amp_dp', 'inp', 'L', x_dp)
    _, inn_dp = pb('amp_dp', 'inn', 'L', x_dp)
    st_p = (cp.top - 1.3, cp.top - 0.15)                 # Cin_p's strip high
    st_n = (cp.top - 2.9, cp.top - 1.75)                 # Cin_n's strip lower
    for c, (s0_, s1_), xcol, (ylo, yhi), via_y in ((cp, st_p, x_a, (in_dp.bottom, in_dp.top), yg_p),
                                                   (cn, st_n, x_b, (inn_dp.bottom, inn_dp.top), (hn.bottom, hn.top))):
        strip = box(c.left, s0_, xcol + 0.5, s1_)
        bot = mim(b, c, strip)
        b.rect('m4', strip)
        col = box(xcol, min(ylo, via_y[0]), xcol + 0.5, s1_)
        b.rect('m3', col)
        b.via('via3', box(xcol, s0_, xcol + 0.5, s1_))
        b.via('via2', box(xcol, via_y[0], xcol + 0.5, via_y[1]), enc=(0.065, 0.065))
        b.rect('m3', box(xcol, ylo, x_dp + 0.5, yhi))      # into amp_dp's pin (met3)
        # pad-side plate: a met3 tab up to the top edge (the pin)
        tab = box(bot.left + 2.0, bot.top - 0.5, bot.left + 4.0, bot.top + 1.0)
        b.rect('m3', tab)
        b.pin('m3', box(tab.left, tab.top - 0.5, tab.right, tab.top), 'inp' if c is cp else 'inn')

    # ---- the gaps
    taps = []
    for i in range(1, NST):
        xl = xs[i - 1] + (W1 if i == 1 else Wc)          # right edge of stage i
        xr_ = xs[i]                                       # left edge of stage i+1
        src = 'amp_dp' if i == 1 else 'amp_dpc'
        dx_s = xs[i - 1]
        # rails
        b.rect('m1', box(xl - 0.5, 0, xr_ + 0.5, RAIL_H))
        b.rect('m2', box(xl - 0.5, 0, xr_ + 0.5, RAIL_H))
        b.rect('m3', box(xl - 0.5, 0, xr_ + 0.5, RAIL_H))
        _, vl = pb(src, 'VDD', None, dx_s)
        _, vr = pb('amp_dpc', 'VDD', None, xr_)
        vy0, vy1 = max(vl.bottom, vr.bottom), min(vl.top, vr.top)
        for lay in ('m1', 'm2', 'm3'):
            b.rect(lay, box(xl - 0.5, vy0, xr_ + 0.5, vy1))
        # nb
        _, nl = pb(src, 'nb', 'R', dx_s)
        _, nr = pb('amp_dpc', 'nb', 'L', xr_)
        xm = (xl + xr_) / 2
        b.rect('m2', box(nl.left, nl.bottom, xm + 0.2, nl.top))
        b.rect('m2', box(xm - 0.2, min(nl.bottom, nr.bottom), xm + 0.2, max(nl.top, nr.top)))
        b.rect('m2', box(xm - 0.2, nr.bottom, nr.right, nr.top))
        # outputs -> inputs
        for o, inn_ in (('outp', 'inp'), ('outn', 'inn')):
            lo, ob = pb(src, o, 'R', dx_s)
            _, ib = pb('amp_dpc', inn_, 'L', xr_)
            net = f'o{i}{o[-1]}'
            if lo == 70:                                  # amp_dp: met3 out, met2 in, rows overlap
                y0, y1 = max(ob.bottom, ib.bottom), min(ob.top, ib.top)
                assert y1 - y0 >= 0.3, (net, ob, ib)
                b.rect('m3', box(ob.left, ob.bottom, xm + 0.3, ob.top))
                b.rect('m2', box(xm - 0.3, ib.bottom, ib.right, ib.top))
                vb = box(xm - 0.3, y0, xm + 0.3, y1)
                b.rect('m2', vb)
                b.via('via2', vb, enc=(0.065, 0.04))
                pbx = box(xm - 0.3, ib.bottom, xm + 0.3, ib.top)
            else:                                         # amp_dpc: met2 both; outn steps down to inn
                b.rect('m2', box(ob.left, ob.bottom, xm + 0.2, ob.top))
                b.rect('m2', box(xm - 0.2, min(ob.bottom, ib.bottom), xm + 0.2, max(ob.top, ib.top)))
                b.rect('m2', box(xm - 0.2, ib.bottom, ib.right, ib.top))
                pbx = box(xm - 0.2, ib.bottom, xm + 0.2, ib.top)
            b.pin('m2', pbx, net)
            taps.append(net)
    # last stage outputs: the pins
    for o in ('outp', 'outn'):
        _, ob = pb('amp_dpc', o, 'R', xs[-1])
        b.pin('m2', ob, o)
    _, vt = pb('amp_dpc', 'VDD', None, xs[-1])
    b.pin('m1', box(W - 1.0, vt.bottom, W, vt.top), 'VDD')
    print(f'lna_chain: {W:.1f} x {max(cp.top + e + 1.0, 21.21):.1f} um; Cin {CINW} um, Rb {LRB:.2f} um; '
          f'stages at x = {", ".join(f"{x:.1f}" for x in xs)}')
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
