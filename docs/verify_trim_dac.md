# Trim DAC linearity with the real bit drivers (2026-11-12, branch `trim-dac`)

From [handoff_trim_dac.md](handoff_trim_dac.md). The tt08 scope capture of the reused R2R DAC steps *down* at the
127 → 128 carry. Question: is that here too, and does it cost sensitivity?

**Answer: yes, it's here, and it costs a little at the edge. Decision (Matt, 2026-11-12): accept it for this
tapeout. Don't touch the macro for it, but if `radio_digital` is re-hardened for any other reason, drive
`trim_out[7:0]` with `sky130_fd_sc_hd__buf_8` (see "If the macro is re-hardened").**

## Summary

| | today (`clkdlybuf4s25_1`) | with `buf_8` (re-harden) | ideal drivers |
|---|---|---|---|
| driver R_hi / R_lo, tt 27 °C (40 µA) | 4.7 k / 2.5 k (all corners 4.1–5.6 k / 2.0–3.7 k) | 0.53 k / 0.18 k | 0 |
| DNL 127 → 128 (LSB) | −11 … −18 (overlap 10–14 codes) | −1.3 (overlap 1) | 0 |
| DNL 191 → 192 | −5 … −9 | −0.55 | 0 |
| **median code step, codes 140–255 (× ideal LSB)** | **1.25 … 1.43** (tt 1.29, fs 50 °C 1.28, ss_ll 1.43) | 1.03 | 1.00 |
| V(255) | 1.786–1.789 V | 1.7925 V | 1.7930 V |
| chips with a gap (DNL > +0.5) in 120–255, MC 200 | 0 % tt / fs 50 °C; 100 % ss_ll (the 1.6-LSB bit-0 step, not mismatch) | – | 7.5 % (tt, mismatch alone) |
| mixed signal −92 dBm, pooled over 3 balance points | **96/104** | – | **103/104** |
| e2e −92 dBm, fs 50 °C (worst corner), median / p95 chip | 79–84 / 74–83 of 96 | – | 90 / 87 of 96 |
| e2e tt 27 °C, −92 / −94 dBm | 96 / 25–33 of 96 | – | 96 / 49 of 96 |

The handoff expected the overlaps to be harmless, and they are: the servo only cares about voltage, settling
(0.64 → 0.71 ms) and code wander (σ ≈ 1.5 codes) are unchanged, and a chip balanced inside an overlap detects as
well as anywhere else. **What it didn't expect:** the ladder's end points barely move (V(0) = 0, V(255) −5 mV), so
when every carry steps down, the steps between carries must get bigger. In the band where chips balance, each code
moves the trim voltage ~1.3× the ideal LSB, so **every chip's comparator trim step is ~1.3× coarser** than the
H135 analysis assumed ([verify_supply_mc.md](verify_supply_mc.md) §2.2 measured it against an ideal 1.8 V / 256
LSB). H135's p95 step at fs 50 °C, 0.135 mV, becomes ~0.17 mV, past the e2e edge (~0.14 mV).

What this means: a typical chip still detects −92 dBm every time (tt e2e 96/96); the worst corner (fs 50 °C) drops
from ~92 % to ~85 % of sends at −92 dBm; −94 dBm, already a best case, gets about half as likely. Roughly 0.5 dB at
threshold (estimate, not fitted).

## 1. The driver (`sim/dac/tb_drv.py`)

`trim_out[7:0]` leave the macro through `sky130_fd_sc_hd__clkdlybuf4s25_1` (`radio_digital.nl.v:11335`), a
weak delay buffer: output pfet W 1.0 hvt, nfet W 0.42. DC bench, one cell sourcing and one sinking 0–100 µA
(a 2R leg draws at most ~86 µA). Chord resistance at 40 µA (Ω):

| corner | 10 °C | 27 °C | 50 °C | 85 °C |
|---|---|---|---|---|
| tt | 4716 / 2354 | 4690 / 2470 | 4659 / 2627 | 4620 / 2865 |
| ss | 5510 / 2954 | 5502 / 3118 | 5489 / 3342 | 5468 / 3686 |
| ff | 4224 / 1971 | 4183 / 2061 | 4138 / 2181 | 4092 / 2363 |
| sf | 5563 / 2087 | 5473 / 2187 | 5368 / 2321 | 5238 / 2526 |
| fs | 4075 / 2709 | 4085 / 2846 | 4098 / 3032 | 4117 / 3313 |

Not ~1 kΩ as guessed: 2R is 21 kΩ, so the driver is 10–25 % of a leg. For reference (tt / ss 85 °C):
`buf_2` 2.2 k / 0.72 k, `buf_4` 1.07 k / 0.36 k (1.24 k / 0.49 k), `buf_8` 0.53 k / 0.18 k (0.61 k / 0.25 k);
`python3 sim/dac/tb_drv.py --cell=buf_8`.

