"""Pinout check: info.yaml <-> top schematic <-> radio_digital macro.

PINOUT below is the single source of truth for what each TT pin does. The script checks:
- info.yaml's pinout labels are exactly the PINOUT labels;
- in xschem/tt_um_mattvenn_radio.sch every port of xdig (radio_digital) and xana
  (radio_analog) lands on the expected net, so each TT pin reaches the block port PINOUT
  says, the digital <-> analog nets are the right ones, and ena / ua[5..7] are unconnected;
- the radio_digital symbol's pins are the hardened macro's pins (GL netlist and LEF);
- each uio_oe bit is wired to the macro's uio_oe bit (the value is checked in test/: it
  must equal UIO_OE_OUT after reset, from the PINOUT directions).

The top schematic (xschem/gen/top.py: labels, iopins and wires) is parsed directly, so the check
needs no xschem. With --xschem NETLIST the parse is cross-checked against an xschem netlist
of the same schematic (`xschem -q -x -n -s -o <dir> xschem/tt_um_mattvenn_radio.sch`).
--verilog OUT writes the tt_um wrapper used by the cocotb tests in test/ (radio_digital
as the macro, radio_analog as a stub that test/ drives and reads).

    python3 tools/check_pinout.py [--xschem build/.../tt_um_mattvenn_radio.spice] [--verilog OUT]
"""
import argparse
import os
import re
import sys

import yaml

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SCH = os.path.join(REPO, 'xschem/tt_um_mattvenn_radio.sch')
MACRO = os.path.join(REPO, 'macros/radio_digital')

# TT pin -> (info.yaml label, block port(s) it lands on). uio: (label, direction, ports).
PINOUT = {
    'ui': [(f'code bit {i}', [('xdig', f'ui_in[{i}]')]) for i in range(7)]
    + [('role (1 = TX, 0 = RX)', [('xdig', 'ui_in[7]')])],
    'uo': [(f'segment {c}', [('xdig', f'uo_out[{i}]')]) for i, c in enumerate('abcdefg')]
    + [('dp: LED toggle (RX)', [('xdig', 'uo_out[7]')])],
    'uio': [('mode select (strap)', 'in'), ('mode select (strap)', 'in'),
            ('raw TX key in / data UART', 'in'), ('raw RX comparator out', 'out'),
            ('debug: burst detected', 'out'), ('debug: toggle event', 'out'),
            ('debug: trim direction', 'out'), ('debug: TX active', 'out')],
    'ua': [('RX dipole +', [('xana', 'rx_p')]), ('RX dipole -', [('xana', 'rx_n')]),
           ('debug: detector output', [('xana', 'dbg')]), ('TX dipole +', [('xana', 'tx_p')]),
           ('TX dipole -', [('xana', 'tx_n')]), ('', [])],
}
# uio_oe after reset: 1 for each uio PINOUT marks 'out'
UIO_OE_OUT = sum(1 << i for i, (_, d) in enumerate(PINOUT['uio']) if d == 'out')

# internal nets: net -> the block ports on it
INTERNAL = {
    'comp': [('xdig', 'comp_in'), ('xana', 'comp_out')],
    **{f'trim[{i}]': [('xdig', f'trim_out[{i}]'), ('xana', f'trim[{i}]')] for i in range(8)},
    **{n: [('xdig', n), ('xana', n)] for n in ('tx_en', 'tx_en_n', 'rx_en', 'dbg_en', 'sc_phi1', 'sc_phi2')},
    'VDPWR': [('xdig', 'VPWR'), ('xana', 'VDPWR')],
    'VGND': [('xdig', 'VGND'), ('xana', 'VGND')],
    'VAPWR': [('xana', 'VAPWR')],
}
TT_PORTS = (['VGND', 'VDPWR', 'VAPWR', 'ena', 'clk', 'rst_n']
            + [f'{b}[{i}]' for b in ('ui_in', 'uo_out', 'uio_in', 'uio_out', 'uio_oe', 'ua') for i in range(8)])


def expected():
    """{net: sorted [(inst, port)]} for the whole top level."""
    want = {n: [] for n in TT_PORTS}
    want['clk'] = [('xdig', 'clk')]
    want['rst_n'] = [('xdig', 'rst_n')]
    for grp, net in (('ui', 'ui_in'), ('uo', 'uo_out'), ('ua', 'ua')):
        for i, (_, ports) in enumerate(PINOUT[grp]):
            want[f'{net}[{i}]'] = list(ports)
    for i in range(8):
        for b in ('uio_in', 'uio_out', 'uio_oe'):
            want[f'{b}[{i}]'] = [('xdig', f'{b}[{i}]')]
    want.update(INTERNAL)
    return {n: sorted(p) for n, p in want.items()}


def bits(name):
    """'x[7:0]' -> ['x[7]', ..., 'x[0]']; 'x' -> ['x']."""
    m = re.fullmatch(r'(\w+)\[(\d+):(\d+)\]', name)
    if not m:
        return [name]
    b, hi, lo = m.group(1), int(m.group(2)), int(m.group(3))
    step = -1 if hi >= lo else 1
    return [f'{b}[{i}]' for i in range(hi, lo + step, step)]


