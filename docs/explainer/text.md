<!-- The explainer's words, one section per page in tour order. Edit here, or press e on the page
     (served by docs/explainer/edit.py) to type into it. Format and placeholders: textfile.py. -->

## intro
name: A radio on a tiny open-source chip
short: The idea
cap: My first radio chip: transmitter and receiver in six Tiny Tapeout tiles, with two bare wires for an antenna.

My first semiconductor radio, and one of the first radios on a Tiny Tapeout shuttle. The transmitter and the receiver share six tiles, about 0.1 mm² of silicon.

It's designed to use the minimum of external components: an external 10 MHz clock and two 16.5 cm long wires for the antenna. It should work to around 80 metres in good conditions.

The design can either transmit or receive, so two demo boards are needed to demonstrate. Pressing reset on one toggles the LED on the other.

## air
name: Predicting range
short: Range
cap: With the new transmitter the receiver should see about −32 dBm at 1 m. At ~80 m it is down to −92 dBm: over a million times weaker, below its own noise.

On the bench, I used an earlier [ring oscillator design](https://tinytapeout.com/chips/ttsky25b/tt_um_mattvenn_analog_ring_osc) as a transmitter. I used 14.5 cm wire dipoles held parallel and measured the received signal with a scope. The results are the white dots on the graph.

That transmitter was weak: a 1.8 V pad with only about 200 mV of swing, −8.5 dBm. The new transmitter has 3.3 V drivers on both wires of the dipole. After the chip's pads, the simulation gives about 1.2 V peak-to-peak across the dipole at 485 MHz, around 5 times the old swing: about +3.5 dBm, so 12 dB more. The solid line is the bench measurement shifted up by those 12 dB: about −32 dBm at 1 m.

Further out the reflection off the ground is expected to cancel more and more of the direct path. With both boards 1 m above the ground that takes over near 6 m, and the two-ray model then loses 40 dB per decade.

The receiver has a sensitivity of about −92 dBm, so I'm expecting a range of about 80 m.

## ook
name: Trick 1: keep the radio simple
short: On-off keying
sub: On-off keying (OOK)
cap: Trick 1: on is a 1, off is a 0. The receiver only measures energy, so the carrier needs no crystal.

On-off keying is the simplest form of amplitude-shift keying. The transmitter switches a carrier around 450–470 MHz (aimed at the 433 MHz band) on and off to send 1s and 0s.

Each on/off bit lasts 104 µs, about 48,000 carrier cycles (the docs and code call these bits chips).

The receiver doesn't tune to the carrier: it only measures how much RF energy arrives, anywhere in 330–560 MHz. Loud is 1, quiet is 0.

Near the limit, a 1 hardly stands out from the noise and many bits come out wrong (red): move the boards closer and they clear.

## code
name: Trick 2: send a pattern, not a bit
short: The code
sub: A 127-bit Gold code, checked by correlation
cap: Trick 2: send a 127-bit pattern. Noise matches ~64; 97 is a detection, even with a quarter of the bits wrong.

The transmitter sends a fixed pattern of 127 bits, a [[gold|Gold code]] picked by the DIP switches, three times.

The receiver doesn't need every bit right. After each bit it [[corr|counts how many of the last 127 match]] the pattern it expects.

With no signal, the bits are random and about half match by luck: around 64. A detection needs 97 or more. That is far more than noise produces, yet still lets about a quarter of the bits be wrong.

The [[led|LED]] toggles when two of the three bursts are detected.

## link
name: All together
short: Both boards
cap: Putting it together: the code goes out three times, some bits arrive wrong, the score still clears 97 and the LED toggles.

Two boards with the same chip on each, one set to transmit, the other to receive. If the receiver detects its code in two of the three bursts, it toggles the LED.

## chip
cap: Functional diagram

## chip:tx
cap: The transmitter: digital code → ring oscillator → level shifter → two drivers → dipole.

## gold
name: Gold code (digital)
cap: The digital generates the Gold code from two 7-bit LFSRs and sends it three times.

Seven DIP switches pick one of 128 Gold codes: two 7-bit LFSRs, the second started later by the switch value, XORed together.

Flip the switches on the right.

127 noise-like bits, half on, half off. Each bit lasts 104 µs, so one burst takes 13.2 ms.

The TX keys the [[tx_ring|ring]] with the code three times, with 64 silent bits between bursts.

## tx_ring
name: tx_ring
sub: Free-running ring oscillator
cap: A free-running ring of inverters. No crystal, no PLL: the receiver doesn't care about the exact frequency.

22 standard-cell inverters and a NAND gate form a ring of 23 stages.

Its frequency depends on the chip, the temperature and the supply voltage. I'm expecting between 450 and 470 MHz.

The ring is turned on and off with a NAND gate enable.

## tx_ls
name: tx_ls
sub: level shifter 1.8 V → 3.3 V
cap: The level shifter's two latch nodes are opposite in phase: one for each arm of the dipole.

For a more powerful transmitter, we want to convert the 1.8 V output of the ring to 3.3 V.

It also provides an inverted output to drive the [[tx_drv|dipole's two arms]].

## tx_drv
name: tx_drv ×2
sub: output drivers, one per dipole arm
cap: Two 3.3 V drivers in antiphase put about +3.5 dBm into the wire dipole.

A tapered buffer: a NAND (the enable) and five thick-oxide 3.3 V inverters, getting wider towards the pin (PMOS 1.3 → 5 → 20 → 81 → 144 µm).

The last one is big enough to drive the pin and antenna, but far too big for the small [[tx_ls|level shifter]] to switch quickly; stepping up 4× per stage gets the edge through fastest.

One drives ua[3], the other ua[4]. Each driver swings about 2.4 V peak-to-peak on the die, but the pad's inductance and capacitance leave about 0.65 V on each wire at 485 MHz.

Driving the two arms in antiphase doubles that across the dipole: {dipole_swing} in simulation, and +4.1 to +4.3 dBm into it across the process corners (+3.1 to +3.4 dBm with the extracted layout).

## chip:rx
cap: The receiver: amplify, measure energy, compare, then let the digital decide.

## lna_chain
name: lna_chain
cap: Six differential stages, ~80 dB of gain (10,000×). The last stages limit: that is used by the detector.

Six differential stages, ~80 dB of gain in total (10,000× in voltage).

Differential means each stage amplifies the difference between two wires and ignores noise common to both, like the chip's own 10 MHz clock.

Stage 1 is the low-noise amplifier, and the chain's noise figure is about 11 dB. Stages 2–6 have a capacitor between their sources: full gain at RF, almost none at DC, so offsets don't build up along the chain.

## log_det
name: log_det
sub: successive-detection log detector
cap: The log detector turns RF power into a voltage that is a straight line in dB: 70 dB in ~1 V.

One rectifier cell per [[lna_chain|chain stage]]. A weak signal only registers at the last stages; as it grows, earlier stages saturate one after another.

Summing the cells gives an output that is a straight line in dB, so 70 dB of range fits in ~1 V, about 13 mV per dB. Note it goes down as the signal goes up.

The cells rectify the carrier, and the detector's output node smooths it with its own ~20 MHz low-pass: the output follows the carrier's strength, settling in ~16 ns, and only a few mV of ripple are left of the carrier.

On the bottom graph, the carrier is keyed on at 0.5 µs and off at 2.5 µs: about 870 cycles while on, so the whole view draws it as its envelope; zoom in to see the cycles arrive and the detector settle.

## lpf_rc
name: lpf_rc
sub: 14 kHz RC low-pass
cap: A 14 kHz low-pass keeps the bit-rate envelope and removes most of the noise.

The [[log_det|log detector]] has already removed the carrier with its own ~20 MHz low-pass, so its output follows how strong the carrier is.

But that output is noisy (grey): the [[lna_chain|amplifiers]] have no narrow filter (the receiver accepts anything from 330 to 560 MHz), so they amplify noise across that whole wide band along with the signal, and the detector turns it into a jittery voltage.

This 14 kHz RC low-pass, about 1,500 times slower, smooths away everything faster than a 104 µs bit, leaving the on/off envelope.

## avg_sc
name: avg_sc
sub: switched-capacitor slow average
cap: The threshold is the signal's own slow average: the code is half on, half off, so it sits in the middle.

The threshold for the [[comp_ct|comparator]]. A Gold code is half on and half off, so the slow average of the signal sits in the middle of it at any range. A small capacitor clocked by the digital (sc_phi1/2) acts as a very large resistor, giving a time constant of about 0.45 ms.

## comp_ct
name: comp_ct
sub: continuous-time comparator
cap: The comparator decides on or off. Near the limit the difference is ~1 mV, as big as the noise.

[[lpf_rc|Filtered signal]] on one input, [[avg_sc|slow average]] on the other: is this bit on or off? Near the sensitivity limit the difference is ~1 mV and the noise is about as big, so many decisions are wrong.

That's fine: the [[corr|correlator]] only needs most of them right.

The digital [[slicer|samples it]] every 13 µs, 8 times per bit.

## r2r
name: r2r + trim servo
sub: 8-bit DAC, offset trim
cap: An 8-bit DAC servo cancels the comparator's own offset in ~0.07 mV steps.

The receiver would work without this, but it helps to increase sensitivity and hence range.

Every [[comp_ct|comparator]] has a small built-in error from imperfectly matched transistors, its offset: it might only flip when one input is 2 mV above the other.

Near the sensitivity limit the signal is only ~1 mV, so without correction the comparator would always say 1 (or always 0).

Every 13 µs sample, the digital steps an 8-bit DAC up for a 1 and down for a 0: 7 mV at the DAC, ~0.07 mV at the comparator through a weak second input pair.

It settles where the comparator says 1 half the time, which cancels the offset{comp_high}.

## slicer
name: bit slicer (digital)
sub: majority vote per bit
cap: Eight samples per bit, majority vote, at four timing offsets at once.

The [[comp_ct|comparator]] is read every 13 µs: 8 samples per 104 µs bit.

Many samples are wrong near the limit, so the 8 are combined by majority vote (5 or more 1s means on).

The receiver doesn't know where each bit starts, so instead of recovering the transmitter's timing it runs four slicers at once, their windows offset by 2 samples; one of them is always nearly lined up.

Each keeps its last 127 bit decisions for the [[corr|correlator]].

## corr
name: correlator (digital)
sub: score the last 127 bits
cap: Count matches with the expected code: chance is ~64, 97 is a detection. Lots of wrong bits are fine.

After every bit, count how many of the last 127 [[slicer|decisions]] match this board's own [[gold|code]].

Chance gives ~64. 97 or more is a detection: 6σ above chance.

Even when a quarter of the decisions are wrong the score still clears 97.

## led
name: 2-of-3 + LED
cap: Two detections one burst period apart toggle the LED. Noise and other codes don't.

The TX sends the burst three times. The LED toggles only if two [[corr|detections]] arrive one or two burst periods (191 bits) apart, within ±2 bits, then the code is ignored for ~1 s.

Other codes, garage remotes and noise don't toggle it.

## bias_gen
name: bias_gen
sub: support

Makes the reference currents and the mid-rail voltage for every analog block. On-chip decoupling capacitors supply the TX's current spikes at the carrier frequency locally so they don't disturb the receiver.
