"""Trim transfer of comp_ct: input-referred threshold vs trim (DAC) voltage, with the trim pair's op.

Sweeps the trim voltage 0.2..1.8 V in 50 mV steps; at each, a DC sweep of vd finds the threshold (the vd
where out crosses 0.9 V), then an op gives sa / sb / vref and the trim pair currents. The nominal chip
balances where the threshold is 0; the "fine-trim window" is the stretch where the step stays ~flat.
Same bench as tb_comp_ct.py (ideal 1 uA bias, CM 1.5 V, VDD 1.8 V, nominal devices).

    python3 sim/comp_ct/trim_curve.py <tag> [corner] [key=val ...]

key=val: a comp_ct param (rdeg=1.2Meg, mta=...), or a device change:
  W3= / W4= (trim pair W), L34= (trim pair L), LR1= / LR2= (vref divider lengths, VDD side / VSS side;
  vref = 1.8 * LR2 / (LR1 + LR2)), WTA= / LTA= (Mta tails), WP= / LP= (mirror Mp1 / Mp2), cm=, temp=.
Writes build/trim/<tag>.json (rows), build/trim/<tag>_sub.spice and <tag>_prm: the modified subckt and its
params, for tb_comp_ct.py's Monte Carlo:
    COMP_SUB=build/trim/<tag>_sub.spice COMP_PRM="$(cat build/trim/<tag>_prm)" COMP_TAG=<tag> \\
        python3 sim/comp_ct/tb_comp_ct.py --mc 200 --step <corner>
Run one first on its own: it netlists comp_ct once into build/trim/comp_ct_sub.spice (parallel xschem runs
overwrite each other's netlist).
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tb_comp_ct as T   # noqa: E402

ROOT, B = T.ROOT, T.B
OUT = os.path.join(B, 'trim')


def build(tag, kv):
    os.makedirs(OUT, exist_ok=True)
    cache = os.path.join(OUT, 'comp_ct_sub.spice')
    if not os.path.exists(cache):
        open(cache, 'w').write(T.subckt())
    sub = open(cache).read()
    prm = dict(p.split('=') for p in T.PRM.split())
    for k in list(kv):
        if k in prm:
            prm[k] = kv.pop(k)

    def dev(names, key, val):
        nonlocal sub
        for n in names:
            line = re.search(rf'^X{n} .*$', sub, re.M).group(0)
            sub = sub.replace(line, re.sub(rf" {key}=\S+", f' {key}={val}', line), 1)
    for k, names, key in (('W3', ['M3'], 'W'), ('W4', ['M4'], 'W'), ('L34', ['M3', 'M4'], 'L'),
                          ('LR1', ['Rr1'], 'L'), ('LR2', ['Rr2'], 'L'),
                          ('WTA', ['Mta_sa', 'Mta_sb'], 'W'), ('LTA', ['Mta_sa', 'Mta_sb'], 'L'),
                          ('WP', ['Mp1', 'Mp2'], 'W'), ('LP', ['Mp1', 'Mp2'], 'L')):
        if k in kv:
            dev(names, key, kv[k])
    P = ' '.join(f'{k}={v}' for k, v in prm.items())
    sub = re.sub(r'(\.subckt comp_ct inp inn trim ibias out VDD VSS) .*', r'\1 ' + P, sub, count=1)
    open(os.path.join(OUT, f'{tag}_sub.spice'), 'w').write(sub)
    open(os.path.join(OUT, f'{tag}_prm'), 'w').write(P)
    return sub, P


def deck(tag, corner, sub, P, cm, temp):
    vts = [round(0.05 * i, 3) for i in range(4, 37)]
    loop = ''.join(f"""alter Vt dc = {vt}
dc Vdif -30m 30m 0.01m
meas dc th when v(out)=0.9 cross=1
set t = "$&th"
op
echo TC {vt} $t $&v(x1.sa) $&v(x1.sb) $&v(x1.vref) $&@m.x1.xm3.msky130_fd_pr__nfet_01v8_lvt[id] \
$&@m.x1.xm4.msky130_fd_pr__nfet_01v8_lvt[id]
""" for vt in vts)
    pdk = os.environ.get('PDK_ROOT', '/foss/pdks')
    return f"""* comp_ct trim curve {tag}
.lib {pdk}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
{sub}
VD VDD 0 1.8
Ib VDD ibias 1u
Vcm inn 0 {cm}
Vdif inp inn dc 0
Vt trim 0 0.9
x1 inp inn trim ibias out VDD 0 comp_ct {P}
Co out 0 10f
.temp {temp}
.options method=GEAR savecurrents
.control
set num_threads=1
{loop}.endc
.end
"""


def main():
    args = sys.argv[1:]
    tag = args[0]
    rest = args[1:]
    corner = rest[0] if rest and '=' not in rest[0] else 'tt'
    kv = dict(a.split('=', 1) for a in rest if '=' in a)
    cm, temp = kv.pop('cm', '1.5'), kv.pop('temp', '27')
    sub, P = build(tag, kv)
    with open(os.path.join(OUT, f'{tag}.spice'), 'w') as fh:
        fh.write(deck(tag, corner, sub, P, cm, temp))
    subprocess.run([T.OSIC, 'bash', '-c', f'cd build && ngspice -b trim/{tag}.spice > trim/{tag}.log 2>&1'],
                   cwd=ROOT)
    rows = []
    for r in re.findall(r'^TC (.*)$', open(os.path.join(OUT, f'{tag}.log')).read(), re.M):
        f = r.split()
        try:
            rows.append([float(x) for x in f[:7]])
        except ValueError:
            rows.append([float(f[0])] + [float('nan')] * 6)
    json.dump(rows, open(os.path.join(OUT, f'{tag}.json'), 'w'))
    print(f'{tag} {corner} {temp} C, CM {cm} V: {P} {kv}')
    print(' vt     th_mV  step_mV/LSB  sa     sb     vref   I3uA  I4uA')
    prev = None
    for o in rows:
        st = ('' if prev is None or o[1] != o[1] or prev[1] != prev[1]
              else f'{abs(o[1] - prev[1]) * 1e3 / ((o[0] - prev[0]) / T.LSB):.3f}')
        print(f'{o[0]:.2f} {o[1] * 1e3:+8.3f} {st:>8}  {o[2]:.3f} {o[3]:.3f} {o[4]:.3f} '
              f'{o[5] * 1e6:5.2f} {o[6] * 1e6:5.2f}')
        prev = o


if __name__ == '__main__':
    main()
