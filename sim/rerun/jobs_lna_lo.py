"""Verification of branch lna-lo-shunt (docs/handoff_lna_lo.md), sim-0 (28 CPUs, fresh pod 2026-11-04).
    nohup setsid python3 sim/rerun/sched.py sim/rerun/jobs_lna_lo.py --budget 26 --out build/rerun_lnalo > build/rerun_lnalo/sched.log 2>&1 &
Results: build/rerun_lnalo/logs/<name>.log (+ each script's own outputs); write-up docs/verify_lna_lo.md.
Before the first run on a fresh pod: tools/osic bash sim/mixed/build_so.sh (the mixed jobs read its obj dir).
Base: jobs_2026-10-13.py (the full set), with the strap off (vglo 1.8) everywhere it was, plus the handoff's
new items: GL with test_lna_lo_strap (1), the chain stability on the extracted chain in both strap states (3),
the seeded chain MC with the step (4), low-gain sensitivity at transistor level (5: noise_tran, mixed signal,
extracted-tile pair), the extracted tile with vglo 0 (6). Needs build/top/ (top.py + route.py, done by hand).
threads = ngspice threads. Benches run from build/ read build/.spiceinit (8 threads unless NT / num_threads);
build/real and build/pexsim read ~/.spiceinit (4)."""

M642 = 'OSIC_MAGIC=$HOME/.local/magic642/bin'
O = 'OSIC=tools/osic'
H = 3600
TB = ('tbnet', 45)                   # tb_tile family: rewrites build/tb_radio_analog.spice at start
JOBS = []
J = JOBS.append

# ======== layout signoff
BLOCKS = ('amp_dpc amp_dp avg_sc bias_gen comp_ct ctrim_1p dbg_tg decap_vapwr_p1 decap_vapwr_p2 decap_vapwr_p3 '
          'decap_vapwr_p4 decap_vapwr_p5 decap_vdpwr_p1 decap_vdpwr_p2 decap_vdpwr_p3 det_cell lna_chain log_det '
          'lpf_rc r2r tx_drv tx_ls_en tx_ls tx_ring').split()
J(dict(name='check_top', cmd='tools/osic bash layout/check_top.sh', threads=1, est=600, lock='top'))
J(dict(name='xor_gds', cmd='tools/osic klayout -b -r sim/rerun/xor_gds.py', threads=1, est=300))
for m, est in (('lvs', 600), ('c', 900), ('rc', H)):
    J(dict(name=f'pex_tile_{m}', cmd=f'{M642} tools/osic bash layout/pex_tile.sh {m} && '
           f'grep -q "missing ports: \\[\\]" build/rerun_lnalo/logs/pex_tile_{m}.log', threads=1, est=est))
for b in BLOCKS:
    J(dict(name=f'check_{b}', cmd=f'tools/osic bash layout/check.sh {b} && grep -q "match uniquely" build/lvs/{b}/lvs.report',
           threads=1, est=120, lock=f'blk_{b}'))
PEXB = 'amp_dp amp_dpc avg_sc bias_gen dbg_tg det_cell lna_chain log_det lpf_rc r2r tx_drv tx_ls tx_ls_en tx_ring'.split()
for b in PEXB:                       # re-extract; the netlist must come out as committed
    J(dict(name=f'pex_{b}', cmd=f'{M642} tools/osic bash layout/pex.sh {b} && git diff --stat layout/pex/{b}.spice',
           threads=1, est=300, lock=f'blk_{b}', deps=[f'check_{b}']))

# ======== digital (RTL and macro changed: lna_lo strap, re-hardened macro)
J(dict(name='pinout', cmd='python3 tools/check_pinout.py', threads=1, est=5))
J(dict(name='rtl', cmd="bash -c 'cd verilog/test && make COCOTB_CONFIG=cocotb-config' && ! grep -q '<failure' verilog/test/results.xml "
       "&& grep -c '<testcase' verilog/test/results.xml && grep -q test_lna_lo_strap verilog/test/results.xml",
       threads=1, est=720, lock='cocotb'))
