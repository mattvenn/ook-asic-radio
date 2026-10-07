"""
Numbers + plot for the RX gain chain (tb_chain). Reads build/tb_chain_*.raw
(or build/tb_chain_<variant>_*.raw), prints gain per stage tap at 330 / 434 /
560 MHz, NF, CM and supply rejection, and writes sim/plots/tb_chain.png.

    python sim/chain/analyse.py [variant ...]
"""
import os
import sys

import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from rawread import read_raw

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

F0, FCMI = 433.92e6, 10e6
BAND = (330e6, F0, 560e6)
KT4_ANT = 4 * 1.380649e-23 * 300.15 * 73


def raw(name, what):
    return read_raw(os.path.join(ROOT, 'build', f'tb_{name}_{what}.raw'))[0]['vars']


def db(x):
    return 20 * np.log10(np.abs(x))


def taps(v):
    """Stage output taps present in the raw, in order, ending with out."""
    t, i = [], 1
    while f'v(x1.o{i}p)' in v:
        t.append((f'o{i}', v[f'v(x1.o{i}p)'] - v[f'v(x1.o{i}n)']))
        i += 1
    t.append(('out', v['v(out_p)'] - v['v(out_n)']))
    return t


def analyse(name):
    r = {}
    op = raw(name, 'op')
    r['I total mA'] = -np.real(op['i(vdpwr)'][0]) * 1e3
    v = raw(name, 'acdiff')
    f = np.real(v['frequency'])
    emf = v['v(emf_p)'] - v['v(emf_n)']
    curves = {}
    for nm, y in taps(v):
        g = db(y / emf)
        curves[nm] = g
        r[f'gain EMF->{nm} dB @330/434/560'] = '/'.join(f'{np.interp(fx, f, g):.1f}' for fx in BAND)
    gout = curves['out']
    pk = np.argmax(gout)
    band = f[gout > gout[pk] - 3]
    r['out -3dB band MHz'] = f'{band[0] / 1e6:.0f}-{band[-1] / 1e6:.0f}'
    r['out peak gain dB @ MHz'] = f'{gout[pk]:.1f} @ {f[pk] / 1e6:.0f}'
    r['gain EMF->out dB @10M/100M/1G'] = '/'.join(f'{np.interp(fx, f, gout):.1f}' for fx in (10e6, 100e6, 1e9))
    c = raw(name, 'accm')
    cmd = db(c['v(out_p)'] - c['v(out_n)'])
    cmc = db((c['v(out_p)'] + c['v(out_n)']) / 2)
    r['CM->out diff dB @10M/434M'] = f'{np.interp(FCMI, f, cmd):.1f}/{np.interp(F0, f, cmd):.1f}'
    r['CM->out CM dB @10M/434M'] = f'{np.interp(FCMI, f, cmc):.1f}/{np.interp(F0, f, cmc):.1f}'
    s = raw(name, 'acpsrr')
    sd = db(s['v(out_p)'] - s['v(out_n)'])
    r['VDD->out diff dB @10M/434M'] = f'{np.interp(FCMI, f, sd):.1f}/{np.interp(F0, f, sd):.1f}'
    n = raw(name, 'noise')
    fn = np.real(n['frequency'])
    on = np.real(n['onoise_spectrum'])
    gmag = np.interp(fn, f, 10 ** (gout / 20))
    nf = 10 * np.log10(on ** 2 / (gmag ** 2 * KT4_ANT))
    r['NF dB @330/434/560'] = '/'.join(f'{np.interp(fx, fn, nf):.1f}' for fx in BAND)
    return r, dict(f=f, curves=curves, cmd=cmd, cmc=cmc, sd=sd, fn=fn, nf=nf)


def main(names):
    res = {n: analyse(n) for n in names}
    keys = list(res[names[0]][0])
    print(f'{"":32s}' + ''.join(f'{n:>22s}' for n in names))
    for k in keys:
        row = ''
        for n in names:
            x = res[n][0][k]
            row += f'{x:>22s}' if isinstance(x, str) else f'{x:22.2f}'
        print(f'{k:32s}{row}')

    fig, ax = plt.subplots(1, 3, figsize=(16, 5))
    for j, n in enumerate(names):
        p = res[n][1]
        for i, (nm, g) in enumerate(p['curves'].items()):
            ax[0].semilogx(p['f'], g, f'C{i}', ls=['-', '--', ':'][j % 3],
                           label=f'{n}: {nm}' if j == 0 or nm == 'out' else None)
        ax[1].semilogx(p['f'], p['cmd'], f'C{j}', label=f'{n}: CM->diff out')
        ax[1].semilogx(p['f'], p['cmc'], f'C{j}', ls='--', label=f'{n}: CM->CM out')
        ax[1].semilogx(p['f'], p['sd'], f'C{j}', ls=':', label=f'{n}: VDD->diff out')
        ax[2].semilogx(p['fn'], p['nf'], f'C{j}', label=n)
    titles = ['gain, antenna EMF -> each stage output (dB)',
              'common mode / supply -> chain output (dB)', 'chain NF vs 73 ohm antenna (dB)']
    for a, t in zip(ax, titles):
        a.set_title(t, fontsize=10)
        a.grid(True, which='both', alpha=0.3)
        a.legend(fontsize=7)
        for fx in BAND:
            a.axvline(fx, color='k', lw=0.5, ls='-' if fx == F0 else ':')
    ax[0].set_xlim(1e6, 3e9)
    ax[0].set_ylim(-20, 80)
    ax[1].set_xlim(1e6, 3e9)
    ax[2].set_ylim(0, 30)
    fig.tight_layout()
    out = os.path.join(ROOT, 'sim', 'plots', 'tb_chain.png')
    fig.savefig(out, dpi=110)
    print('wrote', out)


if __name__ == '__main__':
    main(sys.argv[1:] or ['chain'])
