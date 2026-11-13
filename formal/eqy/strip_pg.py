#!/usr/bin/env python3
"""Strip the power pins from a netlist (VPWR / VGND ports and declarations, the cells'
VPWR / VGND / VPB / VNB connections). With --canon, print a canonical form instead (one
statement per line, declarations and cell instances sorted), for comparing two netlists.
Usage: strip_pg.py [--canon] netlist.v"""
import re, sys

canon = '--canon' in sys.argv
txt = open(sys.argv[-1]).read()
txt = re.sub(r'\n\s*(VPWR|VGND),', '', txt)                       # module port list
txt = re.sub(r'\n\s*inout\s+(VPWR|VGND);', '', txt)               # port declarations
txt = re.sub(r'\.(VPWR|VGND|VPB|VNB)\((VPWR|VGND)\)\s*,?\s*', '', txt)  # cell pins
txt = re.sub(r',(\s*)\)', r'\1)', txt)                            # a trailing comma left behind
if not canon:
    sys.stdout.write(txt)
    sys.exit()
stmts = [' '.join(s.split()) for s in txt.split(';')]
stmts = [re.sub(r'\( ', '(', re.sub(r' \)', ')', s)) for s in stmts if s]
head = [s for s in stmts if s.startswith('module')]
body = sorted(s for s in stmts if not s.startswith('module'))
print('\n'.join(head + body))
