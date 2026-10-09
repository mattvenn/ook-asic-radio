# bias_gen layout (xschem/gen/bias.py:bias_gen).
#
# Mirror array: the 123 PMOS units (W 2 / L 1) of Mpr (60, diode, net pr) and the
# outputs ib_chain (60), ib_det (2), ib_comp (1), in three rows of one multi-finger
# pcell each. A slot is one drain strip shared by two fingers (2 units):
#   rows 0..2: 20 slots 'ABBA' x 5 (A = pr, B = ib_chain), point-symmetric about the
#   array centre, so the pr and ib_chain centroids coincide; row 2 adds the ib_det slot
#   and the single ib_comp finger at its right end (bias currents, no matching needed).
#   Dummy fingers (gate, source and drain on VDD) at the row ends, except where
#   ib_comp's finger ends row 2.
# Wiring is met1/met2 only (MIMs can sit over the array):
#   pr drain strips run straight into the met1 gate bar (the diode); rows 1 and 2 face
#   each other and share one gate bar; a met2 spine on the left joins the two bars and
#   is the pr pin.
#   Output drain strips land on met2 buses on the other side of their row; a met2
#   spine on the right joins the ib_chain buses; ib_det / ib_comp leave to the right
#   above it.
#   Source strips run into met1 VDD bars (rows 0 and 1 share one), which join the
#   n-tap guard ring.
# Run: tools/osic klayout -b -r layout/gen/bias_gen.py
import os
import sys
import pya
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, REPO, box, snap, ring, write_ref   # noqa: E402
from passives import PolyRes, mim, CAPM_ENC_M3                # noqa: E402
from rows import Dev, Net, build, inverter_roles     # noqa: E402

UW, UL = 2.0, 1.0           # mirror unit (wpu, L), as the schematic
SLOTS = 'ABBA' * 5          # per row
NET = {'A': 'pr', 'B': 'ib_chain', 'det': 'ib_det'}
BUS_H, BUS_S = 0.4, 0.14    # met2 bus height / spacing
BUS_0 = 0.3                 # diffusion edge to the first bus
BAR_H, BAR_S = 0.6, 0.26    # VDD bar height, last bus to bar
ROW_GAP = 0.75                # pad to pad between the two rows sharing a gate bar (poly heads 0.21 apart)
SPINE_W = 0.4


def row_nets(slots, comp_end):
    """Strip nets and finger gate nets of one row."""
    strips, gates = ['VDD', 'VDD'], ['VDD']           # left dummy
    for s in slots:
        strips += [NET[s], 'VDD']
        gates += ['pr', 'pr']
    if comp_end:
        strips.append('ib_comp')
        gates.append('pr')
    else:
        strips.append('VDD')                           # right dummy
        gates.append('VDD')
    return strips, gates


