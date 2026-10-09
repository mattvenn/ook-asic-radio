# ASIC radio: Tiny Tapeout sky130 UHF OOK link (proof of concept)

## Goal
A rough-and-ready radio link between two TT demo boards that select the same TT project. A DIP switch sets each board's role to TX or RX. The antennas are bare ~15 cm wires on analog pins, with no external components.

- **Code mode (standalone, stock firmware):** set a 7-bit code on the TX DIP switches and send it. The RX compares the received code with its own DIP switches and toggles an LED on a match. Its 7-seg display shows status and link quality (correlation score).
- **Data mode (optional, secondary):** UART from the TX board's RP2350 goes over the air and comes out of the RX chip to the RX board's RP2350. Expected to need the boards closer together than code mode.
- **Raw modes (debug, and a general 433 OOK front end):**
  - **Raw RX:** the comparator's bit stream goes straight to a `uio` pin, for the RP2350 to sample with PIO.
  - **Raw TX:** a `uio` input keys the ring oscillator directly.
  - Uses include bring-up, debugging, and experiments driven from MicroPython (e.g. recording and replaying a fixed-code 433 remote; that also needs the stretch-goal frequency trim).

Area, cost and legality are not constraints. Workflow: measure, then model, then schematic and RTL, then ASIC.

**Target: ttsky26d (tapeout November 2026), 3×2 analog tile (available; the repo is still set up as 2×2 + VAPWR), sky130.** This is ~6–8 weeks from 2026-10-07, so the analog is the critical path and stretch goals are out of scope.

## What phase 0 measured (bench/, data in bench/data/)
| Item | Result |
|---|---|
| TX power, existing ttsky25b ring osc (ring 1, pin K / ua[0]) into 50 Ω | −8.5 dBm at 518 MHz; source ~210 Ω; H2 −21 dBc |
| Path loss, 14.5 cm wires, 10 cm–4 m | exponent n = 1.89 (far field); −44 dBm at 1 m; ±5 dB multipath |
| Frequency stability | settled std 45 kHz; hot air −0.11%; chip-to-chip ~0.2%; same chip on different boards ~1.5% (supply) |
| Keying (ring enable) | on/off ~30/40 ns, 48 dB on/off ratio; −3.8 MHz chirp for ~20–40 µs per turn-on (supply droop) |
| Phase noise | −85 dBc/Hz at 1 MHz; ±50 kHz wander; ±2.8 MHz spurs (board regulator) |
| OOK packets (PIO-keyed ring, 9600 baud) | decoded from the RF at 0.5 m (−32 dBm), 2 m (−44 dBm), 4 m (−50 dBm) |
| Ambient | 450–600 MHz quiet (below the scope floor); strong signal at ~392 MHz (~−62 dBm) |
| Antennas at 1.5 m (`bench/data/antenna_test.csv`) | Ground-referenced dipoles at both ends gave +5 dB over monopoles. The TX dipole halved the sensitivity to the USB cable (1.7 vs 3.3 dB) and to a hand (−4.6 vs −7.5 dB). The RX dipole added +2.4 to +5 dB |

**Software RX model** (`bench/rx_model.py`, run on the real recording, NF 10 dB assumed):
- **Sensitivity:**
  - **about −90 dBm** with a wideband 400 MHz LNA (radiometer effect);
  - −92 dBm with 100 MHz selectivity;
  - −80 dBm with the 392 MHz interferer present.
- **Slicer:**
  - A fixed threshold only covers ~20 dB of range (pulse stretching).
  - A peak/valley tracker with squelch covers the full range, matching the ideal threshold.
  - A log detector with the tracker is equally good.
- **Back end:** a sync-word correlator is required; a 0x55 preamble breaks naive UART framing.
- **Expected range:** tens of metres with 15 dB fade margin. The real limit will be the LNA noise figure, interferers and self-interference.

