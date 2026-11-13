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

| Corner | Strap | Node | Gain at 434 MHz, sch / pex (dB) | Ccpl_crit AC, sch (fF) | Kick edge, sch (fF) | Margin at 0.1 fF, sch (dB) | f, sch (MHz) | Ccpl_crit AC, pex (fF) | Kick edge, pex (fF) | Margin at 0.1 fF, pex (dB) | f, pex (MHz) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| tt 27 °C | full | pad_p | 76.4 / 75.5 | 0.780 | 0.781–0.797 | 17.8 | 623 | 0.925 | 0.925–0.953 | 19.3 | 466 |
| tt 27 °C | full | o1p | 76.4 / 75.5 | 0.563 | 0.562–0.578 | 14.9 | 739 | 0.782 | 0.782–0.806 | 17.8 | 529 |
| tt 27 °C | low | pad_p | 64.4 / 65.3 | 2.728 | 2.75–2.81 | 28.7 | 731 | 2.805 | 2.81–2.89 | 28.9 | 548 |
| tt 27 °C | low | o1p | 64.4 / 65.3 | 1.825 | 1.81–1.84 | 25.2 | 888 | 2.212 | 2.21–2.28 | 26.8 | 632 |
| ss 10 °C | full | pad_p | 80.9 / 79.5 | 0.474 | 0.472–0.481 | 13.5 | 619 | 0.586 | 0.586–0.604 | 15.3 | 468 |
| ss 10 °C | full | o1p | 80.9 / 79.5 | 0.358 | 0.35–0.359 | 11.0 | 727 | 0.512 | 0.512–0.527 | 14.1 | 527 |
| ss 10 °C | low | pad_p | 69.4 / 70.1 | 1.562 | 1.56–1.59 | 23.8 | 721 | 1.641 | 1.64–1.69 | 24.3 | 543 |
| ss 10 °C | low | o1p | 69.4 / 70.1 | 1.098 | 1.09–1.12 | 20.7 | 866 | 1.341 | 1.34–1.38 | 22.5 | 621 |
| sf 27 °C | full | pad_p | 76.4 / 75.5 | 0.785 | 0.781–0.797 | 17.8 | 633 | 0.935 | 0.935–0.963 | 19.4 | 472 |
| sf 27 °C | full | o1p | 76.4 / 75.5 | 0.556 | 0.547–0.562 | 14.8 | 756 | 0.780 | 0.78–0.804 | 17.8 | 537 |
| sf 27 °C | low | pad_p | 65.9 / 67.0 | 2.317 | 2.31–2.38 | 27.2 | 736 | 2.332 | 2.33–2.4 | 27.3 | 546 |
| sf 27 °C | low | o1p | 65.9 / 67.0 | 1.527 | 1.53–1.56 | 23.6 | 897 | 1.822 | 1.82–1.88 | 25.2 | 631 |
| ff 50 °C | full | pad_p | 73.1 / 70.1 | 1.125 | 1.12–1.16 | 21.0 | 629 | 1.681 | 1.68–1.73 | 24.5 | 473 |
| ff 50 °C | full | o1p | 73.1 / 70.1 | 0.798 | 0.797–0.812 | 18.0 | 756 | 1.386 | 1.39–1.43 | 22.8 | 543 |
| ff 50 °C | low | pad_p | 60.8 / 59.7 | 4.033 | > 4 | 32.1 | 744 | 5.191 | 5.19–5.35 | 34.3 | 561 |
| ff 50 °C | low | o1p | 60.8 / 59.7 | 2.649 | 2.69–2.75 | 28.4 | 915 | 3.975 | 3.97–4.09 | 31.9 | 655 |
| ss 10 °C 1.89 V | full | pad_p | 81.2 / 80.0 | 0.458 | 0.453–0.463 | 13.2 | 623 | 0.556 | 0.556–0.573 | 14.9 | 470 |
| ss 10 °C 1.89 V | full | o1p | 81.2 / 80.0 | 0.346 | 0.341–0.35 | 10.7 | 732 | 0.485 | 0.485–0.5 | 13.7 | 530 |
| ss 10 °C 1.89 V | low | pad_p | 68.5 / 69.3 | 1.724 | 1.72–1.75 | 24.7 | 732 | 1.795 | 1.8–1.85 | 25.0 | 552 |
| ss 10 °C 1.89 V | low | o1p | 68.5 / 69.2 | 1.206 | 1.19–1.22 | 21.6 | 881 | 1.460 | 1.46–1.5 | 23.2 | 633 |

