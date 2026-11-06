# Verification of the LNA low-gain strap (branch `lna-lo-shunt`, sim-0, 2026-11-04 / 05)

The handoff's 9 items (`docs/handoff_lna_lo.md` "Verification to run here"), run on sim-0. Job list:
`sim/rerun/jobs_lna_lo.py` (the 2026-10-13 set plus the new checks), scheduler `sim/rerun/sched.py`. Logs:
`build/rerun_lnalo/logs/` on sim-0. Final count: 425 OK, 24 ended under an earlier scheduler instance (exit code lost,
each checked by its log), 0 failed.

## Summary

| # | Item | Result |
|---|---|---|
| 1 | GL cocotb | **pass**: RTL 16/16, GL 16/16 incl. `test_lna_lo_strap`; TT-level RTL 5/5, tt_gl pass; formal prove PASS |
| 2 | Full rerun vs `verify_2026-10-13.md` | **pass, one FAIL**: chain / RX −0.53…−0.73 dB extracted, −0.2…−0.3 dB sch, as predicted; overload gap scan (`mixed_-90_ov*`) no longer shows one dead time, unexplained |
| 3 | Chain stability, extracted, both strap states | **pass**: low gain decays at ≥ 1 fF everywhere (worst ss 10 °C 1.62 V: 1 fF ok, 1.5 fF oscillates) |
| 4 | MC on the step | **pass on the full GDS extraction**: step 11.9 dB at tt, 10.1 dB at sf 27 °C (~99 % ≥ 9 dB by the block MC's σ; MC not run on it). The block extraction ([verify_system_2.md](verify_system_2.md) finding #5's pessimistic bound) fails: sf 9.3 % ≥ 9 dB (nominal 8.46), ss 10 °C 86.4 %, but low gain still stabilises the chain at sf, so it also passes with the spec stated as a stability margin (follow-up below) |
| 5 | Low-gain sensitivity, transistor level | **FAIL** at −88 dBm (7/20 detect); reliable at −86 dBm (19/20); a non-monotonic dip at −88 (−90: 16/20) |
| 6 | Extracted tile, vglo 1.8 / 0 | **pass**: RX current identical, −60 dBm det shifts by ~10 dB of slope |
| 7 | FasterCap, st5 / st6 Cs ↔ g1 | **pass**: −0.19 / −0.55 / −2.31 aF (kpex bound 6.6 / 9.8 aF) |
| 8 | Substrate study | **pass**: late stages 1.2e-5 fF (≤ 1e-4); every link 1.44e-4 fF, identical to main (above 1e-4 taken literally) |
| 9 | TT precheck | **pass**: GitHub docs / gds / lvs succeed |

