# To do

Things that aren't chip design work, or that wait for silicon. Add the date and where it came from.

## Tiny Tapeout submission
- [ ] **Mark the project as dangerous in Tiny Tapeout.** It's an uncertified transmitter (README "Radio regulations",
  Harald's review point 15): the flag is an extra layer of protection, so it isn't enabled or demoed casually. Find
  where TT sets it for this shuttle (info.yaml or the submission page) and set it before submitting. (2026-11-14)

## Long simulation runs (before tape-out and while in fab)
- [x] **A whole code through the extracted RX, to an LED toggle** (Harald's review, action 12). **Closed 2026-11-20
  (Matt): not feasible, and its parts are covered.**
  - Cut down to 16 chips to the slicer at −85 dBm, split into 28 RF pieces run in parallel, joined, then the
    extracted mixed-signal bench. The pipeline worked: the schematic version got 0 of 16 wrong.
  - On `rx_t` with noise each piece ran at 0.107 µs/h with the machine full (28 runs share a 16-core CPU, ~3×
    slower each than alone): ~22-27 days. The chain-only deck (extracted chain, schematic detector, tap C lumped)
    would take ~6 days but only joins pieces already tested apart; noise-free `rx_t` is fast but repeats the CW
    drop runs (`cw_drop.py --rx`). Neither run.
  - Covered instead by: joined schematic RX within 0.5 dB of the model, extracted CW drop, the extracted-tile
    noisy pair, and the mixed runs on the extracted baseband (`docs/verify_system_2.md` item 8 reached the same
    view on 2026-11-06).
  - Found on the way: `tb_tile_joined.py`'s noise file times were rounded (fixed; the pair results hold,
    `docs/verify_tall.md` "Joined RX pair"), and `gen_det.py`'s `SHIFT_DB` was set for the old noise (now −5.01 dB).
  - The scripts (`sim/rx/chip16.py`, `sim/rerun/jobs_chip16.py`, `model/chip16_err.py`) are in git history
    (commit 3c7ea1e). Why the extracted noise runs are slow: `docs/verify_tall.md`.
- [x] **Real transient noise** (Harald's review, action 13): VACASK with sky130, or ngspice device noise in transient,
  against today's workaround (an equivalent input noise from a linear analysis, `sim/rx/gen_det.py`, NF 11 dB over
  450 MHz). The case to look for: stage-1 noise driving later stages into limiting. (2026-11-14)
  - Done 2026-11-21 in ngspice with per-device PWL noise sources (`sim/noise/`; VACASK can't read the sky130 models
    without a parser build that isn't possible on the pod), `docs/verify_tall.md` §5 "Device noise in transient".
    Device noise costs ~0.9 dB more than the same NF injected at the antenna, and ngspice's NF 11.0 leaves out 1/f
    (a NaN in the pad switch): real NF 11.6 (thermal) / 12.5 dB (with 1/f). Sensitivity likely ~1.5 dB (up to ~2 dB)
    worse than the mixed bench says.
- [ ] **Recalibrate `gen_det.py` to device noise** (follows action 13): put the noise-only det at the device-noise
  level (Dth, 1.43715 V; or Dall 1.42679 V as the bound), rerun the −92 / −94 dBm paired check to get the sensitivity
  cost directly instead of from the swings.

## Bring-up hardware
- [ ] **RX adapter board** for the TT breakout (Harald's review, action 14; [bringup.md](docs/bringup.md)): SMD
  footprints (0402 / 0603) for a shunt part across the RX pins `ua[3]` / `ua[2]`, a shunt part from each to ground and
  a series part in each, plus an SMA (single-ended) and a balun footprint. Unpopulated by default (0 Ω links in
  series). It's the rescue path if the chain oscillates, and the way into the cabled tests. (2026-11-14)

## Tests and demos
- [ ] **Book the university EM chamber** for the air-link tests (Harald's review, action 15). Until then, keep
  public demos and videos cabled with attenuators, or say they were done in a shielded environment. (2026-11-14)
