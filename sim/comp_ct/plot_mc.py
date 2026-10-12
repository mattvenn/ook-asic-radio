"""Histograms of the comparator-path Monte Carlo (tb_comp_ct.py / tb_avg_sc.py --mc, mc_chain.py).

    python3 sim/comp_ct/plot_mc.py      -> sim/plots/mc_comp.png, sim/plots/mc_avg_chain.png
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
MC = os.path.join(ROOT, 'build', 'mc')
OUT = os.path.join(ROOT, 'sim', 'plots')
LSB = 1.8 / 256
BAR, INK, MUTED = '#3b6fb6', '#222222', '#777777'
COMP = [('tt_27_cm1.5', 'tt 27 °C, CM 1.5 V'), ('fs_50_cm1.5', 'fs 50 °C, CM 1.5 V'),
        ('sf_10_cm1.45', 'sf 10 °C, CM 1.45 V')]


def style(ax):
    ax.grid(axis='y', color='#dddddd', lw=0.6)
    ax.set_axisbelow(True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8)


def comp():
    fig, axs = plt.subplots(3, 1, figsize=(8, 7.5), sharex=True)
    for ax, (f, title) in zip(axs, COMP):
        code = np.loadtxt(os.path.join(MC, f'comp_{f}.txt'))[:, 1] / LSB
        ax.hist(code, bins=np.arange(0, 257, 4), color=BAR, edgecolor='white', linewidth=0.8)
        top = ax.get_ylim()[1]
        for x, lab in ((96, ''), (112, ' nominal 112'), (242, ' trim end')):
            ax.axvline(x, color=MUTED, lw=1, ls='--')
            ax.text(x, top * 0.95, lab, fontsize=7, color=MUTED, va='top')
        ax.text(4, top * 0.95, 'left of 96: step > 0.13 mV/LSB,\nworse than -92 dBm',
                fontsize=7, color=MUTED, va='top')
        n = len(code)
        ax.set_title(f'{title}: {np.mean(code < 96) * 100:.0f} % below code 96, '
                     f'{(np.sum(code > 242) + 200 - n) / 2:.0f} % at the end / no switch (n = 200)',
                     fontsize=9, color=INK, loc='left')
        ax.set_ylabel('chips', fontsize=8, color=MUTED)
        style(ax)
    axs[-1].set_xlabel('DAC code where comp_ct switches (no signal), with mismatch', fontsize=8, color=MUTED)
    axs[-1].set_xlim(0, 256)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'mc_comp.png'), dpi=110)


def avg_chain():
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.2))
    a = np.loadtxt(os.path.join(MC, 'avg_tt_27.txt'))[:, 3] * 1e3
    axs[0].hist(a, bins=25, color=BAR, edgecolor='white', linewidth=0.8)
    axs[0].set_title(f'avg_sc settled offset, tt 27 °C: sigma {a.std(ddof=1):.2f} mV', fontsize=9, loc='left')
    axs[0].set_xlabel('mV', fontsize=8, color=MUTED)
    g = np.loadtxt(os.path.join(MC, 'chain_tt.txt'))[:, 7]
    axs[1].hist(g, bins=10, color=BAR, edgecolor='white', linewidth=0.8)
    axs[1].set_title(f'lna_chain gain at 434 MHz, tt: {g.min():.1f}..{g.max():.1f} dB (n = {len(g)})',
                     fontsize=9, loc='left')
    axs[1].set_xlabel('dB', fontsize=8, color=MUTED)
    for ax in axs:
        style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'mc_avg_chain.png'), dpi=110)


if __name__ == '__main__':
    comp()
    avg_chain()
    print('wrote sim/plots/mc_comp.png, sim/plots/mc_avg_chain.png')
