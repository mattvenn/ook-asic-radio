# Where we are (handoff, end of 2026-10-08)

Read **PLAN.md** for the decisions and their evidence. This file is the "pick up from here" note: the summary and next steps first, per-block detail below.
Repo: github.com/mattvenn/ook-asic-radio (`main`).

## Start here

**State (end of 2026-10-08): pre-layout work done and re-verified; layout started (TX driver, see `docs/layout.md`).**
- **RX:** every block is transistor level with real PDK passives and a real bias generator.
  - Chain: pad → 6-stage NMOS diff-pair limiting chain.
  - Detector: successive-detection log detector → 14 kHz RC LPF (2.95 MΩ / 3.7 pF).
  - Comparator side: switched-cap average (τ ~0.45 ms) → continuous comparator; trim from the reused R2R ladder, driven by the RTL servo.
  - **Confirmed three ways:** the fully joined transistor-level run (antenna → comparator) matches the split model. Corners 10–50 °C give a worst case of **≈ −92…−93 dBm**. And the **mixed-signal run** (RTL servo → real `r2r` → real `comp_ct`) detects −70 and −94 dBm bursts.
- **TX:** xschem blocks, +3.7…+3.9 dBm at all corners, both arms low when off, single-ended fallback (`tx_en_n`). VAPWR decap ~50 pF.
- **Digital:** **clock-gated** (`rd_cg.v`, one `sky130_fd_sc_hd__dlclkp_1` per 127-bit chip register), hardened with LibreLane at **260 × 190 µm**.
  - Signoff clean (DRC, LVS, antenna 0; timing met at all corners).
  - **RTL suite 15/15 and gate-level suite 15/15** on the hardened netlist (`make GL=1`).
- **Top level:** `radio_analog` (all analog blocks + bias + decap) and the `tt_um_mattvenn_radio` schematic; ua[0]/[1] TX, ua[2]/[3] RX, ua[4] debug (det via a debug-only TG).
- **Area** (`sim/area/area_netlist.py`): the analog needs ~49k µm² of the ~57k left beside the macro in the 3x2 (493 × 226 µm): **85 %**, 93 % of the tile. The VAPWR decap (~18k µm²) is the biggest block.
- **Operating range 10–50 °C only.**
- **Layout flow (KLayout pcells → DRC/LVS → PEX → block test) works end to end on `tx_drv`.** See `docs/layout.md` for the steps, power/PDN rules, EM table and lessons.
  - **tx_drv v2:** 40.9 × 27.6 µm; DRC (Magic + KLayout) and LVS clean. EM-sized from measured currents.
  - **Block test** (`sim/tx/tb_tx_drv.py [--pex]`): −0.32 dB vs schematic.
  - **Policy:** each block gets a small `tb_<block>` (schematic vs extracted). One end-to-end run on the full extracted design at the end.
  - **Power pins:** met4 straps (≥ 1.2 µm, full height) on both the left and the right of the tile.
  - **TX blocks:** `tx_drv`, `tx_ls`, `tx_ls_en` laid out with the row builder `layout/gen/rows.py`; all clean. Previews: `layout/README.md` (TT GDS viewer links).
  - **Level shifter:** its ctrl_n inverter was upsized (M8/M7 4 / 1.68): extracted A duty 28 → 36 %, arm outputs 39 / 44 % (schematic 44 / 48 %). This schematic change isn't in `tb_tx` results yet.
  - **Ring:** `tx_ring` laid out (std cells, 34.5 × 4.2 µm, clean). Extracted 508.5 MHz tt → **~440 MHz on silicon** (×0.866).
  - **Plan (Matt, 2026-10-08):** a first take on every leaf block, then floorplan the whole tile; assemble `tx_top` as part of that floorplan.
    - Outputs exit the bottom of the tile: ua[0] = 136.6, ua[1] = 117.3 µm in the 3x2 DEF, so the TX goes there.
    - The digital macro's `tx_en`/`tx_en_n` leave its west edge near the bottom.
  - **Leaf blocks done** (`layout/README.md` has viewer links):
    - TX: `tx_drv`, `tx_ls`, `tx_ls_en`, `tx_ring`.
    - Trim DAC: `r2r` (the tt08 layout reused; extracted error ≤ 0.02 LSB).
    - RX: `avg_sc` (τ 0.434 ms extracted; **open:** ±~4 mV static offset from phi coupling, within the trim range); `lpf_rc` and `dbg_tg` (other sessions).
    - Also by other sessions: `bias_gen` (in progress), the decaps.
    - **`comp_ct`:** done (ABBA pairs + dummies, passives, clean; extracted offset +0.56 mV, trim 0.0655 mV/LSB). 5.0k µm², larger than estimated. Matching dummies were added to the schematic (`Mdn*`/`Mdp*`).
    - **Still to do here:** `log_det`, `lna_chain` (last, after the stability check).

