# Verification of the tall chain stages (branch `chain-tall-stages`, sim-0, 2026-11-15 / 17)

Full rerun after the tall-stage chain, the merged `rx_t` block (chain + one-row detector + the tap wiring between them),
the via-array and TX VAPWR feed work and the `ua[0]` stub. Job list: `sim/rerun/jobs_tall.py`, scheduler
`sim/rerun/sched.py`, logs `build/rerun_tall/logs/` on sim-0. Reference: [verify_lna_lo.md](verify_lna_lo.md) (the
last full run, on the U chain). Follow-ups: `sim/rerun/jobs_tall_follow.py`, logs `build/rerun_tall_follow/logs/`.

Run: 2026-11-15 16:39 → 11-17 09:47, 41 h. 471 job runs (442 jobs, some run twice after a fix): **441 OK**, 29 of
them `exited` (ended under an earlier scheduler instance, exit code lost, each checked by its log: all ran to the
end), **1 failed** (a dropped bench, below), 0 stalled.

## Summary

| # | Item | Result |
|---|---|---|
| 1 | Digital: RTL / GL cocotb, TT top, formal, eqy, pinout, vectors, e2e | **pass**, identical to the reference |
| 2 | Layout signoff: 36 blocks, tile check, xor | **pass**: every block DRC 0 (magic + KLayout), antenna 0, LVS PASS; tile precheck PASS, antenna 7 (the macro's own), LVS PASS; exported tile metal identical |
| 3 | Per-block benches, sch / pex | **pass**: the unchanged blocks identical; the tall stages as their design note |
| 4 | Chain stability, extracted `rx_t` | **pass**: full gain stable to 0.75 fF at every corner and supply, low gain to 1.5 fF (better than the U chain); sf (follow-up) full to 1 fF, low to 3 fF |
| 5 | Gain step (full − low gain), MC | **open - needs Matt's call** (low gain stable at sf to 3 fF, follow-up): on the block extraction 9.27 dB at tt, **7.58 dB at sf** (0 % ≥ 9 dB), 8.50 at ss 10 °C (8 %). The tile shows ~10.2 dB at tt (CW drops), so the block is ~1 dB pessimistic; sf on the tile is ~8.5 dB by the same offset |
| 6 | RX sensitivity, extracted | **CHANGED, worse: −1.3 to −2.3 dB** against the U chain (tile pair −92 dBm −1.3 dB, noise runs −2.0 dB, tile CW −2.3 dB). Not in the expected −1 to −1.5 dB. The schematic is unchanged |
| 7 | Mixed signal, full gain (sch and pex baseband), overload | **pass**, identical pattern to the reference (overload scan event times identical) |
| 8 | Low-gain mixed signal | sch **pass** (over burst timing 92 / 55 / 38 % at −86 / −88 / −90, reference 90 / 68 / 40). Extracted: `lopex` invalid as run (calibration); recalibrated rerun `lopex2` 80 / 50 / 20 %, ~1 dB below the schematic (follow-ups) |
| 9 | Corners, supply, TX, power-up, overload, power delivery | **pass**; TX at the marginal 1.71 / 3.3 V ss / fs points −0.5 / −0.6 dB; power-delivery numbers changed by the re-route (mostly better) |

Findings to decide (Matt):
1. **The gain step on the extracted chain** (item 5). The last run passed it with "low gain still stabilises the chain
   at sf". The follow-up checked that on the extracted `rx_t`: low gain at sf is stable to 3 fF (below), so the
   condition holds. The step itself is still short of 9 dB at sf.
2. **The extracted RX is ~2 dB worse than the U chain** (item 6), though its schematic gain is the same and its
   extracted chain alone (`lna_chain_t`) has 0.37 dB more gain than the U. The loss is in `rx_t`: the detector's
   inputs and the tap wiring load the chain. Block `rx_t` −4.9 dB against its schematic, the tile −1.5 dB.

## Follow-ups (2026-11-17)

Run on sim-0 after the main run (`sim/rerun/jobs_tall_follow.py`).

### Low-gain stability at sf 27 °C, extracted `rx_t`

`stabx_sf27_v1.8_glo{0,1.8}`: the same bench and cases as "Chain stability, extracted" (section 3), at sf 27 °C 1.8 V. 133 min
each on 4 threads (the job file guessed 6 h).

| Gain | 0 | 0.3 fF | 0.5 fF | 0.75 fF | 1 fF | 1.5 fF | 2 fF | 3 fF |
|---|---|---|---|---|---|---|---|---|
| full: result | ok | ok | ok | ok | ok | OSC 0.01 | | |
| full: gain at 434 MHz, dB | 71.07 | 72.93 | 74.44 | 76.78 | 79.95 | 98.23 | | |
| low: result | ok | | ok | | ok | **ok** | ok | ok |
| low: gain at 434 MHz, dB | 63.53 | | 64.47 | | 65.41 | 66.32 | 67.10 | 67.83 |

**Pass.** Low gain at sf is stable to 3 fF, the widest margin of any corner (ss 10 °C oscillates at 3 fF), so the
condition the last run passed the gain step on holds: switching to low gain still stabilises the chain at sf. Full
gain at sf is stable to 1 fF (1.5 fF still ringing, 7.8 mV late p-p, but decaying: growth 0.009). The gain step at
C = 0 is 7.53 dB, matching the MC's 7.58 dB at sf. At 3 fF the low-gain response peaks 9.6 dB above its 434 MHz gain
(at 502 MHz), so 3 fF is near its edge.

### Extracted low-gain mixed runs, recalibrated (`lopex2`)

The `lopex` runs' `--gain` came from `sim/rx/lo_gain.py`, which maps a noise-only detector level through the
*schematic* detector curve. `rx_t` brings its own extracted detector, which sits lower (noise-only, low gain: 1.484 V
against 1.510 V), and the mapping read that as +6.6 dB of gain: −5.59 dB against the schematic's −12.21. Those runs
detect 5/5 down to −90 dBm, far better than the schematic: an artefact.

The extracted noise runs give a cleaner calibration. At low gain, every extracted detector drop (noise-only level minus
the level with signal) is the same fraction of the schematic's:

| Level, dBm | −80 | −84 | −86 | −88 | −90 | −92 |
|---|---|---|---|---|---|---|
| sch drop, mV | 3.21 | 1.40 | 0.94 | 0.63 | 0.43 | 0.29 |
| pex drop, mV | 2.16 | 0.94 | 0.63 | 0.42 | 0.29 | 0.20 |
| pex / sch | 0.673 | 0.671 | 0.670 | 0.667 | 0.674 | 0.690 |

A constant ratio is what an SNR loss looks like: the same signal-to-noise as the schematic with the noise figure (NF)
10·log(1/0.672) = 1.7 dB higher. `lopex2` keeps the schematic's gain (−12.21 dB) and raises the NF from 11.7 to
13.4 dB (`lo_gain.py --nf`). It counts all of the loss as SNR and none as detector slope, so it errs on the safe side.
(At full gain the ratio is 0.632, −2.0 dB: the same loss.)

Result (25 runs, 2.0–2.3 min each; schematic baseband; `replay_corr.py` agrees with the event pin 25/25):

| Level, dBm | −84 | −86 | −88 | −90 | −92 |
|---|---|---|---|---|---|
| `lopex2` detected, as simulated | 5/5 | 3/5 | 3/5 | 1/5 | 0/5 |
| `lopex2` over burst timing | 100 % | **80 %** | **50 %** | **20 %** | 0 % |
| sch (`lo`, item 5) over burst timing | 100 % | 92 % | 55 % | 38 % | 30 % |

The extracted low-gain RX reaches 50 % at ≈ −88 dBm and ~80 % at −86, against ≈ −88.5 and 92 % on the schematic:
~0.5–1.5 dB worse, consistent with the 1.7 dB NF step at this slope. Five seeds a level (±20 %), so the shape is
reliable, not the last half dB. Pin order OK in all 25. **Low gain on the extracted chain: reliable at ≈ −85 dBm,
half the bursts at −88.** Against "detects at −88" that is the same ~half the schematic gives (last run passed it on
those terms).

### Why the extracted noise runs took 14-16 h

Two suspects (TODO.md): the bigger netlist, and a bug in the noise file. `sim/logdet/gen_noise.py` wrote its PWL
times as `{t:.4e}`, 5 significant figures, so from 1 µs on, 50 ps steps round onto each other: 20,000 of each
source's 60,002 points repeat or go back in time (the 80,000 "non-increasing PWL time points" warnings), across most
of `noise_tran.sh`'s 0.5–3 µs window. Fixed: 7 significant figures. Timing runs to 1.2 µs (0.2 µs past the first
repeated time), noise only, 3 threads each, sim-0 at load 4-9 of 28:

