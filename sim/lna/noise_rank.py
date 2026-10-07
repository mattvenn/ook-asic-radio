"""Rank noise contributors from noise_break.sh output (stdin): share of total
output noise power at 433.92 MHz, grouped per device (both halves summed)."""
import re
import sys
from collections import defaultdict

kind, data = None, defaultdict(dict)
for line in sys.stdin:
    if line.startswith('==='):
        kind = line.split()[1]
        continue
    m = re.match(r'onoise[._](\S+) = (\S+)', line)
    if m:
        data[kind][m.group(1)] = float(m.group(2))
for kind, d in data.items():
    tot = d.pop('spectrum') ** 2
    groups, flick = defaultdict(float), defaultdict(float)
    for name, v in d.items():
        # per-device totals: resistors 'r.x1.rl_p' / 'rant_p', mosfets 'm.x1.xmp.msky130_...'
        # (mosfet sub-terms '.id', '.1overf', ... follow as a 5th field)
        if name.endswith(('_thermal', '_1overf')):
            continue
        parts = name.split('.')
        if name.startswith('m.'):
            dev = '.'.join(parts[1:-1]) if len(parts) == 4 else '.'.join(parts[1:-2])
            if len(parts) == 5:
                if parts[-1] == '1overf':
                    flick[re.sub(r'_[pn]$', '_pn', dev)] += v ** 2
                continue
        else:
            dev = name
        dev = re.sub(r'_[pn]$', '_pn', dev)
        dev = re.sub(r'xpad_[pn]', 'xpad_pn', dev)
        groups[dev] += v ** 2
    print(f'=== {kind}: total {tot ** 0.5 * 1e9:.1f} nV/rtHz at o1, accounted '
          f'{100 * sum(groups.values()) / tot:.0f} %')
    for dev, p in sorted(groups.items(), key=lambda x: -x[1])[:10]:
        fl = f'  (1/f: {100 * flick[dev] / tot:4.1f} %)' if dev in flick else ''
        print(f'  {dev:30s} {100 * p / tot:5.1f} %{fl}')
