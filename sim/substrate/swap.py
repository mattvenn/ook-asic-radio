# Copy a stability.sh deck with its lna_chain subckt replaced: python3 swap.py <deck> <lna_chain netlist> <out deck>
import sys
src = open(sys.argv[1]).read().split('\n'); new = open(sys.argv[2]).read().rstrip()
out, skip = [], False
for ln in src:
    if ln.startswith('.subckt lna_chain '): skip = True; continue
    if skip:
        if ln.startswith('.ends'): skip = False; out.append(new)
        continue
    out.append(ln)
open(sys.argv[3], 'w').write('\n'.join(out))
