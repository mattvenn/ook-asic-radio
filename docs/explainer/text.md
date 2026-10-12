<!-- The explainer's words, one section per page in tour order. Edit here, or press e on the page
     (served by docs/explainer/edit.py) to type into it. Format and placeholders: textfile.py. -->

## intro
name: A radio on a tiny open-source chip
short: The idea
sub: my first semiconductor radio
cap: My first radio chip: transmitter and receiver in six Tiny Tapeout tiles, with two bare wires for an antenna.

My first semiconductor radio, and one of the first radios on a Tiny Tapeout shuttle. The transmitter and the receiver share six tiles, about 0.1 mm² of silicon. The 433 MHz carrier comes from a [[tx_ring|ring of inverters]], with no crystal and no PLL. The antenna is two bare wires, with no parts on the board around the chip. The only thing it borrows from the board is a 10 MHz clock for timing. Two boards run the same chip: one sends a code, and the other toggles an [[led|LED]] when it hears it.

## air
name: How weak does the signal get?
short: Over the air
sub: received power vs distance, two wire dipoles
cap: At 1 m the receiver sees −44 dBm. At ~45 m it is down to −94 dBm: 100,000× weaker, below its own noise.

A normal radio uses crystals, filters and tuned circuits. This one has none of them, so how much signal is there to work with? On the bench, with an earlier chip (ttsky25b, its ring at 518 MHz) and 14.5 cm wire dipoles held parallel, the receiver got −44 dBm at 1 m, falling as 1/d^1.89 out to 4 m. Further out the reflection off the ground cancels more and more of the direct path. With both boards 1 m up that takes over near 6 m, and the two-ray model then loses 40 dB per decade. On that model the −94 dBm sensitivity is reached at about 45 m: 100,000× weaker than at 1 m, and below the receiver's own noise. Distances past 4 m are that model, not a measurement.

## ook
name: Trick 1: keep the radio simple
short: On-off keying
sub: on-off keying (OOK)
cap: Trick 1: on is a 1, off is a 0. The receiver only measures energy, so the carrier needs no crystal.

The transmitter switches a 433 MHz carrier on and off, at about +4 dBm, and that is all it does. The receiver doesn't tune to the carrier: it only measures how much RF energy arrives, anywhere in 330–560 MHz. Loud is 1, quiet is 0. That is why the carrier can be sloppy, and a [[tx_ring|free-running ring of inverters]] is good enough. Each on/off bit lasts 104 µs, about 45,000 carrier cycles (the docs and code call these bits chips). Near the limit, though, a 1 hardly stands out from the noise and many bits come out wrong (red): move the boards closer and they clear.

## code
name: Trick 2: send a pattern, not a bit
short: The code
sub: a 127-chip Gold code, checked by correlation
cap: Trick 2: send a 127-chip pattern. Noise matches ~64; 97 is a detection, even with a quarter of the chips wrong.

The transmitter sends a fixed pattern of 127 chips, a [[gold|Gold code]] picked by the DIP switches, three times. The receiver doesn't need every chip right. After each chip it [[corr|counts how many of the last 127 match]] the pattern it expects. Noise matches about half, ~64. 97 or more is a detection, 6σ above chance, so a quarter of the chips can be wrong and the code still gets through. The [[led|LED]] toggles when two of the three bursts are detected. This is what lets the receiver work where the bits on their own are lost in the noise.

## link
name: Does it get through?
cap: Putting it together: the code goes out three times, some chips arrive wrong, the score still clears 97 and the LED toggles.

Two boards run the same chip: the left one sends its code three times, the right one toggles its LED when it hears two of them. Each antenna is two bare wires. Move the received-power slider to move the boards apart. Click a board to open its signal chain, the gap for how power relates to distance, the LED for how a send is confirmed, or the bits below for the idea.

## chip
cap: Functional diagram

## chip:tx
cap: The transmitter: digital code → ring oscillator → level shifter → two drivers → dipole.