def sym_pins(sym):
    """[(pin name, x, y)] of an xschem symbol, in sim_pinnumber order."""
    pins = []
    for m in re.finditer(r'^B 5 (\S+) (\S+) (\S+) (\S+) \{([^}]*)\}', open(sym).read(), re.M):
        x1, y1, x2, y2 = map(float, m.groups()[:4])
        attrs = dict(re.findall(r'(\w+)=(\S+)', m.group(5)))
        pins.append((int(attrs['sim_pinnumber']), attrs['name'], (x1 + x2) / 2, (y1 + y2) / 2))
    return [(n, x, y) for _, n, x, y in sorted(pins)]


def parse_sch(path):
    """{net: sorted [(inst, port)]} from the top schematic: block pins, the lab_pins / iopins that name
    nets, and the wires between them. A wire joins its two ends and anything lying on it (end or
    middle); each group of joined points takes its name from its label(s) or iopin."""
    text = open(path).read()
    comps = re.findall(r'^C \{([^}]*)\} (\S+) (\S+) (\S+) (\S+) \{([^}]*)\}', text, re.M)
    wires = [tuple(map(float, m)) for m in re.findall(r'^N (\S+) (\S+) (\S+) (\S+) ', text, re.M)]
    names, iopins, insts = [], [], []          # names: (xy, net name) from lab_pins and iopins
    for sym, x, y, rot, flip, attrs in comps:
        a = dict(re.findall(r'(\w+)=(\S+)', attrs))
        xy = (float(x), float(y))
        if sym == 'devices/lab_pin.sym':
            names.append((xy, a['lab']))
        elif sym == 'devices/iopin.sym':
            iopins += bits(a['lab'])
            names.append((xy, a['lab']))
        elif sym in ('radio_digital.sym', 'radio_analog.sym'):
            if (rot, flip) != ('0', '0'):
                sys.exit(f'{a["name"]}: rotated / flipped instance, not handled')
            insts.append((a['name'], os.path.join(REPO, 'xschem', sym), xy))
    pins = [(name, pin, (ix + px, iy + py)) for name, sym, (ix, iy) in insts for pin, px, py in sym_pins(sym)]
    # union-find over the points of interest and the wire ends
    pts = [xy for xy, _ in names] + [xy for _, _, xy in pins] + [e for w in wires for e in (w[:2], w[2:])]
    up = {q: q for q in pts}

    def root(q):
        while up[q] != q:
            up[q] = up[up[q]]
            q = up[q]
        return q

    def on(q, w):                                 # q on the (axis-parallel or not) segment w
        (x, y), (x1, y1, x2, y2) = q, w
        return (abs((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)) < 1e-6
                and min(x1, x2) - 1e-6 <= x <= max(x1, x2) + 1e-6 and min(y1, y2) - 1e-6 <= y <= max(y1, y2) + 1e-6)
    for w in wires:
        for q in up:
            if on(q, w):
                up[root(q)] = root(w[:2])
    named = {}
    for xy, n in names:
        named.setdefault(root(xy), set()).add(n)
    nets = {}
    for name, pin, xy in pins:
        labs = sorted(named.get(root(xy), ()))
        if len(labs) != 1:
            sys.exit(f'{name}.{pin}: {len(labs)} net names on the pin ({labs})')
        pb, lb = bits(pin), bits(labs[0])
        if len(pb) != len(lb):
            sys.exit(f'{name}.{pin}: width {len(pb)} vs net {labs[0]}')
        for p, n in zip(pb, lb):
            nets.setdefault(n, []).append((name, p))
    for n in iopins:
        nets.setdefault(n, [])
    return {n: sorted(p) for n, p in nets.items()}, iopins


def parse_xschem(path):
    """Same as parse_sch, from an xschem netlist (instance pins in symbol order)."""
    lines = []
    for ln in open(path).read().splitlines():
        if ln.startswith('+') and lines:
            lines[-1] += ' ' + ln[1:]
        else:
            lines.append(ln)
    nets = {}
    for ln in lines:
        tok = ln.split()
        if not tok or tok[0] not in ('xdig', 'xana'):
            continue
        sym = os.path.join(REPO, 'xschem', tok[-1] + '.sym')
        ports = [b for p, _, _ in sym_pins(sym) for b in bits(p)]
        if len(ports) != len(tok) - 2:
            sys.exit(f'{tok[0]}: {len(tok) - 2} nets for {len(ports)} pins')
        for p, n in zip(ports, tok[1:-1]):
            nets.setdefault(n, []).append((tok[0], p))
    return {n: sorted(p) for n, p in nets.items()}


def check_info_yaml(err):
    pin = yaml.safe_load(open(os.path.join(REPO, 'info.yaml')))['pinout']
    for grp, rows in PINOUT.items():
        for i, row in enumerate(rows):
            got = pin.get(f'{grp}[{i}]')
            if got != row[0]:
                err(f'info.yaml {grp}[{i}]: "{got}", PINOUT says "{row[0]}"')


