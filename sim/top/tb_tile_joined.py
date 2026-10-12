"""
Joined RX run on the extracted tile: sim/rx/joined.sh's stimulus (keyed 434 MHz antenna EMF +
trnoise at the receiver's NF, real chip timing) on xschem/tb_radio_analog.sch with radio_analog
from the extracted tile (layout/pex_tile.sh c), i.e. pad -> lna_chain -> log_det -> lpf_rc ->
avg_sc -> comp_ct with the r2r trim, all from the layout.

The trim servo is the RTL's (sim/mixed/); here the DAC code is held fixed at the comparator's
switching point, found first with DC operating points (avg = lpf: both sc clocks held high):

    python3 sim/top/tb_tile_joined.py scan                 trim code scan (~min)
    python3 sim/top/tb_tile_joined.py run -90 [400u] [code]   the joined transient (many hours)
    python3 sim/top/tb_tile_joined.py --no-run run -90        analyse build/tile_joined_-90.raw
    python3 sim/top/tb_tile_joined.py pair -92 [30u] [code] [seed]   on / off pair (~15 h each, in parallel)
    python3 sim/top/tb_tile_joined.py --no-run pair -92       analyse build/tile_pair_-92_{on,off}.raw

pair: the stand-in for the full run (~8 days on sim-0), docs/verify_2026-10-11.md. Two short runs,
keyed on at 1 us and on to the end, one with the signal and one without (vemf = 0), with the same
RF noise. ngspice 47 doesn't repeat trnoise between runs (.options seed, set rndseed and setseed all
fail), so the pair replaces it with one noise waveform from numpy (seeded; same sigma and 50 ps step)
that both runs read through an XSPICE filesource. det / LPF off - on per window then shows whether the signal reaches det and the LPF
at the model's size (~1.1 mV at -92 dBm); it checks level, not detection.

Keying as joined.sh: off 0-60 us, chips on / off / on (104 us each), off to the end. Clock and key
edges sit 25 ps off trnoise's 50 ps grid ('timestep too small' otherwise).
"""
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tb_tile  # noqa: E402
from tb_tile import B, OSIC, ROOT, read_raw  # noqa: E402

NZ = 2.76e-9 * math.sqrt(1 / (2 * 50e-12))          # per-arm trnoise sigma, as joined.sh (NF ~11 dB)
KEY = ('pwl(0 0 60.000025u 0 60.010025u 1 164.000025u 1 164.010025u 0 '
       '268.000025u 0 268.010025u 1 372.000025u 1 372.010025u 0)')
SAVE = '.save v(key) v(xana.x1.det) v(xana.x1.lpf) v(xana.x1.avg) v(xana.x1.trim) v(comp)'


def bits_ctl(code):
    return ''.join(f'alter vt{i} = {1.8 if (code >> i) & 1 else 0}\n' for i in range(8))


def base(src):
    d = tb_tile.deck_for(src, 'c')
    d = d.replace('xana.x1.vcm', 'xana.x1.avg')               # (the deck saves vcm; we want avg)
    # TX off as plain DC (its PWL edges at 5 / 60 ns sit on the trnoise grid)
    d = re.sub(r'^(Vtxn?) (\S+) GND pwl\(.*\)$', r'\1 \2 GND 0', d, flags=re.M)
    # sc clocks 25 ps off the trnoise grid
    d = d.replace('pulse(0 1.8 0 10n 10n 6.09u 13u)', 'pulse(0 1.8 25p 10n 10n 6.09u 13u)')
    d = d.replace('pulse(0 1.8 6.5u 10n 10n 6.09u 13u)', 'pulse(0 1.8 6.500025u 10n 10n 6.09u 13u)')
    d = re.sub(r'^\.save .*$', SAVE, d, count=1, flags=re.M)
    return d


def scan_deck(src, codes):
    d = base(src)
    # both sc switches on: avg = lpf, so comp sees only its own offset and the trim
    d = d.replace('pulse(0 1.8 25p 10n 10n 6.09u 13u)', '1.8').replace('pulse(0 1.8 6.500025u 10n 10n 6.09u 13u)', '1.8')
    ctl = '.control\nalterparam ven_rx = 1.8\nalterparam vemf = 0\nreset\n'
    for c in codes:
        ctl += bits_ctl(c) + f'op\necho SCAN {c} $&v(comp) $&v(xana.x1.trim) $&v(xana.x1.lpf) $&v(xana.x1.avg)\ndestroy all\n'
    ctl += '.endc\n'
    return re.sub(r'^\.control\b.*?^\.endc\b[^\n]*\n', lambda m: ctl, d, count=1, flags=re.S | re.M)


