"""Power-up of the analog tile (plan_verify_gaps 3.6, G9): xschem/tb_radio_analog.sch with radio_analog
from the schematic or the extracted tile (sim/top/tb_tile.py's views: sch / lvs / c / rc).

Ramp:  VDPWR and VAPWR 0 -> 1.8 / 3.3 V linearly over --ramp (10u or 10m). The digital inputs come from
the (unsimulated) macro, which runs on VDPWR, so every one of them is scaled by v(VDPWR) / 1.8: the
trim bits sit at the reset code 128, sc_phi1 / sc_phi2 run, tx_en stays 0, and rx_en rises 20 us after
the ramp (ena / rst_n released). Runs to 3 ms after rx_en.
Measures: vcm (bias up: 95 % of its final value), det / lpf / avg (settled to within 2 mV of their value
at the end, after rx_en), TX outputs (max |tx_p|, |tx_n| over the run: no TX output before tx_en), the
peak supply currents during the ramp, and the currents at the end.

Off state with one supply missing (--off): rx_en = tx_en = 0, operating point with VDPWR 1.8 / VAPWR 0
and with VDPWR 0 / VAPWR 3.3: supply currents and the TX outputs.

    OSIC=tools/osic NT=4 python3 sim/top/tb_powerup.py --ramp=10m --corner=ss --temp=10 c
    OSIC=tools/osic python3 sim/top/tb_powerup.py --off --corner=tt c
    python3 sim/top/tb_powerup.py --no-run --ramp=10m --corner=ss --temp=10 c      (analyse)
"""
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
DIG = ['rx_en', 'dbg_en', 'tx_en', 'tx_en_n', 'sc_phi1', 'sc_phi2'] + [f'trim[{i}]' for i in range(8)]


def sec(x):
    return float(x[:-1]) * {'u': 1e-6, 'm': 1e-3}[x[-1]] if x[-1] in 'um' else float(x)


def base(src, mode, corner, temp):
    deck = T.deck_for(src, mode)
    deck = re.sub(r'(sky130\.lib\.spice) tt\b', rf'\1 {corner}', deck)
    deck = re.sub(r'^\.end\s*$', f'.temp {temp:g}\n.end', deck, count=1, flags=re.M)
    deck = re.sub(r'^\.control\b.*?^\.endc\b[^\n]*\n', '', deck, flags=re.S | re.M)
    deck = re.sub(r'^\.save .*\n(\+.*\n)*', '', deck, flags=re.M)
    deck, k = re.subn(r'^\.param vemf=\S+', '.param vemf=0', deck, flags=re.M)      # no RF
    assert k == 1
    # every digital input through a raw source scaled by VDPWR / 1.8
    for n in DIG:
        deck, k = re.subn(rf'^(V\w+) {re.escape(n)} GND (.*)$',
                          lambda m: f'{m[1]} {n}_raw GND {m[2]}\nB{m[1][1:]} {n} GND V = v({n}_raw) * v(VDPWR) / 1.8',
                          deck, count=1, flags=re.M)
        assert k == 1, n
    return deck


def ramp_deck(src, mode, corner, temp, tr, nt):
    deck = base(src, mode, corner, temp)
    ten, tstop = tr + 20e-6, tr + 20e-6 + 3e-3
    deck, n = re.subn(r'^VDPWR VDPWR GND dc 1\.8 .*$', f'VDPWR VDPWR GND pwl(0 0 {tr:g} 1.8)', deck, flags=re.M)
    deck, m = re.subn(r'^VA VAPWR GND 3\.3$', f'VA VAPWR GND pwl(0 0 {tr:g} 3.3)', deck, flags=re.M)
    assert n == m == 1, (n, m)
    # reset code 128, rx_en after the ramp, TX off
    for i in range(8):
        deck = re.sub(rf'^(Vt{i} trim\[{i}\]_raw GND) \S+$', rf'\1 {1.8 if i == 7 else 0}', deck, flags=re.M)
    deck = re.sub(r"^(Vrx rx_en_raw GND) .*$", rf'\1 pwl(0 0 {ten:g} 0 {ten + 10e-9:g} 1.8)', deck, flags=re.M)
    p = '' if mode == 'sch' else 'x1.'
    save = (f'.save v(VDPWR) v(VAPWR) v(rx_en) v(xana.{p}vcm) v(xana.{p}det) v(xana.{p}lpf) v(xana.{p}avg) '
            f'v(xana.{p}trim) v(tx_p) v(tx_n) v(comp) i(vdpwr) i(va)\n')
    ctl = (f'{save}.options method=GEAR\n'
           f'.control\nset num_threads={nt}\ntran 1u {tstop:g} 0 1u\nwrite {{name}}.raw\n.endc\n')
    return re.sub(r'^\.end\s*$', ctl + '.end', deck, count=1, flags=re.M), ten


