#!/usr/bin/env python3
"""Via audit (read-only): single cuts and single rows of cuts, per block and cut layer.

Harald Pretl's review point 11 (docs/handoff_via_arrays.md): every junction between two metals
should be a cut array (>= 2 x 2 where it fits), never one cut. This counts, per GDS and per cut
layer (mcon, via1, via2, via3):

  clusters  groups of cuts that touch at array spacing (cuts closer than GAP join one cluster)
  single    clusters of exactly 1 cut
  row       clusters of n >= 2 cuts all in one row or one column (1 x n)
  short     of those rows, the ones with n <= 3

mcon clusters whose li also carries a licon (device source/drain strips, gate pads, taps: the
pcell's own contacts) are counted apart as 'mcon-dev'; 'mcon' is the li wiring to met1 only.

Each cluster is named by the labels on the metal it lands on (upper metal first, then lower);
'?' when no label on that metal shape names it. Labels come from the flattened cell, so a
block's internal labels count too.

Run (the klayout Python module: on sim-0 directly, elsewhere inside tools/osic):
  python3 tools/via_audit.py                      # every block in scope + the tile, table
  python3 tools/via_audit.py tx_drv bias_gen      # just these blocks (layout/<b>.gds)
  python3 tools/via_audit.py --list tx_drv        # plus every single cut / short row: layer, net, x, y
  python3 tools/via_audit.py --md                 # the table as Markdown (for docs/layout.md)

The tile entry is gds/tt_um_mattvenn_radio.gds with the digital macro (radio_digital) left out:
'tile' counts everything else flattened, 'tile-top' only the shapes drawn in the top cell
(the top-level routing of top_nets.py / route.py).
"""
import os
import sys

import klayout.db as kdb

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# cut layer: (gds layer, datatype), metal below, metal above
CUTS = {
    'mcon': ((67, 44), 'li', 'm1'),
    'via1': ((68, 44), 'm1', 'm2'),
    'via2': ((69, 44), 'm2', 'm3'),
    'via3': ((70, 44), 'm3', 'm4'),
}
METAL = {'li': (67, 20), 'm1': (68, 20), 'm2': (69, 20), 'm3': (70, 20), 'm4': (71, 20)}
LABEL = {'li': [(67, 5), (67, 16)], 'm1': [(68, 5), (68, 16)], 'm2': [(69, 5), (69, 16)],
         'm3': [(70, 5), (70, 16)], 'm4': [(71, 5), (71, 16)]}
GAP = 0.25          # um: cuts closer than this are one cluster (array spacing is 0.17-0.20)

# the analog blocks of the tile (layout/floorplan/floorplan.json), plus the tall chain cells
BLOCKS = ['tx_drv', 'tx_ls', 'tx_ls_en', 'tx_ring', 'bias_gen', 'comp_ct', 'avg_sc', 'lpf_rc',
          'ctrim_1p', 'r2r', 'dbg_tg',
          'decap_vapwr_p1', 'decap_vapwr_p2', 'decap_vapwr_p3', 'decap_vapwr_p4', 'decap_vapwr_p5',
          'decap_vapwr_p6', 'decap_vapwr_p7', 'decap_vdpwr_p1', 'decap_vdpwr_p2', 'decap_vdpwr_p3',
          'decap_vdpwr_p4',
          'det_cell', 'log_det_t', 'cdet_t', 'amp_dp_t', 'amp_dpc_t', 'amp_dpc_ts', 'chain_in_t',
          'lna_chain_t', 'rx_t']
TILE = 'gds/tt_um_mattvenn_radio.gds'
MACRO = 'radio_digital'


def load(path, skip=None, top_only=False):
    """Layout with the top cell flattened (minus instances of cell `skip`, or minus every
    instance when top_only)."""
    ly = kdb.Layout()
    ly.read(path)
    top = ly.top_cell()
    for inst in list(top.each_inst()):
        if top_only or (skip and inst.cell.name == skip):
            inst.delete()
    top.flatten(-1, True)
    return ly, top


def texts(ly, top, metal):
    out = []
    for lay in LABEL[metal]:
        li = ly.find_layer(*lay)
        if li is None:
            continue
        for s in top.shapes(li).each():
            if s.is_text():
                out.append((s.text_string, s.text.trans.disp))
    return out


