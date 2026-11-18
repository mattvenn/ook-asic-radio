"""Where the extracted RX block (rx_t) loses its gain: the detector's inputs, or the tap wiring to them (2026-11-18).

rx_t extracted has 4.7 dB less gain at 434 MHz than lna_chain_t extracted alone (docs/verify_tall.md). Each tap
(o1..o5, out) runs from the chain's tap column along a shielded track to its det_cell, up to ~60 um: rx_t's tap nets
carry 14-32 fF more than the chain's. This runs the stability bench's AC (build/pexsim/stab_2n_0.spice: tt 27 C,
full gain, 2 nH, real decap, C = 0) on one deck per version of the RX, and prints the gain at every tap:

    sch       layout/ref/rx_t.spice: schematic chain + schematic detector
    chain     lna_chain_t extracted, no detector
    chain+det lna_chain_t extracted + the schematic detector on the taps (ideal tap wires)
    rx_t      rx_t extracted (chain, detector and tap wiring)
    lumped    chain+det plus, on each tap net, the C to ground that rx_t adds over the chain (from the extractions)
    lumped_k  the same on tap k only (k = 1..6)

chain+det -> rx_t is the cost of the tap wiring and the detector's layout; per stage, a tap's load shows as a lower
gain into that node. Run in the tools image from the repo root:
    tools/osic python3 sim/chain/tap_loss.py            (results: build/tap_loss/, ~minutes)
"""
import collections
import math
import os
import re
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'build', 'tap_loss')
BASE = os.path.join(ROOT, 'build', 'pexsim', 'stab_2n_0.spice')
PORTS = 'inp inn ibias vcm lna_lo_n outp outn o1p o1n o2p o2n o3p o3n o4p o4n o5p o5n'
TAPS = [('o1p', 'o1n'), ('o2p', 'o2n'), ('o3p', 'o3n'), ('o4p', 'o4n'), ('o5p', 'o5n'), ('outp', 'outn')]
# the bench's names for the chain's tap ports (x1 pad_p pad_n ibias vcm glo out_p out_n o1p ...)
BENCH = {'outp': 'out_p', 'outn': 'out_n'}


def subckt(name, text):
    m = re.search(rf'^\.subckt {name}\s.*?^\.ends[^\n]*\n', text, flags=re.S | re.M)
    assert m, name
    return m.group(0)


def cval(v):
    u = {'f': 1e-15, 'a': 1e-18, 'p': 1e-12, 'n': 1e-9}
    return float(v[:-1]) * u[v[-1]] if v[-1] in u else float(v)


def tap_c(path):
    """Total extracted C on each tap net (all its segments, every C it touches), F."""
    tot = collections.defaultdict(float)
    for line in open(path):
        p = line.split()
        if line[0] == 'C' and len(p) >= 4:
            for n in p[1:3]:
                tot[n.split('.t')[0]] += cval(p[3])
    return tot


def det_lib(ref):
    return subckt('log_det_t', ref) + subckt('det_cell', ref)


