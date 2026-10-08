# Render a GDS to PNG with KLayout (batch):
#   klayout -zz -rd gds=<in.gds> -rd png=<out.png> [-rd w=1600] [-rd hide=75/20,64/20] -r tools/render_gds.py
import pya, os
gds, png = gds, png  # noqa: F821  (set with -rd)
w = int(globals().get('w', 1600))
lv = pya.LayoutView()
lv.set_config("background-color", "#ffffff")
lv.set_config("grid-visible", "false")
lv.set_config("text-visible", "false")
lv.load_layout(gds, 0)
lyp = os.path.join(os.environ.get('PDK_ROOT', '/foss/pdks'), 'sky130A/libs.tech/klayout/tech/sky130A.lyp')
if os.path.exists(lyp):
    lv.load_layer_props(lyp)
hide = [tuple(map(int, x.split('/'))) for x in globals().get('hide', '').split(',') if x]
it = lv.begin_layers()
while not it.at_end():
    lp = it.current()
    if (lp.source_layer, lp.source_datatype) in hide:
        lp.visible = False
        lv.set_layer_properties(it, lp)
    it.next()
lv.max_hier()
lv.zoom_fit()
bb = lv.active_cellview().cell.dbbox()
h = int(w * bb.height() / bb.width())
lv.save_image(png, w, h)
print('wrote', png, w, 'x', h)
