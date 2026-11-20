"""16 chips through the extracted RX to the slicer (TODO.md, 2026-11-19; Matt: -85 dBm, pass <= 3 of 16 wrong).

The RF half (antenna -> pads -> rx_t extracted: chain, detector, tap wiring) remembers only a few hundred ns, so
the RF record is cut into pieces that run in parallel, each with WARM of warm-up taken from the end of the piece
before it. All pieces see one seeded numpy noise waveform (2.76 nV/rtHz per arm, 50 ps, as joined.sh /
tb_tile_joined.py pair), read through an XSPICE filesource. The joined det then drives the mixed-signal bench
(sim/mixed/gen_mixed.py --pex: extracted lpf_rc / avg_sc / comp_ct / r2r, the RTL's trim servo and sc clocks).

RF record, time 0 = start of chip 67 of code 0: chips 67-84 (18 chips, 1872 us). Chips 68-83 (1011010111100010)
are the test; chips 67 and 84 let the first and last slicer windows open and close. The window is mid-burst and
typical (model, tt_pex at -85 dBm: 1.0 chips wrong expected, P(<= 3) 99.9 %). The first try, chips 3-18, sat
right after the burst gap, where the slicer's threshold average and trim servo have only seen noise: the model
gives ~50 % errors on its first five zeros and 80 % on chip 18 (the fourth 1 of a run), so <= 3 wrong passed
only 46 % of the time whatever the circuit did (schematic dry run: chips 4, 5, 6, 18 wrong, 2026-11-20).
The mixed bench first sees LEAD_CHIPS (20) chips of lead-in: the code's chips 47-66, each made of the det of a
simulated chip of the same value, so the threshold average and trim come into the window as they would mid-burst.

Slicer: the RTL's comparator decisions are read back from its trim code (the servo steps +-1 every sample), and
run through model/radio.py's RxDigital (bit-exact with the RTL) to get each phase's chip bits. Pass: <= 3 of the
16 chips wrong on the best phase (the correlator's 30/127 budget scaled to 16).

    python3 sim/rx/chip16.py prep          noise files and one deck per piece (build/chip16/pieces/)
    python3 sim/rx/chip16.py join          det from the pieces -> build/det_-85_chip16.inc, mixed deck
    python3 sim/rx/chip16.py check         slicer bits from the mixed run, pass / fail
    python3 sim/rx/chip16.py status        progress: us/h, elapsed, ETA, chips as they arrive
The run itself: sim/rerun/jobs_chip16.py (sched.py).
"""
import json
import math
import os
import re
import sys
import time

import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'model'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
TAG = os.environ.get('CHIP16_TAG', 'chip16')    # chip16sch: the dry run on the schematic deck (CHIP16_BASE)
OUT = os.path.join(ROOT, 'build', TAG)
PD = os.path.join(OUT, 'pieces')
BASE = os.environ.get('CHIP16_BASE', os.path.join(ROOT, 'build', 'tb_logdet_pex.spice'))    # rx_t swapped into tb_logdet (sim/chain/mk_pex_rx.py)
SCHED = os.path.join(ROOT, 'build', f'rerun_{TAG}')

LEVEL = -85
CODE = 0
FIRST, LAST = 68, 83        # the 16 chips tested (model/chip16_err.py)
C0, C1 = 67, 84             # chips simulated
CHIP = 104e-6                # 1040 clocks at 10 MHz
DT = 50e-12                  # noise sample step
TREC = (C1 - C0 + 1) * CHIP
NP = 28                      # pieces: one per CPU, 1 thread each
WARM = 3e-6
LEAD_CHIPS = 20              # mixed bench lead-in: chips C0-20 .. C0-1 (gen_mixed.det_start averages its first 1.4 ms)
LEAD = LEAD_CHIPS * CHIP
SEED = 1
NZ = 2.76e-9 * math.sqrt(1 / (2 * DT))
EDGE = 10e-9                 # key rise / fall
CKPT = 1e-6                  # progress checkpoint, sim time


def chips():
    from gold import gold
    return [int(x) for x in gold(CODE)]


def bounds():
    """Piece k covers [b[k], b[k+1]) of the record; it simulates from b[k] - WARM (0 for piece 0)."""
    n = int(round(TREC / DT))
    return [int(round(n * k / NP)) * DT for k in range(NP + 1)]


def span(k):
    b = bounds()
    return max(0.0, b[k] - WARM), b[k + 1]