## Architecture decisions
- **433.92 MHz nominal (the garage-door / ISM band), far field, OOK.** The 13.56 MHz near-field idea is dropped.
  - 518 MHz was only where the existing ring happened to run. The envelope RX doesn't care about the exact frequency, so 433 brings:
    - the 433 ecosystem: RTL-SDR + `rtl_433`, cheap 433 receiver modules, remotes or a Flipper as test transmitters, SMA whips;
    - a relatable demo;
    - ~1.6 dB less path loss.
  - The band is busy with bursty OOK (remotes, sensors); the Gold correlator and 2-of-3 pairing handle that.
  - **The TX ring is untrimmed:** ±10–20% process spread is fine for our own wideband link.
  - **Stretch:** a ring frequency trim plus an on-chip frequency counter, to land within ±0.2% for commercial 433 receivers (see Stretch).
  - All phase-0 data was taken at 518 MHz; the path-loss, sensitivity and threshold conclusions are frequency-agnostic.
- **Signalling**, decided by `bench/scheme_compare.py` (same RX model, noise / fading / bursty interferer):
  - **Code mode:** each 7-bit code selects a **127-chip Gold sequence** at ~9.6 kchip/s (13 ms). The RX runs a **normalised sliding correlator** for its *own* code only.
    - Sensitivity about −96 dBm, versus −88 for NRZ UART + tracker.
    - Unaffected by ±10 dB fading.
    - The only scheme that survives a strong bursty interferer.
    - No UART, threshold or framing.
  - **Data mode (secondary / stretch):** Gold-sequence sync preamble, then a **Manchester** payload with a half-bit energy comparison, CRC-8, and the packet sent 3× (accept any copy with a good CRC). Kept deliberately simple.
    - **Expect shorter range than code mode:** about −92 dBm in noise, but fades and interferer bursts corrupt bits, and one bad bit fails the CRC.
    - Spreading data bits over N chips or adding FEC would help (~+1.5 dB per doubling of N) but isn't planned; code mode is the headline demo.
  - **NRZ UART over the air is dropped.** UART remains only at the RP2350 interface.
- **Antennas: balanced dipoles on both TX and RX** (2 × ~16.5 cm wires per board at 433 MHz (λ/4 = 17.3 cm, ~5% shorter for end effects; trim on the bench), straight out in opposite directions).
  - **Antenna assembly:** two equal-length feed wires from the two `ua` header pins, wherever they land, twisted together into a balanced feed line, then split into the two ~16.5 cm arms (measured from the split).
    - The twisted section doesn't radiate.
    - A pin-position or trace mismatch of up to ~10 cm is only ~14° (negligible).
    - The same assembly works for TX and RX.
  - **Fallback:** a digital TX option to drive only one output (single-ended / monopole mode), in case the antiphase buffers misbehave on silicon. Built into `tx_top` as per-arm enables (en_n = 0): ~7 dB less power.
  - TX is driven in antiphase from two `ua` pins (+3 dB drive, no ground return).
  - RX goes into a differential LNA, which rejects common-mode board ground and self-interference.
- **TX** (first pass simulated, `sim/tx/`; see docs/history.md):
  - ring oscillator from std cells (nand2_2 enable + 22 × inv_2, as the ttsky25b ring but longer);
  - → the R2R DAC's 1.8 → 3.3 V level shifter with a **skewed core** (it fails at 433 MHz as built);
  - → thick-oxide buffer tapers on the latch's two complementary nodes (inherently antiphase);
  - → final drivers N 48 / P 144 µm on VAPWR (3.3 V) → `ua` pins → dipole;
  - keyed directly as OOK by on-chip digital logic; no PLL, no calibration; the chirp and drift don't matter to an envelope RX.
  - **xschem blocks done** (`xschem/gen/tx.py`, `sim/tx/tb_tx.py`): +3.7…+3.9 dBm at all five process corners. Off state: both arms low (thick NAND gate at the head of each taper).
