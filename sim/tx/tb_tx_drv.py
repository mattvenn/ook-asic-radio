"""Block testbench for tx_drv (schematic vs extracted layout).

Two tx_drv arms driven antiphase by ideal 434 MHz squares (3.3 V, 150 ps edges,
en high) into the real load: pad_model per arm + the dipole (73 ohm + 100 pF).
Measures, per run: power into the dipole, out rise/fall (20-80 %), delay
in -> out, and VAPWR current (avg/rms).
The schematic run also probes the currents the layout wiring must carry
(stage 4/5 drain and source connections, rails, out) for EM sizing.

    python sim/tx/tb_tx_drv.py [--pex] [corner]       (default tt)
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from pexswap import swap   # noqa: E402

B = os.path.join(ROOT, 'build')
OSIC = os.path.join(ROOT, 'tools', 'osic')
F = 433.92e6
T = 1 / F
TSET, NPER = 10e-9, 8          # settle, then measure over NPER periods


def schematic_subckts():
    """tx_drv (from xschem, LVS style) and pad_model (from the tb_tx netlist)."""
    out = os.path.join(B, 'tb_tx_drv')
    os.makedirs(out, exist_ok=True)
    subprocess.run([OSIC, 'bash', '-c', 'xschem -n -s -q --tcl "set top_subckt 1" -o build/tb_tx_drv xschem/tx_drv.sch'],
                   cwd=ROOT, capture_output=True)
    drv = open(os.path.join(out, 'tx_drv.spice')).read()
    # xschem comments out the top level's '.subckt' / '.ends' ('**') outside LVS mode
    drv = re.search(r'^\**\.subckt tx_drv .*?^\**\.ends', drv, re.S | re.M).group(0)
    drv = re.sub(r'^\**\.(subckt|ends)', r'.\1', drv, flags=re.M) + '\n'
    if not os.path.exists(os.path.join(B, 'tb_tx.spice')):
        subprocess.run([OSIC, 'bash', '-c', 'xschem -n -s -q -o build xschem/tb_tx.sch'], cwd=ROOT, capture_output=True)
    tb = open(os.path.join(B, 'tb_tx.spice')).read()
    m = re.search(r'^\.subckt pad_model .*?^\.ends\s*$', tb, re.S | re.M)
    return drv, m.group(0) + '\n'


def probe(drv):
    """Insert 0 V ammeters into the schematic tx_drv: stage 5/4 drains (out, y4)
    and their P/N source connections. Logical lines (continuations joined)."""
    lines = []
    for ln in drv.splitlines():
        if ln.startswith('+') and lines:
            lines[-1] += ' ' + ln[1:]
        else:
            lines.append(ln)
    out = []
    for ln in lines:
        t = ln.split()
        if t and t[0] in ('XM5p', 'XM5n', 'XM4p', 'XM4n'):
            st, k = t[0][2], t[0][3]
            d, s = t[1], t[3]
            t[1] = f'd{st}{k}'
            t[3] = f's{st}{k}'
            ln = ' '.join(t)
            out.append(ln)
            out.append(f'Vd{st}{k} d{st}{k} {d} 0')
            out.append(f'Vs{st}{k} {s} s{st}{k} 0')
            continue
        out.append(ln)
    return '\n'.join(out) + '\n'


def deck(corner, pex):
    drv, pad = schematic_subckts()
    if not pex:
        drv = probe(drv)
    hp = T / 2
    probes = '' if pex else ' '.join(f'i(v.xdp.v{a}{st}{k})' for st in '45' for k in 'pn' for a in 'ds')
    src = f"""* tb_tx_drv ({'extracted' if pex else 'schematic'}), {corner}
