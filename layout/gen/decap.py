# Decap parts: the floorplan's xdeca (VAPWR, thick-oxide MOS) and xdecd (VDPWR, thin-oxide MOS)
# rectangles as blocks (xschem/gen/decap.py: MOS cap with gate on the supply, source / drain /
# body on VGND, and a MIM above it, top plate on the supply).
#
# Each part, own frame (0, 0) - (w, h):
#   MOS rows (L = 5, 2 fingers per unit, finger width fitted to the height), sharing met1 rails:
#   VGND, supply, VGND, ... from the bottom. p-tap stripes under the VGND rails. The rails are a
#   comb: VGND ones run to a met1 bus in the left edge band, supply ones to a bus in the right one.
#   MIM (where the part allows it): one met3 bottom-plate sheet (VGND) between the edge bands,
#   capm tiles on it, a met4 strip with via3 down each tile column (top plate), joined by a met4
#   bus along the top edge (the supply pin). The VGND bus climbs into the sheet (via1 / via2) in
#   the left band; the supply bus climbs to the met4 bus in the right band (met3 island >= 1.34
#   from the capm, capm.2b_a).
#   Met2 is only used in the edge bands (the via stacks): elsewhere it stays free for the top-level
#   routes that cross the decaps.
#   No capm / met4 in the columns of power straps of other nets that cross the part (keep_x).
# Pins: VGND (met1 bus; met3 sheet when there is one), supply (met1 bus; met4 bus with MIM).
# Writes layout/<cell>.gds and layout/ref/<cell>.spice (one subckt per part; the LVS source's
# decap_vapwr / decap_vdpwr are written as the sum of the parts: layout/ref/decap_vapwr.spice).
#   tools/osic-mac klayout -b -r layout/gen/decap.py
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, REPO, box, snap, L as LAY   # noqa: E402
from passives import mim, CAPM_ENC_M3, CAPM_ENC_V3      # noqa: E402
import pya                                               # noqa: E402

FP = json.load(open(os.path.join(REPO, 'layout/floorplan/floorplan.json')))
LG = 5.0                  # gate length
EDGE = 3.5                # edge bands (via stacks, comb buses)
RAIL = 0.6                # met1 rail height
UNIT_X = 12.0             # MOS unit pitch (the 2-finger L = 5 pcell is 11.64 wide)
UNIT_X1 = 6.7             # 1-finger unit (6.34 wide), for narrow parts
EDGE_MOS = 1.6            # edge bands of a MOS-only part (just the comb buses)
WF_MAX = 10.0
CAPM_MAX = 20.0
CAPM_SP = 0.84            # capm.2a
Y_BOT = 3.2               # decaps start above the full-width VDPWR bar (y 1.7-2.6)

# per part: MIM allowed below this own-frame y (None: everywhere, False: nowhere), MOS on/off
SPEC = {
    ('xdeca', 1): dict(mim_top=160.0 - Y_BOT, mos=True),    # top of part 1 MOS only (TT staircase)
    ('xdeca', 2): dict(mim_top=None, mos=True),
    ('xdeca', 3): dict(mim_top=None, mos=True),
    ('xdeca', 4): dict(mim_top=None, mos=True),
    ('xdeca', 5): dict(mim_top=None, mos=False),             # MIM only, over r2r (met1 only)
    ('xdecd', 1): dict(mim_top=False, mos=True),             # beside the west straps / TX feeds
    ('xdecd', 2): dict(mim_top=False, mos=True),
    ('xdecd', 3): dict(mim_top=None, mos=True),
}


def parts():
    out = []
    for b in FP['blocks']:
        if not b['cell'].startswith('decap_'):
            continue
        key = (b['inst'], b['part'])
        if key not in SPEC:
            continue
        y0 = max(b['y'], Y_BOT)
        out.append(dict(key=key, cell=f"{b['cell']}_p{b['part']}", x=b['x'], y=y0, w=b['w'],
                        h=b['y'] + b['h'] - y0, vt='g5' if b['inst'] == 'xdeca' else '',
                        sup='VAPWR' if b['inst'] == 'xdeca' else 'VDPWR', **SPEC[key]))
    return out


