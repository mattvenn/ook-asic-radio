"""jobs_shift.py plus an old-vs-new calibration check (2026-11-20). In the first jobs_shift run the schematic
baseband detected -92 dBm on 3/5 seeds (5/5 before the recalibration) and -94 dBm on 2/6 (3/6), but both sit at
the edge (best scores 93-106 against 97), so 5 seeds can't tell a real loss from scatter. Here: 20 more seeds
(6-25) at -92 and -94 dBm on the schematic baseband, each with the new SHIFT_DB (-5.01, tag 'new') and the old one
(-3.8, tag 'old') on the same noise: 80 runs. Read with the event pin (plot_mixed) and over burst timing:
    python3 sim/mixed/replay_corr.py new -92 -94 && python3 sim/mixed/replay_corr.py old -92 -94
Run instead of jobs_shift.py (one scheduler: net_mixed rewrites a shared netlist):

    tools/osic bash sim/mixed/build_so.sh
    mkdir -p build/rerun_shift && nohup setsid python3 sim/rerun/sched.py sim/rerun/jobs_shift_ab.py --budget 28 \\
        --load 28 --out build/rerun_shift > build/rerun_shift/sched.log 2>&1 &
"""
import os
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
JOBS = list(runpy.run_path(os.path.join(HERE, 'jobs_shift.py'))['JOBS'])
SEEDS = range(6, 26)
SHIFT = {'new': -5.01, 'old': -3.8}

for tag, sh in SHIFT.items():
    JOBS.append(dict(name=f'gen_det_{tag}', cmd=f'for s in {" ".join(map(str, SEEDS))}; do python3 sim/rx/gen_det.py '
                     f'--shift={sh} --tag={tag} --seed=$s -92 -94; done', threads=1, est=600))
    for s in SEEDS:
        for lvl in (-92, -94):
            name = f'{lvl}_s{s}_{tag}'
            JOBS.append(dict(name=f'mixed_{name}', cmd=f': sch; python3 sim/mixed/gen_mixed.py --seed={s} --tag={tag} {lvl} && '
                             f'(tools/osic bash -c "cd build/mixed && ngspice -b mixed_{name}.cir > mixed_{name}.log 2>&1"; true) '
                             f'&& python3 sim/mixed/plot_mixed.py {name}', threads=1, est=1200,
                             deps=[f'gen_det_{tag}', 'net_mixed'], stagger=('mixed', 10)))

assert len({j['name'] for j in JOBS}) == len(JOBS), 'duplicate job names'
