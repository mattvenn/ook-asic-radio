"""
Generate the ua[4] debug switch and its testbench.

  dbg_tg : thin-oxide transmission gate a <-> b, on when en = 1 (local
           inverter for the PMOS gate). Connects the log detector output
           'det' to the ua[4] pad in debug mode only (dbg_en from the
           digital: magic + uio_in[2] at reset). Off, det sees only the
           switch's off capacitance, so pickup on the pin / board trace /
           probe doesn't reach the ~1 mV signal near sensitivity, and the
           pad's ~5 pF and leakage are off det. Thin devices: keep ua[4]
           within 0..1.8 V.
  tb_dbg : det modelled as its source (Vdet behind rdet 8k || cdet 5p, as
           log_det) -> dbg_tg -> pad_model -> pin, with an external source
           on the pin (Vext behind rext: 50 ohm generator / pickup, or 1 Meg + 15 pF
           for a scope).
           Measures: Vext -> det isolation off / drive on (AC); det -> pin
           bandwidth on; det DC shift from the pad with the pin at 0 / 1.8 V,
           switch off and on.

    python xschem/gen/dbg.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from xsch import Sch, mos, ports, write_symbol

XDIR = os.path.normpath(os.path.join(HERE, '..'))
TG_PARAMS = {'wn': 2, 'wp': 4}


def dbg_tg():
    s = Sch()
    s.text(-600, -560, 'dbg_tg: transmission gate a <-> b, on when en = 1\n'
           'thin 1.8 V devices (keep the pad side within 0..1.8 V); local inverter for enb', 0.4)
    ports(s, -600, -460, ['VDD', 'VSS', 'en', 'a', 'b'])
    p = mos(s, 'p', -200, -150, W=1, L=0.15, name='Mip')
    s.connect(p, D='enb', G='en', S='VDD', B='VDD')
    n = mos(s, 'n', -200, 100, W=0.5, L=0.15, name='Min')
    s.connect(n, D='enb', G='en', S='VSS', B='VSS')
    n = mos(s, 'n', 200, 100, W="'wn'", L=0.15, name='Mn')
    s.connect(n, D='a', G='en', S='b', B='VSS')
    p = mos(s, 'p', 200, -150, W="'wp'", L=0.15, name='Mp')
    s.connect(p, D='a', G='enb', S='b', B='VDD')
    s.write(os.path.join(XDIR, 'dbg_tg.sch'))
    write_symbol(os.path.join(XDIR, 'dbg_tg.sym'), left=['a', 'en'], right=['b'], top=['VDD'],
                 bottom=['VSS'], params=TG_PARAMS)


TB_CODE = """
.param vdet=1.44 ven=0 vpin=0.9 rext=50
.options method=GEAR
.control
* AC from the pin source to det, switch off then on
foreach e 0 1.8
  alterparam ven = $e
  reset
  ac dec 20 1k 1g
  let g = db(v(det))
  meas ac g10k find g at=10e3
  meas ac g10m find g at=10e6
  meas ac g100m find g at=100e6
  echo RESULT ext_to_det en $e dB_10k $&g10k dB_10M $&g10m dB_100M $&g100m
  destroy all
end
* on: det -> pin bandwidth (source = Vdet) into a scope (1 Meg || 15 pF probe + cable)
alterparam ven = 1.8
alterparam rext = 1Meg
reset
alter @vext[acmag] = 0
alter @vdet[acmag] = 1
ac dec 20 1k 1g
let g = db(v(pin))
meas ac g0 find g at=1e3
let g3 = g0 - 3
meas ac f3db when g=g3 fall=1
echo RESULT det_to_pin_on dB_1k $&g0 f3dB $&f3db
destroy all
alter @vdet[acmag] = 0
alterparam rext = 50
* DC: det shift from the pad path (leakage, ESD) with the pin held at 0 / 1.8 V
foreach e 0 1.8
  foreach vp 0 1.8
    alterparam ven = $e
    alterparam vpin = $vp
    reset
    op
    let dv = (v(det) - 1.44) * 1e6
    echo RESULT dc en $e pin $vp det_shift_uV $&dv
    destroy all
  end
end
.endc
"""


def tb_dbg():
    s = Sch()
    s.place('sky130_fd_pr/corner.sym', -1000, -620, name='CORNER', only_toplevel='true', corner='tt')
    s.text(-1000, -760, 'tb_dbg: det (8k || 5p source) -> dbg_tg -> pad_model -> ua[4] pin <- Vext (50 ohm)', 0.5)
    s.text(-1000, -710, 'ven = 0 (normal) / 1.8 (debug); results: RESULT lines in the log', 0.3)
    vd = s.place('devices/vsource.sym', -900, -450, name='VDD', value='1.8')
    s.connect(vd, p='VDD', m='GND')
    ve = s.place('devices/vsource.sym', -700, -450, name='Ven', value="'ven'")
    s.connect(ve, p='en', m='GND')
    # det: Thevenin of log_det's output (rdet from VDD in the real block)
    v = s.place('devices/vsource.sym', -900, -100, name='Vdet', value='"dc \'vdet\' ac 0"')
    s.connect(v, p='vd', m='GND')
    r = s.place('devices/res.sym', -700, -150, name='Rdet', value='8k', m='1')
    s.connect(r, P='vd', M='det')
    c = s.place('devices/capa.sym', -600, -50, name='Cdet', value='5p', m='1')
    s.connect(c, p='det', m='GND')
    x = s.place('dbg_tg.sym', -300, -150, name='x1')
    s.connect(x, a='det', b='mod', en='en', VDD='VDD', VSS='GND')
    pad = s.place('pad_model.sym', 100, -150, rot=0, flip=1, name='xpad')
    s.connect(pad, pin='pin', mod='mod', VGND='GND')
    r = s.place('devices/res.sym', 400, -150, name='Rext', value="'rext'", m='1')
    s.connect(r, P='ext', M='pin')
    c = s.place('devices/capa.sym', 300, -50, name='Cprobe', value='15p', m='1')
    s.connect(c, p='pin', m='GND')
    v = s.place('devices/vsource.sym', 500, -50, name='Vext', value='"dc \'vpin\' ac 1"')
    s.connect(v, p='ext', m='GND')
    s.code(-1000, 100, 'SIMULATION', TB_CODE)
    s.write(os.path.join(XDIR, 'tb_dbg.sch'))


if __name__ == '__main__':
    dbg_tg()
    tb_dbg()
    print('wrote dbg_tg (.sch/.sym), tb_dbg.sch')
