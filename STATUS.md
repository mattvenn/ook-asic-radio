# Where we are (handoff, end of 2026-10-09)

Read **PLAN.md** for the decisions and their evidence. This file is the "pick up from here" note: summary, next steps, how to run things. Per-block
detail and the history behind each result: **docs/history.md** (read the section you need, not the whole file).
New agents: start with **docs/agent_start.md**.
Repo: github.com/mattvenn/ook-asic-radio (`main`).

## Start here

**State (2026-10-10): the 3x2 tile is assembled and routed (all 95 nets, decaps in): magic + KLayout DRC 0, LVS clean, TT precheck pass. Extracted-tile sims done (`docs/handoff_sim.md`): the c-mode anomalies were floating pin stubs (tied off in `sim/top/tb_tile.py`), the TX loss is fixed (tx_ls kn 14 / kp 8, TX corner re-floorplanned; extracted RC +3.18 dBm). Power delivery benchmarked (`docs/power.md`): west VAPWR strap fails EM, RX ground 57–67 Ω; proposals there for Matt. How to run every check: `docs/verification.md`. Details: docs/history.md, docs/layout.md "Top level".**
- **Floorplan:** `layout/floorplan/pins.md` / `floorplan.json` (layout 5: comp_ct and r2r flipped to MYR90, macro pins level with what they connect to; `docs/floorplan_spec.md` "Chosen floorplan"). Pin moves per block: `docs/layout.md` "Pin moves for the floorplan".
- **Macro:** `macros/radio_digital/` (GDS, LEF, DEF, netlists), from `openlane/radio_digital` (`PIN_ORDER.md`). Signoff clean; RTL and GL cocotb 15/15 on the final netlist.
- **RX:** every block is transistor level with real PDK passives and a real bias generator.
  - Chain: pad → 6-stage NMOS diff-pair limiting chain.
  - Detector: successive-detection log detector → 14 kHz RC LPF (2.95 MΩ / 3.7 pF).
  - Comparator side: switched-cap average (τ ~0.45 ms) → continuous comparator; trim from the reused R2R ladder, driven by the RTL servo.
  - **Confirmed three ways:** the fully joined transistor-level run (antenna → comparator) matches the split model. Corners 10–50 °C give a worst case of **≈ −92…−93 dBm**. And the **mixed-signal run** (RTL servo → real `r2r` → real `comp_ct`) detects −70 and −94 dBm bursts.
- **TX:** xschem blocks, +3.7…+3.9 dBm at all corners, both arms low when off, single-ended fallback (`tx_en_n`). VAPWR decap ~50 pF.
- **Digital:** **clock-gated** (`rd_cg.v`, one `sky130_fd_sc_hd__dlclkp_1` per 127-bit chip register), hardened with LibreLane at **200 × 220 µm** (2026-10-09; was 260 × 190).
  - Signoff clean (DRC, LVS, antenna 0; timing met at all corners).
  - **RTL suite 15/15 and gate-level suite 15/15** on the hardened netlist (`make GL=1`).
