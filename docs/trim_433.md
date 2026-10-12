# Stretch goal: record and replay a 433.92 MHz fixed-code fob

Work plan with review gates: [plan_ring_tune.md](plan_ring_tune.md).

What it would take to record a garage-door fob with the RX and replay it with the TX so a commercial receiver
accepts it. **No new sims were run.** Every number here comes from results already in the repo (PLAN.md,
docs/history.md, STATUS.md, bench/data). Estimates are marked *(est.)*.

Scope: **fixed-code** fobs only (PT2262 / EV1527 / CAME / Nice-style 12–24 bit codes). Rolling-code fobs
(KeeLoq, Somfy RTS, most cars) reject replays by design (PLAN "Stretch").

## Summary

| | Today's silicon | What's missing |
|---|---|---|
| **Record** (RX) | Works. The RX is wideband (330–560 MHz), so it hears a 433.92 fob with no tuning. The raw comparator bit is already on `uio[3]` in every mode, synchronised to the 10 MHz clock. | Nothing essential. Software on the RP2350 has to clean up the noise in the gaps between frames. Optional digital tweak: a slower slicer average in raw mode. |
| **Replay** (TX) | Keying works: raw TX mode, `uio[2]` drives `tx_en` combinationally, so RP2350 PIO timing passes straight through. | **The carrier frequency.** Predicted ~459 MHz (+5.8 %), with a process window of roughly 430–613 MHz. A superhet receiver needs ±0.1 MHz. Fixing it needs a ring trim (analog), a way to measure the ring (analog + digital), and a way to load the trim (digital). |

The record side is done. The whole job is landing the TX carrier within ~±100 kHz of 433.92 MHz.

## 1. How accurate the TX has to be

| Receiver type | Acceptance window *(est., typical parts)* | Untrimmed ring (459 MHz) |
|---|---|---|
| Superheterodyne (SAW LO + 10.7 MHz ceramic IF, or SYN4xx / MICRF2xx-class ICs) | about ±100–150 kHz (≈ ±0.03 %). Fob SAW resonators are ±75 kHz, and the receiver's window is sized for that. | No chance: 25 MHz off gives ~36 MHz IF, outside the IF filter. |
| Super-regenerative (cheap gate / garage receivers, LC tank, Q ~50–100) | −3 dB about ±2–4 MHz | Might work at short range: 25 MHz off is about 20·log(2·Q·Δf/f) ≈ **−19 dB** at Q 75. +3 dBm at 0.5 m is ~−16 dBm at the receiver, far above a ~−100 dBm sensitivity. |
| Regulatory (EU SRD 433.05–434.79 MHz) | 433.92 ± 0.87 MHz (±0.2 %) | Outside the band. 459 MHz is licensed land-mobile spectrum, so transmitting there over the air isn't legal. |

**Target: ±100 kHz (±230 ppm).** That means trim steps of ≤ ~20 kHz (so drift has the margin) and measuring
the frequency to ≤ ~10 kHz.

### Where the ring will land untrimmed (from existing data)

- Extracted tile, tt, RC: **520–530 MHz** (23 stages, nand + 22 × inv_2).
- The ttsky25b ring measured **0.866 ×** its extracted-tt value: **~459 MHz** if this lot is like that one.
- Corner spread from the ttsky25b re-sim (history.md "TX ring frequency calibration"): ss 0.828 ×, ff 1.134 × tt.
  That gives **~439 MHz (ss) … ~601 MHz (ff)**.
- Temperature, sim: +0.5 % from 27 to 60 °C (≈ +66 kHz/°C). Bench hot air: −0.11 %. Call it ±0.3 % over 10–50 °C.
- Supply: same chip on different boards **~1.5 %** (bench). *(est.)* A std-cell ring moves ~0.5 %/10 mV of
  VDPWR, so that 1.5 % is ~30 mV between boards.
- **Overall untrimmed window ≈ 430–613 MHz.** To hit 433.92 MHz the tuning has to cover **×0.71 to ×1.01**.
  With the current 23-stage ring the slowest silicon may already be just *below* 433.92, which no amount of
  slowing can fix.
- **No trim at all:** `NINV` 22 → ~459 MHz (+5.8 %); 24 → ~422 MHz (−2.7 %). NINV has to stay even (odd
  inversions with the nand). 24 is closer: a superregen would be ~12 dB down instead of ~19. Neither is in
  the band.

### Stability after trimming (bench, PLAN "What phase 0 measured")

