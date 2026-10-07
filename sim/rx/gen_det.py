"""
Detector waveform for the baseband part of the whole-RX transient: one Gold
burst (code 0x5A, 127 chips x 104 us) after a 1.5 ms signal-free lead-in,
with the receiver's RF noise (NF 11 dB over 450 MHz, as the e2e model),
mapped to the log detector's output voltage.

Mapping: the 6-stage chain + log_det CW transfer (sim/logdet/transfer_cw.txt),
shifted by -3.8 dB so that the noise-only level matches the transistor-level
noise run (det = 1.439 V with the noise floor alone; see
sim/logdet/noise_tran_results.txt). Writes build/det_<level>.inc (a PWL
source 'Vdet det 0') and build/det_<level>.npz (chips, timing).

    python sim/rx/gen_det.py -94 -70
"""
import os
import sys

import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'bench'))
sys.path.insert(0, os.path.join(ROOT, 'model'))
import rx_model as rxm
from gold import gold

R = 1e6                  # detector samples per second (1 us blocks)
B_RF, NF_DB = 450e6, 11.0
SPC = 104                # samples per chip (1040 clocks at 10 MHz)
LEAD, TAIL = 1500, 500   # us
SHIFT_DB = -3.8
CODE = 0x5A


def det_curve():
    rows = np.loadtxt(os.path.join(ROOT, 'sim', 'logdet', 'transfer_cw.txt'), skiprows=1)
    return rows[:, 0], rows[:, 1]


def main(levels):
    chips = gold(CODE).astype(bool)
    on = np.concatenate([np.zeros(LEAD, bool), np.repeat(chips, SPC), np.zeros(TAIL, bool)])
    pin, vdet = det_curve()
    up = int(B_RF / R)
    for lvl in levels:
        rng = np.random.default_rng(42)
        p_w = 10 ** ((lvl - 30) / 10)
        n_var = rxm.KT * 10 ** (NF_DB / 10) * B_RF
        p = np.empty(len(on))
        for i in range(0, len(on), 1000):          # chunks: keep memory small
            seg = on[i:i + 1000]
            s = np.repeat(seg * np.sqrt(p_w), up).astype(np.complex64)
            x = s + (rng.standard_normal(len(s), dtype=np.float32) +
                     1j * rng.standard_normal(len(s), dtype=np.float32)) * np.float32(np.sqrt(n_var / 2))
            p[i:i + len(seg)] = rxm.block_mean(np.abs(x) ** 2, up)
        dbm = 10 * np.log10(p) + 30
        v = np.interp(dbm + SHIFT_DB, pin, vdet)
        t = np.arange(len(v)) / R
        with open(os.path.join(ROOT, 'build', f'det_{int(lvl)}.inc'), 'w') as fh:
            fh.write(f'* detector waveform, {lvl} dBm, code 0x{CODE:02X}, NF {NF_DB} dB / {B_RF/1e6:.0f} MHz\n')
            fh.write('Vdet det 0 pwl(\n')
            for k in range(0, len(t), 8):
                fh.write('+ ' + ' '.join(f'{t[j]:.6e} {v[j]:.6f}' for j in range(k, min(k + 8, len(t)))) + '\n')
            fh.write('+ )\n')
        np.savez(os.path.join(ROOT, 'build', f'det_{int(lvl)}.npz'), t=t, v=v, on=on, chips=chips,
                 lead=LEAD, spc=SPC)
        print(f'{lvl} dBm: det noise-only {np.median(v[:LEAD]):.4f} V, '
              f'on-chips {np.median(v[on]):.4f} V, off-chips {np.median(v[LEAD:-TAIL][~on[LEAD:-TAIL]]):.4f} V')


if __name__ == '__main__':
    main([float(a) for a in sys.argv[1:]] or [-94, -70])
