# System level on the extracted chip, 2026-10-12 (sim-0)

Phase 3 of [plan_verify_gaps.md](plan_verify_gaps.md): gaps G3 (sensitivity through the extracted RF chain),
G5 (tile corners with real bias), G6 (seeds at the edge), G8 (overload) and G9 (power-up). `main` after 0439b48
(phase 2), ring `NINV` 22, sim-0, IIC-OSIC-TOOLS 2026.09 (ngspice 47), extraction with magic 8.3.642. Per the
plan, failing checks are recorded here and left for a design change; nothing in the design was changed.

## Summary

| Check | Result |
|---|---|
| 3.1 CW det drop on the extracted tile (c and rc) vs model | ✅ −0.3 dB at −100 dBm, +0.5 dB at −90 dBm (0.72 / 7.00 mV against 0.77 / 6.27); the tile's schematic gives 0.53 / 5.20 mV |
| 3.1 the same on the block extractions (`lna_chain` + `log_det`, `layout/pex.sh`) | ⚠️ 2.4 dB *below* the schematic (0.31 / 3.13 mV). The two extraction flows disagree on the chain's gain at 434 MHz by 3.6 dB (tile +1.4 dB, blocks −2.2 dB at o5, against the schematic): same devices and resistor lengths, but the block flow puts 4–20 fF more on each stage node (log_det's taps 9.6 fF against 1.4 fF in the schematic). Not resolved; open for Gate 3 |
| 3.1 e2e | ✅ on the tile numbers: −92 dBm 12/12 at all 9 supply points (phase 2, schematic slopes, which the tile meets). On the block numbers as a pessimistic bound (slope × 0.75 in the log region): −92 dBm 12/12 at tt and at fs 50 °C 1.71 V with a nominal comparator; with mismatch, 10/12 and 6/12 at fs 50 °C 1.71 V for steps 0.096 / 0.13 mV/LSB (35–39 % / 26 % of chips); −90 dBm 12/12 everywhere |
| G3 pair, extracted tile (c), −92 dBm, shared noise | ✅ det off − on **1.36 mV** over 2–30 µs (windows 1.13–1.56), model 1.14 mV |
| 3.2 closed loop through the extracted chain | ⏹ not run: the joined RX with extracted `lna_chain` + `log_det` and RF noise runs at ~10 000 s per simulated µs (schematic 38 s/µs); one 13 ms burst would take years (schematic ~6 days). Stopped at 3.1 as the plan says |
| 3.3 seeds at −92 dBm | ✅ schematic 5/5 (events 14.664–14.671 ms), extracted baseband (`--pex`) 5/5 (14.668–14.674 ms). −94 dBm (information): schematic 3/5, extracted 4/5 |
| 3.4 RX corners with the real `bias_gen` (`BIAS=real`) | ⚠️ det idle within the ideal-bias range; slope too, except **ff 85 °C: 5.9 mV/dB (ideal 6.8)**; real bias costs 0.6–0.9 dB of gain at 85 °C. Comparator CM at sf: unchanged (no threshold at 1.55 V, det idle ≤ 1.515 V) |
| 3.4 e2e at 85 °C (outside the 10–50 °C range verified so far) | ⚠️ −92 dBm: ff 4/12 (real bias; 10/12 ideal), fs 10/12; −90 dBm 12/12 |
| 3.4 tile rc at fs 50 / ss 10 / ff 50 (real bias) | ✅ det idle 1.500 / 1.502 / 1.475 V and the drop at −60 dBm 264 / 324 / 214 mV, both where the block corners put them (tile offset −30 mV, drop ∝ slope); RX 2.93–3.02 mA; TX 459 / 370 / 509 MHz on silicon (×0.866, the tile factor), +2.3 to +3.5 dBm |
| 3.5 overload, −10 dBm burst then −90 dBm | ✅ −90 dBm detected after gaps of 0.1 / 0.25 / 0.5 / 1 / 2 / 5 ms: detection dead time < 0.1 ms. The trim servo is pulled to code ~30 (touching 0) for ~2.8 ms after the strong burst; the correlation rides through it |
| 3.5 0 / +6 dBm at the pads (schematic tile) | ✅ pads clamp at ±0.59 V (1.16 V differential), antenna current 11.7 mA peak; VDPWR current and vcm back to their exact pre-burst values; det back within 2 mV 0.3 µs after the tone, LPF back in its normal band ~55 µs after |
| 3.6 power-up, 10 µs and 10 ms ramps (schematic tt; extracted c at tt 27 / ss 10 / ff 50) | ✅ vcm at 95 % 8 µs into the ramp; det settled 6 µs after rx_en, LPF within 2 mV in 1.5–1.6 ms, avg in 2.65–2.73 ms; no RF from the TX (one common-mode step of ≤ 0.29 V on tx_p/tx_n while VDPWR < 0.7 V, ≤ 76 mV differential, gone 3.8 µs into the ramp); currents end at their normal values. 10 ms ramp (c, same corners): ✅ the same picture: vcm at 95 % at 6.26 ms (VDPWR 1.13 V), LPF 0.64–0.69 ms and avg 2.06–2.12 ms after rx_en, tx_p ≤ 0.28 V common mode (≤ 4 mV differential) while VDPWR < 0.35 V; ramp currents ≤ 26 / 42 µA |
| 3.6 one supply missing (c, tt / ss / ff) | ⚠️ VDPWR 1.8 / VAPWR 0: 0.91–1.02 µA. VDPWR 0 / VAPWR 3.3: ≤ 16 nA, but **tx_p = tx_n = 3.3 V** (not the off state with both supplies up, where they sit at 0): no DC path and no RF |

