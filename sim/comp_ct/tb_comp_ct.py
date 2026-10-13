"""Block testbench for comp_ct (schematic vs extracted layout).

VDD 1.8, ibias 1 uA (as bias_gen), inp = 1.0 V + vd, inn = 1.0 V, Cl load on out 10 fF.
  offset: DC sweep of vd at trim 0.9 V (mid code) -> vd where out crosses 0.9 V;
  trim gain: the same at trim 0.9 + 64 LSB (1.8 / 256 per LSB) -> mV per LSB;
  response: at the balance trim (where the threshold is 0, from the two points above), vd steps
            -1 mV -> +1 mV at 20 us, back at 60 us -> out delays (0.9 V).
(H135 trim, 2026-10-13, CM 1.0 V: offset at trim mid -7.2..-7.9 mV, balance code 182-185, trim 0.131-0.139
mV/LSB, 0.36-0.46 us at 1 mV over tt/ss/ff/sf/fs, extracted within 1 code / 1.2 % of the schematic.)
--pex swaps in layout/pex/comp_ct.spice.

    python sim/comp_ct/tb_comp_ct.py [--pex] [corner]
    python sim/comp_ct/tb_comp_ct.py --mc 200 [--cm 1.5] [--temp 27] [--jobs 8] [corner]

--mc N: Monte Carlo with the PDK's mismatch models (<corner>_mm: MC_MM_SWITCH=1, AGAUSS per device;
each `reset` redraws). Inputs at the operating CM (--cm, default 1.5 V: LPF idle 1.45-1.52 V), ideal
1 uA bias. Per sample: the offset at trim mid (0.9 V), and the trim voltage where out switches
with vd = 0, i.e. the DAC code the servo settles to without signal. Samples split over --jobs
single-thread ngspice runs, one sample per run with a random .options seed (before 2026-10-13 the
jobs all drew the same samples: --jobs 8 gave 8 copies of n/8).
Rows in build/mc/comp_<corner>_<temp>_cm<cm>.txt; prints mean, sigma and the 4-sigma code range.
--step also finds the switching trim with vd = +-0.1 mV, so each sample's own trim step at its switching
point (mV/LSB, third column; files *_step).
--vdd V: the bench supply (default 1.8); the trim sweep runs 0..V and a code is V / 256 (the R2R ladder runs
off VDPWR, so vref and the DAC both scale). Files get _vdd<V> when it isn't 1.8.
COMP_SUB=<file> (a comp_ct .subckt), COMP_PRM='<params>' and COMP_TAG=<name> run a modified comparator.
MM_OFF="pfet_01v8_lvt nfet_01v8" in the environment zeroes those device types' Vt mismatch
(sw_mm_vth0_sky130_fd_pr__<type>), to see which devices set the spread (files *_no-<types>).
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.environ.get('OSIC', os.path.join(ROOT, 'tools', 'osic'))
PRM = os.environ.get('COMP_PRM', 'w1=20 l1=1 mt1=10 rdeg=0.85Meg mta=2 lref1=68 lref2=204 wcl=22')
LSB = 1.8 / 256


def subckt():
    if os.environ.get('COMP_SUB'):                  # a modified comp_ct subckt (design exploration)
        return open(os.environ['COMP_SUB']).read()
    out = os.path.join(B, 'tb_comp_ct')
    os.makedirs(out, exist_ok=True)
    subprocess.run([OSIC, 'bash', '-c', 'xschem -n -s -q --tcl "set top_subckt 1" -o build/tb_comp_ct xschem/comp_ct.sch'],
                   cwd=ROOT, capture_output=True)
    s = open(os.path.join(out, 'comp_ct.spice')).read()
    s = re.search(r'^\**\.subckt comp_ct .*?^\**\.ends', s, re.S | re.M).group(0)
    s = re.sub(r'^\**\.(subckt|ends)', r'.\1', s, flags=re.M)
    return s.replace('.subckt comp_ct inp inn trim ibias out VDD VSS', '.subckt comp_ct inp inn trim ibias out VDD VSS ' + PRM, 1)


def deck(corner, pex):
    pdk = os.environ.get('PDK_ROOT', '/foss/pdks')
    sub = '.include ../layout/pex/comp_ct.spice' if pex else subckt()
    inst = 'x1 inp inn trim ibias out VDD 0 comp_ct' + ('' if pex else ' ' + PRM)
    t1 = 0.9 + 64 * LSB
    return f"""* tb_comp_ct ({'extracted' if pex else 'schematic'}), {corner}
