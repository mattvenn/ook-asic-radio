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
    right chip bits. **Chips 68-83 of code 0** (`1011010111100010`, Matt 2026-11-20) at **−85 dBm**, clear of
    the edge so a fail means something. **Pass: ≤ 3 of the 16 chips wrong on the slicer's best phase** (Matt), the
    correlator's 30/127 budget scaled to 16. The system model (`model/chip16_err.py`, tt + extracted loss, NF +2.2
    dB, 80 windows) at −85 dBm: 1.0 chips wrong expected in this window, P(≤ 3) 99.9 %.
    The first choice, chips 3-18 (`0000011010110111`), was wrong: they follow the 64-chip gap, where the
    slicer's threshold average and trim have seen only noise, so the first five zeros are coin flips (model ~50 %
    each) and chip 18, the fourth 1 of a run, is wrong 80 % of the time: 3.7 expected, P(≤ 3) 46 % whatever the
    circuit. The schematic dry run got exactly those (4, 5, 6, 18 wrong). The model numbers first quoted here (6.9 /
    11.1 / 13.0 % chip errors) were for code 0x5A over whole bursts, not this window. Errors pile up on runs: the
    threshold follows a long run and the trim servo pulls the comparator to 50 %. The mixed bench's 2.08 ms lead-in
    is the code's chips 47-66, built from simulated chips of the same value.
  - **2026-11-20 status: no long run going; next step waiting on Matt.**
    - Schematic dry run (`CHIP16_TAG=chip16sch CHIP16_BASE=build_tall/tb_logdet.spice`, chips 68-83, −85 dBm):
      **0 of 16 wrong** (phase 4; other phases 0-2). Jobs: 28 pieces 58-61 min, join 0.2, mixed 46.0, check 0.2.
      Seams between pieces: ±1.7 mV mean, ~9 mV rms at 10 ns (~1 mV over 1 µs), not shrinking over the 3 µs
      warm-up; small against the ±2.9 mV per-chip signal.
    - **`rx_t` with noise is too slow for a week.** With the machine full (28 runs, 1 thread each; the VM's 30
      CPUs are a 16-core Ryzen 7950X) each run slows ~3×. Measured µs of sim per hour per run
      (`build/chip16_ab`, `build/chip16_nn`):

      | Deck, noise, runs × threads | Per run, µs/h | Machine, µs/h | 1953 µs of record, days |
      |---|---|---|---|
      | `rx_t`, filesource, 28 × 1 | 0.107 | 3.0 | 27 |
      | `rx_t`, PWL, 28 × 1 | 0.130 | 3.64 | 22 |
      | `rx_t`, PWL, 14 × 2 | 0.239 | 3.34 | 24 |
      | `rx_t`, PWL, 1 alone | 0.41 | - | - |
      | `rx_t`, filesource, 1 alone | 0.32 | - | - |
      | chain + schematic det + lumped tap C, PWL, 28 × 1 | 0.504 | 14.1 | 5.8 |
      | `rx_t`, **no noise**, 50 ps max step, 28 × 1 | 1.24 | 34.8 | 2.3 |

      Matt: no test longer than a week. The chain-only deck (a9fbe58: `chip16.py` BASE / LEVEL now point at it,
      −85.5 dBm) was started and stopped: it only joins pieces already tested apart. **Revert BASE / LEVEL to
      `rx_t` / −85 or to whatever the next step needs.**
    - **Noise-free `rx_t` needs a max step ≤ 100 ps** (1.5 µs of a 1 chip at −85 dBm, quiet machine): det drop
      from no-signal (1.48935 V) 4.68 mV at 50 ps (2215 s), 4.31 at 100 ps (1475 s), 2.76 at 200 ps (1004 s),
      0 with no limit (56 s: steps over the carrier). 50 ps not checked against finer.
    - **Proposed (not started):** (1) noise-free `rx_t` end to end: short on / off / edge runs at 50 ps (det is
      flat within a chip without noise), build the 38-chip det waveform, extracted mixed bench + slicer check
      (~5 h; connectivity and gain, passes trivially at −85); same on the schematic for the extracted-vs-schematic
      swing. (2) Margin: schematic deck with noise at −87.2 dBm (extracted NF +2.2 dB) and lower, ~2 h each.
    - `sim/top/tb_tile_joined.py` `noise_file` wrote times with `%.6g`: the same repeated-time bug, from 10 µs
      on. Fixed 2026-11-20 (8cb3622); the pair results hold (`docs/verify_tall.md` "Joined RX pair"). ~1.9 ms of RF with warm-up: ~925
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
