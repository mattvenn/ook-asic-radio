# How it works

A 433 MHz radio link on six Tiny Tapeout tiles (3×2, sky130). Two demo boards run the same chip: one transmits, the other receives. Each board's antenna is two bare wires, and there are no other external parts.

This page covers the idea, the measurements and models that set the specs, each schematic, and the layout. For test instructions see [info.md](info.md).

To click through it instead, with simulated waveforms at each block: [interactive explainer](https://mattvenn.github.io/ook-asic-radio/docs/explainer.html).

## Overview

![block diagram](images/block_diagram.png)

- **RX (top):** the dipole on ua[0]/ua[1] feeds a 6-stage amplifier chain (`lna_chain`). Each stage's output taps into the log detector (`log_det`), which turns RF power into a DC level. That level is filtered (`lpf_rc`) and compared (`comp_ct`) against its own slow average (`avg_sc`), plus a fine trim from the DAC (`r2r`). The comparator bit goes to the digital macro. `bias_gen` supplies every block's currents.
- **TX (bottom):** the digital macro keys the ring oscillator (`tx_ring`). The level shifter (`tx_ls`) turns it into two opposite-phase 3.3 V signals, one driver per dipole arm (`tx_drv`, ua[3]/ua[4]).
- Dashed lines are enables from the digital. This is the "Block diagram" view of the floorplanning tool ([layout/floorplan](../layout/floorplan)).

## Theory of operation

### On-off keying (OOK)
The transmitter switches a 433 MHz carrier on and off, and that is all it does. The receiver doesn't tune to the carrier. It only measures how much RF energy arrives (the *envelope*), so "loud" means 1 and "quiet" means 0.

Because of that, the transmitter needs no crystal or PLL. It is a free-running ring of inverters, and if it lands anywhere in 330–560 MHz the receiver still works. 433 MHz was chosen for its ecosystem: cheap SDRs, `rtl_433`, and garage remotes as test signals.

**dBm** is power on a log scale: 0 dBm = 1 mW, and every −10 dB is 10× less power (−30 dBm = 1 µW). Voltage changes more slowly: −20 dB is 10× less voltage. The transmitter puts out about +4 dBm. At 1 m the receiver sees about −32 dBm (the bench measurement, −44 dBm with the old 1.8 V transmitter, plus the new one's 12 dB), and it can still detect a signal at about −92 dBm. That is 60 dB lower: a million times less power, or 1,000× less voltage. On the same path model that is about 80 m.

### Finding a signal weaker than the noise
Near the sensitivity limit, "carrier on" moves the detector output by only ~1 mV, and the noise is about as large. A single on/off decision there is barely better than a coin flip. So we don't send single bits:

- Each 7-bit code (DIP switches) selects a **[Gold code](https://en.wikipedia.org/wiki/Gold_code)**: a fixed, noise-like pattern of 127 on/off slots called *chips*. One chip is 104 µs, so one burst is 13.2 ms.
- The receiver makes one 1-bit decision per chip and compares the last 127 decisions with its own code's pattern. The **score** is how many match. Chance gives ~64 out of 127; **≥ 97 counts as a detection** (6σ above chance).
- At −92 dBm the comparator is right only ~80 % of the time, but that is still enough to score ~104.
- The TX sends the burst 3 times. The RX toggles the LED only if 2 of the 3 bursts arrive with the right spacing, then ignores the code for ~1 s. Other codes, remote controls and noise don't toggle it.

### Where the threshold goes
The comparator has to decide "on or off" around a level that changes by tens of dB with distance, inside a window of ~1 mV. It does this with two parts:
- The **slow average** of the detector output. A Gold code is half on and half off, so the average sits in the middle of the signal at any range.
- A **trim servo**. The digital moves an 8-bit DAC up or down one step per sample so that the comparator outputs 1 half of the time. This cancels the comparator's own offset (a few mV, which is more than the signal) in ~0.07 mV steps.

More detail: [slicer.md](slicer.md).

## Testing that set the specs

### Bench measurements (phase 0)
These were measured on an existing chip (ttsky25b) that has a ring oscillator, using wire antennas and a scope. Data and scripts are in [`bench/`](../bench).

| What | Result |
|---|---|
| Path loss, 14.5 cm wires, 10 cm–4 m | close to free space (1/d^1.89): **−44 dBm at 1 m** |
| Ring frequency | measured 518 MHz vs 598 MHz simulated, so silicon runs at ×0.866 of simulation |
| Frequency stability | ~0.1 % with temperature, ~1.5 % with supply. Fine for an envelope receiver |
| Keying | on/off in ~30–40 ns, 48 dB on/off ratio |
| Antennas | dipoles beat monopoles by +5 dB and are less sensitive to cables and hands |

![path loss](../bench/data/sweep2/ota_sweep.png)

### Models
- `bench/scheme_compare.py` compared three signalling schemes on the same receiver model with noise, fading and a bursty interferer. Gold-127 correlation won in every case, so it is what the chip uses.
  ![scheme comparison](../bench/data/scheme_compare.png)
- `model/` holds a bit-exact Python model of the whole link. It is the reference that the RTL is tested against. End to end with the H135 comparator at tt, every send is detected at −92 dBm in noise (48/48) and about half at −94 dBm (27/48) ([verify_2026-10-13.md](verify_2026-10-13.md)). With ±10 dB fading (default model settings), every send gets through down to −90 dBm. There are zero false toggles.
  ![end to end](../model/e2e.png)

### Specs

Every number says where it comes from:
- **Schematic:** transistor-level simulation of the xschem schematic.
- **Extracted:** simulation of the layout with its parasitics (PEX). Where both exist, the extracted number is the one to expect.
- **Silicon est.:** an extracted number scaled by a factor measured on an earlier chip.
- **Mixed-signal:** the RTL (Verilog) driving a transistor-level baseband.
- **Model:** the bit-exact Python model of the link (`model/`).
- **Bench:** measured on real hardware (the earlier ttsky25b chip).
- **RTL:** fixed by the digital design, exact by construction.

None of this has been measured on this chip yet: see [bringup.md](bringup.md).

**Transmitter**

| Spec | Value | From |
|---|---|---|
| Frequency | ~448 MHz typical; 332–545 MHz over process corners and supply | Silicon est.: extracted × 0.866 / × 0.845, the factors from the ttsky25b rings (518 MHz measured, 598 simulated). STATUS.md, [verify_supply_mc.md](verify_supply_mc.md) |
| Power into the dipole (73 Ω) | +3.1 dBm typical (+2.7 at 50 °C, +3.5 at 10 °C) | Extracted (whole tile, RC). [verify_2026-10-11.md](verify_2026-10-11.md) |
| | +4.1 to +4.3 dBm at all corners | Schematic |
| Power vs VAPWR | −1.2 / +1.1 dB at 3.0 / 3.6 V | Schematic |
| Phase between the arms | within 1.2° | Schematic (PLAN.md) |
| On / off time | a few ns | Schematic (PLAN.md) |
| VAPWR current, keyed on | 6.65 mA average (18.4 mA peak) per arm, ~13 mA for both; ~0 when off | Schematic currents ([power.md](power.md)) |
| Off state | both arms driven low | Schematic, by design |
| Weak point | the arm enable (`tx_ls_en`) fails at VDPWR 1.71 V with VAPWR 3.6 V (ss, fs) | Extracted ([verify_supply_mc.md](verify_supply_mc.md)) |

**Receiver**

| Spec | Value | From |
|---|---|---|
| Sensitivity, at the pins | −92 dBm | Mixed-signal: 6/6 on the schematic and 6/6 on the extracted baseband ([verify_2026-10-13.md](verify_2026-10-13.md)) |
| | for ≥ 99 % of chips at every 1.8 V corner, 10–50 °C | Schematic Monte Carlo of the comparator alone (200 mismatch samples per corner); each sample's trim step mapped to dBm with the model. Not extracted ([verify_supply_mc.md](verify_supply_mc.md) "Trim redesign candidates") |
| | −94 dBm about half the time on a typical chip | Model (27/48 sends) and mixed-signal (2/6) |
| | −90 dBm at 85 °C (outside the verified range) | Schematic ([verify_system_2.md](verify_system_2.md)) |
| Input band | 330–560 MHz, covering the TX ring's spread | Schematic (chain gain) |
| Chain gain at 434 MHz | 73–81 dB over corners and temperature (76.7 nominal) | Schematic; each extracted stage is 0.2–0.45 dB below its schematic. The low-gain shunt (off) costs a further 0.65–0.8 dB extracted |
| Low-gain strap (`uio[7:4]` = `1011` at reset) | 9.5–10.4 dB less chain gain; NF +0.4–1.0 dB; sensitivity ~−88 dBm (vs ~−93) | Extracted chain (gain, NF); link model (sensitivity). The chain then tolerates ~2.5× the out → in coupling before it oscillates (1–2 fF at ss 10 °C vs 0.5–1 fF) ([handoff_lna_lo.md](handoff_lna_lo.md)) |
| Noise figure | 9.4–12 dB | Schematic |
| Detector slope | 10–14 mV per dB, falling with power, over ~70 dB | Schematic |
| Detector at idle | 1.49 V | Extracted (1.50–1.54 V schematic corners) |
| Detector at −60 dBm | 1.21 V | Extracted (whole tile) |
| Envelope filter | 14 kHz RC low-pass | Schematic |
| Slow average | τ 0.42 ms | Extracted (0.45 ms schematic) |
| Trim step | 0.136–0.147 mV per LSB, 8 bits | Schematic corners; 0.136 extracted |
| Overload | −10 dBm is fine; a weak signal is missed for 0.25–0.3 ms after it | Mixed-signal ([verify_2026-10-13.md](verify_2026-10-13.md)) |
| VDPWR current | 2.99 mA | Extracted (whole tile); 2.84–2.91 mA schematic corners |

**Link**

| Spec | Value | From |
|---|---|---|
| Chip | 104 µs (8 comparator samples, 13 µs apart) | RTL |
| Burst | 127-chip Gold code, 13.2 ms; 128 codes from 7 switches | RTL |
| One send | 3 bursts, each followed by 64 off chips: 59.6 ms | RTL |
| Detection | score ≥ 97 of 127 chips, 2 of the 3 bursts at the right spacing; then the code is ignored for ~1 s | RTL |
| Signal at 1 m | ~−32 dBm | Bench path loss (−44 dBm at 1 m with the old 1.8 V ring) + 12 dB for the new TX |
| Range | ~80 m, line of sight | Estimate: −92 dBm sensitivity on the bench path loss (1/d^1.89) |
| With fading (±10 dB) | every send gets through down to −90 dBm | Model |
| False toggles | 0 | Model |
| Raw mode (RP2350 data) | a few kbps, DC-balanced coding (Manchester) | Estimate from the filter and the average time constant |

**General**

| Spec | Value | From |
|---|---|---|
| Supplies | VDPWR 1.8 V; VAPWR 3.3 V for the TX output stage | Design |
| Clock | 10 MHz from the demo board | RTL |
| Temperature | 10–50 °C verified | Schematic and extracted corners |
| Area | 3×2 tiles (493 × 226 µm); the digital macro is 200 × 220 µm | Layout |
| Digital timing | met at all 9 corners | Signoff STA (`openlane/radio_digital/signoff/`) |
| Antenna | per board, two ~16.5 cm wires (a dipole); no other parts | Design |

*Corners* are the PDK's fast and slow transistor models. A design that works at all corners and temperatures should work on any chip from the run.

## Schematics

Each link opens the schematic in the online xschem viewer. The block generators are in [`xschem/gen/`](../xschem/gen) and the testbenches in [`sim/`](../sim).

### Top level
- [tt_um_mattvenn_radio](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/tt_um_mattvenn_radio.sch): the TT tile, with the digital macro, the analog block and the pins.
- [radio_analog](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/radio_analog.sch): all the analog blocks, the bias and the decoupling capacitors.

### Transmitter
- [tx_top](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/tx_top.sch): the whole TX chain. There are per-arm enables, so one arm can be driven alone as a fallback (monopole mode).
- [tx_ring](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/tx_ring.sch): the oscillator, a NAND gate (the on/off enable) plus a ring of standard-cell inverters.
- [tx_ls](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/tx_ls.sch): the level shifter from 1.8 V to 3.3 V. Its two latch nodes are naturally opposite in phase, which gives the dipole's two arms.
- [tx_drv](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/tx_drv.sch): thick-oxide buffer tapers into the 3.3 V output drivers, one per arm.

From top to bottom: ring output, the level-shifter latch nodes, the two drivers in antiphase, and the voltage across the dipole.
![TX signal flow](../sim/plots/tx.png)

### Receiver: amplifier chain
- [lna_chain](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/lna_chain.sch): six differential amplifier stages. *Differential* means each stage amplifies the difference between two wires and ignores noise common to both, such as the chip's own 10 MHz clock.
  - [amp_dp](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/amp_dp.sch): stage 1, the low-noise amplifier (LNA).
  - [amp_dpc](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/amp_dpc.sch): stages 2–6. Coupling capacitors set the band and stop small DC offsets building up along the chain.

Left: gain to each stage output, peaking around 433 MHz. Middle: rejection of common-mode and supply noise. Right: noise figure.
![chain](../sim/plots/tb_chain.png)

### Receiver: detector, filter, threshold
- [log_det](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/log_det.sch) / [det_cell](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/det_cell.sch): the log detector, with one rectifier cell per chain stage. A weak signal is only big enough to register at the last stages; as the signal grows, earlier stages saturate one after another. Summing the cells gives an output that is a straight line in dB, so 70 dB of range fits in ~1 V.
  ![log detector](../sim/plots/logdet_taps.png)
- [lpf_rc](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/lpf_rc.sch): a 14 kHz RC low-pass filter, which keeps the chip-rate envelope and removes most of the noise.
- [avg_sc](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/avg_sc.sch): the slow average (τ ≈ 0.45 ms), built from a switched capacitor. A small capacitor clocked by the digital acts as a very large resistor.
- [comp_ct](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/comp_ct.sch): a continuous-time comparator. The filtered signal goes on one input and the average on the other. A second, weak input pair adds the trim.
- [r2r](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/r2r.sch): an 8-bit resistor-ladder DAC (reused from an earlier TT project), driven by the trim servo.

At −70 dBm (fully joined transistor-level run): the detector output, then the filtered signal crossing the slow average, then the comparator output.
![RX at -70 dBm](../sim/plots/rx_joined.png)

At −92 dBm the signal is buried in noise. Here the real RTL servo drives the real DAC and comparator: the trim code settles and dithers, and the burst is still detected.
![RX at -92 dBm](../sim/plots/mixed_-92.png)

### Support
- [bias_gen](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/bias_gen.sch): makes the reference currents and the mid-rail voltage for every analog block.
- [dbg_tg](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/dbg_tg.sch): a switch that connects the detector output to ua[2] in debug mode only.
- [decap_vapwr](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/decap_vapwr.sch) / [decap_vdpwr](https://xschem-viewer.com/?file=https://github.com/mattvenn/ook-asic-radio/blob/main/xschem/decap_vdpwr.sch): on-chip supply decoupling. It supplies the TX's 433 MHz current spikes locally, so they don't disturb the receiver.

### Digital (`radio_digital` macro)
Verilog is in [`verilog/rtl`](../verilog/rtl), hardened with LibreLane to 200 × 220 µm ([`openlane/radio_digital`](../openlane/radio_digital)).
- **TX:** two LFSRs generate the Gold code, and the TX keys the ring with it three times.
- **RX:** samples the comparator every 13 µs, decides each chip by majority vote (8 samples) at 4 timing offsets, and scores the last 127 chips against its own code. It then runs the 2-of-3 burst check and toggles the LED.
- **Trim servo**, the switched-capacitor clocks, the 7-segment display and the debug/raw modes.
- The RTL and the gate-level netlist both pass the cocotb tests ([`verilog/test`](../verilog/test)), which use vectors from the Python model.

## Layout

Each analog block is generated by a Python script using KLayout and the sky130 parametric cells ([`layout/gen/`](../layout/gen)). Every block goes through:
1. DRC (design rule check: can the fab build it?) and LVS (layout vs schematic: is it the same circuit?).
2. Parasitic extraction: the wires' resistance and capacitance are added back into the netlist.
3. Re-simulation, comparing the extracted block with the schematic.

Per-block previews (TT GDS viewer links) are in [layout/README.md](../layout/README.md). The flow and lessons are in [layout.md](layout.md).

### Floorplan
The tile is 3×2 TT tiles (493 × 226 µm). The digital macro takes the right side. The analog blocks are placed so the signal flows a short way from pin to pin:
- The **RX chain** runs along the bottom, starting at the RX pins ua[0]/ua[1]. It is folded into a U so its output stays far from its own input; feedback from the output to the input would make it oscillate.
- The **TX** sits on the left, above its pins ua[3]/ua[4] and away from the chain's input.
- The signal goes up from the chain: **detector → filter / average → comparator**. The **DAC** and **trim** sit next to the macro's trim outputs.
- The **decaps** fill the gaps.

Block placement, orientation and the nets between them:
![floorplan](images/floorplan.png)

Pin positions and the reasons behind them: [layout/floorplan/pins.md](../layout/floorplan/pins.md) and [floorplan_spec.md](floorplan_spec.md).

### The routed tile
The finished tile is DRC and LVS clean. Power delivery (supply resistance, IR drop, TX→RX coupling) is analysed in [power.md](power.md).
![tile](images/tile.png)

## Further reading
- [verification.md](verification.md): how it was tested: RTL, gate level, mixed signal, per block and system level.
- [PLAN.md](../PLAN.md): every design decision and the evidence behind it.
- [STATUS.md](../STATUS.md): current state and next steps.
- [history.md](history.md): per-block simulation results.
- [sim_learnings.md](sim_learnings.md): xschem / ngspice lessons.
