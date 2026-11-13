# Chain stability: small-signal margin, RC loads and bond-wire coupling (2026-11-13)

This doc answers actions 4, 5 and 6 of [Harald Pretl's design review](review_harald_2026-11-13.md), from the
handoff [handoff_chain_stability_ac.md](handoff_chain_stability_ac.md). It is simulation only: nothing in `xschem/`,
`layout/` or `gds/` changed. Every variant is a netlist edit made by a script.

## Summary

- **(A) The kick test now has a small-signal margin, and the two agree.** The AC loop gain through the coupling
  capacitor `Ccpl` gives the coupling at which the chain oscillates to within 1.5 % of the kick-test edge in all
  20 schematic cases. The worst case is ss 10 °C, 1.89 V, full gain, `Ccpl` to stage 2's input (`o1p`): it oscillates
  at 0.346 fF on the schematic and 0.485 fF on the extracted chain. Against the 0.1 fF budget that is a gain margin of
  **10.7 dB (schematic) and 13.7 dB (extracted)**. The low-gain strap adds 7.4–11.5 dB. The extracted layout's own
  out → in coupling (1.44e-4 fF, [verify_lna_lo.md](verify_lna_lo.md)) is about 70 dB below the extracted edge (0.485 fF).
- **The chain is unconditionally stable as a two-port** (Rollett K ≥ 10.5 extracted, ≥ 1200 schematic, |Δ| < 1, at
  every corner from 10 MHz to 5 GHz). It can't oscillate on its own with any passive source or load. Only a feedback
  path from its output back to its input can make it oscillate.
- **(B) RC loads trade gain for margin at about 1:1** (1.0–1.3 dB of margin per dB of in-band gain, for coupling to
  `pad_p`; the strap gives 0.84–0.95 dB per dB). The loop's phase crosses 0° at 620–740 MHz
  on the schematic and at **466–537 MHz on the extracted chain, inside the 330–560 MHz band**. A first-order pole
  can't separate that from 448 MHz. Within the gain-loss limit (0.5 dB at 448 MHz, 1 dB at 560 MHz) the best variant
  buys ×1.07 (0.6 dB).
- **(C) Bond-wire coupling can't make the chain oscillate in this model**, at any k up to 1, at any corner, with
  either strap state, wire L 2 or 5 nH, and either orientation. With the plausible k ≤ 0.3 it lowers the tolerable
  on-chip `Ccpl` by at most 8.6 %. The 0.1 fF budget keeps ≥ 10.6 dB of margin with both paths together.
- **Recommendation:** none of actions 8–10 or RC loads is needed for stability on this evidence. If one is done as
  insurance against paths that aren't modelled (board, antenna, the real package), a lower-gain option (action 10)
  is the only one of them that buys margin for every path, at about 1 dB per dB. Details at the end.

## Setup

- Bench: `stability.sh`'s, rebuilt in Python by [sim/chain/stab_deck.py](../sim/chain/stab_deck.py) so that the new
  scripts share it. It uses `tb_chain` (the pad / ESD / mux model on both inputs, 36.5 Ω per side), board 1.8 V →
  0.5 Ω → `Lsup` → chip VDPWR, chip ground → `Lgnd` → board ground, 2 nH each, and the real `decap_vdpwr`. Its
  kick gives the same numbers as `stability.sh` to every printed digit (ss 10 °C, 0.45 and 0.5 fF).
- Schematic: `tb_chain` netlisted to `build/real`. Extracted: `layout/pex/lna_chain.spice` (the block extraction,
  the pessimistic bound for the strap step) swapped in with `mk_pex_tb.py` (`build/pexsim`).
- ngspice 47, sky130A as in the image, one thread per deck, up to 24 decks at once on sim-0.
- Corners: tt 27 °C, ss 10 °C (highest gain), sf 27 °C, ff 50 °C, ss 10 °C at VSUP 1.89 V. Strap: `VGLO` 1.8 (full
  gain) and 0 (low gain). `tb_chain`'s 1 % pair mismatch (`mm=0.01`) stays in.

## (A) Small-signal stability margin

### Method

**Loop break** ([sim/chain/stability_ac.py](../sim/chain/stability_ac.py)). In the closed loop, `Ccpl` carries
jωC (v(out_p) − v(X)) from `out_p` into X (`pad_p` or `o1p`). The bench lifts `Ccpl`'s `out_p` end onto a 1 V AC
test source and puts a C of the same value from `out_p` to ground. Then:

- X sees jωC (v_t − v(X)). That is the closed-loop expression with v(out_p) replaced by v_t, so this side is exact.
- `out_p`'s load is jωC v(out_p) instead of jωC (v(out_p) − v(X)). The difference is v(X) / v(out_p), one over the
  chain's forward gain. That is small wherever |T| can approach 1.

So the return ratio is T = v(out_p) / v_t, and the chain oscillates at T = +1. Both halves of the chain stay
connected and only `out_p` is coupled, so T carries both the differential and the common-mode routes.

**Margins.** The gain margin is −20 log|T| where the phase of T crosses 0°; the smallest such margin counts. T is
linear in `Ccpl`: the 0.1 fF and 1 fF runs give the same critical coupling to within 0.8 %. So
`Ccpl_crit` = `Ccpl` × 10^(GM/20), and the margin at the budget is 20 log(`Ccpl_crit` / 0.1 fF). At 0.1 fF |T| stays
below 1 everywhere, so there is no phase margin to quote. The gain margin is the margin.

**Kick cross-check** ([sim/chain/kick_edge.py](../sim/chain/kick_edge.py)). This is `stability.sh`'s kick, with the
edge found by bisection to 3 %. The first pass disagreed by 1–3 % in one direction, and the cause was the kick
criterion, not the loop break. `stability.sh` calls a case "OSC" when the output is still ≥ 1 mV peak-to-peak (p-p)
at 250–300 ns. Just inside the edge, the ring-down is that slow. At ss 10 °C:

- 0.4625 fF is still at millivolts at 300 ns but has decayed by 600 ns, for both a 1 µA and a 1 pA kick.
- 0.468 fF decays and 0.476 fF grows (a 1 pA kick grows ×42), against an AC edge of 0.472 fF.

`kick_edge.py` therefore calls "OSC" only for an output that is not decaying: 250–300 ns p-p ≥ 0.97 × the
150–200 ns p-p, and ≥ 1 mV. `stability.sh`'s published edges are 1–3 % pessimistic, which is harmless.

**K-factor** ([sim/chain/kfactor.py](../sim/chain/kfactor.py)). This treats the chain as a differential two-port.
Two AC runs inject a differential test current at port 1 and then at port 2 (the other port open), which gives the
differential Z parameters. Rollett's K = (2 Re z11 Re z22 − Re z12 z21) / |z12 z21| doesn't depend on the immittance
or reference impedance. |Δ| and Edwards' μ come from S at 100 Ω differential. Port 2 is `out_p` − `out_n`, including
the 50 fF loads. Port 1 is either the board side of the pad models (the pad / ESD / mux model inside the two-port) or
the chip pins (pad models removed). The bench uses the 2 nH supply and the real decap, with no `Ccpl`.

### Results

<<A>>

- The **AC edge and the kick edge agree everywhere**, to within 1.5 %. On the extracted chain the kick was run on a
  grid at 0.9 / 0.97 / 1.03 / 1.1 × the AC edge and then bisected; each run there takes about 5 min.
- Where the loop has its 0° crossing: on the schematic, 620–630 MHz (coupling to `pad_p`) and 730–760 MHz (to
  `o1p`) at full gain, and 720–920 MHz at low gain. **On the extracted chain it is 466–473 MHz and 527–543 MHz**, in
  the band. The extraction adds C, which slows each stage and moves the 0° crossing down. With that phase change,
  the extracted chain tolerates more coupling than the schematic: ss 10 °C full gain 0.586 vs 0.474 fF to `pad_p`.
- **`o1p` is the worse landing point** (by 1–4 dB). It has one stage less of attenuation from the input network
  and a phase that crosses 0° at a higher frequency, where the chain's gain is still high.
- **The strap is worth 7.4–11.5 dB of margin** (extracted ss 10 °C: 15.3 → 24.3 dB to `pad_p`, 14.1 → 22.5 dB to
  `o1p`; tt: 19.3 → 28.9 dB to `pad_p`). That is 0.84–0.95 dB of margin per dB of gain it removes.
- **K-factor:** K is far above 1 at every corner and strap state. Its minimum on the extracted chain is 10.5 (ports
  at the pins) at 752 MHz, the supply resonance (2 + 2 nH with the 10.6 pF decap). |Δ| ≤ 0.973 and μ ≥ 1.025, which
  is reached at the low end, where the input is nearly lossless. |S12| ≤ −113 dB extracted (−124 dB schematic). The
  chain is unconditionally stable for any passive source and load.

<<K>>

## (B) RC loads

### Method

[sim/chain/rcload.py](../sim/chain/rcload.py). Each stage's load R runs from VDD (VDPWR) to an output net. "Cl across
the load R" is therefore a capacitor from VDPWR to `o<k>p` and to `o<k>n` (`out_p` / `out_n` for stage 6), added in
the testbench, so `lna_chain` is untouched. Cl = 1 / (2π R f_pole), with R = 1 kΩ for stage 1 and 4 kΩ for stages
2–6. That is the pole R and Cl alone would set. Each node already has a pole of its own from the next stage's input
C, at 1.5–1.8 GHz for stages 2–6, so the real loss is larger than this pole alone suggests. One deck per variant
gives the gain, every stage's gain, NF at 448 MHz (noise analysis, NF = onoise² / (|G|² · 4kT · 73 Ω), as in
`analyse.py`), and the AC loop gain to `pad_p` and to `o1p`. Kick edges were rerun on the variants that meet the
gain-loss limit.

