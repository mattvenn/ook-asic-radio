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
exit code, start and end. A restarted scheduler adopts jobs an earlier instance left running (state
'exited' when they end: their exit status is lost, judge them by their logs). The job file is re-read when it changes, so jobs can be appended while it runs;
a failed job whose command changed runs again. It exits once nothing is running or waiting and
<jobs>.final exists. A restart skips jobs already OK.
Kept moving without anyone watching (2026-11-15):
  stalled: a running job whose processes (its whole session) used no CPU for --stall minutes (default 30) is
           waiting on nothing: its process group is killed and it counts as failed ('stalled'). No wall-time
           limit: long jobs are fine as long as they compute.
  errors:  a round that throws is logged (ERROR + traceback) and the next one carries on; status.json's
           '_sched' entry has a heartbeat (time of the last round) for sim/rerun/watch.py.
  idle:    with jobs waiting and under half the budget in use for 15 min, one IDLE line says why
           (deps, locks, load, reservation, stagger), then again every 15 min while it lasts (--idle).

    nohup setsid python3 sim/rerun/sched.py sim/rerun/jobs_2026-10-13.py --budget 26 > build/rerun/sched.log 2>&1 &
    python3 sim/rerun/sched.py --status [--out build/rerun]
"""
import argparse
import json
import os
import runpy
import signal
import subprocess
import time
import traceback

H_RESERVE = 3600                                          # jobs this long (s) reserve their threads
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))


def load_status(path):
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return {}


def alive(pid):
    """A job's process is the leader of its own session (start_new_session); bash may have exec'd the
    command, so don't match on the name."""
    try:
        return os.getsid(pid) == pid
    except OSError:
        return False


TICK = os.sysconf('SC_CLK_TCK')


def session_cpu(sid):
    """CPU seconds (user + system, live processes) of every process in session sid."""
    tot = 0
    for d in os.listdir('/proc'):
        if not d.isdigit():
            continue
        try:
            f = open(f'/proc/{d}/stat').read()
        except OSError:
            continue
        x = f[f.rindex(')') + 2:].split()             # fields from 3 (state) on
        if int(x[3]) == sid:                           # field 6: session
            tot += int(x[11]) + int(x[12]) + int(x[13]) + int(x[14])   # utime stime cutime cstime
    return tot / TICK


