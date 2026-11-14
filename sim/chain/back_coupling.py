"""Back-coupling in a chain extraction: every coupling C between two nets two or more stages
apart (later -> earlier), all R-split sub-nodes of a net together. Each stage instance's place
in the chain comes from the extraction itself (the net on its pair's gates). Ranks: inp/inn -1,
g1 0, o<k> k, out 6; a stage's internal nodes (sp, sn, tail, ...) sit between its input and
output.

    python3 sim/chain/back_coupling.py layout/pex/lna_chain_t.spice
"""
import re
import sys
from collections import defaultdict


def val(s):
    m = re.match(r'([0-9.eE+-]+)\s*([a-zA-Z]*)', s)
    u = m.group(2).lower()[:1]
    return float(m.group(1)) * {'a': 1e-18, 'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'm': 1e-3, 'k': 1e3}.get(u, 1)


def net(n):
    return re.sub(r'\.[nt]\d+$', '', n)


def main(path):
    txt = re.sub(r'\n\+', ' ', open(path).read())
    stage = {}
    for ln in txt.splitlines():
        t = ln.split()
        if ln[:1] in 'Xx' and len(t) > 5 and 'nfet' in ln:
            d, g, s = net(t[1]), net(t[2]), net(t[3])
            g = g[len('lna_chain_t_0.'):] if g.startswith('lna_chain_t_0.') else g
            gm = re.fullmatch(r'o(\d)[pn]', g)
            st = 1 if g in ('g1p', 'g1n') else int(gm.group(1)) + 1 if gm else None
            for x in (d, s):
                mm = re.fullmatch(r'(.*)\.\w+', x)
                if mm and st:
                    stage[mm.group(1)] = st

    # rx_t (chain + detector): the chain's own nets carry its instance prefix; each det_cell's
    # internal nodes (gp, gn, sp, sn) take the rank of the tap on its Cc (a MIM from its gp / gn)
    pre = 'lna_chain_t_0.'
    detc = {}
    for ln in txt.splitlines():
        t = ln.split()
        if ln[:1] in 'Xx' and 'cap_mim' in ln:
            a, b2 = net(t[1]), net(t[2])
            for x, y in ((a, b2), (b2, a)):
                m = re.fullmatch(r'(.*det_cell_\d+)\.g[pn]', x)
                mo = re.fullmatch(r'(o\d|out)[pn]', y)
                if m and mo:
                    detc[m.group(1)] = 6 if mo.group(1) == 'out' else int(mo.group(1)[1])

    def rank(n):
        if n.startswith(pre):
            n = n[len(pre):]
        m = re.fullmatch(r'(.*det_cell_\d+)\.\w+', n)
        if m and m.group(1) in detc and not n.endswith('.VSS'):
            return detc[m.group(1)]
        if n in ('inp', 'inn'):
            return -1
        if n in ('g1p', 'g1n'):
            return 0
        m = re.fullmatch(r'o(\d)[pn]', n)
        if m:
            return int(m.group(1))
        if n in ('outp', 'outn'):
            return 6
        m = re.fullmatch(r'(.*)\.\w+', n)
        return stage[m.group(1)] - 0.5 if m and m.group(1) in stage else None
    pair = defaultdict(float)
    for ln in txt.splitlines():
        if ln[:1] in 'Cc':
            t = ln.split()
            a, b, c = net(t[1]), net(t[2]), val(t[3])
            ra, rb = rank(a), rank(b)
            if ra is None or rb is None or abs(ra - rb) < 2:
                continue
            pair[(a, b) if ra > rb else (b, a)] += c
    print(f'{path}: stages {dict(sorted(stage.items(), key=lambda kv: kv[1]))}')
    if detc:
        print(f'  detector cells (tap rank): {dict(sorted(detc.items(), key=lambda kv: kv[1]))}')
    for (hi, lo), c in sorted(pair.items(), key=lambda kv: -kv[1])[:20]:
        print(f'  {hi} -> {lo}: {c * 1e18:.2f} aF')
    print(f'  {len(pair)} pairs two or more stages apart, {sum(pair.values()) * 1e18:.2f} aF in all')


if __name__ == '__main__':
    for p in sys.argv[1:]:
        main(p)
