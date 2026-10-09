# Handoff: power-delivery measurement on the laid-out tile

Prompt for a new session (written 2026-10-09 by the top-level layout session). Paste it as is.

---

The tile is assembled and routed. Your job: **measure how well power is delivered to every block, with magic extraction and ngspice only** (the tools we trust; no home-made solvers), take a benchmark, then propose improvements for Matt to choose from. **Don't change the layout yet**: another session owns the top level (`layout/gen/top.py`, `route.py`, `top_nets.py`, `decap.py`) and is still editing it. Measure, report, propose. Commit and push to `main` as you go (small commits; other sessions push to `main` too).

## Read first
- `docs/agent_start.md` (rules for agents on this repo), `STATUS.md`.
- `docs/layout.md`: "Power: how the TT PDN connects", "Current limits: EM and IR", the tx_drv current table.
- `docs/handoff_toplevel.md`: what the tile is made of (blocks, placements, straps, nets).

## Tools
- Mac: `tools/osic-mac <cmd>` from the repo root (Linux: `tools/osic`).
- **Run anything slow in the background and end the turn** so Matt can keep talking. Never wait on a background job with a foreground loop. Don't run ngspice jobs in parallel.

## What exists
- **Tile build:** `tools/osic-mac klayout -b -r layout/gen/top.py` (placement, straps, decaps) then `tools/osic-mac python3 layout/gen/route.py` gives `build/top/tt_um_mattvenn_radio.gds`. Block pins in tile µm: `build/top/pins.json`. Checks: `layout/check_top.sh` (LVS clean, magic + KLayout DRC 0 as of 2026-10-09).
- **Extraction of the analog part** (tile minus the digital macro, as a drop-in `radio_analog`): `tools/osic-mac bash layout/pex_tile.sh {lvs|c|rc}` writes `layout/pex/radio_analog_<mode>.spice`.
  - It flattens first, so the substrate is part of VGND.
  - It's fast: rc takes ~11 s and gives ~85k R, ~18k C, 1125 devices.
  - In rc mode, VGND is split into ~117k `VGND.nN` sub-nodes, VDPWR into `VDPWR.nN` / `VDPWR.tN` (device terminals), likewise VAPWR. Block-internal nets keep hierarchical names (`comp_ct_0.tail`, `avg_sc_0.cs`, …).
  - Route labels name the inter-block nets (`det`, `lpf`, `avg`, `trim`, `vcm`, …).
- **End-to-end deck:** `python3 sim/top/tb_tile.py sch lvs c rc` runs `xschem/tb_radio_analog.sch` with `radio_analog` from the schematic or the extracted tile. The RX/TX source setup and pad models are in `xschem/gen/top.py` (`tb_radio_analog`, `TB_CODE`).

