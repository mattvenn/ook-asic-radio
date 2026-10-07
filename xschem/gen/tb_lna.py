"""
Generate xschem/tb_lna_dp.sch and xschem/tb_lna_pinv.sch: the first-stage LNA
experiment. Same front end as tb_input (balanced 73 ohm dipole -> pad_model
per side), on-chip AC coupling, then the stage under test (x1) loaded by an
identical copy of itself (x2).

Sources:
  Vant_p/n : antiphase dipole EMF (ac 0.5 / 0.5 @180 => 1 V differential)
  Vcmi     : in the antenna common path (board/digital junk, our 10 MHz clock)
  VDPWR    : 1.8 V, with an ac term for PSRR

The control block writes raw files only; sim/lna/analyse.py does the numbers
and plots.

    python xschem/gen/tb_lna.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from xsch import Sch
from frontend import antenna_pad

XDIR = os.path.normpath(os.path.join(HERE, '..'))

PARAMS = """
.param f0=433.92e6
* vemf: differential EMF amplitude for the transient. -80 dBm from 73 ohm:
* vemf = sqrt(8 * 73 * 1e-11) = 76.4 uV
.param vemf=76.4e-6
* common-mode interferer: 20 mV at 10 MHz (our clock)
.param vcmi=20e-3 fcmi=10e6
* 1 % device mismatch between the p and n halves (so CM -> diff shows up)
.param mm=0.01
* lna_dp sizing
.param w_dp=20 l_dp=0.15 rl_dp=2k wt_dp=6 vcm_dp=1.2 ibias_dp=60u rb_dp=20k
* lna_dpp sizing (output CM = drop across rl to ground ~0.6 V; input CM to match)
.param w_dpp=80 l_dpp=0.15 rl_dpp=2k wt_dpp=12 vcm_dpp=0.6 ibias_dpp=60u rb_dpp=20k
* lna_pinv sizing
.param wn_inv=10 wp_inv=20 rf_inv=20k
.param cc=2p
"""

CONTROL = """
.options method=GEAR
.control
op
let idd = -i(vdpwr)
print idd v(in_p) v(o1p) v(o1n) {extra_op}
write tb_lna_{kind}_op.raw
* 1: differential input
ac dec 100 1meg 3g
write tb_lna_{kind}_acdiff.raw
* 2: common-mode input (source in the antenna common path)
alter @vant_p[acmag]=0
alter @vant_n[acmag]=0
alter @vcmi[acmag]=1
ac dec 100 1meg 3g
write tb_lna_{kind}_accm.raw
* 3: supply
alter @vcmi[acmag]=0
alter @vdpwr[acmag]=1
ac dec 100 1meg 3g
write tb_lna_{kind}_acpsrr.raw
alter @vdpwr[acmag]=0
* noise at the first stage output, whole front end included
noise v(o1p,o1n) vant_p dec 100 10meg 3g
setplot previous
write tb_lna_{kind}_noise.raw
* same at the stage 2 output: the cascade, stage 2 noise included
noise v(o2p,o2n) vant_p dec 100 10meg 3g
setplot previous
write tb_lna_{kind}_noise2.raw
* weak -80 dBm signal + 20 mV 10 MHz common-mode interferer
tran 20p 400n
write tb_lna_{kind}_tran.raw
.endc
"""


def tb(kind):
    s = Sch()
    s.place('sky130_fd_pr/corner.sym', -1400, -620, name='CORNER', only_toplevel='true', corner='tt')
    s.text(-1400, -760, f'tb_lna_{kind}: first-stage LNA experiment ({kind}), loaded by a copy of itself', 0.6)
    s.text(-1400, -710, 'dipole (36.5 ohm per side, common path through Vcmi) -> pad_model -> Cc -> x1 -> x2\n'
           'analyse with: python sim/lna/analyse.py', 0.3)

    antenna_pad(s)
    for side, y in (('p', -300), ('n', 40)):
        c = s.place('devices/capa.sym', -600, y - 60, rot=1, name=f'Cc_{side}', value="'cc'", m='1')
        s.connect(c, p=f'in_{side}', m=f'pad_{side}')
        if kind != 'pinv':
            rb = s.place('devices/res.sym', -500, y, name=f'Rb_{side}', value=f"'rb_{kind}'", m='1')
            s.connect(rb, P='vcm', M=f'in_{side}')

    if kind != 'pinv':
        vcm = s.place('devices/vsource.sym', -500, 300, name='Vcm', value=f"'vcm_{kind}'")
        s.connect(vcm, p='vcm', m='GND')
        for i, x in ((1, -300), (2, 100)):
            ib = s.place('devices/isource.sym', x - 100, 250, name=f'Ib{i}', value=f"'ibias_{kind}'")
            # dp: current into an NMOS diode; dpp: current out of a PMOS diode
            if kind == 'dp':
                s.connect(ib, p='VDPWR', m=f'ib{i}')
            else:
                s.connect(ib, p=f'ib{i}', m='GND')

    for i, x, inp, inn, outp, outn in ((1, -200, 'in_p', 'in_n', 'o1p', 'o1n'),
                                        (2, 300, 'i2p', 'i2n', 'o2p', 'o2n')):
        if kind != 'pinv':
            # diff pair output CM ~ its input CM, so the load copy is DC coupled
            inp, inn = ('o1p', 'o1n') if i == 2 else (inp, inn)
        x1 = s.place(f'lna_{kind}.sym', x, -150, name=f'x{i}')
        nets = dict(inp=inp, inn=inn, outp=outp, outn=outn, VDD='VDPWR', VSS='GND')
        if kind != 'pinv':
            nets['ibias'] = f'ib{i}'
        s.connect(x1, **nets)
    if kind == 'pinv':
        # self-biased stages: AC couple into the load copy
        for side, y in (('p', -350), ('n', 50)):
            c = s.place('devices/capa.sym', 100, y, rot=1, name=f'Cc2_{side}', value="'cc'", m='1')
            s.connect(c, p=f'i2{side}', m=f'o1{side}')

    extra = 'v(o2p)' if kind == 'pinv' else 'v(x1.tail)'
    s.code(-1400, 450, 'SIMULATION', PARAMS + CONTROL.format(kind=kind, extra_op=extra))
    s.launcher(-1400, 900, 'load tran', f'xschem raw_read $netlist_dir/tb_lna_{kind}_tran.raw tran')
    s.graph(-200, 250, 700, 600, ['"o1 diff; o1p o1n -"'],
            x_lo=0, x_hi=400e-9, y_lo=-0.02, y_hi=0.02,
            title='tran: stage 1 differential output (V)')
    out = os.path.join(XDIR, f'tb_lna_{kind}.sch')
    s.write(out)
    print('wrote', out)


for k in ('dp', 'dpp', 'pinv'):
    tb(k)