Ccpl_crit from the 0.1 fF and 1 fF runs differ by at most 0.8 %.

- The **AC edge and the kick edge agree everywhere**: to within 1.5 % on the schematic, and on the extracted chain
  the kick edge lies between 1.00 and 1.03 × the AC edge in all 20 cases (the kick grid there was 0.9 / 0.97 / 1.03 /
  1.1 × the AC edge, then bisected once, so 3 % is its resolution). An extracted kick run takes 5–50 min, longest near the edge,
  where the ring-down is slow; the 20 cases took 2 h 24 min on 24 CPUs.
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

| Chain | Corner | Strap | K min (port 1 at the board side) | K min (port 1 at the pins) | f of K min (MHz) | \|Δ\| max | μ min | \|S12\| max (dB) |
|---|---|---|---|---|---|---|---|---|
| sch | tt 27 °C | full | 5.67e+04 | 1.89e+03 | 752 / 1728 | 0.972 | 1.026 | -126 |
| sch | tt 27 °C | low | 1.89e+05 | 7.39e+03 | 752 / 770 | 0.972 | 1.026 | -129 |
| sch | ss 10 °C | full | 3.16e+04 | 1.21e+03 | 752 / 770 | 0.971 | 1.026 | -128 |
| sch | ss 10 °C | low | 9.74e+04 | 4.2e+03 | 752 / 770 | 0.971 | 1.026 | -131 |
| sch | sf 27 °C | full | 7.06e+04 | 1.69e+03 | 752 / 1852 | 0.972 | 1.026 | -125 |
| sch | sf 27 °C | low | 1.96e+05 | 5.92e+03 | 735 / 2559 | 0.972 | 1.026 | -128 |
| sch | ff 50 °C | full | 9.41e+04 | 2.03e+03 | 752 / 1939 | 0.972 | 1.025 | -124 |
| sch | ff 50 °C | low | 3.23e+05 | 9.65e+03 | 752 / 2872 | 0.972 | 1.025 | -128 |
| sch | ss 10 °C 1.89 V | full | 3.14e+04 | 1.2e+03 | 752 / 770 | 0.971 | 1.026 | -128 |
| sch | ss 10 °C 1.89 V | low | 1.12e+05 | 4.86e+03 | 752 / 752 | 0.971 | 1.026 | -131 |
| pex | tt 27 °C | full | 209 | 15.1 | 752 / 752 | 0.972 | 1.025 | -113 |
| pex | tt 27 °C | low | 494 | 36.3 | 752 / 752 | 0.972 | 1.025 | -113 |
| pex | ss 10 °C | full | 133 | 10.8 | 752 / 752 | 0.971 | 1.026 | -113 |
| pex | ss 10 °C | low | 286 | 23.5 | 752 / 752 | 0.971 | 1.026 | -113 |
| pex | sf 27 °C | full | 209 | 14.2 | 752 / 752 | 0.972 | 1.025 | -113 |
| pex | sf 27 °C | low | 417 | 28.8 | 752 / 752 | 0.972 | 1.025 | -113 |
| pex | ff 50 °C | full | 382 | 23.3 | 752 / 752 | 0.973 | 1.025 | -113 |
| pex | ff 50 °C | low | 957 | 59.3 | 752 / 752 | 0.973 | 1.025 | -113 |
| pex | ss 10 °C 1.89 V | full | 127 | 10.5 | 752 / 752 | 0.971 | 1.026 | -113 |
| pex | ss 10 °C 1.89 V | low | 312 | 26 | 752 / 752 | 0.971 | 1.026 | -113 |

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

