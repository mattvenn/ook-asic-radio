# lpf_rc layout: post-detection RC low-pass (xschem/gen/lpf.py:lpf_rc), lr=400 nc=2:
#   R1 res_xhigh_po_0p35 L 400 um (~2.95 MOhm) in -> out; C1 2 x 30x30 um cap_mim_m3_1 out -> VSS.
# Floorplan (bottom to top): VSS rail (met1+2+3); the resistor (16 x 25 um segments, a
# serpentine) in a p-tap guard ring on VSS; the two MIM caps on one met3 bottom plate (VSS)
# over the resistor (the plate also shields it). The plate joins the rail's met3.
# The top plates (out) are contacted by one met4 strip that drops to met3/met2 on the right.
# in on the left edge (met2), out on the right edge (met3).
# Currents are nA: minimum widths everywhere, 2 cuts per layer change for robustness.
# Run: tools/osic klayout -b -r layout/gen/lpf_rc.py
import os
import re
import subprocess
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, REPO, box, ring          # noqa: E402
from passives import (PolyRes, mim, CAPM_ENC_M3, BOT_PLATE_SPACE)   # noqa: E402

PARAMS = dict(lr=400, nc=2)
CAP = 30.0          # MIM unit (W = L), as the schematic
NSEG = 16           # resistor segments (25 um each)
RAIL_H = 2.0


def make():
    b = Block('lpf_rc')
    assert PARAMS['nc'] == 2
    e = CAPM_ENC_M3
    # MIM caps: each bottom plate starts at the rail top, so it abuts the rail's met3 (VSS)
    # capm to capm: each cap has its own bottom plate; plates 1.2 apart (capm.2b) and no
    # met3 within 1.34 of the other capm (magic capm.11)
    gap = 2.0
    y0 = RAIL_H
    caps = [box(e + k * (CAP + gap), y0 + e, e + k * (CAP + gap) + CAP, y0 + e + CAP) for k in range(2)]
    plate_r = caps[-1].right + e
    # top-plate contact: one met4 strip along the caps' top edge, on to the drop point
    drop_x = plate_r + BOT_PLATE_SPACE            # out's met3 pad starts here
    W = drop_x + 1.6                              # block width
    strip = box(caps[0].left, caps[0].top - 1.6, W - 0.2, caps[0].top - 0.2)
    for c in caps:
        mim(b, c, strip)
    b.rect('m4', strip)

    # resistor under the caps, in a p-tap ring
    r = PolyRes(b, PARAMS['lr'], NSEG)
    rw = (NSEG - 1) * r.pitch + r._bbox.width()
    rx = (plate_r - rw) / 2 - (r._bbox.left - r._poly.left)       # centre the array under the plate
    grw = 0.4
    m = 0.6                                        # rpm marker to ring (spacing)
    inner_y0 = y0 + grw
    seg_y = inner_y0 + m + (r._poly.bottom - r._bbox.bottom) + 1.3    # room for the in/out met2 row
    r.place(rx, seg_y)
    inner = box(r.bbox.left - m, inner_y0, r.bbox.right + m, r.bbox.top + m)
    ring(b, inner, 'p', grw)
    # ring bottom (met1) onto the rail: VSS
    b.rect('m1', box(inner.left - grw, y0 - 0.01, inner.right + grw, inner_y0))

    # VSS rail (met1+2+3), full width
    b.stack(box(0, 0, W, RAIL_H), 'm1', 'm3')

    # in / out: via1 on the end heads, met2 to the edges, both on one row inside the ring
    hin, hout = r.ends
    yr0 = inner_y0 + 0.3
    yr1 = yr0 + 0.6
    for h in (hin, hout):
        b.rect('m1', box(h.left, yr0, h.right, h.top))
    vin = box(hin.left, yr0, hin.right, yr1)
    vout = box(hout.left, yr0, hout.right, yr1)
    b.via('via1', vin, enc=(0.055, 0.085))
    b.via('via1', vout, enc=(0.055, 0.085))
    b.rect('m2', box(0, yr0, hin.right, yr1))
    # out: met2 to the drop column, up through via2 to the met3 pad, via3 to the strip
    pad = box(drop_x, yr0, W, strip.top)
    b.rect('m2', box(hout.left, yr0, W, yr1))
    b.via('via2', box(drop_x, yr0, W, yr1), enc=(0.085, 0.065))
    b.rect('m3', pad)
    b.via('via3', box(drop_x, strip.bottom, W - 0.2, strip.top))
    b.pin('m2', box(0, yr0, 0.5, yr1), 'in')
    b.pin('m3', box(W - 0.5, yr0, W, yr0 + 2.0), 'out')
    b.pin('m1', box(0, 0, 1.0, RAIL_H), 'VSS')
    for k, ln in enumerate(r.links, 1):
        b.label('m1', ln, f'r{k}')
    print(f'lpf_rc: {NSEG} x {r.lseg} um segments, pitch {r.pitch}, ring {inner}, block {W:.2f} x '
          f'{max(strip.top, inner.top + grw) :.2f} um')
    return b


def write_ref():
    """LVS/PEX reference: the xschem netlist with lr / nc substituted (netgen can't
    evaluate L='lr')."""
    tmp = os.path.join(REPO, 'build', 'lay', 'ref')
    os.makedirs(tmp, exist_ok=True)
    subprocess.run(['xschem', '-n', '-s', '-q', '--tcl', 'set top_subckt 1; set lvs_netlist 1', '-o', tmp,
                    'xschem/lpf_rc.sch'], cwd=REPO, capture_output=True)
    src = open(os.path.join(tmp, 'lpf_rc.spice')).read()
    src = re.sub(r"'(\w+)'", lambda mm: str(PARAMS[mm.group(1)]) if mm.group(1) in PARAMS else mm.group(0), src)
    os.makedirs(os.path.join(REPO, 'layout', 'ref'), exist_ok=True)
    with open(os.path.join(REPO, 'layout', 'ref', 'lpf_rc.spice'), 'w') as fh:
        fh.write(f'* lpf_rc: xschem/lpf_rc.sch with {PARAMS} (layout/gen/lpf_rc.py)\n' + src)


if __name__ == '__main__':
    make().write(os.path.join(REPO, 'layout', 'lpf_rc.gds'))
    write_ref()
