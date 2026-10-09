# ctrim_1p layout: Ctrim, the 1 pF shunt cap on the trim node (xschem/gen/top.py: Ctrim c0 =
# trim, c1 = VGND; it strips the clock-edge spikes the r2r's 10.6k output would pass to
# comp_ct.trim). One cap_mim_m3_1, 22.035 x 22.035 um (sqrt(1p / 2.06 fF/um2)).
#   bottom plate (met3, capm + 0.2): VGND, pins on the W and N edges;
#   top plate: an L of met4 strips with via3 over the capm, the trim pins at their ends: on the S edge near
#   the W corner (placed MX at the top level, that edge faces north, up to comp_ct.trim) and
#   on the E edge at mid-height (toward r2r out). Floorplan matt layout 5, pins.md.
# Also writes layout/ref/ctrim_1p.spice (LVS / PEX reference).
# Run: tools/osic klayout -b -r layout/gen/ctrim_1p.py
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, REPO, box, snap               # noqa: E402
from passives import mim, CAPM_ENC_M3                 # noqa: E402

C = 1e-12
W = snap(math.sqrt(C / 2.06e-15))                     # capm side, as the schematic's W = L


def make():
    b = Block('ctrim_1p')
    e = CAPM_ENC_M3
    capm = box(e, e, e + W, e + W)
    S = capm.right + e                                # block side (the bottom plate)
    ys = snap(S / 2)
    # top plate contact: an L of met4 strips (as the other MIMs: low met4 density), via3
    # where they cross the capm; the strips run on to the trim pins
    sv = box(0.75, 0, 2.15, capm.top - 0.2)                      # up the W side, from the S edge
    sh = box(0.75, ys - 0.7, S, ys + 0.7)                         # across at mid-height, to the E edge
    for st in (sv, sh):
        b.rect('m4', st)
    mim(b, capm)
    b.via('via3', box(sv.left, capm.bottom + 0.2, sv.right, sh.bottom - 0.3))
    b.via('via3', box(sv.left, sh.top + 0.3, sv.right, capm.top - 0.2))
    b.via('via3', box(sh.left, sh.bottom, capm.right - 0.2, sh.top))
    b.pin('m4', box(0.75, 0, 1.25, 0.5), 'trim')
    b.pin('m4', box(S - 0.5, ys - 0.25, S, ys + 0.25), 'trim')
    # VGND: the bottom plate, pins on the W and N edges
    b.pin('m3', box(0, ys - 0.25, 0.5, ys + 0.25), 'VGND')
    b.pin('m3', box(ys - 0.25, S - 0.5, ys + 0.25, S), 'VGND')
    print(f'ctrim_1p: capm {W} x {W} um ({W * W * 2.06e-3:.3f} pF), block {S:.3f} x {S:.3f} um')
    return b


def write_ref():
    os.makedirs(os.path.join(REPO, 'layout', 'ref'), exist_ok=True)
    with open(os.path.join(REPO, 'layout', 'ref', 'ctrim_1p.spice'), 'w') as fh:
        fh.write(f'* ctrim_1p: Ctrim of xschem/radio_analog.sch (xschem/gen/top.py), layout/gen/ctrim_1p.py\n'
                 f'.subckt ctrim_1p trim VGND\n'
                 f'XC1 trim VGND sky130_fd_pr__cap_mim_m3_1 W={W:g} L={W:g} m=1\n'
                 f'.ends\n')


if __name__ == '__main__':
    make().write(os.path.join(REPO, 'layout', 'ctrim_1p.gds'))
    write_ref()