| Corner | Strap | Gain at 434 MHz (dB) | −20 dB at (MHz) | −40 dB at (MHz) | Stage upper −3 dB edges, 1–6 (MHz) | Stage gain peaks, 1–6 (MHz) | NF at 448 MHz (dB) |
|---|---|---|---|---|---|---|---|
| tt 27 °C | full | 76.42 | 1403 | 2559 | 3299, 1575, 1688, 1688, 1809, 1575 | 221, 412, 432, 432, 432, 485 | 11.08 |
| tt 27 °C | low | 64.39 | 1650 | 3150 | 3618, –, 1688, 1688, 1809, 1575 | 376, 1114, 432, 432, 432, 485 | 11.91 |
| ss 10 °C | full | 80.89 | 1340 | 2443 | 2939, 1470, 1612, 1575, 1728, 1504 | 231, 412, 432, 432, 432, 496 | 10.57 |
| ss 10 °C | low | 69.39 | 1575 | 2939 | 3224, –, 1612, 1575, 1728, 1504 | 376, 1063, 432, 432, 432, 496 | 11.14 |

Stage 1 is a low-pass from about 220 MHz up, with its upper edge at 2.9–3.3 GHz. Stages 2–6 are band-passes (the
capacitive degeneration gives the high-pass), peaking at 410–500 MHz with upper edges at 1.5–1.8 GHz. The whole chain
is 20 dB down at 1.34–1.40 GHz and 40 dB down at 2.4–2.6 GHz. The margins are set at 620–740 MHz (schematic) and
470–540 MHz (extracted), well below those edges. **The chain's phase, not its gain roll-off, sets the oscillation
frequency.**

### The sweep (schematic, full gain)