def mirror(b, x0, y0):
    """Mirror array with row 0's diffusion at (x0, y0). Returns its terminals."""
    spec = [(list(SLOTS), 'bottom', ['ib_chain'], False),
            (list(SLOTS), 'top', ['ib_chain'], False),
            (list(SLOTS) + ['det'], 'bottom', ['ib_chain', 'ib_det', 'ib_comp'], True)]
    rows = []
    for slots, gate, buses, comp in spec:
        strips, gates = row_nets(slots, comp)
        f = Fet(b, 'p', UW * len(gates), UL, nf=len(gates), gate=gate, vt='', bulk='None')
        rows.append(dict(f=f, gate=gate, buses=buses, strips=strips, gates=gates))

    def bus_side(r, yd):
        """y ranges of a row's buses and VDD bar, given its diffusion bottom yd."""
        up = r['gate'] == 'bottom'
        edge = yd + UW if up else yd
        sgn = 1 if up else -1
        ys, d = {}, BUS_0
        for n in r['buses']:
            ys[n] = tuple(sorted((edge + sgn * d, edge + sgn * (d + BUS_H))))
            d += BUS_H + BUS_S
        d += BAR_S - BUS_S
        ys['VDD'] = tuple(sorted((edge + sgn * d, edge + sgn * (d + BAR_H))))
        return ys

    # vertical stacking: rows 0 / 1 share the VDD bar, rows 1 / 2 the gate bar
    f0 = rows[0]['f']
    ys0 = bus_side(rows[0], y0)
    # row 1 (buses below): its VDD bar must equal row 0's
    probe = bus_side(rows[1], 0.0)
    y1 = snap(ys0['VDD'][0] - probe['VDD'][0])
    rows[1]['f'].place(x0, y1)
    pad_top1 = max(p.top for p in rows[1]['f'].pads)
    rows[2]['f'].place(x0, 0)
    pad_bot2 = min(p.bottom for p in rows[2]['f'].pads)           # relative to its diff at 0
    y2 = snap(pad_top1 + ROW_GAP - pad_bot2)
    for r, yd in zip(rows, (y0, y1, y2)):
        r['f'].place(x0, yd)
        r['f'].commit()
        r['ys'] = bus_side(r, yd)
        r['band'] = (min(p.bottom for p in r['f'].pads), max(p.top for p in r['f'].pads))

    # ring hole and the x extent of bars
    xl = x0 - 0.75                                   # ring hole left (room for the pr spine)
    xr_dev = max(r['f'].diff.right for r in rows)
    xs_c = snap(xr_dev + 0.5)                        # ib_chain spine (met2), right of all rows
    xr = snap(xs_c + SPINE_W + 0.5)                  # ring hole right
    yb = rows[0]['band'][0] - 0.4
    yt = rows[2]['ys']['VDD'][1]                     # the top VDD bar touches the ring top
    hole = box(xl, yb, xr, yt)
    rg = ring(b, hole, 'n', 0.4)
    b.rect('nwell', box(rg.left - 0.3, rg.bottom - 0.3, rg.right + 0.3, rg.top + 0.3))

    bars = {}
    for k, r in enumerate(rows):
        f, ys = r['f'], r['ys']
        up = r['gate'] == 'bottom'
        # VDD bar, ring side to ring side (merges with the ring's met1)
        b.rect('m1', box(xl, ys['VDD'][0], xr, ys['VDD'][1]))
        for s, net in zip(f.strips, r['strips']):
            cx = s.center().x
            if net == 'VDD':                         # source strip into the VDD bar
                y_to = ys['VDD'][0] if up else ys['VDD'][1]
                b.rect('m1', box(s.left, s.top if up else s.bottom, s.right, y_to))
            elif net == 'pr':                        # diode: drain strip into the gate bar
                y_to = r['band'][1] if up else r['band'][0]
                b.rect('m1', box(s.left, s.bottom if up else s.top, s.right, y_to))
            else:                                    # output drain strip to its bus
                y0b, y1b = ys[net]
                ext = box(cx - 0.145, s.top if up else y0b, cx + 0.145, y1b if up else s.bottom)
                b.rect('m1', ext)
                b.via('via1', box(cx - 0.145, y0b, cx + 0.145, y1b), enc=(0.07, 0.085))
        # gate bar over the active ('pr') fingers' pads; dummy pads tied to the end strip
        act = [p for p, g in zip(f.pads, r['gates']) if g == 'pr']
        bars[k] = b.rect('m1', box(act[0].left, r['band'][0], act[-1].right, r['band'][1]))
        for i, g in enumerate(r['gates']):
            if g != 'VDD':
                continue
            p = f.pads[i]
            s = f.strips[0] if i == 0 else f.strips[-1]
            b.rect('m1', box(s.left, p.bottom, s.right, s.bottom if up else s.top))
            b.rect('m1', box(min(s.left, p.left), p.bottom, max(s.right, p.right), p.top))
        # buses (met2): from the first strip on the net to the right
        for net in r['buses']:
            xs = [s.center().x for s, n in zip(f.strips, r['strips']) if n == net]
            x_end = xs_c + SPINE_W if net == 'ib_chain' else xr + 1.0     # det / comp: out
            bb = box(xs[0] - 0.145, ys[net][0], x_end, ys[net][1])
            b.rect('m2', bb)
            if net != 'ib_chain':
                b.label('m2', bb, net)
    # rows 1 and 2 share the gate bar: join them where both run
    j0 = max(bars[1].left, bars[2].left)
    j1 = min(bars[1].right, bars[2].right)
    b.rect('m1', box(j0, bars[1].top, j1, bars[2].bottom))

    # pr spine (met2, left): stubs over the dummy pads onto the two gate bars
    xs_p = snap(x0 - 0.6)
    spine_p = box(xs_p, yb - 2.0, xs_p + SPINE_W, rows[1]['band'][1])
    b.rect('m2', spine_p)
    for k in (0, 1):
        bar = bars[k]
        land = box(bar.left, bar.bottom, bar.left + 0.6, bar.top)
        b.rect('m2', box(xs_p, bar.bottom, land.right, bar.top))
        b.via('via1', land)
    # ib_chain spine (met2, right): bus 0 .. bus 2
    spine_c = box(xs_c, rows[0]['ys']['ib_chain'][0], xs_c + SPINE_W, rows[2]['ys']['ib_chain'][1])
    b.rect('m2', spine_c)
    b.label('m2', bars[0], 'pr')
    b.label('m2', spine_c, 'ib_chain')
    return dict(ring=rg, pr=spine_p, ib_chain=spine_c, ib_chain_bus=rows[2]['ys']['ib_chain'],
                ib_det=rows[2]['ys']['ib_det'], ib_comp=rows[2]['ys']['ib_comp'], x_out=xr + 1.0)


