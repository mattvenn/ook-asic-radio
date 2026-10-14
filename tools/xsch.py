"""
Tiny xschem schematic writer, so testbenches and blocks can be generated
from scripts in the same style as the hand-drawn ones (TT_MODELS +
SIMULATION code blocks, launcher, embedded graphs, lab_pin connections).

Connectivity is by net labels: every pin gets a lab_pin placed exactly on it,
which xschem treats as connected. Generated schematics are checked by
netlisting them with xschem (tools/osic xschem -n -s -q ...).
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
XSCHEM_DIR = os.path.join(os.path.dirname(HERE), 'xschem')

# pin offsets of the xschem/PDK library symbols we use (from their .sym files)
LIB_PINS = {
    'devices/vsource.sym': {'p': (0, -30), 'm': (0, 30)},
    'devices/isource.sym': {'p': (0, -30), 'm': (0, 30)},
    'devices/res.sym': {'P': (0, -30), 'M': (0, 30)},
    'devices/capa.sym': {'p': (0, -30), 'm': (0, 30)},
    'devices/ind.sym': {'p': (0, -30), 'm': (0, 30)},
    'devices/vcvs.sym': {'p': (0, -30), 'm': (0, 30), 'cp': (-40, -20), 'cm': (-40, 20)},
    'devices/gnd.sym': {'p': (0, 0)},
    'devices/lab_pin.sym': {'p': (0, 0)},
    'devices/ipin.sym': {'p': (0, 0)},
    'devices/opin.sym': {'p': (0, 0)},
    'devices/iopin.sym': {'p': (0, 0)},
    'sky130_fd_pr/nfet_01v8.sym': {'D': (20, -30), 'G': (-20, 0), 'S': (20, 30), 'B': (20, 0)},
    'sky130_fd_pr/pfet_01v8.sym': {'D': (20, 30), 'G': (-20, 0), 'S': (20, -30), 'B': (20, 0)},
    'sky130_fd_pr/nfet_01v8_lvt.sym': {'D': (20, -30), 'G': (-20, 0), 'S': (20, 30), 'B': (20, 0)},
    'sky130_fd_pr/pfet_01v8_lvt.sym': {'D': (20, 30), 'G': (-20, 0), 'S': (20, -30), 'B': (20, 0)},
    'sky130_fd_pr/pfet_01v8_hvt.sym': {'D': (20, 30), 'G': (-20, 0), 'S': (20, -30), 'B': (20, 0)},
    'sky130_fd_pr/nfet_g5v0d10v5.sym': {'D': (20, -30), 'G': (-20, 0), 'S': (20, 30), 'B': (20, 0)},
    'sky130_fd_pr/pfet_g5v0d10v5.sym': {'D': (20, 30), 'G': (-20, 0), 'S': (20, -30), 'B': (20, 0)},
    # 3-terminal variants: body is the instance property 'body' (same netlist line)
    **{f'sky130_fd_pr/{k}fet3_{m}.sym': {'D': (20, -30) if k == 'n' else (20, 30), 'G': (-20, 0),
                                         'S': (20, 30) if k == 'n' else (20, -30)}
       for k in 'np' for m in ('01v8', '01v8_lvt', '01v8_hvt', 'g5v0d10v5')},
    # std cells: supplies are instance properties (VPWR=, VGND=, VPB=, VNB=), not pins
    'sky130_stdcells/inv_2.sym': {'A': (-40, 0), 'Y': (40, 0)},
    'sky130_stdcells/nand2_2.sym': {'A': (-60, -20), 'B': (-60, 20), 'Y': (60, 0)},
    'sky130_fd_pr/res_high_po_0p35.sym': {'P': (0, -30), 'M': (0, 30), 'B': (-20, 0)},
    'sky130_fd_pr/res_xhigh_po_0p35.sym': {'P': (0, -30), 'M': (0, 30), 'B': (-20, 0)},
    'sky130_fd_pr/cap_mim_m3_1.sym': {'c0': (0, -30), 'c1': (0, 30)},
    **{f'sky130_fd_pr/res_{k}_po_{w}.sym': {'P': (0, -30), 'M': (0, 30), 'B': (-20, 0)}
       for k in ('high', 'xhigh') for w in ('0p69', '1p41', '2p85')},
    # pinless
    'sky130_fd_pr/corner.sym': {},
    'devices/code.sym': {},
    'devices/code_shown.sym': {},
    'devices/launcher.sym': {},
}


def local_pins(sym):
    """Pin offsets of a symbol in this repo's xschem/ directory."""
    pins = {}
    with open(os.path.join(XSCHEM_DIR, sym)) as fh:
        for line in fh:
            m = re.match(r'B 5 (\S+) (\S+) (\S+) (\S+) \{.*?name=(\S+?)[\s}]', line)
            if m:
                x1, y1, x2, y2 = map(float, m.groups()[:4])
                pins[m.group(5)] = ((x1 + x2) / 2, (y1 + y2) / 2)
    return pins


