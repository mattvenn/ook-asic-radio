# Row-based analog cell builder (from tx_drv v2), reusable for simple transistor blocks.
#
#   rail(s) on top (met1+2+3), one section per P segment's supply
#   PMOS row: segments (LV / HV), each with its own n-tap guard ring and nwell
#   routing channel: met3 tracks, met2 stubs up (P) / down (N) to the devices
#   NMOS row: segments, each with its own p-tap guard ring
#   VSS rail (met1+2+3)
#
# A segment is a run of devices with the same oxide (thin / thick 'g5') and rail.
# Segment k of the P row and of the N row share a column (same x range), so rings,
# wells and hvi line up; columns are separated by SEG_GAP (HV/LV nwell spacing 2 um).
#
# Channel routing: every stub's x range is planned first. A P stub of net a that
# overlaps (in x) an N stub of net b forces track(a) above track(b), otherwise the two
# met2 stubs would cross. Tracks are assigned by the constrained left-edge algorithm
# (nets share a track when their spans don't overlap and the constraints allow).
#
# Per net (Net): stub widths, track width, RMS current (cut check), and io:
#   None: internal; 'L': pin at the left edge (track runs to x = 0);
#   'R': pin at the right edge; 'riser': drain bars (met2+met3) into a riser on the
#   right edge (big outputs), which is the pin.
from collections import defaultdict
from lay import box, snap, ring, cuts_needed

RING_W = 0.4
RING_X = 0.45          # ring hole to diffusion, sides
RING_RAIL = 0.47       # ring hole to diffusion, rail side
RING_CH = 0.45         # ring hole to the gate straps, channel side
M3S = 0.3              # met3 spacing
M2S = 0.145            # met2 spacing (min 0.14)
V2ENC = (0.04, 0.085)  # via2 in a narrow vertical stub: 0.04 sides, 0.085 along it
DGAP = 0.9             # diffusion gap between neighbouring devices in a row
SEG_GAP = 4.7          # diffusion to diffusion across a segment boundary (rings, wells, nwell.8 2.0)


class Net:
    def __init__(self, stub_d=0.3, stub_g=0.3, track=0.5, irms=0.1, io=None):
        self.stub_d, self.stub_g, self.track, self.irms, self.io = stub_d, stub_g, track, irms, io


class Dev:
    """A FET in a row. roles per S/D strip: 'R' (to the segment's rail), 'D' (the drain
    net), a net name (pass devices: both sides are signals), or None (unconnected).
    gates: [(net, [finger indices])]. drain: net name. hb: drain bar height. rail: supply
    net of the 'R' strips (P: VAPWR/VDD, N: VSS)."""

    def __init__(self, fet, roles, gates, drain, hb=0.5, rail=None):
        self.f, self.roles, self.gates, self.drain, self.hb = fet, roles, gates, drain, hb
        self.rail = rail or ('VSS' if fet.kind == 'n' else 'VAPWR')
        self.hv = fet.vt == 'g5'


def inverter_roles(f):
    return ['R' if k % 2 == 0 else 'D' for k in range(f.nf + 1)]


def segments(row):
    segs = []
    for d in row:
        if segs and segs[-1][0] == (d.hv, d.rail):
            segs[-1][1].append(d)
        else:
            segs.append(((d.hv, d.rail), [d]))
    return segs


def strip_net(d, r):
    return d.drain if r == 'D' else (None if r == 'R' else r)