def audit(ly, top):
    """{cut: [(n, kind, net, x, y), ...]} for every cluster; kind 'single' / 'row' / 'array'."""
    res = {}
    dbu = ly.dbu
    g = int(round(GAP / 2 / dbu))
    metals, labels = {}, {}
    for m, lay in METAL.items():
        li = ly.find_layer(*lay)
        metals[m] = kdb.Region(top.shapes(li)).merged() if li is not None else kdb.Region()
        labels[m] = texts(ly, top, m)
    for cut, (lay, lo, hi) in CUTS.items():
        li = ly.find_layer(*lay)
        res.setdefault(cut, [])
        if cut == 'mcon':
            res.setdefault('mcon-dev', [])
        if li is None:
            continue
        cuts = kdb.Region(top.shapes(li))
        cuts.merged_semantics = False
        if cuts.is_empty():
            continue
        licon = ly.find_layer(66, 44)
        licon = kdb.Region(top.shapes(licon)) if licon is not None else kdb.Region()
        groups = cuts.sized(g).merged()
        for grp in groups.each():
            gr = kdb.Region(grp)
            mine = [c for c in cuts.interacting(gr).each()]
            n = len(mine)
            xs = {c.bbox().center().x for c in mine}
            ys = {c.bbox().center().y for c in mine}
            kind = 'single' if n == 1 else ('row' if len(xs) == 1 or len(ys) == 1 else 'array')
            name = cut
            if cut == 'mcon' and not metals['li'].interacting(gr).interacting(licon).is_empty():
                name = 'mcon-dev'
            net = '?'
            for m in (hi, lo):
                land = metals[m].interacting(gr)
                names = sorted({t for t, p in labels[m] if any(poly.inside(p) for poly in land.each())})
                if names:
                    net = '/'.join(names[:2])
                    break
            c = grp.bbox().center()
            res.setdefault(name, []).append((n, kind, net, round(c.x * dbu, 2), round(c.y * dbu, 2)))
    return res


def row_of(name, res):
    r = {}
    for cut, cl in res.items():
        r[cut] = (len(cl), sum(1 for c in cl if c[1] == 'single'), sum(1 for c in cl if c[1] == 'row'),
                  sum(1 for c in cl if c[1] == 'row' and c[0] <= 3))
    return r


def main(argv):
    lst = '--list' in argv
    md = '--md' in argv
    names = [a for a in argv if not a.startswith('--')] or BLOCKS + ['tile', 'tile-top']
    table = []
    for b in names:
        if b == 'tile':
            ly, top = load(os.path.join(REPO, TILE), skip=MACRO)
        elif b == 'tile-top':
            ly, top = load(os.path.join(REPO, TILE), top_only=True)
        else:
            p = os.path.join(REPO, 'layout', b + '.gds')
            if not os.path.exists(p):
                print(f'# {b}: no {p}', file=sys.stderr)
                continue
            ly, top = load(p)
        res = audit(ly, top)
        table.append((b, row_of(b, res)))
        if lst:
            for cut, cl in res.items():
                for n, kind, net, x, y in sorted(cl, key=lambda c: (c[2], c[3], c[4])):
                    if kind == 'single' or (kind == 'row' and n <= 3):
                        print(f'{b:16s} {cut:5s} {kind:6s} n={n:<3d} {net:24s} ({x:.2f}, {y:.2f})')
    cols = ['mcon-dev'] + list(CUTS)
    if md:
        print('| block | ' + ' | '.join(f'{c} cl / 1 / 1×n (≤3)' for c in cols) + ' |')
        print('|---|' + '---|' * len(cols))
        for b, r in table:
            print(f'| {b} | ' + ' | '.join('{} / {} / {} ({})'.format(*r[c]) if r[c][0] else '-' for c in cols) + ' |')
    else:
        print(f'{"block":16s} ' + ' '.join(f'{c + " cl/1/1xn(<=3)":>22s}' for c in cols))
        for b, r in table:
            print(f'{b:16s} ' + ' '.join(f'{"{}/{}/{}({})".format(*r[c]) if r[c][0] else "-":>22s}' for c in cols))


if __name__ == '__main__':
    main(sys.argv[1:])