def key_pwl(g0, g1):
    c = chips()
    on = lambda t: c[C0 + min(int(t / CHIP), C1 - C0)]
    pts = [(0.0, on(g0))]
    for j in range(C0 - C0 + 1, C1 - C0 + 1):
        te = j * CHIP
        if g0 < te < g1 and c[C0 + j] != c[C0 + j - 1]:
            t = te - g0 + 25e-12                       # off the 50 ps noise grid
            pts += [(t, c[C0 + j - 1]), (t + EDGE, c[C0 + j])]
    return 'pwl(' + ' '.join(f'{t:.9g} {v}' for t, v in pts) + ')'


def deck(k, base):
    g0, g1 = span(k)
    T = g1 - g0
    ve = math.sqrt(8 * 73 * 1e-3 * 10 ** (LEVEL / 10))
    d = re.sub(r'^\.control\b.*?^\.endc\b[^\n]*\n', '', base, flags=re.S | re.M)
    d = re.sub(r'^\.end\s*$', '', d, flags=re.M)
    for s, sg in (('p', ''), ('n', '-')):
        d, n = re.subn(rf'^Vant_{s} emf_{s} acm .*$',
                       f'Bant_{s} emf_{s} acm V = {sg}v(key) * vemf/2 * sin(2*pi*f0*(time + {g0:.12g}))', d, flags=re.M)
        assert n == 1, s
        d, n = re.subn(rf'^Rant_{s} ant_{s} emf_{s} 36.5$',
                       f'Rant_{s} an_{s} emf_{s} 36.5\nEnz_{s} ant_{s} an_{s} nz{s} 0 1', d, flags=re.M)
        assert n == 1, s
    d += (f'\n* ---- chip16 piece {k}: record {g0 * 1e6:.6f} - {g1 * 1e6:.6f} us (generated by sim/rx/chip16.py)\n'
          f'Vkey key 0 {key_pwl(g0, g1)}\n'
          'anz %v([nzp nzn]) nzsrc\n'
          f'.model nzsrc filesource (file="noise_{k:02d}.txt" amploffset=[0 0] amplscale=[1 1] '
          'timeoffset=0 timescale=1 timerelative=false amplstep=false)\n'
          '.save v(det) v(key)\n.options method=GEAR interp\n'
          '.control\nset num_threads=1\n'
          f'alterparam vemf = {ve:.6g}\nreset\n'
          f'let a = 0\nlet tc = {CKPT:g}\nstop when time > {CKPT:g}\n'
          f'tran 10n {T:.12g} 0 50p\n'
          f'while tc < {T:.12g}\n'
          '  meas tran m avg v(det) from=$&a to=$&tc\n'
          '  echo PROG $&tc $&m\n'
          f'  wrdata part_{k:02d}.txt v(det)\n'
          '  let a = tc\n'
          f'  let tc = tc + {CKPT:g}\n'
          '  delete all\n'
          '  stop when time > $&tc\n'
          '  resume\n'
          'end\n'
          f'meas tran m avg v(det) from=$&a to={T:.12g}\n'
          f'echo PROG {T:.12g} $&m\n'
          f'wrdata part_{k:02d}.txt v(det)\n'
          f'write piece_{k:02d}.raw v(det) v(key)\n'
          'echo DONE\n.endc\n.end\n')
    return d


def prep():
    os.makedirs(PD, exist_ok=True)
    base = open(BASE).read()
    assert TAG != 'chip16' or re.search(r'^x1 .* rx_t$', base, re.M), 'BASE is not the rx_t deck'
    init = re.sub(r'num_threads=\d+', 'num_threads=1', open(os.path.join(ROOT, '.spiceinit')).read())
    open(os.path.join(PD, '.spiceinit'), 'w').write(init)
    n = int(round(TREC / DT)) + 2
    x = np.random.default_rng(SEED).normal(0, NZ, (n, 2))
    for k in range(NP):
        g0, g1 = span(k)
        i0, i1 = int(round(g0 / DT)), int(round(g1 / DT)) + 1
        t = (np.arange(i0, i1 + 1) - i0) * DT
        with open(os.path.join(PD, f'noise_{k:02d}.txt'), 'w') as fh:
            # times to 10 figures: '%.6g' rounds 50 ps steps onto each other from 10 us on (repeated times, half the
            # noise wrong: the dry run's seams were ~12 mV, 2026-11-19; gen_noise.py had the same bug)
            np.savetxt(fh, np.column_stack([t, x[i0:i1 + 1]]), fmt=['%.10e', '%.6g', '%.6g'])
        open(os.path.join(PD, f'piece_{k:02d}.spice'), 'w').write(deck(k, base))
    json.dump(dict(level=LEVEL, code=CODE, chips=chips()[C0:C1 + 1], c0=C0, first=FIRST, last=LAST, chip=CHIP,
                   bounds=bounds(), warm=WARM, seed=SEED, np=NP, base=BASE,
                   base_md5=__import__('hashlib').md5(base.encode()).hexdigest()),
              open(os.path.join(OUT, 'setup.json'), 'w'), indent=1)
    print(f'{NP} pieces of {(span(1)[1] - span(1)[0]) * 1e6:.2f} us (incl. {WARM * 1e6:g} us warm-up), record '
          f'{TREC * 1e6:.0f} us, chips {C0}-{C1} of code {CODE}: {"".join(map(str, chips()[C0:C1 + 1]))}')


