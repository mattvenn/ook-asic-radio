"""Top-level nets for layout/gen/route.py, in routing order. Connectivity from
xschem/gen/top.py (radio_analog + tt_um_mattvenn_radio); routing intent from
docs/handoff_toplevel.md "Nets and routing intent".

A terminal is a list of tags (any one of them may be hit): 'inst.pin' for a block pin,
the bare name for a tile pin, 'NET@w|m|e' for a power strap (west / mid / east set).
Coordinates in tile um.
"""

STRAPS = {n: [f'{n}@{s}' for s in ('w', 'm', 'e', 'bar')] for n in ('VDPWR', 'VGND', 'VAPWR')}
# "RX in the corner" (layout/floorplan/floorplan.json, 2026-11-14): rx_t (the tall chain with its
# one-row detector, the taps wired inside it) at the bottom, input section at its west end over
# ua[3] / ua[2]; the TX drivers west of it over ua[4] / ua[5]; dbg on ua[1] (under the chain).
CHAIN = (74.84, 7.4, 198.37, 70.0)           # lna_chain_t inside rx_t (from just above its south-edge pins)
RX = (67.14, 6.5, 204.19, 93.01)             # all of rx_t (the detector on top, x 67.14-204.19)
ANALOG = ['det', 'lpf', 'avg', 'xcomp.inp', 'xcomp.inn', 'xavg.in', 'xavg.out', 'xlpf.out', 'xlpf.in',
          'xrx.det', 'xcdet.det', 'trim', 'xcomp.trim', 'xctrim.trim', 'xdac.out']
TRIM = ['trim', 'xcomp.trim', 'xctrim.trim', 'xdac.out']
# RX supply trunks, in routing order: (name, block supply pin, strap set). The blocks east of
# x ~130 from the mid straps, the west ones (detector end, lpf, dbg, avg) from the west straps.
TRUNK_VGND = [('comp', 'xcomp.VSS', 'm'), ('bias', 'xbias.VSS', 'm'), ('ctrim', 'xctrim.VGND', 'm'),
              ('dac', 'xdac.VGND', 'm'), ('avg', 'xavg.VSS', 'w'), ('det', 'xrx.VSS_det', 'w'),
              ('lpf', 'xlpf.VSS', 'w'), ('dbg', 'xdbg.VSS', 'w')]
TRUNK_VDPWR = [('comp', 'xcomp.VDD', 'm'), ('bias', 'xbias.VDD', 'm'), ('avg', 'xavg.VDD', 'w'),
               ('det', 'xrx.VDDD', 'w'), ('dbg', 'xdbg.VDD', 'w')]


def N(name, *terms, **kw):
    terms = [t if isinstance(t, list) else [t] for t in terms]
    own = set(kw.pop('own', [])) | {t for tt in terms for t in tt}
    return dict(name=name, terms=terms, own=sorted(own), label=kw.pop('label', None), **kw)


def blk(x0, y0, x1, y1, layers=None):
    return (x0, y0, x1, y1, layers, 'block')