- **RX: no superheterodyne, no SAR** (decided by `model/rx_eval.py`, `model/threshold_variants.py`, `model/tau_study.py`).
  - **Analog** (first pass simulated at tt, transistor level, `xschem/gen/`; see docs/history.md):
    - 6-stage NMOS differential-pair limiting chain: stage 1 low-noise (1.2 mA), stages 2–6 capacitively degenerated (band shaping, no offset build-up), ~80 dB;
    - → successive-detection log detector (one rectifier per stage tap);
    - → RC LPF (~14 kHz, poly R + MIM);
    - → **one continuous-time comparator** (no strobe, so no kickback), sampled by the digital.
    - Comparator inputs: the LPF output, and a **slow switched-cap average of the LPF output** (τ ≈ 0.47 ms). The **fine offset trim** from the reused **R2R DAC** enters through a degenerated trim pair inside the comparator (~0.087 mV/LSB).
    - Chosen over the inverter LNA because pseudo-differential inverters amplify common mode, so a 60 dB chain would rail on our own 10 MHz clock.
  - **Why:** near sensitivity the whole signal swing is ~0.27 dB (~4 mV) at −90 dBm, and only ~0.08 dB (~1 mV at the simulated 12 mV/dB) at −94 dBm, below the noise in the RF band. A full-range 8-bit DAC threshold (0.44 dB/LSB) fails below −80 to −90 dBm, and an untrimmed 2 mV comparator offset loses 4+ dB.
  - **Digital:**
    - **Trim servo:** steps the DAC to keep the comparator's 1s density at 50%.
    - **Code mode:** 1-bit chip decisions (majority of 8 samples/chip) at 4 chip-timing phases → 127-bit shift registers → sequential XNOR-popcount against the RX's own Gold code → threshold ≥ 97/127 (z = 6) → 2-of-3 bursts with the right spacing → toggle LED.
    - **Signal strength:** the correlation score is the link-quality indicator for the 7-seg.
  - **Modelled sensitivity:** ≈ −94 dBm, within ~2 dB of a multi-bit soft correlator, at ~10× less storage. Robust to fading; works with a bursty −60 dBm interferer down to ≈ −66..−72 dBm signal.
  - **With the simulated chain** (NF ≈ 11 dB, ~450 MHz noise bandwidth, 12 mV/dB): −94 dBm still decodes, but only just: score 99/127 against a threshold of 97 in the whole-RX transistor-level transient. Margin across corners is the main open analog question.
- **Clock: ~10 MHz** from the RP2350 (`config.ini`), not 50 MHz. The digital needs only ~1 MHz (comparator sampled every 130 clocks, sequential popcount).
  - **The harmonics are still in the LNA band**, every 10 MHz, including 430 and 440 MHz either side of 433.92 MHz.
  - **But they're weaker:** each line is ~14 dB weaker at ~450 MHz than a 50 MHz harmonic, total in-band power is ~7 dB lower, and the average supply noise is ~5× lower.
  - **They're steady (CW) lines,** so they add a constant offset that the normalised correlator and the Manchester half-bit decision ignore. The remaining risk is LNA desensitisation, handled by isolation.
  - All timing derives from this clock.

