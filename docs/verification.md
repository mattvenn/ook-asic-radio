# Testing and verification

How we check that the chip does what [how_it_works.md](how_it_works.md) says. Every check traces back to one reference, the bit-exact Python model in [`model/`](../model).

**Last full run: 2026-10-11 on `main` @ 91786fa, results in [verify_2026-10-11.md](verify_2026-10-11.md).** Everything below was rerun and matches, except where noted.

```
model (Python) ──vectors──► RTL ──► gate level ──► mixed signal (RTL + transistor-level analog)
                                                          ▲
schematic blocks ──► per-block tests (schematic vs layout) ┘──► system level (joined RX, TX, extracted tile)
```

## Running the checks
- Everything runs from the repo root in the IIC-OSIC-TOOLS image: `tools/osic <cmd>` on the Linux host, `tools/osic-mac <cmd>` on the Mac. The Python runners call it themselves: set `OSIC=$PWD/tools/osic` (Linux) or `OSIC=$PWD/tools/osic-mac` (the default in most). Host-side analysis needs Python with numpy.
- Already inside the image (e.g. the sim-0 pod, no docker): `tools/osic` runs the command directly through `tools/osic-inimage`. sim-0 has 28 CPUs (2026-10-12): keep the threads of all running ngspice at ≤ 28 (check `/sys/fs/cgroup/cpu.max` on a new pod). **Extract with magic 8.3.642**: the 2026.09 image's 8.3.684 drops node-to-substrate C from `ext2spice` (`OSIC_MAGIC=<bin dir of 8.3.642>`).
- **One ngspice at a time** (each uses 8 threads), and keep the machine awake for the long runs (`systemd-inhibit` / `tools/longrun` on Linux, `caffeinate -i` on the Mac). Outputs go to `build/`.
- Before the extracted-tile runs, build and extract the tile (a few minutes):
  ```
  tools/osic klayout -b -r layout/gen/top.py && tools/osic python3 layout/gen/route.py   # build/top/
  tools/osic bash layout/check_top.sh            # precheck, KLayout + magic DRC, antenna, LVS (~6 min)
  tools/osic bash layout/pex_tile.sh c           # also: lvs, rc  -> layout/pex/radio_analog_<mode>.spice
  tools/osic bash layout/export_tt.sh            # gds/ + lef/ for the TT action (after any layout change)
  ```
- Rough run times: per-block tests minutes each; `tb_tile.py rc` ~1 h; mixed signal ~15 min per level; joined RX 10+ h per level.

## Digital

### Reference model
[`model/radio.py`](../model/radio.py) is the TX and RX digital written as plain Python, bit for bit. [`model/export_vectors.py`](../model/export_vectors.py) runs it on 9 RX scenarios (clean, weak, strong, fading, bursty interferer, wrong code, no signal, two sends, holdoff) plus the TX code table. It records the comparator bits it saw and everything the digital must output: trim codes, detection events and LED toggles. The format and timing contract are in [vectors/README.md](../verilog/test/vectors/README.md).

### RTL
The cocotb tests in [`verilog/test/test_radio.py`](../verilog/test/test_radio.py) run on Icarus:
- **RX:** each scenario replays the model's comparator bits into the RTL. Every trim code, event and toggle must match the model exactly, sample for sample.
- **TX:** each code's chip sequence and the 3-burst timing; a code change triggers a send.
- **Straps and modes:** raw TX and raw RX, monopole fallback, the debug switch, and the switched-capacitor clock phases.

Result: **15/15 pass**. Run with `cd verilog/test && make` (~12 min; on the Mac `tools/osic-mac bash -c 'cd verilog/test && make COCOTB_CONFIG=cocotb-config'`, ~8 min; STATUS.md "How to run things" has the PATH traps).

