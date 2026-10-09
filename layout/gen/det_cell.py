# det_cell layout: one tap's full-wave rectifier (xschem/gen/logdet.py:det_cell), defaults
# wd=1 rs=10k cc=100f rb=200k. Per side (p: inp/gp/sp, n: inn/gn/sn):
#   Cc  cap_mim_m3_1 ~6.97 x 6.97 um: bottom plate (met3) = in, top plate = g
#   Rb  res_xhigh_po_0p35 L 27.1 um: vb -> g          (4 segments of 6.78 um)
#   M   nfet_01v8 W wd L 0.15: D out, G g, S s
#   Rs  res_high_po_0p35 L 9.08 um: s -> VSS          (2 segments of 4.54 um: see below)
# Floorplan: p half on the left, n half mirrored on the right; one p-tap ring (VSS) round
# everything. Bottom up: VSS rail (met1+2+3); a channel with the out and vb buses (met2,
# full width, pins on both edges so cells abut in log_det); the resistor arrays (all
# terminals at their bottom heads) with the two NMOS in the middle; the MIMs packed over
# the resistors (met3 density is high there, by choice). Each top plate is contacted by a
# met4 strip that drops to met3 in the gap between the MIMs (1.2 um from each bottom
# plate), down to its gate, and across (met3, below the plates) to its Rb end.
# Rs is 2 segments, so the layout carries one more ~963 Ohm end term than the schematic
# (the high-poly model has it per device; the schematic sizes L = (rs - 963) / 995): ~10.96k
# instead of 10k, ~-10 % rectified current (inside the poly's +-15 % process spread; agreed
# 2026-10-09). A lone segment would be exact but fails magic rpm.1 (a single 0.35 um
# resistor's generated RPM region is too narrow; two side by side merge and pass).
# Currents are uA: minimum widths.
# Run: tools/osic klayout -b -r layout/gen/det_cell.py
import math
import os
import re
import subprocess
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, REPO, box, ring, snap   # noqa: E402
from passives import PolyRes, mim, CAPM_ENC_M3, BOT_PLATE_SPACE   # noqa: E402

PARAMS = dict(wd=1, rs=10e3, cc=100e-15, rb=200e3)
CAPW = snap(math.sqrt(PARAMS['cc'] / 2.06e-15))        # as the schematic: W = L = sqrt(cc / 2.06f)
LRB = PARAMS['rb'] / 7379                               # as the schematic's L expressions
LRS = (PARAMS['rs'] - 963) / 995
RAIL_H = 1.2
GRW = 0.4
M3W = 0.5                                               # gate drop / gate route (met3) width


