# Handoff: move block pins and re-harden the digital macro for the chosen floorplan

Prompt for a new session (2026-10-09). Paste it as is.

---

We've chosen the top-level floorplan of the 3x2 analog tile. Your job is to make the blocks match it: move pins in the analog block layouts, and re-harden the digital macro at its new size and pin order. Don't change block placements; ask if something can't be done as specified.

**Read first:** `STATUS.md` (how to run things), `docs/layout.md` (the layout flow and power rules), `docs/floorplan_spec.md` (the last section, "Chosen floorplan"). The source of truth for positions is **`layout/floorplan/pins.md`** and **`layout/floorplan/floorplan.json`** (variant "Matt layout 3 (Claude)" on the floorplan page).

**Conventions in `pins.md`:** µm. Each block's pins are given in the block's *own* frame (its bbox lower-left = 0, 0, before its placement orientation), grouped by its own edge, with the tile direction that edge faces once placed. Pins marked "moved" are the new positions; the rest stay where the GDS has them. Positions along an edge are targets (±a few µm is fine); **the edge and the order along it matter more than the exact x / y**. Keep each moved pin on the same layer as now unless the block's flow needs otherwise.

**Pin map (changed 2026-10-09):** ua[0] / ua[1] = RX (rx_p / rx_n), ua[2] = debug (det), ua[3] / ua[4] = TX (tx_p / tx_n).

## 1. Digital macro `radio_digital` (`openlane/radio_digital/`)
- **New size:** `DIE_AREA` [0, 0, 450.5, 109.66] (same area as 260 × 190, ~4.1 : 1). It's placed **MY** in the tile at (19.5, 103.5), so its own west edge faces east in the tile; all positions below are in the macro's own frame.
- **Risk, check first:** an earlier trial at 340 × 170 failed detailed routing (~3,100 violations, mostly horizontal overflow; `docs/history.md`, "Size trials"). Run a trial harden at 450.5 × 109.66 before anything else. If it doesn't route clean, stop and report (with what you tried: density, layers, a taller/narrower option such as ~380 × 130): the floorplan depends on this shape.
- **New `pin_order.cfg`** (LibreLane: N/S left → right, `$n` = empty slots, no comment lines; see `PIN_ORDER.md`). Use `$n` spacers to land pins near these x positions:
  - **North (42 TT pins, ~2.76 µm pitch, east end):** `clk` 339.9, `rst_n` 342.6, `ui_in[0..7]` 345.4 … 364.7, `uio_in[0..7]` 367.5 … 386.8, `uo_out[0..7]` 389.5 … 408.9, `uio_out[0..7]` 411.6 … 430.9, `uio_oe[0..7]` 433.7 … 449.5 (exact values in `pins.md`). The order is reversed from the old cfg because the macro is mirrored.
  - **South (analog interface):** `trim_out[7]` 1.0, `[6]` 2.0, `[5]` 3.0, `[4]` 5.75, `[3]` 13.25, `[2]` 20.75, `[1]` 28.25, `[0]` 43.25, then `sc_phi2` / `sc_phi1` and `comp_in` just after trim_out[0] (~45–53; `pins.md` has phi at 39.7 / 41.4 between trim_out[1] and [0]: move them after [0] so the trim bus stays contiguous), then `rx_en` 381.5, `dbg_en` 389.0, `tx_en` 415.3, `tx_en_n` 436.1. The trim bits can spread more than 1 µm apart if the tool needs it; keep their order.
  - **West / East:** no signal pins.
- **After the harden:** signoff clean (DRC, LVS, antenna, timing at all corners, as for `cg_260x190`); RTL and gate-level cocotb suites (STATUS.md "How to run things"; point the GL netlist at the new run). Update `config.json`, `PIN_ORDER.md` (the rationale is now "analog below the macro"), STATUS.md and `docs/history.md`. Report the real pin positions from the DEF so we can check them against `pins.md`.

## 2. Analog blocks: pin moves (re-layout with the existing flow)
For each block: edit `layout/gen/<block>.py` (or the block's layout source), regenerate, then `layout/check.sh` (DRC + LVS clean), `layout/pex.sh`, and its block test (`tb_<block>`, schematic vs extracted, no regression) per the policy in STATUS.md. Change only pin positions and the routing to them; no circuit changes. Positions are (x, y) in the block's own frame.

- **`lna_chain`** (placed MX): `ibias` and `vcm` move to the **south edge at the input end**: ibias (1.0, 0.25), vcm (2.0, 0.25) (they face north, up to bias_gen). The stage taps, inp / inn and outp / outn stay.
- **`bias_gen`** (R0): `ib_chain` (5.0, 0.25) and `vcm` (6.0, 0.25) on the **south edge, west end** (down to the chain's input end); `ib_det` (79.97, 13.3) and `ib_comp` (79.97, 43.4) on the **east edge**; `en` (2.05, 48.8) on the **north edge** (up to the macro's rx_en).
- **`log_det`** (MX): `det` (0.25, 30.0) and `ibias_det` (0.25, 17.7) on the **west edge** (toward lpf_rc and bias_gen). t1–t6 stay.
- **`lpf_rc`** (R0): `in` (64.95, 1.0) and `out` (64.95, 2.0) both on the **east edge** (log_det and avg / comp are east). Don't put in and out 1 µm apart: separate them by a few µm with a VSS shield between, so the filter isn't bypassed.
- **`avg_sc`** (R0): `out` (1.0, 30.15), `phi1` (67.5, 30.15) and `phi2` (69.1, 30.15) on the **north edge**; `in` (0.25, 29.4) on the **west edge** at the top. Keep the phi lines off the Cavg top plates (`docs/layout.md`).
- **`comp_ct`** (R0): `inp` (0.25, 1.0) and `ibias` (0.25, 30.1) on the **west edge**; `inn` (16.9, 0.25) and `trim` (72.45, 0.25) on the **south edge** (avg_sc and Ctrim are below); `out` (72.45, 41.7) on the **north edge** (up to the macro's comp_in).
- **`r2r`** (MX): `b0..b7` on its **south edge** (faces north, up to the macro) at x 5.6, 20.6, 28.1, 35.6, 43.1, 47.9, 48.9, 49.9 (b5–b7 are packed; spread them toward b4 if needed, keep the order); `out` (20.9, 53.9) on the **north edge** (faces south, down to Ctrim). r2r must stay met1-only: a 65.3 × 52.1 µm MIM-only VAPWR decap sits on top of it (`floorplan.json`, xdeca part 8).
- **`dbg_tg`** (R0): `a` (det side) (5.45, 15.3) and `b` (pad side) (5.45, 1.0) on the **east edge**; `en` (1.0, 16.05) on the **north edge**.
- **Ctrim** (1 pF MIM, not laid out yet): 23.5 × 23.5 µm at (441, 4.5) MX; `p` (from r2r out) and `n` (to comp_ct trim) on its south edge (faces north).
- **No change:** the TX blocks (`tx_ring`, `tx_ls`, `tx_ls_en` × 2, `tx_drv` × 2) keep their GDS pins.

## 3. Don't
- Don't move or resize blocks, or change circuits or schematics, to make a pin fit: report it instead.
- Don't regenerate the floorplan files by hand. If a pin has to land somewhere else, write down where; we'll update the floorplan page (`layout/floorplan/page/`) and re-run `pinreport.js`.
