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

**Case B** (the stripe pairs swapped) changes little: VGND identical; RX VDPWR R +0.7 Ω (chain 6.0
→ 7.9 Ω), RX VDPWR IR drop 2 → 5 mV (chain 15.6 → 21.3 mV); the TX drivers' VAPWR R 3.0 / 1.6 →
2.5 / 1.1 Ω, TX average drop 29 / 19 → 22 / 13 mV. The benchmark uses case A (worse for the TX).

### TX keyed (transient, `tran_tx.py`)
tx_en keyed at 5 ns, RX biased on as well, 30 ns, last 10 ns, case A:

| block | local VDD−VSS p-p (mV) | of which 434 MHz (mV) |
|---|---|---|
| tx_drv_p | 63.2 | 6.3 |
| tx_drv_n | 37.3 | 1.8 |
| log_det | 11.6 | 0.50 |
| dbg_tg | 11.9 | 0.47 |
| tx_ring | 8.9 | 0.29 |
| chain / avg_sc / comp_ct / bias | 6.6–7.2 | 0.19–0.26 |

- The arms' anti-phase currents cancel most of the 434 MHz on the shared supply: the RX blocks see
  0.2–0.5 mV at 434 MHz (the AC run's per-arm estimate, 5.5 mV at log_det, is the no-cancellation
  bound). The p-p is mostly the keying step ringing.
- The whole chip rings ~355 mV p-p against the board ground (vdpwr, vapwr and VGND together): the
  assumed 2 nH package with 1 nF of chip grid C, undamped; common mode, not across any block.
  Depends on the package assumptions, not on our layout.

### EM (`em.py`, both arms at their average current, 0.5 µm mesh, case A)
| path | worst | limit | |
|---|---|---|---|
| **via4, west VAPWR strap (x 2.5) at the y 107 stripe** | **5.2 mA/cut** | 2.49 | **2.1× over** |
| **met4, west VAPWR strap (1.2 µm)** | **13.8 mA/µm** | 6.8 | **2.0× over** |
| **met3, VAPWR_TX at the drivers (54, 120)** | 10.5 mA/µm | 6.8 | 1.5× over |
| via3 at the west VAPWR strap | 0.53 mA/cut | 0.48 | 1.1× over |
| mcon (VAPWR) | 0.24 mA/cut | 0.36 | 67 % |
| VGND worst: via3 at (30.5, 120) | 0.30 mA/cut | 0.48 | 62 % |

Most of the TX's VAPWR current enters through the west strap's single via4 column under one met5
stripe and runs along the 1.2 µm met4 strap. These are average currents: the RMS (9.45 mA per arm)
is higher. (Partly covered mesh cells at a 1.2 µm strap's edges read high; the strap as a whole
carries ~13 mA, ~11 mA/µm, so the overstress is real.)

## Proposals (for Matt to pick; estimates, not yet simulated)
The weak spots, in order: **(1) TX VAPWR EM at the west strap (a reliability fail), (2) RX ground
57–67 Ω and RX VDPWR 27–32 Ω (flat to 500 MHz), (3) the decaps doing nothing at the blocks.**

| # | change | effect (estimate) |
|---|---|---|
| 1 | **West VAPWR strap 1.2 → ≥ 4 µm** (2 via4 columns per landing), VAPWR_TX met3 at the drivers ≥ 3 µm, more via3 there | EM: via4 2.6 mA/cut → still over; with the strap ≥ 6 µm (3 columns) ~1.7 mA/cut (68 %); met4 ~2.8 mA/µm. TX VAPWR R −1 Ω (~−13 mV avg). **Needed.** |
| 2 | **Wider RX trunks** (VDPWR_RX / VGND_RX 1 → 4 µm, met3 + met4 stacked where free) | The trunks are most of the RX R: avg_sc / comp_ct VGND 57–67 → ~15–20 Ω, VDPWR 27 → ~8–10 Ω; chain IR 36 → ~12 mV. |
| 3 | **Extra met4 VDPWR / VGND strap pair in the middle of the analog** (a met4-free column, e.g. x ~150, between log_det and Ctrim) | Halves the trunk length for log_det / comp_ct / avg_sc / bias: ~−50 % on their R (with 2: ~−75 %). Needs the met5 stripes to land on it (they cross the whole tile: free). |
| 4 | **Join the RX side to the mid straps** across decap parts 1 / 3 below the macro-pin band | comp_ct / bias / r2r get a second, short path: their R ~−40 %. |
| 5 | **Decap at the load**: wire each decap part straight to the block it serves (TX: the VAPWR decap rails onto VAPWR_TX at the drivers; RX: VDPWR decap onto the chain / det rails) | Today \|Z\| at the blocks is the mesh R (flat). A 20 pF part within ~1 Ω of tx_drv: \|Z\| at 434 MHz 11 → ~6 Ω at the driver. For RX, only useful with 2 or 3 (otherwise the decap sits behind the same R). |
| 6 | **More via cuts** on the RX trunks' layer changes | Small (vias are a few Ω of the 30–60); do with 2. |