| Deck | Netlist | Old noise file, min | Fixed noise file, min | Det, old / fixed, V |
|---|---|---|---|---|
| schematic | | 0.8 | 0.8 | 1.45225 / 1.45261 |
| `lna_chain_t` alone (chain-only, as last run) | 0.83 MB | 44.1 | 47.7 | 1.46016 / 1.46047 |
| `rx_t` (chain + detector) | 1.65 MB | 172.1 | 172.3 | 1.45855 / 1.45879 |

**The noise file isn't the cause: the old and fixed files take the same time.** It's the netlist and the load:
- `rx_t` is 3.6× slower than the chain-only extraction, and that is 58× slower than the schematic.
- A full 3 µs `rx_t` run (`nt3_rx_t_*`, four at once, 3 threads each, load ~15-20) took 416 min, 6.9 h: the cost
  is even in time (172 min × 2.5 = 430). The main run's took 13-15 h with 12 of them at once
  alongside the extracted MC and stability, the machine at its 28-CPU limit: about 2× from load.
- The job file's 10 min was never measured. The last run's noise runs used the chain-only deck (~2 h each by this
  table) and their times weren't kept.

The 1.2 µs det levels barely move with the fix (≤ 0.4 mV); over the whole 3 µs window they do. Full 3 µs runs, det
mean over 0.5-3 µs, V:

| Bench | Gain | Noise only, old file | Noise only, fixed | −90 dBm, fixed | Drop at −90, old / fixed, mV |
|---|---|---|---|---|---|
| sch | full | 1.44406 | 1.44973 | 1.44729 | 2.24 / 2.44 |
| sch | low | 1.50975 | 1.51088 | 1.51046 | 0.43 / 0.42 |
| pex `rx_t` | full | 1.45416 | 1.45751 | 1.45605 | 1.42 / 1.46 |
| pex `rx_t` | low | 1.48445 | 1.48504 | 1.48476 | 0.29 / 0.28 |

Extracted against schematic drop at −90 dBm with the fixed file: 0.60× full gain (old 0.63×), 0.67× low gain (old
0.67×), so the `lopex2` calibration (0.672) holds. One noise waveform, one level: the drops are a few tenths of a mV
on a ±0.1 mV-class mean, so read the ratios to ±0.05.

The fix changes the noise the benches see: noise-only det +5.7 mV (sch) / +3.4 mV (`rx_t`) at full gain, +1.1 /
+0.6 mV at low gain. The old file's repeated points made steps, which add power. So `gen_det.py`'s calibration (`SHIFT_DB`, set so that noise alone gives 1.439 V) and `lo_gain.py`'s reference levels
should be redone from the fixed noise before the next run. Every comparison in this report is like for like (both
sides with the old file), so the findings stand.

## Run times

Follow-ups (`jobs_tall_follow.py`): 46 jobs, all OK, 13:06 → 22:56 (9.8 h), 146 declared thread-hours. Longest:
`nt3_rx_t` 416 min (4 × 3 threads), `joined_-90_s*` 212-223 min (2 threads), `timing_rx_t_*` 172 min, `stabx_sf27`
132-133 min (4 threads; the job file had 6 h), `timing_chain_t_*` 44-48 min; the 25 `lopex2` mixed runs 2.0-2.3 min
each. Merged into `sim/rerun/durations_tall.json`.

Main run, per job family, minutes, against `jobs_tall.py`'s estimates as they were for this run. "Measured" is the scheduler's
start to end, so it includes queueing inside a job (a lock, `xargs -P 1`) but not waiting to start. Every job ran
alongside ~10-25 others on 28 CPUs.

