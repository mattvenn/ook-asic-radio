# comp_ct layout: continuous comparator (xschem/gen/comp.py:comp_ct).
#   lvt NMOS pair M1/M2 (W 20 / L 1, nf 4) + lvt PMOS mirror Mp1/Mp2 (4 / 1); trim pair
#   M3/M4 (lvt 2 / 1) with split tails Mta (4 / 2, nf 2) and Rdeg (xhigh, 2 MOhm); VDD/2
#   reference Rr1/Rr2 (xhigh L 136) + Cref (10x10 MIM); Cl (22x22 MIM) on d2; stage 2
#   Mp3 (lvt 4 / 1) + Mn3 (9.1 / 2, nf 2); output inverter; bias diode Mb, tail Mt1 (18.2 / 2, nf 4).
#
# Matching (docs/layout.md checklist): each pair split into halves placed A B B A
# (1D common centroid), same orientation, with rail-tied dummies (rows.dummy) either
# side. N row: [d] M1 M2 M2 M1 [d d] M3 M4 M4 M3 [d d] bias + stage 2 + inverter;
# P row: [d] Mp1 Mp2 Mp2 Mp1 [d d] Mp3 Mip.
# Run: tools/osic klayout -b -r layout/gen/comp_ct.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, box, snap, ring, write_ref, REPO   # noqa: E402
from rows import Dev, Net, build, inverter_roles, dummy   # noqa: E402
from passives import PolyRes, mim, CAPM_ENC_M3, BOT_PLATE_SPACE   # noqa: E402

PARAMS = dict(w1=20, l1=1, mt1=10, rdeg=2e6, mta=2, lref=136, wcl=22)   # radio_analog's xcomp
NETS = {'inp': Net(), 'inn': Net(), 'trim': Net(io='R', pin=False), 'ibias': Net(io='R', pin=False),
        'out': Net(io='R', pin=False),
        'tail': Net(), 'd1': Net(), 'd2': Net(), 'sa': Net(), 'sb': Net(), 'vref': Net(), 'o2': Net()}


def make(passives=True, xp=None):
    """xp: x where Mp3 and Mip start (over Mn3 and Min, so o2/out stay at the right end
    of the channel; Mip right after Mp3 puts two o2 met2 stubs < 0.14 apart).
    None: a first pass without it finds Mn3's and Min's x."""
    if xp is None:
        b0 = make(False, (0, 0))
        xp = (b0.mn3.f.diff.left, b0.min_.f.diff.left)
    b = Block('comp_ct')
    P_ = dict(PARAMS)

    def fet(kind, W, l, vt='', nf=1):
        return Fet(b, kind, W, l, nf=nf, gate='bottom' if kind == 'p' else 'top', vt=vt, bulk='None')

    def dev(kind, W, l, vt, gate, drain, nf=1, roles=None, xmin=None):
        f = fet(kind, W, l, vt, nf)
        return Dev(f, roles or inverter_roles(f), [(gate, list(range(f.nf)))], drain,
                   rail='VDD' if kind == 'p' else 'VSS', xmin=xmin)

    def dmy(kind, W, l, vt):
        return dummy(fet(kind, W, l, vt), 'VDD' if kind == 'p' else 'VSS')

    w1, l1 = P_['w1'], P_['l1']
    half = w1 / 2                                       # each half: 2 fingers of w1/4

    def pair(g, d):                                     # S D S: tail on both sides
        return dev('n', half, l1, 'lvt', g, d, nf=2, roles=['tail', d, 'tail'])

    def trim(g, d, s):
        return dev('n', 1.0, 1.0, 'lvt', g, d, roles=[s, d])

    def mirror(d):
        return dev('p', 2.0, 1.0, 'lvt', 'd1', d)

    # core first (main pair, then the trim pair on the same d1/d2), then bias + stage 2 +
    # inverter: d1/d2 stay short and out/o2 stay away from them. The L 2 bias devices are
    # folded into 4.55 um fingers (Mt1, Mn3; W corrected for the bin), not unit copies.
    N = ([dmy('n', w1 / 4, l1, 'lvt'), pair('inp', 'd1'), pair('inn', 'd2'), pair('inn', 'd2'), pair('inp', 'd1'),
          dmy('n', w1 / 4, l1, 'lvt'), dmy('n', 1, 1, 'lvt'),
          trim('vref', 'd1', 'sa'), trim('trim', 'd2', 'sb'), trim('trim', 'd2', 'sb'), trim('vref', 'd1', 'sa'),
          dmy('n', 1, 1, 'lvt'), dmy('n', 2, 2, '')]
         + [dev('n', 2, 2, '', 'ibias', 'ibias'),                          # Mb (diode)
            dev('n', 1.82 * P_['mt1'], 2, '', 'ibias', 'tail', nf=4),      # Mt1 (W bin, see comp.py)
            dev('n', 2 * P_['mta'], 2, '', 'ibias', 'sa', nf=P_['mta']),    # Mta_sa
            dev('n', 2 * P_['mta'], 2, '', 'ibias', 'sb', nf=P_['mta']),    # Mta_sb
            mn3 := dev('n', 9.1, 2, '', 'ibias', 'o2', nf=2),               # Mn3
            min_ := dev('n', 1, 0.15, '', 'o2', 'out')])                    # Min
    P = ([dmy('p', 2, 1, 'lvt'), mirror('d1'), mirror('d2'), mirror('d2'), mirror('d1'), dmy('p', 2, 1, 'lvt'),
          dmy('p', 4, 1, 'lvt'),
          dev('p', 4, 1, 'lvt', 'd2', 'o2', xmin=xp[0]),                      # Mp3
          dev('p', 2, 0.15, '', 'o2', 'out', xmin=xp[1])])                  # Mip
    build(b, P, N, NETS, rail_h=1.5)
    b.mn3, b.min_ = mn3, min_
    if passives:
        add_passives(b, P_)
        add_pins(b)
    return b