Suggested set: **1 (must) + 2 + 3**, then 5 for the TX. Each can be checked on this flow before the
top-level session commits it (the mesh run takes ~30 min per supply set).

## What-ifs (2026-10-10, case A, 0.5 µm mesh, the extraction copy only)
`pex_power.sh` takes `VAR=<tag> STRAP_W='{"<old x0>": [x0, x1]}'` (straps widened in the copy, kept
0.3 µm from other nets' met4 / via3 / MIM; check `magic.log` for "shorted" before simulating); `mesh.py`
takes `IDEAL=1` (strap R = 0) and `TRUNK=k` (top-level routing outside the blocks ×k), `MESH_TAG`.
- **W**: west VAPWR 0.3–5.3, VDPWR 5.8–10.5, VGND 12.0–15.1 (10.8 shorts VDPWR in the copy), east
  VAPWR 481.0–489.22. **ideal**: W with every strap ideal. **W+trunk3**: W with the routing ×3.

| block (R mean, Ω) | VDPWR base / W / ideal / W+trunk3 | VGND base / W / ideal / W+trunk3 |
|---|---|---|
| chain | 6.0 / 5.7 / 5.5 / 5.6 | 7.1 / 7.0 / 6.7 / 7.0 |
| log_det | 28.6 / 27.9 / 27.4 / 23.2 | 13.6 / 13.5 / 13.3 / 11.7 |
| avg_sc | 27.7 / 28.5 / 28.0 / 21.6 | 66.8 / 67.3 / 66.0 / 64.7 |
| comp_ct | 26.6 / 25.6 / 25.1 / 18.6 | 56.8 / 56.4 / 55.1 / 54.0 |
| bias | 13.6 / 13.4 / 12.8 / 11.0 | 30.9 / 31.0 / 29.6 / 29.3 |
| tx_drv_p (VAPWR) | 3.0 / 2.4 / 2.1 / 1.9 | 2.5 / 2.4 / 2.2 / 1.8 |
| tx_drv_n (VAPWR) | 1.5 / 0.8 / 0.6 / 0.8 | 2.0 / 2.0 / 1.8 / 1.5 |

TX average VAPWR drop at tx_drv_p: 29 → 20 (W) → 16 (ideal) → 17 mV (W+trunk3). Chain IR unchanged
(~15 / 20 mV). EM with W: west strap via4 210 → 62 %, met4 202 → 51 %; still over: **VAPWR_TX met3
at the drivers (56.5, 120.5) 18.7 mA/µm = 275 %** and via3 at the west strap 107 %.

**Findings**
- **Wider straps fix the TX** (VAPWR R and the strap / via4 EM) but **do nothing for the RX**: even
  ideal straps leave avg_sc / comp_ct at 55–66 Ω to VGND.
- **The RX ground resistance is in the path, not in any one wire**: the lowest-R path from avg_sc to
  the grid winds through other blocks' rails (bias met3 ~14 Ω, decap part 3 met1 ~10 Ω, the chain,
  comp_ct) and the 1 µm routes (~55 Ω), ~150 Ω in series (67 Ω with the parallel paths). Scaling the
  top-level routes ×3 doesn't help VGND (its R is inside block bboxes: rails used as the trunk).
- **No full-height column for a new strap in the RX area**: every x in 16–239 hits block met4 / MIM.
  Removing decap frees full-height columns only in decap part 1 (x 239.5–242.5 for 3 µm, 251.5–273.5
  for 6 µm), next to the mid straps the RX already reaches: small gain.

**Recommendation**
1. **TX (do):** west VAPWR strap ≥ 5 µm (as W), VAPWR_TX met3 at the drivers ≥ 3× wider (or
   met3 + met4 stacked) and ≥ 2× the via3 at the west strap; west VDPWR / VGND as wide as W.
2. **RX (do):** a **dedicated VGND_RX (and VDPWR_RX) trunk**, ≥ 4 µm, met3 + met4 stacked where free,
   from the mid VGND / VDPWR straps straight to avg_sc, comp_ct, lpf, log_det, Ctrim / r2r, so their
   current no longer runs through bias / decap rails. Make room by trimming decap (parts 1, 3, 4).
   Not yet simulated: needs the route geometry (top-level session), then this flow re-runs on it.
3. A strap in decap part 1 (x ~251–273, 6 µm): only if 2 can't reach the mid straps.

## Re-running
```
tools/osic-mac bash -c 'CASE=A bash sim/power/pex_power.sh'    # extraction copy + magic rc (~30 s)
tools/osic-mac python3 sim/power/mesh.py A 0.5                 # supply meshes (and 1.0 for the AC runs)
python3 sim/power/r_mesh.py A                                  # DC R per block (~25 min, VGND is slow)
python3 sim/power/ir_rx.py A                                   # IR at the RX op and the TX currents
python3 sim/power/z_ac.py A                                    # |Z| per block, TX -> RX (~30 min)
```
