"""TX keyed, the RX's supplies watched (benchmark step 5, transient).

The stitched tile (sim/power/stitch.py, 1 um mesh, TT PDN model) in xschem/tb_radio_analog.sch's TX
run (tx_en keyed at 5 ns), with the RX biased on as well (ven_rx = 1.8) so its blocks' local
supplies are what they would see. Saved: each block's local VDD and VSS mesh node (as z_ac.py),
det / lpf / avg / vcm, the gate outputs, the drivers' outputs.

    python3 sim/power/tran_tx.py [A|B] [stop_ns]       (default A, 30)
Writes build/power/tran_tx_<case>.raw and prints the bounce (peak-to-peak and RMS over the last
10 ns, 434 MHz component) at each block.
"""
import json
import os
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import common  # noqa: E402
import stitch  # noqa: E402
import z_ac  # noqa: E402
from rawread import read_raw  # noqa: E402


def main(case, stop):
    txt, term, _ = stitch.tile_text(case)
    pr = common.probes(case)
    xy = common.node_xy(case)
    loc = {}
    for b, sup in z_ac.BLOCKS.items():
        if b in pr and sup in pr[b] and 'VGND' in pr[b]:
            loc[b] = (z_ac.local(pr[b][sup], term, xy), z_ac.local(pr[b]['VGND'], term, xy))
    src = open(os.path.join(common.ROOT, 'build', 'tb_radio_analog.spice')).read()
    deck, n = re.subn(r'^\.subckt\s+radio_analog\s.*?^\.ends\b[^\n]*\n', '', src, flags=re.S | re.M | re.I)
    assert n == 1
    deck = stitch.pdn_model(deck)
    x = lambda nd: f'xana.x1.{nd}'.lower()
    save = sorted({x(nd) for d, s in loc.values() for nd in (d, s)} | {x(s) for s in z_ac.SIG} |
                  {'vdpwr', 'vapwr', 'vg_chip', 'tx_p', 'tx_n'})
    name = f'tran_tx_{case}'
    ctl = ['.control', 'alterparam ven_tx = 1.8', 'alterparam ven_rx = 1.8', 'reset',
           f'tran 2p {stop}n 0', f'write {name}.raw', '.endc']
    deck = re.sub(r'^\.control.*?^\.endc', '\n'.join(ctl), deck, flags=re.S | re.M)
    deck = re.sub(r'^\.save .*$', '.save ' + ' '.join(f'v({nd})' for nd in save) + ' i(vdpwr) i(va)', deck, flags=re.M)
    deck = re.sub(r'^\.end\s*$', txt + '.end', deck, flags=re.M)
    open(os.path.join(common.B, name + '.spice'), 'w').write(deck)
    json.dump(loc, open(os.path.join(common.B, name + '_loc.json'), 'w'))
    subprocess.run([common.OSIC, 'bash', '-c', f'cd build/power && ngspice -b {name}.spice > {name}.log 2>&1'],
                   cwd=common.ROOT)
    analyse(case, stop)


def analyse(case, stop):
    name = f'tran_tx_{case}'
    loc = json.load(open(os.path.join(common.B, name + '_loc.json')))
    p = read_raw(os.path.join(common.B, name + '.raw'))[0]['vars']
    t = np.real(p['time'])
    x = lambda nd: f'v(xana.x1.{nd.lower()})'
    m = t > (stop - 10) * 1e-9
    tt = t[m]

    def comp(v, f=433.92e6):
        # amplitude of the f component over the window (uneven steps: least squares)
        A = np.vstack([np.cos(2 * np.pi * f * tt), np.sin(2 * np.pi * f * tt), np.ones_like(tt)]).T
        c, *_ = np.linalg.lstsq(A, v, rcond=None)
        return float(np.hypot(c[0], c[1]))
    print(f'case {case}: TX keyed (RX on), last 10 ns: local VDD-VSS and VSS (to board ground) at each block, mV')
    print(f'{"block":10s} {"dd p-p":>8s} {"dd 434M":>8s} {"ss p-p":>8s} {"ss 434M":>8s} {"dd mean":>8s}')
    for b, (d, s) in loc.items():
        vd, vs = np.real(p[x(d)])[m], np.real(p[x(s)])[m]
        dd = vd - vs
        print(f'{b:10s} {np.ptp(dd) * 1e3:8.2f} {comp(dd) * 1e3:8.2f} {np.ptp(vs) * 1e3:8.2f} {comp(vs) * 1e3:8.2f} {dd.mean():8.4f}')
    for sg in z_ac.SIG:
        v = np.real(p[x(sg)])[m]
        print(f'{sg:10s} p-p {np.ptp(v) * 1e3:8.2f} mV, 434 MHz {comp(v) * 1e3:8.2f} mV, mean {v.mean():.4f} V')
    for n in ('vdpwr', 'vapwr', 'vg_chip'):
        v = np.real(p[f'v({n})'])[m]
        print(f'{n:10s} mean {v.mean():.4f} V  p-p {np.ptp(v) * 1e3:.1f} mV')


if __name__ == '__main__':
    case = sys.argv[1] if len(sys.argv) > 1 else 'A'
    stop = float(sys.argv[2]) if len(sys.argv) > 2 else 30
    if len(sys.argv) > 3 and sys.argv[3] == '--no-run':
        analyse(case, stop)
    else:
        main(case, stop)