| Family | Jobs | Threads | Min, min | Median, min | Max, min | Estimate, min | Measured / estimate |
|---|---|---|---|---|---|---|---|
| nt_pex | 12 | 3 | 772.3 | 880.6 | 894.2 | 10 | 88.1x |
| pwrup | 6 | 1/4 | 103.8 | 396.1 | 679.5 | 180/420 | - |
| tile_pair | 2 | 4 | 560.7 | 585.7 | 610.6 | 540 | 1.1x |
| mc_chain (pex) | 5 | 4 | 254.8 | 400.4 | 522.6 | 15 | 26.7x |
| pwr_tran_tx | 1 | 2 | 398.3 | 398.3 | 398.3 | 120 | 3.3x |
| mixed (pex) | 12 | 1 | 271.5 | 289.1 | 374.0 | 180 | 1.6x |
| stabx | 10 | 4 | 305.1 | 331.0 | 339.3 | 40 | 8.3x |
| joined | 3 | 2 | 257.8 | 271.1 | 294.1 | 960 | 0.3x |
| tile_rc | 7 | 2/4 | 133.5 | 231.8 | 271.2 | 90/270 | - |
| tile_cw_rc | 2 | 5 | 73.8 | 100.2 | 126.5 | 150 | 0.7x |
| tx_corners (pex) | 1 | 1 | 105.4 | 105.4 | 105.4 | 30 | 3.5x |
| pwr_r_mesh | 1 | 2 | 79.8 | 79.8 | 79.8 | 30 | 2.7x |
| stab_t | 1 | 4 | 70.5 | 70.5 | 70.5 | 40 | 1.8x |
| cw_drop | 2 | 10 | 52.6 | 59.3 | 66.1 | 50 | 1.2x |
| pwr_z_ac | 1 | 2 | 57.4 | 57.4 | 57.4 | 30 | 1.9x |
| pad_ovl | 2 | 4 | 10.2 | 25.4 | 40.7 | 20/60 | - |
| tx_pex | 45 | 1 | 16.1 | 19.2 | 28.2 | 30 | 0.6x |
| tile_c | 4 | 4 | 9.2 | 17.5 | 18.1 | 15 | 1.2x |
| pwr_ir_rx | 1 | 2 | 17.6 | 17.6 | 17.6 | 20 | 0.9x |
| mc_chain | 5 | 4 | 9.5 | 12.1 | 14.0 | 15 | 0.8x |
| gl | 1 | 1 | 13.5 | 13.5 | 13.5 | 150 | 0.1x |
| formal_prove | 1 | 1 | 13.2 | 13.2 | 13.2 | 40 | 0.3x |
| tile_scan | 2 | 4 | 2.8 | 7.3 | 11.7 | 600 | 0.0x |
| tile_cw_sch_c | 2 | 10 | 6.2 | 7.6 | 9.1 | 15 | 0.5x |
| rtl, check_top, pwrup_sch, tb_comp_ct (pex), tile_lvs | 5 | 1-8 | 5.2 | 7.2 | 7.4 | 5-15 | 0.5-1.2x |
| mixed (sch baseband) | 127 | 1 | 1.8 | 2.2 | 4.8 | 20/25/40 | ~0.1x |
| tx, tx_corners, e2e, tt_gl, tile_tx, tile_sup, rxc_corners, mc_avg, mc_comp, nt_sch, lnalo, eqy | 90 | 1-8 | 0.2 | 1.5 | 3.0 | 2-120 | 0.0-0.6x |
| every other job (block checks, extractions, block benches, netlists, gen_*) | 120 | 1-8 | 0.2 | ~0.5 | 6.0 | 1-60 | ≤ 1.2x |

471 job runs; wall clock 41.0 h; **1286 declared thread-hours**. The full per-job table: `sim/rerun/durations_tall.json`
(minutes per job; `python3 sim/rerun/durations.py --json` writes it).

What the times say:
- **The critical path was the extracted noise runs** (12 × ~14.7 h at 3 threads each), then the extracted MC (up to
  8.7 h) and the extracted stability (5.5 h each). That is the `rx_t` netlist and the load, not a bug (follow-up
  timing runs above): expect the same next time unless the noise runs go back to the chain-only deck (~2 h each).
  A noise run needs a whole `rx_t` only for the detector's own level; the drop ratio against the schematic could
  come from the chain-only deck plus one `rx_t` pair.
- **The estimates in `jobs_tall.py` were copied from `jobs_lna_lo.py`**, written when those jobs were added and never
  measured. The old run's `sched.log` / `status.json` weren't kept. Every big miss was an extracted `rx_t` bench:
  `rx_t` (chain + detector, 1.65 MB, ~41,700 R) replaced last run's chain-only extraction (827 KB, ~22,000 R).
  - extracted stability: 35-55 min per case, 6 cases per job, longer as the shunt C grows;
  - extracted MC: 255-523 min against 15 (the schematic: 10-14 min);
  - extracted noise: 150-260 ns of simulated time per hour under load, ~420 ns/h at load 4-9; the schematic version
    takes 1.5 min.
