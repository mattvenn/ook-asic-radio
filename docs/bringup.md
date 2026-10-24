# Bring-up plan

How to test the silicon: first the digital alone, then the transmitter alone, then the receiver alone, then the two together. Every test lists what to do, what to expect (from simulation, with the source), and what to record. Write results into the table at each step and keep raw captures in `bench/data/<date>/`.

Order matters: each stage only uses parts the earlier stages have already checked. If a stage fails, stop and debug it before moving on.

## Equipment

- 2 × TT demo boards (RP2350), 3.3 V and 1.8 V supplies checked (expect 1.80–1.81 / 3.30 V, measured on 3 boards).
- Keysight HD304MSO scope (`bench/scope.py`), 1 MΩ probes.
- RTL-SDR (any SDR covering 300–600 MHz), with `rtl_power` / `rtl_sdr`.
- SMA DC blocks, 50 Ω attenuators (a 10 dB step set adding up to ≥ 100 dB), SMA cables, a balun if available.
- Optional, makes the RX tests much better: an RF signal generator with pulse/OOK modulation at 300–600 MHz, and an AWG.
- 4 × 16.5 cm wires for the dipoles.
- A 433.92 MHz key fob or garage remote (an uncalibrated test signal).

## Reference values

| Item | Expected | Source |
|---|---|---|
| TX frequency | ~448 MHz (anything in 330–560 MHz works) | STATUS.md step 1 (tile RC 519 MHz × 0.866) |
| TX power into the dipole | +3.1 to +3.4 dBm (extracted), +4.1 to +4.3 dBm (schematic) | how_it_works.md |
| TX VAPWR current, keyed on | ~13 mA (6.65 mA average per arm), ~0 when off | docs/power.md |
| RX VDPWR current | ~3.0 mA (2.985 mA, extracted tile) | verify_2026-10-11.md |
| Detector `det` at idle | ~1.49 V (extracted) | STATUS.md, log_det |
| Detector slope | ~13 mV/dB over ~70 dB, falls with power (1.21 V at −60 dBm) | how_it_works.md, verify_2026-10-11.md |
| RX sensitivity | −92 dBm at the pins (≥ 99 % of chips), −94 dBm best case | verify_2026-10-13.md |
| Path loss with the dipoles | ~−32 dBm at 1 m, ~1/d^1.89, ~80 m range | how_it_works.md |
| Chip | 104 µs (130 clocks × 8 samples at 10 MHz) | radio_digital.v |
| One send | 3 × (127 chips on/off + 64 chips off) = 59.6 ms | rd_tx.v |
| After a toggle | the RX ignores its code for ~1 s, and shows the quality digit for ~1.7 s | rd_rx.v |

**Pin limits:** `ua[2]` uses thin-oxide devices, so keep it within 0–1.8 V. Never connect a TX pin (`ua[3]`/`ua[4]`, 3.3 V push-pull) straight into an RF input. Always use a DC block, and attenuate to below the input's limit (RTL-SDR: below about +10 dBm, so use ≥ 20 dB). Never connect a TX pin to an RX pin without ≥ 40 dB in between.

## Demo-board firmware

Base it on `bench/fw/ringkey.py`. It already selects a project with the shuttle forced and keys a pin from a PIO state machine. The new firmware needs:

- `PROJECT = 'tt_um_mattvenn_radio'`, with a 10 MHz project clock.
- **Strapped reset** (raw / debug / monopole modes). The straps are read on the first clock edge after `rst_n` goes high, and `uio[7:3]` become outputs on the second. So use the clock to make the hand-over clean:
  1. Clock running. Hold reset. The RP2350 drives `uio[7:4]` = `1010`, `uio[1:0]` = mode, `uio[2]` = debug, `uio[3]` = monopole.
  2. Stop the clock. Release reset. Pulse the clock once: the straps are latched.
  3. Set the RP2350's `uio[7:3]` to inputs. Then restart the clock: the chip turns its outputs on.

  This avoids any time where the RP2350 and the chip both drive `uio[7:4]`.
- PIO keying of `uio[2]`: steady, square wave at a given rate, Manchester bytes.
- PIO sampling of `uio[3]` at a fixed rate (≥ 77 kS/s) into a buffer, for the raw-RX tests.
- A counter for the `uio[5]` toggle pulse (it is one clock long, 100 ns: use an edge-triggered PIO, not polling).
- `ui_in[7]` (role) and `ui_in[6:0]` (code).

Generate test patterns from the model: `model/gold.py` `gold(k)` gives the 127-chip pattern for code `k`.

---