## gold
name: Gold code (digital)
sub: radio_digital macro, TX side
cap: The digital generates the Gold code from two 7-bit LFSRs and sends it three times.

The 7 DIP switches pick one of 128 Gold codes: two 7-bit LFSRs, the second started later by the switch value, XORed together. Flip the switches below. 127 noise-like bits, half on, half off. Each bit lasts 104 µs, so one burst takes 13.2 ms. The TX keys the [[tx_ring|ring]] with the code three times, with 64 silent bits between bursts.

## tx_ring
name: tx_ring
sub: free-running ring oscillator
cap: A free-running ring of inverters. No crystal, no PLL: the receiver doesn't care about the exact frequency.

A NAND gate (the on/off enable) plus a ring of standard-cell inverters. No crystal: wherever it lands in 330–560 MHz the receiver still works. It runs at {f_mhz} MHz in simulation (tt), and silicon ran at ×0.87 of simulation on the bench chip. In simulation it starts on the first edge after the enable (zoom below), and the voltage across the dipole reaches full swing {on_ns} ns after the enable rises and dies away {off_ns} ns after it falls: about two carrier cycles each way.

## tx_ls
name: tx_ls
sub: level shifter 1.8 V → 3.3 V
cap: The level shifter's two latch nodes are opposite in phase: one for each arm of the dipole.

