# tx_drv layout v2: one antenna arm, out = in & en (xschem/gen/tx.py:tx_drv).
#   thick NAND2, then inverters x4 per stage: N 0.42 / 1.68 / 6.72 / 26.88 / 48, P = 3 N, L 0.5.
#
# Floorplan (left to right = signal flow):
#   VAPWR rail (met1+2+3)
#   PMOS row, fingers <= 8 um, one shared n-tap guard ring (nwell)
#   routing channel: one met3 track per net, met2 stubs up/down to the devices
#   NMOS row, fingers <= 4.5 um, one shared p-tap guard ring
#   VSS rail (met1+2+3)
# The output stage sits at the right end of both rows; its drain bars (met2+met3)
# join a met2+met3 riser on the right edge, which is the 'out' pin.
#
# Wire widths and cut counts come from the measured currents (sim/tx/tb_tx_drv.py,
# tt, per arm; docs/layout.md) at 2x margin on the tech-LEF limits:
#   VAPWR 6.65 mA avg / 9.45 rms (stage 5 PMOS sources), VSS 2.3 / 3.6,
#   out 9.8 mA rms, y4 ~1.45 mA rms per side, y3 ~0.4, earlier nets << 1 mA.
# v1 (one column per stage) is in git history / build/lay/tx_drv_v1.py.
# Run: tools/osic klayout -b -r layout/gen/tx_drv.py
import os
import sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, box, snap, ring, cuts_needed, REPO   # noqa: E402

DRV_N = [0.42, 1.68, 6.72, 26.88, 48]   # as xschem/gen/tx.py
LG = 0.5
HP, HN = 8.0, 4.5      # max finger height (um), P and N rows: rows come out about equal length
RAIL_H = 3.0           # rail height on each of met1/2/3
DGAP = 0.9             # diffusion gap between neighbouring devices in a row
RING_W = 0.4
RING_X = 0.45          # ring hole to diffusion, sides
RING_RAIL = 0.47       # ring hole to diffusion, rail side
RING_CH = 0.45         # ring hole to the gate straps, channel side
STRIP_W = 0.45         # S/D met1 strip width (pcell draws 0.23)
M3S = 0.3              # met3 spacing
M2S = 0.145            # met2 spacing (min 0.14)
V2ENC = (0.04, 0.085)  # via2 in a narrow vertical stub: 0.04 sides, 0.085 along it
OUT_W = 3.0            # out riser width (met2+met3)

# per net: (stub width at drains, stub width at gates, track width, RMS current mA for the cut check)
NETS = {
    'in': (0.3, 0.3, 0.5, 0.05), 'en': (0.3, 0.3, 0.5, 0.05),
    'y0': (0.28, 0.3, 0.5, 0.05), 'y1': (0.3, 0.3, 0.5, 0.1), 'y2': (0.4, 0.4, 0.5, 0.2),
    'y3': (0.8, 0.8, 0.6, 0.45), 'y4': (1.6, 2.0, 1.0, 1.45),
}


class Dev:
    """A FET in a row: strip roles ('R' rail, 'D' drain, None), gate groups [(net, [fingers])]."""

    def __init__(self, fet, roles, gates, drain, hb):
        self.f, self.roles, self.gates, self.drain, self.hb = fet, roles, gates, drain, hb


def devices(b):
    P, N = [], []
    p = Fet(b, 'p', 2 * 1.26, LG, nf=2, gate='bottom', bulk='None')
    n = Fet(b, 'n', 2 * 0.84, LG, nf=2, gate='top', bulk='None')
    P.append(Dev(p, ['R', 'D', 'R'], [('in', [0]), ('en', [1])], 'y0', 0.5))
    N.append(Dev(n, ['D', None, 'R'], [('in', [0]), ('en', [1])], 'y0', 0.5))
    for i, wn in enumerate(DRV_N, 1):
        g, d = f'y{i - 1}', ('out' if i == len(DRV_N) else f'y{i}')
        for row, kind, W, H in ((P, 'p', 3 * wn, HP), (N, 'n', wn, HN)):
            f = Fet(b, kind, W, LG, gate='bottom' if kind == 'p' else 'top', bulk='None', nfmax=H)
            roles = ['R' if k % 2 == 0 else 'D' for k in range(f.nf + 1)]
            # drain bar height: enough via1 rows for the net's current
            hb = {'out': 3.0 if kind == 'p' else 2.0, 'y4': 2.0, 'y3': 1.3, 'y2': 0.8}.get(d, 0.5)
            row.append(Dev(f, roles, [(g, list(range(f.nf)))], d, hb))
    return P, N


