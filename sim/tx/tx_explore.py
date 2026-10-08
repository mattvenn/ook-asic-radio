"""
TX chain exploration (raw spice, before the xschem blocks): 433.92 MHz 1.8 V
square -> thin W9/3 inverter (same load the ring was calibrated with) ->
skewed level shifter (R2R DAC dac_drive core, NMOS x kn) -> identical
thick-oxide buffer taper on both latch nodes A/B (antiphase) -> final drivers
(N = wn um, P = 3 wn) -> pad_model (reversed: chip side 'mod' driven) x2 ->
73 ohm dipole between the pins.

Measures: duty cycle at A, B and the driver outputs; phase error between the
two arms (deg from 180); fundamental power into 73 ohm; H2/H3; supply currents.

    python sim/tx/tx_explore.py                     # kp sweep at tt
    python sim/tx/tx_explore.py ss 10 4 48 [f]      # one case: corner kn kp wn_final [f]
    python sim/tx/tx_explore.py ring tt ss ff       # real 23-stage ring, keyed on/off
"""
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from rawread import read_raw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'build', 'tx')
F0 = 433.92e6
PAD = open(os.path.join(ROOT, 'sim', 'tx', 'pad_model.spice')).read()

THICK_N = 'sky130_fd_pr__nfet_g5v0d10v5'
THICK_P = 'sky130_fd_pr__pfet_g5v0d10v5'


def inv_thick(name, a, y, wn, wp, nf=1):
    nf = max(1, int(round(wn / 10)))
    nfp = max(1, int(round(wp / 10)))
    return (f'X{name}n {y} {a} 0 0 {THICK_N} L=0.5 W={wn:.3g} nf={nf}\n'
            f'X{name}p {y} {a} VAPWR VAPWR {THICK_P} L=0.5 W={wp:.3g} nf={nfp}\n')


def ring_netlist(n, ton, toff, cw='3.2f'):
    """nand2_2 enable + n x inv_2 (std cells), cw wiring per stage (calibrated
    against the ttsky25b ring's extracted layout); output node 'ring'."""
    s = ['.include /foss/pdks/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice',
         f'Ven en 0 pwl(0 0 {ton:.4e} 0 {ton + 50e-12:.4e} 1.8 {toff:.4e} 1.8 {toff + 50e-12:.4e} 0)',
         f'Xr0 en r{n} 0 0 VDPWR VDPWR ring sky130_fd_sc_hd__nand2_2', f'Cr0 ring 0 {cw}']
    prev = 'ring'
    for i in range(1, n + 1):
        s += [f'Xr{i} {prev} 0 0 VDPWR VDPWR r{i} sky130_fd_sc_hd__inv_2', f'Cr{i} r{i} 0 {cw}']
        prev = f'r{i}'
    return '\n'.join(s)


def deck(corner, kn, wn_final, taper=4.0, f=F0, kp=1.0, name='txe', ring=0, ton=5e-9, toff=60e-9, tstop=None):
    per = 1 / f
    s = [f'* TX explore: corner {corner}, kn {kn}, final N {wn_final} um',
         f'.lib /foss/pdks/sky130A/libs.tech/combined/sky130.lib.spice {corner}',
         'VA VAPWR 0 3.3', 'VD VDPWR 0 1.8',
         (f'Vin ring 0 pulse(0 1.8 0.5n 60p 60p {per / 2 - 60e-12:.6e} {per:.6e})' if not ring else
          ring_netlist(ring, ton, toff)),
         # thin W9/3 inverter: the load the ring was calibrated against
         'Xi1p ctrl ring VDPWR VDPWR sky130_fd_pr__pfet_01v8 L=0.15 W=9 nf=1',
         'Xi1n ctrl ring 0 0 sky130_fd_pr__nfet_01v8 L=0.15 W=3 nf=1',
         # level shifter: ctrl_n inverter + skewed thick core
         'XM8 ctrl_n ctrl VDPWR VDPWR sky130_fd_pr__pfet_01v8_hvt L=0.15 W=1 nf=1',
         'XM7 ctrl_n ctrl 0 0 sky130_fd_pr__nfet_01v8 L=0.15 W=0.42 nf=1',
         f'XM9 A ctrl 0 0 {THICK_N} L=0.5 W={0.42 * kn:.3g} nf=1',
         f'XM10 B ctrl_n 0 0 {THICK_N} L=0.5 W={0.42 * kn:.3g} nf=1',
         f'XM11 A B VAPWR VAPWR {THICK_P} L=0.5 W={0.42 * kp:.3g} nf=1',
         f'XM12 B A VAPWR VAPWR {THICK_P} L=0.5 W={0.42 * kp:.3g} nf=1']
    # buffer taper from ~W 0.42/1.26 up to the final driver, identical on A and B
    sizes = []
    wn = 0.42
    while wn * taper < wn_final:
        sizes.append(wn)
        wn *= taper
    sizes.append(wn_final)
    if len(sizes) % 2:          # even number of inverters: drv_p in phase with A
        sizes.insert(0, 0.42)
    for side, node in (('p', 'A'), ('n', 'B')):
        prev = node
        for i, w in enumerate(sizes):
            y = f'drv_{side}' if i == len(sizes) - 1 else f'{side}{i}'
            s.append(inv_thick(f'b{side}{i}', prev, y, w, 3 * w).rstrip())
            prev = y
    s.append(PAD.rstrip())
    s += ['xpad_p 0 ant_p drv_p pad_model', 'xpad_n 0 ant_n drv_n pad_model',
          'Rdip ant_p dmid 73', 'Cdip dmid ant_n 100p',   # dipole: 73 ohm at RF, open at DC
          '.save v(A) v(B) v(drv_p) v(drv_n) v(ant_p) v(ant_n) i(VA) i(VD) v(ring)',
          '.options method=GEAR', '.control',
          (f'tran 2p {30 * per:.6e} {10 * per:.6e}' if not ring else f'tran 2p {tstop:.4e} 0'),
          f'meas tran pa avg i(VA)', 'meas tran pd avg i(VD)',
          'let ia = -pa * 1e3', 'let id = -pd * 1e3',
          'echo RESULT IA_mA $&ia ID_mA $&id',
          f'write {name}.raw',
          '.endc', '.end']
    return '\n'.join(s) + '\n'


