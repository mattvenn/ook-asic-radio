# Simulation netlist of lna_chain from the kpex 2.5D extraction, with or without the substrate network.
#   venv/bin/python mknet.py --case a|b [--Y h1_n300] [--gscale 1|0.1|0.01] --out sim/b1/lna_chain_sub.spice
# Case a: every device bulk and every VSUBS cap on VSS (today's assumption).
# Case b: each NMOS bulk on its own substrate port node (sub_<port>); Rb / stage-load resistor
#   bulks on rb_p/n and on the port of the device whose drain they load; each net's VSUBS cap split
#   over ports / VSS by vsubs_map.json; the solved port network (Y, taps = VSS) as resistors,
#   conductances multiplied by --gscale.
# The subckt has the schematic's port order (inp inn ibias vcm outp outn o1p o1n ... o5n VDD VSS).
import argparse, json, os, re, numpy as np
D = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--case', required=True, choices=['a', 'b'])
ap.add_argument('--Y', default='h1_n300')
ap.add_argument('--gscale', type=float, default=1.0)
ap.add_argument('--kpex', default=f'{D}/../kpex/h100/lna_chain__lna_chain/lna_chain_k25d_pex_netlist.spice')
ap.add_argument('--gmin', type=float, default=1e-12)    # drop links below this (S)
ap.add_argument('--out', required=True)
ap.add_argument('--cutall', action='store_true')   # drop every link between different stages (input zone = stage 0)
ap.add_argument('--cut', action='store_true')   # drop the links between the late stages (st3-st6) and the input zone (Cin, Rb, Mref, st1)
a = ap.parse_args()
g = json.load(open(f'{D}/geom.json')); meta = g['meta']
vmap = json.load(open(f'{D}/vsubs_map.json'))
PORTS = 'inp inn ibias vcm outp outn o1p o1n o2p o2n o3p o3n o4p o4n o5p o5n VDD VSS'.split()

# kpex netlist: join continuation lines
lines = []
for ln in open(a.kpex):
    ln = ln.rstrip('\n')
    if ln.startswith('+'): lines[-1] += ' ' + ln[1:].strip()
    elif ln.strip() and not ln.startswith('*'): lines.append(ln)
SI = {'P': 1e-12, 'U': 1e-6, 'F': 1e-15, 'A': 1e-18, 'N': 1e-9}
def num(s):
    s = s.upper(); m = re.match(r'^([-0-9.E+]+)([A-Z]?)$', s)
    return float(m.group(1)) * SI.get(m.group(2), 1)
mos_ports = {n: m for n, m in meta.items() if m['kind'] == 'mos'}
def find_mos(d, gt, s):
    for n, m in mos_ports.items():
        t = m['nets']
        if t['G'] == gt and {t['S'], t['D']} == {s, d}: return n
    raise SystemExit(f'no port for device {d} {gt} {s}')
drain_port = {}
for n, m in mos_ports.items():
    for t in (m['nets']['D'], m['nets']['S']):
        if t not in ('VSS',) and n.startswith('st') and not ('mtail' in n): drain_port.setdefault(t, n)
for n, m in mos_ports.items():
    if m['nets']['D'] not in drain_port: drain_port[m['nets']['D']] = n