**Re-verified (2026-10-08 evening): rdeg 2 MΩ, decap blocks, chain stability.** Details in "Re-verify: rdeg 2 MΩ, decaps, chain stability" below.
- Trim step at the operating point (DAC 0.8–1.2 V) is **0.062–0.076 mV/LSB at all corners, 10–50 °C**. e2e at −94 dBm: tt 11/12, fs 50 °C 8/12, ff 50 °C 10/12; −92 dBm 12/12.
- Decaps: **50.06 pF** (VAPWR) and **29.9 pF** (VDPWR), flat to 434 MHz and over ±10 % supply.
- `tb_radio_analog`: unchanged. Mixed-signal −94 dBm (real servo loop) still detects the burst. Bias OTA loop: PM ~90° at all corners. R/C corners: trim step 0.056–0.085 mV/LSB.
- **Chain layout rule:** keep chain output → input coupling (pad or stage-2 input) **≤ 0.1 fF** asymmetric. At the highest-gain corner (ss 10 °C, 81 dB), 0.2 fF gives +2.8 dB of peaking near 600 MHz and **0.5 fF oscillates** (1 fF at tt). Supply/ground L up to 5 nH with the 30 pF decap is fine.

**Next steps, in order:**
1. **Floorplan** (with Matt):
   - the macro at the right of the tile (the pin order assumes it), the analog on the left next to the ua pins;
   - analog block placement, decap, guard rings;
   - TX away from the RX input; deep n-well for the RX chain or not;
   - the chain coupling rule above: keep the chain's last stages and the detector away from the pads and stage 1.
2. **Layout of the remaining blocks with the same flow** (`layout/gen/<block>.py`, `layout/check.sh`, `layout/pex.sh`, a `tb_<block>`), then **integration in the 3x2.** Switch `mag/Makefile` to `tt_analog_3x2_3v3.def`, `make start`, place the hardened macro (`openlane/radio_digital/runs/cg_260x190`).
3. Not blocking: overload recovery (key a −10 dBm tone), TX at 10/50 °C, the −90 dBm joined run, the max-slew warnings in the harden (marginal, mostly ss).

**Parked:** 63-chip Gold code (e2e first), tnt's `rf_top` SRAM (if data mode needs buffers), dipole tuning (wait for real radios), wire-as-matching antenna idea, SDR bench tests (not needed).

## Re-verify: rdeg 2 MΩ, decaps, chain stability (2026-10-08 evening)
Run from `build/vfy` (its own `.spiceinit` with `num_threads=4`, so it can share the CPU with another ngspice).
- **Comparator** (`tb_comp`, and `TBS=comp sim/corners/rx_corners.sh`, which now has trim points 0.6 0.8 0.9 1.0 1.1 1.2 1.8 V):
  - tt 27 °C: trim offset −18.6 mV (DAC 0) … −5.4 (0.6 V) … +0.8 (0.9 V) … +8.9 mV (1.8 V), monotonic. Offset vs CM, noise (28 µV) and speed (0.36 µs) unchanged.
  - **The old "0.107–0.153 mV/LSB" was the average over DAC 0.6–1.2 V.** The transfer is steep near 0.6 V, so that average overstated the step where the servo actually sits (~0.95 V, code ~135). Same metric now: 0.086–0.135.
  - **Local step, DAC 0.8–1.2 V, every corner at 10/27/50 °C: 0.062–0.076 mV/LSB.** The trim at 0.8 / 1.2 V is about −0.2 / +3.6 mV. That covers the +0.5…+2.5 mV comparator offset with room either side; the full code range reaches −18…+9 mV.
  - sf at CM 1.55 V still has no threshold (known; det stays ≤ ~1.45 V in operation).