Routed wire, macro pin → r2r `b_i`: ~45 µm of straight met1–met3 (macro W pins at tile x ≈ 282.7, r2r b pins at
x ≈ 238.6; `layout/gen/top_nets.py`), ≲ 50 Ω with vias. Estimated from the floorplan, not extracted; ~1 % of the
driver, ignored.

## 2. Block bench (`sim/dac/tb_r2r.py --drv`)

Each `b_i` through one driver cell on the ladder's 1.8 V / 0 V rails; full 256-code sweep (one `op` per code).
11 corners (tt ss ff sf fs, ll hh, ss_ll ss_hh sf_ll fs_ll) × 10 / 27 / 50 / 85 °C, schematic; extracted at the
five device corners, 10 and 50 °C. Table: `python3 sim/dac/r2r_summary.py`.

- Schematic and extracted agree within 0.03 LSB everywhere; without drivers the ladder is exact (sch) / ≤ 0.04
  LSB (pex), as before.
- tt 27 °C: 127 → 128 −12.7 LSB (overlap 11 codes), 63 → 64 −6.9, 191 → 192 −6.0, 159 → 160 −3.2, 223 → 224 −2.8;
  bit-0 steps +0.23 … +0.42. Matches `ladder_model.py` with step 1's R (−12.4) to 0.3 LSB, the rest being the
  drivers' nonlinearity.
- Worst: ss_ll (slow devices, low-R poly): −18 LSB, step factor 1.43. Best: ff / hh, −11 LSB, 1.25. Temperature
  moves it < 0.6 LSB.
- Rout 10.6 → 12.0 kΩ; 127 → 128 settles in 45 ns into 1 pF (was 25): irrelevant at a 13 µs tick.

## 3. Monte Carlo (`tb_r2r.py --drv --mc=200`, `r2r_mc.py`)

200 samples each, one process per sample with its own `.options seed`, no duplicates.

| | DNL 127 → 128 p5 / 50 / 95 | 191 → 192 | max DNL 120–254 (worst) | gap > +0.5 | step factor p5 / 50 / 95 |
|---|---|---|---|---|---|
| ideal drivers, tt | −0.59 / +0.04 / +0.55 | −0.28 / 0.00 / +0.28 | +0.83 | 7.5 % | 0.994 / 1.000 / 1.006 |
| drivers, tt 27 °C | −13.6 / −12.7 / −12.0 | −6.5 / −6.1 / −5.5 | +0.44 | 0 % | 1.283 / 1.294 / 1.303 |
| drivers, fs 50 °C | −13.7 / −12.6 / −11.5 | −6.9 / −6.2 / −5.6 | +0.40 | 0 % | 1.267 / 1.279 / 1.296 |
| drivers, ss_ll 27 °C | −19.4 / −18.0 / −16.8 | −9.6 / −8.7 / −7.9 | +0.64 | 100 % | 1.409 / 1.429 / 1.447 |

Unit-resistor mismatch is small (DNL σ ≈ 0.35 LSB at 127 → 128, i.e. ~0.3 % per unit). With ideal drivers, 7.5 %
of chips have a small mismatch gap; the drivers' negative bias at the carries removes those. The ss_ll "gaps" are the
systematic 1.6-LSB bit-0 step, the same effect as the step factor. The spread between chips is tiny: the step
factor is set by the corner, not by mismatch.

## 4. Mixed signal (`gen_mixed.py --drv --vos=<mV>`)

Each `trim_out` `dac_bridge` goes through a real `clkdlybuf4s25_1` before `xdac`; `--vos` is a DC source in series
with comp_ct's inp. Ideal DAC, tt: +1 mV ≈ +7.7 codes (vos −8 / −4 / 0 → codes 117 / 148 / 179). −92 dBm, schematic,
detection from `replay_corr.py` averaged over burst timing (it now reads the digital `trim_out` bits; with drivers
`v(trim)` is no longer code × LSB):

| balance point | vos | ideal drivers (code) | drivers (code) |
|---|---|---|---|
| nominal | 0 | 20/20 + 20/20 = 100 % (178) | 18 + 18 / 40 = 90 % (183) |
| inside the 127/128 overlap | −7.1 mV | 20 + 19 / 40 = 98 % (122) | 19 + 17 / 40 = 90 % (131) |
| inside the 191/192 overlap | +1.4 mV | 12 + 12 / 24 = 100 % (188) | 12 + 12 / 24 = 100 % (197) |
| pooled | | **103/104** | **96/104** |