## Block requirements (initial, to be refined by the golden model and simulation)
| Block | Requirement |
|---|---|
| Ring osc + buffers (TX) | **~433 MHz on silicon.** The ttsky25b ring measured 518 MHz against 598 extracted-tt (×0.866), so **design to ~500 MHz extracted-tt**: nand + 22 inv_2 → 484 MHz tt sim → ~419 MHz expected (20 inv → ~466). Spread across corners is OK (RX band 330–560). Antiphase arms from the level shifter's complementary nodes: phase within 1.2° (≤ 10° budget). **3.3 V output stage** (thick-oxide `g5v0d10v5`): **+3.3…+4.0 dBm into the 73 Ω dipole across corners, +4.2 dB over the old 1.8 V driver**; ~10 mA from VAPWR, only ~0.2 mA step on VDPWR (so less turn-on chirp). Larger drivers gain nothing (the pad/mux path dominates). The dipole has no DC path. Enable from the digital; on/off in a few ns |
| LNA/limiter chain | **differential input**; ≥ 60 dB small-signal gain across ~330–560 MHz (433 ± ~25% to cover TX ring spread); NF ≲ 10 dB including pad and ESD; good common-mode rejection; the ~392 MHz signal measured on the bench will be in band, so rely on the correlator for it. **Simulated (tt):** 5 stages 66.6 dB flat 330–434 MHz; 6 stages (~80 dB) used so the noise floor sits in the detector's log range. NF ≈ 11 dB, wires only: off-chip matching would give ~3 dB but is not allowed. FM −23 dB, 10 MHz −96 dB re band; ~2.9 mA |
| Log detector | ~50 dB dynamic range, roughly linear in dB (~16 mV/dB assumed; simulated 12.6 mV/dB, ~11–14 at the noise floor); video bandwidth ≥ 100 kHz before the LPF; low noise and drift, since the signal near sensitivity is only ~0.3 dB |
| LPF | ~15 kHz (RC on chip). **Done:** 1 MΩ xhigh poly + 10.9 pF MIM, 14.4 kHz; the e2e model is insensitive to 10–20 kHz |
| Averaging reference | τ ≈ 0.3–1 ms (model insensitive to 0.3–5 ms); switched-capacitor resistor clocked at the sample rate. **Done:** 0.25 pF ↔ 9.1 pF on the digital's sc_phi1/2, τ = 0.47 ms, offset ≤ 0.04 mV |
| Comparator + trim DAC | Comparator: decisions at ~77 kS/s (every 130 clocks at 10 MHz); offset of a few mV OK (trimmed); **input noise ≤ 0.5 mV rms per decision** (e2e with the simulated chain: 0.6 mV starts losing −94 dBm, 1 mV costs ~2–4 dB).<br>**Reuse the ttsky25b R2R DAC** (`mattvenn/tt08-analog-r2r-dac-3v3`, 8-bit poly ladder, R ≈ 10 kΩ) driven from 1.8 V and **attenuated to ~±10 mV** as the comparator offset trim (~0.08 mV/LSB); servoed digitally. **Simulated comparator:** continuous-time, low-Vt NMOS pair; offset +0.5…1.8 mV over input CM 0.55–1.6 V; decision noise 28 µV rms; 0.36 µs at 1 mV overdrive; trim 0.087 mV/LSB |
| Digital | **Size:** ~40,500 µm² placed as is. It fits a 3×2; if space is needed, clock-gate the chip registers first (−8,400 µm², `dlclkp` has sky130 silicon evidence). ~10 MHz clock. Trim servo; 4 × 127-bit chip registers; sequential popcount (127 cycles per chip-phase, 4 phases per 1040-clock chip); 2-of-3 burst timing; LED toggle with holdoff; correlation score to the 7-seg; Gold TX chip generator (two 7-bit LFSRs, `model/gold.py`); data mode: Gold sync + Manchester (half-bit 1s counts) + CRC; UART only at the RP2350 interface |
| Isolation | quiet digital during RX; separate analog supply routing, guard rings, decoupling capacitance in spare area; keep the chip's own ~10 MHz clock harmonics (every 10 MHz through the band) well below the LNA's compression point; clock-gate unused logic during reception |

