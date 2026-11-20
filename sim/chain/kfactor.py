#!/usr/bin/env python3
"""(A5) Rollett stability factor of the chain as a differential two-port, 10 MHz - 5 GHz.

Port 1 is the differential input, port 2 the differential output (out_p - out_n, with the 50 fF Cload each side
kept as part of the two-port). Two AC runs inject a differential test current (+I into the p node, -I out of the
n node) at port 1, then at port 2, with the other port open, giving the differential Z parameters:
z11 = Vd1/I1, z21 = Vd2/I1, z12 = Vd1/I2, z22 = Vd2/I2. Then
  K = (2 Re z11 Re z22 - Re(z12 z21)) / |z12 z21|   (the same K as from S or Y: it doesn't depend on the immittance
                                                     or reference impedance)
and, from S at Z0 = 100 ohm differential, |Delta| = |S11 S22 - S12 S21| and Edwards' mu = (1 - |S11|^2) /
(|S22 - Delta conj(S11)| + |S12 S21|). Unconditionally stable for any passive source and load: K > 1 and
|Delta| < 1 (equivalently mu > 1).
Port 1 'ant': at the board side of the two pad models (ant_p / ant_n; the pad / ESD / mux model is inside the
two-port, the 36.5 ohm antenna resistors removed). Port 1 'pad': at the chip pins pad_p / pad_n (pad models
removed). The common mode is left open (1 GOhm to ground for DC) at port 1. Supply as stability.sh: 2 nH, real
decap. No Ccpl.

usage: python3 sim/chain/kfactor.py [--chain sch|pex]   -> build/stab_ac/kfactor_<chain>.json + table
"""
import argparse, json, os, re, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import stab_deck as sd

CORNERS = [('tt', 27, 1.8), ('ss', 10, 1.8), ('sf', 27, 1.8), ('ff', 50, 1.8), ('ss', 10, 1.89)]
OUT = os.path.join(sd.REPO, 'build/stab_ac')


def deck(chain, corner, temp, vsup, vglo, port1):
    s = sd.base_deck(chain, corner, temp, vsup, vglo)
    s = re.sub(r'^Rant_([pn]) ant_([pn]) emf_([pn]) .*$', r'Rant_\1 ant_\2 emf_\3 1G', s, flags=re.M)
    if port1 == 'pad':
        s = re.sub(r'^xpad_([pn]) .*$', r'Rdc_\1 pad_\1 GND 1G', s, flags=re.M)
        p, n = 'pad_p', 'pad_n'
    else:
        p, n = 'ant_p', 'ant_n'
    s += f"""I1p GND {p} dc 0 ac 1
I1n GND {n} dc 0 ac 1 180
I2p GND out_p dc 0 ac 0
I2n GND out_n dc 0 ac 0 180
.options method=GEAR
.control
op
ac dec 100 10meg 5g
let v1 = v({p}) - v({n})
let v2 = v(out_p) - v(out_n)
wrdata port1.txt v1 v2
alter @i1p[acmag]=0
alter @i1n[acmag]=0
alter @i2p[acmag]=1
alter @i2n[acmag]=1
ac dec 100 10meg 5g
let v1 = v({p}) - v({n})
let v2 = v(out_p) - v(out_n)
wrdata port2.txt v1 v2
.endc
.end
"""
    return s


def cplx(rows):
    a = np.array(rows)   # wrdata of two vectors: f re im f re im
    return a[:, 0], a[:, 1] + 1j * a[:, 2], a[:, 4] + 1j * a[:, 5]


def one(chain, corner, temp, vsup, vglo, port1):
    log = sd.run(deck(chain, corner, temp, vsup, vglo, port1))
    f, z11, z21 = cplx(sd.wrfile(log, 'port1.txt'))
    _, z12, z22 = cplx(sd.wrfile(log, 'port2.txt'))
    p = z12 * z21
    K = (2 * z11.real * z22.real - p.real) / np.abs(p)
    Z0 = 100.0
    D = (z11 + Z0) * (z22 + Z0) - p
    s11 = ((z11 - Z0) * (z22 + Z0) - p) / D
    s22 = ((z11 + Z0) * (z22 - Z0) - p) / D
    s12 = 2 * z12 * Z0 / D
    s21 = 2 * z21 * Z0 / D
    dl = s11 * s22 - s12 * s21
    mu = (1 - np.abs(s11) ** 2) / (np.abs(s22 - dl * np.conj(s11)) + np.abs(s12 * s21))
    i = K.argmin()
    r = dict(chain=chain, corner=corner, temp=temp, vsup=vsup, vglo=vglo, port1=port1, warn=sd.check_op(log),
             Kmin=float(K[i]), f_Kmin=float(f[i]), K_below1_MHz=[float(x / 1e6) for x in f[K < 1]],
             absDelta_max=float(np.abs(dl).max()), mu_min=float(mu.min()), f_mumin=float(f[mu.argmin()]),
             Re_z11_min=float(z11.real.min()), Re_z22_min=float(z22.real.min()),
             s21_434_dB=float(20 * np.log10(np.abs(np.interp(433.92e6, f, s21.real) +
                                                   1j * np.interp(433.92e6, f, s21.imag)))),
             s12_max_dB=float(20 * np.log10(np.abs(s12).max())))
    np.save(os.path.join(OUT, f'K_{chain}_{corner}{temp}_{vsup}_{vglo}_{port1}.npy'), np.c_[f, K, mu, np.abs(dl)])
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chain', default='sch')
    ap.add_argument('--jobs', type=int, default=20)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    cases = [(a.chain, *k, v, p) for k in CORNERS for v in (1.8, 0) for p in ('ant', 'pad')]
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda x: one(*x), cases))
    json.dump(res, open(os.path.join(OUT, f'kfactor_{a.chain}.json'), 'w'), indent=1)
    for r in res:
        print(f"{r['chain']} {r['corner']} {r['temp']} {r['vsup']} {'full' if r['vglo'] else 'low'} port1={r['port1']}: "
              f"Kmin {r['Kmin']:.3g} @ {r['f_Kmin'] / 1e6:.0f} MHz, K<1 at {len(r['K_below1_MHz'])} pts, "
              f"|D|max {r['absDelta_max']:.3g}, mu_min {r['mu_min']:.3g} @ {r['f_mumin'] / 1e6:.0f}, "
              f"Re z11/z22 min {r['Re_z11_min']:.3g}/{r['Re_z22_min']:.3g}, S21(434) {r['s21_434_dB']:.1f} dB, "
              f"S12max {r['s12_max_dB']:.1f} dB {r['warn']}")


if __name__ == '__main__':
    main()
