# tb_chain.spice (build/real, xschem) with the schematic lna_chain replaced by an extracted one:
#   python3 mkbench.py <dir> <lna_chain netlist>   -> <dir>/tb_chain.spice
import sys, os, re
d, net = sys.argv[1], sys.argv[2]
D = os.path.dirname(os.path.abspath(__file__))
src = open(f'{D}/../real/tb_chain.spice').read().split('\n')
out, skip, drop_cont = [], False, False
for ln in src:
    if drop_cont:
        if ln.startswith('+'): continue
        drop_cont = False
    if ln.startswith('.subckt lna_chain '): skip = True; continue
    if skip:
        if ln.startswith('.ends'): skip = False; out.append(open(net).read().rstrip())
        continue
    if ln.startswith('x1 ') and ' lna_chain' in ln:
        ln = ln[:ln.index(' lna_chain') + len(' lna_chain')]; drop_cont = True
    out.append(ln)
os.makedirs(d, exist_ok=True)
open(f'{d}/tb_chain.spice', 'w').write('\n'.join(out))
print(d, 'ok')