- **e2e** (`model/e2e.py`, noise case, 12 trials, 0.3 mV comparator noise, `--trim-mv` = the local step; outputs in `build/e2e/rdeg2_*.txt`):

| corner | NF / slope / trim | −92 dBm | −94 dBm |
|---|---|---|---|
| tt 27 °C | 11 / 12 mV/dB / 0.066 | 12/12 | 11/12 |
| fs 50 °C | 12 / 12.4 / 0.068 | 12/12 | 8/12 (was 3–4/12) |
| ff 50 °C | 11.4 / 9.7 / 0.067 | 12/12 | 10/12 (was 3–4/12) |

  - `--out` is resolved relative to `model/`; pass an absolute path, or the PNG save fails after the results print.
- **Passive (R/C) corners, comparator** (`CORNERS="hh ll ss_hh fs_ll" TEMPS="10 50" TBS=comp`): the local step is 0.056–0.060 at hh / ss_hh and 0.072–0.085 mV/LSB at ll / fs_ll, ∝ 1/rdeg as expected. Offsets are unchanged. **The whole MOS × R/C × temperature span is 0.056–0.085 mV/LSB.**
  - The averager's τ is a cap ratio, so it doesn't move. The LPF corner moves with R·C (~11 kHz at hh, ~20 kHz at ll), inside the 10–20 kHz span the e2e `--bv` sweep already covered.
- **Bias OTA loop** (`sim/bias/loop.sh`): the loop is broken at M2's gate (Middlebrook voltage injection) in tb_bias, with real diode loads. At all 5 MOS corners × 10/27/50 °C: **PM 90–91.5°**, unity gain 0.75–2.2 MHz (Cc dominant pole), −180° near 100–115 MHz (large gain margin), DC loop gain 28–35 dB. That loop error is why tb_bias shows 59.4 rather than 60 µA.
- **Mixed-signal −94 dBm with rdeg 2 MΩ** (RTL servo → real `r2r` → real `comp_ct`; `sim/plots/mixed_-94.png`): pin order OK (1172 settled steps, all ±1). The servo goes 128 → mean 109 and dithers 102–118 (std 3.4 LSB ≈ 0.24 mV at ~0.07 mV/LSB; before: 105–122, std 3.2 LSB at the larger step). **The burst is detected: the event pin opens at 14.67 ms**, the same as with 1.4 MΩ.
  - The `tools/longrun` done marker says `exit 1` for these runs. That's the `grep -v` at the end of `tools/osic`, which exits 1 when all output went to a log. Check the log tail instead.
- **Decaps** (`sim/decap/decap_ac.sh`; C = Im(I)/ωV, ESR = Re(1/Y)):
  - decap_vapwr **50.06 pF**, ESR 0.011 Ω; decap_vdpwr **29.9 pF**, ESR 0.069 Ω. Same at 1 / 100 / 434 MHz and at supply ±10 %. One 10×10 MIM unit is 206 fF, so the MOS part is ~29.4 pF thick-oxide (2.9 fF/µm²) and ~23.8 pF thin (7.9 fF/µm²).
  - BSIM here is quasi-static, so it shows no channel resistance. Hand estimate: ~1–2 Ω for the parallel L = 5 µm channels, an RC corner of several GHz. Fine.
