# Supply sweeps and mismatch, 2026-10-12 (sim-0)

Phase 2 of [plan_verify_gaps.md](plan_verify_gaps.md): gaps G1 (supply never varied at system level) and G2
(no mismatch on the comparator path). `main` after d198dbe, ring `NINV` 22, sim-0, IIC-OSIC-TOOLS 2026.09
(ngspice 47). Supplies: VDPWR 1.71 / 1.80 / 1.89 V, VAPWR 3.0 / 3.3 / 3.6 V (the plan's ±5 % / ±10 %; the TT
board tolerances were not looked up, so these may be wider than real).

## Summary

| Check | Result |
|---|---|
| RX chain gain / NF over VDPWR (tt 27, ss 10, fs 50 °C) | ✅ ±0.4 dB, NF unchanged (ideal bias sources) |
| Detector idle / slope over VDPWR | ✅ idle tracks VDPWR (1.44 / 1.52 / 1.60 V at tt); slope 11.8–14.1 mV/dB |
| Comparator offset at the operating CM, trim step | ✅ +0.4…+1.7 mV (nominal devices), step 0.064–0.069 mV/LSB |
| e2e −92 dBm at every supply × corner (nominal devices) | ✅ 12/12 at all 9 points |
| Chain stability, 1.89 V, ss 10 °C, 0.1 fF rule | ✅ stable (growth ≤ 5e-9), +1.6 dB peaking at 576 MHz with 0.1 fF |
| TX, schematic, 5 corners × 3 × 3 supplies | ⚠️ **ss at 1.71 V / 3.6 V: the p arm never turns on** (enable level shifter `tx_ls_en` stuck); fs there is weak (+3.4 dBm). Power follows VAPWR (−1.2 / +1.1 dB at 3.0 / 3.6 V) |
| TX, extracted ring + driver, 5 corners × 9 supplies | ⚠️ frequency 332–545 MHz on silicon (×0.845), inside the 330–560 MHz RX band but **ss at 1.71 V is at the bottom edge** (and likely below it hot). `tx_ls_en` is worse than in the schematic: **ss and fs at 1.71 / 3.6 V fail**, ss / fs at 1.71 / 3.3 V lose 1.5 dB |
| Analog top with real bias over supply (`tb_tile.py sch`, 7 points) | ✅ RX operating point tracks VDPWR; −60 dBm det drop 0.23–0.35 V everywhere. TX: ss 1.71 / 3.6 V fails here too; ss 10 °C 1.71 / 3.0 V turns off slowly (18 ns) |
| **Comparator-path mismatch (Monte Carlo)** | ❌ **offset sigma 2.8–3.4 mV. Rerun 2026-10-13 (200 distinct samples, each chip's own step): at tt / ss / fs 27 °C, 26–34 % of chips miss −92 dBm (about −90 dBm) and 8–10 % only reach about −88 dBm; 1 in 200 (ss) can't trim.** The first run here had duplicated samples (below) |
| avg_sc mismatch | ✅ settled offset sigma 0.13–0.16 mV |
| lna_chain mismatch (20 samples, tt) | ✅ gain 76.3–77.3 dB (nominal 76.7), no stage saturates |

**Gate 2 needs a decision on the comparator**, and a smaller one on `tx_ls_en` (fails at VDPWR 1.71 V with VAPWR 3.6 V at ss and fs, extracted; weak at 1.71 / 3.3 V). Details and options below.

## 2.1 Supply

### RX (`VDD=… OUT=… sim/corners/rx_corners.sh`, ideal bias sources)

| VDPWR | corner | I mA | gain 434 MHz dB | NF dB | det idle V | slope mV/dB | comp offset at op. CM mV | trim step mV/LSB (0.8–1.2 V) |
|---|---|---|---|---|---|---|---|---|
| 1.71 | tt 27 | 2.85 | 76.3 | 11.1 | 1.438 | 12.8 | +1.47 (CM 1.4) | 0.066 |
| 1.71 | ss 10 | 2.82 | 80.7 | 10.6 | 1.452 | 13.6 | +1.66 | 0.064 |
| 1.71 | fs 50 | 2.82 | 75.2 | 12.0 | 1.443 | 11.8 | +1.67 | 0.069 |
| 1.80 | tt 27 | 2.88 | 76.7 | 11.0 | 1.520 | 13.4 | +0.95…+1.26 | 0.067 |
| 1.80 | ss 10 | 2.85 | 81.2 | 10.5 | 1.535 | 13.8 | +0.87…+2.62 | 0.064 |
| 1.80 | fs 50 | 2.86 | 75.7 | 12.0 | 1.525 | 12.4 | +1.22…+1.30 | 0.069 |
| 1.89 | tt 27 | 2.90 | 76.9 | 10.9 | 1.602 | 13.8 | +0.51…+0.62 | 0.067 |
| 1.89 | ss 10 | 2.87 | 81.5 | 10.5 | 1.617 | 14.1 | +0.41…+0.63 | 0.064 |
| 1.89 | fs 50 | 2.89 | 76.0 | 11.9 | 1.607 | 12.9 | +0.79…+0.86 | 0.069 |

- The detector idle level moves with VDPWR (~0.9 V/V), and the comparator's input CM with it, so the
  comparator keeps the same headroom. At 1.71 V the comparator has no threshold at CM 1.55 V (ss) or
  +5 mV offset there (tt), but det can't reach 1.55 V at that supply (idle 1.44 V; signal only pulls it down).
- These benches use ideal bias currents, so they show the blocks' own supply sensitivity; the bias
  generator's (1.7–1.9 V, `tb_bias_gen.py`) is separate. The whole analog top with the real bias over
  supply is `tb_tile.py --vdd=… --vapwr=… sch`, below.
- **e2e** (`model/e2e.py`, noise case, 12 trials, 0.3 mV comparator noise, each row's NF / slope / offset /
  step): −92 dBm **12/12 at all 9 points**; −94 dBm (information) 5/12 at fs 50 °C 1.71 V, 7–9/12 at fs,
  10–12/12 elsewhere. No false toggles.
- **Stability** (`VSUP=1.89 CORNER=ss TEMP=10 sim/chain/stability.sh`): gain 85.2 dB at 434 MHz; every case
  decays (kick growth 2e-10…5e-9). 0.1 fF output → input: 84.8 dB, +1.6 dB peaking at 576 MHz (stable).

### TX (`tb_tx.py --vdd=… --vapwr=…`, schematic, 27 °C)

Antiphase power into the 73 Ω dipole, dBm (frequency in brackets, schematic ring, MHz):

| corner | 1.71 / 3.0 | 1.71 / 3.3 | 1.71 / 3.6 | 1.8 / 3.0 | 1.8 / 3.3 | 1.8 / 3.6 | 1.89 / 3.0 | 1.89 / 3.3 | 1.89 / 3.6 |
|---|---|---|---|---|---|---|---|---|---|
| tt | 3.15 (442) | 4.39 | 5.48 | 2.89 (486) | 4.14 | 5.25 | 2.68 (526) | 3.93 | 5.05 |
| ss | 3.17 (361) | 4.43 | **FAIL** | 2.95 (402) | 4.26 | 5.39 | 2.69 (440) | 4.01 | 5.17 |
| ff | 3.21 (506) | 4.39 | 5.44 | 2.95 (548) | 4.14 | 5.20 | 2.70 (586) | 3.89 | 4.96 |
| sf | 3.23 (417) | 4.43 | 5.56 | 3.01 (462) | 4.23 | 5.37 | 2.76 (504) | 4.00 | 5.15 |
| fs | 3.14 (458) | 4.37 | **3.42** | 2.88 (502) | 4.14 | 5.17 | 2.62 (543) | 3.89 | 4.94 |

- **ss 1.71 / 3.6 V fails:** the ring and the data level shifter (a / b) run, but `enh_p` never rises
  (`enhb_p` stuck at ~2.8 V in contention) and `enh_n` flips ~45 ns late, so the p arm stays off.
  `tx_ls_en` is tx_ls at kn = kp = 1: at low VDPWR its 1.8 V NMOS can't overpower the 3.6 V PMOS. fs at the
  same supplies loses 2 dB the same way. 3.3 V is fine at every corner.
- Frequency follows VDPWR (~0.9 %/10 mV); VAPWR doesn't move it. Power follows VAPWR: −1.2 / +1.1 dB at
  3.0 / 3.6 V vs 3.3 V, just outside the plan's "within 1 dB", which is the expected V² scaling of a ±10 % supply.

### TX, extracted ring + driver (`tb_tx.py --pex --pex-ring --vdd=… --vapwr=…`, 27 °C)

Frequency on silicon (extracted × 0.845, the ttsky25b calibration; tb_tx still prints ×0.866) and antiphase
power, dBm. Frequency doesn't depend on VAPWR (within 1 MHz), so one column per VDPWR:

| corner | f 1.71 V | f 1.80 V | f 1.89 V | P 1.71 / 3.0 | 1.71 / 3.3 | 1.71 / 3.6 | 1.8 / 3.0 | 1.8 / 3.3 | 1.8 / 3.6 | 1.89 / 3.0 | 1.89 / 3.3 | 1.89 / 3.6 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tt | 408 | 448 | 485 | 2.41 | 3.71 | 4.84 | 2.04 | 3.42 | 4.59 | 1.58 | 3.11 | 4.33 |
| ss | **332** | 370 | 404 | 2.49 | **2.22** | **FAIL** | 2.19 | 3.56 | 4.74 | 1.90 | 3.33 | 4.55 |
| ff | 471 | 509 | 545 | 2.20 | 3.52 | 4.64 | 1.73 | 3.17 | 4.33 | 1.21 | 2.83 | 4.04 |
| sf | 388 | 429 | 468 | 2.46 | 3.77 | 4.94 | 2.02 | 3.43 | 4.64 | 1.48 | 3.05 | 4.30 |
| fs | 421 | 460 | 497 | 2.39 | **2.21** | **FAIL** | 2.01 | 3.40 | 4.51 | 1.59 | 3.11 | 4.27 |

- **Band:** every point is inside 330–560 MHz, but ss at 1.71 V is 2 MHz from the bottom edge at 27 °C. The
  ring slows ~3 % hot (ff 1.89 V: 586 → 570 MHz schematic, 27 → 85 °C), so ss / 1.71 V / 85 °C is probably
  ~322 MHz, just outside. The top end has 15 MHz to spare (ff 1.89 V).
- **`tx_ls_en`** is worse extracted than in the schematic: at 1.71 / 3.6 V both ss and fs never turn the p arm
  on, and at 1.71 / 3.3 V (nominal VAPWR) ss and fs lose 1.5 dB (the p arm switches late and stays high ~20 ns
  after the key). Everything at VDPWR ≥ 1.8 V is fine.
- Extracted power is ~0.7 dB below the schematic (3.42 vs 4.14 dBm at tt nominal), as before.

### Analog top with real bias (`tb_tile.py --vdd=… --vapwr=… --corner=… --temp=… sch`)

`tb_radio_analog` with the real bias generator, both pads, schematic blocks (one run ~50 s at 8 threads):

| VDPWR / VAPWR, corner | IDPWR RX mA | vcm V | det idle V | det at −60 dBm V | off µA | TX f MHz (sch) | TX P73 dBm |
|---|---|---|---|---|---|---|---|
| 1.8 / 3.3, tt 27 | 2.97 | 1.201 | 1.521 | 1.206 | 0.91 | 486 | 4.14 |
| 1.71 / 3.0, tt 27 | 2.79 | 1.141 | 1.450 | 1.166 | 0.86 | 442 | 3.15 |
| 1.89 / 3.6, tt 27 | 3.16 | 1.261 | 1.592 | 1.247 | 0.95 | 526 | 5.05 |
| 1.71 / 3.0, ss 10 | 2.81 | 1.141 | 1.461 | 1.121 | 0.86 | 358 | 3.43 (off in 18 ns) |
| 1.71 / 3.6, ss 10 | 2.81 | 1.141 | 1.461 | 1.121 | 0.86 | **FAIL** (`tx_ls_en`) | |
| 1.71 / 3.0, fs 50 | 2.75 | 1.141 | 1.458 | 1.194 | 0.88 | 457 | 2.77 |
| 1.89 / 3.6, ff 85 | 3.07 | 1.261 | 1.573 | 1.341 | 1.46 | 570 | 4.18 |

- The bias generator's vcm follows VDPWR (2/3), and det idle with it, as in the ideal-bias benches. The
  −60 dBm det drop is 0.23–0.35 V at every point, so the detector works across supply with the real bias.
- At ss 10 °C, 1.71 / 3.0 V, after the key the arms park at p high / n low with ~6 mA from VAPWR, and turn
  off 18 ns after the key (checked to 2 µs; normally ~4 ns). Harmless at OOK bit rates.

## 2.2 Mismatch (Monte Carlo)

sky130A in the 2026.09 image: `.lib … <corner>_mm` sets `MC_MM_SWITCH=1`, which adds `AGAUSS` per device
(FETs: Vt, scaled 1/sqrt(W·L·mult); resistors; MIM caps). Each `reset` redraws.

**Correction (2026-10-13): the first runs below drew duplicated samples.** Without a seed every ngspice
process starts from the same sequence, so `--jobs 8` gave 8 copies of the same 25 chips (`--jobs 4` in
`mc_chain.py`: 4 copies of 5). `tb_comp_ct.py` now runs one sample per process with its own `.options seed`
(sim_learnings.md). The comparator was rerun ("Rerun" below); the avg_sc and lna_chain tables are still
from the duplicated runs (25 and 5 distinct samples), which is too few for their sigmas but unlikely to
change their verdicts.

### comp_ct (`tb_comp_ct.py --mc 200 --cm … --temp … <corner>`)

Ideal 1 µA bias, inputs at the operating CM. Per sample: offset at trim mid, and the trim voltage where the
output switches with no input difference (the code the servo settles to without signal).

First run (duplicated samples, about 25 distinct; superseded by the rerun below):

| corner, CM | offset mean | sigma | switch code mean ± sigma | below code 96 | code > 242 or no switch |
|---|---|---|---|---|---|
| tt 27 °C, 1.5 V | +0.79 mV | 3.22 mV | 126 ± 40 | 26 % | 2 % |
| fs 50 °C, 1.5 V | +1.25 mV | 2.91 mV | 121 ± 31 | 26 % | 0 % |
| sf 10 °C, 1.45 V | +2.67 mV | 3.65 mV | 109 ± 32 | 48 % | 0 % |
| sf 10 °C, 1.5 V | +13.4 mV | 6.5 mV | 80 ± 9 | (known no-threshold region) | |

![comparator Monte Carlo](../sim/plots/mc_comp.png)

**Rerun (2026-10-13, Linux host): 200 distinct samples, each chip's own step.**
`tb_comp_ct.py --mc 200 --jobs 6 --step <corner>` (27 °C, CM 1.5 V): `--step` finds the switching trim
with vd = ±0.1 mV, so each sample's own step at its switching point, instead of the nominal transfer
used for the fractions above. e2e at each step (`model/e2e.py --nf 11 --brf 450e6 --slope 13.4
--offset-mv 1.26 --comp-noise-mv 0.3 --cases noise --trials 12`, tt 27 °C, nominal supply):

| step mV/LSB | 0.077 | 0.15 | 0.19 | 0.30 | 0.43 | 0.57 |
|---|---|---|---|---|---|---|
| −94 dBm | 11/12 | 2/12 | 1/12 | 0/12 | 0/12 | 0/12 |
| −92 dBm | 12/12 | 12/12 | 12/12 | 9/12 | 1/12 | 1/12 |
| −90 dBm | 12/12 | 12/12 | 12/12 | 12/12 | 11/12 | 8/12 |
| −88 dBm | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 |

| corner | offset mean ± sigma | switch code | step median | ≤ 0.19 (−92 dBm) | 0.19–0.43 (≈ −90) | 0.43–0.6 (≈ −88) | no switching point |
|---|---|---|---|---|---|---|---|
| tt 27 °C | +1.34 ± 3.17 mV | 120 ± 36 | 0.077 | 70 % | 20 % | 10 % | 0 (2 at code > 242) |
| ss 27 °C | +1.02 ± 3.35 mV | 126 ± 37 | 0.075 | 66 % | 24 % | 10 % | 1 |
| fs 27 °C | +0.92 ± 2.79 mV | 124 ± 32 | 0.075 | 74 % | 17 % | 8 % | 0 |

The steps split in two: a chip lands either on the linear part (0.06–0.08 mV/LSB) or well down the steep
part, up to 0.57–0.60 mV/LSB, steeper than the nominal transfer gives for the same code because the
mismatch bends each chip's transfer too. The corner barely matters (the spread is mismatch). Not rerun:
ss 10 °C, fs 50 °C, sf, and the 1.71 V supply corner, where the earlier e2e loses more at the same step.

**Why it matters: the trim transfer is not linear around the nominal code.** At CM 1.5 V, tt, nominal
devices, the comparator switches at code 112 (0.786 V), not ~135 (0.95 V) as assumed for the "local step
0.8–1.2 V" figures. Below ~code 105 the step grows fast:

| input offset cancelled | 0 | −1 mV | −1.5 | −2 | −2.5 | −3 | −4 | −6 |
|---|---|---|---|---|---|---|---|---|
| switch code | 112 | 100 | 96 | 94 | 92 | 90 | 87 | 83 |
| step mV/LSB | 0.069 | 0.096 | 0.131 | 0.18 | 0.24 | 0.29 | 0.39 | 0.51 |

Above code 112 the step is 0.06 mV/LSB up to the end (+7.5 mV at code 233). e2e at the worst supply corner
(fs 50 °C, 1.71 V) against the step: 0.10 → −92 dBm 12/12; 0.13 → 11/12; 0.16 → 9/12; 0.19 → 6/12 (−90 and
−88 dBm still 12/12); 0.3 → 1/12. Against offset (linear trim model): +6.4 and +8.0 mV 12/12, +9.6 mV 0/12
(the trim runs out). So a chip whose comparator lands below code ~96 loses 1–3 dB of sensitivity, and one past
the top end misses −92 dBm: the servo stops at code 255 and the rest of the offset stays, costing part of the
~2 dB the servo buys (more the further past the end; only −92 dBm was run). The fractions above use the nominal transfer for every sample, so they are
estimates.

**What sets the spread** (tt, 100 samples each, one device type's Vt mismatch zeroed with
`MM_OFF=… tb_comp_ct.py --mc`): all off → 0.04 mV (resistors and caps don't matter);
`pfet_01v8_lvt` off → 1.85 mV; `nfet_01v8_lvt` off → 2.72 mV; `nfet_01v8` off → 2.85 mV. By variance:
**~65 % the PMOS mirror load** (Mp1 / Mp2, pfet_01v8_lvt W 4 L 1; the PDK's A_Vt for that type is
10.9 mV·µm, so σVt ≈ 5.4 mV per device), ~28 % the nfet_lvt input and trim pairs, ~22 % the nfet current
sources (Mta_sa / sb, Mt1).

Options for Gate 2 (options 2 + 3 being tried, 2026-10-13: `sim/comp_ct/trim_curve.py`, [handoff_comp_trim.md](handoff_comp_trim.md)):
1. **Bigger mirror**: Mp1 / Mp2 at 4× area halves their term (e.g. W 8 L 2); pfet_01v8 (A_Vt 5.9) instead of
   lvt helps too if headroom allows. Then the nfet terms: input pair, Mta pair.
2. **Centre the operating point in the linear part of the trim**: today nominal sits at the knee (code 112),
   so any negative offset falls into the steep part. A designed-in offset (or vref) that puts nominal near
   code ~170 gives ±3.5 mV of fine trim either side.
3. **Wider linear trim** (smaller rdeg or larger trim current): more range per code, at a larger step
   (0.08 mV/LSB still passes e2e).

### Trim redesign candidates (2026-10-13, sim-0, branch `comp-trim`): gate for Matt

[handoff_comp_trim.md](handoff_comp_trim.md) steps 1–5. Every candidate: trim pair M3 / M4 W 2 → 8. Tags give
Rdeg and vref: **A** 1.2 MΩ, **B** 1.0, **E** 0.8, **G** 0.9 MΩ; **C / F / G** add option 1's mirror (Mp1 / Mp2
W 4 L 1 → W 8 L 2); the number is vref (124 = 1.24 V). Curves: `trim_curve.py` + `trim_summary.py`; Monte Carlo:
`tb_comp_ct.py --mc 200 --jobs 24 --step` (200 distinct samples, **no duplicate rows in any run**; `mc_bins.py`).

**Which vref the layout can make.** vref is a bottom link of the Rr1 + Rr2 string, and `PolyRes` puts the bottom
links after an even number of segments from VDD (`links[k]`, k odd). The 32-segment string today gives 1.35 /
1.24 / 1.125 / 1.01 V. **1.286 V needs a 28-segment string** (same 8.5 µm segments, tap after 8: LR1 68 /
LR2 170 µm), which is narrower than today's.

**What decides it.** The offset σ (~3.2 mV without the mirror) has to fit in the window both ways. The top end
is the harder one: past code 255 (the DAC end) the servo stops and the rest of the offset stays, so the chip loses
part of the sensitivity the servo buys (a little just past the end, more further out; not quantified). Between code 242
and 255 the step only gets *finer*. The bottom end is soft: past it, chips trim on the steep part and lose dB.
- **Without the mirror no buildable vref works.** B124 / B113 / A113 / A124 put 100 % of chips at −92 dBm at tt,
  but their code σ is 29–34, so mean + 4σ = 276–288 codes, past the DAC. E (0.8 MΩ) gets to 253–262.
- **The mirror cuts the offset σ to 2.0–2.6 mV** (17–21 codes) at every corner.
- **sf 10 °C at CM 1.45 V moves every chip ~40 codes down**, into the steep part, so vref can't go low:
  C113 has 70 % there, F124 94 %, F129 / G129 / F135 / G135 96–100 %.
- **The worst supply corner sets the step.** e2e at fs 50 °C / 1.71 V (`--nf 12 --slope 11.8 --offset-mv 1.67`,
  48 trials), −92 dBm: step 0.077 → 48/48, 0.110 → 46, 0.122 → 47, 0.130 → 45, **0.138 → 40/48** (pass ≥ 44).
  F (0.8 MΩ) has its p95 step there at 0.135 (median 0.130), so about half its chips are at the edge.

**Gate table** (% of chips with step ≤ 0.19 / 0.19–0.43 / > 0.43 mV/LSB ≈ −92 / ≈ −90 / ≈ −88 dBm; 27 °C CM 1.5 V
unless noted; supply rows with CM scaled with VDD, 1.43 / 1.58 V, sf 1.52 V at 1.89 V; +4σ = mean + 4σ switching
code, worst corner):

| candidate | tt | ss | fs | ss 10 °C | fs 50 °C | sf 10 °C CM 1.45 | 1.71 V (tt, fs 50) | 1.89 V (tt, fs 50, sf 10, ss 10) | can't trim | +4σ code | step med (p95 worst) | −94 dBm, typical chip (tt / worst corner, 48 trials) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| today (nom) | 78 / 15 / 8 | 66 / 24 / 10 † | 74 / 17 / 8 † | | | 47 / 28 / 25 | | | 0–1 | 266 | 0.069 (0.62) | 43 / 16 of 48 |
| C113 (1.0 MΩ, mirror, 1.125 V) | 100 | 98 / 2 / 0 | 100 | 100 | 100 | **70 / 24 / 6** | | | 0 | 233 | 0.110 (0.44 sf) | 32 / 4 |
| F124 (0.8 MΩ, mirror, 1.24 V) | 100 | 100 | 100 | 100 | 100 | **94 / 6 / 0** | | | 0 | 237 | 0.134 (0.19 sf) | 23 / 0 |
| F129 (0.8 MΩ, mirror, 1.286 V) | 100 | 100 | 100 | 100 | 100 | 100 | 100, 100 | 100 ×4 | 0 | 245 | 0.134 (0.135 at fs 50 / 1.71: **e2e ✗**) | 23 / 0 |
| F135 (0.8 MΩ, mirror, 1.35 V) | 100 | 100 | 100 | 100 | 100 | 99 / 1 / 0 | 100, 100 | 100 ×3 | 0 | 249 | as F129: **e2e ✗** | 23 / 0 |
| G135 (0.9 MΩ, mirror, 1.35 V) | 100 | | 100 | | 100 | 100 | | | 0 | **257** | 0.121 | 30 / 2 |
| **G129 (0.9 MΩ, mirror, 1.286 V)** | **100** | **100** | **100** | **100** | **100** | **96 / 4 / 0** | **100, 100** | **100 ×4** | **0** | **253** | **0.121 (0.122 at fs 50 / 1.71: 47/48)** | **30 / 2 of 48** |

† ss / fs for today's design are from the Linux-host rerun above.

**Supply (Matt, 2026-10-13): the chip can rely on good 1.8 / 3.3 V supplies.** Measured on 3 TT boards: IO /
VDDA 3.30 V on all three, core 1.80 / 1.80 / 1.81 V. So the 1.71 / 1.89 V columns above are information only.
The worst corner at 1.8 V is fs 50 °C (`--nf 12.0 --slope 12.4 --offset-mv 1.3`, 48 trials), −92 dBm: step
0.077 → 48/48, 0.122 → 48, 0.128 → 47, 0.137 → 48, **0.142 → 43**, 0.148 → 42, 0.166 → 42 (pass ≥ 44). The
F designs' p95 there is 0.142–0.143, right at the edge (borderline, no longer a clear fail). G129's is 0.128.
One more candidate under that rule: **H135** (Rdeg 0.85 MΩ, mirror, 1.35 V: today's 32-segment string, tap moved
only). −92 dBm 100 % at tt / ss / fs / ss 10 / fs 50 / ff 50 / sf 27 CM 1.45, 99 % at sf 10 CM 1.45. p95 at
fs 50 °C 0.135 (passes). But its +4σ code is **256 at tt** (180 ± 19), one past the DAC end. G129 also gained
ff 50 °C (100 %, p95 0.135) and sf 27 °C CM 1.45 (99.5 %).

**Recommendation: G129** is the only candidate that meets every pass condition: ≥ 95 % of chips at −92 dBm at
every corner and supply, where the lowest is 96 % at sf 10 °C / CM 1.45; the e2e at its p95 step on the worst
corner; and no chip past the DAC end at 4σ, with 253 the worst (tt) against 255, so only a few codes spare.
**Cost:** −94 dBm on the typical chip drops from 43/48 to 30/48 at tt, and from 16/48 to 2/48 at the worst
corner. −94 dBm becomes a best-case number; −92 dBm becomes the number for nearly every chip, not 2/3 to 3/4 of
them. F129 has more room at the top (245) but a coarser step that misses the e2e bar at fs 50 °C / 1.71 V. The
two candidates that fit today's 32-segment string fail: G135 on the top end (257), F135 on the e2e.

**Layout and design change (G129):**
- Schematic: `COMP_PARAMS` rdeg 2 MΩ → 0.9 MΩ; M3 / M4 W 2 → 8; Mp1 / Mp2 W 4 L 1 → 8 / 2; Rr1 / Rr2
  `lref` 136 / 136 → 68 / 170 µm.
- Layout: Rdeg 30 segments, 271 → 122 µm total, so shorter segments. vref string 32 → 28 segments, tap
  `rr.links[15]` → `links[7]`; the divider current goes up ~14 %, to ~1.3 µA. The trim halves go W 1.0 → 4.0,
  under the main pair's 5 µm fingers.
  **The mirror is the open layout question:** four halves of W 2 L 1 become W 4 L 2 in the ABBA P row. That row
  gets taller and its gates longer, and nobody has checked yet whether it fits the 73.5 × 42.0 µm footprint
  without moving pins.
- The servo's nominal code goes from 112 to ~170. The RTL resets to 128, so add ~40 ticks (~0.6 ms) of settling
  after reset.

**Found on the way (new finding, not a trim problem): sf 10 °C at VDPWR 1.71 V.** At CM 1.38 V (≈ det idle
there), today's design has 16 % of chips at −92 dBm (offset +8.1 ± 4.6 mV, balance code ~91, on the steep
part) and G129 has 2 % (+16.5 ± 5.9 mV). At CM 1.43 V neither has a threshold for most or all chips: 75 / 200
rows for today's, none for G129. This is the known sf "no threshold at high CM" region (CM 1.55 V at 1.8 V),
moving down with VDD. The input pair runs out of headroom, which a trim can't fix. It was never run before. If
TT's VDPWR stays ≥ 1.75 V it may not occur; see [verify_system_2.md](verify_system_2.md) Findings #12.

