"""
Table of the RX corner x temperature sweep (sim/corners/rx_corners.sh).

Per case: chain supply current; gain antenna EMF -> chain out at 330 / 434 /
560 MHz; NF at 434 MHz (vs 73 ohm at 300.15 K, as sim/chain/analyse.py);
detector idle level, slope between -80 and -70 dBm (where the noise floor
sits, ~-76 dBm equivalent at tt), level at -40 dBm; comparator offset spread
over input CM 0.6..1.55 V; trim offset at DAC 0.6 / 1.8 V and the trim step
per DAC LSB (1.8/256 V) between 0.6 and 1.2 V.

    python sim/corners/rx_corners.py          (CORNERS_DIR=... for another run)
"""
import glob
import os
import sys
from collections import defaultdict

import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from rawread import read_raw

D = os.environ.get('CORNERS_DIR', os.path.join(ROOT, 'build', 'corners'))
KT4_ANT = 4 * 1.380649e-23 * 300.15 * 73
BAND = (330e6, 433.92e6, 560e6)
LSB = 1.8 / 256


def results():
    r = defaultdict(dict)
    for path in glob.glob(os.path.join(D, 'rx_*.log')):
        for line in open(path, errors='replace').read().replace('\r', '\n').splitlines():
            if not line.startswith('RESULT'):
                continue
            p = line.split()
            kind, c, t = p[1], p[2], int(float(p[3]))
            if kind == 'chain':
                r[(c, t)]['idd'] = float(p[5])
            else:
                r[(c, t)].setdefault(kind, {})[float(p[4])] = float(p[5])
    return r


def chain(c, t):
    a = os.path.join(D, f'chain_{c}_{t}_ac.raw')
    n = os.path.join(D, f'chain_{c}_{t}_noise.raw')
    if not (os.path.exists(a) and os.path.exists(n)):
        return None
    v = read_raw(a)[0]['vars']
    f = np.real(v['frequency'])
    g = np.abs((v['v(out_p)'] - v['v(out_n)']) / (v['v(emf_p)'] - v['v(emf_n)']))
    gains = [20 * np.log10(np.interp(fx, f, g)) for fx in BAND]
    on = np.real(read_raw(n)[0]['vars']['onoise_spectrum'])[0]
    g434 = np.interp(BAND[1], f, g)
    nf = 10 * np.log10(on ** 2 / (g434 ** 2 * KT4_ANT))
    return gains, nf


def main():
    r = results()
    hdr = (f'{"corner":>6} {"T":>4} {"I mA":>5} {"gain 330/434/560 dB":>20} {"NF":>5} '
           f'{"det idle":>8} {"slope mV/dB":>11} {"det -40":>7} {"cmp off mV (CM)":>15} '
           f'{"trim mV @0.6/1.8":>16} {"mV/LSB":>6}')
    print(hdr)
    order = {'tt': 0, 'ss': 1, 'ff': 2, 'sf': 3, 'fs': 4}
    for (c, t) in sorted(r, key=lambda k: (order.get(k[0], 9), k[1])):
        x = r[(c, t)]
        ch = chain(c, t)
        g = '/'.join(f'{v:.1f}' for v in ch[0]) if ch else '-'
        nf = f'{ch[1]:5.1f}' if ch else '    -'
        ld = x.get('logdet', {})
        idle = f'{ld[-110]:8.3f}' if -110 in ld else '       -'
        slope = f'{(ld[-80] - ld[-70]) / 10 * 1e3:11.1f}' if -80 in ld and -70 in ld else '          -'
        d40 = f'{ld[-40]:7.3f}' if -40 in ld else '      -'
        cm = x.get('comp_cm', {})
        cms = f'{min(cm.values()):+.1f}..{max(cm.values()):+.1f}' if cm else '-'
        tr = x.get('comp_trim', {})
        trs = f'{tr[0.6]:+.1f}/{tr[1.8]:+.1f}' if 0.6 in tr and 1.8 in tr else '-'
        step = f'{(tr[1.2] - tr[0.6]) / (0.6 / LSB):6.3f}' if 0.6 in tr and 1.2 in tr else '     -'
        idd = f'{x["idd"]:5.2f}' if 'idd' in x else '    -'
        print(f'{c:>6} {t:4d} {idd} {g:>20} {nf} {idle} {slope} {d40} {cms:>15} {trs:>16} {step}')


if __name__ == '__main__':
    main()
