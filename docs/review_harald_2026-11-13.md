# Design review with Harald Pretl (2026-11-13)

A one-hour video review with Harald Pretl (JKU / IIC-OSIC), from the transcript. This doc has a summary, his points
checked against the repo, the actions that follow, and what Matt decided to do with them.

## Summary

Harald thinks the design is sound. In his words, functionality "seems like you have assured properly", and he
praised the explainer page, the floorplan tool and how compact and filled the layouts are ("this could be a manual
layout").

His main message: **the most likely way this chip fails is the 80 dB chain oscillating.** Folding the chain into a U
puts its output back near its input, which is "the worst thing you can do". Too much noise only costs range;
oscillation is a functional failure, because it overloads the receiver. His isolation rule of thumb on a chip:
60 dB is easy, 80 dB needs proper engineering, 100 dB is tough, 120 dB is "hand waving and black magic". Two things
help us: only the input goes off chip (no bond-wire loop from output to input), and the chain is fully
differential.

His second theme was simulation discipline:
- transient and PEX sims have no device noise;
- a small-signal (AC) stability analysis would complement the kick test;
- formal equivalence checking would complement gate-level sims;
- long simulations should run in the background, before tape-out and while the silicon is in fab.

On regulations: transmitting without certification isn't legal, not even experimentally, and an output filter doesn't
change that. Demos should be cabled with attenuators, or done in a shielded room or the university EM chamber.

## Points and where we stand

| # | Point | Status in the repo |
|---|---|---|
| 1 | **No input band-pass.** A wideband input detects everything in the air (FM, TV); our own TX is probably the strongest signal, but nothing guarantees it | Known and deliberate: no SAW and no match ([PLAN.md](../PLAN.md) "Open questions and risks", [how_it_works.md](how_it_works.md)). The pad model is rough, so out-of-band rejection is an estimate. |
| 2 | **No impedance match.** The input sees the 2 pF input capacitors and 20 kΩ bias resistors, so it's high-impedance, not ~100 Ω differential. He suggested resistive feedback on stage 1 to set a real input resistance | Not addressed. In the review Matt said the input was matched to TT's impedance; it isn't. The ~11 dB NF already includes the mismatch. Corrected in [how_it_works.md](how_it_works.md). "Wire-as-matching antenna" is parked (STATUS). |
| 3 | The capacitively degenerated diff pair (stages 2–6) is "a really nice structure": no DC path, a built-in high-pass, offsets don't build up | No action. |
| 4 | **RC loads, not R.** Today the roll-off above the band comes from the next stage's input C, which isn't controlled. A defined low-pass in each load kills the gain before the frequency where it could oscillate | Not done. → action 5. |
| 5 | **The U-fold is the worst case.** Lay the chain out straight, even if the block becomes long: flip it, run it along the left edge, make each stage tall and thin (the input caps are easy to squash) | Not done. The chain is the U (145.4 × 70.5 µm) with a 14 µm guard-ring moat. → action 8. |
| 6 | **Decoupling is too far from the RF blocks.** Fill the empty space inside each high-frequency block with local decap | Open: [power.md](power.md) proposal 5, "decap at the load"; \|Z\| at the blocks is flat ≈ R to 500 MHz. → action 9. |
| 7 | Coupling sims only include what you put in them: bond wires, package and board aren't in a block extraction | Known. The stability bench has 2–5 nH supply / ground L and the real decap, but no bond-wire mutual coupling. → action 6. Also corrected from the review: the out → in coupling budget is **0.1 fF**, not 1 fF. At ss 10 °C 0.5 fF oscillates, at tt 1 fF rings. The extracted chain has 0 aF (wires) and far below 0.1 fF through the substrate ([substrate_2026-10-29.md](substrate_2026-10-29.md)). |
| 8 | **Add a small-signal stability analysis** (a K-factor or loop-gain method). It's quantitative and wideband; the kick covers the large-signal side. People do both | Not done. `sim/chain/stability.sh` is a kick plus AC gain / peaking. → action 4. |
| 9 | The stability results he saw predate the low-gain strap | Already in [verification.md](verification.md) (strap on: stable up to 1 fF at every corner; [verify_lna_lo.md](verify_lna_lo.md) item 3), but at the end of a long table cell. The row now leads with the current result. |
| 10 | Comparator: a more differential version is possible (two mirror loads, the second mirrored to the output, push-pull). Not critical: the envelope is slow | No action. His sketch wasn't captured. |
| 11 | Layout: share drain / source between devices in a row (more compact); use **multiple vias** wherever they fit | Known weakness (the agent tends to place single vias). Not fixed in the block layouts. Pick up with action 8. |
| 12 | **Equivalence checking (LEC, e.g. eqy).** His own Yosys synthesis bug passed gate-level sims and was only found by a dedicated eqy run. GL sims only prove the patterns you give them | Not done. Formal covers RTL properties only (`formal/radio_digital.sby`). → action 7. |
| 13 | **Transient noise.** Transient and PEX sims have no thermal / flicker / shot noise. Injecting an equivalent input noise from a linear noise analysis is a workaround: it misses input noise driving later stages nonlinear. VACASK can do real transient noise | We use exactly that workaround (`sim/rx/gen_det.py`, NF 11 dB over 450 MHz). Earlier VACASK work stopped at no sky130 models (PLAN.md "Stretch"). → action 13. |
| 14 | **Long runners:** a days-long sim sending a whole code, on a server, before tape-out and while waiting for silicon, to prepare bring-up | Not done: a 30 µs on/off pair stands in for the ~8-day extracted-tile joined run. → action 12. |
| 15 | **Regulations:** no legal transmission without certification. Cable + attenuators (say 45–50 dB ≈ "50 m"), or a shielded room / EM chamber | README has the regulations notice; the bring-up plan already does the cabled link (L1) before the air link. → action 15. |
| 16 | Bring-up plan is good; **check for oscillation first** | R0 is the oscillation check. |
| 17 | **Rescue path:** the input is the only off-chip node, so an external network on it (shunt / series R, L, C, or a cable into a quiet source) may stop an oscillation. Put SMD footprints on the board | Added to [bringup.md](bringup.md) ("If the chain oscillates") and its equipment list. → action 14. |
| 18 | Dropping to ~60 dB of gain takes most of the risk out. He'd expect problems from 80 dB up | The strap gives ~70 dB. No 60 dB option yet. → action 10. |

## Actions

**Corrections, done in this commit**
1. [how_it_works.md](how_it_works.md): the input is high-impedance and unmatched; what that costs.
2. [verification.md](verification.md): the `lna_chain` row leads with the current stability result, strap included.
3. [bringup.md](bringup.md): "If the chain oscillates" (rescue networks on the input, in order) and an adapter
   board in the equipment list.

**Sims, no layout change** (handed off, below)

4. **AC stability margin** of the chain: loop gain through the coupling path, gain / phase margin against
   coupling, corners and strap state, cross-checked against the kick test.
5. **RC loads**: a C across each load R, sized for ≤ 0.5 dB loss in band, and how much coupling margin it buys.
6. **Bond-wire / package coupling**: mutual L between the input and supply / ground bond wires, and the k
   at which the chain oscillates.
7. **Equivalence check** of `radio_digital`: RTL vs the shipped netlist with eqy, including a planted-bug run to
   prove the check isn't vacuous.

**Design changes, later** (depend on 4–6)

8. A straight (or L) chain layout: tall thin stages, squashed input caps, multiple vias; re-floorplan.
9. Local decap inside the chain blocks.
10. A lower-gain option (~60 dB): a harder strap, or a second level.
11. A resistive-feedback input stage for a defined input resistance. Trades NF for match; only if the bench shows the
    mismatch hurts.

**Long runners, after any LNA change** (12, 13)

12. A multi-day joined run on the extracted tile, sending a whole code.
13. Real transient noise (VACASK with sky130, or ngspice device noise in transient) against the NF-11 workaround,
    especially stage-1 noise driving later stages into limiting.

**Hardware**

14. An adapter board on the TT breakout: SMD footprints for shunt and series parts on `ua[0]` / `ua[1]`, and an
    SMA or balun footprint for cabled tests.
15. Book the university EM chamber for the air-link tests. Keep public demos and videos cabled, or state they were
    done in a shielded environment.

## Decisions (Matt, 2026-11-13)

- 1–3: done in this commit.
- 4, 5, 6: one session, branch `chain-stability-ac`, [handoff_chain_stability_ac.md](handoff_chain_stability_ac.md).
- 7: one session, branch `digital-eqy`, [handoff_eqy.md](handoff_eqy.md).
- 8: first a sketch of tall, thin stage cells, to see if a straight chain fits in the U's box (it can also be
  flipped, input on the left): branch `chain-tall-stages`, [handoff_tall_stages.md](handoff_tall_stages.md).
- 9–11: later, once 4–6 have reported.
- 12 and up: only after any LNA changes are made.