# Pins (floorplan matt layout 5, layout/floorplan/pins.md; the block is placed MYR90, so its
# own N edge faces west, E south, S east). Own-frame targets (lower-left = 0, 0):
PIN_X = {'inp': 37.85, 'inn': 42.45}          # N edge: inn = lpf (lpf_rc out, below), inp = avg (avg_sc out, above)
PIN_Y = {'ibias': 22.47, 'trim': 19.47}       # E edge, toward bias_gen (corridor) / Ctrim n
OUT_X = 72.45                                 # S edge at the east end, toward the macro


def add_pins(b):
    """inp / inn: a met4 riser from the track's east end up past the tracks above it, met3
    east under the VDD rail (empty there), up through a gap in the rail's met3 to the N edge.
    inn's horizontal runs below inp's (inp's pin is west of inn's, so they don't cross).
    out / trim / ibias: their tracks run east (io 'R'); each drops down its own met4 column
    at the east end (no met4 there): ibias on the outside, stopping at its pin; trim inside
    it, turning east to the edge below ibias's end; out innermost, on down to the S edge.
    Nothing crosses on one layer."""
    g = b.rows
    t, xs = g['tracks'], g['xs']
    bb = b.cell.dbbox()
    ox, oy, R, top = bb.left, bb.bottom, bb.right, bb.top
    yrail = g['ytop']                                     # VDD rail bottom
    ych = max(tt['y1'] for tt in t.values())              # top of the channel
    for n, yh in (('inn', ych + 1.5), ('inp', ych + 2.5)):
        tr, xe = t[n], xs[n][1] + 0.1                      # track's east end
        col = box(xe - 0.5, tr['y0'], xe, yh + 0.5)
        b.via('via3', box(col.left, tr['y0'], col.right, tr['y1']))
        b.rect('m4', col)
        X = snap(ox + PIN_X[n])
        b.rect('m3', box(col.left, yh, X + 0.25, yh + 0.5))
        b.via('via3', box(col.left, yh, col.right, yh + 0.5))
        b.clear(('m3', 'via2'), box(X - 0.55, yrail, X + 0.55, top))
        b.rect('m3', box(X - 0.25, yh, X + 0.25, top))
        b.pin('m3', box(X - 0.25, top - 0.5, X + 0.25, top), n)
    cols = {'ibias': (R - 0.5, R), 'trim': (R - 1.3, R - 0.8), 'out': (R - 2.1, R - 1.6)}
    for n, (x0, x1) in cols.items():
        tr = t[n]
        b.rect('m3', box(g['xmax'] - 0.5, tr['y0'], R, tr['y1']))          # track on to the edge
        land(b, n, x0, x1)                                                    # (out's stub is east of its column)
        b.via('via3', box(x0, tr['y0'], x1, tr['y1']))
        if n == 'out':
            b.rect('m4', box(x0, oy, x1, tr['y1']))
            b.pin('m4', box(x0, oy, x1, oy + 0.5), n)
        else:
            yp = snap(oy + PIN_Y[n])
            b.rect('m4', box(x0, yp - 0.25, x1, tr['y1']))
            b.rect('m4', box(x0, yp - 0.25, R, yp + 0.25))
            b.pin('m4', box(R - 0.5, yp - 0.25, R, yp + 0.25), n)


