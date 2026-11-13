#!/usr/bin/env python3
"""Markdown tables for docs/stability_ac_2026-11.md from build/stab_ac/*.json (stability_ac.py, kick_edge.py,
kfactor.py, rcload.py, stability_bond.py). usage: python3 sim/chain/stab_tables.py [a|b|c]"""
import json, math, os, sys
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'build/stab_ac')


def load(n):
    p = os.path.join(OUT, n)
    return json.load(open(p)) if os.path.exists(p) else []


def corner_name(r):
    v = '' if r['vsup'] == 1.8 else f" {r['vsup']} V"
    return f"{r['corner']} {r['temp']} °C{v}"


def table_a():
    rows = []
    kick = {c: {(k['corner'], k['temp'], k['vsup'], k['vglo'], k['node']): k for k in load(f'kick_{c}.json')}
            for c in ('sch', 'pex')}
    ac = {c: {(r['corner'], r['temp'], r['vsup'], r['vglo'], r['node']): r for r in load(f'ac_{c}.json')
              if r['C'] == '1f'} for c in ('sch', 'pex')}
    ac01 = {c: {(r['corner'], r['temp'], r['vsup'], r['vglo'], r['node']): r for r in load(f'ac_{c}.json')
                if r['C'] == '0.1f'} for c in ('sch', 'pex')}
    print('| Corner | Strap | Node | Gain at 434 MHz, sch / pex (dB) | Ccpl_crit AC, sch (fF) | Kick edge, sch (fF) | '
          'Margin at 0.1 fF, sch (dB) | f, sch (MHz) | Ccpl_crit AC, pex (fF) | Kick edge, pex (fF) | '
          'Margin at 0.1 fF, pex (dB) | f, pex (MHz) |')
    print('|' + '---|' * 12)
    lin = []
    for key, s in ac['sch'].items():
        p = ac['pex'].get(key)
        ks, kp = kick['sch'].get(key), kick['pex'].get(key)
        fmt_k = lambda k: '–' if not k else (f"{k['ok']:.3g}–{k['osc']:.3g}" if k['osc'] else f"> {k['ok']:.3g}")
        m = lambda r: f"{r['GM_dB']:.1f}" if r else '–'
        a01s, a01p = ac01['sch'].get(key), ac01['pex'].get(key)
        for a1, a0 in ((s, a01s), (p, a01p)):
            if a1 and a0:
                lin.append(abs(a1['Ccpl_crit_fF'] / a0['Ccpl_crit_fF'] - 1))
        print(f"| {corner_name(s)} | {'full' if s['vglo'] else 'low'} | {s['node']} | {s['gain434_dB']:.1f} / "
              f"{p['gain434_dB']:.1f} | {s['Ccpl_crit_fF']:.3f} | {fmt_k(ks)} | {m(a01s)} | {s['f_GM'] / 1e6:.0f} | "
              f"{p['Ccpl_crit_fF']:.3f} | {fmt_k(kp)} | {m(a01p)} | {p['f_GM'] / 1e6:.0f} |" if p else '')
    print(f'\nCcpl_crit from the 0.1 fF and 1 fF runs differ by at most {100 * max(lin):.1f} %.\n')
    print('| Chain | Corner | Strap | K min (port 1 at the board side) | K min (port 1 at the pins) | f of K min (MHz) | '
          '\\|Δ\\| max | μ min | \\|S12\\| max (dB) |')
    print('|' + '---|' * 9)
    for c in ('sch', 'pex'):
        rs = load(f'kfactor_{c}.json')
        for r in rs:
            if r['port1'] != 'ant':
                continue
            q = [x for x in rs if x['port1'] == 'pad' and all(x[k] == r[k] for k in ('corner', 'temp', 'vsup', 'vglo'))][0]
            print(f"| {c} | {corner_name(r)} | {'full' if r['vglo'] else 'low'} | {r['Kmin']:.3g} | {q['Kmin']:.3g} | "
                  f"{r['f_Kmin'] / 1e6:.0f} / {q['f_Kmin'] / 1e6:.0f} | {max(r['absDelta_max'], q['absDelta_max']):.3f} | "
                  f"{min(r['mu_min'], q['mu_min']):.3f} | {max(r['s12_max_dB'], q['s12_max_dB']):.0f} |")


