# avg_sc layout: switched-cap average (xschem/gen/comp.py:avg_sc), tau = Cavg / (Cs f_phi).
#   phi1: Cs <- in (S1), phi2: Cs -> out (S2), transmission gates N 0.5 / P 1 (L 0.15),
#   local phi inverters P 1 / N 0.5. Cs = ncs x wcs^2 MIM (7 x 7 um), Cavg = nca x 30x30 MIM.
#
# v2 (offset, area, pins). Every charge per cycle that a clock couples onto cs or out
# shifts the average by dQ/Cs (Cavg doesn't dilute it), and v1's phi/phib imbalance
# (~0.2 fF) gave ~4 mV. So the channel is mirror-symmetric by construction:
#   tracks top to bottom: phi2b phi1b | VDD shield | in out cs | VSS shield | phi1 phi2
#   - phib (P gates) on top, phi (N gates) at the bottom, mirrored: each TG's P and N
#     stubs sit at the same x, so a signal stub crosses phib going up exactly as its
#     partner crosses phi going down; gate stubs cross no signal track;
#   - the shields stop phib/phi coupling sideways into in/cs;
#   - nothing crosses the channel: cs and out leave on met4 risers right of the ring
#     (only in/out/cs tracks reach there), the phi pins rise on met4 at the left end,
#     over the inverters, where only clock tracks run.
# Floorplan: Cavg pair at the left (full height); the switch column at the right with
# Cs hanging under its VSS rail; out's met4 strip along the bottom of the Cavg plates.
# Pins: phi1, phi2 on the top edge (met4); in, out on the right edge (met3), next to
# each other for comp_ct (inn, inp). Mirror the cell at the top level as needed.
# Also writes layout/ref/avg_sc.spice (parameters substituted for netgen).
# Run: tools/osic klayout -b -r layout/gen/avg_sc.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, box, write_ref, REPO      # noqa: E402
from rows import Dev, Net, build, inverter_roles     # noqa: E402
from passives import mim, CAPM_ENC_M3                # noqa: E402

PARAMS = dict(ncs=1, nca=2, wcs=7)        # as the avg_sc symbol defaults
CAVG = 30.0
GAP = 2.0                                 # Cavg bottom plate to bottom plate
CAP_SW = 2.0                              # Cavg plate to the switch column's met3 (>= 1.2)
NETS = {n: Net() for n in ('in', 'phi1', 'phi2', 'phi1b', 'phi2b', 'cs', 'out', 'shp', 'shn')}
ORDER = [['phi2b'], ['phi1b'], ['shp'], ['in'], ['out'], ['cs'], ['shn'], ['phi1'], ['phi2']]
V3 = dict(enc=(0.065, 0.09))


