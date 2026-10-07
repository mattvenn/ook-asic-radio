"""
RF analysis helpers for scope captures (numpy only).
"""
import numpy as np


def spectrum_dbm(v, fs, r_load=50.0):
    """Single-sided power spectrum in dBm per bin, assuming v is across r_load.
    Blackman-Harris window, amplitude-corrected so a tone's peak bin reads its power."""
    n = len(v)
    w = np.blackman(n)
    x = np.fft.rfft((v - v.mean()) * w)
    amp = 2 * np.abs(x) / w.sum()          # peak amplitude of a tone
    p_w = (amp / np.sqrt(2)) ** 2 / r_load
    f = np.fft.rfftfreq(n, 1 / fs)
    return f, 10 * np.log10(p_w / 1e-3 + 1e-30)


def peak(f, dbm, fmin=0.0, fmax=None):
    """Strongest bin in [fmin, fmax] with parabolic interpolation -> (freq, dBm)."""
    m = (f >= fmin) & (f <= (fmax if fmax else f[-1]))
    idx = np.flatnonzero(m)
    i = idx[np.argmax(dbm[m])]
    if 0 < i < len(f) - 1:
        a, b, c = dbm[i - 1], dbm[i], dbm[i + 1]
        d = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else 0.0
        return f[i] + d * (f[1] - f[0]), b - 0.25 * (a - c) * d
    return f[i], dbm[i]


def envelope(v, fs, fc, bw):
    """Complex baseband around fc with a brick-wall low-pass of +/-bw/2;
    abs() of the result is the RF envelope."""
    n = len(v)
    x = np.fft.fft(v - v.mean())
    f = np.fft.fftfreq(n, 1 / fs)
    keep = np.abs(f - fc) <= bw / 2       # positive-frequency band only
    analytic = np.fft.ifft(np.where(keep, x, 0) * 2)
    t = np.arange(n) / fs
    return analytic * np.exp(-2j * np.pi * fc * t)


def dbm_to_vpp(dbm, r_load=50.0):
    return 2 * np.sqrt(2) * np.sqrt(1e-3 * 10 ** (dbm / 10) * r_load)


def write_pwl(path, t, v, decimate=1):
    """Two-column time/value file for an ngspice XSPICE filesource."""
    t = np.asarray(t)[::decimate]
    v = np.asarray(v)[::decimate]
    np.savetxt(path, np.column_stack([t - t[0], v]), fmt='%.6e')
