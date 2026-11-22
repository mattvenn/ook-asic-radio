# Handoff: top-level layout, first routing, extracted-tile verification

Prompt for a new session (written 2026-10-09 at the end of the pin / re-harden session). Paste it as is.

---

Every block is now laid out to the chosen floorplan, and the digital macro is re-hardened to match. Your job: **assemble the 3x2 analog tile, do a first routing attempt that follows the layout rules and the design intent, then verify the extracted tile**: top-level DRC / LVS, then the end-to-end tests on an extracted netlist, **first connectivity only (LVS-style extraction), then full parasitics.** Commit and push to `main` as you go (small commits; other sessions push to `main` too).

This is a first attempt: when the routing intent below can't be met, or a block needs to change, **stop and write down what and why** rather than forcing it. Matt decides block moves. Ask him when a decision is his.

## Read first
- `docs/agent_start.md` (rules for agents on this repo), `STATUS.md` (state, how to run things).
- `docs/layout.md`: "Checklist", "Power: how the TT PDN connects", "Block convention", "Current limits: EM and IR". These are the layout rules.
- `docs/floorplan_spec.md`, the last section ("Chosen floorplan"), then **`layout/floorplan/pins.md`** and **`layout/floorplan/floorplan.json`** (variant **"matt layout 5 (routing review)"**: placements, orientations, straps, decap rectangles, every pin by edge). `floorplan.json` has the KLayout placement transform in its `transform` field.
- `docs/future_flow.md` "The final router is the hard part" and its draft constraints file: the net classes there are a good starting point for routing rules.
- The schematic is the source of truth for connectivity: `xschem/gen/top.py` (writes `radio_analog.sch` and `tt_um_mattvenn_radio.sch`).