J(dict(name='gl_models', cmd="tools/osic bash -c 'mkdir -p build/gl_models && cp $PDK_ROOT/$PDK/libs.ref/sky130_fd_sc_hd/verilog/"
       "primitives.v $PDK_ROOT/$PDK/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v build/gl_models/'; "
       "test -s build/gl_models/primitives.v -a -s build/gl_models/sky130_fd_sc_hd.v", threads=1, est=5))
J(dict(name='gl', cmd="bash -c 'cd verilog/test && make COCOTB_CONFIG=cocotb-config GL=1 SIM_BUILD=sim_build_gl "
       "COCOTB_RESULTS_FILE=results_gl.xml' && ! grep -q '<failure' verilog/test/results_gl.xml "
       "&& grep -c '<testcase' verilog/test/results_gl.xml && grep -q test_lna_lo_strap verilog/test/results_gl.xml",
       threads=1, est=2.5 * H, lock='cocotb', deps=['gl_models']))      # est: run early
J(dict(name='formal_prove', cmd="tools/osic bash -c 'cd formal && sby -f radio_digital.sby prove' ; "
       "grep -q PASS formal/radio_digital_prove/status", threads=2, est=1800))
J(dict(name='tt_rtl', cmd=": ; bash -c 'cd test && make COCOTB_CONFIG=cocotb-config' && ! grep -q '<failure' test/results.xml",
       threads=1, est=120, lock='ttcocotb'))
J(dict(name='tt_gl', cmd=": ; bash -c 'cd test && make COCOTB_CONFIG=cocotb-config GL=1 SIM_BUILD=sim_build_gl "
       "COCOTB_RESULTS_FILE=results_gl.xml' && ! grep -q '<failure' test/results_gl.xml",
       threads=1, est=240, lock='ttcocotb', deps=['tt_rtl', 'gl_models']))
J(dict(name='vectors', cmd='python3 model/export_vectors.py && git diff --exit-code --stat verilog/test/vectors',
       threads=1, est=300, deps=['rtl', 'gl']))
J(dict(name='e2e_default', cmd='python3 model/e2e.py --out ../build/rerun_lnalo/e2e_default.png', threads=1, est=1800))
for tag, a in (('tt', '--nf 11 --slope 13.4 --offset-mv 1.26 --trim-mv 0.127'),
               ('fs50', '--nf 12.0 --slope 12.4 --offset-mv 1.3 --trim-mv 0.135')):
    J(dict(name=f'e2e_h135_{tag}', cmd=f'python3 model/e2e.py --brf 450e6 {a} --comp-noise-mv 0.3 --cases noise '
           f'--levels -94 -92 -90 -88 --trials 48 --out ../build/rerun_lnalo/e2e_h135_{tag}.png', threads=1, est=1500))

# ======== netlists the corner / joined / stability benches read
NL = 'build/tb_chain.spice build/tb_logdet.spice build/tb_comp.spice build/tb_rx_bb.spice build/real/tb_chain.spice'
J(dict(name='netlists', cmd=f"rm -f {NL}; tools/osic bash -c 'for t in tb_chain tb_logdet tb_comp tb_rx_bb; do xschem -n -s -q -o build "
       f"xschem/$t.sch; done; xschem -n -s -q -o build/real xschem/tb_chain.sch'; ls {NL} && ! grep -l 'IS MISSING' {NL} && "
       "grep -q '^Vglo glo GND' build/tb_logdet.spice && grep -q '^Vglo glo GND' build/tb_chain.spice", threads=1, est=60))
