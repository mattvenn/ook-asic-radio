"""Tidy magic's extracted netlist into a drop-in replacement for the schematic subckt.

    python3 layout/pexfix.py <magic.spice> <schematic.spice> <out.spice>

- ports reordered to the schematic's .subckt line (instances connect by position);
- the substrate node (VSUBS) and any other extra port become internal nodes tied
  to VSS by renaming (so substrate C goes to VSS);
- prints a summary (devices, R, C, total C per port).
"""
import re
import sys
from collections import defaultdict


def logical_lines(text):
    out = []
    for ln in text.splitlines():
        if ln.startswith('+') and out:
            out[-1] += ' ' + ln[1:].strip()
        else:
            out.append(ln)
    return out


def main(raw, sch, dst):
    sport = None
    for ln in logical_lines(open(sch).read()):
        if ln.lower().startswith('.subckt'):
            t = ln.split()
            name, sport = t[1], [p for p in t[2:] if '=' not in p]
            break
    lines = logical_lines(open(raw).read())
    body, lports, lname = [], None, None
    for ln in lines:
        if ln.lower().startswith('.subckt'):
            t = ln.split()
            lname, lports = t[1], t[2:]
        elif ln.lower().startswith('.ends'):
            pass
        elif lports is not None:
            body.append(ln)
    missing = [p for p in sport if p not in lports]
    if missing:
        sys.exit(f'ports missing in layout: {missing} (layout ports {lports})')
    extra = [p for p in lports if p not in sport]
    ren = {p: 'VSS' for p in extra if p.upper() in ('VSUBS', 'SUB', 'VSUB')}
    other = [p for p in extra if p not in ren]
    if other:
        print('note: extra layout ports left internal:', other)

    def fix(ln):
        if not ln or ln[0] in '*.':
            return ln
        return ' '.join(ren.get(tok, tok) for tok in ln.split())
    body = [fix(ln) for ln in body if ln.strip()]

    nd = sum(1 for ln in body if ln[0] in 'Xx' or ln[0] in 'Mm')
    caps = [ln for ln in body if ln[0] in 'Cc']
    ress = [ln for ln in body if ln[0] in 'Rr']

    def val(s):
        m = re.match(r'([0-9.eE+-]+)\s*([a-zA-Z]*)', s)
        x = float(m.group(1))
        u = m.group(2).lower()
        return x * {'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'm': 1e-3, 'k': 1e3, '': 1}.get(u[:1], 1)
    ctot = defaultdict(float)
    for ln in caps:
        t = ln.split()
        c = val(t[3])
        ctot[t[1]] += c
        ctot[t[2]] += c
    with open(dst, 'w') as fh:
        fh.write(f'* {name}: magic R+C extraction of layout/{name}.gds (layout/pex.sh)\n')
        fh.write(f'.subckt {name} {" ".join(sport)}\n')
        fh.write('\n'.join(body) + '\n.ends\n')
    print(f'{dst}: {nd} devices, {len(ress)} R, {len(caps)} C ({sum(val(l.split()[3]) for l in caps) * 1e15:.1f} fF)')
    print('  C per port node: ' + ', '.join(f'{p} {ctot.get(p, 0) * 1e15:.1f} fF' for p in sport))


if __name__ == '__main__':
    main(*sys.argv[1:4])