Re-run: `python3 sim/comp_ct/trim_curve.py G129 LR1=68 LR2=170 rdeg=0.9Meg W3=8 W4=8 WP=8 LP=2`, then
`COMP_SUB=build/trim/G129_sub.spice COMP_PRM="$(cat build/trim/G129_prm)" COMP_TAG=G129 python3
sim/comp_ct/tb_comp_ct.py --mc 200 --jobs 24 --step [--temp T] [--cm C] [--vdd V] <corner>` (~40 s for 200
samples on sim-0), `python3 sim/comp_ct/mc_bins.py [--vdd V] build/mc/comp_*_step_G129.txt`.

### avg_sc (`tb_avg_sc.py --mc 200 --temp … <corner>`)

Cs / (Cs + Cavg) 0.0280 with no measurable spread. Settled charge-injection offset: tt 27 °C −0.04 ± 0.13 mV,
fs 50 °C 0.00 ± 0.13, sf 10 °C −0.05 ± 0.16 mV. Negligible next to the comparator (adds < 0.01 mV in quadrature).

### lna_chain (`sim/chain/mc_chain.py --mc 20 tt`)

Differential DC at each stage output: sigma 14–19 mV, max 49 mV, and it doesn't grow along the chain. Gain at
434 MHz 76.3–77.3 dB against 76.7 nominal: within 1 dB, so no stage is pushed into compression.

