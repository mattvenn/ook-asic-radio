# layout/ref/lna_chain.spice -> build/kpex/lna_chain_flat_ref.spice: one flat .subckt,
# primitive M / R / C lines (KLayout reader units), m folded into W, internal nets st<k>_<net>.
import re, sys, math
src = open('layout/ref/lna_chain.spice').read().splitlines()
subs = {}; cur = None
for ln in src:
    if ln.startswith('.subckt'):
        f = ln.split(); cur = f[1]; subs[cur] = {'ports': f[2:], 'body': []}
    elif ln.startswith('.ends'): cur = None
    elif cur and ln and ln[0] in 'Xx': subs[cur]['body'].append(ln.split())
STAGE = {'xa1': 'st1', 'xa2': 'st2', 'xa3': 'st3', 'xa4': 'st4', 'xa5': 'st5', 'xa6': 'st6'}
out = []
def params(f):
    return {k: float(v) for k, v in (p.split('=') for p in f if '=' in p)}
def emit(f, nmap, pre):
    name = pre + f[0][1:]
    toks = [t for t in f[1:] if '=' not in t]; p = params(f)
    model = toks[-1]; nets = [nmap(n) for n in toks[:-1]]
    if 'fet' in model:
        W = p['W'] * p.get('m', 1); nets[3] = 'sky130_gnd'   # KLayout's substrate net
        out.append(f"M{name} {' '.join(nets)} {model} L={p['L']}u W={W}u")
    elif 'res' in model:
        nets[2] = 'sky130_gnd'
        w = {'0p35': 0.35, '0p69': 0.69, '1p41': 1.41}[model.split('_')[-1]]
        out.append(f"R{name} {' '.join(nets)} {model} L={math.ceil(p['L'] * 100 - 1e-6) / 100}u W={w}u")   # as drawn (rounded up to 0.01 um)
    elif 'cap_mim' in model:
        w, l = round(p['W'], 2), round(p['L'], 2)   # the deck compares a MIM's A and P (C is off)
        out.append(f"C{name} {' '.join(nets)} sky130_fd_pr__model__cap_mim A={w*l:.6g}P P={2*(w+l):.6g}u")
    else:
        sys.exit('unknown ' + model)
top = subs['lna_chain']
for f in top['body']:
    model = f[-1] if '=' not in f[-1] else [t for t in f if '=' not in t][-1]
    if model in subs:
        s = subs[model]; conn = [t for t in f[1:-1]]
        m = dict(zip(s['ports'], conn)); pre = STAGE[f[0]] + '_'
        for g in s['body']:
            emit(g, lambda n: m.get(n, pre + n), pre)
    else:
        emit(f, lambda n: n, '')
hdr = '.subckt lna_chain ' + ' '.join(top['ports'])
open('build/kpex/lna_chain_flat_ref.spice', 'w').write(hdr + '\n' + '\n'.join(out) + '\n.ends\n')
print(hdr); print('\n'.join(out))