# the extracted chain swapped into tb_chain (stability, MC) and tb_logdet (noise_tran), after re-extraction
PX = ("mkdir -p build/pexsim && python3 sim/chain/mk_pex_tb.py build/real/tb_chain.spice layout/pex/lna_chain.spice "
      "build/pexsim/tb_chain.spice && python3 sim/chain/mk_pex_tb.py build/tb_logdet.spice layout/pex/lna_chain.spice "
      "build/tb_logdet_pex.spice && tools/osic bash -c 'xschem -n -s -q -o build/pexsim xschem/decap_vdpwr.sch' ; "
      "sed -i 's/^\\*\\*\\.subckt /.subckt /; s/^\\*\\*\\.ends/.ends/' build/pexsim/decap_vdpwr.spice && "
      "grep -q '^\\.subckt decap_vdpwr' build/pexsim/decap_vdpwr.spice && grep -q '^\\.param vglo' build/pexsim/tb_chain.spice "
      "&& grep -q '^\\.subckt lna_chain inp inn ibias vcm lna_lo_n' build/tb_logdet_pex.spice")
J(dict(name='pexsim', cmd=PX, threads=1, est=60, deps=['netlists', 'pex_lna_chain']))

# ======== per-block tests, tt, schematic and extracted
TBS = {'amp_dp': 'sim/amp_dp/tb_amp_dp.py', 'amp_dpc': 'sim/amp_dpc/tb_amp_dpc.py', 'det_cell': 'sim/det_cell/tb_det_cell.py',
       'log_det': 'sim/logdet/tb_log_det.py', 'lpf_rc': 'sim/lpf_rc/tb_lpf_rc.py', 'avg_sc': 'sim/avg_sc/tb_avg_sc.py',
       'r2r': 'sim/dac/tb_r2r.py', 'bias_gen': 'sim/bias/tb_bias_gen.py', 'dbg_tg': 'sim/dbg_tg/tb_dbg_tg.py',
       'tx_ring': 'sim/tx/tb_tx_ring.py', 'tx_drv': 'sim/tx/tb_tx_drv.py', 'comp_ct': 'sim/comp_ct/tb_comp_ct.py'}
LOCK = {'bias_gen': 'tbbias'}
for b, sc in TBS.items():
    for pex in (False, True):
        J(dict(name=f'tb_{b}' + ('_pex' if pex else ''), cmd=f'{O} python3 {sc} {"--pex " if pex else ""}tt', threads=8, est=300,
               lock=LOCK.get(b, f'blk_{b}'), deps=[f'pex_{b}'] if pex and b != 'comp_ct' else []))
for b in ('tx_ls', 'tx_ls_en'):
    for pex in (False, True):
        J(dict(name=f'tb_{b}' + ('_pex' if pex else ''), cmd=f'{O} python3 sim/tx/tb_tx_ls.py {"--pex " if pex else ""}{b} tt',
               threads=8, est=300, lock='txls', deps=[f'pex_{b}'] if pex else []))
# the strap's own chain numbers (handoff "Results so far": gain / NF, full and low gain), schematic and extracted
for d, dep in (('real', 'netlists'), ('pexsim', 'pexsim')):
    for c, t in (('tt', 27), ('ss', 10), ('ff', 50)):
        for g in ('1.8', '0'):
            J(dict(name=f'lnalo_{d}_{c}{t}_glo{g}', cmd=f"tools/osic bash -c 'cd build/{d} && VGLO={g} CORNER={c} TEMP={t} "
                   f"CASES=\"x:0:none\" bash ../../sim/chain/lna_lo.sh'", threads=4, est=300, deps=[dep], lock=f'lnalo_{d}'))

# ======== chain stability (2 nH, real decap, Ccpl out_p -> pad_p). Schematic as 2026-10-13; extracted both states
for tag, env in (('tt', ''), ('ss10', 'CORNER=ss TEMP=10 '), ('ss10_v189', "VSUP=1.89 CORNER=ss TEMP=10 CASES='0:0 2n:0 2n:0.1f' ")):
    J(dict(name=f'stab_{tag}', cmd=f'tools/osic bash -c "cd build/real && {env}bash ../../sim/chain/stability.sh"',
           threads=4, est=1800, lock='stab', deps=['netlists']))
