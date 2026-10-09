"""Top-level nets for layout/gen/route.py, in routing order. Connectivity from
xschem/gen/top.py (radio_analog + tt_um_mattvenn_radio); routing intent from
docs/handoff_toplevel.md "Nets and routing intent".

A terminal is a list of tags (any one of them may be hit): 'inst.pin' for a block pin,
the bare name for a tile pin or a power strap.
"""


def N(name, *terms, **kw):
    terms = [t if isinstance(t, list) else [t] for t in terms]
    own = set(kw.pop('own', [])) | {t for tt in terms for t in tt}
    return dict(name=name, terms=terms, own=sorted(own), label=kw.pop('label', None), **kw)


def nets():
    out = []
    # --- RX analog path ---
    out.append(N('rx_p', 'ua[0]', 'xchain.inp', w=2.0, layers=['m3', 'm4']))
    out.append(N('rx_n', 'ua[1]', 'xchain.inn', w=2.0, layers=['m3', 'm4']))
    out.append(N('det', 'xdet.det', 'xlpf.in', 'xdbg.a', label='det'))
    out.append(N('lpf', 'xlpf.out', 'xcomp.inn', 'xavg.in', label='lpf'))
    out.append(N('avg', 'xavg.out', 'xcomp.inp', label='avg'))
    return out
