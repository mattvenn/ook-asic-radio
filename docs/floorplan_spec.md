# Top-level floorplan: spec for the interactive floorplan page

Written 2026-10-08 for a Claude session (cloud) to pick up. Read this, then `STATUS.md` (where we are),
then the parts of `docs/layout.md` you need (block notes, power rules). Don't read `docs/history.md` whole.

## Goal
Matt and Claude agree the top-level floorplan of the 3x2 analog tile together:
- An **interactive floorplan page** (a claude.ai artifact) that both can see and edit.
- Matt drags blocks around. Claude proposes **named variants**. Matt flips between them, tweaks one and picks.
- The chosen placement is exported to **`layout/floorplan/floorplan.json`** in the repo. A later `layout/gen/top.py` reads that file to build the real top-level GDS, so nothing is re-typed.

## Data (in the repo)
- **`layout/floorplan/tile.json`**: the tile outline (493.12 × 225.76 µm) and all 51 signal pins (met4, 1 µm deep, on the top and bottom edges), from tt-support-tools `tech/sky130A/def/analog/tt_analog_3x2_3v3.def`.
  - Note: `def/tt_block_3x2_pg.def` is the *digital* 3x2 (508.76 µm wide, no `ua` pins). Not ours.
  - Bottom edge: `ua[0]` x 136.6, `ua[1]` 117.3, `ua[2]` 98.0, `ua[3]` 78.7, `ua[4]` 59.3, `ua[5]` 40.0 (free), `ua[6]`/`ua[7]` not usable (`src/project.v`).
  - Top edge: the TT digital pins between x 15 and 131 (`uio_oe` 15–35, `uio_out` 37–57, `uo_out` 59–79, `uio_in` 81–101, `ui_in` 103–123, `rst_n` 125.6, `clk` 128.3, `ena` 131.1).
  - Nothing to the right of x ≈ 137: the whole right part of the tile is free.
- **`layout/floorplan/blocks.json`**: every laid-out block's bbox (w × h, µm, origin at its lower-left) and its labels (pins plus some internal nets), with the layer and position.
  - Regenerate with `tools/floorplan_blocks.py` when a block changes. It needs the `klayout` Python module: `pip install klayout` works on Linux. On Matt's Mac it runs via `tools/osic-mac`.
- **`layout/README.md`**: the same sizes plus TT GDS viewer links for each block.

## What goes in the tile

| instance | cell | size (µm) | status | notes |
|---|---|---|---|---|
| macro | `radio_digital` | 260 × 190, +5 halo | hardened (`openlane/radio_digital/runs/cg_260x190`) | Pins: N = TT digital pins (fanning in from the top-left), W = analog interface (see Nets). Max layer met4. |
| xchain | `lna_chain` | 145.4 × 70.5 | done (U fold, 2026-10-09) | Front row: input section (2 × Cin 2 pF MIM, Rb pair, Mref) + `amp_dp` + `amp_dpc`; 14 µm guard-ring moat; back row: 4 × `amp_dpc` rotated 180. Placed R180: inputs on its tile-south edge over ua[0] / ua[1], taps on the tile-north edge, vcm / ibias toward bias_gen. |
| xdet | `log_det` | 87.3 × 31.0 | done | Taps all six stage outputs, so it pairs tightly with the chain. Top row t1 t2 t3 inputs on the top edge, bottom row t4 t5 t6 on the bottom edge; t1 and t6 on opposite corners. `det`/`ibias_det` at the left edge, VDD strip down the right edge. |
| xlpf | `lpf_rc` | 65.2 × 35.0 | done | |
| xavg | `avg_sc` | 77.3 × 30.4 | done | `phi1`/`phi2` on the top edge (met4); `in`/`out` on the right edge (met3), adjacent, meant to face `comp_ct`'s left edge. Keep clock wiring off the Cavg top plates. |
| xcomp | `comp_ct` | 73.5 × 42.0 | done | `inn`/`inp` on its left edge. |
| xdac | `r2r` | 71.8 × 54.1 | done | `b0..b7` from the macro's `trim_out[0..7]`; `out` → Ctrim → `comp_ct.trim`. |
| Ctrim | 1 pF MIM | ~23.5 × 23.5 | **not laid out** (top-level cap) | On the `trim` node. |
| xbias | `bias_gen` | 80.2 × 49.1 | done | `en` left (met3); `ib_chain`/`ib_det`/`ib_comp` right (met2); `vcm` right (met3). VDD rail is in the *middle* (met3, x 0–27.7), VSS at top and bottom. |
| xdbg | `dbg_tg` | 5.7 × 16.3 | done | Switches `det` onto `ua[2]`. |
| xtx.xring | `tx_ring` | 18.3 × 7.0 | done | |
| xtx.xls | `tx_ls` | 14.2 × 19.0 | done | |
| xtx.xlse_p, xtx.xlse_n | `tx_ls_en` | 13.3 × 15.5 each | done | Assumed: the two arm-enable shifters use the `tx_ls_en` layout. Check `xschem/tx_top.sch`. |
| xtx.xdrv_p, xtx.xdrv_n | `tx_drv` | 40.9 × 26.7 each | done | Outputs on met3 (2.5 µm) to `ua[3]`/`ua[4]`. |
| xdeca | `decap_vapwr` | **estimate** ~18k µm² | **not laid out** | 50 pF on VAPWR: n = 100 units of 2 × thick-oxide MOS (10 × 5) + one 10×10 MIM. 18k is `sim/area/area_netlist.py`'s footprint rule; a dense tile could be ~13–14k. |
| xdecd | `decap_vdpwr` | **estimate** ~4.1k µm² | **not laid out** | 30 pF on VDPWR: n = 30 units, thin MOS. |

