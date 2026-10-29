# Substrate geometry in the lna_chain block frame (um), for solve.py.
# In: build/kpex/lna_chain_flat.gds (the block), build/kpex/lvs/lna_chain.lvsdb.gz (devices),
#     gds/tt_um_mattvenn_radio.gds (the tile: taps / wells in the margin, chain instance removed).
# Out: build/substrate/geom.json: domain, ptap / nwell boxes, ports {name: boxes}, port meta.
# Run: tools/osic-mac python3 build/substrate/geom.py
import json, sys, klayout.db as db
MARGIN = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
L = lambda ly, a, b: ly.layer(a, b)
def reg(ly, cell, a, b):
    r = db.Region(cell.begin_shapes_rec(L(ly, a, b))); r.merge(); return r
# --- block
bl = db.Layout(); bl.read('build/kpex/lna_chain_flat.gds'); bc = bl.top_cell()
bbox = bc.dbbox()
diff, tap, nw, nsd, psd = (reg(bl, bc, *x) for x in [(65, 20), (65, 44), (64, 20), (93, 44), (94, 20)])
poly, capm = reg(bl, bc, 66, 20), reg(bl, bc, 89, 44)
ptap_b = (tap & psd) - nw
nact = (diff & nsd) - nw
print('block: ptap', ptap_b.area() * 1e-6, 'um2; n-active', nact.area() * 1e-6, 'um2; nwell', nw.area() * 1e-6)
print('  diff/tap in nwell (ignored):', ((diff + tap) & nw).area() * 1e-6, 'um2; p-diff outside nwell:', ((diff & psd) - nw).area() * 1e-6)
# --- tile margin (tile -> block: x = 158.5 - X, y = 76.97 - Y, i.e. R180 + shift)
tl = db.Layout(); tl.read('gds/tt_um_mattvenn_radio.gds'); tt = tl.top_cell()
for inst in list(tt.each_inst()):
    if inst.cell.name == 'lna_chain': inst.delete()
T = db.ICplxTrans(1, 180, False, db.Vector(158500, 76970))
dom = db.Box(-MARGIN * 1000, -MARGIN * 1000, bbox.right * 1000 + MARGIN * 1000, bbox.top * 1000 + MARGIN * 1000)
tdom = dom.transformed(T.inverted())
def treg(a, b):
    r = db.Region(tt.begin_shapes_rec_touching(L(tl, a, b), tdom)); r.merge(); r = r.transformed(T); return r & db.Region(dom)
blockreg = db.Region(db.Box(0, 0, bbox.right * 1000, bbox.top * 1000))
t_nw, t_tap, t_psd = treg(64, 20), treg(65, 44), treg(94, 20)
ptap_t = ((t_tap & t_psd) - t_nw) - blockreg
nw_t = t_nw - blockreg
tile_in = db.Region(db.Box(0, 0, 493120, 225760).transformed(T)) & db.Region(dom)
print('margin: ptap', ptap_t.area() * 1e-6, 'nwell', nw_t.area() * 1e-6, '; domain outside the tile', (db.Region(dom) - tile_in).area() * 1e-6, 'um2')
ptap = ptap_b + ptap_t; ptap.merge(); nwell = nw + nw_t; nwell.merge()
# --- ports
lvs = db.LayoutVsSchematic(); lvs.read('build/kpex/lvs/lna_chain.lvsdb.gz')
top = lvs.netlist().circuit_by_name('lna_chain')
xr = lvs.xref(); cp = next(xr.each_circuit_pair())
sname = {p.first().id(): p.second().name.lower() for p in xr.each_device_pair(cp)}
ports, meta = {}, {}
def pick(region, pts):
    out = db.Region()
    for poly_ in region.each_merged():
        if any(poly_.inside(p) for p in pts): out.insert(poly_)
    return out
