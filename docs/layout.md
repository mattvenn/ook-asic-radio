# Layout flow (KLayout pcells → DRC/LVS → PEX → re-simulation)

Developed on `tx_drv` first; the same steps apply to every analog block.

## Steps
1. **One-time setup:** `tools/osic bash tools/kpcell_setup.sh`.
   - The sky130 KLayout pcells in the PDK (Mabrains, `libs.tech/klayout/python/cells`) need gdsfactory 8.x, but the tools image has 9.x.
   - This installs gdsfactory 8.5 into `build/pyold`, which `layout/gen/lay.py` puts first on `sys.path`. The pip copy of `klayout` is removed so KLayout's own module wins.
2. **Generate:** `tools/osic klayout -b -r layout/gen/<block>.py` writes `layout/<block>.gds`.
   - `layout/gen/lay.py`:
     - `Fet` wraps a pcell (W total, split over nf) and reads its terminals from the geometry: met1 S/D strips, gate pads, guard ring outer/hole, diffusion;
     - `Block.via` fills DRC-safe cut arrays (per-axis enclosure for narrow strips);
     - `Block.stack` builds metal stacks; `Block.pin` adds pins.
3. **Check:** `tools/osic bash layout/check.sh <block>` (~10 s) runs:
   - magic DRC (full), the KLayout `sky130A_mr.drc` deck (feol + beol);
   - magic antenna check (flattened, own session) and a per-layer metal density report;
   - netgen LVS of the magic extraction against the xschem netlist (`top_subckt`, `lvs_netlist`).
   - Results in `build/lvs/<block>/`.
4. **Extract:** `tools/osic bash layout/pex.sh <block>` (magic, flattened; extresist + C to 0 fF).
   - `layout/pexfix.py` reorders the ports to the schematic's `.subckt` order (instances connect by position) and ties any substrate port to VSS.
   - Output: `layout/pex/<block>.spice`.
5. **Re-simulate:** `tools/pexswap.py` `swap(deck, [blocks])` removes the schematic subckt from a netlist and includes the extracted one.
   - `sim/tx/tb_tx.py --pex <corners>` does this for `tx_drv`; outputs are tagged `_pex`.

## Checklist (every block, and the top level)
From the IIC-JKU guides and our own lessons:
- the circuit designer's etiquette: <https://github.com/iic-jku/analog-circuit-design/blob/main/content/appendix/_app_circuit_designers_etiquette.qmd>
- the layout chapter: <https://github.com/iic-jku/design-complex-ic/blob/main/content/layout/_sec_layout.qmd>

**Before drawing**
- [ ] **Floorplan first, top-down** (their "common mistake": lots of cells, then a mess at assembly). Each block gets a target outline, pin sides and rail heights from the floorplan.
- [ ] **Unit devices in the schematic for anything matched:** same W and L, a ratio from multiples of a unit. Fix it in the schematic, not in layout.
- [ ] **Digital controls into analog blocks are buffered locally**, by an inverter on the block's own supply (`sc_phi1/2`, `rx_en`, `dbg_en`, `trim[7:0]`).
- [ ] **A defined off state:** no floating nodes when powered down. The block testbench covers off and start-up, not just on.

**Supplies, grounds, noise**
- [ ] **Noisy and quiet are separate.** TX (VAPWR + its VSS) and RX get their own supply/ground routing, joined only at the met4 straps / met5 PDN.
  - Guard rings and substrate ties of the RX go to the RX's own quiet ground, never to a TX return.
  - TX far from the RX input.
- [ ] **VDD and VSS run as a pair** (small loop): each met4 strap of one net next to a strap of the other, on both the left and the right of the tile.
- [ ] **Decouple to the right potential,** and check the bond-wire L + on-chip C resonance (`sim/chain/stability.sh`).
- [ ] **Hot spots:** the TX drivers dissipate ~50 mW. Keep matched devices far away or on a symmetry line through the hot spot.