def plan(d, nets, strip_w):
    """x positions of a device's stubs (independent of y): strip width, strip indices per
    net (didx), gate stubs [net, x0, x1, fingers], strip-net stubs {net: (x0, x1)}
    (none for riser nets).
    One strip net (inverters): gate stub on the pads' left, drain stub at the drain
    strip furthest from it (the tx_drv / tx_ls layouts). Several (pass devices): all
    stubs packed side by side in natural x order across the device, reaching up to
    DGAP/2 into the gaps either side; bars and straps extend to their stubs."""
    f = d.f
    sw = min(strip_w, snap(f.strips[1].center().x - f.strips[0].center().x - 0.18))
    snets = []
    for r in d.roles:
        n = strip_net(d, r)
        if n is not None and n not in snets:
            snets.append(n)
    didx = {n: [k for k, r in enumerate(d.roles) if strip_net(d, r) == n] for n in snets}
    gst, dsts = [], {}
    if snets == [d.drain]:
        dstrips = [f.strips[k] for k in didx[d.drain]]
        for k, (net, fingers) in enumerate(d.gates):
            pads = [f.pads[i] for i in fingers]
            w = nets[net].stub_g
            if k == 0:                               # first gate group: stub on its left edge
                gst.append([net, pads[0].left, pads[0].left + w, fingers])
            else:                                    # later groups (NAND en): on the right edge
                gst.append([net, pads[-1].right - w, pads[-1].right, fingers])
        dst = None
        if nets[d.drain].io != 'riser':
            wd = nets[d.drain].stub_d
            best = max(dstrips, key=lambda s: min(abs(s.center().x - (g[1] + g[2]) / 2) for g in gst))
            dx0 = best.center().x - wd / 2
            for g in gst:                            # keep clear of the gate stubs
                if dx0 + wd > g[1] - M2S and dx0 < g[2] + M2S:
                    dx0 = g[2] + M2S if best.center().x >= (g[1] + g[2]) / 2 else g[1] - M2S - wd
            dst = (snap(dx0), snap(dx0 + wd))
            dsts[d.drain] = dst
        for g in gst:                                # gate stubs stop short of the drain stub
            if dst and g[2] > dst[0] - M2S and g[1] < dst[0]:
                g[2] = dst[0] - M2S
            assert g[2] - g[1] >= 0.28 - 1e-9, (d.drain, g)
    else:
        items = []                                   # (natural x, width, net, fingers or None)
        for net, fingers in d.gates:
            xs = [f.pads[i].center().x for i in fingers]
            items.append((sum(xs) / len(xs), nets[net].stub_g, net, fingers))
        for net in snets:
            assert nets[net].io != 'riser', 'riser nets need a single-drain device'
            xs = [f.strips[k].center().x for k in didx[net]]
            items.append((sum(xs) / len(xs), nets[net].stub_d, net, None))
        items.sort(key=lambda t: t[0])
        lo = f.diff.left - (DGAP - M2S) / 2
        hi = f.diff.right + (DGAP - M2S) / 2
        pos, x = [], lo
        for nx, w, net, fingers in items:
            x0 = max(nx - w / 2, x)
            pos.append([x0, x0 + w])
            x = x0 + w + M2S
        over = pos[-1][1] - hi
        if over > 0:                                 # pull back from the right, keep the order
            x = hi
            for q in reversed(pos):
                w = q[1] - q[0]
                q[1] = min(q[1], x)
                q[0] = q[1] - w
                x = q[0] - M2S
        assert pos[0][0] >= lo - 1e-9, (d.drain, 'stubs do not fit', pos)
        for (nx, w, net, fingers), (x0, x1) in zip(items, pos):
            if fingers is None:
                dsts[net] = (snap(x0), snap(x1))
            else:
                gst.append([net, snap(x0), snap(x1), fingers])
    return dict(sw=sw, didx=didx, gst=gst, dsts=dsts)


