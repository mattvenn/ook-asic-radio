# Plan: tunable TX ring (433.92 MHz for fob record / replay)

Why, and the numbers behind it: [trim_433.md](trim_433.md). This is the work plan. It has six phases. Each phase
ends at a **gate where Matt reviews and approves** before the next phase starts. Nothing merges to `main`
until gate 5: all work happens on a branch (`ring-tune`), so `main` stays a tapeout-ready fallback (the
untrimmed ring, `NINV` 22 or 24) the whole time.

**Target spec** (confirmed or changed by Matt at gate 1):

| Item | Target |
|---|---|
| Tuning range on silicon | covers 433.92 MHz at every corner, 10–50 °C, VDPWR 1.71–1.89 V, with the ×0.866 silicon factor applied **and** with ×1.0 (a true-tt lot) |
| Fine step | ≤ 20 kHz effective (with ΣΔ), monotonic within each coarse setting |
| Coarse / fine overlap | fine range ≥ 1.3 × the largest coarse step, at every corner |
| FM from the control path | ≤ 10 kHz (ΣΔ ripple, DAC glitches) |
| Jitter / wander | not worse than the current ring by more than 2× (bench: 45 kHz std) |
| TX power at the 433.92 setting | within 0.5 dB of today's (extracted tile RC +3.18 dBm), arm duty within today's range |
| Off state | both arms low; with the ring free-running, carrier leakage ≥ 40 dB below on |
| RX | unchanged: every RX regression number identical, or within its noise |
| Area | ≤ 1.5k µm² analog; macro ≤ 210 × 220 µm |

---

## Phase 1: verify the approach (sims only, no layout)

**Goal:** choose the tuning structure from measurements, not estimates. Everything runs on the extracted
`tx_ring` (`layout/pex/tx_ring.spice`) or on its calibrated schematic stand-in (3.2 fF per stage).

**Candidates:**
- **A. Taps + varactor:** std-cell ring with a tap-select mux (coarse) and `cap_var_lvt` loads driven by the
  filtered R2R (fine).
- **B. Starving legs + varactor:** a short, fast ring of custom inverters with binary-weighted header /
  footer legs switched digitally (coarse), plus varactor fine as in A.
- **C. Analog current-starved:** custom ring with an analog bias from the R2R, plus an attenuated second
  fine path.

**Tests:** new scripts in `sim/ring/tune/`, one ngspice at a time.

1. **Tuning curves:** frequency vs control (every coarse code; fine swept 0–1.8 V in 32 steps) at tt / ss /
   ff / sf / fs × 10 / 27 / 50 °C. Output: range, overlap and the largest local Kvco per corner. Check the
   target-spec range and overlap rows.
2. **Supply sensitivity:** df/dVDD at 1.71 / 1.80 / 1.89 V, tt and ss. This replaces the 0.5 %/10 mV estimate
   in trim_433.md.
3. **Jitter:** a transient-noise run (`trnoise` on the devices, as in `sim/logdet/noise_tran.sh`) of 2000
   periods. Period-jitter histogram → frequency std. Compare against the same run on today's ring.
   Includes the bias noise for B and C.
4. **Duty into tx_ls:** ring → `tx_ls` (kn 14 / kp 8) → `tx_drv` → pad model, at the 433.92 setting per
   corner, with arm duty and power from `sim/tx/tb_tx.py`'s metrics. Pass: within 0.5 dB of today.
5. **Control path:** R2R (`sim/dac/tb_r2r.py` netlist) → RC filter → varactor node, driven by a first-order
   ΣΔ stimulus at 10 MHz.
   - Measure ripple, the FM it produces, and settling.
   - Check the worst idle-tone fractions (1/16, 15/16).
   - Check the extra load on `trim` doesn't change the comparator trim step (`tb_comp_ct.py`).
6. **Divider:** ripple ÷256 on the ring output at the fastest setting, ff 10 °C. Does the first flop
   toggle with margin, and how much does its load shift the frequency?
7. **Free-running leakage:** `tx_top` with `key = 1` and `en_p = en_n = 0`. Carrier at the dipole vs on.

