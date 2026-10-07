"""
Host-side control of the demo board running bench/fw/ringkey.py.

    python bench/board.py install           # copy ringkey.py to the board
    python bench/board.py on [ring]
    python bench/board.py off
    python bench/board.py square 1000 [ring]
    python bench/board.py uart 9600 [ring]

Modes that key continuously keep running on the board after this script
exits; the next mpremote connection stops them.
"""
import os
import subprocess
import sys

DEV = os.environ.get(
    'MPREMOTE_DEV',
    '/dev/serial/by-id/usb-MicroPython_Board_in_FS_mode_fe51a94fb9e0008e-if00',
)
FW = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fw', 'ringkey.py')


def _clean_env():
    env = os.environ.copy()
    env.pop('PYTHONHOME', None)
    env.pop('PYTHONPATH', None)
    return env


def mpremote(*args, timeout=30):
    r = subprocess.run(['mpremote', 'connect', DEV, *args],
                       capture_output=True, text=True, timeout=timeout,
                       env=_clean_env())
    out = '\n'.join(l for l in r.stdout.splitlines() if 'BOOT' not in l)
    if r.returncode != 0:
        raise RuntimeError(f'mpremote failed: {r.stderr.strip()}\n{out}')
    return out


def install():
    return mpremote('cp', FW, ':ringkey.py')


def run(mode, rate=1000, ring=1):
    code = f"import ringkey; ringkey.main({mode!r}, {rate}, {ring})"
    if mode in ('on', 'off'):
        return mpremote('exec', code)
    # keep keying after we disconnect
    return mpremote('exec', '--no-follow', code)


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == 'install':
        print(install())
    elif a[0] in ('on', 'off'):
        print(run(a[0], ring=int(a[1]) if len(a) > 1 else 1))
    else:
        print(run(a[0], int(a[1]), int(a[2]) if len(a) > 2 else 1))
