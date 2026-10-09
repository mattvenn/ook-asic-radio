"""Shared helpers for the power study (sim/power/): the extracted tile with the TT PDN drawn in
(sim/power/pex_power.sh -> build/power/ext_<case>/), its supply probe points per block, and the
PDN model outside the tile.
"""
import collections
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build', 'power')
OSIC = os.environ.get('OSIC', os.path.join(ROOT, 'tools', 'osic-mac'))
SUP = ('VDPWR', 'VAPWR', 'VGND')

# Outside the tile, per supply (ASSUMED, not from TT: bond wire + package + the chip grid to the gate).
# The gates' on-resistance is in pdn.R_GATE (simulated). CHIP_C: the chip-wide grid's own
# capacitance at the gate input (other tiles, the pad ring): a guess, swept in the AC run.
UP = {'R': 0.5, 'L': 2e-9, 'CHIP_C': 1e-9}


def ext_dir(case):
    return os.path.join(B, f'ext_{case}')


def raw_lines(case):
    """The extracted netlist with '+' continuations joined."""
    lines = []
    for ln in open(os.path.join(ext_dir(case), 'radio_analog_lay_raw.spice')):
        ln = ln.rstrip('\n')
        if ln.startswith('+') and lines:
            lines[-1] += ' ' + ln[1:].strip()
        else:
            lines.append(ln)
    return lines


def supply_of(node):
    """'VDPWR' for VDPWR / VDPWR.n12 / VDPWR.t3, None for anything else."""
    base = node.split('.')[0]
    return base if base in SUP else None


def block_of(node):
    """Block instance a hierarchical node belongs to: 'comp_ct_0', 'tx_top_0.tx_drv_1', ..."""
    m = re.match(r'(tx_top_0\.[a-z_]+_\d+|[a-z0-9_]+_\d+)\.', node)
    return m.group(1) if m else None


NICE = {'lna_chain_0': 'chain', 'log_det_0': 'log_det', 'lpf_rc_0': 'lpf', 'avg_sc_0': 'avg_sc',
        'comp_ct_0': 'comp_ct', 'r2r_0': 'r2r', 'bias_gen_0': 'bias', 'dbg_tg_0': 'dbg_tg',
        'tx_top_0.tx_drv_0': 'tx_drv_0', 'tx_top_0.tx_drv_1': 'tx_drv_1', 'tx_top_0.tx_ls_0': 'tx_ls',
        'tx_top_0.tx_ls_en_0': 'tx_ls_en_0', 'tx_top_0.tx_ls_en_1': 'tx_ls_en_1',
        'tx_top_0.tx_ring_0': 'tx_ring'}


CHAIN_NETS = re.compile(r'^(o[1-5][pn]|out_?[pn])$')


def device_block(nodes, model):
    blks = sorted({block_of(n) for n in nodes} - {None})
    if blks:
        return NICE.get(blks[0], blks[0])
    if any(CHAIN_NETS.match(n) for n in nodes):
        return 'chain'
    sups = {supply_of(n) for n in nodes} - {None}
    if 'VAPWR' in sups and 'VGND' in sups and ('g5v0d10v5' in model or 'cap_mim' in model):
        return 'decap_a'
    if 'VDPWR' in sups and 'VGND' in sups and ('nfet_01v8' in model or 'cap_mim' in model):
        return 'decap_d'
    return 'other'


def devices(case):
    """(model, nodes, block) of every device in the extracted tile."""
    out = []
    for ln in raw_lines(case):
        t = ln.split()
        if not t or t[0][0] not in 'Xx':
            continue
        nodes = [n for n in t[1:] if '=' not in n]
        model, nodes = nodes[-1], nodes[:-1]
        out.append((model, nodes, device_block(nodes, model)))
    return out


POS = {'xchain': 'chain', 'xdet': 'log_det', 'xlpf': 'lpf', 'xavg': 'avg_sc', 'xcomp': 'comp_ct',
       'xdac': 'r2r', 'xctrim': 'ctrim', 'xbias': 'bias', 'xdbg': 'dbg_tg', 'xtx.xring': 'tx_ring',
       'xtx.xls': 'tx_ls', 'xtx.xlse_p': 'tx_lse_p', 'xtx.xlse_n': 'tx_lse_n', 'xtx.xdrv_p': 'tx_drv_p',
       'xtx.xdrv_n': 'tx_drv_n'}