Turns the 1.8 V [[tx_ring|ring]] into 3.3 V swings. Its two latch nodes are naturally opposite in phase, which gives the [[tx_drv|dipole's two arms]] for free.

## tx_drv
name: tx_drv ×2
sub: output drivers, one per dipole arm
cap: Two 3.3 V drivers in antiphase put about +4 dBm into the wire dipole.

A tapered buffer: four thick-oxide 3.3 V inverters, each about 4× wider than the one before (PMOS 1.3 → 5 → 20 → 81 µm). The last one is big enough to drive the pin and antenna, but far too big for the small [[tx_ls|level shifter]] to switch quickly; stepping up 4× per stage gets the edge through fastest. One drives ua[3], the other ua[4]. Driving the two arms in antiphase puts the full swing across the dipole: {dipole_swing} in simulation, and +3.7 to +3.9 dBm into it across the process corners. Per-arm enables allow a monopole fallback.

## chip:rx
cap: The receiver: amplify, measure energy, compare, then let the digital decide.

## lna_chain
name: lna_chain
sub: 6 differential amplifier stages
cap: Six differential stages, ~80 dB of gain (10,000×). The last stages limit: that is used by the detector.

Six differential stages, ~80 dB of gain in total (10,000× in voltage). Differential means each stage amplifies the difference between two wires and ignores noise common to both, like the chip's own 10 MHz clock. Stage 1 is the low-noise amplifier, and the chain's noise figure is about 11 dB. Coupling capacitors between stages stop DC offsets building up.

## log_det
name: log_det
sub: successive-detection log detector
cap: The log detector turns RF power into a voltage that is a straight line in dB: 70 dB in ~1 V.

One rectifier cell per [[lna_chain|chain stage]]. A weak signal only registers at the last stages; as it grows, earlier stages saturate one after another. Summing the cells gives an output that is a straight line in dB, so 70 dB of range fits in ~1 V, about 13 mV per dB. Note it goes down as the signal goes up. The cells rectify the 434 MHz carrier, and the detector's output node smooths it with its own ~20 MHz low-pass: the output follows the carrier's strength, settling in ~16 ns, and only a few mV of ripple are left of the carrier. Below, the carrier is keyed on at 0.5 µs and off at 2.5 µs: about 870 cycles while on, so the whole view draws it as its envelope; zoom in to see the cycles arrive and the detector settle.

## lpf_rc
name: lpf_rc
sub: 14 kHz RC low-pass
cap: A 14 kHz low-pass keeps the bit-rate envelope and removes most of the noise.

The [[log_det|log detector]] has already removed the 434 MHz carrier with its own ~20 MHz low-pass, so its output follows how strong the carrier is. But that output is noisy (grey): the [[lna_chain|amplifiers]] have no narrow filter (the receiver accepts anything from 330 to 560 MHz), so they amplify noise across that whole wide band along with the signal, and the detector turns it into a jittery voltage. This 14 kHz RC low-pass, about 1,500 times slower, smooths away everything faster than a 104 µs bit, leaving the on/off envelope.

## avg_sc
name: avg_sc
sub: switched-capacitor slow average
cap: The threshold is the signal's own slow average: the code is half on, half off, so it sits in the middle.

The threshold for the [[comp_ct|comparator]]. A Gold code is half on and half off, so the slow average of the signal sits in the middle of it at any range. A small capacitor clocked by the digital (sc_phi1/2) acts as a very large resistor, giving a time constant of about 0.45 ms.

## comp_ct
name: comp_ct
sub: continuous-time comparator
cap: The comparator decides on or off. Near the limit the difference is ~1 mV, as big as the noise.

[[lpf_rc|Filtered signal]] on one input, [[avg_sc|slow average]] on the other: is this bit on or off? Near the sensitivity limit the difference is ~1 mV and the noise is about as big, so many decisions are wrong. That is fine: the [[corr|correlator]] only needs most of them right. The digital [[slicer|samples it]] every 13 µs, 8 times per bit.

## r2r
name: r2r + trim servo
sub: 8-bit DAC, offset trim
cap: An 8-bit DAC servo cancels the comparator's own offset in ~0.07 mV steps.

Every [[comp_ct|comparator]] has a small built-in error from imperfectly matched transistors, its offset: it might only flip when one input is 2 mV above the other. Near the sensitivity limit the signal is only ~1 mV, so without correction the comparator would always say 1 (or always 0). Every 13 µs sample, the digital steps an 8-bit DAC up for a 1 and down for a 0: 7 mV at the DAC, ~0.07 mV at the comparator through a weak second input pair. It settles where the comparator says 1 half the time, which cancels the offset{comp_high}. In this simulation a behavioural stand-in plays the digital servo; a mixed-signal run with the real RTL settles the same way at −94 dBm.

## slicer
name: bit slicer (digital)
sub: majority vote per bit
cap: Eight samples per bit, majority vote, at four timing offsets at once.

The [[comp_ct|comparator]] is read every 13 µs: 8 samples per 104 µs bit. Many samples are wrong near the limit, so the 8 are combined by majority vote (5 or more 1s means on). The receiver doesn't know where each bit starts, so instead of recovering the transmitter's timing it runs four slicers at once, their windows offset by 2 samples; one of them is always nearly lined up. Each keeps its last 127 bit decisions for the [[corr|correlator]]. Below: green votes are right, red wrong, grey a window split half and half.

## corr
name: correlator (digital)
sub: score the last 127 bits
cap: Count matches with the expected code: chance is ~64, 97 is a detection. Lots of wrong bits are fine.

After every bit, count how many of the last 127 [[slicer|decisions]] match this board's own [[gold|code]]. Chance gives ~64. 97 or more is a detection: 6σ above chance. Even when a quarter of the samples are wrong the score still clears 97.

## led
name: 2-of-3 + LED
sub: burst check
cap: Two detections one burst period apart toggle the LED. Noise and other codes don't.

The TX sends the burst three times. The LED toggles only if two [[corr|detections]] arrive one or two burst periods (191 bits) apart, within ±2 bits, then the code is ignored for ~1 s. Other codes, garage remotes and noise don't toggle it.

## bias_gen
name: bias_gen
sub: support

Makes the reference currents and the mid-rail voltage for every analog block. On-chip decoupling capacitors supply the TX's 433 MHz current spikes locally so they don't disturb the receiver.
