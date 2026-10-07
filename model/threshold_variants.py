"""Which comparator threshold scheme survives near sensitivity? (quick study)"""
import numpy as np, rx_eval as r, scheme_compare as ch
from gold import gold
cb = gold(r.CODE); on = np.repeat(cb.astype(bool), r.SPC)
FS = 1e6 / r.SAMP                          # RX sample rate, 76.9 kS/s

def comp_dac_loop(v, lsb_db):
    """median-tracking DAC with a given step (in dB), threshold quantised to that step"""
    step = lsb_db / r.LSB_DB
    thr = v[0]; out = np.empty(len(v), np.uint8)
    for i, x in enumerate(v):
        c = x > thr; out[i] = c
        thr += step if c else -step
    return out

def comp_avg_ref(v, tau=2e-3, offset_db=0.0, trim_lsb_db=None):
    """analog RC average as the reference; optional comparator offset; optional
    fine DAC trim servo (step trim_lsb_db) that drives the ones-density to 50%"""
    a = 1 / (tau * FS); avg = v[0]; trim = 0.0
    off = offset_db / r.LSB_DB
    step = None if trim_lsb_db is None else trim_lsb_db / r.LSB_DB
    out = np.empty(len(v), np.uint8)
    for i, x in enumerate(v):
        avg += a * (x - avg)
        c = x > avg + off + trim; out[i] = c
        if step is not None:
            trim += step if c else -step
    return out

VARIANTS = {
    'DAC loop 0.44 dB (8-bit full range)': lambda v: comp_dac_loop(v, 0.44),
    'DAC loop 0.05 dB':                    lambda v: comp_dac_loop(v, 0.05),
    'RC-average ref':                      lambda v: comp_avg_ref(v),
    'RC-avg ref + 2 mV offset (0.125 dB)': lambda v: comp_avg_ref(v, offset_db=0.125),
    'RC-avg + offset + fine trim servo':   lambda v: comp_avg_ref(v, offset_db=0.125, trim_lsb_db=0.005),
}
rng = np.random.default_rng(5)
levels = (-80, -86, -90, -94, -98)
trials = 5
print('level   soft  ' + '  '.join(f'[{k}]' for k in VARIANTS))
for lvl in levels:
    ok = dict.fromkeys(VARIANTS, 0); soft = 0
    for _ in range(trials):
        st = int(rng.uniform(1e-3, ch.REC - 14.5e-3) * 1e6)
        y = ch.received_envelope(on, st, 10 ** ((lvl - 30) / 10), 'noise', rng)
        v = r.to_lsb(y[::r.SAMP])
        soft += r.soft_detect(v, 2.0 * cb - 1)[0]
        for k, f in VARIANTS.items():
            ok[k] += r.hard_detect(f(v), cb)[0]
    print(f'{lvl:4d}  {soft}/{trials}   ' + '   '.join(f'{ok[k]}/{trials}' for k in VARIANTS), flush=True)
# false alarms
fa = dict.fromkeys(VARIANTS, 0)
for _ in range(4):
    y = ch.received_envelope(on, 0, 0.0, 'noise', rng); v = r.to_lsb(y[::r.SAMP])
    for k, f in VARIANTS.items():
        fa[k] += r.hard_detect(f(v), cb)[0]
print('false alarms (4 empty records):', fa)
