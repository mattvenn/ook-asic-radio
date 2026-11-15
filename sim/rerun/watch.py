"""Watch a sched.py run and return when something needs a person: prints the event(s) and exits.

    python3 sim/rerun/watch.py [--out build/rerun_tall]

Events: a FAIL / STALLED / ERROR / IDLE line in <out>/sched.log, the scheduler's 'all done' line, or its
heartbeat (status.json '_sched') older than --dead minutes (default 5) - the scheduler has died or hung.
It remembers how far into sched.log it has read (<out>/watch.pos), so each event is reported once:
run it again after each exit (from a Claude session: Bash run_in_background, one notification per event).
"""
import argparse
import json
import os
import re
import time

EVENT = re.compile(r'^\S+ (FAIL|STALLED|ERROR|IDLE|all done)\b')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='build/rerun_tall')
    ap.add_argument('--dead', type=float, default=5, help='minutes without a heartbeat')
    ap.add_argument('--poll', type=float, default=60)
    a = ap.parse_args()
    logf, posf = os.path.join(a.out, 'sched.log'), os.path.join(a.out, 'watch.pos')
    pos = int(open(posf).read()) if os.path.exists(posf) else 0
    while True:
        out = []
        if os.path.exists(logf):
            with open(logf) as fh:
                fh.seek(pos)
                text = fh.read()
            if text.endswith('\n') or not text:
                lines = text.splitlines()
                for i, ln in enumerate(lines):
                    if EVENT.match(ln):
                        out.append(ln)
                        if ' ERROR ' in ln:             # the traceback follows: its last line says what
                            tb = [x for x in lines[i + 1:i + 30] if x.strip(' ~^') and not EVENT.match(x)]
                            out.extend('    ' + x for x in tb[-2:])
                pos += len(text.encode())
        try:
            hb = json.load(open(os.path.join(a.out, 'status.json'))).get('_sched')
        except (OSError, ValueError):
            hb = None
        if hb and time.time() - hb['beat'] > a.dead * 60 and not any('all done' in x for x in out):
            age = (time.time() - hb['beat']) / 60
            alive = os.path.exists(f"/proc/{hb['pid']}")
            out.append(f"DEAD scheduler: no heartbeat for {age:.0f} min (pid {hb['pid']} "
                       f"{'still there: hung' if alive else 'gone'})")
        if out:
            open(posf, 'w').write(str(pos))
            print('\n'.join(out), flush=True)
            return
        open(posf, 'w').write(str(pos))
        time.sleep(a.poll)


if __name__ == '__main__':
    main()