def rotate(x, y, rot, flip):
    """xschem's ROTATION macro around the instance origin."""
    if flip:
        x = -x
    return [(x, y), (-y, x), (-x, -y), (y, -x)][rot % 4]


def fmt(v):
    v = round(v, 4)
    return str(int(v)) if v == int(v) else str(v)


class Inst:
    def __init__(self, sym, x, y, rot, flip, props):
        self.sym, self.x, self.y, self.rot, self.flip, self.props = sym, x, y, rot, flip, props
        self.pins = LIB_PINS[sym] if sym in LIB_PINS else local_pins(sym)

    def pin(self, name):
        px, py = rotate(*self.pins[name], self.rot, self.flip)
        return (self.x + px, self.y + py)

    def text(self):
        body = '\n'.join(f'{k}={v}' for k, v in self.props.items())
        return f'C {{{self.sym}}} {fmt(self.x)} {fmt(self.y)} {self.rot} {self.flip} {{{body}}}'


class Sch:
    def __init__(self):
        self.items, self.boxes, self.texts, self.wires = [], [], [], []
        self._n = {}
        self.pin_order = None

    def _name(self, prefix):
        self._n[prefix] = self._n.get(prefix, 0) + 1
        return f'{prefix}{self._n[prefix]}'

    def place(self, sym, x, y, rot=0, flip=0, name=None, **props):
        prefix = {'devices/vsource.sym': 'V', 'devices/isource.sym': 'I', 'devices/res.sym': 'R',
                  'devices/capa.sym': 'C', 'devices/ind.sym': 'L', 'devices/vcvs.sym': 'E'}.get(sym, 'x')
        p = {'name': name or self._name(prefix)}
        p.update(props)
        inst = Inst(sym, x, y, rot, flip, p)
        self.items.append(inst)
        return inst

    def label(self, pt, net, right=False):
        """lab_pin exactly on a pin; right=True puts the text to the right."""
        self.items.append(Inst('devices/lab_pin.sym', pt[0], pt[1], 0, 1 if right else 0,
                               {'name': self._name('p'), 'sig_type': 'std_logic', 'lab': net}))

    def gnd(self, pt):
        self.items.append(Inst('devices/gnd.sym', pt[0], pt[1], 0, 0, {'name': self._name('l'), 'lab': 'GND'}))

    def connect(self, inst, **nets):
        """Label several pins of an instance: connect(r1, P='a', M='b'). Net
        'GND' gets a ground symbol."""
        for pin, net in nets.items():
            pt = inst.pin(pin)
            if net == 'GND':
                self.gnd(pt)
            else:
                self.label(pt, net, right=pt[0] >= inst.x)

    def wire(self, a, b, lab=''):
        self.wires.append((a, b, lab))

    # --- drawn wiring (classical schematics). Every wire end sits on a pin or
    # on another wire's end: T junctions are split so xschem dots them.
    def route(self, *pts, vfirst=False):
        """Orthogonal wire through pts. A diagonal step gets one corner:
        horizontal first, or vertical first with vfirst=True."""
        out = [pts[0]]
        for p in pts[1:]:
            q = out[-1]
            if q[0] != p[0] and q[1] != p[1]:
                out.append((q[0], p[1]) if vfirst else (p[0], q[1]))
            out.append(p)
        for a, b in zip(out, out[1:]):
            if a != b:
                self.wire(a, b)

    def bus(self, a, b, taps=()):
        """Straight wire a -> b split at the tap points on it (T junctions)."""
        pts = sorted({a, b, *taps})
        for p, q in zip(pts, pts[1:]):
            self.wire(p, q)

    def rail(self, y, x1, x2, taps=(), net=None, port=False):
        """Horizontal supply rail at y from x1 to x2; taps = pins below/above it
        (each gets a vertical drop to the rail). The rail is labelled net at x1,
        with an iopin there when port=True."""
        xs = []
        for t in taps:
            if t[1] != y:
                self.wire(t, (t[0], y))
            xs.append((t[0], y))
        self.bus((x1, y), (x2, y), xs)
        if net:
            (self.port if port else self.label)((x1, y), net)

    def port(self, pt, net, right=False):
        """iopin at a wire end; text outward (left, or right with right=True)."""
        self.items.append(Inst('devices/iopin.sym', pt[0], pt[1], 0, 0 if right else 1,
                               {'name': self._name('p'), 'lab': net}))

    def code(self, x, y, name, value, only_toplevel='false', tcleval=False):
        props = {'name': name, 'only_toplevel': only_toplevel}
        if tcleval:
            props['format'] = '"tcleval( @value )"'
        props['value'] = '"' + value.replace('"', '\\"') + '"'
        props['spice_ignore'] = 'false'
        self.items.append(Inst('devices/code.sym', x, y, 0, 0, props))

    def launcher(self, x, y, descr, tcl):
        self.items.append(Inst('devices/launcher.sym', x, y, 0, 0,
                               {'name': self._name('h'), 'descr': f'"{descr}"', 'tclcommand': f'"{tcl}"'}))

    def graph(self, x1, y1, x2, y2, nodes, colors=None, x_lo=0, x_hi=1e-6, y_lo=0, y_hi=1,
              logx=0, title=''):
        colors = colors or [4, 10, 6, 15, 7, 8][:len(nodes)]
        node = '\n'.join(nodes)
        props = [f'flags=graph', f'y1={y_lo}', f'y2={y_hi}', 'ypos1=0', 'ypos2=2', 'divy=5',
                 'subdivy=1', 'unity=1', f'x1={x_lo}', f'x2={x_hi}', 'divx=5', 'subdivx=1',
                 'xlabmag=1.0', 'ylabmag=1.0', f'node="{node}"',
                 f'color="{" ".join(map(str, colors))}"', 'dataset=-1', 'unitx=1',
                 f'logx={logx}', 'logy=0']
        self.boxes.append(f'B 2 {fmt(x1)} {fmt(y1)} {fmt(x2)} {fmt(y2)} {{' + '\n'.join(props) + '\n}')
        if title:
            self.text(x1, y1 - 30, title, 0.4)

    def text(self, x, y, s, size=0.3):
        self.texts.append(f'T {{{s}}} {fmt(x)} {fmt(y)} 0 0 {size} {size} {{}}')

    def write(self, path):
        lines = ['v {xschem version=3.4.5 file_version=1.2', '}', 'G {}', 'K {}', 'V {}', 'S {}', 'E {}']
        lines += self.boxes + self.texts
        for (x1, y1), (x2, y2), lab in self.wires:
            lines.append(f'N {fmt(x1)} {fmt(y1)} {fmt(x2)} {fmt(y2)} {{' + (f'\nlab={lab}' if lab else '') + '}')
        items = self.items
        if self.pin_order:
            # ports first, in pin_order: keeps the netlist's *.PININFO order
            # independent of where the ports are drawn
            ports_ = sorted((i for i in items if i.sym == 'devices/iopin.sym'),
                            key=lambda i: self.pin_order.index(i.props['lab']))
            items = ports_ + [i for i in items if i.sym != 'devices/iopin.sym']
        lines += [i.text() for i in items]
        with open(path, 'w') as fh:
            fh.write('\n'.join(lines) + '\n')


