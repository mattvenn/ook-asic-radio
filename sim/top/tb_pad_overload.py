"""Strong signal at the RX pads (plan_verify_gaps 3.5, G8): xschem/tb_radio_analog.sch (tile view from
sim/top/tb_tile.py: sch / lvs / c / rc), RX on, a 433.92 MHz tone keyed on 1..6 us at --dbm (available
from the 73 ohm dipole; 0 and +6 dBm = a second board ~10 cm away), then off to --tstop.

Measures: peak pad voltages (each side and differential: the chain's input devices are 1.8 V parts
behind the pad model), peak antenna current, VDPWR current before / during / long after the burst
(a latch or a stuck bias shows as a different current afterwards; no parasitic SCR is modelled), and
det / lpf recovery to within 2 mV of their pre-burst level.

    OSIC=tools/osic NT=4 python3 sim/top/tb_pad_overload.py --dbm=6 sch c
"""
import math
import os
import re
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import tb_tile as T                      # noqa: E402
from rawread import read_raw             # noqa: E402

B = T.B
TON, TOFF = 1e-6, 6e-6


def deck(src, mode, dbm, tstop, nt):
    d = T.deck_for(src, mode)
    d = re.sub(r'^\.control\b.*?^\.endc\b[^\n]*\n', '', d, flags=re.S | re.M)
    d = re.sub(r'^\.save .*\n(\+.*\n)*', '', d, flags=re.M)
    ve = math.sqrt(8 * 73 * 1e-3 * 10 ** (dbm / 10))
    d, n = re.subn(r"^Vant_p emf_p acm .*$", 'Bant_p emf_p acm V = v(key) * vemf / 2 * sin(2 * pi * f0 * time)', d, flags=re.M)
    d, m = re.subn(r"^Vant_n emf_n acm .*$", 'Bant_n emf_n acm V = -v(key) * vemf / 2 * sin(2 * pi * f0 * time)', d, flags=re.M)
    assert n == m == 1
    d, k = re.subn(r'^\.param vemf=\S+', f'.param vemf={ve:.6g}', d, flags=re.M)
    d, j = re.subn(r'^\.param vcmi=\S+', '.param vcmi=0', d, flags=re.M)
    assert k == j == 1
    p = '' if mode == 'sch' else 'x1.'
    ctl = (f'Vkey key 0 pwl(0 0 {TON:g} 0 {TON + 2e-9:g} 1 {TOFF:g} 1 {TOFF + 2e-9:g} 0)\n'
           f'.save v(pad_p) v(pad_n) v(ant_p) v(ant_n) v(key) v(xana.{p}det) v(xana.{p}lpf) v(xana.{p}vcm) '
           f'v(comp) i(vdpwr) i(va) i(bant_p)\n.options method=GEAR\n'
           f'.control\nset num_threads={nt}\ntran 50p {tstop:g} 0 50p\nwrite {{name}}.raw\n.endc\n')
    return re.sub(r'^\.end\s*$', ctl + '.end', d, count=1, flags=re.M)


def analyse(name, mode):
    v = read_raw(os.path.join(B, name + '.raw'))[0]['vars']
    t = np.real(v['time'])
    p = '' if mode == 'sch' else 'x1.'
    r = lambda k: np.real(v[k])
    pp, pn = r('v(pad_p)'), r('v(pad_n)')
    on = (t > TON) & (t < TOFF)
    idp = -r('i(vdpwr)') * 1e3
    pre, dur, end = t < TON * 0.9, on, t > t[-1] - 2e-6
    out = [f'{name}: pad_p {pp.min():+.3f}..{pp.max():+.3f} V, pad_n {pn.min():+.3f}..{pn.max():+.3f} V, '
           f'|pad_p - pad_n| max {np.abs(pp - pn).max():.3f} V; antenna current peak '
           f'{np.abs(r("i(bant_p)")).max() * 1e3:.2f} mA',
           f'  IDPWR before {idp[pre].mean():.3f} mA, during {idp[dur].mean():.3f} mA, at end {idp[end].mean():.3f} mA; '
           f'vcm before {r(f"v(xana.{p}vcm)")[pre].mean():.4f} / at end {r(f"v(xana.{p}vcm)")[end].mean():.4f} V']
    for k in ('det', 'lpf'):
        x = r(f'v(xana.{p}{k})')
        ref = x[pre].mean()
        bad = np.where((t > TOFF) & (np.abs(x - ref) > 2e-3))[0]
        rec = (t[bad[-1]] - TOFF) * 1e6 if len(bad) else 0.0
        tail = 'not recovered by the end' if len(bad) and bad[-1] == len(t) - 1 else f'back within 2 mV {rec:.1f} us after key-off'
        out.append(f'  {k}: before {ref:.4f} V, min {x[on].min():.4f} V during, {tail} (end {x[-1]:.4f} V)')
    print('\n'.join(out), flush=True)


if __name__ == '__main__':
    a = sys.argv[1:]
    opt = dict(x[2:].split('=') for x in a if x.startswith('--') and '=' in x)
    modes = [x for x in a if not x.startswith('--')] or ['sch']
    dbm, tstop = float(opt.get('dbm', 6)), float(opt.get('tstop', 40e-6))
    src = None if '--no-run' in a else T.netlist()
    for md in modes:
        name = f'padov_{md}_{dbm:+g}dBm'
        if src is not None:
            with open(os.path.join(B, name + '.spice'), 'w') as fh:
                fh.write(deck(src, md, dbm, tstop, os.environ.get('NT', '1')).replace('{name}', name))
            subprocess.run([T.OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
        analyse(name, md)