## Draft pin map (finalize against tt-demo-pcb)
| Pin | Function |
|---|---|
| `ui_in[6:0]` | code (TX: send; RX: match) |
| `ui_in[7]` | role: 0 = RX, 1 = TX |
| `rst_n` / code change | TX sends a packet (×3) on reset release and on any code change |
| `uo_out[7:0]` | 7-seg: TX status / RX match LED, link-quality bar (correlation score), DP = detection |
| `uio[0]` | mode select with `uio[1]` (strapped/latched at reset): code (default) / data / raw |
| `uio[1]` | mode select (second bit). **Floating `uio` on a bare board must give code mode.** Check whether TT's `uio` pads give a defined default level; if not, enter data/raw mode only via an explicit command (magic header on the UART pin), never on pin levels alone |
| `uio[2]` | data mode: UART in (TX) / UART out (RX). **Raw TX: key input** (drives the ring enable directly) |
| `uio[3]` | **raw RX: comparator bit stream** (always available; doubles as debug) |
| `uio[4..7]` | debug: burst detected, pair/toggle event, trim-servo direction, TX active |
| `ua[0]` / `ua[1]` | TX dipole: antiphase buffer outputs. The header position depends on where TT places the project, so it's not necessarily adjacent; see the antenna assembly note |
| `ua[2]` / `ua[3]` | RX dipole: differential LNA input |
| `ua[4]` | debug: detector output `det`, through a transmission gate that is **on only in debug mode** (strap: magic `1010` + `uio_in[2]` = 1 at reset). Off, det is isolated from the pin. On, a scope sees det (656 kHz bandwidth), or an AWG can drive det (×0.65 from 50 Ω) to test the baseband without RF. Thin devices: keep the pin within 0–1.8 V |

## Bursts and false-trigger protection
- **Code mode:**
  - The TX sends the Gold-127 burst for its code **3×**.
  - The RX toggles the LED only if its correlator exceeds ρ > 0.4 in **at least 2 of the 3** expected slots, then holds off ~1 s. So one send means one toggle.
  - Wrong codes peaked at ρ ≈ 0.34 under interference in the model. Consider 255 chips if the margin proves too thin.
- **Data mode (secondary):** Gold sync, length, Manchester payload, CRC-8, sent 3×.

## Repo layout
This follows the TT analog template flow of `mattvenn/tt08-analog-r2r-dac-3v3`, updated to ttsky26d (see README.md):
```
asic-radio/
  info.yaml docs/info.md src/project.v   TT project files (src/project.v = LVS stub)
  .github/workflows/                     gds + docs (@ttsky26d), lvs (magic/netgen)
  mag/                                   Magic layout; make start / drc / lvs (2x2 + VAPWR template)
  gds/ lef/                              layout outputs
  xschem/ sim/                           analog schematics, testbenches, ngspice runs
  verilog/rtl verilog/gl verilog/test    digital macro radio_digital; cocotb tests + vectors/
  openlane/radio_digital/                hardening config for the digital macro
  model/                                 bit-exact Python model + RX studies; exports verilog/test/vectors
  bench/ stim/                           phase-0 bench tools, data, recorded RF stimuli
  tools/osic                             run IIC-OSIC-TOOLS headless from the repo
  PLAN.md docs/slicer.md
```

## Phases
**Phase 0: channel and TX measurement (done)**
See the tables above.

**Phase 1: golden model of RX option B** (`model/`)
- **Done for code mode:**
  - `model/gold.py`: bit-exact LFSR Gold codes.
  - `model/radio.py`: bit-exact TX send and RX digital (trim servo, 4-phase chip slicer, 127-bit correlator, events, 2-of-3 pairing, holdoff, LED), plus the behavioural analog comparator.
  - `model/e2e.py`, end to end:
    - all sends detected to −94 dBm in noise, −90 dBm with ±10 dB fading, −70 dBm with a bursty −60 dBm interferer (partial to −90);
    - zero false toggles (wrong-code RX on 75 sends, 9 signal-free records).
  - `verilog/test/vectors/`: 9 RX scenarios + the TX code table, with the timing contract in `verilog/verilog/test/vectors/README.md`.
  - `docs/slicer.md`: how the comparator/servo works.
- **Still to model:** data mode (Gold sync + Manchester + CRC, secondary) and the raw modes (pass-throughs). Do these alongside the RTL.
- Choose the DAC range, bit width, sample rate and time constants. Confirm sensitivity stays ~−90 dBm and the slicer works from −40 to −90 dBm with the recordings.
- **Gate:** the integer model decodes the recorded packets and synthetic sweeps; it exports comparator/DAC test vectors.