**Deliverable:**
- `docs/ring_tune_results.md`: one table per candidate (range, overlap, step, df/dVDD, jitter, TX power,
  area estimate, risk) plus plots in `sim/plots/ring_tune_*.png`.
- A recommendation and the frozen block spec: stage count, number of coarse bits, fine range, filter R / C,
  divider ratio.

> **Gate 1 (Matt):**
> - pick A, B or C;
> - confirm the target spec, the control-bit budget (coarse bits and fine bits → macro pins) and whether
>   the raw-RX slicer tweak (`sc_phi` ÷4) is in;
> - go / no-go. **No-go → set `NINV` on `main` (STATUS next step 1) and stop here.**

---

## Phase 2: build the tunable ring block

**Goal:** the new TX blocks, schematic and layout, each clean and matching its extraction.

1. **Schematics** (generators, as now):
   - `xschem/gen/tx.py`: `tx_ring_tune` (the chosen ring, with coarse inputs and a `vtune` pin),
     `ring_div` (÷256), `tune_rc` (R + C filter);
   - `tx_top` gets a separate `ring_en` (key), keeping `en_p` / `en_n`, plus new ports `ring_sel[n:0]`,
     `vtune_in`, `ring_div`.
   - Netlist check: no `IS MISSING`.
2. **Block testbenches:** `sim/tx/tb_tx_ring_tune.py [--pex] [corner] [codes]`, reporting frequency vs code,
   duty, current and divider output. Re-run `tb_tx.py` (all corners) with the new ring at the 433.92 setting.
3. **Layout:**
   - `layout/gen/tx_ring.py` (v2) using `rows.py`, keeping the two-row fold so there's no long feedback
     wire, with the varactors and divider in the same rows;
   - `tune_rc` from `passives.py` (xhigh poly + MOS / MIM cap, like `lpf_rc`).
   - Power: VDPWR / VGND rails sized from the measured currents (docs/layout.md EM table).
4. **Checks per block:** `tools/osic bash layout/check.sh <block>` (magic DRC, antenna, KLayout DRC, LVS);
   `layout/pex.sh <block>`; `tb_* --pex` vs schematic.
   - Pass: frequency vs code within 2 % of schematic-plus-wiring at tt, the same overlap margin at all
     corners, TX power within 0.3 dB of the schematic run.
5. **Docs:** a "Tunable ring" section in docs/layout.md, and the block rows in docs/verification.md.

**Deliverable:**
- clean GDS for each block (viewer links in layout/README.md);
- the schematic vs extracted table;
- the frequency-vs-code table that firmware will start from.

> **Gate 2 (Matt):** review the schematics, the layouts in the viewer, the extracted tuning curves and the
> TX power. Approve the block footprints and pin positions for the floorplan.

---

## Phase 3: control in the RTL and the macro

**Goal:** `radio_digital` drives the ring, hardened and passing every test.

1. **RTL** (`verilog/rtl/`): a new `rd_tune.v`, wired up in `radio_digital.v`:
   - **Config register:** loaded in raw TX mode from `ui_in[0]` (shift clock), `ui_in[1]` (data) and
     `ui_in[2]` (latch), through the existing `code_s1/s2` synchroniser with edge detect. Holds
     `{ring_free, ring_sel, fine}`, with widths from gate 1. Reset value: the mid-range code from phase 2.
   - **ΣΔ:** a first-order accumulator on the fine LSBs, so `trim_out = role_tx ? fine_msb + carry :
     servo_trim` (saturating).
   - **Enables:** `ring_en = raw ? (ring_free | uio_in[2]) : tx_code_en`. `tx_en` / `tx_en_n` still drive
     the arms. Code mode is bit-identical to today.
   - **Measurement:** 2-flop synchroniser on `ring_div` → `uio_out[6]` in raw TX (RX trim direction
     otherwise).
   - The raw-RX `sc_phi` ÷4, if approved at gate 1.
   - `lint.sh` clean.
2. **Tests** (`verilog/test/test_radio.py`):
   - **The existing 15 must still pass unchanged** (code mode and RX are untouched).
   - New tests:
     - config shift and latch;
     - reset value;
     - ΣΔ mean over 4096 clocks equals `fine` / 16 to 1 LSB for a sweep of codes;
     - `trim_out` stays the servo in RX;
     - `ring_en` / arm enables in all modes;
     - `ring_div` passthrough;
     - `sc_phi` ÷4 timing.