def show(out):
    st = load_status(os.path.join(out, 'status.json'))
    hb = st.pop('_sched', None)
    now = time.time()
    if hb:
        print(f"scheduler heartbeat {now - hb['beat']:.0f} s ago (pid {hb['pid']})")
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
    ap.add_argument('--stall', type=float, default=30, help='minutes with no CPU before a job counts as stalled')
    ap.add_argument('--idle', type=float, default=15, help='minutes under half the budget before an IDLE line')
    a = ap.parse_args()
    if a.status:
        return show(a.out)
    os.makedirs(os.path.join(a.out, 'logs'), exist_ok=True)
    spath = os.path.join(a.out, 'status.json')
    st = load_status(spath)
    st.pop('_sched', None)
    jobs, mtime = {}, None
    cpu = {}                                              # name -> (cpu s, time it last grew)
    idle_since, idle_said = None, 0
    run = {}                                              # name -> Popen
    last = {}                                             # stagger group -> last start time
    adopted = {n: s0['pid'] for n, s0 in st.items()       # still running from an earlier instance
               if s0.get('state') == 'run' and s0.get('pid') and alive(s0['pid'])}

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
            if n not in run and n not in adopted and (s0.get('state') not in ('ok', 'fail', 'stalled', 'skip', 'exited')
                                 or (s0.get('state') in ('fail', 'stalled', 'skip') and s0.get('cmd') != new[n]['cmd'])):
                st[n] = dict(state='wait', threads=new[n]['threads'])
        for n in list(st):                                # dropped from the file: forget it unless running
            if n not in new and n not in run and n not in adopted and st[n]['state'] == 'wait':
                del st[n]
        jobs = {**{n: jobs[n] for n in run}, **{n: dict(threads=st[n]['threads'], deps=[], lock=None, est=0, cmd='')
                                                 for n in adopted if n not in new}, **new}
        mtime = os.path.getmtime(a.jobs)

    def save():
        st['_sched'] = dict(beat=time.time(), pid=os.getpid())
        json.dump(st, open(spath + '.tmp', 'w'), indent=1)
        st.pop('_sched')
        os.replace(spath + '.tmp', spath)

    def log(msg):
        print(time.strftime('%H:%M:%S'), msg, flush=True)

    reload()
    for n, pid in adopted.items():
        log(f'adopted {n} (pid {pid}, started by an earlier instance)')
    nonlocal_idle = [None]

    def explain_idle(now, since):
        """One IDLE line (then one every 15 min) while jobs wait and under half the budget is in use."""
        waiting = [n for n in jobs if st[n]['state'] == 'wait']
        used = sum(jobs[m]['threads'] for m in run) + sum(st[m]['threads'] for m in adopted)
        if not waiting or used >= a.budget / 2:
            return None
        since = since or now
        if now - since >= a.idle * 60:
            why = {}
            for n in waiting:
                j = jobs[n]
                pend = [d for d in j['deps'] if st[d]['state'] not in ('ok', 'exited')]
                if pend:
                    k = 'deps: ' + ', '.join(sorted(set(pend))[:3])
                elif j['lock'] and any(jobs[m]['lock'] == j['lock'] for m in list(run) + list(adopted) if m in jobs):
                    k = f"lock {j['lock']}"
                elif used + j['threads'] > a.budget:
                    k = 'threads / reservation'
                else:
                    k = f'load {os.getloadavg()[0]:.1f} (limit {a.load:g}) or stagger'
                why[k] = why.get(k, 0) + 1
            log(f'IDLE {used}/{a.budget} threads for {(now - since) / 60:.1f} min, {len(waiting)} waiting: '
                + '; '.join(f'{v} on {k}' for k, v in sorted(why.items(), key=lambda kv: -kv[1])[:5]))
            since = now                                   # say it again in --idle min if it lasts
        return since

    def one_round():
        nonlocal mtime
        for n, pid in list(adopted.items()):
            if not alive(pid):                            # its exit status isn't ours to read: judge by its log
                st[n].update(state='exited', rc=None, end=time.time())
                del adopted[n]
                log(f'exited {n} (adopted; check its log)')
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
        # a failed dep fails its dependents; a skipped job waits again once its deps have recovered
        for n, j in jobs.items():
            if st[n]['state'] == 'skip' and not any(st[d]['state'] in ('fail', 'skip', 'stalled') for d in j['deps']):
                st[n].update(state='wait')
                log(f'requeue {n} (its deps recovered)')
            if st[n]['state'] == 'wait' and any(st[d]['state'] in ('fail', 'skip', 'stalled') for d in j['deps']):
                st[n].update(state='skip', rc=None)
                log(f'skip {n} (a dep failed)')
        ready = [n for n, j in jobs.items() if st[n]['state'] == 'wait'
                 and all(st[d]['state'] in ('ok', 'exited') for d in j['deps'])]
        ready.sort(key=lambda n: -jobs[n]['est'])
        reserved = 0                                      # threads held back for a longer job that didn't fit
        for n in ready:
            j = jobs[n]
            used = sum(jobs[m]['threads'] for m in run) + sum(st[m]['threads'] for m in adopted) + reserved
            if used + j['threads'] > a.budget and (run or adopted):
                # don't let shorter jobs keep filling the gap it is waiting for (2026-10-13: an 8-thread
                # job starved behind 4-thread ones): hold its threads unless it can never fit
                # (one job at a time: 2026-11-04 three waiting 8-thread jobs each reserved, 24 of 26, and
                # nothing else started for ~7 h at load 7)
                if j['est'] >= H_RESERVE and j['threads'] <= a.budget and not reserved:
                    reserved += j['threads']
                continue
            if j['lock'] and any(jobs[m]['lock'] == j['lock'] for m in list(run) + list(adopted) if m in jobs):
                continue
            if j.get('stagger') and time.time() - last.get(j['stagger'][0], 0) < j['stagger'][1]:
                continue
            ext = max(0.0, os.getloadavg()[0] - used)    # load from work outside the scheduler
            if (run or adopted) and used + j['threads'] + ext > a.load:
                continue                                  # a smaller job may still fit (was break: stalled)
            fh = open(os.path.join(a.out, 'logs', n + '.log'), 'w')
            run[n] = subprocess.Popen(['bash', '-c', j['cmd']], cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT,
                                      start_new_session=True)
            st[n].update(state='run', start=time.time(), pid=run[n].pid, cmd=j['cmd'])
            if j.get('stagger'):
                last[j['stagger'][0]] = time.time()
            log(f'start {n} ({j["threads"]} thr, est {j["est"] / 60:.0f} min; running {used + j["threads"]})')
        # stalled: no CPU in the job's whole session for --stall minutes
        now = time.time()
        for n, p in list(run.items()) + [(n, None) for n in adopted]:
            sid = p.pid if p else adopted[n]
            c = session_cpu(sid)
            if n not in cpu:
                cpu[n] = (c, now)                         # first look: the clock starts now
                continue
            c0, t0 = cpu[n]
            if c > c0 + 1:                                # more than 1 s of CPU since: it's working
                cpu[n] = (c, now)
            elif now - t0 > a.stall * 60:
                log(f'STALLED {n}: no CPU for {a.stall:g} min ({c:.0f} s in all): killing it')
                try:
                    os.killpg(sid, signal.SIGKILL)
                except OSError:
                    pass
                st[n].update(state='stalled', rc=None, end=now)
                run.pop(n, None)
                adopted.pop(n, None)
                cpu.pop(n, None)
        # idle: jobs waiting, under half the budget in use
        nonlocal_idle[0] = explain_idle(now, nonlocal_idle[0])
        save()

    errs = {}                                             # traceback -> when last logged
    while True:
        try:
            one_round()
        except Exception:                                 # never die quietly: log it, carry on
            tb = traceback.format_exc()
            if time.time() - errs.get(tb, 0) > 600:       # the same error every round: once per 10 min
                errs[tb] = time.time()
                log('ERROR in a scheduler round (carrying on):\n' + tb)
            try:
                save()                                    # keep the heartbeat going
            except Exception:
                pass
        if not run and not adopted and not any(s['state'] == 'wait' for s in st.values()) and os.path.exists(a.jobs + '.final'):
            break                                         # touch <jobs>.final when no more jobs will be added
        time.sleep(10)
    log('all done: ' + ', '.join(f'{k} {sum(1 for s in st.values() if s["state"] == k)}'
                                  for k in ('ok', 'fail', 'stalled', 'skip')))


if __name__ == '__main__':
    main()
