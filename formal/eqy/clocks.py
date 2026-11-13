#!/usr/bin/env python3
"""Clock check alongside eqy. eqy's strategies treat every flop as clocked by one implicit
global clock, so they never look at which clock net a flop is on. This checks that: each flop
(found by its output name, as eqy matches it) must be clocked from the same source in the RTL
and in the netlist: the clk port directly (the netlist's clock-tree buffers are gone after
flattening), or the output of the same clock-gate instance.
Usage: clocks.py gold.json gate.json"""
import json, sys, collections

def load(path):
    mod = json.load(open(path))['modules']['radio_digital']
    names = collections.defaultdict(set)
    for n, d in mod['netnames'].items():
        if n.startswith('$'):
            continue
        for i, b in enumerate(d['bits']):
            names[b].add(n if len(d['bits']) == 1 else f'{n}[{i}]')
    src = {}                                   # bit -> clock source
    for b in mod['ports']['clk']['bits']:
        src[b] = 'clk'
    for cn, c in mod['cells'].items():
        if c['type'] == 'sky130_fd_sc_hd__dlclkp_1':
            src[c['connections']['GCLK'][0]] = cn
    flops = {}                                 # output name -> clock source
    load.other = getattr(load, 'other', 0)
    for cn, c in mod['cells'].items():
        t = c['type']
        if t in ('$dff', '$_DFF_P_') or t.startswith('$_DFF_'):
            q, clk = c['connections']['Q'], c['connections']['CLK'][0]
            if t not in ('$dff', '$_DFF_P_') or c.get('parameters', {}).get('CLK_POLARITY', '1') not in ('1', 1, '00000000000000000000000000000001'):
                sys.exit(f'{path}: unexpected flop {cn} {t}')
            s = src.get(clk, f'other net {sorted(names[clk]) or clk}')
            load.other += s not in ('clk',) and not s.startswith('u_corr.')
            for b in q:
                for n in names[b]:
                    flops[n] = s
    return flops

gold, gate = load(sys.argv[1]), load(sys.argv[2])
common = sorted(set(gold) & set(gate))
bad = [(n, gold[n], gate[n]) for n in common if gold[n] != gate[n]]
by = collections.Counter(gold[n] for n in common)
print(f'clocks: {len(common)} flop output names on both sides; sources {dict(by)}; '
      f'{len(bad)} mismatched, {load.other} flops on another clock net')
for b in bad[:20]:
    print('  mismatch:', *b)
sys.exit(1 if bad or load.other or not common else 0)