used = db.Region(); cap_later = []
for d in top.each_device():
    n = sname[d.id()]; cls = d.device_class().name
    pts = [d.trans.disp] + [(d.trans * ca.trans).disp for ca in d.each_combined_abstract()]
    pts = [db.Point(round(p.x * 1000), round(p.y * 1000)) for p in pts]
    if 'nfet' in cls: r = pick(nact, pts); kind = 'mos'
    elif 'res' in cls:
        if not n.startswith('rb'): continue          # stage loads: their nets' VSUBS go to the stage's devices
        r = pick(poly, pts); kind = 'res'
    elif 'cap_mim' in cls:
        if not n.startswith('cin'): continue
        r = pick(capm, pts); kind = 'cap'
    if kind == 'cap':
        cap_later.append((n, r, d)); continue
    if (r & used).area(): print('WARNING overlapping port', n)
    used += r
    nets = {t.name: d.net_for_terminal(i).name for i, t in enumerate(d.device_class().terminal_definitions()) if d.net_for_terminal(i)}
    ports[n] = [[b.left / 1000, b.bottom / 1000, b.right / 1000, b.top / 1000] for b in r.decompose_trapezoids_to_region(db.Polygon.TD_htrapezoids).each() for b in [b.bbox()]]
    meta[n] = {'kind': kind, 'nf': len(pts), 'nets': nets, 'area': r.area() * 1e-6, 'bbox': [r.bbox().left / 1000, r.bbox().bottom / 1000, r.bbox().right / 1000, r.bbox().top / 1000]}
    print(f'  port {n:12} {kind} {len(pts):3d} pts area {r.area() * 1e-6:8.2f} um2 bbox {r.bbox().to_dtype(0.001)} {nets}')
# Cin: the MIM footprint minus the ports under it, the taps and n-well, as 3 x 3 sub-patches
# (one equipotential 31 um patch would short the p-well under the cap)
NS = 3
for n, r, d in cap_later:
    r = r - used - ptap - nwell
    bb = r.bbox(); nets = {t.name: d.net_for_terminal(i).name for i, t in enumerate(d.device_class().terminal_definitions())}
    for i in range(NS):
        for j in range(NS):
            w, h = bb.width() / NS, bb.height() / NS
            sub = r & db.Region(db.Box(bb.left + i * w, bb.bottom + j * h, bb.left + (i + 1) * w, bb.bottom + (j + 1) * h))
            nm = f'{n}_{i}{j}'
            ports[nm] = [[b.left / 1000, b.bottom / 1000, b.right / 1000, b.top / 1000] for b in (q.bbox() for q in sub.decompose_trapezoids_to_region(db.Polygon.TD_htrapezoids).each())]
            meta[nm] = {'kind': 'cap', 'nets': nets, 'area': sub.area() * 1e-6, 'bbox': [sub.bbox().left / 1000, sub.bbox().bottom / 1000, sub.bbox().right / 1000, sub.bbox().top / 1000]}
    print(f'  port {n}_ij  cap  area {r.area() * 1e-6:8.2f} um2 (after removing ports / taps / n-well under it) bbox {bb.to_dtype(0.001)}')
islands = sum(1 for _ in nact.each_merged()); print('n-active islands', islands, 'ports', len(ports))
unused = nact - used
print('n-active not in any port', unused.area() * 1e-6, 'um2', [str(p.bbox().to_dtype(0.001)) for p in unused.each_merged()][:10])
def boxes(r):
    return [[b.left / 1000, b.bottom / 1000, b.right / 1000, b.top / 1000] for b in (q.bbox() for q in r.decompose_trapezoids_to_region(db.Polygon.TD_htrapezoids).each())]
json.dump({'domain': [dom.left / 1000, dom.bottom / 1000, dom.right / 1000, dom.top / 1000],
           'block': [0, 0, bbox.right, bbox.top], 'tile_in_domain': boxes(tile_in),
           'ptap': boxes(ptap), 'ptap_block': boxes(ptap_b), 'ptap_margin': boxes(ptap_t), 'nwell': boxes(nwell),
           'ports': ports, 'meta': meta}, open('build/substrate/geom.json', 'w'))
