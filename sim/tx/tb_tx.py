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
    python sim/tx/tb_tx.py --pex --pex-ring tt   (tx_ring extracted too; files *_pexr)
    python sim/tx/tb_tx.py --vdd=1.71 --vapwr=3.0 tt   (supplies; files *_v171_a30)
NT=1 in the environment sets ngspice's threads (default: .spiceinit's 8).
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
SUPPLY = {'vdd': 1.8, 'vapwr': 3.3}


def tag(corner):
    sup = ''
    if SUPPLY != {'vdd': 1.8, 'vapwr': 3.3}:
        sup = f'_v{SUPPLY["vdd"]:g}_a{SUPPLY["vapwr"]:g}'.replace('.', '')
    return corner + ('_pex' if PEX else '') + ('r' if 'tx_ring' in PEX else '') + sup


def run(corner, src):
    deck = re.sub(r'(sky130\.lib\.spice) tt', rf'\1 {corner}', src)
    deck = re.sub(r'write tb_tx_(\w+)\.raw', rf'write tb_tx_{tag(corner)}_\1.raw', deck)
    if PEX:
        deck = swap(deck, PEX)
    if 'tx_ring' in PEX:        # the extracted ring has no cw parameter
        deck, n = re.subn(r'^(xring .* tx_ring) cw=\S+', r'\1', deck, flags=re.M)
        assert n == 1
    deck, n = re.subn(r'^VA VAPWR GND 3\.3$', f'VA VAPWR GND {SUPPLY["vapwr"]:g}', deck, flags=re.M)
    deck, m = re.subn(r'^VD VDPWR GND 1\.8$', f'VD VDPWR GND {SUPPLY["vdd"]:g}', deck, flags=re.M)
    assert n == m == 1, (n, m)
    if os.environ.get('NT'):
        deck = re.sub(r'^\.control$', f'.control\nset num_threads={os.environ["NT"]}', deck, count=1, flags=re.M)
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
        try:
            m = ring_metrics(v, TON, TOFF, drv=('out_p', 'out_n'))
        except IndexError:          # an output never toggles (e.g. an enable level shifter stuck)
            print(f'{tag(corner)} {vn}: FAIL, an output arm never toggles', flush=True)
            out[vn] = None
            continue
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
    if '--pex-ring' in args:
        PEX.append('tx_ring')
    for a in args:
        if a.startswith('--vdd=') or a.startswith('--vapwr='):
            k, x = a[2:].split('=')
            SUPPLY[k] = float(x)
    corners = [a for a in args if not a.startswith('--')] or ['tt']
    src = netlist() if dorun else None
    for c in corners:
        if dorun:
            for line in run(c, src):
                print(c, line)
        analyse(c)