### Gate level (GL)
The same 15 tests run on the hardened netlist ([`macros/radio_digital/`](../macros/radio_digital)) with `make GL=1 SIM_BUILD=sim_build_gl COCOTB_RESULTS_FILE=results_gl.xml` (~35 min, ~17 on the Mac). This checks that synthesis, clock gating and place and route didn't change the behaviour. Result: **15/15 pass**.

LibreLane signoff ([`openlane/radio_digital`](../openlane/radio_digital)) is clean: DRC, LVS, antenna, and timing at all corners.

### Formal
[`formal/radio_digital.sby`](../formal/radio_digital.sby) (SymbiYosys, in the image) proves properties of the RTL
for all time, with every input free (straps, DIP code, comparator, `rst_n` at any moment) and only a reset in the
first clock assumed. The harness [`formal/fv_radio_digital.sv`](../formal/fv_radio_digital.sv) doesn't touch the RTL:
`fv_props` latches its own copy of the straps, and reaches internal signals through `connect -set` in the
.sby (Yosys has no hierarchical references). The four 127-bit chip registers are abstracted (free state), which
is sound here because no property depends on their contents.
- **TX / RX safety:** `rx_en` follows the role strap; the n arm is never on without the p arm; `dbg_en` only with
  the magic and debug strap; in code mode, `tx_en` is never high while `rx_en` is.
- **Correlator timing** (the assumptions in `rd_corr` / `rd_rx`): a chip window never ends while the popcount or
  the post-reset clear runs; `done` comes exactly 128 clocks after the window end and only then; a score never
  arrives in the clock an event closes.
- **Switched-cap clocks:** `sc_phi1` and `sc_phi2` never overlap, have ≥ 4 clocks with both low between them, and
  are off when `rx_en` is.

Result (2026-10-13): **all pass** (PDR, single-threaded: 13–45 min from run to run; 38 min without the abstraction). Each property group catches a deliberate
bug in a copy of the RTL: 2 dead clocks (dead-time assert), `tx_en_n` = `tx_en` ^ `se` (n-arm assert), the
popcount one clock longer (`done` timing) and the popcount never clearing `busy` (window end while busy). The
"score never arrives as an event closes" assert wasn't mutation-tested (a mutant would need a full burst).
Two findings:
- **Raw mode keys the TX in the RX role** (task `raw_rx`, an expected FAIL): with the magic strap, mode `01` and
  `ui_in[7]` = 0 (RX), `tx_en` = `uio_in[2]` while `rx_en` = 1.
  **Intended** (Matt, 2026-10-13): raw RX with TX keying is a loopback test, now described in docs/info.md. The `raw_rx`
  task stays as a record that the property doesn't hold in raw mode.
- **Dead time after a short reset:** if `sc_phi2` is high when a 1-clock reset arrives (at power-up the
  flops start random, or a very short `rst_n` pulse), reset clears it and `sc_phi1` rises 2 clocks later instead
  of ≥ 4. They still never overlap. The dead-time check is waived across a reset for that reason.

Run: `tools/osic bash -c 'cd formal && sby -f radio_digital.sby prove'` (and `raw_rx` for the counterexample trace,
`formal/radio_digital_raw_rx/engine_0/trace.vcd`).