SC_FULL = '2n:0 2n:0.3f 2n:0.5f 2n:0.75f 2n:1f 2n:1.5f'
SC_LO = '2n:0 2n:0.5f 2n:1f 2n:1.5f 2n:2f 2n:3f'
for c, t in (('ss', 10), ('tt', 27), ('ff', 50)):
    for v in ('1.8', '1.62', '1.98'):
        if v != '1.8' and c != 'ss':
            continue
        for g, cs in (('1.8', SC_FULL), ('0', SC_LO)):
            J(dict(name=f'stabx_{c}{t}_v{v}_glo{g}', cmd=f"tools/osic bash -c \"cd build/pexsim && VGLO={g} CORNER={c} TEMP={t} "
                   f"VSUP={v} CASES='{cs}' bash ../../sim/chain/stability.sh\"", threads=4, est=2400, deps=['pexsim']))

# ======== other analog
J(dict(name='decap_ac', cmd="tools/osic bash -c 'xschem -n -s -q -o build xschem/tb_radio_analog.sch && cd build && ../sim/decap/decap_ac.sh'",
       threads=8, est=600, stagger=TB))
J(dict(name='bias_loop', cmd="tools/osic bash -c 'xschem -n -s -q -o build xschem/tb_bias.sch && cd build && CORNERS=\"tt ss ff sf fs\" "
       "../sim/bias/loop.sh'", threads=8, est=900, lock='tbbias'))

# ======== corners and temperatures, supply (rx_corners: one process per corner)
CORNERS = 'tt ss ff sf fs'.split()
RXC = []
for out, env, temps in (('corners', '', '10 50'), ('corners_realbias', 'BIAS=real ', '-20 27 85'), ('corners_ideal', '', '-20 27 85')):
    for c in CORNERS:
        n = f'rxc_{out}_{c}'
        RXC.append(n)
        J(dict(name=n, cmd=f"tools/osic bash -c 'cd build && {env}OUT={out} CORNERS={c} TEMPS=\"{temps}\" NT=1 ../sim/corners/rx_corners.sh'",
               threads=1, est=900, deps=['netlists']))
    J(dict(name=f'rxc_{out}', cmd=f'CORNERS_DIR=build/{out} python3 sim/corners/rx_corners.py', threads=1, est=30,
           deps=[f'rxc_{out}_{c}' for c in CORNERS]))
for v, out in (('1.71', 'corners_v171'), ('1.8', 'corners_v18'), ('1.89', 'corners_v189')):
    for c, t in (('tt', '27'), ('ss', '10'), ('fs', '50')):
        n = f'rxc_{out}_{c}'
        RXC.append(n)
        J(dict(name=n, cmd=f"tools/osic bash -c 'cd build && VDD={v} OUT={out} CORNERS={c} TEMPS={t} NT=1 ../sim/corners/rx_corners.sh'",
               threads=1, est=600, deps=['netlists']))
    J(dict(name=f'rxc_{out}', cmd=f'CORNERS_DIR=build/{out} python3 sim/corners/rx_corners.py', threads=1, est=30,
           deps=[f'rxc_{out}_{c}' for c in ('tt', 'ss', 'fs')]))
for c, t in (('fs', 50), ('ss', 10), ('ff', 50)):
    J(dict(name=f'tile_rc_{c}{t}', cmd=f'{O} NT=2 python3 sim/top/tb_tile.py --corner={c} --temp={t} rc', threads=2, est=4.5 * H,
           deps=['pex_tile_rc'], stagger=TB))
for t in (10, 50):
    J(dict(name=f'tile_c_{t}', cmd=f'{O} NT=4 python3 sim/top/tb_tile.py --temp={t} c', threads=4, est=900, stagger=TB,
           deps=['pex_tile_c']))
    J(dict(name=f'tile_rc_{t}', cmd=f'{O} NT=4 python3 sim/top/tb_tile.py --temp={t} rc', threads=4, est=1.5 * H,
           deps=['pex_tile_rc'], stagger=TB))
    for c in CORNERS:
        J(dict(name=f'tile_tx_{c}{t}', cmd=f'{O} NT=2 python3 sim/top/tb_tile_tx.py sch:corner={c},temp={t}', threads=2, est=300,
               stagger=TB))
