"""
End-to-end check of the laid-out tile: xschem/tb_radio_analog.sch (radio_analog with pad models,
both dipoles, the debug probe, the digital interface from sources) with radio_analog taken from
the schematic or from the extracted tile (layout/pex_tile.sh -> layout/pex/radio_analog_<mode>.spice).

Prints the deck's RESULT lines (RX operating point, all-off current, det at -60 dBm) and the TX
run's frequency / power into the 73 ohm dipole / supply currents.

    python3 sim/top/tb_tile.py sch lvs [c] [rc]       (each one ~3 min, more with parasitics)
    python3 sim/top/tb_tile.py --no-run lvs           (analyse existing raws)
Runs ngspice in build/ through tools/osic-mac (set OSIC=... for the Linux host). One at a time.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'sim', 'tx'))
from rawread import read_raw            # noqa: E402
from tx_explore import ring_metrics, fmt_ring   # noqa: E402

B = os.path.join(ROOT, 'build')
OSIC = os.environ.get('OSIC', os.path.join(ROOT, 'tools', 'osic-mac'))


def netlist():
    subprocess.run([OSIC, 'bash', '-c', 'xschem -n -s -q -o build xschem/tb_radio_analog.sch'], cwd=ROOT,
                   capture_output=True)
    src = open(os.path.join(B, 'tb_radio_analog.spice')).read()
    if 'IS MISSING' in src:
        raise RuntimeError('netlist has missing symbols')
    return src


def deck_for(src, mode):
    deck = re.sub(r'write tb_radio_analog_tx\.raw', f'write tb_tile_{mode}_tx.raw', src)
    if mode == 'sch':
        return deck
    pex = os.path.join(ROOT, 'layout', 'pex', f'radio_analog_{mode}.spice')
    if not os.path.exists(pex):
        raise FileNotFoundError(f'{pex}: run tools/osic-mac bash layout/pex_tile.sh {mode}')
    pat = re.compile(r'^\.subckt\s+radio_analog\s.*?^\.ends\b[^\n]*\n', re.S | re.M | re.I)
    deck, n = pat.subn('', deck)
    assert n == 1, n
    inc = f'.include ../layout/pex/radio_analog_{mode}.spice\n'
    return re.sub(r'^\.end\s*$', inc + '.end', deck, flags=re.M)


def run(src, mode):
    name = f'tb_tile_{mode}'
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck_for(src, mode))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    res = [ln for ln in log.splitlines() if ln.startswith('RESULT')]
    if not res:
        print(f'{mode}: no RESULT lines; tail of build/{name}.log:')
        print('\n'.join(log.splitlines()[-15:]))
    return res


def analyse(mode):
    path = os.path.join(B, f'tb_tile_{mode}_tx.raw')
    if not os.path.exists(path):
        print(f'{mode}: no TX raw')
        return
    v = dict(read_raw(path)[0]['vars'])
    v['v(ant_p)'], v['v(ant_n)'], v['i(vd)'] = v['v(ant_tx_p)'], v['v(ant_tx_n)'], v['i(vdpwr)']
    m = ring_metrics(v, 5e-9, 60e-9, drv=('tx_p', 'tx_n'))
    print(f'{mode} TX: ' + fmt_ring(m), flush=True)


if __name__ == '__main__':
    args = sys.argv[1:]
    modes = [a for a in args if not a.startswith('--')] or ['sch', 'lvs']
    src = None if '--no-run' in args else netlist()
    for md in modes:
        if src is not None:
            for ln in run(src, md):
                print(md, ln, flush=True)
        analyse(md)
