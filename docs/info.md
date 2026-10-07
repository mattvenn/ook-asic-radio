<!---
This file is used to generate your project datasheet.
-->

## How it works

A 433 MHz on-off-keyed (OOK) radio. Two boards running this project talk to each other with bare-wire dipole antennas.

- **Transmitter:**
  - An on-chip ring oscillator at ~433 MHz is switched on and off by the digital logic.
  - It sends a 127-chip Gold-code pattern selected by the 7 DIP switches, three times.
  - Antiphase drivers feed a dipole on `ua[0]` / `ua[1]`.
- **Receiver:**
  - A differential inverter LNA on `ua[2]` / `ua[3]`, a log envelope detector, and one comparator whose threshold is a slow average of the detector output plus a fine digital trim.
  - The digital logic correlates the comparator bits against the receiver's own code. If 2 of the 3 bursts are detected, it toggles the decimal-point LED. The 7-segment display shows link quality.

## How to test

1. Put the project on two demo boards with a 10 MHz clock. Fit a dipole to each: two ~16.5 cm wires, straight out in opposite directions, from `ua[0]`/`ua[1]` (TX) or `ua[2]`/`ua[3]` (RX).
2. Board A: `ui_in[7]` = 1 (TX). Board B: `ui_in[7]` = 0 (RX). Set the same 7-bit code on both.
3. Reset the TX board, or change its code, to send. The RX toggles its decimal point when it hears its code.

**Raw modes (debug):** the comparator bit stream appears on `uio[3]`, and `uio[2]` can key the transmitter directly. See `PLAN.md` for the mode-select strap.

## External hardware

Wire antennas (4 × ~16.5 cm). An RTL-SDR or a scope is handy for checking the transmitter.