def part(k):
    """(global time, det) simulated so far by piece k, warm-up dropped; plus its last checkpoint (local s)."""
    p = os.path.join(PD, f'part_{k:02d}.txt')
    g0, g1 = span(k)
    try:
        a = np.loadtxt(p, ndmin=2)
    except (OSError, ValueError):
        return np.zeros(0), np.zeros(0)
    if a.size == 0:
        return np.zeros(0), np.zeros(0)
    t, v = a[:, 0] + g0, a[:, 1]
    keep = t >= bounds()[k]
    return t[keep], v[keep]


def raw_det(k):
    from rawread import read_raw
    v = dict(read_raw(os.path.join(PD, f'piece_{k:02d}.raw'))[0]['vars'])
    g0, _ = span(k)
    return np.real(v['time']) + g0, np.real(v['v(det)'])


def join():
    ts, vs, seams = [], [], []
    for k in range(NP):
        t, v = raw_det(k)
        if k:                                  # warm-up overlap vs the piece before: the cost of the split
            tp, vp = ts[-1], vs[-1]
            b = bounds()[k]
            m = (t >= b - 1e-6) & (t < b)
            if m.any():
                d = v[m] - np.interp(t[m], tp, vp)
                seams.append((k, float(np.sqrt(np.mean(d ** 2))) * 1e3, float(np.mean(d)) * 1e3))
        keep = (t >= bounds()[k]) & (t < bounds()[k + 1])
        ts.append(t[keep])
        vs.append(v[keep])
    t, v = np.concatenate(ts), np.concatenate(vs)
    # 100 ns bins (the mixed bench steps 0.1 us; lpf_rc is ~15 kHz)
    g = np.arange(0, TREC, 100e-9)
    idx = np.searchsorted(t, g)
    det = np.add.reduceat(v, idx) / np.diff(np.append(idx, len(v)))
    c = chips()
    nc = int(round(CHIP / 100e-9))
    seg = {0: [], 1: []}                                       # simulated chips by value (chip C0 has no history)
    for j in range(C0 + 1, C1 + 1):
        seg[c[j]].append(det[(j - C0) * nc:(j - C0 + 1) * nc])
    use = {0: 0, 1: 0}
    lead = []
    for j in range(C0 - LEAD_CHIPS, C0):                       # the code's own chips before the record
        lead.append(seg[c[j]][use[c[j]] % len(seg[c[j]])])
        use[c[j]] += 1
    full = np.concatenate(lead + [det])
    tt = np.arange(len(full)) * 100e-9
    with open(os.path.join(ROOT, 'build', f'det_{LEVEL}_{TAG}.inc'), 'w') as fh:
        fh.write(f'* detector waveform, {LEVEL} dBm, chips {C0}-{C1} of code {CODE}, extracted rx_t in {NP} pieces '
                 f'(sim/rx/chip16.py); {LEAD * 1e3:g} ms lead-in: chips {C0 - LEAD_CHIPS}-{C0 - 1} made of simulated chips of the same value\nVdet det 0 pwl(\n')
        for i in range(0, len(tt), 8):
            fh.write('+ ' + ' '.join(f'{a:.6e} {b:.6f}' for a, b in zip(tt[i:i + 8], full[i:i + 8])) + '\n')
        fh.write('+ )\n')
    per = []
    for j in range(C1 - C0 + 1):
        m = (g >= j * CHIP) & (g < (j + 1) * CHIP)
        per.append((C0 + j, c[C0 + j], float(np.mean(det[m]))))
    json.dump(dict(seams=seams, chips=per), open(os.path.join(OUT, 'join.json'), 'w'), indent=1)
    print('seams (warm-up vs the piece before, last 1 us): rms / mean mV')
    for k, r, m in seams:
        print(f'  piece {k:2d}: {r:.3f} / {m:+.3f}')
    sys.path.insert(0, os.path.join(ROOT, 'sim', 'mixed'))
    import gen_mixed
    gen_mixed.main(LEVEL, f'{(LEAD + TREC) * 1e3:.4f}m', pex=True, tag=TAG)


