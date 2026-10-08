"""Block testbench for bias_gen (schematic vs extracted layout).

Runs xschem/tb_bias.sch (diode loads like the chain / detector / comparator): the
output currents and vcm at VDD 1.7 / 1.8 / 1.9 V and 10 / 27 / 50 C, the en = 0 supply
current, and the start-up / en toggling transient. --pex swaps in
layout/pex/bias_gen.spice. Prints both columns when both runs exist.

    python sim/bias/tb_bias_gen.py [--pex] [corner]
OSIC overrides the tools wrapper (default tools/osic).
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from pexswap import swap  # noqa: E402

B = os.path.join(ROOT, 'build')
OSIC = os.environ.get('OSIC', os.path.join(ROOT, 'tools', 'osic'))


def run(pex, corner):
    subprocess.run([OSIC, 'bash', '-c', 'xschem -n -s -q -o build xschem/tb_bias.sch'], cwd=ROOT,
                   capture_output=True)
    deck = open(os.path.join(B, 'tb_bias.spice')).read()
    deck = re.sub(r"(\.lib\s+\S+\s+)tt\b", rf'\g<1>{corner}', deck)
    deck = deck.replace('write tb_bias.raw', '')
    tag = f'tb_bias_gen_{corner}' + ('_pex' if pex else '')
    if pex:
        deck = swap(deck, ['bias_gen'])
        deck = re.sub(r'^(x1 .* bias_gen)\s.*$', r'\1', deck, flags=re.M)   # the pex subckt has no params
    open(os.path.join(B, tag + '.spice'), 'w').write(deck)
    out = subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {tag}.spice'], cwd=ROOT,
                         capture_output=True, text=True).stdout
    res = [ln for ln in out.splitlines() if ln.startswith('RESULT')]
    if not res:
        print(out[-3000:])
        raise SystemExit(f'{tag}: no RESULT lines')
    open(os.path.join(B, tag + '.txt'), 'w').write('\n'.join(res) + '\n')
    return res


def parse(lines):
    vals = {}
    for ln in lines:
        t = ln.split()
        if t[1] == 'op':
            key = f'VDD {t[3]} T {t[5]}'
            vals[key + ' ib_chain uA'] = float(t[7])
            vals[key + ' ib_det uA'] = float(t[9])
            vals[key + ' ib_comp uA'] = float(t[11])
            vals[key + ' vcm V'] = float(t[13])
        elif t[1] == 'off':
            vals['en=0 IDD uA'] = float(t[3])
        elif t[1] == 'tran' and t[2] == 'ib_chain_uA':
            vals['tran ib_chain at 30u uA'] = float(t[4])
            vals['tran ib_chain at 50u (en=0) uA'] = float(t[6])
            vals['tran ib_chain at 99u uA'] = float(t[8])
        elif t[1] == 'tran' and t[2] == 'last':
            vals['re-enable: last rise through 54 uA, us'] = float(t[-1]) * 1e6
    return vals


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    corner = args[0] if args else 'tt'
    pex = '--pex' in sys.argv
    run(pex, corner)
    cols = {}
    for p in (False, True):
        f = os.path.join(B, f'tb_bias_gen_{corner}' + ('_pex' if p else '') + '.txt')
        if os.path.exists(f):
            cols['pex' if p else 'sch'] = parse(open(f).read().splitlines())
    keys = list(next(iter(cols.values())).keys())
    print(f'{"":40s}' + ''.join(f'{c:>12s}' for c in cols) + ('   pex/sch' if len(cols) == 2 else ''))
    for k in keys:
        v = [cols[c].get(k) for c in cols]
        rel = f'   {100 * (v[1] / v[0] - 1):+.2f} %' if len(v) == 2 and v[0] and 'IDD' not in k else ''
        print(f'{k:40s}' + ''.join(f'{x:12.4g}' for x in v) + rel)