3. **Model:** `model/tune.py`, a behavioural ring (the phase-2 frequency table) plus the calibration
   algorithm the firmware will use (binary search over coarse then fine against a count of `ring_div`).
   This shows the search converges to ±10 kHz at every corner table, in ≤ 20 measurements.
4. **Mixed signal:** `sim/mixed/` with the new RTL driving the real `r2r` → `tune_rc` → extracted tuning node
   (with the ring), for a few `fine` codes. Check the ripple / FM and settling seen by the ring.
5. **Harden** (`openlane/radio_digital`):
   - new pins in `layout/floorplan/variant_layout5.json` → regenerate `pin_order.cfg`;
   - DIE_AREA 200 × 220 first, 210 × 220 if routing fails (the 190 failure in history.md is the reference);
   - signoff: DRC, LVS, antenna, timing at all corners;
   - `make GL=1` all tests on the new netlist;
   - copy to `macros/radio_digital/`, update `PIN_ORDER.md`.

**Deliverable:**
- RTL + tests (RTL and GL all passing);
- macro views with the signoff summary and utilisation;
- calibration-model results;
- mixed-signal ripple numbers.

> **Gate 3 (Matt):** review the RTL diff, the pin list, the test results, the macro size, and the
> calibration flow (which also becomes the firmware spec).

---

## Phase 4: floorplan

**Goal:** everything placed and the routes planned before anything is routed.

1. Update `layout/floorplan/blocks.json` with the new block sizes and the macro size, then re-run the
   floorplan tool (`layout/floorplan/page`) from layout 5 as a new variant.
2. **TX corner:** `tx_ring_tune` and `ring_div` sit where `tx_ring` is now (beside `tx_ls`, ring output
   up), keeping the ring → `tx_ls` route ≤ 22 µm and the a / b routes as now (13.5 / 13.7 fF).
   `tune_rc` goes next to the ring so the high-impedance `vtune` node is short.
3. **New routes** (`layout/gen/top_nets.py`): `ring_sel[n:0]`, `ring_en`, `ring_div` (macro ↔ TX corner,
   in the TT channel along the top with the existing enables), and the `trim` branch from `r2r` to
   `tune_rc`. That last one is the sensitive route. Rules:
   - it doesn't cross the chain's input zone or `det` / `lpf` / `avg`;
   - coupling into RX nodes is held to the existing budgets (≤ 0.1 fF asymmetric into the chain input;
     shield where it passes `avg` / `comp`);
   - `ring_div` (a 1.7 MHz square wave) is routed away from `lpf` / `avg` / `comp` and shielded.
4. **Power:** the new block's VDPWR / VGND feeds, keeping the power-fix structure (dedicated RX trunks,
   `VDPWR_TX`).
5. Update `layout/floorplan/pins.md`, docs/floorplan_spec.md ("Chosen floorplan") and the area numbers
   (`sim/area/area_netlist.py`).

**Deliverable:** a floorplan image and the variant JSON, the route plan with lengths and expected coupling,
and the updated area / utilisation.

> **Gate 4 (Matt):** approve the floorplan and the compromises, especially the `trim` branch route and
> anything that moved.

---

## Phase 5: tile GDS and TT precheck

**Goal:** the routed tile, clean, exported, with the GitHub actions green.

1. Build and route: `tools/osic klayout -b -r layout/gen/top.py && tools/osic python3 layout/gen/route.py`.
2. `tools/osic bash layout/check_top.sh`:
   - magic + KLayout DRC 0;
   - LVS "Circuits match uniquely" against the updated `tt_um_mattvenn_radio` schematic (`xschem/gen/top.py`
     with the new nets);
   - TT power-pin precheck pass;
   - antenna: only the 7 known macro-internal violations, or fewer.
3. **Power re-check** (`sim/power/`, docs/power.md "Re-running"): EM on the new feeds < 50 %, TX VAPWR /
   VDPWR drop, and TX → RX coupling no worse than the "After the fix" numbers. This also covers the
   still-open rerun of the TX results after the re-floorplan.