The TX is assembled as `tx_top` at the top level (STATUS: "assemble `tx_top` as part of that floorplan"), so its parts can be placed as a group or individually.

## Nets between blocks (for flylines and wire-length checks)
- **Pins (reassigned 2026-10-09):** `ua[0]`/`ua[1]` RX, `ua[2]` debug, `ua[3]`/`ua[4]` TX (was TX 0/1, RX 2/3, debug 4).
- **RX path:** `ua[0]` → chain `inp` (rx_p); `ua[1]` → chain `inn` (rx_n). Stage k outputs → `log_det` tk (differential, k = 1..6; t6 = the chain output). `log_det.det` → `lpf_rc.in` and → `dbg_tg` → `ua[2]`. `lpf_rc.out` → `avg_sc.in` and `comp_ct.inp`; `avg_sc.out` → `comp_ct.inn`. `comp_ct.out` → macro `comp_in`.
- **Trim:** macro `trim_out[0..7]` → `r2r.b0..b7`; `r2r.out` → Ctrim → `comp_ct.trim`.
- **Clocks and enables from the macro:** `sc_phi1`/`sc_phi2` → `avg_sc.phi1`/`phi2`; `rx_en` → `bias_gen.en`; `dbg_en` → `dbg_tg.en`; `tx_en`/`tx_en_n` → TX.
- **Bias:** `bias_gen.ib_chain` → chain, `ib_det` → `log_det.ibias_det`, `ib_comp` → `comp_ct.ibias`, `vcm` → chain (Rb).
- **TX:** ring → `tx_ls` → `tx_ls_en` (×2) → `tx_drv` (×2) → `ua[3]` (tx_p) / `ua[4]` (tx_n).
- **Macro west-edge pin order**, bottom → top (`openlane/radio_digital/pin_order.cfg`): `tx_en`, `tx_en_n`, then `rx_en`, `dbg_en`, then `comp_in`, `sc_phi1`, `sc_phi2`, then `trim_out[0..7]`, all in the lower part of the edge.

