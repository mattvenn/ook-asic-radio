# Where we are (handoff, end of 2026-10-08)

Read **PLAN.md** for the decisions and their evidence. This file is the "pick up from here" note: the summary and next steps first, per-block detail below.
Repo: github.com/mattvenn/ook-asic-radio (`main`, pushed).

## Start here

**State (end of 2026-10-08):**
- **RX:** every analog block has a working first pass at tt, transistor level: pad → 6-stage NMOS diff-pair limiting chain → successive-detection log detector → 14 kHz RC LPF → switched-cap average (τ 0.47 ms) → continuous comparator with DAC trim.
  - The bit-exact digital detects a −94 dBm burst (score 99/127, threshold 97): **right at the edge.** −70 dBm is clean.
  - Plots: `sim/plots/rx_rf.png`, `rx_bb.png`.
  - **The fully joined transistor-level run (antenna → comparator, RF noise, −70 dBm) matches the split model** (2026-10-08, below).
- **TX: xschem blocks done** (`xschem/gen/tx.py`: `tx_ring`, `tx_ls`, `tx_drv`, `tx_top`, `tb_tx`; run `sim/tx/tb_tx.py [corners]`): ring (nand + 22 inv_2) → skewed level shifter → thick NAND-gated tapers → antiphase drivers → pad → dipole. **+3.7…+3.9 dBm at all five corners**; ~420 MHz expected on silicon. Off: both arms low. Single-ended fallback built in (en_n = 0).
- **Area:** fits a **3x2** (available) with the digital as is. Clock gating is the first lever if space runs short.
- **PLAN.md was brought up to date on 2026-10-08** (architecture, block table, open risks).
- RTL done (not resized); layout not started.

**The joined overnight run (done 2026-10-08 12:08, 14.3 h):** the fully joined transistor-level RX at −70 dBm (antenna → comparator, with RF noise, 400 µs, real chip timing; `sim/rx/joined.sh`). Plot: `sim/rx/plot_joined.py -70` → `sim/plots/rx_joined.png`.

| −70 dBm | det off | det on | det swing | LPF noise, signal off (1 µs det std) |
|---|---|---|---|---|
| joined (transistor level) | 1.4411 V | 1.3407 V | **100.4 mV** | **0.52 mV** rms (1.88 mV) |
| split model (gen_det.py) | 1.4381 V | 1.3325 V | 105.6 mV | 0.59 mV rms (2.12 mV) |

- Swing −5 % (~0.4 dB at 12.6 mV/dB); noise-only fluctuation, which is what sets −94 dBm, within ~10 %. The comparator follows the chips, and avg / trim behave as in the split runs. **RX first pass confirmed.**
- With the signal on, the LPF noise is higher in the joined run (1.06 vs 0.52 mV). That's irrelevant at a 100 mV swing, and statistically thin (2 × 64 µs).
- **Optional −90 run, shorter** (would check the near-sensitivity regime directly):
  ```
  tools/longrun joined90 tools/osic bash -c 'cd build && LEVELS=-90 TSTOP=250u ../sim/rx/joined.sh'
  ```
  ~6–10 h, keeps the PC awake.

**Next steps, in order:**
1. ~~Joined-run check~~ (done: matches). ~~TX into xschem blocks~~ (done, "TX xschem blocks" below).
1b. ~~ua[4] debug~~ (done 2026-10-08: det via a debug-only transmission gate, `dbg_en` strap).
2. ~~Digital for the TX enables~~ (done 2026-10-08): `radio_digital` has a new output `tx_en_n` (= `tx_en` unless single-ended); `tx_en` drives both the ring `key` and `en_p`. The single-ended strap is `uio_in[3]`, latched at reset only with the `1010` magic. **Full cocotb suite 14/14 pass** (incl. the new `test_single_ended_strap`; run with the project venv first on PATH, see below). Not re-hardened.
3. **Corners and temperature, whole design** (the main open risk):
   - **Operating range is 10–50 °C only** (decided 2026-10-08): no design effort for extremes.
   - RX gain, NF, detector slope, comparator offset/trim range, and −94 dBm margin at ss/ff/sf/fs, 10 / 27 / 50 °C. **Running** (`sim/corners/rx_corners.sh`, table: `sim/corners/rx_corners.py`); results in "RX corners" below.
   - Caveat: the chain and detector R/C are still ideal (`devices/res`, `devices/capa`), and bias is ideal, so this is MOS variation only. Converting them to poly/MIM (and a bias whose gm tracks the load poly) belongs to step 4.
   - TX: process corners done (`sim/tx/tb_tx.py`); 10/50 °C still to do.
   - Use `option temp` after `reset` (see `docs/sim_learnings.md`).
4. **Make the analog real:**
   - ~~real passives in chain + detector~~, ~~bias generator with power-down on rx_en~~ (done 2026-10-08, below); integrate bias_gen at the top;
   - VAPWR decoupling + bond-wire droop (10 mA TX step);
   - ~~hook up the R2R DAC~~ (done: `r2r` schematic matching the reused layout, driven from `trim_out`, below);
   - overload recovery.
5. **RTL:** the full suite now passes (14/14, 2026-10-08). The digital size stays as is unless space is needed (then clock gating).
6. **Layout + integration in a 3x2** (PLAN phase 4). Switch the template from 2x2 to 3x2.

**Parked:** 63-chip Gold code (e2e first), tnt's `rf_top` SRAM (if data mode needs buffers), dipole tuning (wait for real radios), wire-as-matching antenna idea, SDR bench tests (not needed).

**How to run things:**
- cocotb: `cd verilog/test && PATH=$HOME/work/asic-workshop/venv/bin:/usr/bin:/bin make` (~12 min). With the login PATH, oss-cad-suite's python (no numpy) gets picked up and the run dies at import. `COCOTB_TEST_FILTER` takes one test name (a `|` alternative matched nothing).
- Generators: `python3 xschem/gen/<x>.py`. Netlist: `tools/osic bash -c 'xschem -n -s -q -o build xschem/<tb>.sch'` (grep the netlist for `IS MISSING`).
- Simulate in `build/` via `tools/osic`. Analysis/plots: `~/work/asic-workshop/venv/bin/python` (system python has no numpy).
- `tools/osic` copies the tracked root `.spiceinit` into `build/` each run.
- **Don't run ngspice processes in parallel** (each uses 8 threads), and **don't edit a script while it's running**.
- **All the xschem/ngspice traps and speed lessons are in `docs/sim_learnings.md`.** Read that before writing a new testbench.