### TT top level and pinout
- **Pinout check** ([`tools/check_pinout.py`](../tools/check_pinout.py)): its `PINOUT` table is the one statement of what each TT pin does. The script checks that `info.yaml`'s pinout labels match it. It checks that in the top schematic every `radio_digital` and `radio_analog` port lands on the expected net, including the digital ↔ analog nets, with `ena` and `ua[5..7]` unconnected. It also checks that the `radio_digital` symbol's pins are the macro's (GL netlist and LEF). It parses the schematic directly (labels on pins, no xschem), and `--xschem <netlist>` cross-checks that parse against xschem's netlist. It runs in the `lvs` GitHub action. Result (2026-10-12): OK, and it catches a swapped `ua[0]`/`ua[1]`, a reversed trim bus and a wrong `info.yaml` label. Run: `python3 tools/check_pinout.py`.
- **TT-level cocotb** ([`test/`](../test)): `tt_um_mattvenn_radio` with a wrapper generated from the top schematic (`check_pinout.py --verilog`, which also runs the check), the macro inside it and `radio_analog` as a stub. It runs `test_tx_codes`, `test_raw_and_straps` and `test_debug_strap` from `test_radio.py` through the TT pins, plus `test_uio_oe` (`uio_oe` is 0 in reset, then 1 on exactly the uio pins `PINOUT` marks as outputs). The macro ↔ analog signals are driven and read at the stub's ports, so they go through the schematic's wiring. Result (2026-10-12): **4/4 pass** RTL (~1 min) and GL (~2 min). Run: `cd test && make` and `make GL=1 SIM_BUILD=sim_build_gl COCOTB_RESULTS_FILE=results_gl.xml` (cell models from `$PDK_ROOT/sky130A`).

## Analog, per block

Each block has its own small testbench (`tb_<block>`). It applies an ideal stimulus with the block's real load and measures only what that block has to do. Each one runs twice: on the **schematic**, and on the **extracted layout** (the layout's transistors plus the resistance and capacitance of its wiring). The layout passes if it is close enough to the schematic.

