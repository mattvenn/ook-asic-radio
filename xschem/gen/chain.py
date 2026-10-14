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
from xsch import Sch, mim, mos, poly_r, ports, write_symbol, value_notes
from frontend import antenna_pad

XDIR = os.path.normpath(os.path.join(HERE, '..'))
NSTAGES = 6

# defaults = the chip's values (stage 1 / stages 2-6), so the sheets' value notes are the chip's
AMP_PARAMS = {'w': 80, 'l': 0.15, 'rl': '1k', 'wt': 6, 'mt': 20, 'mm': 0}   # mm: test mismatch, 0 in silicon
AMPC_PARAMS = {'w': 20, 'l': 0.15, 'rl': '4k', 'wt': 6, 'mt': 6, 'mm': 0, 'cs': '0.6p'}
CHAIN_PARAMS = {'w1': 80, 'rl1': '1k', 'mt1': 20, 'w2': 20, 'rl2': '4k', 'mt2': 6,
                'cs': '0.6p', 'cin': '2p', 'rb': '20k', 'mm': 0}


def diff_pair(s, r_w, rl='rl', after_side=None):
    """Textbook resistor-loaded NMOS pair: VDD rail on top, loads, the pair
    (right half mirrored), outputs and inputs wired out to ports at the sides.
    Returns the two source pins (left, right) for the caller's tail."""
    XL, XR, YV = -200, 600, -420
    tops, srcs = [], []
    for side, x, gate, drain, sgn, fl in (('p', 0, 'inp', 'outn', '+', 0), ('n', 400, 'inn', 'outp', '-', 1)):
        r = poly_r(s, x, -320, rl, 'high', r_w, name=f'Rl_{side}')
        s.connect(r, B='VSS')
        m = mos(s, 'n', x + (20 if fl else -20), -150, W=f"'w*(1{sgn}mm/2)'", L="'l'", nf=4,
                name=f'M{side}', flip=fl, body='VSS')
        if after_side:
            after_side(side, x, fl, m)
        tap = (x, -240)
        s.bus(r.pin('M'), m.pin('D'), [tap])
        edge = XR if fl else XL
        s.route(tap, (edge, -240))
        s.port((edge, -240), drain, right=bool(fl))
        s.route(m.pin('G'), (edge, -150))
        s.port((edge, -150), gate, right=bool(fl))
        tops.append(r.pin('P'))
        srcs.append(m.pin('S'))
    s.rail(YV, XL, XR - 200, tops, 'VDD', port=True)
    return srcs


def amp_dp():
    s = Sch()
    s.pin_order = ['VDD', 'VSS', 'nb', 'inp', 'inn', 'outp', 'outn']
    s.text(-200, -560, 'amp_dp: NMOS diff pair, resistor loads, tail gate from pin nb\n'
           'params: w l rl (pair, load), mt (tail multiplier of unit W=wt, L=0.5)', 0.4)
    sp, sn = diff_pair(s, '1p41')
    mt = mos(s, 'n', 180, 10, W="'wt'", L=0.5, nf=2, mult="'mt'", name='Mtail', body='VSS')
    s.route(sp, (0, -80))
    s.route(sn, (400, -80))
    s.bus((0, -80), (400, -80), [(200, -80)])
    s.route((200, -80), mt.pin('D'))
    s.label((200, -80), 'tail', right=True)
    s.route(mt.pin('G'), (-200, 10))
    s.port((-200, 10), 'nb')
    s.rail(100, -200, 400, [mt.pin('S')], 'VSS', port=True)
    value_notes(s, AMP_PARAMS)
    s.write(os.path.join(XDIR, 'amp_dp.sch'))
    write_symbol(os.path.join(XDIR, 'amp_dp.sym'), left=['inp', 'inn', 'nb'],
                 right=['outp', 'outn'], top=['VDD'], bottom=['VSS'], params=AMP_PARAMS)


def amp_dpc():
    s = Sch()
    s.pin_order = ['VDD', 'VSS', 'nb', 'inp', 'inn', 'outp', 'outn']
    s.text(-200, -560, 'amp_dpc: NMOS diff pair, resistor loads, split tail + cs between sources\n'
           'params: w l rl (pair, load), mt (total tail multiplier, mt/2 per side), cs', 0.4)

    def tail(side, x, fl, m):
        mt = mos(s, 'n', x + (20 if fl else -20), 10, W="'wt'", L=0.5, nf=2, mult="'mt/2'",
                 name=f'Mtail_{side}', flip=fl, body='VSS')
        y = -90 if fl else -30            # sn joins the caps' top line, sp the bottom one
        s.bus(m.pin('S'), mt.pin('D'), [(x, y)])
        s.label((x, y), f's{side}', right=bool(fl))
        tails.append(mt)
    tails = []
    diff_pair(s, '0p69', after_side=tail)
    # Cs as two MIM halves, anti-parallel: each source sees one bottom plate
    # (Cs_b drawn upside down: top plate c0 at the bottom, on sp)
    ca = mim(s, 120, -60, 'cs/2', name='Cs_a')
    cb = mim(s, 280, -60, 'cs/2', rot=2, name='Cs_b')
    s.bus((0, -30), cb.pin('c0'), [ca.pin('c1')])
    s.bus(ca.pin('c0'), (400, -90), [cb.pin('c1')])
    s.route(tails[0].pin('G'), (-200, 10))
    s.port((-200, 10), 'nb')
    s.label(tails[1].pin('G'), 'nb', right=True)
    s.rail(100, -200, 400, [t.pin('S') for t in tails], 'VSS', port=True)
    value_notes(s, AMPC_PARAMS, at={'Cs_a': (-10, -58), 'Cs_b': (-170, 48)})
    s.write(os.path.join(XDIR, 'amp_dpc.sch'))
    write_symbol(os.path.join(XDIR, 'amp_dpc.sym'), left=['inp', 'inn', 'nb'],
                 right=['outp', 'outn'], top=['VDD'], bottom=['VSS'], params=AMPC_PARAMS)


