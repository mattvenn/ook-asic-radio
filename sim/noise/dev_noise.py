"""Device noise in transient for ngspice (Harald's review, action 13), without VACASK.

ngspice has no device noise in transient, so each noisy device gets its own repeatable PWL noise current source in
parallel (MOSFET drain-source, resistor terminals), sized so that the source alone gives the same output noise at
434 MHz as the device does in ngspice's .noise analysis:

    S_i (A^2/Hz) = onoise_dev^2 / |H_dev|^2,  H_dev = v(out_p, out_n) per amp injected across the device (AC)

so the sources reproduce .noise by construction, but now the noise starts inside each stage and goes through the real
nonlinear chain (the question: does stage-1 noise drive the later stages into limiting differently from the
workaround's one equivalent source at the antenna?). Two parts per device, written separately:
  thermal: every component but 1/f (channel, rd / rs / rg, body resistors, resistor thermal)
  flicker: the 1/f component at 434 MHz (sky130's BSIM4 puts stage 1's corner near 180 MHz)
Both white to 10 GHz (50 ps samples, as gen_noise.py), the same Gaussian stream per device, so the two files differ
only in level. Limits: white at its 434 MHz level (the 1/f part is too low below ~200 MHz and too high above), not
cyclostationary (sized at the idle operating point), the detector's baseband 1/f is not in it.

The pad's 5 V pass device (xpad_*.xm1, Vds = 0) gives NaN thermal noise in ngspice, and the NaN drops every 1/f
contribution from ngspice's total onoise / inoise (checked: without the pad the per-device sum matches the total; with
it the total equals the sum without 1/f). Here it gets 4kT gds from the operating point instead.

    python3 sim/noise/dev_noise.py [tb] [tstop_s] [seed]       (default build/tb_logdet.spice 3e-6 11)

Writes build/devnoise/: nz_all.txt (per-device .noise), sources.json (S_i, H_i, nodes), and the PWL includes
dev_thermal_s<seed>.inc / dev_all_s<seed>.inc (thermal + flicker), included by sim/noise/run_devnoise.sh.
"""
import json
import math
import os
import re
import subprocess
import sys

import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'build', 'devnoise')
F0, T, KT = 433.92e6, 50e-12, 1.380649e-23 * 300.15
COVER = 0.999                 # keep the devices that make this share of the output noise power
OSIC = os.environ.get('OSIC', os.path.join(ROOT, 'tools', 'osic'))


def ngspice(deck, log):
    with open(os.path.join(OUT, log), 'w') as fh:
        subprocess.run([OSIC, 'bash', '-c', f'cd {OUT} && ngspice -b {deck}'], stdout=fh, stderr=subprocess.STDOUT,
                       cwd=ROOT, check=False)
    return open(os.path.join(OUT, log)).read()


def base_deck(tb):
    """The testbench without its control block (as noise_tran.sh does)."""
    out, skip = [], False
    for l in open(tb):
        if l.startswith('.control'):
            skip = True
        if not skip and l.strip() != '.end':
            out.append(l)
        if l.startswith('.endc'):
            skip = False
    return ''.join(out)


def parse(text):
    """Subcircuits and the top level: name -> (ports, {instance: (nodes, model)}), lower case, + lines joined."""
    lines = []
    for l in text.splitlines():
        if l.startswith('+') and lines:
            lines[-1] += ' ' + l[1:]
        else:
            lines.append(l)
    subs, cur = {'': ([], {})}, ''
    for l in lines:
        t = re.sub(r"'[^']*'", "''", l).split()            # quoted expressions hold spaces
        if not t or t[0].startswith('*'):
            continue
        k = t[0].lower()
        if k == '.subckt':
            cur = t[1].lower()
            subs[cur] = ([x.lower() for x in t[2:] if '=' not in x], {})
        elif k == '.ends':
            cur = ''
        elif k[0] in 'xrmcvi':
            pos = [x.lower() for x in t[1:] if '=' not in x]
            if k[0] == 'x':
                subs[cur][1][k] = (pos[:-1], pos[-1])
            else:
                subs[cur][1][k] = (pos[:2], k[0])
    return subs