.lib {pdk}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
{sub}
VD VDD 0 1.8
Ib VDD ibias 1u
Vcm inn 0 1.0
Vdif inp inn dc 0 pwl(0 -1m 20u -1m 20.01u 1m 60u 1m 60.01u -1m)
Vt trim 0 0.9
{inst}
Co out 0 10f
.options method=GEAR
.control
dc Vdif -20m 20m 0.02m
meas dc off0 when v(out)=0.9 cross=1
echo RES off0=$&off0
set o0 = "$&off0"
reset
alter Vt dc = {t1:.5f}
dc Vdif -40m 40m 0.02m
meas dc off1 when v(out)=0.9 cross=1
echo RES off1=$&off1
set o1 = "$&off1"
reset
let vbal = 0.9 - $o0 * {t1 - 0.9:.5f} / ($o1 - $o0)
echo RES vbal=$&vbal
alter Vt dc = $&vbal
tran 20n 100u 0
meas tran tup TRIG v(inp) VAL=1.0 RISE=1 TARG v(out) VAL=0.9 CROSS=1 TD=19u
meas tran tdn TRIG v(inp) VAL=1.0 FALL=1 TD=50u TARG v(out) VAL=0.9 CROSS=1 TD=59u
echo RES tup=$&tup tdn=$&tdn
.endc
.end
"""


STEP_VD = 0.1e-3


def mc_deck(corner, n, cm, temp, sub, step=False, seed=1, vdd=1.8):
    pdk = os.environ.get('PDK_ROOT', '/foss/pdks')
    loop = ''.join(f"""reset
dc Vdif -40m 40m 0.02m
meas dc off0 when v(out)=0.9 cross=1
set o0 = "$&off0"
dc Vt 0 {vdd:g} 0.5m
meas dc vsw when v(out)=0.9 cross=1
echo MC {k} $o0 $&vsw
""" + (f"""alter Vdif dc = {STEP_VD}
dc Vt 0 {vdd:g} 0.5m
meas dc vp when v(out)=0.9 cross=1
set op = "$&vp"
alter Vdif dc = {-STEP_VD}
dc Vt 0 {vdd:g} 0.5m
meas dc vm when v(out)=0.9 cross=1
alter Vdif dc = 0
echo STEP {k} $op $&vm
""" if step else '') + """destroy all
""" for k in range(n))
    return f"""* tb_comp_ct Monte Carlo, {corner}_mm, {temp} C, CM {cm}
