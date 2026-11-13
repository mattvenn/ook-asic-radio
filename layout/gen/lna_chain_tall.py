# lna_chain_t: the whole chain, straight, from the tall cells (docs/tall_stages_2026-11.md):
# chain_in_t (input section, flattened in) | amp_dp_t | amp_dpc_ts (stage 2 with the low-gain
# shunt) | 4 x amp_dpc_t, abutted; stages 2, 4, 6 flipped (MX). Same ports as today's lna_chain.
# Taps: every output reaches the chain's TOP edge only (log_det is north of the chain in the
# tile), so each stage cell is built with one-edge tap columns: 'top' for unflipped stages,
# 'bottom' for flipped ones (variants written here: amp_dp_tu, amp_dpc_tsd, amp_dpc_tu,
# amp_dpc_td). In the tile the chain is mirrored (MY) so it flows west from the input pads.
# LVS reference: the input section's devices (as layout/ref/lna_chain.spice, Cin / Cs drawn as
# rectangles) and the stage cells' references.
# Run (after chain_in_tall.py): tools/osic klayout -b -r layout/gen/lna_chain_tall.py
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pya   # noqa: E402
from lay import Block, REPO, box, PIN, LBL   # noqa: E402
import amp_dpc_tall as dpc   # noqa: E402
import amp_dp_tall as dp   # noqa: E402
import amp_dpc_shunt_tall as dps   # noqa: E402
from chain_strip_tall import pins   # noqa: E402

N = 6
PORTS = 'inp inn ibias vcm lna_lo_n outp outn o1p o1n o2p o2n o3p o3n o4p o4n o5p o5n VDD VSS'.split()
TAPS = os.environ.get('CHAIN_TAPS', 'edge')   # edge: one-edge columns (north); both: full height


def variants():
    """Build and write the stage cells the chain uses; returns {stage: cell name}."""
    edge = TAPS == 'edge'
    want = {
        'amp_dp_tu': lambda: dp.make(taps='top' if edge else True, name='amp_dp_tu'),
        'amp_dpc_tsd': lambda: dpc.make(name='amp_dpc_tsd', extra=0.7, riser_left=True,
                                        hook=lambda b, c: dps.shunt(b, c, flip=edge),
                                        taps='bottom' if edge else True),
        'amp_dpc_tu': lambda: dpc.make(name='amp_dpc_tu', taps='top' if edge else True),
        'amp_dpc_td': lambda: dpc.make(name='amp_dpc_td', taps='bottom' if edge else True),
    }
    src = {'amp_dp_tu': 'amp_dp_t', 'amp_dpc_tsd': 'amp_dpc_ts', 'amp_dpc_tu': 'amp_dpc_t', 'amp_dpc_td': 'amp_dpc_t'}
    for name, fn in want.items():
        b, _ = fn()
        b.write(os.path.join(REPO, 'layout', name + '.gds'))
        ref = open(os.path.join(REPO, 'layout', 'ref', src[name] + '.spice')).read()
        ref = re.sub(rf'^\.subckt {src[name]} ', f'.subckt {name} ', ref, flags=re.M)
        open(os.path.join(REPO, 'layout', 'ref', name + '.spice'), 'w').write(f'* {name}: {src[name]} with taps {TAPS}\n' + ref)
    return {1: 'amp_dp_tu', 2: 'amp_dpc_tsd', 3: 'amp_dpc_tu', 4: 'amp_dpc_td', 5: 'amp_dpc_tu', 6: 'amp_dpc_td'}


def make(cells):
    b = Block('lna_chain_t')
    for c in sorted(set(cells.values()) | {'chain_in_t'}):
        b.ly.read(os.path.join(REPO, 'layout', c + '.gds'))
    cin = b.ly.cell('chain_in_t')
    H = b.ly.cell(cells[1]).dbbox().height()
    # the input section, flattened in; its g1p / g1n pins become labels only
    pin_in = pins(cin, b.ly)
    b.place(cin, 0, 0).flatten()
    b.ly.delete_cell_rec(cin.cell_index())           # and its pcells, now orphans
    for net in ('g1p', 'g1n'):
        for lay, r in pin_in[net]:
            sh = b.cell.shapes(b.ly.layer(*PIN[lay]))
            for s in list(sh.each()):
                if s.is_box() and s.dbox == r:
                    sh.erase(s)
    x = max(r.right for lay, r in pin_in['g1p'])     # chain_in_t's right edge
    stages = []
    for i in range(1, N + 1):
        c = b.ly.cell(cells[i])
        flip = i % 2 == 0
        tr = pya.DCplxTrans(1, 0, flip, x, H if flip else 0)
        b.place(c, x, H if flip else 0, 0, flip)
        stages.append((i, c, tr, x))
        x += c.dbbox().width()
    L = x
    # ports: the input section's are already there (inp, inn, ibias, vcm, VSS); VDD from stage 1,
    # lna_lo_n from stage 2, the taps (o1..o5, out) at the top edge
    p1 = pins(stages[0][1], b.ly)
    lay, r = p1['VDD'][0]
    b.pin(lay, stages[0][2] * r, 'VDD')
    lay, r = pins(stages[1][1], b.ly)['lna_lo_n'][0]
    b.pin(lay, stages[1][2] * r, 'lna_lo_n')
    taps = {}
    for i, c, tr, x0 in stages:
        pc = pins(c, b.ly)
        for net in ('outp', 'outn'):
            name = net if i == N else f'o{i}{net[-1]}'
            cand = [tr * r for lay, r in pc[net] if lay == 'm4' and (tr * r).top > H - 0.01]
            b.pin('m4', cand[0], name)
            taps[name] = cand[0].center().x
    print(f'lna_chain_t: {L:.2f} x {H:.2f} um; input section {stages[0][3]:.2f}, stage x: ' +
          ', '.join(f'st{i} {x0:.2f}' for i, _, _, x0 in stages))
    print('  taps (top edge, column centre x): ' + ', '.join(f'{k} {v:.2f}' for k, v in sorted(taps.items())))
    return b, dict(L=L, H=H, taps=taps)


def write_ref(cells):
    body = re.search(r'^\.subckt chain_in_t [^\n]*\n(.*?)^\.ends', open(os.path.join(REPO, 'layout', 'ref', 'chain_in_t.spice')).read(),
                     re.S | re.M).group(1)
    out = ['* lna_chain_t: xschem/lna_chain.sch as layout/ref/lna_chain.spice, from the tall cells (lna_chain_tall.py)',
           '.subckt lna_chain_t ' + ' '.join(PORTS), body.rstrip('\n')]
    for i in range(1, N + 1):
        a = ('g1p', 'g1n') if i == 1 else (f'o{i - 1}p', f'o{i - 1}n')
        o = ('outp', 'outn') if i == N else (f'o{i}p', f'o{i}n')
        sh = ' lna_lo_n' if i == 2 else ''
        out.append(f'Xa{i} {a[0]} {a[1]} ibias {o[0]} {o[1]} VDD VSS{sh} {cells[i]}')
    out.append('.ends')
    for c in sorted(set(cells.values())):
        out.append(open(os.path.join(REPO, 'layout', 'ref', c + '.spice')).read())
    open(os.path.join(REPO, 'layout', 'ref', 'lna_chain_t.spice'), 'w').write('\n'.join(out) + '\n')


if __name__ == '__main__':
    cells = variants()
    b, meta = make(cells)
    b.write(os.path.join(REPO, 'layout', 'lna_chain_t.gds'))
    write_ref(cells)
