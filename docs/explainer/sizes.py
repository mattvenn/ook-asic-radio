"""Write docs/explainer/sizes.json: the numbers on each block page.

  analog:  every layout/*.gds top cell's bbox (um^2), the tile's, and the tile's analog total: each block
           as many times as layout/floorplan/floorplan.json places it (as layout/gen/top.py does).
  digital: standard cells per RTL module (yosys, hierarchy kept, sky130_fd_sc_hd tt),
           and the hardened macro's cells by kind (macros/radio_digital/radio_digital.nl.v).

    tools/osic docs/explainer/sizes.py      (tools/osic-mac on the Mac; needs klayout + yosys)
"""
import glob
import json
import os
import re
import subprocess
import tempfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
LIB = os.path.join(os.environ.get('PDK_ROOT', '/foss/pdks'), os.environ.get('PDK', 'sky130A'),
                   'libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib')
PHYS = ('fill', 'decap', 'tapvpwrvgnd', 'diode')   # cells with no logic: not counted as "used"


def bbox(path):
    import klayout.db as kdb
    ly = kdb.Layout()
    ly.read(path)
    b = ly.top_cell().dbbox()
    return {'w': round(b.width(), 2), 'h': round(b.height(), 2), 'um2': round(b.width() * b.height())}


def analog():
    out = {os.path.basename(p)[:-4]: bbox(p) for p in sorted(glob.glob(os.path.join(ROOT, 'layout', '*.gds')))}
    out['tile'] = bbox(os.path.join(ROOT, 'gds', 'tt_um_mattvenn_radio.gds'))
    return out


def tile_totals(a):
    fp = json.load(open(os.path.join(ROOT, 'layout', 'floorplan', 'floorplan.json')))
    n = Counter()
    for b in fp['blocks']:
        cell = f"{b['cell']}_p{b['part']}" if b['cell'].startswith('decap_') else b['cell']
        if cell in a:   # (the macro is digital; decap parts with no GDS are dropped by top.py)
            n[cell] += 1
    dec = sum(a[c]['um2'] * k for c, k in n.items() if c.startswith('decap_'))
    return {'instances': dict(n), 'circuits_um2': sum(a[c]['um2'] * k for c, k in n.items()) - dec, 'decap_um2': dec}


def synth():
    """Cells per module, hierarchy kept (LibreLane flattens, so its count differs slightly)."""
    rtl = sorted(glob.glob(os.path.join(ROOT, 'verilog', 'rtl', '*.v')))
    with tempfile.TemporaryDirectory() as tmp:
        js = os.path.join(tmp, 'stat.json')
        ys = (f'read_liberty -lib {LIB}; read_verilog {" ".join(rtl)}; synth -top radio_digital; '
              f'dfflibmap -liberty {LIB}; abc -liberty {LIB}; opt_clean; tee -q -o {js} stat -json')
        subprocess.run(['yosys', '-q', '-p', ys], check=True)
        mods = json.load(open(js))['modules']
    # own cells only (sub-module instances are not std cells); add each sub-module's cells in
    own = {m.lstrip('\\'): {c: n for c, n in v['num_cells_by_type'].items()} for m, v in mods.items()}
    def total(m):
        return sum(n if c.startswith('sky130') else n * total(c.lstrip('\\')) for c, n in own[m].items())
    return {m: total(m) for m in own}


def macro():
    nl = open(os.path.join(ROOT, 'macros', 'radio_digital', 'radio_digital.nl.v')).read()
    cells = Counter(re.sub(r'_\d+$', '', c) for c in re.findall(r'^\s*sky130_fd_sc_hd__(\w+)\s', nl, re.M))
    phys = sum(n for c, n in cells.items() if c.startswith(PHYS))
    hold = cells['dlygate4sd3']   # the resizer's hold buffers
    return {'cells': sum(cells.values()) - phys, 'hold_buffers': hold, 'physical': phys,
            'size': bbox(os.path.join(ROOT, 'macros', 'radio_digital', 'radio_digital.gds'))}


if __name__ == '__main__':
    a = analog()
    d = {'analog': a, 'tile': tile_totals(a), 'digital': synth(), 'macro': macro()}
    with open(os.path.join(HERE, 'sizes.json'), 'w') as f:
        json.dump(d, f, indent=1)
    print(json.dumps(d, indent=1))
