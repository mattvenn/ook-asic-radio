# Deliberate antenna violation, to prove layout/check.sh's antenna check fires:
# a 0.5 x 0.42 um g5 gate on 300 um^2 of met1 (ratio ~1033 > 400).
#   tools/osic klayout -b -r layout/gen/ant_test.py && tools/osic bash layout/check.sh ant_test
# (expect "antenna count 1"; delete layout/ant_test.gds afterwards)
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, box, REPO   # noqa: E402

b = Block('ant_test')
f = Fet(b, 'n', 0.42, 0.5, nf=1, gate='top').commit()
p = f.pads[0]
b.rect('m1', box(p.left, p.bottom, p.left + 1.0, p.top + 300))
b.write(os.path.join(REPO, 'layout', 'ant_test.gds'))
