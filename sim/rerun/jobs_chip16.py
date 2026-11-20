"""16 chips through the extracted RX to the slicer (sim/rx/chip16.py; TODO.md 2026-11-19, window 2026-11-20). 28 RF pieces at once,
1 thread each, then the join, the mixed-signal bench and the slicer check.

    cp build_tall/tb_logdet_pex.spice build/ && python3 sim/rx/chip16.py mkbase   (the lumped deck, chip16.py BASE)
    mkdir -p build/rerun_chip16 && touch sim/rerun/jobs_chip16.py.final && nohup setsid python3 sim/rerun/sched.py \\
        sim/rerun/jobs_chip16.py --budget 28 --load 28 --out build/rerun_chip16 > build/rerun_chip16/sched.log 2>&1 &
    python3 sim/rx/chip16.py status            (progress: us/h, elapsed, ETA, chips as they arrive)

CHIP16_TAG=chip16sch CHIP16_BASE=build_tall/tb_logdet.spice: the same pipeline on the schematic RX (the dry run,
~1 h), out to build/chip16sch and build/rerun_chip16sch.
est: 28 at once, 1 thread, PWL noise, machine full (2026-11-20, build/chip16_ab): lumped deck 0.50 us/h a piece
(~6 days); rx_t 0.13 (0.107 with a filesource), ~22-27 days, so not rx_t (Matt: no more than a week).
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rx'))
from chip16 import LEVEL

TAG = os.environ.get('CHIP16_TAG', 'chip16')
ENV = f"CHIP16_TAG={TAG} " + (f"CHIP16_BASE={os.environ['CHIP16_BASE']} " if 'CHIP16_BASE' in os.environ else '')
RATE = 0.50e-6 / 3600 if TAG == 'chip16' else 1.5e-6 / 60        # sim s per wall s: lumped deck 28 at once (build/chip16_ab)
NP = 28
PIECE = 1872e-6 / NP + 3e-6
JOBS = []
J = JOBS.append
J(dict(name=f'{TAG}_prep', cmd=f'{ENV}python3 sim/rx/chip16.py prep', threads=1, est=600))
J(dict(name=f'{TAG}_so', cmd='tools/osic bash sim/mixed/build_so.sh', threads=1, est=300, lock='mixed_so'))
for k in range(NP):
    J(dict(name=f'{TAG}_p{k:02d}', threads=1, est=round(PIECE / RATE), deps=[f'{TAG}_prep'],
           cmd=f"tools/osic bash -c 'cd build/{TAG}/pieces && ngspice -b piece_{k:02d}.spice > piece_{k:02d}.log 2>&1'; "
               f"grep -q '^DONE' build/{TAG}/pieces/piece_{k:02d}.log"))
J(dict(name=f'{TAG}_join', cmd=f'{ENV}python3 sim/rx/chip16.py join', threads=1, est=600,
       deps=[f'{TAG}_p{k:02d}' for k in range(NP)] + [f'{TAG}_so']))
J(dict(name=f'{TAG}_mixed', threads=1, est=2900, deps=[f"{TAG}_join"],
       cmd=f'tools/osic bash -c "cd build/mixed && ngspice -b mixed_{LEVEL}_pex_{TAG}.cir > mixed_{LEVEL}_pex_{TAG}.log 2>&1"; '
           f'test -s build/mixed/mixed_{LEVEL}_pex_{TAG}.raw'))
J(dict(name=f'{TAG}_check', cmd=f'{ENV}python3 sim/rx/chip16.py check', threads=1, est=120, deps=[f'{TAG}_mixed']))
