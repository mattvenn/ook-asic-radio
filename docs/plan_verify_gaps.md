# Plan: close the verification gaps

Where these come from: a review of [verify_2026-10-11.md](verify_2026-10-11.md) against
[verification.md](verification.md). Every check the plan lists passes. This plan adds the checks the plan
doesn't have yet. The tunable TX ring is out of scope; it has its own plan, [plan_ring_tune.md](plan_ring_tune.md).

The work is in four phases, ordered by what they depend on, not only by severity. Each phase ends at a
**gate where Matt reviews the results**. A failing check opens a design change and is not patched over in this plan.

**Interaction with the ring work:** phases 1 and 2 don't depend on the ring and can start now. The TX parts
of 2.1 and all of phase 3 run on the tile. If the ring changes, run them after the ring lands, or run them
now and repeat them as part of that rerun. Item 4.1 (decap flatten) is a layout change, so do it in the same
tile rebuild as the ring.

## Gaps, ranked

| # | Gap | Severity | Phase |
|---|---|---|---|
| G1 | Supply voltage never varied at system level (only `bias_gen` alone, 1.7–1.9 V). PLAN.md calls supply the main open analog risk | High | 2 |
| G2 | No mismatch / Monte Carlo on the comparator path: offsets are systematic only, trim coverage unproven | High | 2 |
| G3 | Detection on the extracted RF chain never closed: mixed signal uses a modelled det waveform; the extracted-tile joined check is a 30 µs pair, 0.84 ± 0.5 mV vs 1.1 expected | High | 3 |
| G4 | TT wrapper / pin mapping never simulated: `src/project.v` is a stub, cocotb tests drive `radio_digital` directly, root `test/` is empty | High | 1 |
| G5 | No corners or temperatures on the whole extracted chip's RX; `rx_corners.sh` uses ideal bias sources | Medium | 3 |
| G6 | Sensitivity-edge margin in transistor sims rests on one noise seed per level | Medium | 3 |
| G7 | The mixed-signal ladder-step check fails at −94 dBm (1173 vs 1169 ± 3) and is waved off as ±1 toggling | Medium | 1 |
| G8 | Overload only partly covered: −10 dBm, ~130 µs bursts; no full 13 ms packet, no weak-after-strong, nothing ≥ 0 dBm | Medium | 3 |
| G9 | Tile power-up not checked (bias start-up only on `bias_gen` alone); "defined off state" item not verified | Low | 3 |
| G10 | The extracted-tile stand-in scripts live only in `build/`; verify report says the `plot_joined.py` fix is uncommitted (it went in with df17a26) | Low | 1 |
| G11 | `decap_vapwr_p1`–`p4` standalone magic DRC hvi.5 flags (tile clean) | Low | 4 |

---

## Phase 1: cheap, independent fixes (no long sims)

**1.1 Pinout check (G4).** Two parts:
- `tools/check_pinout.py`: parse `info.yaml`'s pinout, the `tt_um_mattvenn_radio` schematic netlist
  (`xschem -n`), and the macro's `PIN_ORDER.md`. Assert that every `ui_in` / `uo_out` / `uio_*` / `ua` bit lands on
  the macro or analog port info.yaml says it does. Also check that `uio_oe` is tied to match each uio pin's direction. Run it in the `lvs` or `docs` GitHub action.