- **Top level:** `radio_analog` (all analog blocks + bias + decap) and the `tt_um_mattvenn_radio` schematic; ua[0]/[1] RX, ua[2] debug (det via a debug-only TG), ua[3]/[4] TX (reassigned 2026-10-09; was TX 0/1, RX 2/3, debug 4).
- **Power delivery benchmark** (2026-10-10, `docs/power.md`, `sim/power/`): the TT PDN modelled from tt-multiplexer (switched VDPWR / VAPWR on two met5 stripes each from gates west of the tile). RX R to the supply: VGND 57–67 Ω (avg_sc, comp_ct), VDPWR 27–32 Ω, flat to 500 MHz (decaps sit behind the mesh); chain IR ~36 mV. **EM fail: the west VAPWR strap (1.2 µm met4, one via4 column) carries the TX current at 2× the limit.** Proposals there for Matt.
- **Area** (`sim/area/area_netlist.py`): the analog needs ~49k µm² of the ~57k left beside the macro in the 3x2 (493 × 226 µm): **85 %**, 93 % of the tile. The VAPWR decap (~18k µm²) is the biggest block.
- **Operating range 10–50 °C only.**
- **Layout flow (KLayout pcells → DRC/LVS → PEX → block test) works end to end on `tx_drv`.** See `docs/layout.md` for the steps, power/PDN rules, EM table and lessons.
  - **tx_drv v2:** 40.9 × 27.6 µm; DRC (Magic + KLayout) and LVS clean. EM-sized from measured currents.
  - **Block test** (`sim/tx/tb_tx_drv.py [--pex]`): −0.32 dB vs schematic.
  - **Policy:** each block gets a small `tb_<block>` (schematic vs extracted). One end-to-end run on the full extracted design at the end.
  - **Power pins:** met4 straps (≥ 1.2 µm, full height) on both the left and the right of the tile.
  - **TX blocks:** `tx_drv`, `tx_ls`, `tx_ls_en` laid out with the row builder `layout/gen/rows.py`; all clean. Previews: `layout/README.md` (TT GDS viewer links).
  - **Level shifter:** tx_ls **kn 14 / kp 8** (was 10 / 4, 2026-10-10): the extracted tile lost 1.5 dB to the p arm's duty under the real a / b load. `tb_tx` +4.14…+4.26 dBm at all corners; extracted tile RC **+3.18 dBm** (was +2.11). TX corner re-floorplanned (tx_ls beside the ring, the two tx_ls_en underneath). Details: docs/history.md "Extracted-tile sims".
  - **Ring:** `tx_ring` laid out, **folded into two rows** so there's no long feedback wire (std cells, 17.9 × 7.0 µm, clean). Extracted 529.9 MHz tt → **~459 MHz on silicon** (×0.866), +5.8 % on 433.92. The ring is untrimmed and the RX band is 330–560 MHz, so this is fine. 24 inverters would give ~422.
  - **Plan (Matt, 2026-10-08):** a first take on every leaf block, then floorplan the whole tile; assemble `tx_top` as part of that floorplan.
    - Outputs exit the bottom of the tile: ua[3] = 78.7, ua[4] = 59.3 µm in the 3x2 DEF, so the TX goes there (pins reassigned 2026-10-09).
    - The digital macro's `tx_en`/`tx_en_n` leave its west edge near the bottom.
  - **Leaf blocks done** (`layout/README.md` has viewer links):
    - TX: `tx_drv`, `tx_ls`, `tx_ls_en`, `tx_ring`.
    - Trim DAC: `r2r` (the tt08 layout reused; extracted error ≤ 0.02 LSB).
    - RX: `avg_sc` **v2** (2.35k µm², was 3.25k; mirrored phi/phib channel with shields: extracted clock-coupling imbalance on cs/out 0.2 → ≤ 0.011 fF, extracted hold drift ±1.8 → +0.07 mV over 20 cycles, i.e. static offset ~4 → ~0.15 mV; τ 0.423 ms); `lpf_rc` and `dbg_tg` (other sessions).
    - Also by other sessions: the decaps.
    - **`bias_gen`:** done, 80.2 × 49.1 µm (3.9k µm²): mirror array (123 units, ABBA common centroid) under Cc + 2 × Cvcm, the small devices (rows.py), the resistors under one Cvref. Clean; extracted currents and vcm within 0.1 % of the schematic over VDD 1.7–1.9 V, 10–50 °C (`sim/bias/tb_bias_gen.py`). Schematic changes: Cvcm / Cvref as 2 × 22 µm units, 5 array dummies `Mdum`, Rref as two 5 kΩ halves. Details in `docs/layout.md`.
    - **`comp_ct`:** done, v2 **73.5 × 42.0 µm (3.08k µm², was 5.0k)**: trim pair next to the main pair (out/o2 → d1/d2 coupling 7.4 / 6.2 fF → 0), bias tails folded into 4.55 µm fingers, Cl (2 × 22 × 11) + Cref over the resistor ring. Clean; extracted offset +0.56 mV, trim 0.0656 mV/LSB. Matching dummies are in the schematic (`Mdn*`/`Mdp*`).
    - **`det_cell`** (another agent) / **`log_det`:** done, **compacted to 2 rows × 3 cells: 87.3 × 31.0 µm (2.7k µm², was 5.4k bbox)**. The rows share the VSS rail (bottom row mirrored), so the inputs face out top and bottom, with t1 and t6 on opposite corners. The vb replica (Rs_b drawn like the cells' Rs) and Rdet sit in an end column under Cdet. VDD is a met3 strip down the right edge. Clean.
      - Extracted idle det 1.520 → 1.489 V (high-po contact term per segment: Rs/Rdet ~10 % high); 100 mV on t6 −1.56 → −1.46 mV. Unchanged from the 1 × 6 layout.
    - **`lna_chain`:** done (2026-10-09), folded as a U for the tile: **145.36 × 70.47 µm**, R180 at (13.14, 6.5), input section over ua[0] / ua[1], stages 3–6 back across a 14 µm guard-ring moat. Clean. Extracted late-stage → input coupling 0 aF. Stable at tt / ss 10 °C, with gain 0.44 / 0.47 dB below the straight chain (the o2 turn). Details in `docs/layout.md` "lna_chain".

**Re-verified (2026-10-08 evening): rdeg 2 MΩ, decap blocks, chain stability.** Details in docs/history.md, "Re-verify: rdeg 2 MΩ, decaps, chain stability".
- Trim step at the operating point (DAC 0.8–1.2 V) is **0.062–0.076 mV/LSB at all corners, 10–50 °C**. e2e at −94 dBm: tt 11/12, fs 50 °C 8/12, ff 50 °C 10/12; −92 dBm 12/12.
- Decaps: **50.06 pF** (VAPWR) and **29.9 pF** (VDPWR), flat to 434 MHz and over ±10 % supply.
- `tb_radio_analog`: unchanged. Mixed-signal −94 dBm (real servo loop) still detects the burst. Bias OTA loop: PM ~90° at all corners. R/C corners: trim step 0.056–0.085 mV/LSB.
- **Chain layout rule:** keep chain output → input coupling (pad or stage-2 input) **≤ 0.1 fF** asymmetric. At the highest-gain corner (ss 10 °C, 81 dB), 0.2 fF gives +2.8 dB of peaking near 600 MHz and **0.5 fF oscillates** (1 fF at tt). Supply/ground L up to 5 nH with the 30 pF decap is fine.

**Next steps, in order:**
1. **Power fixes** (Matt to pick from `docs/power.md` "Proposals": 1 must (west VAPWR strap ≥ 4–6 µm, EM), 2 + 3 for RX R, 5 for the TX), then re-run `check_top.sh` and the power mesh.
   **Open RX runs on the extracted tile** (Matt, on the faster machine, after the power changes): the tile joined run (`sim/top/tb_tile_joined.py`, 10+ h) and mixed `--pex`; see `docs/verification.md` "Open items". Antenna: 7 violations inside the macro (same as before the TX move).
   Open from the top level (Matt): tx_p's 2 µm neck through the chain; decap 43 pF VAPWR / 11 pF VDPWR as laid out (xdecd part 4 dropped, top of xdeca part 1 MOS only); sc_phi 10–20 µm from avg / comp inputs; det / lpf not shielded yet.
2. Open (Matt): **ring inverter count**: the folded `tx_ring` runs ~459 MHz on silicon (+5.8 %), 24 inverters would give ~422 MHz (`NINV` in `xschem/gen/tx.py` and `layout/gen/tx_ring.py`, then `tb_tx_ring --pex` and `tb_tx`). Not blocking: overload recovery (key a −10 dBm tone), TX at 10/50 °C, the −90 dBm joined run, the macro's max-slew warnings (marginal, mostly ss).

**Parked:** 63-chip Gold code (e2e first), tnt's `rf_top` SRAM (if data mode needs buffers), dipole tuning (wait for real radios), wire-as-matching antenna idea, SDR bench tests (not needed).

## How to run things
- cocotb: `cd verilog/test && PATH=$HOME/work/asic-workshop/venv/bin:/usr/bin:/bin make` (~12 min); gate level: add `GL=1 SIM_BUILD=sim_build_gl COCOTB_RESULTS_FILE=results_gl.xml` (~35 min; the default netlist is `macros/radio_digital/radio_digital.nl.v`). On the Mac: `tools/osic-mac bash -c 'cd verilog/test && make COCOTB_CONFIG=cocotb-config ...'` (RTL ~8 min, GL ~17 min). Run it as `bash -c 'cd verilog/test && …'`: `make -C` breaks the Makefile's `$(PWD)`, and a backgrounded `cd` may not stick. With the login PATH, oss-cad-suite's python (no numpy) gets picked up and the run dies at import. `COCOTB_TEST_FILTER` takes one test name (a `|` alternative matched nothing).
- Generators: `python3 xschem/gen/<x>.py`. Netlist: `tools/osic bash -c 'xschem -n -s -q -o build xschem/<tb>.sch'` (grep the netlist for `IS MISSING`).
- Simulate in `build/` via `tools/osic`. Analysis/plots: `~/work/asic-workshop/venv/bin/python` (system python has no numpy).
- `tools/osic` copies the tracked root `.spiceinit` into `build/` each run.
- **Don't run ngspice processes in parallel** (each uses 8 threads), and **don't edit a script while it's running**.
- **All the xschem/ngspice traps and speed lessons are in `docs/sim_learnings.md`.** Read that before writing a new testbench.
- **On Matt's Mac** (repo at /Users/mattvenn/asic/ook-asic-radio): `tools/osic` only works on the Linux host. Use `tools/osic-mac <cmd>` instead (same image, sky130A via `~/asic/.designinit`). The sim scripts take `OSIC=$PWD/tools/osic-mac`.
