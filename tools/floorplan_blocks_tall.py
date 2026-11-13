"""Add the tall-stage blocks to layout/floorplan/blocks.json (docs/tall_stages_2026-11.md):

  lna_chain_t  the straight tall chain, from its GDS (as tools/floorplan_blocks.py), with two
               fixes: ibias is the met4 pin on the south edge (the met2 one at the input
               section's east edge is inside the chain now), and the input section's g1p / g1n
               labels (internal nodes) are dropped;
  log_det_t    a SKETCH, not laid out: log_det unwrapped into one row to sit along the chain's
               north edge. Six det_cells (layout/det_cell.gds, unchanged) in a row, t1 next to
               the end section, every input on the cells' Cc bottom plates as drawn (reached from
               the south, across the VSS rail). End section (Mbias, Rs_b, Rdet, ~10 um) at the t1
               end with det / ibias_det. Cdet (1 pF) is not in the row: it is the separate
               estimate block 'cdet' in the floorplan page.

    python3 tools/floorplan_blocks_tall.py      (needs the klayout module)
"""
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorplan_blocks as fb   # noqa: E402

END_W = 10.0        # end section: Mbias, Rs_b (2 x 0.35 um high_po), Rdet (3 x 0.69 um high_po), its tap ring


def chain():
    b = fb.block(os.path.join(ROOT, 'layout', 'lna_chain_t.gds'))
    for n in ('g1p', 'g1n'):
        b['pins'].pop(n, None)
    # the south-edge met4 ibias pin (lna_chain_t: x 42.63-43.03 in the GDS, whose bbox starts at 0.5)
    b['pins']['ibias'] = {'layer': 'met4', 'x': 42.33, 'y': 0.25}
    return b


def det_sketch(cell):
    w, h = cell['w'], cell['h']
    # Cc met4 (top-plate straps) in the cell frame, from log_det's top row (cell origin at y 14.905)
    cc = [[1.4, 7.82, 8.87, 6.96], [10.56, 7.82, 8.87, 6.96]]
    pins = {'det': {'layer': 'met2', 'x': 0.25, 'y': 4.0}, 'ibias_det': {'layer': 'met2', 'x': 0.25, 'y': 12.0},
            'VDD': {'layer': 'met3', 'x': END_W / 2, 'y': round(h - 0.6, 2)}, 'VSS': {'layer': 'met3', 'x': END_W + 0.5, 'y': 0.6}}
    m4 = []
    for k in range(6):
        x0 = END_W + k * w
        for s in ('p', 'n'):
            p = cell['pins']['inp' if s == 'p' else 'inn']
            pins[f't{k + 1}{s}'] = {'layer': 'met3', 'x': round(x0 + p['x'], 2), 'y': p['y']}
        m4 += [[round(x0 + r[0], 2), r[1], r[2], r[3]] for r in cc]
    return {'w': round(END_W + 6 * w, 2), 'h': h, 'pins': pins, 'm4': m4, 'sketch': True}


def main():
    p = os.path.join(ROOT, 'layout', 'floorplan', 'blocks.json')
    d = json.load(open(p))
    d['lna_chain_t'] = chain()
    d['log_det_t'] = det_sketch(d['det_cell'])
    with open(p, 'w') as fh:
        json.dump(d, fh, indent=1, sort_keys=True)
    for k in ('lna_chain_t', 'log_det_t'):
        print(f"{k:12s} {d[k]['w']:6.2f} x {d[k]['h']:5.2f}  {' '.join(sorted(d[k]['pins']))}")


if __name__ == '__main__':
    main()
