"""DC resistance from each block's local supply to the PDN (benchmark step 1), with ngspice on the
extracted supply metal only (build/power/ext_<case>/, sim/power/pex_power.sh).

For each supply net: its port (the power gate's output for VDPWR / VAPWR, the global grid for
VGND; the met5 stripes and via4s are in the extraction) is grounded, 1 A is shared equally between
the block's current-carrying terminals on that net, taken on the metal side of each device's own
terminal resistor (sim/power/common.py rail_probes), and their voltages are read: mean and worst = the block's R to the port. Add pdn.R_GATE (and the package) for
the R to the pad.

    python3 sim/power/r_dc.py [A|B]
Writes build/power/r_dc_<case>.json.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import common  # noqa: E402
from rawread import read_raw  # noqa: E402


def main(case):
    pr = common.rail_probes(case)
    rlines = common.r_only(case)
    res = {}
    for net in common.SUP:
        blks = [b for b in sorted(pr) if net in pr[b]]
        name = f'r_dc_{case}_{net}'
        deck = [f'* {name}: R from each block to the {net} port', '.options gmin=1e-12']
        deck += [ln for ln in rlines if common.supply_of(ln.split()[1]) == net]
        deck.append(f'Vport {net} 0 0')
        for b in blks:
            nodes = pr[b][net]
            deck.append(f".param ib_{b}=0")
            for k, n in enumerate(nodes):
                deck.append(f"I_{b}_{k} 0 {n} dc 'ib_{b}/{len(nodes)}'")
        save = sorted({n for b in blks for n in pr[b][net]})
        deck.append('.save ' + ' '.join(f'v({n})' for n in save))
        deck.append('.control')
        for b in blks:
            for b2 in blks:
                deck.append(f'alterparam ib_{b2}={1 if b2 == b else 0}')
            deck += ['reset', 'op', f'write {name}_{b}.raw', 'destroy all']
        deck += ['.endc', '.end']
        os.makedirs(common.B, exist_ok=True)
        open(os.path.join(common.B, name + '.spice'), 'w').write('\n'.join(deck) + '\n')
        subprocess.run([common.OSIC, 'bash', '-c', f'cd build/power && ngspice -b {name}.spice > {name}.log 2>&1'],
                       cwd=common.ROOT)
        for b in blks:
            v = read_raw(os.path.join(common.B, f'{name}_{b}.raw'))[0]['vars']
            vs = [float(v[f'v({n.lower()})'][0]) for n in pr[b][net]]
            res.setdefault(b, {})[net] = {'mean': sum(vs) / len(vs), 'max': max(vs), 'n': len(vs)}
    json.dump(res, open(os.path.join(common.B, f'r_dc_{case}.json'), 'w'), indent=1)
    print(f'case {case}: R (ohm) from each block\'s terminals to the port, mean / worst')
    print(f'{"block":12s} {"VDPWR":>14s} {"VAPWR":>14s} {"VGND":>14s}')
    for b in sorted(res):
        row = [f"{res[b][n]['mean']:6.2f} / {res[b][n]['max']:5.2f}" if n in res[b] else '' for n in common.SUP]
        print(f'{b:12s} ' + ' '.join(f'{c:>14s}' for c in row))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'A')
