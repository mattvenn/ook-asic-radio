# tx_drv layout (v2): one antenna arm, out = in & en (xschem/gen/tx.py:tx_drv).
#   thick NAND2, then inverters x4 per stage: N 0.42 / 1.68 / 6.72 / 26.88 / 48, P = 3 N, L 0.5.
# Built with rows.py: PMOS row (fingers <= 8 um), routing channel, NMOS row (<= 4.5 um),
# one guard ring per row, VAPWR / VSS rails. The output stage sits at the right end of
# both rows; its drain bars (met2+met3) join the 'out' riser on the right edge.
#
# Wire widths and cut counts come from the measured currents (sim/tx/tb_tx_drv.py,
# tt, per arm; docs/layout.md) at 2x margin on the tech-LEF limits:
#   VAPWR 6.65 mA avg / 9.45 rms (stage 5 PMOS sources), VSS 2.3 / 3.6,
#   out 9.8 mA rms, y4 ~1.45 mA rms per side, y3 ~0.4, earlier nets << 1 mA.
# Run: tools/osic klayout -b -r layout/gen/tx_drv.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, REPO          # noqa: E402
from rows import Dev, Net, build, inverter_roles   # noqa: E402

DRV_N = [0.42, 1.68, 6.72, 26.88, 48]   # as xschem/gen/tx.py
LG = 0.5
HP, HN = 8.0, 4.5      # max finger height (um), P and N rows: rows come out about equal length

NETS = {
    'in': Net(0.3, 0.3, 0.5, 0.05, io='L'), 'en': Net(0.3, 0.3, 0.5, 0.05, io='L'),
    'y0': Net(0.28, 0.3, 0.5, 0.05), 'y1': Net(0.3, 0.3, 0.5, 0.1), 'y2': Net(0.4, 0.4, 0.5, 0.2),
    'y3': Net(0.8, 0.8, 0.6, 0.45), 'y4': Net(1.6, 2.0, 1.0, 1.45),
    'out': Net(io='riser', irms=9.8),
}


def make():
    b = Block('tx_drv')
    P, N = [], []
    p = Fet(b, 'p', 2 * 1.26, LG, nf=2, gate='bottom', bulk='None')
    n = Fet(b, 'n', 2 * 0.84, LG, nf=2, gate='top', bulk='None')
    P.append(Dev(p, ['R', 'D', 'R'], [('in', [0]), ('en', [1])], 'y0'))
    N.append(Dev(n, ['D', None, 'R'], [('in', [0]), ('en', [1])], 'y0'))
    for i, wn in enumerate(DRV_N, 1):
        g, d = f'y{i - 1}', ('out' if i == len(DRV_N) else f'y{i}')
        for row, kind, W, H in ((P, 'p', 3 * wn, HP), (N, 'n', wn, HN)):
            f = Fet(b, kind, W, LG, gate='bottom' if kind == 'p' else 'top', bulk='None', nfmax=H)
            # drain bar height: enough via1 rows for the net's current
            hb = {'out': 3.0 if kind == 'p' else 2.0, 'y4': 2.0, 'y3': 1.3, 'y2': 0.8}.get(d, 0.5)
            row.append(Dev(f, inverter_roles(f), [(g, list(range(f.nf)))], d, hb))
    return build(b, P, N, NETS, rail_h=3.0, out_w=3.0, align_last=True)


if __name__ == '__main__':
    make().write(os.path.join(REPO, 'layout', 'tx_drv.gds'))
