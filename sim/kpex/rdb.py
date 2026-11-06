# list kpex 2.5D report items involving the given net pair: python3 rdb.py <run> netA netB
import sys, klayout.rdb as rdb, os
D = os.path.dirname(os.path.abspath(__file__))
db = rdb.ReportDatabase(''); db.load(f'{D}/{sys.argv[1]}/lna_chain__lna_chain/lna_chain_k25d_pex_report.rdb.gz')
a, b = sys.argv[2], sys.argv[3]
def path(c):
    p = []
    while c: p.insert(0, c.name()); c = c.parent()
    return '/'.join(p)
for cat in db.each_category():
    stack = [cat]
    while stack:
        c = stack.pop(); stack.extend(c.each_sub_category())
        pp = path(c)
        if a in pp and b in pp and c.num_items():
            print(pp, c.num_items(), c.description[:200])
            for it in list(db.each_item_per_category(c.rdb_id()))[:3]:
                for v in it.each_value(): print('    ', str(v)[:200])
