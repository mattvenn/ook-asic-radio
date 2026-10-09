"""The TT PDN around our tile, as built by tt-multiplexer (github.com/TinyTapeout/tt-multiplexer,
ol2/tt_top: pdn.tcl, build.py, odb_route.py ModulePowerStrapper; py/tt/elements.py). Tile um.

- VGND: the global met5 grid. Sets of three 8.75 um stripes (vdpwr, vgnd, vapwr, 2.25 um apart,
  'starts_with POWER'), set pitch 57.12 um. The power-gated user tiles take the 19.75 um gap
  between sets for their switched stripes (below), so the sets sit at mid +- 28.56 + k * 57.12 and
  vgnd (the middle stripe) lands on our VGND met4 at 27.20, 84.32, 141.44, 198.56.
- VDPWR / VAPWR are switched: tt_pg_1v8_*_2 (9.2 um) and tt_pg_3v3_2 (13.8 um), full-height cells
  on the tile's WEST side (vdd gate outermost). Their outputs (GPWR / GAPWR, met4 columns) feed
  met5 stripes drawn from the gate across the tile to our pins (ModulePowerStrapper, two gates):
    gate 0: narrow (8.75) at mid + 5.5,  wide (19.75) at mid - 57.12
    gate 1: narrow (8.75) at mid - 5.5,  wide (19.75) at mid + 57.12
  Which supply is gate 0 (pin order) and whether the tile is placed N or FS (mirrored in y) aren't
  known; both give one of the two cases in CASES. The vgnd positions are the same either way.
- Gate on-resistance (sim/power/pg_rdson.spice, tt, 20 mA, 10-50 C): 1v8 hp 0.76-0.78 ohm,
  ll 0.89-0.91 ohm; 3v3 1.93-2.17 ohm.
"""
H = 225.76
MID = H / 2
W, WW, GAP, PITCH = 8.75, 19.75, 2.25, 57.12
VGND_Y = [MID - 3 * 28.56, MID - 28.56, MID + 28.56, MID + 3 * 28.56]
LOW = [(MID + 5.5, W), (MID - PITCH, WW)]          # gate 0
HIGH = [(MID - 5.5, W), (MID + PITCH, WW)]         # gate 1
CASES = {'A': {'VDPWR': LOW, 'VAPWR': HIGH}, 'B': {'VDPWR': HIGH, 'VAPWR': LOW}}
TILE_W = 493.12
# the gates' output columns (met4), tile x: each gate takes its width + a 4-site margin west of
# the tile (py/tt/elements.py), 3v3 next to the tile, 1v8 west of it (tt_pg_*_2 LEFs: GAPWR at
# 8.85-13.8 of 13.8, GPWR at 5.7-9.2 of 9.2), 224.24 um tall
MARGIN = 4 * 0.46
_VAA0 = -(MARGIN + 13.8)
_VDD0 = _VAA0 - (MARGIN + 9.2)
GATE_COL = {'VAPWR': (_VAA0 + 8.85, _VAA0 + 13.8), 'VDPWR': (_VDD0 + 5.7, _VDD0 + 9.2)}
# for the extraction, widened west over the gate cells (pdn_gds.py)
GATE_COL_EXT = {'VAPWR': (_VAA0, GATE_COL['VAPWR'][1]), 'VDPWR': (_VDD0 - 15, GATE_COL['VDPWR'][1])}
R_GATE = {'VDPWR': 0.77, 'VAPWR': 2.04}           # tt 27 C
RSQ = {'m4': 0.047, 'm5': 0.0285}
R_VIA4 = 0.38                                      # per cut
ALIAS = {'VPWR': 'VDPWR'}


def stripes(net):
    """(centre y, height) of every met5 stripe that can land on a met4 column of this net, over
    both cases (the extraction gets a node at each; the deck picks the case)."""
    net = ALIAS.get(net, net)
    if net == 'VGND':
        return [(y, W) for y in VGND_Y]
    return sorted(set(LOW + HIGH))


def landings(net, yb, yt):
    """(y0, y1) of each landing on a met4 column of this net spanning yb..yt."""
    out = []
    for yc, h in stripes(net):
        y0, y1 = max(yc - h / 2, yb), min(yc + h / 2, yt)
        if y1 - y0 > 1.6:
            out.append((y0, y1))
    return out
