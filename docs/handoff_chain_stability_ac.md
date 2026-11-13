# Handoff: chain stability, AC margin, RC loads and bond-wire coupling (branch `chain-stability-ac`)

From Harald Pretl's design review ([review_harald_2026-11-13.md](review_harald_2026-11-13.md), actions 4, 5 and 6).
Written 2026-11-13. Paste the prompt at the end into a session on sim-0.

## Why

Harald's view is that the most likely way this chip fails is the 80 dB chain oscillating, and that our U-folded layout
is the worst case for it. Today we know stability only from a **kick test** (`sim/chain/stability.sh`): a 1 µA, 1 ns
current kick into `pad_p`, then whether the output envelope grows or decays, swept over an asymmetric coupling
capacitor `Ccpl` from `out_p` back to `pad_p` (or `CNODE`). That gives a pass / fail edge (e.g. 0.5–0.75 fF at ss in
full gain) but no margin, and it only covers the coupling paths we put in. This work adds three things, **all as
simulation, with no change to the design files**:

- **(A) A small-signal stability margin** to go with the kick test: the loop gain through the coupling path, its gain
  and phase margins, and the coupling at which the margin reaches 0 dB, over corners and the strap.
- **(B) RC loads:** how much a defined low-pass in each stage's load (a C across the load R) would add to that margin
  for how much in-band gain. Today the roll-off above the band comes only from the next stage's input C, which isn't
  controlled.
- **(C) Bond-wire / package coupling:** a feedback path the block extraction can't see. The chain output stays on the
  chip, but its RF current returns through the VDPWR / VGND bond wires, which are mutually coupled to the `ua[0]` /
  `ua[1]` input bond wires.

The results decide whether the later layout work (a straight chain, local decap, a lower-gain option; review actions
8–10) is needed and which of it matters most. **Don't redesign or re-lay out anything here.** Report numbers, then stop
for Matt.

## Read first

- `docs/agent_start.md`, `STATUS.md`, `docs/sim_learnings.md` (ngspice traps; read before writing a testbench),
  `docs/verification.md` (sim-0 notes: CPU quota, magic 8.3.642).
- `docs/review_harald_2026-11-13.md`: the review.
- `sim/chain/stability.sh` (the bench you build on), `docs/stability_2026-10-17.md`, and items 3 and 4 plus the
  2026-11-06 follow-up in `docs/verify_lna_lo.md` (the current stability edges, block vs full GDS extraction).
- `xschem/gen/chain.py`: the `lna_chain` / `tb_chain` generator. `CHAIN_PARAMS` has the sizes (stage 1 `rl1` 1 kΩ,
  stages 2–6 `rl2` 4 kΩ, `cin` 2 pF, `rb` 20 kΩ). `xschem/pad_model.sch` is the pad / ESD / mux model in `tb_chain`.
- `sim/chain/mk_pex_tb.py` swaps the extracted chain (`layout/pex/lna_chain.spice`) into `tb_chain`.

## Setup

- `git fetch && git checkout chain-stability-ac`.
- Netlist `tb_chain` into `build/real` as `stability.sh`'s header says, and make the extracted version with
  `mk_pex_tb.py` into `build/pexsim`.
- New scripts go in `sim/chain/`. Results go in **`docs/stability_ac_2026-11.md`**. Commit small and often, to this
  branch only.

## Reference cases

Use these everywhere, so (A), (B) and (C) can be compared:
- **Corners:** tt 27 °C, ss 10 °C (highest gain, ~81 dB), sf 27 °C (the worst strap step), and ff 50 °C (lowest gain,
  sanity check). Add ss 10 °C at VSUP 1.89 V for the final table.
- **Strap:** `VGLO=1.8` (full gain) and `VGLO=0` (low gain).
- **Chain:** the schematic for the sweeps, then the extracted chain (`build/pexsim`) for the final table. Note the
  block extraction is the pessimistic bound for the strap step (verify_lna_lo.md follow-up).
