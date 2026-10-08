"""
Area estimate from the real analog netlist (radio_analog, as netlisted for
tb_radio_analog): every device's evaluated W / L / nf / m, resistor and MIM
geometry, grouped by block. Replaces the hand-typed sizes of
sim/area_estimate.py.

Footprint rules (budgeting only; same spirit as sim/area_estimate.py):
  thin MOS      (W/nf + 1.0) x (nf*(L + 0.6) + 0.6) um, x m
  thick MOS     (W/nf + 2.0) x (nf*(L + 1.0) + 1.5) um, x m   (g5v0d10v5: HV spacing)
  poly R        (W + 1.0) x (L + 3.0) um, x m                  (two contact heads)
  MIM           (W + 1.5) x (L + 1.5) um, x MF                 (met3/capm: may sit over devices)
  std cells     cell area (sky130_fd_sc_hd)
  routing       x ROUTE on device sums; measured layouts (ring, R2R ladder) as they are
  block area    max(routed devices, MIM): MIM can sit over a block's own devices, but a
                block that is mostly capacitor (LPF, averager) is as big as its MIM
Plus the items that aren't in the schematic yet (decap, guard rings).

    python sim/area/area_netlist.py [netlist]     (default build/real/tb_radio_analog.spice)
"""
import math
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
ROUTE = 2.5
TILE = 493.12 * 225.76                       # 3x2 analog tile (tt_analog_3x2_3v3.def)
DIGITAL = (300, 210)                         # hardened macro (openlane run pins_300x210)
HALO = 5                                     # keep-out around the macro, um
STDCELL = {'sky130_fd_sc_hd__inv_2': 3.7536, 'sky130_fd_sc_hd__nand2_2': 6.256}
POLY_W = {'0p35': 0.35, '0p69': 0.69, '1p41': 1.41, '2p85': 2.85, '5p73': 5.73}
# measured layouts: ttsky25b ring (19 stages 228 um^2, magic bbox) scaled to 23; tt08 r2r 71.6 x 54.0
MEASURED = {'xring': 228 * 23 / 19, 'xdac': 71.6 * 54.0}