## Done
- **Phase 0 bench** (bench/, results in PLAN.md): the ring osc as an OOK TX, path loss, drift, keying, phase noise, recorded packets, antenna test.
- **Phase 1 model:**
  - `model/radio.py` + `model/gold.py`: bit-exact code-mode digital.
  - `model/e2e.py`: about −94 dBm, no false toggles.
  - Vectors and the timing contract in `verilog/test/vectors/`.
- **Repo restructured** to the TT analog template, following the R2R DAC flow:
  - ttsky26d, **2x2 + VAPWR**, top `tt_um_mattvenn_radio`;
  - root `xschemrc` (netlists go to `build/`);
  - `tools/osic` runs the IIC-OSIC image headless from the repo.
- **Decisions since PLAN was last summarised (all recorded in PLAN.md):**
  - Retargeted to **433.92 MHz**; dipole arms ~16.5 cm.
  - **3.3 V TX output stage is in.** The TT "4 mA" limit is electromigration/RMS (tnt): not a concern.
  - Raw modes: `uio[3]` = comparator out, `uio[2]` = TX key in. Floating `uio` must give code mode.
  - Ring frequency trim + counter is a stretch goal (needed for fixed-code remote replay).
- **Analog step 1 done:** `xschem/tb_input.sch` (generated by `xschem/gen/tb_input.py`): antenna → pad_model → core.
  - The core sees −2.2 dB of the dipole EMF at 433.92 MHz: ~3.8 mVpp diff at −50 dBm, ~24 µVpp at −94 dBm.
  - Plot: `sim/plots/tb_input.png`.

## RTL (done by an agent; see verilog/RTL_REPORT.md)
- **Tests:** `verilog/rtl/` matches the model bit-exact on all 9 RX vectors, plus TX/debounce/raw/sc_phi tests: 13 cocotb tests, a ~11.5 min run. The `results.xml` left behind only holds a final 2-test run, so **rerun the full suite once to confirm**. Check with `! grep -q '<failure' results.xml` (plain 'failure' also matches failures="0").
- **Size problem:** 716 flip-flops, ~24,300 µm² of cells, **~40,500 µm² placed = ~54% of the 2x2 tile**. Too big next to the analog. The 4 × 127-bit chip registers are 63% of it.
  - Options: clock-gate the phase registers (−5,000 µm² cells, no behaviour change); 2 timing phases instead of 4 (−7,600 µm²; **re-run `model/e2e.py` first** to check sensitivity). Together → ~23,000 µm² placed (~31%).
  - Data mode would add ~4,500 µm² of cells.
- **Decision (2026-10-08): 3x2 is available, so the digital stays as is for now. If space is needed, clock-gate the chip registers first** (~−8,400 µm² placed, no behaviour change). 2 phases: no (costs sensitivity).
  - Considered and parked: tnt's `rf_top` SRAM macro (32×32, 1W2R, 132.6 × 118.7 µm, silicon-proven: tnt's validation chip, FemtoRV and SPELL on ttsky25b). For our 508 bits it's about the same area as clock-gated flops (~17k µm² placed either way) plus nested-macro integration, and the licence isn't explicit (ask tnt). Revisit if data mode needs buffers: the spare half would be free storage.
  - The 63-chip Gold code is an open option. Same chip length costs ~1.5 dB; double chip length keeps sensitivity. Either way it's a 6-bit code and weaker wrong-code rejection, ~−12,800 µm² placed. Quantify with e2e before choosing.
  - **Clock gating silicon evidence:** `sky130_fd_sc_hd__dlclkp_1` (+ a `clkbuf_8` per gate) is in toivoh's TT08 #770 "Sequential Shadows" synth registers (`USE_LATCHES`, `BUFFER_CLOCK_GATE`), reported working on the TT08 chip ("works just like in the simulation").
    - His gates drive latches with small fan-out; ours would drive 127 flops each. So add a clock buffer/CTS after each gate, check hold, and run gate-level sim of the hardened netlist on the existing vectors.
    - The clock-gated shift-register idea is in toivoh/tt08-on-chip-memory-test (no silicon results published).
- **Open items from the report:**
  - Sample timing is offset by the registered reset + the 2-flop synchroniser (documented in `radio_digital.v`).
  - The mode strap (`uio[7:4] == 1010`) risks contention if the RP2350 keeps driving it.
  - No trim freeze/override yet.
  - The verilator path is untried.

## Analog step 2: LNA first-stage experiment (first pass done)
Files:
- `xschem/gen/lna_blocks.py` writes `lna_dp` and `lna_pinv` (.sch + .sym). Sizes are global spice params, so they can be swept without regenerating.
- `xschem/gen/tb_lna.py` writes `tb_lna_dp` / `tb_lna_pinv`: the tb_input front end, AC coupling, x1, and x2 as the load copy. The antenna common path goes through `Vcmi`; `mm` = 1 % p/n device mismatch.
- `sim/lna/analyse.py` prints the comparison table and writes `sim/plots/tb_lna.png`. Run it with `~/work/asic-workshop/venv/bin/python` (system python has no numpy).
- `sim/lna/noise_break.sh | noise_rank.py` gives per-device noise at 434 MHz; `sim/lna/sweep_pair.sh dp|dpp "widths"` sweeps NF/gain vs current and W; `sim/lna/variant.sh` runs a testbench with .param overrides as a named variant for analyse.py.
- The xsch.py helpers `mos()`, `write_symbol()` and `ports()` now work: both netlists are clean.

Results at roughly equal current (dp 0.63, pinv 0.55 mA/stage), tt corner:

