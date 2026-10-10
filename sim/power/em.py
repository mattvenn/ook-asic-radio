"""EM on the TX supply paths (benchmark step 6): current per via cut and per um of metal width at the
TX currents, against docs/layout.md's limits (want >= 2x margin).

The VAPWR and VGND meshes (sim/power/mesh.py, 0.5 um) solved in ngspice with the drivers' measured
currents (docs/layout.md: per arm 6.65 mA average on VAPWR, 2.29 mA on VSS; both arms on) spread over
each driver's terminals, every node saved. Each mesh resistor's current: metal links -> mA per um of
width (the link's cell pitch x coverage), via links -> mA per cut (the cut R / the link R). Average
currents are checked against the DC limits (the supply nets: docs/layout.md uses the average there).

    python3 sim/power/em.py [A|B]
"""
import collections
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import common  # noqa: E402
import ir_rx  # noqa: E402
import r_mesh  # noqa: E402
from rawread import read_raw  # noqa: E402

LAYERS = ['li', 'm1', 'm2', 'm3', 'm4', 'm5']
RS = {'li': 12.8, 'm1': 0.125, 'm2': 0.125, 'm3': 0.047, 'm4': 0.047, 'm5': 0.0285}
LIM_W = {'m1': 2.8, 'm2': 2.8, 'm3': 6.8, 'm4': 6.8, 'm5': 10.17}          # mA/um DC
CUTS = {0: ('mcon', 9.3, 0.36), 1: ('via1', 4.5, 0.29), 2: ('via2', 3.41, 0.48), 3: ('via3', 3.41, 0.48),
        4: ('via4', 0.38, 2.49)}                                             # (name, R/cut, mA/cut)


def main(case):
    pr = common.probes(case)
    xy = common.node_xy(case)
    p = 0.5
    for net in ('VAPWR', 'VGND'):
        meta, lines = r_mesh.load_mesh(case, net)
        lines, alive, _ = r_mesh.connected(lines, net)
        inj = collections.Counter()
        for b in ('tx_drv_p', 'tx_drv_n'):
            ns = [r_mesh.place(meta, xy[t], alive) for t in pr[b][net] if t in xy]
            ns = [n for n in ns if n]
            for n in ns:
                inj[n] += ir_rx.TX[net]['avg'] / len(ns) * (1 if net == 'VAPWR' else -1)
        name = f'em_{case}_{net}'
        deck = [f'* {name}'] + lines + [f'Vport {net} 0 0']
        deck += [f'I{k} {n} 0 dc {i:.6e}' for k, (n, i) in enumerate(inj.items())]
        deck += ['.control', 'op', f'write {name}.raw', '.endc', '.end']
        open(os.path.join(common.B, name + '.spice'), 'w').write('\n'.join(deck) + '\n')
        subprocess.run([common.OSIC, 'bash', '-c', f'cd build/power && ngspice -b {name}.spice > {name}.log 2>&1'],
                       cwd=common.ROOT)
        v = read_raw(os.path.join(common.B, name + '.raw'))[0]['vars']
        V = lambda n: 0.0 if n == net else float(v[f'v({n.lower()})'][0])
        worst = {}
        for ln in lines:
            t = ln.split()
            if not t or t[0][0] != 'R' or net in (t[1], t[2]):
                continue
            ka = int(re.match(r'm(\d)_', t[1]).group(1)); kb = int(re.match(r'm(\d)_', t[2]).group(1))
            r = float(t[3]); i = abs(V(t[1]) - V(t[2])) / r * 1e3          # mA
            if ka == kb:
                lay = LAYERS[ka]
                if lay not in LIM_W:
                    continue
                w = RS[lay] / r * p                                          # coverage x pitch
                key, val, lim = lay, i / w, LIM_W[lay]
            else:
                cn, rc, lim = CUTS[min(ka, kb)]
                ncut = rc / r
                key, val = cn, i / ncut
            if key not in worst or val / lim > worst[key][0]:
                xa = t[1].split('_')
                worst[key] = (val / lim, val, lim, meta['x0'] + int(xa[1]) * p, meta['y0'] + int(xa[2]) * p)
        print(f'case {case} {net}, TX both arms at their average current ({ir_rx.TX[net]["avg"] * 2e3:.1f} mA):')
        for k, (frac, val, lim, x, y) in sorted(worst.items(), key=lambda kv: -kv[1][0]):
            unit = 'mA/um' if k in LIM_W else 'mA/cut'
            flag = '  <-- under 2x margin' if frac > 0.5 else ''
            if k in ('mcon', 'via1') and frac > 0.5:
                # each device terminal's current goes in at one mesh point, so the cuts next to it
                # read high: in the cell the current spreads along the finger (tx_drv stage 5:
                # 22 mcon per source strip, ~0.034 mA/cut at the average current, ~9 %)
                flag += ' (point injection: reads high, see docs/power.md)'
            print(f'  {k:5s} worst {val:7.3f} {unit} (limit {lim}, {frac * 100:5.1f} %) at ({x:.1f}, {y:.1f}){flag}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'A')