MOS_DEFAULTS = {
    'nf': '1', 'mult': '1',
    'ad': '"\'int((nf+1)/2) * W/nf * 0.29\'"', 'pd': '"\'2*int((nf+1)/2) * (W/nf + 0.29)\'"',
    'as': '"\'int((nf+2)/2) * W/nf * 0.29\'"', 'ps': '"\'2*int((nf+2)/2) * (W/nf + 0.29)\'"',
    'nrd': '"\'0.29 / W\'"', 'nrs': '"\'0.29 / W\'"', 'sa': '0', 'sb': '0', 'sd': '0',
}


def mos(sch, kind, x, y, W, L, nf=1, mult=1, name=None, rot=0, flip=0, vt='', body=None):
    """Place a sky130 nfet/pfet with the PDK's standard property set.
    vt='lvt' / 'hvt' selects that 1.8 V flavour (pfet_01v8_lvt needs L >= 0.35);
    vt='g5' gives the thick-oxide 3.3 V device (g5v0d10v5, L >= 0.5).
    body=<net> uses the 3-terminal symbol (body as a property, no B pin to
    wire); the netlist line is the same as with B wired to that net."""
    model = f'{kind}fet_g5v0d10v5' if vt == 'g5' else f'{kind}fet_01v8' + (f'_{vt}' if vt else '')
    sym = f'sky130_fd_pr/{model}.sym'
    props = dict(MOS_DEFAULTS)
    if body:
        sym = sym.replace(f'{kind}fet_', f'{kind}fet3_')
        props['body'] = body
    props.update({'L': str(L), 'W': str(W), 'nf': str(nf), 'mult': str(mult),
                  'model': model, 'spiceprefix': 'X'})
    return sch.place(sym, x, y, rot=rot, flip=flip, name=name or sch._name('M'), **props)


