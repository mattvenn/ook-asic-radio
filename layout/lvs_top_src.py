"""Schematic side of the top-level LVS: build/lvs/top/tt_um_mattvenn_radio_src.spice.

Built from the xschem netlist of xschem/tt_um_mattvenn_radio.sch alone (LVS mode, top as a
subckt), so the layout is compared against the schematic, never against what a layout
generator says it drew (layout/ref/ is for the per-block checks only). netgen can't evaluate
parameters, so every parameterised subckt is elaborated per instance: the instance's values
(themselves evaluated in the parent's parameters) over the .subckt defaults, substituted into
each device's quoted expressions, and the instance parameters dropped. Two instances of a cell
must give the same devices unless they're mapped to different layout cells (VARIANT).

Also:
- plain C / R / L elements (no X prefix: wiring estimates, e.g. tx_ring's cw) are dropped;
- tx_top's enable level shifters are the tx_ls_en layout cell (tx_ls with kn = kp = 1);
- radio_analog's Ctrim device is wrapped as the ctrim_1p layout cell, with the schematic's W / L;
- xdig (radio_digital) is re-ordered to the port order of macros/radio_digital/radio_digital.pnl.v
  (xschem orders it by the symbol's pins; netgen reads the verilog's).

    python3 layout/lvs_top_src.py     (after the xschem netlist is in build/lvs/top/)
"""
import math
import os
import re

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
OUT = os.path.join(REPO, 'build/lvs/top')
SCH = os.path.join(OUT, 'tt_um_mattvenn_radio.spice')
TOP = 'tt_um_mattvenn_radio'
VARIANT = {('tx_top', 'xlse_p'): 'tx_ls_en', ('tx_top', 'xlse_n'): 'tx_ls_en'}   # (parent, instance): cell
WRAP = {('radio_analog', 'XCtrim'): ('xctrim', 'ctrim_1p', ['trim', 'VGND'])}   # device -> layout cell


def lines(path):
    """Netlist lines with '+' continuations joined."""
    out = []
    for ln in open(path).read().splitlines():
        if ln.startswith('+') and out:
            out[-1] += ' ' + ln[1:].strip()
        else:
            out.append(ln)
    return out


def subckts(ls):
    """{name: [lines]} of the .subckt ... .ends blocks."""
    d, cur = {}, None
    for ln in ls:
        w = ln.split()
        if w and w[0].lower() == '.subckt':
            cur = w[1]
            d[cur] = [ln]
        elif cur:
            d[cur].append(ln)
            if w and w[0].lower() == '.ends':
                cur = None
    return d


def bus(name, rng=None):
    if rng:
        a, b = map(int, rng.split(':'))
        step = -1 if a > b else 1
        return [f'{name}[{i}]' for i in range(a, b + step, step)]
    return [name]


def sym_pins(path):
    out = []
    for m in re.finditer(r'name=([A-Za-z_]\w*)(?:\[(\d+:\d+)\])?', open(path).read()):
        if m.group(1) != 'x1':
            out += bus(m.group(1), m.group(2))
    return out


def verilog_ports(path):
    txt = open(path).read()
    hdr = re.search(r'module radio_digital\s*\((.*?)\);', txt, re.S).group(1)
    names = [n.strip() for n in hdr.split(',')]
    width = dict((m.group(2), m.group(1)) for m in
                 re.finditer(r'^\s*(?:input|output|inout)\s*(?:\[(\d+:\d+)\])?\s*(\w+)\s*;', txt, re.M))
    out = []
    for n in names:
        out += bus(n, width.get(n))
    return out


