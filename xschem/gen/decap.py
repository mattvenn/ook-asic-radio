"""
Generate the supply decoupling blocks (placed in radio_analog).

  decap_vapwr : n units, each = thick-oxide MOS cap (nfet_g5v0d10v5, gate on
                VAPWR, source / drain / body on VGND, so it sits in inversion;
                2 fingers W 10 / L 5 to keep the channel resistance low at
                434 MHz) + a 10 x 10 um MIM above it (top plate VAPWR).
                Estimated ~0.3 pF (thick Cox ~3 fF/um^2) + 0.21 pF MIM per
                unit; default n = 100 -> ~50 pF (sim/tx/vapwr.sh: 50 pF keeps
                the 434 MHz ripple on VAPWR to ~0.05 V pp).
  decap_vdpwr : the same with thin-oxide nfet_01v8 on VDPWR (thin Cox
                ~8 fF/um^2): ~0.8 + 0.21 pF per unit; default n = 30 -> ~30 pF,
                local decoupling for the RX.
MIM is rated 0..5 V between plates (SkyWater PDK docs, cap_mim), so it is
fine on VAPWR. The per-unit capacitance is an estimate from oxide
thicknesses: check it with a small AC run (not done yet).

    python xschem/gen/decap.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from xsch import Sch, mos, ports, write_symbol

XDIR = os.path.normpath(os.path.join(HERE, '..'))


def decap(name, sup, vt, n):
    s = Sch()
    s.text(-500, -460, f'{name}: n units of MOS cap (gate {sup}; S/D/B VGND; 2 x W10/L5, '
           f'{"thick g5v0d10v5" if vt else "thin 01v8"}) + 10x10 um MIM above (top plate {sup})', 0.4)
    ports(s, -500, -360, [sup, 'VGND'])
    m = mos(s, 'n', 0, 0, W=10, L=5, nf=1, mult="'2*n'", name='Mcap', vt=vt)
    s.connect(m, D='VGND', G=sup, S='VGND', B='VGND')
    c = s.place('sky130_fd_pr/cap_mim_m3_1.sym', 200, 0, name='Cmim', model='cap_mim_m3_1',
                W='10', L='10', MF="'n'", spiceprefix='X')
    s.connect(c, c0=sup, c1='VGND')
    s.write(os.path.join(XDIR, f'{name}.sch'))
    write_symbol(os.path.join(XDIR, f'{name}.sym'), top=[sup], bottom=['VGND'], params={'n': n}, width=120)


if __name__ == '__main__':
    decap('decap_vapwr', 'VAPWR', 'g5', 100)
    decap('decap_vdpwr', 'VDPWR', '', 30)
    print('wrote decap_vapwr, decap_vdpwr (.sch/.sym)')