| Variant | Pole (GHz) | Cl per side, stage 1 / 2–6 (fF) | tt: ΔG 448 / 560 (dB) | ss 10 °C: ΔG 448 / 560 (dB) | ΔNF 448 (dB) | Ccpl_crit ×, tt pad_p / o1p | Ccpl_crit ×, ss 10 °C pad_p / o1p | Meets 0.5 / 1 dB |
|---|---|---|---|---|---|---|---|---|
| all | 0.6 | 265 / 66 | -13.19 / -15.35 | -14.11 / -16.38 | +0.32 | 4.64 / 5.30 | 5.06 / 5.72 | no |
| all | 0.8 | 199 / 50 | -9.90 / -11.54 | -10.61 / -12.34 | +0.20 | 3.26 / 3.64 | 3.48 / 3.85 | no |
| all | 1.0 | 159 / 40 | -7.91 / -9.23 | -8.49 / -9.89 | +0.14 | 2.61 / 2.87 | 2.76 / 3.01 | no |
| all | 1.5 | 106 / 27 | -5.25 / -6.13 | -5.65 / -6.59 | +0.08 | 1.92 / 2.06 | 1.99 / 2.12 | no |
| all | 2.0 | 80 / 20 | -3.93 / -4.59 | -4.23 / -4.94 | +0.05 | 1.64 / 1.73 | 1.68 / 1.77 | no |
| all | 3.0 | 53 / 13 | -2.61 / -3.05 | -2.82 / -3.29 | +0.03 | 1.39 / 1.45 | 1.42 / 1.47 | no |
| all | 5.0 | 32 / 8 | -1.56 / -1.83 | -1.69 / -1.97 | +0.02 | 1.22 / 1.25 | 1.24 / 1.26 | no |
| last3 | 0.6 | – / 66 | -7.09 / -8.03 | -7.51 / -8.48 | -0.00 | 2.38 / 2.57 | 2.48 / 2.65 | no |
| last3 | 0.8 | – / 50 | -5.38 / -6.11 | -5.71 / -6.46 | -0.00 | 1.95 / 2.07 | 2.01 / 2.12 | no |
| last3 | 1.0 | – / 40 | -4.33 / -4.92 | -4.60 / -5.22 | -0.00 | 1.72 / 1.81 | 1.76 / 1.84 | no |
| last3 | 1.5 | – / 27 | -2.91 / -3.31 | -3.10 / -3.52 | -0.00 | 1.44 / 1.50 | 1.47 / 1.52 | no |
| last3 | 2.0 | – / 20 | -2.19 / -2.50 | -2.33 / -2.66 | -0.00 | 1.32 / 1.36 | 1.34 / 1.37 | no |
| last3 | 3.0 | – / 13 | -1.46 / -1.67 | -1.56 / -1.78 | -0.00 | 1.21 / 1.23 | 1.22 / 1.24 | no |
| last3 | 5.0 | – / 8 | -0.88 / -1.01 | -0.94 / -1.07 | -0.00 | 1.12 / 1.13 | 1.13 / 1.14 | no |
| last2 | 0.6 | – / 66 | -4.72 / -5.35 | -4.99 / -5.64 | -0.00 | 1.80 / 1.90 | 1.85 / 1.94 | no |
| last2 | 0.8 | – / 50 | -3.57 / -4.07 | -3.79 / -4.30 | -0.00 | 1.57 / 1.64 | 1.60 / 1.66 | no |
| last2 | 1.0 | – / 40 | -2.87 / -3.28 | -3.05 / -3.47 | -0.00 | 1.44 / 1.49 | 1.46 / 1.51 | no |
| last2 | 1.5 | – / 27 | -1.93 / -2.21 | -2.05 / -2.34 | -0.00 | 1.28 / 1.31 | 1.29 / 1.32 | no |
| last2 | 2.0 | – / 20 | -1.45 / -1.66 | -1.54 / -1.77 | -0.00 | 1.20 / 1.23 | 1.21 / 1.24 | no |
| last2 | 3.0 | – / 13 | -0.97 / -1.11 | -1.03 / -1.18 | -0.00 | 1.13 / 1.15 | 1.14 / 1.15 | no |
| last2 | 5.0 | – / 8 | -0.58 / -0.67 | -0.62 / -0.71 | -0.00 | 1.08 / 1.09 | 1.08 / 1.09 | no |
| s1 | 0.6 | 265 / – | -1.35 / -1.90 | -1.54 / -2.14 | +0.28 | 1.22 / 1.28 | 1.24 / 1.30 | no |
| s1 | 0.8 | 199 / – | -0.91 / -1.31 | -1.05 / -1.49 | +0.18 | 1.15 / 1.19 | 1.16 / 1.21 | no |
| s1 | 1.0 | 159 / – | -0.68 / -0.98 | -0.78 / -1.12 | +0.13 | 1.11 / 1.14 | 1.12 / 1.15 | no |
| s1 | 1.5 | 106 / – | -0.39 / -0.58 | -0.46 / -0.67 | +0.07 | 1.06 / 1.08 | 1.07 / 1.09 | yes |
| s1 | 2.0 | 80 / – | -0.27 / -0.40 | -0.32 / -0.47 | +0.05 | 1.04 / 1.06 | 1.05 / 1.06 | yes |
| s1 | 3.0 | 53 / – | -0.17 / -0.25 | -0.19 / -0.29 | +0.03 | 1.02 / 1.04 | 1.03 / 1.04 | yes |
| s1 | 5.0 | 32 / – | -0.09 / -0.14 | -0.11 / -0.16 | +0.02 | 1.01 / 1.02 | 1.01 / 1.02 | yes |

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

