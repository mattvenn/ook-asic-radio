"""Follow-ups to the chain-tall-stages verification (docs/verify_tall.md, 2026-11-17), on sim-0:
    mkdir -p build/rerun_tall_follow && nohup setsid python3 sim/rerun/sched.py sim/rerun/jobs_tall_follow.py --budget 28 --load 28 --out build/rerun_tall_follow > build/rerun_tall_follow/sched.log 2>&1 &
Needs the main run's outputs (build/pexsim, build/tb_logdet*.spice, build/nt_*.log, build/real/tb_radio_analog.spice).

1. Why the extracted noise runs took 14-16 h (TODO.md): gen_noise.py wrote its PWL times to 5 significant figures, so
   from 1 us on every other point repeats a time. Timing runs to 1.2 us (0.2 us past the first repeat) on three
   decks - the schematic, lna_chain_t alone (chain-only, as last run) and rx_t (chain + detector) - each with the old
   noise file and the fixed one; then the full 3 us noise-only and -90 dBm cases with the fixed file on the schematic
   and rx_t, to see whether the det levels move.
2. Low-gain stability on the extracted rx_t at sf 27 (the corner with the smallest gain step, 7.6 dB): stabx did
   ss / tt / ff only.
3. The extracted low-gain mixed runs again (tag lopex2): the 'lopex' runs' gain came from mapping rx_t's own detector
   level through the schematic curve (-5.59 dB, invalid). Now the schematic's gain (-12.21 dB) with the NF raised by
   the measured drop ratio (sim/rx/lo_gain.py --nf: 13.4 dB).
"""
H = 3600
JOBS = []
J = JOBS.append
SP = '/foss/designs/ook-asic-radio-tall-stages/.spiceinit'

# ======== 1. noise run timing
T = 'build/nt_timing'
J(dict(name='timing_prep', threads=1, est=120, cmd=(
    f'rm -rf {T} && mkdir -p {T}/old {T}/new && cp build/noise_pwl.inc {T}/old/ && '
    f'python3 sim/logdet/gen_noise.py 3e-6 7 {T}/new/noise_pwl.inc && '
    f"sed 's/^\\.subckt lna_chain_t /.subckt lna_chain /' layout/pex/lna_chain_t.spice > {T}/lna_chain_t_as_chain.spice && "
    f'python3 sim/chain/mk_pex_tb.py build/tb_logdet.spice {T}/lna_chain_t_as_chain.spice {T}/tb_chain_t.spice && '
    f'for d in old new; do cp build/tb_logdet.spice {T}/$d/tb_sch.spice; cp build/tb_logdet_pex.spice {T}/$d/tb_rx_t.spice; '
    f'cp {T}/tb_chain_t.spice {T}/$d/; cp {SP} {T}/$d/.spiceinit; done && grep -q "^x1 .* lna_chain$" {T}/tb_chain_t.spice')))
for deck, est in (('sch', 600), ('chain_t', 2 * H), ('rx_t', 4 * H)):
    for nz in ('old', 'new'):
        J(dict(name=f'timing_{deck}_{nz}', threads=3, est=est, deps=['timing_prep'],
               cmd=f"tools/osic bash -c 'cd {T}/{nz} && TSTOP=1.2u TB=tb_{deck}.spice TAG=_{deck} bash ../../../sim/logdet/noise_tran.sh none' "
                   f"&& grep -q '^RESULT' {T}/{nz}/nt_none_{deck}.log"))
for deck, est in (('sch', 600), ('rx_t', 4 * H)):
    for g in ('1.8', '0'):
        for p in ('none', '-90'):
            J(dict(name=f'nt3_{deck}_glo{g}_{p}', threads=3, est=est, deps=[f'timing_{deck}_new'],
                   cmd=f"tools/osic bash -c 'cd {T}/new && VGLO={g} TB=tb_{deck}.spice TAG=_full_{deck}_glo{g} "
                       f"bash ../../../sim/logdet/noise_tran.sh {p}' && grep -q '^RESULT' {T}/new/nt_{p}_full_{deck}_glo{g}.log"))

# ======== 2. low-gain stability, extracted rx_t, sf 27 (same cases as jobs_tall.py's stabx; full gain alongside)
SC_FULL = '2n:0 2n:0.3f 2n:0.5f 2n:0.75f 2n:1f 2n:1.5f'
SC_LO = '2n:0 2n:0.5f 2n:1f 2n:1.5f 2n:2f 2n:3f'
for g, cs in (('0', SC_LO), ('1.8', SC_FULL)):
    J(dict(name=f'stabx_sf27_v1.8_glo{g}', threads=4, est=6 * H,
           cmd=f"tools/osic bash -c \"cd build/pexsim && VGLO={g} CORNER=sf TEMP=27 VSUP=1.8 CASES='{cs}' "
               f"bash ../../sim/chain/stability.sh\""))

# ======== 3. extracted low-gain mixed runs, recalibrated (25: 5 levels x 5 seeds, as jobs_tall.py's lopex)
J(dict(name='gen_det_lopex2', threads=1, est=600, cmd=(
    'G=$(python3 sim/rx/lo_gain.py build/nt_none_sch_glo0.log 11.7) && NF=$(python3 sim/rx/lo_gain.py --nf _sch_glo0 _pex_glo0 11.7) '
    '&& echo gain $G nf $NF && for s in 1 2 3 4 5; do python3 sim/rx/gen_det.py --gain=$G --nf=$NF --tag=lopex2 --seed=$s '
    '-92 -90 -88 -86 -84; done')))
for lvl in (-92, -90, -88, -86, -84):
    for s in range(1, 6):
        n = f'{lvl}_s{s}_lopex2'
        J(dict(name=f'mixed_{n}', threads=1, est=600, deps=['gen_det_lopex2'], stagger=('mixed', 10),
               cmd=f'python3 sim/mixed/gen_mixed.py --seed={s} --tag=lopex2 {lvl} && (tools/osic bash -c "cd build/mixed && '
                   f'ngspice -b mixed_{n}.cir > mixed_{n}.log 2>&1"; true) && python3 sim/mixed/plot_mixed.py {n}'))

assert len({j['name'] for j in JOBS}) == len(JOBS), 'duplicate job names'
