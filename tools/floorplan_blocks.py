"""Write layout/floorplan/blocks.json: every layout/*.gds top cell's bbox (um, origin
moved to the bbox's lower-left corner) and its pin labels (text on the sky130
label/pin purposes, met1..met4 and li), for the floorplan page.

    tools/osic-mac python3 tools/floorplan_blocks.py      (needs the klayout module)
"""
import glob
import json
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
LAYERS = {67: 'li1', 68: 'met1', 69: 'met2', 70: 'met3', 71: 'met4'}   # sky130 drawing layer numbers
PURPOSES = (5, 16)                                                     # label, pin


def block(path):
    import klayout.db as kdb
    ly = kdb.Layout()
    ly.read(path)
    top = ly.top_cell()
    b = top.dbbox()
    pins = {}
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        if info.layer not in LAYERS or info.datatype not in PURPOSES:
            continue
        it = top.begin_shapes_rec(li)
        while not it.at_end():
            sh = it.shape()
            if sh.is_text() and it.path() == []:          # top-cell labels only, not subcell ones
                t = sh.dtext.transformed(it.dtrans())
                pins.setdefault(t.string, {'layer': LAYERS[info.layer],
                                           'x': round(t.x - b.left, 2), 'y': round(t.y - b.bottom, 2)})
            it.next()
    return {'w': round(b.width(), 2), 'h': round(b.height(), 2), 'pins': pins}


def main():
    out = {}
    for g in sorted(glob.glob(os.path.join(ROOT, 'layout', '*.gds'))):
        out[os.path.basename(g)[:-4]] = block(g)
    d = os.path.join(ROOT, 'layout', 'floorplan')
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'blocks.json'), 'w') as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    for k, v in out.items():
        print(f"{k:10s} {v['w']:6.1f} x {v['h']:5.1f}  {' '.join(sorted(v['pins']))}")


if __name__ == '__main__':
    main()