## Rules, ranked
The radio is **half-duplex** (`ui[7]` sets the role). In RX the ring's enable (`key`) is low, so the ring is stopped and both TX arms are held low. Nothing in the TX switches while we receive. So TX ↔ RX separation is a *soft* preference. What switches during RX are the aggressors.
1. **Chain input far from the digital macro.** At a 10 MHz clock, the 43rd and 44th harmonics are 430 and 440 MHz, in the chain's 330–560 MHz band, and the correlator runs all the time in RX. Maximise the distance from the macro (and its supply) to the `ua[0]/[1]` → stage-1 input. Keep macro → analog signal wires off the chain.
2. **Chain output → input coupling ≤ 0.1 fF** (asymmetric). The ss 10 °C corner oscillates at 0.5 fF. Keep stages 5–6, `log_det` t5/t6 and anything carrying full-swing 434 MHz away from the pads, the `ua[0]/[1]` wires and stage 1. No wire from the late stages should run alongside the input.
3. **Keep clock edges off the RX:** `sc_phi1/2` (macro → `avg_sc` top edge) and `comp_ct.out` (→ macro) stay away from the chain and `log_det`. Don't route them over the Cavg top plates.
4. **Short analog signal path:** `log_det` → `lpf_rc` → `avg_sc` → `comp_ct`, and `r2r` → Ctrim → `comp_ct`. `avg_sc.in/out` face `comp_ct`'s left edge.
5. **TX at `ua[3]/ua[4]`** with short, wide (met3, 2.5 µm) driver → pad wires. `tx_en`/`tx_en_n` come from the bottom of the macro's west edge.
6. **Bias:** `bias_gen` near the chain (ib_chain and vcm are the sensitive ones), with reasonable reach to `log_det` and `comp_ct`.
7. **Decaps as fill:** close to their supply straps. The strip above or below the macro (~270 × 26 µm, or one ~31 µm band if the macro is pushed to the top or bottom edge) is decap-only space.
8. **TX vs RX distance:** soft. Nice to have, not at the cost of rules 1–2.
9. **Spacing:** ≥ ~2–3 µm between blocks for guard rings (a "keep-out" setting on the page; the area check adds 10 %).

## Power and layer constraints (`docs/layout.md`, "Power: how the TT PDN connects")
- Power pins are **vertical met4 straps**, ≥ 1.2 µm wide, running from within 10 µm of the bottom edge to within 10 µm of the top. Several per net are allowed; they must not touch each other. Nets: VDPWR, VAPWR, VGND.
- **No met5** (reserved for the TT PDN, which runs horizontal met5 stripes at 57.12 µm pitch).
- Plan: straps on both the left and right of the analog area, plus a mid strap if needed. Blocks connect from their met3 rails with via3 where a strap crosses, or with short met3 spurs.
- **Straps need clear met4 lanes.** MIM top plates are met4 (`cap_mim_m3_1`), and some pins are met4 (`avg_sc` phi1/phi2 and its `out` strip). A full-height strap can't cross those. The page should show the strap lanes and flag a strap crossing a block that uses met4.
- **Open question: the right-edge straps vs the macro.** The macro routes up to met4, so straps can't cross it. Either leave a lane at the tile's right edge (shift the macro left by ~10–15 µm), or put the "right" straps between the analog area and the macro.

## Area budget (2026-10-08 fit check)
- Tile 111.3k µm². Macro + halo 270 × 200 = 54.0k µm². Left: **~57.3k**. That's a ~223 × 226 µm rectangle (~50.4k) plus the strip by the macro (~7k, decap only).
- Signal blocks ~28k (laid-out ~25.3k, chain inputs ~2.2k and Ctrim ~0.55k estimated). Decaps ~22k (estimated). Spacing ~2.8k. **Total ~53k ≈ 92 % of the space left.**
- A hand packing of the real outlines puts the signal blocks in ~160 µm of the 226 µm height, leaving ~11–14k below them plus the 7k strip for ~22k of decap. Tight.
- Levers if it doesn't fit: VAPWR decap 50 → 30 pF (−7k; ripple ~0.05 → ~0.15 V), a denser decap tile, the macro pushed to the top or bottom edge, a re-hardened denser macro.

## The page
- **Canvas:** the tile to scale, with zoom and pan and a µm grid (snap 0.5 µm). Tile pins drawn and labelled at their DEF positions; the macro with its halo; strap lanes.
- **Blocks:** rectangles at real size, labelled, with their pins from `blocks.json` drawn as small marks.
  - Drag; rotate 90°; mirror X/Y. Use the GDS orientations R0/R90/R180/R270/MX/MY/MXR90/MYR90 so the export maps straight onto a KLayout `DCplxTrans`.
  - Estimated blocks (chain, decaps, Ctrim) drawn hatched, with an editable w × h. The decaps can be split into several rectangles of a given total area.
  - The macro is draggable too, but it starts at the right.