def keep_x(p):
    """Own-frame x bands of power straps crossing the part (no capm / met4 there)."""
    out = []
    for s in FP['straps']:
        x0, x1 = s['x'] - p['x'], s['x'] + s['w'] - p['x']
        if x1 > 0 and x0 < p['w']:
            out.append((x0 - 0.8, x1 + 0.8))
    return out


def spans(a, b, keeps):
    """[a, b] minus the keep bands: list of (lo, hi)."""
    out, cur = [], a
    for k0, k1 in sorted(keeps):
        if k1 <= cur or k0 >= b:
            continue
        if k0 > cur:
            out.append((cur, k0))
        cur = max(cur, k1)
    if cur < b:
        out.append((cur, b))
    return out


def licons(b, tp):
    """licon cuts (0.17, space 0.17) along a tap stripe, 0.12 tap enclosure."""
    n = int((tp.width() - 0.24 + 0.17) // 0.34)
    x0 = snap(tp.left + (tp.width() - (n * 0.34 - 0.17)) / 2)
    yc = (tp.bottom + tp.top) / 2
    for i in range(n):
        x = snap(x0 + i * 0.34)
        b.rect('licon', box(x, yc - 0.085, x + 0.17, yc + 0.085))


def make(p):
    b = Block(p['cell'])
    W, H = snap(p['w']), snap(p['h'])
    sup = p['sup']
    devs = []                                   # (W, L, nf) per MOS
    caps = []                                   # (w, l) per capm
    xa, xb = EDGE, W - EDGE                     # core between the edge bands
    gb = box(0.3, 0.3, 1.3, H - 0.3)            # VGND met1 bus (left band)
    sb = box(W - 1.3, 0.3, W - 0.3, H - 0.3)    # supply met1 bus (right band)
    rails = []
    if p['mos']:
        b.rect('m1', gb)
        b.rect('m1', sb)
        b.pin('m1', box(gb.left, gb.bottom, gb.right, gb.bottom + 1.0), 'VGND')
        b.pin('m1', box(sb.left, sb.bottom, sb.right, sb.bottom + 1.0), sup)
        # rows of pitch wf + 3.1 between shared rails (VGND, sup, VGND, ...):
        #   up row (gate top):      rail | 1.0 | diff wf | pads 1.18 | 0.3 | rail
        #   mirrored (gate bottom): rail | 0.3 | pads 1.18 | diff wf | 1.0 | rail
        n = max(1, math.ceil((H - 1.2) / (WF_MAX + 3.1)))
        wf = math.floor(((H - 1.2) / n - 3.1) * 20) / 20
        ma, mb = (xa, xb) if p['mim_top'] is not False else (EDGE_MOS, W - EDGE_MOS)
        nf, ux = (2, UNIT_X) if mb - ma >= UNIT_X else (1, UNIT_X1)
        ncol = int((mb - ma + 0.36) // ux)
        if wf >= 2.0 and ncol >= 1:
            x0 = snap(ma + ((mb - ma) - (ncol * ux - 0.36)) / 2 + 0.37)
            y = 0.3
            for r in range(n + 1):
                net = 'VGND' if r % 2 == 0 else sup
                rb = box(gb.left if net == 'VGND' else gb.right + 0.4, y,
                         sb.left - 0.4 if net == 'VGND' else sb.right, y + RAIL)
                b.rect('m1', rb)
                rails.append((net, rb))
                if net == 'VGND':                       # p-tap stripe under it (body = VGND)
                    tp = box(max(ma, rb.left + 0.1), y + 0.05, min(mb, rb.right - 0.1), y + RAIL - 0.05)
                    b.rect('tap', tp)
                    b.rect('psdm', box(tp.left - 0.13, tp.bottom - 0.13, tp.right + 0.13, tp.top + 0.13))
                    b.rect('li', tp)
                    licons(b, tp)
                    b.via('mcon', tp)
                if r == n:
                    break
                up = (r % 2 == 0)                       # VGND below: gate pads up to the sup rail
                yn = snap(y + wf + 3.1)                 # next rail
                yd = snap(y + RAIL + 1.0) if up else snap(y + RAIL + 0.3 + 1.18)
                vg_lo, vg_hi = (y + RAIL - 0.1, None) if up else (None, yn + 0.1)
                row = []
                for c in range(ncol):
                    f = Fet(b, 'n', nf * wf, LG, nf=nf, vt=p['vt'], bulk='None', gate='top' if up else 'bottom')
                    f.place(x0 + c * ux, yd)
                    f.commit()
                    row.append(f)
                    devs.append((nf * wf, LG, nf))
                    for st in f.strips:                 # S/D -> VGND rail
                        if up:
                            b.rect('m1', box(st.left, y + RAIL - 0.1, st.right, st.top))
                        else:
                            b.rect('m1', box(st.left, st.bottom, st.right, yn + 0.1))
                    for k, pd in enumerate(f.pads):     # gate pads -> sup rail
                        jx = pd.left + 0.1 if k == 0 else pd.right - 0.4
                        if up:
                            b.rect('m1', box(jx, pd.bottom, jx + 0.3, yn + 0.1))
                        else:
                            b.rect('m1', box(jx, y + RAIL - 0.1, jx + 0.3, pd.top))
                if p['vt'] == 'g5':                     # one hvi over the row (no gaps between units)
                    b.rect('hvi', box(row[0].bbox.left, min(f.bbox.bottom for f in row),
                                      row[-1].bbox.right, max(f.bbox.top for f in row)))
                y = yn
    # MIM
    if p['mim_top'] is not False:
        # met4 top-plate bus along the top of the MIM region (the part's top edge, or mim_top)
        ytop = snap(min(H - 2.2, p['mim_top'] + 0.6)) if p['mim_top'] else H - 2.2
        y1 = ytop - 0.6
        e = CAPM_ENC_M3
        sheet_x = (xa - 0.2, xb + 0.2)
        cols = []
        # only the strap-free span that reaches the right band: its met4 bus meets the supply
        # stack there (a bus across a strap of another net would short them)
        sp_all = spans(xa + 0.4, xb - 1.6, keep_x(p))
        bus_lo = sp_all[-1][0] if sp_all else xa
        for lo, hi in sp_all[-1:]:
            span = hi - lo
            if span < 4:
                continue
            nc = max(1, math.ceil((span + CAPM_SP) / (CAPM_MAX + CAPM_SP)))
            cw = math.floor((span - (nc - 1) * CAPM_SP) / nc * 100) / 100
            for k in range(nc):
                cols.append((snap(lo + k * (cw + CAPM_SP)), cw))
        yl, yh = 1.4, y1                         # (bottom plates >= 1.2 from the VDPWR bar below)
        nr = max(1, math.ceil((yh - yl + CAPM_SP) / (CAPM_MAX + CAPM_SP)))
        ch = math.floor(((yh - yl) - (nr - 1) * CAPM_SP) / nr * 100) / 100
        if cols and ch >= 4:
            # bottom plate: one sheet per group of capm columns between strap keep-outs
            groups = []
            for cx, cw in cols:
                if groups and cx - groups[-1][1] <= CAPM_SP + 0.01:
                    groups[-1][1] = cx + cw
                else:
                    groups.append([cx, cx + cw])
            # one sheet across the strap keep-outs too (met3 under a met4 strap is fine): every
            # bottom plate on one VGND polygon
            sheet = box(groups[0][0] - e, yl - e, groups[-1][1] + e, yl + nr * ch + (nr - 1) * CAPM_SP + e)
            b.rect('m3', sheet)
            b.rect('m4', box(bus_lo, ytop, xb, ytop + 1.4))                   # top-plate bus
            b.pin('m4', box(xb - 1.0, ytop, xb, ytop + 1.4), sup)
            for cx, cw in cols:
                st = box(cx + cw / 2 - 0.7, yl, cx + cw / 2 + 0.7, ytop + 0.1)
                b.rect('m4', st)
                for r in range(nr):
                    cy = snap(yl + r * (ch + CAPM_SP))
                    capm = box(cx, cy, cx + cw, cy + ch)
                    mim(b, capm, strip=st)
                    caps.append((snap(cw), snap(ch)))
            sh = box(sheet.left, sheet.bottom, sheet.left + 1.0, sheet.bottom + 1.0)
            b.pin('m3', sh, 'VGND')
            if p['mos']:
                # VGND bus -> sheet: via1 / via2 at the bus bottom into a met3 tab of the sheet
                vb = box(gb.left, 0.6, gb.right, 1.6)
                b.stack(vb, 'm1', 'm3')
                b.rect('m3', box(vb.left, vb.bottom, sheet.left + 0.5, vb.top))
                # supply bus -> top-plate bus: a stack in the right band, island >= 1.34 from capm
                vs = box(sb.left, ytop, sb.right, ytop + 1.4)
                b.stack(vs, 'm1', 'm4')
                b.rect('m4', box(xb - 0.1, ytop, vs.right, ytop + 1.4))
    print(f"{p['cell']}: {W} x {H}, {len(devs)} MOS ({sum(d[0] for d in devs) * LG:.0f} um2 gate), "
          f"{len(caps)} MIM ({sum(c[0] * c[1] for c in caps):.0f} um2)")
    return b, devs, caps


def write_ref(cell, sup, vt, devs, caps):
    mos = 'sky130_fd_pr__nfet_g5v0d10v5' if vt == 'g5' else 'sky130_fd_pr__nfet_01v8'
    lines = [f'* {cell}: layout/gen/decap.py', f'.subckt {cell} {sup} VGND']
    for i, (w, l, nf) in enumerate(devs):
        lines.append(f'XM{i} VGND {sup} VGND VGND {mos} L={l:g} W={w:g} nf={nf}')
    for i, (w, l) in enumerate(caps):
        lines.append(f'XC{i} {sup} VGND sky130_fd_pr__cap_mim_m3_1 W={w:g} L={l:g} m=1')
    lines.append('.ends')
    return lines


def main():
    os.makedirs(os.path.join(REPO, 'layout', 'ref'), exist_ok=True)
    total = {'VAPWR': [], 'VDPWR': []}
    for p in parts():
        b, devs, caps = make(p)
        b.write(os.path.join(REPO, 'layout', p['cell'] + '.gds'))
        ref = write_ref(p['cell'], p['sup'], p['vt'], devs, caps)
        open(os.path.join(REPO, 'layout', 'ref', p['cell'] + '.spice'), 'w').write('\n'.join(ref) + '\n')
        total[p['sup']].append((p, devs, caps))
    # the schematic's decap_vapwr / decap_vdpwr as the sum of the parts (LVS source)
    for sup, name in (('VAPWR', 'decap_vapwr'), ('VDPWR', 'decap_vdpwr')):
        devs = [d for _, dd, _ in total[sup] for d in dd]
        caps = [c for _, _, cc in total[sup] for c in cc]
        vt = 'g5' if sup == 'VAPWR' else ''
        ref = write_ref(name, sup, vt, devs, caps)
        open(os.path.join(REPO, 'layout', 'ref', name + '.spice'), 'w').write('\n'.join(ref) + '\n')
        gate = sum(d[0] for d in devs) * LG
        area = sum(c[0] * c[1] for c in caps)
        print(f'{name}: {len(devs)} MOS ({gate:.0f} um2 gate), {len(caps)} MIM ({area:.0f} um2 = {area * 2.06e-3:.1f} pF)')


main()