**Phase 2: digital RTL + FPGA** (`src/`, `test/`, `fpga/`)
- TX: packetizer, ring-enable keying, send trigger.
- RX: trim servo, chip slicer, 1-bit correlator, burst pairing, LED/7-seg, data-mode Manchester + CRC, UART to the RP2350.
- cocotb tests bit-exact against the golden model.
- **FPGA, TX hardware-in-the-loop:** the FPGA board runs the TX digital. Its keying output goes by jumper to the ttsky25b board's `ui_in[0]`, so the real ring osc transmits the FPGA's packets. Check them with `bench/record.py`.
- **FPGA, RX:** runs the RX digital with comparator decisions replayed from the golden model on the recordings. The analog front end isn't available until silicon.
- **Gate:** all tests pass; real FPGA-generated packets decode off-air; the RX digital decodes the replayed recordings on the FPGA.

**Phase 3: analog schematics** (`xschem/`, `sim/`; IIC-OSIC-TOOLS docker with the sky130 PDK). **Status 2026-10-08:** every RX block has a first pass at tt and the whole RX transient detects −94 dBm (just); the TX has a first pass in raw spice. Still to do: corners/temperature, bias generation, power-down, R2R DAC hookup, TX as xschem blocks. See STATUS.md.
- LNA/limiter chain, log detector, LPF, comparator, R-2R/capacitor DAC, ring osc and buffer (from ttsky25b).
- Testbenches drive the RX input with `stim/packet_*.pwl` through a pad model (~200–500 Ω, few pF) and compare the detector output against the model.
- **Gate:**
  - LNA gain and NF meet the targets across corners and −20 to 85 °C;
  - the recorded packets decode via ngspice → comparator decisions → golden model/RTL;
  - self-interference is simulated (digital switching coupled to the LNA input).

**Phase 4: mixed-signal integration**
- Analog plus hardened digital macro in the TT analog template (**3×2**), **following the ttsky25b R2R DAC project's flow**:
  - the digital is hardened with OpenLane as a macro (pin-order config);
  - it's placed in the Magic top level with the analog;
  - `src/project.v` is the LVS stub;
  - `sim/mixed.cir` provides ngspice + Verilator co-simulation.
- Layout: guard rings, separate analog supply routing, met4 power stripes, no met5, decoupling in spare area.
- **Gate:** DRC/LVS clean; post-layout re-simulation of the key testbenches; TT precheck.

**Stretch (only if time allows)**
- **Ring frequency trim + on-chip frequency counter:** coarse stage select + fine current DAC; the counter measures the ring against the 10 MHz clock, and the logic or the RP2350 trims to 433.92 MHz (±0.2%).
  - Needed for interoperating with commercial 433 receivers, e.g. replaying a recorded **fixed-code** remote via raw TX. Rolling-code fobs reject replays anyway.
  - The measured drift after trim (±0.1% with temperature, ~±50 kHz wander) should stay within a SAW receiver's window.
- **Shared TX/RX antenna pins (half-duplex):** one dipole on `ua[0]`/`ua[1]` for both roles, freeing `ua[2]`/`ua[3]` (one antenna per board, fewer analog pins, no long RX input route). Needs:
  - `tx_drv` tri-stated in RX (P gate to VAPWR, N gate to 0) instead of today's "both arms low", which would short the LNA input; keep the two arms' delay matched. The monopole fallback becomes "tri-state one arm".
  - LNA input protection in TX: the pin swings 0–3.3 V, putting ~±1.6 V on stage 1's thin gates through `cin`. Preferred: a shunt switch from the stage-1 gates to `vcm` (≲ 20 Ω) during TX, so nothing goes in series with the RX path. Cost: ~9 mW per side from VAPWR into `cin`. Alternative: a thick-oxide series switch ahead of `cin` (cleaner isolation, but it costs NF). Power the chain down in TX.
  - Re-simulate `tb_radio_analog` with a shared pad: the off driver's drain junctions add input capacitance (guess: a few tenths of a dB NF, against today's thin −94 dBm margin) and the `cin` load on TX power. The floorplan puts the TX driver and the LNA input at the same pad; keep the chain's late stages and detector away from it.
