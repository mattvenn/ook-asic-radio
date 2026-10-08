# comp_ct layout: continuous comparator (xschem/gen/comp.py:comp_ct).
#   lvt NMOS pair M1/M2 (W 20 / L 1, nf 4) + lvt PMOS mirror Mp1/Mp2 (4 / 1); trim pair
#   M3/M4 (lvt 2 / 1) with split tails Mta (2 / 2 x2) and Rdeg (xhigh, 2 MOhm); VDD/2
#   reference Rr1/Rr2 (xhigh L 136) + Cref (10x10 MIM); Cl (22x22 MIM) on d2; stage 2
#   Mp3 (lvt 4 / 1) + Mn3 (2 / 2 x5); output inverter; bias diode Mb, tail Mt1 (2 / 2 x10).
#
# Matching (docs/layout.md checklist): each pair split into halves placed A B B A
# (1D common centroid), same orientation, with rail-tied dummies (rows.dummy) either
# side. N row: [d] M1 M2 M2 M1 [d d] bias + stage 2 + inverter [d d] M3 M4 M4 M3 [d];
# P row: [d] Mp1 Mp2 Mp2 Mp1 [d d] Mp3 Mip.
# Run: tools/osic klayout -b -r layout/gen/comp_ct.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, box, snap, ring, write_ref, REPO   # noqa: E402
from rows import Dev, Net, build, inverter_roles, dummy   # noqa: E402
from passives import PolyRes, mim, CAPM_ENC_M3            # noqa: E402

PARAMS = dict(w1=20, l1=1, mt1=10, rdeg=2e6, mta=2, lref=136, wcl=22)   # radio_analog's xcomp
NETS = {'inp': Net(io='L'), 'inn': Net(io='L'), 'trim': Net(io='L'), 'ibias': Net(io='L'), 'out': Net(io='R'),
        'tail': Net(), 'd1': Net(), 'd2': Net(), 'sa': Net(), 'sb': Net(), 'vref': Net(), 'o2': Net()}