| Term | Size | Fits ±100 kHz? |
|---|---|---|
| Settled jitter | 45 kHz std, ±50 kHz wander | Yes, roughly |
| Temperature | ~66 kHz/°C (sim) | Only if recalibrated just before the replay (a 25 ms job, see §3) |
| Turn-on chirp | Measured −3.8 MHz for 20–40 µs on the 1.8 V-driver ring. The 3.3 V driver cut the VDPWR step from ~10 mA to ~0.2 mA. *(est.)* ~50× smaller, ~−80 kHz | Yes. It goes away entirely if the ring free-runs and only the arms are keyed (§4). |
| VDPWR drift / ripple | ~0.5 %/10 mV *(est.)*; board regulator spurs at ±2.8 MHz measured | **The main risk.** 2 mV of slow drift is ~0.1 % (430 kHz). Calibrating under the same load right before the replay cancels slow drift but not ripple. An on-chip ring LDO (PLAN "Stretch") is the robust fix, but it's a much larger analog job. |

Conclusion: a trimmed ring that is recalibrated right before each replay should reach superregen receivers
reliably, and superhet receivers probably, as long as the board's VDPWR is quiet.

## 2. Analog side: the ring trim

The ring is 23 std-cell stages with ~11 fF per node (3.2 fF wiring + inv_2 gate + drain), ~250 fF in total.
It has to tune over ~×0.65–0.92 and step by ~0.005 % (~20 kHz). One knob can't do both, so use two.

### Coarse: ring length select (digital, std cells)

- Shorten the base ring and add a tail. Build a chain of ~30 inv_2 with taps after inverter 20, 22, 24, …, 30.
  A small std-cell mux (2 × mux4 + mux2, or one mux8 tree) picks the tap that feeds the nand's B input.
  Taps have to be 2 inverters apart to keep an odd number of inversions.
- Steps are ~1/N per 2 stages, **~6.5–9 % each**. Six taps cover ~×1.0 → ×0.68.
- The mux adds ~3–4 inverter delays *(est.: mux4 ~150 ps vs ~41 ps per stage at 530 MHz)*, so the tap set
  has to be rescaled in sim. Choose taps so that the **shortest tap is ≥ ~470 MHz at ss 10 °C on silicon**
  (×0.866 applied) and the **longest is ≤ ~420 MHz at ff 50 °C**.
- Control: 3 bits from the macro (`ring_sel[2:0]`).

### Fine: varactor loads driven by the existing R2R DAC

- In the TX role the RX trim DAC (`r2r`, 8 bits, 0–1.8 V, ~10.6 kΩ Rout) is idle. The servo only steps on
  `rx_tick`, so it sits at 128. **Reuse it.** Branch the `trim` net through an RC filter to the tuning node
  of a few MOS varactors (`sky130_fd_pr__cap_var_lvt`) hung on ~4–6 ring nodes. In RX the extra branch is
  inert: the ring is off, and the comparator input is unchanged apart from a little more C on `trim`, which
  already has Ctrim = 1 pF.
- Fine range has to exceed the biggest coarse step with margin: **~10–12 %**. That needs ΔC_total ≈ 0.11 ×
  250 fF ≈ **30 fF**, so ~5–8 fF of tuning per node over 4–6 nodes. *(est.)* The node swings rail to rail,
  so the varactor's C(V) gets averaged and its effective tuning ratio drops to about half of the DC curve.
  Size it in sim. Kvco ≈ 11 %/1.8 V ≈ 6 %/V ≈ 26 MHz/V at 434.
- **Resolution:** 8 bits over 11 % is 0.043 %/LSB ≈ **190 kHz**, too coarse, especially since Kvco is
  nonlinear and some local steps will be 2× that. So add **first-order ΣΔ dither on the DAC LSB** in the
  macro (4 extra bits → 12-bit effective, **~12 kHz** steps).
  - The filter: **R ≈ 1 MΩ** (xhigh poly) + **C ≈ 2 pF** (MOS cap; the varactors add to it), τ ≈ 2 µs.
    The ripple from 10 MHz dither is ~7 mV × 100 ns / 2 µs ≈ 0.35 mV, i.e. ~9 kHz of FM at 10 MHz
    (β ≈ 0.001, negligible). Settling is ~10 µs, well before the first key edge.
- Linearity and monotonicity barely matter: the loop is closed by measuring (§3).

**Rejected alternatives:**
- A switched-capacitor bank only (all digital). The fine unit would be ~0.1 fF (0.04 % of 250 fF), too small
  to switch reliably.
- A current-starved stage. It shifts the ring output's duty cycle, and the tx_ls / tx_drv p arm already lost
  1.5 dB to duty (history.md "TX loss split").
- Tuning VDPWR from the board. This is the only no-silicon-change knob, worth ~±8 % over 1.62–1.98 V
  *(est.)*. But the digital runs on VDPWR too, the TT demo board's 1.8 V isn't meant to be adjusted, and at
  ~230 kHz/mV it would need sub-mV stability.

