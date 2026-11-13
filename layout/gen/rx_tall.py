# rx_t: the tall chain (lna_chain_t) with the one-row detector (log_det_t) along its north edge
# and the six tap pairs wired between them (docs/tall_stages_2026-11.md, "RX block").
#
#   log_det_t   | end | t1 | t2 | t3 | t4 | t5 | t6 |       (VSS rail along its bottom)
#   channel     shield / o3, out / shield / o2, o5 / shield / o1, o4 / shield    (met3, east-west)
#   lna_chain_t | input section | st1 | st2 | ... | st6 |   (VDD rail along its top)
#
# The detector's cells are 20.83 um wide and the stages 11.7 um, so each tap runs along the
# channel to its detector: up from the chain's tap column (met4) to its track, along the track
# (met3), up again (met4) to a met3 stub that comes down from the det_cell's Cc bottom plate
# (p plate: its outer-left edge, n plate: its outer-right edge; there the cell has no met3
# between the plate and its rail). Risers are met4 and tracks met3, so they cross freely.
# Tracks: the pairs share three track pairs (o1 / o4, o2 / o5, o3 / out: their runs don't
# overlap), so the wires that run side by side are at most one stage apart; grounded met3 shields
# (VSS, tied to the detector's rail at both ends) separate the groups, and the bottom one also
# shields o1's run back over the input section.
# Supplies: VDD (chain) and VDDD (detector) are separate in the block (both VDPWR at the top level);
# VSS is one net: the detector's rail and the shields join the chain's ground through the p-substrate
# (both blocks' p-tap rings), as magic extracts it. Pins: the chain's inp / inn / vcm / ibias / lna_lo_n (south),
# VDD (south, on the bottom rail), VSS (east end of the centre line); the detector's det /
# ibias_det (its west edge), VDDD (its north edge), VSS (its rail, the shields).
# Run (after lna_chain_tall.py and log_det_tall.py): tools/osic klayout -b -r layout/gen/rx_tall.py
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pya   # noqa: E402
from lay import Block, REPO, box, snap   # noqa: E402
from chain_strip_tall import pins        # noqa: E402

DX = -7.2          # log_det_t origin, from the chain's (the row overhangs the input end; see the floorplan)
SIG_W, SH_W, SP = 0.4, 0.3, 0.3          # track widths (signal: via3 enclosure), spacing
RISER_W = 0.4
GROUPS = [('o1', 'o4'), ('o2', 'o5'), ('o3', 'out')]   # bottom (next to the chain) to top
PLATE_W = 7.365                          # det_cell Cc bottom plate (6.965 + 2 x 0.2)
STUB_Y0 = 1.5                            # stub bottom in the detector's frame (its met3 rail ends at 1.2)


def import_gds(b, name):
    src = pya.Layout()
    src.read(os.path.join(REPO, 'layout', name + '.gds'))
    c = b.ly.create_cell(name)
    c.copy_tree(src.top_cell())
    return c