def run_deck(src, level, tstop, code):
    d = base(src)
    ve = math.sqrt(8 * 73 * 1e-3 * 10 ** (level / 10))      # EMF for <level> dBm into 73 ohm
    d = re.sub(r'^Vant_p emf_p acm .*$', 'Bant_p emf_p acm V = v(key) * vemf/2 * sin(2*pi*f0*time)', d, flags=re.M)
    d = re.sub(r'^Vant_n emf_n acm .*$', 'Bant_n emf_n acm V = -v(key) * vemf/2 * sin(2*pi*f0*time)', d, flags=re.M)
    for s in 'pn':
        d = re.sub(rf'^Rant_{s} ant_{s} emf_{s} 36.5$',
                   f'Rant_{s} an_{s} emf_{s} 36.5\nVnz_{s} ant_{s} an_{s} dc 0 trnoise({NZ:.6g} 50p 0 0)', d, flags=re.M)
    d = d.replace('.param ven_rx=1.8', f'Vkey key 0 {KEY}\n.param ven_rx=1.8')
    d = d.replace('.options method=GEAR', '.options method=GEAR interp')
    ctl = (f'.control\nalterparam vemf = {ve:.6g}\nalterparam ven_rx = 1.8\nreset\n{bits_ctl(code)}'
           f'tran 10n {tstop} 0 50p\nwrite tile_joined_{level}.raw\n.endc\n')
    return re.sub(r'^\.control\b.*?^\.endc\b[^\n]*\n', lambda m: ctl, d, count=1, flags=re.S | re.M)


PAIR_KEY = 'pwl(0 0 1.000025u 0 1.010025u 1)'
PAIR_WIN = [(1e-6, 5e-6), (5e-6, 10e-6), (10e-6, 20e-6), (20e-6, 30e-6)]


