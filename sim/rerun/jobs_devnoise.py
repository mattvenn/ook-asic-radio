"""Device noise in the mixed bench (Harald's review action 13 follow-up, 2026-11-22). gen_det.py fitted by
sim/noise/cal_gen_det.py to the transistor noise runs (sim/noise/devnoise_results.txt) on both the no-signal det and
the swings at -94 / -90 / -85 dBm:
    afit  case A (injected NF 11, what every mixed result so far used): --shift=-5.01 --sig=+0.90
    dth   device noise, thermal:                                         --shift=-3.71 --sig=-1.94
    dall  device noise, thermal + 1/f (upper bound):                     --shift=-2.95 --sig=-3.52
Seeds 6-25 (the same noise as the 'new' / 'old' runs of jobs_shift_ab.py), schematic baseband. Read with
    python3 sim/mixed/replay_corr.py <tag> <level> ...

    mkdir -p build/rerun_devnoise && nohup setsid python3 sim/rerun/sched.py sim/rerun/jobs_devnoise.py --budget 28 \\
        --load 28 --out build/rerun_devnoise > build/rerun_devnoise/sched.log 2>&1 &
"""
import os
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
JOBS = [j for j in runpy.run_path(os.path.join(HERE, 'jobs_tall.py'))['JOBS'] if j['name'] == 'net_mixed']
SEEDS = range(6, 26)
CASES = {'afit': ('-5.01', '+0.90', (-90, -92, -94)),
         'dth': ('-3.71', '-1.94', (-86, -88, -90, -92, -94)),
         'dall': ('-2.95', '-3.52', (-86, -88, -90, -92))}

for tag, (sh, sig, levels) in CASES.items():
    lv = ' '.join(map(str, levels))
    JOBS.append(dict(name=f'gen_det_{tag}', cmd=f'for s in {" ".join(map(str, SEEDS))}; do python3 sim/rx/gen_det.py '
                     f'--shift={sh} --sig={sig} --tag={tag} --seed=$s {lv}; done', threads=1, est=900))
    for s in SEEDS:
        for lvl in levels:
            name = f'{lvl}_s{s}_{tag}'
            JOBS.append(dict(name=f'mixed_{name}', cmd=f': sch; python3 sim/mixed/gen_mixed.py --seed={s} --tag={tag} {lvl} && '
                             f'(tools/osic bash -c "cd build/mixed && ngspice -b mixed_{name}.cir > mixed_{name}.log 2>&1"; true) '
                             f'&& python3 sim/mixed/plot_mixed.py {name}', threads=1, est=1200,
                             deps=[f'gen_det_{tag}', 'net_mixed'], stagger=('mixed', 10)))

assert len({j['name'] for j in JOBS}) == len(JOBS), 'duplicate job names'