- **`tb_radio_analog`** with the decaps: op_rx, op_off, −60 dBm det (1.206 V) and TX (484.8 MHz, +3.67 dBm, VAPWR 11.25 mA, VDPWR 0.23 mA) are all identical to before. The TX run had died on ngspice's memory check; the generator now has a `.save` list.
- **Chain stability** (`sim/chain/stability.sh`, from tb_chain with real passives, tt, 1 % mismatch; `CNODE=o1p` moves the coupling to stage 2's input; ~20 s per case). The script now zeroes the testbench's −80 dBm tone and 10 MHz CM tone, and its early window is 5–25 ns (the kick has rung down by 20 ns).

| L (supply and ground) | Ccpl out_p → | kick: late/early | AC gain 434 MHz | AC peak |
|---|---|---|---|---|
| 0 / 2 / 5 nH | none | ~2e-10 (decays) | 76.7 dB | 76.9 dB @ 381 MHz |
| 2 nH | pad_p 0.01 / 0.1 fF | decays | 76.7 / 76.8 | 76.9 / 76.8 |
| 2 nH | pad_p 0.2 fF | decays | 76.9 | 77.4 |
| 2 nH | pad_p 0.3 fF | decays | 76.7 | 78.7 @ 576 MHz |
| 2 nH | pad_p 0.5 fF | decays | 76.2 | 83.2 @ 603 MHz |
| 2 / 5 nH | pad_p 1 fF | **1.0: oscillates (2.1 V pp)** | 73.6 | 83.3 @ ~630 MHz |
| 2 nH | o1p 0.01 / 0.03 / 0.1 / 0.3 fF | decays | 76.6 / 76.6 / 76.3 / 75.1 | 76.9 / 76.7 / 76.3 / 78.7 |

  - **ss 10 °C** (`CORNER=ss TEMP=10`; 81.2 dB at 434 MHz, the highest-gain corner), 2 nH, coupling into pad_p: 0 / 0.05 / 0.1 / 0.2 / 0.3 fF give peaks of 81.4 / 81.3 / 81.6 / 83.6 / 87.6 dB, all decaying; **0.5 fF oscillates** (late/early 0.79, 1.6 V pp; AC peak 98 dB). So the limit is half the tt one: **≤ 0.1 fF**.
  - **Supply/ground bounce is not a problem.** The differential chain draws nearly constant current; VDPWR moves < 7 µV pp after the kick, even at 5 nH (which with 30 pF resonates near 410 MHz).
  - **Coupling is the problem.** Keep out → input (pad or o1) asymmetric coupling ≤ 0.1 fF (ss 10 °C), i.e. don't run the last stages' outputs or the detector taps next to the input or stage 1. Symmetric coupling (both sides alike) mostly cancels, so route the chain as a differential pair with mirrored geometry.

## Clock gating + gate-level tests (2026-10-08)
- **`rd_cg.v`:** `sky130_fd_sc_hd__dlclkp_1` (latch-based ICG; silicon evidence from TT08 #770). Under `ifdef SIM` it's a behavioural latch + AND, for RTL cocotb and the mixed-signal build.
- **`rd_corr.v`:** sr0..sr3 are clocked by `gclk0..3 = clk & en0..3`, with the same enables as before (shift on a window end, the 127-clock rotation, the post-reset clear). That removes 508 enable muxes.
- **Harden:**

| run | die (µm) | std cells | hold buffers | util | result |
|---|---|---|---|---|---|
| pins_300x210 (no gating) | 300 × 210 | 40.6k µm² | 841 | 75 % | clean |
| cg_300x210 | 300 × 210 | 32.5k | 638 | 60 % | clean |
| **cg_260x190** | **260 × 190** | 31.7k | 637 | 77 % | **clean**: setup ≥ 26.7 ns, hold ≥ 0.11 ns (all corners), 0 DRC / LVS / antenna |

  - CTS builds a tree after each gate (clock buffers 1.5k → 2.2k µm²). The 4 dlclkp cells are in the netlist.
- **Gate-level simulation:** `cd verilog/test && PATH=$HOME/work/asic-workshop/venv/bin:/usr/bin:/bin GL=1 SIM_BUILD=sim_build_gl COCOTB_RESULTS_FILE=results_gl.xml make` (~35 min).
  - It uses the hardened `nl.v` (default `runs/cg_260x190`; override `GL_NETLIST`) plus the cell models in `build/gl_models/`, copied from the image's PDK (command in the Makefile). Flags: `-DFUNCTIONAL -DUNIT_DELAY=#1`.
  - **15/15 pass**: all 9 RX vectors (trim code checked at every sample, events and toggles), the TX codes, straps and phases.
  - In GL mode the tests use pins only: event close = falling edge of `uio_out[4]`, score = the 7-seg digit, LED = DP. Two TX checks that read internal signals are skipped. `PINMON=1` runs the pin monitors on RTL; they agree with the internal ones.

## Mixed-signal: the RTL servo on the real analog (sim/mixed/, 2026-10-08)
- **Build:** `tools/osic bash sim/mixed/build_so.sh` verilates the RTL (with `SIM`) into `build/mixed/radio_digital.so` for an XSPICE `d_cosim` instance.
  - This is ngspice's `vlnggen` redone in bash: the image's ngspice lowercases the script's shell lines, and Verilator 5.048 rejects `-mdir`.
- **Deck:** `python sim/mixed/gen_mixed.py <level> [tstop]` writes `build/mixed/mixed_<level>.cir`.
  - **The d_cosim port list is generated from the build's `inputs.h` / `outputs.h`**: header order, each bus MSB first, as `verilator_shim.cpp` maps them. Every bit gets its own node name (`trim_out_7 … trim_out_0`), so the list can't drift from the .so. (Outputs come in port-declaration order, e.g. `rx_en` first, not the order you'd guess.)
  - Analog: det (`build/det_<level>.inc` from `sim/rx/gen_det.py`) → `lpf_rc` → `avg_sc` (sc_phi from the RTL) → `comp_ct` (trim = `r2r`(trim_out) + 1 pF) → comp_in. The comparator bias is ideal (1 µA); the subcircuits come from the `radio_analog` netlist.
- **Run** in the osic image from `build/mixed`: `ngspice -b mixed_<level>.cir` (15.2 ms ≈ 14 min alone). **Analyse:** `python sim/mixed/plot_mixed.py <level>` → `sim/plots/mixed_<level>.png`.
  - **Pin-order check:** rx_en high; the code starts at 128; every settled ladder change is exactly ±1 LSB, one per 13 µs tick. A reversed or shifted bus would give other step sizes.
- **Results** (comparator with rdeg 1.4 MΩ, i.e. before the change):

| det | pin order | servo | event pin (uio_out[4]) |
|---|---|---|---|
| −70 dBm | OK (1169 steps, all ±1) | 128 → ~114 in 0.25 ms (trims ~1.75 mV of real comparator offset); during the burst it wanders ±40 codes chasing 50 % ones over long chip runs (harmless: the 100 mV swing dwarfs the ±10 mV trim) | opens at the end of the 127-chip burst (14.68 ms) |
| −94 dBm | OK (1171 steps, all ±1) | dithers 105–122 around ~113 (std 3.2 LSB ≈ 0.4 mV) on the detector noise | **opens (14.67 ms): the burst is detected in the real loop** |

- One burst per run, so no LED toggle (that needs 2 of 3 bursts).

**How to run things:**
- cocotb: `cd verilog/test && PATH=$HOME/work/asic-workshop/venv/bin:/usr/bin:/bin make` (~12 min); gate level: add `GL=1 SIM_BUILD=sim_build_gl COCOTB_RESULTS_FILE=results_gl.xml` (~35 min). Run it as `bash -c 'cd verilog/test && …'`: `make -C` breaks the Makefile's `$(PWD)`, and a backgrounded `cd` may not stick. With the login PATH, oss-cad-suite's python (no numpy) gets picked up and the run dies at import. `COCOTB_TEST_FILTER` takes one test name (a `|` alternative matched nothing).
- Generators: `python3 xschem/gen/<x>.py`. Netlist: `tools/osic bash -c 'xschem -n -s -q -o build xschem/<tb>.sch'` (grep the netlist for `IS MISSING`).
- Simulate in `build/` via `tools/osic`. Analysis/plots: `~/work/asic-workshop/venv/bin/python` (system python has no numpy).
- `tools/osic` copies the tracked root `.spiceinit` into `build/` each run.
- **Don't run ngspice processes in parallel** (each uses 8 threads), and **don't edit a script while it's running**.
- **All the xschem/ngspice traps and speed lessons are in `docs/sim_learnings.md`.** Read that before writing a new testbench.

## Joined overnight run (done 2026-10-08 12:08, 14.3 h)
The fully joined transistor-level RX at −70 dBm: antenna → comparator, RF noise, 400 µs, real chip timing (`sim/rx/joined.sh`). Plot: `sim/rx/plot_joined.py -70` → `sim/plots/rx_joined.png`. (Ideal passives and bias, as of then.)

| −70 dBm | det off | det on | det swing | LPF noise, signal off (1 µs det std) |
|---|---|---|---|---|
| joined (transistor level) | 1.4411 V | 1.3407 V | **100.4 mV** | **0.52 mV** rms (1.88 mV) |
| split model (gen_det.py) | 1.4381 V | 1.3325 V | 105.6 mV | 0.59 mV rms (2.12 mV) |

- Swing −5 % (~0.4 dB at 12.6 mV/dB). The noise-only fluctuation, which is what sets −94 dBm, is within ~10 %. **RX first pass confirmed.**
- Optional −90 run: `tools/longrun joined90 tools/osic bash -c 'cd build && LEVELS=-90 TSTOP=250u ../sim/rx/joined.sh'` (~6–10 h).

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

## Area and the cap shrink (sim/area/area_netlist.py, 2026-10-08)
- **`sim/area/area_netlist.py`** evaluates the real `radio_analog` netlist (every device's W/L/nf/m, poly R and MIM geometry), grouped by block.
  - Footprint rules: thin MOS (W/nf+1)·(nf·(L+0.6)+0.6); thick MOS with HV spacing; poly (W+1)·(L+3); MIM (W+1.5)·(L+1.5); ×2.5 routing.
  - The ring and the R2R ladder use their measured layouts. **Each block counts as max(routed devices, its MIM).**
  - Plus decap (VAPWR 50 pF, VDPWR ~30 pF) and 10 % for guard rings and spacing. Treat as ±25 %.
- **Before the shrink:** analog 51.8k µm² against 43.1k left beside the digital (300 × 210 + 5 µm halo): **120 %**.
- **Cap shrink, same time constants:**

| | was | now | check |
|---|---|---|---|
| LPF | 1 MΩ (136 µm) + 6 × 30² MIM (10.9 pF) | **2.95 MΩ (400 µm) + 2 × 30² (3.7 pF)** | tb_lpf: 14.7 kHz (14.4), rise 23.7 µs (24) |
| averager | Cs 11² (0.25 p), Cavg 5 × 30² (9.1 p) | **Cs 7² (0.1 p), Cavg 2 × 30² (3.7 p)** | tb_avg: τ 0.44–0.46 ms (0.47–0.48); offset ≤ 0.09 mV (≤ 0.04), static, trimmed out |
| cdet | 5 pF | **1 pF** (det pole ~20 MHz) | CW transfer DC levels identical; 434/868 MHz ripple on det 2–18 mV pp (was 1–4), removed by the LPF |
| chain cin | 2 pF | **kept at 2 pF** | 1 pF cost 0.6 dB NF (11.0 → 11.6) for ~1k µm²: not worth it |

  - kT/C on the LPF is still ~35 µV. The comparator is continuous-time (no kickback), so the big LPF cap wasn't needed.
  - tb_radio_analog unchanged: RX op, off current, TX; −60 dBm gives det 1.206 V.
- **After: analog 42.2k against 43.1k: 98 %, about 99 % of the whole tile.** It fits, but with no margin for a ±25 % estimate.
  - Next levers: clock-gate the digital's chip registers (~8–10k with fewer hold buffers); VAPWR decap 50 → 30 pF (~5k, ripple 0.05 → ~0.15 V); bias mirrors with fewer, wider units (~1.5k).
- `sim/logdet/transfer_cw.txt` is an old curve (~40 mV below the current detector in the mid range). `gen_det.py` / `plot_joined.py` use it with their calibrated −3.8 dB shift, so it's left as is.

## Digital re-harden (LibreLane v3, openlane/radio_digital/config.json, 2026-10-08; before clock gating, see "Clock gating" above for the final 260 × 190)
- **Run:** `tools/longrun harden tools/osic bash -c 'cd openlane/radio_digital && librelane --pdk sky130A --run-tag <tag> --overwrite config.json'` (~5–10 min).
  - `config.json` replaces the OpenLane 1 `config.tcl` (kept for reference). The root Makefile's `harden` target is still the OpenLane 1 flow and doesn't work here.
- **Synthesis:** 27,704 µm² of cells, 55 % flip-flops (717).
  - `rd_gold.v`'s LFSR step functions became wires: Yosys' pre-synthesis check flags function-local wires in always blocks as undriven (a false positive; the post-synthesis check was clean). cocotb 15/15 after the change.
- **Size trials:**

| die (µm) | result |
|---|---|
| 300 × 150 | detailed placement fails: after CTS, ~850 hold buffers push utilisation over |
| 340 × 170 | detailed routing doesn't converge (~3,100 violations, 1,847 global-route overflows, mostly horizontal); killed |
| **300 × 210** | **clean** |

- **300 × 210 µm, final pin order** (run `pins_300x210`):
  - 0 DRC (router, magic), 0 LVS, 0 antenna violations;
  - setup slack ≥ 26.8 ns and hold ≥ 0.11 ns at all corners (50 ns constraint; it runs at 100 ns);
  - utilisation 75 %, incl. 841 hold buffers (~10.4k µm², from the shift registers' flop-to-flop paths);
  - warnings: max slew, marginal (worst 0.756 vs 0.75 ns at tt; 179 across corners, mostly ss); max fanout on clock-tree leaves (14 vs 10). Harmless at 10 MHz; tighten in the final run.
- **Pin order** (`pin_order.cfg`, rationale in `PIN_ORDER.md`), assuming the macro sits at the **right end of the tile** with the analog to its west near the `ua` pins:
  - **North:** the 42 TT pins in the template's left-to-right order, at the template's own 2.76 µm pitch, x 37.5–150.7 from the macro's west edge: uio_oe[7..0], uio_out[7..0], uo_out[7..0], uio_in[7..0], ui_in[7..0], rst_n, clk.
  - **West, bottom → top:** tx_en, tx_en_n (12–17 µm); rx_en, dbg_en (33–37); comp_in, sc_phi1/2 (53–62); trim_out[0..7] contiguous (74–102).
- **The 3x2 template** (`tt_analog_3x2_3v3.def`, 493.12 × 225.76 µm): all pins are in the tile's left ~140 µm. TT digital pins along the top at x 15–131; ua[0..7] along the bottom (ua[0] 137, ua[1] 117, ua[2] 98, ua[3] 79, ua[4] 59 µm). With a 300 × 210 macro at the right, the analog gets ~190 × 226 µm (~43k µm²) next to the ua pins. Tight against the area estimate, so clock gating (−8k µm²) may be needed. That's for the floorplan.

## Analog top + TT top (xschem/gen/top.py, 2026-10-08)
- **`radio_analog`:** every analog block wired as on the chip, real bias.
  - `bias_gen` (en = rx_en) feeds vcm, the chain (60 µA), the detector (2 µA) and the comparator (1 µA).
  - RX: `lna_chain` → `log_det` → det → `lpf_rc` → lpf; `avg_sc` (lpf, sc_phi1/2) → avg; `comp_ct` (inp avg, inn lpf, trim = `r2r`(trim[7:0]) + 1 pF MIM) → comp_out.
  - det → `dbg_tg` (dbg_en) → dbg.
  - TX: `tx_top` with key = en_p = tx_en, en_n = tx_en_n.
- **`radio_digital.sym`:** black box for the hardened macro (`spice_sym_def`). Its netlist comes from the OpenLane run.
- **`tt_um_mattvenn_radio.sch`:** the two together on the TT pins: ua[0]/ua[1] TX, ua[2]/ua[3] RX, ua[4] debug.
- The chain's mismatch knob `mm` is now a subcircuit parameter (default 0; the testbenches pass their `.param mm`), so top-level netlists don't depend on a testbench global.
- **`tb_radio_analog`** (pad models on all five pins, both dipoles, a 1 MΩ probe on ua[4], digital interface from sources; ~3 min):

| case | result |
|---|---|
| RX on, no signal | VDPWR 2.97 mA, VAPWR 0; vcm 1.201 V, det = lpf 1.521 V, trim 0.949 V (code 135), TX pins 0 V |
| all off (rx_en = tx_en = 0) | 0.9 µA (the comparator's unswitched VDD/2 divider) |
| TX keyed, RX off | 484.8 MHz, +3.67 dBm, 3.3 / 3.9 ns on / off, VAPWR 11.25 mA, VDPWR 0.23 mA, the same as `tb_tx` |

- Not in the loop yet: the digital (a mixed-signal run with the RTL, as tt08's `sim/mixed.cir`, would close it).

## VAPWR feed and decap (sim/tx/vapwr.sh + vapwr.py, 2026-10-08)
- **Model:** tb_tx with an ideal 3.3 V source → 0.5 Ω → L (bond wire + package + board) → on-chip VAPWR, decap Cdec to ground. The ground return is still ideal. tt; ~1 min per case.

| L | Cdec | P into dipole | VAPWR min at turn-on | ripple while on |
|---|---|---|---|---|
| 2 nH | 0 | +3.64 dBm | 2.94 V | 0.53 V pp |
| 5 nH | 0 | +3.75 | 2.61 | 1.01 |
| 5 nH | 20 pF | +3.75 | 3.06 | 0.31 |
| 5 nH | **50 pF** | +3.67 | 3.18 | **0.05** |
| 5 nH | 100 pF | +3.65 | 3.21 | 0.04 |
| 10 nH | 0 | +3.85 | 2.42 | 1.20 |
| 10 nH | 50 pF | +3.66 | 3.12 | 0.07 |

- **The TX doesn't need the decap:** power and frequency (the ring is on VDPWR) don't move.
- **But without it ~1 V pp of 434 MHz rides on the chip's 3.3 V net**, which is other projects' supply and another radiator. **Reserve ~50 pF on VAPWR** (above that, little gain): roughly 10–12k µm² as thick-oxide MOS cap with MIM over it. Add it to the area estimate and floorplan.

## Trim DAC (xschem/gen/dac.py, 2026-10-08)
- **`r2r`:** an 8-bit R-2R schematic matching the reused tt08 layout (`tt08-analog-r2r-dac-3v3/mag/r2r.mag`, its `r2r.lvs.spice`) device for device, so LVS lines up:
  - unit R = `res_high_po_1p41` L 45 ≈ 10.6 kΩ; 2R = two units in series;
  - a start module with the 2R termination, 7 bit tiles, and 2 dummies (27 units).
  - The TT08 *schematic* used 0p35 devices, but its layout is 1p41.
- **Driven straight from the digital's `trim_out`** (1.8 V std-cell outputs; no level shifters, unlike TT08's 3.3 V version), so the output is 0…1.79 V.
- **`tb_dac`:** out = code/256·1.8 V exactly (0, 1, 85, 128, 135, 255); Rout 10.64 kΩ.
  - VDD ripple: the trim pair compares the DAC against its own VDD/2, so what's left is (code/256 − ½) = 0.027 at the operating code (~135). Through the trim gain (~1/56) that's < 1 µV per mV of ripple at the comparator input: no filtering needed beyond a small MIM on `trim` against clock-edge spikes (add at the top level).
  - The digital's output drivers (~hundreds of Ω) sit in series with the 21 kΩ 2R legs: ~1–2 LSB of DNL at the major transitions (0.25 mV of trim). Fine for the servo. When re-hardening, use balanced, strong buffers on `trim_out`.

## ua[4] debug switch (xschem/gen/dbg.py, done 2026-10-08)
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

## Area ballpark (sim/area_estimate.py; superseded by sim/area/area_netlist.py, see "Area and the cap shrink")
- Analog, all blocks now first-passed: devices ~15,700 µm² (×2.5 routing; ring and R2R ladder from measured layouts: 228 µm² for 19 stages, 3,864 µm² for the ladder) + MIM ~21,300 µm² (28 % of a 2x2; can't overlap the digital).
- **2x2:** ~102 % with the digital as is (40,500 µm² placed); **~79 %** with the RTL size reduction (~23,000 µm²). Both before decap, guard rings and power routing.
- **3x2** (~113,000 µm²): ~68 % / ~53 %.
- **Decision (2026-10-07): fine for now; go to 3x2 if needed** rather than shrink early. 3x2 is confirmed allowed for analog (2026-10-08).
- Easy cap savings if ever wanted: LPF 4 MΩ / 2.7 pF (the comparator has no kickback); avg Cs 0.1 p / Cavg 3.6 p; cdet 1 p; chain cin 1 p (NF check). Together 19k → ~8k µm² of MIM.