**Devices**
- [ ] **PMOS grouped, NMOS grouped** (rows): the diffusion-to-nwell spacing is large.
- [ ] **Series devices of equal W share a diffusion** (multi-finger pcell, e.g. the NAND's series NMOS).
- [ ] **RF gates:** each gate finger's resistance < 1/gm. Watch finger width, and contact both ends for the LNA chain if needed.
- [ ] **Matching:**
  - identical units, the same orientation and the **same current direction** (no snaking);
  - dummies at the edges, **tied to a defined potential, never floating**;
  - common centroid for pairs, symmetric wiring parasitics;
  - no low-level metal over sensitive devices;
  - matched PMOS away from nwell edges (well-proximity effect).
- [ ] **Matched R and C arrays:** unit elements at a constant pitch, dummies tied off, common centroid for ratios.

**Wiring**
- [ ] **Measure the currents** in the block testbench, then size widths and **cut counts** (≥ 2× the tech-LEF limits; table below). The generator prints the cut check.
- [ ] **Label internal nets** (`Block.label`), so LVS and PEX name them (`y4`, not `a_4018_655#`).
- [ ] **No met5** (TT PDN). Power pins: met4, ≥ 1.2 µm, full height.
- [ ] **Good neighbour on density:** TT adds fill after submission, but the PDK rule is ≥ 40 % clear area per layer (li, met1–met3), so stay **well under 60 % metal** in any region.
  - No needless solid plates; rails only as wide as the current needs.
  - Mind the decaps: MIM fills met3/met4 over its whole area. `check.sh` reports density per layer and flags > 50 %.

**Checks (`layout/check.sh`)**
- [ ] Magic DRC 0, KLayout `sky130A_mr` DRC 0.
- [ ] **Antenna 0** (Magic `antennacheck`, flattened, in its own session; verified to catch a deliberate violation).
- [ ] LVS match, with pins equivalent.
- [ ] Density per layer under 50 %.
- [ ] PEX + block testbench: the extracted result is close enough to the schematic.

**Extraction for the final end-to-end run**
- Full RC per block is fine (~2 min). A full-chip RC run will be slow. Consider coupling-C-only for most of the chip, with RC only on the RF path.
- KLayout-PEX (`kpex`, sky130A supported) can cross-check magic's extraction.

## Verification policy: block tests, one end-to-end at the end
- **Per block, a small dedicated testbench** (`tb_<block>`): ideal stimulus, the block's real load, and measurement of just what the block must do.
  - Run it on the schematic and on the extracted layout (`pexswap`) and check the layout is close enough. That's seconds to minutes, not the whole chain.
- **Don't re-run the end-to-end testbenches (`tb_tx`, the joined RX, `tb_radio_analog`) per block.**
- **One end-to-end run on the fully extracted design right at the end**, after top-level integration.

## Pcell facts (sky130 g5v0d10v5, Mabrains)
- **Finger width:** the pcell's `w` is per finger. S/D strips sit at a 0.8 µm pitch (L 0.5); each is li + mcon + a 0.23 µm met1 strip.
- **Strips need widening for via1:** at 0.23 µm they're too narrow. Widen to 0.29 µm (via1 0.15 µm + 0.07 µm each side; 0.085 µm along the strip).
- **Gate pads:** met1, on one side (`gate_con_pos` top/bottom). From nf ≥ 2 they're staggered on two heights; finger 0 is nearest the diffusion.
- **Guard ring (`bulk='guard ring'`):** tap + li only, no metal. Add mcon + met1 yourself.
- **Wells and markers:** each pcell carries its own nwell/hvi. Draw one nwell over the PMOS row and one hvi over everything so neighbours merge (`nwell.9` needs the hv marker to cover the HV nwell).

## Power: how the TT PDN connects (checked 2026-10-08)
Sources: <https://tinytapeout.com/specs/analog/#power-pins>, tt-multiplexer `ol2/tt_top/pdn.tcl` + `build.py`, tt-support-tools `precheck/pin_check.py`.
- **Top-level grid:** horizontal **met5** stripes, 8.75 µm wide with 2.25 µm spacing, set pitch 57.12 µm (= branch pitch / 5).
  - Nets: vdpwr, vgnd, vapwr. Each set probably holds one stripe of each net; the order hasn't been confirmed.
  - The macro grid is `add_pdn_connect -layers met4 met5` on the `tt_um_*` macros. **Any met4 power-pin shape that crosses a same-net met5 stripe gets via4s automatically.**
- **Our power pins** (precheck + spec):
  - **met4**, ≥ 1.2 µm wide, vertical;
  - each rectangle starts within 10 µm of the bottom edge and reaches within 10 µm of the top (so it crosses every stripe);
  - **several pins per net are allowed**, with different sizes;
  - pins must not overlap or abut each other.
- **No met5 in our design** (reserved for the PDN). The 3.3 V supply needs the `_3v3` template and `uses_vapwr: true` (done).
- **The templates start with the straps on the left.** That's a convention, not a rule: **put VAPWR/VGND (and VDPWR) straps on both the left and the right of the tile**, and more if useful, for a lower-impedance connection to the PDN.
- **IR drop:** about 20 mA gives ~0.1 V drop through the PDN (spec). The TX takes ~11 mA average (two arms) from VAPWR in ~50% bursts, so strap count and width matter here.

### Block convention (so the top level is easy)
- **Rails:** every block has full-width horizontal rails: VAPWR (or VDPWR) along the top and VSS along the bottom, stacked **met1 + met2 + met3** with via arrays. Rail height is 2.5 µm for the TX driver.
- **Top level:** full-height vertical met4 straps (the power pins) on the tile's left and right edges, plus a mid strap if needed. They meet the blocks' met3 rails with via3 arrays where they cross, or through short met3 spurs.
- **Signal pins:** met2/met3 at block edges, the TX output on met3 (2.5 µm).

## Current limits: EM and IR (sky130, from the tech LEF)
Source: `$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef` (`DCCURRENTDENSITY` / `ACCURRENTDENSITY`, Tj = 90 °C; at ≤ 50 °C the lifetime is far longer, but keep ~2× margin anyway).

| layer | DC avg | AC RMS |
|---|---|---|
| met1, met2 | 2.8 mA/µm | 6.1 mA/µm |
| met3, met4 | 6.8 mA/µm | 14.9 mA/µm |
| met5 | 10.17 mA/µm | 22.34 mA/µm |
| mcon | 0.36 mA per cut | |
| via1 | **0.29 mA per cut** | |
| via2, via3 | 0.48 mA per cut | |
| via4 | 2.49 mA per cut | |

- **Vias are the weak point.** A 1 mA path through one via1 is 3.5× over. Size every layer change in a current path by cut count: cuts ≥ 2 × I / limit.
  - Use the RMS current for AC nets and the average for supply nets; the LEF only gives DC per cut, so treat it as the limit for both.
- **Sheet resistance:** met1/met2 ~0.125 Ω/□, met3/met4 ~0.047 Ω/□. Wide met3 is cheap and strong, so stack big currents onto met3.
- **Measure the currents with the block testbench** (0 V ammeters in the schematic subckt), then size. Don't guess.

### tx_drv currents (tb_tx_drv, tt, ideal 434 MHz drive, per arm)

| path | avg | RMS | peak |
|---|---|---|---|
| stage 5 PMOS source / VAPWR | 6.65 mA (DC) | 9.45 mA | 18.4 mA |
| stage 5 NMOS source / VSS | 2.29 mA | 3.62 mA | 11.9 mA |
| out | ~0 (AC) | 9.8 mA | 16.9 mA |
| y4 (stage 4 drains → stage 5 gates) | | ~1.45 mA each side | 7.4 mA |
| y3 and earlier | | ≪ 1 mA | |

### v1 layout lessons (one column per stage)
- **Under-sized connections:**
  - **Gate links** land with a single via1 on a 0.37 µm met1 riser, so y4 sees 5× over the via1 limit.
  - **Source strips:** the stage 5 PMOS inner source strips at 0.29 µm met1 are rated 0.81 mA and carry ~0.95 mA average.
  - **Output bar:** the 2 µm met2 out bar has too little RMS margin.
- **Measured cost:** the extracted layout loses 0.46 dB, edges are +30 ps and the in→out delay is +26 % (+5.35 vs +5.81 dBm).
- **Floorplan waste:** one column per stage makes every small stage as tall as the 10 µm-finger output stage. The empty space was filled with met1 plates to the rails.
  - Better: pack the PMOS and NMOS rows separately, with finger heights chosen so the rows are the same length.
  - Use one guard ring per row, and a met3 horizontal / met2 vertical routing channel between the rows.

## Simulation gotchas (layout-specific)
- **Save only what you measure** on extracted netlists. Thousands of R nodes × timepoints overflow ngspice's output memory ("memory required … more than memory available"). Use a `save` list in `.control` before `tran`.
- **Subckt source names:** in `meas`, use `let` to make vectors first: `meas` won't take expressions. Sources inside subckts are named `v.<inst>.<name>`, e.g. `i(v.xdp.vd5p)`.
- **xschem top-level subckt:** outside LVS mode it writes `**.subckt` / `**.ends` (commented) even with `top_subckt 1`. With `lvs_netlist 1` they're real.
- **Edge thresholds:** under the pad + dipole load, `out` doesn't reach 80 % of 3.3 V. Measure 20–80 % of the actual swing.

### v2 (current, 2026-10-08): packed rows + routing channel
- **Floorplan:** PMOS row (fingers ≤ 8 µm) and NMOS row (≤ 4.5 µm), one shared guard ring each (the PDK `guard_ring_gen` pcell, met1), a met3-track / met2-stub channel between them, rails 3 µm.
  - Per-net stub/track widths and drain-bar heights come from the measured currents; the generator prints a via1/via2 count check against 2× margin.
- **Result:** 40.9 × 27.6 µm (1129 µm², −19 % vs v1). DRC/LVS clean. Block test (tt) vs schematic: −0.32 dB, edges +30 ps, delay +35 %.
- **Left on the table** (not worth it yet): the NMOS row has a gap (each N is aligned under its P), and the small PMOS devices still hang from tall source straps. Possible fixes:
  - stack NAND/inv1/inv2 as a mini-cell in the top-left corner;
  - pack the NMOS row tight.

### v2 lessons
- **Magic interprets each GDS cell on its own.** A tap only becomes an HV n-well tap when nwell + hvi are in the same cell. The ring pcell has no well, so flatten it into the cell that has the wells (`lay.ring` does).
  - Symptoms: nwell.4 "nwells must contain N+ taps", LU.3, nwell.8 "HV to LV nwell".
- **Ringless (`bulk='None'`) nfet pcells leave notches in hvntm** (hvntm.2), and neighbours sit closer than its 0.7 µm spacing. Draw one hvntm rectangle over the whole NMOS row.
- **Overlapping via arrays from two `stack()` calls** (a bar running into a riser) give via2.1a/via2.2 errors in KLayout. Magic doesn't flag them, so let shapes abut instead of overlap.
- **A riser spanning rail to rail shorts `out` to both supplies.** LVS shows it as "(no pin, node is out)" for VAPWR/VSS.
- **Narrow met2 stubs:** via2 needs 0.04 µm met2 enclosure on two sides and 0.085 µm on the other two. That fits a 0.28 µm stub, with the track (met3) extended 0.1 µm past the end stubs.
- **Magic DRC locations:** `check.sh` now prints them in µm (`cif scale out`). Magic's `what -list` needs a `select area` first.
- **Magic's `antennacheck` can silently report nothing.** It is only trustworthy:
  - on a **flattened** cell: on the hierarchy it misses pcell gates driven by metal in the parent;
  - in a **fresh session**: after the LVS extraction in the same session it found nothing;
  - with **`antennacheck debug`**: otherwise violations only go to the feedback list.
  - Verified with a deliberate violation (`layout/gen/ant_test.py`: a 0.5 × 0.42 µm g5 gate on 300 µm² of met1, ratio 1033 > 400).
- **Net labels:** text on the metal's label purpose (e.g. 70/5) without a pin shape names the net in magic's extraction without making it a port.