TX = ('tbtx', 60)
J(dict(name='tx_corners', cmd='NT=1 python3 sim/tx/tb_tx.py tt ss ff sf fs', threads=1, est=600, stagger=TX))
J(dict(name='tx_corners_pex', cmd='NT=1 python3 sim/tx/tb_tx.py --pex tt ss ff sf fs', threads=1, est=1800, stagger=TX,
       deps=['pex_tx_drv']))
for vd in ('1.71', '1.8', '1.89'):
    for va in ('3.0', '3.3', '3.6'):
        if (vd, va) != ('1.8', '3.3'):
            J(dict(name=f'tx_v{vd}_{va}', cmd=f'NT=1 python3 sim/tx/tb_tx.py --vdd={vd} --vapwr={va} tt ss ff sf fs', threads=1,
                   est=300, stagger=TX))
        for c in CORNERS:
            J(dict(name=f'tx_pex_v{vd}_{va}_{c}', cmd=f'NT=1 python3 sim/tx/tb_tx.py --pex --pex-ring --vdd={vd} --vapwr={va} {c}',
                   threads=1, est=1800, stagger=TX, deps=['pex_tx_drv', 'pex_tx_ring']))
for args in ('--vdd=1.71 --vapwr=3.0', '--vdd=1.89 --vapwr=3.6', '--vdd=1.71 --vapwr=3.0 --corner=ss --temp=10',
             '--vdd=1.71 --vapwr=3.6 --corner=ss --temp=10', '--vdd=1.71 --vapwr=3.0 --corner=fs --temp=50',
             '--vdd=1.89 --vapwr=3.6 --corner=ff --temp=85'):
    n = 'tile_sup_' + args.replace('--', '').replace('=', '').replace(' ', '_').replace('vapwr', '').replace('corner', '').replace('temp', '')
    J(dict(name=n, cmd=f'{O} NT=4 python3 sim/top/tb_tile.py {args} sch', threads=4, est=300, stagger=TB))

# ======== mismatch
MC = [('tt', ''), ('ss', ''), ('fs', ''), ('ss', '--temp 10'), ('fs', '--temp 50'), ('ff', '--temp 50'),
      ('sf', '--temp 10 --cm 1.45'), ('sf', '--temp 27 --cm 1.45')]
for c, a in MC:
    n = f'mc_comp_{c}' + a.replace('--temp ', '_').replace(' --cm ', '_cm').replace(' ', '')
    J(dict(name=n, cmd=f'python3 sim/comp_ct/tb_comp_ct.py --mc 200 --jobs 8 --step {a} {c}', threads=8, est=300, lock='mccomp'))
J(dict(name='mc_bins', cmd='python3 sim/comp_ct/mc_bins.py $(ls build/mc/comp_*_step.txt)', threads=1, est=10,
       deps=[j['name'] for j in JOBS if j['name'].startswith('mc_comp_')]))
for c, t in (('tt', 27), ('fs', 50), ('sf', 10)):
    J(dict(name=f'mc_avg_{c}{t}', cmd=f'python3 sim/avg_sc/tb_avg_sc.py --mc 200 --temp {t} --jobs 1 {c}', threads=1, est=2 * H,
           stagger=('avgsc', 60)))
# lna_chain: seeded, both strap states per sample (handoff item 4)
for c, t in (('tt', 27), ('ss', 10), ('ff', 50), ('sf', 27), ('fs', 27)):
    for pex in ('', ' --pex'):
        J(dict(name=f'mc_chain_{c}{t}' + pex.replace(' --', '_'), cmd=f'{O} python3 sim/chain/mc_chain.py --mc 1000 --jobs 4 '
               f'--temp {t}{pex} {c}', threads=4, est=900, deps=['pexsim' if pex else 'netlists'], lock='mcchain'))

