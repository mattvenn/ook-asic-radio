"""
Shared RX testbench front end: VDPWR (1.8 V, ac term for PSRR), Vcmi in the
antenna common path, balanced 73 ohm dipole (Vant_p/n antiphase, 36.5 ohm per
side) and pad_model per side. Leaves the core side on nets pad_p / pad_n.
Testbench params used: vemf, f0, vcmi, fcmi.
"""


def antenna_pad(s):
    vd = s.place('devices/vsource.sym', -1300, -420, name='VDPWR', value='"dc 1.8 ac 0"')
    s.connect(vd, p='VDPWR', m='GND')
    vc = s.place('devices/vsource.sym', -1300, 300, name='Vcmi',
                 value='"dc 0 ac 0 sin(0 \'vcmi\' \'fcmi\')"')
    s.connect(vc, p='acm', m='GND')
    for side, y, phase in (('p', -300, 0), ('n', 40, 180)):
        v = s.place('devices/vsource.sym', -1300, y, name=f'Vant_{side}',
                    value=f'"dc 0 ac 0.5 {phase} sin(0 \'vemf/2\' \'f0\' 0 0 {phase})"')
        s.connect(v, p=f'emf_{side}', m='acm')
        r = s.place('devices/res.sym', -1150, y - 60, rot=1, name=f'Rant_{side}', value='36.5', m='1')
        s.connect(r, P=f'ant_{side}', M=f'emf_{side}')
        pad = s.place('pad_model.sym', -850, y - 40, name=f'xpad_{side}')
        s.connect(pad, pin=f'ant_{side}', mod=f'pad_{side}', VGND='GND')
