"""lna_chain Monte Carlo (mismatch): DC offset per stage, and gain at 434 MHz in both strap states.

From build/tb_chain.spice (netlist xschem/tb_chain.sch first), or with --pex the extracted chain
(build/pexsim/tb_chain.spice, made by sim/chain/mk_pex_tb.py), with the PDK's mismatch models
(<corner>_mm: AGAUSS per device). One sample per ngspice process, each with its own .options seed
(sim_learnings.md: without one, parallel processes draw the same samples). Every `reset` re-seeds to
that seed, so one process measures the same sample twice: full gain (vglo 1.8) and low gain (vglo 0,
the lna_lo_n strap on). Per state: the operating point (each stage's differential DC output o1..o5,
out, and the output common mode), then the AC gain from the differential antenna EMF to out at
433.92 MHz. Before the samples: the nominal chain (no mismatch) at a sweep of vglo (the strap's gate
voltage), to show where the switch turns on.

    python3 sim/chain/mc_chain.py [--mc 20] [--jobs 4] [--temp 27] [--pex] [corner]

Rows in build/mc/chain_<corner>[_<temp>][_pex].txt: per sample, the full-gain DC row and gain, the
low-gain DC row and gain.
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
SWEEP = [1.8, 1.6, 1.4, 1.3, 1.2, 1.1, 1.0, 0.9, 0.8, 0.6, 0.4, 0.2, 0.0]


def deck(src, corner, temp, vglos, seed=None):
    src = re.sub(r'^\.control\b.*?^\.endc\b[^\n]*\n', '', src, flags=re.S | re.M)
    src = re.sub(r'(sky130\.lib\.spice) tt\b', rf'\1 {corner}', src)
    lets = ''.join(f'let d{i} = v({s}_p)-v({s}_n)\n' if s == 'out' else f'let d{i} = v({s}p)-v({s}n)\n'
                   for i, s in enumerate(STAGES))
    dc = ' '.join(f'"$&d{i}"' for i in range(len(STAGES)))
    loop = ''
    for g in vglos:
        loop += (f'alterparam vglo = {g}\nreset\nop\n{lets}let cm = (v(out_p)+v(out_n))/2\nset dc = ( {dc} "$&cm" )\n'
                 f'destroy all\nac lin 1 {F0} {F0}\nlet g = db(v(out_p)-v(out_n))\nset gdb = "$&g"\ndestroy all\n'
                 f'echo MC {g} $dc $gdb\n')
    opt = f'.temp {temp:g}\n' + (f'.options seed={seed}\n' if seed is not None else '')
    ctl = f'{opt}.control\nset num_threads=1\n{loop}.endc\n'
    return re.sub(r'^\.end\s*$', ctl + '.end', src, count=1, flags=re.M)


def run(corner, n, jobs, temp=27.0, pex=False):
    os.makedirs(os.path.join(B, 'mc'), exist_ok=True)
    src = open(os.path.join(B, 'pexsim' if pex else '', 'tb_chain.spice')).read()
    assert re.search(r'^\.param vglo=', src, re.M), 'no .param vglo in tb_chain.spice'
    tag = f'chain_{corner}' + ('' if temp == 27 else f'_{temp:g}') + ('_pex' if pex else '')
    seed0 = int.from_bytes(os.urandom(3), 'little')

    def one(args):
        j, c, vglos, seed = args
        name = f'mc/{tag}_{j}'
        with open(os.path.join(B, name + '.spice'), 'w') as fh:
            fh.write(deck(src, c, temp, vglos, seed))
        subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
        log = open(os.path.join(B, name + '.log')).read()
        rows = {float(g): [float(x) for x in r.split()] for g, r in re.findall(r'^MC (\S+) (.*)$', log, re.M)
                if 'failed' not in r}
        return rows

    tasks = [('nom', corner, SWEEP, None)] + [(j, corner + '_mm', [1.8, 0.0], seed0 + j) for j in range(n)]
    with ThreadPoolExecutor(jobs) as ex:
        res = list(ex.map(one, tasks))
    nom = res[0]
    ok = [r for r in res[1:] if 1.8 in r and 0.0 in r]
    rows = np.array([r[1.8] + r[0.0] for r in ok])
    np.savetxt(os.path.join(B, 'mc', f'{tag}.txt'), rows,
               header=' '.join(f'{s}_diff_V' for s in STAGES) + ' out_cm_V gain_dB  (full gain, then low gain)')
    k = len(STAGES) + 2
    dup = len(rows) - len({tuple(np.round(r, 9)) for r in rows})
    print(f'lna_chain MC {corner} {temp:g} C{" extracted" if pex else ""}: {len(rows)}/{n} samples '
          f'({dup} duplicates). Nominal gain vs the strap gate voltage vglo:')
    for g in SWEEP:
        if g in nom:
            print(f'  vglo {g:4.2f} V: {nom[g][-1]:6.2f} dB  (step {nom[1.8][-1] - nom[g][-1]:5.2f} dB)')
    hdr = ' '.join(f'{s:>8}' for s in STAGES)
    for st, off in (('full gain', 0), ('low gain', k)):
        r = rows[:, off:off + k]
        print(f'{st}: differential DC out per stage, mV')
        print(f'            {hdr}   out CM V  gain dB')
        print(f'  nominal   ' + ' '.join(f'{x * 1e3:+8.1f}' for x in nom[1.8 if off == 0 else 0.0][:6]) +
              f'   {nom[1.8 if off == 0 else 0.0][6]:.3f}    {nom[1.8 if off == 0 else 0.0][7]:.2f}')
        print(f'  sigma     ' + ' '.join(f'{x * 1e3:8.1f}' for x in r[:, :6].std(0, ddof=1)) +
              f'   {r[:, 6].std(ddof=1):.3f}    {r[:, 7].std(ddof=1):.2f}')
        print(f'  max |x|   ' + ' '.join(f'{x * 1e3:8.1f}' for x in np.abs(r[:, :6]).max(0)) +
              f'   {r[:, 6].min():.3f}..{r[:, 6].max():.3f}  {r[:, 7].min():.2f}..{r[:, 7].max():.2f}')
    step = rows[:, k - 1] - rows[:, 2 * k - 1]
    dfull = rows[:, k - 1] - nom[1.8][-1]
    print(f'step (full - low gain): mean {step.mean():.2f} dB, sigma {step.std(ddof=1):.2f}, '
          f'min {step.min():.2f}, max {step.max():.2f}; >= 9 dB in {np.mean(step >= 9):.1%} '
          f'(nominal {nom[1.8][-1] - nom[0.0][-1]:.2f})')
    print(f'full gain - nominal: {dfull.min():+.2f}..{dfull.max():+.2f} dB; within 1 dB in {np.mean(np.abs(dfull) <= 1):.1%}')
    return nom, rows


if __name__ == '__main__':
    a = sys.argv[1:]
    opt = {k: a[i + 1] for i, k in enumerate(a) if k in ('--mc', '--jobs', '--temp')}
    pos = [x for i, x in enumerate(a) if not x.startswith('-') and (i == 0 or a[i - 1] not in opt)]
    run(pos[0] if pos else 'tt', int(opt.get('--mc', 20)), int(opt.get('--jobs', 4)), float(opt.get('--temp', 27)),
        '--pex' in a)
