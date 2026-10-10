# Picture of routed nets over the block outlines, from route.py's RDUMP=1 shape dump:
#   tools/osic-mac bash -c 'RDUMP=1 python3 layout/gen/route.py'
#   python3 tools/power_routing_draw.py VGND_RX,VDPWR_RX,VGND_RXL,VAPWR_TXF docs/images/power_fix_routing.png
# (first argument: net-name prefixes to draw; met4 hatched, grey = blocks)
import json, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
S = json.load(open('build/top/route_shapes.json'))
P = json.load(open('build/top/pins.json'))
fig, ax = plt.subplots(figsize=(22, 10.5))
for i, b in P['insts'].items():
    ax.add_patch(Rectangle((b[0], b[1]), b[2]-b[0], b[3]-b[1], fill=True, fc='#eeeeee', ec='#888', lw=0.6))
    ax.text((b[0]+b[2])/2, (b[1]+b[3])/2, i.replace('xtx.', ''), ha='center', va='center', fontsize=7, color='#555')
cols = {}
pal = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#17becf', '#bcbd22', '#7f7f7f', '#000080']
def col(t):
    if t not in cols: cols[t] = pal[len(cols) % len(pal)]
    return cols[t]
sel = sys.argv[1].split(',')
for L, a in (('m1', .3), ('m2', .4), ('m3', .55), ('m4', .8)):
    for t, polys in S[L].items():
        if not any(t.startswith(s) for s in sel):
            continue
        for p in polys:
            ax.add_patch(Polygon(p, closed=True, fc=col(t), ec=col(t), alpha=a, lw=0.3, hatch='//' if L == 'm4' else None))
for t, c in cols.items():
    ax.plot([], [], color=c, lw=6, label=t)
ax.legend(loc='upper right', fontsize=7, ncol=2)
ax.set_xlim(0, 300); ax.set_ylim(0, 226); ax.set_aspect('equal'); ax.grid(alpha=.2)
ax.set_title('RX supply trunks (m4 hatched); grey = blocks')
plt.tight_layout(); plt.savefig(sys.argv[2], dpi=110)