# small devices (rows.py): P row on VDD, N row on VSS. M1 / M2 (OTA pair, source tail)
# and Mn (source x, to rref) have signal sources: single fingers with a named strip net
# (rows.py's pass-device roles), the nets side by side; Mn is 4 parallel W 5 fingers.
RNETS = {'en': Net(io='L', pin=False), 'enb': Net(), 'pb': Net(io='R'), 'tail': Net(), 'd1': Net(),
         'vref': Net(io='R'), 'x': Net(io='R'), 'ota': Net(io='L'), 'pr': Net(io='L'),
         'dsw': Net(io='R'), 'tsw': Net(io='R')}


def small(b):
    def dev(kind, W, L, gnet, drain, nfmax=None, roles=None):
        f = Fet(b, kind, W, L, gate='bottom' if kind == 'p' else 'top', vt='', bulk='None', nfmax=nfmax)
        return Dev(f, roles or inverter_roles(f), [(gnet, list(range(f.nf)))], drain,
                   rail='VDD' if kind == 'p' else 'VSS')
    P = [dev('p', 1, 0.15, 'en', 'enb'),                                   # Meip
         dev('p', 1, 0.15, 'en', 'pr'),                                    # Mpu
         dev('p', 4, 1, 'pb', 'pb', 2),                                    # Mpb (diode)
         dev('p', 4, 1, 'pb', 'tail', 2),                                  # Mpt
         dev('p', 4, 1, 'vref', 'd1', roles=['tail', 'D']),                # M1
         dev('p', 4, 1, 'x', 'ota', roles=['D', 'tail'])]                  # M2
    N = [dev('n', 0.5, 0.15, 'en', 'enb'),                                 # Mein
         dev('n', 1, 0.15, 'en', 'dsw'),                                   # Mdsw
         dev('n', 1, 0.15, 'en', 'tsw'),                                   # Mtsw
         dev('n', 1, 0.15, 'enb', 'ota'),                                  # Mpd
         dev('n', 2, 2, 'd1', 'd1'),                                       # M3 (diode)
         dev('n', 2, 2, 'd1', 'ota'),                                      # M4
         ] + [dev('n', 5, 0.5, 'ota', 'pr', roles=['x', 'D'] if k % 2 else ['D', 'x'])
              for k in range(4)]                                    # Mn: 4 x W 5
    return build(b, P, N, RNETS, rail_h=1.5)


def test_small():
    b = Block('bias_small')
    small(b)
    return b


def test_mirror():
    """The mirror array alone, as cell bias_mirror (build/lay/), for DRC/LVS."""
    b = Block('bias_mirror')
    t = mirror(b, 0, 0)
    b.pin('m2', box(t['pr'].left, t['pr'].bottom, t['pr'].right, t['pr'].bottom + 0.5), 'pr')
    b.pin('m2', t['ib_chain'], 'ib_chain')
    for n in ('ib_det', 'ib_comp'):
        y0, y1 = t[n]
        b.pin('m2', box(t['x_out'] - 0.5, y0, t['x_out'], y1), n)
    rg = t['ring']
    b.pin('m1', box(rg.left, rg.top - 0.4, rg.left + 1.0, rg.top), 'VDD')
    return b