def assign_tracks(P, N, nets, plans):
    """Constrained left-edge channel routing over the planned stubs."""
    stubs = []                                       # (net, x0, x1, 'P'/'N')
    for row, side in ((P, 'P'), (N, 'N')):
        for d in row:
            p = plans[id(d)]
            stubs += [(g[0], g[1], g[2], side) for g in p['gst']]
            stubs += [(n, x0, x1, side) for n, (x0, x1) in p['dsts'].items()]
    span = {}
    for net, a, c, _ in stubs:
        s = span.get(net, (1e9, -1e9))
        span[net] = (min(s[0], a), max(s[1], c))
    for n, (a, c) in span.items():
        if nets[n].io == 'L':
            span[n] = (0, c)
        if nets[n].io == 'R':
            span[n] = (a, 1e9)
    above = defaultdict(set)                         # above[b] = nets whose track must be above b's
    for na, a0, a1, sa in stubs:
        for nb, b0, b1, sb in stubs:
            if sa == 'P' and sb == 'N' and na != nb and a0 < b1 + M2S and b0 < a1 + M2S:
                above[nb].add(na)
    tracks, placed, todo = [], set(), set(span)
    while todo:
        t = dict(nets=[], w=0)
        end = -1e9
        for net in sorted(todo, key=lambda n: span[n][0]):
            if above[net] <= placed and span[net][0] > end + 1.0:
                t['nets'].append(net)
                end = span[net][1]
                t['w'] = max(t['w'], nets[net].track)
        if not t['nets']:
            raise RuntimeError(f'channel: cyclic stub constraints among {sorted(todo)}')
        placed |= set(t['nets'])
        todo -= set(t['nets'])
        tracks.append(t)
    return tracks


