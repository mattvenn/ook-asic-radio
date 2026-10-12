"""
End-to-end check of the laid-out tile: xschem/tb_radio_analog.sch (radio_analog with pad models,
both dipoles, the debug probe, the digital interface from sources) with radio_analog taken from
the schematic or from the extracted tile (layout/pex_tile.sh -> layout/pex/radio_analog_<mode>.spice).

Prints the deck's RESULT lines (RX operating point, all-off current, det at -60 dBm) and the TX
run's frequency / power into the 73 ohm dipole / supply currents.

    python3 sim/top/tb_tile.py sch lvs [c] [rc]       (each one ~3 min, more with parasitics)
    python3 sim/top/tb_tile.py --no-run lvs           (analyse existing raws)
    python3 sim/top/tb_tile.py --vdd=1.71 --vapwr=3.0 --corner=fs --temp=50 sch c
                                                      (supplies / MOS corner / temperature; files
                                                       tb_tile_<mode>_<tag>, e.g. _v171_a30_fs_50)
NT=1 in the environment sets ngspice's threads (default: .spiceinit's 8).
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
    # internal nodes the deck measures: one level down in the extracted tile (the wrapper's X1),
    # named by the route labels (layout/gen/top_nets.py)
    deck = re.sub(r'xana\.(vcm|det|lpf|trim)\b', r'xana.x1.\1', deck)
    # The tile's digital-pin stubs (nc_* in the wrapper: the macro isn't extracted) carry only
    # wiring C in the c / rc netlists: no DC path, so the op fails (singular matrix), ngspice falls
    # back to a transient op and returns unsettled nodes (lpf 0.89 V, off current +0.7 uA).
    # Tie each one to VGND through 1 G in a copy of the netlist.
    net = open(pex).read()
    wrap = re.search(r'^\.subckt\s+radio_analog\s.*?^\.ends\b', net, re.S | re.M)
    ncs = sorted(set(re.findall(r'\b(nc_\w+)', wrap.group(0))))
    ties = ''.join(f'Rtie_{n} {n} VGND 1G\n' for n in ncs)
    end = wrap.end() - len('.ends')
    open(os.path.join(B, f'radio_analog_{mode}_tied.spice'), 'w').write(net[:end] + ties + net[end:])
    inc = f'.include radio_analog_{mode}_tied.spice\n'
    return re.sub(r'^\.end\s*$', inc + '.end', deck, flags=re.M)


COND = {'vdd': 1.8, 'vapwr': 3.3, 'corner': 'tt', 'temp': 27.0}


def suffix():
    t = ''
    if (COND['vdd'], COND['vapwr']) != (1.8, 3.3):
        t += f'_v{COND["vdd"]:g}_a{COND["vapwr"]:g}'.replace('.', '')
    if (COND['corner'], COND['temp']) != ('tt', 27.0):
        t += f'_{COND["corner"]}_{COND["temp"]:g}'
    return t


def conditions(deck, mode):
    """COND applied to a deck: supplies, the .lib corner, .temp, raw names."""
    deck, n = re.subn(r'^VDPWR VDPWR GND dc 1\.8 ', f'VDPWR VDPWR GND dc {COND["vdd"]:g} ', deck, flags=re.M)
    deck, m = re.subn(r'^VA VAPWR GND 3\.3$', f'VA VAPWR GND {COND["vapwr"]:g}', deck, flags=re.M)
    assert n == m == 1, (n, m)
    deck = re.sub(r'(sky130\.lib\.spice) tt\b', rf'\1 {COND["corner"]}', deck)
    deck = re.sub(r'^\.end\s*$', f'.temp {COND["temp"]:g}\n.end', deck, count=1, flags=re.M)
    deck = deck.replace(f'write tb_tile_{mode}_tx.raw', f'write tb_tile_{mode}{suffix()}_tx.raw')
    if os.environ.get('NT'):
        deck = re.sub(r'^\.control$', f'.control\nset num_threads={os.environ["NT"]}', deck, count=1, flags=re.M)
    return deck


def run(src, mode):
    name = f'tb_tile_{mode}{suffix()}'
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(conditions(deck_for(src, mode), mode))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    res = [ln for ln in log.splitlines() if ln.startswith('RESULT')]
    if not res:
        print(f'{mode}: no RESULT lines; tail of build/{name}.log:')
        print('\n'.join(log.splitlines()[-15:]))
    return res


def analyse(mode):
    path = os.path.join(B, f'tb_tile_{mode}{suffix()}_tx.raw')
    if not os.path.exists(path):
        print(f'{mode}: no TX raw')
        return
    v = dict(read_raw(path)[0]['vars'])
    v['v(ant_p)'], v['v(ant_n)'], v['i(vd)'] = v['v(ant_tx_p)'], v['v(ant_tx_n)'], v['i(vdpwr)']
    try:
        m = ring_metrics(v, 5e-9, 60e-9, drv=('tx_p', 'tx_n'))
    except IndexError:          # an output never toggles (e.g. an enable level shifter stuck)
        print(f'{mode}{suffix()} TX: FAIL, an output arm never toggles', flush=True)
        return
    print(f'{mode}{suffix()} TX: ' + fmt_ring(m), flush=True)


if __name__ == '__main__':
    args = sys.argv[1:]
    modes = [a for a in args if not a.startswith('--')] or ['sch', 'lvs']
    for a in args:
        k = a[2:].split('=')[0]
        if '=' in a and k in COND:
            COND[k] = a.split('=')[1] if k == 'corner' else float(a.split('=')[1])
    src = None if '--no-run' in args else netlist()
    for md in modes:
        if src is not None:
            for ln in run(src, md):
                print(md, ln, flush=True)
        analyse(md)
