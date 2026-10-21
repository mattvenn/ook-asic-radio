"""
Build docs/explainer.html: collect simulated and measured traces, embed them
(quantized to 1 byte, gzipped, base64) into template.html at /*__PAYLOAD__*/.

Sources (see README.md):
  bench/data/sweep2/ota.csv            measured path loss
  build/tb_tx_ab.raw                   TX chain transient (sims.sh)
  build/rx_rf_tone.raw, rx_rf_key.raw  RX antenna -> 6 stages -> log_det (sims.sh)
  sim/logdet/taps.txt, transfer_cw.txt log detector transfer, per-tap amplitudes
  build/rx_bb_<lvl>.raw, det_<lvl>.npz baseband det -> LPF -> avg -> comparator (sims.sh)
  model/                               link model sweep (Gold code, comparator, bit-exact digital)

A missing raw is reported and its view is left out of the payload; the page
shows a "no data" note for it.

    python3 docs/explainer/gendata.py
"""
import base64
import csv
import gzip
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build')
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'model'), os.path.join(ROOT, 'bench'),
                os.path.join(B, 'explainer_stub')]   # bench/scope.py imports pyvisa; sims.sh makes the stub
from rawread import read_raw

CODE = 0x5A
report = []


def q8(y):
    """Quantize to 1 byte over [lo, hi]; returns a dict the page decodes."""
    y = np.asarray(y, float)
    lo, hi = float(np.min(y)), float(np.max(y))
    if hi == lo:
        hi = lo + 1e-12
    b = np.round((y - lo) / (hi - lo) * 255).astype(np.uint8)
    return {'lo': lo, 'hi': hi, 'b': base64.b64encode(b.tobytes()).decode()}


def resample(t, y, t0, t1, n):
    tt = np.linspace(t0, t1, n)
    return np.interp(tt, t, y)


def trace(t, y, t0, t1, n):
    return dict(q8(resample(t, y, t0, t1, n)), t0=t0, t1=t1)


def raw(name):
    p = os.path.join(B, name)
    if not os.path.exists(p):
        report.append(f'MISSING {name} (run docs/explainer/sims.sh)')
        return None
    v = read_raw(p)[0]['vars']
    report.append(f'sim     {name}')
    return {k: np.real(a) for k, a in v.items()}


def path_loss():
    rows = [r for r in csv.DictReader(open(os.path.join(ROOT, 'bench', 'data', 'sweep2', 'ota.csv')))
            if r['dist_cm'].replace('.', '').isdigit()]
    d = np.array([float(r['dist_cm']) / 100 for r in rows])
    p = np.array([float(r['p_on_dbm']) for r in rows])
    report.append(f'bench   bench/data/sweep2/ota.csv ({len(d)} points)')
    return {'d_m': d.tolist(), 'p_dbm': p.tolist(), 'ref_dbm': -44.0, 'n': 1.89}


def tx():
    v = raw('tb_tx_ab.raw')
    if v is None:
        return None
    t = v['time'] * 1e9
    dip = v['v(ant_p)'] - v['v(ant_n)']
    out = {}
    for name, y in (('key', v['v(key)']), ('ring', v['v(xtx.ring)']), ('a', v['v(xtx.a)']),
                    ('b', v['v(xtx.b)']), ('drv_p', v['v(out_p)']), ('drv_n', v['v(out_n)']),
                    ('dipole', dip)):
        out[name] = trace(t, y, 0.0, 80.0, 2400)            # whole keyed burst, ns
        out[name + '_z'] = trace(t, y, 40.0, 46.0, 400)      # zoom: ~2.6 carrier cycles
        out[name + '_on'] = trace(t, y, 4.0, 10.0, 400)      # same 6 ns zoom, on the turn-on: enable rises at 5 ns
    on = (t > 20) & (t < 55)
    zc = np.where(np.diff(np.sign(v['v(xtx.ring)'][on] - 0.9)) > 0)[0]
    f = (len(zc) - 1) / (t[on][zc[-1]] - t[on][zc[0]]) * 1e3
    out['f_mhz'] = round(f, 1)
    out['dipole_vpk'] = round(float(np.max(np.abs(dip[on]))), 2)
    # keying speed of the actual circuit: the dipole's AC swing (half the peak-to-peak over one carrier period) vs the enable edges
    key = v['v(key)']
    kr = t[np.argmax(key > 0.9)]
    kf = t[np.where((key[:-1] > 0.9) & (key[1:] <= 0.9))[0][0]]
    def swing(tq):
        w = (t > tq - 2.3) & (t <= tq)
        return float(np.ptp(dip[w]) / 2) if w.sum() > 2 else 0.0
    steady = float(np.median([swing(x) for x in np.arange(25, 55, 0.5)]))
    ts = np.arange(kr, kr + 20, 0.05)
    out['on_ns'] = round(float(ts[np.argmax([swing(x) >= 0.9 * steady for x in ts])] - kr), 1)
    ts = np.arange(kf, kf + 25, 0.05)
    out['off_ns'] = round(float(ts[np.argmax([swing(x) <= 0.1 * steady for x in ts])] - kf), 1)
    out['dipole_swing'] = round(steady, 2)
    return out


