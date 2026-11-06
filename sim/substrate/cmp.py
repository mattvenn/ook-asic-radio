# Compare complex AC gains: H_x / H_ref - 1, and the equivalent Ccpl from a Ccpl calibration deck.
#   python3 cmp.py <ref.ac.txt> <cal_ref.ac.txt> <cal.ac.txt> <cal_C_fF> <x.ac.txt> [...]
# ref: the same circuit without the effect (e.g. the cut network); cal_ref / cal: case a without / with Ccpl.
import sys, math, cmath
def load(p):
    d = {}
    for ln in open(p):
        f = ln.split()
        if len(f) >= 3: d[round(float(f[0]))] = complex(float(f[1]), float(f[2]))
    return d
ref, cref, cal, cc = load(sys.argv[1]), load(sys.argv[2]), load(sys.argv[3]), float(sys.argv[4])
fs = sorted(ref)
f434 = min(fs, key=lambda f: abs(f - 433.92e6))
fpk = max(fs, key=lambda f: abs(ref[f]))
for p in sys.argv[5:]:
    x = load(p)
    def at(f):
        dx = x[f] / ref[f] - 1; dc = cal[f] / cref[f] - 1
        eq = cc * dx / dc
        return dx, dc, eq
    print(p)
    for lab, f in (('434M', f434), ('peak', fpk)):
        dx, dc, eq = at(f)
        print(f'  {lab} {f / 1e6:7.1f} MHz: |H_ref| {20 * math.log10(abs(ref[f])):.4f} dB; H_x/H_ref-1 = {abs(dx):.3e} @ {math.degrees(cmath.phase(dx)):6.1f} deg '
              f'({20 * math.log10(abs(1 + dx)):+.4f} dB); Ccpl {cc}f gives {abs(dc):.3e} @ {math.degrees(cmath.phase(dc)):6.1f} deg; '
              f'equivalent Ccpl = {abs(eq):.3g} fF (in-phase part {eq.real:+.3g} fF)')
    eqs = [abs(at(f)[2]) for f in fs if 2e8 < f < 1e9]
    print(f'  max |equivalent Ccpl| over 200 MHz - 1 GHz: {max(eqs):.3g} fF')