Run: `python3 sim/<dir>/tb_<block>.py [--pex] [corner]` (no flag = schematic, `--pex` = the block's extraction in `layout/pex/<block>.spice`, made by `layout/pex.sh <block>`; corner default tt). The exceptions: `sim/chain/stability.sh` and `sim/decap/decap_ac.sh` run in the image from `build/` after netlisting their testbench (headers of the scripts), and `tb_tx_ls.py` takes `tx_ls` or `tx_ls_en`.

| Block | Test | Schematic vs extracted layout |
|---|---|---|
| `lna_chain` | [chain/stability.sh](../sim/chain/stability.sh), [tb_amp_dp](../sim/amp_dp/tb_amp_dp.py), [tb_amp_dpc](../sim/amp_dpc/tb_amp_dpc.py) | gain −0.44 dB from the U fold; stable at all corners; output-to-input coupling 0 aF |
| `log_det` / `det_cell` | [tb_log_det](../sim/logdet/tb_log_det.py), [tb_det_cell](../sim/det_cell/tb_det_cell.py) | idle 1.52 → 1.49 V (contact resistance); same slope at high level. In the chain, the block extraction loses 2.4 dB at −90 dBm against the schematic; the tile extraction doesn't (open, [verify_system_2.md](verify_system_2.md) 3.1) |
| `lpf_rc` | [tb_lpf_rc](../sim/lpf_rc/tb_lpf_rc.py) | −3 dB frequency, carrier ripple at 434 / 868 MHz, step response |
| `avg_sc` | [tb_avg_sc](../sim/avg_sc/tb_avg_sc.py) | τ 0.42 ms; clock-coupling offset ~0.15 mV |
| `comp_ct` | [tb_comp_ct](../sim/comp_ct/tb_comp_ct.py) | offset +0.56 mV; trim 0.066 mV/LSB |
| `r2r` | [tb_r2r](../sim/dac/tb_r2r.py) | error ≤ 0.02 LSB |
| `bias_gen` | [tb_bias_gen](../sim/bias/tb_bias_gen.py) | currents and vcm within 0.1 %, VDD 1.7–1.9 V, 10–50 °C |
| `dbg_tg` | [tb_dbg_tg](../sim/dbg_tg/tb_dbg_tg.py) | on resistance; off isolation from the pad into det |
| `tx_ring` | [tb_tx_ring](../sim/tx/tb_tx_ring.py) | 530 MHz extracted, ~459 MHz expected on silicon |
| `tx_ls` | [tb_tx_ls](../sim/tx/tb_tx_ls.py) | kn 14 / kp 8 (2026-10-10): A duty 43.4 → 36.4 %, arm duty 41.4 / 48.3 % (schematic 45.7 / 50.5 %) |
| `tx_drv` | [tb_tx_drv](../sim/tx/tb_tx_drv.py) | output power −0.32 dB |
| decaps | [decap_ac.sh](../sim/decap/decap_ac.sh) | capacitance flat to 434 MHz |

Every block layout is also DRC and LVS clean (`tools/osic bash layout/check.sh <block>`: magic DRC as the TT precheck runs it, antenna, KLayout DRC, LVS). Exception: checked on their own, `decap_vapwr_p1`–`p4` show magic hvi.5 flags (per-device hvi, not flattened). In the tile they are clean.

**Corners:** [sim/corners/rx_corners.sh](../sim/corners/rx_corners.sh) runs the RX blocks at all 5 process corners and 10–50 °C. The worst corner (fs 50 °C) still decodes −92 dBm, which sets the worst-case sensitivity spec. Run in the image from `build/` after netlisting `tb_chain`, `tb_logdet`, `tb_comp`: `CORNERS="tt ss ff sf fs" TEMPS="10 50" ../sim/corners/rx_corners.sh`, then `python3 sim/corners/rx_corners.py`.

## Mixed signal
[`sim/mixed/`](../sim/mixed) compiles the RTL with Verilator and runs it inside ngspice, next to the transistor-level `lpf_rc`, `avg_sc`, `comp_ct` and `r2r`. This closes the real trim-servo loop: digital → DAC → comparator → digital. The test checks the bus order end to end, then runs a −94 dBm burst. The servo settles, dithers by about ±8 codes, and the burst is detected at −92 dBm ([plot](../sim/plots/mixed_-92.png)) and on the extracted blocks at −94 and −92 dBm ([plot](../sim/plots/mixed_-92_pex.png)). −94 dBm on the schematic is at the edge: detected with the older ngspice, missed with ngspice 47 (2026-10-11), so quote −92 dBm.

The pin-order verdict (`plot_mixed.py`): rx_en high, first code 128, every settled ladder step exactly ±1 LSB, and at least one step per servo tick, −3. Extra ±1 steps are the comparator toggling near a clock edge; they are counted and reported, not failed (−94 dBm schematic, 2026-10-12: OK with 4 extra, 1173 steps for 1169 ticks). Swapping `trim_out[1]` and `trim_out[0]` in the −70 dBm deck gives 588 steps of ±2 and fails. The burst is still detected, so detection alone would not catch it.

Run: `tools/osic bash sim/mixed/build_so.sh` (verilates the RTL), `tools/osic bash -c 'xschem -n -s -q -o build/real xschem/tb_radio_analog.sch'` (the block subcircuits `gen_mixed.py` reads), `python3 sim/rx/gen_det.py -94 -70` (detector waveforms; it imports `bench/`, which needs `pyvisa`), `python3 sim/mixed/gen_mixed.py [--pex] -94`, then `ngspice -b mixed_-94.cir` in the image from `build/mixed`, and `python3 sim/mixed/plot_mixed.py -94`. `--pex` takes the four blocks from their extracted layouts (files `mixed_<level>_pex.*`).

## System level
- **Joined RX** ([sim/rx/joined.sh](../sim/rx/joined.sh)): the whole receiver at transistor level, antenna to comparator, with RF noise. It matches the block-by-block model ([plot](../sim/plots/rx_joined.png)). Run in the image from `build/` after netlisting `tb_logdet` and `tb_rx_bb`: `LEVELS="-90" TSTOP=400u ../sim/rx/joined.sh` (the −70 run took 14.3 h); plot `python3 sim/rx/plot_joined.py -90`. The −90 dBm run (2026-10-11) matches the model within ~0.5 dB. Its swing over only two chips is noisy (±0.5 mV 1σ), so read it per chip ([verify_2026-10-11.md](verify_2026-10-11.md)). The same deck at −10 dBm checks overload: the comparator follows the keying, and the averager takes ~1.3 ms to recover.
- **TX** ([sim/tx/tb_tx.py](../sim/tx/tb_tx.py)): ring to dipole, giving **+4.14…+4.26 dBm** at every corner with the tx_ls kn 14 / kp 8 sizing (2026-10-10; was +3.7…+3.9), +4.41…+4.55 at 10 °C and +3.75…+3.89 at 50 °C, ~0.4 dB less with the extracted driver, and both arms low when off. Run: `python3 sim/tx/tb_tx.py tt ss ff sf fs` (`--pex` swaps in the extracted tx_drv).
- **Analog top** ([xschem/tb_radio_analog.sch](../xschem/tb_radio_analog.sch)): every analog block together: RX operating point and supply current, all-off current, detector at −60 dBm, and the TX.
- **Extracted tile** ([sim/top/tb_tile.py](../sim/top/tb_tile.py)): `tb_radio_analog` on the routed tile's extraction ([layout/pex_tile.sh](../layout/pex_tile.sh)). With full RC on the power-fix layout (2026-10-11): RX 2.985 mA, all off 0.910 µA, det / lpf idle 1.491 V, det at −60 dBm 1.206 V (schematic 1.206), TX **+3.13 dBm** at 519 MHz (+3.47 / +2.67 dBm at 10 / 50 °C). The earlier c-mode DC shifts were a failed operating point (unconnected pin stubs; the runner now ties them off), and the TX loss was the level shifter, now resized ([history.md](history.md) "Extracted-tile sims"). Run: `python3 sim/top/tb_tile.py sch lvs c rc` (one per mode, rc ~1 h).
  - **TX split** ([sim/top/tb_tile_tx.py](../sim/top/tb_tile_tx.py)): the TX transient alone, with extracted C dropped or kept per net, extra C, scaled devices, or kn / kp / corner / temperature changes, e.g. `python3 sim/top/tb_tile_tx.py c 'c:drop=tx_top_0\.(a|b)'`.
  - **Joined RX on the extracted tile** ([sim/top/tb_tile_joined.py](../sim/top/tb_tile_joined.py)): the joined RX stimulus into the whole extracted tile (c mode), trim held at the comparator's switching code. `python3 sim/top/tb_tile_joined.py scan`, then `run -90 400u <code>` (10+ h), `--no-run run -90` to analyse. On sim-0 this runs at ~2 µs/h (~8 days for 400 µs), so 2026-10-11 used a 30 µs on/off pair at −92 dBm instead ([verify_2026-10-11.md](verify_2026-10-11.md)). That checks the signal level on the extracted tile, not detection. Run the pair with `python3 sim/top/tb_tile_joined.py pair -92 [30u] [code] [seed]`: two runs in parallel, ~15 h each, keyed on at 1 µs, with and without the signal, and the same RF noise: one numpy waveform both runs read through an XSPICE `filesource`, because ngspice 47 doesn't repeat trnoise between runs, seed or not ([sim_learnings.md](sim_learnings.md)). `--no-run pair -92` prints the det / LPF off − on table. Result on the rebuilt tile (2026-10-12, shared noise, code 117): det off − on **1.36 mV** over 2–30 µs, model 1.14 mV ([verify_system_2.md](verify_system_2.md)).
- **Power delivery** ([sim/power/](../sim/power)): supply resistance, IR drop, and coupling from the TX into the RX supplies on the routed tile ([power.md](power.md); commands in its "Re-running" section). Rerun 2026-10-11 on the final layout: R, IR, EM and |Z| match "After the fix". The keyed TX transient halved at the drivers (tx_drv_p 63 → 29 mV p-p), and the RX blocks see ≤ 0.22 mV at 434 MHz.
- **Tile checks** ([layout/check_top.sh](../layout/check_top.sh)): magic and KLayout DRC 0, LVS "Circuits match uniquely", TT power-pin precheck pass. **Open:** magic's antenna check reports 7 violations on gates inside the digital macro. The GitHub actions ([.github/workflows](../.github/workflows)) re-run the TT GDS, docs and LVS checks on every push.

## Supply and mismatch
[verify_supply_mc.md](verify_supply_mc.md) (2026-10-12) has the tables and run commands.
- **Supply:** `VDD=` / `OUT=` / `NT=` on `sim/corners/rx_corners.sh`, `--vdd=` / `--vapwr=` on `sim/tx/tb_tx.py`
  (and `--pex-ring` for the extracted ring), `--vdd= --vapwr= --corner= --temp=` on `sim/top/tb_tile.py`,
  `VSUP=` on `sim/chain/stability.sh`. RX and e2e pass at VDPWR 1.71–1.89 V, also with the real bias. The
  TX enable level shifter `tx_ls_en` fails at VDPWR 1.71 V / VAPWR 3.6 V (ss and fs, extracted). The extracted
  ring stays in the RX band, but ss at 1.71 V is at its bottom edge (332 MHz on silicon).
- **Mismatch:** `--mc N` on `sim/comp_ct/tb_comp_ct.py` and `sim/avg_sc/tb_avg_sc.py`, and
  `sim/chain/mc_chain.py`, with the PDK's `<corner>_mm` models. The comparator offset (sigma ~3 mV, mostly
  the pfet_lvt mirror) puts ~26 % of chips where the trim step is too coarse for −92 dBm: open at Gate 2.