# ---------------------------------------------------------------- the block
PARAMS = dict(rref=10e3, rdiv=200e3, rtail=250e3, wpu=2, cc=1e-12)   # as the bias_gen symbol
CAP = 22.035            # MIM unit side: Cc 1 pF, Cvcm / Cvref 2 x 1 pF (sqrt(1p / 2.06 fF/um2))
PLATE = snap(CAP + 2 * CAPM_ENC_M3)
CGAP = 2.0              # bottom plate to bottom plate (capm.2b 1.2 / magic capm.11)
M3CAP = 1.2             # bottom plate to unrelated met3
RAIL = 1.5
LANE_V1 = (0.07, 0.085)  # via1 enclosure in a 0.4 column / 0.5 lane
PIN_XY = {'ib_chain': (28.18, 48.82), 'vcm': (31.32, 48.82), 'ib_det': (79.22, 48.82),   # pins.md
          'ib_comp': (79.97, 48.07), 'en': (2.05, 0.25)}
INTERNAL = ('pb', 'vref', 'x', 'dsw', 'tsw', 'ota', 'pr')    # rows io nets that are not block pins


def make():
    """bias_gen:
      bottom band: small devices (rows.py, VDD rail on top = the block's middle rail, VSS
        rail at the bottom); right of them a transition zone (tracks met3 -> met2 lanes;
        the vcm riser and the vref drop on met4), then the resistors (p-tap ring on VSS)
        under the first Cvref unit, then the second Cvref unit. Lanes (met2) run at the
        track heights, met1 columns rise / fall to the resistor heads.
      top band: the mirror array on the middle VDD rail, under Cc + 2 x Cvcm.
      VSS rails at the bottom and the top (the MIM bottom plates abut them), VDD in the
      middle. Pins (floorplan, layout/floorplan/pins.md): en (south, met2), ib_chain /
      ib_det / vcm (north, met2 / met2 / met4), ib_comp (east at the top corner, met2),
      VDD (middle rail), VSS (both rails)."""
    b = Block('bias_gen')
    pin0 = b.pin
    b.pin = lambda lay, bx, name: (b.label(lay, bx, name) if name in INTERNAL else pin0(lay, bx, name))
    small(b)
    b.pin = pin0
    nw_small = pya.Region(b.cell.begin_shapes_rec(b.li('nwell'))).bbox().to_dtype(b.ly.dbu)
    rw = b.rows
    ytop, ybot, xs_ = rw['ytop'], rw['ybot'], rw['xmax']
    tr = rw['tracks']
    ymid = ytop + RAIL                                   # middle VDD rail top

    def ty(n):
        return tr[n]['y0'], tr[n]['y1']

    # ---- transition zone: tracks -> lanes; vcm riser, vref drop (met4)
    X_VCM = (xs_ + 0.1, xs_ + 0.6)
    X_VREF = (xs_ + 1.0, xs_ + 1.5)
    x_c3 = snap(X_VREF[1] + M3CAP + 0.1)                 # first bottom cap plate (over the resistors)
    lanes = {}
    for n in ('dsw', 'vref', 'pb', 'tsw', 'x'):
        y0, y1 = ty(n)
        b.rect('m3', box(xs_ - 0.2, y0, (X_VREF[1] if n == 'vref' else X_VCM[1]), y1))
        b.via('via2', box(X_VCM[0], y0, X_VCM[1], y1))
        lanes[n] = (y0, y1)
    # vcm lane: a channel track row whose nets all end well left of the zone (free to its right)
    free = [t for t in {id(t): t for t in tr.values()}.values()
            if all(RNETS[n].io is None and rw['xs'][n][1] < xs_ - 1.5 for n in t['nets'])]
    assert free, 'no free channel row for the vcm lane'
    yv0 = free[0]['y0']
    lanes['vcm'] = (yv0, free[0]['y1'])

    # ---- resistors
    rd = PolyRes(b, 3 * PARAMS['rdiv'] / 7379, 9)
    rt = PolyRes(b, PARAMS['rtail'] / 7379, 4)
    rr = PolyRes(b, 2 * (PARAMS['rref'] / 2 - 526) / 470.9, 2, w=0.69,     # Rref1 + Rref2
                 typ='sky130_fd_pr__res_high_po_0p69')
    rr.pitch = 1.2      # 0p69: rpm markers (1.27 wide) merge; psdm merged below (psdm.1)
    yc = (ybot + ytop) / 2
    xb = x_c3 + 1.0                                      # next array's bbox left
    for r in (rd, rt, rr):
        r.place(xb + (r._poly.left - r._bbox.left), snap(yc - (r._poly.height()) / 2))
        xb = r.bbox.right + 1.4                          # rpm markers 0.84 apart (rpm.2)
    b.rect('psdm', box(rr.poly.left - 0.11, rr.poly.bottom - 0.11, rr.poly.right + 0.11, rr.poly.top + 0.11))
    heads_lo = max(max(h[0].top for h in r.heads) for r in (rd, rt, rr))
    heads_hi = min(min(h[1].bottom for h in r.heads) for r in (rd, rt, rr))
    for n, (y0, y1) in lanes.items():
        assert heads_lo + 0.3 < y0 and y1 < heads_hi - 0.3, (n, y0, y1, heads_lo, heads_hi)
    inner = box(min(r.bbox.left for r in (rd, rt, rr)) - 0.6, min(r.bbox.bottom for r in (rd, rt, rr)) - 0.6,
                max(r.bbox.right for r in (rd, rt, rr)) + 0.6, max(r.bbox.top for r in (rd, rt, rr)) + 0.6)
    assert inner.top + 0.4 < ytop - 0.14, ('resistor ring into the VDD rail', inner)
    rg = ring(b, inner, 'p', 0.4)
    b.rect('m1', box(rg.left, ybot - 0.01, rg.right, rg.bottom + 0.4))      # ring -> VSS rail
    for k, ln in enumerate(rd.links):
        b.label('m1', ln, {2: 'vref', 5: 'vcm'}.get(k, f'rd{k}'))
    for k, ln in enumerate(rt.links):
        b.label('m1', ln, f'rt{k}')
    b.label('m1', rr.links[0], 'xr')

    def column(head, net, up):
        """met1 column from a head / link to its lane, via1 at the lane, lane met2 from the
        zone to the column."""
        cx = head.center().x
        y0, y1 = lanes[net]
        b.rect('m1', box(cx - 0.2, head.bottom if up else y0, cx + 0.2, y1 if up else head.top))
        b.via('via1', box(cx - 0.2, y0, cx + 0.2, y1), enc=LANE_V1)
        b.rect('m2', box(X_VCM[0], y0, cx + 0.2, y1))
    column(rd.heads[0][0], 'dsw', True)
    column(rd.links[2], 'vref', False)
    column(rd.links[5], 'vcm', True)
    column(rt.heads[0][0], 'pb', True)
    column(rt.heads[3][0], 'tsw', True)
    column(rr.heads[0][0], 'x', True)
    # VDD: the divider's top end -> met2 up to the middle rail (met1 + met2 extended over)
    hv = rd.heads[8][1]
    b.via('via1', hv, enc=(0.055, 0.085))
    b.rect('m2', box(hv.left, hv.bottom, hv.right, ytop + 0.5))
    b.stack(box(xs_, ytop, hv.right + 0.3, ymid), 'm1', 'm2')        # abuts the rows rail
    # VSS: Rref's free end -> met2 down to the bottom rail
    hs = rr.heads[1][0]
    b.via('via1', hs, enc=(0.055, 0.085))
    b.rect('m2', box(hs.left, ybot - 0.5, hs.right, hs.top))

    # ---- bottom caps (Cvref x 2): plates abut the bottom VSS rail; top plates on one met4 strip
    caps_b = [box(x_c3 + k * (PLATE + CGAP) + CAPM_ENC_M3, ybot + CAPM_ENC_M3,
                  x_c3 + k * (PLATE + CGAP) + CAPM_ENC_M3 + CAP, ybot + CAPM_ENC_M3 + CAP) for k in range(2)]
    sb = box(X_VREF[0], caps_b[0].top - 1.6, caps_b[-1].right - 0.2, caps_b[0].top - 0.2)
    for c in caps_b:
        mim(b, c, sb)
    b.rect('m4', sb)
    vy0, vy1 = ty('vref')
    b.rect('m4', box(X_VREF[0], vy0, X_VREF[1], sb.top))                     # vref drop
    b.via('via3', box(X_VREF[0], vy0, X_VREF[1], vy1))
    b.label('m4', sb, 'vref')
    plate_b_top = caps_b[0].top + CAPM_ENC_M3

    # ---- mirror on the middle rail
    mt = mirror(b, 0.0, snap(ymid + 1.98))
    assert abs(mt['ring'].bottom - ymid) < 0.01, mt['ring']
    # nwell bridge: the small block's PMOS nwell up to the mirror's (both VDD)
    b.rect('nwell', box(nw_small.left, nw_small.top - 0.5, nw_small.right, ymid))
    # pr: the mirror's spine down to the pr track (extended left)
    py0, py1 = ty('pr')
    sp = mt['pr']
    b.rect('m2', box(sp.left, py0, sp.right, sp.bottom))
    b.rect('m3', box(sp.left, py0, 0.5, py1))
    b.via('via2', box(sp.left, py0, sp.right, py1))

    # ---- top caps: Cc, Cvcm, Cvcm
    y_tc = snap(max(ymid + M3CAP, plate_b_top + M3CAP))
    caps_t = [box(k * (PLATE + CGAP) + CAPM_ENC_M3, y_tc + CAPM_ENC_M3,
                  k * (PLATE + CGAP) + CAPM_ENC_M3 + CAP, y_tc + CAPM_ENC_M3 + CAP) for k in range(3)]
    plate_t_top = caps_t[0].top + CAPM_ENC_M3
    assert mt['ring'].top < y_tc + 0.5 or True
    x_r = snap(max(caps_b[-1].right, caps_t[-1].right) + CAPM_ENC_M3 + M3CAP + 0.8)
    x_l = -1.8
    # Cc (ota): strip on cap 0, out to the left; ota track extended left; met4 riser
    s0 = box(x_l, caps_t[0].top - 1.6, caps_t[0].right - 0.2, caps_t[0].top - 0.2)
    mim(b, caps_t[0], s0)
    b.rect('m4', s0)
    oy0, oy1 = ty('ota')
    b.rect('m3', box(x_l, oy0, 0.5, oy1))
    b.rect('m4', box(x_l, oy0, x_l + 0.6, s0.top))
    b.via('via3', box(x_l, oy0, x_l + 0.6, oy1))
    b.label('m4', s0, 'ota')
    # Cvcm: strip over caps 1, 2, from the cap0/1 gap to the right edge (vcm pin)
    gx0 = snap(caps_t[0].right + CAPM_ENC_M3 + 0.7)
    s1 = box(gx0, caps_t[1].top - 1.6, x_r, caps_t[1].top - 0.2)
    for c in caps_t[1:]:
        mim(b, c, s1)
    b.rect('m4', s1)
    # vcm route: lane -> zone landing (met2 / met3 / met4) -> riser -> under the top caps
    # (met4 below their plates) to the cap0/1 gap -> up to the strip
    lv = box(X_VCM[0], yv0, X_VCM[1], lanes['vcm'][1])
    b.rect('m3', lv)
    b.via('via2', lv)
    b.via('via3', lv)
    yh0, yh1 = snap(ymid + 0.3), snap(ymid + 0.8)
    b.rect('m4', box(X_VCM[0], yv0, X_VCM[1], yh1))
    b.rect('m4', box(gx0, yh0, X_VCM[1], yh1))
    b.rect('m4', box(gx0, yh0, gx0 + 0.6, s1.top))

    # ---- rails: bottom VSS and top VSS full width; middle VDD is the small block's
    for xa, xb in ((x_l, 0.0), (xs_, x_r)):                 # abut the rows VSS rail (no via overlap)
        b.stack(box(xa, ybot - RAIL, xb, ybot), 'm1', 'm3')
    b.stack(box(x_l, plate_t_top, x_r, plate_t_top + RAIL), 'm1', 'm3')
    b.pin('m3', box(x_l, plate_t_top, x_l + 1.0, plate_t_top + RAIL), 'VSS')
    b.rect('m1', box(x_l, ybot - RAIL, x_l + 0.5, plate_t_top + RAIL))      # top VSS rail <-> bottom
    # top plates' met3 up to the top rail: they abut it (plate top = rail bottom)

    # ---- pins (floorplan, layout/floorplan/pins.md; x / y below in the block's own frame,
    # lower-left = 0). The top VSS rail is the north edge: met2 pins cross it through gaps
    # in its met2 (met1 / met3 stay whole).
    ox, oy = x_l, ybot - RAIL                            # bbox lower-left
    ytop_b = plate_t_top + RAIL                          # north edge
    yr0 = plate_t_top                                    # rail bottom

    def north_m2(x, y_from, name, w=0.4):
        xa = snap(ox + x - w / 2)
        b.clear(('m2', 'via1', 'via2'), box(xa - 0.3, yr0, xa + w + 0.3, ytop_b))
        b.rect('m2', box(xa, y_from, xa + w, ytop_b))
        b.pin('m2', box(xa, ytop_b - 0.5, xa + w, ytop_b), name)
        return xa

    # ib_chain (28.18, N): up from the mirror's row-2 ib_chain bus under Cc / Cvcm (met2 is
    # free there) through the rail
    north_m2(PIN_XY['ib_chain'][0], mt['ib_chain_bus'][0], 'ib_chain')
    # vcm (31.32, N): the Cvcm top-plate strip (met4) straight up over the rail (met4: met3
    # can't come within 1.34 of the caps' capm)
    xv = snap(ox + PIN_XY['vcm'][0] - 0.3)
    b.rect('m4', box(xv, s1.top - 0.1, xv + 0.6, ytop_b))
    b.pin('m4', box(xv, ytop_b - 0.5, xv + 0.6, ytop_b), 'vcm')
    # ib_det (79.22, N) and ib_comp (east edge, 48.07: in the rail's height) up the right
    # margin (clear of the caps): ib_comp on the outside column, ib_det inside it. ib_comp's
    # bus is above ib_det's, so it hops ib_det's column on met1 (free in the margin).
    (d0, d1), (c0, c1) = mt['ib_det'], mt['ib_comp']
    xd = north_m2(PIN_XY['ib_det'][0], d0, 'ib_det')
    b.rect('m2', box(mt['x_out'] - 0.5, d0, xd + 0.4, d1))
    xc = snap(x_r - 0.4)
    yc = snap(oy + PIN_XY['ib_comp'][1])
    hop = (snap(xd - 0.3 - 0.4), xc)                     # met2 off / on, either side of ib_det
    b.rect('m2', box(mt['x_out'] - 0.5, c0, hop[0] + 0.4, c1))
    b.rect('m1', box(hop[0], c0, x_r, c1))
    for xh in hop:
        b.via('via1', box(xh, c0, xh + 0.4, c1), enc=LANE_V1)
    b.clear(('m2', 'via1', 'via2'), box(xc - 0.3, yr0, x_r, ytop_b))
    b.rect('m2', box(xc, c0, x_r, yc + 0.2))
    b.pin('m2', box(xc, yc - 0.2, x_r, yc + 0.2), 'ib_comp')
    # en (2.05, S): from its channel track's left end (x 0, met3) down on met2 (via2) past
    # the lower tracks (met3: ota / pr run out to the left edge) through the bottom rail
    te = tr['en']
    b.via('via2', box(0, te['y0'], 0.4, te['y1']), enc=(0.085, 0.065))
    b.clear(('m2', 'via1', 'via2'), box(-0.3, oy, 0.7, ybot))
    b.rect('m2', box(0, oy, 0.4, te['y1']))
    b.pin('m2', box(0, oy, 0.4, oy + 0.5), 'en')
    print(f'bias_gen: {x_r - x_l:.1f} x {plate_t_top + RAIL - (ybot - RAIL):.1f} um')
    return b


if __name__ == '__main__':
    t = os.environ.get('BIAS_TEST')
    if t:
        {'mirror': test_mirror, 'small': test_small}[t]().write(os.path.join(REPO, 'layout', f'bias_{t}.gds'))
    else:
        make().write(os.path.join(REPO, 'layout', 'bias_gen.gds'))
        write_ref('bias_gen', 'bias_gen', PARAMS)
