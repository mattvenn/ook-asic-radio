# tx_ring layout: nand2_2 enable + NINV x inv_2 ring (xschem/gen/tx.py:tx_ring), std cells.
#
# Folded into two rows so no wire runs the length of the ring:
#   row 0 (y 0..H, R0, VSS bottom): tap, inv_1 .., inv_ROW0, left to right;
#   row 1 (y H..2H, R180, VSS top):  inv_ROW0+1 .. inv_NINV, nand2_2, right to left,
# sharing the VDD rail in the middle. The turn (inv_ROW0 Y -> next A) and the feedback
# (nand Y = 'out' -> inv_1 A) are short met2 verticals at the right and left ends.
# Taps every <= 8 inverters (LU <= 15 um). Stage k's Y -> stage k+1's A in a row: a short
# met1 strap (mcon at both li pins). 'out' and 'en' (nand A) are met3 pins on the left edge.
# Rails: VSS bottom and top on met1-met3 (joined by a met2 strap at the right edge), VDD in
# the middle on met1 and met3 (met2 only between the two end verticals).
# The schematic's cw (3.2 fF per stage) is a wiring estimate calibrated on the ttsky25b
# layout; here the extracted netlist decides the frequency (sim/tx/tb_tx_ring.py).
# Also writes layout/ref/tx_ring.spice (the LVS reference: the xschem netlist without
# the cw capacitors).
# Run: tools/osic klayout -b -r layout/gen/tx_ring.py
import os
import re
import subprocess
import sys
import pya
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, box, snap, REPO, PDKDIR   # noqa: E402

NINV = 22             # as xschem/gen/tx.py
ROW0 = 12             # inverters in row 0 (row 1 has the rest + the nand: about the same width)
TAP_EVERY = 8         # inverters between taps (8 x 1.38 = 11 um)
RAIL_H = 1.0          # outer VSS rails; the ring draws little current
VDD_H = 0.7           # the shared middle VDD rail (cells' rail is 0.48)
SC = 'sky130_fd_sc_hd__'
H = 2.72              # cell height