# --- spice parameter evaluation
SUFFIX = {'t': 1e12, 'g': 1e9, 'meg': 1e6, 'k': 1e3, 'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12, 'f': 1e-15}
NUM = re.compile(r'(?<![\w.])(\d+\.?\d*(?:e[-+]?\d+)?|\.\d+(?:e[-+]?\d+)?)(meg|[tgkmunpf])?(?![a-z_])', re.I)
FUNCS = {'sqrt': math.sqrt, 'max': max, 'min': min, 'abs': abs, 'int': int}


def ev(expr, env):
    """A spice value or expression ('4k', "'max((rl-278)/230.3,0.5)'", 'w1') -> float."""
    e = expr.strip().strip("'\"")
    e = NUM.sub(lambda m: repr(float(m.group(1)) * SUFFIX.get((m.group(2) or '').lower(), 1)), e)
    return float(eval(e, {'__builtins__': {}, **FUNCS}, {k.lower(): v for k, v in env.items()}))


def split_params(words):
    """['a', 'b', 'W=1', "L='x*2'"] -> (['a', 'b'], {'W': '1', 'L': "'x*2'"})."""
    pos, prm = [], {}
    for w in words:
        if '=' in w:
            k, v = w.split('=', 1)
            prm[k] = v
        else:
            pos.append(w)
    return pos, prm


def fmt(v):
    return f'{v:.6g}'


class Elab:
    def __init__(self, defs):
        self.defs = defs
        self.out = {}          # cell name -> lines
        self.order = []        # children first
        self.dropped = []

    def header(self, cell):
        pos, prm = split_params(self.defs[cell][0].split())
        return pos[2:], prm

    def cell(self, cell, env, name):
        """Elaborate subckt `cell` with parameters env as `name`; returns name."""
        pins, _ = self.header(cell)
        body = [f'.subckt {name} {" ".join(pins)}']
        for ln in self.defs[cell][1:-1]:
            w = ln.split()
            if not w or w[0].startswith('*'):
                continue
            inst = w[0]
            pos, prm = split_params(w)
            if inst[0] in 'CRLcrl':
                self.dropped.append(f'{name}/{inst}')
                continue
            if inst[0] not in 'xX':
                raise SystemExit(f'{cell}: unexpected element {ln}')
            ref = pos[-1]
            vals = {k: fmt(ev(v, env)) for k, v in prm.items()}
            if (cell, inst) in WRAP:
                winst, wcell, wpins = WRAP[(cell, inst)]
                self.emit(wcell, [f'.subckt {wcell} {" ".join(wpins)}',
                                  ' '.join([inst] + pos[1:] + [f'{k}={v}' for k, v in vals.items()]), '.ends'])
                body.append(' '.join([winst] + pos[1:-1] + [wcell]))
            elif ref in self.defs:
                _, defaults = self.header(ref)
                cenv = {k: ev(v, {}) for k, v in defaults.items()}
                cenv.update({k: float(v) for k, v in vals.items()})
                child = self.cell(ref, cenv, VARIANT.get((cell, inst), ref))
                body.append(' '.join(pos[:-1] + [child]))
            else:      # a device, a std cell or the digital macro
                body.append(' '.join(pos + [f'{k}={v}' for k, v in vals.items()]))
        body.append('.ends')
        self.emit(name, body)
        return name

    def emit(self, name, body):
        if name in self.out:
            if self.out[name] != body:
                raise SystemExit(f'{name}: instances with different parameters map to the same layout cell:\n'
                                 + '\n'.join(sorted(set(self.out[name]) ^ set(body))))
            return
        self.out[name] = body
        self.order.append(name)


def main():
    defs = subckts(lines(SCH))
    e = Elab(defs)
    e.cell(TOP, {}, TOP)

    # xdig (radio_digital): the verilog's port order
    sp = sym_pins(os.path.join(REPO, 'xschem/radio_digital.sym'))
    vp = verilog_ports(os.path.join(REPO, 'macros/radio_digital/radio_digital.pnl.v'))
    assert sorted(sp) == sorted(vp), set(sp) ^ set(vp)
    top = []
    for ln in e.out[TOP]:
        ws = ln.split()
        if ws and ws[-1] == 'radio_digital':
            m = dict(zip(sp, ws[1:-1]))
            ln = ' '.join([ws[0]] + [m[p] for p in vp] + ['radio_digital'])
        top.append(ln)
    e.out[TOP] = top

    path = os.path.join(OUT, f'{TOP}_src.spice')
    with open(path, 'w') as f:
        f.write('* top-level LVS source (layout/lvs_top_src.py): the xschem netlist, elaborated per instance\n')
        for n in e.order:
            f.write('\n'.join(e.out[n]) + '\n\n')
    print('wrote', path, len(e.order), 'subckts; dropped (not devices):', ', '.join(e.dropped) or 'none')


main()