def make():
    assert PARAMS['ncs'] == 1, 'one Cs unit'
    b = Block('avg_sc')

    def fet(kind, W):
        return Fet(b, kind, W, 0.15, gate='bottom' if kind == 'p' else 'top', vt='', bulk='None')

    def inv(kind, W, g, d, flip=False):
        f = fet(kind, W)
        roles = inverter_roles(f)[::-1] if flip else inverter_roles(f)
        return Dev(f, roles, [(g, [0])], d, rail='VDD' if kind == 'p' else 'VSS')

    def tg(kind, W, g, a, c):
        f = fet(kind, W)
        return Dev(f, [a, c], [(g, [0])], c, rail='VDD' if kind == 'p' else 'VSS')

    # phi2's inverter flipped: its rail strip, not its phi2b drain, faces S1's in strip
    # (v2 first cut: in coupled 0.72 fF to phi2b against 0.07 to phi2 through that gap)
    P = [inv('p', 1.0, 'phi1', 'phi1b'), inv('p', 1.0, 'phi2', 'phi2b', True),
         tg('p', 1.0, 'phi1b', 'in', 'cs'), tg('p', 1.0, 'phi2b', 'cs', 'out')]
    N = [inv('n', 0.5, 'phi1', 'phi1b'), inv('n', 0.5, 'phi2', 'phi2b', True),
         tg('n', 0.5, 'phi1', 'in', 'cs'), tg('n', 0.5, 'phi2', 'cs', 'out')]
    build(b, P, N, NETS, rail_h=1.5, order=ORDER)
    g = b.rows
    T, xs = g['tracks'], g['xs']
    e = CAPM_ENC_M3
    ytop, ybot, rh, xm = g['ytop'], g['ybot'], g['rail_h'], g['xmax']
    top, bot = ytop + rh, ybot - rh                       # switch column extent (rails)

    def hband(net, x0, x1):                               # met3 on net's track
        return b.rect('m3', box(x0, T[net]['y0'], x1, T[net]['y1']))

    def drop(net, x0, x1, y_end):                         # met4 from net's track to y_end
        t = T[net]
        b.rect('m4', box(x0, min(t['y0'], y_end), x1, max(t['y1'], y_end)))
        b.via('via3', box(x0, t['y0'], x1, t['y1']), **V3)

    # riser zone right of the ring (left to right): shield risers, cs, out; then the edge
    x_shp, x_shn, x_cs, x_out = xm + 0.3, xm + 1.1, xm + 1.9, xm + 3.8
    XR = x_out + 1.0 + 0.3
    for y0, y1 in ((ytop, top), (bot, ybot)):             # rails on to the edge
        b.stack(box(xm, y0, XR, y1), 'm1', 'm3')
    # shields: from just left of the signal stubs to their riser, onto VDD / VSS
    xsig = min(xs[n][0] for n in ('in', 'cs', 'out')) - 0.5
    hband('shp', xsig, x_shp + 0.5)
    hband('shn', xsig, x_shn + 0.5)
    drop('shp', x_shp, x_shp + 0.5, top)
    b.via('via3', box(x_shp, ytop, x_shp + 0.5, top), **V3)
    drop('shn', x_shn, x_shn + 0.5, bot)
    b.via('via3', box(x_shn, bot, x_shn + 0.5, ybot), **V3)
    # in, out: tracks on to the right edge (pins); cs to its riser
    for n in ('in', 'out'):
        r = hband(n, xs[n][1], XR)
        b.pin('m3', box(XR - 0.5, r.bottom, XR, r.top), n)
    hband('cs', xs['cs'][1], x_cs + 1.0)

    # phi pins: met4 from the tracks' left ends up to the top edge, left of phi1b's span
    x_p1, x_p2 = 0.0, 0.7
    assert x_p2 + 0.4 + 0.1 < xs['phi1b'][0], 'phi2 riser would sit under phi1b'
    for n, x0 in (('phi1', x_p1), ('phi2', x_p2)):
        hband(n, x0, xs[n][0])
        drop(n, x0, x0 + 0.4, top)
        b.pin('m4', box(x0, top - 0.5, x0 + 0.4, top), n)

    # Cs under the VSS rail (its bottom plate abuts it), the cs riser over its right side
    wcs = PARAMS['wcs']
    cs = box(x_cs + 1.3 - wcs, bot - e - wcs, x_cs + 1.3, bot - e)
    assert cs.right + e + 0.3 < x_out, 'Cs plate would reach the out riser'
    drop('cs', x_cs, x_cs + 1.0, cs.bottom + 0.2)
    mim(b, cs, box(x_cs, cs.bottom + 0.2, x_cs + 1.0, cs.top))

    # Cavg: nca caps left of the column, top plates level with the column top
    pitch = CAVG + 2 * e + GAP
    xr = min(0.0, x_p1) - CAP_SW - e                      # last capm's right edge
    yt = top - e
    caps = [box(xr - CAVG - k * pitch, yt - CAVG, xr - k * pitch, yt) for k in range(PARAMS['nca'])][::-1]
    yb = caps[0].bottom
    assert yb + 0.2 + 1.4 < cs.bottom - e - 0.3, 'out strip would run into Cs'
    # out: riser at the right down to a met4 strip along the Cavg plates' bottom edge
    strip = box(caps[0].left, yb + 0.2, x_out + 1.0, yb + 1.6)
    for c in caps:
        mim(b, c, strip)
    b.rect('m4', strip)
    drop('out', x_out, x_out + 1.0, strip.top)
    b.label('m4', strip, 'out')
    # VSS to the Cavg bottom plates: the rail's met3 on left into the plates, and across the gap
    b.rect('m3', box(caps[0].left - e, bot, 0.0, ybot))
    print(f'avg_sc: Cs {wcs}x{wcs} um, Cavg {PARAMS["nca"]} x {CAVG:g}x{CAVG:g} um')
    return b


if __name__ == '__main__':
    make().write(os.path.join(REPO, 'layout', 'avg_sc.gds'))
    write_ref('avg_sc', 'avg_sc', PARAMS)