| | dp (W 20, R 2k) | pinv (10/20, Rf 20k) |
|---|---|---|
| EMF → o1 gain @434 MHz | 11.8 dB | 10.3 dB |
| stage gain, loaded by a copy | 14.2 dB | 12.7 dB (20 dB unloaded) |
| −3 dB band | 4–496 MHz | 17–202 MHz |
| CM → CM per stage @10 MHz / @434 MHz | −20 / −11 dB | **+7 / +10 dB** |
| CMRR @434 MHz (1 % mismatch) | 69 dB | 43 dB |
| VDD → output CM @434 MHz | 0 dB | +6 dB |
| NF @434 MHz (incl. pad) | 14.3 dB | 13.4 dB |
| tran: 20 mV 10 MHz CM → stage 2 output CM | 0.2 mV | **104 mV** |

Takeaways:
- **pinv amplifies common mode.** Every stage adds gain, so 60 dB would rail on our own 10 MHz clock unless CM feedback is added.
- **dp is DC coupled, so offset accumulates:** 1 % mismatch → 8 mV at o1, ~50 mV at o2. A chain needs AC coupling or offset cancellation every 2–3 stages.
- **Noise is dominated by the input devices** (~70–95 %):
  - In these models, NMOS flicker noise is still ~40 % of the transistor noise at 434 MHz; PMOS has almost none.
  - The pad's 50 Ω R2 contributes ~6–8 %; the antenna only ~4 %.
- **dp NF sweep** (0.6 V load drop held, EMF→o1 gain stays ~9–11 dB):
  - W=80: 11.7 dB at 0.6 mA, 10.0 dB at 1.2 mA, 8.7 dB at 2.4 mA.
  - L=0.3 is ~1.5 dB worse than 0.15, so flicker is not the lever; gm/I and W are.

Follow-up: PMOS pair vs wider NMOS pair at higher current.
- **`lna_dpp` (PMOS pair, n-well tied to tail, loads to ground):** at equal current and 2× W, NF is ~1–1.5 dB worse and gain 3–4 dB lower than NMOS. Its low flicker doesn't pay for the lower gm.
  - Upside: VDD → output CM is −20 dB, against 0 dB for NMOS with resistor loads.
- **NMOS candidates** (tt corner; NF is EMF-referred, pad included):

| variant | I/stage | W | EMF→o1 gain | NF at o1 | NF at o2 (incl. stage 2) | −3 dB band |
|---|---|---|---|---|---|---|
| dp | 0.63 mA | 20 | 11.8 dB | 14.3 dB | 14.5 dB | 4–496 MHz |
| dp_1m2 | 1.26 mA | 80 | 10.7 dB | **10.1 dB** | 10.3 dB | 4–432 MHz |
| dp_2m4 | 2.52 mA | 160 | 9.8 dB | **7.4 dB** | 7.6 dB | 3–412 MHz |

  - Stage 2 adds only ~0.2 dB of NF, so later stages can be small.
  - CM rejection is unchanged with size (CMRR 64–71 dB).
  - The wide pair's gate capacitance plus the pad pulls the band top just under 434 MHz.
  - NF is lowest near 270 MHz in every variant; it's already rising at 434 MHz.
- **Gain is capped by the 0.6 V load drop:** stage gain ≈ (gm/Id)·0.6 V ≈ 14 dB whatever the current. More gain would need active loads with CM feedback.

**Decision (tentative): NMOS diff pair, ~1.2–2.4 mA, W 80–160 µm.**

