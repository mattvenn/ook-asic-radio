"""Resistor mesh of each supply net of the tile, with the TT PDN drawn in, as an ngspice netlist.

magic's extresist is not usable for the supply nets (it lumps large parts of them into the port node:
avg_sc's and comp_ct's ground terminals came out on the VGND port itself), so the supply metal is
traced here and meshed; ngspice solves it. Same method as tools/power_r.py, which this replaces for
the power study: KLayout traces each supply net (li .. met5 + mcon, via1-4; a via3 on a MIM top
plate is not a met3-met4 contact), each layer is rasterized on a P um grid, neighbouring cells of a
layer are joined by R = rs / coverage, and the cells of two layers by the cut R / number of cuts in
the cell. Sheet / cut R: the PDK (magic tech / tech LEF).

Input: the extraction copy from sim/power/pex_power.sh (build/power/ext_<case>/radio_analog_lay.gds:
the tile without the macro, plus the power gates' output columns, the met5 stripes, the via4s,
one label per supply: on the gate column for VDPWR / VAPWR, on the met5 frame for VGND). The
port of each net is all of its label shape's cells tied together.

    tools/osic-mac python3 sim/power/mesh.py [A|B] [pitch_um]        (default A, 0.5)
Writes build/power/mesh_<case>/<net>.spice (R lines; node m<layer>_<ix>_<iy>, port node <net>)
and <net>.json (layer names, grid, origin), for sim/power/r_mesh.py.
"""
import json
import os
import sys

import numpy as np
import klayout.db as db

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
CASE = sys.argv[1] if len(sys.argv) > 1 else 'A'
P = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
DBU = 0.001
GDS = os.path.join(ROOT, 'build', 'power', f'ext_{CASE}', 'radio_analog_lay.gds')
OUT = os.path.join(ROOT, 'build', 'power', f'mesh_{CASE}' + ('' if P == 0.5 else f'_p{P:g}'))
# what-ifs (env): IDEAL=1 ties every tile-strap met4 cell to the port (strap R = 0); TRUNK=k multiplies
# the conductance of top-level routing (met1-met4 cells outside every block and not a strap) by k.
# MESH_TAG names the output (mesh_<tag>), so `case` = <tag> works downstream (link ext_<tag>).
IDEAL = os.environ.get('IDEAL') == '1'
TRUNK = float(os.environ.get('TRUNK', '1'))
if os.environ.get('MESH_TAG'):
    OUT = os.path.join(ROOT, 'build', 'power', 'mesh_' + os.environ['MESH_TAG'])
# sheet R (ohm/sq) and per-cut R (ohm) / cut size (um): magic sky130A.tech, tech LEF
LAY = [('li', (67, 20), 12.8), ('m1', (68, 20), 0.125), ('m2', (69, 20), 0.125),
       ('m3', (70, 20), 0.047), ('m4', (71, 20), 0.047), ('m5', (72, 20), 0.0285)]
CUT = [('mcon', (67, 44), 9.3, 0.17), ('v1', (68, 44), 4.5, 0.15), ('v2', (69, 44), 3.41, 0.2),
       ('v3', (70, 44), 3.41, 0.2), ('v4', (71, 44), 0.38, 0.8)]
TEXT = {'m3': [(70, 5), (70, 16)], 'm4': [(71, 5), (71, 16)], 'm5': [(72, 5), (72, 16)]}
NETS = ('VDPWR', 'VAPWR', 'VGND')