## Stage 0: power and digital (one board, no RF)

| # | Test | Expected | Result |
|---|---|---|---|
| D1 | Select the project, 10 MHz clock, `ui_in[7]` = 0, reset | display `-`, dp off | |
| D2 | `ui_in[7]` = 1, reset | display `t` | |
| D3 | Supply current, RX role vs TX role idle | RX ~3 mA more on VDPWR; TX idle: ~0 on VAPWR | |
| D4 | `uio[7:3]` direction after reset | outputs (`uio_oe` = `11111000`); `uio[2:0]` inputs | |
| D5 | Strapped reset, raw mode (`1010`, mode `01`) | display `r` | |
| D6 | Reset without the `1010` pattern, mode `01` on `uio[1:0]` | normal mode (`-` or `t`): the straps are ignored | |
| D7 | Change `ui_in[6:0]` in TX role | `uio[7]` high for 59.6 ms, display `1` `2` `3` then `t`; no send if the code changes back within ~50 ms | |

If D1 fails, check that the project is selected (the board's carrier detect may fail: force the shuttle, as `ringkey.py` does) and that the clock is running.

## Stage 1: transmitter alone

One board, TX role unless noted. Use a DC block and ≥ 20 dB of attenuation between the TX pin and any instrument.

| # | Test | How | Expected | Result |
|---|---|---|---|---|
| T1 | Carrier exists | Raw mode, `uio[2]` = 1 (steady). SDR with a short wire near the board, or cabled from `ua[3]` | a carrier near 448 MHz | |
| T2 | Frequency | Scope FFT or SDR peak, cabled | 330–560 MHz (~448 expected). Record the frequency and the spread across the two boards | |
| T3 | Drift | Steady on for 10 min, frequency every 10 s; breathe on it / warm it with a finger | slow drift of a few MHz is fine; the RX doesn't tune | |
| T4 | Power, each arm | Scope at 50 Ω on `ua[3]`, then `ua[4]` (DC block + attenuator), `bench/rf.py spectrum_dbm`. Correct for the attenuator | similar on both arms. Into 50 Ω single-ended it reads lower than the differential dipole figure: record it, and compare it with the old ring's −8.5 dBm into 50 Ω (PLAN.md) | |
| T5 | Harmonics | Same capture, H2 and H3 | record in dBc (the old ring: H2 −21 dBc) | |
| T6 | VAPWR current | Steady on vs off | ~13 mA on, ~0 off | |
| T7 | Keying edges and chirp | Raw mode, `uio[2]` square wave 1 kHz; `bench/keying.py` | on/off in a few ns at the pin (PLAN.md). Record how long the frequency takes to settle after turn-on, compared with one chip (104 µs) | |
| T8 | Monopole strap | Strapped reset with `uio[3]` = 1, keyed | `ua[3]` carries the carrier, `ua[4]` stays low | |
| T9 | Code-mode burst timing | Code mode, change the code. Scope a 1 MΩ probe near the antenna (or the SDR envelope) and `uio[7]` | 3 bursts of 13.2 ms with 6.7 ms gaps, 59.6 ms in all, inside `uio[7]` high | |
| T10 | Code-mode chip pattern | Decode the T9 envelope at 104 µs per chip | matches `gold(code)` for 3 codes (e.g. 0, 1, 127) | |
| T11 | Off is off | Code mode, idle: SDR at max gain near the board | no carrier between sends | |

If T1 fails: check the 3.3 V supply reaches VAPWR (`uses_vapwr`) and repeat in the RX role (raw mode can key the TX in either role). T8 tells you whether one arm or the shared ring/level shifter is broken.

## Stage 2: receiver alone

One board, RX role (`ui_in[7]` = 0). Do R1–R3 with no antenna fitted.

| # | Test | How | Expected | Result |
|---|---|---|---|---|
| R1 | Idle | Scope `uio[3]` (comparator) and `uio[6]` (trim direction) | both toggle, roughly 50 % duty: the servo dithers the threshold around the noise | |
| R2 | RX current | VDPWR, RX vs TX role idle | ~3 mA difference | |
| R3 | Detector, idle | Debug strap (`1010`, `uio[2]` = 1). 1 MΩ probe on `ua[2]` | ~1.49 V, quiet | |
| R4 | Debug off | Normal reset | `ua[2]` floats: it doesn't follow det | |
| R5 | Baseband injection (no RF) | Debug mode. AWG (50 Ω) on `ua[2]`: it drives det at ×0.65 through the debug switch. Send `gold(code)` as steps of ~20 mV at 104 µs per chip around the idle level. Stay within 0–1.8 V | `uio[3]` follows the pattern, `uio[4]` opens, the LED toggles, the display shows a quality digit. A wrong code doesn't toggle | |
| R6 | Detector curve | Signal generator, CW at the T2 frequency, into `ua[0]` (single-ended through a DC block, `ua[1]` open, which costs ~6 dB; or through a balun). Sweep −100 → −20 dBm in 5 dB steps, record `ua[2]` | falls ~13 mV/dB, straight over ~70 dB; ~1.21 V at −60 dBm (less the input loss) | |
| R7 | Frequency response | Fixed level (e.g. −60 dBm), sweep 300–600 MHz | flat-ish over 330–560 MHz, peaking near 433 | |
| R8 | Comparator vs power | Generator pulse-modulated: a square wave of 2 chips period (4.8 kHz), stepping down from −60 dBm. The RP2350 samples `uio[3]` and scores it against the known square | ~100 % correct at strong signal, ~80 % at the sensitivity limit (−92 dBm at the pins) | |
| R9 | Code-mode detection | Generator with arbitrary modulation (or another board's raw TX keyed with the pattern, see L1): 3 bursts of `gold(code)` with the T9 timing. Step the level down | LED toggles; the quality digit falls with level; record the lowest level that toggles ≥ 19/20 | |
| R10 | Wrong code / noise | As R9 with a different code, and with the key fob held near the board | no toggle, ever | |
| R11 | Overload | −10 dBm keyed | `uio[3]` follows the keying, detection still works; recovers within ~1.3 ms after a strong burst ends | |
| R12 | False-toggle soak | Antenna fitted, overnight, RP2350 counting `uio[5]` | 0 toggles | |

Without a signal generator: do R1–R5 and R10–R12. Leave sensitivity to L1, which uses a measured TX as the source. The key fob gives a quick check that `det` and `uio[3]` respond at all.

The input loss matters for R6–R9: the board traces, the TT analog mux and the pad all sit between the SMA and the chain. Record levels at the SMA, and work out the loss from the R6 curve against the simulated one.

## Stage 3: both together

Two boards, the same code on both unless noted.

| # | Test | How | Expected | Result |
|---|---|---|---|---|
| L1 | Cabled link, calibrated | TX board monopole strap (`ua[3]` only), DC block, step attenuator, RX `ua[0]`. Code mode, 20 sends per setting. Start at 60 dB, add 10 then 2 dB at a time | the toggle rate drops off near TX power (T4) − attenuation ≈ −92 dBm. Record the 95 % point | |
| L1a | Leakage check | At the L1 threshold, disconnect the cable | no toggles (otherwise the boards hear each other over the air: separate them or shield one) | |
| L2 | Air link, 1 m | Dipoles on both boards | LED toggles on every send, high quality digit; RX sees ~−32 dBm | |
| L3 | Wrong code | TX on a different code | no toggle | |
| L4 | Range walk | 1, 3, 10, 20, 40, 80 m, line of sight, boards at the same height, dipoles parallel. The TX RP2350 sends every 2 s (code change or reset); the RX RP2350 counts `uio[5]`. 20 sends per point | ~100 % out to tens of m, falling off near ~80 m. Record the hit rate and the quality digit at each distance | |
| L5 | Orientation | At a distance with ~100 % hits, turn one dipole 90° | big drop (cross polarisation): shows it is the dipoles linking, not the board wiring | |
| L6 | Raw link (RP2350 data) | TX board raw mode: the RP2350 sends Manchester bytes on `uio[2]` at 1 kbps. RX board in any mode: the RP2350 samples `uio[3]` and decodes | bytes decode at 1 m. Then try 2 and 4 kbps, and record the bit error rate vs distance. Keep the data DC-balanced: the threshold servo pulls towards 50 % ones | |
| L7 | Half duplex on one board | Both boards in RX role + raw mode: each can key its TX on `uio[2]` and read `uio[3]`. Ping-pong a message between them | each hears the other. Each also hears itself while it sends (the loopback), so take turns | |
| L8 | Interference | L4 at a good distance with the key fob pressed near the RX | no false toggles; a send may be missed while the fob transmits | |
| L9 | Board-to-board spread | Swap the TX and RX boards, repeat L1 | the thresholds agree within a few dB | |

## Reporting

For each stage, write a short summary with the measured values next to the expected ones, and add it to STATUS.md. If a measurement is well away from the simulation (more than 3 dB on power or sensitivity, or the frequency outside 330–560 MHz), note it as a finding with the capture, as in `docs/verify_system_2.md`.
