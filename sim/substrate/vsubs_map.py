# Where each net's substrate (VSUBS) capacitance lands: kpex 2.5D report items (overlap polygons,
# fringe edges) between a net and VSUBS, each assigned to the nearest substrate port or p-tap
# (geom.json; a tap = VSS). Output: vsubs_map.json {net: {dest: fraction}} (dest = port name or 'VSS').
#   tools/osic-mac python3 build/substrate/vsubs_map.py [kpex run, default h100]
import sys, re, json, os, numpy as np, klayout.rdb as rdb
D = os.path.dirname(os.path.abspath(__file__))
run = sys.argv[1] if len(sys.argv) > 1 else 'h100'
g = json.load(open(f'{D}/geom.json'))
names = list(g['ports'])
dest, bx = [], []
for n in names:
    for b in g['ports'][n]: dest.append(n); bx.append(b)
for b in g['ptap']: dest.append('VSS'); bx.append(b)
bx = np.array(bx); dest = np.array(dest)
db = rdb.ReportDatabase(''); db.load(f'{D}/../kpex/{run}/lna_chain__lna_chain/lna_chain_k25d_pex_report.rdb.gz')
items = []   # (net, fF, x, y)
num = re.compile(r'#\d+:? ([0-9.]+) fF')
def walk(c, p, val):
    p = p + '/' + c.name(); subs = list(c.each_sub_category())
    m = num.search(c.name())
    if m: val = float(m.group(1))
    if not subs and 'VSUBS' in p and val is not None and c.name() in ('Top Polygon', 'Inside Edge'):   # not the substrate's own shape
        nets = re.findall(r'(?:inside_net=|outside_net=)([^/]+)', p) or re.findall(r'/([^/ ]+) – ([^/ ]+)/', p)
        if nets and isinstance(nets[0], tuple): nets = list(nets[0])
        net = [x for x in nets if x != 'VSUBS']
        if not net: return
        pts = []
        for it in db.each_item_per_category(c.rdb_id()):
            for v in it.each_value():
                s = str(v)
                pts += [tuple(map(float, q)) for q in re.findall(r'(-?[0-9.]+),(-?[0-9.]+)', s)]
        if pts:
            a = np.array(pts); items.append((net[0], val, a[:, 0].mean(), a[:, 1].mean()))
    for s in subs: walk(s, p, val)
for c in db.each_category(): walk(c, '', None)
print(len(items), 'VSUBS items')
xy = np.array([(i[2], i[3]) for i in items]); w = np.array([i[1] for i in items]); nets = np.array([i[0] for i in items])
best = np.empty(len(items), int)
for s in range(0, len(items), 20000):
    p = xy[s:s + 20000]
    dx = np.maximum(0, np.maximum(bx[None, :, 0] - p[:, None, 0], p[:, None, 0] - bx[None, :, 2]))
    dy = np.maximum(0, np.maximum(bx[None, :, 1] - p[:, None, 1], p[:, None, 1] - bx[None, :, 3]))
    best[s:s + 20000] = np.argmin(dx * dx + dy * dy, axis=1)
res = {}
for n in sorted(set(nets)):
    m = nets == n; tot = w[m].sum()
    d = {}
    for k in np.where(m)[0]: d[dest[best[k]]] = d.get(dest[best[k]], 0) + w[k]
    res[n] = {k: v / tot for k, v in sorted(d.items(), key=lambda x: -x[1])}
    print(f'{n:10} {tot:8.2f} fF (report sum): ' + ', '.join(f'{k} {v:.2f}' for k, v in list(res[n].items())[:5]))
json.dump(res, open(f'{D}/vsubs_map.json', 'w'), indent=1)
