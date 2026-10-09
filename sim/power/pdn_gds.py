# KLayout script (run by sim/power/pex_power.sh): the extraction copy of the tile for the power study.
#   klayout -b -rd src=<tile gds> -rd pins=<pins.json> -rd repo=<repo> -rd case=A|B -rd dst=<out gds> -r pdn_gds.py
# 1. The tile without the digital macro, with pins where the macro's wires ended (as layout/pex_tile.sh).
# 2. The TT PDN drawn in (sim/power/pdn.py): the power gates' output columns (met4, widened) west of the tile,
#    the switched VDPWR / VAPWR met5 stripes from them across the tile, the global VGND met5 stripes
#    (joined outside the tile by a met5 frame), and via4 cuts wherever a stripe crosses a met4
#    power-pin shape of its net.
# 3. One port per supply: VDPWR / VAPWR on their gate's output column, VGND on the frame. All the
#    tile's own supply labels are removed: magic joins every label point of a net into one ideal
#    node (which shorts the straps end to end), and with several differently named ports on a net
#    its extresist writes the whole net once per port.
# Writes ties.json next to dst: every via4 landing (net, x, y, cuts) for the reports.
import json, os, sys
import pya

sys.path.insert(0, os.path.join(repo, 'sim', 'power'))
import pdn

ly = pya.Layout(); ly.read(src)
top = [c for c in ly.top_cells() if c.name != 'radio_digital'][0]
for inst in list(top.each_inst()):
    if inst.cell.name == 'radio_digital':
        inst.delete()
P = json.load(open(pins))
NAME = {'comp_in': 'comp_out', 'rx_en': 'rx_en', 'sc_phi1': 'sc_phi1', 'sc_phi2': 'sc_phi2',
        'dbg_en': 'dbg_en', 'tx_en': 'tx_en', 'tx_en_n': 'tx_en_n'}
NAME.update({f'trim_out[{i}]': f'trim[{i}]' for i in range(8)})
lm, lp, lt = ly.layer(70, 20), ly.layer(70, 16), ly.layer(70, 5)
for pn, net in NAME.items():
    for lay, b in P['pins']['macro'][pn]:
        bx = pya.DBox(b[0] - 0.3, b[1], b[0] + 0.2, b[3])
        top.shapes(lm).insert(bx); top.shapes(lp).insert(bx)
        top.shapes(lt).insert(pya.DText(net, pya.DTrans(bx.center().x, bx.center().y)))

# substrate labels (the std cells' VNB on 64/59 and 122/16) name the substrate, so magic merges it
# with VGND and extresist leaves every VGND device terminal on the bare port node. Without them
# the substrate is VSUBS (as in the block PEX), tied to VGND in the wrapper (sim/power/common.py).
for li in [ly.layer(64, 59), ly.layer(122, 16)]:
    for cell in ly.each_cell():
        for sh in list(cell.shapes(li).each()):
            if sh.is_text():
                cell.shapes(li).erase(sh)

# p-taps (tap & psdm outside nwell, and their licons): magic treats the substrate as one ideal node,
# so through the taps every VGND rail is shorted to every other one. Without them VGND reaches the
# devices through metal only, and the substrate (VSUBS, the bulk terminals) is tied to the VGND port
# in the wrapper. Substrate coupling is not modelled. Flat, so subcells' taps go too.
# (cell by cell: a KLayout-flattened copy makes magic's ext2spice crash)
notap = globals().get('notap', '1') == '1'
nrm = 0
if notap:
    lt_, lp_, ln_, lc_ = ly.layer(65, 44), ly.layer(94, 20), ly.layer(64, 20), ly.layer(66, 44)
    for cell in ly.each_cell():
        if cell.shapes(lt_).is_empty():
            continue
        ptap = (pya.Region(cell.begin_shapes_rec(lt_)) & pya.Region(cell.begin_shapes_rec(lp_))) - \
            pya.Region(cell.begin_shapes_rec(ln_))
        ptap = ptap & pya.Region(cell.shapes(lt_))
        if ptap.is_empty():
            continue
        for li in (lc_, lt_):
            r = pya.Region(cell.shapes(li))
            k = r - ptap
            nrm += r.count() - k.count() if li == lc_ else 0
            cell.shapes(li).clear(); cell.shapes(li).insert(k)
print('p-tap licons removed:', nrm)

m4, m4p, m4t = ly.layer(71, 20), ly.layer(71, 16), ly.layer(71, 5)
v4, m5, m5p, m5t = ly.layer(71, 44), ly.layer(72, 20), ly.layer(72, 16), ly.layer(72, 5)
SUP = ('VAPWR', 'VDPWR', 'VGND', 'VPWR')