def rx_rf():
    v = raw('rx_rf_tone.raw')
    if v is None:
        return None
    t = v['time'] * 1e9
    nodes = [('antenna', 'emf_'), ('pad', 'pad_'), ('stage 1', 'o1'), ('stage 2', 'o2'), ('stage 3', 'o3'),
             ('stage 4', 'o4'), ('stage 5', 'o5'), ('stage 6', 'out_')]
    def stages(v):
        t = v['time'] * 1e9
        res = []
        for label, n in nodes:
            y = v[f'v({n}p)'] - v[f'v({n}n)']
            w = t > 300
            res.append({'label': label, 'vpk': float(np.ptp(y[w]) / 2),   # AC amplitude: a DC offset would swamp tiny signals
                        'w': trace(t, y, 380.0, 390.0, 300)})
        return res
    out = {'nodes': stages(v), 'det': trace(t, v['v(det)'], 300.0, 400.0, 400)}
    # the same tone at more levels (docs/explainer/rf_levels.sh rx_rf_tone); -60 dBm is rf.sh's own run
    out['tone_levels'] = []
    for lvl in KEY_LEVELS:
        tv = v if lvl == -60 else raw(f'rx_rf_tone_{lvl}.raw')
        if tv is not None:
            out['tone_levels'].append({'lvl': lvl, 'nodes': stages(tv)})
    k = raw('rx_rf_key.raw')
    if k is not None:
        tk = k['time'] * 1e6
        out['key'] = trace(tk, k['v(key)'], 0.0, 3.5, 700)
        out['key_det'] = trace(tk, k['v(det)'], 0.0, 3.5, 700)
    # the same keyed run at more levels (docs/explainer/rf_levels.sh rx_rf_key); -60 dBm is rf.sh's own run
    out['key_levels'] = []
    for lvl in KEY_LEVELS:
        kl = k if lvl == -60 else raw(f'rx_rf_key_{lvl}.raw')
        if kl is not None:
            tk = kl['time'] * 1e6
            rf = (kl['v(out_p)'] - kl['v(out_n)']) * 1000          # last amplifier stage, differential, mV
            # 434 MHz is ~870 cycles while on: too fast to draw over 3.5 us, so keep its envelope (max and min per 5 ns)
            edges = np.searchsorted(tk, np.linspace(0.0, 3.5, 701))
            edges = np.clip(edges[:-1], 0, len(tk) - 1)
            hi, lo = np.maximum.reduceat(rf, edges), np.minimum.reduceat(rf, edges)
            tg = np.linspace(0.0, 3.5, 700, endpoint=False) + 0.0025
            out['key_levels'].append({'lvl': lvl, 'det': trace(tk, kl['v(det)'], 0.0, 3.5, 700),
                                      'rf_hi': trace(tg, hi, 0.0, 3.5, 700), 'rf_lo': trace(tg, lo, 0.0, 3.5, 700),
                                      # 40 ns around the switch-on (key rises at 0.5 us): the sine itself, and det settling
                                      'rf_z': trace(tk * 1e3, rf, 495.0, 535.0, 800), 'det_z': trace(tk * 1e3, kl['v(det)'], 495.0, 535.0, 400)})
    return out


def logdet():
    rows = np.loadtxt(os.path.join(ROOT, 'sim', 'logdet', 'taps.txt'), comments='#')
    report.append('sim     sim/logdet/taps.txt, transfer_cw.txt')
    cw = np.loadtxt(os.path.join(ROOT, 'sim', 'logdet', 'transfer_cw.txt'), skiprows=1)
    return {'pin': rows[:, 0].tolist(), 'det': rows[:, 1].tolist(),
            # taps.txt holds each tap's peak-to-peak amplitude (amp_pp_V): halve to peak
            'tap_amp': [(rows[:, 2 + 2 * i] / 2).tolist() for i in range(6)],
            'tap_i': [rows[:, 3 + 2 * i].tolist() for i in range(6)],
            'cw_pin': cw[:, 0].tolist(), 'cw_det': cw[:, 1].tolist()}


def sample_bits(t, comp, n):
    ts = np.arange(1, n + 1) * 13e-6 - 50e-9
    return ts, (np.interp(ts, t, comp) > 0.9).astype(np.uint8)


