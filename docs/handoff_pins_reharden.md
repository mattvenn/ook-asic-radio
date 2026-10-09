# Handoff: move block pins and re-harden the digital macro for the chosen floorplan

**Done (2026-10-09).** Carried out with a routing review on top (floorplan "matt layout 5": comp_ct and r2r flipped to MYR90, macro pins re-ordered); results in `docs/history.md` "Blocks and macro to the chosen floorplan". Next: `docs/handoff_toplevel.md`.

Prompt for a new session (2026-10-09, second version: "matt layout 4 (handoff)"). Paste it as is.

---

We've chosen the top-level floorplan of the 3x2 analog tile. Your job is to make the blocks match it: re-harden the digital macro at its new size and pin order, and move pins in the analog block layouts. Don't change block placements; ask if something can't be done as specified.

**Read first:** the "Notes from the size trials" section at the end of this file (pin-slot mechanics, Mac run commands, what's already in `config.json`), `STATUS.md` (how to run things), `docs/layout.md` (the layout flow and power rules), `docs/floorplan_spec.md` (the last section, "Chosen floorplan"). The source of truth for positions is **`layout/floorplan/pins.md`** and **`layout/floorplan/floorplan.json`** (variant "matt layout 4 (handoff, chain folded)": "matt layout 4 (handoff)" with the real folded chain).

**Conventions in `pins.md`:** µm. Each block's pins are given in the block's *own* frame (its bbox lower-left = 0, 0, before its placement orientation), grouped by its own edge, with the tile direction that edge faces once placed. Pins marked "moved" are the new positions; the rest stay where the GDS has them. Positions along an edge are targets (±a few µm is fine); **the edge and the order along it matter more than the exact x / y**. Keep each moved pin on the same layer as now unless the block's flow needs otherwise.

**Pin map:** ua[0] / ua[1] = RX (rx_p / rx_n), ua[2] = debug (det), ua[3] / ua[4] = TX (tx_p / tx_n).

**Layout in one line:** the macro fills the east end of the tile at full height; the analog blocks sit west of it, with the RX chain along the bottom at the pads, the detector → lpf → avg / comp path above it, r2r + Ctrim next to the macro, and the TX blocks at the west end. The 42 TT wires come in at the top left (x 15–131) and run east along the top of the tile to the macro's west side.

## 1. Digital macro `radio_digital` (`openlane/radio_digital/`)
- **New size:** `DIE_AREA` [0, 0, 200, 220] (44,000 µm²). Matt has already trial-hardened 200 × 220 and it routes. It's placed **MY** in the tile at (282.5, 2.88), so its own **east** edge faces **west** in the tile, toward the analog blocks. All positions below are in the macro's own frame.
- **New `pin_order.cfg`** (LibreLane; see `PIN_ORDER.md` for the syntax). **All signal pins go on the macro's own east edge**, bottom → top in this order (y targets in `pins.md`):
  - `rx_en` 6.6 (bottom corner, to bias_gen `en`)
  - the analog interface, y 52–106: `trim_out[0]` 52.7, `trim_out[1]` 67.7, `comp_in` 73.7, `trim_out[2]` 75.2, `trim_out[3]` 82.7, `dbg_en` 86.5, `trim_out[4]` 90.2, `tx_en_n` 92.5, `trim_out[5]` 97.7, `tx_en` 103.3, `trim_out[6]` 105.2, then `trim_out[7]` 126.5. If interleaving the singles with the trim bus is awkward, keep `trim_out[0..7]` contiguous in this band and put `comp_in`, `dbg_en`, `tx_en_n`, `tx_en` just above it (below ~140).
  - `sc_phi2` 147.1, `sc_phi1` 148.1. Keep these at or above ~140: lower, their run to avg_sc passes over log_det (rule 3, clock edges off the RX).
  - the 42 TT pins at the top, 1 µm pitch: `clk` 178, `uio_oe[7..0]` 179–186, `uio_out[7..0]` 187–194, `uo_out[7..0]` 195–202, `uio_in[7..0]` 203–210, `ui_in[7..0]` 211–218, `rst_n` 219.
  - **North / South / West:** no signal pins.
- **After the harden:** signoff clean (DRC, LVS, antenna, timing at all corners, as for `cg_260x190`); RTL and gate-level cocotb suites (STATUS.md "How to run things"; point the GL netlist at the new run). Update `config.json`, `PIN_ORDER.md` (the rationale is now "analog to the west of the macro, TT pins at the top of the same edge"), STATUS.md and `docs/history.md`. Report the real pin positions from the DEF so we can check them against `pins.md`.

## 2. Analog blocks: pin moves (re-layout with the existing flow)
For each block: edit `layout/gen/<block>.py` (or the block's layout source), regenerate, then `layout/check.sh` (DRC + LVS clean), `layout/pex.sh`, and its block test (`tb_<block>`, schematic vs extracted, no regression) per the policy in STATUS.md. Change only pin positions and the routing to them; no circuit changes. Positions are (x, y) in the block's own frame; the tile direction is in brackets.

- **`bias_gen`** (R90 at (160.5, 7.5)): `ib_chain` (28.18, 48.82) and `vcm` (31.32, 48.82) and `ib_det` (79.22, 48.82) on the **north edge** [faces west, to the chain and log_det]; `ib_comp` (79.97, 48.07) on the **east edge** [faces north, up to comp_ct]; `en` (2.05, 0.25) on the **south edge** [faces east, to the macro's rx_en].
- **`log_det`** (MX at (67.5, 80)): `det` (1.0, 0.25) on the **south edge** [faces north, up to lpf_rc and dbg_tg]; `ibias_det` (87.08, 24.29) on the **east edge** [to bias_gen]. t1–t6 stay.
- **`lpf_rc`** (R0 at (67, 113.6)): `in` (1.5, 0.25) on the **south edge** [down to log_det]; `out` (64.95, 34.02) on the **east edge**, top corner [to avg_sc and comp_ct]. In and out are now on different edges, so the filter can't be bypassed by coupling between them.
- **`avg_sc`** (R0 at (53, 151.2)): `in` (76.35, 0.25) on the **south edge**, east end; `phi2` (77.1, 1.0), `phi1` (77.1, 19.15) and `out` (77.1, 20.15) on the **east edge** [to the macro and comp_ct]. Keep the phi lines off the Cavg top plates (`docs/layout.md`), and put a VSS shield between `phi1` and `out` (1 µm apart).
- **`comp_ct`** (R90 at (137.5, 116.6)): `inp` (31.02, 41.72) and `inn` (35.6, 41.72) on the **north edge** [faces west, to lpf_rc and avg_sc]; `ibias` (0.25, 17.97) and `trim` (0.25, 19.47) on the **west edge** [faces south, to bias_gen and Ctrim]; `out` (1.0, 0.25) on the **south edge** [faces east, to the macro's comp_in].
- **`r2r`** (R90 at (185, 91)): `b0..b7` on its **south edge** [faces east, to the macro] at x 5.62, 20.62, 28.12, 35.62, 43.12, 50.62, 58.12, 65.62; `out` (11.05, 53.87) on the **north edge** [faces west, to Ctrim]. r2r must stay met1-only: a 54.1 × 71.8 µm MIM-only VAPWR decap sits on top of it (`floorplan.json`, xdeca part 5).
- **`dbg_tg`** (R0 at (57.5, 124)): `a` (det side) (3.7, 0.25) and `b` (pad side) (4.7, 0.25) on the **south edge**; `en` (5.45, 6.35) on the **east edge**.
- **Ctrim** (1 pF MIM, not laid out yet): 23.5 × 23.5 µm at (159, 90.3) MX; `n` (1.0, 0.25) on its south edge [faces north, to comp_ct trim], `p` (23.25, 11.75) on its east edge [to r2r out].
- **No change:** the TX blocks (`tx_ring`, `tx_ls`, `tx_ls_en` × 2, `tx_drv` × 2) keep their GDS pins. The TX driver → pad wires are ~110–120 µm: route them wide (≥ 5 µm, met3 or higher) rather than 2.5 µm. The TX is off whenever the RX is on, so they can cross the chain.

## 2b. Power straps (top level, for reference)
Three sets of full-height met4 straps (1.2 µm, `floorplan.json` "straps"): the west end (VDPWR x 9.3, VGND x 13.9), **a new set in the gap between the analog blocks and the macro** (VAPWR x 276.5, VGND x 278.2, VDPWR x 279.9), and the east end (VAPWR 488.02, VGND 489.72, VDPWR 491.42). Nothing in the blocks changes for them, but the macro's west-facing pins (its own east edge) must reach the analog blocks on layers below met4.

## 3. `lna_chain`: done, no work here
The chain is re-laid out as a U fold (2026-10-09): **145.36 × 70.47 µm, placed R180 at (13.14, 6.5)**. The input section and stages 1–2 run along the bottom with Cin_p / Cin_n tabs right over ua[0] / ua[1]. Stages 3–6 come back along the top, across a 14 µm guard-ring moat. `vcm` / `ibias` are on its tile-east edge toward bias_gen, and the taps are on its tile-north edge toward log_det (`pins.md`). Don't change it; `layout/gen/lna_chain.py` and `docs/layout.md` "lna_chain" have the details. At the top level, keep the ua[2] debug wire off the chain: route it west along the bottom gap and up outside it, so it can't bridge stage 5 to Cin_n.

## 4. Don't
- Don't move or resize blocks, or change circuits or schematics, to make a pin fit: report it instead.
- Don't regenerate the floorplan files by hand. If a pin has to land somewhere else, write down where; we'll update the floorplan page (`layout/floorplan/page/`) and re-run `pinreport.js`.

## Floorplan checks on this layout
With the folded chain: pass 1 (chain input ↔ macro 119 µm), 3 (clock edges 25 µm), 4 (analog path 48 µm), 6 (bias 11 µm), 9 (no overlaps), straps (8, all lanes clear). Known and accepted: 2 (14 µm: the moat; the extracted late → input coupling is 0, see §3), 5 (TX wire length, see TX note), 7 VAPWR at 97 %, 8 (soft, 39 µm), and the page's "TT pin channel clear" (a false fail: the TT wires end on the macro's own pins). **Open (Matt):** 7 VDPWR is down to 89 % (≈ 27 of 30 pF), because the decap strip west of the chain lost 7.4 µm to the wider chain.

## Notes from the size trials (2026-10-09, previous session)

**What's in the tree now (uncommitted when written):** `openlane/radio_digital/config.json` has `DIE_AREA` [0, 0, 200, 220] and `TOP_MARGIN_MULT` / `BOTTOM_MARGIN_MULT` = 2 (default 4). `pin_order.cfg` is the **trial's N/S order** (TT pins north, analog south), *not* this handoff's east-edge order: replace it.

**Size trials** (y 220 sweep, same config otherwise; the runs are Mac-local, `openlane/radio_digital/runs/trial_*`):

| die (µm) | util | result |
|---|---|---|
| 450.5 × 109.66, default margins | 85 % | fails at antenna repair (DPL-0036: no room for diodes next to hold buffers). The default 4-row top/bottom margins cost ~22 µm of a 110 µm die. |
| 450.5 × 109.66, 2-row margins | 76 % | fails detailed routing: GRT overflow 1,879 (horizontal met1 / met3), DRT stuck at ~10k violations (shorts). Too flat for the horizontal wiring; no met5 (TT PDN). |
| 220 × 220 | 74 % | **clean**: setup ws 26.7 ns, hold ws 0.108 ns, 643 hold buffers |
| 210 × 220 | 78 % | **clean**: setup 26.5, hold 0.108 |
| **200 × 220** (`trial_200x220`) | 82 % | **clean**: 0 DRT / Magic DRC / LVS / antenna; setup 26.4, hold 0.106; 648 hold buffers; ~6 min |
| 190 × 220 | 86 % | fails: GRT overflow 550, DRT stuck at 7 violations (met1 spacing / shorts) after 19 iterations |

These went into `docs/history.md` "Size trials" when you update it. The trial pins were on N/S; moving them all to the east edge changes routing a little, so 200 × 220 should still route but isn't proven with this pin order.

**How `pin_order.cfg` slots work** (LibreLane `scripts/odbpy/io_place.py`, read in the image):
- Slots are track positions: N/S on met2 tracks (origin 0.23, step 0.46), **E/W on met3 tracks (origin 0.34, step 0.68)**, taking every `ceil(min_distance / step)`-th track. For a 220-tall die: 323 met3 tracks, so `@min_distance=1` gives 162 slots at y = 0.34 + 1.36·i; `@min_distance=0.5` gives 323 slots at 0.34 + 0.68·i. **A 1 µm pitch isn't on the grid:** use 1.36 (42 TT pins = 56 µm, e.g. clk at ~163 up to ~219, still above sc_phi at ~148) or 0.68.
- Pins and `$n` fill consecutive slots. If the total (pins + `$n`) is **less than** the slot count, the whole group is spread (`floor(slots/total)` tracks per pin) and centred, so positions drift. If it **equals** the slot count, io_place hits an `AssertionError` (a bug in the all-tracks case). **So pad with a trailing `$n` to exactly slot count − 1**: then slot i is at origin + i·pitch, starting at the die edge.
- Track count: the last track keeps half a pitch from the die edge: count = floor((L − 2·origin) / step) + 1 (L in µm).
- E/W are bottom → top. Pins go on met3 for E/W (not met4: the tile's VAPWR / VGND / VDPWR straps at x 276.5–279.9 sit between the macro and the analog).

**Quick pin check without a full harden** (~30 s): `librelane ... --to Odb.CustomIOPlacement config.json`, then read the PINS section of `runs/<tag>/final/def/radio_digital.def` (PLACED x y in DBU, 1000 / µm). The trial session iterated `$n` counts this way and landed every pin within 1.5 µm.

**Running on the Mac:** `tools/longrun` needs systemd (Linux only). Use `caffeinate -i tools/osic-mac bash -c 'cd openlane/radio_digital && librelane --pdk sky130A --run-tag <tag> --overwrite config.json' > build/<tag>.log 2>&1` as a background job. Killing the client leaves the container running: `docker ps`, then `docker stop <id>`. For quick trials, `"DRT_OPT_ITERS": 20` caps a non-converging route (good runs reach 0 in ~6 iterations); leave it out of the final config.