def edges(t, y, th, rising):
    s = np.sign(y - th)
    idx = np.where((s[:-1] < 0) & (s[1:] >= 0))[0] if rising else np.where((s[:-1] > 0) & (s[1:] <= 0))[0]
    return t[idx] + (th - y[idx]) * (t[idx + 1] - t[idx]) / (y[idx + 1] - y[idx])


def duty(t, y, th):
    r, fa = edges(t, y, th, True), edges(t, y, th, False)
    per = np.mean(np.diff(r))
    hi = [fa[fa > x][0] - x for x in r[:-1] if (fa > x).any()]
    return 100 * np.mean(hi) / per, per


def analyse(name, f):
    v = read_raw(os.path.join(OUT, name + '.raw'))[0]['vars']
    t = np.real(v['time'])
    g = np.arange(t[0], t[-1], 1e-12)
    w = {k: np.interp(g, t, np.real(v[f'v({k})'])) for k in ('a', 'b', 'drv_p', 'drv_n', 'ant_p', 'ant_n')}
    dA, per = duty(g, w['a'], 1.65)
    dP, _ = duty(g, w['drv_p'], 1.65)
    dN, _ = duty(g, w['drv_n'], 1.65)
    # phase: drv_n relative to drv_p from the fundamental (lock-in)
    def ph(y):
        return np.angle(np.sum(y * np.exp(-2j * np.pi * f * g)))
    phase = np.degrees((ph(w['drv_n']) - ph(w['drv_p'])) % (2 * np.pi))
    vd = w['ant_p'] - w['ant_n']
    n = int(round((g[-1] - g[0]) * f)) / f
    m = g < g[0] + n
    harm = [2 * np.abs(np.sum(vd[m] * np.exp(-2j * np.pi * k * f * g[m]))) / m.sum() for k in (1, 2, 3)]
    pdbm = 10 * np.log10(harm[0] ** 2 / (2 * 73) / 1e-3)
    return dict(dA=dA, dP=dP, dN=dN, phase=phase, pdbm=pdbm,
                h2=20 * np.log10(harm[1] / harm[0]), h3=20 * np.log10(harm[2] / harm[0]))


def run(corner, kn, wn_final, f=F0, kp=1.0):
    name = f'txe_{corner}_{kn}_{kp:g}_{wn_final}_{int(f / 1e6)}'
    with open(os.path.join(OUT, name + '.spice'), 'w') as fh:
        fh.write(deck(corner, kn, wn_final, f=f, kp=kp, name=name))
    r = subprocess.run([os.path.join(ROOT, 'tools', 'osic'), 'bash', '-c',
                        f'cd build/tx && ngspice -b {name}.spice'], capture_output=True, text=True,
                       cwd=ROOT)
    res = {}
    for line in r.stdout.splitlines():
        if line.startswith('RESULT'):
            p = line.split()[1:]
            res = {p[i]: p[i + 1] for i in range(0, len(p) - 1, 2)}
    try:
        m = analyse(name, f)
    except Exception as e:                       # noqa: BLE001
        print(f'{name}: analysis failed: {e}')
        return
    print(f'{corner} kn={kn:2g} kp={kp:3g} N={wn_final:3d}um f={f / 1e6:4.0f}MHz  P73={m["pdbm"]:6.2f} dBm  '
          f'H2 {m["h2"]:6.1f} H3 {m["h3"]:6.1f} dBc  duty A {m["dA"]:5.1f} drv_p {m["dP"]:5.1f} '
          f'drv_n {m["dN"]:5.1f} %  arm phase {m["phase"]:6.1f} deg  IA {res.get("IA_mA", "?")[:5]} mA',
          flush=True)