KEY_LEVELS = [-25, -30, -40, -50, -60, -70, -80, -90, -100, -110]   # rf.sh's tone and keyed runs repeated at these (rf_levels.sh)
BB_LEVELS = [-25, -30, -40, -50, -60, -70, -74, -78, -82, -86, -90, -94, -100, -110]   # sims.sh runs these (sim/rx/gen_det.py + sim/rx/bb.sh)


def baseband(lvl):
    import radio
    v = raw(f'rx_bb_{lvl}.raw')
    dp = os.path.join(B, f'det_{lvl}.npz')
    if v is None or not os.path.exists(dp):
        return None
    d = np.load(dp)
    t = v['time']
    n = int(t[-1] / 13e-6) - 1
    ts, bits = sample_bits(t, v['v(comp)'], n)
    rx = radio.RxDigital(CODE)
    scores = np.empty(n)
    for i, c in enumerate(bits):
        rx.step(int(c))
        scores[i] = rx.last_score
    lead, spc, on = int(d['lead']), int(d['spc']), d['on']
    truth = on[np.clip((ts * 1e6).astype(int), 0, len(on) - 1)]
    burst = (ts * 1e6 >= lead) & (ts * 1e6 < lead + 127 * spc)
    base = float(np.median(v['v(lpf)'][(t > 1.0e-3) & (t < 1.5e-3)]))
    t0, t1 = 3.0e-3, 6.0e-3               # window shown, ms
    tm = t * 1e3
    w = (ts > t0) & (ts < t1)
    return {
        'lvl': lvl, 'base': base,
        'det': trace(tm, v['v(det)'], 3.0, 6.0, 1500),          # absolute volts; base = the no-signal level
        'lpf': trace(tm, v['v(lpf)'], 3.0, 6.0, 1500),
        'avg': trace(tm, v['v(avg)'], 3.0, 6.0, 1500),
        'trim': trace(tm, v['v(trim)'], 3.0, 6.0, 1500),
        'comp': trace(tm, v['v(comp)'], 3.0, 6.0, 1500),          # what drives the trim servo stand-in: high steps it up
        'bits': base64.b64encode(np.packbits(bits[w]).tobytes()).decode(),
        'truth': base64.b64encode(np.packbits(truth[w].astype(np.uint8)).tobytes()).decode(),
        'nbits': int(w.sum()), 'bt0': float(ts[w][0] * 1e3), 'bdt': 13e-3,
        'agree': round(float(np.mean(bits[burst] == truth[burst]) * 100), 1),
        'score': trace(ts * 1e3, scores, 0.0, float(ts[-1] * 1e3), 1000),
        'peak': int(scores.max()), 'burst_ms': [lead / 1e3, (lead + 127 * spc) / 1e3],
    }


# Link model settings: tt with the H135 comparator, as e2e_h135_tt in sim/rerun/jobs_2026-10-13.py
# (docs/verify_2026-10-13.md: -94 dBm 27/48, -92 dBm 48/48).
MODEL = {'nf_db': 11.0, 'brf': 450e6, 'slope_mv_db': 13.4, 'offset_mv': 1.26, 'trim_mv': 0.127, 'noise_mv': 0.3,
         'levels': list(range(-110, -24, 2)), 'sends': 12, 'seed': 7}
MODEL_CACHE = os.path.join(B, 'explainer_model.json')   # the sweep takes ~2 min: rerun only when MODEL changes