### Today's roll-off (schematic)

<<B1>>

Stage 1 is a low-pass from about 220 MHz up, with its upper edge at 2.9–3.3 GHz. Stages 2–6 are band-passes (the
capacitive degeneration gives the high-pass), peaking at 410–500 MHz with upper edges at 1.5–1.8 GHz. The whole chain
is 20 dB down at 1.34–1.40 GHz and 40 dB down at 2.4–2.6 GHz. The margins are set at 620–740 MHz (schematic) and
470–540 MHz (extracted), well below those edges. **The chain's phase, not its gain roll-off, sets the oscillation
frequency.**

### The sweep (schematic, full gain)

<<B2>>

"Ccpl_crit ×" is the tolerable coupling relative to no Cl. The kick confirms the AC numbers for the passing variants:

| Variant | tt pad_p / o1p, kick (fF) | ss 10 °C pad_p / o1p, kick (fF) | AC, ss 10 °C pad_p (fF) |
|---|---|---|---|
| none | 0.781–0.797 / 0.562–0.578 | 0.472–0.481 / 0.350–0.359 | 0.474 |
| stage 1, 1.5 GHz | 0.825–0.838 / 0.606–0.613 | 0.506–0.513 / 0.391–0.394 | 0.507 |
| stage 1, 2.0 GHz | 0.813–0.819 / 0.594–0.600 | 0.494–0.500 / 0.381–0.384 | 0.496 |
| last two, 5 GHz (fails by 0.1 dB) | 0.838–0.850 / 0.613–0.619 | 0.513–0.519 / 0.391–0.394 | 0.513 |

