"""lna_chain Monte Carlo (mismatch): DC offset per stage and gain at 434 MHz.

From build/tb_chain.spice (netlist xschem/tb_chain.sch first), with the PDK's mismatch models
(<corner>_mm: AGAUSS per device; each `reset` redraws). Per sample: the operating point (each
stage's differential DC output o1..o5, out, and the output common mode), then the AC gain from
the differential antenna EMF to out at 433.92 MHz. Prints the nominal case (no mismatch) first.

    python3 sim/chain/mc_chain.py [--mc 20] [--jobs 4] [corner]

Rows in build/mc/chain_<corner>.txt. Seeds aren't repeatable in ngspice 47, so neither are samples.
"""
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.environ.get('OSIC', os.path.join(ROOT, 'tools', 'osic'))
STAGES = ['o1', 'o2', 'o3', 'o4', 'o5', 'out']
F0 = 433.92e6


def deck(corner, n):
    src = open(os.path.join(B, 'tb_chain.spice')).read()
    src = re.sub(r'^\.control\b.*?^\.endc\b[^\n]*\n', '', src, flags=re.S | re.M)
    src = re.sub(r'(sky130\.lib\.spice) tt\b', rf'\1 {corner}', src)
    lets = ''.join(f'let d{i} = v({s}_p)-v({s}_n)\n' if s == 'out' else f'let d{i} = v({s}p)-v({s}n)\n'
                   for i, s in enumerate(STAGES))
    dc = ' '.join(f'"$&d{i}"' for i in range(len(STAGES)))
    loop = ''
    for k in range(n):
        loop += (f'reset\nop\n{lets}let cm = (v(out_p)+v(out_n))/2\nset dc = ( {dc} "$&cm" )\ndestroy all\n'
                 f'ac lin 1 {F0} {F0}\nlet g = db(v(out_p)-v(out_n))\nset gdb = "$&g"\ndestroy all\n'
                 f'echo MC {k} $dc $gdb\n')
    ctl = f'.control\nset num_threads=1\n{loop}.endc\n'
    return re.sub(r'^\.end\s*$', ctl + '.end', src, count=1, flags=re.M)


def run(corner, n, jobs):
    os.makedirs(os.path.join(B, 'mc'), exist_ok=True)
    per = [n // jobs + (j < n % jobs) for j in range(jobs)]

    def one(args):
        c, k, j = args
        name = f'mc/chain_{c}_{j}'
        with open(os.path.join(B, name + '.spice'), 'w') as fh:
            fh.write(deck(c, k))
        subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
        log = open(os.path.join(B, name + '.log')).read()
        return [[float(x) for x in r.split()] for r in re.findall(r'^MC \d+ (.*)$', log, re.M)]

    tasks = [(corner, 1, 'nom')] + [(corner + '_mm', k, j) for j, k in enumerate(per)]
    with ThreadPoolExecutor(len(tasks)) as ex:
        res = list(ex.map(one, tasks))
    nom, rows = np.array(res[0][0]), np.array([r for rr in res[1:] for r in rr])
    np.savetxt(os.path.join(B, 'mc', f'chain_{corner}.txt'), rows,
               header=' '.join(f'{s}_diff_V' for s in STAGES) + ' out_cm_V gain_dB')
    hdr = ' '.join(f'{s:>8}' for s in STAGES)
    print(f'lna_chain MC {corner}: {len(rows)}/{n} samples. Differential DC out per stage, mV:')
    print(f'            {hdr}   out CM V  gain dB')
    print(f'  nominal   ' + ' '.join(f'{x * 1e3:+8.1f}' for x in nom[:6]) + f'   {nom[6]:.3f}    {nom[7]:.2f}')
    print(f'  sigma     ' + ' '.join(f'{x * 1e3:8.1f}' for x in rows[:, :6].std(0, ddof=1)) +
          f'   {rows[:, 6].std(ddof=1):.3f}    {rows[:, 7].std(ddof=1):.2f}')
    print(f'  max |x|   ' + ' '.join(f'{x * 1e3:8.1f}' for x in np.abs(rows[:, :6]).max(0)) +
          f'   {rows[:, 6].min():.3f}..{rows[:, 6].max():.3f}  {rows[:, 7].min():.2f}..{rows[:, 7].max():.2f}')
    return nom, rows


if __name__ == '__main__':
    a = sys.argv[1:]
    opt = {k: a[i + 1] for i, k in enumerate(a) if k in ('--mc', '--jobs')}
    pos = [x for i, x in enumerate(a) if not x.startswith('-') and (i == 0 or a[i - 1] not in opt)]
    run(pos[0] if pos else 'tt', int(opt.get('--mc', 20)), int(opt.get('--jobs', 4)))
