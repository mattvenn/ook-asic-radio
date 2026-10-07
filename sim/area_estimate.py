"""
Rough layout-area estimate for the RX analog blocks, from the device sizes in
the generators (xschem/gen/*.py), against the 2x2 analog tile.

Footprint rules (deliberately simple, for budgeting only):
  MOS     (W/nf + 1.0) x (nf*(L + 0.6) + 0.6) um per device, x m
  poly R  xhigh_po 0.35 um wide at 7.37 kOhm/um: length x 0.95 um pitch + 3 um^2 heads
  cap     MIM at ~2 fF/um^2 (+ 1.5 um edge per unit). Ideal caps in the
          schematics are costed as MIM. MIM is on met3/capm, so it can sit
          over devices: counted separately.
  routing x2.5 on the device sum (typical analog density 30-40 %).

    python sim/area_estimate.py
"""
TILE = 334.88 * 225.76          # 2x2 analog tile, um^2
ROUTE = 2.5


def mos(w, l, nf=1, m=1):
    return (w / nf + 1.0) * (nf * (l + 0.6) + 0.6) * m


def res(r):
    length = r / 7370
    return length * 0.95 + 3


def mim(c=None, w=None, l=None, n=1):
    if c is not None:
        side = (c / 2e-15) ** 0.5
        w = l = side
    return (w + 1.5) * (l + 1.5) * n


blocks = {}

# ---- gain chain: stage 1 + 5 cap-degenerated stages (chain.py, NSTAGES = 6)
dev = 2 * mos(80, 0.15, 4) + mos(6, 0.5, 2, 20) + mos(6, 0.5, 2) + 2 * res(1e3) + 2 * res(20e3)
dev += 5 * (2 * mos(20, 0.15, 4) + 2 * mos(6, 0.5, 2, 3) + 2 * res(4e3))
cap = 2 * mim(2e-12) + 5 * mim(0.6e-12)
blocks['gain chain (6 stages)'] = (dev, cap)

# ---- log detector: 6 cells + replica + rdet/cdet (logdet.py)
dev = 6 * (2 * mos(1, 0.15) + 2 * res(200e3) + 2 * res(10e3)) + mos(1, 0.15) + res(10e3) + res(8e3)
cap = 6 * 2 * mim(100e-15) + mim(5e-12)
blocks['log detector'] = (dev, cap)

# ---- LPF (lpf.py): 1 MOhm xhigh + 6 x 30x30 MIM
blocks['LPF'] = (res(1e6), mim(w=30, l=30, n=6))

# ---- comparator (comp.py)
dev = (2 * mos(20, 1, 4) + 3 * mos(4, 1) + 2 * mos(2, 1) + mos(2, 2, 1, 10) + mos(2, 2)
       + 2 * mos(2, 2, 1, 2) + mos(2, 2, 1, 5) + mos(2, 0.15) + mos(1, 0.15)
       + res(1.4e6) + 2 * res(1e6))
cap = mim(w=22, l=22) + mim(w=10, l=10)
blocks['comparator'] = (dev, cap)

# ---- switched-cap averager (comp.py)
dev = 4 * mos(0.5, 0.15) + 4 * mos(1, 0.15)
cap = mim(w=11, l=11) + mim(w=30, l=30, n=5)
blocks['SC averager'] = (dev, cap)

print(f'2x2 tile: {TILE:,.0f} um^2\n')
print(f'{"block":24s} {"devices x2.5":>13s} {"MIM":>8s}')
tot_d = tot_c = 0
for name, (d, c) in blocks.items():
    print(f'{name:24s} {d * ROUTE:13,.0f} {c:8,.0f}')
    tot_d += d * ROUTE
    tot_c += c
print(f'{"RX analog total":24s} {tot_d:13,.0f} {tot_c:8,.0f}'
      f'   -> {tot_d / TILE:.1%} devices, {tot_c / TILE:.1%} MIM (can overlap devices)')
