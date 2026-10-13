"""Noise-free CW det drop through lna_chain + log_det, schematic vs extracted (plan_verify_gaps 3.1).

xschem/tb_logdet.sch (pad models, 6-stage chain, log_det, ideal bias), no noise, no CM interference
(vcmi 0). One ngspice per level and view, single-threaded, in parallel: det averaged over the last
200 ns of 1 us, minus the same run with no signal. --pex swaps in layout/pex/lna_chain.spice and
layout/pex/log_det.spice.

    python3 sim/chain/cw_drop.py [--corner=tt] [--jobs=10] [--blocks=lna_chain,log_det] [--levels=-90]

--blocks picks which blocks the extracted view swaps (default both: which one loses the gain);
--levels limits the levels (no-signal reference always runs); --pex-only reuses the schematic logs.

Model column: the e2e/gen_det model's numbers from verify_2026-10-11 (square law, 0.77 mV at -100 dBm).
"""
import math
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from pexswap import swap  # noqa: E402

B = os.path.join(ROOT, 'build')
OSIC = os.environ.get('OSIC', os.path.join(ROOT, 'tools', 'osic'))
LEVELS = [None, -100, -90, -80, -70]
MODEL = {-100: 0.77, -90: 6.27, -80: 47.3, -70: 175.0}     # other levels: nan


def base(corner):
    subprocess.run([OSIC, 'bash', '-c', 'xschem -n -s -q -o build xschem/tb_logdet.sch'], cwd=ROOT,
                   capture_output=True)
    src = open(os.path.join(B, 'tb_logdet.spice')).read()
    if 'IS MISSING' in src:
        raise RuntimeError('netlist has missing symbols')
    src = re.sub(r'^\.control\b.*?^\.endc\b[^\n]*\n', '', src, flags=re.S | re.M)
    src = re.sub(r'(sky130\.lib\.spice) tt\b', rf'\1 {corner}', src)
    src, n = re.subn(r'^\.param vcmi=\S+', '.param vcmi=0', src, flags=re.M)
    assert n == 1
    return src


BLOCKS = ['lna_chain', 'log_det']


def deck(src, pex, lvl):
    if pex:
        src = swap(src, BLOCKS)
        # the extracted subckts have no parameters: drop them from the instances (with continuation lines)
        for blk in BLOCKS:
            src, n = re.subn(rf'^(x\d+ [^\n]* {blk})\b[^\n]*\n(\+[^\n]*\n)*', r'\1\n', src, flags=re.M)
            assert n == 1, blk
    ve = 0 if lvl is None else math.sqrt(8 * 73 * 1e-3 * 10 ** (lvl / 10))
    ctl = (f'.options method=GEAR\n.control\nset num_threads=1\nalterparam vemf = {ve:.6e}\nreset\n'
           'tran 50p 1u 700n\nmeas tran detavg avg v(det) from=800n to=1u\n'
           'echo RESULT $&detavg\n.endc\n')
    return re.sub(r'^\.end\s*$', ctl + '.end', src, count=1, flags=re.M)


def one(args):
    src, pex, lvl, corner = args
    tag = '_pex' + ('' if len(BLOCKS) == 2 else '_' + BLOCKS[0]) if pex else ''
    name = f'cwdrop_{corner}{tag}_{"none" if lvl is None else -lvl}'
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(src, pex, lvl))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    m = re.search(r'^RESULT (\S+)', open(os.path.join(B, name + '.log')).read(), re.M)
    return float(m.group(1)) if m else float('nan')


if __name__ == '__main__':
    opt = dict(a[2:].split('=') for a in sys.argv[1:] if a.startswith('--') and '=' in a)
    corner, jobs = opt.get('corner', 'tt'), int(opt.get('jobs', 10))
    if 'blocks' in opt:
        BLOCKS[:] = opt['blocks'].split(',')
    if 'levels' in opt:
        LEVELS[:] = [None] + [int(x) for x in opt['levels'].split(',')]
    views = (True,) if '--pex-only' in sys.argv else (False, True)
    src = base(corner)
    tasks = [(src, pex, lvl, corner) for pex in views for lvl in LEVELS]
    with ThreadPoolExecutor(jobs) as ex:
        res = list(ex.map(one, tasks))
    det = {(t[1], t[2]): r for t, r in zip(tasks, res)}
    if views == (True,):        # reuse the schematic logs from a full run
        for lvl in LEVELS:
            name = f'cwdrop_{corner}_{"none" if lvl is None else -lvl}'
            det[(False, lvl)] = float(re.search(r'^RESULT (\S+)', open(os.path.join(B, name + '.log')).read(), re.M)[1])
    print(f'CW det drop, {corner}, noise-free, extracted: {"+".join(BLOCKS)}. det idle: sch {det[(False, None)]:.4f} V, '
          f'pex {det[(True, None)]:.4f} V')
    print('  level     sch mV   pex mV   model mV   pex-sch dB  pex-model dB')
    for lvl in LEVELS[1:]:
        s = (det[(False, None)] - det[(False, lvl)]) * 1e3
        p = (det[(True, None)] - det[(True, lvl)]) * 1e3
        db = lambda a, b: 10 * math.log10(a / b) if a > 0 and b > 0 else float('nan')
        print(f'  {lvl:5d}   {s:8.2f} {p:8.2f}   {MODEL.get(lvl, float("nan")):8.2f}     {db(p, s):+6.2f}       {db(p, MODEL.get(lvl, float("nan"))):+6.2f}')