def nets():
    out = tt_bus()          # fixed geometry first: every routed net then keeps clear of it
    out.append(tx_feed())
    out.append(tx_gnd_feed())
    out.append(vgnd_landing())
    nochain = [blk(*CHAIN)]
    # ---------------- RX analog path ----------------
    # antenna inputs: straight up from the pads to the chain's south-edge pins, nothing else near
    out.append(N('rx_p', 'ua[3]', 'xrx.inp', w=2.0, layers=['m3', 'm4']))
    out.append(N('rx_n', 'ua[2]', 'xrx.inn', w=2.0, layers=['m3', 'm4']))
    # (the taps o1..o5 / out are wired inside rx_t)
    # det: slow, high impedance; short: the detector's west end -> lpf, dbg_tg, Cdet
    out.append(N('det', 'xrx.det', 'xlpf.in', 'xdbg.a', 'xcdet.det', zones=nochain, margin=10, label='det'))
    out.append(N('lpf', 'xlpf.out', 'xcomp.inn', 'xavg.in', label='lpf'))
    out.append(N('avg', 'xavg.out', 'xcomp.inp', label='avg'))
    # trim: r2r out -> Ctrim (either trim pin) -> comp trim; met2 straight over r2r
    out.append(N('trim', 'xdac.out', 'xctrim.trim', 'xcomp.trim', layers=['m1', 'm2', 'm3', 'm4'],
                 layer_cost={'m1': 4, 'm2': 1, 'm3': 2, 'm4': 2}, label='trim'))
    # trim_out[i] -> r2r b_i: straight horizontals across xdeca part 6 and the straps
    for i in range(8):
        out.append(N(f'trim[{i}]', f'macro.trim_out[{i}]', f'xdac.b{i}', layers=['m1', 'm2', 'm3'],
                     margin=6, label=f'trim[{i}]'))
    # comp out -> macro (after the trim bits): east over r2r on met2 (under its MIM decap) between
    # b4 and b3, down the x 233-236 gap west of xdeca part 6 on met3 (across the trim bits' met2),
    # east under them over the decap, far from the detector's top edge and the trim node; a met4
    # jumper just west of the mid straps (antenna: the macro input sees only the last met3)
    out.append(N('comp', 'xcomp.out', 'macro.comp_in', via=[(177.6, 127.9), (234.6, 127.9, 'm3'), (234.6, 90.6, 'm3'),
                                                            (274.4, 89.4, 'm4'), (275.4, 89.4, 'm4')],
                 zones=[blk(60, 0, 206, 95.3)], avoid=[(TRIM, 3.0, 30)], margin=10, label='comp'))
    # bias: ib_det / ib_comp up out of bias_gen's north-west corner; ib_chain / vcm down its west
    # face and west under the chain to its south-edge pins
    out.append(N('ib_det', 'xbias.ib_det', 'xrx.ibias_det', zones=nochain, margin=8, label='ib_det'))
    out.append(N('ib_comp', 'xbias.ib_comp', 'xcomp.ibias', zones=[blk(*RX)], margin=8, label='ib_comp'))   # (not over the detector)
    out.append(N('ib_chain', 'xbias.ib_chain', 'xrx.ibias', zones=nochain, margin=6, label='ib_chain'))
    out.append(N('vcm', 'xbias.vcm', 'xrx.vcm', zones=nochain, margin=6, label='vcm'))

    # ---------------- TX ----------------
    # (TX-internal wires and the TX supply wiring go into the tx_top cell: LVS against tx_top.sch)
    tx_vss = ['VGND_TXF', 'xtx.xring.VSS', 'xtx.xls.VSS', 'xtx.xlse_p.VSS', 'xtx.xlse_n.VSS']
    out.append(N('VAPWR_TX', 'VAPWR@w', 'VAPWR_TXF', 'xtx.xls.VAPWR',
                 'xtx.xlse_n.VAPWR', 'xtx.xlse_p.VAPWR', w_try=[2.0, 1.5, 1.0], layers=['m3', 'm4'], margin=8, wide=True,
                 cell='tx_top', late=['VAPWR@w']))
    out.append(N('VGND_TX', 'VGND@w', *tx_vss, w_try=[2.0, 1.5, 1.0], layers=['m3', 'm4'], margin=8, wide=True,
                 cell='tx_top', late=['VGND@w']))
    out.append(N('VDPWR_TX', 'VDPWR@w', 'xtx.xring.VDD', 'xtx.xls.VDD', 'xtx.xlse_p.VDD',
                 'xtx.xlse_n.VDD', w_try=[2.0, 1.5, 1.0, 0.8], layers=['m2', 'm3', 'm4'], margin=8, wide=True,
                 cell='tx_top', late=['VDPWR@w']))
    out.append(N('ring', 'xtx.xring.out', 'xtx.xls.in', margin=8, label='ring', cell='tx_top'))
    out.append(N('tx_a', 'xtx.xls.A', 'xtx.xdrv_p.in', margin=6, label='a', cell='tx_top'))
    out.append(N('tx_b', 'xtx.xls.B', 'xtx.xdrv_n.in', margin=6, label='b', cell='tx_top'))
    out.append(N('enh_p', 'xtx.xlse_p.A', 'xtx.xdrv_p.en', margin=6, label='enh_p', cell='tx_top'))
    out.append(N('enh_n', 'xtx.xlse_n.A', 'xtx.xdrv_n.en', margin=6, label='enh_n', cell='tx_top'))
    # TX outputs: straight down from the drivers' outputs (their south edge) to the pads, met4
    # over the full-width met3 bars. (EM: 9.8 mA RMS.)
    out.append(N('tx_n', 'xtx.xdrv_n.out', 'ua[5]', w=4.0, layers=['m3', 'm4'], margin=6))
    out.append(N('tx_p', 'xtx.xdrv_p.out', 'ua[4]', w=4.0, layers=['m3', 'm4'], margin=6))

    # ---------------- digital interface ----------------
    # avg_sc clocks: macro -> west over xdeca part 6 (met2 over its MIM), up the x 232.4-236 gap,
    # west over the top of comp_ct and down over xdecd part 4 onto avg_sc's north edge
    phi_z = [blk(0, 0, 232.6, 161.0), blk(132.6, 161.0, 232.6, 166.0), nochain[0]]
    out.append(N('sc_phi1', 'xavg.phi1', 'macro.sc_phi1', zones=phi_z, via=[(233.4, 165.0), (233.4, 197.5)],
                 avoid=[(ANALOG, 20.0, 8)], margin=12, label='sc_phi1'))
    out.append(N('sc_phi2', 'xavg.phi2', 'macro.sc_phi2', zones=phi_z, via=[(232.8, 164.0), (232.8, 196.9)],
                 avoid=[(ANALOG, 20.0, 8)], follow=[('sc_phi1', 0.7)], margin=12, label='sc_phi2'))
    # ua[1] debug: from dbg_tg down the gap west of the chain (x 72.34-74.84) and east under it
    # (beneath the RX input wires, on met2) to the pad
    out.append(N('dbg', 'xdbg.b', 'ua[1]', via=[(73.6, 60.0), (73.6, 4.0)], layers=['m2', 'm3', 'm4'],
                 zones=nochain, margin=8, label='dbg'))
    # LNA low-gain strap (lna_lo_n, DC, latched at reset): west along the very bottom of the tile
    # from the macro, under bias_gen, and up into the chain's south edge
    out.append(N('lna_lo', 'macro.lna_lo_n', 'xrx.lna_lo_n', via=[(279.0, 3.6), (205.0, 2.1)],
                 layers=['m1', 'm2', 'm3', 'm4'], zones=nochain, margin=6, label='lna_lo_n'))
    out.append(N('rx_en', 'macro.rx_en', 'xbias.en', margin=8, label='rx_en'))
    # (gap columns: the lower the macro pin, the further west and the lower the turn at the top;
    # at the west end the lowest track turns down first, so nothing crosses)
    # enables: west across xdeca part 6 at their own height (below every TT pin), up the
    # x 232.4-236 gap, west on met2 above comp_ct / over xdecd part 4, then down the west side over
    # xdeca part 5 to dbg_tg / the TX cluster
    en_z = [blk(76, 0, 232.6, 196.0), nochain[0]]
    out.append(N('dbg_en', 'macro.dbg_en', 'xdbg.en', via=[(234.0, 161.0), (234.0, 198.7), (53.8, 198.7)],
                 zones=en_z[:2], margin=8, label='dbg_en'))
    out.append(N('tx_en', 'macro.tx_en', 'xtx.xring.en', 'xtx.xlse_p.in', via=[(235.2, 163.7), (235.2, 199.9), (52.6, 199.9)],
                 zones=en_z[:2], margin=8, label='tx_en'))
    # (tx_en_n: a met4 jumper just before xlse_n's input: antenna, the gate sees only the last met3)
    out.append(N('tx_en_n', 'macro.tx_en_n', 'xtx.xlse_n.in', via=[(234.6, 162.4), (234.6, 199.3), (53.2, 199.3), (28.8, 62.7, 'm4'), (27.6, 62.7, 'm4')],
                 zones=en_z[:2], margin=8, label='tx_en_n'))

    # ---------------- power ----------------
    # RX trunks (docs/power.md): one net per block from its strap set, w 4 (necked only where it
    # has to). Each may land on the strap or on the trunks routed before it from the same set,
    # never on another block's rail.
    for net, blocks in (('VGND', TRUNK_VGND), ('VDPWR', TRUNK_VDPWR)):
        prev = {'m': [], 'w': []}
        for b, pins, side in blocks:
            nm = f'{net}_RX_{b}'
            land = [f'{net}@{side}'] + (['VGND_RXL'] if net == 'VGND' and side == 'm' else []) + prev[side]
            out.append(N(nm, land, pins, anchors=land, own=prev[side], w_try=[4.0, 3.0, 2.0, 1.0],
                         layers=['m1', 'm2', 'm3', 'm4'], layer_cost={'m1': 6, 'm2': 3, 'm3': 1, 'm4': 1}, margin=30,
                         zones=[blk(0, 212.7, 300, 226), nochain[0]], wide=True))
            prev[side].append(nm)
    # the rest (chain, VDPWR decaps): the chain's VDD from the full-width VDPWR bar right under
    # it, and both the west and the mid straps (this also joins them inside the tile)
    out.append(N('VDPWR_RX', STRAPS['VDPWR'], 'xrx.VDD', 'xdecd1.VDPWR', 'xdecd2.VDPWR', 'xdecd3.VDPWR', 'xdecd4.VDPWR',
                 w=1.0, layers=['m1', 'm2', 'm3', 'm4'], layer_cost={'m1': 6, 'm2': 2, 'm3': 1, 'm4': 1},
                 margin=30, anchors=STRAPS['VDPWR'], zones=[blk(0, 212.7, 300, 226)], wide=True))
    out.append(N('VGND_RX', STRAPS['VGND'], 'xrx.VSS', 'xdecd1.VGND', 'xdecd2.VGND', 'xdecd3.VGND', 'xdecd4.VGND',
                 w=1.0, anchors=STRAPS['VGND'],
                 layers=['m1', 'm2', 'm3', 'm4'], layer_cost={'m1': 6, 'm2': 2, 'm3': 1, 'm4': 1}, margin=30,
                 zones=[blk(0, 212.7, 300, 226)], wide=True))
    # Cdet's bottom plate: VDPWR (as log_det's Cdet)
    out.append(N('VDPWR_cdet', 'VDPWR@w', 'xcdet.VDD', anchors=['VDPWR@w'], w_try=[2.0, 1.0],
                 layers=['m1', 'm2', 'm3', 'm4'], margin=30, wide=True))

    # VAPWR decaps: their rails also join the west and mid VAPWR / VGND straps (the TX supply's
    # own return: joins the RX ground only at the straps)
    deca = [f'xdeca{k}' for k in range(1, 8)]
    out.append(N('VAPWR_DEC', 'VAPWR@w', 'VAPWR@m', *[f'{d}.VAPWR' for d in deca], w=1.0,
                 layers=['m1', 'm2', 'm3', 'm4'], layer_cost={'m1': 6, 'm2': 2, 'm3': 1, 'm4': 1}, margin=30, wide=True))
    out.append(N('VGND_DEC', 'VGND@w', 'VGND@m', *[f'{d}.VGND' for d in deca], w=1.0,
                 layers=['m1', 'm2', 'm3', 'm4'], layer_cost={'m1': 6, 'm2': 2, 'm3': 1, 'm4': 1}, margin=30, wide=True))

    return out