Items 4 and 5 are reported for Matt, not fixed (handoff: don't redesign).

## 1. Gate-level cocotb, formal, pinout

| Check | Result | Reference |
|---|---|---|
| `verilog/test` RTL | 16/16 | 16/16 |
| `verilog/test` GL (`make GL=1`) | 16/16, incl. `test_lna_lo_strap` | 16/16 |
| TT-level `test/` RTL / GL | 5/5 / pass | – |
| Formal `radio_digital_prove` (abc pdr) | PASS, 2139 s | PASS |
| `tools/check_pinout.py` | OK | OK |
| Rebuilt tile vs `gds/` (`sim/rerun/xor_gds.py`) | metal identical | – |

Fixed on the way (harness, not design):
- the formal harness had a stale 1010-only magic. Now 1010 / 1011, plus a property: `lna_lo_n == !(1011 latched at reset)` (17a7b39);
- the TT-level `radio_analog` stub had no `lna_lo_n` port, so tt_rtl didn't elaborate (2e2af54).

## 3. Chain stability on the extracted chain

`sim/chain/stability.sh` in `build/pexsim` (extracted `lna_chain` swapped into `tb_chain`), real decap, L 2 nH, a 1 µA kick.
"ok" = the kick decays (growth ~1e-9). "OSC" = sustained oscillation (late p-p > 1 mV, growth ~1). The number given
is the growth.

| Corner | Strap | 0 | 0.3 fF | 0.5 fF | 0.75 fF | 1 fF | 1.5 fF | 2 fF | 3 fF |
|---|---|---|---|---|---|---|---|---|---|
| ss 10 °C 1.8 V | off | ok | ok | ok | OSC 0.99 | OSC | OSC | | |
| ss 10 °C 1.8 V | **on** | ok | | ok | | **ok** | ok 3e-7 | OSC 1.0 | OSC |
| ss 10 °C 1.62 V | off | ok | ok | ok | OSC 0.62 | OSC | OSC | | |
| ss 10 °C 1.62 V | **on** | ok | | ok | | **ok** | OSC 1.01 | OSC | OSC |
| ss 10 °C 1.98 V | off | ok | ok | ok 4e-4 | OSC 0.98 | OSC | OSC | | |
| ss 10 °C 1.98 V | **on** | ok | | ok | | **ok** | ok | OSC 1.3 | OSC |
| tt 27 °C 1.8 V | off | ok | ok | ok | ok | OSC 1.0 | OSC | | |
| tt 27 °C 1.8 V | **on** | ok | | ok | | **ok** | ok | ok | OSC 1.7 |
| ff 50 °C 1.8 V | off | ok | ok | ok | ok | ok | ok | | |
| ff 50 °C 1.8 V | **on** | ok | | ok | | **ok** | ok | ok | ok |

**Pass** (low gain decays to ≥ 1 fF at every corner). Low gain moves the edge from 0.5–0.75 fF to 1–1.5 fF at ss,
and from 0.75–1 fF to 2–3 fF at tt. The thinnest case is **ss 10 °C, 1.62 V: 1 fF ok, 1.5 fF oscillates.**

## 4. Monte Carlo on the step

`sim/chain/mc_chain.py`: 1000 mismatch samples per corner. Each sample is one seeded process that measures
vglo 1.8 and 0 on the same draw (0 duplicates). Gain at 434 MHz.

| Corner | Bench | Step mean / σ / min, dB | ≥ 9 dB | Nominal step | Strap-off gain vs nominal | Within 1 dB |
|---|---|---|---|---|---|---|
| tt 27 | sch | 12.03 / 0.25 / 11.11 | 100 % | 12.04 | −1.24…+0.96 | 99.4 % |
| ss 10 | sch | 11.52 / 0.34 / 10.48 | 100 % | 11.53 | −1.11…+1.00 | 99.4 % |
| ff 50 | sch | 12.27 / 0.18 / 11.70 | 100 % | 12.26 | −1.18…+0.96 | 99.9 % |
| fs 27 | sch | 12.90 / 0.18 / 12.21 | 100 % | 12.90 | −1.18…+1.02 | 99.5 % |
| sf 27 | sch | 10.55 / 0.41 / 9.07 | 100 % | 10.56 | −1.17…+1.23 | 99.5 % |
| tt 27 | **pex** | 10.17 / 0.26 / 9.15 | 100 % | 10.17 | −1.22…+0.96 | 99.7 % |
| ss 10 | **pex** | 9.41 / 0.37 / 7.99 | **86.4 %** | 9.44 | −1.03…+0.91 | 99.8 % |
| ff 50 | **pex** | 10.41 / 0.20 / 9.77 | 100 % | 10.43 | −0.62…+0.40 | 100 % |
| fs 27 | **pex** | 11.12 / 0.18 / 10.44 | 100 % | 11.12 | −0.96…+0.76 | 100 % |
| sf 27 | **pex** | 8.45 / 0.44 / 6.92 | **9.3 %** | **8.46** | −1.22…+0.72 | 99.7 % |

**FAIL** (≥ 9 dB in ≥ 99 %) on the extracted chain at sf 27 °C and ss 10 °C. At sf even the nominal is short. The
handoff's corner table had tt / ss / ff only. The extracted gain bench (`sim/chain/lna_lo.sh`) confirms it:
- sf 27: 75.48 / 67.02 dB, step 8.46;
- fs 27: 75.41 / 64.29 dB, step 11.12.

"Strap-off within 1 dB of nominal": 99.4–100 % of samples, spread about ±1.2 dB. If that has to hold for every
sample, it misses in ≤ 0.6 %.

**Why:** the shunt PMOS (W 18, L 0.15, body VDD) has its gate at 0 V and its source at the o2 common mode (~1.1 V).
With body effect that is close to threshold, so Ron follows the PMOS corner. One device at the o2 bias
(0.001 V across it):

| Corner | tt 27 | ss 10 | ff 50 | sf 27 | fs 27 |
|---|---|---|---|---|---|
| Ron, Ω | 711 | 1759 | 396 | 1851 | 378 |

The nominal vglo sweep shows the same: the step is still rising steeply at 0 V (vglo 0.4 V: 0.22 dB, 0.2 V: 2.0 dB,
0 V: 8.5 dB at sf extracted). o2 CM is the same at sf and fs (1.106 / 1.117 V), so it's the device, not the bias.
Options for Matt: a wider shunt, or the body on the source. Not changed here.

### Follow-up (2026-11-06): block vs full GDS extraction, stability at sf, a wider shunt

**The FAIL depends on which extraction is used.** The MC above swaps the block extraction
(`layout/pex/lna_chain.spice`, `layout/pex.sh`) into `tb_chain`. That's the flow
[verify_system_2.md](verify_system_2.md) finding #5 already found disagrees with the full GDS extraction
(`layout/pex_tile.sh`: the whole tile GDS, extracted in its real surroundings) by ~3.6 dB of chain gain on `main`, before the shunt. That finding keeps the block result as a
pessimistic bound and quotes the tile. The step comes out differently in the two flows too. At −90 dBm, in square
law, step = 10·log10(det drop off / on):

| Bench (tt 27 °C unless noted) | Strap off | Strap on | Step |
|---|---|---|---|
| A: `tb_chain`, block extraction (AC gain, dB) | 75.48 | 65.31 | 10.17 |
| Tile bench, schematic (det drop, mV) | 4.92 | 0.32 | 11.9 |
| Tile bench, schematic tile + block-extracted chain swapped in | 4.18 | 0.40 | 10.2 |
| Tile bench, full GDS extraction c (item 6) | 5.94 | 0.39 | 11.8 |
| **Tile bench, schematic, sf 27 °C** | 4.86 | 0.43 | 10.5 |
| **Tile bench, full GDS extraction c, sf 27 °C** | 5.76 | 0.56 | **10.1** |

The block extraction gives the same 10.2 dB in either bench, so `tb_chain` and `mk_pex_tb.py` are fine. Tile AC
sweeps (100 MHz–2 GHz, 434 MHz): the difference is all in stage 2's strap-off gain (o2 − o1: block 11.59, tile 13.05,
schematic 12.63 dB; strap on, both 1.2–1.3 dB). The block-extracted chain peaks at 339 MHz; the tile and the
schematic peak at ~447 MHz.

What it isn't:
- not regeneration: the tile has no peaking, and removing its 6.4 fF o1n–o2p coupling raises gain by 0.2 dB;
- not the devices: identical sizes, fingers, Cs MIM, loads and drain areas;
- not the total C: 836.4 vs 835.8 fF over all chain nodes;
- not the bias: o2 CM 1.119 vs 1.121 V;
- not resistance: shorting every one of the block extraction's 21 993 resistors leaves the step at 10.34 dB;
- not the layout: the XOR of `layout/lna_chain.gds` against the tile's copy is slivers (~0.03 µm² on contact layers).