## Tools
- Linux host: `tools/osic <cmd>`. Matt's Mac: `tools/osic-mac <cmd>` (from the repo root; sim scripts take `OSIC=$PWD/tools/osic-mac`).
- cocotb on the Mac: `make COCOTB_CONFIG=cocotb-config ...` (the Makefile's default path is the Linux venv).
- Long jobs (LibreLane, full-tile extraction, long ngspice runs) in the background; don't run ngspice jobs in parallel.
- Floorplan picture with every net as a flyline: `node tools/floorplan_dump.js > build/fp.json && python3 tools/floorplan_draw.py build/fp.json build/fp.png`. The floorplan page itself: `layout/floorplan/page/page.html`.

## What exists

### Blocks (all DRC / LVS / antenna clean, extracted and block-tested)
Each block has `layout/<cell>.gds`, a generator `layout/gen/<cell>.py` (r2r: magic source in `layout/src/r2r/`, written by `layout/gen/r2r.sh`), an LVS reference `layout/ref/<cell>.spice` (or `xschem/<cell>.sch`), and an extracted `layout/pex/<cell>.spice`. Placements (lower-left of the placed bbox, tile µm) from `floorplan.json`:

| inst | cell | place (x, y) | orient | size (own frame) | notes |
|---|---|---|---|---|---|
| macro | radio_digital | 282.5, 2.88 | MY | 200 × 220 | `macros/radio_digital/` (see below) |
| xchain | lna_chain | 13.14, 6.5 | R180 | 145.36 × 70.47 | U fold; input section over ua[0]/ua[1] |
| xdet | log_det | 67.5, 80 | MX | 87.33 × 31.01 | |
| xlpf | lpf_rc | 67, 113.6 | R0 | 65.2 × 35.02 | |
| xavg | avg_sc | 53, 151.2 | R0 | 77.35 × 30.4 | |
| xcomp | comp_ct | 137.5, 116.6 | **MYR90** | 73.55 × 41.16 | flipped 2026-10-09 |
| xdac | r2r | 185, 91 | **MYR90** | 71.75 × 54.12 | flipped 2026-10-09; met1 only |
| xctrim | ctrim_1p | 159, 90.3 | MX | 22.435 × 22.435 | new 2026-10-09 |
| xbias | bias_gen | 160.5, 7.5 | R90 | 80.22 × 49.07 | |
| xdbg | dbg_tg | 57.5, 124 | R0 | 5.7 × 16.3 | |
| xtx.xring | tx_ring | 17.5, 140.5 | MXR90 | | TX: placed flat, as `tx_top`'s instances |
| xtx.xls | tx_ls | 36, 124 | MYR90 | | |
| xtx.xlse_p / _n | tx_ls_en | 27.5, 141 / 13, 124 | MYR90 / R270 | | |
| xtx.xdrv_p / _n | tx_drv | 37.5, 80.5 / 5.5, 80.5 | R270 / MYR90 | | |

The sizes changed a little from the floorplan estimates (comp_ct 73.55 × 41.16, was 73.45 × 41.97; Ctrim 22.4, was 23.5). `floorplan.json` / `pins.md` already use the real ones.

### Digital macro
`macros/radio_digital/`: `radio_digital.gds`, `.lef`, `.def`, `.nl.v`, `.pnl.v`, copied from the LibreLane run `openlane/radio_digital/runs/l5b_200x220` (config `openlane/radio_digital/config.json`, pins `pin_order.cfg`, rationale `PIN_ORDER.md`). 200 × 220 µm, signoff clean, RTL and GL cocotb 15/15. All 57 signal pins are on its own **east** edge (placed MY, so they face **west** into the tile), on met3, at y = 0.34 + 1.36 i (macro frame; tile y = that + 2.88). Bottom → top: rx_en; comp_in; trim_out[7..0] (level with r2r b7..b0); sc_phi2, sc_phi1; dbg_en, tx_en_n, tx_en; then the 42 TT pins (clk, uio_oe[7..0], uio_out, uo_out, uio_in, ui_in, rst_n) from y 162 to 218.

### Not laid out yet (your job)
- **Decaps.** `xdeca` (VAPWR, target ~50 pF; parts 1–5) and `xdecd` (VDPWR, ~30 pF; parts 1–4) are rectangles in `floorplan.json`. The schematics are `xschem/decap_vapwr.sch` / `decap_vdpwr.sch` (MIM + MOS). **xdeca part 5 is MIM-only on top of r2r** (r2r is met1-only for this). Open (Matt): VDPWR decap is at 89 % of target, VAPWR 97 %.
- **Power straps** (met4, full height, `floorplan.json` "straps"): VDPWR x 9.3 / VGND 13.9 (west), VAPWR 276.5 / VGND 278.2 / VDPWR 279.9 (between the analog and the macro), VAPWR 488.02 / VGND 489.72 / VDPWR 491.42 (east). ≥ 1.2 µm wide, each within 10 µm of the tile's top and bottom (TT precheck), no met5. Block rails are met1–met3: join them to the straps with via3 where they cross or with met3 spurs. The macro's power pins: see its LEF (met4).
- **All inter-block wiring** (below) and the tile pins.

## Nets and routing intent
Coordinates are tile µm, pin centres from `pins.md` / the engine. Layer notes: the three straps at x 276.5–281.1 are met4, so everything reaching the macro crosses them on met3 or below. Avoid met4 over MIM caps (their top plates are met4). No met5 anywhere.

| net(s) | from → to | intent |
|---|---|---|
| rx_p / rx_n | ua[0] (136.6) / ua[1] (117.3) pads → chain inp / inn (just above, y 6.8) | shortest possible, as a pair; nothing else near. |
| chain taps o1..o5 p/n, out_p/n | chain's tile-north edge → log_det t1..t6 p/n | differential pairs routed together. **o4, o5, out (late, big swing) stay away from the chain's input section and stage 1** (rule 2; chain coupling rule: output → input ≤ 0.1 fF asymmetric, 0.5 fF oscillates). log_det is MX: t4..t6 are on its top side, so those pairs go round it. |
| det | log_det det (67.7, 110.8) → lpf_rc in (68.5, 113.8) and → dbg_tg a (57.8, 124.2) | slow, high-impedance (8 kΩ / 1 pF node): short, shielded with VSS, no clocks near. |
| dbg (ua[2]) | dbg_tg b → ua[2] pad (98, 0) | **don't cross the chain**: west along the gap at the bottom and up outside it, so it can't bridge stage 5 to Cin_n (handoff of the chain). |
| lpf | lpf_rc out (131.9, 144.6) → avg_sc in (130.1, 151.4) and → comp_ct **inn** (137.8, 147.7) | 2.95 MΩ node: shielded, short, away from sc_phi. |
| avg | avg_sc out (130.1, 173.5) → comp_ct **inp** (137.8, 152.3) | down the 7 µm channel between avg_sc and comp_ct. |
| sc_phi1 / sc_phi2 | avg_sc N edge (~118.5, 181.6) → macro (282.8, 159.6 / 158.3) | clocks (aggressors). Leave avg_sc over the top, east in a corridor above comp_ct (comp top y 190.1, xdeca part 2 starts y 193: cut the decap back if you need room), down the x 239–242 gap east of xdeca part 4, across xdeca part 1 / the straps on a low layer to the macro. Keep ≥ ~20 µm from comp inp / inn, lpf, avg; shield if they run long next to anything analog. |
| comp_in | comp_ct out (178.4, 118.5) → macro (282.8, 88.9) | toggling (comparator output). Down between Ctrim (x 182.5) and r2r (x 185), then east along the y 88–91 gap under r2r. **Keep it off the trim node.** |
| trim_out[0..7] → r2r b0..b7 | macro (282.8, y 97–157) → r2r's tile-east face (238.6, same y) | eight straight 44 µm horizontals, crossing xdeca part 1 and the straps on met2/met3. Static in RX. |
| trim (DAC out) | r2r out (238.6, 100.6) → Ctrim's E-edge trim pin (181.4, 101.5); Ctrim's S-edge trim pin (160, 112.5) → comp_ct trim (159.2, 116.9) | **one net** (Ctrim is a 1 pF shunt cap trim → VGND). A straight met2 run west over r2r (under the MIM decap's met3 plate, which shields it; r2r is met1-only). Ctrim has two trim pins on purpose (the engine draws only one of them). |
| ib_comp | bias_gen (161.5, 87.5) → comp_ct ibias (156.2, 116.9) | up the 4 µm corridor between log_det (x 154.8) and Ctrim (x 159). |
| ib_chain, vcm, ib_det | bias_gen north / east edge → chain (W edge) / log_det | short (2–11 µm). Bias: keep them off clocks. |
| rx_en | macro (282.8, 10) → bias_gen en (209.3, 9.5) | straight along the bottom. |
| dbg_en, tx_en, tx_en_n | macro (282.8, 161–164) → dbg_tg en (63, 130), TX (tx_ring en, tx_ls_en in ×2) | static in RX. Up into the TT channel at the top of the tile, west **below** the TT lanes, down to the TX cluster at the west end. Not across the RX path. |
| TT bus (42) + clk | TT pins on the tile's top edge (x 15–131) → macro pins (y 162–218) | the top channel (y ~213–225, above xdeca part 2), east, then a staircase down to the macro pins (TT channel check on the page is a known false fail). |
| tx_p / tx_n | tx_drv outs → ua[3] (78.7) / ua[4] (59.3) | **≥ 5 µm wide, met3 or higher** (~110–120 µm runs, EM table in `docs/layout.md`). The TX is off whenever the RX is on, so they may cross the chain. |
| TX internal | ring → ls → drv, ls_en → drv en (`xschem/tx_top.sch`) | short, inside the TX cluster. |
| supplies | VDPWR: RX blocks, bias, digital interface buffers; VAPWR: TX drivers / level shifters (`tx_top`); VGND everywhere | each block's rails (met1–met3) to the nearest strap; RX and TX grounds join only at the straps (checklist "noisy and quiet are separate"). |

Pin layers that aren't met2/met3: met4 for comp_ct out / trim / ibias, bias_gen vcm, Ctrim trim (and the TX outputs on met3, 2.5 µm). All in `blocks.json`.

## Verification, in this order
1. **Top-level DRC** (magic + KLayout `sky130A_mr`), antenna, density, the TT precheck rules for analog (power pins, no met5). `mag/` is the TT analog template flow: **switch `mag/Makefile` to `tt_analog_3x2_3v3.def`** (it still says 2x2), `make start`, then place and route in that cell.
2. **Top-level LVS** against `tt_um_mattvenn_radio` (`xschem/tt_um_mattvenn_radio.sch` netlist + the macro's `radio_digital.pnl.v` + the sky130_fd_sc_hd spice). `mag/tcl/lvs_netgen.tcl` is still the template from an old project (`r2r_dac_control`): rewrite its `readnet` lines for this design. Note `tx_top` is placed flat (its instances are top-level cells): flatten it in the source or add a `tx_top` cell in the layout.
3. **Extracted tests, connectivity first:** extract the tile without parasitics (LVS-style netlist) and run the end-to-end tests on it instead of the schematic: `tb_radio_analog` (`xschem/tb_radio_analog.sch`: bias, operating points, det with/without −60 dBm, TX power), the joined RX run (`sim/rx/joined.sh`), `sim/tx/tb_tx.py`, the mixed-signal run (`sim/mixed/`: RTL servo + real r2r + comp). `tools/pexswap.py` shows how blocks are swapped into a deck. This catches wiring mistakes cheaply.
4. **Then full parasitics** (`docs/layout.md` "Extraction for the final end-to-end run": RC on everything will be slow; C-only for most of the tile with RC on the RF path is the suggested split; KLayout-PEX can cross-check magic). Re-run the same tests. Reference numbers from the schematic runs: RX sensitivity ≈ −92…−93 dBm worst case (10–50 °C), TX +3.7…+3.9 dBm, trim step 0.062–0.076 mV/LSB, comp offset +0.56 mV, det idle ~1.49 V (STATUS.md, `docs/history.md`).
5. Report each step's numbers in STATUS.md / `docs/history.md`, and update `docs/layout.md` with the top-level routing lessons.

## Known issues to keep in mind
- The floorplan engine's net list had two errors, fixed 2026-10-09 (`layout/floorplan/page/engine.js`): comp_ct **inp = avg, inn = lpf** (it had them swapped), and Ctrim is a **shunt** cap on trim (it was modelled in series). Trust `xschem/gen/top.py` over the engine.
- The page's checks still show rule 2 (chain late stages 14 µm from the input: the guard-ring moat, extracted coupling 0), rule 5 (TX wire length: accepted, route it wide), rule 8 (soft) and the TT channel false fail. Accepted by Matt.
- Open (Matt): VDPWR decap 89 %, tx_ring inverter count (runs ~459 MHz on silicon), max-slew warnings in the macro harden (marginal, mostly ss; ~220 across corners).

## Don't
- Don't move, resize or re-orient blocks, or change circuits, to make a route fit: write it down for Matt.
- Don't hand-edit `floorplan.json` / `pins.md`: they come from `layout/floorplan/mk_layout5.js` → `variant_layout5.json` → `page/pinreport.js`.
- Don't put met5 anywhere, or met4 that isn't a power strap where a block or MIM already uses met4.
