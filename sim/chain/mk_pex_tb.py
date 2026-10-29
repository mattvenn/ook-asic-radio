# usage: python3 sim/chain/mk_pex_tb.py build/real/tb_chain.spice layout/pex/lna_chain.spice build/pexsim/tb_chain.spice
# tb_chain.spice with the lna_chain subckt replaced by the extracted one (layout/pex/lna_chain.spice)
import re, sys
src, pex, out = sys.argv[1:4]
s = open(src).read().replace('\n+', ' ')
s = re.sub(r'^\.subckt lna_chain\s.*?^\.ends[^\n]*\n', open(pex).read() + '\n', s, flags=re.S | re.M)
for c in ('amp_dp', 'amp_dpc', 'lna_shunt'):
    s = re.sub(rf'^\.subckt {c}\s.*?^\.ends[^\n]*\n', '', s, flags=re.S | re.M)
s = re.sub(r'^(x1 .*? lna_chain)\b.*$', r'\1', s, flags=re.M)
open(out, 'w').write(s)
