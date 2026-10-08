# avg_sc layout: switched-cap average (xschem/gen/comp.py:avg_sc), tau = Cavg / (Cs f_phi).
#   phi1: Cs <- in (S1), phi2: Cs -> out (S2), transmission gates N 0.5 / P 1 (L 0.15),
#   local phi inverters P 1 / N 0.5. Cs = ncs x wcs^2 MIM (7 x 7 um), Cavg = nca x 30x30 MIM.
#
# Switches: rows.py (one thin column: VDD rail on top, VSS below); the transmission
# gates are pass devices (strip roles 'in'/'cs', 'cs'/'out').
# Caps: in a row under the VSS rail, each MIM bottom plate (met3, VSS) abutting the rail
# (own plates, 2 um apart: capm.2b / magic capm.11, as lpf_rc). Cs sits under the
# switches; its top plate rises on a met4 strip straight to the 'cs' track. The Cavg
# top plates share one met4 strip along their top edge, which rises to the 'out' track
# at the switch block's right edge (the 'out' pin).
# Also writes layout/ref/avg_sc.spice (parameters substituted for netgen).
# Run: tools/osic klayout -b -r layout/gen/avg_sc.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, box, snap, write_ref, REPO   # noqa: E402
from rows import Dev, Net, build, inverter_roles      # noqa: E402
from passives import mim, CAPM_ENC_M3                 # noqa: E402

PARAMS = dict(ncs=1, nca=2, wcs=7)        # as the avg_sc symbol defaults
CAVG = 30.0
GAP = 2.0                                 # bottom plate to bottom plate
NETS = {'in': Net(io='L'), 'phi1': Net(io='L'), 'phi2': Net(io='L'), 'phi1b': Net(), 'phi2b': Net(),
        'cs': Net(), 'out': Net(io='R')}


def make():
    assert PARAMS['ncs'] == 1, 'one Cs unit'
    b = Block('avg_sc')

    def fet(kind, W):
        return Fet(b, kind, W, 0.15, gate='bottom' if kind == 'p' else 'top', vt='', bulk='None')

    def inv(kind, W, g, d):
        f = fet(kind, W)
        return Dev(f, inverter_roles(f), [(g, [0])], d, rail='VDD' if kind == 'p' else 'VSS')

    def tg(kind, W, g, a, c):
        f = fet(kind, W)
        return Dev(f, [a, c], [(g, [0])], c, rail='VDD' if kind == 'p' else 'VSS')

    # phase inverters first, then S1, S2: keeps the phi lines away from 'out' at the right
    # (v1 had the phi2 inverter rightmost: out coupled 1.15 fF to phi2 vs 0.50 to phi2b,
    # and the extracted hold drift was +1.9 mV over 20 cycles)
    P = [inv('p', 1.0, 'phi1', 'phi1b'), inv('p', 1.0, 'phi2', 'phi2b'),
         tg('p', 1.0, 'phi1b', 'in', 'cs'), tg('p', 1.0, 'phi2b', 'cs', 'out')]
    N = [inv('n', 0.5, 'phi1', 'phi1b'), inv('n', 0.5, 'phi2', 'phi2b'),
         tg('n', 0.5, 'phi1', 'in', 'cs'), tg('n', 0.5, 'phi2', 'cs', 'out')]
    build(b, P, N, NETS, rail_h=1.5)
    g = b.rows
    e = CAPM_ENC_M3
    yr = g['ybot'] - g['rail_h']                 # VSS rail bottom edge: the plates hang from it
    tcs, tout = g['tracks']['cs'], g['tracks']['out']

    # Cs under the cs track's span; its met4 strip rises straight to the track
    wcs = PARAMS['wcs']
    xc = (g['xs']['cs'][0] + g['xs']['cs'][1]) / 2
    cs = box(xc - wcs / 2, yr - e - wcs, xc + wcs / 2, yr - e)
    s_cs = box(xc - 0.5, cs.bottom + 0.2, xc + 0.5, tcs['y1'])
    mim(b, cs, s_cs)
    b.rect('m4', s_cs)
    b.via('via3', box(s_cs.left, tcs['y0'], s_cs.right, tcs['y1']), enc=(0.065, 0.09))

    # Cavg: nca caps to the right, plates GAP apart; one met4 strip along their top edge
    x0 = cs.right + e + GAP + e
    caps = []
    for k in range(PARAMS['nca']):
        caps.append(box(x0 + k * (CAVG + 2 * e + GAP), yr - e - CAVG, x0 + k * (CAVG + 2 * e + GAP) + CAVG, yr - e))
    rx1 = g['xmax']                               # riser up to the out track at the switch block's edge
    rx0 = rx1 - 1.0
    assert rx0 > s_cs.right + 0.3, 'out riser would hit the Cs strip'
    # VSS rail on across the caps: each bottom plate abuts it (as lpf_rc)
    b.stack(box(g['xmax'], g['ybot'] - g['rail_h'], caps[-1].right + e, g['ybot']), 'm1', 'm3')
    strip = box(min(rx0, caps[0].left), caps[0].top - 1.6, caps[-1].right, caps[0].top - 0.2)
    for c in caps:
        mim(b, c, strip)
    b.rect('m4', strip)
    riser = box(rx0, strip.bottom, rx1, tout['y1'])
    b.rect('m4', riser)
    b.via('via3', box(rx0, tout['y0'], rx1, tout['y1']), enc=(0.065, 0.09))
    b.label('m4', strip, 'out')
    print(f'avg_sc: Cs {wcs}x{wcs} um, Cavg {PARAMS["nca"]} x {CAVG:g}x{CAVG:g} um')
    return b


if __name__ == '__main__':
    make().write(os.path.join(REPO, 'layout', 'avg_sc.gds'))
    write_ref('avg_sc', 'avg_sc', PARAMS)
