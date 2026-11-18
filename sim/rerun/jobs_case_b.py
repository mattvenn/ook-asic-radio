"""Power delivery in case B (2026-11-18): the TT strap pairs swapped (sim/power/pdn.py CASES; tile placed N or FS and
the pin order aren't known). jobs_tall.py runs case A only; this is its power section with CASE B, on the same tile.
    mkdir -p build/rerun_case_b && nohup setsid python3 sim/rerun/sched.py sim/rerun/jobs_case_b.py --budget 28 --load 28 --out build/rerun_case_b > build/rerun_case_b/sched.log 2>&1 &
Results: build/power/*_B*; compare with case A in docs/verify_tall.md section 8. est: the case A times (durations_tall.json) + 10 %.
"""
import json
import os

M642 = 'OSIC_MAGIC=$HOME/.local/magic642/bin'
O = 'OSIC=tools/osic'
MEASURED = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'durations_tall.json')))
JOBS = []
J = JOBS.append
J(dict(name='pwr_pex_B', cmd=f"{M642} tools/osic bash -c 'CASE=B bash sim/power/pex_power.sh' && ! grep -i shorted build/power/ext_B/magic.log",
       threads=1))
J(dict(name='pwr_mesh05_B', cmd='tools/osic python3 sim/power/mesh.py B 0.5', threads=1, deps=['pwr_pex_B']))
J(dict(name='pwr_mesh10_B', cmd='tools/osic python3 sim/power/mesh.py B 1.0', threads=1, deps=['pwr_pex_B']))
for s in ('r_mesh', 'ir_rx', 'em'):
    J(dict(name=f'pwr_{s}_B', cmd=f'{O} python3 sim/power/{s}.py B', threads=2, deps=['pwr_mesh05_B']))
J(dict(name='pwr_z_ac_B', cmd=f'{O} python3 sim/power/z_ac.py B', threads=2, deps=['pwr_mesh10_B']))
J(dict(name='pwr_tran_tx_B', cmd=f'{O} python3 sim/power/tran_tx.py B 30', threads=2, deps=['pwr_mesh10_B']))
for j in JOBS:
    j['est'] = max(60, round(MEASURED[j['name'][:-2]] * 60 * 1.1))