## System on the extracted chip
[verify_system_2.md](verify_system_2.md) (2026-10-12/13) has the tables. **Sensitivity: −92 dBm at 10–50 °C, −90 dBm
for every chip and at 85 °C.**
- **CW sensitivity, extracted:** `python3 sim/chain/cw_drop.py [--blocks=… --levels=… --pex-only]` (block
  extractions, noise-free) and `OSIC=tools/osic NT=1 python3 sim/top/tb_tile.py --cw sch c rc` (whole tile). The
  tile is within 0.5 dB of the model; the block extractions are 2.4 dB lower (open: the two flows disagree).
- **Closed loop on the extracted chain:** `PEX=1 NT=2 ../sim/rx/joined.sh` from `build/`. Too slow (~10 000 s per
  simulated µs); not run to a burst.
- **Seeds:** `python3 sim/rx/gen_det.py --seed=N <lvl>`, `python3 sim/mixed/gen_mixed.py --seed=N [--pex] <lvl> <tstop>`,
  `python3 sim/mixed/plot_mixed.py <lvl>[_pex]_sN`. −92 dBm 5/5 on the schematic and on the extracted baseband.
- **Corners with real bias:** `BIAS=real OUT=… sim/corners/rx_corners.sh`; extracted tile at a corner:
  `OSIC=tools/osic NT=2 python3 sim/top/tb_tile.py --corner=ss --temp=10 rc`. At 85 °C ff, −92 dBm is 4/12 in e2e.
- **Overload:** `python3 sim/rx/gen_det.py --overload=<gap ms> -90` + `gen_mixed.py --tag=ov<gap> -90 <tstop>`
  (−10 dBm burst, then −90 dBm: detection dead time < 0.1 ms); `OSIC=tools/osic python3 sim/top/tb_pad_overload.py
  --dbm=6 sch` (pads clamp at ±0.59 V, everything recovers).
- **Power-up:** `OSIC=tools/osic NT=4 python3 sim/top/tb_powerup.py --ramp=10u|10m --corner= --temp= c`, and
  `--off` for one supply missing. Ready ~3 ms after `rx_en`; with VDPWR missing and VAPWR up, tx_p = tx_n = 3.3 V
  (open).

## Not covered by simulation
- The pad and antenna model is rough, so absolute noise figure and out-of-band rejection are estimates.
- Silicon speed: the ring frequency uses a ×0.845 correction measured on ttsky25b's blocks (×0.866 whole tile).
- Real-world interferers and indoor fading; these are only in the model.