- **Flylines** for the nets above, from block pin to block pin, coloured by class (RX signal, clock/digital, bias, TX, trim). Each net's Manhattan length is shown on hover and listed.
- **Live checklist** for the ranked rules, each pass/warn/fail with the number behind it. For example: "chain input ↔ macro 182 µm", "stage 6 ↔ stage-1 input 64 µm", "phi lines cross RX: no", "overlaps: none", "strap lane blocked by avg_sc met4". Thresholds editable on the page.
- **Area panel:** used / free, signal blocks vs decap vs spacing, matching the budget above.
- **Variants:** named, each with the placement and a short note. Claude writes variants into the page's shared state, and Matt's edits are saved there as well, so each side can read the other's. Flip, duplicate, rename, delete.
- **Export/import** of `floorplan.json`:

```json
{
  "variant": "A: RX left, TX middle, macro right",
  "tile": {"w": 493.12, "h": 225.76},
  "blocks": [
    {"inst": "xdet", "cell": "log_det", "x": 12.0, "y": 140.0, "orient": "R0", "estimate": false},
    {"inst": "xdeca", "cell": "decap_vapwr", "x": 230.0, "y": 0.0, "w": 260.0, "h": 30.0, "orient": "R0", "estimate": true}
  ],
  "straps": [{"net": "VGND", "x": 2.0, "w": 2.0}, {"net": "VAPWR", "x": 6.0, "w": 2.0}]
}
```
  `x`, `y` are the lower-left corner of the placed (transformed) bbox, in tile µm. `w`, `h` only for estimated blocks.
- Follow the repo's artifact flow: claude.ai artifact, private by default, shared state through the artifact's database. Give Matt the link.

## Starting variants (Claude's suggestions; refine them on the page)
- *(Written before the 2026-10-09 pin reassignment, when RX was ua[2]/[3] and TX ua[0]/[1].)*
- **A: RX left, TX middle, macro right.** Chain + `log_det` along the left with the input near `ua[2]/[3]` (x 79–98, bottom). Detector → LPF → avg → comp going up and right, `bias_gen` next to the chain. TX in the middle-bottom at `ua[0]/[1]`, as the idle buffer between the macro and the RX. `r2r` + Ctrim beside `comp_ct` near the macro's trim pins. Decap in the leftover rectangles and the strip by the macro.
- **B: A with the macro pushed to the top edge.** The strip by the macro becomes one ~31 µm decap band along the bottom right. That's easier to tile, and keeps the macro's top-edge pins short to the TT pins.
- **C: chain input low-left, signal path along the top.** The chain runs bottom-left to bottom-centre from the pads, `log_det` above it, and LPF → avg → comp along the top, toward the macro's west pins. This keeps clocks and comparator wires in the upper half, away from the chain. The TX sits at the bottom between the chain's late stages and the macro. Check rule 2: the chain's output end is near the TX pads then, which is fine since the TX is idle in RX.

## Done when
Matt has picked a variant and `layout/floorplan/floorplan.json` is committed, along with any open questions it settles (straps vs macro, decap size). Then: `layout/gen/top.py` places the GDS from it. The chain and decap layouts drop into their reserved outlines.

