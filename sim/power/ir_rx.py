"""IR drop with the real currents (benchmark step 3).

1. RX operating point (rx_en = 1, TX off, no signal) of xschem/tb_radio_analog.sch with radio_analog
   from the extraction with the PDN drawn in (build/power/ext_<case>/, ideal supplies at its ports).
   Each supply terminal's current = the current through the resistors attached to it.
2. Those currents into the supply meshes (sim/power/mesh.py, port at 0 V): each mesh node's voltage
   is its drop from the port; per block mean / worst over its device terminals. TX: the drivers'
   measured arm currents (docs/layout.md: 6.65 mA average, 18.4 mA peak per arm on VAPWR, 2.29 /
   11.9 mA on VSS) spread over each driver's terminals.

    python3 sim/power/ir_rx.py [A|B]
Writes build/power/ir_<case>.json.
"""
import collections
import json
import os
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import common  # noqa: E402
import r_mesh  # noqa: E402
from rawread import read_raw  # noqa: E402

TX = {'VAPWR': {'avg': 6.65e-3, 'peak': 18.4e-3}, 'VGND': {'avg': 2.29e-3, 'peak': 11.9e-3}}


def rx_op(case):
    """{supply terminal node: current into the tile's supply metal from the device, A} at the RX op."""
    src = open(os.path.join(common.ROOT, 'build', 'tb_radio_analog.spice')).read()
    deck, n = re.subn(r'^\.subckt\s+radio_analog\s.*?^\.ends\b[^\n]*\n', '', src, flags=re.S | re.M | re.I)
    assert n == 1
    deck = re.sub(r'^\.control.*?^\.endc', '.control\nop\nwrite ir_op_%s.raw\n.endc' % case, deck,
                  flags=re.S | re.M)
    deck = re.sub(r'^\.save .*$', '.save all', deck, flags=re.M)
    wrap = common.sch_wrapper(case)
    # the tile's digital-pin stubs: 1G to VGND (floating otherwise)
    stubs = sorted(set(re.findall(r'\bnc_\w+', wrap)))
    lines = wrap.splitlines()
    i = max(k for k, l in enumerate(lines) if l.startswith('.ends'))
    lines[i:i] = [f'Rnc{k} {s} VGND 1G' for k, s in enumerate(stubs)]
    path = os.path.join(common.B, f'ir_op_{case}.spice')
    open(path, 'w').write(re.sub(r'^\.end\s*$', '\n'.join(lines) + '\n.end', deck, flags=re.M))
    subprocess.run([common.OSIC, 'bash', '-c', f'cd build/power && ngspice -b ir_op_{case}.spice > ir_op_{case}.log 2>&1'],
                   cwd=common.ROOT)
    v = read_raw(os.path.join(common.B, f'ir_op_{case}.raw'))[0]['vars']
    top = {'VDPWR': 'v(vdpwr)', 'VAPWR': 'v(vapwr)'}

    def V(n):
        if n == 'VGND':
            return 0.0
        return float(v[top[n] if n in top else f'v(xana.x1.{n.lower()})'][0])
    cur = collections.Counter()
    for ln in common.r_only(case):
        t = ln.split()
        a, b, r = t[1], t[2], float(t[3])
        for x, y in ((a, b), (b, a)):
            if '.t' in x and '.t' not in y:
                try:
                    cur[x] += (V(x) - V(y)) / r
                except KeyError:
                    pass
    return cur, v