def node_xy(case):
    """{node: (x, y)} in tile um, from the extraction's .res.ext."""
    xy = {}
    for ln in open(os.path.join(ext_dir(case), 'radio_analog_lay.res.ext')):
        if ln.startswith('rnode'):
            t = ln.split()
            xy[t[1].strip('"')] = (int(t[4]) * 0.005, int(t[5]) * 0.005)
    return xy


def locate(xy, model, insts):
    """Block at a point: the blocks first, then the decap parts (decap part 5 is MIM over r2r)."""
    x, y = xy
    inside = [k for k, b in insts.items() if b[0] - 0.5 <= x <= b[2] + 0.5 and b[1] - 0.5 <= y <= b[3] + 0.5]
    if 'cap_mim' in model and any(k.startswith('xdeca') for k in inside):
        return 'decap_a'
    for k in inside:
        if k in POS:
            return POS[k]
    for k in inside:
        if k.startswith('xdeca'):
            return 'decap_a'
        if k.startswith('xdecd'):
            return 'decap_d'
    return 'route'


def probes(case):
    """{block: {supply: [terminal nodes]}}: the supply nodes the devices of each block draw current
    through (MOS drain / source, resistor and capacitor ends; not MOS bulk or a resistor's body),
    the block found from the terminal's position (build/top/pins.json bounding boxes)."""
    insts = json.load(open(os.path.join(ROOT, 'build', 'top', 'pins.json')))['insts']
    xy = node_xy(case)
    out = collections.defaultdict(lambda: collections.defaultdict(set))
    for model, nodes, _ in devices(case):
        cur = [nodes[0], nodes[2]] if 'fet' in model else nodes[:2]
        for n in cur:
            s = supply_of(n)
            if s and n in xy:
                out[locate(xy[n], model, insts)][s].add(n)
    return {b: {s: sorted(v) for s, v in d.items()} for b, d in out.items()}


def rail_probes(case, pr=None):
    """probes() moved to the metal side: each device terminal (.tN) replaced by the node(s) at the
    far end of the resistor(s) attached to it, so the device's own diffusion / contact R (up to
    ~360 ohm for a one-contact source) isn't counted as PDN resistance."""
    pr = pr or probes(case)
    nb = collections.defaultdict(set)
    for ln in r_only(case):
        t = ln.split()
        nb[t[1]].add(t[2]); nb[t[2]].add(t[1])
    out = {}
    for b, d in pr.items():
        out[b] = {}
        for s, nodes in d.items():
            r = set()
            for n in nodes:
                far = {m for m in nb[n] if '.t' not in m} or {n}
                r |= far
            out[b][s] = sorted(r)
    return out


def sch_wrapper(case, lines=None):
    """.subckt radio_analog with the schematic's port order around the extracted radio_analog_lay
    (as layout/pex_tile.sh), plus the extracted netlist itself (or `lines`, a modified copy)."""
    lines = lines or raw_lines(case)
    ports = None
    for ln in lines:
        if ln.lower().startswith('.subckt radio_analog_lay'):
            ports = ln.split()[2:]
    sch = ['rx_en', 'tx_en', 'tx_en_n', 'dbg_en', 'sc_phi1', 'sc_phi2'] + \
          [f'trim[{i}]' for i in range(7, -1, -1)] + \
          ['comp_out', 'tx_p', 'tx_n', 'rx_p', 'rx_n', 'dbg', 'VDPWR', 'VAPWR', 'VGND']
    tile = {'ua[3]': 'tx_p', 'ua[4]': 'tx_n', 'ua[0]': 'rx_p', 'ua[1]': 'rx_n', 'ua[2]': 'dbg'}
    conn = []
    for p in ports:
        s = tile.get(p, p)
        if p in ('VSUBS', 'VSUB'):
            s = 'VGND'          # the substrate, as one node tied to the VGND port (not modelled)
        conn.append(s if s in sch else f'nc_{re.sub(r"[^A-Za-z0-9_]", "_", p)}')
    missing = [s for s in sch if s not in conn]
    assert not missing, missing
    return '\n'.join(lines) + '\n\n.subckt radio_analog ' + ' '.join(sch) + '\nX1 ' + ' '.join(conn) + \
        ' radio_analog_lay\n.ends\n'


def r_only(case, nets=SUP):
    """The resistors of the supply nets only (devices and C dropped), at top level."""
    out = []
    for ln in raw_lines(case):
        t = ln.split()
        if t and t[0][0] in 'Rr' and supply_of(t[1]) in nets and supply_of(t[2]) in nets:
            out.append(ln)
    return out
