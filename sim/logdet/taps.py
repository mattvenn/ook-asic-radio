"""Successive detection, tap by tap: tb_logdet (dipole -> pad -> lna_chain -> log_det) with a
0 V probe in series with each det_cell's drain, so each cell's current is seen separately.

For a 434 MHz tone swept over available power, records per level:
  - each tap's differential amplitude (o1..o5, out), peak, over 500-600 ns;
  - each cell's average drain current (into det) over 500-600 ns;
  - det (average).
Writes sim/logdet/taps.txt and sim/plots/logdet_taps.png.

    python sim/logdet/taps.py [corner]        (OSIC=$PWD/tools/osic-mac on the Mac)
    python sim/logdet/taps.py --plot          (re-plot from taps.txt)
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
B = os.path.join(ROOT, 'build', 'taps')
OSIC = os.environ.get('OSIC', os.path.join(ROOT, 'tools', 'osic'))
TXT = os.path.join(HERE, 'taps.txt')
PNG = os.path.join(ROOT, 'sim', 'plots', 'logdet_taps.png')
LEVELS = [x / 2 for x in range(-220, 1, 5)]   # -110 .. 0 dBm, 2.5 dB steps
TAPS = ['o1', 'o2', 'o3', 'o4', 'o5', 'out']


def deck(corner):
    subprocess.run([OSIC, 'bash', '-c', 'xschem -n -s -q -o build/taps xschem/tb_logdet.sch'],
                   cwd=ROOT, capture_output=True)
    s = open(os.path.join(B, 'tb_logdet.spice')).read()
    s = re.sub(r'^\.control.*?^\.endc\n', '', s, flags=re.S | re.M)
    s = re.sub(r'^(\.lib \S+sky130\.lib\.spice) tt$', rf'\1 {corner}', s, count=1, flags=re.M)
    # split the summing node: xd<i> drains to dc<i>, Vm<i> det -> dc<i> measures the cell current
    s = re.sub(r'^(xd(\d) t\d+p t\d+n ibias_det )det ', r'Vm\2 det dc\2 0\n\1dc\2 ', s, flags=re.M)
    assert s.count('\nVm') == 6, 'det_cell instances not found'
    save = ' '.join(f'v({t}p) v({t}n)' if t != 'out' else 'v(out_p) v(out_n)' for t in TAPS)
    save += ' v(det) ' + ' '.join(f'i(v.x2.vm{i})' for i in range(1, 7))
    meas = ''
    for k, t in enumerate(TAPS, 1):
        p, n = (f'{t}p', f'{t}n') if t != 'out' else ('out_p', 'out_n')
        meas += f'  let d{k} = v({p}) - v({n})\n  meas tran a{k} pp d{k} from=500n to=600n\n'
        meas += f'  meas tran i{k} avg i(v.x2.vm{k}) from=500n to=600n\n'
    echo = ' '.join(f'$&a{k} $&i{k}' for k in range(1, 7))
    ctl = f""".save {save}
.options method=GEAR
.control
foreach p {' '.join(map(str, LEVELS))}
  let ve = sqrt(8 * 73 * 1e-3 * 10^($p/10))
  alterparam vemf = $&ve
  reset
  tran 50p 600n 400n
  meas tran det avg v(det) from=500n to=600n
{meas}  echo RES $p $&det {echo}
  destroy all
end
.endc
"""
    return s.replace('\n.end\n', '\n' + ctl + '.end\n')


def run(corner):
    os.makedirs(B, exist_ok=True)
    with open(os.path.join(B, 'taps.spice'), 'w') as fh:
        fh.write(deck(corner))
    subprocess.run([OSIC, 'bash', '-c', 'cp .spiceinit build/taps/ && cd build/taps && ngspice -b taps.spice > taps.log 2>&1'],
                   cwd=ROOT)
    rows = re.findall(r'^RES (.*)$', open(os.path.join(B, 'taps.log')).read(), re.M)
    if len(rows) < len(LEVELS):
        sys.exit(f'only {len(rows)} of {len(LEVELS)} levels; see build/taps/taps.log')
    with open(TXT, 'w') as fh:
        fh.write(f'# {corner}: Pin_dBm det_V, then per tap (o1..o5, out): amp_pk_V cell_A\n')
        fh.write('\n'.join(rows) + '\n')


def plot():
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    d = np.loadtxt(TXT)
    p, det = d[:, 0], d[:, 1]
    amp = d[:, 2::2] / 2                       # pp -> peak (differential)
    cur = d[:, 3::2]
    dcur = (cur - cur[0]) * 1e6                # extra current over idle, uA
    cols = plt.cm.viridis(np.linspace(0, 0.9, 6))
    fig, ax = plt.subplots(3, 1, figsize=(9, 11), sharex=True)
    for k in range(6):
        ax[0].plot(p, 20 * np.log10(amp[:, k]), color=cols[k], label=TAPS[k])
    ax[0].set_ylabel('tap amplitude (dBV peak, diff)')
    ax[0].set_title('Successive detection: chain taps, cell currents, and their sum (tb_logdet)')
    ax[0].legend(ncol=6, fontsize=8)
    ax[1].stackplot(p, dcur.T, colors=cols, labels=[f'cell {t}' for t in TAPS], alpha=0.85)
    ax[1].plot(p, dcur.sum(1), 'k', lw=1.5, label='sum')
    ax[1].set_ylabel('extra cell current over idle (uA), stacked')
    ax[1].legend(ncol=4, fontsize=8, loc='upper left')
    ax[2].plot(p, det, 'k.-', label='det (summed, through rdet)')
    lin = (p >= -80) & (p <= -10)
    k, c = np.polyfit(p[lin], det[lin], 1)
    ax[2].plot(p[lin], k * p[lin] + c, 'r--', lw=1, label=f'fit -80..-10 dBm: {k * 1e3:.1f} mV/dB')
    ax[2].set_ylabel('det (V)')
    ax[2].set_xlabel('available input power (dBm)')
    ax[2].legend(fontsize=8)
    for a in ax:
        a.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(PNG, dpi=110)
    print(f'wrote {PNG}')


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--plot' not in args:
        run(next((a for a in args if not a.startswith('-')), 'tt'))
    plot()
