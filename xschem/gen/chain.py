"""
Generate the RX gain chain (the limiter for the successive-detection log
detector) and its testbench:

  amp_dp    : NMOS diff pair, resistor loads, tail gate = pin nb (bias is
              mirrored from one diode for the whole chain). Instance params
              w l rl (pair W/L, load R) and mt (tail = mt x unit W=wt, L=0.5).
  amp_dpc   : amp_dp with the tail split in two (mt/2 each) and cs between
              the sources: capacitive degeneration. Full gain above
              ~gm/(2 cs), 20 dB/decade below it, ~0 differential gain at DC.
  lna_chain : on-chip input coupling (cin + rb to vcm) -> stage 1 (amp_dp,
              big, low noise) -> N-1 smaller amp_dpc stages, DC coupled (each
              output CM ~ next input CM ~ VDD - 0.6 V). The degeneration
              shapes the low side of the band (FM broadcast, our 10 MHz clock)
              and stops offsets accumulating, without loading any node.
              Reference: ibias into a diode of unit W, so stage tail current =
              mt x ibias. Stage outputs o<i>p / o<i>n (i < N) are pins too:
              the taps for the successive-detection log detector.
  tb_chain  : the tb_lna front end (dipole, pad_model) -> lna_chain.

    python xschem/gen/chain.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from xsch import Sch, mim, mos, poly_r, ports, write_symbol
from frontend import antenna_pad

XDIR = os.path.normpath(os.path.join(HERE, '..'))
NSTAGES = 6

AMP_PARAMS = {'w': 20, 'l': 0.15, 'rl': '4k', 'wt': 6, 'mt': 5}
AMPC_PARAMS = dict(AMP_PARAMS, mt=6, cs='0.6p')
CHAIN_PARAMS = {'w1': 80, 'rl1': '1k', 'mt1': 20, 'w2': 20, 'rl2': '4k', 'mt2': 6,
                'cs': '0.6p', 'cin': '2p', 'rb': '20k'}


def amp_dp():
    s = Sch()
    s.text(-400, -560, 'amp_dp: NMOS diff pair, resistor loads, tail gate from pin nb\n'
           'params: w l rl (pair, load), mt (tail multiplier of unit W=wt, L=0.5)', 0.4)
    ports(s, -400, -460, ['VDD', 'VSS', 'nb', 'inp', 'inn', 'outp', 'outn'])
    for side, x, gate, drain, sgn in (('p', 0, 'inp', 'outn', '+'), ('n', 300, 'inn', 'outp', '-')):
        r = poly_r(s, x + 20, -300, 'rl', 'high', '1p41', name=f'Rl_{side}')
        s.connect(r, P='VDD', M=drain, B='VSS')
        m = mos(s, 'n', x, -150, W=f"'w*(1{sgn}mm/2)'", L="'l'", nf=4, name=f'M{side}')
        s.connect(m, D=drain, G=gate, S='tail', B='VSS')
    mt = mos(s, 'n', 150, 50, W="'wt'", L=0.5, nf=2, mult="'mt'", name='Mtail')
    s.connect(mt, D='tail', G='nb', S='VSS', B='VSS')
    s.write(os.path.join(XDIR, 'amp_dp.sch'))
    write_symbol(os.path.join(XDIR, 'amp_dp.sym'), left=['inp', 'inn', 'nb'],
                 right=['outp', 'outn'], top=['VDD'], bottom=['VSS'], params=AMP_PARAMS)


def amp_dpc():
    s = Sch()
    s.text(-400, -560, 'amp_dpc: NMOS diff pair, resistor loads, split tail + cs between sources\n'
           'params: w l rl (pair, load), mt (total tail multiplier, mt/2 per side), cs', 0.4)
    ports(s, -400, -460, ['VDD', 'VSS', 'nb', 'inp', 'inn', 'outp', 'outn'])
    for side, x, gate, drain, sgn in (('p', 0, 'inp', 'outn', '+'), ('n', 300, 'inn', 'outp', '-')):
        r = poly_r(s, x + 20, -300, 'rl', 'high', '0p69', name=f'Rl_{side}')
        s.connect(r, P='VDD', M=drain, B='VSS')
        m = mos(s, 'n', x, -150, W=f"'w*(1{sgn}mm/2)'", L="'l'", nf=4, name=f'M{side}')
        s.connect(m, D=drain, G=gate, S=f's{side}', B='VSS')
        mt = mos(s, 'n', x, 50, W="'wt'", L=0.5, nf=2, mult="'mt/2'", name=f'Mtail_{side}')
        s.connect(mt, D=f's{side}', G='nb', S='VSS', B='VSS')
    # Cs as two MIM halves, anti-parallel: each source sees one bottom plate
    for nm, top, bot, y in (('Cs_a', 'sn', 'sp', -60), ('Cs_b', 'sp', 'sn', 60)):
        c = mim(s, 150, y, 'cs/2', name=nm)
        s.connect(c, c0=top, c1=bot)
    s.write(os.path.join(XDIR, 'amp_dpc.sch'))
    write_symbol(os.path.join(XDIR, 'amp_dpc.sym'), left=['inp', 'inn', 'nb'],
                 right=['outp', 'outn'], top=['VDD'], bottom=['VSS'], params=AMPC_PARAMS)


def lna_chain(n=NSTAGES):
    s = Sch()
    s.text(-600, -760, f'lna_chain: {n} diff-pair stages; stage 1 sized for noise, 2..{n} cap-degenerated\n'
           'tail current of stage i = mt x ibias (one reference diode)', 0.4)
    taps = [f'o{i}{sd}' for i in range(1, n) for sd in 'pn']
    ports(s, -600, -660, ['VDD', 'VSS', 'ibias', 'vcm', 'inp', 'inn', 'outp', 'outn'] + taps)
    md = mos(s, 'n', -400, 300, W=AMP_PARAMS['wt'], L=0.5, nf=2, name='Mref')
    s.connect(md, D='ibias', G='ibias', S='VSS', B='VSS')
    prev = ('inp', 'inn')
    for i in range(1, n + 1):
        x = (i - 1) * 700
        first = i == 1
        last = i == n
        outp, outn = ('outp', 'outn') if last else (f'o{i}p', f'o{i}n')
        if first:
            for side, y, src in (('p', -400, prev[0]), ('n', -200, prev[1])):
                # bottom plate on the pad side (already ~5 pF there)
                c = mim(s, x - 250, y, 'cin', name=f'Cin_{side}')
                s.connect(c, c0=f'g1{side}', c1=src)
                rb = poly_r(s, x - 150, y + 60, 'rb', 'high', '0p35', name=f'Rb_{side}')
                s.connect(rb, P='vcm', M=f'g1{side}', B='VSS')
            a = s.place('amp_dp.sym', x, -300, name='xa1',
                        w="'w1'", l='0.15', rl="'rl1'", wt=AMP_PARAMS['wt'], mt="'mt1'")
            gp, gn = 'g1p', 'g1n'
        else:
            a = s.place('amp_dpc.sym', x, -300, name=f'xa{i}', w="'w2'", l='0.15', rl="'rl2'",
                        wt=AMP_PARAMS['wt'], mt="'mt2'", cs="'cs'")
            gp, gn = prev
        s.connect(a, inp=gp, inn=gn, nb='ibias', outp=outp, outn=outn, VDD='VDD', VSS='VSS')
        prev = (outp, outn)
    s.write(os.path.join(XDIR, 'lna_chain.sch'))
    write_symbol(os.path.join(XDIR, 'lna_chain.sym'), left=['inp', 'inn', 'ibias', 'vcm'],
                 right=['outp', 'outn'] + taps, top=['VDD'], bottom=['VSS'], params=CHAIN_PARAMS,
                 width=200)


PARAMS = """
.param f0=433.92e6
* transient EMF (differential amplitude); -80 dBm from 73 ohm = 76.4 uV
.param vemf=76.4e-6
.param vcmi=20e-3 fcmi=10e6
.param mm=0.01
* reference current (stage tail = mt x iref) and gate bias
.param iref=60u vcm_dc=1.2
* chain sizing (passed to x1; sweep these)
.param w1=80 rl1=1k mt1=20 w2=20 rl2=4k mt2=6 cs=0.6p cin=2p rb=20k
"""

CONTROL = """
.options method=GEAR
.control
op
let idd = -i(vdpwr)
print idd
print v(o1p)-v(o1n) v(o2p)-v(o2n) v(out_p)-v(out_n)
write tb_chain_op.raw
ac dec 100 1meg 3g
write tb_chain_acdiff.raw
alter @vant_p[acmag]=0
alter @vant_n[acmag]=0
alter @vcmi[acmag]=1
ac dec 100 1meg 3g
write tb_chain_accm.raw
alter @vcmi[acmag]=0
alter @vdpwr[acmag]=1
ac dec 100 1meg 3g
write tb_chain_acpsrr.raw
alter @vdpwr[acmag]=0
noise v(out_p,out_n) vant_p dec 50 100meg 1.5g
setplot previous
write tb_chain_noise.raw
.endc
"""


def tb_chain():
    s = Sch()
    s.place('sky130_fd_pr/corner.sym', -1400, -620, name='CORNER', only_toplevel='true', corner='tt')
    s.text(-1400, -760, 'tb_chain: dipole -> pad_model -> lna_chain', 0.6)
    s.text(-1400, -710, 'analyse with: python sim/chain/analyse.py', 0.3)
    antenna_pad(s)
    x1 = s.place('lna_chain.sym', -300, -150, name='x1', w1="'w1'", rl1="'rl1'", mt1="'mt1'",
                 w2="'w2'", rl2="'rl2'", mt2="'mt2'", cs="'cs'", cin="'cin'", rb="'rb'")
    s.connect(x1, inp='pad_p', inn='pad_n', ibias='ibias', vcm='vcm', outp='out_p', outn='out_n',
              VDD='VDPWR', VSS='GND', **{f'o{i}{sd}': f'o{i}{sd}' for i in range(1, NSTAGES) for sd in 'pn'})
    ib = s.place('devices/isource.sym', -500, 250, name='Iref', value="'iref'")
    s.connect(ib, p='VDPWR', m='ibias')
    vcm = s.place('devices/vsource.sym', -300, 250, name='Vcm', value="'vcm_dc'")
    s.connect(vcm, p='vcm', m='GND')
    for side, x in (('p', 100), ('n', 200)):
        c = s.place('devices/capa.sym', x, 100, name=f'Cload_{side}', value='50f', m='1')
        s.connect(c, p=f'out_{side}', m='GND')
    s.code(-1400, 450, 'SIMULATION', PARAMS + CONTROL)
    s.write(os.path.join(XDIR, 'tb_chain.sch'))


if __name__ == '__main__':
    amp_dp()
    amp_dpc()
    lna_chain()
    tb_chain()
    print('wrote amp_dp, amp_dpc, lna_chain (.sch/.sym), tb_chain.sch')
