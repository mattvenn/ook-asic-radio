"""The tile netlist with its supply metal replaced by the mesh (sim/power/mesh.py), and the TT PDN
outside the tile, for the AC / transient power runs.

magic's extraction (build/power/ext_<case>/) keeps the devices, the signal nets' R and C, and every
C that touches a supply net. Its supply R network is dropped (it lumps much of each net into the
port, sim/power/r_mesh.py) and replaced by the mesh:
- each device's supply terminal (VDPWR.tN ...) joins the mesh node at its position through its own
  terminal resistance (diffusion / contact: the magic resistors from it to the rest of its net, in
  parallel);
- each C on a supply node moves to the mesh node at that node's position (any layer, nearest within
  3 um; else the port);
- mesh nodes are p<D|A|G>_m<layer>_<ix>_<iy>; the port nodes stay VDPWR / VAPWR / VGND.

pdn_model(): what replaces the testbench's ideal supplies: source -> R_up + L_up (package, bond wire,
assumed) -> the chip grid (C_chip to the chip's VGND, assumed) -> the gate (pdn.R_GATE) -> the tile's
port; the tile's VGND port is the chip grid, which goes to the board ground through R_up + L_up.
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import pdn  # noqa: E402
import r_mesh  # noqa: E402

PFX = {'VDPWR': 'pD_', 'VAPWR': 'pA_', 'VGND': 'pG_'}
ALL = tuple(range(6))


def build(case, pitch=1.0):
    """(netlist lines of radio_analog_lay with the mesh, {supply terminal: mesh node})"""
    xy = common.node_xy(case)
    lines = common.raw_lines(case)
    mesh, meta, alive = {}, {}, {}
    for net in common.SUP:
        meta[net], ml = r_mesh.load_mesh(case, net, pitch)
        ml, alive[net], _ = r_mesh.connected(ml, net)
        mesh[net] = ml

    def mnode(net, n, layers=ALL, radius=3.0):
        if n in common.SUP or n not in xy:
            return net
        m = r_mesh.place(meta[net], xy[n], alive[net], layers, radius)
        return PFX[net] + m if m else net

    # terminal resistance of each device supply terminal: its magic resistors to non-terminal
    # nodes of its net, in parallel
    gt = collections.Counter()
    for ln in lines:
        t = ln.split()
        if t and t[0][0] in 'Rr' and common.supply_of(t[1]) and common.supply_of(t[2]):
            for a, b in ((t[1], t[2]), (t[2], t[1])):
                if '.t' in a and '.t' not in b:
                    gt[a] += 1.0 / max(float(t[3]), 1e-6)
    out, term = [], {}
    nmesh = collections.Counter()
    for ln in lines:
        t = ln.split()
        if not t or ln.startswith('*'):
            out.append(ln)
            continue
        if ln.lower().startswith('.ends'):
            # the mesh, then each terminal's own resistance to it
            for net in common.SUP:
                for m in mesh[net]:
                    if m.startswith('R'):
                        r = m.split()
                        a = r[1] if r[1] == net else PFX[net] + r[1]
                        b = r[2] if r[2] == net else PFX[net] + r[2]
                        out.append(f'Rm{PFX[net]}{r[0][1:]} {a} {b} {r[3]}')
                        nmesh[net] += 1
            for k, (n, node) in enumerate(sorted(term.items())):
                out.append(f'Rterm{k} {n} {node} {1.0 / gt[n] if gt[n] else 0.01:.5g}')
            out.append(ln)
            continue
        c = t[0][0].upper()
        if c == 'R' and (common.supply_of(t[1]) or common.supply_of(t[2])):
            continue                                   # magic's supply R network: replaced
        if c == 'C':
            a, b = t[1], t[2]
            sa, sb = common.supply_of(a), common.supply_of(b)
            a = mnode(sa, a) if sa else a
            b = mnode(sb, b) if sb else b
            if a == b:
                continue
            out.append(f'{t[0]} {a} {b} ' + ' '.join(t[3:]))
            continue
        if c == 'X':
            for n in t[1:]:
                s = common.supply_of(n)
                if s and '.t' in n and n not in term:
                    # li / met1 first (where the device is), then any layer
                    m = mnode(s, n, (0, 1), 1.5)
                    term[n] = m if m != s else mnode(s, n)
        out.append(ln)
    return out, term, nmesh


def pdn_model(deck, up=common.UP, r_gate=pdn.R_GATE):
    """Replace the testbench's ideal VDPWR / VA sources and the tile's direct VGND with the PDN."""
    deck, n1 = re.subn(r'^VDPWR VDPWR GND dc 1\.8 ac 0$', 'VDPWR vd_src GND dc 1.8 ac 0', deck, flags=re.M)
    deck, n2 = re.subn(r'^VA VAPWR GND 3\.3$', 'VA va_src GND 3.3', deck, flags=re.M)
    deck, n3 = re.subn(r'(\+ pad_p pad_n dbg VDPWR VAPWR) GND (radio_analog)', r'\1 vg_chip \2', deck)
    assert (n1, n2, n3) == (1, 1, 1), (n1, n2, n3)
    R, L, C = up['R'], up['L'], up['CHIP_C']
    pdn_lines = f"""
* PDN outside the tile (sim/power/stitch.py): package / bond wire (assumed), chip grid C (assumed),
* the power gates (sim/power/pg_rdson.spice)
Rup_d vd_src vd_l {R}
Lup_d vd_l vd_chip {L}
Rup_a va_src va_l {R}
Lup_a va_l va_chip {L}
Rup_g vg_chip vg_l {R}
Lup_g vg_l GND {L}
Cchip_d vd_chip vg_chip {C}
Cchip_a va_chip vg_chip {C}
Rgate_d vd_chip VDPWR {r_gate['VDPWR']}
Rgate_a va_chip VAPWR {r_gate['VAPWR']}
"""
    return re.sub(r'^\.end\s*$', pdn_lines + '.end', deck, flags=re.M)


def tile_text(case, pitch=1.0):
    """The stitched radio_analog_lay + the radio_analog wrapper (digital stubs tied 1G to VGND)."""
    lines, term, nmesh = build(case, pitch)
    wrap = common.sch_wrapper(case, lines)
    wl = wrap.splitlines()
    stubs = sorted(set(re.findall(r'\bnc_\w+', wl[-2] if wl[-1].startswith('.ends') else wrap)))
    i = max(k for k, l in enumerate(wl) if l.startswith('.ends'))
    wl[i:i] = [f'Rnc{k} {s} VGND 1G' for k, s in enumerate(stubs)]
    return '\n'.join(wl) + '\n', term, nmesh


if __name__ == '__main__':
    case = sys.argv[1] if len(sys.argv) > 1 else 'A'
    txt, term, nmesh = tile_text(case)
    path = os.path.join(common.B, f'tile_mesh_{case}.spice')
    open(path, 'w').write(txt)
    on_port = sum(1 for v in term.values() if v in common.SUP)
    print(f'{path}: mesh R {dict(nmesh)}, {len(term)} supply terminals ({on_port} fell back to the port)')