def ring_metrics(v, ton, toff, drv=('drv_p', 'drv_n')):
    """Keyed-ring run (raw vars): frequency, power into the dipole, on/off
    times, supply currents. drv = the two arm nodes (frequency from drv[0])."""
    t = np.real(v['time'])
    g = np.arange(t[0], t[-1], 1e-12)
    w = {k: np.interp(g, t, np.real(v[f'v({k})'])) for k in (drv[0], drv[1], 'ant_p', 'ant_n')}
    ia = np.interp(g, t, -np.real(v['i(va)'])) * 1e3
    idd = np.interp(g, t, -np.real(v['i(vd)'])) * 1e3
    vd = w['ant_p'] - w['ant_n']
    r = edges(g, w[drv[0]], 1.65, True)
    on = r[(r > ton + 20e-9) & (r < toff)]
    fr = (len(on) - 1) / (on[-1] - on[0])
    # steady window: 20 ns after enable to toff
    m = (g > ton + 20e-9) & (g < toff)
    n_c = int((g[m][-1] - g[m][0]) * fr)
    m2 = m & (g < g[m][0] + n_c / fr)
    a1 = 2 * np.abs(np.sum(vd[m2] * np.exp(-2j * np.pi * fr * g[m2]))) / m2.sum()
    pdbm = 10 * np.log10(a1 ** 2 / (2 * 73) / 1e-3)
    # envelope: peak |vd| per period
    env_t = np.arange(0, g[-1], 1 / fr)
    # RF envelope: half peak-to-peak per period (the DC across the dipole's series C doesn't count)
    env = np.array([np.ptp(vd[(g >= a) & (g < a + 1 / fr)]) / 2 if ((g >= a) & (g < a + 1 / fr)).any()
                    else 0 for a in env_t])
    full = np.median(env[(env_t > ton + 20e-9) & (env_t < toff - 2e-9)])
    t90 = env_t[(env_t > ton) & (env >= 0.9 * full)][0] - ton
    after = (env_t > toff) & (env <= 0.1 * full)
    t10 = env_t[after][0] - toff if after.any() else float('nan')
    i_on = lambda x: np.mean(x[m])
    i_off = lambda x: np.mean(x[(g > 1e-9) & (g < ton)])
    return dict(g=g, vd=vd, ia=ia, idd=idd, f=fr, pdbm=pdbm, t90=t90, t10=t10, ia_off=i_off(ia), ia_on=i_on(ia),
                id_off=i_off(idd), id_on=i_on(idd))


def fmt_ring(m):
    return (f'f = {m["f"] / 1e6:6.1f} MHz (x0.866 -> {0.866 * m["f"] / 1e6:5.1f} on silicon), '
            f'P73 {m["pdbm"]:5.2f} dBm, on in {m["t90"] * 1e9:4.1f} ns, off in {m["t10"] * 1e9:4.1f} ns, '
            f'VAPWR {m["ia_off"]:5.2f} -> {m["ia_on"]:5.2f} mA, VDPWR {m["id_off"]:5.2f} -> {m["id_on"]:5.2f} mA')


def run_ring(corner, n=22, kn=10, kp=4, wn_final=48, ton=5e-9, toff=60e-9, tstop=80e-9):
    """Step 3+4: real ring, keyed. Frequency, power, currents, on/off times."""
    name = f'txr_{corner}_{n}'
    with open(os.path.join(OUT, name + '.spice'), 'w') as fh:
        fh.write(deck(corner, kn, wn_final, kp=kp, name=name, ring=n, ton=ton, toff=toff, tstop=tstop))
    subprocess.run([os.path.join(ROOT, 'tools', 'osic'), 'bash', '-c',
                    f'cd build/tx && ngspice -b {name}.spice > {name}.log 2>&1'], cwd=ROOT)
    m = ring_metrics(read_raw(os.path.join(OUT, name + '.raw'))[0]['vars'], ton, toff)
    print(f'{corner} ring {n}+1 stages: ' + fmt_ring(m), flush=True)
    return m


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    args = sys.argv[1:]
    if args and args[0] == 'ring':           # ring <corner...>
        for c in args[1:] or ['tt']:
            run_ring(c)
    elif args:                                  # corner kn kp wn [f]
        run(args[0], float(args[1]), int(args[3]), float(args[4]) if len(args) > 4 else F0, float(args[2]))
    else:
        for kp in (1, 2, 4, 8):
            run('tt', 10, 48, kp=kp)
