"""
Generate the trim DAC ladder (reused layout: mattvenn/tt08-analog-r2r-dac-3v3
mag/r2r.mag) and its testbench.

  r2r     : 8-bit R-2R ladder matching the reused layout device for device
            (its r2r.lvs.spice), so LVS lines up: unit R = res_high_po_1p41
            L 45 (~10.6 kOhm), 2R = two units in series.
              start module : b0 -2R- a, a -2R- VGND (termination), 1 dummy
              7 bit tiles  : a(i) -R- a(i+1), a(i+1) -2R- b(i+1)
              end module   : 1 dummy
            out = a after the last tile = code / 256 x V(bits); Rout = R.
            Driven straight from the digital's trim_out (1.8 V std-cell
            outputs). The comparator compares this against its own VDD/2,
            so VDD ripple cancels to first order near the operating code.
  tb_dac  : codes 0 / 1 / 85 / 128 / 135 / 255 -> out, output resistance,
            and VDD sensitivity at code 135 relative to VDD/2.

    python xschem/gen/dac.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from xsch import Sch, ports, write_symbol

XDIR = os.path.normpath(os.path.join(HERE, '..'))
UNIT = dict(L='45', model='res_high_po_1p41', mult='1', spiceprefix='X')
RSYM = 'sky130_fd_pr/res_high_po_1p41.sym'


def r2r():
    s = Sch()
    s.pin_order = ['b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'out', 'VGND']
    s.text(-500, -560, 'r2r: 8-bit R-2R ladder, matches the reused tt08 r2r layout\n'
           'unit R = res_high_po_1p41 L 45 (~10.6 k); 2R = two units; out = code/256 x V(bits)', 0.4)
    n = [0]
    YA, YG = -300, 80                       # ladder node row, VGND rail
    gnd = []

    def unit(p, m, x, y, rot=0):
        n[0] += 1
        r = s.place(RSYM, x, y, rot=rot, name=f'R{n[0]}', **UNIT)
        s.connect(r, B='VGND')
        return r

    def leg(x, top, bot):
        """2R leg from the node row down: two stacked units joined at a labelled mid node"""
        s.bus((x, YA), top.pin('M' if top.rot == 2 else 'P'))
        s.bus(top.pin('P' if top.rot == 2 else 'M'), bot.pin('M' if bot.rot == 2 else 'P'), [(x, -140)])

    def dummy(x):
        r = unit('VGND', 'VGND', x, 200)
        s.route(r.pin('P'), (x, YG))
        s.label(r.pin('M'), 'VGND', right=True)
        gnd.append((x, YG))

    def bit(x, pin, b):
        s.route(pin, (x, 0))
        s.port((x, 0), b, right=True)
    # start module: b0 -2R- a0 (drawn upside down: a0 on top), a0 -2R- VGND (termination), dummy
    lo = unit('b0', 's0', 0, -80, rot=2)
    up = unit('s0', 'a0', 0, -200, rot=2)
    leg(0, up, lo)
    s.label((0, -140), 's0', right=True)
    bit(0, lo.pin('P'), 'b0')
    up = unit('a0', 's1', -250, -200)
    lo = unit('s1', 'VGND', -250, -80)
    leg(-250, up, lo)
    s.label((-250, -140), 's1')
    s.route(lo.pin('M'), (-250, YG))
    gnd.append((-250, YG))
    dummy(-500)
    s.label((0, YA), 'a0', right=True)
    for i in range(1, 8):
        a_prev, a_next = f'a{i - 1}', 'out' if i == 7 else f'a{i}'
        x = i * 250
        r = unit(a_prev, a_next, x - 125, YA, rot=3)      # series R along the node row
        s.route((x - 250, YA), r.pin('P'))
        s.route(r.pin('M'), (x, YA))
        up = unit(a_next, f't{i}', x, -200)               # 2R to the bit
        lo = unit(f't{i}', f'b{i}', x, -80)
        leg(x, up, lo)
        s.label((x, -140), f't{i}', right=True)
        bit(x, lo.pin('M'), f'b{i}')
        if i < 7:
            s.label((x, YA), a_next, right=True)
    s.route((1750, YA), (1900, YA))
    s.port((1900, YA), 'out', right=True)
    s.route((-250, YA), (0, YA))
    dummy(1900)                                           # end dummy
    s.rail(YG, -500, 1900, gnd, 'VGND', port=True)
    s.write(os.path.join(XDIR, 'r2r.sch'))
    write_symbol(os.path.join(XDIR, 'r2r.sym'), left=[f'b{i}' for i in range(8)], right=['out'],
                 bottom=['VGND'])


TB_CODE = """
.param code=0 vdd=1.8
.control
echo code out_V ideal_V
foreach c 0 1 85 128 135 255
  alterparam code = $c
  reset
  op
  let ideal = $c / 256 * 1.8
  echo RESULT code $c out $&v(out) ideal $&ideal
  destroy all
end
* output resistance at code 135: 1 uA into out
alterparam code = 135
reset
op
let v0 = v(out)
set v0s = $&v0
destroy all
alter @iout[dc] = 1u
op
let rout = (v(out) - $v0s) / 1u
echo RESULT rout_ohm $&rout
destroy all
alter @iout[dc] = 0
* VDD sensitivity at code 135, relative to VDD/2 (what the trim pair sees)
alterparam vdd = 1.81
reset
op
let d = (v(out) - 0.905) - ($v0s - 0.9)
let s = d / 0.01
echo RESULT dtrim_minus_dvdd2_per_dvdd $&s
.endc
"""


def tb_dac():
    s = Sch()
    s.place('sky130_fd_pr/corner.sym', -1000, -620, name='CORNER', only_toplevel='true', corner='tt')
    s.text(-1000, -760, 'tb_dac: r2r driven by ideal 1.8 V bits (B-sources from code)', 0.5)
    for i in range(8):
        b = s.place('devices/vsource.sym', -900 + i * 120, -400, name=f'Vb{i}',
                    value=f"'vdd*(floor(code/{2 ** i})-2*floor(code/{2 ** (i + 1)}))'")
        s.connect(b, p=f'b{i}', m='GND')
    x = s.place('r2r.sym', -300, -100, name='x1')
    s.connect(x, out='out', VGND='GND', **{f'b{i}': f'b{i}' for i in range(8)})
    i = s.place('devices/isource.sym', 0, -100, name='Iout', value='0')
    s.connect(i, p='GND', m='out')
    s.code(-1000, 100, 'SIMULATION', TB_CODE)
    s.write(os.path.join(XDIR, 'tb_dac.sch'))


if __name__ == '__main__':
    r2r()
    tb_dac()
    print('wrote r2r (.sch/.sym), tb_dac.sch')