def off_deck(src, mode, corner, temp):
    deck = base(src, mode, corner, temp)
    lines = []
    for vd, va in ((1.8, 0), (0, 3.3)):
        lines += [f'alter vdpwr dc = {vd}', f'alter va dc = {va}', 'op',
                  'let idp = -i(vdpwr) * 1e6', 'let iap = -i(va) * 1e6',
                  f'echo RESULT off vdpwr {vd} vapwr {va} IDPWR_uA $&idp IAPWR_uA $&iap '
                  'tx_p $&v(tx_p) tx_n $&v(tx_n)', 'destroy all']
    deck = re.sub(r'^(Vrx rx_en_raw GND) .*$', r'\1 0', deck, flags=re.M)
    ctl = ('.control\n' + '\n'.join(lines) + '\n.endc\n')
    return re.sub(r'^\.end\s*$', ctl + '.end', deck, count=1, flags=re.M)


def run(deck, name):
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck.replace('{name}', name))
    subprocess.run([T.OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)


def settle(t, x, t0, tol):
    """First time after t0 from which x stays within tol of its final value."""
    m = t >= t0
    bad = np.where(np.abs(x[m] - x[-1]) > tol)[0]
    return t[m][bad[-1] + 1] if len(bad) and bad[-1] + 1 < m.sum() else (t[m][0] if not len(bad) else np.nan)


def analyse(name, mode, tr, ten):
    v = read_raw(os.path.join(B, name + '.raw'))[0]['vars']
    t = np.real(v['time'])
    p = '' if mode == 'sch' else 'x1.'
    g = lambda k: np.real(v[f'v(xana.{p}{k})'])
    vcm = g('vcm')
    up = t[np.argmax(vcm >= 0.95 * vcm[-1])]
    out = [f'{name}: ramp {tr * 1e3:g} ms, rx_en at {ten * 1e3:.3f} ms; vcm {vcm[-1]:.3f} V (95 % at {up * 1e3:.3f} ms)']
    for k in ('det', 'lpf', 'avg'):
        x = g(k)
        ts = settle(t, x, ten, 2e-3)
        out.append(f'  {k} end {x[-1]:.4f} V, within 2 mV from {(ts - ten) * 1e3:.3f} ms after rx_en')
    txp, txn = np.real(v['v(tx_p)']), np.real(v['v(tx_n)'])
    idp, iap = -np.real(v['i(vdpwr)']) * 1e3, -np.real(v['i(va)']) * 1e3
    r = t <= tr * 1.05
    out.append(f'  TX outputs max |tx_p| {np.abs(txp).max() * 1e3:.1f} mV, |tx_n| {np.abs(txn).max() * 1e3:.1f} mV')
    out.append(f'  supply current peak during ramp: VDPWR {idp[r].max():.3f} mA, VAPWR {iap[r].max():.3f} mA; '
               f'at end {idp[-1]:.3f} / {iap[-1]:.4f} mA; comp at end {np.real(v["v(comp)"])[-1]:.2f} V')
    print('\n'.join(out), flush=True)


if __name__ == '__main__':
    a = sys.argv[1:]
    opt = dict(x[2:].split('=') for x in a if x.startswith('--') and '=' in x)
    modes = [x for x in a if not x.startswith('--')] or ['c']
    corner, temp = opt.get('corner', 'tt'), float(opt.get('temp', 27))
    src = None if '--no-run' in a else T.netlist()
    for md in modes:
        tag = f'pwr_{md}_{corner}_{temp:g}'
        if '--off' in a:
            if src is not None:
                run(off_deck(src, md, corner, temp), tag + '_off')
            log = open(os.path.join(B, tag + '_off.log')).read()
            print('\n'.join(f'{tag}: {ln}' for ln in re.findall(r'^RESULT (.*)$', log, re.M)) or log[-2000:])
            continue
        tr = sec(opt.get('ramp', '10u'))
        name = f'{tag}_r{opt.get("ramp", "10u")}'
        if src is not None:
            deck, ten = ramp_deck(src, md, corner, temp, tr, os.environ.get('NT', '1'))
            run(deck, name)
        analyse(name, md, tr, tr + 20e-6)
