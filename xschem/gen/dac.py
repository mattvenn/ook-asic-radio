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
    s.text(-800, -660, 'r2r: 8-bit R-2R ladder, matches the reused tt08 r2r layout\n'
           'unit R = res_high_po_1p41 L 45 (~10.6 k); 2R = two units; out = code/256 x V(bits)', 0.4)
    ports(s, -800, -560, ['b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'out', 'VGND'])
    n = [0]

    def unit(p, m, x, y):
        n[0] += 1
        r = s.place(RSYM, x, y, name=f'R{n[0]}', **UNIT)
        s.connect(r, P=p, M=m, B='VGND')
    # start module: b0 -2R- a0, a0 -2R- VGND, dummy
    unit('b0', 's0', -500, -200)
    unit('s0', 'a0', -500, -100)
    unit('a0', 's1', -400, -200)
    unit('s1', 'VGND', -400, -100)
    unit('VGND', 'VGND', -300, -200)
    for i in range(1, 8):
        a_prev, a_next = f'a{i - 1}', 'out' if i == 7 else f'a{i}'
        x = -200 + i * 200
        unit(a_prev, a_next, x, -300)                  # series R
        unit(a_next, f't{i}', x, -200)                 # 2R to the bit
        unit(f't{i}', f'b{i}', x, -100)
    unit('VGND', 'VGND', 1500, -200)                   # end dummy
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