.lib {os.environ.get('PDK_ROOT', '/foss/pdks')}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
{drv}
{pad}
VAp VAPWR_p 0 3.3
VAn VAPWR_n 0 3.3
VSp VSS_p 0 0
VSn VSS_n 0 0
Ven en 0 3.3
Vin_p in_p 0 pulse(0 3.3 0 150p 150p {hp - 150e-12:.4e} {T:.4e})
Vin_n in_n 0 pulse(3.3 0 0 150p 150p {hp - 150e-12:.4e} {T:.4e})
xdp in_p en out_p VAPWR_p VSS_p tx_drv
xdn in_n en out_n VAPWR_n VSS_n tx_drv
Vop out_p pin_p 0
xpad_p 0 ant_p pin_p pad_model
xpad_n 0 ant_n out_n pad_model
Rdip ant_p dmid 73
Cdip dmid ant_n 100p
.options method=GEAR
.control
* keep only what's measured: the extracted netlist has thousands of nodes
save v(out_p) v(out_n) v(in_p) v(ant_p) v(ant_n) v(dmid) i(VAp) i(VSp) i(Vop) {probes}
tran 2p {TSET + NPER * T:.4e} 0
let t0 = {TSET:.4e}
let t1 = {TSET + NPER * T:.4e}
let vd = v(ant_p) - v(ant_n)
let pdip = (v(ant_p) - v(dmid)) * (v(ant_p) - v(dmid)) / 73
meas tran p_dip avg pdip from=$&t0 to=$&t1
meas tran ia_avg avg i(VAp) from=$&t0 to=$&t1
meas tran ia_rms rms i(VAp) from=$&t0 to=$&t1
meas tran is_rms rms i(VSp) from=$&t0 to=$&t1
meas tran io_rms rms i(Vop) from=$&t0 to=$&t1
let iop = abs(i(Vop))
let iap = abs(i(VAp))
meas tran io_pk max iop from=$&t0 to=$&t1
meas tran ia_pk max iap from=$&t0 to=$&t1
meas tran vhi max v(out_p) from=$&t0 to=$&t1
meas tran vlo min v(out_p) from=$&t0 to=$&t1
let v20 = vlo + 0.2 * (vhi - vlo)
let v80 = vlo + 0.8 * (vhi - vlo)
meas tran tr TRIG v(out_p) VAL=$&v20 RISE=6 TARG v(out_p) VAL=$&v80 RISE=6
meas tran tf TRIG v(out_p) VAL=$&v80 FALL=6 TARG v(out_p) VAL=$&v20 FALL=6
meas tran tdr TRIG v(in_p) VAL=1.65 RISE=6 TARG v(out_p) VAL=1.65 RISE=6
meas tran tdf TRIG v(in_p) VAL=1.65 FALL=6 TARG v(out_p) VAL=1.65 FALL=6
"""
    if not pex:
        for st in '45':
            for k in 'pn':
                # subckt sources are named v.<inst>.<name> in ngspice
                src += (f'let jd{st}{k} = i(v.xdp.vd{st}{k})\nlet js{st}{k} = i(v.xdp.vs{st}{k})\n'
                        f'let ad{st}{k} = abs(jd{st}{k})\nlet as{st}{k} = abs(js{st}{k})\n'
                        f'meas tran id{st}{k} rms jd{st}{k} from=$&t0 to=$&t1\n'
                        f'meas tran is{st}{k} rms js{st}{k} from=$&t0 to=$&t1\n'
                        f'meas tran ida{st}{k} avg ad{st}{k} from=$&t0 to=$&t1\n'
                        f'meas tran isa{st}{k} avg as{st}{k} from=$&t0 to=$&t1\n'
                        f'meas tran ipk{st}{k} max as{st}{k} from=$&t0 to=$&t1\n')
    src += """echo RESULTS
print p_dip ia_avg ia_rms is_rms io_rms io_pk ia_pk tr tf tdr tdf
"""
    if not pex:
        src += 'print id5p is5p id5n is5n id4p is4p id4n is4n\n'
    src += f"write tb_tx_drv_{corner}{'_pex' if pex else ''}.raw v(out_p) v(out_n) v(in_p) v(ant_p) v(ant_n) i(VAp)\n.endc\n.end\n"
    if pex:
        src = swap(src, ['tx_drv'])
    return src


def run(corner, pex):
    name = f'tb_tx_drv_{corner}' + ('_pex' if pex else '')
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(corner, pex))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    vals = dict(re.findall(r'^(\w+)\s+=\s+([-0-9.eE+]+)', log, re.M))
    if 'p_dip' not in vals:
        sys.exit(f'{name}: no results; see build/{name}.log')
    return {k: float(v) for k, v in vals.items()}


def report(r, label):
    import math
    print(f'{label}: P_dip {10 * math.log10(r["p_dip"] / 1e-3):+.2f} dBm, '
          f'out tr/tf {r["tr"] * 1e12:.0f}/{r["tf"] * 1e12:.0f} ps, delay r/f {r["tdr"] * 1e12:.0f}/{r["tdf"] * 1e12:.0f} ps, '
          f'VAPWR/arm avg {-r["ia_avg"] * 1e3:.2f} mA rms {r["ia_rms"] * 1e3:.2f} pk {r["ia_pk"] * 1e3:.1f}; '
          f'VSS rms {r["is_rms"] * 1e3:.2f}; out rms {r["io_rms"] * 1e3:.2f} pk {r["io_pk"] * 1e3:.1f} mA')
    if 'id5p' in r:
        for st in '54':
            print(f'  stage {st}: ' + ', '.join(
                f'{k.upper()} drain rms {r[f"id{st}{k}"] * 1e3:.2f} (|avg| {r[f"ida{st}{k}"] * 1e3:.2f}) / '
                f'source rms {r[f"is{st}{k}"] * 1e3:.2f} (|avg| {r[f"isa{st}{k}"] * 1e3:.2f}, pk {r[f"ipk{st}{k}"] * 1e3:.1f}) mA'
                for k in 'pn'))


if __name__ == '__main__':
    args = sys.argv[1:]
    pex = '--pex' in args
    corners = [a for a in args if not a.startswith('--')] or ['tt']
    for c in corners:
        report(run(c, pex), c + (' pex' if pex else ' sch'))