- Superheterodyne RX with a ring LO (~+15 dB, rejects the 392 MHz interferer).
- FSK via a trimmed ring.
- An on-chip regulator for the ring.
- A met3/met4 spiral-inductor LC test structure.
- **Periodic-steady-state simulation with VACASK** (in the latest IIC-OSIC image; the 2026.05 image we use only has HB). Needs the sky130 ngspice models converted (`ng2vc.py`) and checked against ngspice first. In order of value here:
  - **PNOISE / HBNOISE:** detector output noise including noise folding through the rectifier, i.e. sensitivity directly instead of statistical transient-noise runs; ring phase noise (bench: −85 dBc/Hz at 1 MHz).
  - **Autonomous PSS:** ring frequency / duty over corners, supply and temperature without long transients.
  - **HB:** fast steady state for the driven parts (detector CW slope, chain gain / compression / IM3 vs the 392 MHz interferer, TX power into the dipole).
  - **HBAC / PAC:** only if the superheterodyne stretch happens (mixer conversion gain).

## Lessons from earlier TT projects (multi-seg-monitor, ring osc, R2R DAC)
- **cocotb:**
  - `make` returns success even when tests fail. Check `results.xml` and delete it to force a rerun.
  - Use doubled quotes in `COCOTB_TEST_FILTER`.
  - Verilator locally for speed; Icarus as the CI and gate-level reference.
- **Bit-exact Python model ↔ RTL checked by cocotb** is the proven pattern; that's our golden model.
- **Floating pins on a bare board:**
  - Latch role and mode from `ui_in` straps at reset, so outputs are safe from the first cycle.
  - Require a magic or valid header before data mode acts on a strobe.
  - Never rely on unpulled `uio` levels at power-up.
- **FPGA:**
  - Keep the FPGA build at feature parity with the ASIC; never assume initialised memory.
  - Flash via `tt_fpga.py configure --upload`. Its environment may need `klayout`/`chevron`.
- **RP2350 limits:** continuous USB-CDC streaming into it stalls after ~1–2 s (MicroPython 1.29). Data-mode demos from a PC must use chunked raw-REPL transfers or data stored on the board.
- **Hardening:** keep utilisation ≲ 80%; mind the macro halo and rotation (LibreLane).
- **ngspice in the IIC-OSIC image:** the OSDI load errors from the global spiceinit are harmless for sky130. Use `tools/osic` to run the image headless from the project.

## Open questions and risks
- ~~TT analog-pin 4 mA limit~~ **Resolved (tnt, 2026-10-07):** the limit is electromigration (RMS, lifetime). Even 20 mA would outlive interest in the chip, and the ≤500 Ω path caps the current at 6.6 mA from 3.3 V anyway. OOK at ~50% duty lowers the RMS further. **So the 3.3 V TX driver is in (+~5 dB).**
- LNA noise figure through the pad/ESD path: NF ≈ 11 dB at tt (sensitivity −94 dBm only just). **Gain, detector slope and comparator margin across corners and supply are the main open analog risk.**
- The pad model (`xschem/pad_model.sch`) is rough: absolute NF and the upper-band rejection (GSM-900 ≈ −8 dB re band in sim) are indicative. Measure the real pin + dipole before adding on-chip shaping.
- TX frequency lands ~419 MHz on silicon if the lot is as slow as the ttsky25b part; the spread is inside the RX band.
- Self-interference from the chip's own digital logic into a 60 dB+ LNA.
- Venue interferers (the 392 MHz-type signals); fade margin indoors (the fading and orientation test is still to do).
- TT mixed-signal flow details (digital macro inside the analog template, power domains, 3.3 V use). The VAPWR 10 mA TX step needs decoupling.
- Pin choice for antennas on the demo-board header (ua order: must use pins in order from ua[0]).
