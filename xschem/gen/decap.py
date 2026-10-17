"""
Generate the supply decoupling blocks (placed in radio_analog).

  decap_vapwr : thick-oxide MOS caps (nfet_g5v0d10v5, gate on VAPWR, source /
                drain / body on VGND, so they sit in inversion; L 5) + MIM
                caps (top plate VAPWR).
  decap_vdpwr : the same with thin-oxide nfet_01v8 on VDPWR.

The devices are the ones laid out (layout/gen/decap.py, the sum of its parts in
layout/ref/decap_*.spice), written out here by hand so the tile LVS compares
the layout against this schematic: a change to either shows up as an LVS
property error. Each group is one symbol with a multiplier: netgen adds the
W of parallel MOS of the same L, and matches the MIMs by size.

Planned (sim/tx/vapwr.sh: 50 pF keeps the 434 MHz ripple on VAPWR to ~0.05 V pp)
was n = 100 units of 2 x W10/L5 thick MOS + one 10 x 10 um MIM (~50 pF) on
VAPWR, and n = 30 units with thin MOS (~30 pF) on VDPWR. That was reduced to
what fits the 6-tile area beside the other blocks.

Capacitance per area from sim/decap/decap_ac.sh (docs/history.md): thick MOS
2.9 fF/um^2, thin MOS 7.9 fF/um^2, MIM 2.06 fF/um^2.

    python xschem/gen/decap.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from xsch import Sch, mos, write_symbol

XDIR = os.path.normpath(os.path.join(HERE, '..'))
L_MOS = 5
COX = {'g5': 2.9e-3, '': 7.9e-3}       # pF / um^2 of gate
CMIM = 2.06e-3                          # pF / um^2

# as laid out: MOS (W, nf, count), L = L_MOS; MIM (W, L, count)
LAYOUT = {
    'decap_vapwr': dict(
        sup='VAPWR', vt='g5',
        mos=[(19.8, 2, 32), (16.6, 2, 8), (12.6, 2, 38), (11.6, 2, 9)],
        mim=[(15.44, 19.8, 3), (14.08, 11.48, 4), (19.05, 15.8, 11), (14.47, 16.25, 12), (11.58, 18.69, 16)],
        planned='Planned: n = 100 units of 2 x W10/L5 thick MOS + one 10 x 10 um MIM: '
                '200 MOS (gate 10000 um2) + 100 MIM (10000 um2), ~50 pF'),
    'decap_vdpwr': dict(
        sup='VDPWR', vt='',
        mos=[(17.6, 2, 7), (8.5, 1, 6), (8.15, 1, 3)],
        mim=[(17, 19.52, 4)],
        planned='Planned: n = 30 units of 2 x W10/L5 thin MOS + one 10 x 10 um MIM: '
                '60 MOS (gate 3000 um2) + 30 MIM (3000 um2), ~30 pF'),
}
DX = 220


def decap(name, sup, vt, mos_groups, mim_groups, planned):
    s = Sch()
    s.pin_order = [sup, 'VGND']
    gate = sum(w * n for w, _, n in mos_groups) * L_MOS
    area = sum(w * l * n for w, l, n in mim_groups)
    c_mos, c_mim = gate * COX[vt], area * CMIM
    s.text(-300, -330, f'{name}: MOS caps (gate {sup}; S/D/B VGND; L {L_MOS}, '
           f'{"thick g5v0d10v5" if vt else "thin 01v8"}) + MIM caps (top plate {sup}), as laid out', 0.4)
    s.text(-300, -290, f'{sum(n for *_, n in mos_groups)} MOS, gate {gate:.0f} um2 (~{c_mos:.1f} pF) + '
           f'{sum(n for *_, n in mim_groups)} MIM, {area:.0f} um2 (~{c_mim:.1f} pF): ~{c_mos + c_mim:.0f} pF', 0.3)
    s.text(-300, 180, planned + '.', 0.3)
    s.text(-300, 210, 'Reduced to what fits the 6-tile area (layout/gen/decap.py fills the floorplan\'s decap parts).', 0.3)
    top, bot = [], []
    x = 0
    for i, (w, nf, n) in enumerate(mos_groups):
        m = mos(s, 'n', x, 0, W=w, L=L_MOS, nf=nf, mult=n, name=f'Mcap{i + 1}', vt=vt, body='VGND')
        # MOS cap: gate on the supply, drain and source tied to ground
        s.route(m.pin('G'), (x - 20, -100))
        s.route(m.pin('D'), (x + 80, -30), (x + 80, 30), m.pin('S'))
        top.append((x - 20, -100))
        bot.append(m.pin('S'))
        x += DX
    for i, (w, l, n) in enumerate(mim_groups):
        c = s.place('sky130_fd_pr/cap_mim_m3_1.sym', x, 0, flip=1, name=f'Cmim{i + 1}', model='cap_mim_m3_1',
                    W=f'{w:g}', L=f'{l:g}', MF=str(n), spiceprefix='X')
        top.append(c.pin('c0'))
        bot.append(c.pin('c1'))
        x += DX
    s.rail(-100, -300, x - DX, top, sup, port=True)
    s.rail(100, -300, x - DX, bot, 'VGND', port=True)
    s.write(os.path.join(XDIR, f'{name}.sch'))
    write_symbol(os.path.join(XDIR, f'{name}.sym'), top=[sup], bottom=['VGND'], width=120)
    return c_mos + c_mim


if __name__ == '__main__':
    for nm, d in LAYOUT.items():
        c = decap(nm, d['sup'], d['vt'], d['mos'], d['mim'], d['planned'])
        print(f'wrote {nm} (.sch/.sym): ~{c:.1f} pF')