def table_b():
    ro = load('rcload_rolloff_sch.json')
    print('| Corner | Strap | Gain at 434 MHz (dB) | −20 dB at (MHz) | −40 dB at (MHz) | Stage upper −3 dB edges, 1–6 (MHz) | '
          'Stage gain peaks, 1–6 (MHz) | NF at 448 MHz (dB) |')
    print('|' + '---|' * 8)
    for r in ro:
        e = ', '.join(f"{s['f3dB_up'] / 1e6:.0f}" if s['f3dB_up'] else '–' for s in r['stages'])
        pk = ', '.join(f"{s['f_peak'] / 1e6:.0f}" for s in r['stages'])
        print(f"| {r['corner']} {r['temp']} °C | {'full' if r['vglo'] else 'low'} | {r['g434']:.2f} | "
              f"{r['f_minus20'] / 1e6:.0f} | {r['f_minus40'] / 1e6:.0f} | {e} | {pk} | {r['nf448']:.2f} |")
    sw = load('rcload_sweep_sch.json')
    base = {r['corner']: r for r in sw if r['variant'] == 'none' and r['vglo'] == 1.8}
    print('\n| Variant | Pole (GHz) | Cl per side, stage 1 / 2–6 (fF) | tt: ΔG 448 / 560 (dB) | ss 10 °C: ΔG 448 / 560 (dB) | '
          'ΔNF 448 (dB) | Ccpl_crit ×, tt pad_p / o1p | Ccpl_crit ×, ss 10 °C pad_p / o1p | Meets 0.5 / 1 dB |')
    print('|' + '---|' * 9)
    for v in ('all', 'last3', 'last2', 's1'):
        for fp in sorted({r['fpole'] for r in sw if r['variant'] == v}):
            t = [r for r in sw if r['variant'] == v and r['fpole'] == fp and r['corner'] == 'tt'][0]
            s = [r for r in sw if r['variant'] == v and r['fpole'] == fp and r['corner'] == 'ss'][0]
            bt, bs = base['tt'], base['ss']
            d = lambda r, b, k: r[k] - b[k]
            ok = all(d(r, b, 'g448') >= -0.5 and d(r, b, 'g560') >= -1 for r, b in ((t, bt), (s, bs)))
            c1 = f"{1e15 / (2 * math.pi * 1e3 * fp):.0f}" if v in ('all', 's1') else '–'
            c2 = f"{1e15 / (2 * math.pi * 4e3 * fp):.0f}" if v != 's1' else '–'
            print(f"| {v} | {fp / 1e9:.1f} | {c1} / {c2} | {d(t, bt, 'g448'):+.2f} / {d(t, bt, 'g560'):+.2f} | "
                  f"{d(s, bs, 'g448'):+.2f} / {d(s, bs, 'g560'):+.2f} | {d(t, bt, 'nf448'):+.2f} | "
                  f"{t['crit_pad_p'] / bt['crit_pad_p']:.2f} / {t['crit_o1p'] / bt['crit_o1p']:.2f} | "
                  f"{s['crit_pad_p'] / bs['crit_pad_p']:.2f} / {s['crit_o1p'] / bs['crit_o1p']:.2f} | {'yes' if ok else 'no'} |")


def table_c():
    rs = load('bond_ac_sch.json')
    print('| Corner | Strap | L = Lb | k_crit, any aggressor and pattern |')
    print('|---|---|---|---|')
    seen = set()
    for r in rs:
        key = (r['corner'], r['temp'], r['vsup'], r['vglo'], r['L'])
        if key in seen:
            continue
        seen.add(key)
        g = [x for x in rs if (x['corner'], x['temp'], x['vsup'], x['vglo'], x['L']) == key and x['k_crit']]
        ks = 'none (no real k at any frequency)' if not g else f"{min(abs(x['k_crit']) for x in g):.3g}"
        print(f"| {corner_name(r)} | {'full' if r['vglo'] else 'low'} | {r['L']} | {ks} |")
    cb = load('bond_combined_sch.json')
    print('\n| Corner | L = Lb | Node | Ccpl_crit, k = 0 (fF) | Worst with \\|k\\| ≤ 0.3 (fF) | Change | Worst case | '
          'Margin at 0.1 fF (dB) |')
    print('|' + '---|' * 8)
    for c in ('ss', 'tt'):
        for L in ('2n', '5n'):
            for n in ('pad_p', 'o1p'):
                s = [x for x in cb if x['corner'] == c and x['L'] == L and x['node'] == n]
                b = [x for x in s if x['k'] == 0][0]['Ccpl_crit_fF']
                w = min(s, key=lambda x: x['Ccpl_crit_fF'])
                print(f"| {c} {s[0]['temp']} °C | {L} | {n} | {b:.3f} | {w['Ccpl_crit_fF']:.3f} | "
                      f"{100 * (w['Ccpl_crit_fF'] / b - 1):+.1f} % | {w['agg']}, k {w['sign'] * w['k']:+.1f} | "
                      f"{20 * math.log10(w['Ccpl_crit_fF'] / 0.1):.1f} |")
    cu = load('bond_current_sch.json')
    print('\n| Corner | Strap | L | Input (dBm) | Out diff at 434 MHz (mV amplitude) | I(Lsup) 434 / 868 MHz (µA) | '
          'I(Lgnd) 434 / 868 MHz (µA) |')
    print('|' + '---|' * 7)
    for r in cu:
        print(f"| {r['corner']} {r['temp']} °C | {'full' if r['vglo'] else 'low'} | {r['L']} | {r['P_dBm']} | "
              f"{r['vod_h1'] * 1e3:.0f} | {r['isup_h1'] * 1e6:.2f} / {r['isup_h2'] * 1e6:.1f} | "
              f"{r['ignd_h1'] * 1e6:.2f} / {r['ignd_h2'] * 1e6:.1f} |")


if __name__ == '__main__':
    for x in (sys.argv[1:] or ['a', 'b', 'c']):
        {'a': table_a, 'b': table_b, 'c': table_c}[x]()
        print()
