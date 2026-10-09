"""Supply impedance at each block and TX -> RX coupling through the supplies (benchmark steps 4, 5).

xschem/tb_radio_analog.sch with radio_analog = the stitched tile (sim/power/stitch.py: magic's
devices and C, the supply mesh, the TT PDN outside), RX biased on (the testbench's op), antenna AC
off. Per block, a local VDD and VSS node: the mesh nodes of the block's supply terminals nearest
the middle of its terminals. For each block in turn a 1 A AC current is drawn from its VDD node into
its VSS node (ngspice `alter`, one AC sweep each):
  Z_dd = |V(vdd) - V(vss)|, the block's local supply impedance;
  Z_gnd = |V(vss)| to the board ground.
The TX drivers' runs also give the transfer to the RX: |V| at the RX blocks' supply nodes and at
det / lpf / avg / trim / vcm per A drawn at the driver (x 9.45 mA RMS per arm at 434 MHz,
docs/layout.md, for mV).

    python3 sim/power/z_ac.py [A|B]
Writes build/power/z_ac_<case>.json.
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
from rawread import read_raw  # noqa: E402

BLOCKS = {'chain': 'VDPWR', 'log_det': 'VDPWR', 'avg_sc': 'VDPWR', 'comp_ct': 'VDPWR', 'bias': 'VDPWR',
          'dbg_tg': 'VDPWR', 'tx_ring': 'VDPWR', 'tx_drv_p': 'VAPWR', 'tx_drv_n': 'VAPWR'}
SIG = ['det', 'lpf', 'avg', 'trim', 'vcm']
FREQS = {'77k': 77e3, '434M': 433.92e6, '500M': 500e6}


def local(nodes, term, xy):
    """The mesh node of the terminal nearest the middle of a block's terminals."""
    pts = [(n, xy[n]) for n in nodes if n in xy and n in term and term[n] not in common.SUP]
    if not pts:
        return None
    cx = np.mean([p[1][0] for p in pts]); cy = np.mean([p[1][1] for p in pts])
    n = min(pts, key=lambda p: (p[1][0] - cx) ** 2 + (p[1][1] - cy) ** 2)[0]
    return term[n]


def main(case):
    txt, term, _ = stitch.tile_text(case)
    pr = common.probes(case)
    xy = common.node_xy(case)
    loc = {}
    for b, sup in BLOCKS.items():
        if b in pr and sup in pr[b] and 'VGND' in pr[b]:
            loc[b] = (local(pr[b][sup], term, xy), local(pr[b]['VGND'], term, xy))
    src = open(os.path.join(common.ROOT, 'build', 'tb_radio_analog.spice')).read()
    deck, n = re.subn(r'^\.subckt\s+radio_analog\s.*?^\.ends\b[^\n]*\n', '', src, flags=re.S | re.M | re.I)
    assert n == 1
    deck = re.sub(r'\bac 0\.5 (0|180)\b', 'ac 0', deck)
    deck = stitch.pdn_model(deck)
    x = lambda nd: f'xana.x1.{nd}'.lower()
    srcs = ''.join(f'Iz_{b} {x(d)} {x(s)} dc 0 ac 0\n' for b, (d, s) in loc.items())
    save = sorted({x(nd) for d, s in loc.values() for nd in (d, s)} | {x(s) for s in SIG})
    ctl = ['.control', 'op', 'print i(vdpwr) i(va)']
    for b in loc:
        ctl += [f'alter @iz_{b}[acmag] = 1', 'ac dec 10 1e4 2e9', f'write z_ac_{case}_{b}.raw',
                f'alter @iz_{b}[acmag] = 0', 'destroy all']
    ctl += ['.endc']
    deck = re.sub(r'^\.control.*?^\.endc', '\n'.join(ctl), deck, flags=re.S | re.M)
    deck = re.sub(r'^\.save .*$', '.save ' + ' '.join(f'v({nd})' for nd in save), deck, flags=re.M)
    deck = re.sub(r'^\.end\s*$', srcs + txt + '.end', deck, flags=re.M)
    name = f'z_ac_{case}'
    open(os.path.join(common.B, name + '.spice'), 'w').write(deck)
    print('local nodes:', loc, flush=True)
    subprocess.run([common.OSIC, 'bash', '-c', f'cd build/power && ngspice -b {name}.spice > {name}.log 2>&1'],
                   cwd=common.ROOT)
    res = {}
    for b, (d, s) in loc.items():
        p = read_raw(os.path.join(common.B, f'z_ac_{case}_{b}.raw'))[0]
        f = np.real(p['vars']['frequency'])
        V = lambda nd: p['vars'][f'v({x(nd)})']
        zdd = np.abs(V(d) - V(s))
        r = {'f': f.tolist(), 'zdd': zdd.tolist(), 'zgnd': np.abs(V(s)).tolist(),
             'to': {o: np.abs(V(loc[o][0]) - V(loc[o][1])).tolist() for o in loc if o != b}}
        r['to'].update({sg: np.abs(V(sg)).tolist() for sg in SIG})
        res[b] = r
    json.dump(res, open(os.path.join(common.B, f'z_ac_{case}.json'), 'w'))
    at = lambda arr, f, fq: float(np.interp(np.log10(fq), np.log10(f), arr))
    print(f'case {case}: |Z| between each block\'s local VDD and VSS (ohm), and |V(vss)| per A to board ground')
    print(f'{"block":10s} ' + ' '.join(f'{"Zdd " + k:>10s}' for k in FREQS) + ' ' + ' '.join(f'{"Zgnd " + k:>10s}' for k in FREQS))
    for b, r in res.items():
        f = np.array(r['f'])
        print(f'{b:10s} ' + ' '.join(f'{at(r["zdd"], f, v):10.2f}' for v in FREQS.values()) + ' ' +
              ' '.join(f'{at(r["zgnd"], f, v):10.2f}' for v in FREQS.values()))
    for b in ('tx_drv_p', 'tx_drv_n'):
        if b in res:
            r = res[b]; f = np.array(r['f'])
            print(f'TX -> RX at 434 MHz, per A at {b} (ohm; x 9.45 mA RMS -> mV x 9.45):')
            print('   ' + '  '.join(f'{o}: {at(v, f, 433.92e6):.3f}' for o, v in r['to'].items()))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'A')