def tx_feed():
    """The TX drivers' VAPWR feed (fixed, in tx_top). Each driver's met3 VAPWR rail (3 x 40 um,
    vertical: xdrv_n's on its west edge x 16.4-19.4, xdrv_p's on its east edge x 69.34-72.34, both
    y 4.5-44.65) fed along its whole length, never through the other's rail.
    - xdrv_n: a met3 sheet x 0.3-16.4 joined to its rail along the full height (under the west
      VDPWR / VGND straps; xdeca part 1 below it is met1 only), via3 up into the west VAPWR strap
      (met4 x 0.3-5.3) all the way up.
    - xdrv_p: via3 from xdrv_n's rail up to a met4 bus (y 8.2-24) east over both drivers (they have
      no met4), and a met4 strip over xdrv_p's rail with via3 along it.
    """
    Y0, Y1 = 4.5, 44.65                         # the drivers' rails
    BY0, BY1 = 8.2, 24.0                        # met4 bus band
    f = [('box', 'm3', 0.3, Y0, 16.4, Y1)]
    f += [('via', 'm3', 'm4', 2.8, round(7.5 + 3.6 * k, 2), 4.4) for k in range(10)]
    f += [('box', 'm4', 15.6, BY0, 72.34, BY1)]
    f += [('via', 'm3', 'm4', 17.9, round(BY0 + 1.5 + 2.5 * k, 2), 3.0) for k in range(6)]
    f += [('box', 'm4', 69.34, BY0, 72.34, Y1)]
    f += [('via', 'm3', 'm4', 70.84, round(BY0 + 1.5 + 2.5 * k, 2), 3.0) for k in range(14)] + [('via', 'm3', 'm4', 70.84, Y1 - 1.5, 3.0)]
    return dict(name='VAPWR_TXF', fixed=f, w=3.0, cell='tx_top',
                own=['VAPWR@w', 'xtx.xdrv_n.VAPWR', 'xtx.xdrv_p.VAPWR'])


