"""gen_det.py's SHIFT_DB recalibrated to the fixed noise file (2026-11-20: -3.8 -> -5.01 dB, noise-only det 1.439 ->
1.44973 V, the swing unchanged): rerun the full-gain mixed-signal set from jobs_tall.py (schematic and extracted
baseband, -92 / -94 dBm, base + 5 seeds; -70 / -90; overload gaps) to check detection with det's DC level where the
transistor-level detector puts it.

    mkdir -p build/rerun_shift && nohup setsid python3 sim/rerun/sched.py sim/rerun/jobs_shift.py --budget 28 \\
        --load 28 --out build/rerun_shift > build/rerun_shift/sched.log 2>&1 &
"""
import os
import runpy

_all = runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jobs_tall.py'))['JOBS']
_keep = lambda n: n in ('gen_det', 'net_mixed') or (n.startswith('mixed_') and not n.endswith(('_lo', '_lopex')))
JOBS = [dict(j, deps=[d for d in j.get('deps', []) if _keep(d)]) for j in _all if _keep(j['name'])]
