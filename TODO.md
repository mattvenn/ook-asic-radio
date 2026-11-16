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
- [ ] **Find out why the extracted noise runs are so slow** (2026-11-16, the `chain-tall-stages` verification). The
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