## Power structure (as built)
- **Straps (met4, the tile's power pins):** west VAPWR x 2.5 / VDPWR 9.3 / VGND 13.9; mid VAPWR 276.5 / VGND 278.2 / VDPWR 279.9; east 488.0 / 489.7 / 491.4. The macro's two VPWR and two VGND met4 stripes are power pins too.
- **Joins:** met3 bars along the bottom (VAPWR y 0.4–1.3, VDPWR 1.7–2.6, the VDPWR one full width) and VGND along the top (y 223.4–224.4) join the mid and east straps. The decap rails join the west and mid VAPWR/VGND.
- **TT PDN:** met5 stripes land on every met4 power-pin shape where they cross, set pitch 57.12 µm. The phase relative to the tile isn't known: say what you assumed.
- **Supply routing** (`layout/gen/top_nets.py`):
  - TX: VAPWR_TX / VGND_TX / VDPWR_TX, 2–2.5 µm, from the west straps.
  - RX: VDPWR_RX / VGND_RX, 1 µm, from any strap.
  - Decaps: VAPWR_DEC / VGND_DEC.
  - The RX and TX grounds join only at the straps.
- **Decaps** (`layout/gen/decap.py`):
  - VAPWR ≈ 20 pF MOS (thick oxide) + 23 pF MIM.
  - VDPWR ≈ 8 pF MOS + 2.7 pF MIM.
  - Parts: xdeca1–5 (VAPWR: x 242–275 full height; the top band y 193–213; x 0–50 y 162–190; x 182–239 y 166–190; over r2r) and xdecd1–3 (VDPWR: west edge; x 213–239 y 3–88).

## First benchmark (a rough cross-check, not the answer)
A quick mesh solve over the traced metal (`tools/power_r.py`, straps ideal, current injected at each block's pin marker) gave the DC resistance from each block's supply pin to the straps:
- **TX:** 0.15–2.2 Ω (tx_drv_p VAPWR 2.17 Ω, VSS 1.87 Ω; tx_drv_n VAPWR 0.27 Ω).
- **RX VDPWR:** chain 3.5, bias 10.7, log_det 14.5, avg_sc 24, comp_ct 24 Ω.
- **RX VGND:** chain 9.0, det 24, bias 27, lpf 31, Ctrim 47, comp 55, avg 61 Ω.
- **Decaps to the straps:** VAPWR side 7–33 Ω, VGND side 5–47 Ω. At 434 MHz a 20 pF decap is only ~18 Ω of reactance, so the far decaps may barely help the TX.

Reproduce these with magic + ngspice and say where they disagree.

## Measurements wanted (magic rc extraction + ngspice)
1. **Probe points:** a block's local supply = the supply sub-nodes its own devices connect to (devices that also touch `<block>_0.*` nodes). Pick a sensible set per block, e.g. the tail / source terminals, and say how you chose.
2. **PDN ties:** the met5 landing points on each strap.
   - The extracted netlist exposes each supply as a port at one point. Find a way to get a node at each met5 crossing, for example extra labels on the straps in the extraction copy of the GDS (`layout/pex_tile.sh` strips the macro and adds labels already), and check how magic keeps them.
   - Tie them through a PDN model: met5/via4 R per landing, plus the package/bond-wire L and R. Ask Matt for the values or take the TT spec's ~0.1 V at 20 mA, and state the assumption.
3. **DC:** resistance from each block's local VDD and VSS to the ties. Then IR drop with real currents: tx_drv 6.65 mA average / 18.4 mA peak per arm on VAPWR (`docs/layout.md`), RX total ~3 mA on VDPWR (split per block from the schematic's op).
4. **AC:** |Z(f)| at each block's local supply (VDD to VSS, and each to its tie), 1 MHz–2 GHz, with the RX biased on and the real decaps and device capacitances in. Read off 434 MHz, the ring's actual frequency (~460–530 MHz extracted) and the sc_phi rate (77 kHz).
5. **TX→RX coupling:** AC current at the TX drivers' VAPWR/VSS, then the voltage at the chain input stage's VSS/VDD, det, lpf, avg and comp_ct's local ground. Also a transient with the TX keyed (the TX run in `TB_CODE`) watching the RX ground and supply bounce.
6. **EM:** current per via cut and per µm on the main supply paths at the TX currents, against the table in `docs/layout.md` (≥ 2× margin).

## Then
- **Put the benchmark in one table** (per block: R to the ties, IR drop, |Z| at 434 MHz, TX→RX transfer) in `docs/power.md`, plus a line in STATUS.md.
- **Propose improvements with an estimate of each one's effect.** Ideas already on the table:
  - wider RX supply trunks on met3/met4;
  - an extra met4 VDPWR/VGND strap pair in the middle of the analog (needs a met4-free column);
  - joining the RX side to the mid straps across decap parts 1 and 3, below the macro-pin band;
  - moving VAPWR decap close to the TX and wiring each decap directly to the load it serves;
  - more via cuts.
- **Matt picks;** the top-level session (or you, if Matt says so) implements.

## Don't
- Don't edit `layout/gen/top.py`, `route.py`, `top_nets.py`, `decap.py` or the block generators. Write new measurement scripts (e.g. `sim/power/`).
- Don't trust `tools/power_r.py` over ngspice: it's only a cross-check.
