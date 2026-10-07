"""
Spectral purity of the ring: one long capture with the ring steady on,
fine-resolution spectrum around the carrier -> single-sideband phase
noise estimate L(f) in dBc/Hz, plus any discrete FM spurs.

    python bench/phasenoise.py [duration_ms]
"""
import os
import sys
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import board
import rf
from scope import Scope

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
OFFSETS = (1e3, 10e3, 100e3, 1e6, 3e6)


def main(dur_ms=5.0):
    os.makedirs(DATA, exist_ok=True)
    print(board.run('on').splitlines()[-1])
    time.sleep(2)
    sc = Scope()
    sc.setup_channel(1, scale=0.01, fifty=True)
    t, v, fs = sc.capture(1, duration=dur_ms * 1e-3)
    sc.close()
    n = len(v)
    print(f'captured {n/1e6:.1f} Mpts at {fs/1e9:.2f} GSa/s ({n/fs*1e3:.2f} ms)')

    # coarse carrier, then mix to baseband and decimate around it
    f, dbm = rf.spectrum_dbm(v[: 1 << 16], fs)
    fc, _ = rf.peak(f, dbm, 400e6, 650e6)
    span = 20e6
    bb = rf.envelope(v, fs, fc, span)          # complex baseband, +/-10 MHz
    dec = int(fs // (2 * span))
    bb = bb[::dec]
    fsb = fs / dec
    w = np.blackman(len(bb))
    X = np.fft.fftshift(np.fft.fft(bb * w))
    fo = np.fft.fftshift(np.fft.fftfreq(len(bb), 1 / fsb))
    P = np.abs(X) ** 2
    rbw = fsb / len(bb) * 1.73                 # Blackman ENBW
    pc = P.max()
    L = 10 * np.log10(P / pc) - 10 * np.log10(rbw)
    i0 = np.argmax(P)
    fpk = fc + fo[i0]

    # carrier power fraction within +/-50 kHz: a measure of how 'clean' it is
    near = np.abs(fo - fo[i0]) < 50e3
    frac = P[near].sum() / P.sum()
    print(f'carrier {fpk/1e6:.4f} MHz; RBW {rbw:.0f} Hz; '
          f'{frac*100:.1f}% of power within +/-50 kHz')

    def at(off):
        vals = []
        for s in (+1, -1):
            m = np.abs(fo - (fo[i0] + s * off)) < max(off * 0.1, 3 * rbw)
            vals.append(np.median(L[m]))
        return np.mean(vals)
    for off in OFFSETS:
        print(f'  L({off/1e3:g} kHz) ~ {at(off):.0f} dBc/Hz')

    # discrete spurs: bins > 15 dB above local median, outside +/-20 kHz
    k = 201
    med = np.convolve(L, np.ones(k) / k, mode='same')
    spur = (L - med > 15) & (np.abs(fo - fo[i0]) > 20e3)
    if spur.any():
        idx = np.flatnonzero(spur)
        top = idx[np.argsort(L[idx])[-8:]]
        print('  spurs:', ', '.join(f'{(fo[i]-fo[i0])/1e3:+.1f} kHz {L[i]-10*np.log10(1/rbw):.0f} dBc'
                                    for i in sorted(top)))

    stamp = time.strftime('%Y%m%d_%H%M%S')
    base = os.path.join(DATA, f'phasenoise_{stamp}')
    np.savez(base + '.npz', fo=fo, L=L, fc=fpk, rbw=rbw)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 8))
    a1.plot(fo / 1e6, L - L.max())
    a1.set_xlim(-10, 10); a1.set_xlabel('offset MHz'); a1.set_ylabel('dBc (per bin)')
    a1.set_title(f'ring 1 spectrum around {fpk/1e6:.3f} MHz, RBW {rbw:.0f} Hz'); a1.grid()
    pos = fo - fo[i0] > 0
    a2.semilogx(fo[pos] - fo[i0], L[pos], lw=0.5)
    a2.set_xlim(1e3, 10e6); a2.set_xlabel('offset Hz'); a2.set_ylabel('L(f) dBc/Hz'); a2.grid(which='both')
    fig.tight_layout(); fig.savefig(base + '.png', dpi=110)
    print('saved', base + '.{npz,png}')


if __name__ == '__main__':
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 5.0)