| Corner | L = Lb | Node | Ccpl_crit, k = 0 (fF) | Worst with \|k\| ≤ 0.3 (fF) | Change | Worst case | Margin at 0.1 fF (dB) |
|---|---|---|---|---|---|---|---|
| ss 10 °C | 2n | pad_p | 0.457 | 0.433 | -5.2 % | sup, k -0.3 | 12.7 |
| ss 10 °C | 2n | o1p | 0.359 | 0.340 | -5.3 % | gnd, k -0.3 | 10.6 |
| ss 10 °C | 5n | pad_p | 0.433 | 0.396 | -8.6 % | gnd, k -0.3 | 11.9 |
| ss 10 °C | 5n | o1p | 0.360 | 0.354 | -1.7 % | gnd, k -0.3 | 11.0 |
| tt 27 °C | 2n | pad_p | 0.753 | 0.728 | -3.3 % | sup, k -0.3 | 17.2 |
| tt 27 °C | 2n | o1p | 0.563 | 0.542 | -3.9 % | gnd, k -0.3 | 14.7 |
| tt 27 °C | 5n | pad_p | 0.713 | 0.679 | -4.7 % | gnd, k -0.3 | 16.6 |
| tt 27 °C | 5n | o1p | 0.565 | 0.563 | -0.3 % | gnd, k +0.3 | 15.0 |

Adding the input bond wire itself changes the tolerable coupling a little (k = 0 here vs (A): ss 10 °C `pad_p` 0.474
→ 0.457 fF at 2 nH, 0.433 fF at 5 nH). The mutual coupling then takes off at most another 8.6 %. **The 0.1 fF budget
keeps ≥ 10.6 dB of margin with both paths together** (schematic, the worse bench).

**The aggressor's size** (`stability_bond.py current`): the RF current in the supply wires with a CW input at
−90 and −60 dBm (from 73 Ω), measured over the last 200 ns of 400 ns:

| Corner | Strap | L | Input (dBm) | Out diff at 434 MHz (mV amplitude) | I(Lsup) 434 / 868 MHz (µA) | I(Lgnd) 434 / 868 MHz (µA) |
|---|---|---|---|---|---|---|
| tt 27 °C | full | 2n | -90 | 171 | 0.21 / 0.3 | 0.22 / 0.3 |
| tt 27 °C | full | 2n | -60 | 1405 | 0.43 / 96.9 | 0.60 / 100.2 |
| tt 27 °C | full | 5n | -90 | 188 | 0.23 / 0.2 | 0.24 / 0.3 |
| tt 27 °C | full | 5n | -60 | 1405 | 1.36 / 15.0 | 1.52 / 21.6 |
| tt 27 °C | low | 2n | -90 | 43 | 0.20 / 0.2 | 0.20 / 0.2 |
| tt 27 °C | low | 2n | -60 | 1136 | 0.28 / 17.6 | 0.31 / 17.1 |
| tt 27 °C | low | 5n | -90 | 47 | 0.21 / 0.2 | 0.21 / 0.2 |
| tt 27 °C | low | 5n | -60 | 1196 | 0.52 / 3.8 | 0.55 / 4.4 |
| ss 10 °C | full | 2n | -90 | 284 | 0.21 / 0.6 | 0.23 / 0.7 |
| ss 10 °C | full | 2n | -60 | 1385 | 0.52 / 128.1 | 0.70 / 132.0 |
| ss 10 °C | full | 5n | -90 | 313 | 0.27 / 0.2 | 0.29 / 0.4 |
| ss 10 °C | full | 5n | -60 | 1384 | 1.67 / 18.9 | 1.85 / 26.7 |
| ss 10 °C | low | 2n | -90 | 76 | 0.20 / 0.2 | 0.20 / 0.2 |
| ss 10 °C | low | 2n | -60 | 1336 | 0.33 / 54.4 | 0.38 / 52.0 |
| ss 10 °C | low | 5n | -90 | 84 | 0.22 / 0.2 | 0.22 / 0.2 |
| ss 10 °C | low | 5n | -60 | 1352 | 0.90 / 10.8 | 0.96 / 11.3 |

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
