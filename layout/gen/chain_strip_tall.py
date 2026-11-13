# chain_strip_t: a throwaway strip to try the tall stages in a straight chain
# (docs/handoff_tall_stages.md): amp_dp_t, then 5 x amp_dpc_t, abutted with no wiring between
# them; stages 2, 4, 6 flipped (MX) so each stage's outn lands on the next stage's inn. No input
# section. Ports: stage 1's inputs, stage 6's outputs, the taps o1..o5 (the met4 columns' top
# ends), nb, VDD, VSS. LVS reference: the two cells' references, st1 to st6 in series.
# Run (after amp_dp_tall.py and amp_dpc_tall.py): tools/osic klayout -b -r layout/gen/chain_strip_tall.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pya   # noqa: E402
from lay import Block, REPO, box, PIN, LBL   # noqa: E402

N = 6


def pins(cell, ly):
    """{name: [(layer, box)]} of a cell's pins (text on a LBL layer inside a PIN shape)."""
    out = {}
    for lay in ('m1', 'm2', 'm3', 'm4'):
        lt, lp = ly.find_layer(*LBL[lay]), ly.find_layer(*PIN[lay])
        if lt is None or lp is None:
            continue
        rects = [s.dbox for s in cell.shapes(lp).each() if s.is_box()]
        for t in cell.shapes(lt).each():
            if not t.is_text():
                continue
            p = t.dtext.trans.disp
            for r in rects:
                if r.contains(pya.DPoint(p.x, p.y)):
                    out.setdefault(t.dtext.string, []).append((lay, r))
    return out


def make():
    b = Block('chain_strip_t')
    for c in ('amp_dp_t', 'amp_dpc_t'):
        b.ly.read(os.path.join(REPO, 'layout', c + '.gds'))
    dp, dpc = b.ly.cell('amp_dp_t'), b.ly.cell('amp_dpc_t')
    H = dpc.dbbox().height()
    assert abs(dp.dbbox().height() - H) < 1e-6
    x = 0.0
    stages = []
    for i in range(1, N + 1):
        c = dp if i == 1 else dpc
        flip = i % 2 == 0 and str(i) != os.environ.get("STRIP_NOFLIP")   # mutation test hook
        if flip:
            b.place(c, x, H, 0, True)                  # MX: mirror about the centre line
            tr = pya.DCplxTrans(1, 0, True, x, H)
        else:
            b.place(c, x, 0)
            tr = pya.DCplxTrans(1, 0, False, x, 0)
        stages.append((i, c, tr, x))
        x += c.dbbox().width()
    L = x
    # ports
    p1 = pins(dp, b.ly)
    t1 = stages[0][2]
    for net in ('inp', 'inn', 'nb', 'VSS', 'VDD'):
        lay, r = p1[net][0]
        b.pin(lay, t1 * r, net)
    taps = {}
    for i, c, tr, x0 in stages:
        pc = pins(c, b.ly)
        for net in ('outp', 'outn'):
            name = net if i == N else f'o{i}{net[-1]}'
            # the tap column's end at the strip's top edge (or, cells built without tap
            # columns, the output track at the cell's right edge)
            cand = [(lay, tr * r) for lay, r in pc[net] if lay == 'm4' and (tr * r).top > H - 0.01]
            cand = cand or [(lay, tr * r) for lay, r in pc[net] if lay == 'm2']
            lay, rr = cand[0]
            b.pin(lay, rr, name)
            taps[name] = rr.center().x
    print(f'chain_strip_t: {L:.2f} x {H:.2f} um; stage x: ' +
          ', '.join(f'st{i} {x0:.2f}' for i, _, _, x0 in stages))
    print('  tap x (column centre, from the strip left edge): ' + ', '.join(f'{k} {v:.2f}' for k, v in sorted(taps.items())))
    return b, dict(L=L, H=H, taps=taps, x=[s[3] for s in stages])


def write_ref():
    refs = [open(os.path.join(REPO, 'layout', 'ref', c + '.spice')).read() for c in ('amp_dp_t', 'amp_dpc_t')]
    taps = ' '.join(f'o{i}p o{i}n' for i in range(1, N))
    top = [f'.subckt chain_strip_t inp inn nb outp outn {taps} VDD VSS']
    for i in range(1, N + 1):
        a = ('inp', 'inn') if i == 1 else (f'o{i - 1}p', f'o{i - 1}n')
        o = ('outp', 'outn') if i == N else (f'o{i}p', f'o{i}n')
        top.append(f'X{i} {a[0]} {a[1]} nb {o[0]} {o[1]} VDD VSS {"amp_dp_t" if i == 1 else "amp_dpc_t"}')
    top.append('.ends')
    with open(os.path.join(REPO, 'layout', 'ref', 'chain_strip_t.spice'), 'w') as fh:
        fh.write('* chain_strip_t: amp_dp_t + 5 x amp_dpc_t in series (chain_strip_tall.py)\n'
                 + '\n'.join(top) + '\n' + '\n'.join(refs) + '\n')     # top first: pexfix reads the first .subckt


if __name__ == '__main__':
    b, meta = make()
    b.write(os.path.join(REPO, 'layout', 'chain_strip_t.gds'))
    write_ref()
