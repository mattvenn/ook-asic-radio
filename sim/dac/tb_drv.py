"""Output resistance of the trim-bit drivers: sky130_fd_sc_hd__clkdlybuf4s25_1 (macro trim_out[7:0]).

DC: one cell with A high sourcing 0..100 uA, one with A low sinking 0..100 uA (a bit leg draws at most
1.8 V / 21 kOhm ~ 86 uA). Reports per corner and temperature:
  R_hi / R_lo  chord resistance at 40 uA (the typical leg current: |Vbit - Vnode| / 2R ~ 0.9 V / 21 k)
  r0           small-signal slope at 0..5 uA, r86 chord at 86 uA (the extremes the ladder sees)

    python3 sim/dac/tb_drv.py [--cell=<std cell>] [corner ...]       default tt ss ff sf fs
--cell: another sky130_fd_sc_hd buffer (non-inverting, pins A VGND VNB VPB VPWR X), e.g. buf_4 for a re-driver
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.environ.get('OSIC', os.path.join(ROOT, 'tools', 'osic'))
TEMPS = [10, 27, 50, 85]
CELL = 'sky130_fd_sc_hd__clkdlybuf4s25_1'


def deck(corner, cell=CELL):
    pdk = os.environ.get('PDK_ROOT', '/foss/pdks')
    loop = ''
    for t in TEMPS:
        loop += f"""reset
option temp = {t}
dc Il 0 100u 1u
meas dc h5 find v(xh) at=5u
meas dc l5 find v(xl) at=5u
meas dc h40 find v(xh) at=40u
meas dc l40 find v(xl) at=40u
meas dc h86 find v(xh) at=86u
meas dc l86 find v(xl) at=86u
meas dc h0 find v(xh) at=0
meas dc l0 find v(xl) at=0
let r0h = (h0 - h5) / 5u
let r0l = (l5 - l0) / 5u
let r40h = (1.8 - h40) / 40u
let r40l = l40 / 40u
let r86h = (1.8 - h86) / 86u
let r86l = l86 / 86u
echo RES {t} $&r40h $&r40l $&r0h $&r0l $&r86h $&r86l $&h0 $&l0
destroy all
"""
    return f"""* tb_drv {corner}
.lib {pdk}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
.include {pdk}/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice
VDD vdd 0 1.8
xh vdd 0 0 vdd vdd xh {cell}
xl 0 0 0 vdd vdd xl {cell}
* the same current out of the high cell and into the low cell
Il 0 n 0
Vil n 0 0
Fh xh 0 Vil 1
Fl 0 xl Vil 1
.control
set num_threads=1
{loop}
.endc
.end
"""


def run(corner, cell=CELL):
    name = f'tb_drv_{corner}' + ('' if cell == CELL else '_' + cell.split('__')[1])
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(corner, cell))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    rows = re.findall(r'^RES (\d+) (.*)$', log, re.M)
    if len(rows) != len(TEMPS):
        sys.exit(f'{name}: missing results; see build/{name}.log')
    return {int(t): [float(x) for x in v.split()] for t, v in rows}


if __name__ == '__main__':
    corners = [a for a in sys.argv[1:] if not a.startswith('-')] or ['tt', 'ss', 'ff', 'sf', 'fs']
    cell = next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--cell=')), CELL)
    cell = cell if cell.startswith('sky130') else 'sky130_fd_sc_hd__' + cell
    print(cell)
    print('corner  T   R_hi  R_lo (40 uA)   r0 hi/lo     r86 hi/lo    (Ohm)   Voh/Vol at 0 uA')
    for c in corners:
        for t, (rh, rl, r0h, r0l, r86h, r86l, h0, l0) in run(c, cell).items():
            print(f'{c:5s} {t:3d}  {rh:5.0f} {rl:5.0f}        {r0h:5.0f}/{r0l:<5.0f}  {r86h:5.0f}/{r86l:<5.0f}         '
                  f'{h0:.4f}/{l0 * 1e3:.2f} mV')
