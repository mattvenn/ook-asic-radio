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
    on = (t > 20) & (t < 55)
    zc = np.where(np.diff(np.sign(v['v(xtx.ring)'][on] - 0.9)) > 0)[0]
    f = (len(zc) - 1) / (t[on][zc[-1]] - t[on][zc[0]]) * 1e3
    out['f_mhz'] = round(f, 1)
    out['dipole_vpk'] = round(float(np.max(np.abs(dip[on]))), 2)
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
            out['key_levels'].append({'lvl': lvl, 'det': trace(kl['time'] * 1e6, kl['v(det)'], 0.0, 3.5, 700)})
    return out


def logdet():
    rows = np.loadtxt(os.path.join(ROOT, 'sim', 'logdet', 'taps.txt'), comments='#')
    report.append('sim     sim/logdet/taps.txt, transfer_cw.txt')
    cw = np.loadtxt(os.path.join(ROOT, 'sim', 'logdet', 'transfer_cw.txt'), skiprows=1)
    return {'pin': rows[:, 0].tolist(), 'det': rows[:, 1].tolist(),
            # taps.py measures each tap with ngspice 'meas ... pp' (peak-to-peak) though its header says amp_pk: halve to peak
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
        'trim': trace(tm, v['v(trim)'], 3.0, 6.0, 600),
        'bits': base64.b64encode(np.packbits(bits[w]).tobytes()).decode(),
        'truth': base64.b64encode(np.packbits(truth[w].astype(np.uint8)).tobytes()).decode(),
        'nbits': int(w.sum()), 'bt0': float(ts[w][0] * 1e3), 'bdt': 13e-3,
        'agree': round(float(np.mean(bits[burst] == truth[burst]) * 100), 1),
        'score': trace(ts * 1e3, scores, 0.0, float(ts[-1] * 1e3), 1000),
        'peak': int(scores.max()), 'burst_ms': [lead / 1e3, (lead + 127 * spc) / 1e3],
    }


def model_sweep():
    """Link model at 2 dB steps: one send (3 bursts) of code 0x5A in receiver noise
    (NF 11 dB over 450 MHz), log detector, comparator with 2 mV offset, 0.07 mV trim
    steps and 0.3 mV noise at 13 mV/dB, then the bit-exact digital."""
    import e2e
    import radio
    import scheme_compare as ch
    import rx_eval as r
    ch.rxm.NF_DB, ch.B_RF = 11.0, 450e6
    rng = np.random.default_rng(7)
    on = e2e.send_onoff(CODE)
    levels = list(range(-110, -58, 2))
    res = []
    for lvl in levels:
        v = e2e.run_record(on, 10 ** ((lvl - 30) / 10), 'noise', rng)
        afe = radio.AfeModel(offset_db=2 / 13, trim_lsb_db=0.07 / 13, noise_db=0.3 / 13, rng=rng)
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
            m = int(np.sum(chips == radio.tx_chips(CODE)[:127]))
            if best is None or m > best[0]:
                best = (m, chips, seg)
        res.append({'lvl': lvl, 'scores': base64.b64encode(np.array(scores, np.uint8).tobytes()).decode(),
                    'events': [int(s) for _, s in rx.events], 'toggled': len(rx.toggles) == 1,
                    'chips': base64.b64encode(np.packbits(best[1]).tobytes()).decode(),
                    'chip_ok': best[0]})
    report.append(f'model   model/ link sweep {levels[0]}..{levels[-1]} dBm')
    return {'levels': levels, 'runs': res, 'lead_chips': e2e.LEAD_CHIPS, 'period': radio.PERIOD,
            'thresh': radio.THRESH}


def gold_chips():
    from gold import gold
    return ''.join(map(str, gold(CODE)))


def main():
    import gold as G   # the two LFSR sequences: code k = M1 xor M2 shifted by k (k = 127: M1 alone), as in model/gold.py
    payload = {'code': CODE, 'gold': gold_chips(), 'm1': ''.join(map(str, G.M1)), 'm2': ''.join(map(str, G.M2)), 'path': path_loss(), 'tx': tx(), 'rx_rf': rx_rf(),
               'logdet': logdet(), 'bb': [b for b in map(baseband, BB_LEVELS) if b],
               'model': model_sweep()}
    blob = base64.b64encode(gzip.compress(json.dumps(payload, separators=(',', ':')).encode(), 9)).decode()
    html = open(os.path.join(HERE, 'template.html')).read().replace('/*__PAYLOAD__*/', blob)
    out = os.path.join(ROOT, 'docs', 'explainer.html')
    open(out, 'w').write(html)
    for line in report:
        print(line)
    print(f'payload {len(blob) / 1e3:.0f} kB -> {os.path.relpath(out, ROOT)} ({len(html) / 1e3:.0f} kB)')


if __name__ == '__main__':
    main()