- A cocotb smoke test at the `tt_um` level, gate level, in the root `test/` (the TT layout): a Verilog
  wrapper made from the schematic netlist (the analog blocks as empty stubs, the macro's GL netlist inside). Run three of
  the existing tests through the TT pins: `test_tx_codes`, `test_raw_and_straps`, `test_debug_strap`.

  Pass: the script finds no mismatches, and the three tests pass through the `tt_um` pins.

**1.2 Ladder-step check (G7).** In `sim/mixed/plot_mixed.py` (or wherever the 1169 ± 3 check lives), count steps of
size > 1 LSB separately from ±1 steps. The pin-order verdict uses only the large steps. Then rerun the −94 dBm
schematic case from its existing raw file.

  Pass: −94 dBm reports pin order OK with N ±1 steps, and a real bus swap is still caught. To confirm that, swap two DAC bits in a copy of
`radio_digital_sim.v`, rerun −70 dBm and check that it fails.

**1.3 Reproducibility (G10).** Move `build/verify/tile_joined_short.py` and `build/diag/tile_pair.py` into
`sim/top/` (e.g. as a `pair` mode of `tb_tile_joined.py`), and document the run command in verification.md. Fix the
"uncommitted" line in verify_2026-10-11.md.

> **Gate 1 (Matt):** pinout table confirmed, the new ladder check accepted, CI runs the pinout script.

---

## Phase 2: block-level statistics and supply (G1, G2)

**2.1 Supply sweeps (G1).** VDPWR 1.71 / 1.80 / 1.89 V; VAPWR 3.0 / 3.3 / 3.6 V for the TX driver. (Confirm the
TT supply tolerances first; use them if they're wider.)
- Add a `VDD=` / `VAPWR=` option to `rx_corners.sh`, `sim/tx/tb_tx.py` and `sim/top/tb_tile.py`, matching how
  `tb_bias_gen.py` already sweeps.
- **RX:** chain gain at 434 MHz, NF, det idle and slope, comparator offset and trim step at the DAC operating point.
  Run at tt and the two worst corners (ss 10 °C for gain and stability, fs 50 °C for sensitivity) × 3 supplies.
  Rerun `sim/chain/stability.sh` at 1.89 V, ss 10 °C, the highest-gain point.
- **TX:** ring frequency, power and arm duty, at 5 corners × 3 VDPWR × 3 VAPWR, schematic, and
  `--pex` at tt.
- Feed the worst RX gain / slope / trim into `model/e2e.py` (as for the corners): −92 dBm at the worst supply ×
  fs 50 °C.

  Pass: e2e −92 dBm ≥ 11/12 at every supply corner. Chain stable with the 0.1 fF rule. TX in the RX band
  (330–560 MHz on silicon, ×0.866) at every point, power within 1 dB of nominal.

**2.2 Comparator-path Monte Carlo (G2).** Use the sky130 mismatch models. Check which form the image's sky130A
supports (`mc_mm_switch=1` / the `_mm` corner sections) and record it in sim_learnings.md.
- `tb_comp_ct.py --mc N` (N ≈ 200): offset at the operating CM (LPF idle, 1.45–1.52 V), and the DAC code where
  the comparator switches. Run at tt 27 °C, then repeat at fs 50 °C and sf 10 °C (the high-CM offset corner, history.md).
- `tb_avg_sc.py --mc N`: hold offset and drift.
- Add the two (per-sample sum) and compare against the trim. Pass: at 4σ the switching code stays
  inside the servo's range with margin, i.e. the DAC within 0.6–1.4 V, where the step is still ≤ 0.085 mV/LSB, and not at a code end.
- `lna_chain` DC offset with mismatch: ~20 samples of the tt chain, output offset and gain. Pass: no stage
  saturates, gain within 1 dB of nominal.
- If the tail is wide, rerun e2e with the 4σ trim step and offset.

**Deliverable:** `docs/verify_supply_mc.md` with the tables, plus histograms in `sim/plots/mc_*.png`.

> **Gate 2 (Matt):** the supply and mismatch margins are accepted, or a design change is opened (trim range,
> attenuator ratio, comparator sizing).

---

## Phase 3: system level on the extracted chip (G3, G5, G6, G8, G9)

Run on sim-0 with at most 3 ngspice at once, extracting with magic 8.3.642.

**3.1 Extracted chain sensitivity, noise-free (G3).** The CW det-drop table from verify_2026-10-11 (−100 /
−90 / −80 / −70 dBm, no noise), on the extracted `lna_chain` + `log_det`. Also on the extracted tile (c and rc), with
the RF input at the pads and the trim held. This runs in minutes and gives an exact extracted-vs-model offset in dB.

  Pass: within 1 dB of the model at −90 / −100 dBm. Then feed the measured offset into e2e. Pass: −92 dBm ≥ 11/12.

**3.2 Closed-loop detection through the extracted RF chain (G3).** Build a mixed-signal deck that takes det from
the extracted chain + log_det with RF noise. Today it takes det from `gen_det.py`'s model waveform. Run a short
burst, not a full 127-chip run: the shortest stimulus where the correlator can open an event, e.g. a shorter
holdoff and a pre-settled averager / trim from the 3.1 operating point. Estimate the run time on sim-0 first;
if it is over ~2 days, report that and stop at 3.1.

  Pass: event at −90 dBm (the margin case) on the extracted chain.

**3.3 Seeds at the edge (G6).** Add `--seed` to `sim/rx/gen_det.py` and `gen_mixed.py`. Run mixed signal at −92 dBm, 5 seeds, schematic and `--pex`
(~15 min each).

  Pass: ≥ 4/5 on both. Record −94 dBm on the same seeds, as information only.

**3.4 Tile corners with real bias (G5).** `tb_tile.py rc` at fs 50 °C, ss 10 °C and ff 50 °C (`tb_tile_tx.py`
already takes corner and temperature; extend `tb_tile.py` the same way). Measure RX current, det idle, det at −60 dBm and
TX. Also make `rx_corners.sh` take the real `bias_gen` (an option; the ideal-source mode stays for comparison).

  Pass: det idle and slope within the RX corner ranges; comparator CM ≤ 1.45 V at sf (history.md's no-threshold
region).

**3.5 Overload (G8).** On the joined schematic deck:
- One full 13 ms burst at −10 dBm, then a −90 dBm burst after 0.5 / 1 / 2 / 5 ms. If the joined deck is
  too slow, use the mixed-signal deck with det from the schematic chain's CW response (3.1) plus model noise.
- 0 dBm and +6 dBm at the pads (bench case: a second board at 10 cm). Check for latch-up, the chain's
  recovery, and current through the input devices.

  Pass: −90 dBm detected after ≤ 2 ms (document the actual dead time), and no stuck state.

**3.6 Power-up (G9).** Tile c-mode transient: VDPWR / VAPWR ramps of 10 µs and 10 ms, then `ena` / `rst_n`
released, through to the averager and trim settled. Run at tt, ss 10 °C and ff 50 °C. Also measure the all-off current with VAPWR up and
VDPWR down, and the other way round.

  Pass: the bias starts at every ramp and corner, no floating nodes in the off state (layout.md checklist), the servo settles within ~2 ms
of reset, and no TX output before `tx_en`.

**Deliverable:** `docs/verify_system_2.md`, plus a row in verification.md for each new check with its run command.

> **Gate 3 (Matt):** sensitivity with the extracted chain stated as one number (with the 3.1 offset), and the
> overload dead time accepted for the protocol.

---

## Phase 4: housekeeping, with the next tile rebuild

**4.1 Decap hvi.5 (G11).** `lay.py` `write(flatten=True)` for `decap_vapwr_p1`–`p4`, as for the TX blocks in
13c28aa. Then `layout/check.sh` on each part, and drop the caveat from verification.md. Do this in the same tile
rebuild as the ring change, followed by `check_top.sh`, `export_tt.sh` and the GitHub precheck.

**4.2 Full rerun.** After the ring lands (or if it doesn't), rerun verification.md end to end, including
every check added here, and write `docs/verify_<date>.md` as before.

> **Gate 4 (Matt):** tapeout sign-off on verification.