def rx_versions():
    ref = open(os.path.join(ROOT, 'layout', 'ref', 'rx_t.spice')).read()
    chain_pex = open(os.path.join(ROOT, 'layout', 'pex', 'lna_chain_t.spice')).read()
    rx_pex = os.path.join(ROOT, 'layout', 'pex', 'rx_t.spice')
    taps = ' '.join(n for t in TAPS[:5] for n in t)
    head = f'.subckt rx_t {PORTS} ibias_det det VDD VSS VDDD\n'
    xc = f'Xc {PORTS} VDD VSS lna_chain_t\n'
    xd = f'Xd {taps} outp outn ibias_det det VDDD VSS log_det_t\n'
    v = {}
    v['sch'] = ref                                            # rx_t + lna_chain_t + amps + log_det_t + det_cell
    # no detector: det and ibias_det still need a DC path (Cdet and Ibd sit on them in the wrapper)
    v['chain'] = head + xc + 'Rdet det VDDD 10k\nRbd ibias_det VSS 1k\n.ends\n' + chain_pex
    v['chain+det'] = head + xc + xd + '.ends\n' + chain_pex + det_lib(ref)
    v['rx_t'] = open(rx_pex).read()
    cr, cc = tap_c(rx_pex), tap_c(os.path.join(ROOT, 'layout', 'pex', 'lna_chain_t.spice'))
    dc = {n: cr[n] - cc[n] for t in TAPS for n in t}
    lump = {n: f'Cx_{n} {n} VSS {dc[n]:.4g}\n' for n in dc}
    v['lumped'] = head + xc + xd + ''.join(lump.values()) + '.ends\n' + chain_pex + det_lib(ref)
    for k, t in enumerate(TAPS, 1):
        v[f'lumped_{k}'] = head + xc + xd + ''.join(lump[n] for n in t) + '.ends\n' + chain_pex + det_lib(ref)
    return v, dc


def deck(base, rx):
    s = base
    a = s.index('.subckt rx_t ')
    b = s.index('.ends', a)
    b = s.index('\n', b) + 1
    s = s[:a] + rx + s[b:]
    meas = []
    for k, (p, n) in enumerate(TAPS, 1):
        p, n = BENCH.get(p, p), BENCH.get(n, n)
        meas.append(f'let m{k} = db(v({p}) - v({n}))[0]')
    nodes = ' '.join(f'v({BENCH.get(x, x)})' for t in TAPS for x in t)
    ctl = (f'.control\nsave {nodes}\nac lin 1 433.92e6 433.92e6\n' + '\n'.join(meas) + '\n'
           'echo RESULT ' + ' '.join(f'$&m{k}' for k in range(1, 7)) + '\n.endc\n')
    return re.sub(r'^\.control.*?^\.endc\n', lambda m: ctl, s, count=1, flags=re.S | re.M)


def main():
    os.makedirs(OUT, exist_ok=True)
    base = open(BASE).read()
    vers, dc = rx_versions()
    with open(os.path.join(OUT, 'tap_dc.txt'), 'w') as f:
        for n, c in dc.items():
            f.write(f'{n} {c * 1e15:.2f} fF\n')
    # 12 decks at once, 2 threads each (24 of the machine's 28)
    init = re.sub(r'num_threads=\d+', 'num_threads=2', open(os.path.join(ROOT, '.spiceinit')).read())
    open(os.path.join(OUT, '.spiceinit'), 'w').write(init)
    procs = {}
    for name, rx in vers.items():
        sp = os.path.join(OUT, f'{name}.spice')
        open(sp, 'w').write(deck(base, rx))
        procs[name] = subprocess.Popen(f'cd {OUT} && ngspice -b {name}.spice > {name}.log 2>&1',
                                       shell=True)
    for p in procs.values():
        p.wait()
    res = {}
    for name in vers:
        m = re.search(r'^RESULT (.*)$', open(os.path.join(OUT, f'{name}.log')).read(), re.M)
        res[name] = [float(x) for x in m.group(1).split()] if m else None
    print('| Version | ' + ' | '.join(f'{p[:-1]}, dB' for p, _ in TAPS) + ' |')
    print('|---' * 7 + '|')
    for name, r in res.items():
        print(f'| {name} | ' + (' | '.join(f'{x:.2f}' for x in r) if r else 'no RESULT') + ' |')
    print('\nPer-stage gain (into each tap, dB):')
    for name, r in res.items():
        if r:
            print(f'  {name:10s}', ' '.join(f'{x:6.2f}' for x in [r[0]] + [r[i] - r[i - 1] for i in range(1, 6)]))
    print('\nExtra C rx_t adds over the chain on each tap net, fF:',
          ' '.join(f'{n} {c * 1e15:.1f}' for n, c in dc.items()))


if __name__ == '__main__':
    sys.exit(main())
