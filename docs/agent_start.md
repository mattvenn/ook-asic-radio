# Agent start-up (read this first)

Several Claude sessions work on this repo at once, all pushing to `main`. Keep the start-up
read small: context spent on setup is context not spent on the block.

## Rules
- **Only work on what Matt assigned you.** The leaf-block list in STATUS.md "Start here" says
  what's done; if it's unclear whether a block is taken, ask.
- **Before every push:** `git fetch`, rebase onto `origin/main`, and re-check STATUS.md /
  docs/layout.md merged cleanly (they conflict most). Push small commits often.
- **Shared code** (`layout/gen/rows.py`, `lay.py`, `passives.py`, `tools/`): other blocks depend on
  it. If you change it, regenerate the blocks that use it and XOR their GDS against the committed
  ones (they must come out identical), then push the change on its own, early.
- **Tools:** on the Linux host `tools/osic <cmd>`; on Matt's Mac `tools/osic-mac <cmd>` (from the
  repo root). Sim scripts take `OSIC=$PWD/tools/osic-mac`. Don't run ngspice jobs in parallel.

## What to read (and what not to)
- `STATUS.md`: all of it (short). Per-block history is in `docs/history.md`: grep it for your
  block, read only that section.
- `docs/layout.md` (if doing layout): "Steps", "Checklist", "Block convention", the EM table, and
  the newest block section. Skip the rest unless you hit the problem it describes.
- `docs/sim_learnings.md` before writing a new testbench.
- The block's schematic generator (`xschem/gen/<x>.py`) and **one** finished generator of a similar
  block as a template (`layout/gen/<similar>.py`).
- `rows.py` / `lay.py` / `passives.py`: function signatures and docstrings only
  (`grep -n "^def \|^class \|\"\"\"" layout/gen/rows.py`), not the bodies.
- Don't print whole files or long tool output: grep/sed the part you need; pipe installs,
  netlists and sim logs through `tail` / `grep`.
- Don't re-verify other people's blocks unless you changed shared code.

## Done (layout block)
- DRC 0 in both magic and KLayout, antenna 0, LVS match (`layout/check.sh <block>`).
- PEX (`layout/pex.sh <block>`) and a `sim/<dir>/tb_<block>.py [--pex]` comparing schematic vs
  extracted on what the block must do.
- One section or table row in `docs/layout.md` (results + lessons others can reuse), one line in
  STATUS.md's leaf-block list, `python3 tools/gds_links.py` for the viewer link.
- Fetch, rebase, push. Report the numbers briefly.

## Example prompt
```
Read docs/agent_start.md, then lay out <block> (assigned to you; other sessions are on
<blocks>). Template: layout/gen/<similar>.py. <Anything specific: floorplan outline, pin sides.>
```