# met4 power-pin shapes (tile straps, the macro's stripes) and their nets
cols = [s.dbbox() for s in top.shapes(m4p).each()]
net_of = {}
for s in top.shapes(m4t).each():
    if s.is_text() and s.text_string in SUP:
        p = s.dtext.position()
        for c in cols:
            if c.contains(p):
                net_of[(c.left, c.bottom, c.right, c.top)] = pdn.ALIAS.get(s.text_string, s.text_string)
for li in ly.layer_indexes():
    for sh in list(top.shapes(li).each()):
        if sh.is_text() and sh.text_string in SUP:
            top.shapes(li).erase(sh)


def via4(box):
    """via4 cuts (0.8 um, 1.6 um pitch, 0.19 / 0.31 enclosure) filling box (met4 and met5 overlap)."""
    nx = max(1, int((box.width() - 0.38 + 0.8) // 1.6))
    ny = max(1, int((box.height() - 0.62 + 0.8) // 1.6))
    x0 = box.center().x - (nx * 1.6 - 0.8) / 2
    y0 = box.center().y - (ny * 1.6 - 0.8) / 2
    for i in range(nx):
        for j in range(ny):
            top.shapes(v4).insert(pya.DBox(x0 + 1.6 * i, y0 + 1.6 * j, x0 + 1.6 * i + 0.8, y0 + 1.6 * j + 0.8))
    return nx * ny


ties = []
gate = {}
for net in ('VDPWR', 'VAPWR'):
    # the gate's output column, widened west over the gate (magic puts the port at the column's
    # lower-left corner, and the real switch is spread along it: keep the column's own R between
    # its two stripes ~0.1-0.2 ohm) and only as tall as the two stripes it feeds
    gx0, gx1 = pdn.GATE_COL_EXT[net]
    st = pdn.CASES[case][net]
    g = pya.DBox(gx0, min(y - h / 2 for y, h in st), gx1, max(y + h / 2 for y, h in st))
    top.shapes(m4).insert(g); top.shapes(m4p).insert(g)
    top.shapes(m4t).insert(pya.DText(net, pya.DTrans(g.center().x, g.center().y)))
    gate[net] = g
mycols = {n: [c for c, k in net_of.items() if k == n] for n in SUP[:3]}
for net, stripes in pdn.CASES[case].items():
    xr = max(c[2] for c in mycols[net]) + 0.12
    for yc, h in stripes:
        s = pya.DBox(gate[net].left - 0.12, yc - h / 2, xr, yc + h / 2)
        top.shapes(m5).insert(s)
        ties.append({'net': net, 'where': 'gate', 'x': gate[net].center().x, 'y': yc,
                     'cuts': via4(s & gate[net])})
# VGND: the global stripes, joined west and east of the tile and over its top by a met5 frame
FX0, FX1, FY1 = -80.0, pdn.TILE_W + 40, pdn.H + 40
for yc in pdn.VGND_Y:
    top.shapes(m5).insert(pya.DBox(FX0, yc - pdn.W / 2, FX1, yc + pdn.W / 2))
for fr in (pya.DBox(FX0, pdn.VGND_Y[0] - pdn.W / 2, FX0 + 10, FY1),
           pya.DBox(FX1 - 10, pdn.VGND_Y[0] - pdn.W / 2, FX1, FY1),
           pya.DBox(FX0, FY1 - 10, FX1, FY1)):
    top.shapes(m5).insert(fr)
vg = pya.DBox(FX0, pdn.MID - 1, FX0 + 10, pdn.MID + 1)
top.shapes(m5p).insert(vg)
top.shapes(m5t).insert(pya.DText('VGND', pya.DTrans(vg.center().x, vg.center().y)))
# landings on our met4 power pins
stripes = dict(pdn.CASES[case]); stripes['VGND'] = [(y, pdn.W) for y in pdn.VGND_Y]
for c, net in net_of.items():
    cb = pya.DBox(*c)
    for yc, h in stripes[net]:
        ov = cb & pya.DBox(cb.left, yc - h / 2, cb.right, yc + h / 2)
        if ov.empty() or ov.height() < 1.42:
            continue
        ties.append({'net': net, 'where': 'pin', 'x': cb.center().x, 'y': ov.center().y,
                     'xl': cb.left, 'xr': cb.right, 'y0': ov.bottom, 'y1': ov.top, 'cuts': via4(ov)})
json.dump(ties, open(os.path.join(os.path.dirname(dst), 'ties.json'), 'w'), indent=1)
top.name = 'radio_analog_lay'
ly.cleanup()
for c in [c for c in ly.top_cells() if c.name != 'radio_analog_lay']:
    c.delete()
ly.write(dst)