def inv(sch, x, y, pkw, nkw, h=75):
    """CMOS inverter drawn as a textbook stack: PMOS (mos() kwargs pkw) over
    NMOS (nkw), drain column at x, gates joined at x - 40. Returns
    (p, n, gate junction, drain junction); the sources (p.pin('S') at the
    top, n.pin('S') at the bottom) are left for the caller's rails."""
    p = mos(sch, 'p', x - 20, y - h, **pkw)
    n = mos(sch, 'n', x - 20, y + h, **nkw)
    g, d = (x - 40, y), (x, y)
    sch.bus(p.pin('G'), n.pin('G'), [g])
    sch.bus(p.pin('D'), n.pin('D'), [d])
    return p, n, g, d


def write_symbol(path, left=(), right=(), top=(), bottom=(), width=160, params=None):
    """Box symbol for a subcircuit: pins listed per side, 40 units apart.
    Pin order in the netlist = order given (left, right, top, bottom).
    params = {name: default}: passed per instance; xschem puts the defaults on
    the .subckt line, so the schematic can use them as 'name'."""
    nl, nr = len(left), len(right)
    h = max(nl, nr, 1) * 40 + 20
    w2, h2 = width // 2, h // 2
    params = params or {}
    fmt_p = ''.join(f' {k}=@{k}' for k in params)
    tmpl_p = ''.join(f' {k}={v}' for k, v in params.items())
    out = ['v {xschem version=3.4.5 file_version=1.2', '}', 'G {}',
           'K {type=subcircuit', f'format="@name @pinlist @symname{fmt_p}"', f'template="name=x1{tmpl_p}"', '}',
           'V {}', 'S {}', 'E {}',
           f'L 4 -{w2} -{h2} {w2} -{h2} {{}}', f'L 4 -{w2} {h2} {w2} {h2} {{}}',
           f'L 4 -{w2} -{h2} -{w2} {h2} {{}}', f'L 4 {w2} -{h2} {w2} {h2} {{}}']
    n = 0
    def pin(name, x, y, tx, ty, flip):
        nonlocal n
        n += 1
        out.append(f'B 5 {x-2.5} {y-2.5} {x+2.5} {y+2.5} {{name={name} dir=inout sim_pinnumber={n}}}')
        out.append(f'T {{{name}}} {tx} {ty} 0 {flip} 0.2 0.2 {{}}')
    for i, nm in enumerate(left):
        y = -h2 + 30 + i * 40
        out.append(f'L 7 -{w2+20} {y} -{w2} {y} {{}}'); pin(nm, -w2 - 20, y, -w2 + 5, y - 6, 0)
    for i, nm in enumerate(right):
        y = -h2 + 30 + i * 40
        out.append(f'L 7 {w2} {y} {w2+20} {y} {{}}'); pin(nm, w2 + 20, y, w2 - 5, y - 6, 1)
    for i, nm in enumerate(top):
        x = -w2 + 30 + i * 40
        out.append(f'L 7 {x} -{h2+20} {x} -{h2} {{}}'); pin(nm, x, -h2 - 20, x - 6, -h2 + 5, 0)
    for i, nm in enumerate(bottom):
        x = -w2 + 30 + i * 40
        out.append(f'L 7 {x} {h2} {x} {h2+20} {{}}'); pin(nm, x, h2 + 20, x - 6, h2 - 20, 0)
    out.append('T {@symname} -40 -6 0 0 0.3 0.3 {}')
    out.append(f'T {{@name}} {w2-30} -{h2+20} 0 0 0.2 0.2 {{}}')
    with open(path, 'w') as fh:
        fh.write('\n'.join(out) + '\n')