### Input matching (sim/lna/match.sh)
The pad model (`xschem/pad_model.sch`, tnt's TT analog-pin path) is **rough and ready**. Treat absolute NF and the exact L value as indicative only.
- Per side the path is: 2 pF at the pin → 1 nH bond wire → 3 pF → 50 Ω → TT mux switch (plus an off switch) → 250 fF.
- None of it can be changed from the chip side.

Results:
- **On-chip shunt spiral (Q 5): always worse.** Dropped.
- **Off-chip differential shunt L across the pins (Q 30):** about 1 dB better at best (~40 nH).
- **Off-chip series L in each antenna arm (Q 30): the winner.** The optimum is broad (~16–20 nH; within 0.5 dB from 12 to 26 nH):
  - dp_1m2: NF 10.0 → **6.9 dB**, EMF→o1 gain at 434 MHz 10.7 → 14.4 dB;
  - dp_2m4: NF 7.3 → **4.7 dB**.
  - Gain across 330/434/560 MHz becomes 15.4 / 14.4 / 10.5 dB (it tilts down).
- **Tolerance** (dp_1m2, 18 nH): pad C ×0.7 / ×1.3 → NF 6.2 / 8.0 dB (none: 9.6 / 10.5 dB). Bond wire 0.5–2 nH: no effect.
- **But the project is wires only on the pins (no external parts), so off-chip matching is out.** The chain is designed without it (NF ≈ 11 dB).
- Parked idea: get the series inductance from the wire itself (arms longer than resonant look inductive), or use a folded dipole (4× impedance, 2× EMF). Compare by noise referred to incident field. Needs a dipole impedance model (scipy isn't in the venv).

## Analog step 3: gain chain (xschem/gen/chain.py, first pass done)
Blocks (instance params via symbol templates; `write_symbol(params=...)`):
- `amp_dp`: diff pair with the tail gate as pin `nb`.
- `amp_dpc`: diff pair with a split tail and **Cs between the sources**. This capacitive degeneration gives full gain above ~gm/(2Cs) and ~0 differential gain at DC.
- `lna_chain`, 5 stages:
  - on-chip input coupling: `cin` 2 p + `rb` 20 k to `vcm`;
  - stage 1: `amp_dp` W 80, rl 1 k, 1.2 mA;
  - stages 2–5: `amp_dpc` W 20, rl 4 k, 0.36 mA, Cs 0.6 p, **DC coupled**;
  - one reference diode; tail current = mt × ibias (60 µA).
- `tb_chain`: the tb_lna front end → chain → 50 fF loads.
  - Analyse: `sim/chain/analyse.py [variants]`. Variants: `sim/chain/variant.sh`. Level sweep: `sim/chain/levels.sh`.
- Interstage AC coupling was tried first and dropped. A small bias R loads the previous stage in band (0.5 pF ≈ 730 Ω at 434 MHz), so raising the high-pass corner that way cost gain and NF.

Results (tt, 1 % mismatch):
- **Gain EMF→out:** 66.6 / 66.6 / 65.0 dB at 330 / 434 / 560 MHz; −3 dB band 237–625 MHz.
- **Out-of-band:** 100 MHz (FM) −23 dB re band; 10 MHz −96 dB re band.
- **Upper side:** 900 MHz −8 dB, 1 GHz −10 dB, 2 GHz −27 dB re 434 MHz. About half of that is the pad model (antenna→pad −2.3 dB at 434, −6.2 at 900) and half the chain (−4.3 dB at 900).
  - The real rejection is likely better: the pad model is rough (more C or ESD loading rolls off harder), and the sim's antenna is a flat 73 Ω. A 434 MHz dipole is near full-wave at 900 MHz, a high reactive impedance into a pin with several pF.
  - So **no on-chip upper shaping for now**. Measure the real pin + dipole response from 400 MHz to 1 GHz on the bench before spending in-band gain on it (GSM-900).
- **Supply:** 2.56 mA total.
- **NF:** 10.8 / 11.0 / 11.6 dB (330 / 434 / 560 MHz).
- **Noise at the output:** 197 mV rms differential (447 MHz noise bandwidth). Limiting is ~1.35 V amplitude (~0.95 V rms), so the chain doesn't limit on its own noise.
- **Offsets:** 3.8 mV at o1, 0.2 mV at the output (degeneration kills DC gain).
- **Limiting** (434 MHz tone, available power): out limits from ~−55 dBm, o4 ~−45, o3 ~−35, o2 ~−25, o1 ~−10 dBm. The taps are ~13 dB apart; successive detection covers roughly −95 to −10 dBm.
- **CM→out diff and VDD→out diff are ~0 dB at 434 MHz** with 1 % mismatch (CMRR ≈ 70 dB, but the gain is 66 dB). Supply ripple at the 430/440 MHz clock harmonics reaches the output ~1:1, so supply isolation and decoupling matter (PLAN isolation row).
- **vs the e2e model's assumptions** (NF 10 dB, 400 MHz; `bench/scheme_compare.py`): ~1 dB worse NF and ~0.5 dB wider bandwidth → roughly −92.5 instead of −94 dBm. Not re-run.

Still open for the chain:
- upper-side rejection: measure the real pad + dipole first (see above);
- a current budget (stage 1 at 2.4 mA buys ~2.5 dB NF, which would give sensitivity margin).

## Analog step 4: log detector (xschem/gen/logdet.py, first pass done)
- **Chain is now 6 stages** (`NSTAGES` in chain.py; ~80 dB, ~2.9 mA). The 6th stage puts the chain's own noise floor (≈ −76 dBm equivalent) into the detector's log-linear range. With 5 stages it sat in the square-law tail at only 2–6 mV/dB. `lna_chain` exposes taps o1..o5 as pins.
- **`det_cell`:** full-wave rectifier, two NMOS (W 1, L 0.15).
  - Gates AC coupled (100 f / 200 k) and biased at ~Vth from `vb`; source degeneration rs 10 k.
  - Idle current ~2 µA per side.
- **`log_det`:** one det_cell per tap (o1..o5, out), drains summed into rdet 8 k ∥ cdet 5 p from VDD, so `det` falls with power. `vb` comes from a replica diode with the same rs, fed by ibias_det = 2 µA.
- **CW transfer** (`tb_logdet`, tone sweep): log-linear from ~−80 to −10 dBm at ~12.6 mV/dB, ±~1 dB ripple. Saturates once stage 1 limits (above ~−5 dBm). Results: `sim/logdet/transfer_cw.txt`; noise runs in `sim/logdet/noise_tran_results.txt`.
- **With noise** (`sim/logdet/noise_tran.sh`): repeatable PWL noise from `gen_noise.py` (3.9 nV/√Hz differential at the antenna ≈ NF 11 dB), 3 µs per case, ~1 min each.
  - Detector change vs no signal: −100 dBm −0.38 mV, **−94 dBm −1.07 mV**, −88 dBm −3.4 mV, −80 dBm −17 mV.
  - Slope at the noise floor ≈ 11–14 mV/dB (plan assumed ~16).
  - So near sensitivity the signal is ~1 mV at the detector. The comparator trim (~0.08 mV/LSB) and the comparator's noise after the 15 kHz LPF must be well below that.
- **e2e re-run with the real chain** (`model/e2e.py --nf 11 --brf 450e6 --slope 12`; new options also take offset, trim step and comparator noise in mV):
  - Noise case: still decodes **−94 dBm** (11/12; −96 dBm 0/12): the edge is sharp. Fading: −90 dBm OK, −94 2/5 (baseline 3/5). Bursty −60 dBm interferer: −70 OK, −86 1/5 (baseline 3/5; 5 trials, coarse). No false toggles anywhere.
  - PLAN's "0.27 dB / ~4 mV near sensitivity" was for ~−90 dBm. At −94 dBm the swing is ~0.08 dB ≈ 1 mV (0.11 dB in the original model).
  - **Comparator noise budget: ≤ 0.5 mV rms per decision.** 0–0.4 mV costs nothing measurable at −94 (12 trials); 0.6 mV → 8/12; 1 mV → 0/5 (−90 still fine, so ~2–4 dB lost). Reason: the detector's own radiometer fluctuation after the 15 kHz LPF is ~0.025 dB ≈ 0.3 mV, and comparator noise above that adds to it.
  - The 2 mV offset and 0.08 mV trim step, converted at 12 mV/dB, are fine.
  - `AfeModel(noise_db=...)` defaults to 0, so exported vectors are unchanged (checked).
- Open:
  - overload recovery (key a −10 dBm tone on/off);
  - detector idle drift over temperature/corners (absorbed by the comparator's averaging reference, but check range);
  - bias generation; corners.
- Simulation learnings (speed, traps, noise recipes) are collected in `docs/sim_learnings.md`. Tracked `.spiceinit` at the root; `tools/osic` copies it into build/.

## Analog step 5: post-detection LPF (xschem/gen/lpf.py, done)
- **Options considered:** passive RC, MOS pseudo-resistor, switched-cap R, active Gm-C, integrate-and-dump. **Chosen: passive RC.** No clock, noise √(kT/C) ≈ 20 µV, and the e2e model doesn't care about the exact cutoff.
- **e2e vs cutoff** (`--bv`; NF 11, 450 MHz, 12 mV/dB, 0.4 mV comparator noise, 12 trials). At −94 dBm, noise case 9/12, 12/12, 10/12 at 10 / 15 / 20 kHz; fading similar. So ±30 % RC spread is fine.
- **`lpf_rc`:** `res_xhigh_po_0p35` L = 136 µm (7.37 kΩ/µm → ~1.0 MΩ) + 6 × 30×30 µm `cap_mim_m3_1` (1.82 pF each → 10.9 pF). The MIM can sit over other circuitry.
  - `tb_lpf` (8 kΩ source like `det`): f−3dB = 14.4 kHz, rise 24 µs.
  - The cap is kept large to soak up comparator kickback (the node carries ~1 mV of signal near sensitivity).
- **Keep the `ua[4]` debug pin off the LPF output** (nA of pad/ESD leakage × 1 MΩ = mV of offset). Tap `det` (8 kΩ), or buffer. **Decided 2026-10-08: det via `dbg_tg`** ("ua[4] debug switch" below).
- **The 0.5 ms averaging reference** for the comparator (−) input should be fed from the LPF output. It needs a switched-cap R (poly would be ~50 MΩ); that belongs with the comparator block.
- Not checked: passive process spread (MOS corners don't move the passives; use the PDK's resistor/cap corner sections).

## Analog step 6: comparator + averaging reference (xschem/gen/comp.py, first pass done)
- **`comp_ct`, continuous-time** (no strobe, so no kickback onto the ~1 mV LPF node). The digital's 2-flop synchroniser samples it every 130 clocks.
  - Stage 1: lvt NMOS pair W 20 / L 1, 10 µA tail, lvt PMOS mirror load, Cl ≈ 1 pF dominant pole (~340 kHz).
  - Stage 2: PMOS common source + NMOS sink; then an inverter. ~20 µA total.
  - **Trim:** degenerated lvt NMOS pair (1.4 MΩ xhigh poly between split tails) comparing `trim` (R2R DAC voltage) with an on-chip VDD/2 divider. This is the plan's attenuator. Raising `trim` acts like raising `inn`.
- **`tb_comp` results:**
  - Offset +0.5 to +1.8 mV over input CM 0.55–1.6 V (covers det from −10 dBm to idle).
  - Trim 0.087 mV/LSB in its linear range (DAC ~0.6–1.8 V), −19 to +12 mV, monotonic.
  - **Decision noise 28 µV rms** (output noise ÷ DC gain, 1 Hz–100 MHz) against the ≤ 0.5 mV budget.
  - ±1 mV overdrive → 0.36 µs.
- **`avg_sc`:** Cs (11×11 µm MIM, ~0.25 pF) shuttles in→out on `sc_phi1/2` into Cavg (5 × 30×30 µm, ~9.1 pF); transmission gates with local inverters.
  - `tb_avg` (the digital's exact phi timing): **τ = 0.47–0.48 ms** at 0.6 / 1.0 / 1.4 / 1.5 V; offset ≤ 0.04 mV.
- **Wiring for integration** (det falls with power):
  - `avg_sc.in` = LPF out; `comp_ct.inp` = avg; `comp_ct.inn` = LPF out.
  - So c = 1 when power is above its average, and trim↑ makes c = 1 rarer. That matches the model and the servo (trim += c).
- ngspice traps found here (in `docs/sim_learnings.md`): `option klu` breaks `.noise`; `inoise_total` overstates noise above a pole (use onoise_total / DC gain); `destroy all` deletes vectors, so keep values in `set` variables.

## TX ring frequency calibration (sim/ring/ttsky25b_ring.sh)
Measured ring: tt08/ttsky25b `tt_um_mattvenn_analog_ring_osc`, ring 1 = 18 × `sky130_fd_sc_hd__inv_2` + `nand2_2` (19 stages; std-cell PMOS are **hvt**). The "600 MHz" target was already from the *extracted* layout (`mag/ring.sim.spice`) with its driver + pad_model; measured **518 MHz**.
- Re-simulated here (same extracted netlist), 1.8 V (VDD is good on the demoboards):

| corner | 27 °C | 60 °C |
|---|---|---|
| ff | 678 | |
| fs | 614 | |
| **tt** | **598** | 601 |
| sf | 573 | |
| ss | 495 | 498 |

- Measured / extracted-tt = **0.866**: between tt and ss, consistent with a slow part (the mini-mosbius chip fitted **ss**). Temperature is not the explanation (+0.5 % from 27 to 60 °C), and neither is VDD.
- **Rule for the 433 MHz ring:** design to **433 / 0.866 ≈ 500 MHz extracted-tt**. With the same std-cell ring that's ~23 stages (22 inv + nand) if the load stays similar (f ∝ 1/N: 19 × 598 / 500 ≈ 22.7).
  - If the new lot is really tt it lands ~500 MHz; if ss, ~414 MHz. Both are inside the RX band (330–560 MHz).
- ngspice trap: in a control loop, `option temp = X` must come **after** `reset` (`set temp` does nothing).
- **Schematic vs extracted:** the original schematic (10 fF wiring per stage in `inverter`) gives only **357 MHz** against 598 extracted, so it was very pessimistic. **3.2 fF per stage** reproduces the extracted ring (`sim/ring/ttsky25b_ring_sch.sh` sweeps it).
- **New ring sizing** with that calibrated model (`sim/ring/ring_stages.sh`; nand2_2 enable + N × inv_2, same first-driver load):
  - 18 inverters: 590 MHz (check vs 598);
  - 20: 538 → ~466 on silicon;
  - **22: 494 MHz → ~428 MHz on silicon (×0.866). Choose 22 inverters + nand (23 stages).**
  - 24: 457 → ~396.
  - Keep the ring's load the same as the ttsky25b driver's first inverter (W 9/3), so the next stage (level shift / pre-driver) should present that input.
- **Level shifter: reuse the R2R DAC's `dac_drive`, skewed** (`sim/ring/ls_dac_drive.sh`, `ls_fmax.sh`, `ls_skew.sh`; tt08-analog-r2r-dac-3v3).
  - As built (thick-oxide cross-coupled core, all W 0.42 / L 0.5): full swing to ~200 MHz, degrading at 300, **fails at 433 MHz** (core stuck below 1 V). The core fight (1.8 V-driven thick NMOS vs equal thick PMOS) is longer than a half-period. Scaling everything (×10) is worse.
  - **Skewed core** (pull-down NMOS ×4–10, cross-coupled PMOS minimum): the core swings full rail (−0.5…3.5 V) at 433 **and 600 MHz, tt and ss**. ~0.4 mA from 3.3 V.
  - Still to do: the output buffers. With the original W 9/3 final stage into 0.3 pF, the output only reaches ~0.4–3.0 V at 433 MHz (worse at 600). That's a buffer taper towards the big driver, not a core problem.

## TX chain, first pass (sim/tx/tx_explore.py, raw spice; plot `sim/plots/tx.png`)
Ring (nand2_2 + 22 inv_2, 3.2 fF/stage) → thin W 9/3 inverter (the load the ring was calibrated with) → skewed level shifter → identical thick-oxide buffer tapers (×4 per stage) on latch nodes A and B (inherently antiphase) → final drivers N 48 / P 144 µm, L 0.5 → `pad_model` per arm → dipole (73 Ω + 100 pF series: open at DC).
- **Level shifter core:** NMOS ×10 (W 4.2), PMOS kp = 4 (W 1.7), thick L 0.5. kp = 4 balances best: duty at A ~38–40 % (the core's pull-up is slower than its pull-down). The arms run ~35–50 % duty, costing < 1 dB, with H2 ≈ −18 dBc.
- **Final size:** N 24 → −2.5 dBm, **N 48 → +3.7…+4.3 dBm**, N 96 → no better (the pad/mux path limits).
- **Reference:** the old 1.8 V thin driver (P72/N24) antiphase into the same model gives +0.1 dBm, so the 3.3 V stage is **+4.2 dB** (PLAN estimated +5).
- **Square-drive corners at 433 MHz:** ss +3.7, tt +4.3, ff +4.7 dBm; arm phase 178.8–179.4° (≤ 10° budget). At 600 MHz: tt +2.5 / ss +1.4 dBm, phase 175 / 170°. So there's speed margin.
- **With the real keyed ring** (`tx_explore.py ring tt ss ff`):

| corner | ring f (sim) | P into dipole | on / off | VAPWR | VDPWR |
|---|---|---|---|---|---|
| tt | 484 MHz (×0.866 → ~419 on silicon) | +3.3 dBm | 7 / 4 ns | 10.2 mA | 0.22 mA |
| ss | 400 MHz | +4.0 dBm | <1 / 5 ns | 9.4 mA | 0.18 mA |
| ff | 546 MHz | +3.7 dBm | 0.5 / 2 ns | 11.0 mA | 0.26 mA |

  - The ring runs ~2 % below the calibrated 494 MHz with this load, so ~419 MHz is expected on silicon (433.92 target, well inside the RX band). 20 inverters would give ~466.
  - **VDPWR steps only ~0.2 mA** when TX turns on (the old all-1.8 V design stepped ~10 mA through the ring's supply). The bench turn-on chirp, which came from 1.8 V droop, should be much smaller. The 10 mA step is now on VAPWR, which only feeds the shifter/drivers.
  - Disabled: no static current. One arm idles at 3.3 V and the other at 0 (DC across the dipole, no current). Consider gating both low.
- Next for the TX:
  - xschem blocks (ring, level shifter, buffers/drivers) from a generator;
  - corners of the whole chain with extracted-style wiring;
  - VAPWR decoupling and on-chip droop with a bond-wire model;
  - the disable state.

## TX xschem blocks (xschem/gen/tx.py, done 2026-10-08)
- **Blocks:** `tx_ring` (cw param, 3.2 fF), `tx_ls` (kn/kp/wpi/wni params), `tx_drv` (one arm), `tx_top` (ring → ls → two arms + two small enable level shifters), `tb_tx`.
  - `tools/xsch.py` gained thick-oxide FETs (`vt='g5'`), hvt PMOS and `stdcell()` (sky130_fd_sc_hd; supplies are instance properties).
  - The testbench needs the std-cell spice include as a tcleval code block (`STDCELLS`).
- **Disabled state: both arms low.** The first (smallest) stage of each arm's taper is a thick NAND2 (`in`, `en`; series NMOS 2 × 0.42, PMOS 1.26), so out = in & en. Each arm's `en` comes from its own small unskewed `tx_ls` (kn 1 / kp 1, input inverter 1 / 0.42).
  - With en_p = en_n = key, nothing is left across the dipole when off.
  - en_n = 0 gives the single-ended (monopole) fallback that PLAN asked for, with no extra hardware.
- **`sim/tx/tb_tx.py [corners]`:** netlists, rewrites the corner, runs both cases (`ab` antiphase, `se` single-ended; ~1 min per corner) and analyses with `tx_explore.ring_metrics`.

| corner | ring f (sim) | P into dipole | single-ended | on / off | VAPWR | VDPWR |
|---|---|---|---|---|---|---|
| tt | 484.8 MHz (×0.866 → ~420 on silicon) | **+3.67 dBm** | −3.18 dBm | 3.3 / 3.9 ns | 11.2 mA | 0.23 mA |
| ss | 401.0 | +3.89 | −3.45 | 5.0 / 7.3 | 10.2 | 0.18 |
| ff | 547.0 | +3.69 | −3.43 | 2.3 / 2.2 | 12.1 | 0.26 |
| sf | 461.9 | +3.80 | −3.69 | 1.5 / 2.8 | 11.0 | 0.21 |
| fs | 501.3 | +3.75 | −3.27 | 5.0 / 5.8 | 11.4 | 0.24 |

  - Matches the raw-spice first pass (tt 484 MHz, +3.3 dBm, 10.2 mA). The xschem devices carry ad/as/pd/ps diffusion parasitics, which the raw spice didn't.
  - Arms before and after the key: ≤ 0.1 V (the dipole's series C bleeding off through the pads).
  - Single-ended is ~7 dB below antiphase (half the drive voltage gives −6 dB).
  - ×0.866 is the extracted-tt → silicon factor, so only the tt row maps to silicon that way. The sim spread (401–547 MHz) sits inside the RX band (330–560).
- Still open for the TX: temperature; extracted-style wiring beyond the ring's 3.2 fF; VAPWR decoupling and bond-wire droop (11 mA step); layout.

## RX corners (sim/corners/, done 2026-10-08)
`sim/corners/rx_corners.sh` (in the osic image from build/; ~8 min for 5 corners × 3 temperatures) then `python sim/corners/rx_corners.py` for the table. Ideal bias, ideal chain/detector passives: MOS variation only (the passives and bias are covered below).

| over all 5 corners, 10–50 °C | range |
|---|---|
| chain gain @434 MHz | 72.9 (ff 50 °C) … 81.8 dB (ss 10 °C) |
| NF @434 MHz | 9.4 (ff 10 °C) … **12.0 dB** (fs 50 °C); ~+0.4 dB per 10 °C |
| det idle | 1.505 … 1.530 V |
| det slope at the noise floor (−80…−70 dBm) | **9.7** (ff 50 °C) … 14.4 mV/dB |
| comparator offset over CM 0.6–1.45 V | +0.5 … +2.5 mV |
| trim range (DAC 0.6 → 1.8 V) | −4.6…−8.5 to +9.7…+12.8 mV; 0.107–0.153 mV/LSB |

- **e2e at the worst corners** (noise case, 12 trials, 0.3 mV comparator noise): fs 50 °C (NF 12.0, 12.4 mV/dB) and ff 50 °C (NF 11.4, 9.7 mV/dB) both decode **−92 dBm 12/12**, −94 dBm only 3–4/12 (tt 27 °C: 10/12). **Worst-case sensitivity ≈ −92…−93 dBm**, 1–2 dB off nominal.
- **Comparator CM:** at sf, the offset grows above CM 1.45 V (+2.4 mV at 1.45, +9.4 at 1.5, no threshold within ±30 mV at 1.55). In operation the comparator CM is the LPF output, which is ≤ ~1.45 V (the chain's noise floor pulls det below its noise-free 1.52 V), so it's fine, but don't let det idle rise.
- Earlier −20/85 °C run (tt, ss) is kept in `build/corners/wide/` (85 °C: NF 12.8 dB, −92 dBm).

## Real passives (xschem/gen/chain.py, logdet.py; 2026-10-08)
- The chain and detector R/C are now PDK devices, via `poly_r()` / `mim()` in `tools/xsch.py`. These place a resistor or cap by value; the geometry is a netlist expression, fitted R(L) = a + b·L (`sim/pdk/passives.spice`).
  - Loads: stage 1 high_po 1p41 (1 kΩ, 0.6 mA/side); stages 2–6 high_po 0p69 (4 kΩ); input rb high_po 0p35 (20 kΩ); cin MIM (bottom plate on the pad side).
  - Cs: two MIM halves anti-parallel, so each source sees one bottom plate.
  - Detector: rb xhigh 0p35 (200 kΩ); rs high_po 0p35 (10 kΩ); rdet high_po 0p69 (8 kΩ); cc MIM (bottom plate on the chain tap); cdet 4 × ~25 µm MIM (bottom plate on VDD).
- **PDK passives (tt, 27 °C):**

| | Ω/µm | ends | corners `hh` / `ll` | tempco |
|---|---|---|---|---|
| high_po 0p35 / 0p69 / 1p41 | 995 / 471 / 230 | 963 / 526 / 278 Ω | +14 % / −15 % | +0.05 %/°C |
| xhigh_po 0p35 | 7379 | ~0 | +15 % / −15 % | ~0 |

  - MIM: 2.06 fF/µm², `hh` +14 % / `ll` −13 %.
  - The MOS corner libs (tt/ss/ff/…) keep R and C typical. The R/C corners are separate lib sections (`hh`, `ll`, `hl`, `lh`, and combined e.g. `ss_hh`).
  - **The models have no parasitic C** (poly to substrate, MIM bottom plate): that only shows up after layout extraction.
- **At tt the conversion changes nothing:** gain 76.7 dB, NF 11.0 dB, det within 6 mV of the ideal-passive netlist.

## Bias generator (xschem/gen/bias.py, first pass done 2026-10-08)
- **`bias_gen`:** an OTA forces vref = VDD/3 across rref (high_po 0p69, 10 kΩ, **the same poly as the chain loads**). I = 60 µA goes into a PMOS diode (60 units W 2 / L 1). Mirrors: ib_chain 60 µA, ib_det 2 µA, ib_comp 1 µA.
  - vcm = 2·VDD/3 comes from the same xhigh divider (3 × 200 kΩ), MIM-decoupled.
  - OTA: PMOS input pair, tail from a resistor-biased PMOS diode, so there's no zero-current state.
  - `en` (= rx_en) low: everything off (< 1 nA).
- **`tb_bias`** (loads = the real diode loads):

| | result |
|---|---|
| ib_chain / det / comp (tt, 27 °C) | 59.4 / 1.98 / 0.99 µA |
| over 10–50 °C | −1.1 % |
| vs VDD | ∝ VDD (1.7 / 1.9 V: −6 % / +6 %); vcm = 2·VDD/3 |
| MOS corners ss / ff | 60.3 / 58.5 µA |
| R corners `hh` / `ll` | 52.2 / 69.5 µA (∝ 1/R, as intended) |
| start-up (VDD ramp 10 µs) / re-enable | clean / < 0.5 µs to 90 % |
| supply | ~130 µA incl. outputs |

- **Why I ∝ 1/R:** the DC-coupled chain's operating points depend on I·RL. Real-passive chain at the R/C corners, fixed 60 µA vs this bias:

| | `hh` | tt | `ll` |
|---|---|---|---|
| gain @434 MHz, fixed 60 µA | 80.5 dB | 76.7 dB | 71.3 dB |
| gain @434 MHz, tracking bias | **78.1** | 76.7 | **73.7** |
| NF @434 MHz, tracking bias | 11.1 | 11.0 | 11.0 |

  - What's left is the R·C band shift (206–519 MHz at `hh`, 299–718 at `ll`).
  - Detector with tracking bias: idle 1.520 / 1.521 / 1.524 V (tt / hh / ll), so the comparator CM doesn't move. Slope at the noise floor 13.4 / 14.1 / 10.3 mV/dB: `ll` is ~−93 dBm, like ff 50 °C.
- Not yet: integrating bias_gen into the RX testbenches/top (it feeds `iref`, `ibias_det`, `Ibc` and `vcm`, which are ideal sources today); stability margin check of the OTA loop (the start-up and en transients settle cleanly; no AC loop-gain run yet).

## Trim DAC (xschem/gen/dac.py, 2026-10-08)
- **`r2r`:** an 8-bit R-2R schematic matching the reused tt08 layout (`tt08-analog-r2r-dac-3v3/mag/r2r.mag`, its `r2r.lvs.spice`) device for device, so LVS lines up:
  - unit R = `res_high_po_1p41` L 45 ≈ 10.6 kΩ; 2R = two units in series;
  - a start module with the 2R termination, 7 bit tiles, and 2 dummies (27 units).
  - The TT08 *schematic* used 0p35 devices, but its layout is 1p41.
- **Driven straight from the digital's `trim_out`** (1.8 V std-cell outputs; no level shifters, unlike TT08's 3.3 V version), so the output is 0…1.79 V.
- **`tb_dac`:** out = code/256·1.8 V exactly (0, 1, 85, 128, 135, 255); Rout 10.64 kΩ.
  - VDD ripple: the trim pair compares the DAC against its own VDD/2, so what's left is (code/256 − ½) = 0.027 at the operating code (~135). Through the trim gain (~1/56) that's < 1 µV per mV of ripple at the comparator input: no filtering needed beyond a small MIM on `trim` against clock-edge spikes (add at the top level).
  - The digital's output drivers (~hundreds of Ω) sit in series with the 21 kΩ 2R legs: ~1–2 LSB of DNL at the major transitions (0.25 mV of trim). Fine for the servo. When re-hardening, use balanced, strong buffers on `trim_out`.

## ua[4] debug switch## ua[4] debug switch (xschem/gen/dbg.py, done 2026-10-08)
- **`dbg_tg`:** thin transmission gate (N W 2, P W 4, L 0.15, local inverter) from `det` to the ua[4] pad. `dbg_en` comes from the digital: magic `1010` + `uio_in[2]` = 1 at reset (cocotb `test_debug_strap`). Default off.
  - Raw TX + debug together works, but `uio_in[2]` = 1 during reset then also keys the TX until reset is released.
- **`tb_dbg`** (det as 8 kΩ ∥ 5 pF, pad_model, pin source; tt):
  - **Off:** pin → det below −145 dB (10 kHz–100 MHz) in the model. In layout, a stray fF between the det and pad wires dominates (~−70…−90 dB against 5 pF): still plenty. det DC shift < 0.1 µV with the pin at 0 or 1.8 V.
  - **On, scope (1 MΩ ∥ 15 pF):** 0 dB, −3 dB at 656 kHz.
  - **On, 50 Ω generator:** det follows the pin at ×0.65 (−3.8 dB; Ron ≈ 4.4 kΩ), so an AWG can drive the baseband (LPF → avg → comparator → digital) with no RF.

## Whole-RX transient (sim/rx/, first pass done)
Two halves, both transistor level (a 13 ms burst at 434 MHz can't be simulated in one piece).
- **RF** (`sim/rx/rf.sh` on tb_logdet), −60 dBm tone. Antenna EMF 0.76 mV → pad 0.59 → stage 1 2.9 → 12.7 → 57.6 → 261 → stage 5 1080 (starting to clip) → stage 6 1630 mV (limited, square). Carrier keyed on/off: det steps 1.52 → 1.19 V in ~0.1 µs.
- **Baseband** (`xschem/gen/tb_rx_bb.py`, `sim/rx/bb.sh`): det → `lpf_rc` → `avg_sc` (digital phi timing) → `comp_ct`, with a B-source trim servo stand-in (±1 DAC LSB per 13 µs).
  - Driven by `sim/rx/gen_det.py`: one Gold burst (code 0x5A) with NF 11 dB / 450 MHz noise, mapped through the measured 6-stage detector curve (shifted −3.8 dB to match the transistor-level noise run).
  - The comparator is sampled every 13 µs and fed to the bit-exact `RxDigital`.
- **Results:**
  - −70 dBm: chips swing det by 104 mV; comparator = TX chip 98 %; correlator 127/127 → detected.
  - −94 dBm: swing ~0.7 mV in ±3 mV of noise; comparator = chip 67 %; correlator **99/127** (threshold 97) → detected, just.
  - This matches the behavioural model (75 % / 106 at −94 in `model/comparator_view.png`).
- **Plots:** `sim/plots/rx_rf.png`, `sim/plots/rx_bb.png` (`sim/rx/plot_rx.py`). Runs: rf ~1 min, bb ~1 min per level.
- **Not yet in the loop:**
  - the real R2R DAC (ideal servo stand-in);
  - noise in the RF half (handled by the calibrated det waveform);
  - all three bursts / LED toggle (one burst only);
  - corners.

## Area ballpark (sim/area_estimate.py, updated 2026-10-08 with TX, DAC, bias)
- Analog, all blocks now first-passed: devices ~15,700 µm² (×2.5 routing; ring and R2R ladder from measured layouts: 228 µm² for 19 stages, 3,864 µm² for the ladder) + MIM ~21,300 µm² (28 % of a 2x2; can't overlap the digital).
- **2x2:** ~102 % with the digital as is (40,500 µm² placed); **~79 %** with the RTL size reduction (~23,000 µm²). Both before decap, guard rings and power routing.
- **3x2** (~113,000 µm²): ~68 % / ~53 %.
- **Decision (2026-10-07): fine for now; go to 3x2 if needed** rather than shrink early. 3x2 is confirmed allowed for analog (2026-10-08).
- Easy cap savings if ever wanted: LPF 4 MΩ / 2.7 pF (the comparator has no kickback); avg Cs 0.1 p / Cavg 3.6 p; cdet 1 p; chain cin 1 p (NF check). Together 19k → ~8k µm² of MIM.
