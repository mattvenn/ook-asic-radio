"""
Numbers + plot for the first-stage LNA experiment (tb_lna_dp, tb_lna_pinv).
Reads build/tb_lna_<kind>_*.raw, prints a comparison table and writes
sim/plots/tb_lna.png.

    python sim/lna/analyse.py [dp pinv ...]

A kind is a testbench (dp, dpp, pinv) or a variant made by sim/lna/variant.sh.
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
KT4_ANT = 4 * 1.380649e-23 * 300.15 * 73      # ngspice runs at 27 C
STAGES = 2


def raw(kind, what):
    p = read_raw(os.path.join(ROOT, 'build', f'tb_lna_{kind}_{what}.raw'))
    return p[0]


def at(f, y, f0):
    return np.interp(f0, f, np.abs(y))


def db(x):
    return 20 * np.log10(np.abs(x))


def fit(t, y, freqs):
    """Least-squares amplitude of each frequency in freqs (plus DC)."""
    cols = [np.ones_like(t)]
    for f in freqs:
        cols += [np.sin(2 * np.pi * f * t), np.cos(2 * np.pi * f * t)]
    c, *_ = np.linalg.lstsq(np.array(cols).T, y, rcond=None)
    return [np.hypot(c[1 + 2 * i], c[2 + 2 * i]) for i in range(len(freqs))]


def analyse(kind):
    r = {}
    op = raw(kind, 'op')['vars']
    r['I/stage mA'] = float(np.real(op['i(vdpwr)'][0])) * -1e3 / STAGES

    d = raw(kind, 'acdiff')
    f = np.real(d['vars']['frequency'])
    v = d['vars']
    emf = v['v(emf_p)'] - v['v(emf_n)']
    o1 = v['v(o1p)'] - v['v(o1n)']
    g = o1 / emf
    r['gain EMF->o1 dB'] = db(at(f, g, F0))
    r['stage gain o1/in dB'] = db(at(f, o1 / (v['v(in_p)'] - v['v(in_n)']), F0))
    r['stage2 gain o2/o1 dB'] = db(at(f, (v['v(o2p)'] - v['v(o2n)']) / o1, F0))
    gdb = db(g)
    pk = np.argmax(gdb)
    band = f[gdb > gdb[pk] - 3]
    r['-3dB band MHz'] = f'{band[0] / 1e6:.0f}-{band[-1] / 1e6:.0f}'

    c = raw(kind, 'accm')['vars']
    cm2d = c['v(o1p)'] - c['v(o1n)']
    cm2cm = (c['v(o1p)'] + c['v(o1n)']) / 2
    cm2cm2 = (c['v(o2p)'] + c['v(o2n)']) / 2
    for fx, nm in ((FCMI, '10M'), (F0, '434M')):
        r[f'CM->diff @{nm} dB'] = db(at(f, cm2d, fx))
        r[f'CM->CM o1 @{nm} dB'] = db(at(f, cm2cm, fx))
        r[f'CM->CM o2 @{nm} dB'] = db(at(f, cm2cm2, fx))
    r['CMRR @434M dB'] = r['gain EMF->o1 dB'] - r['CM->diff @434M dB']

    s = raw(kind, 'acpsrr')['vars']
    for fx, nm in ((FCMI, '10M'), (F0, '434M')):
        r[f'VDD->diff @{nm} dB'] = db(at(f, s['v(o1p)'] - s['v(o1n)'], fx))
        r[f'VDD->CM o1 @{nm} dB'] = db(at(f, (s['v(o1p)'] + s['v(o1n)']) / 2, fx))

    n = raw(kind, 'noise')['vars']
    fn = np.real(n['frequency'])
    on = np.real(n['onoise_spectrum'])
    gmag = np.interp(fn, f, np.abs(g))
    nf = 10 * np.log10(on ** 2 / (gmag ** 2 * KT4_ANT))
    r['NF @434M dB'] = float(np.interp(F0, fn, nf))
    r['in-ref noise nV/rtHz'] = float(np.interp(F0, fn, on / gmag)) * 1e9
    n2 = raw(kind, 'noise2')['vars']
    g2 = np.abs((v['v(o2p)'] - v['v(o2n)']) / emf)
    on2 = np.interp(F0, np.real(n2['frequency']), np.real(n2['onoise_spectrum']))
    r['NF @434M at o2 dB'] = float(10 * np.log10(on2 ** 2 / (at(f, g2, F0) ** 2 * KT4_ANT)))

    t = raw(kind, 'tran')['vars']
    tt = np.real(t['time'])
    grid = np.arange(200e-9, tt[-1], 10e-12)
    sig = {}
    for nm, y in (('o1 diff', t['v(o1p)'] - t['v(o1n)']), ('o2 diff', t['v(o2p)'] - t['v(o2n)']),
                  ('o1 cm', (t['v(o1p)'] + t['v(o1n)']) / 2), ('o2 cm', (t['v(o2p)'] + t['v(o2n)']) / 2)):
        yy = np.interp(grid, tt, np.real(y))
        a434, a10 = fit(grid, yy, [F0, FCMI])
        r[f'tran {nm} 434M mV'] = a434 * 1e3
        r[f'tran {nm} 10M mV'] = a10 * 1e3
    plots = dict(f=f, g=g, cm2d=cm2d, cm2cm=cm2cm, cm2cm2=cm2cm2,
                 vdd2d=s['v(o1p)'] - s['v(o1n)'], vdd2cm=(s['v(o1p)'] + s['v(o1n)']) / 2,
                 fn=fn, nf=nf, t=tt, o1=np.real(t['v(o1p)'] - t['v(o1n)']),
                 o2p=np.real(t['v(o2p)']), o2n=np.real(t['v(o2n)']))
    return r, plots


def main(kinds):
    res = {k: analyse(k) for k in kinds}
    keys = list(res[kinds[0]][0])
    print(f'{"":28s}' + ''.join(f'{k:>14s}' for k in kinds))
    for key in keys:
        row = ''
        for k in kinds:
            v = res[k][0][key]
            row += f'{v:>14s}' if isinstance(v, str) else f'{v:14.2f}'
        print(f'{key:28s}{row}')

    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    for i, k in enumerate(kinds):
        p = res[k][1]
        c = f'C{i}'
        ax[0, 0].semilogx(p['f'], db(p['g']), c, label=f'{k}: diff gain EMF->o1')
        ax[0, 1].semilogx(p['f'], db(p['cm2d']), c, label=f'{k}: CM->diff o1')
        ax[0, 1].semilogx(p['f'], db(p['cm2cm']), c + '--', label=f'{k}: CM->CM o1')
        ax[0, 1].semilogx(p['f'], db(p['cm2cm2']), c + ':', label=f'{k}: CM->CM o2')
        ax[0, 2].semilogx(p['f'], db(p['vdd2d']), c, label=f'{k}: VDD->diff o1')
        ax[0, 2].semilogx(p['f'], db(p['vdd2cm']), c + '--', label=f'{k}: VDD->CM o1')
        ax[1, 0].semilogx(p['fn'], p['nf'], c, label=f'{k}')
        ax[1, 1].plot(p['t'] * 1e9, p['o1'] * 1e3, c, lw=0.5, label=f'{k}: o1 diff')
        ax[1, 2].plot(p['t'] * 1e9, p['o2p'], c, lw=0.5, label=f'{k}: o2p')
        ax[1, 2].plot(p['t'] * 1e9, p['o2n'], c, lw=0.5, alpha=0.5, label=f'{k}: o2n')
    titles = ['differential gain, antenna EMF -> stage 1 out (dB)',
              'common mode (antenna common path) -> stage 1/2 out (dB)',
              'supply -> stage 1 out (dB)',
              'NF at stage 1 out vs 73 ohm antenna (dB)',
              'tran: -80 dBm @434 MHz + 20 mV 10 MHz CM: o1 diff (mV)',
              'tran: stage 2 outputs, single ended (V)']
    for a, tl in zip(ax.flat, titles):
        a.set_title(tl, fontsize=10)
        a.grid(True, which='both', alpha=0.3)
        a.legend(fontsize=7)
    for a in ax[0]:
        a.axvline(F0, color='k', lw=0.5)
        a.axvline(FCMI, color='k', lw=0.5, ls=':')
    ax[1, 0].axvline(F0, color='k', lw=0.5)
    ax[1, 0].set_ylim(0, 30)
    for a in ax[0, :]:
        a.set_xlim(1e6, 3e9)
    fig.tight_layout()
    out = os.path.join(ROOT, 'sim', 'plots', 'tb_lna.png')
    fig.savefig(out, dpi=110)
    print('wrote', out)


if __name__ == '__main__':
    main(sys.argv[1:] or ['dp', 'dpp', 'pinv'])