def check_nets(nets, iopins, err, what):
    if what == 'schematic' and sorted(set(iopins)) != sorted(TT_PORTS):
        err(f'schematic ports {sorted(set(iopins) ^ set(TT_PORTS))} differ from the TT ports')
    want = expected()
    for n in sorted(set(want) | set(nets)):
        w, g = want.get(n, []), nets.get(n, [])
        if w != g:
            err(f'{what}: net {n}: {g}, expected {w}')


def check_macro(err):
    sym = [b for p, _, _ in sym_pins(os.path.join(REPO, 'xschem/radio_digital.sym')) for b in bits(p)]
    sig = sorted(set(sym) - {'VPWR', 'VGND'})
    nl = open(os.path.join(MACRO, 'radio_digital.nl.v')).read()
    decl = re.findall(r'^\s*(input|output|inout)\s*(\[\d+:\d+\])?\s*(\w+);', nl, re.M)
    gl = sorted(b for _, rng, n in decl for b in bits(n + (rng or '')))
    if gl != sig:
        err(f'radio_digital.nl.v ports vs symbol: {sorted(set(gl) ^ set(sig))}')
    lef = sorted(set(re.findall(r'^\s*PIN (\S+)', open(os.path.join(MACRO, 'radio_digital.lef')).read(), re.M)))
    if lef != sorted(sym):
        err(f'radio_digital.lef pins vs symbol: {sorted(set(lef) ^ set(sym))}')


def write_verilog(nets, path):
    """tt_um wrapper from the parsed schematic: xdig = the macro, xana = a stub."""
    conn = {}
    for n, ps in nets.items():
        for inst, p in ps:
            conn[(inst, p)] = n
    sym = {i: [b for p, _, _ in sym_pins(os.path.join(REPO, f'xschem/{s}.sym')) for b in bits(p)]
           for i, s in (('xdig', 'radio_digital'), ('xana', 'radio_analog'))}
    internal = sorted({conn[k] for k in conn if conn[k] not in TT_PORTS})

    def ref(inst, p):
        return conn.get((inst, p), '')

    def esc(n):
        return n if n in TT_PORTS or '[' not in n else '\\' + n + ' '

    def port_list(inst, skip=()):
        groups = {}
        for b in sym[inst]:
            if b in skip:
                continue
            groups.setdefault(re.sub(r'\[\d+\]$', '', b), []).append(b)
        out = []
        for g, bs in groups.items():
            nets_ = [esc(ref(inst, b)) if ref(inst, b) else "1'bz" for b in bs]
            out.append(f'.{g}({{{", ".join(nets_)}}})' if len(bs) > 1 else f'.{g}({nets_[0]})')
        return ',\n        '.join(out)

    v = f"""// Generated by tools/check_pinout.py from xschem/tt_um_mattvenn_radio.sch: do not edit.
// The TT top level with radio_digital (the hardened macro, RTL or GL) and radio_analog as a
// stub: comp_out is driven from the stub's comp_r, the rest of its pins are plain inputs.
`default_nettype none
`timescale 1ns / 1ps

module radio_analog (
    input  wire rx_en, tx_en, tx_en_n, dbg_en, sc_phi1, sc_phi2,
    input  wire [7:0] trim,
    output wire comp_out,
    inout  wire tx_p, tx_n, rx_p, rx_n, dbg,
    inout  wire VDPWR, VAPWR, VGND
);
    reg comp_r = 1'b0;
    assign comp_out = comp_r;
endmodule

module tt_um_mattvenn_radio (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    inout  wire [7:0] ua,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);
    wire VDPWR = 1'b1, VAPWR = 1'b1, VGND = 1'b0;
{''.join(f'    wire {esc(n)};{chr(10)}' for n in internal if n not in ('VDPWR', 'VAPWR', 'VGND'))}
    radio_digital xdig (
        {port_list('xdig', skip=('VPWR', 'VGND'))}
    );
    radio_analog xana (
        {port_list('xana')}
    );
endmodule
"""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    open(path, 'w').write(v)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--xschem', help='xschem netlist of the top schematic to cross-check the parse')
    ap.add_argument('--verilog', help='write the tt_um wrapper here')
    a = ap.parse_args()
    errs = []
    check_info_yaml(errs.append)
    nets, iopins = parse_sch(SCH)
    check_nets(nets, iopins, errs.append, 'schematic')
    if a.xschem:
        check_nets(parse_xschem(a.xschem), iopins, errs.append, 'xschem netlist')
    check_macro(errs.append)
    for e in errs:
        print('FAIL', e)
    if errs:
        sys.exit(1)
    if a.verilog:
        write_verilog(nets, a.verilog)
    n = sum(len(r) for r in PINOUT.values())
    print(f'pinout OK: {n} TT pins, info.yaml = schematic = macro; uio_oe after reset {UIO_OE_OUT:08b}')


if __name__ == '__main__':
    main()