.lib {pdk}/sky130A/libs.tech/combined/sky130.lib.spice {corner}_mm
{sub}
{''.join(f'.param sw_mm_vth0_sky130_fd_pr__{t}=0{chr(10)}' for t in os.environ.get('MM_OFF', '').split())}VD VDD 0 {vdd:g}
Ib VDD ibias 1u
Vcm inn 0 {cm}
Vdif inp inn dc 0
Vt trim 0 0.9
x1 inp inn trim ibias out VDD 0 comp_ct {PRM}
Co out 0 10f
.temp {temp}
.options method=GEAR seed={seed}
.control
set num_threads=1
{loop}.endc
.end
"""


def run_mc(corner, n, cm, temp, jobs, step=False, vdd=1.8):
    import numpy as np
    from concurrent.futures import ThreadPoolExecutor
    sub = subckt()
    os.makedirs(os.path.join(B, 'mc'), exist_ok=True)
    tag = f'comp_{corner}_{temp:g}_cm{cm:g}'
    if os.environ.get('MM_OFF'):
        tag += '_no-' + '-'.join(os.environ['MM_OFF'].split())
    if vdd != 1.8:
        tag += f'_vdd{vdd:g}'
    if step:
        tag += '_step'
    if os.environ.get('COMP_TAG'):
        tag += '_' + os.environ['COMP_TAG']
    # One sample per ngspice run, each with its own .options seed. Without a seed every run starts from
    # the same sequence (parallel jobs drew identical samples), and with one, each reset re-seeds to it.
    per = [1] * n
    seed0 = int.from_bytes(os.urandom(3), 'little')

    def one(j):
        name = f'mc/{tag}_{j}'
        with open(os.path.join(B, name + '.spice'), 'w') as fh:
            fh.write(mc_deck(corner, per[j], cm, temp, sub, step, seed0 + j, vdd))
        subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
        log = open(os.path.join(B, name + '.log')).read()
        rows = re.findall(r'^MC (\d+) (\S+) (\S+)$', log, re.M)
        if not step:
            return [(float(a), float(b)) for _, a, b in rows if a != 'failed' and b != 'failed']
        st = dict((k, (p, m)) for k, p, m in re.findall(r'^STEP (\d+) (\S+) (\S+)$', log, re.M))
        out = []
        for k, a, b in rows:
            p, m = st.get(k, ('failed', 'failed'))
            if 'failed' in (a, b, p, m):
                out.append((float('nan'),) * 3)       # no switching point in 0..1.8 V: out of trim
            else:
                out.append((float(a), float(b), 2 * STEP_VD / abs(float(p) - float(m)) * vdd / 256))
        return out

    with ThreadPoolExecutor(jobs) as ex:
        rows = [r for rr in ex.map(one, range(n)) for r in rr]
    for j in range(n):
        for ext in ('.spice', '.log'):
            os.remove(os.path.join(B, f'mc/{tag}_{j}{ext}'))
    a = np.array(rows)
    np.savetxt(os.path.join(B, 'mc', tag + '.txt'), a,
               header='offset_V trim_switch_V' + (' step_V_per_LSB' if step else ''))
    if step:
        bad = np.isnan(a[:, 2])
        s_mv = a[~bad, 2] * 1e3
        print(f'comp_ct MC {corner} {temp:g} C, CM {cm:g} V: {len(a)}/{n} samples; out of trim {bad.sum()}; '
              f'step mV/LSB median {np.median(s_mv):.3f}; > 0.10: {np.sum(s_mv > 0.10)}, > 0.13: '
              f'{np.sum(s_mv > 0.13)}, > 0.16: {np.sum(s_mv > 0.16)}, > 0.19: {np.sum(s_mv > 0.19)}')
        a = a[~bad]
    off, vsw = a[:, 0] * 1e3, a[:, 1]
    code = vsw / (vdd / 256)
    print(f'comp_ct MC {corner} {temp:g} C, CM {cm:g} V: {len(a)}/{n} samples; offset (trim mid) '
          f'{off.mean():+.2f} mV, sigma {off.std(ddof=1):.2f} mV; switching trim {vsw.mean():.3f} V '
          f'(code {code.mean():.0f}), sigma {vsw.std(ddof=1) * 1e3:.1f} mV ({code.std(ddof=1):.1f} codes); '
          f'4 sigma: {vsw.mean() - 4 * vsw.std(ddof=1):.3f}..{vsw.mean() + 4 * vsw.std(ddof=1):.3f} V; '
          f'samples outside 0.6-1.4 V: {np.sum((vsw < 0.6) | (vsw > 1.4))}')
    return a


def run(corner, pex):
    name = f'tb_comp_ct_{corner}' + ('_pex' if pex else '')
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(corner, pex))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    r = {k: float(v) for k, v in re.findall(r'(\w+)=([-0-9.eE+]+)', ' '.join(re.findall(r'^RES (.*)$', log, re.M)))}
    if 'off0' not in r:
        sys.exit(f'{name}: no results; see build/{name}.log')
    return r


if __name__ == '__main__':
    args = sys.argv[1:]
    opt = {k: args[i + 1] for i, k in enumerate(args) if k in ('--mc', '--cm', '--temp', '--jobs', '--vdd')}
    pos = [a for i, a in enumerate(args) if not a.startswith('-') and (i == 0 or args[i - 1] not in opt)]
    corner = pos[0] if pos else 'tt'
    if '--mc' in opt:
        run_mc(corner, int(opt['--mc']), float(opt.get('--cm', 1.5)), float(opt.get('--temp', 27)),
               int(opt.get('--jobs', 8)), '--step' in args, float(opt.get('--vdd', 1.8)))
        sys.exit()
    pex = '--pex' in args
    r = run(corner, pex)
    gain = (r['off1'] - r['off0']) / 64
    print(f'comp_ct {corner} {"pex" if pex else "sch"}: offset {r["off0"] * 1e3:+.3f} mV (trim mid), '
          f'trim {gain * 1e3:+.4f} mV/LSB, balance code {r.get("vbal", float("nan")) / LSB:.1f}, '
          f'+-1 mV response up/down '
          f'{r.get("tup", float("nan")) * 1e6:.2f}/{r.get("tdn", float("nan")) * 1e6:.2f} us')