# ======== low-gain sensitivity at transistor level (handoff item 5)
# noise_tran: the whole input-referred noise as a fixed PWL waveform (one per run), det averaged over 0.5-3 us.
# Full gain on the schematic is the 2026-10 reference (none 1.43904 V; sim/logdet/noise_tran_results.txt).
J(dict(name='gen_noise', cmd='python3 sim/logdet/gen_noise.py && test -s build/noise_pwl.inc',
       threads=1, est=60))
NT_CASES = [('sch', '1.8', 'tb_logdet.spice', 'none -94 -92 -90 -88'),
            ('sch', '0', 'tb_logdet.spice', 'none -92 -90 -88 -86 -84 -80'),
            ('pex', '1.8', 'tb_logdet_pex.spice', 'none -94 -92 -90 -88'),
            ('pex', '0', 'tb_logdet_pex.spice', 'none -92 -90 -88 -86 -84 -80')]
for kind, g, tb, lv in NT_CASES:
    for p in lv.split():
        tag = f'_{kind}_glo{g}'
        J(dict(name=f'nt{tag}_{p}', cmd=f"tools/osic bash -c 'cd build && VGLO={g} TB={tb} TAG={tag} bash ../sim/logdet/noise_tran.sh {p}' "
               f"&& grep -q '^RESULT' build/nt_{p}{tag}.log", threads=8, est=600,
               deps=['gen_noise', 'netlists'] + (['pexsim'] if kind == 'pex' else [])))
# mixed signal (RTL + transistor baseband) with the low-gain detector waveform: gen_det --gain from noise_tran's
# noise-only det with the strap on (NF +0.7 dB, the extracted chain's NF off / on)
for kind in ('sch', 'pex'):
    t = 'lo' if kind == 'sch' else 'lopex'
    gl = f'$(python3 sim/rx/lo_gain.py build/nt_none_{kind}_glo0.log 11.7)'
    J(dict(name=f'gen_det_{t}', cmd=f'G={gl}; echo gain $G; for s in 1 2 3 4 5; do python3 sim/rx/gen_det.py --gain=$G --nf=11.7 '
           f'--tag={t} --seed=$s -92 -90 -88 -86 -84; done', threads=1, est=600, deps=[f'nt_{kind}_glo0_none']))


def mixed(name, args, est, deps=('gen_det',)):
    J(dict(name=f'mixed_{name}', cmd=f': ; python3 sim/mixed/gen_mixed.py {args} && (tools/osic bash -c "cd build/mixed && ngspice -b '
           f'mixed_{name}.cir > mixed_{name}.log 2>&1"; true) && python3 sim/mixed/plot_mixed.py {name}', threads=1, est=est,
           deps=list(deps), stagger=('mixed', 10)))


for kind in ('lo', 'lopex'):
    for lvl in (-92, -90, -88, -86, -84):
        for s in range(1, 6):
            mixed(f'{lvl}_s{s}_{kind}', f'--seed={s} --tag={kind} {lvl}', 1500, deps=(f'gen_det_{kind}',))

# ======== mixed signal, full gain (as 2026-10-13)
J(dict(name='gen_det', cmd='python3 sim/rx/gen_det.py -94 -92 -90 -70 && for n in 1 2 3 4 5; do python3 sim/rx/gen_det.py --seed=$n -92 -94; '
       'done && for g in 0.1 0.25 0.3 0.4 0.5 1 2 5; do python3 sim/rx/gen_det.py --overload=$g -90; done', threads=1, est=600))
for lvl in ('-70', '-90', '-94'):
    mixed(lvl, lvl, 1200)
mixed('-94_pex', '--pex -94', 3 * H)
mixed('-92_pex', '--pex -92', 3 * H)
for n in range(1, 6):
    mixed(f'-92_s{n}', f'--seed={n} -92', 1200)
    mixed(f'-94_s{n}', f'--seed={n} -94', 1200)
    mixed(f'-92_pex_s{n}', f'--pex --seed={n} -92', 3 * H)
    mixed(f'-94_pex_s{n}', f'--pex --seed={n} -94', 3 * H)