<<BPEX>>

**What it buys.** Across the whole sweep, every dB of in-band gain lost at 448 MHz buys 1.0–1.3 dB of margin for
coupling to `pad_p` (up to 1.8 dB for `o1p` with the smallest Cl, where both numbers are tiny). For example, all six
stages at 2 GHz lose 3.9 dB at 448 MHz and gain ×1.64 (4.3 dB). Removing gain flat does nearly as well: the strap
buys 0.84–0.95 dB per dB. The reason is that the loop's 0° crossing is only 1.1–1.7× above
the band, closer still on the extracted chain, and a first-order pole can't separate two frequencies that close. Only
stage 1 alone (a 1 kΩ node, the lowest gain behind it) stays inside the limits up to a 1.5 GHz pole, and it buys
×1.07–1.09. NF at 448 MHz moves by ≤ 0.08 dB for the passing variants: Cl on stages 4–6 doesn't move it at all, and
Cl on stage 1 adds 0.05–0.07 dB.

**Area.** Stage 1 at 1.5 GHz needs 106 fF per side, about 53 µm² of MIM each at 2 fF/µm² (about 7.3 µm square),
106 µm² in all. `amp_dp` is 36.4 × 20.7 µm (754 µm²) and has no MIM today. The two caps would fit over it on met3 /
met4 only if its upper routing leaves room; otherwise they go beside it, which the U layout doesn't have spare. Cl on
the last two stages at 5 GHz is 8 fF per side (4 µm²) and fits anywhere. Neither is worth doing for ×1.07–1.09.

## (C) Bond-wire and package coupling

### Package data

The Tiny Tapeout documentation doesn't publish bond-wire lengths or package parasitics at the time of writing:

