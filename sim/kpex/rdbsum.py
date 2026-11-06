# per-mechanism sums of kpex 2.5D report items between two nets: python3 rdbsum.py <run> netA netB
import sys, re, klayout.rdb as rdb, os
D = os.path.dirname(os.path.abspath(__file__))
db = rdb.ReportDatabase(''); db.load(f'{D}/{sys.argv[1]}/lna_chain__lna_chain/lna_chain_k25d_pex_report.rdb.gz')
a, b = sys.argv[2], sys.argv[3]
tot = {}
def walk(c, p):
    p = p + '/' + c.name()
    subs = list(c.each_sub_category())
    if not subs:
        m = re.search(r'([0-9.]+) fF', c.name())
        if m and re.search(rf'(=|\b){a}(/|$)', p) and re.search(rf'(=|\b){b}(/|$)', p):
            key = re.sub(r'/#\d+.*', '', p)
            d = re.search(r'distance ([0-9.]+)', c.name())
            t = tot.setdefault(key, [0.0, 0, 1e9, 0])
            t[0] += float(m.group(1)); t[1] += 1
            if d: t[2] = min(t[2], float(d.group(1))); t[3] = max(t[3], float(d.group(1)))
    for s in subs: walk(s, p)
for c in db.each_category(): walk(c, '')
for k, (c, n, dmin, dmax) in sorted(tot.items(), key=lambda x: -x[1][0]):
    print(f'{c*1000:8.2f} aF  {n:4d} items  d {dmin if dmin < 1e9 else "-"}..{dmax}  {k}')