## The page as built (2026-10-08, cloud session)
- **Sources:** `layout/floorplan/page/` holds `page.html` (UI) and `engine.js` (orientations, pins, nets, ranked-rule checks, `floorplan.json` export/import). `tools/floorplan_page.py [out.html] [--dev]` inlines them with `blocks.json`/`tile.json` into one artifact page (`--dev` also embeds `variants.json` for a local preview without the store).
- **Shared state:** the artifact's database: one document per variant in `variants`, and the thresholds in `config/settings`. Matt's drags are saved there (debounced), and Claude reads and writes the same documents.
- **Variants:** `layout/floorplan/variants.json` mirrors the store. `layout/floorplan/page/place.js` anneals the movable blocks of each variant around fixed anchors, fills the leftover space with decap and picks clear strap lanes, then writes `layout/floorplan/variants.json` (seeded into the store). `node layout/floorplan/page/check.js [variants.json | floorplan.json]` prints the same checklist as the page.
- **`blocks.json`** now also has `lna_chain` and, per cell, `m4`: merged met4 + capm (MIM) boxes, for the strap-lane check (`tools/floorplan_blocks.py`).
- **Findings that change the spec:**
  - **`lna_chain` is drawn as laid out:** one 268.1 × 35.3 µm block with its GDS pins (the page briefly showed a two-part fold proposal; Matt asked for real blocks only, 2026-10-09). Beside the macro there are ~223 µm, so lying flat it fits only under or over the macro: with the macro body on the top edge the band below it is 35.76 µm (0.5 µm to spare, no macro halo), and the chain there covers ua[0]-ua[4] unless it starts right of x ~138.
  - **Pin reassignment (2026-10-09): RX on ua[0]/ua[1] (x 136.6 / 117.3), debug ua[2] (98.0), TX ua[3]/ua[4] (78.7 / 59.3).** The RX pads are now the ones nearest the macro, so rule 1 (chain input far from the macro) is harder to meet. The macro's west-edge order (TX enables lowest, `PIN_ORDER.md`) was chosen for the old assignment. The checks score whatever placement is chosen.
  - **The macro's north pins need a routing channel.** The 42 TT pins (x 15-131) go to the macro's north pins (pin_order.cfg, ~x 231-360 with the macro at the right), so ~42 tracks run horizontally above the analog area and enter the macro from above: ~12 µm of channel (the page's "TT pin channel", editable). With the macro body on the top edge (variant B) the north pins can't be reached at all, unless the macro is re-hardened with them on the west edge.
  - **The macro's comp_in / sc_phi / trim pins are in the lower part of its west edge** (y ~72-117 with the macro at y 23.76); the even pin spread is an estimate until the DEF is read.
  - **Area:** with the real chain (9.45k, was a 6.2k estimate) the signal blocks are 31.3k; with the decap target of 22.1k that is ~92 % of the space beside the macro before spacing, so the VAPWR decap is the lever (50 → ~30 pF).
  - **Still estimates:** Ctrim and both decaps (not laid out, hatched), and the macro's pin positions (even spread of pin_order.cfg until the DEF is read).

## Chosen floorplan (2026-10-09, revised)
- **`layout/floorplan/floorplan.json`** and **`layout/floorplan/pins.md`**: "matt layout 4 (handoff, chain folded)", i.e. "matt layout 4 (handoff)" from the page (Matt's layout 4, nudged, pins refitted with `page/pinfit.js`, decap refilled with `page/refine.js --decap-only`, written by `page/pinreport.js`). `pins.md` lists every block's placement and its pins by edge in the block's own frame, with the moved ones marked: that is the input for the block re-layouts and the macro re-harden (`docs/handoff_pins_reharden.md`).
- **Macro:** 200 × 220 µm (44,000 µm²; a trial harden at this size routes), placed MY at (282.5, 2.88): full tile height at the east end, its own east edge facing west toward the analog. All signal pins on that edge: rx_en at the bottom, the analog interface (trim_out[7:0], comp_in, dbg_en, tx_en, tx_en_n) at y 52–127, sc_phi2/1 at ~147, the 42 TT pins at the top (178–219). The TT wires run east along the top of the tile from the TT pins (x 15–131) to the macro.
- **Analog pins moved** (re-layout): bias_gen, comp_ct, avg_sc, lpf_rc, r2r, Ctrim, dbg_tg, log_det `det` / `ibias_det`. The TX blocks keep their GDS pins.
- **Straps:** three met4 sets: west end (VDPWR, VGND), the gap between the analog and the macro (VAPWR 276.5, VGND 278.2, VDPWR 279.9) and the east end (488.0 / 489.7 / 491.4).
- **Chain (2026-10-09):** re-laid out as the U fold (Matt's option 1 of three), 145.36 × 70.47 µm, R180 at (13.14, 6.5), with the real GDS replacing the page's fold option. The input section is right over ua[0] / ua[1]; stages 5–6 sit across a 14 µm moat (p-tap ring, n-well stripe) from the Cin plates. Rule 2 reads 14 µm (the moat; stage 6 output ↔ input 31 µm). The extracted coupling from stages 4–6 into the input zone is 0 (`docs/layout.md` "lna_chain"). The chain grew 11.3 µm in x: xdecd part 1 is 10.6 µm wide (was 18), so **VDPWR decap is 89 %** (open). The engine's chain zones follow the new layout, and the fold option is gone.
- Accepted: rule 5 (TX driver → pad ~120 µm: route it ≥ 5 µm wide; the TX is off whenever the RX is on), VAPWR decap 97 % (≈ 48 pF, incl. a 54 × 72 µm MIM-only decap on top of r2r), and the page's TT channel check (a false fail when the wires end on the macro).