def tx_gnd_feed():
    """The TX drivers' VGND feed (fixed, in tx_top): a met4 bus straight off the west VGND strap's
    met4 (x 12.0-15.1) east over xdrv_n to both drivers' VSS rails (met3, side by side at
    x 40.08-43.08 / 45.66-48.66), above the VAPWR bus, with via3 down onto each rail along it."""
    BY0, BY1 = 26.0, 44.65
    f = [('box', 'm4', 12.0, BY0, 48.66, BY1)]
    for x0 in (40.08, 45.66):
        xc = round(x0 + 1.5, 2)
        f += [('via', 'm3', 'm4', xc, round(BY0 + 1.5 + 2.5 * k, 2), 3.0) for k in range(7)] + [('via', 'm3', 'm4', xc, BY1 - 1.5, 3.0)]
    return dict(name='VGND_TXF', fixed=f, w=3.0, cell='tx_top',
                own=['VGND@w', 'xtx.xdrv_n.VSS', 'xtx.xdrv_p.VSS'])


def vgnd_landing():
    """A wide landing for the RX VGND trunks (fixed). The mid VGND strap (1.2 um) sits 0.5 um from
    the VAPWR / VDPWR straps, so a wide trunk can't put a via on it below y 220.76; above that
    the other two straps end: a met4 bar west from the strap's top end (y 221.45-224.4, 0.4 clear of
    the TT jumpers and the TT bus columns) and a met4 column down the MOS-only top of xdeca part 1
    (free met4 x 251.5-273.5, y 162-226)."""
    f = [('box', 'm4', 252.0, 221.45, 279.4, 224.4), ('box', 'm4', 262.0, 162.3, 268.0, 224.4)]
    return dict(name='VGND_RXL', fixed=f, w=3.0, own=['VGND@m'])


