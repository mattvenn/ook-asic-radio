# Tall, thin chain stages: a sketch for a straight chain (2026-11-13)

Harald Pretl's review ([review_harald_2026-11-13.md](review_harald_2026-11-13.md), point 5, action 8) suggested a straight
chain of tall, thin stages in place of the U fold. This job laid out the two stage cells in tall form and abutted them
into a stage strip, to find out whether a straight chain fits the U's slot (145.4 × 70.5 µm). Brief:
[handoff_tall_stages.md](handoff_tall_stages.md). Branch `chain-tall-stages`. Nothing in the chain, the tile or the
floorplan changed: these are new cells beside the old ones.

**Result: it fits, with room to spare.** The two cells came out well under their target widths. The six stages abut
into a strip of **78.9 × 63.5 µm**. With an input section of about 38.6 µm (sized on paper below), the straight chain is
about **117.5 µm long, 27.9 µm shorter than the slot**, and 7 µm lower. The stages themselves gain more than today's
(+2.7 dB over the chain, unloaded, at tt). The output taps are the cost: drawn as full-height met4 columns, so that each
output reaches either long edge, they take about 0.8 dB per stage and leave the strip 1.6 dB below today's U chain.
How the taps are run is the main open choice for a full re-layout.

All extractions use magic 8.3.642 (`OSIC_MAGIC=$HOME/.local/magic642/bin`), as for the committed ones.

## The cells

Files: `layout/gen/amp_dpc_tall.py` (cell `amp_dpc_t`), `layout/gen/amp_dp_tall.py` (`amp_dp_t`), GDS in `layout/`,
LVS references in `layout/ref/`, extractions in `layout/pex/`. Same circuits and `PARAMS` as `amp_dpc` / `amp_dp`; the
reference is today's (written by `lay.write_ref`), with only the Cs MIM's W and L changed to the drawn rectangle.

Both cells share one frame, so any stage abuts any other:

- **Halves stacked.** The p half sits above the cell's horizontal centre line and the n half is its mirror image below
  (the generator draws one half cell and places it twice).
- **VSS and nb on the centre line, VDD at the top and bottom edges.** VSS goes in the centre because that is where
  the circuit starts. Going out from the centre, each half has the tail (its sources go straight down into the ring
  and rail on met1), the nb strap, the pair, the load and then VDD, so nothing crosses. nb runs on met2 sandwiched
  inside the VSS rail (met1 + met3, with met2 strips at its edges), and each tail's gate strap drops to it on one
  met2 riser. With nb on the centre line too, a flipped (MX) cell lines up with an unflipped one. The two VDD rails
  are joined inside each cell by a met4 column at its left edge.
