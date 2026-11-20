"""16 chips through the extracted RX to the slicer (sim/rx/chip16.py; TODO.md 2026-11-19, window 2026-11-20). 28 RF pieces at once,
1 thread each, then the join, the mixed-signal bench and the slicer check.

    cp build_tall/tb_logdet_pex.spice build/   (or regenerate: jobs_tall.py's pexsim job)
    mkdir -p build/rerun_chip16 && touch sim/rerun/jobs_chip16.py.final && nohup setsid python3 sim/rerun/sched.py \\
        sim/rerun/jobs_chip16.py --budget 28 --load 28 --out build/rerun_chip16 > build/rerun_chip16/sched.log 2>&1 &
    python3 sim/rx/chip16.py status            (progress: us/h, elapsed, ETA, chips as they arrive)

CHIP16_TAG=chip16sch CHIP16_BASE=build_tall/tb_logdet.spice: the same pipeline on the schematic RX (the dry run,
~1 h), out to build/chip16sch and build/rerun_chip16sch.
est: rx_t 2 us at -90 dBm took 216 min on 2 threads with 12 of 28 CPUs busy (2026-11-19, build/piece_timing):
0.55 us/h. 1 thread and a full machine are not measured: the first hours of status will say.
"""
import os

TAG = os.environ.get('CHIP16_TAG', 'chip16')
ENV = f"CHIP16_TAG={TAG} " + (f"CHIP16_BASE={os.environ['CHIP16_BASE']} " if 'CHIP16_BASE' in os.environ else '')
RATE = 0.55e-6 / 3600 if TAG == 'chip16' else 1.5e-6 / 60        # sim s per wall s (sch: 1.2 us in 0.8 min)
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
       cmd=f'tools/osic bash -c "cd build/mixed && ngspice -b mixed_-85_pex_{TAG}.cir > mixed_-85_pex_{TAG}.log 2>&1"; '
           f'test -s build/mixed/mixed_-85_pex_{TAG}.raw'))
J(dict(name=f'{TAG}_check', cmd=f'{ENV}python3 sim/rx/chip16.py check', threads=1, est=120, deps=[f'{TAG}_mixed']))