def make(passives=True):
    b = Block('comp_ct')
    P_ = dict(PARAMS)

    def fet(kind, W, l, vt='', nf=1):
        return Fet(b, kind, W, l, nf=nf, gate='bottom' if kind == 'p' else 'top', vt=vt, bulk='None')

    def dev(kind, W, l, vt, gate, drain, nf=1, roles=None):
        f = fet(kind, W, l, vt, nf)
        return Dev(f, roles or inverter_roles(f), [(gate, list(range(f.nf)))], drain,
                   rail='VDD' if kind == 'p' else 'VSS')

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

    N = ([dmy('n', w1 / 4, l1, 'lvt'), pair('inp', 'd1'), pair('inn', 'd2'), pair('inn', 'd2'), pair('inp', 'd1'),
          dmy('n', w1 / 4, l1, 'lvt'), dmy('n', 2, 2, '')]
         + [dev('n', 2, 2, '', 'ibias', 'ibias'),                          # Mb (diode)
            dev('n', 2 * P_['mt1'], 2, '', 'ibias', 'tail', nf=P_['mt1']),  # Mt1
            dev('n', 2 * P_['mta'], 2, '', 'ibias', 'sa', nf=P_['mta']),    # Mta_sa
            dev('n', 2 * P_['mta'], 2, '', 'ibias', 'sb', nf=P_['mta']),    # Mta_sb
            dev('n', 10, 2, '', 'ibias', 'o2', nf=5),                       # Mn3
            dev('n', 1, 0.15, '', 'o2', 'out')]                             # Min
         + [dmy('n', 2, 2, ''), dmy('n', 1, 1, 'lvt'),
            trim('vref', 'd1', 'sa'), trim('trim', 'd2', 'sb'), trim('trim', 'd2', 'sb'), trim('vref', 'd1', 'sa'),
            dmy('n', 1, 1, 'lvt')])
    P = ([dmy('p', 2, 1, 'lvt'), mirror('d1'), mirror('d2'), mirror('d2'), mirror('d1'), dmy('p', 2, 1, 'lvt'),
          dmy('p', 4, 1, 'lvt'),
          dev('p', 4, 1, 'lvt', 'd2', 'o2'),                                # Mp3
          dev('p', 2, 0.15, '', 'o2', 'out')])                              # Mip
    build(b, P, N, NETS, rail_h=1.5)
    if passives:
        add_passives(b, P_)
    return b


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
    """Rdeg (sa-sb), the Rr1/Rr2 VDD/2 divider (tap: vref) in a p-tap ring, Cl (d2) and
    Cref (vref), all hanging below the VSS rail. Every connection rises on met4."""
    g = b.rows
    e = CAPM_ENC_M3
    if os.environ.get('TRACKS'):
        for n, tt in g['tracks'].items():
            print(f'TRACK {n:6s} y {tt["y0"]:6.2f} x {g["xs"][n][0]:6.2f}..{g["xs"][n][1]:6.2f} shares {tt["nets"]}')
    yr = g['ybot'] - g['rail_h']                      # rail bottom edge
    t = g['tracks']
    # Placement follows the channel tracks: sa/sb/vref only exist at the right (the trim
    # pair), vref can't extend left past ibias (they share a track); d2 runs across.
    # So: Cl at the left (riser to d2); the resistor ring from x ~ 50 (Rdeg ends -> sa, sb;
    # Rr tap -> vref); Cref right of the ring, under vref.
    wcl = P_['wcl']
    cl = box(0.2 + e, yr - e - wcl, 0.2 + e + wcl, yr - e)
    # --- resistors: Rdeg (14 x ~19.4 um), Rr1+Rr2 (16 x 17 um, vref at the middle link)
    rdeg = PolyRes(b, P_['rdeg'] / 7.37e3, 14, pad_w=0.5)
    rr = PolyRes(b, 2 * P_['lref'], 16, pad_w=0.5)
    grw, m = 0.4, 0.6
    inner_top = yr - grw
    x0 = max(50.0, g['xs']['sa'][0])                    # Rdeg's first end lands on sa's track
    top = inner_top - m - (rdeg._bbox.top - rdeg._poly.top)
    rdeg.place(x0, top - (rdeg._poly.top - rdeg._poly.bottom))
    xr = rdeg.bbox.right + 2.0
    rr.place(xr - (rr._bbox.left - rr._poly.left), top - (rr._poly.top - rr._poly.bottom))
    bot = min(rdeg.bbox.bottom, rr.bbox.bottom) - 1.4   # room for the drop pads
    inner = box(rdeg.bbox.left - m, bot, rr.bbox.right + m, inner_top)
    ring(b, inner, 'p', grw)
    b.rect('m1', box(inner.left - grw, inner_top, inner.right + grw, yr + 0.01))   # ring onto the rail
    cref = box(inner.right + grw + 2.0 + e, yr - e - 10, inner.right + grw + 2.0 + e + 10, yr - e)
    # --- caps: plates abut the rail; top plates rise straight to their tracks
    for cap, net in ((cl, 'd2'), (cref, 'vref')):
        xc = cap.center().x
        strip = box(xc - 0.5, cap.bottom + 0.2, xc + 0.5, t[net]['y1'])
        mim(b, cap, strip)
        b.rect('m4', strip)
        land(b, net, strip.left, strip.right)
    if cref.right + e > g['xmax']:                    # the VSS rail must reach Cref's plate
        b.stack(box(g['xmax'], g['ybot'] - g['rail_h'], cref.right + e, g['ybot']), 'm1', 'm3')

    def drop(head, net=None, to_rail=None):
        """m1 pad under a bottom head, via stack to met4, riser up to net's track or the rail."""
        xc = head.center().x
        pad = box(xc - 0.3, head.bottom - 0.8, xc + 0.3, head.bottom - 0.2)
        b.rect('m1', box(head.left, pad.bottom, head.right, head.top))
        b.stack(pad, 'm1', 'm4')
        if net:
            riser = box(xc - 0.3, pad.bottom, xc + 0.3, t[net]['y1'])
            b.rect('m4', riser)
            land(b, net, riser.left, riser.right)
        else:                                         # VDD: up to the VDD rail (m3), via3 there
            yv = g['ytop']
            riser = box(xc - 0.3, pad.bottom, xc + 0.3, yv + g['rail_h'])
            b.rect('m4', riser)
            b.via('via3', box(riser.left, yv, riser.right, yv + g['rail_h']), enc=(0.065, 0.09))
    drop(rdeg.ends[0], 'sa')
    drop(rdeg.ends[1], 'sb')
    drop(rr.ends[0])                                  # Rr1 top end: VDD
    tap = rr.links[7]                                 # between segments 7 and 8: vref
    drop(box(tap.center().x - 0.25, tap.bottom, tap.center().x + 0.25, tap.top), 'vref')
    vss = rr.ends[1]                                  # Rr2 bottom end: to the ring (VSS)
    b.rect('m1', box(vss.left, inner.bottom - grw / 2, vss.right, vss.top))
    for k, ln in enumerate(rdeg.links, 1):
        b.label('m1', ln, f'rdeg{k}')
    print(f'comp_ct passives: Rdeg 14 x {rdeg.lseg} um, Rr 16 x {rr.lseg} um, Cl {wcl}^2, Cref 10^2 um')


if __name__ == '__main__':
    passives = os.environ.get('PASSIVES', '1') != '0'      # PASSIVES=0: transistors only
    make(passives).write(os.path.join(REPO, 'layout', 'comp_ct.gds'))
    # reference: parameters substituted; without the passives while they aren't drawn
    write_ref('comp_ct', 'comp_ct', dict(PARAMS, rdeg=2e6), drop=None if passives else r'^X(R|C)')