def build(b, P, N, nets, rail_h=3.0, out_w=3.0, align_last=False, strip_w=0.45):
    """Place, ring, rail and route rows P (top) and N (bottom) into Block b."""
    sP, sN = segments(P), segments(N)
    assert [k[0] for k, _ in sP] == [k[0] for k, _ in sN], 'P and N rows need the same segment (oxide) order'

    # --- horizontal: pack each column (segment k of both rows) left to right
    x0 = 0.6
    cols = []
    for (kp, dp), (kn, dn) in zip(sP, sN):
        x = x0
        for d in dp:
            d.f.place(x, 0)
            x = d.f.diff.right + DGAP
        x = x0
        for d, e in zip(dn, dp + [None] * len(dn)):
            if e is not None:
                x = max(x, e.f.diff.left)
            d.f.place(x, 0)
            x = d.f.diff.right + DGAP
        cols.append((kp, kn, dp, dn))
        x0 = max(d.f.diff.right for d in dp + dn) + SEG_GAP
    if align_last:                                       # line up the last devices' right edges
        sh = P[-1].f.diff.right - N[-1].f.diff.right
        if sh > 0:
            N[-1].f.place(N[-1].f.x + sh, 0)
        else:
            P[-1].f.place(P[-1].f.x - sh, 0)

    # --- channel: plan stubs, assign tracks; then the rows either side
    plans = {id(d): plan(d, nets, strip_w) for d in P + N}
    tracks = assign_tracks(P, N, nets, plans)
    ch_h = sum(t['w'] for t in tracks) + M3S * (len(tracks) + 1)
    padP = min(p.bottom for d in P for p in d.f.pads)
    padN = max(max(p.top for p in d.f.pads) - d.f.w for d in N)
    for d in P:
        d.f.place(d.f.x, snap(ch_h / 2 + RING_W + RING_CH - padP))
    yNt = snap(-ch_h / 2 - RING_W - RING_CH - padN)
    for d in N:
        d.f.place(d.f.x, yNt - d.f.w)
    for d in P + N:
        d.f.commit()

    # --- rings, wells, implants per column; all P rings share top/bottom, N likewise
    pTop = max(d.f.diff.top for d in P) + RING_RAIL
    pBot = min(p.bottom for d in P for p in d.f.pads) - RING_CH
    nTop = max(p.top for d in N for p in d.f.pads) + RING_CH
    nBot = min(d.f.diff.bottom for d in N) - RING_RAIL
    rings = []
    for kp, kn, dp, dn in cols:
        xl = min(d.f.diff.left for d in dp + dn) - RING_X
        xr = max(d.f.diff.right for d in dp + dn) + RING_X
        rP = ring(b, box(xl, pBot, xr, pTop), 'n', RING_W)
        rN = ring(b, box(xl, nBot, xr, nTop), 'p', RING_W)
        b.rect('nwell', box(rP.left - 0.5, rP.bottom - 0.5, rP.right + 0.5, rP.top + 0.5))
        if kp[0]:                                        # thick oxide column
            b.rect('hvi', box(rP.left - 0.5, rN.bottom - 0.5, rP.right + 0.5, rP.top + 0.5))
            # one hvntm over the HV NMOS: ringless nfet pcells leave notches (hvntm.2)
            b.rect('hvntm', box(min(d.f.diff.left for d in dn) - 0.185, min(d.f.diff.bottom for d in dn) - 0.185,
                                max(d.f.diff.right for d in dn) + 0.185, max(d.f.diff.top for d in dn) + 0.185))
        rings.append((rP, rN, kp[1], kn[1]))
    ytop, ybot = rings[0][0].top - RING_W, rings[0][1].bottom + RING_W
    risers = [n for n in nets if nets[n].io == 'riser']
    xring = rings[-1][0].right
    xmax = snap(xring + 0.6 + out_w) if risers else snap(xring + 0.3)

    # rails: one section per run of columns with the same supply, split between columns
    def rails(idx, y0, y1):
        secs = []
        for i, r in enumerate(rings):
            if secs and secs[-1][0] == r[idx]:
                secs[-1][2] = i
            else:
                secs.append([r[idx], i, i])
        for k, (net, i0, i1) in enumerate(secs):
            xa = 0 if k == 0 else snap((rings[i0 - 1][0].right + rings[i0][0].left) / 2 + 0.3)
            xb = xmax if k == len(secs) - 1 else snap((rings[i1][0].right + rings[i1 + 1][0].left) / 2 - 0.3)
            rb = box(xa, y0, xb, y1)
            b.stack(rb, 'm1', 'm3')
            b.pin('m3', rb, net)
    rails(2, ytop, ytop + rail_h)
    rails(3, ybot - rail_h, ybot)

    y = min(r[0].bottom for r in rings) - M3S
    for t in tracks:
        t['y1'], t['y0'] = snap(y), snap(y - t['w'])
        y = t['y0'] - M3S
    tby = {n: t for t in tracks for n in t['nets']}
    xs = defaultdict(list)
    report = []
    rx0 = xmax - out_w
    outbars = defaultdict(list)

    for row, up in ((P, True), (N, False)):
        for d in row:
            f, p = d.f, plans[id(d)]
            sw = p['sw']
            for s, r in zip(f.strips, d.roles):          # S/D strips widened; rail strips to the rail
                xc = s.center().x
                y0, y1 = (((s.bottom, ytop + RING_W) if up else (ybot - RING_W, s.top)) if r == 'R'
                          else (s.bottom, s.top))
                b.rect('m1', box(xc - sw / 2, y0, xc + sw / 2, y1))
            hb = min(d.hb, max(0.32, f.w - 0.3))         # drain bar (met2), via1 on each drain strip
            yb0, yb1 = ((f.diff.bottom + 0.14, f.diff.bottom + 0.14 + hb) if up
                        else (f.diff.top - 0.14 - hb, f.diff.top - 0.14))
            # one bar band for all strip nets (x-separated): grow it where a strip is short
            for idx in p['didx'].values():
                for s in (f.strips[k] for k in idx):
                    if min(yb1, s.top) - max(yb0, s.bottom) < 0.32:
                        yc = s.center().y
                        yb0, yb1 = min(yb0, yc - 0.16), max(yb1, yc + 0.16)
            for net, idx in p['didx'].items():
                strips = [f.strips[k] for k in idx]
                nv = 0
                for s in strips:
                    xc = s.center().x
                    v0, v1 = max(yb0, s.bottom), min(yb1, s.top)
                    if v1 - v0 < 0.32:
                        yc = s.center().y
                        v0, v1 = yc - 0.16, yc + 0.16
                        b.rect('m1', box(xc - sw / 2, v0, xc + sw / 2, v1))
                    nv += b.via('via1', box(xc - sw / 2, v0, xc + sw / 2, v1), enc=((sw - 0.15) / 2, 0.085))
                bx0 = strips[0].center().x - sw / 2
                bx1 = strips[-1].center().x + sw / 2
                if net in p['dsts']:
                    bx0, bx1 = min(bx0, p['dsts'][net][0]), max(bx1, p['dsts'][net][1])
                if nets[net].io == 'riser':
                    ob = box(bx0, yb0, rx0, yb1)
                    b.stack(ob, 'm2', 'm3')
                    outbars[net].append(ob)
                    continue
                dx0, dx1 = p['dsts'][net]
                b.rect('m2', box(bx0, yb0, bx1, yb1))
                t = tby[net]
                b.rect('m2', box(dx0, yb0 if up else yb1, dx1, t['y0'] if up else t['y1']))
                n2 = b.via('via2', box(dx0, t['y0'], dx1, t['y1']), enc=V2ENC)
                xs[net] += [dx0, dx1]
                report.append((net, f'{f.kind} strip', nv, n2))
            for net, gx0, gx1, fingers in p['gst']:      # gate straps (met1), stubs (met2), cuts
                pads = [f.pads[i] for i in fingers]
                sy0, sy1 = min(q.bottom for q in pads), max(q.top for q in pads)
                if sy1 - sy0 < 0.32:
                    sy0, sy1 = (sy1 - 0.32, sy1) if up else (sy0, sy0 + 0.32)
                b.rect('m1', box(min(gx0, pads[0].left), sy0, max(gx1, pads[-1].right), sy1))
                t = tby[net]
                b.rect('m2', box(gx0, sy1 if up else sy0, gx1, t['y0'] if up else t['y1']))
                n1 = b.via('via1', box(gx0, sy0, gx1, sy1), enc=(0.055, 0.085))
                n2 = b.via('via2', box(gx0, t['y0'], gx1, t['y1']), enc=V2ENC)
                xs[net] += [gx0, gx1]
                report.append((net, f'{f.kind} gate', n1, n2))

    for net, t in tby.items():
        io = nets[net].io
        xa = 0 if io == 'L' else min(xs[net]) - 0.1
        xb = xmax if io == 'R' else max(xs[net]) + 0.1
        b.rect('m3', box(xa, t['y0'], xb, t['y1']))
        if io == 'L':
            b.pin('m3', box(0, t['y0'], 0.5, t['y1']), net)
        elif io == 'R':
            b.pin('m3', box(xmax - 0.5, t['y0'], xmax, t['y1']), net)
        else:
            b.label('m3', box(min(xs[net]), t['y0'], max(xs[net]), t['y1']), net)
    for net, obs in outbars.items():                 # riser between the output bars only
        riser = box(rx0, min(o.bottom for o in obs), xmax, max(o.top for o in obs))
        b.stack(riser, 'm2', 'm3')
        b.pin('m3', riser, net)

    # for generators that add to the block (caps, extra wiring): rails, tracks, extents
    b.rows = dict(ytop=ytop, ybot=ybot, rail_h=rail_h, xmax=xmax, tracks=tby,
                  xs={n: (min(v), max(v)) for n, v in xs.items()})
    print(f'{b.name}: net     where      via1  via2   need via1/via2 (2x margin)')
    for net, where, n1, n2 in report:
        i = nets[net].irms
        need1, need2 = cuts_needed(i, 'via1'), cuts_needed(i, 'via2')
        flag = '' if n1 >= need1 and n2 >= need2 else '   <-- short'
        print(f'  {net:6s}  {where:9s}  {n1:4d}  {n2:4d}   {need1}/{need2}{flag}')
    return b