def land(b, net, x0, x1):
    """Make net's track cover [x0, x1] (for a met4 riser's via3), extending it only if no
    other net on the same track is within 0.5 um of the extension."""
    g = b.rows
    t = g['tracks'][net]
    a, c = g['xs'][net]
    na, nc = min(a, x0 - 0.1), max(c, x1 + 0.1)
    for other in t['nets']:
        if other != net:
            oa, oc = g['xs'][other]
            assert nc < oa - 0.5 or na > oc + 0.5, f'track of {net} would hit {other}'
    b.rect('m3', box(na, t['y0'], nc, t['y1']))
    g['xs'][net] = (na, nc)
    b.via('via3', box(x0, t['y0'], x1, t['y1']), enc=(0.065, 0.09))


def add_passives(b, P_):
    """The band below the VSS rail, as wide as the rows: Rdeg (sa-sb) and the Rr1/Rr2
    VDD/2 divider (tap: vref) in one p-tap ring, with Cl (2 x wcl x wcl/2, d2) and Cref
    (10x10, vref) over it (their VSS met3 bottom plates shield the resistors). The resistor
    ends run on met2 lanes under the caps to one column of met4 risers (sa, sb, VDD, vref)
    where the sa/sb/vref tracks already are; Cref's top plate joins the vref riser on met4."""
    g = b.rows
    e = CAPM_ENC_M3
    if os.environ.get('TRACKS'):
        for n, tt in g['tracks'].items():
            print(f'TRACK {n:6s} y {tt["y0"]:6.2f} x {g["xs"][n][0]:6.2f}..{g["xs"][n][1]:6.2f} shares {tt["nets"]}')
    yr = g['ybot'] - g['rail_h']                      # rail bottom edge
    t = g['tracks']
    grw, m = 0.4, 0.6
    inner_top = yr - grw
    # --- resistors: Rdeg 30 segments, Rr1+Rr2 32 (a multiple of 4: the middle link,
    # vref, is a bottom one), ~9 um each, side by side across the band
    rdeg = PolyRes(b, P_['rdeg'] / 7.37e3, 30, pad_w=0.5)
    rr = PolyRes(b, 2 * P_['lref'], 32, pad_w=0.5)
    xl = 0.2 + grw + m
    for r, x in ((rdeg, xl), (rr, None)):
        if x is None:
            x = rdeg.bbox.right + 2.0
        top = inner_top - m - (r._bbox.top - r._poly.top)
        r.place(x - (r._bbox.left - r._poly.left), top - (r._poly.top - r._poly.bottom))
    # --- met2 lanes below the bottom heads, one per net, to the riser column
    LW, LP = 0.4, 0.8
    yh = min(rdeg.bbox.bottom, rr.bbox.bottom)
    nets = ('sa', 'sb', 'VDD', 'vref')
    lane = {n: yh - 0.5 - k * LP for k, n in enumerate(nets)}          # lane centre y
    rx = {n: snap(23.9 + k * 1.0) for k, n in enumerate(nets)}         # riser left x (0.6 wide)
    tap = rr.links[15]                                                  # between segments 15 and 16
    heads = {'sa': rdeg.ends[0], 'sb': rdeg.ends[1], 'VDD': rr.ends[0],
             'vref': box(tap.center().x - 0.25, tap.bottom, tap.center().x + 0.25, tap.top)}
    risers = {}
    for n in nets:
        h, yc = heads[n], lane[n]
        xc = h.center().x
        b.rect('m1', box(h.left, yc - 0.3, h.right, h.top))            # head down to its lane
        b.rect('m2', box(xc - 0.3, yc - 0.3, xc + 0.3, yc + 0.3))
        b.via('via1', box(xc - 0.3, yc - 0.3, xc + 0.3, yc + 0.3))
        b.rect('m2', box(min(xc, rx[n]) - 0.3, yc - LW / 2, max(xc, rx[n] + 0.6) + 0.3, yc + LW / 2))
        pad = box(rx[n], yc - 0.3, rx[n] + 0.6, yc + 0.3)
        b.stack(pad, 'm2', 'm4')
        if n == 'VDD':                                # up to the VDD rail (m3), via3 there
            yv = g['ytop']
            riser = box(pad.left, pad.bottom, pad.right, yv + g['rail_h'])
            b.rect('m4', riser)
            b.via('via3', box(riser.left, yv, riser.right, yv + g['rail_h']), enc=(0.065, 0.09))
        else:
            riser = box(pad.left, pad.bottom, pad.right, t[n]['y1'])
            b.rect('m4', riser)
            land(b, n, riser.left, riser.right)
        risers[n] = riser
    vss = rr.ends[1]                                  # Rr2 bottom end: to the ring (VSS)
    inner = box(rdeg.bbox.left - m, lane[nets[-1]] - 0.3 - m, rr.bbox.right + m, inner_top)
    b.rect('m1', box(vss.left, inner.bottom - grw / 2, vss.right, vss.top))
    ring(b, inner, 'p', grw)
    b.rect('m1', box(inner.left - grw, inner_top, inner.right + grw, yr + 0.01))   # ring onto the rail
    # --- caps over the ring, plates abutting the rail: Cl_a | risers | Cref | Cl_b
    wcl = P_['wcl']
    hcl = wcl / 2
    xa = 0.2 + e
    cla = box(xa, yr - e - hcl, xa + wcl, yr - e)
    xc0 = risers['vref'].right + BOT_PLATE_SPACE + e
    assert cla.right + e + BOT_PLATE_SPACE <= rx['sa'], 'Cl_a plate too close to the risers'
    cref = box(xc0, yr - e - 10, xc0 + 10, yr - e)
    xb = cref.right + e + BOT_PLATE_SPACE + e
    clb = box(xb, yr - e - hcl, xb + wcl, yr - e)
    for cap in (cla, clb):                            # top plates rise straight to d2
        xc = cap.center().x
        strip = box(xc - 0.5, cap.bottom + 0.2, xc + 0.5, t['d2']['y1'])
        mim(b, cap, strip)
        b.rect('m4', strip)
        land(b, 'd2', strip.left, strip.right)
    strip = box(cref.left + 0.2, cref.bottom + 0.2, cref.left + 1.2, cref.top - 0.2)
    mim(b, cref, strip)
    b.rect('m4', strip)
    ym = cref.center().y
    b.rect('m4', box(risers['vref'].left, ym - 0.5, strip.right, ym + 0.5))   # to the vref riser
    xr = max(clb.right + e, inner.right + grw)
    if xr > g['xmax']:                                # the VSS rail must reach the plates
        b.stack(box(g['xmax'], g['ybot'] - g['rail_h'], xr, g['ybot']), 'm1', 'm3')
    for k, ln in enumerate(rdeg.links, 1):
        b.label('m1', ln, f'rdeg{k}')
    print(f'comp_ct passives: Rdeg 30 x {rdeg.lseg} um, Rr 32 x {rr.lseg} um, Cl 2 x {wcl}x{hcl}, Cref 10^2 um;'
          f' band {inner.bottom - grw:.2f}..{yr:.2f}, right {xr:.2f} (rows {g["xmax"]:.2f})')


if __name__ == '__main__':
    passives = os.environ.get('PASSIVES', '1') != '0'      # PASSIVES=0: transistors only
    make(passives).write(os.path.join(REPO, 'layout', 'comp_ct.gds'))
    # reference: parameters substituted; without the passives while they aren't drawn
    write_ref('comp_ct', 'comp_ct', dict(PARAMS, rdeg=2e6), drop=None if passives else r'^X(R|C)')