def make(ninv=NINV, row0=ROW0):
    b = Block('tx_ring')
    lib = pya.Layout()
    lib.read(os.path.join(PDKDIR, 'libs.ref', 'sky130_fd_sc_hd', 'gds', 'sky130_fd_sc_hd.gds'))
    cells = {}
    names = {'tap': 'tapvpwrvgnd_1', 'inv': 'inv_2', 'nand': 'nand2_2'}

    def cell(n):
        if n not in cells:
            src = lib.cell(SC + n)
            dst = b.ly.create_cell(SC + n)
            dst.copy_tree(src)
            cells[n] = dst
        return cells[n]

    def width(n):
        return snap(lib.cell(SC + n).dbbox().width() - 0.38)       # minus the 0.19 nwell overhang each side

    # sequences in signal order; taps every TAP_EVERY inverters
    def with_taps(kinds):
        out, n = ['tap'], 0
        for k in kinds:
            if k == 'inv' and n and n % TAP_EVERY == 0:
                out.append('tap')
            out.append(k)
            n += k == 'inv'
        return out + ['tap']

    seq0 = with_taps(['inv'] * row0)
    seq1 = with_taps(['inv'] * (ninv - row0) + ['nand'])      # signal order, laid right to left
    w0 = sum(width(names[k]) for k in seq0)
    w1 = sum(width(names[k]) for k in seq1)
    xr = snap(max(w0, w1))
    # pad the narrower row with taps at its signal-start end (row 0: left of inv_1 would move
    # the feedback; so pad row 0 at its right end, row 1 at its right end = its signal start)
    tw = width(names['tap'])
    while w0 < xr - 1e-6:
        seq0.append('tap')
        w0 += tw
    while w1 < xr - 1e-6:
        seq1.insert(0, 'tap')
        w1 += tw
    assert abs(w0 - xr) < 1e-6 and abs(w1 - xr) < 1e-6, (w0, w1)

    # place; pin(kind, x-cell-relative) -> absolute x, plus each row's pin y
    inst = []                   # (kind, row, x_left)
    x = 0.0
    for k in seq0:
        b.place(cell(names[k]), x, 0)
        inst.append((k, 0, x))
        x += width(names[k])
    x = xr
    for k in seq1:              # right to left, rotated 180 about the cell centre
        w = width(names[k])
        x -= w
        b.cell.insert(pya.DCellInstArray(cell(names[k]).cell_index(),
                                         pya.DTrans(pya.DTrans.R180, pya.DVector(snap(x + w), 2 * H))))
        inst.append((k, 1, x))

    def pin(i, xrel):
        k, row, xl = inst[i]
        return snap(xl + xrel) if row == 0 else snap(xl + width(names[k]) - xrel)

    def ymir(row, y):
        return y if row == 0 else 2 * H - y

    def ybox(row, y0, y1):
        a, c = ymir(row, y0), ymir(row, y1)
        return min(a, c), max(a, c)

    stages = [i for i, (k, _, _) in enumerate(inst) if k == 'inv']   # signal order
    nand = [i for i, (k, _, _) in enumerate(inst) if k == 'nand'][0]
    row = {i: inst[i][1] for i in range(len(inst))}

    # li pins (cell-relative x centres; y centre 1.19 in R0)
    A, Y = 0.23, 0.69
    nB, nA, nY = 0.695, 1.615, 2.075
    YC = 1.19

    def mcon_pad(r, xc, y0=YC - 0.115, y1=YC + 0.115):
        yc = ymir(r, YC)
        b.rect('mcon', box(xc - 0.085, yc - 0.085, xc + 0.085, yc + 0.085))
        lo, hi = ybox(r, y0, y1)
        return box(xc - 0.145, lo, xc + 0.145, hi)

    yv0, yv1 = 0.60, 0.92       # via1 below the li pin (0.32: 0.085 enclosure along y), R0 coordinates

    def down_via(r, xc):
        """met1 pad from the pin's mcon to a via1 at yv0..yv1 (mirrored in row 1); returns its y span."""
        p = mcon_pad(r, xc, yv0, YC + 0.115)
        b.rect('m1', p)
        lo, hi = ybox(r, yv0, yv1)
        b.via('via1', box(xc - 0.145, lo, xc + 0.145, hi), enc=(0.07, 0.085))
        return lo, hi

    # stage straps within a row: Y(k) -> A(k+1), the last Y -> nand B
    sinks = [(s, A) for s in stages[1:]] + [(nand, nB)]
    turn = None
    for s, (d, dx) in zip(stages, sinks):
        xs, xd = pin(s, Y), pin(d, dx)
        if row[s] == row[d]:
            p0, p1 = mcon_pad(row[s], xs), mcon_pad(row[d], xd)
            b.rect('m1', box(min(p0.left, p1.left), p0.bottom, max(p0.right, p1.right), p0.top))
        else:
            turn = (xs, xd)
    # the turn: met2 vertical from row 0's Y to row 1's A
    xs, xd = turn
    lo0, _ = down_via(0, xs)
    _, hi1 = down_via(1, xd)
    xt0, xt1 = min(xs, xd) - 0.145, max(xs, xd) + 0.145
    b.rect('m2', box(xs - 0.145, lo0, xs + 0.145, H))
    b.rect('m2', box(xt0, H - 0.145, xt1, H + 0.145))
    b.rect('m2', box(xd - 0.145, H, xd + 0.145, hi1))
    # feedback: nand Y (row 1) -> inv_1 A (row 0), met2 vertical at the left end
    xo, xi = pin(nand, nY), pin(stages[0], A)
    lo0, hi0 = down_via(0, xi)
    _, hi1 = down_via(1, xo)
    xf0, xf1 = min(xo, xi) - 0.145, max(xo, xi) + 0.145
    b.rect('m2', box(xf0, lo0, xf1, hi1))
    b.label('m2', box(xf0, H - 0.2, xf1, H + 0.2), 'out')
    # 'out' pin on the left edge, beside inv_1 A's via (met3 0.3 clear of the VSS rail)
    op = box(0, 0.55, 0.5, 1.05)
    b.rect('m2', box(0, min(lo0, op.bottom), xf1, max(hi0, op.top)))   # no notch against the pin pad
    b.stack(op, 'm2', 'm3')
    b.pin('m3', op, 'out')
    # 'en' = nand A: the original pad/via1/via2 stack toward the VDD rail, mirrored into row 1
    xa = pin(nand, nA)
    ye0, ye1 = 1.55, 1.92                                # 0.37: room for via2
    pe = mcon_pad(1, xa, YC - 0.115, ye1)
    b.rect('m1', pe)
    lo, hi = ybox(1, YC - 0.1, ye1)
    b.rect('m2', box(xa - 0.145, lo, xa + 0.145, hi))
    lo, hi = ybox(1, ye0 - 0.3, ye1)
    b.via('via1', box(xa - 0.145, lo, xa + 0.145, hi), enc=(0.07, 0.085))
    e0, e1 = ybox(1, ye0, ye1)
    b.via('via2', box(xa - 0.145, e0, xa + 0.145, e1), enc=(0.04, 0.085))
    b.rect('m3', box(0, e0, xa + 0.25, e1))             # past the via2 (met3 enclosure)
    b.pin('m3', box(0, e0, 0.5, e1), 'en')
    assert xf1 + 0.14 <= xa - 0.145, 'feedback met2 too close to the en stack'
    # stage net names for the extraction
    for n, s in enumerate(stages, 1):
        xc, yc = pin(s, Y), ymir(row[s], YC)
        b.label('li', box(xc - 0.085, yc - 0.085, xc + 0.085, yc + 0.085), f'r{n}')

    # rails: VSS at y 0 and 2H (m1-m3), VDD at y H (m1, m3; m2 + vias between the end verticals)
    vb = box(0, -RAIL_H + 0.24, xr, 0.24)
    vt = box(0, 2 * H - 0.24, xr, 2 * H - 0.24 + RAIL_H)
    b.stack(vb, 'm1', 'm3')
    b.stack(vt, 'm1', 'm3')
    xs0 = xr - 0.5
    b.rect('m2', box(xs0, vb.bottom, xr, vt.top))       # joins the two VSS rails
    vd = box(0, H - VDD_H / 2, xr, H + VDD_H / 2)
    b.rect('m1', vd)
    b.rect('m3', vd)
    m2l, m2r = xf1 + 0.3, min(xt0, xs0) - 0.3
    b.stack(box(m2l, vd.bottom, m2r, vd.top), 'm1', 'm3')
    b.pin('m3', vb, 'VSS')
    b.pin('m3', vd, 'VDD')
    ntap = sum(k == 'tap' for k, _, _ in inst)
    print(f'tx_ring: {ninv} inv + nand in 2 rows ({row0} + {ninv - row0}), {ntap} taps, '
          f'{xr:.2f} x {vt.top - vb.bottom:.2f} um')
    return b


def write_ref():
    tmp = os.path.join(REPO, 'build', 'lay', 'ref')
    os.makedirs(tmp, exist_ok=True)
    subprocess.run(['xschem', '-n', '-s', '-q', '--tcl', 'set top_subckt 1; set lvs_netlist 1', '-o', tmp,
                    'xschem/tx_ring.sch'], cwd=REPO, capture_output=True)
    src = open(os.path.join(tmp, 'tx_ring.spice')).read()
    out = []
    for ln in src.splitlines():
        if ln.startswith('.subckt tx_ring'):
            ln = re.sub(r'\s+\w+=\S+', '', ln)
        if re.match(r'^C\w*\s', ln):          # cw: wiring estimate, not a device
            continue
        out.append(ln)
    os.makedirs(os.path.join(REPO, 'layout', 'ref'), exist_ok=True)
    with open(os.path.join(REPO, 'layout', 'ref', 'tx_ring.spice'), 'w') as fh:
        fh.write('* tx_ring: xschem/tx_ring.sch without the cw wiring caps (layout/gen/tx_ring.py)\n'
                 + '\n'.join(out) + '\n')


if __name__ == '__main__':
    make().write(os.path.join(REPO, 'layout', 'tx_ring.gds'))
    write_ref()
