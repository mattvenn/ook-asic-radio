"""Nodal model of the r2r trim DAC with bit-driver output resistance and resistor mismatch.

No ngspice: a numpy solve of the ladder (unit R 10.6 k, legs 2R, 2R termination to VGND, as xschem/gen/dac.py).
Each bit leg gets Rhi (bit = 1) or Rlo (bit = 0) in series: the driver's output resistance. Reproduces the shape
seen on the tt08 silicon (a step DOWN at the 127 -> 128 carry, smaller ones at 63/64, 191/192): series drive
resistance makes every bit weaker than the undriven termination, the MSB most.

    python3 sim/dac/ladder_model.py
"""
import numpy as np

R = 10.6e3
LSB = 1.8 / 256


def dac(code, Rhi, Rlo, Rs=None, Rl=None, V=1.8):
    """out for one code. Rs: 7 series R; Rl: 8 bit legs + termination (index 8)."""
    Rs = Rs if Rs is not None else np.full(7, R)
    Rl = Rl if Rl is not None else np.full(9, 2 * R)
    G = np.zeros((8, 8))
    I = np.zeros(8)
    for i in range(8):
        b = (code >> i) & 1
        g = 1 / (Rl[i] + (Rhi if b else Rlo))
        G[i, i] += g
        I[i] += g * V * b
    G[0, 0] += 1 / Rl[8]
    for i in range(1, 8):
        g = 1 / Rs[i - 1]
        G[i, i] += g
        G[i - 1, i - 1] += g
        G[i, i - 1] -= g
        G[i - 1, i] -= g
    return np.linalg.solve(G, I)[7]


def curve(**k):
    return np.array([dac(c, **k) for c in range(256)])


if __name__ == '__main__':
    print('driver R (hi/lo) -> DNL (LSB) at the carries; ideal = 0')
    for Rhi, Rlo in [(0, 0), (500, 300), (1500, 800), (3000, 1500)]:
        v = curve(Rhi=Rhi, Rlo=Rlo)
        d = np.diff(v) / LSB - 1
        over = int(np.argmax(v[128:] > v[127]))
        print(f'  {Rhi:5d}/{Rlo:<5d} 127>128 {d[127]:+.2f}  63>64 {d[63]:+.2f}  191>192 {d[191]:+.2f}  '
              f'159>160 {d[159]:+.2f}  codes overlapped at 128: {over}  V255 {v[255]:.4f}  V180 {v[180]:.4f}')
    rng = np.random.default_rng(1)
    print('unit-resistor mismatch only (ideal drivers), 2000 samples')
    for sig in (0.002, 0.005, 0.01):
        out = []
        for _ in range(2000):
            def u(n):
                return R * (1 + sig * rng.standard_normal(n))
            v = curve(Rhi=0, Rlo=0, Rs=u(7), Rl=u(9) + u(9))
            out.append(np.diff(v) / LSB - 1)
        out = np.array(out)
        print(f'  sigma {sig * 100:.1f} %: DNL sigma 127>128 {out[:, 127].std():.3f}, 191>192 {out[:, 191].std():.3f}; '
              f'P(non-monotonic at 127) {np.mean(out[:, 127] < -1):.3f}; '
              f'P(any DNL > +0.5 in codes 140..230) {np.mean((out[:, 140:230] > 0.5).any(1)):.3f}')
