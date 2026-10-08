"""
Generate the analog top, the TT top level and a whole-analog testbench.

  radio_analog          : every analog block, wired as on the chip, real bias, decap:
      bias_gen (en = rx_en) -> vcm, ib_chain 60 uA, ib_det 2 uA, ib_comp 1 uA
      RX: rx_p/rx_n -> lna_chain -> log_det -> det -> lpf_rc -> lpf
          avg_sc (in lpf, sc_phi1/2) -> avg; comp_ct inp avg, inn lpf,
          trim = r2r(trim[7:0]) + Ctrim -> comp_out
          det -> dbg_tg (dbg_en) -> dbg
      TX: tx_top (key = tx_en, en_p = tx_en, en_n = tx_en_n) -> tx_p / tx_n
  radio_digital (symbol): the hardened macro, a black box here (spice_sym_def);
      its netlist comes from the OpenLane run.
  tt_um_mattvenn_radio  : radio_analog + radio_digital on the TT pins.
      ua[0] / ua[1] TX dipole, ua[2] / ua[3] RX dipole, ua[4] debug (det).
  tb_radio_analog       : radio_analog with the RX front end (dipole + pad
      models), pad models + dipole on the TX pins, a probe on ua[4], and
      sources for the digital interface. RX on: bias, operating points,
      det with / without a -60 dBm tone. TX keyed (RX off): power.

    python xschem/gen/top.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from xsch import Sch, mim, ports, write_symbol
from frontend import antenna_pad
import chain

XDIR = os.path.normpath(os.path.join(HERE, '..'))
NT = chain.NSTAGES
DIG_IN = ['clk', 'rst_n', 'ui_in[7:0]', 'uio_in[7:0]', 'comp_in']
DIG_OUT = ['uo_out[7:0]', 'uio_out[7:0]', 'uio_oe[7:0]', 'trim_out[7:0]', 'tx_en', 'tx_en_n', 'rx_en',
           'dbg_en', 'sc_phi1', 'sc_phi2']
ANA_IF_IN = ['rx_en', 'tx_en', 'tx_en_n', 'dbg_en', 'sc_phi1', 'sc_phi2', 'trim[7:0]']
ANA_PADS = ['tx_p', 'tx_n', 'rx_p', 'rx_n', 'dbg']


def radio_analog():
    s = Sch()
    s.text(-1400, -1060, 'radio_analog: all analog blocks, real bias (bias_gen on rx_en)\n'
           'RX: rx_p/n -> lna_chain -> log_det -> lpf_rc -> avg_sc / comp_ct (+ r2r trim) -> comp_out; '
           'det -> dbg_tg -> dbg. TX: tx_top -> tx_p/n', 0.4)
    ports(s, -1400, -960, ['VDPWR', 'VAPWR', 'VGND'] + ANA_IF_IN + ['comp_out'] + ANA_PADS)
    b = s.place('bias_gen.sym', -900, 400, name='xbias')
    s.connect(b, en='rx_en', vcm='vcm', ib_chain='ib_chain', ib_det='ib_det', ib_comp='ib_comp',
              VDD='VDPWR', VSS='VGND')
    taps = {f'o{i}{sd}': f'o{i}{sd}' for i in range(1, NT) for sd in 'pn'}
    c = s.place('lna_chain.sym', -500, -150, name='xchain')
    s.connect(c, inp='rx_p', inn='rx_n', ibias='ib_chain', vcm='vcm', outp='out_p', outn='out_n',
              VDD='VDPWR', VSS='VGND', **taps)
    d = s.place('log_det.sym', 100, -150, name='xdet')
    nets = {f't{i}{sd}': f'o{i}{sd}' for i in range(1, NT) for sd in 'pn'}
    nets.update({f't{NT}p': 'out_p', f't{NT}n': 'out_n'})
    s.connect(d, ibias_det='ib_det', det='det', VDD='VDPWR', VSS='VGND', **nets)
    f = s.place('lpf_rc.sym', 600, -150, name='xlpf')
    s.connect(f, **{'in': 'det'}, out='lpf', VSS='VGND')
    a = s.place('avg_sc.sym', 900, 0, name='xavg')
    s.connect(a, **{'in': 'lpf'}, out='avg', phi1='sc_phi1', phi2='sc_phi2', VDD='VDPWR', VSS='VGND')
    r = s.place('r2r.sym', 900, 400, name='xdac')
    s.connect(r, out='trim', VGND='VGND', **{f'b{i}': f'trim[{i}]' for i in range(8)})
    ct = mim(s, 1100, 500, 1e-12, name='Ctrim')                 # strips clock-edge spikes (10.6k Rout)
    s.connect(ct, c0='trim', c1='VGND')
    k = s.place('comp_ct.sym', 1300, -100, name='xcomp')
    s.connect(k, inp='avg', inn='lpf', trim='trim', ibias='ib_comp', out='comp_out', VDD='VDPWR', VSS='VGND')
    g = s.place('dbg_tg.sym', 600, 300, name='xdbg')
    s.connect(g, a='det', b='dbg', en='dbg_en', VDD='VDPWR', VSS='VGND')
    t = s.place('tx_top.sym', -500, 700, name='xtx')
    s.connect(t, key='tx_en', en_p='tx_en', en_n='tx_en_n', out_p='tx_p', out_n='tx_n', VDPWR='VDPWR',
              VAPWR='VAPWR', VSS='VGND')
    # supply decoupling (xschem/gen/decap.py): ~50 pF on VAPWR (TX), ~30 pF on VDPWR (RX)
    da = s.place('decap_vapwr.sym', 0, 700, name='xdeca')
    s.connect(da, VAPWR='VAPWR', VGND='VGND')
    dd = s.place('decap_vdpwr.sym', 300, 700, name='xdecd')
    s.connect(dd, VDPWR='VDPWR', VGND='VGND')
    s.write(os.path.join(XDIR, 'radio_analog.sch'))
    write_symbol(os.path.join(XDIR, 'radio_analog.sym'), left=ANA_IF_IN, right=['comp_out'] + ANA_PADS,
                 top=['VDPWR', 'VAPWR'], bottom=['VGND'], width=240)


def radio_digital_sym():
    """Black-box symbol of the hardened digital macro (no schematic)."""
    path = os.path.join(XDIR, 'radio_digital.sym')
    write_symbol(path, left=DIG_IN, right=DIG_OUT, top=['VPWR'], bottom=['VGND'], width=240)
    txt = open(path).read().replace(
        'K {type=subcircuit',
        'K {type=subcircuit\nspice_sym_def="** radio_digital: hardened macro (openlane/radio_digital); '
        'gate-level netlist from the OpenLane run"')
    open(path, 'w').write(txt)


def tt_top():
    s = Sch()
    s.text(-900, -760, 'tt_um_mattvenn_radio: radio_analog + radio_digital (hardened macro) on the TT pins\n'
           'ua[0]/ua[1] TX dipole, ua[2]/ua[3] RX dipole, ua[4] debug (det, dbg_en only)', 0.4)
    ports(s, -900, -660, ['VGND', 'VDPWR', 'VAPWR', 'ui_in[7:0]', 'uo_out[7:0]', 'uio_in[7:0]',
                          'uio_out[7:0]', 'uio_oe[7:0]', 'ua[7:0]', 'ena', 'clk', 'rst_n'])
    dg = s.place('radio_digital.sym', -300, 0, name='xdig')
    s.connect(dg, clk='clk', rst_n='rst_n', **{'ui_in[7:0]': 'ui_in[7:0]', 'uio_in[7:0]': 'uio_in[7:0]',
              'uo_out[7:0]': 'uo_out[7:0]', 'uio_out[7:0]': 'uio_out[7:0]', 'uio_oe[7:0]': 'uio_oe[7:0]',
              'trim_out[7:0]': 'trim[7:0]'},
              comp_in='comp', tx_en='tx_en', tx_en_n='tx_en_n', rx_en='rx_en', dbg_en='dbg_en',
              sc_phi1='sc_phi1', sc_phi2='sc_phi2', VPWR='VDPWR', VGND='VGND')
    an = s.place('radio_analog.sym', 400, 0, name='xana')
    s.connect(an, rx_en='rx_en', tx_en='tx_en', tx_en_n='tx_en_n', dbg_en='dbg_en', sc_phi1='sc_phi1',
              sc_phi2='sc_phi2', comp_out='comp', VDPWR='VDPWR', VAPWR='VAPWR', VGND='VGND',
              tx_p='ua[0]', tx_n='ua[1]', rx_p='ua[2]', rx_n='ua[3]', dbg='ua[4]', **{'trim[7:0]': 'trim[7:0]'})
    s.write(os.path.join(XDIR, 'tt_um_mattvenn_radio.sch'))


TB_CODE = chain.PARAMS + """
.param ven_rx=1.8 ven_tx=0 vdbg=0
.options method=GEAR
* save only what is measured: the 80 ns TX run with every node saved trips
* ngspice's memory check (it counts free RAM, not page cache)
.save v(xana.vcm) v(xana.det) v(xana.lpf) v(xana.trim) v(tx_p) v(tx_n) v(ant_tx_p) v(ant_tx_n) i(va) i(vdpwr)
.control
* 1: RX on, TX off, no signal: operating point
op
let idp = -i(vdpwr) * 1e3
let iap = -i(va) * 1e3
echo RESULT op_rx IDPWR_mA $&idp IAPWR_mA $&iap vcm $&v(xana.vcm) det $&v(xana.det) lpf $&v(xana.lpf) trim $&v(xana.trim) tx_p $&v(tx_p) tx_n $&v(tx_n)
destroy all
* 2: everything off (rx_en = 0, tx_en = 0)
alterparam ven_rx = 0
reset
op
let idp = -i(vdpwr) * 1e6
let iap = -i(va) * 1e6
echo RESULT op_off IDPWR_uA $&idp IAPWR_uA $&iap
destroy all
* 3: RX on, -60 dBm tone at 434 MHz (EMF 0.764 mV): det level (vs op_rx)
alterparam ven_rx = 1.8
alterparam vemf = 7.64e-4
reset
tran 50p 600n 400n
meas tran detavg avg v(xana.det) from=500n to=600n
echo RESULT rx_m60dBm det $&detavg
destroy all
* 4: TX keyed 5..60 ns, RX off
alterparam vemf = 0
alterparam ven_rx = 0
alterparam ven_tx = 1.8
reset
tran 2p 80n 0
write tb_radio_analog_tx.raw
.endc
"""


def tb_radio_analog():
    s = Sch()
    s.place('sky130_fd_pr/corner.sym', -1400, -620, name='CORNER', only_toplevel='true', corner='tt')
    s.code(-1200, -620, 'STDCELLS', '.include $::SKYWATER_STDCELLS/sky130_fd_sc_hd.spice',
           only_toplevel='true', tcleval=True)
    s.text(-1400, -760, 'tb_radio_analog: radio_analog with pad models, both dipoles, debug probe, '
           'digital interface from sources', 0.5)
    s.text(-1400, -710, 'RESULT lines: RX op, all-off current, det at -60 dBm; TX raw for sim/tx/tb_tx.py-style analysis',
           0.3)
    antenna_pad(s)                                     # VDPWR source, RX dipole -> pad_p / pad_n
    va = s.place('devices/vsource.sym', -1100, -420, name='VA', value='3.3')
    s.connect(va, p='VAPWR', m='GND')
    for nm, net, val in (('Vrx', 'rx_en', "'ven_rx'"), ('Vdbg', 'dbg_en', "'vdbg'"),
                         ('Vtx', 'tx_en', '"pwl(0 0 5n 0 5.05n \'ven_tx\' 60n \'ven_tx\' 60.05n 0)"'),
                         ('Vtxn', 'tx_en_n', '"pwl(0 0 5n 0 5.05n \'ven_tx\' 60n \'ven_tx\' 60.05n 0)"'),
                         ('Vphi1', 'sc_phi1', '"pulse(0 1.8 0 10n 10n 6.09u 13u)"'),
                         ('Vphi2', 'sc_phi2', '"pulse(0 1.8 6.5u 10n 10n 6.09u 13u)"')):
        v = s.place('devices/vsource.sym', -900 + len(s.items) * 3, 600, name=nm, value=val)
        s.connect(v, p=net, m='GND')
    for i in range(8):                                 # trim code 135 = 1000 0111
        v = s.place('devices/vsource.sym', -300 + i * 100, 700, name=f'Vt{i}',
                    value='1.8' if (135 >> i) & 1 else '0')
        s.connect(v, p=f'trim[{i}]', m='GND')
    x = s.place('radio_analog.sym', 0, 0, name='xana')
    s.connect(x, rx_en='rx_en', tx_en='tx_en', tx_en_n='tx_en_n', dbg_en='dbg_en', sc_phi1='sc_phi1',
              sc_phi2='sc_phi2', comp_out='comp', VDPWR='VDPWR', VAPWR='VAPWR', VGND='GND',
              tx_p='tx_p', tx_n='tx_n', rx_p='pad_p', rx_n='pad_n', dbg='dbg', **{'trim[7:0]': 'trim[7:0]'})
    # TX pins -> pad models -> dipole; debug pin -> pad model -> scope
    for side, y in (('p', -150), ('n', 50)):
        pad = s.place('pad_model.sym', 700, y, flip=1, name=f'xpadtx_{side}')
        s.connect(pad, pin=f'ant_tx_{side}', mod=f'tx_{side}', VGND='GND')
    r = s.place('devices/res.sym', 1000, -150, name='Rdip', value='73', m='1')
    s.connect(r, P='ant_tx_p', M='dmid')
    c = s.place('devices/capa.sym', 1000, 50, name='Cdip', value='100p', m='1')
    s.connect(c, p='dmid', m='ant_tx_n')
    pad = s.place('pad_model.sym', 700, 300, flip=1, name='xpaddbg')
    s.connect(pad, pin='dbg_pin', mod='dbg', VGND='GND')
    r = s.place('devices/res.sym', 1000, 300, name='Rprobe', value='1Meg', m='1')
    s.connect(r, P='dbg_pin', M='GND')
    s.code(-1400, 900, 'SIMULATION', TB_CODE)
    s.write(os.path.join(XDIR, 'tb_radio_analog.sch'))


if __name__ == '__main__':
    radio_analog()
    radio_digital_sym()
    tt_top()
    tb_radio_analog()
    print('wrote radio_analog (.sch/.sym), radio_digital.sym, tt_um_mattvenn_radio.sch, tb_radio_analog.sch')
