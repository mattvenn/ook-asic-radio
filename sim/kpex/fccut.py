# FasterCap check of the kpex 2.5D upper bound (docs/substrate_2026-10-29.md §1): the st5 / st6 Cs
# plates <-> g1 corner. Cuts build/kpex/lna_chain_flat.gds to the met3 / via3 / met4 / capm shapes in
# BOX (block um) and labels the nets of interest on met4 / met3 (from the kpex LVSDB); the other
# conductors in the cut stay unnamed (kpex names them $N; FasterCap holds them at 0 V like any other).
#   tools/osic python3 build/kpex/fccut.py [x0 y0 x1 y1]     -> build/kpex/fc/cut.gds
#   tools/osic kpex extract --fastercap --gds build/kpex/fc/cut.gds --cell lna_chain_cut --out_dir build/kpex/fc/run ...
import sys, os, klayout.db as db
D = os.path.dirname(os.path.abspath(__file__))
BOX = [float(v) for v in sys.argv[1:5]] if len(sys.argv) >= 5 else [0.0, 0.0, 75.0, 71.0]
NETS = ['g1p', 'g1n', 'st5_sp', 'st5_sn', 'st6_sp', 'st6_sn', 'inp', 'inn', 'o4p', 'o4n', 'o5p', 'o5n', 'outp', 'outn', 'VSS', 'VDD']
KEEP = {(70, 20): (70, 5), (70, 44): None, (71, 20): (71, 5), (89, 44): None}   # met3, via3, met4, capm -> label layer
src = db.Layout(); src.read(f'{D}/lna_chain_flat.gds'); top = src.top_cell()
out = db.Layout(); out.dbu = src.dbu; oc = out.create_cell('lna_chain_cut')
box = db.Region(db.DBox(*BOX).to_itype(src.dbu))
for (a, b), lab in KEEP.items():
    r = db.Region(top.begin_shapes_rec(src.layer(a, b))) & box
    oc.shapes(out.layer(a, b)).insert(r)
    print(f'{a}/{b}: {r.count()} polygons')
# labels: one point on each net's met4 (else met3) shape inside the box
lvs = db.LayoutVsSchematic(); lvs.read(f'{D}/lvs/lna_chain.lvsdb.gz')
c = lvs.netlist().circuit_by_name('lna_chain')
for nn in NETS:
    n = c.net_by_name(nn)
    done = False
    for lname, lab in (('met4_ncap', (71, 5)), ('met3_ncap', (70, 5)), ('met3_cap', (70, 5))):
        reg = lvs.layer_by_name(lname)
        if reg is None or n is None: continue
        s = (lvs.shapes_of_net(n, reg, True) & box)
        for p in s.each():
            for t in p.decompose_trapezoids(db.Polygon.TD_htrapezoids):
                ctr = t.bbox().center()
                oc.shapes(out.layer(*lab)).insert(db.Text(nn, db.Trans(ctr)))
                print(f'label {nn} on {lname} at {ctr.x * src.dbu:.2f},{ctr.y * src.dbu:.2f}')
                done = True
                break
            if done: break
        if done: break
    if not done: print('no shape in the box for', nn)
os.makedirs(f'{D}/fc', exist_ok=True)
out.write(f'{D}/fc/cut.gds')
