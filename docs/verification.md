# Testing and verification

How we check that the chip does what [how_it_works.md](how_it_works.md) says. Every check traces back to one reference, the bit-exact Python model in [`model/`](../model).

```
model (Python) ──vectors──► RTL ──► gate level ──► mixed signal (RTL + transistor-level analog)
                                                          ▲
schematic blocks ──► per-block tests (schematic vs layout) ┘──► system level (joined RX, TX, extracted tile)
```

## Running the checks
- Everything runs from the repo root in the IIC-OSIC-TOOLS image: `tools/osic <cmd>` on the Linux host, `tools/osic-mac <cmd>` on the Mac. The Python runners call it themselves: set `OSIC=$PWD/tools/osic` (Linux) or `OSIC=$PWD/tools/osic-mac` (the default in most). Host-side analysis needs Python with numpy.
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

## Analog, per block

Each block has its own small testbench (`tb_<block>`). It applies an ideal stimulus with the block's real load and measures only what that block has to do. Each one runs twice: on the **schematic**, and on the **extracted layout** (the layout's transistors plus the resistance and capacitance of its wiring). The layout passes if it is close enough to the schematic.

Run: `python3 sim/<dir>/tb_<block>.py [--pex] [corner]` (no flag = schematic, `--pex` = the block's extraction in `layout/pex/<block>.spice`, made by `layout/pex.sh <block>`; corner default tt). The exceptions: `sim/chain/stability.sh` and `sim/decap/decap_ac.sh` run in the image from `build/` after netlisting their testbench (headers of the scripts), and `tb_tx_ls.py` takes `tx_ls` or `tx_ls_en`.

| Block | Test | Schematic vs extracted layout |
|---|---|---|
| `lna_chain` | [chain/stability.sh](../sim/chain/stability.sh), [tb_amp_dp](../sim/amp_dp/tb_amp_dp.py), [tb_amp_dpc](../sim/amp_dpc/tb_amp_dpc.py) | gain −0.44 dB from the U fold; stable at all corners; output-to-input coupling 0 aF |
| `log_det` / `det_cell` | [tb_log_det](../sim/logdet/tb_log_det.py), [tb_det_cell](../sim/det_cell/tb_det_cell.py) | idle 1.52 → 1.49 V (contact resistance); same slope |
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

Every block layout is also DRC and LVS clean (`tools/osic bash layout/check.sh <block>`: magic DRC as the TT precheck runs it, antenna, KLayout DRC, LVS).

**Corners:** [sim/corners/rx_corners.sh](../sim/corners/rx_corners.sh) runs the RX blocks at all 5 process corners and 10–50 °C. The worst corner (fs 50 °C) still decodes −92 dBm, which sets the worst-case sensitivity spec. Run in the image from `build/` after netlisting `tb_chain`, `tb_logdet`, `tb_comp`: `CORNERS="tt ss ff sf fs" TEMPS="10 50" ../sim/corners/rx_corners.sh`, then `python3 sim/corners/rx_corners.py`.

## Mixed signal
[`sim/mixed/`](../sim/mixed) compiles the RTL with Verilator and runs it inside ngspice, next to the transistor-level `lpf_rc`, `avg_sc`, `comp_ct` and `r2r`. This closes the real trim-servo loop: digital → DAC → comparator → digital. The test checks the bus order end to end, then runs a −94 dBm burst. The servo settles, dithers by about ±8 codes, and the burst is detected ([plot](../sim/plots/mixed_-94.png)).

Run: `tools/osic bash sim/mixed/build_so.sh` (verilates the RTL), `python3 sim/rx/gen_det.py -94 -70` (detector waveforms; it imports `bench/`, which needs `pyvisa`), `python3 sim/mixed/gen_mixed.py [--pex] -94`, then `ngspice -b mixed_-94.cir` in the image from `build/mixed`, and `python3 sim/mixed/plot_mixed.py -94`. `--pex` takes the four blocks from their extracted layouts (files `mixed_<level>_pex.*`): **not run yet**.

## System level
- **Joined RX** ([sim/rx/joined.sh](../sim/rx/joined.sh)): the whole receiver at transistor level, antenna to comparator, with RF noise. It matches the block-by-block model ([plot](../sim/plots/rx_joined.png)). Run in the image from `build/` after netlisting `tb_logdet` and `tb_rx_bb`: `LEVELS="-90" TSTOP=400u ../sim/rx/joined.sh` (the −70 run took 14.3 h); plot `python3 sim/rx/plot_joined.py -90`.
- **TX** ([sim/tx/tb_tx.py](../sim/tx/tb_tx.py)): ring to dipole, giving **+4.14…+4.26 dBm** at every corner with the tx_ls kn 14 / kp 8 sizing (2026-10-10; was +3.7…+3.9), and both arms low when off. Run: `python3 sim/tx/tb_tx.py tt ss ff sf fs` (`--pex` swaps in the extracted tx_drv).
- **Analog top** ([xschem/tb_radio_analog.sch](../xschem/tb_radio_analog.sch)): every analog block together: RX operating point and supply current, all-off current, detector at −60 dBm, and the TX.
- **Extracted tile** ([sim/top/tb_tile.py](../sim/top/tb_tile.py)): `tb_radio_analog` on the routed tile's extraction ([layout/pex_tile.sh](../layout/pex_tile.sh)). With full RC (2026-10-10): RX 2.985 mA, all off 0.910 µA, det / lpf idle 1.491 V, det at −60 dBm 1.203 V (schematic 1.206), TX **+3.18 dBm** at 520 MHz. The earlier c-mode DC shifts were a failed operating point (unconnected pin stubs; the runner now ties them off), and the TX loss was the level shifter, now resized ([history.md](history.md) "Extracted-tile sims"). Run: `python3 sim/top/tb_tile.py sch lvs c rc` (one per mode, rc ~1 h).
  - **TX split** ([sim/top/tb_tile_tx.py](../sim/top/tb_tile_tx.py)): the TX transient alone, with extracted C dropped or kept per net, extra C, scaled devices, or kn / kp / corner / temperature changes, e.g. `python3 sim/top/tb_tile_tx.py c 'c:drop=tx_top_0\.(a|b)'`.
  - **Joined RX on the extracted tile** ([sim/top/tb_tile_joined.py](../sim/top/tb_tile_joined.py)): the joined RX stimulus into the whole extracted tile (c mode), trim held at the comparator's switching code. `python3 sim/top/tb_tile_joined.py scan`, then `run -90 400u <code>` (10+ h), `--no-run run -90` to analyse. **Not run yet.**
- **Power delivery** ([sim/power/](../sim/power)): supply resistance, IR drop, and coupling from the TX into the RX supplies on the routed tile ([power.md](power.md); commands in its "Re-running" section). Its TX results were taken before the TX corner was re-floorplanned (2026-10-10): rerun those.
- **Tile checks** ([layout/check_top.sh](../layout/check_top.sh)): magic and KLayout DRC 0, LVS "Circuits match uniquely", TT power-pin precheck pass. **Open:** magic's antenna check reports 7 violations on gates inside the digital macro. The GitHub actions ([.github/workflows](../.github/workflows)) re-run the TT GDS, docs and LVS checks on every push.

## Not covered by simulation
- The pad and antenna model is rough, so absolute noise figure and out-of-band rejection are estimates.
- Silicon speed: the ring frequency uses a ×0.866 correction measured on ttsky25b.
- Real-world interferers and indoor fading; these are only in the model.