# poly resistors, R = a + b * L (tt, 27 C, fitted at L = 2 and 10 um
# (sim/pdk/passives.spice). b in ohm/um, a = the two ends. Process corners: hh +14..15 %, ll -15 %; high_po +0.05 %/C, xhigh ~0.
POLY = {('high', '0p35'): (995.0, 963.0), ('high', '0p69'): (470.9, 526.0), ('high', '1p41'): (230.3, 278.0),
        ('xhigh', '0p35'): (7379.0, 0.0), ('xhigh', '0p69'): (3161.0, 0.0)}
MIM_F_PER_UM2 = 2.06e-15        # cap_mim_m3_1 incl. its perimeter term, 10x10 um (hh +14 %, ll -13 %)


def poly_r(sch, x, y, r, kind='high', w='0p35', rot=0, flip=0, name=None):
    """sky130 poly resistor of value r (a number or a spice param/expression
    string, e.g. "rl"), L computed from the fitted R(L). Pins P, M, B (B = body,
    connect to VSS)."""
    b, a = POLY[(kind, w)]
    expr = f"'max(({r}-{a:g})/{b:g},0.5)'"     # no spaces: xschem splits property values
    return sch.place(f'sky130_fd_pr/res_{kind}_po_{w}.sym', x, y, rot=rot, flip=flip, name=name or sch._name('R'),
                     L=expr, model=f'res_{kind}_po_{w}', mult='1', spiceprefix='X')


def mim(sch, x, y, c, mf=1, rot=0, flip=0, name=None):
    """cap_mim_m3_1 of value c (number or param string) as mf square units
    (keep units <= 30 um, as the LPF / averager: use mf for more than ~1.8 pF).
    Pins c0 (top plate, m4) and c1 (bottom plate, m3): put c1 on the quieter /
    lower-impedance node, since in layout the bottom plate carries the
    substrate parasitic."""
    side = f"'sqrt(({c})/{mf}/{MIM_F_PER_UM2:g})'"
    return sch.place('sky130_fd_pr/cap_mim_m3_1.sym', x, y, rot=rot, flip=flip, name=name or sch._name('C'),
                     model='cap_mim_m3_1', W=side, L=side, MF=str(mf), spiceprefix='X')