What's left is how the C is split between nets. For example, the tile has much more C across each differential pair:
o3p–o3n 6.95 vs 0.82 fF, outp–outn 3.86 vs 0.44, o1p–o1n 13.3 vs 8.45. The tile sees the wiring over the chain
(the det taps, the straps). This is finding #5 again, now with resistance ruled out. Still open.

On the full GDS extraction at sf, 10.1 dB is 2.5σ above 9 dB with the block MC's σ (0.44 dB), so about 99 % by that
estimate. The MC itself hasn't been run on the full GDS extraction.

**Stability at sf 27 °C on the block extraction** (item 3's bench, real decap, L 2 nH, growth): the corner the
handoff's list missed.

| Strap | 0.5 fF | 0.75 fF | 1 fF | 1.5 fF | 2 fF |
|---|---|---|---|---|---|
| off | ok 5e-9 | ok 7e-9 | OSC 1.0 | OSC 1.0 | OSC 1.0 |
| on | ok 3e-9 | ok 3e-9 | ok 3e-9 | ok 3e-9 | ok 3e-9 |

Low gain takes the edge from 0.75–1 fF to above 2 fF, as at tt. The fallback works at sf even with the smaller step.

**A wider shunt, if 9 dB stays the spec** (Msw's 6 extracted fingers scaled by m, block extraction, step / dB):

| Msw W | tt 27 | ss 10 | ff 50 | sf 27 | fs 27 | Full-gain cost vs W 18 |
|---|---|---|---|---|---|---|
| 18 (as built) | 10.17 | 9.44 | 10.43 | 8.46 | 11.12 | 0 |
| 27 | 11.17 | 10.64 | 11.25 | 9.70 | 11.96 | −0.13 dB |
| 36 | 11.71 | 11.31 | 11.67 | 10.43 | 12.38 | −0.25 dB |
| 54 | 12.22 | 11.99 | 12.05 | 11.19 | 12.74 | −0.50 dB |

Strap-off NF changes by ≤ 0.01 dB. The cost is the device's own C only: a wider layout's wiring isn't in it.
W 36 clears 9 dB at every corner even on the block extraction (sf ~3σ).

**Verdict (Matt, 2026-11-06): pass on the full GDS extraction.** It would also pass with the spec relaxed slightly
(e.g. stated as the stability margin: low gain at least doubles the tolerable coupling, at every corner including
sf / fs, which W 18 meets; the 9 dB was a proxy for it). No redesign.

Work files (not in git): `build/whatif_sw/` (width sweep, sf stability, resistor tests), `build/tb_tile_cw_hyb_*`,
`build/tb_tile_ac_*` (tile AC sweeps), `build/tb_tile_cw_*sf_27*` (tile CW at sf).

## 5. Low-gain sensitivity at transistor level

### noise_tran (`sim/logdet/noise_tran.sh`, VGLO / TB / TAG)

Det mean, V. off − on = noise-only det − det at the level.

| Bench | Strap | Noise only | −84 | −86 | −88 | −90 | −92 | −94 |
|---|---|---|---|---|---|---|---|---|
| sch | off | 1.44445 (ref 1.439) | | | 1.44114 | 1.44222 | 1.44292 | 1.4434 |
| sch | on | 1.50983 | 1.50843 | 1.5089 | 1.5092 | 1.5094 | 1.50953 | |
| pex | off | 1.45566 | | | 1.4524 | 1.45344 | 1.45413 | 1.4546 |
| pex | on | 1.50965 | 1.50787 | 1.50846 | 1.50885 | 1.5091 | 1.50928 | |

off − on, mV: full gain −92 1.53 (sch) / 1.53 (pex); low gain −88 **0.63** (sch) / **0.80** (pex), −86 0.93 / 1.19,
−84 1.40 / 1.78. Low gain at −88 gives about half of full gain at −92, and less than full gain at −94 (1.05 / 1.06).

### Joined RX pair (`sim/top/tb_tile_joined.py pair`, extracted tile)

det off − on, mV, by window after key-on:

| Case | 1–5 µs | 5–10 µs | 10–20 µs | 20–30 µs | 2–30 µs |
|---|---|---|---|---|---|
| full gain, −92 dBm | 1.48 | 1.38 | 1.25 | 1.39 | **1.35** |
| low gain, −88 dBm | 0.57 | 0.53 | 0.52 | 0.55 | **0.54** |

This agrees with noise_tran.

### Mixed signal (RTL + transistor baseband, det from `gen_det.py --gain`)

The det waveform is calibrated to noise_tran: `sim/rx/lo_gain.py` gives `--gain` −12.26 dB (sch), so the
noise-only det is 1.5099 V against noise_tran's 1.5098 V.

**The first 50 runs (0 detections, servo at code 0) were a bench artefact.** It was fixed in `sim/mixed/gen_mixed.py`
(a903c95):
- the d_cosim / adc_bridge lost a slow comparator edge: one 0.9 V threshold plus a d2a probe on `comp_in`. See
  `docs/sim_learnings.md`; a minimal ngspice repro is a TODO;
- the lpf / avg `.ic` was the full-gain det level: it is now taken from the det waveform.

All mixed runs below and in item 2 use the fixed bench.

Event-open (detection), low gain, sch baseband:

| Level | Detected | Seeds |
|---|---|---|
| −84 dBm | 5/5 | 1–5 |
| −86 dBm | **19/20** | 1–20 |
| −88 dBm | **7/20** | 1–20 |
| −90 dBm | 16/20 | 1–20 |
| −92 dBm | 2/5 | 1–5 |
| no signal (−150 dBm) | **0/10** | 1–10 |

The det waveform from the extracted chain (`_lopex`, 5 seeds): −84 5/5, −86 5/5, −88 2/5, −90 4/5, −92 3/5.
Full gain (sch baseband, item 2): −92 dBm 5/5 seeds, −94 3/6.

Every detection lands at the burst end (14.64–14.70 ms), and the no-signal control is clean, so the events are real.

**FAIL** (detects at −88 dBm): 7/20. Low gain is reliable at −86 dBm (19/20).
- That is ~6 dB below full gain (−92), not the handoff model's ~4.5 dB (−88.5).
- noise_tran and the joined pair agree: the low-gain det difference at −88 is below full gain at −94.

**Open: the dip at −88.** −90 dBm (16/20) detects more often than −88 dBm (7/20) on the same noise seeds, though the
−88 det steps are twice as large (0.4 vs 0.2 mV on the waveform). Not explained. One untested idea: 0.4 mV is near
one trim LSB at the comparator, so the servo's ±1 LSB dither could partly cancel the signal at that level (the trim
node steps ~7 mV per code before the comparator's attenuation). If true, it is a property of the servo + comparator,
not of the strap, and it may also apply at full gain.

## 6. Extracted tile, vglo 1.8 / 0

`sim/top/tb_tile.py` (c), `--vglo=0` for the strap:

| | Strap off | Strap on | Reference (2026-10-13) |
|---|---|---|---|
| RX IDPWR | 2.98657 mA | **2.98657 mA** | 2.985 |
| det idle | 1.49148 V | 1.49148 V | – |
| det −60 dBm | 1.21516 V | **1.34888 V** (+134 mV) | 1.206 |
| comparator flip (DC scan) | – | codes 180 / 181 | – |

CW det drop at the pads, noise-free, trim held, mV:

| Level | sch off / on | c off / on | rc off / on |
|---|---|---|---|
| −100 | 0.50 / 0.04 | 0.61 / 0.04 | 0.61 / 0.04 |
| −90 | 4.92 / 0.32 | 5.94 / 0.39 | 5.97 / 0.39 |
| −80 | 40.11 / 3.11 | 46.71 / 3.85 | 46.93 / 3.88 |
| −70 | 169.49 / 27.22 | 165.14 / 32.86 | 165.62 / 33.07 |

**Pass**:
- the shunt draws no DC;
- in low gain −80 dBm lands near full gain's −90 (3.9 vs 5.9 mV): ~10–12 dB of detector curve;
- in square law, −100 → −90 dB steps are ×10 off and ×10 on.

Full-gain levels against the 2026-10-13 tolerances: item 2.

## 7. FasterCap, st5 / st6 Cs plates ↔ g1 corner

New scripts `sim/kpex/fccut.py` (met3 / via3 / met4 / capm cut of the flat chain, nets from the LVSDB) and
`sim/kpex/fcsum.py` (asymmetric coupling from the FasterCap matrix), commit 3cc0239.

| | This branch | Reference (`substrate_2026-10-29.md`) |
|---|---|---|
| kpex 0.4.4 upper bound, dm | +6.58 / −9.82 aF | 13.2 / 19.5 aF (older kpex) |
| FasterCap fine, dm → g1 | −0.19 aF | – |
| FasterCap fine, dm → inp / inn | −0.55 / −2.31 aF | – |

**Pass** (comes down, ≪ 50 aF). Caveats: no met1 / met2 in the cut; FasterCap 6.0.7 (< 6.0.9).

## 8. Substrate study (§2 rerun, re-flattened from this branch)

Scripts updated for the shunt (7ae9d06):
- `flatref.py` knows `lna_shunt`;
- `geom.py` skips pfets (n-well);
- `mknet.py` has the `lna_lo_n` port.

| | This branch | Reference |
|---|---|---|
| Equivalent Ccpl, every link | 1.44e-4 fF | 1.44e-4 fF (main) |
| Equivalent Ccpl, late stages | 1.19e-5 fF | 2.83e-5 fF |
| Strap on | ~3× higher | – |

**Pass, with a reading of the criterion.**
- The late-stage figure (1.19e-5 fF) meets "≤ 1e-4 fF".
- The every-link figure (1.44e-4 fF) is above 1e-4 taken literally, but it is identical to main's and the calibration
  matches the doc.
- Both are ~700× below the 0.1 fF coupling budget.

Matt to confirm which figure the handoff's criterion meant.

Rerun notes:
- the x86 uv include path;
- run `acx.sh` before `acvar`.

## 9. TT precheck

GitHub actions on 8a516b8: docs, gds (TT precheck) and lvs all succeed. On d0dfae4 lvs had failed only at the pinout
check, which is fixed. **Pass.**

## Harness fixes made during the run (not design)

| Commit | Fix |
|---|---|
| `xschem/gen/logdet.py`, `tb_logdet.sch` | `lna_lo_n` driven by `Vglo` (was floating) |
| port-list fallout | `pex_tile.sh`, `pdn_gds.py`, `power/common.py`, `tb_powerup.py`, `check_pinout.py`, `test/test.py` get `lna_lo_n` |
| 556dc85 | `sim/power/stitch.py`: the supply-port regex no longer assumes the netlist's line wrap (`pwr_tran_tx`) |
| a903c95 | `sim/mixed/gen_mixed.py`: `.ic` from the det level, one a2d threshold, `comp_in` probe |
| 240441a | `sched.py`: only one waiting long job reserves threads. Three did, and the queue sat at load 7 for ~7 h |

Fresh pod setup, needed before the run:
- `tools/pod_setup.sh`;
- `tools/kpcell_setup.sh`;
- `mag/tt_analog_3x2_3v3.def` from tt-support-tools;
- `sim/mixed/build_so.sh`, by hand, for the Verilator `.so`.

## Item 2. Full rerun against `verify_2026-10-13.md`

Run: `sim/rerun/jobs_lna_lo.py`, sim-0, 2026-11-04 14:12 → 11-05 21:27. 449 jobs: 425 `ok` (all rc 0), 24 `exited`.
This section covers only the 2026-10-13 jobs. The low-gain checks are written up separately.
Tags: **PASS** = within the doc's numbers. **CHANGED** = moved, with a known cause (the shunt, or another change
on this branch, named in the row). **FAIL** = moved with no known cause, beyond the doc's numbers.

**Verdict: PASS, with one FAIL and a few changes that need noting in the write-up.**

- **FAIL (overload):** the overload gap scan no longer has a single dead time. See Mixed signal.
- **CHANGED, not caused by the shunt:**
  - the decap AC numbers (the decap schematic was corrected 2026-10-17);
  - the power-delivery R / |Z| / TX→RX numbers, all better (router via arrays, 82b6462);
  - the 1.71 / 3.3 V extracted ss / fs TX points, back to their verify_supply_mc values.
- **CHANGED, caused by the shunt:** chain / det numbers. They move as predicted: about −0.7 dB on the extracted
  tile, about −0.25 dB on the schematic.

### `exited` jobs: log check (all 18 finished normally)

| Job | Last lines of the log | |
|---|---|---|
| joined_-90 / -70 / -10 | `done … 0 errors` (4.8 / 4.8 / 4.9 h); `build/joined_<lvl>.raw` complete to 400 µs | ✅ |
| pad_ovl_6 | the full summary is printed (pads, IDPWR, det, lpf) | ✅ |
| pwr_tran_tx | First run FAILED in 0.2 min (rc 1, the stitch.py port regex). After 556dc85 it was re-queued and ran 07:38 → 19:25 (adopted by a restarted scheduler); the block table and det / lpf / avg / trim / vcm lines are all printed | ✅ |
| pwrup_10m_tt27 / ss10 / ff50 | the full summary is printed (vcm, det / lpf / avg settle, TX, supply current) | ✅ |
| tile_cw_sch_c | the CW table for sch and c is printed | ✅ |
| tile_pair | code 181, the pair table, then the `--no-run` analysis | ✅ |
| tile_rc_fs50 | op_rx / op_off / −60 dBm / TX lines are printed | ✅ |
| tx_corners_pex | 5 corners × (ab, se) are printed | ✅ |
| tx_pex_v1.71_3.0_tt / _ss, tx_pex_v1.8_3.6_tt / _ss / _ff | 4 lines each (ab + se RESULT, antiphase, single-ended) | ✅ |

### Digital

| Check | Reference | Now | |
|---|---|---|---|
| RTL cocotb | 15/15 | 16/16 (+ `test_lna_lo_strap`) | PASS |
| GL | 15/15 | 16/16 (1210 s) | PASS |
| TT top RTL / GL | 4/4, 4/4 | 5/5, 5/5 (+ `test_lna_lo_strap`) | PASS |
| Formal prove | PASS | PASS (2139 s, run by hand; the job checks its status file) | PASS |
| Formal `raw_rx` | intended FAIL | not in either job list | — |
| Pinout | OK, 30 TT pins | OK, 30 TT pins, info.yaml = schematic = macro | PASS |
| export_vectors | bit-identical | bit-identical (`git diff --exit-code` rc 0) | PASS |
| e2e default | noise −94 5/5, −98 0/5; fading −90 5/5, −94 3/5; bursty −70 5/5, −86 3/5; 0 false | identical | PASS |
| e2e H135 tt | −94 27/48, −92 48/48 | 27/48, 48/48 | PASS |
| e2e H135 fs50 | −94 1/48, −92 45/48 | 1/48, 45/48 | PASS |

### Layout signoff

| Check | Reference | Now | |
|---|---|---|---|
| check_top | precheck PASS, KLayout 0, magic 0, LVS match, antenna 7 | precheck PASS, 0, 0, match, antenna 7; xor_gds: metal identical | PASS |
| check.sh, 24 blocks | DRC 0, antenna 0, LVS match | all 24: DRC 0 (magic + KLayout), antenna 0, LVS match | PASS |
| pex.sh, 14 blocks | done; netlists = committed except names / order | done. `git diff --stat` shows name / order churn only (± equal line counts), and the block tests give the committed numbers | PASS |
| pex_tile rc | 17,994 C, 84,733 R, no missing ports | 17,907 C, 84,365 R (−0.5 % / −0.4 %), missing ports [] | CHANGED (re-route) |
| pex_tile lvs / c | — | 1139 X/M, 70 ports, missing [] (c: 3111 C) | PASS |

### Analog per block (tt)

| Block | Reference sch / pex | Now sch / pex | |
|---|---|---|---|
| amp_dp | 14.74 dB 1.525 mA / 15.58 dB 1.510 mA | 14.74 / 1.525; 15.58 / 1.510 | PASS |
| amp_dpc | 13.59 dB 0.723 mA / 13.69 dB 0.716 mA | 13.59 / 0.723; 13.69 / 0.716 | PASS |
| det_cell | 1.7498 V, 6.64 mV / 1.7515 V, 5.57 mV | identical | PASS |
| log_det | 1.5197 V / 1.4888 V, −1.46 mV | 1.5197 / 1.4888, −1.46 | PASS |
| lpf_rc | 14.75 kHz −89.4 dB / 14.65 kHz −106.9 dB | identical | PASS |
| avg_sc | τ 0.458 ms −0.015 mV / 0.423 ms +0.070 mV | identical | PASS |
| r2r | 0.000 LSB 24.6 ns / ≤ 0.021 LSB 30.6 ns | 0.000, 24.59 / 0.021, 30.58 | PASS |
| bias_gen | 59.36 / 59.31 µA (−0.08 %) | identical | PASS |
| dbg_tg | 0.53 / 4.11 / 1.13 kΩ / 0.57 / 4.14 / 1.15, off −73.5 dB | identical | PASS |
| tx_ring | 485.5 / 530.1 MHz | identical | PASS |
| tx_ls | 43.4 %, 45.7 / 50.5 % / 36.4 %, 41.4 / 48.3 % | identical | PASS |
| tx_ls_en | 1112 / 1380 ps / 3574 / 3808 ps | identical | PASS |
| tx_drv | P_dip +5.49 dBm (pex) | +5.49 | PASS |
| comp_ct | −7.51 mV, 0.1344, code 183.9 / −7.63 mV, 0.1359, 184.1 | −7.508, 0.1344, 183.9 / −7.626, 0.1359, 184.1 | PASS |

| Other analog | Reference | Now | |
|---|---|---|---|
| Chain stability tt / ss10 / ss10 1.89 V | stable to 0.1 fF; 1 fF rings (growth ~0.99); 85.2 dB at ss 10 °C 1.89 V | stable to 0.1 fF (growth ≤ 4e-10); 1 fF growth 0.992 (tt) / 0.988 (ss10); ss10 1.89 V 2n:0 **84.89 dB** at 434 MHz (peak 85.05) | CHANGED: −0.3 dB (shunt, schematic). Now uses the real 10.6 pF decap (2026-10-17) |
| decap AC | VAPWR 50.06 pF, VDPWR 29.91 pF, flat ±10 % | **VAPWR 42.63 pF** (ESR 0.010 Ω), **VDPWR 10.56 pF** (0.18 Ω), flat to 434 MHz and ±10 % | CHANGED, not the shunt: eaa6953 (2026-10-17) made the decap schematics the laid-out devices. Matches verification.md (42.6 / 10.6) |
| bias OTA loop | PM 90–91.5° | PM 89.99–91.50° (15 points) | PASS |

### Corners, temperatures, supply

| Item | Reference | Now | Δ | |
|---|---|---|---|---|
| RX 10 / 50 °C: current | 2.84–2.91 mA | 2.84–2.91 | 0 | PASS |
| gain at 434 MHz | 73.3–81.2 dB | 73.1–80.9 | −0.2 / −0.3 | CHANGED (shunt, sch) |
| NF | 9.4–12.0 dB | 9.4–12.0 | 0 | PASS |
| det idle | 1.499–1.535 V | 1.499–1.535 | 0 | PASS |
| slope | 10.0–14.1 mV/dB | 9.8–14.0 | −0.2 / −0.1 | CHANGED (shunt) |
| comp offset at mid-trim | −5.7…−9.0 mV | −5.7…−9.2 (ss rows reach −1.0 at the CM edge, as before) | ~0 | PASS |
| trim span | ~−14 / +6…+10 mV | −13.3…−14.5 / +5.7…+10.5 | ~0 | PASS |
| step at 10 / 50 °C | 0.136–0.147 mV/LSB | 0.136–0.147 | 0 | PASS |
| sf, CM 1.55 V | no threshold (known) | no result (known) | | PASS |
| Extracted tile rc: det idle fs50 / ss10 / ff50 | 1.500 / 1.502 / 1.475 V | 1.4998 / 1.5022 / 1.4752 | 0 | PASS |
| det at −60 dBm | 1.236 / 1.178 / 1.261 V | 1.2442 / 1.1840 / 1.2683 | +8.2 / +6.0 / +7.3 mV | CHANGED (shunt, ≈ 0.5–0.7 dB of slope) |
| TX | 530 / 427 / 588 MHz, +2.91 / +3.45 / +2.29 dBm | 530.4 / 427.1 / 587.6, +2.91 / +3.45 / +2.29 | 0 | PASS |
| rc 50 °C | +2.67 dBm | +2.66 dBm (520.8 MHz) | −0.01 | PASS |
| TX sch tt ss ff sf fs | +4.14 / +4.26 / +4.14 / +4.23 / +4.14; SE −2.2…−2.6 | identical; SE −2.16…−2.64 | 0 | PASS |
| TX extracted | +3.66…+3.85; SE −2.6…−3.3 | +3.66…+3.85 (3.72 / 3.85 / 3.66 / 3.82 / 3.72); SE −2.58…−3.25 | 0 | PASS |
| Tile TX 10 / 50 °C | +4.41…+4.55 / +3.75…+3.89 | +4.41…+4.55 / +3.75…+3.89 | 0 | PASS |
| TX supply, schematic (8 points × 5) | = verify_supply_mc 2.1; ss 1.71 / 3.6 FAIL | every value identical; ss 1.71 / 3.6 FAIL | 0 | PASS |
| TX supply, extracted (9 × 5) | = supply_mc, but ss / fs at 1.71 / 3.3 **+1.79 / +1.77** | all identical to supply_mc, incl. ss / fs 1.71 / 3.6 FAIL; ss / fs 1.71 / 3.3 **+2.22 / +2.21** | **+0.43 / +0.44 dB** | CHANGED, not the shunt (TX path untouched). Back to the supply_mc values. 2026-10-13 ran these as one 5-corner process, now one process per corner. These are the marginal `tx_ls_en` points (finding #2), and 1.71 V doesn't occur on the board |
| Analog top over supply (6 points) | = supply_mc (−60 dBm 1.166 / 1.247 / 1.121 / 1.194 / 1.341) incl. ss 1.71 / 3.6 TX FAIL | I, vcm, det idle, off, TX identical; −60 dBm 1.1699 / 1.2516 / 1.1243 / 1.1977 / 1.3440; ss 1.71 / 3.6 FAIL | +3…+5 mV at −60 dBm | CHANGED (shunt, sch). Note: ss10 1.71 / 3.0 now prints "off in nan ns" (supply_mc: 18 ns, slow) |

### Mismatch

| | Reference | Now | |
|---|---|---|---|
| comp_ct MC, 6 corners CM 1.5 | 100 % ≤ 0.19 mV/LSB, σ 2.1–2.5 mV, code 170–182 ± 16–20, max 238, no dups | 100 %, σ 2.16–2.51, code 172–181 ± 17–20, max **239** (ss10), 0 dups | PASS (new random seeds each run) |
| comp_ct sf 10 / sf 27, CM 1.45 | 99.5 % / 100 %, code 135 / 148 | 99.5 % / 100 %, code 135 / 151 | PASS |
| avg_sc tt 27 | −0.024 ± 0.143 mV, a 0.0280 | −0.023 ± 0.143, a 0.0280 (fs50 −0.011 ± 0.134, sf10 −0.074 ± 0.157) | PASS |
| lna_chain, 20 samples | 75.9–77.0 dB | the old job (`mc_chain`) is gone, replaced by `mc_chain_*` (reported separately) | not compared |

### Mixed signal (the fixed bench: 0.9 V a2d, comp_in d2a probe, .ic from det)

The full-gain det waveforms are unchanged (`gen_det.py` gain 0; the shunt doesn't enter). Every difference here
comes from the bench or from noise.

| Level | Reference | Now | |
|---|---|---|---|
| −70 dBm | 14.675 ms | 14.678 | PASS (+3 µs) |
| −90 dBm | 14.650 ms | 14.670 | PASS (+20 µs; inside the doc's −92 seed spread of 31 µs) |
| −92 sch, base + 5 seeds | 6/6 (14.642–14.673) | **5/5 seeds** (14.667–14.670). The schematic −92 base is in neither job list and wasn't run | PASS |
| −92 pex, base + 5 seeds | 6/6 (14.645–14.680) | 6/6 (14.661–14.668) | PASS |
| −94 sch / pex (information) | 2/6 / 2/6 | 3/6 (s1, s2, s3) / 1/6 (s3) | PASS (statistics of 6) |
| −70 trim bits swapped | PIN ORDER PROBLEM | PIN ORDER PROBLEM (586 steps of ±2) | PASS |
| Pin order, every other run | OK | OK (≤ 1 extra ±1 step) | PASS |
| Servo | code 177–180, σ 2.6–4.6, settled 0.66 / 0.69 ms | sch 177.0–177.9, pex 179.3–179.8, σ 2.2–4.5; base 0.66 / 0.69 ms, seeds 0.66–0.71 / 0.69–0.77 | PASS |

**Overload** (weak-burst event, ms):

| gap ms | 0.1 | 0.25 | 0.3 | 0.4 | 0.5 | 1 | 2 | 5 |
|---|---|---|---|---|---|---|---|---|
| 2026-10-13 | missed | missed | 28.173 | 28.275 | 28.380 | 28.875 | 29.887 | 32.866 |
| now | **27.981** | **28.138** | **missed** | **missed** | **missed** | 28.893 | 29.879 | 32.866 |

**FAIL (unexplained).** The scan no longer has one dead time: 0.1 and 0.25 ms now detect, and 0.3–0.5 ms now
miss.
- **Not a lost edge:** in the 0.25 / 0.3 / 0.5 raws, `v(comp)` and the d2a probe `comp_in_a` never disagree
  for longer than one time step.
- **The servo track is the same in every run:** it goes down to code 67–70 about 1.3 ms after the strong burst,
  then climbs back. So the misses sit on a marginal −90 dBm burst that spends ~3 ms of its 13 ms off balance.
- **Likely cause:** the bench change (one 0.9 V threshold instead of 0.6 / 1.2 V) moves which chips land while
  the servo is low.
- **Needs:** seeds per gap before finding #13 ("dead time 0.25–0.3 ms") is restated.

### Extracted tile and joined RX

| Run | Reference | Now | Δ | |
|---|---|---|---|---|
| tile lvs | 2.987 mA, +3.07 dBm 680 MHz | 2.987, +3.07, 679.6 | 0 | PASS |
| tile c | 2.987 mA, 0.910 µA, det 1.4915, −60 dBm 1.207 V, +3.38 dBm 537 MHz | 2.987, 0.910, 1.4915, **1.2152**, +3.38, 537.3 | −60: +8.2 mV | CHANGED (shunt) |
| tile rc | 2.985 mA, det 1.491, −60 dBm 1.206 V, +3.13 dBm 519.3 MHz | 2.985, 1.4912, **1.2142**, +3.13, 519.3 | −60: +8.2 mV | CHANGED (shunt) |
| CW tile sch, −100 / −90 / −80 / −70 dBm | 0.53 / 5.20 / 41.94 / 173.14 mV | 0.50 / 4.92 / 40.11 / 169.49 | −0.25 / −0.24 / −0.19 dB (−70 compressed) | CHANGED (shunt, sch) |
| CW tile c | 0.71 / 6.96 / 52.79 / 172.84 | 0.61 / 5.94 / 46.71 / 165.14 | −0.66 / −0.69 / −0.53 dB | CHANGED (shunt, extracted) |
| CW tile rc | 0.72 / 7.00 / 53.05 / 173.36 | 0.61 / 5.97 / 46.93 / 165.62 | −0.72 / −0.69 / −0.53 dB | CHANGED (shunt, extracted) |
| cw_drop blocks pex | 0.31 / 3.14 / 27.71 / 133.69 mV | 0.26 / 2.67 / 24.03 / 123.59 | −0.76 / −0.70 / −0.62 / −0.34 dB | CHANGED (shunt) |
| log region (−84…−72, pex − sch) | −2.20…−1.39 dB | −2.66…−1.69 | −0.3…−0.46 | CHANGED (shunt, extracted − sch difference) |
| lna_chain only / log_det only (−90) | −0.25 / −1.98 dB | **−0.73** / −1.99 | −0.48 / −0.01 | CHANGED (shunt: pex 0.65–0.8 minus sch 0.25–0.3) / PASS |
| Tile scan | flips 180 / 181 | 180 / 181 | 0 | PASS |
| Tile pair −92, 2–30 µs | det 1.41 mV, LPF 0.90; model 1.14 | det 1.35, LPF 0.86 (windows 1.25–1.48) | −0.06 mV (−4 %) | CHANGED (shunt, smaller than the gain loss's ~−15 %; within the window spread) |
| Joined −90 (sch) | 1.43 mV, model 1.80 | **1.83 mV** (LPF 1.04), model 1.80 | +0.40 mV | PASS: inside the ±0.5 mV 1σ of a two-chip window (verification.md). The shunt alone would give ~−6 % |
| Joined −70 | 100.8 mV, model 105.6 | 100.75 (LPF 99.8), model 105.6 | −0.05 | PASS |
| Joined −10: det | 1.4512 → 0.5637 V | 1.4533 → 0.5694 V (my windows: 20–60 µs off; chips with 2 µs settle) | +2.1 / +5.7 mV | CHANGED (shunt: less noise / swing at det; window method may differ from the doc's) |
| Joined −10: comparator | rises 60.15 / 269.22, falls 191.26 / 392.65 µs | rises 60.28 / 269.24, falls 190.65 / 392.58 | ≤ 0.61 µs | PASS (doc: within 1 µs) |

Not a reference item, but worth a look: `tile_rc_10` `op_off` IDPWR is **9.11 µA**, against 0.908 µA for
`tile_c_10` at the same temperature. `tile_rc_fs50` reads 1.517 µA. In both, the off OP needed true gmin stepping
(see `build/tb_tile_rc_tt_10.log`). It looks like a second DC solution of the off OP, not a real leak.

### Power-up, pad overload, power-off

| Item | Reference | Now | |
|---|---|---|---|
| Fast ramp c, tt / ss10 / ff50: LPF / avg settle | 1.49–1.50 / 2.65–2.66 ms | 1.491 / 1.504 / 1.491; 2.648 / 2.661 / 2.648 | PASS |
| \|tx_p\|, end current | 48 / 286 / 16 mV; 2.985 / 3.017 / 2.945 mA | 48.3 / 286.4 / 15.8; 2.985 / 3.017 / 2.945 | PASS |
| Slow ramp: vcm 95 %, LPF, avg | 6.26 ms, 0.64–0.67, 2.08–2.09 (ff similar) | 6.259 / 6.258 / 6.260; 0.666 / 0.640 / 0.692; 2.090 / 2.077 / 2.116 | PASS |
| Schematic fast ramp | done | done (LPF 1.569, avg 2.726 ms, 2.972 mA) | PASS |
| VDPWR only | 0.910 / 0.907 / 1.015 µA | 0.910 / 0.907 / 1.015 | PASS |
| VAPWR only | ≤ 16 nA, tx = 3.3 V | 1.8 / 0.5 / 16.4 nA, tx 3.3 V | PASS |
| Pad 0 dBm | ±0.296 V | −0.293…+0.296 V, det back 0.2 µs | PASS |
| Pad +6 dBm | ±0.59 V, 1.156 V diff, 11.65 mA, vcm 1.2012, det back 0.3 µs | ±0.59, 1.155, 11.65, 1.2012 / 1.2012, 0.3 µs | PASS |

### Power delivery (case A)

| Item | Reference | Now | |
|---|---|---|---|
| R chain VDPWR / VGND | 5.70 / 6.96 Ω | **2.92 / 4.40** | CHANGED, not the shunt: router via arrays (82b6462: RX trunk vias were single cuts). Better |
| R tx_drv_p | 0.77 / 0.81 | 0.77 / 0.81 | PASS |
| R comp_ct | 8.85 / 8.23 | 8.94 / 8.20 | PASS |
| R avg_sc | 11.87 / 14.36 | 11.96 / 14.34 | PASS |
| IR at tx_drv_p, VAPWR / VGND (avg / peak) | 5.6 / 18.7, 2.7 / 16.3 mV | 5.6 / 18.7, 2.7 / 16.3 | PASS |
| EM VAPWR via4 / met4 / mcon; VGND | 42.4 / 28.8 / 71.2 %; 40.1 / 39.8 % | identical | PASS |
| \|Z\| (power.md "fix": chain 21.7 / 20.0, comp_ct 24.3 / 23.1, avg_sc 24.9 / 23.7 Ω at 77 k / 434 M) | flat to 500 MHz | flat; chain 16.65 / 15.38, comp_ct 20.54 / 19.35, avg_sc 22.76 / 21.56, log_det 31.66 / 30.43 | CHANGED (via arrays; lower) |
| TX → log_det at 434 MHz | 0.068 Ω | **0.020 Ω** (all RX blocks 0.019–0.021; were 0.015–0.069) | CHANGED (via arrays; lower) |
| TX keyed: tx_drv_p p-p (434 MHz) / tx_drv_n | 29.21 (1.43) / 19.55 mV | 29.08 (1.43) / 19.25 | PASS |
| RX blocks dd p-p / 434 MHz | 7.4–7.7 / 0.21–0.22 mV | **5.96–6.16** / 0.21–0.22 | CHANGED (via arrays; 434 MHz part unchanged) |
| det at 434 MHz | 3.47 mV | 3.48 | PASS |

Side note: the rerun's `plot_mixed.py` runs rewrote five tracked plots (`sim/plots/mixed_-70 / -90 / -94 /
-94_pex / -92_pex.png`, modified in the working tree).
