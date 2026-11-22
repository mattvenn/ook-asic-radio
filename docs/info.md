<!---
This file is used to generate your project datasheet.
-->

## How it works

A 433 MHz on-off-keyed (OOK) radio. Two boards running this project talk to each other using bare-wire dipole antennas and no other external parts. The estimated range is about 70 m in good conditions; it hasn't been measured yet.

This project was designed with an AI agent (Claude) doing most of the work, with Matt Venn setting the direction, checking it and signing off ([made with Claude](https://claude.com/claude-code)). The design log and session transcripts are in the repo.

- **Interactive explainer:** [click through the link, TX and RX with simulated waveforms](https://mattvenn.github.io/ook-asic-radio/docs/explainer.html).
- **Article:** [Can AI design an analog chip? I built a radio to find out](https://www.zerotoasiccourse.com/post/ai_codesigned_radio/) ([zerotoasiccourse.com/radio](https://zerotoasiccourse.com/radio)).
- **Videos:** [An open-source radio in 0.1 mm² of silicon: how it works](https://www.youtube.com/watch?v=fUDIhpx34Qk) and [I put AI to the test on analog chip design](https://www.youtube.com/watch?v=c53n4mH_RYg).

In brief:

- **TX:** an on-chip ring oscillator (~433 MHz) is keyed on and off with a 127-chip Gold code chosen by the 7 DIP switches. The burst is sent three times, by antiphase drivers into a dipole on `ua[4]` / `ua[5]` (about +3 dBm).
- **RX:** a differential amplifier chain on `ua[3]` / `ua[2]` feeds a log detector and a self-trimming comparator. The digital logic correlates the comparator bits against the RX's own code. When it hears 2 of the 3 bursts, it toggles the decimal-point LED. Simulated sensitivity is about −90 dBm (reliable detection, including the transistors' own noise).

More detail, all in the [project repository](https://github.com/mattvenn/ook-asic-radio):

- [How it works](https://github.com/mattvenn/ook-asic-radio#how-it-works): theory, specs, schematics and layout.
- [How it was made](https://github.com/mattvenn/ook-asic-radio#how-it-was-made): the AI-assisted design, with the full log.
- [Schematics](https://github.com/mattvenn/ook-asic-radio#schematics), [layout](https://github.com/mattvenn/ook-asic-radio#layout) and [digital](https://github.com/mattvenn/ook-asic-radio#digital).
- [Verification](https://github.com/mattvenn/ook-asic-radio#verification) and the [bring-up plan](https://github.com/mattvenn/ook-asic-radio#bring-up).

## How to test

1. Put the project on two demo boards with a **10 MHz clock**.
2. Fit a dipole to each board: two ~16.5 cm wires going straight out in opposite directions, one from each pin. TX board: `ua[4]` / `ua[5]`. RX board: `ua[3]` / `ua[2]`.
3. Set `ui_in[7]` = 1 on board A (TX) and 0 on board B (RX), and reset both.
4. Set the same 7-bit code (`ui_in[6:0]`) on both boards.
5. Reset the TX board, or change its code, to send. The TX display shows `1`, `2`, `3` while it sends and `t` when idle.
6. The RX toggles its decimal point when it hears its code. For ~1.7 s the display then shows link quality, 0 (just detected) to 9 (strong). The rest of the time it shows `-`.

**Debug:**
- `uio[3]` always outputs the raw comparator bits.
- `uio[4..7]` show burst detected, toggle, trim direction and TX active.
- The mode is latched at reset, and only when `uio[7:4]` = `1010`. Raw mode (`uio[1:0]` = `01`) lets `uio[2]` key the transmitter directly, in either role, and the display shows `r`: on an RX board the receiver stays on, so `uio[3]` shows the chip hearing its own transmission (a loopback test). Release `uio[2]` after reset if you also strapped debug with it. Debug (`uio[2]` = 1) connects the detector output to `ua[1]`. Monopole fallback (`uio[3]` = 1) drives `ua[4]` only. `uio[7:4]` = `1011` does the same as `1010` and also selects **low LNA gain** (about 10 dB less): a fallback in case the receiver chain oscillates, at the cost of about 5 dB of sensitivity. Use the normal `1010` (or no straps) first. Details are in the [pins section](https://github.com/mattvenn/ook-asic-radio#pins) of the repository, and a stage-by-stage test plan in the [bring-up plan](https://github.com/mattvenn/ook-asic-radio#bring-up).

## External hardware

4 × ~16.5 cm wires (two per board). An RTL-SDR or a scope is useful for checking the transmitter.

## Radio regulations

This is an experimental, uncertified transmitter. The ring oscillator is not tuned: it can land anywhere in about 330–560 MHz (~448 MHz typical), mostly outside the 433.05–434.79 MHz licence-exempt band, and its square wave has strong harmonics. That range includes aviation, emergency-service and 406 MHz distress-beacon frequencies. Power is low (about +3 dBm, 2 mW), but transmitting over the air may need an amateur radio licence (70 cm band: 420–450 MHz in the US, 430–440 MHz in the UK and much of Europe), and outside the amateur band it may not be legal at all. Measure the frequency with an SDR first, keep transmissions short, and prefer the cabled link test in the [bring-up plan](https://github.com/mattvenn/ook-asic-radio/blob/main/docs/bringup.md). Receiving is fine. You are responsible for following your local rules.
