"""
TX-only runs of tb_radio_analog (the keyed 5..60 ns TX transient of sim/top/tb_tile.py) for
splitting the extracted tile's TX loss by cause.

Each variant is <mode>[:key=value,...]:
    sch:cw=2.2f          schematic, ring wiring cap per stage set to 2.2 fF (default 3.2 fF), so the
                         schematic can be compared at the extracted ring's frequency
    c:drop=<regex>       extracted netlist with every C that touches a net matching <regex> removed
    c:keep=<regex>       ... with only the C on nets matching <regex> kept (C touching only the
                         supplies / VGND dropped too unless the other end matches)
    sch:kn=15,kp=8       schematic with tx_ls (xls) resized (default kn=10 kp=4)
    <any>:corner=ss,temp=10   process corner (.lib ... tt rewritten) and temperature
    sch:addc=a:9f;b:13f  schematic with extra C to VSS on tx_top's nets (what-if for the wiring)
    c:dev=<regex>,wx=2   extracted netlist with the W of each device whose line matches <regex> scaled
                         (what-if for a sizing change the layout doesn't have yet)
    rc                   the full RC extraction

    python3 sim/top/tb_tile_tx.py sch:cw=2.2f c 'c:drop=ua\\[[34]\\]'
    python3 sim/top/tb_tile_tx.py --no-run <variant> ...      (analyse existing raws)
Prints f, P into 73 ohm, on / off time and supply currents per variant. One ngspice at a time.
"""
import os
import re
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tb_tile  # noqa: E402
from tb_tile import B, OSIC, ROOT, read_raw, ring_metrics, fmt_ring  # noqa: E402

TX_CONTROL = """.control
alterparam vemf = 0
alterparam ven_rx = 0
alterparam ven_tx = 1.8
reset
{temp}tran 2p 80n 0
write {raw}
.endc
"""


def parse(variant):
    mode, _, rest = variant.partition(':')
    opts = dict(kv.split('=', 1) for kv in rest.split(',') if kv)
    return mode, opts


def tag(variant):
    return re.sub(r'[^A-Za-z0-9]+', '_', variant).strip('_')


def filter_caps(path, out, drop=None, keep=None):
    """Copy the (tied) netlist without the C elements selected by drop / keep."""
    rd, rk = (re.compile(drop) if drop else None), (re.compile(keep) if keep else None)
    lines, n = [], 0
    for ln in open(path).read().splitlines(keepends=True):
        t = ln.split()
        if t and t[0][0] in 'Cc' and len(t) >= 4:
            a, b = t[1], t[2]
            if rd and (rd.fullmatch(a) or rd.fullmatch(b)):
                n += 1
                continue
            if rk and not (rk.fullmatch(a) or rk.fullmatch(b)):
                n += 1
                continue
        lines.append(ln)
    open(out, 'w').write(''.join(lines))
    return n


def scale_w(path, dev, k):
    """Scale w (and ad / as / pd / ps roughly) of the device lines matching dev, in place."""
    rx, n, out = re.compile(dev), 0, []
    for ln in open(path).read().splitlines(keepends=True):
        if ln.startswith('X') and rx.search(ln):
            ln = re.sub(r'\b(w|ad|as)=([0-9.eE+-]+)', lambda m: f'{m.group(1)}={float(m.group(2)) * k:g}', ln)
            n += 1
        out.append(ln)
    open(path, 'w').write(''.join(out))
    return n


def deck(src, variant):
    mode, opts = parse(variant)
    raw = f'tb_tile_tx_{tag(variant)}.raw'
    d = tb_tile.deck_for(src, mode)
    d = re.sub(r'^\.control\b.*?^\.endc\b[^\n]*\n', lambda m: TX_CONTROL.format(
        raw=raw, temp=f'option temp = {opts["temp"]}\n' if 'temp' in opts else ''), d,
               count=1, flags=re.S | re.M)
    if 'cw' in opts:
        d, n = re.subn(r'^(xring .* tx_ring) cw=\S+', rf'\1 cw={opts["cw"]}', d, flags=re.M)
        assert n == 1, n
    for k in ('kn', 'kp'):
        if k in opts:
            d, n = re.subn(rf'^(xls .* tx_ls .*\b{k})=\S+', rf'\g<1>={opts[k]}', d, flags=re.M)
            assert n == 1, (k, n)
    if 'corner' in opts:
        d, n = re.subn(r'^(\.lib \S+sky130\.lib\.spice) tt$', rf'\1 {opts["corner"]}', d, flags=re.M)
        assert n == 1, n
    if 'addc' in opts:
        cs = ''.join(f'Cadd_{k} {k} VSS {v}\n' for k, v in (kv.split(':') for kv in opts['addc'].split(';')))
        d, n = re.subn(r'^(\.subckt tx_top .*\n)', lambda m: m.group(1) + cs, d, flags=re.M)
        assert n == 1, n
    if {'drop', 'keep', 'dev'} & set(opts):
        tied = os.path.join(B, f'radio_analog_{mode}_tied.spice')
        mine = f'radio_analog_{tag(variant)}.spice'
        n = filter_caps(tied, os.path.join(B, mine), opts.get('drop'), opts.get('keep'))
        if 'dev' in opts:
            n_dev = scale_w(os.path.join(B, mine), opts['dev'], float(opts['wx']))
            print(f'{variant}: {n_dev} devices scaled', flush=True)
        print(f'{variant}: {n} C removed', flush=True)
        d = d.replace(f'.include radio_analog_{mode}_tied.spice', f'.include {mine}')
    return d, raw


def run(src, variant):
    d, raw = deck(src, variant)
    name = f'tb_tile_tx_{tag(variant)}'
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(d)
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)


def analyse(variant):
    path = os.path.join(B, f'tb_tile_tx_{tag(variant)}.raw')
    if not os.path.exists(path):
        print(f'{variant}: no raw (see build/tb_tile_tx_{tag(variant)}.log)')
        return
    v = dict(read_raw(path)[0]['vars'])
    v['v(ant_p)'], v['v(ant_n)'], v['i(vd)'] = v['v(ant_tx_p)'], v['v(ant_tx_n)'], v['i(vdpwr)']
    try:
        m = ring_metrics(v, 5e-9, 60e-9, drv=('tx_p', 'tx_n'))
    except (IndexError, ValueError):
        t = np.real(v['time'])
        w = (t > 25e-9) & (t < 60e-9)
        rng = ', '.join(f'{k} {np.real(v[f"v({k})"])[w].min():.2f}..{np.real(v[f"v({k})"])[w].max():.2f} V'
                        for k in ('tx_p', 'tx_n'))
        print(f'{variant}: NOT SWITCHING (latched?): {rng}', flush=True)
        return
    # arm duty (fraction of the steady window above half VAPWR)
    t = np.real(v['time'])
    g = np.arange(25e-9, 60e-9, 1e-12)
    duty = [np.mean(np.interp(g, t, np.real(v[f'v({k})'])) > 1.65) for k in ('tx_p', 'tx_n')]
    print(f'{variant}: ' + fmt_ring(m) + f', duty p / n {duty[0]:.1%} / {duty[1]:.1%}', flush=True)


if __name__ == '__main__':
    args = sys.argv[1:]
    variants = [a for a in args if not a.startswith('--')]
    src = None if '--no-run' in args else tb_tile.netlist()
    for va in variants:
        if src is not None:
            run(src, va)
        analyse(va)