def tt_bus():
    """The 42 TT wires as a two-layer channel (fixed geometry, not maze-routed).
    Tile pins (met4, top edge, x 15-131) -> the macro's west-edge pins (met3, y 165-221).
    Channel: y 213.75-225.4, above xdeca part 2 (whose MIM reserves met3/met4 below 213).
    - West group (the 24 westernmost pins): met4 drop -> met2 track east (0.48 pitch) ->
      met2 column down over the MOS-only top of xdeca part 1 -> met3 into the macro pin.
      Columns ordered by track height (higher track, further east), so nothing crosses.
    - East group (18): met3 tracks (0.65 pitch: a via3 pad next to a passing track). Pins
      level with the channel run straight in; the rest drop on met4 columns west of the
      west group's columns, then met3 into the pin.
    """
    import json, os
    P = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../build/top/pins.json')))
    tt = ['clk', 'rst_n'] + [f'{b}[{k}]' for b in ('ui_in', 'uio_in', 'uo_out', 'uio_out', 'uio_oe')
                             for k in range(8)]
    DEF = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../mag/tt_analog_3x2_3v3.def')
    import re
    txt = open(DEF).read()
    xpin = {}
    for m in re.finditer(r'- (\S+) \+ NET .*?PLACED \( (-?\d+) (-?\d+) \)', txt, re.S):
        xpin[m.group(1)] = int(m.group(2)) / 1000
    mac = {}
    for n in tt:
        b = P['pins']['macro'][n][0][1]
        mac[n] = (b[0], round((b[1] + b[3]) / 2, 3))          # (left x, centre y)
    order = sorted(tt, key=lambda n: xpin[n])                 # west -> east

    def into_pin(x0, y, x1):
        # antenna: a met4 jumper just west of the straps, so at the met3 etch a macro input gate
        # sees only the last ~7 um of met3 (the long track is on the other side of the jumper)
        return [('wire', 'm3', x0, y, XJ0, y), ('via', 'm3', 'm4', XJ0, y), ('wire', 'm4', XJ0, y, XJ1, y),
                ('via', 'm3', 'm4', XJ1, y), ('wire', 'm3', XJ1, y, x1, y)]
    W, E = order[:24], order[24:]
    YPIN = 225.26                                             # tile pin centre
    XSTRAP = 15.7                   # first met4 drop x clear of the west VGND strap (12.0-15.1: > 3 um, 0.4 apart)
    XJ0, XJ1 = 274.0, 275.4         # antenna jumper (met4) west of the mid straps (met4 from 276.5)
    XMAC = lambda n: round(mac[n][0] + 0.3, 3)                # into the macro pin
    nets = []
    # east group: tracks
    ytop, ylow = 225.45, 213.75
    straight = [n for n in E if mac[n][1] >= ylow]
    slots = []
    ys = sorted(mac[n][1] for n in straight)
    y = ylow
    while y <= ytop + 1e-9:
        if all(abs(y - p) >= 0.65 - 1e-9 for p in ys) and all(abs(y - q) >= 0.65 - 1e-9 for q in slots):
            slots.append(round(y, 3))
        y = round(y + 0.01, 3)
    rest = [n for n in E if n not in straight]
    assert len(slots) >= len(rest), (len(slots), len(rest))
    # lowest macro pin -> lowest slot (and westmost column): tidy, not required
    rest.sort(key=lambda n: mac[n][1])
    xc = 243.0
    for n, yt in zip(rest, slots):
        x0, yp = xpin[n], mac[n][1]
        f = [('wire', 'm4', x0, YPIN, x0, yt), ('via', 'm3', 'm4', x0, yt),
             ('wire', 'm3', x0, yt, xc, yt), ('via', 'm3', 'm4', xc, yt),
             ('wire', 'm4', xc, yt, xc, yp), ('via', 'm3', 'm4', xc, yp),
             *into_pin(xc, yp, XMAC(n))]
        nets.append(dict(name=n, fixed=f, w=0.3))
        xc = round(xc + 0.7, 3)                                # (via3 pads on met4)
    for n in straight:
        x0, yp = xpin[n], mac[n][1]
        f = [('wire', 'm4', x0, YPIN, x0, yp), ('via', 'm3', 'm4', x0, yp),
             *into_pin(x0, yp, XMAC(n))]
        nets.append(dict(name=n, fixed=f, w=0.3))
    # west group: met2 tracks; column x rises with the track
    yts = [round(ylow + 0.48 * k, 3) for k in range(len(W))]
    assert yts[-1] <= ytop
    # lowest macro pin gets the lowest track (its column is the westmost: its met3 run to the
    # macro then passes only higher columns, which are met2 and end above it)
    Ws = sorted(W, key=lambda n: mac[n][1])
    xc = round(xc + 1.0, 3)
    for n, yt in zip(Ws, yts):
        x0, yp = xpin[n], mac[n][1]
        f = []
        if x0 < XSTRAP:                 # the west VGND strap (met4, to y 220.76) is right below
            f += [('wire', 'm4', x0, YPIN, x0, 221.4), ('wire', 'm4', x0, 221.4, XSTRAP, 221.4)]
            x0 = XSTRAP
        f += [('wire', 'm4', x0, YPIN if not f else 221.4, x0, yt), ('via', 'm3', 'm4', x0, yt),
              ('via', 'm2', 'm3', x0, yt), ('pad', 'm3', x0, yt, 0.5),
             ('wire', 'm2', x0, yt, xc, yt), ('wire', 'm2', xc, yt, xc, yp), ('via', 'm2', 'm3', xc, yp),
             *into_pin(xc, yp, XMAC(n))]
        nets.append(dict(name=n, fixed=f, w=0.3))
        xc = round(xc + 0.6, 3)
    assert xc < 275.0, xc
    return nets
