# tx_ring layout: nand2_2 enable + NINV x inv_2 ring (xschem/gen/tx.py:tx_ring), std cells.
#
# One row, VDD on top, VSS at the bottom (the cells' own met1 rails, under block rails on
# met1+met2+met3): tap, inv_1 .. inv_NINV (taps in between, LU <= 15 um), nand2_2, tap.
# Stage k's Y -> stage k+1's A: a short met1 strap (mcon at both li pins). The last
# inverter feeds the nand's B next to it; the nand's Y ('out') returns on met2 to inv_1's
# A and runs on to the 'out' pin at the right edge. 'en' (nand A) comes in on met3 from
# the left edge.
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
TAP_EVERY = 8         # inverters between taps (8 x 1.38 = 11 um)
RAIL_H = 1.0           # the ring draws little current; keep the narrow block's density down
SC = 'sky130_fd_sc_hd__'
H = 2.72              # cell height


def make(ninv=NINV):
    b = Block('tx_ring')
    lib = pya.Layout()
    lib.read(os.path.join(PDKDIR, 'libs.ref', 'sky130_fd_sc_hd', 'gds', 'sky130_fd_sc_hd.gds'))
    cells = {}

    def cell(n):
        if n not in cells:
            src = lib.cell(SC + n)
            dst = b.ly.create_cell(SC + n)
            dst.copy_tree(src)
            cells[n] = dst
        return cells[n]

    def width(n):
        return snap(lib.cell(SC + n).dbbox().width() - 0.38)       # minus the 0.19 nwell overhang each side

    # placement, left to right
    x = 0.0
    seq = ['tap']
    for i in range(ninv):
        if i and i % TAP_EVERY == 0:
            seq.append('tap')
        seq.append('inv')
    seq += ['nand', 'tap']
    pos = []
    for kind in seq:
        n = {'tap': 'tapvpwrvgnd_1', 'inv': 'inv_2', 'nand': 'nand2_2'}[kind]
        b.place(cell(n), x, 0)
        pos.append((kind, x))
        x += width(n)
    xr = snap(x)
    stages = [px for k, px in pos if k == 'inv']
    xn = [px for k, px in pos if k == 'nand'][0]

    # li pins (cell-relative x centres; y centre 1.19)
    A, Y = 0.23, 0.69
    nB, nA, nY = 0.695, 1.615, 2.075
    yc = 1.19

    def mcon_pad(xc, y0=yc - 0.115, y1=yc + 0.115):
        b.rect('mcon', box(xc - 0.085, yc - 0.085, xc + 0.085, yc + 0.085))
        return box(xc - 0.145, y0, xc + 0.145, y1)

    # stage straps: Y(k) -> A(k+1), and the last Y -> nand B
    sinks = [s + A for s in stages[1:]] + [xn + nB]
    for s, xa in zip(stages, sinks):
        p0, p1 = mcon_pad(s + Y), mcon_pad(xa)
        b.rect('m1', box(p0.left, p0.bottom, p1.right, p0.top))
    # 'out' = nand Y: met1 pad down to y 0.85, via1, met2 return to inv_1's A and on to the right edge
    yo0, yo1 = 0.60, 0.92                                # 0.32: via1 with 0.085 enclosure along y
    py = mcon_pad(xn + nY)
    b.rect('m1', box(py.left, yo0, py.right, py.top))
    pa = mcon_pad(stages[0] + A)
    b.rect('m1', box(pa.left, yo0, pa.right, pa.top))
    for xc in (xn + nY, stages[0] + A):
        b.via('via1', box(xc - 0.145, yo0, xc + 0.145, yo1), enc=(0.07, 0.085))
    ret = box(stages[0] + A - 0.145, yo0, xr, yo1)
    b.rect('m2', ret)
    op = box(xr - 0.5, 0.55, xr, 1.05)                  # pin pad: room for via2, met3 0.3 clear of the VSS rail
    b.stack(op, 'm2', 'm3')
    b.pin('m3', op, 'out')
    b.label('m2', box(stages[0], yo0, stages[0] + 1, yo1), 'out')
    # 'en' = nand A: mcon + met1 pad, via1, met2 pad, via2, met3 track from the left edge
    ye0, ye1 = 1.55, 1.92                                # 0.37: room for via2
    pe = mcon_pad(xn + nA)
    b.rect('m1', box(pe.left, pe.bottom, pe.right, ye1))
    b.rect('m2', box(xn + nA - 0.145, yc - 0.1, xn + nA + 0.145, ye1))
    b.via('via1', box(xn + nA - 0.145, ye0 - 0.3, xn + nA + 0.145, ye1), enc=(0.07, 0.085))
    b.via('via2', box(xn + nA - 0.145, ye0, xn + nA + 0.145, ye1), enc=(0.04, 0.085))
    b.rect('m3', box(0, ye0, xn + nA + 0.25, ye1))             # past the via2 (met3 enclosure)
    b.pin('m3', box(0, ye0, 0.5, ye1), 'en')
    # stage net names for the extraction
    for i, s in enumerate(stages, 1):
        b.label('li', box(s + Y - 0.085, yc - 0.085, s + Y + 0.085, yc + 0.085), f'r{i}')

    # block rails on the cells' rails: VSS at y 0, VDD at y 2.72
    b.stack(box(0, -RAIL_H + 0.24, xr, 0.24), 'm1', 'm3')
    b.stack(box(0, H - 0.24, xr, H - 0.24 + RAIL_H), 'm1', 'm3')
    b.pin('m3', box(0, -RAIL_H + 0.24, xr, 0.24), 'VSS')
    b.pin('m3', box(0, H - 0.24, xr, H - 0.24 + RAIL_H), 'VDD')
    print(f'tx_ring: {ninv} inv + nand, {len([k for k, _ in pos if k == "tap"])} taps, {xr:.2f} um wide')
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