def decisions():
    """The RTL's comparator decisions: its trim code steps +1 (comp high) or -1 every sample."""
    from rawread import read_raw
    v = dict(read_raw(os.path.join(ROOT, 'build', 'mixed', f'mixed_{LEVEL}_pex_{TAG}.raw'))[0]['vars'])
    t, tr = np.real(v['time']), np.real(v['v(trim)'])
    code = np.round(tr * 256 / 1.8).astype(int)
    # one servo step every 13 us; the DAC glitches through other codes on a carry (127 -> 128 ...), so group the
    # changes into events (a quiet gap of > 3 us between them) and compare the code before and well after each
    ch = np.nonzero(np.diff(code))[0] + 1
    ch = ch[t[ch] > 3e-6]                     # after reset (rst_n high at 2 us: 0 -> 128)
    ev = [ch[0]] + [b for a, b in zip(ch, ch[1:]) if t[b] - t[a] > 3e-6]
    at = lambda x: code[min(np.searchsorted(t, x), len(t) - 1)]
    steps = np.array([at(t[i] + 3e-6) - code[i - 1] for i in ev])
    assert np.all(np.abs(steps) == 1), f'trim steps other than +-1: {sorted(set(steps.tolist()))}'
    gap = np.diff(t[ev])
    assert np.all(np.abs(gap - 13e-6) < 1e-6), f'servo steps not every 13 us: {gap.min() * 1e6:.2f}-{gap.max() * 1e6:.2f} us'
    return t[ev], (steps > 0).astype(int), np.array([at(t[i] + 3e-6) for i in ev])


def check():
    import radio
    t, c, code = decisions()

    class Log(radio.RxDigital):
        def __init__(s, cd):
            super().__init__(cd)
            s.bits = {p: [] for p in radio.PHASES}

        def _shift(s, p, bit):
            s.bits[p].append((s.n, bit))
            super()._shift(p, bit)

    rx = Log(CODE)
    for x in c:
        rx.step(x)
    sent = chips()
    res = {}
    for p, bl in rx.bits.items():
        # window of sample n covers decisions n-7 .. n: centre time -> record chip
        for lag in (-1, 0, 1):
            got = {}
            for n, b in bl:
                if n - 7 < 0:
                    continue
                tc = 0.5 * (t[n - 7] + t[n]) - LEAD
                j = int(math.floor(tc / CHIP)) + C0 + lag
                got.setdefault(j, b)
            if all(j in got for j in range(FIRST, LAST + 1)):
                err = [j for j in range(FIRST, LAST + 1) if got[j] != sent[j]]
                res[(p, lag)] = (err, ''.join(str(got[j]) for j in range(FIRST, LAST + 1)))
    (p, lag), (err, bits) = min(res.items(), key=lambda kv: len(kv[1][0]))
    want = ''.join(str(sent[j]) for j in range(FIRST, LAST + 1))
    t3 = LEAD + (FIRST - C0) * CHIP                                    # the first tested chip starts
    settled = code[np.searchsorted(t, t3) - 1]
    lead = code[(t > LEAD - 0.5e-3) & (t < t3)]
    out = dict(sent=want, got=bits, phase=p, lag=lag, errors=err, n_err=len(err), passed=len(err) <= 3,
               trim_at_first=int(settled), trim_last_lead=[int(lead.min()), int(lead.max())],
               all_phases={f'{a}/{b}': len(e) for (a, b), (e, _) in sorted(res.items())})
    json.dump(out, open(os.path.join(OUT, 'check.json'), 'w'), indent=1)
    print(f'sent     {want}\nslicer   {bits}  (phase {p}, lag {lag:+d})\n'
          f'{len(err)} of 16 wrong {err}: {"PASS" if out["passed"] else "FAIL"} (pass <= 3)\n'
          f'errors per phase/lag: {out["all_phases"]}; trim code entering chip {FIRST}: {out["trim_at_first"]} '
          f'(range over the last 0.5 ms before it: {out["trim_last_lead"]})')
    return 0 if out['passed'] else 1


