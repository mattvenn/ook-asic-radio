"""Block testbench for avg_sc (schematic vs extracted layout), short form.

The digital's sc_phi timing (13 us period: phi1 6.1 us, 0.4 us gap, phi2 6.1 us), VDD 1.8.
20 cycles from out = cs = 1.0 V (.ic through the operating point, not uic: in the extracted
netlist the cap plates sit behind wire R, and uic would start them at 0 V):
  step run: in = 1.010 V. The error left after n cycles is e0 (1 - a)^n, so
            a = Cs / (Cs + Cavg) (incl. parasitics) and tau = T / -ln(1 - a);
  hold run: in = 1.000 V: out's drift over 20 cycles is the charge-injection offset.
(sim/... tb_avg ran 0.47-0.48 ms for the schematic over the full step response.)
--pex swaps in layout/pex/avg_sc.spice.

    python sim/avg_sc/tb_avg_sc.py [--pex] [corner]
    python sim/avg_sc/tb_avg_sc.py --mc 200 [--temp 27] [--jobs 8] [corner]

--mc N: Monte Carlo with the PDK's mismatch models (<corner>_mm; each `reset` redraws), both runs
per sample. Reports the hold drift over the 20 cycles and the settled injection offset it implies
(drift / (1 - (1 - a)^20)), split over --jobs single-thread runs. Rows in build/mc/avg_<corner>_<temp>.txt.
"""
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.environ.get('OSIC', os.path.join(ROOT, 'tools', 'osic'))
T, NCYC, V0, DV = 13e-6, 20, 1.0, 0.010
PRM = 'ncs=1 nca=2 wcs=7'


def subckt():
    out = os.path.join(B, 'tb_avg_sc')
    os.makedirs(out, exist_ok=True)
    subprocess.run([OSIC, 'bash', '-c', 'xschem -n -s -q --tcl "set top_subckt 1" -o build/tb_avg_sc xschem/avg_sc.sch'],
                   cwd=ROOT, capture_output=True)
    s = open(os.path.join(out, 'avg_sc.spice')).read()
    s = re.search(r'^\**\.subckt avg_sc .*?^\**\.ends', s, re.S | re.M).group(0)
    s = re.sub(r'^\**\.(subckt|ends)', r'.\1', s, flags=re.M)
    return s.replace('.subckt avg_sc in phi1 phi2 out VDD VSS', '.subckt avg_sc in phi1 phi2 out VDD VSS ' + PRM, 1)


def deck(corner, pex):
    pdk = os.environ.get('PDK_ROOT', '/foss/pdks')
    sub = '.include ../layout/pex/avg_sc.spice' if pex else subckt()
    inst = 'x1 in phi1 phi2 out VDD 0 avg_sc' + ('' if pex else ' ' + PRM)
    t1 = NCYC * T
    runs = ''
    for tag, vin in (('step', V0 + DV), ('hold', V0)):
        runs += f"""alter Vin dc = {vin}
tran 20n {t1:.4e} 0
meas tran o_{tag} find v(out) at={t1 - 0.2e-6:.4e}
echo RES o_{tag}=$&o_{tag}
reset
"""
    return f"""* tb_avg_sc ({'extracted' if pex else 'schematic'}), {corner}
.lib {pdk}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
{sub}
VD VDD 0 1.8
Vin in 0 {V0}
Vphi1 phi1 0 pulse(0 1.8 0 10n 10n 6.09u 13u)
Vphi2 phi2 0 pulse(0 1.8 6.5u 10n 10n 6.09u 13u)
{inst}
.ic v(out)={V0} v(x1.cs)={V0}
.options method=GEAR
.control
save v(out)
{runs}.endc
.end
"""


