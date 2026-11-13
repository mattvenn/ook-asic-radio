#!/usr/bin/env python3
"""Write eqy's [match] and [partition] sections: match only the ports, every name of each flop's output,
and the clock-gate (black-box) cells and their outputs. Internal combinational nets are
left unmatched, so eqy doesn't cut there: a cut makes e.g. rx_en and role_tx independent
inputs, though rx_en = ~role_tx, and the partitions that use one or the other then fail.
Usage: match.py gold.json gate.json > match.txt   (the designs after the [gold] / [gate] scripts)
Only names present on both sides are listed (the rest would be eqy warnings)."""
import json, sys, collections

mod = json.load(open(sys.argv[1]))['modules']['radio_digital']
gate = json.load(open(sys.argv[2]))['modules']['radio_digital']
gate_ids = set(gate['netnames']) | set(gate['cells'])
names = collections.defaultdict(set)          # bit -> every public name of it
for n, d in mod['netnames'].items():
    if n.startswith('$'):
        continue
    bits = d['bits']
    for i, b in enumerate(bits):
        names[b].add(n if len(bits) == 1 else f'{n}[{i}]')

keep = set(mod['ports'])
cells = []
n_ff = 0
for cname, c in mod['cells'].items():
    if c['type'] == '$dff':
        for b in c['connections']['Q']:
            keep |= {x.split('[')[0] if x.split('[')[0] in mod['ports'] else x for x in names[b]}
            n_ff += 1
    elif not c['type'].startswith('$'):        # black box (the clock gates)
        cells.append(cname)
        for p, sig in c['connections'].items():
            if c['port_directions'][p] == 'output':
                for b in sig:
                    keep |= names[b]
    elif c['type'] not in ('$scopeinfo',) and 'Q' in c['connections']:
        sys.exit(f'unexpected state element {cname} ({c["type"]})')

both = sorted(n for n in keep | set(cells) if n in gate_ids)
print('[match sky130_fd_sc_hd__dlclkp_1]\ngold-match *\n')
print('[match radio_digital]\nnodefault')
for n in both:
    # eqy patterns: escape the brackets of bit names
    print('gold-match', n.replace('[', '\\[').replace(']', '\\]'))
# Output ports are always matched, so eqy cuts there too. A combinational output that the
# design also reads inside (rx_en = ~role_tx; tx_en, the raw-mode mux) then becomes a free
# input to the logic that reads it, while the netlist computes that logic from role_tx
# directly: amend those partitions with the port's driver logic instead.
qbits = {b for c in mod['cells'].values() if c['type'] == '$dff' for b in c['connections']['Q']}
comb_out = sorted(p for p, d in mod['ports'].items()
                  if d['direction'] == 'output' and not all(b in qbits for b in d['bits']))
print('\n[partition radio_digital]')
for p in comb_out:
    print('amend', p)
print(f'# combinational outputs (amended): {" ".join(comb_out)}', file=sys.stderr)

ffb = [b for c in mod['cells'].values() if c['type'] == '$dff' for b in c['connections']['Q']]
n_named = sum(1 for b in ffb if any((x.split('[')[0] if x.split('[')[0] in mod['ports'] else x) in gate_ids for x in names[b]))
print(f'# gold: {n_ff} flop bits, {n_named} with a name in the netlist; {len(cells)} clock gates; '
      f'{len(both)} names matched', file=sys.stderr)