- **Supply:** `stability.sh`'s default, 2 nH and the real `decap_vdpwr`.
- **Coupling:** asymmetric `Ccpl` from `out_p` to `pad_p` and to `o1p` (stage 2's input), 0.01 / 0.1 / 0.2 / 0.5 /
  0.75 / 1 / 1.5 / 2 fF.

## (A) Small-signal stability margin

1. **Loop gain through the coupling path.** Break the loop at `Ccpl` and measure the return ratio T(f), 10 MHz–5 GHz.
   Use Tian's or Middlebrook's method, or (simpler, since the loop is a single capacitor) drive `out_p`'s side of
   `Ccpl` with an AC source while the chain's real output stays loaded as before, and measure what returns at
   `out_p`. Whatever you pick, **write down why it's valid for this loop**. Keep the differential chain's other half
   connected: the coupling is asymmetric on purpose, so the loop goes from `pad_p` differential-and-common through
   the chain. Report |T| and the phase of T.
2. **Margins:** the gain margin (how far |T| is below 1 where the phase of T crosses 0° / 360°) and the phase margin
   (where |T| = 1, if it is reached), and the frequencies. Do it for each corner, strap state and node, and for `Ccpl`
   = 0.1 fF and 1 fF.
3. **Tolerable coupling:** since T scales almost linearly with `Ccpl`, gain margin 0 dB gives the `Ccpl` at which the
   chain oscillates. Tabulate it, and the margin at our 0.1 fF budget, in dB.
4. **Cross-check against the kick test.** Run `stability.sh` at the same cases. The AC edge must agree with the kick
   edge (e.g. ss 10 °C full gain 0.5–0.75 fF). If it doesn't, find out why before going on: a wrong loop break is the
   likely cause.
5. **Wideband check, independent of any coupling path:** Harald's K-factor. Treat the chain as a two-port (`pad`
   differential in, `out` differential out, with the pad model's source impedance), and compute Rollett's K and |Δ|
   (or μ) vs frequency, 10 MHz–5 GHz, at the corners. ngspice 46+ has `.sp` analysis; if it's awkward, compute S or Y
   parameters from two AC runs. Report where K < 1, if anywhere. This shows whether the chain is unconditionally stable
   for any source and load, or only for the ones we simulate.

## (B) RC loads

1. **First, today's roll-off.** For each stage, the -3 dB upper edge of its gain, and the frequency where the
   whole chain's gain falls 20 and 40 dB below its 434 MHz value. From (A), note the frequency where each margin is
   set.
2. **The experiment.** Add a capacitor `Cl` across each stage's load R (both halves, so it stays differential), as a
   **netlist edit in the script** (sed / Python on the netlist, like `stability.sh` does), not in `chain.py`. Sweep:
   - all six stages, then only the last two or three (they have the most gain behind them), then only stage 1;
   - `Cl` so the pole lands at roughly 0.6, 0.8, 1.0, 1.5 and 2 GHz with the stage's R (1 kΩ stage 1, 4 kΩ stages 2–6).
3. **Constraints:** the band is 330–560 MHz (the TX ring's spread; the typical TX is ~448 MHz). Keep the chain's gain
   loss within **0.5 dB at 448 MHz and 1 dB at 560 MHz**, at tt and ss 10 °C. Report NF at 448 MHz too; it should barely
   move.
4. **What it buys:** for the variants that meet the constraints, rerun (A)'s tolerable coupling and the kick edge, at
   ss 10 °C full gain and tt. The headline is the factor of extra coupling margin vs gain lost.
5. **Area:** for the best one or two variants, the capacitor per stage (MIM ~2 fF/µm²) and whether it fits in today's
   stage outline (`layout/gen/lna_chain.py`, the stage cells) or needs the re-layout.

## (C) Bond-wire and package coupling

1. **The path.** Find the TT package and the bond-wire lengths for the analog pins and the supplies. Check the current
   Tiny Tapeout docs and the TT pin map; **don't guess, and quote your source**. If no lengths are available, use 1 nH/mm
   and a 1–3 mm range, and say so.
2. **Model.** Extend `stability.sh` (a copy, e.g. `sim/chain/stability_bond.sh`):
   - a bond-wire L in series with each input (`pad_p`, `pad_n`) between the pad model and the board side;
   - the existing `Lsup` (VDPWR) and `Lgnd` (ground) as the supply bond wires;
   - mutual inductance `K` between the supply / ground wires and the input wires. Asymmetric is what matters: couple
     only to `pad_p`'s wire, or `k` on `pad_p` and `k/2` on `pad_n`. Symmetric coupling is common mode and the chain
     rejects it; check that too and say how much.
   - Sweep k from 0.01 to 0.3 (typical for neighbouring bond wires: 0.1–0.4) at 2 nH and 5 nH.
3. **Results:** the kick and the AC loop gain as in (A), at the reference corners and both strap states. Give the k at
   which the chain oscillates, and how far the plausible range is from it.
4. **Also:** with no `Ccpl` at all and the realistic k, is there a margin left for the 0.1 fF on-chip budget? I.e.
   combine the two paths.
5. Stage-output RF current into the supply is what drives this path. Report the RF current in `Lsup` / `Lgnd` at
   434 MHz with a −60 dBm input (the chain limiting) vs a −90 dBm input, so we know the aggressor's size.

## Report (docs/stability_ac_2026-11.md)

- Method for each of (A), (B), (C), with commands to rerun them.
- (A): one table, corners × strap × node: tolerable `Ccpl` from AC and from the kick, the margin at 0.1 fF (dB), and
  the frequencies. The K-factor result.
- (B): today's roll-off; the variants' in-band loss, NF and margin gain; the area of the best one.
- (C): the package data and source; tolerable k per case; the supply RF current.
- A short **recommendation** for Matt: does the chain need action 8 (straight layout), 9 (local decap), 10 (lower gain)
  or RC loads, in what order, and how much margin each would buy. Recommend; don't implement.
- Update the `lna_chain` row in `docs/verification.md` (one sentence plus the link) and add one line to STATUS.md
  "Start here".

## Rules

- No changes to `xschem/`, `layout/`, `verilog/`, `gds/`, `lef/` or `macros/`. Everything is a netlist edit in a
  script.
- sim-0: the threads of all running ngspice add up to ≤ 28. These decks are small: run them single-threaded, many at
  once.
- If something doesn't make sense (AC and kick disagree, a margin is negative where the kick decays), stop and report
  with numbers. Don't paper over it.
- Push to `chain-stability-ac` only. Matt merges.

## Prompt

```
Read docs/agent_start.md, then docs/handoff_chain_stability_ac.md, and do it on branch chain-stability-ac
(git fetch && git checkout chain-stability-ac). Simulation only: no changes to the design files. Push results to
that branch in small commits; stop and report with numbers when (A), (B) and (C) are done, or if AC and the kick
test disagree.
```
