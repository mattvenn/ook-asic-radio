"""Schematic side of the top-level LVS: build/lvs/top/tt_um_mattvenn_radio_src.spice.

The xschem netlist of xschem/tt_um_mattvenn_radio.sch (LVS mode, top as a subckt) with
- each laid-out block's definition replaced by the reference its block LVS matched
  (layout/ref/<cell>.spice; r2r and tx_drv have no parameters and keep the xschem one),
  and the instance parameters dropped (the refs carry the values);
- tx_top's enable level shifters as tx_ls_en (the layout cell of tx_ls with kn = kp = 1);
- Ctrim as the ctrim_1p cell;
- xdig (radio_digital) re-ordered to the port order of macros/radio_digital/radio_digital.pnl.v
  (xschem orders it by the symbol's pins; netgen reads the verilog's).
The decaps (decap_vapwr / decap_vdpwr) come from layout/ref/ when those exist.

    python3 layout/lvs_top_src.py     (after the xschem netlist is in build/lvs/top/)
"""
import os
import re

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
OUT = os.path.join(REPO, 'build/lvs/top')
SCH = os.path.join(OUT, 'tt_um_mattvenn_radio.spice')
REFS = ['bias_gen', 'lna_chain', 'log_det', 'lpf_rc', 'avg_sc', 'comp_ct', 'dbg_tg', 'tx_ring', 'tx_ls',
        'tx_ls_en', 'ctrim_1p', 'decap_vapwr', 'decap_vdpwr']
KEEP = ['tt_um_mattvenn_radio', 'radio_analog', 'tx_top', 'r2r', 'tx_drv', 'decap_vapwr', 'decap_vdpwr']


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


def strip_params(ln):
    return ' '.join(w for w in ln.split() if '=' not in w)


def main():
    sch = subckts(lines(SCH))
    defs = {}
    for c in REFS:
        p = os.path.join(REPO, 'layout/ref', c + '.spice')
        if os.path.exists(p):
            for n, body in subckts(lines(p)).items():
                defs.setdefault(n, body)
    for c in KEEP:
        if c not in defs:
            defs[c] = sch[c]
    cells = set(defs)

    # instance lines of the kept hierarchy: drop parameters of laid-out cells, rename
    sp = sym_pins(os.path.join(REPO, 'xschem/radio_digital.sym'))
    vp = verilog_ports(os.path.join(REPO, 'macros/radio_digital/radio_digital.pnl.v'))
    assert sorted(sp) == sorted(vp), set(sp) ^ set(vp)
    for top in ('tt_um_mattvenn_radio', 'radio_analog', 'tx_top'):
        body = []
        for ln in defs[top]:
            w = ln.split()
            if w and w[0][0] in 'xX' and not ln.startswith('XC'):
                ws = strip_params(ln).split()
                cell = ws[-1]
                if top == 'tx_top' and ws[0] in ('xlse_p', 'xlse_n'):
                    ws[-1] = cell = 'tx_ls_en'
                if cell == 'radio_digital':
                    m = dict(zip(sp, ws[1:-1]))
                    ws = [ws[0]] + [m[p] for p in vp] + [cell]
                assert cell in cells or cell == 'radio_digital', (top, cell)
                ln = ' '.join(ws)
            elif ln.startswith('XCtrim'):
                ln = 'xctrim trim VGND ctrim_1p'
            body.append(ln)
        defs[top] = body

    order = ['tt_um_mattvenn_radio', 'radio_analog', 'tx_top'] + sorted(n for n in defs if n not in
                                                                       ('tt_um_mattvenn_radio', 'radio_analog', 'tx_top'))
    path = os.path.join(OUT, 'tt_um_mattvenn_radio_src.spice')
    with open(path, 'w') as f:
        f.write('* top-level LVS source (layout/lvs_top_src.py)\n')
        for n in order[::-1]:
            f.write('\n'.join(defs[n]) + '\n\n')
    print('wrote', path, len(defs), 'subckts')


main()
