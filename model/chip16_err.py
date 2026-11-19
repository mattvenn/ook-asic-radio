"""Run from the repo root: python3 model/chip16_err.py [trials] (40: ~5 min; results 2026-11-19 in TODO.md).
Chip errors at the slicer (system model) per level: for the 16-chip extracted test (TODO.md, 2026-11-19).
e2e.py's noise channel and AfeModel, radio.RxDigital bit-exact; logs each phase's chip bits, aligns them to the sent
chips, counts errors on the best phase over bursts 2-3 (trim settled) and on chips 3-18 of each."""
import sys, os
sys.path.insert(0, 'model'); sys.path.insert(0, 'bench')
import numpy as np
import scheme_compare as ch, radio, rx_eval as r, e2e

class Log(radio.RxDigital):
    def __init__(s, code):
        super().__init__(code); s.bits = {p: [] for p in radio.PHASES}
    def _shift(s, p, bit):
        s.bits[p].append(bit); super()._shift(p, bit)

SETS = {'tt': dict(nf=11.0, slope=13.4, off=1.26, trim=0.127),
        'tt_pex': dict(nf=13.2, slope=13.4, off=1.26, trim=0.127),   # extracted/sch drop 0.60 at -90: +2.2 dB NF
        'fs50_pex': dict(nf=14.2, slope=12.4, off=1.3, trim=0.135)}
LEVELS = [-94, -92, -90, -88, -85, -82]
TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 40
ch.B_RF = 450e6
tx = radio.tx_chips(e2e.CODE).astype(int)
L, G = radio.LEN, radio.GAP
on = np.repeat(tx.astype(bool), r.SPC)
for name, s in SETS.items():
    ch.rxm.NF_DB = s['nf']
    rng, crng = np.random.default_rng(21), np.random.default_rng(5)
    for lvl in LEVELS:
        errs, n, w0 = 0, 0, 0; wins = 0; worst = 0
        for _ in range(TRIALS):
            v = e2e.run_record(on, 10 ** ((lvl - 30) / 10), 'noise', rng)
            afe = radio.AfeModel(offset_db=s['off'] / s['slope'], trim_lsb_db=s['trim'] / s['slope'],
                                 noise_db=0.3 / s['slope'], rng=crng)
            rx = Log(e2e.CODE)
            trim = rx.trim
            for x in v:
                trim = rx.step(afe.compare(x, trim))
            best = None
            for p, b in rx.bits.items():
                b = np.array(b)
                for lag in range(e2e.LEAD_CHIPS - 3, e2e.LEAD_CHIPS + 4):
                    seg = b[lag:lag + len(tx)]
                    if len(seg) < len(tx): continue
                    e = np.sum(seg != tx)
                    if best is None or e < best[0]: best = (e, seg)
            seg = best[1]
            for k in (1, 2):                      # bursts 2 and 3
                a = k * (L + G)
                errs += np.sum(seg[a:a + L] != tx[a:a + L]); n += L
                we = np.sum(seg[a + 3:a + 19] != tx[a + 3:a + 19]); wins += 1; w0 += we == 0; worst = max(worst, we)
        print(f'{name:9s} {lvl:4d} dBm  chip errors {errs / n * 100:5.2f} %  16-chip windows all correct {w0}/{wins}  worst window {worst}', flush=True)