**For Gate 3.** Sensitivity: **−92 dBm at 10–50 °C** (tile extraction, noisy pair and seeds agree), **−90 dBm**
at 85 °C (for every Monte Carlo chip in the first run; the 2026-10-13 comparator rerun puts 8–10 % of chips at about −88 dBm, finding 1). Overload: detection dead time < 0.1 ms after a −10 dBm burst, servo
disturbed ~2.8 ms; +6 dBm at the pads recovers fully. Power-up: ready ~3 ms after `rx_en` (~2 ms with a slow supply ramp). Open findings: [Findings](#findings-phases-2-and-3) below, none fixed (per the plan).

## Findings (phases 2 and 3)

All findings and failures from [verify_supply_mc.md](verify_supply_mc.md) (phase 2) and this doc (phase 3),
with what each one does to the design's performance. None was fixed (Matt, Gate 2 / 3); phase 4's full rerun
happens only if one of these leads to a design change.

| # | Finding | Detail | What this means |
|:-:|---|---|---|
| 1 | ❌ Comparator mismatch vs trim step | Offset σ ≈ 3 mV; the nominal chip switches at the knee of the trim transfer (code 112), so offsets of one sign land where the step is steep. Rerun 2026-10-13 (200 distinct samples, each chip's own step, tt / ss / fs 27 °C; [verify_supply_mc.md](verify_supply_mc.md) "Rerun"): 66–74 % of chips at −92 dBm, 17–24 % at about −90 dBm, 8–10 % at about −88 dBm, 1 in 200 (ss) can't trim. | A quarter to a third of chips lose 2–4 dB of sensitivity (20–40 % less range); about 1 in 10 is in the 4 dB group. The corner barely matters. The biggest effect on yield. (The phase 2 figures, 26 % / 48 % / 2 %, came from duplicated samples.) |
| 2 | ❌ TX enable level shifter `tx_ls_en` | Fails at VDPWR 1.71 V / VAPWR 3.6 V at ss and fs (extracted): one output arm never turns on. At 1.71 / 3.3 V the TX loses 1.5 dB. | Some chips won't transmit, or transmit weakly, with VDPWR low and VAPWR high. At nominal supplies the TX is fine. Whether it matters depends on TT's real supply tolerances, which weren't looked up. |
| 3 | ⚠️ TX frequency at the band edge | ss at 1.71 V gives 332 MHz on silicon, at the RX band's 330 MHz bottom edge; likely below it hot. | A slow chip on a low supply may transmit at or just outside what another chip's receiver accepts: chip-to-chip range drops or the link fails at that corner. (The TX is untrimmed, so it's never exactly on 433.92 MHz anyway.) |
| 4 | ⚠️ Slow TX turn-off | 18 ns at ss 10 °C, 1.71 / 3.0 V. | No practical effect: a chip lasts ~100 µs, so 18 ns is ~0.02 % of it. |
| 5 | ⚠️ Block vs tile extraction disagree | The two flows differ by 3.6 dB of chain gain at 434 MHz; the block flow adds 4–20 fF per stage node. Unresolved. | ~2 dB of uncertainty on sensitivity. If the tile flow is right (the noisy simulation agrees with it), −92 dBm holds. If the block flow is right, typical chips still reach −92 dBm, but chips with mismatch (#1) drop to −90 dBm. |
| 6 | ⚠️ Sensitivity at 85 °C | ff with the real bias: detector slope drops to 5.9 mV/dB, only 4/12 model runs detect −92 dBm. | Hot fast chips lose ~2 dB: −90 dBm at 85 °C. Irrelevant at room / bench temperature. |
| 7 | ⚠️ TX outputs high with VDPWR missing | VDPWR 0 / VAPWR 3.3 V: tx_p = tx_n = 3.3 V, ≤ 16 nA. | Harmless with the antenna: both sides at the same voltage, so no current and no transmission. It only matters if a board powers VAPWR alone and something on the TX pins expects them low. On TT both supplies come up together. |
| 8 | ⏹ Closed loop through the extracted RF chain not run | ~10 000 s per simulated µs. | No simulation detects a burst end to end with the extracted RF chain. The extracted signal level and extracted baseband detection were each checked on their own, so this is a coverage gap, not a known problem. |
| 9 | ℹ️ Not covered | Latch-up / substrate injection at +6 dBm not modelled. Supply ranges (±5 % / ±10 %) assumed, not TT's figures. | Unknowns, not known failures. Latch-up with a strong nearby transmitter is a bench check. If TT's real supply range is tighter, #2 and #3 may never occur in practice. |
| 10 | ✅ accepted: raw mode keys the TX in the RX role (formal, 2026-10-13) | With the magic strap, mode `01` and the RX role, `tx_en` follows `uio_in[2]` while `rx_en` = 1 ([verification.md](verification.md) "Formal"). | The chip can transmit while its own receiver is on. That only happens if someone straps raw mode on an RX board and drives `uio[2]`; in the default code mode it can't (proven). **Intended (Matt, 2026-10-13):** a loopback test, now described in docs/info.md; no change. |
| 11 | ℹ️ Shorter switched-cap dead time after a 1-clock reset (formal) | If `sc_phi2` is high when a 1-clock reset arrives, `sc_phi1` rises 2 clocks later instead of ≥ 4. | No effect: the phases still never overlap (proven), and 2 clocks (200 ns) is far longer than the switches need. |
| 12 | ⚠️ Comparator at sf 10 °C, VDPWR 1.71 V | Found 2026-10-13 during the trim redesign ([verify_supply_mc.md](verify_supply_mc.md) "Trim redesign candidates"). At CM 1.38 V, 16 % of chips at −92 dBm (offset +8 ± 4.6 mV); at CM 1.43 V most chips have no threshold. The sf no-threshold region (CM 1.55 V at 1.8 V) moves down with VDD. The trim redesign doesn't fix it (G129: 2 % at 1.38 V, none at 1.43 V). | A slow-n / fast-p chip, cold, on a low supply loses 2–4 dB or doesn't detect at all. Input-pair headroom, not trim. Depends on TT's real VDPWR range (#9). **Supply settled (Matt, 2026-10-13): good 1.8 / 3.3 V, measured 1.80–1.81 / 3.30 V on 3 boards, so 1.71 V does not occur.** |

## 3.1 Extracted chain sensitivity, noise-free (G3)

`python3 sim/chain/cw_drop.py` (new): `xschem/tb_logdet.sch` (pad models, 6-stage `lna_chain`, `log_det`, ideal
bias, CM interference off), a 433.92 MHz tone with no noise, det averaged over 0.8–1 µs, minus the no-signal
run. Schematic and extracted (`layout/pex/lna_chain.spice` + `log_det.spice`), tt 27 °C:

| level | schematic mV | extracted mV | model mV | extracted − schematic | extracted − model |
|---|---|---|---|---|---|
| −100 dBm | 0.55 | 0.31 | 0.77 | −2.49 dB | −3.95 dB |
| −90 dBm | 5.41 | 3.13 | 6.27 | −2.38 dB | −3.02 dB |
| −80 dBm | 43.43 | 27.69 | 47.30 | −1.95 dB | −2.33 dB |
| −70 dBm | 176.93 | 133.63 | 175.00 | −1.22 dB | −1.17 dB |

det idle: schematic 1.5197 V, extracted 1.4888 V (the known contact-resistance shift). The schematic column
repeats verify_2026-10-11 (0.55 / 5.42 / 43.5 / 177.0 mV), so the bench is the same. The detector is square law
here, so a det-drop ratio in dB (10 log) equals the loss of RF voltage gain in dB.

**Where it goes** (`--blocks=… --levels=-90 --pex-only`, and an AC run at 434 MHz on the same deck):

| extracted | det drop at −90 dBm vs schematic | chain gain to out (o5) at 434 MHz |
|---|---|---|
| nothing | 0 | 77.63 dB (63.79) |
| `lna_chain` only | −0.25 dB | |
| `log_det` only | −1.98 dB | 75.92 dB (62.28) |
| both | −2.38 dB | 75.58 dB (61.41) |

The block benches don't show it: `tb_log_det.py` drives tap 6 from an ideal source (−0.3 dB at 100 mV), and
`tb_det_cell.py` shows the cell itself at −0.5 dB, with its input capacitance 1.4 → 4.7 fF extracted. In the
chain, the six det cells' extracted input capacitance and the log_det tap wiring load the stage outputs (out, o5,
o4: all lose 1.1–1.7 dB). verification.md's "log_det: same slope" was the slope at high level, which is set
by the log law and doesn't see this.

**On the extracted tile** (`OSIC=tools/osic NT=1 python3 sim/top/tb_tile.py --cw sch c rc`, new: the tile deck
with the tone at the pads, real bias, trim held, one deck per level and view in parallel):

| level | tile schematic | tile c | tile rc | model |
|---|---|---|---|---|
| idle | 1.5214 V | 1.4914 V | 1.4911 V | |
| −100 dBm | 0.53 mV | 0.71 | 0.72 | 0.77 |
| −90 dBm | 5.20 mV | 6.96 | 7.00 | 6.27 |
| −80 dBm | 41.94 mV | 52.79 | 53.05 | 47.30 |
| −70 dBm | 173.14 mV | 172.84 | 173.36 | 175.00 |

The tile's extraction is −0.3 dB (−100 dBm) and +0.5 dB (−90 dBm) from the model: **3.1 passes on the tile**, and
c and rc agree. AC at 434 MHz on the same decks: antenna → o5 differential 63.64 dB (schematic) against
65.04 dB (c), antenna → o1p 5.42 / 4.84 dB.

**Block extractions against the tile.** The blocks extracted on their own disagree. Re-extracting `lna_chain`,
`log_det` and `det_cell` from the current layout (magic 8.3.642; the committed ones were from 2026-10-09, before
13c28aa changed det_cell) gives the same −2.4 dB, so it isn't staleness. Same magic settings in both scripts
(flatten, `extract do local`, `cthresh 0`, extresist for R), same devices, same resistor lengths and MIM sizes.
What differs is the parasitic C: summed over each node, tile c against block chain + log_det tap,
o5p 26.5 against 30.5 fF, o5n 32.1 against 43.8 fF, o1p 51.9 against 72.0 fF. log_det's taps alone load each stage
with 9.6 fF in the block extraction (1.4 fF in the schematic; 4.8 µS in both), about −0.35 dB per stage with the
~4 kΩ loads. Which flow is closer to silicon isn't settled here. The tile is extracted in its real surroundings
(the taped-out context), and the G3 pair below, on the tile with noise, agrees with it, so the tile is the
number to quote. The block result is kept as a pessimistic bound in e2e.

**Which slope matters.** The receiver's own noise (NF 11 dB over 450 MHz, about −76.5 dBm) holds det ~80 mV
below idle (1.439 V with noise only, schematic). That's the log part of the curve, and a weak signal moves det by
the local slope there, not by the square-law drop at −90 dBm. The CW curve around it
(`cw_drop.py --levels=-84,-82,-80,-78,-76,-74,-72`):

| level | −84 | −82 | −80 | −78 | −76 | −74 | −72 dBm |
|---|---|---|---|---|---|---|---|
| schematic, drop mV | 19.97 | 29.82 | 43.43 | 61.57 | 84.89 | 113.39 | 145.44 |
| extracted, drop mV | 12.03 | 18.44 | 27.69 | 40.55 | 57.66 | 79.42 | 105.45 |
| extracted − schematic | −2.20 | −2.09 | −1.95 | −1.81 | −1.68 | −1.55 | −1.40 dB |

Local slope at −76 dBm (−78 to −74): schematic 13.0 mV/dB (phase 2 used 13.4), extracted 9.7 mV/dB, a factor
of **0.75**. The G3 pair below (extracted tile, with noise) measured 1.36 mV against the model's 1.14, which
doesn't show even that loss, so 0.75 is the conservative of the two.

**Into e2e, pessimistic bound from the block extraction** (`model/e2e.py`, noise case, 12 trials, 0.3 mV comparator
noise, slope × 0.75). On the tile extraction the slopes are the schematic's or higher, so phase 2's e2e table
(12/12 at −92 dBm at all 9 supply points) applies as it is.

| case | NF | slope mV/dB | offset mV | step mV/LSB | −94 | −92 | −90 dBm |
|---|---|---|---|---|---|---|---|
| tt 27, schematic | 11 | 13.4 | 1.26 | 0.067 | 12/12 | 12/12 | 12/12 |
| tt 27, extracted | 11 | 10.05 | 1.26 | 0.067 | 8/12 | **12/12** | 12/12 |
| tt 27, extracted, step 0.096 | 11 | 10.05 | 1.26 | 0.096 | 4/12 | 12/12 | 12/12 |
| tt 27, extracted, step 0.13 | 11 | 10.05 | 1.26 | 0.13 | 1/12 | 12/12 | 12/12 |
| fs 50 1.71 V, schematic | 12 | 11.8 | 1.67 | 0.069 | 5/12 | 12/12 | 12/12 |
| fs 50 1.71 V, extracted | 12 | 8.85 | 1.67 | 0.069 | 0/12 | **12/12** | 12/12 |
| fs 50 1.71 V, extracted, step 0.096 | 12 | 8.85 | 1.67 | 0.096 | 0/12 | 10/12 | 12/12 |
| fs 50 1.71 V, extracted, step 0.13 | 12 | 8.85 | 1.67 | 0.13 | 0/12 | 6/12 | 12/12 |

With a nominal comparator the plan's pass holds (−92 dBm ≥ 11/12). With mismatch it doesn't at the worst supply
corner: step 0.096 mV/LSB is where the switch code is ~100 (−1 mV of offset to cancel,
[verify_supply_mc.md](verify_supply_mc.md)), and 35 % (tt), 39 % (fs 50 °C), 55 % (sf 10 °C) of the Monte Carlo
chips land below code 100. −90 dBm is 12/12 in every case. (First pass, scaling the slope by the square-law
0.57: −92 dBm still 12/12 with a nominal comparator, 5/12 and 2/12 at steps 0.096 / 0.13; that overstates the
loss.)

**Sensitivity, one number (for Gate 3): −92 dBm** at 10–50 °C and every supply corner: on the tile extraction for
every chip in the Monte Carlo except those that already miss in phase 2 (trim step > 0.19 mV/LSB, 26–34 % at tt / ss / fs
in the 2026-10-13 rerun), and on the pessimistic block extraction for a typical chip. **−90 dBm** covers 85 °C (3.4) and
all but the 8–10 % of chips with a trim step > 0.43 mV/LSB, which reach about −88 dBm (finding 1).

### G3 pair on the extracted tile, shared noise

The rerun that verify_2026-10-11 asked for: rebuilt tile (`top.py`, `route.py` 111/111), `pex_tile.sh c`, trim
scan (comp flips between codes 116 and 117), then `python3 sim/top/tb_tile_joined.py pair -92 30u 117 1`: two
30 µs runs on the extracted tile, keyed on at 1 µs, with and without the signal, both reading one RF noise file
(`build/tile_pair_noise_1.txt`). 4 h 40 min on sim-0 at 2 × 8 threads.

| window | det off − on | LPF off − on |
|---|---|---|
| 1–5 µs | +1.56 mV | +0.15 mV |
| 5–10 µs | +1.44 mV | +0.60 mV |
| 10–20 µs | +1.13 mV | +0.94 mV |
| 20–30 µs | +1.48 mV | +1.14 mV |
| **2–30 µs** | **+1.36 mV** | +0.87 mV |

The model expects ~1.14 mV at −92 dBm. With the noise shared, the windows agree within ±0.2 mV (the
2026-10-11 run, with independent noise, scattered from 0.02 to 2.37 mV). So on the extracted tile, with
noise, the signal reaches det at the model's size or slightly above, although the noise-free CW drop above is
2.4 dB lower. The two are consistent: with the receiver's noise (about −76.5 dBm over 450 MHz) det sits ~80 mV
below idle, in the log part of the curve, where a few dB less RF gain moves the operating point but changes
the slope much less than the square-law drop at −90 dBm suggests.

## 3.2 Closed loop through the extracted chain (G3)

`PEX=1 LEVELS=-90 TSTOP=2u NT=2 ../sim/rx/joined.sh` (new `PEX` / `NT` options): the joined RX (antenna with RF
noise, pad models, `lna_chain`, `log_det`, `lpf_rc`, `avg_sc`, `comp_ct`) with the chain and detector from
their extractions. The schematic deck ran 2 µs in 76 s (38 s per µs at 2 threads); the extracted one reached
0.24 µs in 40 min (~10 000 s per µs) and was stopped. The correlator needs the whole 127-chip burst (13.2 ms)
plus the averager's settling, so even the schematic deck would take ~6 days and the extracted one years. The
shortest stimulus that can open an event is still the full burst (the RTL correlates all 127 chips), so a
shorter holdoff doesn't help. Per the plan: over ~2 days, report and stop at 3.1. The G3 pair below and the
tile CW cover the signal level on the extracted chip; detection on the extracted *baseband* blocks is the
mixed-signal `--pex` runs (3.3).

## 3.3 Seeds at the edge (G6)

`gen_det.py --seed=N` and `gen_mixed.py --seed=N` (new; seeded plots go to `build/mixed/`), seeds 1–5, the
same noise at −92 and −94 dBm for each seed:

| | s1 | s2 | s3 | s4 | s5 |
|---|---|---|---|---|---|
| −92 dBm, schematic | ✅ 14.671 ms | ✅ 14.664 | ✅ 14.666 | ✅ 14.664 | ✅ 14.667 |
| −92 dBm, extracted baseband | ✅ 14.674 | ✅ 14.668 | ✅ 14.673 | ✅ 14.669 | ✅ 14.674 |
| −94 dBm, schematic | ✅ 14.686 | ✗ | ✅ 14.659 | ✅ 14.660 | ✗ |
| −94 dBm, extracted baseband | ✅ 14.667 | ✅ 14.692 | ✅ 14.660 | ✗ | ✅ 14.666 |

Pass (≥ 4/5 at −92 dBm on both views) holds: 5/5 and 5/5. −94 dBm is the edge, as verify_2026-10-11 found
(3/5 here on the schematic, 4/5 extracted). Every run's ladder check passed (2–3 extra ±1 steps). The extracted runs
(`--pex`: `lpf_rc`, `avg_sc`, `comp_ct`, `r2r` from their extractions; det still from the model) take ~4 h each
at one thread (the schematic ones ~3 min).

    python3 sim/rx/gen_det.py --seed=1 -92 && python3 sim/mixed/gen_mixed.py --seed=1 [--pex] -92 <tstop>
    python3 sim/mixed/plot_mixed.py -92[_pex]_s1

## 3.4 Corners with real bias (G5)

`BIAS=real` on `sim/corners/rx_corners.sh` (new) replaces the ideal sources (iref 60 µA, vcm 1.2 V, 2 µA
detector, 1 µA comparator) with `bias_gen` (enabled; its unused outputs into 100 kΩ). Same benches, 5 corners
× −20 / 27 / 85 °C; the ideal-bias run alongside for comparison (`OUT=corners_ideal`):

| corner | T °C | gain 434 MHz dB ideal / real | det idle V ideal / real | slope mV/dB ideal / real |
|---|---|---|---|---|
| tt | −20 / 27 / 85 | 79.7 / 76.7 / 74.7 — 79.8 / 76.5 / 74.1 | 1.525 / 1.520 / 1.511 — 1.523 / 1.521 / 1.518 | 14.6 / 13.4 / 11.3 — 14.6 / 13.1 / 10.5 |
| ss | −20 / 27 / 85 | 82.2 / 80.8 / 79.6 — 82.5 / 80.8 / 79.2 | 1.537 / 1.533 / 1.525 — 1.533 / 1.531 / 1.530 | 13.8 / 13.8 / 13.5 — 14.0 / 13.9 / 13.3 |
| ff | −20 / 27 / 85 | 81.1 / 75.6 / 70.5 — 80.9 / 75.2 / 69.6 | 1.510 / 1.503 / 1.492 — 1.511 / 1.508 / 1.503 | 14.7 / 12.6 / 6.8 — 14.6 / 12.1 / **5.9** |
| sf | −20 / 27 / 85 | 79.7 / 76.7 / 74.7 — 79.7 / 76.5 / 74.0 | 1.516 / 1.510 / 1.501 — 1.515 / 1.512 / 1.509 | 14.6 / 13.3 / 11.2 — 14.6 / 13.1 / 10.5 |
| fs | −20 / 27 / 85 | 79.6 / 76.6 / 74.7 — 79.7 / 76.5 / 74.0 | 1.534 / 1.528 / 1.519 — 1.532 / 1.530 / 1.528 | 14.5 / 13.3 / 11.2 — 14.5 / 13.1 / 10.4 |

Comparator offsets and trim ends are within 0.4 mV of the ideal-bias run, except sf 85 °C at CM 1.55 V (+10.1 against +11.4 mV); the comparator still has no
threshold at CM 1.55 V at sf −20 / 27 °C (as before), and det idle at sf is ≤ 1.515 V noise-free (~1.44 V with
the receiver's noise), so the comparator CM stays below 1.45 V there.

e2e (noise case, 12 trials, 0.3 mV comparator noise, step 0.067 mV/LSB) at 85 °C:

| case | NF | slope | offset | −94 | −92 | −90 dBm |
|---|---|---|---|---|---|---|
| ff 85, ideal bias | 12.6 | 6.8 | 1.6 | 0/12 | 10/12 | 12/12 |
| ff 85, real bias | 12.6 | 5.9 | 1.6 | 0/12 | **4/12** | 12/12 |
| ff 85, real bias, extracted (× 0.75) | 12.6 | 4.4 | 1.6 | 0/12 | 0/12 | 12/12 |
| fs 85, real bias | 13.0 | 10.4 | 1.7 | 0/12 | 10/12 | 12/12 |

So at 85 °C the sensitivity is −90 dBm. The verification so far, and its −92 dBm figure, covers 10–50 °C.

**The extracted tile at three corners** (`OSIC=tools/osic NT=2 python3 sim/top/tb_tile.py --corner=… --temp=… rc`,
new options; real `bias_gen`, full RC):

| | tt 27 (2026-10-11) | fs 50 | ss 10 | ff 50 |
|---|---|---|---|---|
| RX current | 2.985 mA | 3.018 | 2.930 | 2.945 |
| all off | 0.910 µA | 0.907 | 0.945 | 1.015 |
| det idle | 1.491 V | 1.500 | 1.502 | 1.475 |
| det at −60 dBm (drop) | 1.206 V (285 mV) | 1.236 (264) | 1.178 (324) | 1.261 (214) |
| TX f (on silicon, ×0.866 for the tile) | 519 MHz (449) | 530 (459) | 427 (370) | 588 (509) |
| TX P73, on / off | +3.13 dBm | +2.91, 12.0 / 9.8 ns | +3.45, 20.8 / 19.6 ns | +2.29, 3.5 / 4.7 ns |

det idle sits 30 mV below the block corners at each corner (the tile's known contact-resistance shift: tt
1.521 → 1.491 V), and the −60 dBm drop scales with the corner's log slope (relative to tt: ff 50 0.75 against
0.73 from the slopes above, fs 50 0.93 / 0.92, ss 10 1.14 / 1.06). The TX stays in the RX band
(330–560 MHz) at all three. (×0.866 is the ttsky25b factor against a whole-tile extraction; ×0.845 is for the block
extraction, as in phase 2's `tb_tx` grid.)

## 3.5 Overload (G8)

**Strong burst, then a weak one.** The joined schematic deck runs at 38 s per µs (~11 days for the two bursts),
so this uses the plan's fallback: the mixed-signal deck (RTL servo and correlator, transistor-level `lpf_rc`,
`avg_sc`, `comp_ct`, `r2r`) with det from the schematic chain's CW transfer plus model noise.
`gen_det.py --overload=<gap ms> -90` (new) writes a −10 dBm burst (code 0x5A, 127 chips) after the 1.5 ms
lead-in, then the −90 dBm burst `gap` ms after it ends; `gen_mixed.py --tag=ov<gap> -90 <tstop>`.

| gap after the −10 dBm burst | 0.1 ms | 0.25 | 0.5 | 1 | 2 | 5 |
|---|---|---|---|---|---|---|
| −90 dBm burst ends at (ms) | 28.016 | 28.166 | 28.416 | 28.916 | 29.916 | 32.916 |
| event (ms) | 27.967 | 28.119 | 28.377 | 28.872 | 29.887 | 32.864 |

Both bursts are detected in every run; the second event comes at the usual point near the end of its burst.
**Detection dead time < 0.1 ms** at this resolution. The servo is disturbed for longer: it stays at codes
104–114 through the −10 dBm burst, then, with the averager pulled low by the burst, runs down to code ~30
(touching 0 for 6–8 ticks) and is back above code 90 by 17.5 ms in every run, ~2.8 ms after the strong burst.
With a short gap the first ~20 % of the weak burst's chips arrive while the threshold is off, and the 127-chip
correlation still opens the event at the usual point. The det model has no recovery
dynamics of its own, but the transistor-level det recovers in 0.3 µs (below), so that doesn't change the result.
`plot_mixed.py`'s ladder check now leaves out ticks with the code at 0 or 255 (the counter holds there); before,
the 2 ms run failed it by one step. A swapped trim bus still fails (588 steps of ±2).

**0 and +6 dBm at the pads** (`sim/top/tb_pad_overload.py --dbm=… sch`, new): the tile deck, RX on, a 434 MHz
tone keyed on from 1 to 6 µs.

| | 0 dBm | +6 dBm |
|---|---|---|
| pad_p / pad_n swing | −0.293..+0.296 V | −0.565..+0.590 V |
| differential max | 0.59 V | 1.16 V |
| antenna current peak | 5.8 mA | 11.7 mA |
| VDPWR current before / during / after | 2.974 / 3.159 / 2.975 mA | 2.974 / 3.171 / 2.975 mA |
| vcm before / after | 1.2012 / 1.2012 V | 1.2012 / 1.2012 V |
| det min, recovery | 0.500 V, 0.3 µs | 0.488 V, 0.3 µs |
| LPF min, back in its band (1.503–1.512 V) | 1.155 V | 1.150 V, ~55 µs (1.484 V at 34 µs, 1.508 V at 54 µs; 150 µs run) |

No stuck state: currents, bias, det and LPF all come back. The LPF normally wanders in a ~10 mV band, kicked by the averager's switching at each sc_phi edge (also at t = 0, which is why a 2 mV recovery test on it never passes); it is back in that band ~55 µs after the tone, as the −10 dBm joined run on 2026-10-11 found (~45 µs). The pads clamp at about ±0.59 V, i.e. the ESD diodes just
start to conduct at +6 dBm; substrate injection and latch-up from that aren't modelled in SPICE, so they stay a
bench item. The chain's input devices are behind the input coupling capacitors, so their gates see ±0.59 V around
their bias, inside the 1.8 V rating.

## 3.6 Power-up (G9)

`sim/top/tb_powerup.py` (new): the tile deck (`xschem/tb_radio_analog.sch`, real `bias_gen`), VDPWR and VAPWR
ramped together from 0 over 10 µs or 10 ms, no RF. The digital inputs come from the macro, which runs on VDPWR,
so each is scaled by v(VDPWR) / 1.8: trim at the reset code 128, `sc_phi1` / `sc_phi2` running, `tx_en` 0, and
`rx_en` released 20 µs after the ramp. Runs 3 ms past `rx_en`. The trim servo isn't in this deck (code held at
128); its start from code 128 is in every mixed-signal run (3.3): one LSB per ~13 µs tick, from 128 to its working
value (mean ~108 at −92 dBm) in ~0.3 ms, well before the burst at 1.5 ms.

    OSIC=tools/osic NT=4 python3 sim/top/tb_powerup.py --ramp=10u --corner=ss --temp=10 c
    OSIC=tools/osic python3 sim/top/tb_powerup.py --off --corner=tt c

10 µs ramp:

| | schematic tt 27 | c tt 27 | c ss 10 | c ff 50 |
|---|---|---|---|---|
| vcm, 95 % of final | 8 µs | 8 µs | 8 µs | 8 µs |
| det settled after rx_en | 6 µs | 6 µs | 6 µs | 6 µs |
| LPF within 2 mV of final, after rx_en | 1.57 ms | 1.50 ms | 1.50 ms | 1.49 ms |
| avg within 2 mV of final, after rx_en | 2.73 ms | 2.66 ms | 2.66 ms | 2.65 ms |
| max \|tx_p\| during the ramp (differential) | 44 mV | 48 mV (11) | 286 mV (76) | 16 mV (2) |
| peak current during the ramp, VDPWR / VAPWR | 15 / 27 µA | 12 / 45 µA | 12 / 82 µA | 13 / 22 µA |
| current at the end, VDPWR | 2.977 mA | 2.990 | 3.022 | 2.950 |

("det settled" is into its ~3.7 mV switched-cap ripple band; within 2 mV of the last sample never holds for that
reason.) The bias comes up with the supply ramp, and det, LPF and the averager settle on their own time constants
after `rx_en`: about 2.7 ms to the averager, so the receiver is ready ~3 ms after `rx_en`. The TX output step happens only while
VDPWR is between ~0.45 and 0.7 V, when the `tx_en` level shifter's input is undefined; it is a single step,
mostly common mode, with no oscillation, and it is gone 3.8 µs into the ramp. The comparator is low at the end in
every run.

10 ms ramp (c; 6.5 h each at one thread):

| | c tt 27 | c ss 10 | c ff 50 |
|---|---|---|---|
| vcm, 95 % of final (VDPWR then) | 6.26 ms (1.13 V) | 6.26 ms | 6.26 ms |
| det settled after rx_en | at once | at once | at once |
| LPF within 2 mV of final, after rx_en | 0.67 ms | 0.64 ms | 0.69 ms |
| avg within 2 mV of final, after rx_en | 2.08 ms | 2.06 ms | 2.12 ms |
| max \|tx_p\| (differential), VDPWR then | 37 mV (0.6), 0.26 V | 281 mV (4), 0.34 V | 7 mV (0.04) |
| peak current during the ramp, VDPWR / VAPWR | 15 / 8 µA | 8 / 1 µA | 26 / 42 µA |
| current at the end, VDPWR | 2.989 mA | 3.022 | 2.950 |

With the slow ramp the bias is long settled when `rx_en` rises, so the LPF and averager settle faster than with
the 10 µs ramp. The TX step is the same common-mode one, now spread over the first 1.5–1.9 ms (VDPWR < 0.35 V)
and with less than 5 mV differential. The only large current is the RX switching on at `rx_en` (3.3–3.5 mA peak
for a moment, against 2.95–3.02 mA steady). (`tb_powerup.py`'s "peak during ramp" covers up to 1.05 × the ramp,
which for the 10 ms ramp includes `rx_en` at 10.02 ms; the ramp-only figures are in the table.)

**One supply missing** (`--off`, operating point, `rx_en` = `tx_en` = 0):

| | c tt 27 | c ss 10 | c ff 50 |
|---|---|---|---|
| VDPWR 1.8 / VAPWR 0: IDPWR, tx_p = tx_n | 0.910 µA, 32 mV | 0.907 µA, 270 mV | 1.015 µA, 2 mV |
| VDPWR 0 / VAPWR 3.3: IAPWR, tx_p = tx_n | 1.8 nA, 3.3 V | 0.5 nA, 3.3 V | 16 nA, 3.3 V |

With VAPWR up and VDPWR missing, the TX output stage's gate drive (the level shifter's 3.3 V side) has no defined input,
and both outputs go to VAPWR. Both are high together, so no current flows through the antenna and there is no RF,
but it isn't the defined off state. On TT both supplies come up together, so this matters only if a board
powers VAPWR alone. Recorded as a finding.