def seconds(x):
    m = re.fullmatch(r'([0-9.]+)([munp]?)', x)
    return float(m.group(1)) * {'': 1, 'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12}[m.group(2)]


def noise_file(tstop, seed):
    """build/tile_pair_noise_<seed>.txt: time, p arm, n arm; N(0, NZ) every 50 ps, as trnoise(NZ 50p)."""
    import numpy as np
    path = os.path.join(B, f'tile_pair_noise_{seed}.txt')
    t = np.arange(0, seconds(tstop) + 1e-9, 50e-12)
    x = np.random.default_rng(seed).normal(0, NZ, (len(t), 2))
    np.savetxt(path, np.column_stack([t, x]), fmt='%.6g')
    return path


def pair_deck(src, level, tstop, code, seed, on):
    """run_deck keyed on at 1 us for good; on=False: the same deck with no signal."""
    d = run_deck(src, level, tstop, code).replace(f'Vkey key 0 {KEY}', f'Vkey key 0 {PAIR_KEY}')
    # the RF noise from a file both runs share, in place of trnoise
    nz = noise_file(tstop, seed)
    for s in 'pn':
        d, n = re.subn(rf'^Vnz_{s} ant_{s} an_{s} dc 0 trnoise\(.*\)$', f'Enz_{s} ant_{s} an_{s} nz{s} 0 1', d, flags=re.M)
        assert n == 1, s
    d = d.replace(f'Vkey key 0 {PAIR_KEY}', f'Vkey key 0 {PAIR_KEY}\nanz %v([nzp nzn]) nzsrc\n'
                  f'.model nzsrc filesource (file="{os.path.basename(nz)}" amploffset=[0 0] amplscale=[1 1] '
                  'timeoffset=0 timescale=1 timerelative=false amplstep=false)')
    name = f'tile_pair_{level}_{"on" if on else "off"}'
    if not on:
        d = re.sub(r'^alterparam vemf = \S+$', 'alterparam vemf = 0', d, count=1, flags=re.M)
    return name, d.replace(f'write tile_joined_{level}.raw', f'write {name}.raw')


def analyse_pair(level):
    import numpy as np
    r = {}
    for k in ('on', 'off'):
        v = dict(read_raw(os.path.join(B, f'tile_pair_{level}_{k}.raw'))[0]['vars'])
        r[k] = {n: np.real(v[n]) for n in ('time', 'v(xana.x1.det)', 'v(xana.x1.lpf)')}
    t = r['on']['time']
    tg = r['off']['time']
    if len(tg) != len(t) or np.max(np.abs(tg - t)) > 1e-12:     # interp grids should match; else resample
        for n in ('v(xana.x1.det)', 'v(xana.x1.lpf)'):
            r['off'][n] = np.interp(t, tg, r['off'][n])
    diff = {n: (r['off'][n] - r['on'][n]) * 1e3 for n in ('v(xana.x1.det)', 'v(xana.x1.lpf)')}
    print(f'{level} dBm pair, {t[-1] * 1e6:.1f} us: off - on (mV)')
    print('  window       det     LPF')
    for a, b in PAIR_WIN + [(2e-6, 30e-6)]:
        m = (t >= a) & (t < b)
        if m.any():
            print(f'  {a * 1e6:4.0f}-{b * 1e6:<3.0f} us {np.mean(diff["v(xana.x1.det)"][m]):+7.2f} '
                  f'{np.mean(diff["v(xana.x1.lpf)"][m]):+7.2f}')
    print(f'  model at {level} dBm: ~{1.80 * 10 ** ((level + 90) / 10):.2f} mV (1.80 mV at -90, square law)')


def ngspice(name, deck):
    with open(os.path.join(B, name + '.spice'), 'w') as fh:
        fh.write(deck)
    subprocess.run([OSIC, 'bash', '-c', f'cd build && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    return open(os.path.join(B, name + '.log')).read()


def scan(src):
    rows = []
    for codes in (list(range(0, 256, 16)) + [255], None):
        if codes is None:                                      # refine around the flip
            lo = max(c for c, v, *_ in rows if (v > 0.9) == (rows[0][1] > 0.9))
            codes = list(range(lo, min(lo + 17, 256)))
        log = ngspice('tile_joined_scan', scan_deck(src, codes))
        new = [(int(a), *map(float, r)) for a, *r in re.findall(r'^SCAN (\d+) (\S+) (\S+) (\S+) (\S+)', log, re.M)]
        assert new, log[-2000:]
        rows = sorted(set(rows) | set(new))
    for c, comp, trim, lpf, avg in rows:
        print(f'code {c:3d}: comp {comp:6.3f} V  trim {trim:.4f} V  lpf {lpf:.4f}  avg {avg:.4f}')
    flips = [b[0] for a, b in zip(rows, rows[1:]) if (a[1] > 0.9) != (b[1] > 0.9)]
    print('comp flips between codes', [(f - 1, f) for f in flips] if flips else 'never')
    return flips


def analyse(level):
    import numpy as np
    v = dict(read_raw(os.path.join(B, f'tile_joined_{level}.raw'))[0]['vars'])
    t = np.real(v['time'])
    g = lambda k: np.real(v[k])
    key, comp, lpf, avg = g('v(key)'), g('v(comp)'), g('v(xana.x1.lpf)'), g('v(xana.x1.avg)')
    on = [(60e-6, 164e-6), (268e-6, 372e-6)]
    off = [(164e-6, 268e-6), (372e-6, t[-1])]
    frac = lambda w: np.mean([np.mean(comp[(t > a + 20e-6) & (t < b)] > 0.9) for a, b in w])
    print(f'{level} dBm, {t[-1] * 1e6:.0f} us: lpf idle {np.mean(lpf[(t > 30e-6) & (t < 60e-6)]):.4f} V, '
          f'avg {np.mean(avg[t > 30e-6]):.4f} V; comp high {frac(on):.0%} in on-chips, {frac(off):.0%} in off-chips '
          f'(20 us after each edge)')


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if a[0] == 'scan':
        scan(tb_tile.netlist())
    elif a[0] == 'run':
        level = int(a[1])
        if '--no-run' not in sys.argv:
            tstop = a[2] if len(a) > 2 else '400u'
            code = int(a[3]) if len(a) > 3 else 135
            print(f'run {level} dBm, {tstop}, trim code {code}', flush=True)
            ngspice(f'tile_joined_{level}', run_deck(tb_tile.netlist(), level, tstop, code))
        analyse(level)
    elif a[0] == 'pair':
        level = int(a[1])
        if '--no-run' not in sys.argv:
            from concurrent.futures import ThreadPoolExecutor
            tstop = a[2] if len(a) > 2 else '30u'
            code = int(a[3]) if len(a) > 3 else 135
            seed = int(a[4]) if len(a) > 4 else 1
            print(f'pair {level} dBm, {tstop}, trim code {code}, seed {seed}', flush=True)
            src = tb_tile.netlist()
            with ThreadPoolExecutor(2) as ex:
                list(ex.map(lambda on: ngspice(*pair_deck(src, level, tstop, code, seed, on)), (True, False)))
        analyse_pair(level)