![avg_sc and chain Monte Carlo](../sim/plots/mc_avg_chain.png)

## Re-running

- RX supply: from `build/`, `VDD=1.71 OUT=corners_v171 CORNERS=tt TEMPS=27 NT=1 bash ../sim/corners/rx_corners.sh`,
  then `CORNERS_DIR=build/corners_v171 python3 sim/corners/rx_corners.py`.
- TX: `NT=1 python3 sim/tx/tb_tx.py --vdd=1.71 --vapwr=3.6 tt ss ff sf fs` (add `--pex --pex-ring` for the
  extracted ring and driver). Run one tb_tx process at a time: parallel ones overwrite the shared
  `build/tb_tx.spice` netlist.
- Analog top: `OSIC=tools/osic NT=8 python3 sim/top/tb_tile.py --vdd=1.71 --vapwr=3.0 --corner=ss --temp=10 sch`.
- Stability: from `build/real`, `VSUP=1.89 CORNER=ss TEMP=10 CASES='0:0 2n:0 2n:0.1f' bash ../../sim/chain/stability.sh`.
- Monte Carlo: `tb_comp_ct.py --mc 200 --cm 1.5 --temp 27 tt`, `tb_avg_sc.py --mc 200 tt`,
  `sim/chain/mc_chain.py --mc 20 tt`; plots `python3 sim/comp_ct/plot_mc.py`.