def make():
    b = Block('det_cell')
    e = CAPM_ENC_M3
    plate = CAPW + 2 * e
    gap = 2 * (BOT_PLATE_SPACE + M3W) + 0.3             # two drops between the plates
    W = 2 * plate + gap + 2 * 1.2                       # margin each side (ring outside the plates)
    cx = W / 2

    # bottom: rail, ring bottom, buses
    y_in = RAIL_H + GRW                                  # ring hole bottom
    bus = {'out': (y_in + 0.3, y_in + 0.7), 'vb': (y_in + 1.0, y_in + 1.4)}
    y_dev = bus['vb'][1] + 0.6                           # resistor bbox bottom / FET diff bottom

    halves = {}
    for side, sgn in (('p', -1), ('n', 1)):
        rb = PolyRes(b, LRB, 4, typ='sky130_fd_pr__res_xhigh_po_0p35')
        rs = PolyRes(b, LRS, 2, typ='sky130_fd_pr__res_high_po_0p35')
        wrb = 3 * rb.pitch + rb._bbox.width()
        wrs = rs.pitch + rs._bbox.width()
        sp_ = 0.9                                         # Rb (urpm) to Rs (rpm) array gap (magic rpm.2: 0.84 across urpm/rpm)
        # x of the arrays' bbox: Rb outer, Rs inner, under the plate
        inner_edge = cx + sgn * (gap / 2)                 # plate edge on the gap side
        rs_in = 0.2 - (sp_ - 0.6)                         # Rs moves in toward the FETs, Rb stays put
        if sgn < 0:
            xrs = inner_edge - rs_in - wrs
            xrb = xrs - sp_ - wrb
        else:
            xrs = inner_edge + rs_in
            xrb = xrs + wrs + sp_
        yb = y_dev - rb._bbox.bottom + rb._poly.bottom
        rb.place(xrb - (rb._bbox.left - rb._poly.left), yb)
        rs.place(xrs - (rs._bbox.left - rs._poly.left), y_dev - rs._bbox.bottom + rs._poly.bottom)
        # NMOS in the middle, source strip on the outer side
        f = Fet(b, 'n', PARAMS['wd'], 0.15, gate='top', vt='', bulk='None')
        fx = cx + sgn * 0.35 - (f.diff.width() if sgn < 0 else 0)
        f.place(fx, y_dev + 0.2).commit()
        halves[side] = (sgn, rb, rs, f)

    top = max(max(h[1].bbox.top, h[2].bbox.top) for h in halves.values())
    inner = box(min(h[1].bbox.left for h in halves.values()) - 0.6, y_in,
                max(h[1].bbox.right for h in halves.values()) + 0.6, top + 0.6)
    ring(b, inner, 'p', GRW)
    W = max(W, inner.right + GRW + 0.1)
    b.stack(box(0, 0, W, RAIL_H), 'm1', 'm3')
    b.rect('m1', box(inner.left - GRW, RAIL_H - 0.01, inner.right + GRW, y_in))   # ring onto the rail
    for net, (y0, y1) in bus.items():
        b.rect('m2', box(0, y0, W, y1))
        b.pin('m2', box(0, y0, 0.5, y1), net)
        b.pin('m2', box(W - 0.5, y0, W, y1), net)
    b.pin('m1', box(0, 0, 1.0, RAIL_H), 'VSS')

    y_cap_top = top                                       # plates top-aligned with the resistors
    for side, (sgn, rb, rs, f) in halves.items():
        g, s_, inn = f'g{side}', f's{side}', f'in{side}'
        # resistor ends (bottom heads): Rb outer = vb, inner = g; Rs inner = s, outer = VSS
        rb0, rb1 = rb.ends                               # left, right
        rs0, rs1 = rs.ends
        rb_vb, rb_g = (rb0, rb1) if sgn < 0 else (rb1, rb0)
        rs_s, rs_vss = (rs1, rs0) if sgn < 0 else (rs0, rs1)
        # vb: head down to the vb bus
        b.rect('m1', box(rb_vb.left, bus['vb'][0], rb_vb.right, rb_vb.top))
        b.via('via1', box(rb_vb.left, bus['vb'][0], rb_vb.right, bus['vb'][1]), enc=(0.055, 0.085))
        # VSS: Rs outer head down to the ring bottom (crossing the buses in met1)
        b.rect('m1', box(rs_vss.left, y_in - 0.01, rs_vss.right, rs_vss.top))
        # source: S strip (outer) to the Rs inner head, met1 at the head's height
        ss, sd = (f.strips[0], f.strips[1]) if sgn < 0 else (f.strips[1], f.strips[0])
        yl0, yl1 = max(ss.bottom, rs_s.bottom), min(ss.top, rs_s.top)
        assert yl1 - yl0 >= 0.3, (side, ss, rs_s)
        b.rect('m1', box(min(ss.left, rs_s.left), yl0, max(ss.right, rs_s.right), yl1))
        b.label('m1', box(min(ss.left, rs_s.left), yl0, max(ss.right, rs_s.right), yl1), s_)
        # drain: D strip down to the out bus
        dw = 0.29
        dx = sd.center().x
        b.rect('m1', box(dx - dw / 2, bus['out'][0], dx + dw / 2, sd.top))
        b.via('via1', box(dx - dw / 2, bus['out'][0], dx + dw / 2, bus['out'][1]), enc=(0.07, 0.085))
        # gate drop column (met3) in the gap, 1.2 um from the bottom plate
        plate_in = cx + sgn * gap / 2
        xd0 = plate_in - sgn * BOT_PLATE_SPACE
        xd = box(xd0, 0, xd0 - sgn * M3W, 1)
        gx0, gx1 = xd.left, xd.right
        pad = f.pads[0]
        yg0 = pad.bottom
        yg1 = max(pad.top, yg0 + 0.6)
        # gate: met1 from the pad to under the drop, via1 + via2 up to the drop column
        b.rect('m1', box(min(pad.left, gx0), yg0, max(pad.right, gx1), yg1))
        b.rect('m2', box(gx0, yg0, gx1, yg1))
        b.via('via1', box(gx0, yg0, gx1, yg1), enc=(0.085, 0.085))
        b.via('via2', box(gx0, yg0, gx1, yg1), enc=(0.085, 0.085))
        # Rb's g end: via1 + via2 on the head, met3 across (below the plates) to the drop
        hb0 = rb_g.top - 0.6
        b.rect('m2', box(rb_g.left - 0.05, hb0, rb_g.right + 0.05, rb_g.top))
        b.via('via1', box(rb_g.left, hb0, rb_g.right, rb_g.top), enc=(0.055, 0.085))
        hv = box(rb_g.left - 0.05, hb0, rb_g.right + 0.05, rb_g.top)
        b.via('via2', hv, enc=(0.06, 0.085))
        b.rect('m3', box(min(hv.left, gx0), hb0, max(hv.right, gx1), rb_g.top))
        b.label('m3', box(min(hv.left, gx0), hb0, max(hv.right, gx1), rb_g.top), g)
        # MIM: plate top-aligned with the arrays, gap-side edge at plate_in
        if sgn < 0:
            cap = box(plate_in - e - CAPW, y_cap_top - e - CAPW, plate_in - e, y_cap_top - e)
        else:
            cap = box(plate_in + e, y_cap_top - e - CAPW, plate_in + e + CAPW, y_cap_top - e)
        strip = box(cap.left if sgn < 0 else min(gx0, gx1), cap.top - 1.2,
                    max(gx0, gx1) if sgn < 0 else cap.right, cap.top - 0.14)
        bot = mim(b, cap, strip)
        b.rect('m4', strip)
        # drop column from the gate up to the strip; via3 at its top
        b.rect('m3', box(gx0, yg0, gx1, strip.top))
        b.via('via3', box(gx0, strip.bottom, gx1, strip.top))
        assert bot.bottom - max(rb_g.top, yg1) >= BOT_PLATE_SPACE - 1e-6, (side, bot, rb_g.top, yg1)
        b.pin('m3', box(bot.left, bot.bottom, bot.left + 1.0, bot.bottom + 1.0), inn)
    print(f'det_cell: {W:.2f} x {inner.top + GRW:.2f} um; cap {CAPW} um, Rb 4 x {LRB / 4:.3f}, '
          f'Rs 2 x {LRS / 2:.3f}')
    return b


