# Handoff: tall, thin chain stages, a sketch for a straight chain (branch `chain-tall-stages`)

From Harald Pretl's design review ([review_harald_2026-11-13.md](review_harald_2026-11-13.md), action 8). Written
2026-11-13. Paste the prompt at the end into a session on sim-0.

## Why

Harald's main point: the U fold puts the chain's output stages (st5 / st6) 14 µm across a moat from its input (Cin,
st1), the worst place for them. He suggested a straight chain with **tall, thin stages**. The old straight chain was
268 × 35 µm and didn't fit (docs/history.md). At about twice the height and half the width it would be roughly
134 × 70 µm, about the U's own box (145.4 × 70.5 µm, at tile x 13.14–158.5, y 6.5–77). The chain could then be
straight in its current slot, with the input and output about 120 µm apart and no change to the rest of the floorplan.

A rough sum on paper is ~8 µm too long: input section ~32 + st1 ~22 + 5 × st2–6 ~17 + gaps. Whether it fits depends on
how thin the stages can really be. **This job finds out, by laying out the two stage cells in tall form.** It's a
sketch: new cells beside the existing ones. Nothing in the chain, the tile or the floorplan changes.

The chain can also be flipped (MY), so the input comes in on the left and it flows east. So the cells only need to work
in one direction: **input on the left edge, output on the right.** Which way the chain finally runs, and which `ua`
pins it uses, is a floorplan decision for later.

## Read first

- `docs/agent_start.md` (layout rules: shared code, DRC / LVS / PEX "done" criteria), `STATUS.md`.
- `docs/review_harald_2026-11-13.md`, action 8 and points 5 and 11.
- `layout/gen/amp_dpc.py` and `layout/gen/amp_dp.py`: the current stage cells. Read their header comments; they
  explain the structure, the current-density sizing and the matching. You're re-arranging these, not re-designing
  the circuit.
- `xschem/gen/chain.py` (`CHAIN_PARAMS`, the amp_dp / amp_dpc schematics) and `layout/ref/amp_dp*.spice`.
- `docs/layout.md`: the `lna_chain` section (the fold variants and what each cost in gain), "Checklist", the EM table.
- `layout/gen/lna_chain.py`, header only: the isolation rule and the pins the chain needs (taps o1–o5 to log_det).

## The cells

New generators **`layout/gen/amp_dpc_tall.py`** (cell `amp_dpc_t`) and **`layout/gen/amp_dp_tall.py`** (cell `amp_dp_t`),
with the same circuits and `PARAMS` as today's cells, and the same LVS reference.

Requirements, in order of importance:

1. **Halves stacked, not side by side:** the p half above the n half, mirrored about the cell's horizontal centre
   line. The rails are horizontal and run straight across the cell edge to edge: VSS on the centre line and VDD at top
   and bottom, or the other way round. Pick whichever routes better and say why. `nb` also crosses edge to edge.
2. **The stages abut with no wiring between them.** `inp` / `inn` on the left edge, `outp` / `outn` on the right edge,
   at heights where one stage's outputs land on the next stage's inputs, and the rails and `nb` line up. amp_dp's
   right edge has to match amp_dpc's left edge the same way.
   - **Polarity:** the top half's drain is `outn` (Mp drives outn), so a top-to-top abutment joins `outn` to the next
     stage's top gate. Because the cell is mirror-symmetric, flipping every other stage (MX) puts the n half on top.
     `outn` then lands on `inn`, with no crossover and no schematic change. Design for that, and check it in the strip
     below. Any crossover inside the cell costs asymmetric C.
