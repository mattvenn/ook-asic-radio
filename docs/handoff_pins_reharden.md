# Handoff: move block pins and re-harden the digital macro for the chosen floorplan

Prompt for a new session (2026-10-09, second version: "matt layout 4 (handoff)"). Paste it as is.

---

We've chosen the top-level floorplan of the 3x2 analog tile. Your job is to make the blocks match it: re-harden the digital macro at its new size and pin order, and move pins in the analog block layouts. Don't change block placements; ask if something can't be done as specified.

**Read first:** `STATUS.md` (how to run things), `docs/layout.md` (the layout flow and power rules), `docs/floorplan_spec.md` (the last section, "Chosen floorplan"). The source of truth for positions is **`layout/floorplan/pins.md`** and **`layout/floorplan/floorplan.json`** (variant "matt layout 4 (handoff)" on the floorplan page).

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

## 3. Not in this job: `lna_chain`
The chain is folded in this floorplan (134 × 70.5 µm outline at (21, 6.5), MX), but the fold isn't final: the current one puts stages 4–6 right next to the input (floorplan rule 2), and Matt is working on a better fold. **Don't re-lay out `lna_chain`.** Its `ibias` / `vcm` (east edge, toward bias_gen in `pins.md`) will be set with the new fold. If the new fold changes the chain's outline, the blocks above and east of it may shift a few µm; the pin edges above should still hold.

## 4. Don't
- Don't move or resize blocks, or change circuits or schematics, to make a pin fit: report it instead.
- Don't regenerate the floorplan files by hand. If a pin has to land somewhere else, write down where; we'll update the floorplan page (`layout/floorplan/page/`) and re-run `pinreport.js`.

## Floorplan checks on this layout
Pass: 1 (chain input ↔ macro 141 µm), 3 (clock edges 25 µm), 4 (analog path 48 µm), 6 (bias 6 µm), 7 VDPWR, 9 (no overlaps), straps (8, all lanes clear). Known and accepted: 2 (the fold, above), 5 (TX wire length, see TX note), 7 VAPWR at 97 %, 8 (soft), and the page's "TT pin channel clear" (a false fail: the TT wires end on the macro's own pins).