- `tile_pair` keeps ~6 CPUs busy (two ngspice at ~3.1 each) against 4 declared. The load went to 37-39 on the
  28-CPU quota (the container's cgroup `cpu.max`) and everything ran ~5-10 % slower until it ended.
- Many short jobs ran 5-10x under their estimates. Harmless, except that a large `est` decides start order.

Put back for the next run:
- `jobs_tall.py` now takes every job's `est` from `durations_tall.json` (+10 %), the extracted noise runs
  included (~16 h: the timing runs showed the fix doesn't speed them up).
- The priority list no longer raises `est` to 20 h (that hid the real estimate from the scheduler's log and from its
  thread reservation): `sched.py` has a `prio` key for start order and a `reserve` key (the 10-thread `cw_drop`
  runs set it False instead of faking a short `est`).
- `tile_pair` declares 6 threads.

## Harness fixes made during the run (not design)

| Commit | Fix |
|---|---|
| 08a7b03, 26cf5bb | `sched.py`: start jobs by real load (1-min load + threads started in the last 90 s), declared threads only a cap; kill stalled jobs (no CPU for 30 min); heartbeat |
| 01a1127 | `sched.py`: a job held by a lock or its stagger doesn't reserve threads (`mc_chain_ff50`, locked behind `mc_chain_ss10_pex`, held 4 threads at load 24 with 195 jobs ready) |
| 378e1b7 | `sched.py`: a requeued job's stall clock starts afresh (it inherited its first run's CPU reading and was killed at once) |
| cfc1471, fd6f0f8, 378e1b7 | `net_mixed`: no job wrote `build/real/tb_radio_analog.spice`, the schematic baseband for `gen_mixed.py`, so every schematic mixed run failed at once. Judged by the netlist (`tools/osic` exits 1 after a good xschem run) |
| c5a728a, 55e4311 | the 10-thread `cw_drop` runs don't reserve threads; `pwr_z_ac` without the `tilemesh` lock (it waited ~4 h at load 5) |
| 18fd452, c665502 | `watch.py` reports every change; `durations.py` |

The load average over-counts multithreaded ngspice: `tile_pair` (2 × 8 threads) put ~16 on the load for ~6-7 CPUs of
work, which stalled the queue three times. For the next run, measure real CPU (`/proc/stat`) instead.

### The one failed job

`tb_amp_dpc_pex_amp_dpc_ts`: `tb_amp_dpc` has no `lna_lo_n` port, which the shunt stage `amp_dpc_ts` adds, so it
gives no results. It was dropped from the job list during the run (bb94e04); the scheduler kept its first, failed
attempt. The stage is covered by `strip_tt_lo` (68.2 dB, stage 2 1.08 dB at low gain).

### `exited` jobs: log check (all 29 ran to the end)

| Jobs | Last line of the log |
|---|---|
| `stab_t_tt`, `stabx_ss10_v1.62_glo1.8` / `_v1.8_glo0` / `_v1.8_glo1.8` | every case's "2 results" line; RESULT kick + ac in each case log |
| `mc_chain_sf27_pex`, `mc_chain_ss10_pex` | the step line (mean / σ / min / max, ≥ 9 dB) |
| `nt_pex_glo0_-80 / -84 / -86 / -88` | `RESULT` |
| `mixed_-92_pex`, `mixed_-94_pex` | event-open line, plot written |
| `tile_pair`, `tile_pair_glo0` | the full off − on table and the model line |
| `tile_rc_fs50`, `tile_rc_ss10`, `tile_rc_glo0` | op_rx / op_off / −60 dBm / TX lines |
| `tx_corners_pex`, 9 × `tx_pex_*` | ab + se for every corner (or the FAIL line at 1.71 / 3.6 ss / fs) |
| `pwrup_10u_ff50` | the full summary |
| `rtl` | TESTS=16 PASS=16 |

## 1. Digital

| Check | Reference | Now | |
|---|---|---|---|
| RTL cocotb | 16/16 | 16/16 | PASS |
| GL | 16/16 | 16/16 (803 s) | PASS |
| TT top RTL / GL | 5/5, 5/5 | 5/5, 5/5 | PASS |
| Formal prove (abc pdr) | PASS, 2139 s | PASS, 787 s | PASS |
| eqy (RTL vs netlist) | (new) | `nl` 108/108 proven, clocks PASS; mutations `bug_corr_and`, `bug_tx_mux`, `bug_acc_top`, `bug_clk_swap` all caught | PASS |
| Pinout | OK, 30 TT pins | OK, 30 TT pins, info.yaml = schematic = macro | PASS |
| export_vectors | bit-identical | bit-identical (no diff in `verilog/test/vectors`) | PASS |
| e2e default | noise −94 5/5, −98 0/5; fading −90 5/5, −94 3/5; bursty −70 5/5, −86 3/5; 0 false | identical | PASS |
| e2e H135 tt / fs50 | −94 27/48, −92 48/48 / −94 1/48, −92 45/48 | identical | PASS |

## 2. Layout signoff

| Check | Reference | Now | |
|---|---|---|---|
| check_top | precheck PASS, KLayout 0, magic 0, LVS match, antenna 7 | precheck PASS, 0, 0, LVS PASS, antenna 7; xor_gds: metal identical | PASS |
| check.sh | 24 blocks | **36 blocks** (the tall cells, `rx_t`, the decap parts): every one DRC 0 (magic + KLayout), antenna 0, LVS PASS | PASS |
| pex.sh | 14 blocks | 17 blocks done. The 12 unchanged blocks and `lna_chain_t` differ from the committed netlists in names / order only (equal line counts). `amp_dp_t`, `amp_dpc_t`, `amp_dpc_ts`, `chain_strip_t` and `rx_t` gain 70–690 lines: the committed ones predate the via arrays (the job file re-extracts them for that reason). The new netlists are committed with this report | PASS |
| pex_tile rc | 17,907 C, 84,365 R | **15,535 C, 76,549 R**, 70 ports, 1138 X/M, missing [] | CHANGED (re-route: RX in the corner) |
| pex_tile lvs / c | 1139 X/M, 70 ports; c 3111 C | 1138 X/M, 70 ports; c 2985 C | CHANGED (re-route) |
| via audit | (new) | single-cut vias per block and the tile, `build/rerun_tall/logs/via_audit.log` | info |
| back coupling, `rx_t` | (new) | 13 pairs two or more stages apart, 562.66 aF in all; largest o5p → o3p 129.35 aF | info |

## 3. Analog per block (tt)

| Block | Reference sch / pex | Now sch / pex | |
|---|---|---|---|
| amp_dp → `amp_dp_t` | 14.74 dB 1.525 mA / 15.58 dB 1.510 mA | 14.74 / 1.525; **15.55 dB 1.516 mA** (tall) | PASS (tall cell) |
| amp_dpc → `amp_dpc_t` | 13.59 dB 0.723 mA / 13.69 dB 0.716 mA | 13.59 / 0.723; **13.24 dB 0.720 mA** (tall) | CHANGED (tall cell, −0.45 dB per stage) |
| `amp_dpc_ts` (shunt stage) | - | no bench (see the failed job); `strip_tt_lo` stage 2 1.08 dB | - |
| det_cell | 1.7498 V, 6.64 mV / 1.7515 V, 5.57 mV | 1.7498, 6.64 / 1.7515, 5.56; pex Cin 9.7 fF (sch 1.4 fF) | PASS |
| log_det | 1.5197 V | 1.5197 V (sch only: `log_det_t` has no Cdet of its own) | PASS |
| lpf_rc | 14.75 kHz −89.4 dB / 14.65 kHz −106.9 dB | identical | PASS |
| avg_sc | τ 0.458 ms −0.015 mV / 0.423 ms +0.070 mV | 0.458 ms −0.015 mV / 0.423 ms −0.015 mV | PASS |
| r2r | 0.000 LSB 24.6 ns / ≤ 0.021 LSB 30.6 ns | identical | PASS |
| bias_gen | 59.36 / 59.31 µA | identical | PASS |
| dbg_tg | 0.53 / 4.11 / 1.13 kΩ; off −73.5 dB (pex) | 0.56 / 4.14 / 1.15 kΩ; off −73.4 dB | PASS |
| tx_ring | 485.5 / 530.1 MHz | 485.5 / **528.3 MHz** | PASS (−0.3 %) |
| tx_ls | 43.4 %, 45.7 / 50.5 % / 36.4 %, 41.4 / 48.3 % | 43.4 %, 45.7 / 50.5 % / 36.1 %, 41.1 / 48.3 % | PASS |
| tx_ls_en | 1112 / 1380 ps / 3574 / 3808 ps | 1112 / 1380 / **3827 / 3920 ps** | CHANGED (+250 / +110 ps extracted: re-extraction) |
| tx_drv | P_dip +5.49 dBm (pex) | +5.81 sch / +5.49 pex | PASS |
| comp_ct | −7.51 mV, 0.1344, 183.9 / −7.63 mV, 0.1359, 184.1 | −7.508, 0.1344, 183.9 / −7.646, 0.1362, 184.1 | PASS |

| Other analog | Reference | Now | |
|---|---|---|---|
| decap AC | VAPWR 42.63 pF, VDPWR 10.56 pF | **VAPWR 39.26 pF** (ESR 0.010 Ω), **VDPWR 20.66 pF** (0.094 Ω), flat to 434 MHz and ±10 % | CHANGED, expected (the new decap parts) |
| bias OTA loop | PM 89.99–91.50° | PM 89.99–91.50° (12 points) | PASS |

### Chain (schematic and extracted)

AC gain at 434 MHz, `tb_chain` (2 nH, real decap) and `sim/chain/lna_lo.sh`:

| Bench | tt 27 °C, dB | ss 10 °C, dB | ff 50 °C, dB | NF tt, dB |
|---|---|---|---|---|
| sch, full / low gain | 80.16 / 68.12 | 84.50 / 72.84 | 74.80 / 62.82 | 11.02 / 11.74 |
| `lna_chain_t` alone, extracted (bridge to the design note's 75.84) | **75.78** | - | - | - |
| `rx_t` extracted, full / low gain | **71.07 / 61.78** | 74.95 / 66.44 | 66.10 / 56.46 | 11.08 / 11.78 |
| strip (schematic stages), full / low | 78.30 / 68.20 | 82.24 | - | - |

`lna_chain_t` alone matches the design note (75.84 dB, Table IV of [tall_stages_2026-11.md](tall_stages_2026-11.md)).
Adding the detector and the tap wiring (`rx_t`) takes 4.7 dB off it. The detector's extracted input C is 9.7 fF per
cell against 1.4 fF in the schematic.

### Chain stability, extracted

`sim/chain/stability.sh` in `build/pexsim` (`rx_t` swapped into `tb_chain` by `sim/chain/mk_pex_rx.py`), real decap,
L 2 nH, a 1 µA kick. "ok" = the kick decays (growth ≤ 3e-9). "OSC n" = still ringing at the end (late p-p > 1 mV),
with the growth.

| Corner | Gain | 0 | 0.3 fF | 0.5 fF | 0.75 fF | 1 fF | 1.5 fF | 2 fF | 3 fF |
|---|---|---|---|---|---|---|---|---|---|
| ss 10 °C 1.8 V | full | ok | ok | ok | ok | OSC 0.56 | OSC 1.00 | | |
| ss 10 °C 1.8 V | **low** | ok | | ok | | ok | **ok** | ok | OSC 1.13 |
| ss 10 °C 1.62 V | full | ok | ok | ok | ok | ok | OSC 1.01 | | |
| ss 10 °C 1.62 V | **low** | ok | | ok | | ok | **ok** | OSC 0.07 | OSC 1.00 |
| ss 10 °C 1.98 V | full | ok | ok | ok | ok | OSC 1.02 | OSC 1.00 | | |
| ss 10 °C 1.98 V | **low** | ok | | ok | | ok | **ok** | ok | OSC 1.44 |
| tt 27 °C 1.8 V | full | ok | ok | ok | ok | ok | OSC 0.03 | | |
| tt 27 °C 1.8 V | **low** | ok | | ok | | ok | **ok** | ok | ok |
| ff 50 °C 1.8 V | full | ok | ok | ok | ok | ok | ok | | |
| ff 50 °C 1.8 V | **low** | ok | | ok | | ok | **ok** | ok | ok |
| sf 27 °C 1.8 V (follow-up) | full | ok | ok | ok | ok | ok | OSC 0.01 | | |
| sf 27 °C 1.8 V (follow-up) | **low** | ok | | ok | | ok | **ok** | ok | ok |
| `lna_chain_t` alone, tt | full | ok | ok | ok | ok | OSC 1.01 | OSC 1.00 | | |

**Pass.** Full gain is stable to 0.75 fF everywhere (budget 0.1 fF); low gain to 1.5 fF everywhere, against 1 fF on
the U chain (reference: ss 10 °C 1.62 V, 1 fF ok, 1.5 fF oscillates). `lna_chain_t` alone at tt reproduces the
design note's Table IV exactly (0.75 fF ok, 1 fF oscillates); `rx_t`'s lower gain moves it to 1 fF.

Schematic (`stab_tt`, `stab_ss10`, `stab_ss10_v189`): stable to 0.1 fF, 1 fF growth 0.99, 84.49 dB at ss 10 °C
(ss 10 °C 1.89 V 84.93 dB, reference 84.89).

### Gain step, Monte Carlo

`sim/chain/mc_chain.py`, 1000 mismatch samples per corner, both gains on the same draw. Gain at 434 MHz.

| Corner | Bench | Step mean / σ / min, dB | ≥ 9 dB | Nominal step, dB | Reference (U chain) mean, dB / ≥ 9 dB |
|---|---|---|---|---|---|
| tt 27 | sch | 12.03 / 0.24 / 11.16 | 100 % | 12.04 | 12.03 / 100 % |
| ss 10 | sch | 11.53 / 0.34 / 10.21 | 100 % | 11.52 | 11.52 / 100 % |
| ff 50 | sch | 12.25 / 0.18 / 11.66 | 100 % | 12.26 | 12.27 / 100 % |
| fs 27 | sch | 12.90 / 0.17 / 12.17 | 100 % | 12.90 | 12.90 / 100 % |
| sf 27 | sch | 10.54 / 0.41 / 9.09 | 100 % | 10.55 | 10.55 / 100 % |
| tt 27 | **pex `rx_t`** | 9.27 / 0.26 / 8.44 | **85.0 %** | 9.29 | 10.17 / 100 % |
| ss 10 | **pex** | 8.50 / 0.37 / 6.96 | **8.2 %** | 8.49 | 9.41 / 86.4 % |
| ff 50 | **pex** | 9.63 / 0.20 / 8.57 | 99.9 % | 9.64 | 10.41 / 100 % |
| fs 27 | **pex** | 10.25 / 0.18 / 9.65 | 100 % | 10.26 | 11.12 / 100 % |
| sf 27 | **pex** | **7.58** / 0.45 / 5.63 | **0 %** | 7.57 | 8.45 / 9.3 % |

Full gain within 1 dB of nominal: 99.4–100 % of samples at every corner. The schematic is unchanged. Extracted, the
step is 0.8–0.9 dB smaller than the U chain's at every corner.

The block extraction is pessimistic, as last time. On the extracted tile (CW at the pads, noise-free, below), full
against low gain at −90 dBm is 10.2 dB (rc) at tt, where `rx_t` gives 9.27: ~0.9 dB more. Last run's tile gave 11.9
at tt and 10.1 at sf. With the block's tt → sf difference (1.7 dB), sf on the tile is ~8.5 dB. Below 9 dB nominal,
so this passes only with the spec stated as a stability margin, as last time. The sf stability follow-up decides it.

## 4. RX sensitivity, extracted

### CW detector drop, extracted `rx_t` (`sim/chain/cw_drop.py --rx`, tt, noise-free)

| Level, dBm | sch, mV | pex `rx_t`, mV | pex − sch, dB | Reference pex (blocks), mV | Now − reference, dB |
|---|---|---|---|---|---|
| −100 | 0.52 | 0.17 | −4.86 | 0.26 | −1.84 |
| −90 | 5.17 | 1.68 | −4.88 | 2.67 | −2.01 |
| −80 | 41.82 | 15.77 | −4.24 | 24.03 | −1.83 |
| −70 | 173.79 | 95.31 | −2.61 | 123.59 | −1.13 |

Log region (−84…−72 dBm), pex − sch: −4.65…−3.02 dB (reference −2.66…−1.69). det idle: sch 1.5197 V, pex 1.4893 V.

### Extracted tile (`sim/top/tb_tile.py`)

| Run | Reference | Now | Δ | |
|---|---|---|---|---|
| tile lvs | 2.987 mA, +3.07 dBm 680 MHz | 2.987 mA, +3.07 dBm, 679.6 MHz | 0 | PASS |
| tile c | 2.987 mA, 0.910 µA, det 1.4915 V, −60 dBm 1.2152 V, +3.38 dBm 537.3 MHz | 2.987 mA, 0.910 µA, 1.4915 V, **1.2287 V**, +3.45 dBm, 535.1 MHz | −60: +13.5 mV | CHANGED (RX gain) |
| tile rc | 2.985 mA, det 1.4912 V, −60 dBm 1.2142 V, +3.13 dBm 519.3 MHz | 2.985 mA, 1.4914 V, **1.2282 V**, +3.19 dBm, 517.2 MHz | −60: +14.0 mV | CHANGED (RX gain) |
| tile c, low gain −60 dBm | 1.3489 V | 1.3551 V | +6.2 mV | CHANGED |
| rc fs50 / ss10 / ff50: det idle | 1.4998 / 1.5022 / 1.4752 V | 1.5000 / 1.5024 / 1.4754 V | 0 | PASS |
| −60 dBm | 1.2442 / 1.1840 / 1.2683 V | 1.2591 / 1.1933 / 1.2762 V | +14.9 / +9.3 / +7.9 mV | CHANGED (RX gain) |
| TX rc fs50 / ss10 / ff50 | 530.4 / 427.1 / 587.6 MHz, +2.91 / +3.45 / +2.29 dBm | 528.2 / 425.3 / 585.4 MHz, +3.00 / +3.49 / +2.39 dBm | ≤ +0.1 dB | PASS |
| rc 10 / 50 °C | +2.66 dBm (50 °C) | +3.53 / +2.73 dBm; op_off 0.908 / 0.919 µA (`ring` 1.8 V) | | PASS |
| Tile scan | flips 180 / 181 | 180 / 181 (both gains) | 0 | PASS |

CW det drop at the pads, noise-free, trim held, mV:

| Level, dBm | sch full / low | c full / low | rc full / low | Reference rc full / low |
|---|---|---|---|---|
| −100 | 0.51 / 0.04 | 0.36 / 0.04 | 0.36 / 0.04 | 0.61 / 0.04 |
| −90 | 4.97 / 0.32 | 3.53 / 0.33 | **3.55 / 0.34** | 5.97 / 0.39 |
| −80 | 40.38 / 3.14 | 30.59 / 3.27 | 30.70 / 3.29 | 46.93 / 3.88 |
| −70 | 170.00 / 27.45 | 141.16 / 28.61 | 141.49 / 28.79 | 165.62 / 33.07 |

The schematic is unchanged (−90: 4.97 vs 4.92 mV). Extracted full gain is **−2.26 dB** against the reference at −90
dBm (rc), −1.46 dB against this run's schematic (the U chain was +0.84 dB above its schematic). Low gain lost less
(−0.6 dB), so the tile's step went from 11.9 to 10.2 dB at −90 dBm.

### Joined RX pair (`tb_tile_joined.py pair`, extracted tile, 30 µs)

det off − on, mV, by window after key-on:

| Case | 1–5 µs | 5–10 µs | 10–20 µs | 20–30 µs | 2–30 µs | Reference 2–30 µs | Δ, dB |
|---|---|---|---|---|---|---|---|
| full gain, −92 dBm | 1.02 | 1.04 | 0.83 | 1.13 | **1.00** | 1.35 | −1.30 |
| low gain, −88 dBm | 0.49 | 0.46 | 0.45 | 0.47 | **0.46** | 0.54 | −0.70 |

LPF 2–30 µs: 0.63 / 0.30 mV. Model at −92 dBm: ~1.14 mV.

### Joined RX, schematic (`sim/rx/joined.sh`, 400 µs, `trnoise`; `sim/rx/plot_joined.py`)

| Level | Reference | Now | |
|---|---|---|---|
| −90 dBm: det swing (LPF), mV | 1.83 (1.04); model 1.80 | 3.09 (3.12); model 1.80. Three reruns 1.87 / 2.62 / 2.06; mean of four 2.41 ± 0.55 | PASS: realisation noise (below); `noise_tran` gives 2.24-2.44 |
| −70 dBm: det swing, mV | 100.75; model 105.6 | 104.20 (LPF 102.32); model 105.58 | PASS (+0.15 dB) |
| −10 dBm: det off → on, V | 1.4533 → 0.5694 | 1.4499 → 0.5693 | PASS |

The comparator edge times at −10 dBm weren't re-measured.

**The −90 dBm swing (3.09 mV) is within the run-to-run noise.** Each run is one `trnoise` realisation, and it can't
be repeated (neither `set rndseed` nor `.options seed` reaches `trnoise`: tested 2026-11-17):
1.43 mV on 2026-10-13, 1.83 last run, 3.09 now. Split by chip, the det (V) in this run:

| Window | off 20–60 µs | on 62–164 µs | off 166–268 µs | on 270–372 µs | off 374–400 µs |
|---|---|---|---|---|---|
| det mean, mV | 1450.54 | 1447.74 | 1451.95 | 1448.92 | 1450.73 |

- The two chips give 3.50 and 1.92 mV against their neighbouring off windows: the chips differ from each other by as
  much as this run differs from the last.
- The noise-only level wanders by ~0.6 mV rms from one ~100 µs window to the next (the six off windows of the −90 and
  −70 runs: 1450.5–1452.1 mV, the same in both). A swing from three off and two on windows is ±0.55 mV.
- The model's 1.80 mV isn't the right yardstick. The transistor-level noise bench (`noise_tran`, same schematic
  chain and detector) gives a −90 dBm drop of 2.24 mV (old noise file) / 2.44 (fixed), unchanged from the last run;
  `gen_det.py` is ~1.3× low there (at −92 too: 1.54 against 1.15). Against ~2.3 mV, 3.09 is +1.4σ; 1.43 and 1.83 are
  −1.6σ and −0.9σ.
- The chain didn't change the signal: the schematic CW at the pads is the same (−90 dBm 4.97 against 4.92 mV), and so
  is `noise_tran` to 0.01 mV.

Three more realisations (`TAG=_s<n> sim/rx/joined.sh`, follow-up jobs
`joined_-90_s{1,2,3}`, 212-223 min each on 2 threads), measured as `plot_joined.py` does:

| Run | det off, mV | det swing, mV | LPF swing, mV |
|---|---|---|---|
| main run | 1451.42 | 3.09 | 3.12 |
| rerun 1 | 1452.93 | 1.87 | 2.15 |
| rerun 2 | 1449.76 | 2.62 | 2.92 |
| rerun 3 | 1448.22 | 2.06 | 2.55 |
| mean ± sd of the four | 1450.6 ± 2.1 | 2.41 ± 0.55 | 2.69 ± 0.43 |

**Settled: noise.** The four realisations average 2.41 mV, which matches `noise_tran`'s 2.24 / 2.44 mV (old / fixed
noise file), with a spread of ±0.55 mV per run, as the window statistics predicted. 3.09 is +1.2σ. The last run's
1.83 and the 2026-10-13 run's 1.43 are −1.1σ and −1.8σ: one run is not enough to compare at −90 dBm. Next time, run three
at −90 dBm and compare means. The noise-only level wanders too (1448.2-1452.9 mV between runs).

### noise_tran (`sim/logdet/noise_tran.sh`, 3 µs, old noise file)

Det mean, V:

| Bench | Gain | Noise only | −80 | −84 | −86 | −88 | −90 | −92 | −94 |
|---|---|---|---|---|---|---|---|---|---|
| sch | full | 1.44406 | | | | 1.44075 | 1.44182 | 1.44252 | 1.44301 |
| sch | low | 1.50975 | 1.50654 | 1.50835 | 1.50881 | 1.50912 | 1.50932 | 1.50946 | |
| pex `rx_t` | full | 1.45416 | | | | 1.45208 | 1.45274 | 1.45319 | 1.45348 |
| pex `rx_t` | low | 1.48445 | 1.48229 | 1.48351 | 1.48382 | 1.48403 | 1.48416 | 1.48425 | |

off − on, mV: full gain −92 dBm 1.54 (sch) / **0.97** (pex), reference 1.53 / 1.53; low gain −88 dBm 0.63 / **0.42**,
reference 0.63 / 0.80. The schematic is unchanged to 0.01 mV. Extracted, the drop is 0.63× (full) and 0.67× (low) of
the schematic, −2.0 / −1.7 dB. The U chain's block extraction gave 1.00× and 1.27×.

## 5. Mixed signal

Full gain (the det waveform is `gen_det.py`'s model at gain 0, so the RF side is the reference's; the baseband is
schematic, or extracted with `--pex`):

| Level | Reference | Now | |
|---|---|---|---|
| −70 dBm | 14.678 ms | 14.678 ms | PASS |
| −90 dBm | 14.670 ms | 14.670 ms | PASS |
| −92 sch, 5 seeds | 5/5 (14.667–14.670 ms) | 5/5 (14.667–14.670 ms) | PASS |
| −92 pex, base + 5 seeds | 6/6 (14.661–14.668 ms) | 6/6 (14.664–14.666 ms) | PASS |
| −94 sch / pex (information) | 3/6 / 1/6 | 3/6 / 3/6 (pex s3, s4, s5) | PASS (statistics of 6) |
| −70 trim bits swapped | PIN ORDER PROBLEM | PIN ORDER PROBLEM | PASS |
| Pin order, every other run | OK | OK | PASS |

Overload (weak-burst event after a −10 dBm burst, ms):

| Gap, ms | 0.1 | 0.25 | 0.3 | 0.4 | 0.5 | 1 | 2 | 5 |
|---|---|---|---|---|---|---|---|---|
| reference | 27.981 | 28.138 | missed | missed | missed | 28.893 | 29.879 | 32.866 |
| now | 27.981 | 28.138 | missed | missed | missed | 28.893 | 29.879 | 32.866 |

Identical (finding #13 as restated 2026-11-06: ~2–3 dB desensitisation for ~1 ms, no dead time).

Low gain, schematic det model (`gen_det.py --gain` −12.21 dB, reference −12.26), schematic baseband. Detected as
simulated, then over burst timing by `sim/mixed/replay_corr.py` (RTL phases and one sample later; the replay agrees
with the simulated event pin in 70/70 runs):

| Level, dBm | Detected | Over burst timing | Reference: detected / over burst timing |
|---|---|---|---|
| −84 | 5/5 | 100 % | 5/5 / - |
| −86 | 20/20 | **92 %** | 19/20 / 90 % |
| −88 | 2/20 | **55 %** | 7/20 / 68 % |
| −90 | 14/20 | **38 %** | 16/20 / 40 % |
| −92 | 3/5 | 30 % | 2/5 / - |
| no signal (−150) | **0/10** | | 0/10 |

**Pass**, as the reference: reliable at −86 dBm, 50 % at ≈ −88.5 dBm. The −88 / −90 inversion as simulated is the
bench's fixed burst timing (reference follow-up 2026-11-06). −88 at 55 % against 68 % is two-thirds of a seed's
binomial σ (±11 % at 20 seeds) apart.

The extracted low-gain runs (`lopex`) as run: −84 to −90 dBm 5/5, −92 1/5. **Invalid**: their `--gain` (−5.59 dB)
put 6.6 dB too much signal at the detector. Rerun as `lopex2` (follow-ups).

## 6. Corners, temperatures, supply

| Item | Reference | Now | Δ | |
|---|---|---|---|---|
| RX 10 / 50 °C (`rx_corners`, sch): current | 2.84–2.91 mA | 2.84–2.91 mA | 0 | PASS |
| gain at 434 MHz | 73.1–80.9 dB | 73.1–81.0 dB | 0 | PASS |
| NF | 9.4–12.0 dB | 9.4–12.0 dB | 0 | PASS |
| det idle | 1.499–1.535 V | 1.499–1.535 V | 0 | PASS |
| slope | 9.8–14.0 mV/dB | 9.8–14.0 mV/dB | 0 | PASS |
| comp offset at mid-trim | −5.7…−9.2 mV | −5.7…−9.2 mV (ss rows reach −1.0 at the CM edge, as before) | 0 | PASS |
| trim span; step | −13.3…−14.5 / +5.7…+10.5 mV; 0.136–0.147 mV/LSB | identical | 0 | PASS |
| sf, CM 1.55 V | no result (known) | no result (known) | | PASS |
| TX sch, 5 corners | +4.14 / +4.26 / +4.14 / +4.23 / +4.14 dBm; SE −2.16…−2.64 | identical; SE −2.16…−2.64 dBm | 0 | PASS |
| TX extracted, 5 corners | +3.66…+3.85 dBm; SE −2.58…−3.25 | +3.72 / +3.83 / +3.65 / +3.81 / +3.71 dBm (tt ss ff sf fs); SE −2.59…−3.27 dBm | ≤ 0.02 dB | PASS |
| Tile TX 10 / 50 °C | +4.41…+4.55 / +3.75…+3.89 dBm | +4.41…+4.55 / +3.75…+3.89 dBm; 400–549 MHz | 0 | PASS |
| TX supply, schematic (8 points × 5) | = verify_supply_mc 2.1; ss 1.71 / 3.6 FAIL | every value identical; ss 1.71 / 3.6 FAIL (fs 1.71 / 3.6 +3.42 dBm) | 0 | PASS |
| TX supply, extracted (9 × 5) | = supply_mc; ss / fs 1.71 / 3.6 FAIL; ss / fs 1.71 / 3.3 +2.22 / +2.21 dBm | within 0.08 dB of supply_mc at every other point; ss / fs 1.71 / 3.6 FAIL; ss / fs 1.71 / 3.3 **+1.71 / +1.61 dBm** | **−0.51 / −0.60 dB** | CHANGED at the marginal `tx_ls_en` points (finding #2; 1.71 V doesn't occur on the board). They moved +0.43 last run with no design change: these two points are sensitive to small changes |
| Analog top over supply (6 points, sch) | −60 dBm 1.1699 / 1.2516 / 1.1243 / 1.1977 / 1.3440 V; ss 1.71 / 3.6 FAIL | −60 dBm 1.1695 / 1.2510 / 1.1239 / 1.1973 / 1.3436 V; ss 1.71 / 3.6 FAIL; ss 1.71 / 3.0 off in > 18 ns (the window, see reference) | −0.4 mV | PASS |

### Mismatch

| | Reference | Now | |
|---|---|---|---|
| comp_ct MC, 6 corners CM 1.5 V | 100 % ≤ 0.19 mV/LSB, σ 2.16–2.51 mV, code 172–181 ± 17–20, max 239 | 100 %, σ 2.09–2.43 mV, code 170–181 ± 16–19, max **246** (tt27: 1 sample > 242), 0 dups | PASS (new seeds) |
| comp_ct sf 10 / 27, CM 1.45 V | 99.5 % / 100 %, code 135 / 151 | 100 % / 100 %, code 133 / 150 | PASS |
| avg_sc tt 27 | −0.023 ± 0.143 mV, a 0.0280 | −0.038 ± 0.150 mV, a 0.0280 (fs50 −0.023 ± 0.133, sf10 −0.065 ± 0.149) | PASS |

## 7. Power-up, pad overload, power-off

| Item | Reference | Now | |
|---|---|---|---|
| Fast ramp c, tt / ss10 / ff50: LPF / avg settle | 1.491 / 1.504 / 1.491; 2.648 / 2.661 / 2.648 ms | 1.478 / 1.478 / 1.478; 2.648 / 2.642 / 2.642 ms | PASS |
| \|tx_p\|, end current | 48.3 / 286.4 / 15.8 mV; 2.985 / 3.017 / 2.945 mA | 48.9 / 288.0 / 18.0 mV; 2.984 / 3.017 / 2.945 mA | PASS |
| Slow ramp: vcm 95 %, LPF, avg | 6.259 / 6.258 / 6.260 ms; 0.666 / 0.640 / 0.692; 2.090 / 2.077 / 2.116 ms | 6.260 / 6.259 / 6.260; 0.653 / 0.627 / 0.692; 2.077 / 2.051 / 2.116 ms | PASS |
| Schematic fast ramp | LPF 1.569, avg 2.726 ms, 2.972 mA | identical | PASS |
| VDPWR only | 0.910 / 0.907 / 1.015 µA | 0.910 / 0.907 / 1.015 µA | PASS |
| VAPWR only | 1.8 / 0.5 / 16.4 nA, tx 3.3 V | 1.8 / 0.5 / 16.4 nA, tx 3.3 V | PASS |
| Pad 0 dBm | −0.293…+0.296 V, det back 0.2 µs | identical | PASS |
| Pad +6 dBm | ±0.59, 1.155 V, 11.65 mA, vcm 1.2012 V, det back 0.3 µs | identical | PASS |

## 8. Power delivery (case A)

| Item | Reference | Now | |
|---|---|---|---|
| R to the RX (chain, now `rx_t`) VDPWR / VGND | 2.92 / 4.40 Ω | 3.68 / 3.90 Ω (mean) | CHANGED (re-route: RX in the corner) |
| R tx_drv_p VAPWR / VGND | 0.77 / 0.81 Ω | 0.83 / 0.74 Ω | CHANGED (TX VAPWR feed) |
| R comp_ct VDPWR / VGND | 8.94 / 8.20 Ω | 6.94 / 4.36 Ω | CHANGED (better) |
| IR at tx_drv_p, VAPWR / VGND (avg / peak) | 5.6 / 18.7, 2.7 / 16.3 mV | 7.7 / 21.4, 2.3 / 12.2 mV (mean; worst 8.7 / 24.2, 3.1 / 15.9) | CHANGED (TX VAPWR feed; inside the job file's expected 13.3 / 36.7 mV) |
| EM, VAPWR (TX average, 13.3 mA) | via4 / met4 / mcon 42.4 / 28.8 / 71.2 % | mcon 68.5 %, via4 47.4 %, m3 38.0 %, m1 37.7 % (mcon under 2× margin: point injection reads high, docs/power.md) | CHANGED (TX feed; as before, mcon the worst) |
| EM, VGND (TX average) | mcon 40.1 % | mcon 40.1 %, m1 26.1 %, via4 18.1 % | PASS |
| \|Z\| at 434 MHz (Zdd) | chain 15.38, comp_ct 19.35, avg_sc 21.56 Ω | comp_ct 16.39, avg_sc 14.90, bias 29.94 Ω | CHANGED (re-route; lower) |
| TX → det at 434 MHz | 0.020 Ω | **0.111 Ω**; vcm 0.178, lpf / avg 0.152 Ω | CHANGED, worse ×5.5: the RX moved next to the TX driver. In `pwr_tran_tx` it gives 1.49 mV at 434 MHz on det (reference 3.48 mV): the keyed transient is lower |
| TX keyed: tx_drv_p / tx_drv_n dd p-p (434 MHz) | 29.08 (1.43) / 19.25 mV | 28.84 (1.27) / 23.23 (0.95) mV | PASS / CHANGED (TX feed) |
| RX blocks dd p-p / 434 MHz | 5.96–6.16 / 0.21–0.22 mV | 5.42–5.80 / 0.26–0.28 mV | PASS |
| det at 434 MHz (keyed) | 3.48 mV | **1.49 mV** | CHANGED (better) |

## Expected differences (from the job file), found

- RX ~1-1.5 dB down on the extracted tile: found −1.3 dB (tile pair), −2.0 dB (noise), −2.3 dB (tile CW). A little
  more than expected; see finding 2.
- Decap VAPWR ~39 / VDPWR ~21 pF: 39.26 / 20.66 pF.
- TX VAPWR at tx_drv_p 13.3 / 36.7 mV avg / peak (case A): `pwr_ir_rx` gives 7.7 / 21.4 mV mean, 8.7 / 24.2 mV worst at
  the driver, inside the expectation. `rx_t` VDPWR 15.8 mV is a case B number; this job list runs case A only.
- Pinout and the `ua[0]` stub: pinout OK; tile LVS PASS.