### Ring measurement: a divider

- Put a ripple **÷256** (8 toggle flops, std cells) on the ring output next to the ring: ~1.7 MHz at 433.92
  and ~2.6 MHz at the fastest tap. That stays under the 5 MHz Nyquist rate of the macro's 10 MHz 2-flop
  synchroniser.
  - The first flop has to toggle at up to ~670 MHz at ff. sky130 hd flops should manage that, but it needs a
    check in sim.
  - Its load is permanent, so it's part of what gets calibrated.
- Output `ring_div` goes to the macro: 1 new input pin.

### Separate ring and arm enables

Today `key = en_p = tx_en` (`xschem/gen/top.py`). A separate **`ring_en`** from the macro, with `key` on
`ring_en` and `en_p` / `en_n` keyed as now, lets the ring run silently during calibration (arms parked low, no
radiation). It also lets the ring **free-run through the whole replay with only the arms keyed**.
- This removes the turn-on chirp, and VDPWR load stays constant through the replay (the arms are on VAPWR).
- The enable path already keys with 8 ns edges (history.md), which is fine for fob bit rates.
- Cost: ring + tx_ls current (~1–2 mA *(est.)*) for the length of the replay. The off-state carrier leaks
  through the parked arms; *(est.)* > 40 dB down, which a fob receiver's slicer ignores. Check it in the
  tile sim.

### Area and integration

- About **< 1k µm²** *(est.)*: ~10 extra inv_2 + mux ~150 µm², varactors ~50, 1 MΩ xhigh poly ~200,
  2 pF MOS cap ~250, divider ~200.
- The tile is at 93 % with ~8k µm² of slack, and most of this goes in the TX corner next to `tx_ring`.
- New routes: `ring_sel[2:0]`, `ring_en`, `ring_div` (macro ↔ TX corner), and the `trim` branch from the
  `r2r` to the ring. The r2r sits on the RX side, so check the route length / coupling to RX nodes.
- **This changes `tx_ring` and the tile**, so the TX corner re-opens: `layout/gen/tx_ring.py`, DRC / LVS,
  `tb_tx_ring --pex` across taps × corners, then `tb_tx`, the tile build, `tb_tile.py lvs/c/rc`,
  `export_tt.sh` and precheck. That's the same rework STATUS "Next steps 1" already flags for a `NINV`
  change, plus the new blocks.

## 3. Digital side

### Raw RX (record): no change needed; optional tweaks

- `uio_out[3]` = `comp_s2` in all modes. The RP2350 samples it with PIO, or timestamps its edges, at
  ≤ 1 µs resolution.
- Front-end bandwidth: LPF 14.65 kHz (10–90 % ≈ 24 µs), comparator 0.36 µs at 1 mV overdrive, 100 ns
  synchroniser. Fob time units Te ≈ 300–500 µs (pulses 1 Te or 3 Te, sync gap ~31 Te ≈ 10–15 ms) are
  10–20× slower than all of that.
- **The slicer is AC-coupled.** The threshold is the switched-cap average of the LPF output (τ ≈ 0.42 ms,
  extracted), servoed to 50 % ones. That suits a Gold code, but for a fob:
  - **Long pulses droop.** Starting from a mid-level average, a high pulse of width W keeps a margin of
    0.5 · swing · e^(−W/τ).
    - At −70 dBm (swing 137 mV, slicer.md) a 1.2 ms '1' ends with ~4 mV of margin, comparable to the
      noise, so its tail may break up or end early.
    - At −50 dBm (fob within ~1–2 m) the swing is larger and the limited chain's envelope is clean, so the
      margin is fine.
    - Practical rule: **record close (> ~−55 dBm, ≲ 2 m)**.
  - **Gaps fill with noise.** After ~3τ ≈ 1.3 ms of carrier-off the average has sunk to the noise floor, and
    the comparator chatters at ~50 % with ~10 µs correlation time, through the inter-frame sync gap.
    - A software glitch filter of ~100–150 µs removes it. *(est.)* A noise high-run of 150 µs
      (~13 correlation times) turns up only every ~0.1–1 s, and the frame's repetition rejects those.
  - The trim servo keeps running in raw mode. Its ±40-code wander during strong bursts (history.md) is
    ±3 mV, which doesn't matter at fob signal levels.