def write_ref():
    """LVS/PEX reference: the xschem netlist with wd / rs / cc / rb evaluated."""
    tmp = os.path.join(REPO, 'build', 'lay', 'ref')
    os.makedirs(tmp, exist_ok=True)
    subprocess.run(['xschem', '-n', '-s', '-q', '--tcl', 'set top_subckt 1; set lvs_netlist 1', '-o', tmp,
                    'xschem/det_cell.sch'], cwd=REPO, capture_output=True)
    src = open(os.path.join(tmp, 'det_cell.spice')).read()
    env = dict(PARAMS, sqrt=math.sqrt, max=max)
    out = []
    for ln in src.splitlines():
        if ln.startswith('.subckt det_cell'):
            ln = re.sub(r'\s+\w+=\S+', '', ln)
        ln = re.sub(r"(\w+)='([^']+)'",
                    lambda m: f'{m.group(1)}={eval(m.group(2), {}, env):.6g}', ln)
        out.append(ln)
    os.makedirs(os.path.join(REPO, 'layout', 'ref'), exist_ok=True)
    with open(os.path.join(REPO, 'layout', 'ref', 'det_cell.spice'), 'w') as fh:
        fh.write(f'* det_cell: xschem/det_cell.sch with {PARAMS} (layout/gen/det_cell.py)\n' + '\n'.join(out) + '\n')


if __name__ == '__main__':
    make().write(os.path.join(REPO, 'layout', 'det_cell.gds'))
    write_ref()
