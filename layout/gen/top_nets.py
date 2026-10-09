"""Top-level nets for layout/gen/route.py, in routing order. Connectivity from
xschem/gen/top.py (radio_analog + tt_um_mattvenn_radio); routing intent from
docs/handoff_toplevel.md "Nets and routing intent".

A terminal is a list of tags (any one of them may be hit): 'inst.pin' for a block pin,
the bare name for a tile pin, 'NET@w|m|e' for a power strap (west / mid / east set).
Coordinates in tile um.
"""

STRAPS = {n: [f'{n}@{s}' for s in 'wme'] for n in ('VDPWR', 'VGND', 'VAPWR')}
CHAIN = (13.14, 6.5, 158.5, 76.97)
CHAIN_IN = (100, 0, 160, 45)                 # input section + stage 1 (rule 2)
ANALOG = ['det', 'lpf', 'avg', 'xcomp.inp', 'xcomp.inn', 'xavg.in', 'xavg.out', 'xlpf.out', 'xlpf.in',
          'xdet.det', 'trim', 'xcomp.trim', 'xctrim.trim', 'xdac.out']
TRIM = ['trim', 'xcomp.trim', 'xctrim.trim', 'xdac.out']


def N(name, *terms, **kw):
    terms = [t if isinstance(t, list) else [t] for t in terms]
    own = set(kw.pop('own', [])) | {t for tt in terms for t in tt}
    return dict(name=name, terms=terms, own=sorted(own), label=kw.pop('label', None), **kw)


def blk(x0, y0, x1, y1, layers=None):
    return (x0, y0, x1, y1, layers, 'block')