−94 dBm, nominal, seeds 1–8: ideal 6/16, drivers 5/16 (both at the edge). Servo settle 0.64 vs 0.71 ms, code
σ 1.6 vs 1.4 codes. Replay agrees with the simulated event pin in every run. The `--pex` runs at 127/128
(~5 h each) were stopped once the decision was taken; not run.

## 5. e2e with the measured curve (`model/e2e.py --dac-curve`)

`--dac-curve <r2r_curve_*.json>` replaces `AfeModel`'s uniform trim with the measured code → voltage curve;
`--dac-code0` sets which real code the model's 128 sits at (the chip balances ~10 codes below it). With the ideal
curve it reproduces the uniform run exactly. Noise case, 96 trials, 0.3 mV comparator noise, same records per
row:

- **fs 50 °C** (`--nf 12 --brf 450e6 --slope 12.4 --offset-mv 1.3`), −92 dBm, code0 140–210: step 0.130 (H135
  median there) ideal 90/96, drivers 79–84; step 0.135 (p95) ideal 87/96, drivers 74–83. At code0 230–250 the two
  agree (the clip at 255 limits the wander).
- **tt 27 °C** (`--nf 11 --slope 13.4 --offset-mv 1.26`, step 0.136), code0 160 / 195: −92 dBm 96/96 both;
  −94 dBm ideal 49 / 49, drivers 25 / 33.

## Fix options looked at (none implemented)

| option | step factor (model) | DNL 127 | cost |
|---|---|---|---|
| (a) 8 re-drivers in the analog area, `buf_4` | 1.06 | −2.7 | std-cell block + routing between macro and r2r, DRC / LVS, re-export, reruns |
| (a) same, `buf_8` | 1.03 (SPICE 1.027–1.028) | −1.3 | as above |
| (b) series R in the termination only (handoff) | 1.30 | −12.6 | doesn't help: breaks R-2R at every node |
| (b′) + Rd/2 in every series R | 1.01–1.08 | ±0.5…−3 | creates gaps (+0.5 to +0.64 LSB); ladder re-layout |
| (c) unit R × 4 (42 kΩ) | 1.07–1.09 | −3.4…−4.3 | r2r re-layout, 4× resistor area in a 93 % full tile |
| **output buffer in the macro → `buf_8`** | **1.03** | **−1.3** | **a macro re-harden: do it only if one happens anyway** |

## If the macro is re-hardened

- Make `trim_out[7:0]` leave the macro through `sky130_fd_sc_hd__buf_8` (or at least `buf_4`), not
  `clkdlybuf4s25_1`. The cleanest way: instantiate the cells explicitly in the RTL top on the eight outputs
  (`SYNTH_READ_BLACKBOX_LIB` is already on), and check the netlist afterwards:
  `grep -B1 "trim_out\[" macros/radio_digital/radio_digital.nl.v`. (`PL_RESIZER_BUFFER_OUTPUT_PORTS` is 0, so
  today's cells don't come from the resizer's port buffering; find where they come from before relying on a
  flow setting.)
- `buf_8` is on VDPWR like the rest of the macro; 8 of them draw nothing at DC beyond the ladder's own ~86 µA.
- Check: `python3 sim/dac/tb_r2r.py --drv --cell=buf_8 [--temp=T] <corner>` (tt: step factor 1.03, 127 → 128
  −1.3 LSB), then the mixed −92 dBm set as in §4.

## Bring-up check

The servo can be frozen or set by register ([slicer.md](slicer.md) "Overrides"). Sweep the trim code 0–255 with
the comparator inputs held fixed, and record the comparator's ones density per code. Expected: a dip (density falls)
at 127 → 128 spanning ~11 codes, smaller ones at 191 → 192 (~5) and 63 → 64 (~6), and at 159 / 223 (~3). This
measures the real DAC + comparator transfer, drivers included, with no extra pins; the dip size gives the driver R
(`ladder_model.py`).

## Files

`sim/dac/tb_drv.py` (new), `sim/dac/tb_r2r.py` (`--drv`, `--cell`, full sweep, `--mc`), `sim/dac/r2r_summary.py`,
`sim/dac/r2r_mc.py` (new), `model/e2e.py` / `model/radio.py` (`--dac-curve`, `--dac-code0`),
`sim/mixed/gen_mixed.py` (`--drv`, `--vos`, saves `trim_out`), `sim/mixed/replay_corr.py` (reads the digital code).
Run times on sim-0: tb_drv 3 s per corner; tb_r2r 3 s per corner; MC 200 ~2 min at 6 jobs; mixed schematic
~5 min per 15.2 ms run (not hours); mixed `--pex` ~5 h; e2e 96 trials ~75 s.

Open: step 0 (how the tt08 bits were driven, and the size of its drop) wasn't answered, so the model isn't fitted
to silicon. The bring-up sweep above will do that on this chip.