def main():
    ly = db.Layout()
    ly.read(GDS)
    top = ly.cell('radio_analog_lay')
    l2n = db.LayoutToNetlist(db.RecursiveShapeIterator(ly, top, []))
    L = {n: l2n.make_layer(ly.layer(*d), n) for n, d, _ in LAY}
    C = {n: l2n.make_layer(ly.layer(*d), n) for n, d, _, _ in CUT}
    C['v3'] = C['v3'] - l2n.make_layer(ly.layer(89, 44), 'capm')
    for n, ds in TEXT.items():
        for d in ds:
            l2n.connect(L[n], l2n.make_text_layer(ly.layer(*d), f'{n}t{d[0]}_{d[1]}'))
    seq = ['li', 'mcon', 'm1', 'v1', 'm2', 'v2', 'm3', 'v3', 'm4', 'v4', 'm5']
    allL = {**L, **C}
    for n in seq:
        l2n.connect(allL[n])
    for a, b in zip(seq, seq[1:]):
        l2n.connect(allL[a], allL[b])
    l2n.extract_netlist()
    circ = l2n.netlist().circuit_by_name(top.name)
    bb = top.dbbox()
    x0, y0 = bb.left, bb.bottom
    nx, ny = int(bb.width() / P) + 2, int(bb.height() / P) + 2
    px = int(round(P / DBU))
    org = db.Point(int(round(x0 / DBU)), int(round(y0 / DBU)))

    def raster(reg):
        if reg.is_empty():
            return np.zeros((ny, nx))
        a = reg.rasterize(org, db.Vector(px, px), db.Vector(px, px), nx, ny)
        return np.array(a) * (DBU * DBU) / (P * P)

    os.makedirs(OUT, exist_ok=True)
    for netname in NETS:
        nets = [n for n in circ.each_net() if netname in n.expanded_name().split(',')]
        assert len(nets) == 1, (netname, [n.expanded_name() for n in nets])
        net = nets[0]
        cov = [raster(l2n.shapes_of_net(net, L[n], True).merged()) for n, _, _ in LAY]
        cut = [raster(l2n.shapes_of_net(net, C[n], True).merged()) for n, _, _, _ in CUT]
        live = [c > 0.02 for c in cov]
        # strap cells (the tile's met4 power pins of this net) and the routing mask for the what-ifs
        pins_net = db.Region()
        for sh in top.shapes(ly.layer(71, 16)).each():
            if not (l2n.shapes_of_net(net, L['m4'], True) & db.Region(sh.bbox())).is_empty():
                pins_net.insert(sh.bbox())
        strap = raster(pins_net) > 0.5
        route = np.zeros((ny, nx), bool)
        if TRUNK != 1:
            insts = json.load(open(os.path.join(ROOT, 'build', 'top', 'pins.json')))['insts']
            inb = db.Region()
            for k_, b_ in insts.items():
                if k_ != 'macro':
                    inb.insert(db.DBox(*b_).to_itype(DBU))
            route = (raster(inb) < 0.5) & ~strap
        name = lambda k, iy, ix: f'm{k}_{ix}_{iy}'
        lines = [f'* {netname} supply mesh, case {CASE}, pitch {P} um (sim/power/mesh.py)']
        nr = 0
        for k, (ln, _, rs) in enumerate(LAY):
            c, m = cov[k], live[k]
            for dy, dx in ((0, 1), (1, 0)):
                a = m[:ny - dy, :nx - dx] & m[dy:, dx:]
                ys, xs = np.nonzero(a)
                g = np.minimum(c[ys, xs], c[ys + dy, xs + dx])
                for iy, ix, gg in zip(ys, xs, g):
                    nr += 1
                    if 1 <= k <= 4 and route[iy, ix] and route[iy + dy, ix + dx]:
                        gg = gg * TRUNK
                    lines.append(f'R{nr} {name(k, iy, ix)} {name(k, iy + dy, ix + dx)} {rs / gg:.5g}')
        for k, (cn, _, rc, cs) in enumerate(CUT):
            a = (cut[k] > 0) & live[k] & live[k + 1]
            ys, xs = np.nonzero(a)
            for iy, ix in zip(ys, xs):
                ncut = cut[k][iy, ix] * (P * P) / (cs * cs)
                nr += 1
                lines.append(f'R{nr} {name(k, iy, ix)} {name(k + 1, iy, ix)} {rc / ncut:.5g}')
        # the port: every cell of the label's shape (gate column / VGND frame)
        lab = None
        for kk, (ln, _, _) in enumerate(LAY):
            for d in TEXT.get(ln, []):
                for s in top.shapes(ly.layer(*d)).each():
                    if s.is_text() and s.text_string == netname:
                        lab = (kk, s.text.trans.disp.to_dtype(DBU))
        k, p = lab
        shp = [s for s in l2n.shapes_of_net(net, L[LAY[k][0]], True).each() if s.bbox().contains(p.to_itype(DBU))]
        reg = db.Region(shp[0].bbox()) if shp else db.Region()
        r = raster(reg)
        ys, xs = np.nonzero((r > 0.5) & live[k])
        for iy, ix in zip(ys, xs):
            nr += 1
            lines.append(f'R{nr} {name(k, iy, ix)} {netname} 1e-6')
        if IDEAL:
            ys2, xs2 = np.nonzero(strap & live[4])
            for iy, ix in zip(ys2, xs2):
                nr += 1
                lines.append(f'R{nr} {name(4, iy, ix)} {netname} 1e-6')
        open(os.path.join(OUT, f'{netname}.spice'), 'w').write('\n'.join(lines) + '\n')
        json.dump({'layers': [l[0] for l in LAY], 'x0': x0, 'y0': y0, 'p': P, 'nx': nx, 'ny': ny,
                   'live': {LAY[k][0]: [[int(i), int(j)] for i, j in zip(*np.nonzero(live[k]))] for k in (0, 1)}},
                  open(os.path.join(OUT, f'{netname}.json'), 'w'))
        print(f'{netname}: {sum(int(m.sum()) for m in live)} nodes, {nr} R, port cells {len(ys)}', flush=True)


main()
