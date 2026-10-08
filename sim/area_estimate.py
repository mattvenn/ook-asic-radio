"""
Rough layout-area estimate for the analog blocks (RX, TX, trim DAC, bias),
from the device sizes in the generators / sim scripts and measured layouts of
reused blocks, against the 2x2 (and 3x2) analog tile, with the digital.

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

# ---- TX (sim/tx/tx_explore.py). Ring from the measured ttsky25b layout:
# 19 stages = 24.3 x 9.4 um (magic bbox) -> 23 stages ~ 280 um^2 (already laid out, no x2.5).
ring = 228 * 23 / 19
# level shifter + thick buffer tapers (x4) + final N48/P144, both arms; thick-oxide
# devices get x2 extra for HV spacing / guard rings
taper = [0.42, 1.68, 6.72, 26.9, 48]
ls = mos(9, 0.15) + mos(3, 0.15) + mos(1, 0.15) + mos(0.42, 0.15) + 2 * mos(4.2, 0.5) + 2 * mos(1.7, 0.5)
buf = 2 * sum(mos(w, 0.5, max(1, round(w / 10))) + mos(3 * w, 0.5, max(1, round(3 * w / 10))) for w in taper)
blocks['TX (ring, shifter, drivers)'] = ((ls + 2 * buf) + ring / ROUTE, 0)

# ---- trim DAC: reuse the R2R ladder (tt08-analog-r2r-dac-3v3 r2r: 71.6 x 54.0 um,
# measured), driven from 1.8 V (no 3.3 V bit drivers). Already laid out: no x2.5.
blocks['R2R trim DAC (measured)'] = (3864 / ROUTE, 0)

# ---- bias generation (not designed yet): reference + mirrors + vcm divider, guess
blocks['bias generation (guess)'] = (400, 2 * 1e3)

print(f'{"block":30s} {"devices x2.5":>13s} {"MIM":>8s}')
tot_d = tot_c = 0
for name, (d, c) in blocks.items():
    print(f'{name:30s} {d * ROUTE:13,.0f} {c:8,.0f}')
    tot_d += d * ROUTE
    tot_c += c
print(f'{"analog total":24s} {tot_d:13,.0f} {tot_c:8,.0f}'
      f'   -> {tot_d / TILE:.1%} devices, {tot_c / TILE:.1%} MIM')
DIG = (40500, 23000)
for name, tile in (('2x2', TILE), ('3x2', 1.5 * TILE)):          # 3x2 ~ 502 x 226 um
    for dname, d in zip(('digital as is', 'digital reduced'), DIG):
        tot = tot_d + tot_c + d
        print(f'{name} ({tile:,.0f} um^2), {dname} ({d:,} um^2): analog dev + MIM + digital = '
              f'{tot:,.0f} um^2 = {tot / tile:.0%} (+ decap, guard rings, power routing)')
