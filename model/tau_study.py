"""Averaging-reference time constant vs sensitivity, with offset + trim servo."""
import numpy as np, rx_eval as r, scheme_compare as ch, threshold_variants as tv
from gold import gold
cb = gold(r.CODE); on = np.repeat(cb.astype(bool), r.SPC)
rng = np.random.default_rng(9)
taus = (0.3e-3, 1e-3, 2e-3, 5e-3)
trials = 5
for case in ('noise', 'fading', 'bursty'):
    for lvl in ((-70, -90, -94) if case != 'bursty' else (-60, -66, -72)):
        ok = dict.fromkeys(taus, 0)
        for _ in range(trials):
            st = int(rng.uniform(1e-3, ch.REC - 14.5e-3) * 1e6)
            y = ch.received_envelope(on, st, 10 ** ((lvl - 30) / 10), case, rng)
            v = r.to_lsb(y[::r.SAMP])
            for t in taus:
                ok[t] += r.hard_detect(tv.comp_avg_ref(v, tau=t, offset_db=0.125, trim_lsb_db=0.005), cb)[0]
        print(f'{case:7s} {lvl:4d} dBm  ' + '  '.join(f'tau {t*1e3:g}ms {ok[t]}/{trials}' for t in taus), flush=True)