def status():
    setup = json.load(open(os.path.join(OUT, 'setup.json')))
    try:
        st = json.load(open(os.path.join(SCHED, 'status.json')))
    except (OSError, ValueError):
        st = {}
    now = time.time()
    rows, starts = [], []
    for k in range(NP):
        g0, g1 = span(k)
        T = g1 - g0
        j = st.get(f'{TAG}_p{k:02d}', {})
        s0 = j.get('start')
        done = 0.0
        try:
            for ln in open(os.path.join(PD, f'piece_{k:02d}.log'), errors='replace'):
                if ln.startswith('PROG '):
                    done = max(done, float(ln.split()[1]))
        except OSError:
            pass
        if s0:
            starts.append(s0)
        el = ((j.get('end') or now) - s0) / 3600 if s0 else 0
        rows.append((k, T, done, el, j.get('state', 'waiting')))
    tot = sum(r[1] for r in rows)
    dn = sum(r[2] for r in rows)
    print(f'{TAG}: {"extracted rx_t" if TAG == "chip16" else os.path.basename(BASE)}, {LEVEL} dBm, chips {FIRST}-{LAST} of code {CODE}, {NP} pieces '
          f'({time.strftime("%Y-%m-%d %H:%M")})')
    if not starts:
        print('  not started')
    else:
        t0 = min(starts)
        el = (now - t0) / 3600
        rates = [r[2] * 1e6 / r[3] for r in rows if r[3] > 0.05 and r[2] > 0]
        rate = np.median(rates) if rates else 0
        left = [(r[1] - r[2]) * 1e6 / (r[2] * 1e6 / r[3]) for r in rows if r[3] > 0.05 and r[2] > 0 and r[4] == 'running']
        eta_h = max(left) if left else float('nan')
        print(f'  started {time.strftime("%a %d %b %H:%M", time.localtime(t0))}, running {el:.1f} h '
              f'({el / 24:.2f} days)')
        print(f'  simulated {dn * 1e6:.1f} of {tot * 1e6:.0f} us incl. warm-up ({dn / tot:.1%}); per piece {rate:.3f} us/h '
              f'(min {min(rates, default=0):.3f}, max {max(rates, default=0):.3f}), all {rate * len(rates):.1f} us/h')
        if eta_h == eta_h:
            print(f'  RF pieces done in ~{eta_h:.0f} h: {time.strftime("%a %d %b %H:%M", time.localtime(now + eta_h * 3600))}'
                  f' (slowest piece; then join + mixed bench + check, ~1 h)')
        states = {}
        for r in rows:
            states[r[4]] = states.get(r[4], 0) + 1
        print('  pieces:', ', '.join(f'{v} {k}' for k, v in sorted(states.items())),
              '| per piece us done:', ' '.join(f'{r[2] * 1e6:.0f}' for r in rows))
    # chips as they arrive: det mean per chip so far (lower det = more RF)
    c = chips()
    ts, vs = [], []
    for k in range(NP):
        t, v = part(k)
        ts.append(t)
        vs.append(v)
    t, v = np.concatenate(ts), np.concatenate(vs)
    fin = {}
    try:
        fin = json.load(open(os.path.join(OUT, 'check.json')))
    except (OSError, ValueError):
        pass
    if len(v):
        ref = float(np.mean(v))
        print(f'  chips (preview: det mean of what has run, vs the mean of all of it, {ref:.4f} V; '
              f'det drops when the carrier is on)')
        print('   chip  sent  run    det-mean mV  preview  slicer')
        nerr = 0
        for j in range(C0, C1 + 1):
            m = (t >= (j - C0) * CHIP) & (t < (j - C0 + 1) * CHIP)
            cov = np.sum(m) * 10e-9 / CHIP
            if not m.any():
                print(f'   {j:4d}  {c[j]:4d}  {cov:4.0%}')
                continue
            dm = (float(np.mean(v[m])) - ref) * 1e3
            pv = 1 if dm < 0 else 0
            tag = '' if FIRST <= j <= LAST else '(not tested)'
            sl = ''
            if fin and FIRST <= j <= LAST:
                b = int(fin['got'][j - FIRST])
                sl = f'{b} {"ok" if b == c[j] else "WRONG"}'
            ok = 'ok' if pv == c[j] else '--'
            nerr += FIRST <= j <= LAST and pv != c[j] and cov > 0.5
            print(f'   {j:4d}  {c[j]:4d}  {cov:4.0%}  {dm:+9.2f}    {pv} {ok}   {sl} {tag}')
        print(f'  preview: {nerr} of the tested chips past half-run disagree (a rough guide; the slicer decides)')
    if fin:
        print(f'  RESULT: {fin["n_err"]} of 16 wrong on the slicer -> {"PASS" if fin["passed"] else "FAIL"}')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    sys.exit({'prep': prep, 'join': join, 'check': check, 'status': status}[cmd]() or 0)
