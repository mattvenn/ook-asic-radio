"""
Record one whole OOK packet (board running autorun 'uart' mode or
board.py uart 9600), decode it from the RF envelope, and save stimulus
files for the RX simulation.

    python bench/record.py <label> [scale_v_per_div]

Saves bench/data/packet_<label>_<time>.npz containing:
  bb      complex baseband around the carrier, 100 MSa/s (complex64)
  raw     RAW_US of full-rate RF from just before the packet (float32)
plus stim/packet_<label>.pwl (ngspice filesource: time, volts) of the
first PWL_US of that.
"""
import os
import sys
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import rf
from scope import Scope

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
STIM = os.path.join(os.path.dirname(HERE), 'stim')
PACKET = bytes([0x55] * 4) + bytes([0x2D, 0xD4]) + b'HELLO TT'   # = fw/ringkey.py
BAUD = 9600
DURATION = 30e-3          # packet ~14.6 ms, repeats every ~25 ms: 30 ms always holds one
BB_RATE = 100e6
RAW_US = 400
PWL_US = 200


def to_baseband(v, fs, fc, rate=BB_RATE, chunk=1 << 22):
    """Mix to DC and boxcar-decimate to `rate`, chunked to bound memory."""
    dec = int(round(fs / rate))
    out = []
    for i in range(0, len(v) - dec, chunk):
        seg = v[i:i + chunk]
        seg = seg[: len(seg) // dec * dec]
        n = np.arange(i, i + len(seg))
        mixed = seg * np.exp(-2j * np.pi * fc / fs * n)
        out.append(mixed.reshape(-1, dec).mean(axis=1).astype(np.complex64))
    return np.concatenate(out), fs / dec


def uart_decode(bits, rate, baud=BAUD):
    """bits: logic level per sample (1 = idle/mark). Returns list of
    (start_sample, byte, framing_ok)."""
    spb = rate / baud
    out, i = [], 0
    n = len(bits)
    while i < n - int(10 * spb):
        if bits[i] == 1 and bits[i + 1] == 0:          # start bit edge
            c = i + 1 + spb / 2
            if bits[int(c)] == 0:
                val = 0
                for b in range(8):
                    val |= int(bits[int(c + (b + 1) * spb)]) << b
                stop = bits[int(c + 9 * spb)] == 1
                out.append((i, val, stop))
                i = int(c + 9 * spb)
                continue
        i += 1
    return out


def main(label, scale=0.005):
    os.makedirs(DATA, exist_ok=True)
    os.makedirs(STIM, exist_ok=True)
    sc = Scope()
    sc.s.timeout = 300000
    sc.setup_channel(1, scale=scale, fifty=True)

    # find the on-level with short untriggered captures
    amp = None
    for _ in range(10):
        _, v, fs = sc.capture(1, duration=2e-3)
        f, dbm = rf.spectrum_dbm(v[: 1 << 20], fs)
        fc, p = rf.peak(f, dbm, 450e6, 600e6)
        if p > -75:
            amp = np.percentile(np.abs(v - v.mean()), 99.5)
            break
    if amp is None:
        sys.exit('no carrier found; is the TX running?')
    print(f'carrier {fc/1e6:.2f} MHz, ~{amp*1e3:.2f} mV peak')

    t0 = time.time()
    t, v, fs = sc.capture(1, duration=DURATION)
    sc.close()
    print(f'captured {len(v)/1e6:.0f} Mpts at {fs/1e9:.2f} GSa/s in {time.time()-t0:.0f} s')

    # carrier frequency from the strongest stretch of the capture
    blk = 1 << 16
    rms = np.sqrt((v[: len(v) // blk * blk].reshape(-1, blk) ** 2).mean(axis=1))
    j = int(np.argmax(rms)) * blk
    f, dbm = rf.spectrum_dbm(v[j:j + blk], fs)
    fc, _ = rf.peak(f, dbm, 450e6, 600e6)
    bb, rate = to_baseband(v, fs, fc)
    env = np.abs(bb)
    k = int(2e-6 * rate)
    env_s = np.convolve(env, np.ones(k) / k, mode='same')
    on_lvl = np.percentile(env_s, 95)
    off_lvl = np.percentile(env_s, 5)
    thresh = (on_lvl + off_lvl) / 2
    carrier_on = env_s > thresh
    bits = (~carrier_on).astype(np.uint8)     # carrier on = UART space (0)
    frames = uart_decode(bits, rate)
    got = bytes(b for _, b, _ in frames)
    # the 0x55 preamble is there to let the receiver lock on, so only
    # require sync word + payload
    MATCH = PACKET[4:]
    ok = MATCH in got
    # sample index (full rate) of the start of the first complete packet
    dec = int(round(fs / rate))
    pos = got.find(MATCH)
    start = frames[max(0, pos - 4)][0] * dec if ok else int(np.argmax(rms)) * blk
    snr = 20 * np.log10(on_lvl / max(off_lvl, 1e-12))
    print(f'envelope on {on_lvl*1e3:.3f} mV, off {off_lvl*1e3:.4f} mV ({snr:.0f} dB)')
    print(f'decoded {len(frames)} bytes: {got!r}')
    print('PACKET OK' if ok else 'packet mismatch')

    stamp = time.strftime('%Y%m%d_%H%M%S')
    base = os.path.join(DATA, f'packet_{label}_{stamp}')
    a = max(0, start - int(20e-6 * fs))
    raw = v[a:a + int(RAW_US * 1e-6 * fs)]
    np.savez(base + '.npz', bb=bb, bb_rate=rate, fc=fc, fs=fs,
             raw=raw.astype(np.float32), raw_start_s=a / fs,
             label=label, decoded=got, ok=ok)
    pwl = os.path.join(STIM, f'packet_{label}.pwl')
    npwl = int(PWL_US * 1e-6 * fs)
    rf.write_pwl(pwl, np.arange(npwl) / fs, raw[:npwl] - raw[:npwl].mean())

    fig, ax = plt.subplots(2, 1, figsize=(12, 6))
    tb = np.arange(len(env_s)) / rate * 1e3
    d = max(1, len(env_s) // 50000)
    ax[0].plot(tb[::d], env_s[::d] * 1e3); ax[0].axhline(thresh * 1e3, color='r', ls=':')
    ax[0].set_xlabel('ms'); ax[0].set_ylabel('envelope mV'); ax[0].grid()
    ax[0].set_title(f'{label}: {fc/1e6:.2f} MHz, decoded {got!r} {"OK" if ok else "FAIL"}')
    n = int(3e-3 * rate)
    ax[1].plot(tb[:n], env_s[:n] * 1e3); ax[1].set_xlabel('ms'); ax[1].grid()
    ax[1].set_title('first 3 ms (preamble 0x55)')
    fig.tight_layout(); fig.savefig(base + '.png', dpi=110)
    print('saved', base + '.{npz,png}', 'and', pwl)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 0.005)