for g, ts in (('0.1', '28.7m'), ('0.25', '28.9m'), ('0.3', '28.9m'), ('0.4', '29.0m'), ('0.5', '29.1m'), ('1', '29.6m'),
              ('2', '30.6m'), ('5', '33.6m')):
    mixed(f'-90_ov{g}', f'--tag=ov{g} -90 {ts}', 2400)
J(dict(name='mixed_-70swap', cmd="sed '/^adut/s/trim_out_1 trim_out_0/trim_out_0 trim_out_1/; s/^write mixed_-70.raw/write mixed_-70swap.raw/' "
       "build/mixed/mixed_-70.cir > build/mixed/mixed_-70swap.cir && (tools/osic bash -c 'cd build/mixed && ngspice -b mixed_-70swap.cir "
       "> mixed_-70swap.log 2>&1'; true) && python3 sim/mixed/plot_mixed.py -70swap | tee /dev/stderr | grep -q 'PIN ORDER PROBLEM'",
       threads=1, est=1200, deps=['mixed_-70']))

# ======== joined RX, schematic (10+ h each; NT 2)
for lvl in ('-90', '-70', '-10'):
    J(dict(name=f'joined_{lvl}', cmd=f"tools/osic bash -c 'cd build && LEVELS={lvl} TSTOP=400u NT=2 ../sim/rx/joined.sh'", threads=2,
           est=16 * H, deps=['netlists'], stagger=('joined', 60)))

# ======== extracted tile (item 6: also with the strap on)
for g in ('', ' --vglo=0'):
    s = g.replace(' --vglo=0', '_glo0')
    J(dict(name=f'tile_c{s}', cmd=f'{O} NT=4 python3 sim/top/tb_tile.py{g} c', threads=4, est=900, deps=['pex_tile_c'], stagger=TB))
    J(dict(name=f'tile_rc{s}', cmd=f'{O} NT=4 python3 sim/top/tb_tile.py{g} rc', threads=4, est=1.5 * H, deps=['pex_tile_rc'],
           stagger=TB))
    J(dict(name=f'tile_cw_sch_c{s}', cmd=f'{O} NT=1 python3 sim/top/tb_tile.py{g} --cw sch c', threads=10, est=900,
           deps=['pex_tile_c'], stagger=TB))
    J(dict(name=f'tile_cw_rc{s}', cmd=f'{O} NT=1 python3 sim/top/tb_tile.py{g} --cw rc', threads=5, est=2.5 * H,
           deps=['pex_tile_rc'], stagger=TB))
    J(dict(name=f'tile_scan{s}', cmd=f'{O} NT=4 python3 sim/top/tb_tile_joined.py{g} scan', threads=4, est=10 * H,
           deps=['pex_tile_c'], stagger=TB))   # est: priority (the pair waits on it)
    lvl = '-88' if g else '-92'
    J(dict(name=f'tile_pair{s}', cmd=f"code=$(grep -o 'comp flips between codes \\[([0-9]*, [0-9]*)' build/rerun_lnalo/logs/tile_scan{s}.log "
           f"| head -1 | grep -o '[0-9]*)' | tr -d ')'); echo code $code; {O} NT=2 python3 sim/top/tb_tile_joined.py{g} pair {lvl} 30u "
           f"$code 1 && {O} python3 sim/top/tb_tile_joined.py{g} --no-run pair {lvl}", threads=4, est=9 * H,
           deps=[f'tile_scan{s}'], stagger=TB))