- [tinytapeout.com/specs/analog](https://tinytapeout.com/specs/analog/) (read 2026-11-13) gives the analog path limits
  only: "Resistance: < 500 ohm", "Capacitance: < 5 pf", "Max current: 4 mA" (sky130A), and that "A draw of around
  20mA from the power supply will result in a 0.1V drop through the PDN".
- The package type for the ttsky25 chips isn't stated on the TT pages read (analog, pinouts, gpio, pcb-etr, the
  ttsky25a chip page; the ttsky25a datasheet PDF wasn't checked). The only QFN64 pin map found is the older "SKY130
  Open Frame chips" table in
  [tt-multiplexer docs/INFO.md](https://github.com/TinyTapeout/tt-multiplexer/blob/main/docs/INFO.md). There, analog[0]
  is QFN pin 41, between vdda1 (VAPWR, pin 40) and analog[1] (pin 42). That pinout isn't confirmed for ttsky25, and
  the chain's supply is VDPWR, not VAPWR.

So, as the handoff says: **assumed**, about 1 nH/mm, 2 and 5 nH wires (the supply L already used, and the same for
the input wires), k swept up to 0.3 (typical for neighbouring bond wires: 0.1–0.4) and on to 1. The pad model keeps
its own 1 nH; the input bond wire is added in series on the board side of it.

### Method

[sim/chain/stability_bond.py](../sim/chain/stability_bond.py). The model:

- an input bond wire Lb in series with each input (`Rant` → Lb → pad model);
- `Lsup` and `Lgnd` as the supply bond wires;
- K elements from the aggressor (the VDPWR wire, the VGND wire, or both) to `pad_p`'s wire (k) and to `pad_n`'s
  (r·k, with r = 0, 0.5, or 1 for symmetric). All wires are taken to run package → die. The sign of k (the dot
  orientation) isn't known, so both signs are run.

**The loop break needs care here.** The mutual inductance couples both ways, and the input wire is not a
high-impedance node: the pad model's 2 + 3 pF carries real RF current, which induces a voltage back in the supply
wire. My first one-way break (a test voltage in the input wire, measuring the supply-wire current) ignored that. It
predicted closed-loop / open-loop = 1.13 where the simulation with a real K = 0.9 gave 3.9. The method used instead:

1. Series test sources in the four wires (pad_p, pad_n, VDPWR, VGND) give their 4 × 4 short-circuit admittance
   matrix Y(f), from four AC runs.
2. The K elements add series voltages e = jωkM₁i, where M₁ is the unit-k coupling pattern.
3. So a pole sits on the jω axis where det(I − k·jωY·M₁) = 0, i.e. at k = 1/λ for a real eigenvalue λ of jωY·M₁.

`stability_bond.py check` shows that the Y model reproduces the closed loop with real K = ±0.9 elements to 1e-8
(4e-7 for "both, symmetric"). The kick with real K elements (`stability_bond.py kick`) is the independent check.

### Results

- **No k gives a pole on the jω axis**, at any corner, strap state, L = Lb = 2 or 5 nH, or coupling pattern, from
  10 MHz to 5 GHz (180 cases). The eigenvalues come in near-± pairs and never become real. A brute-force check without
  eigenvalue tracking agrees: |det(I − k·jωY·M₁)| ≥ 0.42 for every k in [−1, 1]. Its minimum is at k = +1, 3.2 GHz,
  symmetric coupling, and it is identical for both strap states. That makes it a passive resonance of the wires
  (Lb, Lsup, Lgnd with the pad and decap C), not a loop through the chain's gain.
- The reason: the coupling between two passive, lossy loops (the input wire with the pad C, and the supply loop with
  the decap) dominates the loop gain. That can only reach the jω axis if both loops are lossless. The chain's active
  contribution (input voltage → supply current) is small because the chain is differential and its tails are current
  sources. Taken alone (the
  one-way break), it would need k ≥ 5.8.
- **The kick agrees:** with real K elements, the chain decays for every k up to 0.99 (ss 10 °C with Lsup or Lgnd as
  the aggressor at 2 nH, ss 10 °C Lsup at 5 nH, and tt Lsup at 2 nH; both signs).
- **Symmetric coupling (common mode)** gives the deepest dip, not the shallowest: min |det| is 0.65 with only
  `pad_p`'s wire coupled, 0.58 with k/2 on `pad_n`, and 0.42 symmetric. The dip is the passive resonance, which the
  chain's common-mode rejection doesn't act on. None of them is near 0 (oscillation).

**Combined with on-chip coupling** (`stability_bond.py combined`): `Ccpl_crit` with the bond coupling present, k
= ±0.1 and ±0.3 on `pad_p`'s wire, supply or ground as the aggressor:

<<C2>>

Adding the input bond wire itself changes the tolerable coupling a little (k = 0 here vs (A): ss 10 °C `pad_p` 0.474
→ 0.457 fF at 2 nH, 0.433 fF at 5 nH). The mutual coupling then takes off at most another 8.6 %. **The 0.1 fF budget
keeps ≥ 10.6 dB of margin with both paths together** (schematic, the worse bench).

**The aggressor's size** (`stability_bond.py current`): the RF current in the supply wires with a CW input at
−90 and −60 dBm (from 73 Ω), measured over the last 200 ns of 400 ns:

<<C3>>

The fundamental at 434 MHz is about 0.2 µA at −90 dBm, and that figure barely depends on the gain or the strap state:
it is the input signal's own current returning through the chip, not the chain's output. At −60 dBm, with the chain
limiting, it rises to 0.3–1.9 µA. **The real aggressor is the second harmonic:** 15–132 µA at 868 MHz at −60 dBm
(largest with 2 nH at ss 10 °C), against < 1 µA at −90 dBm. The limiting differential pairs' tail nodes swing at 2f.
It is out of band, and the loop at 868 MHz is far below 1.

## Recommendation for Matt

What this says about each option, in the order I'd do them if any:

1. **Action 10, a lower-gain option: the only one that buys margin against unknown paths.** Margin follows gain at
   0.84–0.95 dB per dB for every path simulated here (`Ccpl` to the pad or to stage 2, at every corner). The strap
   already gives 7.4–11.5 dB (extracted ss 10 °C, worst landing point `o1p`: 14.1 → 22.5 dB). A 60 dB setting, about
   10 dB below the strap, would add roughly another 9 dB. It is the cheapest insurance against what isn't modelled: the board, the antenna and its cable,
   and the real package. It also works after tape-out, which a layout change doesn't.
2. **RC loads (action 5): don't.** They cost in-band gain at the same rate as simply lowering the gain, add MIM area,
   and on the extracted chain the loop's 0° crossing is in the band. Within the 0.5 / 1 dB limit the best (Cl on stage
   1, 1.5 GHz) buys ×1.07.
3. **Action 9, local decap: no stability case from these sims.** The bond-wire / supply path is passive-dominated and
   never reaches the jω axis. The chain's two-port K minimum sits at the 752 MHz supply resonance but is ≥ 10 there.
   It may still be worth doing for the supply-noise reasons in [power.md](power.md), but not for oscillation.
4. **Action 8, a straight chain: not needed for stability.** The U fold's extracted coupling (1.44e-4 fF every link,
   1.2e-5 – 2.8e-5 fF from the late stages) is about 3400× (70 dB) below the worst edge (0.485 fF extracted). The substrate
   coupling is also far below the budget ([substrate_2026-10-29.md](substrate_2026-10-29.md)). A straight layout
   would reduce a number that is already negligible. It is only worth doing if we stop trusting the extraction's
   coverage, and a lower-gain option covers that case better.

