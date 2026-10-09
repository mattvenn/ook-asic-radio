# pin_order.cfg

LibreLane io_place syntax: `#N`/`#S`/`#E`/`#W` sides (N/S left → right, E/W bottom → top; `#NR` etc. reversed), one anchored regex per line, `$n` = n empty slots, `@min_distance=x`. **No comment lines**: anything starting with `#` is read as a side directive.

## radio_digital pin order (floorplan "matt layout 5", 2026-10-09)
The macro is 200 × 220 µm, placed **MY** at the east end of the 3x2 tile at full height, so its own **east** edge faces **west**, toward the analog blocks. **All 57 signal pins are on that edge (met3); N / S / W have none.** Its west face is next to the tile's mid straps (met4, x 276.5–281.1), so the wires reach it on met3 or below.

Bottom → top (macro frame y; tile y = y + 2.88), each level with what it connects to:
- `rx_en` 7.1: bias_gen `en`, straight along the bottom of the tile.
- `comp_in` 86.0: comp_ct `out`, along the gap under r2r.
- `trim_out[7..0]` 94–154: level with r2r `b7..b0` (r2r is placed MYR90, b0 at the top), so the eight wires are straight 44 µm runs.
- `sc_phi2`, `sc_phi1` 155.4 / 156.7: the avg_sc clocks, which come over the top of comp_ct and down the gap west of the decap strip.
- `dbg_en`, `tx_en_n`, `tx_en` 158.1–160.8: static enables, routed west in the TT channel along the top of the tile to the TX cluster and dbg_tg.
- The 42 TT pins 162.2–217.9: `clk`, `uio_oe[7..0]`, `uio_out[7..0]`, `uo_out[7..0]`, `uio_in[7..0]`, `ui_in[7..0]`, `rst_n`. The TT wires come from the tile's top-left (x 15–131), run east along the top, and step down to these pins; the enables use the lowest lanes of the same channel, so nothing crosses.

## Slot mechanics (LibreLane `scripts/odbpy/io_place.py`)
- E/W slots are met3 tracks (origin 0.34, step 0.68); `@min_distance=1` takes every 2nd: **162 slots at y = 0.34 + 1.36 i** on a 220 µm edge. A 1 µm pitch isn't on the grid.
- Pins and `$n` fill consecutive slots. If the total is less than the slot count, the group is spread and centred (positions drift); if it equals it, io_place asserts. **Pad to exactly slot count − 1 (161)**: then slot i is at 0.34 + 1.36 i.
- `pin_order.cfg` is generated from `layout/floorplan/variant_layout5.json` (the macro's pins there are slot positions). Quick check without a full harden: `librelane ... --to Odb.CustomIOPlacement config.json`, then the PINS section of `runs/<tag>/final/def/radio_digital.def` (DBU 1000 / µm).