out = []; ccount = 0; vsubs = {}
def bulk(port): return 'VSS' if a.case == 'a' else f'sub_{port}'
for ln in lines:
    f = ln.split()
    if f[0].startswith('.SUBCKT'): continue
    if f[0].startswith('.ENDS') or f[0] == '.END': continue
    if f[0].startswith('M'):
        d, gt, s, b, model = f[1:6]
        p = {k: v for k, v in (x.split('=') for x in f[6:])}
        port = find_mos(d, gt, s); nf = meta[port]['nf']
        out.append(f"X{port} {d} {gt} {s} {bulk(port)} {model} L={num(p['L']) * 1e6:.4g} W={num(p['W']) * 1e6:.4g} nf={nf} "
                   f"ad={num(p['AD']) * 1e12:.4g} as={num(p['AS']) * 1e12:.4g} pd={num(p['PD']) * 1e6:.4g} ps={num(p['PS']) * 1e6:.4g} mult=1")
    elif f[0].startswith('R'):
        n1, n2, b, val, model = f[1:6]
        p = {k: v for k, v in (x.split('=') for x in f[6:])}
        if 'g1p' in (n1, n2): port = 'rb_p'
        elif 'g1n' in (n1, n2): port = 'rb_n'
        else: port = drain_port[n2 if n1 == 'VDD' else n1]
        out.append(f"X{f[0][1:].replace('$', 'r')} {n1} {n2} {bulk(port)} {model} L={num(p['L']) * 1e6:.4g} mult=1")
    elif f[0] == 'C':          # MIM devices
        ccount += 1; out.append(f'Cmim{ccount} {f[1]} {f[2]} {f[3]}')
    elif f[0].startswith('Cext'):
        n1, n2, v = f[1:4]
        if 'VSUBS' in (n1, n2):
            net = n2 if n1 == 'VSUBS' else n1
            vsubs[net] = vsubs.get(net, 0) + num(v)
            continue
        n1 = 'VSS' if n1 == 'sky130_gnd' else n1; n2 = 'VSS' if n2 == 'sky130_gnd' else n2
        if n1 == n2: continue
        out.append(f'{f[0]} {n1} {n2} {v}')
    else:
        raise SystemExit('unknown line ' + ln)
# VSUBS caps
for net, c in sorted(vsubs.items()):
    net_ = 'VSS' if net == 'sky130_gnd' else net
    if net_ == 'VSS': continue        # VSS to substrate: shorted by the taps anyway
    if a.case == 'a' or net not in vmap:
        out.append(f'Csub_{net} {net_} VSS {c:.5g}')
    else:
        for k, (dst, fr) in enumerate(vmap[net].items()):
            if fr * c < 1e-19: continue
            out.append(f'Csub_{net}_{k} {net_} {"VSS" if dst == "VSS" else "sub_" + dst} {fr * c:.5g}')
# substrate network
nlink = 0; gdrop = 0.0
if a.case == 'b':
    Y = np.load(f'{D}/{a.Y}/Y.npy') * a.gscale
    names = json.load(open(f'{D}/{a.Y}/info.json'))['names']
    P = len(names)
    for i in range(P):
        gi = Y[i].sum()
        out.append(f'Rsub_{names[i]} sub_{names[i]} VSS {1 / gi:.6g}')
        for j in range(i + 1, P):
            gij = -Y[i, j]
            if gij < a.gmin: gdrop += max(gij, 0); continue
            late = lambda n: n[:3] in ('st3', 'st4', 'st5', 'st6')
            early = lambda n: n.startswith(('st1', 'cin', 'rb', 'mref'))
            if a.cut and ((late(names[i]) and early(names[j])) or (late(names[j]) and early(names[i]))):
                gdrop += gij; continue
            grp = lambda n: n[:3] if n.startswith('st') else 'in'
            if a.cutall and grp(names[i]) != grp(names[j]) and not {grp(names[i]), grp(names[j])} == {'in', 'st1'}:
                gdrop += gij; continue
            out.append(f'Rsub_{names[i]}__{names[j]} sub_{names[i]} sub_{names[j]} {1 / gij:.6g}'); nlink += 1
hdr = [f'* lna_chain from kpex 2.5D (CC, halo 100) + substrate case {a.case} (Y {a.Y}, gscale {a.gscale}) - build/substrate/mknet.py',
       '.subckt lna_chain ' + ' '.join(PORTS)]
open(a.out, 'w').write('\n'.join(hdr + out + ['.ends', '']))
print(f'{a.out}: {len(out)} lines, {nlink} substrate links (dropped {gdrop:.3g} S), VSUBS total {sum(vsubs.values()) * 1e15:.1f} fF')