def nets():
    out = tt_bus()          # fixed geometry first: every routed net then keeps clear of it
    # ---------------- RX analog path ----------------
    # antenna inputs: straight up from the pads, as a pair, nothing else near
    out.append(N('rx_p', 'ua[0]', 'xchain.inp', w=2.0, layers=['m3', 'm4']))
    out.append(N('rx_n', 'ua[1]', 'xchain.inn', w=2.0, layers=['m3', 'm4']))
    # chain taps -> log_det (pairs together); late stages kept off the input section
    for k in range(1, 7):
        o = f'o{k}' if k < 6 else 'out'
        z = [blk(*CHAIN_IN)] if k >= 4 else []
        out.append(N(f'{o}p', f'xchain.{o}p', f'xdet.t{k}p', zones=z, label=f'{o}p'))
        out.append(N(f'{o}n', f'xchain.{o}n', f'xdet.t{k}n', zones=z, follow=[(f'{o}p', 0.7)], label=f'{o}n'))
    # det: slow, high impedance; short
    out.append(N('det', 'xdet.det', 'xlpf.in', 'xdbg.a', label='det'))
    out.append(N('lpf', 'xlpf.out', 'xcomp.inn', 'xavg.in', label='lpf'))
    out.append(N('avg', 'xavg.out', 'xcomp.inp', label='avg'))
    # trim: r2r out -> Ctrim (either trim pin) -> comp trim; met2 straight over r2r
    out.append(N('trim', 'xdac.out', 'xctrim.trim', 'xcomp.trim', layers=['m1', 'm2', 'm3', 'm4'],
                 layer_cost={'m1': 4, 'm2': 1, 'm3': 2, 'm4': 2}, label='trim'))
    # comp_in: down between Ctrim and r2r, east under r2r; off the trim node
    out.append(N('comp', 'xcomp.out', 'macro.comp_in', via=[(183.2, 105.0), (190.0, 89.4)],
                 avoid=[(TRIM, 3.0, 30)], margin=10, label='comp'))
    # trim_out[i] -> r2r b_i: straight horizontals across xdeca part 1 and the straps
    for i in range(8):
        out.append(N(f'trim[{i}]', f'macro.trim_out[{i}]', f'xdac.b{i}', layers=['m1', 'm2', 'm3'],
                     margin=6, label=f'trim[{i}]'))
    # bias
    out.append(N('ib_det', 'xbias.ib_det', 'xdet.ibias_det', margin=8, label='ib_det'))
    out.append(N('ib_comp', 'xbias.ib_comp', 'xcomp.ibias', margin=8, label='ib_comp'))
    out.append(N('ib_chain', 'xbias.ib_chain', 'xchain.ibias', margin=8, label='ib_chain'))
    out.append(N('vcm', 'xbias.vcm', 'xchain.vcm', margin=8, label='vcm'))

    # ---------------- TX ----------------
    # (TX-internal wires and the TX supply wiring go into the tx_top cell: LVS against tx_top.sch)
    # TX: VAPWR from the west strap, its own ground run (joins the RX ground only at the straps)
    tx_vss = ['xtx.xring.VSS', 'xtx.xls.VSS', 'xtx.xlse_p.VSS', 'xtx.xlse_n.VSS', 'xtx.xdrv_p.VSS',
              'xtx.xdrv_n.VSS']
    out.append(N('VAPWR_TX', 'VAPWR@w', 'xtx.xdrv_n.VAPWR', 'xtx.xdrv_p.VAPWR', 'xtx.xls.VAPWR',
                 'xtx.xlse_n.VAPWR', 'xtx.xlse_p.VAPWR', w=2.5, layers=['m3', 'm4'], margin=8, wide=True, cell='tx_top', late=['VAPWR@w']))
    out.append(N('VGND_TX', 'VGND@w', *tx_vss, w=2.0, layers=['m3', 'm4'], margin=8, wide=True, cell='tx_top', late=['VGND@w']))
    out.append(N('VDPWR_TX', 'VDPWR@w', 'xtx.xring.VDD', 'xtx.xls.VDD', 'xtx.xlse_p.VDD',
                 'xtx.xlse_n.VDD', w=0.8, layers=['m2', 'm3', 'm4'], margin=8, wide=True, cell='tx_top', late=['VDPWR@w']))
    out.append(N('ring', 'xtx.xring.out', 'xtx.xls.in', margin=8, label='ring', cell='tx_top'))
    out.append(N('tx_a', 'xtx.xls.A', 'xtx.xdrv_p.in', margin=6, label='a', cell='tx_top'))
    out.append(N('tx_b', 'xtx.xls.B', 'xtx.xdrv_n.in', margin=6, label='b', cell='tx_top'))
    out.append(N('enh_p', 'xtx.xlse_p.A', 'xtx.xdrv_p.en', margin=8, label='enh_p', cell='tx_top'))
    out.append(N('enh_n', 'xtx.xlse_n.A', 'xtx.xdrv_n.en', margin=6, label='enh_n', cell='tx_top'))
    # TX outputs: >= 5 um, met3/met4 (may cross the chain: TX is off while RX is on)
    # The chain's top stage row (y 55-77) is solid met4 / MIM except 2.6 um gaps between the
    # stages, and one ~5.4 um column at its west end (x 15.1-20.8). tx_n takes the column, then
    # the gap under the chain; tx_p necks to 2 um through the gap at x ~52 for ~22 um
    # (EM: 9.8 mA RMS -> 4.9 mA/um, limit 14.9), then widens again (open point for Matt).
    out.append(N('tx_n', 'xtx.xdrv_n.out', 'ua[4]', w=4.6, layers=['m3', 'm4'], margin=10,
                 via=[(17.9, 40.0, 'm4')]))
    out.append(N('tx_p_neck', 'xtx.xdrv_p.out', w=2.0, layers=['m3', 'm4'], margin=10,
                 via=[(52.1, 52.0, 'm4')]))
    out.append(N('tx_p', 'tx_p_neck', 'ua[3]', w=5.0, layers=['m3', 'm4'], margin=10))

    # ---------------- power ----------------
    # RX: both the west and the mid straps (this also joins them inside the tile)
    out.append(N('VDPWR_RX', STRAPS['VDPWR'], 'xchain.VDD', 'xdet.VDD', 'xavg.VDD', 'xcomp.VDD',
                 'xbias.VDD', 'xdbg.VDD', w=1.0, layers=['m2', 'm3', 'm4'], layer_cost={'m2': 2, 'm3': 1, 'm4': 1},
                 margin=30, anchors=STRAPS['VDPWR'], zones=[blk(0, 192.6, 300, 226)], wide=True))
    out.append(N('VGND_RX', STRAPS['VGND'], 'xchain.VSS', 'xdet.VSS', 'xlpf.VSS', 'xavg.VSS',
                 'xcomp.VSS', 'xdac.VGND', 'xctrim.VGND', 'xbias.VSS', 'xdbg.VSS', w=1.0, anchors=STRAPS['VGND'],
                 layers=['m1', 'm2', 'm3', 'm4'], layer_cost={'m1': 6, 'm2': 2, 'm3': 1, 'm4': 1}, margin=30,
                 zones=[blk(0, 192.6, 300, 226)], wide=True))

    # ---------------- digital interface ----------------
    # avg_sc clocks: over the top of avg_sc, east above comp_ct, down the x 239-242 gap, across
    # xdeca part 1 / the straps on met2 to the macro; >= ~20 um from the analog nodes
    phi_z = [blk(0, 0, 239, 181.2), blk(130, 181.2, 239, 190.4), blk(243, 162, 276.5, 226)]
    out.append(N('sc_phi1', 'xavg.phi1', 'macro.sc_phi1', zones=phi_z, via=[(240.5, 175.0, 'm3'), (240.5, 191.6)],
                 avoid=[(ANALOG, 20.0, 8)], margin=12, label='sc_phi1'))
    out.append(N('sc_phi2', 'xavg.phi2', 'macro.sc_phi2', zones=phi_z, via=[(239.8, 178.0)],
                 avoid=[(ANALOG, 20.0, 8)], follow=[('sc_phi1', 0.7)], margin=12, label='sc_phi2'))
    # ua[2] debug: west along the bottom gap and up outside the chain (never across it)
    out.append(N('dbg', 'xtx.xdrv_n.out' if False else 'xdbg.b', 'ua[2]', via=[(12.0, 79.0), (12.0, 3.4)],
                 zones=[blk(*CHAIN)], margin=8))
    out.append(N('rx_en', 'macro.rx_en', 'xbias.en', margin=8, label='rx_en'))
    # enables: west across xdeca part 1 at their own height (below every TT pin, so the TT
    # staircase over part 1 crosses nothing), up the x 239-242 gap, west on met2 along the bottom
    # of xdeca part 2 (below the TT wires there), down to the TX cluster / dbg_tg
    en_z = [blk(66, 0, 236.5, 192.6), blk(*CHAIN), blk(243, 162, 276.5, 226), blk(0, 195.6, 242.5, 226)]
    out.append(N('dbg_en', 'macro.dbg_en', 'xdbg.en', via=[(238.6, 175.0, 'm2'), (238.6, 193.9), (64.0, 193.9)],
                 zones=en_z + [blk(0, 0, 50, 192.6)],
                 margin=8, label='dbg_en'))
    out.append(N('tx_en', 'macro.tx_en', 'xtx.xring.en', 'xtx.xlse_p.in', via=[(238.0, 175.0, 'm2'), (238.0, 194.5), (46.0, 194.5)],
                 zones=en_z,
                 margin=8, label='tx_en'))
    out.append(N('tx_en_n', 'macro.tx_en_n', 'xtx.xlse_n.in', via=[(237.4, 175.0, 'm2'), (237.4, 195.1), (40.0, 195.1)], zones=en_z,
                 margin=8, label='tx_en_n'))

    return out


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
    W, E = order[:24], order[24:]
    YPIN = 225.26                                             # tile pin centre
    XSTRAP = 15.6                   # first met4 drop x clear of the west VGND strap (13.9-15.1)
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
             ('wire', 'm3', xc, yp, XMAC(n), yp)]
        nets.append(dict(name=n, fixed=f, w=0.3))
        xc = round(xc + 0.7, 3)                                # (via3 pads on met4)
    for n in straight:
        x0, yp = xpin[n], mac[n][1]
        f = [('wire', 'm4', x0, YPIN, x0, yp), ('via', 'm3', 'm4', x0, yp),
             ('wire', 'm3', x0, yp, XMAC(n), yp)]
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
             ('wire', 'm3', xc, yp, XMAC(n), yp)]
        nets.append(dict(name=n, fixed=f, w=0.3))
        xc = round(xc + 0.6, 3)
    assert xc < 275.0, xc
    return nets