SUFFIX = {'t': 1e12, 'g': 1e9, 'meg': 1e6, 'k': 1e3, 'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12, 'f': 1e-15}
NUM = re.compile(r'(?<![A-Za-z_0-9.])(\d+\.?\d*(?:[eE][-+]?\d+)?)(meg|[tgkmunpf])?(?![A-Za-z_0-9])', re.I)


def num(s):
    return NUM.sub(lambda m: repr(float(m.group(1)) * SUFFIX.get((m.group(2) or '').lower(), 1)), s)


def ev(expr, env):
    e = num(expr.strip().strip("'").strip('{}'))
    return float(eval(e, {'max': max, 'min': min, 'sqrt': math.sqrt, 'floor': math.floor, 'abs': abs}, env))


def read(path):
    lines = []
    for raw in open(path):
        raw = raw.rstrip('\n')
        if raw.startswith('+') and lines:
            lines[-1] += ' ' + raw[1:]
        elif raw.strip() and not raw.startswith('*'):
            lines.append(raw)
    subckts, cur = {}, None
    for ln in lines:
        t = ln.split()
        if t[0].lower() == '.subckt':
            pins = [x for x in t[2:] if '=' not in x]
            params = dict(x.split('=', 1) for x in t[2:] if '=' in x)
            cur = subckts[t[1]] = {'pins': pins, 'params': params, 'body': []}
        elif t[0].lower() == '.ends':
            cur = None
        elif cur is not None:
            cur['body'].append(ln)
    return subckts


def split_inst(line, subckts):
    t = re.findall(r"\S+='[^']*'|\S+", line)
    params = dict(x.split('=', 1) for x in t[1:] if '=' in x)
    rest = [x for x in t[1:] if '=' not in x]
    return t[0], rest[-1], rest[:-1], params


def footprint(model, p):
    g = lambda k, d=1.0: p.get(k, d)
    if 'fet' in model:
        w, l, nf, m = g('w'), g('l'), max(1, round(g('nf'))), g('mult', g('m', 1))
        if 'g5v0d10v5' in model:
            return (w / nf + 2.0) * (nf * (l + 1.0) + 1.5) * m, 0
        return (w / nf + 1.0) * (nf * (l + 0.6) + 0.6) * m, 0
    if 'res_' in model:
        w = POLY_W[model[-4:]]
        return (w + 1.0) * (g('l') + 3.0) * g('mult', 1), 0
    if 'cap_mim' in model:
        return 0, (g('w') + 1.5) * (g('l') + 1.5) * g('mf', g('m', 1))
    if model in STDCELL:
        return STDCELL[model], 0
    return 0, 0


def walk(subckts, name, env, path, acc):
    sc = subckts[name]
    for ln in sc['body']:
        if ln.startswith('.'):
            continue
        inst, model, nodes, params = split_inst(ln, subckts)
        p = {k.lower(): v for k, v in params.items()}
        here = path + [inst.lower()]
        if model in subckts:
            sub = subckts[model]
            senv = {k.lower(): ev(v, env) for k, v in sub['params'].items()}
            senv.update({k: ev(v, env) for k, v in p.items()})
            walk(subckts, model, senv, here, acc)
        elif inst[0] in 'Xx':
            pv = {k: ev(v, env) for k, v in p.items() if k in ('w', 'l', 'nf', 'mult', 'm', 'mf')}
            d, c = footprint(model.replace('sky130_fd_pr__', ''), pv)
            acc.append((here, model, d, c))
        # plain C/R/V elements inside the blocks (ring wiring stand-ins) cost nothing


def main(path):
    subckts = read(path)
    acc = []
    top = subckts['radio_analog']
    walk(subckts, 'radio_analog', {k.lower(): ev(v, {}) for k, v in top['params'].items()} | {'mm': 0.0}, [], acc)
    blocks = defaultdict(lambda: [0.0, 0.0, 0])
    for here, model, d, c in acc:
        b = here[0]
        if b == 'xtx' and len(here) > 1:
            b = 'xtx.' + here[1]
        blocks[b][0] += d
        blocks[b][1] += c
        blocks[b][2] += 1
    names = {'xbias': 'bias generator', 'xchain': 'gain chain (6 stages)', 'xdet': 'log detector',
             'xlpf': 'LPF (1 MOhm + 10.9 pF)', 'xavg': 'SC averager', 'xcomp': 'comparator + trim pair',
             'xdac': 'R2R trim DAC (measured layout)', 'xctrim': 'trim filter cap', 'xdbg': 'debug TG',
             'xtx.xring': 'TX ring (measured layout)', 'xtx.xls': 'TX level shifter',
             'xtx.xlse_p': 'TX arm-enable LS (p)', 'xtx.xlse_n': 'TX arm-enable LS (n)',
             'xtx.xdrv_p': 'TX driver arm p', 'xtx.xdrv_n': 'TX driver arm n'}
    print(f'{"block":34s} {"devices":>5s} {"dev um2":>9s} {"x route":>9s} {"MIM um2":>9s} {"block":>9s}')
    tot_r = tot_c = tot_b = 0
    for b in sorted(blocks, key=lambda k: list(names).index(k) if k in names else 99):
        d, c, n = blocks[b]
        leaf = b.split('.')[-1]
        routed = MEASURED[leaf] if leaf in MEASURED else d * ROUTE
        tot_r += routed
        tot_c += c
        tot_b += max(routed, c)
        print(f'{names.get(b, b):34s} {n:5d} {d:9,.0f} {routed:9,.0f} {c:9,.0f} {max(routed, c):9,.0f}')
    print(f'{"analog (schematic) total":34s} {"":5s} {"":9s} {tot_r:9,.0f} {tot_c:9,.0f} {tot_b:9,.0f}')
    # not in the schematic yet
    extra = {'VAPWR decap 50 pF (thick MOS ~3 fF/um2 + MIM above, +20 %)': 50e-12 / 5e-15 * 1.2,
             'VDPWR decap ~30 pF for the RX (thin MOS ~8 fF/um2 + MIM, +20 %)': 30e-12 / 10e-15 * 1.2,
             'guard rings / block spacing (~10 % of analog)': 0.10 * tot_b}
    for k, v in extra.items():
        print(f'{k:34s} {"":5s} {"":9s} {v:9,.0f}')
    analog = tot_b + sum(extra.values())
    dig = (DIGITAL[0] + 2 * HALO) * (DIGITAL[1] + 2 * HALO)
    print(f'\n3x2 tile                 {TILE:9,.0f} um2 (493.1 x 225.8)')
    print(f'digital macro + halo     {dig:9,.0f} um2 ({DIGITAL[0]} x {DIGITAL[1]} + {HALO} um)')
    print(f'left for analog          {TILE - dig:9,.0f} um2')
    print(f'analog needs             {analog:9,.0f} um2 (blocks at max(devices, MIM), + decap + spacing)')
    print(f'-> analog fill {analog / (TILE - dig):.0%} of what is left; whole tile {(analog + dig) / TILE:.0%}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build', 'real', 'tb_radio_analog.spice'))
