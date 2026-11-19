# To do

Things that aren't chip design work, or that wait for silicon. Add the date and where it came from.

## Tiny Tapeout submission
- [ ] **Mark the project as dangerous in Tiny Tapeout.** It's an uncertified transmitter (README "Radio regulations",
  Harald's review point 15): the flag is an extra layer of protection, so it isn't enabled or demoed casually. Find
  where TT sets it for this shuttle (info.yaml or the submission page) and set it before submitting. (2026-11-14)

## Long simulation runs (before tape-out and while in fab)
- [ ] **A whole code through the extracted RX, to an LED toggle** (Harald's review, action 12). Today a 30 µs on / off
  pair stands in for it. One unbroken run can't reach a whole code: the extracted tile ran at ~2 µs/h (2026-10-11,
  possibly throttled by the old 8-CPU quota), so 400 µs - three chips - took ~8 days, and one 13.2 ms burst would take
  months. Plan, two runs that check each other (2026-11-15):
  - **Run 1, split, the whole path.** The RF half (pads -> chain -> detector) only remembers a few hundred ns, so it
    runs in parallel pieces: `rx_t` extracted (`sim/chain/mk_pex_rx.py`), ~20 µs each plus a few µs of warm-up, keyed
    434 MHz for a real Gold code at about −90 dBm, each piece its own slice of one numpy noise waveform (read
    through a filesource, as `tb_tile_joined.py pair`). The det pieces are joined and drive one run of the
    mixed-signal bench (`sim/mixed/`: extracted LPF, averager, comparator, r2r; the RTL trim servo and correlator),
    which handles ms of baseband in hours. The LED needs two events one burst period apart (191 chips ± 2,
    `model/radio.py` pairing), so the stimulus is burst + 64-chip gap + the **same** burst waveform again one period
    later: 191 chips of RF (~1.5× one burst). The gap is simulated, not repeated (the averager and trim would see a
    periodic noise pattern). Pass: an event with score ≥ 97 on each burst, and the LED toggles. The second burst's
    noise is the first one's, so this proves the path, not a detection rate (the model-driven mixed runs with many
    seeds do that).
  - **Run 2, unbroken, four chips.** The whole extracted tile in one transient (`tb_tile_joined.py run`: shared
    supplies, sc clocks, baseband loading det), sending the code's first four chips with the same noise waveform.
    Run 1's piece boundaries are placed inside those four chips (mid-chip and on on / off edges); det and LPF from
    the two runs are compared there. If they agree, the pieces are good for the whole code; if not, the difference
    is what the split misses (an RF-side memory across a boundary, baseband or supply coupling back into the RF).
  - **Cost:** time `rx_t` and the extracted tile first (a short run of each). If `rx_t` manages 5-10 µs/h, run 1's
    RF (19.9 ms) is ~2,000-4,000 run-hours: about one to two weeks on sim-0, in fab rather than before tape-out; run 2
    ~8 days on a few threads, alongside other work. Neither is started.
  - **2026-11-19: timed on idle sim-0.** 2 µs at −90 dBm (fixed noise, full gain), four runs at once (12 of 28
    CPUs; `build/piece_timing/`):

    | Deck | 2 threads, min | 4 threads, min | Speed, µs/h |
    |---|---|---|---|
    | `rx_t` extracted (chain + detector + tap wiring) | 216 | 221 | 0.55 |
    | `lna_chain_t` extracted + schematic detector | 58 | 58 | 2.07 |

    More threads don't help, so pieces should run on 1-2 threads each, as many at once as fit. With 20 µs pieces
    plus 3 µs warm-up, run 1's 19.9 ms of RF is ~42,000 run-hours on `rx_t` (~4 months at 14 at once) and ~11,000
    on the chain-only deck (~33 days at 14, ~16 days at 28 if 1 thread is as fast and a full machine doesn't slow
    each run; neither is measured yet). Neither fits a week as planned: shorten the stimulus or the extracted part.
  - **2026-11-19, plan changed (Matt): 16 chips to the slicer, not a whole code to the LED.** The GL sims are trusted
    for the slicer, correlator, pairing and LED, so the extracted run only has to show the analog path delivers the
    right chip bits. Chips 3-18 of code 0 (`0000011010110111`: 8 on, 8 off, runs of 1-5) at **−85 dBm**, clear of
    the edge so a fail means something. **Pass: ≤ 3 of the 16 chips wrong on the slicer's best phase** (Matt), the
    correlator's 30/127 budget scaled to 16. The system model (`model/chip16_err.py`, 80 windows a case) at −85 dBm:
    chip errors 6.9 % tt, 11.1 % tt + extracted loss (NF +2.2 dB), 13.0 % fs 50 °C + extracted loss; worst window 1 /
    3 / 3 errors, so a fail means the extracted path is clearly worse than the model. "All 16 correct" would fail
    about 1 run in 3 here (needs about −78 dBm). The mixed bench starts with
    the trim at its settled code from the model and a short noise-only lead-in. ~1.9 ms of RF with warm-up: ~925
    run-hours chain-only + lumped tap C (1.4-2.8 days), ~3,500 on `rx_t` (5-10 days). Run 2 (unbroken tile) shrinks
    to 2 chips around a piece boundary. Before choosing the deck: time chain-only + lumped tap C, 1 thread, 28 at
    once, and compare its det with `rx_t`.
- [x] **Find out why the extracted noise runs are so slow** (2026-11-16, the `chain-tall-stages` verification). The
  `nt_pex_*` jobs (`sim/logdet/noise_tran.sh`, 3 µs with `gen_noise.py`'s PWL noise, `rx_t` swapped in) took ~14-16 h
  each against the job file's 10 min: 150-260 ns of sim time per hour. The schematic version takes 1.5 min. Two
  suspects:
  - The netlist: `rx_t` (chain + detector, 1.65 MB, ~41,700 R) replaced last run's chain-only extraction (827 KB,
    ~22,000 R). That alone should cost 2-4x, not ~100x.
  - The noise file: every noise log, sch and pex, has 80,000 "vnz_n has non-increasing PWL time points" warnings.
    Repeated or backwards time points can force tiny time steps, which cost more the bigger the netlist. On the same
    `rx_t` deck a CW input runs at ~3 µs/h (`cw_drop --rx`), ~15x faster than with noise.

  Three 0.5 µs timing runs separate them: the old chain-only deck with the same noise, `rx_t` with the same noise,
  and `rx_t` with the PWL time points cleaned up. If it's the noise file, fix `gen_noise.py` and check that the
  schematic det levels don't move. Then put the measured time in `jobs_tall.py`'s `est`.
  - **2026-11-17: not the noise file.** Timing to 1.2 µs, old and fixed noise file take the same time: schematic
    0.8 min, `lna_chain_t` alone 44 / 48 min, `rx_t` 172 / 172 min. So it's the `rx_t` netlist (3.6× the chain-only
    deck) and ~2× from the main run's load. `jobs_tall.py` keeps the measured ~15 h. Faster next time: run the
    noise levels on the chain-only deck and only noise-only plus one level on `rx_t`.
  - **2026-11-17: a bug in the noise file, found on the way.** `gen_noise.py` wrote times to 5 significant figures,
    so from 1 µs on every other point repeats a time (20,000 per source). Fixed (7 figures); results in
    [verify_tall.md](docs/verify_tall.md) "Follow-ups". The schematic det **does** move with the fixed
    file (noise-only +5.7 mV at full gain): before the next run, redo `gen_det.py`'s `SHIFT_DB` (noise-only 1.439 V)
    and the `lo_gain.py` reference levels from the fixed noise.
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