def make():
    b = Block('rx_t')
    ch = import_gds(b, 'lna_chain_t')
    dt = import_gds(b, 'log_det_t')
    pc, pd = pins(ch, b.ly), pins(dt, b.ly)
    Hc = ch.dbbox().top
    xc0, xc1 = ch.dbbox().left, ch.dbbox().right

    # tracks, bottom up: shield, (p, n) of group 0, shield, ... , shield; the detector above
    tracks, y = [], snap(Hc + SP)
    for gi in range(len(GROUPS)):
        tracks.append(('sh', None, y, SH_W))
        y = snap(y + SH_W + SP)
        for sd in 'pn':
            tracks.append(('sig', (gi, sd), y, SIG_W))
            y = snap(y + SIG_W + SP)
    tracks.append(('sh', None, y, SH_W))
    y = snap(y + SH_W + SP)
    yd = y                                         # detector origin (its met3 rail from here)
    b.place(ch, 0, 0)
    b.place(dt, DX, yd)
    sig_y = {k: yy for kind, k, yy, w in tracks if kind == 'sig'}

    # chain tap columns (met4 pins on its north edge) and detector stubs
    def col(net):
        cand = [r for lay, r in pc[net] if lay == 'm4' and r.top > Hc - 0.01]
        assert len(cand) == 1, (net, cand)
        return cand[0]

    chain_m4 = [r.to_dtype(b.ly.dbu) for r in pya.Region(ch.begin_shapes_rec(b.ly.layer(71, 20))).each()
                if r.bbox().to_dtype(b.ly.dbu).top > Hc - 0.01]
    chain_m4 = [r.bbox() for r in chain_m4]
    runs = []
    for gi, grp in enumerate(GROUPS):
        for o in grp:
            k = 6 if o == 'out' else int(o[1])
            for sd in 'pn':
                c = col(f'{o}{sd}')
                pb = [r for lay, r in pd[f't{k}{sd}'] if lay == 'm3'][0]
                if sd == 'p':                      # p plate: outer-left edge (pin at its bottom-left corner)
                    s0 = pb.left
                else:                              # n plate: outer-right edge (pin at the plate's gap-side corner)
                    s0 = pb.left + PLATE_W - 1.0
                stub = box(DX + s0, yd + STUB_Y0, DX + s0 + 1.0, yd + pb.bottom + 0.01)
                runs.append(dict(net=f'{o}{sd}', tap=c, stub=stub, y=sig_y[(gi, sd)]))

    # detector risers: inside the stub's x range, as far as possible from the chain's met4 at the
    # top edge that its run reaches up past (every chain riser is drawn first: their columns)
    others = [dict(x0=r['tap'].left, x1=r['tap'].right, y0=Hc, y1=r['y'] + SIG_W) for r in runs]
    for r in runs:
        st = r['stub']
        best = None
        for i in range(int(round((st.width() - RISER_W) / 0.05)) + 1):
            x0 = snap(st.left + 0.05 * i)
            x1 = x0 + RISER_W
            g = min([max(o['x0'] - x1, x0 - o['x1']) for o in others if o['y1'] > r['y'] - 0.1] + [9.0])
            if best is None or g > best[0]:
                best = (g, x0)
        assert best[0] >= SP - 1e-6, (r['net'], best)
        r['rx'] = best[1]

    for r in runs:
        c, st, yy = r['tap'], r['stub'], r['y']
        trk = box(min(c.left, r['rx']), yy, max(c.right, r['rx'] + RISER_W), yy + SIG_W)
        b.rect('m3', trk)
        b.label('m3', trk, r['net'])
        # chain side: the tap column on up to the track, via3
        b.rect('m4', box(c.left, Hc, c.right, yy + SIG_W))
        b.via('via3', box(c.left, yy, c.right, yy + SIG_W), enc=(0.065, 0.065))
        # detector side: met4 riser from the track up to the stub's foot, via3 at both ends
        b.rect('m4', box(r['rx'], yy, r['rx'] + RISER_W, st.bottom + 1.0))
        b.via('via3', box(r['rx'], yy, r['rx'] + RISER_W, yy + SIG_W), enc=(0.065, 0.065))
        b.rect('m3', st)
        b.via('via3', box(r['rx'], st.bottom, r['rx'] + RISER_W, st.bottom + 1.0), enc=(0.09, 0.065))

    # shields: from the detector's west end to past the last stub, tied up to its rail at both ends
    xs0 = DX
    xs1 = snap(max(max(r['stub'].right, r['tap'].right) for r in runs) + SP)
    xd1 = DX + dt.dbbox().right
    assert xs1 + 0.8 <= xd1, (xs1, xd1)
    ysh = [yy for kind, k, yy, w in tracks if kind == 'sh']
    for yy in ysh:
        b.rect('m3', box(xs0, yy, xs1 + 0.8, yy + SH_W))
    for x0 in (xs0, xs1):
        b.rect('m3', box(x0, ysh[0], x0 + 0.8, yd + 1.0))
    b.label('m3', box(xs0, ysh[0], xs0 + 0.8, yd), 'VSS')

    # pins
    for net in ('inp', 'inn', 'vcm', 'ibias', 'lna_lo_n'):
        lay, r = [(la, r) for la, r in pc[net] if r.bottom < 0.01][0]
        b.pin(lay, r, net)
    b.pin('m3', box(xc1 - 2.0, 0, xc1, 0.5), 'VDD')                        # chain's bottom rail
    b.pin('m3', box(xc1 - 0.5, 30.75, xc1, 32.75), 'VSS')                  # centre line, east end
    for net, nn in (('det', 'det'), ('ibias_det', 'ibias_det'), ('VDD', 'VDDD'), ('VSS', 'VSS')):
        lay, r = pd[net][0]
        b.pin(lay, r.moved(pya.DVector(DX, yd)), nn)
    bb = b.cell.dbbox()
    print(f'rx_t: {bb.width():.2f} x {bb.height():.2f} um (x {bb.left:.2f}..{bb.right:.2f}); channel {Hc:.2f}..{yd:.2f} '
          f'({yd - Hc:.2f} um, {len(tracks)} tracks), detector at ({DX}, {yd:.2f})')
    for r in sorted(runs, key=lambda r: r['net']):
        print(f"  {r['net']:5s} tap x {r['tap'].center().x:7.2f} -> riser {r['rx']:7.2f}, track y {r['y']:.2f}, "
              f"run {abs(r['tap'].center().x - r['rx']):5.1f} um")
    return b


def write_ref():
    taps = ' '.join(f'o{i}{s}' for i in range(1, 6) for s in 'pn')
    det_t = ' '.join(f'o{i}p o{i}n' for i in range(1, 6)) + ' outp outn'
    out = ['* rx_t: lna_chain_t + log_det_t with the taps wired (layout/gen/rx_tall.py)',
           '.subckt rx_t inp inn ibias vcm lna_lo_n ibias_det det VDD VSS VDDD',
           f'Xc inp inn ibias vcm lna_lo_n outp outn {taps} VDD VSS lna_chain_t',
           f'Xd {det_t} ibias_det det VDDD VSS log_det_t',
           '.ends']
    for c in ('lna_chain_t', 'log_det_t'):
        out.append(open(os.path.join(REPO, 'layout', 'ref', c + '.spice')).read())
    if 'det_cell' not in out[-1].split('.subckt det_cell')[0] or '.subckt det_cell' not in '\n'.join(out):
        out.append(open(os.path.join(REPO, 'layout', 'ref', 'det_cell.spice')).read())
    open(os.path.join(REPO, 'layout', 'ref', 'rx_t.spice'), 'w').write('\n'.join(out) + '\n')


if __name__ == '__main__':
    b = make()
    b.write(os.path.join(REPO, 'layout', 'rx_t.gds'))
    write_ref()
