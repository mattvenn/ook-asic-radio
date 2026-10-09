"""Draw the floorplan: blocks, decaps, pins and every net as a flyline.
    node tools/floorplan_dump.js > build/fp.json && python3 tools/floorplan_draw.py build/fp.json build/fp.png [xmin,xmax]
"""
import json, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
d = json.load(open(sys.argv[1])); out = sys.argv[2]
T = d['tile']; fig, ax = plt.subplots(figsize=(14 if len(sys.argv) > 3 else 22, 10.5))
ax.add_patch(Rectangle((0, 0), T['w'], T['h'], fill=False, lw=1.5))
for dc in d['decaps']:
    x, y, w, h = dc['rect']; ax.add_patch(Rectangle((x, y), w, h, fc='#f3e9c6' if dc['name'].startswith('xdeca') else '#d9ecd9', ec='none', alpha=.6, hatch='//' if dc['mim'] else None))
for n, i in d['inst'].items():
    x, y, w, h = i['rect']
    ax.add_patch(Rectangle((x, y), w, h, fc='#dde6f5', ec='#3060a0', lw=1))
    ax.text(x + w / 2, y + h / 2, f"{n}\n{i['orient']}", ha='center', va='center', fontsize=9, color='#203a6a', weight='bold')
col = {'rxin': 'red', 'rx': 'orange', 'late': 'darkorange', 'clk': 'magenta', 'en': 'gray', 'bias': 'green', 'tx': 'brown', 'trim': 'teal'}
for nt in d['nets']:
    if not nt.get('pa'): continue
    (x0, y0), (x1, y1) = nt['pa'], nt['pb']
    ax.plot([x0, x1], [y0, y1], color=col[nt['cls']], lw=1.1, alpha=.8)
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, nt['name'], fontsize=6.5, color=col[nt['cls']])
for n, i in d['inst'].items():
    for p, (x, y, mv) in i['pins'].items():
        if n == 'macro' and not any(s in p for s in ('trim', 'comp', 'phi', 'en')): continue
        ax.plot(x, y, 'o', ms=3.5, mfc='orange' if mv else 'k', mec='k', mew=.4)
        ax.text(x, y, ' ' + p, fontsize=5.5, color='#444')
xl = [float(v) for v in sys.argv[3].split(',')] if len(sys.argv) > 3 else (-3, T['w'] + 3)
ax.set_xlim(*xl); ax.set_ylim(-3, T['h'] + 3); ax.set_aspect('equal')
ax.set_xticks(range(0, int(T['w']) + 1, 25)); ax.set_yticks(range(0, int(T['h']) + 1, 25)); ax.grid(alpha=.25)
plt.tight_layout(); plt.savefig(out, dpi=110)