def assign_tracks(P, N):
    """Left-edge track assignment from the devices' x extents; the inputs start at x = 0."""
    span = {}
    for d in P + N:
        for net in [g for g, _ in d.gates] + ([d.drain] if d.drain != 'out' else []):
            a, c = span.get(net, (1e9, -1e9))
            span[net] = (min(a, d.f.diff.left), max(c, d.f.diff.right))
    for n in ('in', 'en'):
        span[n] = (0, span[n][1])
    tracks = []
    for net in sorted(span, key=lambda n: span[n][0]):
        a, c = span[net]
        for t in tracks:
            if t['end'] + 1.0 < a:
                t['nets'].append(net)
                t['end'] = c
                t['w'] = max(t['w'], NETS[net][2])
                break
        else:
            tracks.append(dict(nets=[net], end=c, w=NETS[net][2]))
    return tracks


def build():
    b = Block('tx_drv')
    P, N = devices(b)

    # --- horizontal placement
    x = 0.6
    for d in P:
        d.f.place(x, 0)
        x = d.f.diff.right + DGAP
    x = 0.6
    for d, dp in zip(N, P):              # keep each N under its P where the row allows
        x = max(x, dp.f.diff.left)
        d.f.place(x, 0)
        x = d.f.diff.right + DGAP
    sh = P[-1].f.diff.right - N[-1].f.diff.right      # line up the output stage's right edges
    if sh > 0:
        N[-1].f.place(N[-1].f.x + sh, 0)
    else:
        P[-1].f.place(P[-1].f.x - sh, 0)

    # --- vertical: channel height from the tracks, rows either side
    tracks = assign_tracks(P, N)
    ch_h = sum(t['w'] for t in tracks) + M3S * (len(tracks) + 1)
    padP = min(p.bottom for d in P for p in d.f.pads)                  # below the P diff bottom (at y 0)
    padN = max(max(p.top for p in d.f.pads) - d.f.w for d in N)       # above the N diff top (diff at 0..w)
    for d in P:
        d.f.place(d.f.x, snap(ch_h / 2 + RING_W + RING_CH - padP))
    yNt = snap(-ch_h / 2 - RING_W - RING_CH - padN)                   # N diff tops
    for d in N:
        d.f.place(d.f.x, yNt - d.f.w)
    for d in P + N:
        d.f.commit()
    # hvntm (HV n-tip implant) as one rectangle over the NMOS row: the ringless nfet
    # pcells leave notches (hvntm.2) and neighbours sit closer than its 0.7 spacing
    b.rect('hvntm', box(min(d.f.diff.left for d in N) - 0.185, min(d.f.diff.bottom for d in N) - 0.185,
                        max(d.f.diff.right for d in N) + 0.185, max(d.f.diff.top for d in N) + 0.185))

    # --- rings, wells, rails
    def extent(row, up):
        xs0 = min(d.f.diff.left for d in row) - RING_X
        xs1 = max(d.f.diff.right for d in row) + RING_X
        if up:
            return box(xs0, min(p.bottom for d in row for p in d.f.pads) - RING_CH,
                       xs1, max(d.f.diff.top for d in row) + RING_RAIL)
        return box(xs0, min(d.f.diff.bottom for d in row) - RING_RAIL,
                   xs1, max(p.top for d in row for p in d.f.pads) + RING_CH)
    inP, inN = extent(P, True), extent(N, False)
    xl, xr = min(inP.left, inN.left), max(inP.right, inN.right)
    inP = box(xl, inP.bottom, xr, inP.top)
    inN = box(xl, inN.bottom, xr, inN.top)
    rP = ring(b, inP, 'n', RING_W)
    rN = ring(b, inN, 'p', RING_W)
    xmax = snap(rP.right + 0.6 + OUT_W)                  # out riser beyond the rings
    b.rect('nwell', box(rP.left - 0.5, rP.bottom - 0.5, rP.right + 0.5, rP.top + 0.5))
    b.rect('hvi', box(min(0, rP.left - 0.5), rN.bottom - 0.5, rP.right + 0.5, rP.top + 0.5))
    ytop, ybot = rP.top - RING_W, rN.bottom + RING_W     # rails overlap the rings' rail-side segments
    b.stack(box(0, ytop, xmax, ytop + RAIL_H), 'm1', 'm3')
    b.stack(box(0, ybot - RAIL_H, xmax, ybot), 'm1', 'm3')
    b.pin('m3', box(0, ytop, xmax, ytop + RAIL_H), 'VAPWR')
    b.pin('m3', box(0, ybot - RAIL_H, xmax, ybot), 'VSS')

    # track y positions, top to bottom inside the channel
    y = rP.bottom - M3S
    for t in tracks:
        t['y1'], t['y0'] = snap(y), snap(y - t['w'])
        y = t['y0'] - M3S
    tby = {n: t for t in tracks for n in t['nets']}
    xs = defaultdict(list)          # per net: stub x extents on its track
    report = []
    rx0 = xmax - OUT_W                                # out riser x; its y span comes from the output bars
    outbars = []

    for row, up in ((P, True), (N, False)):
        for d in row:
            f = d.f
            # S/D strips widened; rail strips run into the ring's rail-side segment (met1)
            dstrips = []
            for s, r in zip(f.strips, d.roles):
                xc = s.center().x
                if r == 'R':
                    y0, y1 = (s.bottom, ytop + RING_W) if up else (ybot - RING_W, s.top)
                else:
                    y0, y1 = s.bottom, s.top
                b.rect('m1', box(xc - STRIP_W / 2, y0, xc + STRIP_W / 2, y1))
                if r == 'D':
                    dstrips.append(s)
            # drain bar (met2) at the channel end of the diffusion, via1 on each drain strip
            hb = min(d.hb, f.w - 0.3)
            yb0, yb1 = ((f.diff.bottom + 0.14, f.diff.bottom + 0.14 + hb) if up
                        else (f.diff.top - 0.14 - hb, f.diff.top - 0.14))
            nv = 0
            for s in dstrips:
                xc = s.center().x
                v0, v1 = max(yb0, s.bottom), min(yb1, s.top)
                if v1 - v0 < 0.32:
                    yc = s.center().y
                    v0, v1 = yc - 0.16, yc + 0.16
                    b.rect('m1', box(xc - STRIP_W / 2, v0, xc + STRIP_W / 2, v1))
                    yb0, yb1 = min(yb0, v0), max(yb1, v1)
                nv += b.via('via1', box(xc - STRIP_W / 2, v0, xc + STRIP_W / 2, v1), enc=(0.07, 0.085))
            bx0 = dstrips[0].center().x - STRIP_W / 2
            bx1 = dstrips[-1].center().x + STRIP_W / 2
            # gate stubs (met2) start at the group's first pad
            gstubs = []
            for k, (net, fingers) in enumerate(d.gates):
                pads = [f.pads[i] for i in fingers]
                sy0, sy1 = min(p.bottom for p in pads), max(p.top for p in pads)
                if sy1 - sy0 < 0.32:                     # single row of pads: make room for via1
                    sy0, sy1 = (sy1 - 0.32, sy1) if up else (sy0, sy0 + 0.32)
                w = NETS[net][1]
                if k == 0:                               # first gate group: stub on its left edge
                    gstubs.append([net, pads[0].left, pads[0].left + w, sy0, sy1, pads])
                else:                                    # later groups (NAND en): on the right edge
                    gstubs.append([net, pads[-1].right - w, pads[-1].right, sy0, sy1, pads])
            # drain stub at the drain strip furthest from the gate stubs, kept clear of them
            dst = None
            if d.drain != 'out':
                wd = NETS[d.drain][0]
                best = max(dstrips, key=lambda s: min(abs(s.center().x - (g[1] + g[2]) / 2) for g in gstubs))
                dx0 = best.center().x - wd / 2
                for g in gstubs:
                    if dx0 + wd > g[1] - M2S and dx0 < g[2] + M2S:
                        dx0 = g[2] + M2S if best.center().x >= (g[1] + g[2]) / 2 else g[1] - M2S - wd
                dst = (snap(dx0), snap(dx0 + wd))
                bx0, bx1 = min(bx0, dst[0]), max(bx1, dst[1])
            for g in gstubs:                             # gate stubs stop short of the drain stub
                if dst and g[2] > dst[0] - M2S and g[1] < dst[0]:
                    g[2] = dst[0] - M2S
                assert g[2] - g[1] >= 0.28 - 1e-9, (d.drain, g)
            # drain bar: met2, or met2+met3 to the riser for the output stage
            if d.drain == 'out':
                ob = box(bx0, yb0, rx0, yb1)            # ends at the riser: one via2 array each
                b.stack(ob, 'm2', 'm3')
                outbars.append(ob)
            else:
                b.rect('m2', box(bx0, yb0, bx1, yb1))
                t = tby[d.drain]
                b.rect('m2', box(dst[0], yb0 if up else yb1, dst[1], t['y0'] if up else t['y1']))
                n2 = b.via('via2', box(dst[0], t['y0'], dst[1], t['y1']), enc=V2ENC)
                xs[d.drain] += list(dst)
                report.append((d.drain, f'{f.kind} drain', nv, n2))
            for net, gx0, gx1, sy0, sy1, pads in gstubs:
                b.rect('m1', box(min(gx0, pads[0].left), sy0, max(gx1, pads[-1].right), sy1))
                t = tby[net]
                b.rect('m2', box(gx0, sy1 if up else sy0, gx1, t['y0'] if up else t['y1']))
                n1 = b.via('via1', box(gx0, sy0, gx1, sy1), enc=(0.055, 0.085))
                n2 = b.via('via2', box(gx0, t['y0'], gx1, t['y1']), enc=V2ENC)
                xs[net] += [gx0, gx1]
                report.append((net, f'{f.kind} gate', n1, n2))

    for net, t in tby.items():                         # tracks (met3); inputs run to the left edge
        x0 = 0 if net in ('in', 'en') else min(xs[net]) - 0.1     # past the end stubs: via2 enclosure
        b.rect('m3', box(x0, t['y0'], max(xs[net]) + 0.1, t['y1']))
        if net in ('in', 'en'):
            b.pin('m3', box(0, t['y0'], 0.5, t['y1']), net)
    # out riser (met2+met3) on the right edge, spanning only between the two output
    # drain bars (not to the rails)
    riser = box(rx0, min(o.bottom for o in outbars), xmax, max(o.top for o in outbars))
    b.stack(riser, 'm2', 'm3')
    b.pin('m3', riser, 'out')

    print('net     where      via1  via2   need via1/via2 (2x margin)')
    for net, where, n1, n2 in report:
        i = NETS[net][3]
        need1, need2 = cuts_needed(i, 'via1'), cuts_needed(i, 'via2')
        flag = '' if n1 >= need1 and n2 >= need2 else '   <-- short'
        print(f'{net:6s}  {where:9s}  {n1:4d}  {n2:4d}   {need1}/{need2}{flag}')
    return b


if __name__ == '__main__':
    b = build()
    b.write(os.path.join(REPO, 'layout', 'tx_drv.gds'))