def model_send(job):
    """One send (3 bursts) of CODE at one level: did the LED toggle, plus what the page draws for it."""
    import e2e
    import radio
    import scheme_compare as ch
    lvl, seed = job
    m = MODEL
    ch.rxm.NF_DB, ch.B_RF = m['nf_db'], m['brf']
    rng = np.random.default_rng(seed)
    v = e2e.run_record(e2e.send_onoff(CODE), 10 ** ((lvl - 30) / 10), 'noise', rng)
    s = m['slope_mv_db']
    afe = radio.AfeModel(offset_db=m['offset_mv'] / s, trim_lsb_db=m['trim_mv'] / s, noise_db=m['noise_mv'] / s, rng=rng)
    rx = radio.RxDigital(CODE)
    trim = rx.trim
    scores, comps = [], []
    for x in v:
        c = afe.compare(x, trim)
        trim = rx.step(c)
        comps.append(c)
        if rx.n % radio.S == 0:
            scores.append(rx.last_score)
    # per-chip decision of burst 1 at the best phase: majority of the 8 samples
    comps = np.array(comps)
    lead = e2e.LEAD_CHIPS * radio.S
    best = None
    for off in range(radio.S):
        seg = comps[lead + off: lead + off + 127 * radio.S]
        if len(seg) < 127 * radio.S:
            continue
        chips = (seg.reshape(127, radio.S).sum(1) > radio.S // 2).astype(np.uint8)
        n = int(np.sum(chips == radio.tx_chips(CODE)[:127]))
        if best is None or n > best[0]:
            best = (n, chips)
    return {'lvl': lvl, 'scores': base64.b64encode(np.array(scores, np.uint8).tobytes()).decode(),
            'events': [int(sc) for _, sc in rx.events], 'toggled': len(rx.toggles) == 1,
            'chips': base64.b64encode(np.packbits(best[1]).tobytes()).decode(), 'chip_ok': best[0]}


def model_sweep():
    """Link model at 2 dB steps: MODEL['sends'] sends of code 0x5A per level in receiver noise, log detector,
    comparator with offset, trim steps and noise, then the bit-exact digital. Per level: how many sends
    toggled the LED, and one send for the page to replay (the first whose outcome is the majority's)."""
    import e2e
    import radio
    key = json.dumps(MODEL, sort_keys=True)
    try:
        c = json.load(open(MODEL_CACHE))
        if c['key'] != key:
            raise ValueError
        runs = c['runs']
        src = 'cached ' + os.path.relpath(MODEL_CACHE, ROOT)
    except (OSError, ValueError, KeyError):
        from multiprocessing import Pool
        jobs = [(lvl, MODEL['seed'] * 100003 + i * 1009 + j) for i, lvl in enumerate(MODEL['levels'])
                for j in range(MODEL['sends'])]
        with Pool() as pool:
            sends = pool.map(model_send, jobs)
        runs = []
        for i, lvl in enumerate(MODEL['levels']):
            lv = sends[i * MODEL['sends']:(i + 1) * MODEL['sends']]
            ok = sum(r['toggled'] for r in lv)
            major = ok * 2 >= len(lv)
            runs.append(dict(next(r for r in lv if r['toggled'] == major), ok=ok))
        os.makedirs(B, exist_ok=True)
        json.dump({'key': key, 'runs': runs}, open(MODEL_CACHE, 'w'))
        src = f'{len(jobs)} sends'
    lv = MODEL['levels']
    report.append(f'model   model/ link sweep {lv[0]}..{lv[-1]} dBm, {MODEL["sends"]} sends per level ({src})')
    return {'levels': lv, 'runs': runs, 'sends': MODEL['sends'], 'lead_chips': e2e.LEAD_CHIPS,
            'period': radio.PERIOD, 'thresh': radio.THRESH}


def sizes():
    """Block areas and cell counts: docs/explainer/sizes.json, from sizes.py (run in the osic image)."""
    path = os.path.join(HERE, 'sizes.json')
    if not os.path.exists(path):
        report.append('MISSING docs/explainer/sizes.json (run docs/explainer/sizes.py)')
        return None
    report.append('sizes   docs/explainer/sizes.json')
    return json.load(open(path))


def words():
    """Headings, page text and tour captions: docs/explainer/text.md (format in textfile.py)."""
    import textfile
    pages = textfile.load()[1]
    report.append(f'text    docs/explainer/text.md ({len(pages)} pages)')
    return pages


def layout_jpg():
    """The whole-design render for the opening page: the GitHub gds action's gds_render.png
    (artifact of the same name), scaled to 1200 px wide JPEG as docs/explainer/layout.jpg."""
    f = os.path.join(HERE, 'layout.jpg')
    if not os.path.exists(f):
        report.append('layout  layout.jpg MISSING')
        return None
    report.append('layout  docs/explainer/layout.jpg')
    return base64.b64encode(open(f, 'rb').read()).decode()


def gold_chips():
    from gold import gold
    return ''.join(map(str, gold(CODE)))


def main():
    import gold as G   # the two LFSR sequences: code k = M1 xor M2 shifted by k (k = 127: M1 alone), as in model/gold.py
    payload = {'code': CODE, 'gold': gold_chips(), 'm1': ''.join(map(str, G.M1)), 'm2': ''.join(map(str, G.M2)), 'path': path_loss(), 'tx': tx(), 'rx_rf': rx_rf(),
               'logdet': logdet(), 'bb': [b for b in map(baseband, BB_LEVELS) if b],
               'model': model_sweep(), 'sizes': sizes(), 'layout_jpg': layout_jpg(), 'text': words()}
    blob = base64.b64encode(gzip.compress(json.dumps(payload, separators=(',', ':')).encode(), 9)).decode()
    brand = base64.b64encode(open(os.path.join(HERE, 'brand_header.jpg'), 'rb').read()).decode()   # Zero to ASIC header art
    html = open(os.path.join(HERE, 'template.html')).read().replace('/*__PAYLOAD__*/', blob).replace('/*__BRAND__*/', brand)
    out = os.path.join(ROOT, 'docs', 'explainer.html')
    open(out, 'w').write(html)
    for line in report:
        print(line)
    print(f'payload {len(blob) / 1e3:.0f} kB -> {os.path.relpath(out, ROOT)} ({len(html) / 1e3:.0f} kB)')


if __name__ == '__main__':
    main()
