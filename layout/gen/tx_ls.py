# tx_ls layouts: 1.8 -> 3.3 V level shifter (xschem/gen/tx.py:tx_ls), two variants:
#   tx_ls     kn=14 kp=8 wpi=9 wni=3   (ring -> arms; the input inverter is the ring's load)
#   tx_ls_en  kn=1  kp=1 wpi=1 wni=0.42 (the two arm enables)
# in -> thin inverter (wpi/wni) -> ctrl -> thin inverter (hvt P 4, N 1.68) -> ctrl_n;
# thick core: NMOS pull-downs (0.42 kn; ctrl -> A, ctrl_n -> B), cross-coupled PMOS (0.42 kp).
# Built with rows.py: LV column (thin, VDD = VDPWR) on the left, HV column (thick,
# VAPWR) on the right; VSS along the bottom. in on the left edge, A / B on the right.
# Also writes layout/ref/<variant>.spice (LVS/PEX references, parameters substituted).
# Run: tools/osic klayout -b -r layout/gen/tx_ls.py
import os
import re
import subprocess
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lay import Block, Fet, REPO          # noqa: E402
from rows import Dev, Net, build, inverter_roles   # noqa: E402

VARIANTS = {'tx_ls': dict(kn=14, kp=8, wpi=9, wni=3), 'tx_ls_en': dict(kn=1, kp=1, wpi=1, wni=0.42)}
NETS = {'in': Net(io='L'), 'ctrl': Net(), 'ctrl_n': Net(), 'A': Net(io='R'), 'B': Net(io='R')}


def make(name, kn, kp, wpi, wni):
    b = Block(name)

    def dev(kind, W, l, vt, gate_net, drain, rail, nfmax):
        f = Fet(b, kind, W, l, gate='bottom' if kind == 'p' else 'top', vt=vt, bulk='None', nfmax=nfmax)
        return Dev(f, inverter_roles(f), [(gate_net, list(range(f.nf)))], drain, rail=rail)
    P = [dev('p', wpi, 0.15, '', 'in', 'ctrl', 'VDD', 3.0),          # Mi1p
         dev('p', 4.0, 0.15, 'hvt', 'ctrl', 'ctrl_n', 'VDD', 3.0),   # M8
         dev('p', 0.42 * kp, 0.5, 'g5', 'B', 'A', 'VAPWR', 3.0),     # M11
         dev('p', 0.42 * kp, 0.5, 'g5', 'A', 'B', 'VAPWR', 3.0)]     # M12
    N = [dev('n', wni, 0.15, '', 'in', 'ctrl', 'VSS', 3.0),          # Mi1n
         dev('n', 1.68, 0.15, '', 'ctrl', 'ctrl_n', 'VSS', 3.0),     # M7
         dev('n', 0.42 * kn, 0.5, 'g5', 'ctrl', 'A', 'VSS', 4.5),    # M9
         dev('n', 0.42 * kn, 0.5, 'g5', 'ctrl_n', 'B', 'VSS', 4.5)]  # M10
    return build(b, P, N, NETS, rail_h=2.0)


def write_ref(name, params):
    """LVS/PEX reference for a parameter variant: the xschem tx_ls netlist with the
    parameters substituted into W, renamed to the variant."""
    tmp = os.path.join(REPO, 'build', 'lay', 'ref')
    os.makedirs(tmp, exist_ok=True)
    subprocess.run(['xschem', '-n', '-s', '-q', '--tcl', 'set top_subckt 1; set lvs_netlist 1', '-o', tmp,
                    'xschem/tx_ls.sch'], cwd=REPO, capture_output=True)
    src = open(os.path.join(tmp, 'tx_ls.spice')).read()
    out = []
    for ln in src.splitlines():
        if ln.startswith('.subckt tx_ls'):
            ln = re.sub(r'\s+\w+=\S+', '', ln).replace('.subckt tx_ls', f'.subckt {name}')
        ln = re.sub(r"W='([^']+)'", lambda m: f'W={eval(m.group(1), {}, dict(params)):g}', ln)
        out.append(ln)
    os.makedirs(os.path.join(REPO, 'layout', 'ref'), exist_ok=True)
    with open(os.path.join(REPO, 'layout', 'ref', name + '.spice'), 'w') as fh:
        fh.write(f'* {name}: xschem/tx_ls.sch with {params} (layout/gen/tx_ls.py)\n' + '\n'.join(out) + '\n')


if __name__ == '__main__':
    for name, prm in VARIANTS.items():
        make(name, **prm).write(os.path.join(REPO, 'layout', name + '.gds'), flatten=True)
        write_ref(name, prm)          # also the main variant: netgen can't evaluate W='0.42*kn'
