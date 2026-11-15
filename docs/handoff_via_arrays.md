# Handoff: via arrays at every junction (branch `via-arrays`)

From Harald Pretl's design review ([review_harald_2026-11-13.md](review_harald_2026-11-13.md), point 11). Written
2026-11-14. Paste the prompt at the end into a session on sim-0.

## Why

Harald pointed out that our layouts often join two metals with **one via**, squeezed into a thin wire's width. One
cut has the highest resistance, the least EM headroom, and a single bad cut opens the net. The rule is now in
`docs/layout.md` "Checklist", "Wiring", with Matt's sketch (`docs/images/via_flare_sketch.jpg`):

- **Widen both sides locally:** a tab on the rail / strap / bar, and a flare on the wire just before the junction, so the
  overlap fits a cut array: ≥ 2 × 2 wherever it fits, never one cut.
- The wire goes back to its normal width once clear of the junction.

The tall chain cells (`amp_dp_t`, `amp_dpc_t*`, `chain_in_t`) already put as many cuts as each landing allows, but
don't flare. Their narrowest landings are single-row via1 on the 0.42 µm met2 bars. Every other block predates the
rule. This job brings the whole tile up to it **without changing any circuit, pin position or block outline.**

## Read first

- `docs/agent_start.md`, `STATUS.md`.
- `docs/layout.md`: "Checklist" (the new via-array item), "Current limits: EM and IR", "Block convention", and the
  section of each block before you touch it.
- `layout/gen/lay.py`: `Block.via` (fills a box with a centred cut array), `Block.stack`, `cuts_needed`.
- `docs/tall_stages_2026-11.md`, "The tile": the current tile (floorplan "RX in the corner") and how it's built and
  checked (`layout/gen/top.py`, `top_nets.py`, `route.py`, `layout/check_top.sh`).

## Scope

The analog blocks in the tile (`layout/floorplan/floorplan.json`): `tx_drv`, `tx_ls`, `tx_ls_en`, `tx_ring`,
`bias_gen`, `comp_ct`, `avg_sc`, `lpf_rc`, `ctrim_1p`, `r2r`, `dbg_tg`, the decap parts, `log_det_t` / `cdet_t` /
`det_cell`, the tall chain cells (their single-row landings only), `rx_t`, and the top-level routing (`top_nets.py`
/ `route.py`: where routed wires land on block pins and on the met4 straps). **Not** the digital macro.

## Steps

1. **Inventory first.** Write `tools/via_audit.py` (KLayout, read-only): per block GDS, for each cut layer (mcon,
   via1, via2, via3), group touching cuts into clusters and count the clusters of **1 cut** and of **1 × n** (single
   row or column), with their net where a label names it. Run it on every block and the tile. Commit the table
   (block × cut layer: clusters, single cuts, single rows) **before changing anything**: it's the baseline.
2. **Helper (optional).** If the same pattern keeps coming up, add a `Block.junction(...)` to `lay.py` that draws the tab,
   the flare and the array. Adding a function changes no existing output. Still regenerate the blocks that import
   `lay.py` and XOR them against the committed GDS (agent_start rule), and push that on its own.
3. **Fix, block by block**, in this order:
   1. **Supply and high-current paths:** block rails to straps, decap connections, the TX drivers and level shifters
      (the biggest currents, `docs/layout.md` "tx_drv currents"), bias_gen's outputs, and the top-level supply feeds.
   2. **Every other non-RF junction:** bias lines, enables, clocks, trim, `dbg`.
   3. **RF and sensitive nets** (chain signals and taps, `det`, Cin, comparator inputs, avg_sc's caps): the smallest
      array that fits, ideally 2 cuts, only where the block's PEX shows the added C costs nothing measurable. If it
      does cost something, leave that junction and list it.
   - Generators only: no hand edits to GDS. If a junction can't be flared without moving a pin or growing the
     outline, leave it and list it.
4. **Per block:** `layout/check.sh <block>` (DRC 0 magic + KLayout, antenna 0, LVS match), `layout/pex.sh <block>`
   and its `tb_<block>.py --pex`: the result must be unchanged or better. Rerun `tools/via_audit.py` on it.
5. **Tile:** rebuild (`top.py`, `route.py`), `layout/check_top.sh` (DRC, LVS, antenna = the macro's own 7, precheck),
   `tools/check_pinout.py`, and export to `gds/` and `lef/` as the tall-chain branch does.

## Report

- In `docs/layout.md`, a section "Via arrays (2026-11)": the audit table before / after per block, what was left as
  single cuts and why (one line each), any PEX changes, and the run command for the audit.
- One line in STATUS.md "Start here", and update point 11's row in `docs/review_harald_2026-11-13.md` "Where it
  stands".

## Rules

- No circuit changes, no pin moves, no outline changes. Stop and report if a block would need one.
- Shared code: the agent_start rule (regenerate and XOR).
- sim-0: keep the total of running ngspice threads ≤ 28.
- Push to `via-arrays` only, in small commits (one block per commit is fine). Matt merges.

## Prompt

```
Read docs/agent_start.md, then docs/handoff_via_arrays.md, and do it on branch via-arrays
(git fetch && git checkout -b via-arrays origin/main). No circuit, pin or outline changes. Commit the via audit
baseline first, then fix block by block. Push in small commits; stop and report when the tile is rebuilt and
clean, or if a block needs a pin or outline change.
```
