import json, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
g = json.load(open('build/substrate/geom.json'))
f, ax = plt.subplots(figsize=(18, 11))
def draw(bs, **k):
    for b in bs: ax.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], **k))
draw(g['nwell'], color='gold', alpha=0.5, lw=0)
draw(g['ptap'], color='blue', lw=0)
for n, bs in g['ports'].items():
    draw(bs, color='red' if g['meta'][n]['kind'] == 'mos' else 'green', alpha=0.6, lw=0)
    b = g['meta'][n]['bbox']; ax.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, n, fontsize=6, ha='center')
d = g['domain']; ax.set_xlim(d[0], d[2]); ax.set_ylim(d[1], d[3]); ax.set_aspect('equal')
b = g['block']; ax.add_patch(Rectangle((0, 0), b[2], b[3], fill=False, ec='k'))
for t in g['tile_in_domain']: ax.add_patch(Rectangle((t[0], t[1]), t[2]-t[0], t[3]-t[1], fill=False, ec='gray', ls='--'))
ax.set_title('blue p-tap (0 V), gold n-well (insulating 0-0.8 um), red NMOS ports, green passive ports; dashed: tile area')
plt.savefig('build/substrate/geom.png', dpi=110, bbox_inches='tight')
