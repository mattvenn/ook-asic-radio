"""
Run and analyse xschem/tb_tx.sch (the TX chain as xschem blocks, from
xschem/gen/tx.py) at one or more corners, and compare with the raw-spice
first pass (sim/tx/tx_explore.py ring ...).

Per corner: netlist once (tt), rewrite the .lib corner, run both cases of the
tb (both arms keyed; single-ended with en_n = 0), then print frequency, power
into the dipole, on/off times, supply currents, and the parked (off) arm
levels.

    python sim/tx/tb_tx.py [corners...]          (default tt)
    python sim/tx/tb_tx.py --no-run tt           (analyse existing raws)
    python sim/tx/tb_tx.py --pex tt              (tx_drv from its extracted layout,
                                                  layout/pex/tx_drv.spice; files *_pex)
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from rawread import read_raw
from tx_explore import fmt_ring, ring_metrics
from pexswap import swap

import numpy as np

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.environ.get('OSIC', os.path.join(ROOT, 'tools', 'osic'))
TON, TOFF = 5e-9, 60e-9


def netlist():
    subprocess.run([OSIC, 'bash', '-c', 'xschem -n -s -q -o build xschem/tb_tx.sch'], cwd=ROOT,
                   capture_output=True)
    src = open(os.path.join(B, 'tb_tx.spice')).read()
    if 'IS MISSING' in src:
        sys.exit('tb_tx.spice: IS MISSING in netlist')
    return src


PEX = []    # blocks to take from their extracted layouts (--pex)


def tag(corner):
    return corner + ('_pex' if PEX else '')


def run(corner, src):
    deck = re.sub(r'(sky130\.lib\.spice) tt', rf'\1 {corner}', src)
    deck = re.sub(r'write tb_tx_(\w+)\.raw', rf'write tb_tx_{tag(corner)}_\1.raw', deck)
    if PEX:
        deck = swap(deck, PEX)
    name = f'tb_tx_{tag(corner)}'
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck)
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    return [line for line in log.splitlines() if line.startswith('RESULT')]


def analyse(corner):
    out = {}
    for vn in ('ab', 'se'):
        path = os.path.join(B, f'tb_tx_{tag(corner)}_{vn}.raw')
        v = read_raw(path)[0]['vars']
        m = ring_metrics(v, TON, TOFF, drv=('out_p', 'out_n'))
        t = np.real(v['time'])
        at = lambda k, x: float(np.interp(x, t, np.real(v[k])))
        m['park'] = (at('v(out_p)', 79e-9), at('v(out_n)', 79e-9))
        m['idle'] = (at('v(out_p)', 4e-9), at('v(out_n)', 4e-9))
        out[vn] = m
        label = 'antiphase   ' if vn == 'ab' else 'single-ended'
        print(f'{tag(corner)} {label}: ' + fmt_ring(m) +
              f'; arms before/after key: p {m["idle"][0]:.2f}/{m["park"][0]:.2f} V, '
              f'n {m["idle"][1]:.2f}/{m["park"][1]:.2f} V', flush=True)
    return out


if __name__ == '__main__':
    args = sys.argv[1:]
    dorun = '--no-run' not in args
    if '--pex' in args:
        PEX.append('tx_drv')
    corners = [a for a in args if not a.startswith('--')] or ['tt']
    src = netlist() if dorun else None
    for c in corners:
        if dorun:
            for line in run(c, src):
                print(c, line)
        analyse(c)