Margin today, for the record: worst schematic case 10.7 dB at 0.1 fF, worst extracted 13.7 dB, and about 70 dB to the
layout's own extracted coupling.

## Rerun

From the repo root, in the image, after netlisting `tb_chain` into `build/real` and making `build/pexsim` (see the
handoff), and running `stability.sh` once in `build/real` (it netlists `decap_vdpwr`; copy it to `build/pexsim`):

```
python3 sim/chain/stability_ac.py --chain sch            # (A) loop gain, ~10 s
python3 sim/chain/kick_edge.py --chain sch               # (A) kick edges, ~5 min
python3 sim/chain/kfactor.py --chain sch                 # (A) K-factor, seconds
python3 sim/chain/stability_ac.py --chain pex            # extracted: ~10 min
python3 sim/chain/kfactor.py --chain pex
python3 sim/chain/kick_edge.py --chain pex --around build/stab_ac/ac_pex.json   # ~1.5 h on 24 CPUs
python3 sim/chain/rcload.py rolloff; python3 sim/chain/rcload.py sweep           # (B)
python3 sim/chain/stability_bond.py ac|check|kick|combined|current               # (C)
python3 sim/chain/stab_tables.py a b c                   # the tables in this doc, from build/stab_ac/*.json
```

Results land in `build/stab_ac/` (not in git).