def lna_chain(n=NSTAGES):
    s = Sch()
    taps = [f'o{i}{sd}' for i in range(1, n) for sd in 'pn']
    s.pin_order = ['VDD', 'VSS', 'ibias', 'vcm', 'inp', 'inn', 'outp', 'outn'] + taps
    s.text(-1000, -400, f'lna_chain: {n} diff-pair stages; stage 1 sized for noise, 2..{n} cap-degenerated\n'
           'tail current of stage i = mt x ibias (one reference diode); taps o<i>p/n = stage outputs', 0.4)
    XL, YV, YS = -1000, -220, 220
    # reference diode: stage tail = mt x ibias (each stage's nb labelled ibias)
    md = mos(s, 'n', -860, 150, W=AMP_PARAMS['wt'], L=0.5, nf=2, name='Mref', body='VSS')
    s.bus((XL, 100), (-840, 100), [(-900, 100)])
    s.route((-900, 100), (-900, 150), md.pin('G'))
    s.route((-840, 100), md.pin('D'))
    s.port((XL, 100), 'ibias')
    vdd, vss = [], [md.pin('S')]
    for i in range(1, n + 1):
        x = (i - 1) * 400
        first = i == 1
        last = i == n
        outp, outn = ('outp', 'outn') if last else (f'o{i}p', f'o{i}n')
        if first:
            # on-chip input coupling: Cin (bottom plate on the pad side, already ~5 pF there)
            # in series, Rb from vcm to the gate
            for side, y, src, cy, crot, ry, rrot in (('p', -40, 'inp', -70, 2, -70, 0),
                                                     ('n', 0, 'inn', 30, 0, 30, 2)):
                c = mim(s, x - 650, cy, 'cin', rot=crot, name=f'Cin_{side}')
                rb = poly_r(s, x - 350, ry, 'rb', 'high', '0p35', rot=rrot, name=f'Rb_{side}')
                s.connect(rb, B='VSS')
                s.bus(c.pin('c0'), (x - 100, y), [rb.pin('M')])
                s.label(c.pin('c0'), f'g1{side}')
                py = c.pin('c1')[1]
                s.route(c.pin('c1'), (XL, py))
                s.port((XL, py), src)
                if side == 'p':
                    s.route(rb.pin('P'), (x - 350, -160), (XL, -160))
                    s.port((XL, -160), 'vcm')
                else:
                    s.label(rb.pin('P'), 'vcm', right=True)
            a = s.place('amp_dp.sym', x, 0, name='xa1',
                        w="'w1'", l='0.15', rl="'rl1'", wt=AMP_PARAMS['wt'], mt="'mt1'", mm="'mm'")
        else:
            a = s.place('amp_dpc.sym', x, 0, name=f'xa{i}', w="'w2'", l='0.15', rl="'rl2'",
                        wt=AMP_PARAMS['wt'], mt="'mt2'", cs="'cs'", mm="'mm'")
        s.label(a.pin('nb'), 'ibias')
        vdd.append(a.pin('VDD'))
        vss.append(a.pin('VSS'))
        if last:
            for pin, net in (('outp', 'outp'), ('outn', 'outn')):
                q = a.pin(pin)
                s.route(q, (q[0] + 100, q[1]))
                s.port((q[0] + 100, q[1]), net, right=True)
        else:
            # straight on to the next stage, with the tap brought out as a port
            for pin, nxt, net, tx, ty in (('outp', 'inp', outp, 180, -120), ('outn', 'inn', outn, 220, 120)):
                q = a.pin(pin)
                s.bus(q, (x + 300, q[1]), [(x + tx, q[1])])
                s.route((x + tx, q[1]), (x + tx, ty))
                s.port((x + tx, ty), net, right=True)
    s.rail(YV, XL, (n - 1) * 400, vdd, 'VDD', port=True)
    s.rail(YS, XL, (n - 1) * 400, vss, 'VSS', port=True)
    value_notes(s, CHAIN_PARAMS)
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
                 w2="'w2'", rl2="'rl2'", mt2="'mt2'", cs="'cs'", cin="'cin'", rb="'rb'", mm="'mm'")
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