3. **Width as small as it will go.** Target ≤ 16 µm for amp_dpc and ≤ 22 µm for amp_dp. Height up to ~70 µm (the
   chain's box; ~73 at most).
   - Today's half-width is set by the 12.07 µm square Cs MIMs (0.3 pF each). Make them rectangular, tall and narrow,
     still over the devices.
   - The load resistors (high_po_0p69, L 7.38 µm in amp_dpc; high_po_1p41, L 3.14 µm in amp_dp) can go beside the
     devices or above them.
4. **Taps to log_det.** In a straight chain, log_det sits beside the chain's long edge, so both output nets must be
   reachable from that edge: say the top edge. Reserve a route for the lower half's output up through, or beside, the
   cell (a met3 column, or met4 clear of the MIM top-plate strips). Reaching it from either long edge is better still,
   since the chain may be flipped. Note the C this adds to the output; the fold variants show how much a few fF cost.
5. **amp_dp keeps its matching:** the A B B A common-centroid pair (stage 1 has DC gain). Keep the current-density
   sizing in both cells: the 1.2 mA tail in amp_dp, the via counts and bar widths. Use multiple vias wherever they
   fit (Harald, point 11). Share diffusion between adjacent devices where it's natural.

## Checks per cell

- `layout/check.sh amp_dpc_t` / `amp_dp_t`: magic and KLayout DRC 0, antenna 0, LVS match against the same reference
  as today's cell (copy `layout/ref/amp_dpc.spice` to `layout/ref/amp_dpc_t.spice` with the subckt renamed, or
  however `check.sh` wants it).
- `layout/pex.sh amp_dpc_t`, then the existing testbench on the extracted cell. `tb_amp_dpc.py --pex` reads
  `layout/pex/amp_dpc.spice` by name: add an option to point it at another file (`--pex-file`). **Don't overwrite
  today's `layout/pex/amp_dpc.spice` / `amp_dp.spice`.**
- Compare with today's extracted cells, at tt and ss 10 °C: gain at 434 MHz, the −3 dB edge, output C (in fF), and
  any asymmetry between the halves.

## Then, if the cells come out: a stage strip

A quick throwaway generator (`layout/gen/chain_strip_tall.py`) that abuts amp_dp_t and 5 × amp_dpc_t (alternating MX),
with no input section. Then:
- DRC and LVS against a stages-only reference (st1 to st6 in series, `nb` / VDD / VSS shared);
- PEX and the chain's gain at 434 MHz and the peak (tt, ss 10 °C), against the stages of today's extracted chain;
- its exact length.

On paper only, size the **input section** in a column of the strip's height: Cin_p / Cin_n (2 pF each, ~971 µm² of
MIM), Mref and the Rb pair. Add it to the strip's length and say whether the whole chain fits in 145.4 µm, with how
much to spare or how much short. Also, from the strip, give the x of each tap (o1–o5, out) along the chain.

## Report (`docs/tall_stages_2026-11.md`)

- A picture of each cell (KLayout screenshot) and of the strip.
- One table per cell, tall vs today: W × H, gain at 434 MHz, −3 dB edge, output C, DRC / LVS.
- The strip: its length and its gain against today's chain stages. The input-section estimate, and **fits / doesn't
  fit**, and by how much.
- What set the width of each cell (MIM, devices, resistor, routing), and what it would take to go thinner.
- Anything a full straight-chain re-layout needs to know: pin heights, the tap routes, where the supply should enter.
- One line in STATUS.md "Start here".

## Rules

- New files only. No changes to `amp_dp.py`, `amp_dpc.py`, `lna_chain.py`, any committed GDS, `layout/pex/`,
  `xschem/` or the floorplan.
- Shared code (`lay.py`, `passives.py`, `rows.py`): avoid changes. If one is needed, follow the agent_start rule
  (regenerate the blocks that use it and XOR their GDS against the committed ones).
- Simulation threads on sim-0: keep the total of running ngspice threads ≤ 28. Another session may be running the
  chain stability sweeps (`chain-stability-ac`).
- Push to `chain-tall-stages` only. Matt merges.

## Prompt

```
Read docs/agent_start.md, then docs/handoff_tall_stages.md, and do it on branch chain-tall-stages
(git fetch && git checkout -b chain-tall-stages origin/main). New cells only: don't change the existing chain,
its cells or the floorplan. Push in small commits; stop and report when the two cells (and the strip, if they
come out) are done, or if a cell can't get near its target width.
```
