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

## Row builder (`layout/gen/rows.py`) and the TX level shifters (2026-10-08)
- **`rows.build(block, P, N, nets, ...)`** is `tx_drv` v2's machinery made generic. A block generator just lists its devices (`Dev`: FET, strip roles, gate groups, drain net, rail) and nets (`Net`: stub/track widths, RMS current, io `L`/`R`/`riser`).
  - **Segments:** devices are grouped by oxide (thin / g5) and rail into columns. Each column gets its own rings, nwell, hvi/hvntm (HV only) and rail section.
  - **Segment gap:** 4.7 µm between columns, diffusion to diffusion (rings, wells, HV/LV nwell spacing 2.0 µm).
- **Channel routing lesson:** a P stub (going down to its track) and an N stub (going up) at the same x short in met2 if the P net's track is below the N net's. `tx_drv` avoided this by luck; `tx_ls` hit it (LVS: A shorted to ctrl_n).
  - Fix: plan every stub's x first, add a vertical constraint (P net above N net) for each overlapping pair, and assign tracks with the constrained left-edge algorithm. Nets still share tracks when allowed.
  - `tx_drv` got 0.45 µm shorter from the better sharing.
- **Parameter variants:** a generator writes `layout/ref/<variant>.spice` (the xschem netlist with the parameters substituted and evaluated). `check.sh` and `pex.sh` use it when present.
  - Even the default variant needs one: netgen can't evaluate `W='0.42*kn'` and reports "property errors".
- **Viewer links:** `python3 tools/gds_links.py` rewrites `layout/README.md` with a TT GDS viewer link per block (they work once pushed).

| block | size | DRC / antenna / LVS | block test (tt), schematic → extracted |
|---|---|---|---|
| `tx_drv` | 40.9 × 26.7 µm | clean | −0.32 dB into the dipole |
| `tx_ls` (kn 10, kp 4, wpi/wni 9/3) | 13.8 × 19.0 µm | clean | A edges ~100 → ~190 ps; in→A rise 392 → 660 ps; **A duty 37.3 → 28.4 %** |
| `tx_ls_en` (all ~minimum) | 12.9 × 12.5 µm | clean | delay 1.1 → 3.4 ns (irrelevant: the enables switch at chip rate) |

- **Fixed (mostly): the main shifter's duty cycle.** The slow path was in → ctrl → **ctrl_n** (dac_drive's tiny hvt P 1 / N 0.42 inverter driving M10's thick gate + the ctrl_n wiring). kp 6 didn't help (extracted 27.8 %).
  - **M8/M7 upsized to 4 / 1.68** (`xschem/gen/tx.py`). tt extracted: A duty 28.4 → **35.8 %** (schematic 41.8 %); arm output duty 38.6 / 43.7 % (schematic 44.1 / 47.6 %), about −0.4 dB of fundamental vs schematic.
  - Judge the rest in `tx_top`, with the shifter right against the drivers' inputs.
- **`tx_ring`** (`layout/gen/tx_ring.py`): std cells (PDK GDS copied in): one row of 22 `inv_2` + `nand2_2` + 4 taps, 34.5 × 4.2 µm.
  - Stage straps on met1 (mcon on the li pins), the `out` return on met2, `en` on met3 from the left edge. Block rails 1 µm (m1–m3) over the cells' rails.
  - **LVS with std cells:** `check.sh` loads the hd spice library on the schematic side (netgen tcl).
  - The reference (`layout/ref/tx_ring.spice`) drops the schematic's `cw` caps: they're a wiring estimate, not devices.
  - **Block test** (`sim/tx/tb_tx_ring.py`, into the main level shifter, tt): schematic (cw 3.2 fF) 485.4 MHz → **extracted 508.5 MHz** (+4.8 %, less wiring than the ttsky25b calibration). Silicon estimate ×0.866 → **~440 MHz** (target 433.92), out duty 47.9 %. Keep 22 inverters.
  - Density reads 51–55 % on m1–m3, because the 4.2 µm-tall block is half rails; it averages out inside `tx_top`.
- **`r2r`** (trim DAC, **reused** from tt08-analog-r2r-dac-3v3): the magic sources are copied unchanged into `layout/src/r2r/`; `layout/gen/r2r.sh` writes `layout/r2r.gds`. 71.8 × 54.1 µm (3,882 µm²; the area estimate had 3,866), pins on met1 along the bottom (b0..b7, out, VGND).
  - Clean against `xschem/r2r.sch`, which was drawn to match the layout device for device: DRC 0, antenna 0, LVS match. Density m1 27 %.
  - **Block test** (`sim/dac/tb_r2r.py`, tt): extracted output error ≤ 0.021 LSB; Rout 10.65 kΩ (schematic 10.64); the 127→128 carry into 1 pF settles to 0.1 LSB in 30.6 ns (schematic 24.6), irrelevant at the servo's µs steps.
  - `check.sh`'s "feedback N" counts magic's extraction warnings too (2 here, from flattening); the antenna count is the 'Antenna violation' lines.
- **Row builder: pass devices.** A strip role can now be any net name, so both sides of a transmission gate can be signals.
  - With several strip nets on a device, all its stubs are packed side by side in natural x order across the device, up to DGAP/2 into the gaps. Bars and straps extend to their stubs.
  - Single-drain devices keep the old placement (`tx_ls` identical; in `tx_drv` only the NAND's in/en tracks swapped).
  - `build()` leaves `b.rows` (rails, tracks, track x spans) for generators that add more (caps, wiring).
- **`lay.write_ref(name, sch, params, drop)`:** a parameter-substituted LVS/PEX reference from any xschem cell (netgen can't evaluate `W='wcs'`, `m='nca'`).
- **`avg_sc`** (`layout/gen/avg_sc.py`, 74.5 × 43.6 µm):
  - Layout: 8 thin FETs via rows.py (phase inverters, then S1 and S2 as transmission gates). Cs 7×7 under the switches; 2 × Cavg 30×30 to the right. Each MIM bottom plate abuts the VSS rail, which runs across the caps (`passives.mim`, the other session's).
  - Cs's top plate rises on its own met4 strip to the `cs` track. The Cavg top plates share a met4 strip that rises to the `out` track at the switch block's edge.
  - Checks: DRC/antenna/LVS clean; m3 density 65 % (the MIM plates).
  - **Block test** (`sim/avg_sc/tb_avg_sc.py`, 20 cycles of the digital's 13 µs phi timing, tt): τ 0.458 ms (schematic) → **0.434 ms** (extracted).
  - **Open:** the extracted hold drift is ±1.7–1.9 mV over 20 cycles (schematic −0.015), from phi/phib coupling imbalance onto `cs`/`out`, for example 1.15 fF to phi2 against 0.50 fF to phi2b. Moving the phase inverters only flipped its sign.
    - Steady state is about ±4 mV static offset at the comparator: within the trim range (−19…+12 mV), but about a third of it.
    - Fix if the trim gets tight: a symmetric layout (balanced phi/phib routing around `cs`/`out`, dummy half-switches).
- **Earlier note on the duty cycle:** Its skewed core (weak cross-coupled PMOS pull-up) is sensitive to the ~4.7 fF of wiring on A/B, comparable to its devices' own capacitance.
  - The schematic at kp 6 gives 36.3 %; the extracted run is pending.
  - What matters is the duty at the arms' outputs, so judge it with the level shifter + drivers together, not A alone.
