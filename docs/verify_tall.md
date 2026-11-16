# Verification of the tall chain stages (branch `chain-tall-stages`, sim-0, 2026-11-15 / …)

Full rerun after the tall-stage chain, the merged `rx_t` block (chain + one-row detector), the via-array and TX VAPWR
feed work and the `ua[0]` stub. Job list: `sim/rerun/jobs_tall.py`, scheduler `sim/rerun/sched.py`, logs
`build/rerun_tall/logs/`. Reference: [verify_lna_lo.md](verify_lna_lo.md). Not written yet: the run is still going.

## To include in this report

- **Run times, job by job** (Matt, 2026-11-16): so future runs can be planned from measured times, not guesses. Make
  the table with `python3 sim/rerun/durations.py --json build/rerun_tall/durations.json`. It gives, per job family,
  min / median / max minutes against the job file's estimate, the run's wall-clock span and thread-hours, and every job
  more than 3x over. Then put the measured times back into `jobs_tall.py`'s `est`, and fix `threads` where a job
  uses more CPU than it declares.
- What was learned about times during the run:
  - The estimates in `jobs_tall.py` were copied from `jobs_lna_lo.py`, written when those jobs were added and never
    measured. The old run's `sched.log` / `status.json` weren't kept, so there was nothing to check them against.
    Keep `durations.json` from this run in the repo or the report.
  - Extracted stability (`stabx_*`, 6 cases each on `rx_t`): ~5.5 h against 40 min. Each case took 35-55 min,
    getting longer as the shunt C grew.
  - Extracted noise (`nt_pex_*`, 3 µs with `gen_noise.py`'s PWL noise on `rx_t`): ~14-16 h against 10 min, 150-260
    ns of sim time per hour. The schematic version takes 1.5 min. `rx_t` (chain + detector, 1.65 MB, ~41,700 R)
    replaced last run's chain-only extraction (827 KB, ~22,000 R), and noise runs ~15x slower than a CW input on the
    same deck (cw_drop `--rx`: ~3 µs/h). Every noise log has 80,000 "non-increasing PWL time points" warnings
    for `vnz_n`: check `gen_noise.py` before the next run (timing tests proposed, not yet run).
  - Extracted Monte Carlo (`mc_chain_*_pex`): 523 min against 15 min (the schematic MC: 12-14 min).
  - `tile_pair` keeps ~6 CPUs busy (two ngspice at ~3.1 each) against 4 declared: the load went to 37-39 on a
    28-CPU quota (the container's cgroup `cpu.max`), so everything ran ~5-10 % slower until it ended.
  - The scheduler's 20 h priority bump on `est` (end of `jobs_tall.py`) hides the real estimates from its own log
    lines; `durations.py` reads them as written.
- Jobs whose exit code was lost on the scheduler restart (state `exited`): check each by its log. Done so far
  (all ran to the end): `stab_t_tt`, `stabx_ss10_v1.62_glo1.8`, `stabx_ss10_v1.8_glo0`, `stabx_ss10_v1.8_glo1.8`,
  `tile_rc_fs50`, `tile_rc_ss10`, `tx_corners_pex`, `mixed_-94_pex`, `mixed_-92_pex`.
- Expected differences against the reference: RX ~1-1.5 dB down on the extracted tile; decap VAPWR ~39 / VDPWR ~21 pF;
  TX VAPWR 13.3 / 36.7 mV; `rx_t` VDPWR 15.8 mV (case B); pinout and the `ua[0]` stub.
