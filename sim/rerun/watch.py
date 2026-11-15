"""Watch a sched.py run and return when something changes: prints a status and the new log lines, and exits.

    python3 sim/rerun/watch.py [--out build/rerun_tall] [--every 60] [--settle 2] [--alerts-only]

It returns on:
  - an alert: a FAIL / STALLED / ERROR / IDLE line in <out>/sched.log, the scheduler's 'all done' line, or its
    heartbeat (status.json '_sched') older than --dead minutes (default 5) - the scheduler has died or hung;
  - a change: a job finishing (done / exited / skip / requeue), unless --alerts-only. It waits --settle
    minutes after the first one, so jobs that finish together come back as one report;
  - --every minutes with nothing else to say (0: never): a status only.
The report starts with one status line (job counts, load, what's running), then ALERT lines, then the log.
It remembers how far into sched.log it has read (<out>/watch.pos), so each event is reported once:
run it again after each exit (from a Claude session: Bash run_in_background, one notification per event).
"""
import argparse
import json
import os
import re
import time

EVENT = re.compile(r'^\S+ (FAIL|STALLED|ERROR|IDLE|all done)\b')
CHANGE = re.compile(r'^\S+ (done|exited|skip|requeue)\b')


def status(out):
    """One line: job counts by state, the 1-min load, and the running jobs."""
    try:
        st = json.load(open(os.path.join(out, 'status.json')))
    except (OSError, ValueError):
        return 'status: status.json not readable'
    jobs = {k: v for k, v in st.items() if k != '_sched'}
    n = {}
    for v in jobs.values():
        n[v.get('state')] = n.get(v.get('state'), 0) + 1
    run = sorted(k for k, v in jobs.items() if v.get('state') == 'run')
    return (time.strftime('%H:%M ') + ', '.join(f'{k} {v}' for k, v in sorted(n.items(), key=lambda x: -x[1]))
            + f'; load {os.getloadavg()[0]:.1f}; running: ' + ' '.join(run))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='build/rerun_tall')
    ap.add_argument('--dead', type=float, default=5, help='minutes without a heartbeat')
    ap.add_argument('--poll', type=float, default=60)
    ap.add_argument('--every', type=float, default=60, help='minutes: a status report even with no change (0: off)')
    ap.add_argument('--settle', type=float, default=2, help='minutes to gather changes after the first one')
    ap.add_argument('--alerts-only', action='store_true', help='return only on an alert (the old behaviour)')
    a = ap.parse_args()
    logf, posf = os.path.join(a.out, 'sched.log'), os.path.join(a.out, 'watch.pos')
    pos = int(open(posf).read()) if os.path.exists(posf) else 0
    t0, first_change, alerts, log = time.time(), None, [], []
    while True:
        if os.path.exists(logf):
            with open(logf) as fh:
                fh.seek(pos)
                text = fh.read()
            if text.endswith('\n') or not text:
                lines = text.splitlines()
                for i, ln in enumerate(lines):
                    if EVENT.match(ln):
                        alerts.append(ln)
                        if ' ERROR ' in ln:             # the traceback follows: its last line says what
                            tb = [x for x in lines[i + 1:i + 30] if x.strip(' ~^') and not EVENT.match(x)]
                            alerts.extend('    ' + x for x in tb[-2:])
                    elif ln[:1].isdigit():
                        log.append(ln)
                        if CHANGE.match(ln) and first_change is None:
                            first_change = time.time()
                pos += len(text.encode())
        try:
            hb = json.load(open(os.path.join(a.out, 'status.json'))).get('_sched')
        except (OSError, ValueError):
            hb = None
        if hb and time.time() - hb['beat'] > a.dead * 60 and not any('all done' in x for x in alerts):
            age = (time.time() - hb['beat']) / 60
            alive = os.path.exists(f"/proc/{hb['pid']}")
            alerts.append(f"DEAD scheduler: no heartbeat for {age:.0f} min (pid {hb['pid']} "
                          f"{'still there: hung' if alive else 'gone'})")
        open(posf, 'w').write(str(pos))
        now = time.time()
        changed = not a.alerts_only and first_change is not None and now - first_change >= a.settle * 60
        timed = a.every > 0 and now - t0 >= a.every * 60
        if alerts or changed or timed:
            print(status(a.out))
            print('\n'.join(['ALERT ' + x for x in alerts] + log), flush=True)
            return
        time.sleep(min(a.poll, a.settle * 60) if first_change else a.poll)

if __name__ == '__main__':
    main()