4. `tools/osic bash layout/export_tt.sh`, then push the branch. The GitHub `gds` (TT precheck), `lvs` and
   `docs` actions must pass.
5. Update `info.yaml` pinout descriptions (uio[6] in raw TX, the ui_in roles in raw TX) and docs/info.md.

**Deliverable:** green actions on the branch, the check_top logs, and the power numbers.

> **Gate 5 (Matt):** review the layout in the TT GDS viewer, the precheck and action results, and the power
> numbers. **Approve the merge to `main`.**

---

## Phase 6: end-to-end verification

**Goal:** the whole tile still does everything it did, and the new function works on the extracted layout.

1. **Extracted tile** (`layout/pex_tile.sh lvs c rc`, `sim/top/tb_tile.py lvs c rc`, with `tb_tile_tx.py`
   for the TX sweeps):
   - **TX:** frequency vs code on the extracted tile at enough codes to rebuild the curve (3 coarse ×
     5 fine at tt; the codes nearest 433.92 at ss / ff), power at the 433.92 code, the off state, and
     free-running leakage.
   - **RX regression:** RX current, idle det / lpf, det at −60 dBm and the all-off current. Each must match
     the last RC numbers (2.985 mA, 1.491 V, 1.203 V, 0.910 µA).
2. **Mixed signal on the extracted blocks** (`gen_mixed.py --pex`, never run so far): −94 and −70 dBm bursts
   detected, so the `trim` branch hasn't hurt the servo loop.
3. **Joined RX on the extracted tile** (`tb_tile_joined.py`, 10+ h, already an open item): the
   antenna-to-comparator check on the final layout, now including the `trim` branch.
4. **Calibration end to end:** `model/tune.py` run on the extracted-tile frequency tables (tt / ss / ff).
   Show it converges to 433.92 ± 10 kHz at each corner, plus the predicted silicon code with the ×0.866
   factor.
5. **Raw TX replay in RTL:** cocotb drives a recorded fob pulse list (EV1527-style, Te 400 µs) into raw TX
   with `ring_free = 1`. Check that the arm enables reproduce it to within one clock.
6. **Docs:**
   - docs/verification.md (new rows and results);
   - docs/how_it_works.md (the tuning section);
   - STATUS.md;
   - trim_433.md (replace estimates with the measured numbers);
   - the bench firmware spec: record → clean up → calibrate → replay, in `bench/fw/` for when silicon
     arrives.

**Deliverable:** the results table against the target spec, every regression number side by side with the
last sign-off, and updated docs.

> **Gate 6 (Matt):** final sign-off of the design for the shuttle.

---

## Schedule and risks

Rough effort:

| Phase | Effort | Notes |
|---|---|---|
| 1. Verify | 2–3 days | mostly corner sweeps |
| 2. Block | 3–4 days | |
| 3. RTL + macro | 2–3 days | runs in parallel with phase 2 after gate 1; the harden waits for the pin list |
| 4. Floorplan | 1 day | |
| 5. GDS + precheck | 2–3 days | |
| 6. E2E | 2 days of work + ~1 day of unattended runs | rc ~1 h, joined 10+ h |

About **2.5–3 weeks** in total, against a November 2026 tapeout. The phase 6 runs replace STATUS next steps
2–4, which would have to be run anyway.

**Risks and fallbacks:**
- **Varactor tuning too weak under full swing** (phase 1). Fallback: more nodes, more coarse bits, or B's
  starving legs.
- **Macro doesn't route at 210 × 220.** Fallback: drop the optional `sc_phi` ÷4, or narrow the fine field
  and use more ΣΔ bits.
- **`trim` branch couples into the RX** (phase 4/6). Fallback: a separate small DAC for `vtune` instead of
  reusing `r2r` (more area), or shield the route.
- **TX power loss from duty** (phase 2). Fallback: re-tune `tx_ls` kn / kp with `tb_tile_tx.py`.
- **Schedule slips past the shuttle.** Fallback: `main` still carries the untrimmed design. Any gate can
  stop the work, and `NINV` gets chosen as in STATUS next step 1.
