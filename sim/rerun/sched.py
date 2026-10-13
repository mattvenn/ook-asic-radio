"""Run a list of verification jobs on one machine within a CPU budget (sim-0: 28 CPUs).

A job file (Python) defines JOBS = [dict(name=, cmd=, threads=, est=, deps=[...], lock=None), ...]:
  threads: CPUs the job keeps busy (ngspice NT / num_threads; 1 for python, magic, verilator ...)
  est:     expected wall time, s (longest first: the long runs start early)
  deps:    names that must have finished OK first
  lock:    jobs with the same lock never run together (a shared netlist / output file)
  stagger: (group, s): a job of the group starts at least s after the previous one (scripts that rewrite
           a shared netlist at start, then only read their own copy)
A job starts when its deps are done, its lock is free, the threads of the running jobs plus its own stay
within --budget, and the 1-minute load average is below --load (so work running outside the scheduler
counts too). Each job's output goes to <out>/logs/<name>.log; <out>/status.json has every job's state,
exit code, start and end. The job file is re-read when it changes, so jobs can be appended while it runs;
a failed job whose command changed runs again. It exits once nothing is running or waiting and
<jobs>.final exists. A restart skips jobs already OK.

    nohup setsid python3 sim/rerun/sched.py sim/rerun/jobs_2026-10-13.py --budget 26 > build/rerun/sched.log 2>&1 &
    python3 sim/rerun/sched.py --status [--out build/rerun]
"""
import argparse
import json
import os
import runpy
import subprocess
import time

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))


def load_status(path):
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return {}


def show(out):
    st = load_status(os.path.join(out, 'status.json'))
    now = time.time()
    for name, s in sorted(st.items(), key=lambda kv: (kv[1]['state'], kv[0])):
        t = (s.get('end') or now) - s['start'] if s.get('start') else 0
        print(f"{s['state']:8s} {name:40s} rc={s.get('rc')!s:5s} {t / 60:7.1f} min  thr={s.get('threads')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('jobs', nargs='?')
    ap.add_argument('--budget', type=int, default=26)
    ap.add_argument('--load', type=float, default=28.0)
    ap.add_argument('--out', default=os.path.join(ROOT, 'build', 'rerun'))
    ap.add_argument('--status', action='store_true')
    a = ap.parse_args()
    if a.status:
        return show(a.out)
    os.makedirs(os.path.join(a.out, 'logs'), exist_ok=True)
    spath = os.path.join(a.out, 'status.json')
    st = load_status(spath)
    jobs, mtime = {}, None
    run = {}                                              # name -> Popen
    last = {}                                             # stagger group -> last start time

    def reload():
        """(Re)read the job file: jobs can be added while the scheduler runs. Running / finished jobs
        keep their state; a new or not-yet-OK job waits."""
        nonlocal jobs, mtime
        new = {j['name']: {**dict(deps=[], lock=None, est=600, threads=1), **j}
               for j in runpy.run_path(a.jobs)['JOBS']}
        for j in new.values():
            for d in j['deps']:
                assert d in new, f"{j['name']}: unknown dep {d}"
        for n in new:                                     # new, unfinished, or failed with a changed command
            s0 = st.get(n, {})
            if n not in run and (s0.get('state') not in ('ok', 'fail', 'skip')
                                 or (s0.get('state') in ('fail', 'skip') and s0.get('cmd') != new[n]['cmd'])):
                st[n] = dict(state='wait', threads=new[n]['threads'])
        for n in list(st):                                # dropped from the file: forget it unless running
            if n not in new and n not in run and st[n]['state'] == 'wait':
                del st[n]
        jobs = {**{n: jobs[n] for n in run}, **new}
        mtime = os.path.getmtime(a.jobs)

    def save():
        json.dump(st, open(spath + '.tmp', 'w'), indent=1)
        os.replace(spath + '.tmp', spath)

    def log(msg):
        print(time.strftime('%H:%M:%S'), msg, flush=True)

    reload()
    while True:
        if os.path.getmtime(a.jobs) != mtime:
            try:
                reload()
                log('job file reloaded')
            except Exception as e:                       # a half-written file: try again next round
                log(f'job file not loaded ({e})')
        for n, p in list(run.items()):
            rc = p.poll()
            if rc is not None:
                st[n].update(state='ok' if rc == 0 else 'fail', rc=rc, end=time.time())
                del run[n]
                log(f'{"done" if rc == 0 else "FAIL"} {n} (rc {rc}, {(st[n]["end"] - st[n]["start"]) / 60:.1f} min)')
        # a failed dep fails its dependents
        for n, j in jobs.items():
            if st[n]['state'] == 'wait' and any(st[d]['state'] in ('fail', 'skip') for d in j['deps']):
                st[n].update(state='skip', rc=None)
                log(f'skip {n} (a dep failed)')
        ready = [n for n, j in jobs.items() if st[n]['state'] == 'wait'
                 and all(st[d]['state'] == 'ok' for d in j['deps'])]
        ready.sort(key=lambda n: -jobs[n]['est'])
        for n in ready:
            j = jobs[n]
            used = sum(jobs[m]['threads'] for m in run)
            if used + j['threads'] > a.budget and run:
                continue
            if j['lock'] and any(jobs[m]['lock'] == j['lock'] for m in run):
                continue
            if j.get('stagger') and time.time() - last.get(j['stagger'][0], 0) < j['stagger'][1]:
                continue
            ext = max(0.0, os.getloadavg()[0] - used)    # load from work outside the scheduler
            if run and used + j['threads'] + ext > a.load:
                break
            fh = open(os.path.join(a.out, 'logs', n + '.log'), 'w')
            run[n] = subprocess.Popen(['bash', '-c', j['cmd']], cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT,
                                      start_new_session=True)
            st[n].update(state='run', start=time.time(), pid=run[n].pid, cmd=j['cmd'])
            if j.get('stagger'):
                last[j['stagger'][0]] = time.time()
            log(f'start {n} ({j["threads"]} thr, est {j["est"] / 60:.0f} min; running {used + j["threads"]})')
        save()
        if not run and not any(s['state'] == 'wait' for s in st.values()) and os.path.exists(a.jobs + '.final'):
            break                                         # touch <jobs>.final when no more jobs will be added
        time.sleep(10)
    log('all done: ' + ', '.join(f'{k} {sum(1 for s in st.values() if s["state"] == k)}'
                                  for k in ('ok', 'fail', 'skip')))


if __name__ == '__main__':
    main()
