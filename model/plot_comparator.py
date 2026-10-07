"""Visualise the comparator: detector output, averaged reference, decisions."""
import numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
import rx_eval as r, scheme_compare as ch, radio
from gold import gold
MV_PER_DB = 16.0
code = 0x5A; cb = gold(code); on = np.repeat(cb.astype(bool), r.SPC)
rng = np.random.default_rng(3)
fig, axs = plt.subplots(4, 2, figsize=(14, 10), sharex='col',
                        gridspec_kw={'height_ratios': [3, 1, 1, 1]})
for col, lvl in enumerate((-70, -94)):
    st = 3000
    y = ch.received_envelope(on, st, 10 ** ((lvl - 30) / 10), 'noise', rng)
    v = r.to_lsb(y[::r.SAMP])
    afe = radio.AfeModel(); rx = radio.RxDigital(code); trim = rx.trim
    ref = np.empty(len(v)); comp = np.empty(len(v), np.uint8)
    for i, x in enumerate(v):
        comp[i] = afe.compare(x, trim)
        ref[i] = afe.avg + afe.off + afe.tg * (trim - 128)
        trim = rx.step(comp[i])
    t = np.arange(len(v)) * r.SAMP / 1e3            # ms
    mv = lambda lsb: lsb * r.LSB_DB * MV_PER_DB
    base = mv(np.median(v[: st // r.SAMP - 10]))
    a = (t > 3.2) & (t < 6.2)                        # 3 ms window inside the burst
    truth = on[::r.SAMP][: len(v)] if len(on) else None
    chips_true = np.zeros(len(v)); idx = np.arange(len(v)) * r.SAMP - st
    ok = (idx >= 0) & (idx < len(on)); chips_true[ok] = on[idx[ok]]
    ax = axs[0, col]
    ax.plot(t[a], mv(v[a]) - base, lw=0.8, label='detector output v (comparator +)')
    ax.plot(t[a], mv(ref[a]) - base, lw=2, label='reference = slow average + offset + trim (comparator -)')
    ax.set_ylabel('mV (relative to noise-only level)')
    ax.set_title(f'{lvl} dBm  (signal swing ~{mv(np.median(v[a][chips_true[a]==1]) - np.median(v[a][chips_true[a]==0])):.1f} mV '
                 f'at {MV_PER_DB:g} mV/dB)')
    ax.legend(fontsize=8, loc='upper right'); ax.grid(alpha=0.3)
    axs[1, col].step(t[a], chips_true[a], where='post', color='k'); axs[1, col].set_ylabel('TX chips\n(truth)')
    axs[2, col].step(t[a], comp[a], where='post', color='C3'); axs[2, col].set_ylabel('comparator\nbits')
    agree = np.mean(comp[ok] == chips_true[ok]) * 100
    axs[2, col].set_title(f'comparator agrees with the TX chip {agree:.0f}% of the time', fontsize=9)
    axs[3, col].plot(t[a], np.array([rx.trim]*a.sum()) * 0, alpha=0)  # placeholder
    axs[3, col].text(0.02, 0.4, f'detections: {rx.events}\n(score 97+ of 127 = detected; ~64 = pure chance)',
                     transform=axs[3, col].transAxes, fontsize=9)
    axs[3, col].axis('off')
    for k in range(3): axs[k, col].grid(alpha=0.3)
    axs[2, col].set_xlabel('ms')
fig.tight_layout(); fig.savefig('comparator_view.png', dpi=100)
print('saved model/comparator_view.png')