- **Signals on met2 at the pair's gate height**, ±12.37 µm from the centre. The input enters from the left edge
  straight onto the gate strap. The output (drain bar and the load's bottom head, joined by a met2 spine) leaves at
  the same height to the right edge. So a stage's outputs land on the next stage's inputs.
- **Polarity:** the top half's drain is `outn`. Flipping every other stage puts `outn` onto the next stage's `inn`,
  with no crossover and no schematic change. LVS of the strip checks this, and un-flipping stage 2 fails it.
- **Taps:** each output also runs up a met4 column the full height of the cell, at the right edge, so both outputs
  reach either long edge. A VDD column sits between the two tap columns as a shield (see below).

Pin heights, from the cell's bottom edge (H = 63.5 µm, centre line 31.75 µm):

| | layer | y (µm) |
|---|---|---|
| VDD rails | met1–met3 | 0–1.5 and 62.0–63.5 |
| VSS rail | met1–met3 (met2 at its edges) | 30.75–32.75 |
| nb | met2 | 31.55–31.95 |
| stage signals (in, left edge / out, right edge) | met2 | 19.18–19.59 (n half) and 43.91–44.31 (p half) |
| amp_dp_t inputs (left edge, to the input section) | met2 | inn 17.97–18.47, inp 45.03–45.53 |
| taps | met4 columns, full height | outn at W − 1.95 … W − 1.55, outp at W − 0.55 … W − 0.15 |

### amp_dpc_t (stages 2 to 6)

![amp_dpc_t](images/tall_amp_dpc_t.png)

Fig. 1. amp_dpc_t, 11.7 × 63.5 µm. The tails sit at the centre with the pair and load above (and mirrored below), the
Cs plates over each half, and the tap columns and VDD shield at the right edge.

- Each half's Cs bottom plate (its source node) covers the half. capm starts above a band where the tail-drain and
  pair-source bars via2 up into the plate, since no via2 may sit under capm. The caps are 6.8 × 21.33 µm rectangles
  with the same C as today's 12.07 µm squares: the model's C is Ca (w + 0.15)(l + 0.15), so the drawn area is kept on
  that basis. The top plates cross over on met4 strips: Cs_a's (left) goes down into plate B's band and Cs_b's (right)
  goes up into plate A's.
- The load is a single 0p69 segment beside the pair. A lone segment fails rpm.1 / psdm.1, so the generator draws
  rpm and psdm 1.3 µm wide over it.
- Cut counts are all at or above the 2× EM rule; the generator prints the check.

### amp_dp_t (stage 1)

![amp_dp_t](images/tall_amp_dp_t.png)

Fig. 2. amp_dp_t, 20.4 × 63.5 µm, in amp_dpc_t's frame. The two pair rows (A B B A over B A A B) sit above and below
the split tail, with the loads to their right.

- **Matching kept.** Each pair row is four groups of 4 fingers (5 µm), with the outer two being the half's own device
  and the inner two the other half's. So the top row is A B B A and the bottom row B A A B (A = Mp, B = Mn). Each
  device has half its fingers in each row, and its centroid is the cell centre in x and y. There is one orientation
  per row, and all sources are on the tail.
- The price is four crossings of the centre, all on met4 (there is no MIM in this cell). Each row's inner-group
  drains go to the other half's output, and its inner gate strap goes to the other half's input. The output
  crossings are the full-height tap columns themselves. The input crossings are two short columns left of the rows,
  away from the outputs. The two halves' tail nodes join on a short met4 column (it carries no DC, by symmetry).
- The tail is 2 × nf 20 (3 µm fingers, as the reference diode), one row per half. 1.2 mA tail; via1 / via2 / via3
  counts meet the 2× rule (generator printout).

### Results per cell

Testbenches: `sim/amp_dpc/tb_amp_dpc.py` and `sim/amp_dp/tb_amp_dp.py`, which now take `--pex-file=<path>` (another
extraction; the subckt name is read from the file) and `--temp=<C>`. Today's `layout/pex/amp_dpc.spice` /
`amp_dp.spice` were not touched. The output C is the extracted total on the net (all R-split sub-nodes).

Table I. amp_dpc: tall vs today (extracted; 434 MHz, differential).

| | today `amp_dpc` | `amp_dpc_t` (taps) | `amp_dpc_t`, no tap columns |
|---|---|---|---|
| W × H | 30.54 × 21.21 µm | **11.7 × 63.5 µm** | 11.7 × 63.5 µm |
| gain tt / ss 10 °C | 13.69 / 14.36 dB | 13.25 / 13.89 dB | **14.05 / 14.75 dB** |
| peak tt | 13.75 dB at 374 MHz | 13.36 dB at 357 MHz | 14.07 dB at 392 MHz |
| −3 dB tt | 153–1010 MHz | 147–963 MHz | 159–1081 MHz |
| −3 dB ss 10 °C | 166–953 MHz | 159–913 MHz | 174–1014 MHz |
| output C (outp / outn) | 18.9 / 24.8 fF | 31.3 / 33.4 fF | 13.7 / 13.7 fF |
| imbalance at 434 MHz | −32.3 dB | −50.4 dB | −72.8 dB |
| DRC / antenna / LVS | clean | magic 0, KLayout 0, antenna 0, LVS match | clean |

Table II. amp_dp: tall vs today (extracted; 434 MHz).

| | today `amp_dp` | `amp_dp_t` (taps) |
|---|---|---|
| W × H | 36.4 × 20.73 µm | **20.4 × 63.5 µm** |
| gain tt / ss 10 °C | 15.58 / 16.45 dB | **15.55 / 16.42 dB** |
| peak tt | 15.76 dB at 205 MHz | 15.78 dB at 196 MHz |
| −3 dB edge tt / ss 10 °C | 1499 / 1364 MHz | 1380 / 1261 MHz |
| output C (outp / outn) | 40.4 / 42.6 fF | 55.8 / 57.1 fF |
| imbalance at 434 MHz | −49.6 dB | −54.8 dB |
| DRC / antenna / LVS | clean | magic 0, KLayout 0, antenna 0, LVS match |

Like for like (no taps, since today's cells have none), amp_dpc_t gains 0.36 dB on today's cell. Its outputs carry
13.7 fF against 18.9 / 24.8 fF, because nothing crosses the cell any more, and the halves are balanced. Both tall
cells are much better balanced than today's, as the mirror geometry intended.

**The tap columns** add about 18 fF per output on amp_dpc_t (10.7 fF to VSS, 7.3 fF to VDD) and cost 0.8 dB per
stage. A first version without the VDD shield coupled the two columns 6.9 fF output to output (which counts twice
for the differential signal) and gave 12.95 dB. On amp_dp_t, with its 1 kΩ loads, the columns cost nothing visible.

## The stage strip

`layout/gen/chain_strip_tall.py` abuts amp_dp_t and 5 × amp_dpc_t, flipping stages 2, 4 and 6 (MX). It has no input
section and no wiring between the stages. Its ports are stage 1's inputs, stage 6's outputs, the taps o1–o5 (the
met4 columns' top ends), nb, VDD and VSS.

![chain_strip_t](images/tall_chain_strip_t.png)

Fig. 3. chain_strip_t, 78.9 × 63.5 µm: stage 1 on the left, then stages 2 to 6. The stages abut with no wiring
between them.

- **Checks:** magic and KLayout DRC 0, antenna 0, LVS match against st1 to st6 in series (`layout/ref/chain_strip_t.spice`,
  with the taps as ports). Mutation test: with stage 2 left unflipped, LVS fails ("Top level cell failed pin matching").
- **Length:** exactly 78.9 µm (20.4 + 5 × 11.7).
- **Gain:** `sim/chain/tb_strip_tall.py <strip|u|blocks> [corner] [--temp=C]`. All three cases are driven
  differentially at stage 1's gates (1.2 V DC), with the chain's bias and the outputs and taps unloaded. "u" is
  today's extracted U chain (`layout/pex/lna_chain.spice`, driven at its g1p / g1n nodes, so its input section is out
  of the way). "blocks" is today's block extractions in series, with no wiring between them.

Table III. Stage gain, stage 1 gates to stage 6 output (434 MHz; peak; −3 dB edges; gain per stage st1 … st6).

| | tt 27 °C | ss 10 °C | per stage, tt (dB) |
|---|---|---|---|
| tall strip, tap columns | **79.29 dB**, peak 79.81 at 348 MHz, 231–577 MHz | 83.31 dB, peak 83.83 | 15.34 12.33 12.48 12.42 12.49 14.22 |
| tall strip, no tap columns | 83.58 dB, peak 83.72 at 391 MHz, 251–644 MHz | 87.89 dB, peak 88.01 | 15.41 13.22 13.37 13.24 13.58 14.77 |
| today's U chain (extracted) | **80.87 dB**, peak 81.23 at 369 MHz, 240–594 MHz | 85.05 dB, peak 85.37 | 15.52 11.70 13.00 12.92 13.10 14.62 |
| today's blocks in series | 81.61 dB, peak 81.90 at 369 MHz, 243–605 MHz | 85.82 dB, peak 86.08 | 15.43 12.79 12.94 12.86 13.04 14.53 |

The output imbalance at 434 MHz is −44.8 dB for the strip with taps, −73.5 dB without, and −31.4 dB for today's chain.
These figures are higher than the 76.65 / 80.78 dB quoted for the chain in docs/layout.md, because that bench includes
the input section and the outputs' loads. Compare the rows here with each other, not with those numbers.

The strip without tap columns has 2.7 dB more gain than today's chain (2.0 dB more than the blocks), and nearly all
of that is the shorter output nets. Today's stage 2 gives 11.70 dB in the U against 12.79 dB as a block, a 1.1 dB loss
in this unloaded bench. That is the turn's o2 wiring plus the low-gain shunt across o2, which loads it even when off.
The strip has neither, so this row overstates what a full straight chain would give at stage 2. With full-height tap columns, the strip is 1.6 dB below today's chain at tt (1.7 dB at
ss 10 °C).

**Tap x positions** (column centres, from the strip's left edge): o1n 18.65, o1p 20.05, o2n 30.35, o2p 31.75,
o3n 42.05, o3p 43.45, o4n 53.75, o4p 55.15, o5n 65.45, o5p 66.85, outn 77.15, outp 78.55 µm. Along the chain, with
the input section's 38.6 µm in front, add 38.6: o1 about 57.3–58.7, o2 69.0–70.4, o3 80.7–82.1, o4 92.4–93.8,
o5 104.1–105.5, out 115.8–117.2 µm.

## The input section, on paper

The input section is Cin_p / Cin_n (2 pF each), Mref and the Rb pair. Here it is laid out the same way as the stages:
Cin_p in the top half and Cin_n in the bottom half of a column the strip's height, with the rails continued through
it.

- **Cin.** Today's caps are 31.16 µm squares, so the model's (w + 0.15)(l + 0.15) is 980 µm². In a half, capm can run
  from 2.4 µm (1.2 µm off the VSS rail's met3, plus the plate's 0.2 µm) to 28.85 µm (the same off the VDD rail),
  which gives l = 26.45 µm and w = 980 / 26.6 − 0.15 = **36.7 µm**.
- **Mref and the Rb pair** go under the Cin plates, as they do today. The Rb pair is two side-by-side 0p35 segments
  of 19.1 µm (so their rpm merges), about 1.3 µm wide. Mref is W 6 nf 2 / L 0.5, about 1.3 × 3 µm. Both fit easily in
  the 36.7 × 26 µm under each plate.
- **Width:** 0.5 µm at the pad-side edge, plus 0.2 + 36.7 + 0.2 µm of plate, plus about 1 µm for the top-plate drops
  to amp_dp_t's inputs (met2 at 18.0–18.5 and 45.0–45.5 µm). amp_dp_t's nearest met3 is 1.2 µm inside its own edge,
  so the plate can run right up to the boundary. That makes about **38.6 µm**.

**Whole chain: 38.6 + 78.9 = about 117.5 µm against 145.4 µm. It fits, with about 27.9 µm to spare**, and is 63.5 µm
tall against the slot's 70.5 µm. Two variants buy back length:
- Without VDD rails through the input section (it needs no VDD), Cin is about 34.2 µm wide and the chain about 115 µm.
- If the input column uses the slot's full 70.5 µm height, Cin is about 30 µm wide and the chain about 111 µm.

The input and the output are then about 117 µm apart at the two ends, with stages 2 to 5 between them. The isolation
(out → input coupling, budget ≤ 0.1 fF at ss 10 °C) can only be extracted once the input section is drawn.

## What set the widths, and how to go thinner

- **amp_dpc_t (11.7 µm; target ≤ 16).** The devices need only 7.3 µm (the ring round the nf 6 tail). The width is
  set by the Cs plate (6.8 µm of capm) plus its keep-outs. The plate must sit 1.2 µm from any unrelated met3: on the
  right, that means the tap columns' met3 landings, and those columns plus the shield take 2.6 µm. On the left, the
  previous cell's landings sit across the boundary, which leaves 1.3 µm. To go thinner:
  1. use the slot's full height (capm up to about 25 µm tall), giving about 10.7 µm;
  2. drop the shield and spread the tap columns instead (about −0.7 µm);
  3. land the taps outside the plates' height range, so the 1.2 µm keep-out goes (about −1 µm).
- **amp_dp_t (20.4 µm; target ≤ 22).** The tail sets the width: nf 20 of 3 µm fingers per half is 16.3 µm of
  diffusion. The pair row (11.1 µm) beside its load, plus the input columns, comes to about 17.5 µm, and the output
  columns need 2.1 µm at the right edge. Folding the tail alone barely helps. To go thinner:
  1. put the load above the pair (there are about 17 µm of free height per half);
  2. share diffusion between the pair's groups (all four groups' sources are the tail);
  3. fold the tail into two rows.
  Together these give about 14 µm.
- **Multiple vias** (Harald's point 11): every landing is a cut array as wide as the strip or bar allows. The
  narrowest landings are single-row via1 on the 0.42 µm met2 bars.

## For a full straight-chain re-layout

- **Pin heights:** see the table above. The input section has to bring Cin's top plates to amp_dp_t's left edge at
  18.0–18.5 µm (inn) and 45.0–45.5 µm (inp), on met2.
- **Taps:** decide where log_det sits first. Full-height columns (as drawn here) let the chain flip either way, but
  they cost about 0.8 dB per amp_dpc stage. A column to one edge only, from the output's own height, would be about
  half that on average. It would be asymmetric, though: 19.4 µm for the output on that edge's side and 44.1 µm for
  the other one. With stages alternately flipped, which output that is alternates too. Running log_det's tap wires
  straight off the right-edge output tracks between stages is another option. Whatever the choice, the tap wires
  will load the stages the way the U's tap wires do (o1 +14 fF there).
- **Supply:** the VSS rail (met1–met3, 2 µm) and the VDD rails (met1–met3, 1.5 µm) run the full length, and every
  cell joins the two VDD rails on met4. The chain draws about 3.0 mA (1.2 mA in stage 1, 5 × 0.36 mA in stages 2 to 6,
  plus the reference). The rail resistance end to end is about 1–2 Ω, so the drop is a few mV. Feed both rails from
  the stage-1 end, which carries the biggest current, with a dedicated trunk as in the power fix. Keep the feed away
  from stage 6, so that no shared supply impedance sits between the output stage and the input.
- **Stability:** the strip without taps has 88 dB at ss 10 °C, 3 dB more than today's chain. A straight chain puts
  the output about 117 µm from the input (the U had 14 µm across the moat). But more gain means a smaller coupling
  budget: re-run `sim/chain/stability.sh` on the real chain and extract the out → in coupling.
- **Low-gain shunt (`lna_shunt`, across o2):** not in the strip. Today it sits at the U's turn by the o2 columns: o2p,
  421 Ω, PMOS W 18 / L 0.15, 421 Ω, o2n, with the gate driven from `lna_lo_n` through 20 kΩ and a 5 × 5 µm MOS cap to
  VDD. A straight chain needs it symmetric across o2p / o2n, most simply as a narrow column between stages 2 and 3.
  That costs a few µm of length (of the about 28 µm spare) and adds its off-state C to o2, as it does today.
- **Height:** the cells are 63.5 µm, set by amp_dpc_t's caps at 11.7 µm wide. The slot allows 70.5 µm, which is the
  first lever if length gets tight.

## Not done

- No input section was drawn, so there is no full-chain extraction, coupling check or stability run. The strip has
  no loads on its taps, and `tb_strip_tall` reports stage gain only.
- No corners beyond tt and ss 10 °C, and no Monte Carlo of amp_dp_t's pair, whose matching is common-centroid by
  construction.
