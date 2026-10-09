"""Write layout/floorplan/blocks.json: every layout/*.gds top cell's bbox (um, origin
moved to the bbox's lower-left corner) and its pin labels (text on the sky130
label/pin purposes, met1..met4 and li), and its met4 / MIM (capm) obstructions as merged
boxes (a full-height met4 power strap can't cross them), for the floorplan page.

    tools/osic-mac python3 tools/floorplan_blocks.py      (needs the klayout module)
"""
import glob
import json
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
LAYERS = {67: 'li1', 68: 'met1', 69: 'met2', 70: 'met3', 71: 'met4'}   # sky130 drawing layer numbers
PURPOSES = (5, 16)                                                     # label, pin
OBS = ((71, 20), (89, 44))                                             # met4 drawing, capm (MIM top plate)


def block(path):
    import klayout.db as kdb
    ly = kdb.Layout()
    ly.read(path)
    top = ly.top_cell()
    b = top.dbbox()
    pins, on_pin = {}, set()
    pin_shapes = {}                                       # layer -> Region of its pin (datatype 16) shapes
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        if info.layer in LAYERS and info.datatype == 16:
            pin_shapes[info.layer] = kdb.Region(top.shapes(li))
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        if info.layer not in LAYERS or info.datatype not in PURPOSES:
            continue
        it = top.begin_shapes_rec(li)
        while not it.at_end():
            sh = it.shape()
            if sh.is_text() and it.path() == []:          # top-cell labels only, not subcell ones
                t = sh.dtext.transformed(it.dtrans())
                # a label on a pin shape is the pin; generators also label internal wires
                # with the same name (net names in the extraction), so those only fill in
                # when a name has no pin
                pt = kdb.Point(round(t.x / ly.dbu), round(t.y / ly.dbu))
                rg = pin_shapes.get(info.layer)
                is_pin = rg is not None and not rg.interacting(kdb.Region(kdb.Box(pt, pt).enlarged(1, 1))).is_empty()
                if t.string not in pins or (is_pin and t.string not in on_pin):
                    pins[t.string] = {'layer': LAYERS[info.layer],
                                      'x': round(t.x - b.left, 2), 'y': round(t.y - b.bottom, 2)}
                    if is_pin:
                        on_pin.add(t.string)
            it.next()
    reg = kdb.Region()
    for ln, dt in OBS:
        li = ly.find_layer(ln, dt)
        if li is not None:
            reg += kdb.Region(top.begin_shapes_rec(li))
    s = ly.dbu
    m4 = sorted([round(r.left * s - b.left, 2), round(r.bottom * s - b.bottom, 2),
                 round(r.width() * s, 2), round(r.height() * s, 2)] for r in (p.bbox() for p in reg.merged().each()))
    return {'w': round(b.width(), 2), 'h': round(b.height(), 2), 'pins': pins, 'm4': m4}


def main():
    out = {}
    for g in sorted(glob.glob(os.path.join(ROOT, 'layout', '*.gds'))):
        out[os.path.basename(g)[:-4]] = block(g)
    d = os.path.join(ROOT, 'layout', 'floorplan')
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'blocks.json'), 'w') as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    for k, v in out.items():
        print(f"{k:10s} {v['w']:6.1f} x {v['h']:5.1f}  m4 {len(v['m4']):2d}  {' '.join(sorted(v['pins']))}")


if __name__ == '__main__':
    main()
