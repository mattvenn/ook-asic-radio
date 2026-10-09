# dbg_tg layout: debug transmission gate a <-> b (det <-> ua[2] pad), on when en = 1
# (xschem/gen/dbg.py:dbg_tg), wn=2 wp=4:
#   local inverter en -> enb (Mip P 1 / Min N 0.5); pass gate Mn (N wn, gate en) and
#   Mp (P wp, gate enb) between a and b. Thin 1.8 V devices, L 0.15.
# Built with rows.py: PMOS row [Mip, Mp] over NMOS row [Min, Mn], VDD rail on top, VSS on
# the bottom. rows.py routes one signal net per device, so the pass devices' left strip
# is their 'drain' (a, through the channel to the left edge) and this generator wires the
# right strips (b) itself: via1 on each, one met2 bar from the P strip down past the N
# strip (over the rings and across the channel's met3) through the VSS rail (no met2 there).
# Pins (floorplan, layout/floorplan/pins.md): a and b on the south edge (a west of b; a on
# met3 down the west edge through a gap in the rail's met3), en on the east edge (met3).
# Currents are uA (det through 8 kOhm): minimum widths.
# Also writes layout/ref/dbg_tg.spice (wn / wp substituted; netgen can't evaluate them).
# Run: tools/osic klayout -b -r layout/gen/dbg_tg.py
import os
import re
import subprocess
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, REPO, box          # noqa: E402
from rows import Dev, Net, build, inverter_roles   # noqa: E402

PARAMS = dict(wn=2, wp=4)
NETS = {'en': Net(io='R', pin=False), 'a': Net(io='L', pin=False), 'enb': Net()}
LG = 0.15


def make():
    b = Block('dbg_tg')

    def fet(kind, W):
        return Fet(b, kind, W, LG, gate='bottom' if kind == 'p' else 'top', vt='', bulk='None')
    mip, min_ = fet('p', 1.0), fet('n', 0.5)
    mp, mn = fet('p', PARAMS['wp']), fet('n', PARAMS['wn'])
    P = [Dev(mip, inverter_roles(mip), [('en', [0])], 'enb', rail='VDD'),
         Dev(mp, ['D', None], [('enb', [0])], 'a', rail='VDD')]
    N = [Dev(min_, inverter_roles(min_), [('en', [0])], 'enb', rail='VSS'),
         Dev(mn, ['D', None], [('en', [0])], 'a', rail='VSS')]
    build(b, P, N, NETS, rail_h=2.0)

    # b: the pass devices' right strips (rows.py drew them as met1 strips, unconnected).
    # The cell is narrow, so the channel is full of gate stubs next to these strips: b
    # leaves each strip at its rail-side end on met2, runs right over the ring, and a met2
    # bar outside the rings joins P and N (crossing the channel's met3 tracks); it is the pin.
    bb = b.cell.dbbox()
    xmax = bb.right                                   # the nwell edge, just past the rails' end
    sp, sn = mp.strips[1], mn.strips[1]
    w = 0.3
    xbar = xmax + 0.3
    jogs = []
    for s_, top in ((sp, True), (sn, False)):
        xc = s_.center().x
        v = (box(xc - w / 2, s_.top - 0.45, xc + w / 2, s_.top - 0.05) if top
             else box(xc - w / 2, s_.bottom + 0.05, xc + w / 2, s_.bottom + 0.45))
        b.rect('m1', v)
        b.via('via1', v, enc=(0.055, 0.085))
        jogs.append(b.rect('m2', box(v.left, v.bottom, xbar + w, v.top)))
    # the bar runs on down through the VSS rail (its met2 stops short) to the south edge
    b.rect('m2', box(xbar, bb.bottom, xbar + w, jogs[0].top))
    b.pin('m2', box(xbar, bb.bottom, xbar + w, bb.bottom + 0.5), 'b')
    # extend the rails (metal only: abutting via arrays can break via spacing) to the new edge
    for y0, y1, lays in ((bb.top - 2.0, bb.top, ('m1', 'm2', 'm3')), (bb.bottom, bb.bottom + 2.0, ('m1', 'm3'))):
        for lay in lays:
            b.rect(lay, box(xmax - 1.0, y0, xbar + w, y1))

    # en: its track (io 'R') goes on east over the b bar (met3 over met2) to the east edge
    te = b.rows['tracks']['en']
    b.rect('m3', box(xmax - 0.5, te['y0'], xbar + w, te['y1']))
    b.pin('m3', box(xbar + w - 0.5, te['y0'], xbar + w, te['y1']), 'en')
    # a: its track (io 'L') turns down the west edge on met3, over the N ring, and through
    # a gap in the VSS rail's met3 to the south edge (west of b)
    ta = b.rows['tracks']['a']
    b.clear(('m3', 'via2'), box(bb.left, bb.bottom, bb.left + 0.5 + 0.4, bb.bottom + 2.0))
    b.rect('m3', box(bb.left, ta['y0'], 0, ta['y1']))
    b.rect('m3', box(bb.left, bb.bottom, bb.left + 0.5, ta['y1']))
    b.pin('m3', box(bb.left, bb.bottom, bb.left + 0.5, bb.bottom + 0.5), 'a')
    return b


def write_ref():
    tmp = os.path.join(REPO, 'build', 'lay', 'ref')
    os.makedirs(tmp, exist_ok=True)
    subprocess.run(['xschem', '-n', '-s', '-q', '--tcl', 'set top_subckt 1; set lvs_netlist 1', '-o', tmp,
                    'xschem/dbg_tg.sch'], cwd=REPO, capture_output=True)
    src = open(os.path.join(tmp, 'dbg_tg.spice')).read()
    out = []
    for ln in src.splitlines():
        if ln.startswith('.subckt dbg_tg'):
            ln = re.sub(r'\s+\w+=\S+', '', ln)
        ln = re.sub(r"W='([^']+)'", lambda m: f'W={eval(m.group(1), {}, dict(PARAMS)):g}', ln)
        out.append(ln)
    os.makedirs(os.path.join(REPO, 'layout', 'ref'), exist_ok=True)
    with open(os.path.join(REPO, 'layout', 'ref', 'dbg_tg.spice'), 'w') as fh:
        fh.write(f'* dbg_tg: xschem/dbg_tg.sch with {PARAMS} (layout/gen/dbg_tg.py)\n' + '\n'.join(out) + '\n')


if __name__ == '__main__':
    make().write(os.path.join(REPO, 'layout', 'dbg_tg.gds'))
    write_ref()
