# Handoff: equivalence check of the digital macro (branch `digital-eqy`)

From Harald Pretl's design review ([review_harald_2026-11-13.md](review_harald_2026-11-13.md), action 7). Written
2026-11-13. Paste the prompt at the end into a session on sim-0 or Matt's Mac.

## Why

Gate-level simulation (cocotb GL 16/16 on `macros/radio_digital/radio_digital.nl.v`) only proves the netlist matches
the RTL **for the stimulus we give it**. Harald hit a Yosys synthesis bug on his own blocks that passed gate-level
sims and was only found by a dedicated equivalence check with eqy. A logic-equivalence check (LEC) proves the
synthesised netlist does what the RTL says for **every** input. He uses a mix: GL sims everywhere, LEC wherever it
can be made to prove. Some circuits it can't prove nicely.

Your job: **set up eqy to prove `radio_digital` RTL ≡ the shipped netlist**, show the check isn't vacuous by
catching a planted bug, and report what is proven and what isn't. Don't change the RTL or the macro. If eqy finds a
real mismatch, stop and report it with the failing signals: that's the result this exists to find.

## Read first

- `docs/agent_start.md`, `STATUS.md`, `docs/verification.md` (the "Formal" and digital sections).
- `formal/radio_digital.sby`: how the RTL is read for formal today (`read_verilog -D SIM -formal -sv`, file list,
  `multiclock on`).
- `verilog/rtl/`: `radio_digital.v` (top), `rd_cg.v` (clock gating: one `sky130_fd_sc_hd__dlclkp_1` per 127-bit chip
  register, instantiated **in the RTL**), `rd_gold.v`, `rd_corr.v`, `rd_rx.v`, `rd_tx.v`.
- `openlane/radio_digital/config.json` / `config.tcl`: the synthesis settings (flattening, `SYNTH_*`, any retiming or
  buffering options) and the LibreLane version (3.0.3, run `lnalo`).
- `macros/radio_digital/radio_digital.nl.v` (the netlist that is in the GDS: check this against the LVS'd one) and
  `radio_digital.pnl.v` (with power pins).

## Setup

- `git fetch && git checkout digital-eqy`.
- Find eqy: in the osic image (`tools/osic which eqy`) or oss-cad-suite. Note the Yosys version, and compare it with
  the one LibreLane used for synthesis (in the run's logs, or LibreLane's pinned version). An eqy run on the same
  Yosys that had a bug could miss it: if they're the same, say so in the report.
- Cell models: the sky130_fd_sc_hd **functional** Verilog from the PDK
  (`$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/verilog/`, `primitives.v` + `sky130_fd_sc_hd.v`, without
  `USE_POWER_PINS`). Fill, tap, decap and diode cells have no logic: black-box or drop them.
- New files go in `formal/eqy/`: the `.eqy` file, a `run.sh`, and the planted-bug netlist (or a script that makes it).

## Steps

1. **Gold** = the RTL with the same defines as synthesis (**not** `-D SIM` or `-formal` unless synthesis used them:
   check). **Gate** = `radio_digital.nl.v` + the cell models. Same top, `radio_digital`.
2. **Clock gating.** The ICG cell is instantiated in both, so let eqy match it as a cell, or black-box
   `sky130_fd_sc_hd__dlclkp_1` on both sides so the latch inside doesn't get in the way. Say which you chose and why.
3. **Matching.** Flattened gate netlists rename registers. Use eqy's `[match]` rules and LibreLane's naming, and check
   how many state elements matched by name vs by structure. Unmatched registers usually mean a renaming (fix the
   match), retiming or register merging (find out whether synthesis did it), or constant registers removed (expected:
   list them).
4. **Strategies.** Start with `sat` (combinational between matched registers). For partitions that don't prove, try
   `sby` with induction, and say what was needed.
5. **Planted bug (required).** Make a copy of the netlist with one deliberate change in the logic: swap an `and2` for
   an `or2` in the correlator's or the TX/RX enable's cone, or invert one input. Run the same eqy flow: **it must
   fail, on that partition.** Then try a bug that only shows deep in time (e.g. on the correlator count's top bit),
   to see whether the strategies catch it. Keep the planted-bug run in `run.sh` as a self-test.
6. **Also, cheaply:** run the same check on `radio_digital.pnl.v` (with power pins) or show it's the same as
   `nl.v` with the power ports stripped.

## Report

In `docs/verification.md`, a new "Equivalence (eqy)" subsection next to "Formal":
- the command (`tools/osic bash formal/eqy/run.sh`), the time it takes;
- partitions: total, proven, and which didn't prove and why (one line each);
- the planted-bug results (caught or not, in what time);
- the Yosys versions of synthesis and of eqy.

One line in STATUS.md "Start here". If eqy can't be made to prove most of the design in reasonable time, say so and
recommend whether to keep it (as a partial check) or not.

**Don't** add it to CI yet: report the run time and recommend whether it fits a GitHub action. **Don't** re-harden
the macro. Push to `digital-eqy` only. Matt merges.

## Prompt

```
Read docs/agent_start.md, then docs/handoff_eqy.md, and do it on branch digital-eqy
(git fetch && git checkout digital-eqy). Don't change the RTL or the macro. Push to that branch in small commits;
stop and report if eqy finds a real mismatch, and when the check and the planted-bug self-test are done.
```
