# Top level: the 3x2 3v3 analog tile (tt_um_mattvenn_radio).
# Template pins from mag/tt_analog_3x2_3v3.def, blocks placed as layout/floorplan/floorplan.json,
# the TX blocks grouped in a tx_top subcell (LVS against xschem/tx_top.sch), power straps.
#   tools/osic-mac klayout -b -r layout/gen/top.py
# Writes build/top/tt_um_mattvenn_radio.gds and build/top/pins.json (every block pin in tile um).
import json
import os
import re
import sys

import pya

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import REPO, L, PIN, LBL, Block, snap  # noqa: E402

TOP = 'tt_um_mattvenn_radio'
FP = json.load(open(os.path.join(REPO, 'layout/floorplan/floorplan.json')))
DEF = os.path.join(REPO, 'mag/tt_analog_3x2_3v3.def')
OUT = os.path.join(REPO, 'build/top')
W, H = FP['tile']['w'], FP['tile']['h']
STRAP_Y0, STRAP_Y1 = 5.0, 220.76          # as mag/tcl/tt-analog-draw.tcl (within 10 um of both edges)


def template_pins():
    """[(name, layer, DBox)] from the TT template DEF (all met4)."""
    txt = open(DEF).read()
    pins = []
    for m in re.finditer(r'- (\S+) \+ NET .*?LAYER (\S+) \( (-?\d+) (-?\d+) \) \( (-?\d+) (-?\d+) \)'
                         r'.*?PLACED \( (-?\d+) (-?\d+) \)', txt, re.S):
        n, lay = m.group(1), m.group(2)
        x0, y0, x1, y1, px, py = (int(v) / 1000 for v in m.groups()[2:])
        pins.append((n, lay, pya.DBox(px + x0, py + y0, px + x1, py + y1)))
    return pins


class Tile(Block):
    def __init__(self):
        super().__init__(TOP)
        self.cache = {}

    def import_gds(self, cell):
        """Copy a block's GDS hierarchy in once (subcell name clashes get renamed)."""
        if cell not in self.cache:
            path = os.path.join(REPO, 'macros/radio_digital/radio_digital.gds' if cell == 'radio_digital'
                                else f'layout/{cell}.gds')
            src = pya.Layout()
            src.read(path)
            st = src.top_cell()
            c = self.ly.create_cell(cell)
            c.copy_tree(st)
            self.cache[cell] = c
        return self.cache[cell]


def place_trans(cell, b):
    t = pya.DCplxTrans(1, b['rot'], b['mirror'], 0, 0)
    bb = cell.dbbox().transformed(t)
    return pya.DCplxTrans(1, b['rot'], b['mirror'], snap(b['x'] - bb.left), snap(b['y'] - bb.bottom))


def cell_pins(cell):
    """{name: [(layer, DBox)]}: top-cell pin shapes (datatype 16) with a label on them."""
    ly = cell.layout()
    out = {}
    for lay in ('li', 'm1', 'm2', 'm3', 'm4'):
        texts = []
        for dt in (LBL[lay], PIN[lay]):
            li = ly.find_layer(*dt)
            if li is None:
                continue
            for s in cell.shapes(li).each():
                if s.is_text():
                    texts.append(s.dtext)
        li = ly.find_layer(*PIN[lay])
        if li is None:
            continue
        for s in cell.shapes(li).each():
            if not (s.is_box() or s.is_polygon()):
                continue
            bx = s.dbbox()
            for t in texts:
                if bx.contains(t.trans.disp.to_p()):
                    out.setdefault(t.string, []).append((lay, bx))
                    break
    return out


def main():
    t = Tile()
    ly, top = t.ly, t.cell
    # boundary + template pins
    t.rect((235, 4), pya.DBox(0, 0, W, H))
    for n, lay, bx in template_pins():
        assert lay == 'met4'
        t.rect('m4', bx)
        t.pin('m4', bx, n)

    # blocks; the TX ones go into tx_top (placed at the origin: same tile coordinates)
    txc = ly.create_cell('tx_top')
    top.insert(pya.DCellInstArray(txc.cell_index(), pya.DTrans()))
    pins, insts = {}, {}
    for b in FP['blocks']:
        if b['cell'].startswith('decap_'):
            continue
        c = t.import_gds(b['cell'])
        tr = place_trans(c, b)
        parent = txc if b['inst'].startswith('xtx.') else top
        parent.insert(pya.DCellInstArray(c.cell_index(), tr))
        bb = c.dbbox().transformed(tr)
        assert abs(bb.left - b['x']) < 0.006 and abs(bb.bottom - b['y']) < 0.006, (b['inst'], bb)
        insts[b['inst']] = [round(v, 3) for v in (bb.left, bb.bottom, bb.right, bb.top)]
        pins[b['inst']] = {n: [(lay, [round(v, 3) for v in (lambda r: (r.left, r.bottom, r.right, r.top))(bx.transformed(tr))])
                               for lay, bx in shp] for n, shp in cell_pins(c).items()}

    # met4 power straps (the tile's power pins)
    for s in FP['straps']:
        bx = pya.DBox(snap(s['x']), STRAP_Y0, snap(s['x'] + s['w']), STRAP_Y1)
        t.rect('m4', bx)
        t.pin('m4', bx, s['net'])

    os.makedirs(OUT, exist_ok=True)
    json.dump({'insts': insts, 'pins': pins}, open(os.path.join(OUT, 'pins.json'), 'w'), indent=0)
    t.write(os.path.join(OUT, TOP + '.gds'))


main()
