# Power delivery: benchmark of the routed tile (2026-10-09)

What the supplies look like from each block, measured on the routed tile as of the 20:00 build
(`build/top/tt_um_mattvenn_radio.gds`), before any power changes. Scripts: `sim/power/`
(how to re-run: bottom of this page). Proposals: last section.

## How TT feeds the tile (from tt-multiplexer)
Source: github.com/TinyTapeout/tt-multiplexer, `ol2/tt_top/` (`pdn.tcl`, `build.py`,
`odb_power.py`, `odb_route.py` ModulePowerStrapper), `py/tt/elements.py`, `pg/sky130/`.
Model: `sim/power/pdn.py`.
- **VDPWR and VAPWR are switched** by full-height power-gate cells on the tile's **west** side:
  `tt_pg_1v8_*_2` (9.2 µm) and `tt_pg_3v3_2` (13.8 µm, next to the tile). Each gate's output
  (met4 column) feeds **two met5 stripes drawn across the tile** to our met4 pins: one 8.75 µm at
  mid ± 5.5 µm, one 19.75 µm at mid ∓ 57.12 µm. Every same-net met4 pin they cross gets via4s.
  Which supply gets which pair (pin order) and whether the tile sits N or FS are not known: case A
  = VDPWR at y 118.4 / 55.8, VAPWR at 107.4 / 170.0; case B swapped.
- **VGND** comes from the global met5 grid: 8.75 µm stripes at y 27.2 / 84.3 / 141.4 / 198.6 (the
  middle stripe of each vdpwr / vgnd / vapwr set; the switched stripes take the gaps).
- **Gate on-resistance** (ngspice, the gates' power PMOS, tt, 20 mA, 10–50 °C,
  `sim/power/pg_rdson.spice`): 1v8 hp 0.76–0.78 Ω (ll 0.89–0.91 Ω), **3v3 1.93–2.17 Ω**.
- **Assumed** (not from TT): package + bond wire 0.5 Ω + 2 nH per supply, 1 nF of chip grid C at
  each gate input (`common.UP`).
- So the VAPWR east straps and the macro's stripes get their current along ~500 µm of met5 from
  the west, and each VDPWR / VAPWR strap has only **two** landings.

## Method (and why not magic's rc extraction)
magic's `extresist` (the rc mode of `layout/pex_tile.sh`) is not usable for the supply nets: it
builds its resistor network toward device terminals only and folds large parts of the net into the
port node (avg_sc's and comp_ct's ground terminals came out on the VGND port itself, the straps came
out ideal). No tolerance / threshold / simplify setting changes it, and its FastHenry export is the
same network. Other magic traps on the way (all handled in `sim/power/pdn_gds.py`): several
differently named ports on one net make it write the whole net once per port; same-name labels
short the strap ends together; the std cells' substrate labels and the p-taps merge VGND with an
ideal substrate; a KLayout-flattened GDS crashes ext2spice.

So:
1. **Extraction copy** (`pex_power.sh` / `pdn_gds.py`): the tile without the macro, plus the gates'
   output columns, the met5 stripes and via4s, one port per supply. magic rc gives the devices,
   the signal parasitics, every C on the supplies, and each device terminal's position.
2. **Supply mesh** (`mesh.py`): KLayout traces each supply net (li … met5, mcon … via4), rasterized
   at 0.5 µm; R between cells from the PDK sheet R, cut R × cut count between layers.
3. **ngspice** solves everything: DC R per block (`r_mesh.py`), IR drop with the real currents
   (`ir_rx.py`), and the AC runs on a **stitched** tile (`stitch.py`: magic's devices + C, the
   mesh at 1 µm, the PDN model) (`z_ac.py`).
- **Probe points:** a block's local supply = the mesh nodes at its devices' current-carrying supply
  terminals (MOS drain / source, R / C ends; not bulk), assigned to the block by position.
- **Mesh check:** 0.5 vs 1 µm agree within ~5 % except the long thin RX ground route, where 1 µm
  is ~30 % low (avg_sc 47 vs 67 Ω): the coarse cells bridge neighbouring wires. DC numbers are 0.5 µm;
  the AC runs (1 µm) are that much optimistic on RX ground.
