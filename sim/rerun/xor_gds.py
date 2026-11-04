# XOR the rebuilt tile (build/top/, layout/gen/top.py + route.py) against the committed export (gds/):
#   tools/osic klayout -b -r sim/rerun/xor_gds.py
# Prints the XOR area per layer (um^2) and exits 1 if any metal / via / MIM layer differs.
import os
import sys
import pya

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
A = os.path.join(REPO, 'build/top/tt_um_mattvenn_radio.gds')
B = os.path.join(REPO, 'gds/tt_um_mattvenn_radio.gds')
METAL = {(67, 20), (67, 44), (68, 20), (68, 44), (69, 20), (69, 44), (70, 20), (70, 44), (71, 20), (71, 44),
         (72, 20), (89, 44), (97, 44), (75, 20)}       # li..met5, mcon..via4, capm / capm2
la, lb = pya.Layout(), pya.Layout()
la.read(A)
lb.read(B)
ta, tb = la.top_cell(), lb.top_cell()
keys = {(li.layer, li.datatype) for li in la.layer_infos()} | {(li.layer, li.datatype) for li in lb.layer_infos()}
bad = 0
for k in sorted(keys):
    ia, ib = la.find_layer(*k), lb.find_layer(*k)
    ra = pya.Region(ta.begin_shapes_rec(ia)) if ia is not None else pya.Region()
    rb = pya.Region(tb.begin_shapes_rec(ib)) if ib is not None else pya.Region()
    ra.merge()
    rb.merge()
    x = ra ^ rb
    if not x.is_empty():
        area = x.area() * la.dbu ** 2
        print(f'layer {k[0]}/{k[1]}: XOR {area:.4f} um^2, {x.count()} polygons')
        if k in METAL:
            bad += 1
print('xor:', 'metal identical' if bad == 0 else f'METAL DIFFERS on {bad} layers')
sys.exit(1 if bad else 0)