J(dict(name='tile_lvs', cmd=f'{O} NT=4 python3 sim/top/tb_tile.py lvs', threads=4, est=600, deps=['pex_tile_lvs'], stagger=TB))
CW = ['', '--levels=-84,-82,-80,-78,-76,-74,-72', '--blocks=lna_chain --levels=-90 --pex-only', '--blocks=log_det --levels=-90 --pex-only']
for i, a in enumerate(CW):            # never two cw_drop at once; tb_logdet.spice: after the rx_corners runs
    J(dict(name=f'cw_drop_{i}', cmd=f'python3 sim/chain/cw_drop.py {a}', threads=10, est=1800, lock='cwdrop',
           deps=['pex_lna_chain', 'pex_log_det'] + RXC))

# ======== power-up and pad overload (tb_tile.netlist() at start: stagger)
J(dict(name='pwrup_sch', cmd=f'{O} NT=4 python3 sim/top/tb_powerup.py --ramp=10u --corner=tt --temp=27 sch', threads=4, est=900, stagger=TB))
for c, t in (('tt', 27), ('ss', 10), ('ff', 50)):
    J(dict(name=f'pwrup_10u_{c}{t}', cmd=f'{O} NT=4 python3 sim/top/tb_powerup.py --ramp=10u --corner={c} --temp={t} c', threads=4,
           est=3 * H, stagger=TB, deps=['pex_tile_c']))
    J(dict(name=f'pwrup_10m_{c}{t}', cmd=f'{O} NT=1 python3 sim/top/tb_powerup.py --ramp=10m --corner={c} --temp={t} c', threads=1,
           est=7 * H, stagger=TB, deps=['pex_tile_c']))
    J(dict(name=f'pwrup_off_{c}{t}', cmd=f'{O} python3 sim/top/tb_powerup.py --off --corner={c} --temp={t} c', threads=1,
           est=120, stagger=TB, deps=['pex_tile_c']))
J(dict(name='pad_ovl_0', cmd=f'{O} NT=4 python3 sim/top/tb_pad_overload.py --dbm=0 sch', threads=4, est=1200, stagger=TB))
J(dict(name='pad_ovl_6', cmd=f'{O} NT=4 python3 sim/top/tb_pad_overload.py --dbm=6 --tstop=150e-6 sch', threads=4, est=3600, stagger=TB))

# ======== power delivery (case A)
J(dict(name='pwr_pex', cmd=f"{M642} tools/osic bash -c 'CASE=A bash sim/power/pex_power.sh' && ! grep -i shorted build/power/ext_A/magic.log",
       threads=1, est=120))
J(dict(name='pwr_mesh05', cmd='tools/osic python3 sim/power/mesh.py A 0.5', threads=1, est=120, deps=['pwr_pex']))
J(dict(name='pwr_mesh10', cmd='tools/osic python3 sim/power/mesh.py A 1.0', threads=1, est=120, deps=['pwr_pex']))
for s, est in (('r_mesh', 1800), ('ir_rx', 1200), ('em', 900)):
    J(dict(name=f'pwr_{s}', cmd=f'{O} python3 sim/power/{s}.py A', threads=2, est=est, deps=['pwr_mesh05']))
J(dict(name='pwr_z_ac', cmd=f'{O} python3 sim/power/z_ac.py A', threads=2, est=1800, deps=['pwr_mesh10'], lock='tilemesh'))
J(dict(name='pwr_tran_tx', cmd=f'{O} python3 sim/power/tran_tx.py A 30', threads=2, est=2 * H, deps=['pwr_mesh10'], lock='tilemesh'))

assert len({j['name'] for j in JOBS}) == len(JOBS), 'duplicate job names'

# priority: the handoff's new checks first (the scheduler starts the longest est first; these are short)
PRIO = ('gl_models', 'gl', 'pexsim', 'gen_noise', 'nt_', 'stabx_', 'mc_chain_', 'lnalo_', 'gen_det_lo', 'tile_scan_glo0',
        'tile_pair_glo0', 'tile_c', 'tt_', 'check_lna_chain', 'pex_lna_chain')
for j in JOBS:
    if j['name'].startswith(PRIO):
        j['est'] = max(j['est'], 20 * H)