def solve_mesh(case, net, inj, tag):
    """Mesh node voltages (drop from the port) with currents inj {mesh node: A} drawn out of the net."""
    meta, lines = r_mesh.load_mesh(case, net)
    lines, alive, _ = r_mesh.connected(lines, net)
    name = f'ir_{case}_{net}_{tag}'
    deck = [f'* {name}'] + lines + [f'Vport {net} 0 0']
    for k, (n, i) in enumerate(inj.items()):
        deck.append(f'I{k} {n} 0 dc {i:.6e}')
    deck += ['.save ' + ' '.join(f'v({n})' for n in inj), '.control', 'op', f'write {name}.raw', '.endc', '.end']
    open(os.path.join(common.B, name + '.spice'), 'w').write('\n'.join(deck) + '\n')
    subprocess.run([common.OSIC, 'bash', '-c', f'cd build/power && ngspice -b {name}.spice > {name}.log 2>&1'],
                   cwd=common.ROOT)
    v = read_raw(os.path.join(common.B, name + '.raw'))[0]['vars']
    return {n: float(v[f'v({n.lower()})'][0]) for n in inj}, meta, alive


def main(case):
    pr = common.probes(case)
    xy = common.node_xy(case)
    cur, opv = rx_op(case)
    tot = {s: sum(i for n, i in cur.items() if common.supply_of(n) == s) for s in common.SUP}
    print('RX op: current into the supply metal from the devices (A):', {k: f'{v:.3e}' for k, v in tot.items()})
    out = {'rx': {}, 'tx': {}}
    for net in common.SUP:
        meta, lines = r_mesh.load_mesh(case, net)
        _, alive, _ = r_mesh.connected(lines, net)
        place = {}
        for b in pr:
            for t in pr[b].get(net, []):
                n = r_mesh.place(meta, xy[t], alive) if t in xy else None
                if n:
                    place[t] = (b, n)
        # RX: the op's terminal currents; a VDD terminal sources current (drawn out of the net:
        # inject -I), a VGND terminal sinks it
        inj = collections.Counter()
        for t, (b, n) in place.items():
            inj[n] += -cur.get(t, 0.0)
        drop, _, _ = solve_mesh(case, net, {n: i for n, i in inj.items() if abs(i) > 1e-12}, 'rx')
        per = collections.defaultdict(list)
        for t, (b, n) in place.items():
            if n in drop:
                per[b].append(drop[n])
        out['rx'][net] = {b: {'mean': float(np.mean(v)), 'worst': float(max(v, key=abs))} for b, v in per.items()}
        if net in TX:
            for tag in ('avg', 'peak'):
                inj = collections.Counter()
                for b in ('tx_drv_p', 'tx_drv_n'):
                    ns = [place[t][1] for t in pr[b][net] if t in place]
                    for n in ns:
                        inj[n] += (TX[net][tag] / len(ns)) * (1 if net == 'VAPWR' else -1)
                drop, _, _ = solve_mesh(case, net, dict(inj), f'tx{tag}')
                per = collections.defaultdict(list)
                for t, (b, n) in place.items():
                    if n in drop:
                        per[b].append(drop[n])
                out['tx'].setdefault(net, {})[tag] = {b: {'mean': float(np.mean(v)), 'worst': float(max(v, key=abs))}
                                                      for b, v in per.items()}
    json.dump({'tot': tot, **out}, open(os.path.join(common.B, f'ir_{case}.json'), 'w'), indent=1)
    print(f'case {case}, RX op: drop from the port at each block (mV, mean / worst; VGND: rise)')
    for b in sorted({b for d in out['rx'].values() for b in d}):
        row = [f"{out['rx'][n][b]['mean'] * 1e3:7.2f} / {out['rx'][n][b]['worst'] * 1e3:7.2f}" if b in out['rx'][n] else ''
               for n in common.SUP]
        print(f'{b:10s} ' + ' '.join(f'{c:>18s}' for c in row))
    for tag in ('avg', 'peak'):
        print(f'TX {tag} (both arms): drop at each driver, mV mean / worst')
        for net in TX:
            for b in ('tx_drv_p', 'tx_drv_n'):
                d = out['tx'][net][tag].get(b)
                if d:
                    print(f'  {net:6s} {b:9s} {d["mean"] * 1e3:7.1f} / {d["worst"] * 1e3:7.1f}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'A')