def resolve(subs, path):
    """Instance path (x1.xa1.xmn) -> (top-level node names of its first two terminals for R / d, s for MOS, leaf)."""
    toks, sub, ctx, maps = path.split('.'), '', [], [{}]
    for i, tk in enumerate(toks):
        nodes, model = subs[sub][1][tk]
        here = [maps[-1].get(n, n if not ctx or n in ('gnd', '0') else '.'.join(ctx) + '.' + n) for n in nodes]
        if model in subs and i < len(toks) - 1:            # descend
            ports = subs[model][0]
            maps.append(dict(zip(ports, here)))
            ctx.append(tk)
            sub = model
            continue
        mos = 'fet' in model
        return (here[0], here[2]) if mos else (here[0], here[1]), tk
    raise ValueError(path)


def device_path(key):
    s = key[len('onoise') + 1:]
    if s.startswith('m.'):
        return re.sub(r'\.msky130\w*$', '', s[2:])
    if s.startswith('r.'):
        p = s[2:].split('.')
        return '.'.join(p)
    return s                                               # top-level element, e.g. rant_p


def main(tb, tstop, seed):
    os.makedirs(OUT, exist_ok=True)
    base = base_deck(tb)
    subs = parse(base)
    # 1. .noise at 434 MHz, every device's output contribution; op for the NaN device's gds
    with open(os.path.join(OUT, 'nz.spice'), 'w') as fh:
        fh.write(base + f""".control
op
print @m.xpad_p.xm1.msky130_fd_pr__nfet_g5v0d10v5[gds] @m.xpad_n.xm1.msky130_fd_pr__nfet_g5v0d10v5[gds] > op_gds.txt
noise v(out_p,out_n) vant_p lin 1 {F0} {F0} 1
setplot noise1
print all > nz_all.txt
.endc
.end
""")
    ngspice('nz.spice', 'nz.log')
    vals = {}
    for l in open(os.path.join(OUT, 'nz_all.txt')):
        k, _, v = l.partition('=')
        if v.strip():
            vals[k.strip()] = float(v)
    gds = {}
    for l in open(os.path.join(OUT, 'op_gds.txt')):
        m = re.match(r'@m\.(xpad_[pn])\.xm1\S*\[gds\]\s*=\s*(\S+)', l.strip())
        if m:
            gds[m[1] + '.xm1'] = float(m[2])
    onoise_ng = vals['onoise_spectrum']
    # 2. group components per device instance: thermal (all but 1/f) and flicker
    dev = {}
    for k, v in vals.items():
        if not k.startswith('onoise') or k == 'onoise_spectrum':
            continue
        comp = re.search(r'\.msky130\w*\.(\w+)$', k)
        if comp:                                           # MOSFET component
            c, key = comp[1], k[:comp.start()] + '.msky130'
        elif k.endswith(('_thermal', '_1overf', '_shot', '_flicker')):
            key, c = k.rsplit('_', 1)
        else:
            continue                                       # device totals: summed from the components instead
        path = device_path(key)
        # resistor subckts (x0.rbody, x0.rhead ...): one source across the PDK resistor's terminals
        d = dev.setdefault(path, {'th': 0.0, 'fl': 0.0})
        if not math.isfinite(v):
            d['nan'] = True
            continue
        d['fl' if c in ('1overf', 'flicker') else 'th'] += v * v
    # merge sub-resistors into their PDK instance, NaN MOSFETs get 4kT gds
    merged = {}
    for path, d in dev.items():
        try:
            nodes, leaf = resolve(subs, path)
        except (KeyError, ValueError):
            print('skip (no instance):', path)
            continue
        inst = path if leaf == path.split('.')[-1] else path[:path.index(leaf) + len(leaf)]
        m = merged.setdefault(inst, {'th': 0.0, 'fl': 0.0, 'nodes': nodes})
        m['th'] += d['th']
        m['fl'] += d['fl']
        if d.get('nan'):
            m['nan'] = True
    tot = sum(m['th'] + m['fl'] for m in merged.values())
    keep, acc = [], 0.0
    for inst, m in sorted(merged.items(), key=lambda x: -(x[1]['th'] + x[1]['fl'])):
        if acc / tot >= COVER and not m.get('nan'):
            continue
        keep.append(inst)
        acc += m['th'] + m['fl']
    print(f'.noise: ngspice total {onoise_ng:.4e} V/rtHz; per-device sum {math.sqrt(tot):.4e} (thermal '
          f'{math.sqrt(sum(m["th"] for m in merged.values())):.4e}); {len(keep)} of {len(merged)} devices kept '
          f'({100 * acc / tot:.2f} %)')
    # 3. H per kept device: unit AC current across its terminals, antenna AC off
    inj = ''.join(f'Iinj{i} {merged[p]["nodes"][0]} {merged[p]["nodes"][1]} dc 0 ac 0\n' for i, p in enumerate(keep))
    ctl = ['alter @vant_p[acmag]=0', 'alter @vant_n[acmag]=0']
    for i in range(len(keep)):
        ctl += [f'alter @iinj{i}[acmag]=1', f'ac lin 1 {F0} {F0}', f'let h = mag(v(out_p) - v(out_n))', 'let hh = h[0]',
                f'echo HINJ {i} $&hh', 'destroy all', f'alter @iinj{i}[acmag]=0']
    with open(os.path.join(OUT, 'hinj.spice'), 'w') as fh:
        fh.write(base + inj + '.control\n' + '\n'.join(ctl) + '\n.endc\n.end\n')
    log = ngspice('hinj.spice', 'hinj.log')
    h = {int(a): float(b) for a, b in re.findall(r'^HINJ (\d+) (\S+)', log, re.M)}
    assert len(h) == len(keep), f'AC runs: {len(h)} of {len(keep)} (see hinj.log)'
    # 4. source densities and the PWL files
    src = []
    for i, p in enumerate(keep):
        m = merged[p]
        th = m['th']
        if m.get('nan'):                                   # Vds = 0 pass device: channel noise 4kT gds
            th_s = 4 * KT * gds.get(p, 0.0)
            note = f'NaN in ngspice: 4kT gds, gds {gds.get(p, 0):.4g} S'
        else:
            th_s, note = th / h[i] ** 2, ''
        src.append(dict(dev=p, nodes=m['nodes'], h=h[i], s_th=th_s, s_fl=m['fl'] / h[i] ** 2,
                        out_th=math.sqrt(th_s) * h[i], out_fl=math.sqrt(m['fl']), note=note))
    json.dump(dict(f0=F0, onoise_ngspice=onoise_ng, sources=src), open(os.path.join(OUT, 'sources.json'), 'w'),
              indent=1)
    out_th = math.sqrt(sum(s['out_th'] ** 2 for s in src))
    out_all = math.sqrt(sum(s['out_th'] ** 2 + s['out_fl'] ** 2 for s in src))
    print(f'sources: output noise thermal {out_th:.4e}, thermal + 1/f {out_all:.4e} V/rtHz '
          f'(ngspice total {onoise_ng:.4e}: NF + {20 * math.log10(out_th / onoise_ng):+.2f} / '
          f'{20 * math.log10(out_all / onoise_ng):+.2f} dB)')
    for s in src:
        print(f'  {s["dev"]:<28} {s["nodes"][0]:>14} {s["nodes"][1]:>14}  |H| {s["h"]:9.3e} V/A  '
              f'th {math.sqrt(s["s_th"]) * 1e12:8.3f} pA/rtHz  1/f {math.sqrt(s["s_fl"]) * 1e12:8.3f}  {s["note"]}')
    rng = np.random.default_rng(seed)
    n = int(round(tstop / T)) + 2
    t = np.arange(n) * T
    z = {s['dev']: rng.standard_normal(n) for s in src}   # one stream per device, shared by both files
    for name, fl in ((f'dev_thermal_s{seed}.inc', 0), (f'dev_all_s{seed}.inc', 1)):
        with open(os.path.join(OUT, name), 'w') as fh:
            fh.write(f'* device noise currents ({"thermal + 1/f" if fl else "thermal"} at {F0 / 1e6:.2f} MHz, white), '
                     f'T={T * 1e12:.0f} ps, seed {seed}: sim/noise/dev_noise.py\n')
            for i, s in enumerate(src):
                sig = math.sqrt((s['s_th'] + fl * s['s_fl']) / (2 * T))
                v = z[s['dev']] * sig
                fh.write(f'* {s["dev"]}\nInz{i} {s["nodes"][0]} {s["nodes"][1]} pwl(\n')
                for k in range(0, n, 8):
                    fh.write('+ ' + ' '.join(f'{t[j]:.6e} {v[j]:.4e}' for j in range(k, min(k + 8, n))) + '\n')
                fh.write('+ )\n')
    print('wrote', os.path.join(OUT, f'dev_thermal_s{seed}.inc'), os.path.join(OUT, f'dev_all_s{seed}.inc'))


if __name__ == '__main__':
    a = sys.argv[1:]
    main(a[0] if a else os.path.join(ROOT, 'build', 'tb_logdet.spice'), float(a[1]) if len(a) > 1 else 3e-6,
         int(a[2]) if len(a) > 2 else 11)