# --- value notes: the evaluated value of every parameterised device, drawn next to it, so the
# sheet reads without looking the parameters up
SPICE_SUFFIX = {'t': 1e12, 'g': 1e9, 'meg': 1e6, 'k': 1e3, 'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12, 'f': 1e-15}
NUM = r'(?<![a-z_\d.])(\d+\.?\d*(?:[eE][-+]?\d+)?|\.\d+(?:[eE][-+]?\d+)?)(meg|[tgkmunpf])?(?![a-z_])'


def spice_num(v):
    """'4k', '0.85Meg', '1e-12', 20 -> float."""
    if isinstance(v, (int, float)):
        return float(v)
    m = re.fullmatch(NUM, v.strip().lower())
    if not m:
        raise ValueError(f'not a spice number: {v!r}')
    return float(m.group(1)) * SPICE_SUFFIX.get(m.group(2), 1)


def ev(expr, params):
    """Evaluate a device property ('w1', "'max((rl-278)/230.3,0.5)'", '2') with params."""
    e = str(expr).strip('"\' ').lower()
    e = re.sub(NUM, lambda m: repr(spice_num(m.group(0))), e)
    env = {k.lower(): spice_num(v) for k, v in params.items()}
    return float(eval(e, {'__builtins__': {}, 'sqrt': lambda x: x ** 0.5, 'max': max, 'min': min,
                                           'int': int, 'abs': abs}, env))


def eng(v):
    """3 significant figures, with an SI suffix outside 0.01..1000: 1000 -> '1k', 6e-13 -> '600f'."""
    if 0.01 <= abs(v) < 1000 or v == 0:
        return f'{v:.3g}'
    for s, f in (('M', 1e6), ('k', 1e3), ('', 1), ('m', 1e-3), ('u', 1e-6), ('n', 1e-9), ('p', 1e-12), ('f', 1e-15)):
        if abs(v) >= f * 0.9995:
            return f'{v / f:.3g}{s}'
    return f'{v:.3g}'


def _value_note(it, params):
    """Note text for one instance, or None if none of its shown values is parameterised."""
    p, sym = it.props, it.sym
    if not any("'" in str(p.get(k, '')) for k in ('W', 'L', 'nf', 'mult', 'MF', 'value')) and \
            not (sym.endswith('.sym') and '/' not in sym and any("'" in str(v) for v in p.values())):
        return None
    if 'fet' in sym:                   # same order as the symbol's own 'mult x W / L' label
        m, w, l = (ev(p.get(k, 1), params) for k in ('mult', 'W', 'L'))
        nf = ev(p.get('nf', 1), params)
        return f'= {m:g} x {w:.3g} / {l:.3g}' + (f', nf {nf:g}' if "'" in str(p.get('nf', '')) else '')
    if '_po_' in sym:                  # R from the fitted R(L) the generators size with
        kind, w = re.search(r'res_(x?high)_po_(\w+)\.sym', sym).groups()
        b, a = POLY[(kind, w)]
        lv, mult = ev(p['L'], params), ev(p.get('mult', 1), params)
        return f'R = {eng((a + b * lv) / mult)} (L {lv:.3g} um)'
    if 'cap_mim' in sym:
        w, l, mf = (ev(p.get(k, 1), params) for k in ('W', 'L', 'MF'))
        size = f'{w:.3g} x {l:.3g} um' if mf == 1 else f'{mf:g} x {w:.3g} x {l:.3g} um'
        return f'C = {eng(mf * w * l * MIM_F_PER_UM2)}F ({size})'
    if sym.startswith('devices/'):     # capa / res / sources: their value
        v = eng(ev(p['value'], params))
        return {'devices/capa.sym': f'C = {v}F', 'devices/res.sym': f'R = {v}'}.get(sym, f'= {v}')
    # a subcircuit of this repo: the parameters it is given
    vals = [f'{k} {eng(ev(v, params))}' for k, v in p.items() if k != 'name' and "'" in str(v)]
    return '\n'.join(', '.join(vals[i:i + 3]) for i in range(0, len(vals), 3))


def value_notes(sch, params, at=None, skip=(), size=0.25):
    """Write the evaluated value of every parameterised device next to it (call before
    write()). params: {name: value} the sheet's parameters as used on the chip, or a list
    of (tag, params) when the block is used with several sets (one line per set). at:
    {instance name: (dx, dy)} moves a note (offset from the instance origin) off something
    it lands on; skip: instances to leave alone."""
    sets = params if isinstance(params, list) else [(None, params)]
    at = at or {}
    for it in list(sch.items):
        name = it.props.get('name')
        if name in skip:
            continue
        notes = [(tag, _value_note(it, prm)) for tag, prm in sets]
        if not notes[0][1]:
            continue
        if len({n for _, n in notes}) == 1:
            text = notes[0][1]
        else:
            text = '\n'.join(f'{n} ({tag})' for tag, n in notes)
        if name in at:
            dx, dy = at[name]
        elif 'fet' in it.sym or 'cap_mim' in it.sym or '_po_' in it.sym:
            # under the symbol's own labels (right of the device, left when flipped)
            wid = max(len(t) for t in text.split('\n')) * 27 * size
            dx, dy = (-25 - wid, 38) if it.flip else (25, 38)
            if '_po_' in it.sym and it.rot % 2:
                dx, dy = -30, -50
        elif it.sym.startswith('devices/'):
            dx, dy = 15, 30
        else:
            dx, dy = -60, 15                # inside a box symbol, under its name
        sch.text(it.x + dx, it.y + dy, text, size)


def stdcell(sch, cell, x, y, vdd='VDD', vss='VSS', name=None, flip=0):
    """Place a sky130_fd_sc_hd cell (inv_2, nand2_2, ...) on supplies vdd/vss."""
    return sch.place(f'sky130_stdcells/{cell}.sym', x, y, flip=flip, name=name or sch._name('x'),
                     VGND=vss, VNB=vss, VPB=vdd, VPWR=vdd, prefix='sky130_fd_sc_hd__')


def ports(sch, x0, y0, names, kind='iopin'):
    """Port symbols for a subcircuit schematic, stacked at (x0, y0)."""
    for i, nm in enumerate(names):
        sch.items.append(Inst(f'devices/{kind}.sym', x0, y0 + i * 30, 0, 0,
                              {'name': sch._name('p'), 'lab': nm}))


TT_MODELS = """
** opencircuitdesign pdks install
.lib $::SKYWATER_MODELS/sky130.lib.spice tt
.include $::SKYWATER_STDCELLS/sky130_fd_sc_hd.spice

"""