def mc_deck(corner, n, temp, sub):
    pdk = os.environ.get('PDK_ROOT', '/foss/pdks')
    t1 = NCYC * T
    loop = ''
    for k in range(n):
        loop += 'reset\n'
        for tag, vin in (('step', V0 + DV), ('hold', V0)):
            loop += (f'alter Vin dc = {vin}\ntran 20n {t1:.4e} 0\n'
                     f'meas tran o_{tag} find v(out) at={t1 - 0.2e-6:.4e}\nset v_{tag} = "$&o_{tag}"\ndestroy all\n')
        loop += f'echo MC {k} $v_step $v_hold\n'
    return f"""* tb_avg_sc Monte Carlo, {corner}_mm, {temp} C
.lib {pdk}/sky130A/libs.tech/combined/sky130.lib.spice {corner}_mm
{sub}
VD VDD 0 1.8
Vin in 0 {V0}
Vphi1 phi1 0 pulse(0 1.8 0 10n 10n 6.09u 13u)
Vphi2 phi2 0 pulse(0 1.8 6.5u 10n 10n 6.09u 13u)
x1 in phi1 phi2 out VDD 0 avg_sc {PRM}
.ic v(out)={V0} v(x1.cs)={V0}
.temp {temp}
.options method=GEAR
.control
set num_threads=1
save v(out)
{loop}.endc
.end
"""


def run_mc(corner, n, temp, jobs):
    import numpy as np
    from concurrent.futures import ThreadPoolExecutor
    sub = subckt()
    os.makedirs(os.path.join(B, 'mc'), exist_ok=True)
    tag = f'avg_{corner}_{temp:g}'
    per = [n // jobs + (j < n % jobs) for j in range(jobs)]

    def one(j):
        name = f'mc/{tag}_{j}'
        with open(os.path.join(B, name + '.spice'), 'w') as fh:
            fh.write(mc_deck(corner, per[j], temp, sub))
        subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
        rows = re.findall(r'^MC \d+ (\S+) (\S+)$', open(os.path.join(B, name + '.log')).read(), re.M)
        return [(float(a), float(b)) for a, b in rows]

    with ThreadPoolExecutor(jobs) as ex:
        rows = np.array([r for rr in ex.map(one, range(jobs)) for r in rr])
    off = rows[:, 1] - V0
    e = (V0 + DV) - (rows[:, 0] - off)
    a = 1 - (e / DV) ** (1 / NCYC)
    ss = off / (1 - (1 - a) ** NCYC)
    np.savetxt(os.path.join(B, 'mc', tag + '.txt'), np.column_stack([rows, a, ss]),
               header='o_step_V o_hold_V a settled_offset_V')
    print(f'avg_sc MC {corner} {temp:g} C: {len(rows)}/{n} samples; a {a.mean():.4f} (sigma {a.std(ddof=1):.4f}); '
          f'hold drift over {NCYC} cycles {off.mean() * 1e3:+.3f} mV (sigma {off.std(ddof=1) * 1e3:.3f}); '
          f'settled offset {ss.mean() * 1e3:+.3f} mV, sigma {ss.std(ddof=1) * 1e3:.3f} mV')
    return rows


def run(corner, pex):
    name = f'tb_avg_sc_{corner}' + ('_pex' if pex else '')
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(corner, pex))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    r = {k: float(v) for k, v in re.findall(r'^RES (\w+)=([-0-9.eE+]+)', log, re.M)}
    if 'o_hold' not in r:
        sys.exit(f'{name}: no results; see build/{name}.log')
    off = r['o_hold'] - V0                       # charge-injection drift over NCYC cycles
    e = (V0 + DV) - (r['o_step'] - off)          # step error left, injection removed
    a = 1 - (e / DV) ** (1 / NCYC)
    return dict(a=a, tau=T / -math.log(1 - a), off=off)


if __name__ == '__main__':
    args = sys.argv[1:]
    opt = {k: args[i + 1] for i, k in enumerate(args) if k in ('--mc', '--temp', '--jobs')}
    pos = [a for i, a in enumerate(args) if not a.startswith('-') and (i == 0 or args[i - 1] not in opt)]
    corner = pos[0] if pos else 'tt'
    if '--mc' in opt:
        run_mc(corner, int(opt['--mc']), float(opt.get('--temp', 27)), int(opt.get('--jobs', 8)))
        sys.exit()
    pex = '--pex' in args
    r = run(corner, pex)
    print(f'avg_sc {corner} {"pex" if pex else "sch"}: Cs/(Cs+Cavg) {r["a"]:.4f}, tau {r["tau"] * 1e3:.3f} ms, '
          f'offset drift over {NCYC} cycles {r["off"] * 1e3:+.3f} mV')
