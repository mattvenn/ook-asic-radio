"""
Baseline: ring oscillator straight into the scope.

    python bench/baseline.py probe     # 10x passive probe, CH1 at 1M
    python bench/baseline.py coax      # 50 ohm coax lead, CH1 at 50R

Saves bench/data/baseline_<lead>_<time>.npz and .png.
"""
import os
import sys
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from scope import Scope
import rf

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


def main(lead):
    os.makedirs(DATA, exist_ok=True)
    sc = Scope()
    print(sc.idn)
    fifty = lead == 'coax'
    if fifty and sc.probe_atten(1) != 1:
        sys.exit('CH1 reports a probe attached; remove it before using 50 ohm')
    sc.setup_channel(1, scale=0.2, fifty=fifty)
    r = sc.autorange(1)
    if r:
        print(f'DC {r[0]*1e3:.1f} mV ({r[0]/50*1e3:.2f} mA into 50R)' if fifty else f'DC {r[0]*1e3:.1f} mV')
    m = sc.measure(1)
    print(f"scope meas: freq={m['FREQ']} Vpp={m['VPP']} Vrms={m['VRMS']}")

    t, v, fs = sc.capture(1, duration=2e-6)
    print(f'captured {len(v)} pts at {fs/1e9:.2f} GSa/s')
    f, dbm = rf.spectrum_dbm(v, fs)
    f0, p0 = rf.peak(f, dbm, 50e6, 1e9)
    print(f'fundamental {f0/1e6:.2f} MHz', end='')
    if fifty:
        print(f'  {p0:.1f} dBm into 50R ({rf.dbm_to_vpp(p0)*1e3:.0f} mVpp sine-equivalent)')
        for h in (2, 3, 4, 5):
            if h * f0 < fs / 2:
                fh, ph = rf.peak(f, dbm, h * f0 * 0.97, h * f0 * 1.03)
                print(f'  H{h} {fh/1e6:.1f} MHz {ph:.1f} dBm ({ph-p0:.1f} dBc)')
    else:
        print('  (1M probe: level in dBm not meaningful)')

    stamp = time.strftime('%Y%m%d_%H%M%S')
    base = os.path.join(DATA, f'baseline_{lead}_{stamp}')
    np.savez(base + '.npz', t=t, v=v, fs=fs, lead=lead, meas=str(m))

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 7))
    n = int(20e-9 * fs)
    a1.plot(t[:n] * 1e9, v[:n] * 1e3)
    a1.set_xlabel('ns'); a1.set_ylabel('mV'); a1.grid()
    a1.set_title(f'ring osc baseline ({lead}) {f0/1e6:.1f} MHz')
    a2.plot(f / 1e6, dbm)
    a2.set_xlim(0, 1500); a2.set_ylim(dbm.max() - 100, dbm.max() + 5)
    a2.set_xlabel('MHz'); a2.set_ylabel('dBm (50R)' if fifty else 'dB (rel)'); a2.grid()
    fig.tight_layout(); fig.savefig(base + '.png', dpi=110)
    print('saved', base + '.{npz,png}')
    sc.close()


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'probe')
