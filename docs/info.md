<!---
This file is used to generate your project datasheet.
-->

## How it works

A 433 MHz on-off-keyed (OOK) radio. Two boards running this project talk to each other using bare-wire dipole antennas.

- **TX:** an on-chip ring oscillator (~433 MHz) is keyed on and off with a 127-chip Gold code chosen by the 7 DIP switches. The burst is sent three times, by antiphase drivers into a dipole on `ua[3]` / `ua[4]`.
- **RX:** a differential amplifier chain on `ua[0]` / `ua[1]` feeds a log detector and a self-trimming comparator. The digital logic correlates the comparator bits against the RX's own code. When it hears 2 of the 3 bursts, it toggles the decimal-point LED.

The full description covers theory, specs, schematics and layout: [docs/how_it_works.md](https://github.com/mattvenn/ook-asic-radio/blob/main/docs/how_it_works.md).

## How to test

1. Put the project on two demo boards with a **10 MHz clock**.
2. Fit a dipole to each board: two ~16.5 cm wires going straight out in opposite directions, one from each pin. TX board: `ua[3]` / `ua[4]`. RX board: `ua[0]` / `ua[1]`.
3. Set `ui_in[7]` = 1 on board A (TX) and 0 on board B (RX), and reset both.
4. Set the same 7-bit code (`ui_in[6:0]`) on both boards.
5. Reset the TX board, or change its code, to send. The TX display shows `1`, `2`, `3` while it sends and `t` when idle.
6. The RX toggles its decimal point when it hears its code. For ~1.7 s the display then shows link quality, 0 (just detected) to 9 (strong). The rest of the time it shows `-`.

**Debug:**
- `uio[3]` always outputs the raw comparator bits.
- `uio[4..7]` show burst detected, toggle, trim direction and TX active.
- The mode is latched at reset, and only when `uio[7:4]` = `1010`. Raw TX (`uio[1:0]` = `01`) lets `uio[2]` key the transmitter directly. Debug (`uio[2]` = 1) connects the detector output to `ua[2]`. Monopole fallback (`uio[3]` = 1) drives `ua[3]` only. Details are in the [pin map](https://github.com/mattvenn/ook-asic-radio/blob/main/PLAN.md#draft-pin-map-finalize-against-tt-demo-pcb).

## External hardware

4 × ~16.5 cm wires (two per board). An RTL-SDR or a scope is useful for checking the transmitter.
