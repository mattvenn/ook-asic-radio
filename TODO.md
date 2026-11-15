# To do

Things that aren't chip design work, or that wait for silicon. Add the date and where it came from.

## Tiny Tapeout submission
- [ ] **Mark the project as dangerous in Tiny Tapeout.** It's an uncertified transmitter (README "Radio regulations",
  Harald's review point 15): the flag is an extra layer of protection, so it isn't enabled or demoed casually. Find
  where TT sets it for this shuttle (info.yaml or the submission page) and set it before submitting. (2026-11-14)

## Long simulation runs (before tape-out and while in fab)
- [ ] **Multi-day joined run** on the extracted tile, sending a whole code (Harald's review, action 12). Today a
  30 µs on / off pair stands in for it. Run in the background on sim-0 once the tall-chain tile's PEX is in. (2026-11-14)
- [ ] **Real transient noise** (Harald's review, action 13): VACASK with sky130, or ngspice device noise in transient,
  against today's workaround (an equivalent input noise from a linear analysis, `sim/rx/gen_det.py`, NF 11 dB over
  450 MHz). The case to look for: stage-1 noise driving later stages into limiting. (2026-11-14)

## Bring-up hardware
- [ ] **RX adapter board** for the TT breakout (Harald's review, action 14; [bringup.md](docs/bringup.md)): SMD
  footprints (0402 / 0603) for a shunt part across the RX pins `ua[3]` / `ua[2]`, a shunt part from each to ground and
  a series part in each, plus an SMA (single-ended) and a balun footprint. Unpopulated by default (0 Ω links in
  series). It's the rescue path if the chain oscillates, and the way into the cabled tests. (2026-11-14)

## Tests and demos
- [ ] **Book the university EM chamber** for the air-link tests (Harald's review, action 15). Until then, keep
  public demos and videos cabled with attenuators, or say they were done in a shielded environment. (2026-11-14)
