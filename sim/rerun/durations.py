"""How long each job of a sched.py run took, against the job file's estimate: for the run report and
for the next job file's est / threads.

    python3 sim/rerun/durations.py [--out build/rerun_tall] [--jobs sim/rerun/jobs_tall.py] [--json FILE]

Prints markdown: one row per job family (the name without its corner / level / seed suffixes: count,
min / median / max minutes, estimate, measured / estimated), then the run's wall-clock span, the
thread-hours declared, and the jobs that ran more than 3x over their estimate. --json writes
{job: minutes} for every finished job, so a later job file can take its est from it.

Times are the scheduler's start / end (status.json), so they include queueing inside the job's own
command (a lock, an xargs -P 1) but not time spent waiting to start. Adopted jobs ('exited') keep the
start the first scheduler wrote; their end is when the new one saw them go (within one round, ~10 s).
"""
import argparse
import json
import re
import statistics
import time

SUFFIX = re.compile(r'^(-?\d.*|s\d+|none|tt|ss|ff|sf|fs|glo[\d.]+|v[\d.]+|(tt|ss|ff|sf|fs)\d+|lo|pex)$')


def family(name):
    """'nt_pex_glo1.8_-94' -> 'nt_pex', 'stabx_ss10_v1.8_glo0' -> 'stabx', 'mixed_-92_pex_s1' -> 'mixed (pex)'."""
    parts = name.split('_')
    keep = [parts[0]]
    for i, p in enumerate(parts[1:], 1):
        if SUFFIX.match(p) and not (p == 'pex' and i == 1):       # 'pex' second ('nt_pex') names the family
            break
        keep.append(p)
    f = '_'.join(keep)
    return f + ' (pex)' if 'pex' in parts[len(keep):] else f      # extracted runs take far longer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='build/rerun_tall')
    ap.add_argument('--jobs', default='sim/rerun/jobs_tall.py')
    ap.add_argument('--json')
    a = ap.parse_args()
    st = json.load(open(f'{a.out}/status.json'))
    # older job files raised their priority jobs' est to 20 h (start order; now sched.py's 'prio'): read them as written
    src = open(a.jobs).read().replace("j['est'] = max(j['est'], 20 * H)", 'pass')
    ns = {'__file__': a.jobs, '__name__': 'jobs'}
    exec(compile(src, a.jobs, 'exec'), ns)
    jobs = {j['name']: j for j in ns['JOBS']}
    done = {n: v for n, v in st.items() if n != '_sched' and v.get('end') and v.get('start')}
    mins = {n: (v['end'] - v['start']) / 60 for n, v in done.items()}
    fam = {}
    for n in mins:
        fam.setdefault(family(n), []).append(n)

    print('| Family | Jobs | Threads | Min, min | Median, min | Max, min | Estimate, min | Measured / estimate |')
    print('|---|---|---|---|---|---|---|---|')
    for f, ns in sorted(fam.items(), key=lambda x: -max(mins[n] for n in x[1])):
        m = [mins[n] for n in ns]
        est = sorted({jobs[n].get('est', 0) / 60 for n in ns if n in jobs})
        thr = sorted({done[n].get('threads', jobs.get(n, {}).get('threads', 1)) for n in ns})
        e = est[0] if len(est) == 1 else None
        ratio = f'{statistics.median(m) / e:.1f}x' if e else '-'
        print(f'| {f} | {len(ns)} | {"/".join(map(str, thr))} | {min(m):.1f} | {statistics.median(m):.1f} | '
              f'{max(m):.1f} | {"/".join(f"{x:.0f}" for x in est) or "-"} | {ratio} |')

    t0 = min(v['start'] for v in done.values())
    t1 = max(v['end'] for v in done.values())
    th = sum(mins[n] / 60 * done[n].get('threads', 1) for n in mins)
    print(f'\n{len(mins)} jobs finished; wall clock {time.strftime("%Y-%m-%d %H:%M", time.localtime(t0))} to '
          f'{time.strftime("%Y-%m-%d %H:%M", time.localtime(t1))} ({(t1 - t0) / 3600:.1f} h); '
          f'{th:.0f} declared thread-hours.')
    over = sorted(((mins[n] / (jobs[n]['est'] / 60), n) for n in mins if n in jobs and jobs[n].get('est')), reverse=True)
    over = [(r, n) for r, n in over if r > 3]
    if over:
        print('\nMore than 3x over the estimate: ' + ', '.join(f'{n} {mins[n]:.0f} min ({r:.0f}x)' for r, n in over))
    if a.json:
        json.dump({n: round(m, 1) for n, m in sorted(mins.items())}, open(a.json, 'w'), indent=0)


if __name__ == '__main__':
    main()