- **Cross-check:** `tools/power_r.py` (same idea, straps ideal) agrees once the straps / met5 / gate
  path is added (RX VGND avg_sc 61 → 67, comp_ct 55 → 57, bias 27 → 31 Ω).
- Not modelled: substrate coupling (the substrate is one node tied to the VGND port), the macro.

## Benchmark (case A)
R: from the block's device terminals to its gate output (VDPWR, VAPWR) / the VGND grid, mean over
terminals, 0.5 µm mesh; add the gate (0.77 / 2.0 Ω). IR: RX operating point (3.0 mA VDPWR), drop
below the gate output / rise above the grid. |Z|: between the block's local VDD and VSS, 1 µm mesh
with the decaps, device C and PDN. TX→RX: |ΔV| between the RX block's local VDD and VSS per A drawn
at a TX driver at 434 MHz.

| block | R VDD (Ω) | R VSS (Ω) | IR VDD / VSS (mV) | \|Z\| 77 kHz | \|Z\| 434 MHz | TX→RX at 434 MHz (Ω) |
|---|---|---|---|---|---|---|
| chain | 6.0 | 7.1 | 15.6 / 20.4 | 22.6 | 20.8 | 0.025 |
| log_det | 28.7 | 13.6 | 2.3 / 0.5 | 52.2 | 50.9 | **0.59** |
| avg_sc | 27.7 | **66.8** | 2.1 / 3.5 | 74.5 | 64.7 | 0.038 |
| comp_ct | 26.6 | **56.8** | 2.1 / 3.5 | 81.0 | 71.1 | 0.037 |
| bias | 13.6 | 30.9 | 2.5 / 3.1 | 56.2 | 46.9 | 0.034 |
| r2r | – | 35.2 | – / 6.2 | | | |
| dbg_tg | 31.7 | 26.2 | 14.4 / 0.4 | 63.7 | 62.6 | 0.58 |
| tx_ring | 7.3 | 1.9 | | 17.9 | 16.9 | |
| tx_drv_p | 3.0 (VAPWR) | 2.5 | | 12.0 | 10.8 | |
| tx_drv_n | 1.6 (VAPWR) | 2.1 | | 10.2 | 8.9 | |
| VAPWR decap | 10.9 (worst 19.9) | 7.5 | | | | |
| VDPWR decap | 18.7 | 10.0 | | | | |

- **TX IR (both arms, 6.65 mA average / 18.4 mA peak each on VAPWR):** tx_drv_p VAPWR drop 29 mV
  average, 79 mV peak (+ 27 / up to 75 mV in the 3v3 gate); VGND rise 9.5 / 49 mV. tx_drv_n:
  19 / 53 mV. Both arms at peak at once is pessimistic (they alternate).
- **The supply impedance at every block is resistive and flat to 500 MHz**: |Z| ≈ R VDD + R VSS.
  The decaps sit behind 10–20 Ω of mesh, so they do almost nothing at the blocks.
- **TX → RX:** per A drawn at a driver, log_det's supply moves 0.59 Ω × 9.45 mA RMS ≈ **5.5 mV at
  434 MHz** (the detector rectifies its supply too); the chain, comp_ct, avg_sc ≤ 0.04 Ω (≤ 0.4 mV).
  The arms are in anti-phase, so the 434 MHz supply current partly cancels: the keyed transient
  will give the real figure.

To do: case B, the TX-keyed transient (RX supply / ground bounce), EM per via / µm on the TX paths,
the proposals with estimates.

## Re-running
```
tools/osic-mac bash -c 'CASE=A bash sim/power/pex_power.sh'    # extraction copy + magic rc (~30 s)
tools/osic-mac python3 sim/power/mesh.py A 0.5                 # supply meshes (and 1.0 for the AC runs)
python3 sim/power/r_mesh.py A                                  # DC R per block (~25 min, VGND is slow)
python3 sim/power/ir_rx.py A                                   # IR at the RX op and the TX currents
python3 sim/power/z_ac.py A                                    # |Z| per block, TX -> RX (~30 min)
```
