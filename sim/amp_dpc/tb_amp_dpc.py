"""Block testbench for amp_dpc (schematic vs extracted layout).

As in lna_chain: nb from the reference diode (iref 60 uA into W 6 nf 2 / L 0.5, so each
side's tail is mt/2 x 60 uA = 180 uA); inputs at the previous stage's output level
(1.8 V - 4k x 180 uA = 1.08 V), driven differentially (1 V AC); outputs loaded by a
schematic copy of the next stage. Measures, on the differential output:
  - gain at 434 MHz, peak gain and where, the low / high -3 dB corners (cap degeneration
    gives the low corner, the loads' and parasitics' C the high one);
  - op: output common mode, supply current;
  - the AC imbalance at 434 MHz, |v(outp) + v(outn)| / |v(outp) - v(outn)|, which shows
    asymmetric parasitics (inn / outn cross the cell).
--pex swaps in layout/pex/amp_dpc.spice (layout/pex.sh amp_dpc).
--pex-file=<path> swaps in another extraction instead (e.g. layout/pex/amp_dpc_t.spice, the tall
cell; its .subckt name is read from the file). --temp=<C> sets the temperature (default 27).
--fingers writes the schematic's pair and tails as separate nf=1 fingers (as drawn and as
magic extracts them), the like-for-like reference for the extracted layout.

    python sim/amp_dpc/tb_amp_dpc.py [--pex | --fingers] [corner]
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
OSIC = os.path.join(ROOT, 'tools', 'osic')
PRM = 'w=20 l=0.15 rl=4k wt=6 mt=6 mm=0 cs=0.6p'
F = 433.92e6
PEXFILE = None   # --pex-file
TEMP = None      # --temp


def subckt(name, fingers=False):
    out = os.path.join(B, 'tb_amp_dpc')
    os.makedirs(out, exist_ok=True)
    subprocess.run([OSIC, 'bash', '-c', 'xschem -n -s -q --tcl "set top_subckt 1" -o build/tb_amp_dpc xschem/amp_dpc.sch'],
                   cwd=ROOT, capture_output=True)
    s = open(os.path.join(out, 'amp_dpc.spice')).read()
    s = re.search(r'^\**\.subckt amp_dpc .*?^\**\.ends', s, re.S | re.M).group(0)
    s = re.sub(r'^\**\.(subckt|ends)', r'.\1', s, flags=re.M)
    # the top-level netlist drops the parameter defaults; rename (the load copy stays schematic)
    s = re.sub(r'^\.subckt amp_dpc ([^\n]*)', rf'.subckt {name} \1 {PRM}', s, count=1, flags=re.M)
    if fingers:                       # pair 4 x W/4 per side, each tail 6 x W 3 (as drawn)
        s = re.sub(r'\n\+', ' ', s)     # join continuation lines first (they carry m=...)
        lines = []
        for ln in s.splitlines():
            m = re.match(r'^(XM\w+) (\S+ \S+ \S+ \S+) (\S+) (.*)$', ln)
            if m and 'nfet' in ln:
                nm, pins, model, rest = m.groups()
                keep = ' '.join(t for t in re.findall(r"\w+=(?:'[^']*'|\S+)", rest)
                                if t.split('=')[0].lower() not in ('l', 'w', 'nf', 'm', 'mult'))
                if 'tail' in nm:
                    lines += [f'{nm}_{k} {pins} {model} L=0.5 W=3 nf=1 {keep}' for k in range(6)]
                else:
                    sg = '+' if nm == 'XMp' else '-'
                    lines += [f"{nm}_{k} {pins} {model} L=0.15 W='w*(1{sg}mm/2)/4' nf=1 {keep}" for k in range(4)]
                continue
            lines.append(ln)
        s = '\n'.join(lines)
    return s


def deck(corner, mode):
    pex = mode == 'pex'
    pf = PEXFILE or os.path.join(ROOT, 'layout', 'pex', 'amp_dpc.spice')
    pdut = re.search(r'^\.subckt (\S+)', open(pf).read(), re.M).group(1) if pex else ''
    dut = pdut if pex else 'amp_dpc_x'
    return f"""* tb_amp_dpc ({mode}), {corner}
.lib {os.environ.get('PDK_ROOT', '/foss/pdks')}/sky130A/libs.tech/combined/sky130.lib.spice {corner}
{subckt('amp_dpc_sch')}
{'' if pex else subckt('amp_dpc_x', mode == 'fingers')}
{'.include ' + pf if pex else ''}
{'.temp ' + str(TEMP) if TEMP is not None else ''}
VD VDD 0 1.8
Iref VDD nb 60u
XMref nb nb 0 0 sky130_fd_pr__nfet_01v8 L=0.5 W=6 nf=2
Vp inp 0 dc 1.08 ac 0.5
Vn inn 0 dc 1.08 ac 0.5 180
x1 inp inn nb outp outn VDD 0 {dut}
xload outp outn nb lp ln VDD 0 amp_dpc_sch
.options method=GEAR
.control
save v(outp) v(outn) i(VD)
op
let ocm = (v(outp) + v(outn)) / 2
let idd = -i(VD)
print ocm idd
ac dec 50 1e6 5e9
let gd = db(v(outp) - v(outn))
let imb = db(abs(v(outp) + v(outn)) / abs(v(outp) - v(outn)))
meas ac g434 find gd at={F:.6e}
meas ac imb434 find imb at={F:.6e}
meas ac gmax max gd
let gm3 = gmax - 3
meas ac flo when gd=gm3 rise=1
meas ac fhi when gd=gm3 fall=last
echo RESULTS
.endc
.end
"""


def run(corner, mode):
    name = f'tb_amp_dpc_{corner}' + ('' if mode == 'sch' else '_' + mode)
    if PEXFILE:
        name += '_' + os.path.basename(PEXFILE).replace('.spice', '')
    if TEMP is not None:
        name += f'_{TEMP:g}C'
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck(corner, mode))
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    log = open(os.path.join(B, name + '.log')).read()
    r = {k: float(x) for k, x in re.findall(r'^(\w+)\s+=\s+([-0-9.eE+]+)', log, re.M)}
    m = re.search(r'^gmax\s+=\s+\S+\s+at=\s+([-0-9.eE+]+)', log, re.M)
    if m:
        r['fpk'] = float(m.group(1))
    if 'g434' not in r or 'fhi' not in r:
        sys.exit(f'{name}: no results; see build/{name}.log')
    return r


if __name__ == '__main__':
    args = sys.argv[1:]
    for a in args:
        if a.startswith('--pex-file='):
            PEXFILE = os.path.abspath(a.split('=', 1)[1])
            args.append('--pex')
        elif a.startswith('--temp='):
            TEMP = float(a.split('=', 1)[1])
    mode = 'pex' if '--pex' in args else 'fingers' if '--fingers' in args else 'sch'
    corner = next((a for a in args if not a.startswith('-')), 'tt')
    r = run(corner, mode)
    if PEXFILE:
        mode += ' ' + os.path.basename(PEXFILE)
    if TEMP is not None:
        corner += f' {TEMP:g} C'
    print(f'amp_dpc {corner} {mode}: gain at 434 MHz {r["g434"]:.2f} dB '
          f'(peak {r["gmax"]:.2f} dB at {r["fpk"] / 1e6:.0f} MHz), -3 dB {r["flo"] / 1e6:.1f} MHz .. '
          f'{r["fhi"] / 1e6:.0f} MHz; imbalance at 434 MHz {r["imb434"]:.1f} dB; '
          f'out CM {r["ocm"]:.3f} V, I(VDD) {r["idd"] * 1e3:.3f} mA')