- **Optional digital-only improvement:** in raw mode run `sc_phi1/2` once every 4 ticks instead of every
  tick. That makes τ ≈ 1.7 ms (the average's τ scales with the switch period), so the end-of-1.2 ms margin
  goes from ~3 % to ~25 % of the swing. Hold drift is negligible (avg_sc v2: +0.07 mV over 20 cycles).
  Cost: a 2-bit counter and a gate in the sc phase logic.
- **Alternative path:** the debug strap puts `det` on `ua[2]`. An external ADC or scope plus a software
  peak/valley slicer with squelch is the slicer bench/rx_model.py found best over the full range.

### Raw TX (replay): needs a frequency register, ΣΔ, measurement path

Minimal set, all in `radio_digital`:

1. **Config load in raw TX mode.** `ui_in[6:0]` are unused in raw mode, and the RP2350 can drive `ui_in`
   with the DIP switches off. Use `ui_in[0]` = shift clock, `ui_in[1]` = data, `ui_in[2]` = latch (through
   the existing `code_s1/s2` synchroniser, edge-detected) into a 16-bit register:
   `{ring_free, ring_sel[2:0], fine[11:0]}`.
2. **`trim_out` mux plus ΣΔ:** `trim_out = role_tx ? fine[11:4] + carry : servo_trim`. The carry comes from
   a 4-bit accumulator adding `fine[3:0]` every clock; saturate at 255.
3. **Enables:** `ring_en = raw ? (ring_free | uio_in[2]) : tx_code_en`. Arms keep `tx_en` / `tx_en_n`
   as now. Code mode is unchanged.
4. **Measurement:** synchronise `ring_div` (2 flops). Pick one:
   - **(a) Recommended, smallest:** put it on `uio_out[6]` in raw TX (it's the RX trim direction, unused in
     TX). The RP2350 counts edges with PIO against its crystal (±30 ppm, plenty). Calibration lives in
     MicroPython.
   - **(b) On-chip counter:** gate = 256,000 clocks (25.6 ms). Then **count = f / 10 kHz directly**
     (433.92 MHz → 43392): a 16-bit counter + an 18-bit timer, read back serially over a uio pin.
     Accuracy is the RP2350's 10 MHz clock either way, so (a) gives the same answer with ~35 fewer flops.
5. Optional: the raw-RX `sc_phi` ÷4 from above.

Size *(est.)*: ~25 flops + adder/mux ≈ 1.2–1.8k µm² placed. The macro is at 82 % utilisation on
200 × 220 µm (190 failed to route), so expect **210 × 220**, about 2.2k µm² out of the analog's slack.
Five new pins on the E edge: `ring_sel[2:0]`, `ring_en`, `ring_div`. Re-harden, re-run RTL and GL cocotb,
and add tests for the config shift, ΣΔ average and enables. Update `PIN_ORDER.md`, the floorplan and the
tile routes.

### RP2350 firmware (no silicon)

1. **Record:** raw RX. PIO captures edges on `uio[3]`. Glitch filter (~120 µs), estimate Te (histogram of
   pulse widths), quantise to 1/3 Te, find the sync gap and check that ≥ 3 consecutive frames match. Store
   the code as a pulse list (like rtl_433's flex decoder).
2. **Calibrate:** raw TX, `ring_free = 1` with the arms off. Binary-search `ring_sel` then `fine` against
   the PIO count of `ring_div` until it reads 433.92 MHz ± 10 kHz (~16 measurements × 25 ms ≈ 0.4 s).
   Repeat before each replay (temperature ~66 kHz/°C).
3. **Replay:** keep the ring running, PIO keys `uio[2]` with the clean, re-synthesised pulse list, and
   repeats the frame 5–10 times the way a fob does while held.

## 4. Options by effort

| Option | Silicon change | Gets you |
|---|---|---|
| **0. Nothing** (or `NINV` 24, ~422 MHz) | none / one parameter | Recording works. Replay *might* trigger a super-regenerative receiver at < 1–2 m. Not in the ISM band, and no superhet. |
| **1. Digital only** | macro: raw-RX `sc_phi` ÷4 | Cleaner recordings. Replay unchanged. |
| **2. Full trim** (§2 + §3) | `tx_ring` v2 (taps + mux + varactors), RC filter, ÷256, `ring_en`; macro config / ΣΔ / pins; tile re-route | Calibrated 433.92 ± ~20–50 kHz at the time of calibration. Superregen reliable; superhet likely if VDPWR is quiet. In band. |
| **3. Full trim + ring LDO** | option 2 + a regulator for the ring | Removes the supply sensitivity (board 1.5 %, ripple spurs): superhet robust. A new analog block with its own loop and decap; the biggest job. |

**Timing:** STATUS has the TX-frequency decision as next step 1, before the c / rc tile runs and
precheck, with tapeout in Nov 2026. Option 2 adds about one TX-corner iteration plus a macro re-harden;
that's the only point where it fits in the schedule.

**Open questions** that only sims can settle:
- varactor tuning ratio under a full-swing node;
- the mux delay and tap placement across corners;
- the ÷256 first stage toggling at ff;
- off-state leakage with the ring free-running;
- whether the `trim` branch route couples into the RX.
