# Handoff: end-to-end simulations on the extracted tile

Prompt for a new session (written 2026-10-09 by the top-level layout session). Paste it as is.

---

The 3x2 tile is assembled, routed, DRC and LVS clean (`docs/history.md` "Top level"). Your job:
**run the end-to-end tests on the extracted tile, explain where they differ from the schematic, and fix or report.**
First explain two anomalies, then the TX loss, then the long runs. Commit and push to `main` as you go (small
commits; other sessions push to `main` too).

## Read first
- `docs/agent_start.md`, `STATUS.md`, `docs/sim_learnings.md` (ngspice traps).
- `docs/history.md` "Top level" (what was built, the numbers so far). `docs/layout.md` "Top level" (flow, extraction).

## Tools
- Mac: `tools/osic-mac <cmd>` from the repo root; sim scripts take `OSIC=$PWD/tools/osic-mac`.
- **Run slow jobs in the background and end the turn** (never wait on them with a foreground loop) so Matt can keep
  talking. **Don't run ngspice jobs in parallel.**

## What exists
- **Tile GDS:** `build/top/tt_um_mattvenn_radio.gds`. If `build/` is missing, rebuild it:
  `tools/osic-mac klayout -b -r layout/gen/top.py && tools/osic-mac python3 layout/gen/route.py`.
- **Extraction:** `tools/osic-mac bash layout/pex_tile.sh {lvs|c|rc}` writes `layout/pex/radio_analog_<mode>.spice`.
  - It's the tile minus the digital macro, flattened (the substrate is VGND), with a wrapper subckt `radio_analog` in
    the schematic's port order.
  - Inter-block nets keep the route labels as names (`det`, `lpf`, `avg`, `trim`, `vcm`, …); block-internal nets are
    `<block>_0.<net>`.
  - Times: lvs ~5 s, c ~10 s, rc ~11 s (85k R).
- **Runner:** `python3 sim/top/tb_tile.py sch lvs c rc` runs `xschem/tb_radio_analog.sch` with `radio_analog` from
  the schematic or an extracted mode.
  - It prints the deck's RESULT lines and the TX analysis (frequency, P into 73 Ω, on / off time, currents).
  - The probes `xana.det` etc. are mapped to `xana.x1.det` for the extracted modes.
  - ~3 min per mode without R; rc will be longer.

## Results so far (schematic / connectivity only / + wiring C)

| | sch | lvs | c |
|---|---|---|---|
| RX on, I(VDPWR) | 2.974 mA | 2.986 | 2.978 |
| all off, I(VDPWR) | 0.908 µA | 0.910 | **1.589** |
| vcm | 1.201 V | 1.201 | 1.201 |
| det idle | 1.521 V | 1.491 | 1.490 |
| lpf idle | 1.521 V | 1.491 | **0.891** |
| det at −60 dBm | 1.206 V | 1.097 | 1.202 |
| TX f | 485 MHz | 679 | 532 |
| TX P into 73 Ω | +4.05 dBm | +2.87 | +2.32 |
| TX on / off | 3.2 / 3.9 ns | 3.8 / 3.3 | 8.2 / 7.7 |

- det idle 1.49 vs 1.52 V is known: the log_det block extraction gives the same (high-po contact R).
- The lvs-mode TX frequency is high because the schematic ring carries wiring-estimate caps (`cw`) that a bare
  netlist lacks.

## Do, in order
1. **The c-mode anomalies.**
   - lpf idles at 0.89 V (det 1.49 V; lpf_rc should pass DC), and the all-off current rises by 0.68 µA. Capacitors
     can't change a DC operating point, and the devices on `lpf` are identical in the lvs and c netlists. So find what
     differs: operating-point convergence (`.option` / gmin, `.nodeset`), a resistor or diode that only c mode emits,
     node-name aliasing in the c netlist, or something else.
   - Diff the two netlists' non-C elements first.
2. **TX −1.7 dB, slow edges (c mode).**
   - Split it: per-block PEX is known good (`sim/tx/tb_tx_drv.py --pex` −0.32 dB; `tx_ring` extracted ~530 MHz tt).
     So look at the top-level wiring: the ring → ls → drv nets, the 2 µm neck on tx_p through the chain
     (`layout/gen/top_nets.py`), and the TX supply and ground routing R.
   - Use rc mode for this, or swap in only the TX part.
   - Report the dB budget per cause and what would recover it, e.g. a wider tx_p route, which needs a chain/route
     change (Matt decides).
3. **Full RC:** `tb_tile.py rc`. Compare RX op, det at −60 dBm, TX.
4. **Then the long runs, on the extracted tile:**
   - the joined RX sensitivity run (`sim/rx/joined.sh` style, ~2 h per level: −90 dBm first, in the background);
   - `sim/tx/tb_tx.py`;
   - the mixed-signal run (`sim/mixed/`: RTL servo + the extracted r2r and comp_ct, i.e. the tile).
   Reference numbers from the schematic runs: RX sensitivity ≈ −92…−93 dBm worst case (10–50 °C), TX +3.7…+3.9 dBm,
   trim step 0.062–0.076 mV/LSB, comp offset +0.56 mV, det idle ~1.49 V.
5. **Report** each step's numbers in STATUS.md / `docs/history.md`. A new runner goes under `sim/top/`.

## Don't
- Don't edit the layout generators (`layout/gen/top.py`, `route.py`, `top_nets.py`, `decap.py`, block generators):
  report what needs changing. A power-delivery session is working from `docs/handoff_power.md` at the same time.
