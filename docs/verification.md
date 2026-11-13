# Testing and verification

How we check that the chip does what [how_it_works.md](how_it_works.md) says. Every check traces back to one reference, the bit-exact Python model in [`model/`](../model).

**Last full run: 2026-11-04/05 on branch `lna-lo-shunt` (the LNA low-gain strap; merged to `main` as PR #1), results in [verify_lna_lo.md](verify_lna_lo.md), follow-ups 2026-11-06; run it with `sim/rerun/sched.py sim/rerun/jobs_lna_lo.py` (the 2026-10-13 set plus the low-gain checks, ~31 h on sim-0). Previous: 2026-10-13/14 on `comp-trim` (H135 comparator), [verify_2026-10-13.md](verify_2026-10-13.md); 2026-10-11 on `main` @ 91786fa, [verify_2026-10-11.md](verify_2026-10-11.md).** Everything below was rerun and matches, except where noted.

```
model (Python) ──vectors──► RTL ──► gate level ──► mixed signal (RTL + transistor-level analog)
                                                          ▲
schematic blocks ──► per-block tests (schematic vs layout) ┘──► system level (joined RX, TX, extracted tile)
```

## Running the checks
- Everything runs from the repo root in the IIC-OSIC-TOOLS image: `tools/osic <cmd>` on the Linux host, `tools/osic-mac <cmd>` on the Mac. The Python runners call it themselves: set `OSIC=$PWD/tools/osic` (Linux) or `OSIC=$PWD/tools/osic-mac` (the default in most). Host-side analysis needs Python with numpy.
- Already inside the image (e.g. the sim-0 pod, no docker): `tools/osic` runs the command directly through `tools/osic-inimage`. sim-0 has 28 CPUs (2026-10-12): keep the threads of all running ngspice at ≤ 28 (check `/sys/fs/cgroup/cpu.max` on a new pod). **Extract with magic 8.3.642**: the 2026.09 image's 8.3.684 drops node-to-substrate C from `ext2spice` (`OSIC_MAGIC=<bin dir of 8.3.642>`).
- **On the Mac, one ngspice at a time** (each uses 8 threads; on sim-0 the ≤ 28-thread budget above applies), and keep the machine awake for the long runs (`systemd-inhibit` / `tools/longrun` on Linux, `caffeinate -i` on the Mac). Outputs go to `build/`.
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
- **Straps and modes:** raw TX and raw RX, monopole fallback, the debug switch, the LNA low-gain strap (`test_lna_lo_strap`: `lna_lo_n` low only with `uio[7:4]` = `1011` at reset), and the switched-capacitor clock phases.

Result (2026-11-05): **16/16 pass**. Run with `cd verilog/test && make` (~12 min; on the Mac `tools/osic-mac bash -c 'cd verilog/test && make COCOTB_CONFIG=cocotb-config'`, ~8 min; STATUS.md "How to run things" has the PATH traps).

### Gate level (GL)
The same 16 tests run on the hardened netlist ([`macros/radio_digital/`](../macros/radio_digital)) with `make GL=1 SIM_BUILD=sim_build_gl COCOTB_RESULTS_FILE=results_gl.xml` (~35 min, ~17 on the Mac). This checks that synthesis, clock gating and place and route didn't change the behaviour. Result (2026-11-05): **16/16 pass**.

LibreLane signoff ([`openlane/radio_digital`](../openlane/radio_digital)) is clean: DRC, LVS, antenna, and timing at all corners.

### Formal
[`formal/radio_digital.sby`](../formal/radio_digital.sby) (SymbiYosys, in the image) proves properties of the RTL
for all time, with every input free (straps, DIP code, comparator, `rst_n` at any moment) and only a reset in the
first clock assumed. The harness [`formal/fv_radio_digital.sv`](../formal/fv_radio_digital.sv) doesn't touch the RTL:
`fv_props` latches its own copy of the straps, and reaches internal signals through `connect -set` in the
.sby (Yosys has no hierarchical references). The four 127-bit chip registers are abstracted (free state), which
is sound here because no property depends on their contents.
- **TX / RX safety:** `rx_en` follows the role strap; the n arm is never on without the p arm; `dbg_en` only with
  the magic (`uio[7:4]` = `1010` or `1011`) and debug strap; in code mode, `tx_en` is never high while `rx_en` is;
  `lna_lo_n` is low (low gain) exactly when `1011` was latched at reset.
- **Correlator timing** (the assumptions in `rd_corr` / `rd_rx`): a chip window never ends while the popcount or
  the post-reset clear runs; `done` comes exactly 128 clocks after the window end and only then; a score never
  arrives in the clock an event closes.
- **Switched-cap clocks:** `sc_phi1` and `sc_phi2` never overlap, have ≥ 4 clocks with both low between them, and
  are off when `rx_en` is.

Result (2026-10-13; 2026-11-05 with the low-gain property, 36 min): **all pass** (PDR, single-threaded: 13–45 min from run to run; 38 min without the abstraction). Each property group catches a deliberate
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

### Equivalence (eqy)
Gate-level simulation only shows that the netlist matches the RTL (register transfer level) for the stimulus the tests
give it. A logic equivalence check (LEC) proves it for every input. [`formal/eqy/`](../formal/eqy) uses eqy (Yosys'
equivalence checker) to prove that the RTL in `verilog/rtl/` and the shipped netlist
`macros/radio_digital/radio_digital.nl.v` (run `lnalo`) do the same thing, as recommended in Harald Pretl's design
review (`docs/review_harald_2026-11-13.md`, action 7).

Result (2026-11-13): **equivalent. 108/108 partitions proven, the clock check passes, and all four planted bugs are caught.**
The check takes about 3 s, and the whole script with the self-test about 15 s.
- **Gold** is the RTL read as LibreLane synthesis reads it: the same six files, no `SIM` (synthesis doesn't define it),
  so `rd_cg` instantiates the real `sky130_fd_sc_hd__dlclkp_1`. **Gate** is `nl.v` with the PDK's functional cell
  models (`sky130_fd_sc_hd.v`, `FUNCTIONAL`, no power pins). Yosys can't read the models' UDPs (user-defined primitives),
  so [`udp.v`](../formal/eqy/udp.v) has Verilog stand-ins for the three that are used (flop, latch, 2:1 mux), plus the
  tie cell's pullup / pulldown. Fill, tap, decap and diode cells are dropped.
- **Clock gates:** black-boxed on both sides ([`icg_bb.v`](../formal/eqy/icg_bb.v)). It's the same library cell,
  instantiated by name in the RTL, so eqy pairs the four instances by name and proves their inputs (`CLK`, `GATE` =
  `en0`…`en3`) equivalent. The latch inside is the same cell on both sides, so there is nothing to prove there.
- **Matching:** all **718 flops match by name** on both sides (508 chip-register bits, 210 others), **none by
  structure**. Synthesis didn't retime, merge or remove any register. The netlist names each bus bit as its own net
  (`\burst[1]`), so the gold's internal vectors are split the same way. [`match.py`](../formal/eqy/match.py) matches only ports,
  flop outputs and the clock gates. An internal combinational net would become a cut point, and a cut there gives
  false failures: `rx_en = ~role_tx` becomes a free input to the logic that reads it, while the netlist computes that
  logic from `role_tx`. For the same reason the six combinational outputs that are also read inside (`rx_en`, `tx_en`,
  `tx_en_n`, `lna_lo_n`, `uio_oe`, `uio_out`) are `amend`ed into the partitions that use them.
- **Strategy:** `sat` alone. Every partition proves at induction length 1, so each is combinational logic between matched
  registers. Nothing needed `sby` or a deeper induction, and no partition is left unproven.
- **Clocks:** eqy's strategies treat every flop as clocked by one implicit global clock, so they never look at
  which clock net a flop is on. [`clocks.py`](../formal/eqy/clocks.py) checks that separately. Each flop must be on
  the same source in the RTL and in the netlist: `clk` (210 flops, through the clock tree buffers) or the same
  clock gate (127 each). Result: 0 mismatched.
- **`pnl.v`** (with power pins): with the power pins stripped it is the same 6931 statements as `nl.v`
  ([`strip_pg.py`](../formal/eqy/strip_pg.py)), so the check covers it.

**Planted bugs** ([`plant.py`](../formal/eqy/plant.py), one text edit each on a copy of `nl.v`, all in `run.sh`):

| Bug | Edit | Result |
|---|---|---|
| `corr_and` | `or2` → `and2` in the chip registers' clock-gate enable (`clr \| …`) | caught, 3 s: `en0`…`en3` not equivalent (a counterexample), 6 downstream partitions unknown |
| `tx_mux` | the raw / code mux in front of `tx_en` with its inputs swapped | caught, 2 s: `tx_en` not equivalent |
| `acc_top` | the popcount's top bit `acc[6]` reads `acc[5]` | caught, 2 s: `u_corr.acc` unknown (induction fails at length 1) |
| `clk_swap` | chip-register flop `sr0[5]` on register 1's gated clock | **eqy passes it (108/108)**; the clock check catches it |

`acc_top` only matters once a rotation counts more than 64 matches, so a simulation needs a strong, well-aligned burst
to see it. eqy finds it in the same 2 s as the others, because every register is a cut point and the bug sits in the logic
between two of them. It shows up as "unknown" rather than "not equivalent": the base case runs only 5 clocks, not long
enough to reach a count of 64. The induction step gives two equal states that diverge in one clock, which is the bug.

**Versions:** eqy and Yosys 0.69 (image 2026.09). The macro was synthesised by LibreLane 3.0.3, most likely in image
2026.05 (`tools/osic`'s default when the `lnalo` run was made), which ships Yosys 0.65. That isn't recorded in the repo,
since the run folder wasn't kept. So the check doesn't run on the Yosys that synthesised the macro. Only Yosys' Verilog
reader and flatten touch the netlist here; the logic comes from the PDK's cell models.

**Not covered:** the cell models are the PDK's functional Verilog, so a wrong model (or a UDP stand-in that's wrong)
would go unseen. LVS ties the layout to `pnl.v`, and this ties `pnl.v` to the RTL. The clock gates' latch
behaviour and the clock tree's timing are STA's (static timing analysis) and GL simulation's job.

**CI:** the `eqy` GitHub action ([`.github/workflows/eqy.yaml`](../.github/workflows/eqy.yaml)) runs `run.sh` on
every push, with YosysHQ's oss-cad-suite (build 2026-09-30) and the `lvs` action's PDK cache. The check itself takes
about 15 s. After a re-harden, the edits in `plant.py` need updating: they name instances in the `lnalo` netlist, and
`plant.py` stops with an error if an edit doesn't match, so the action fails until they are updated.

**Image trap:** `/foss/tools/bin/eqy` is a symlink, and eqy looks for its Yosys plugins next to its own path, so it
fails with "Can't load module eqy_combine.so". `run.sh` calls it by its real path (`readlink -f`).

Run: `tools/osic bash formal/eqy/run.sh` (the check, `pnl.v` and the self-test; exit 0 if all pass; also the `eqy` action) or
`tools/osic bash formal/eqy/run.sh check` (only the check). Logs in `build/eqy/`.

### TT top level and pinout
- **Pinout check** ([`tools/check_pinout.py`](../tools/check_pinout.py)): its `PINOUT` table is the one statement of what each TT pin does. The script checks that `info.yaml`'s pinout labels match it. It checks that in the top schematic every `radio_digital` and `radio_analog` port lands on the expected net, including the digital ↔ analog nets, with `ena` and `ua[5..7]` unconnected. It also checks that the `radio_digital` symbol's pins are the macro's (GL netlist and LEF). It parses the schematic directly (labels on pins, no xschem), and `--xschem <netlist>` cross-checks that parse against xschem's netlist. It runs in the `lvs` GitHub action. Result (2026-10-12): OK, and it catches a swapped `ua[0]`/`ua[1]`, a reversed trim bus and a wrong `info.yaml` label. Run: `python3 tools/check_pinout.py`.
- **TT-level cocotb** ([`test/`](../test)): `tt_um_mattvenn_radio` with a wrapper generated from the top schematic (`check_pinout.py --verilog`, which also runs the check), the macro inside it and `radio_analog` as a stub. It runs `test_tx_codes`, `test_raw_and_straps`, `test_debug_strap` and `test_lna_lo_strap` from `test_radio.py` through the TT pins, plus `test_uio_oe` (`uio_oe` is 0 in reset, then 1 on exactly the uio pins `PINOUT` marks as outputs). The macro ↔ analog signals are driven and read at the stub's ports, so they go through the schematic's wiring. Result (2026-11-05): **5/5 pass** RTL (~1 min) and GL (~2 min). Run: `cd test && make` and `make GL=1 SIM_BUILD=sim_build_gl COCOTB_RESULTS_FILE=results_gl.xml` (cell models from `$PDK_ROOT/sky130A`).

## Analog, per block

Each block has its own small testbench (`tb_<block>`). It applies an ideal stimulus with the block's real load and measures only what that block has to do. Each one runs twice: on the **schematic**, and on the **extracted layout** (the layout's transistors plus the resistance and capacitance of its wiring). The layout passes if it is close enough to the schematic.

Run: `python3 sim/<dir>/tb_<block>.py [--pex] [corner]` (no flag = schematic, `--pex` = the block's extraction in `layout/pex/<block>.spice`, made by `layout/pex.sh <block>`; corner default tt). The exceptions: `sim/chain/stability.sh` and `sim/decap/decap_ac.sh` run in the image from `build/` after netlisting their testbench (headers of the scripts), and `tb_tx_ls.py` takes `tx_ls` or `tx_ls_en`.

| Block | Test | Schematic vs extracted layout |
|---|---|---|
| `lna_chain` | [chain/stability.sh](../sim/chain/stability.sh), [tb_amp_dp](../sim/amp_dp/tb_amp_dp.py), [tb_amp_dpc](../sim/amp_dpc/tb_amp_dpc.py) | **Stability (current):** with output-to-input coupling (`Ccpl`, asymmetric, 2 nH supply / ground, real decap) the extracted chain decays up to 0.5–0.75 fF at ss and 0.75–1 fF at tt / sf in full gain, and up to 1 fF at every corner with the low-gain strap on; the layout's own coupling is 0 aF (wires) and far below the 0.1 fF budget through the substrate. Kick test only: no small-signal margin yet ([review_harald_2026-11-13.md](review_harald_2026-11-13.md) action 4). History: gain −0.44 dB from the U fold; stable at all corners. Stability rerun 2026-10-17 with the real VDPWR decap (`decap_vdpwr` subckt, 10.6 pF; before, an ideal 30 pF): tt, ss 10 °C and ss 10 °C 1.89 V all decay (growth ≤ 3e-10) up to 0.1 fF, 1 fF rings (0.992–0.996), gain / peaks identical to 30 pF to 0.01 dB ([stability_2026-10-17.md](stability_2026-10-17.md)). **Low-gain strap** (`lna_shunt` across o2, 2026-11-05, [verify_lna_lo.md](verify_lna_lo.md)): full gain −0.25 dB schematic / ~−0.7 dB extracted from the shunt's C; step 11.9 dB tt, 10.1 dB sf on the full GDS extraction (block extraction 8.5–11.1 dB, `sim/chain/mc_chain.py` 1000 samples per corner, `sim/chain/lna_lo.sh`); with the strap on, the extracted chain stays stable up to 1 fF of output-to-input coupling at every corner (strap off: 0.5–0.75 fF at ss, 0.75–1 fF at tt and sf) |
| `log_det` / `det_cell` | [tb_log_det](../sim/logdet/tb_log_det.py), [tb_det_cell](../sim/det_cell/tb_det_cell.py) | idle 1.52 → 1.49 V (contact resistance); same slope at high level. In the chain, the block extraction loses 2.4 dB of det drop at −90 dBm against the schematic (~3.6 dB of chain gain at 434 MHz); the full GDS extraction (`layout/pex_tile.sh`) doesn't. Open ([verify_system_2.md](verify_system_2.md) finding #5); since 2026-11-06 resistance, devices, total C, bias and layout are ruled out, leaving how C is split between nets ([verify_lna_lo.md](verify_lna_lo.md) item 4 follow-up) |
| `lpf_rc` | [tb_lpf_rc](../sim/lpf_rc/tb_lpf_rc.py) | −3 dB frequency, carrier ripple at 434 / 868 MHz, step response |
| `avg_sc` | [tb_avg_sc](../sim/avg_sc/tb_avg_sc.py) | τ 0.42 ms; clock-coupling offset ~0.15 mV |
| `comp_ct` | [tb_comp_ct](../sim/comp_ct/tb_comp_ct.py) | H135 trim (2026-10-13), CM 1.0 V: balance code 184.1 (sch 183.9), trim 0.136 mV/LSB (sch 0.134); within 1 code / 1.2 % at all 5 corners |
| `r2r` | [tb_r2r](../sim/dac/tb_r2r.py) | error ≤ 0.02 LSB |
| `bias_gen` | [tb_bias_gen](../sim/bias/tb_bias_gen.py) | currents and vcm within 0.1 %, VDD 1.7–1.9 V, 10–50 °C. Noise ([bias_noise](../sim/bias/bias_noise.sh), 2026-11-07): 0.04 mV rms at the comparator (LPF − average, idle, all 5 corners at 27 °C), nearly all from the 2 µA `ib_det` mirror; with the detector's own 0.33 mV the total moves by < 0.003 mV (budget 0.5 mV) |
| `dbg_tg` | [tb_dbg_tg](../sim/dbg_tg/tb_dbg_tg.py) | on resistance; off isolation from the pad into det |
| `tx_ring` | [tb_tx_ring](../sim/tx/tb_tx_ring.py) | 530 MHz extracted, ~448 MHz expected on silicon (×0.845, the ttsky25b block factor; the tile rc 519 MHz × 0.866 gives the same) |
| `tx_ls` | [tb_tx_ls](../sim/tx/tb_tx_ls.py) | kn 14 / kp 8 (2026-10-10): A duty 43.4 → 36.4 %, arm duty 41.4 / 48.3 % (schematic 45.7 / 50.5 %) |
| `tx_drv` | [tb_tx_drv](../sim/tx/tb_tx_drv.py) | output power −0.32 dB |
| decaps | [decap_ac.sh](../sim/decap/decap_ac.sh) | as laid out (2026-10-17): VAPWR 42.6 pF, ESR 0.010 Ω; VDPWR 10.6 pF, ESR 0.18 Ω; flat to 434 MHz (planned 50 / 30 pF, reduced to fit) |

Every block layout is also DRC and LVS clean (`tools/osic bash layout/check.sh <block>`: magic DRC as the TT precheck runs it, antenna, KLayout DRC, LVS). The `decap_vapwr` parts are written flattened (since 2026-10-13, as the TX blocks), so they are clean on their own too, not only in the tile.

**Corners:** [sim/corners/rx_corners.sh](../sim/corners/rx_corners.sh) runs the RX blocks at all 5 process corners and 10–50 °C. The worst corner (fs 50 °C) still decodes −92 dBm, which sets the worst-case sensitivity spec. Run in the image from `build/` after netlisting `tb_chain`, `tb_logdet`, `tb_comp`: `CORNERS="tt ss ff sf fs" TEMPS="10 50" ../sim/corners/rx_corners.sh`, then `python3 sim/corners/rx_corners.py`.

## Mixed signal
[`sim/mixed/`](../sim/mixed) compiles the RTL with Verilator and runs it inside ngspice, next to the transistor-level `lpf_rc`, `avg_sc`, `comp_ct` and `r2r`. This closes the real trim-servo loop: digital → DAC → comparator → digital. The test checks the bus order end to end, then runs a −94 dBm burst. The servo settles, dithers by about ±8 codes, and the burst is detected at −92 dBm ([plot](../sim/plots/mixed_-92.png)) and on the extracted blocks at −94 and −92 dBm ([plot](../sim/plots/mixed_-92_pex.png)). −94 dBm on the schematic is at the edge: detected with the older ngspice, missed with ngspice 47 (2026-10-11), so quote −92 dBm.

Bench fixes (a903c95, 2026-11-05; [sim_learnings.md](sim_learnings.md)): one 0.9 V a2d threshold plus a d2a probe on `comp_in` (the d_cosim / adc_bridge lost slow comparator edges), and the LPF / avg `.ic` taken from the det waveform's level. Near threshold, one run is a coin flip: every run starts its burst at the same instant against the RTL's 4-of-8 sample phases. [`sim/mixed/replay_corr.py`](../sim/mixed/replay_corr.py) replays the RTL's slicer and correlator from a run's servo steps at all 8 alignments (matches the event pin 60/60); quote near-threshold detection averaged over burst timing ([verify_lna_lo.md](verify_lna_lo.md) item 5).

The pin-order verdict (`plot_mixed.py`): rx_en high, first code 128, every settled ladder step exactly ±1 LSB, and at least one step per servo tick, −3. Extra ±1 steps are the comparator toggling near a clock edge; they are counted and reported, not failed (−94 dBm schematic, 2026-10-12: OK with 4 extra, 1173 steps for 1169 ticks). Swapping `trim_out[1]` and `trim_out[0]` in the −70 dBm deck gives 586–588 steps of ±2 and fails. The burst is still detected, so detection alone would not catch it.

Run: `tools/osic bash sim/mixed/build_so.sh` (verilates the RTL), `tools/osic bash -c 'xschem -n -s -q -o build/real xschem/tb_radio_analog.sch'` (the block subcircuits `gen_mixed.py` reads), `python3 sim/rx/gen_det.py -94 -70` (detector waveforms; it imports `bench/`, which needs `pyvisa`), `python3 sim/mixed/gen_mixed.py [--pex] -94`, then `ngspice -b mixed_-94.cir` in the image from `build/mixed`, and `python3 sim/mixed/plot_mixed.py -94`. `--pex` takes the four blocks from their extracted layouts (files `mixed_<level>_pex.*`).

## System level
- **Joined RX** ([sim/rx/joined.sh](../sim/rx/joined.sh)): the whole receiver at transistor level, antenna to comparator, with RF noise. It matches the block-by-block model ([plot](../sim/plots/rx_joined.png)). Run in the image from `build/` after netlisting `tb_logdet` and `tb_rx_bb`: `LEVELS="-90" TSTOP=400u ../sim/rx/joined.sh` (the −70 run took 14.3 h); plot `python3 sim/rx/plot_joined.py -90`. The −90 dBm run (2026-10-11) matches the model within ~0.5 dB. Its swing over only two chips is noisy (±0.5 mV 1σ), so read it per chip ([verify_2026-10-11.md](verify_2026-10-11.md)). The same deck at −10 dBm checks overload: the comparator follows the keying, and the averager takes ~1.3 ms to recover.
- **TX** ([sim/tx/tb_tx.py](../sim/tx/tb_tx.py)): ring to dipole, giving **+4.14…+4.26 dBm** at every corner with the tx_ls kn 14 / kp 8 sizing (2026-10-10; was +3.7…+3.9), +4.41…+4.55 at 10 °C and +3.75…+3.89 at 50 °C, ~0.4 dB less with the extracted driver, and both arms low when off. Run: `python3 sim/tx/tb_tx.py tt ss ff sf fs` (`--pex` swaps in the extracted tx_drv).
- **Analog top** ([xschem/tb_radio_analog.sch](../xschem/tb_radio_analog.sch)): every analog block together: RX operating point and supply current, all-off current, detector at −60 dBm, and the TX.
- **Extracted tile** ([sim/top/tb_tile.py](../sim/top/tb_tile.py)): `tb_radio_analog` on the routed tile's extraction ([layout/pex_tile.sh](../layout/pex_tile.sh)). With full RC on the power-fix layout (2026-10-11): RX 2.985 mA, all off 0.910 µA, det / lpf idle 1.491 V, det at −60 dBm 1.206 V (schematic 1.206), TX **+3.13 dBm** at 519 MHz (+3.47 / +2.67 dBm at 10 / 50 °C). Rerun 2026-11-05 with the low-gain shunt: identical except det at −60 dBm 1.214 V (+8 mV, the shunt's ~0.7 dB); with the strap on (`--vglo=0`, c mode) 1.349 V and the same RX current. The earlier c-mode DC shifts were a failed operating point (unconnected pin stubs; the runner now ties them off), and the TX loss was the level shifter, now resized ([history.md](history.md) "Extracted-tile sims"). Run: `python3 sim/top/tb_tile.py sch lvs c rc` (one per mode, rc ~1 h).
  - **TX split** ([sim/top/tb_tile_tx.py](../sim/top/tb_tile_tx.py)): the TX transient alone, with extracted C dropped or kept per net, extra C, scaled devices, or kn / kp / corner / temperature changes, e.g. `python3 sim/top/tb_tile_tx.py c 'c:drop=tx_top_0\.(a|b)'`.
  - **Joined RX on the extracted tile** ([sim/top/tb_tile_joined.py](../sim/top/tb_tile_joined.py)): the joined RX stimulus into the whole extracted tile (c mode), trim held at the comparator's switching code. `python3 sim/top/tb_tile_joined.py scan`, then `run -90 400u <code>` (10+ h), `--no-run run -90` to analyse. On sim-0 this runs at ~2 µs/h (~8 days for 400 µs), so 2026-10-11 used a 30 µs on/off pair at −92 dBm instead ([verify_2026-10-11.md](verify_2026-10-11.md)). That checks the signal level on the extracted tile, not detection. Run the pair with `python3 sim/top/tb_tile_joined.py pair -92 [30u] [code] [seed]`: two runs in parallel, ~15 h each, keyed on at 1 µs, with and without the signal, and the same RF noise: one numpy waveform both runs read through an XSPICE `filesource`, because ngspice 47 doesn't repeat trnoise between runs, seed or not ([sim_learnings.md](sim_learnings.md)). `--no-run pair -92` prints the det / LPF off − on table. Result on the rebuilt tile (2026-10-12, shared noise, code 117): det off − on **1.36 mV** over 2–30 µs, model 1.14 mV ([verify_system_2.md](verify_system_2.md)); 2026-11-05 with the shunt 1.35 mV, and with the strap on at −88 dBm 0.54 mV.
- **Power delivery** ([sim/power/](../sim/power)): supply resistance, IR drop, and coupling from the TX into the RX supplies on the routed tile ([power.md](power.md); commands in its "Re-running" section). Rerun 2026-10-11 on the final layout: R, IR, EM and |Z| match "After the fix". The keyed TX transient halved at the drivers (tx_drv_p 63 → 29 mV p-p), and the RX blocks see ≤ 0.22 mV at 434 MHz. Since the router's via arrays (82b6462; rerun 2026-11-05) the chain's supply R is 2.92 / 4.40 Ω (VDPWR / VGND, was 5.70 / 6.96), TX → RX coupling 0.019–0.021 Ω at 434 MHz (was 0.015–0.069), RX dd ripple 6.0–6.2 mV p-p (was 7.4–7.7).
- **Tile checks** ([layout/check_top.sh](../layout/check_top.sh)): magic and KLayout DRC 0, LVS "Circuits match uniquely" with no property errors (the script and the `lvs` action fail on any "property errors" in the report: netgen still prints the match line when W / L / m differ, with "Property errors were found" for the top cell or "had property errors" for a subcell). The schematic side is the top-level xschem netlist alone, each block elaborated with its instance parameters (`layout/lvs_top_src.py`), so a parameter changed in the schematic but not in the layout fails (checked 2026-10-17: comp_ct `w1` 20 → 24 gives an 18 % W property error). `layout/ref/` is only the per-block checks' reference. Until 2026-10-17 the tile LVS used it too: the decaps were then compared against the layout generator's own list, and every block against its generator's copy of the parameters. **Open:** magic's antenna check reports 7 violations on gates inside the digital macro. The GitHub actions ([.github/workflows](../.github/workflows)) re-run the TT GDS, docs and LVS checks on every push.

## Supply and mismatch
[verify_supply_mc.md](verify_supply_mc.md) (2026-10-12) has the tables and run commands.
- **Supply:** `VDD=` / `OUT=` / `NT=` on `sim/corners/rx_corners.sh`, `--vdd=` / `--vapwr=` on `sim/tx/tb_tx.py`
  (and `--pex-ring` for the extracted ring), `--vdd= --vapwr= --corner= --temp=` on `sim/top/tb_tile.py`,
  `VSUP=` on `sim/chain/stability.sh`. RX and e2e pass at VDPWR 1.71–1.89 V, also with the real bias. The
  TX enable level shifter `tx_ls_en` fails at VDPWR 1.71 V / VAPWR 3.6 V (ss and fs, extracted). The extracted
  ring stays in the RX band, but ss at 1.71 V is at its bottom edge (332 MHz on silicon).
- **Mismatch:** `--mc N` on `sim/comp_ct/tb_comp_ct.py` and `sim/avg_sc/tb_avg_sc.py`, and
  `sim/chain/mc_chain.py`, with the PDK's `<corner>_mm` models. The comparator offset (sigma ~3 mV, mostly
  the pfet_lvt mirror) put 26–34 % of chips where the trim step was too coarse for −92 dBm, 8–10 % at about
  −88 dBm (`tb_comp_ct.py --mc 200 --step`, rerun 2026-10-13). Fixed by the H135 trim redesign (2026-10-13,
  [verify_supply_mc.md](verify_supply_mc.md) 2.2): ≥ 99 % of chips at −92 dBm at every 1.8 V corner, offset σ
  2.2–3.1 mV.

## System on the extracted chip
[verify_system_2.md](verify_system_2.md) (2026-10-12/13) has the tables. **Sensitivity: −92 dBm at 10–50 °C, −90 dBm
for every chip and at 85 °C.** With the low-gain strap: reliable at ≈ −86 dBm, 50 % at ≈ −89 dBm (averaged over burst timing,
[verify_lna_lo.md](verify_lna_lo.md) item 5).
- **CW sensitivity, extracted:** `python3 sim/chain/cw_drop.py [--blocks=… --levels=… --pex-only]` (block
  extractions, noise-free) and `OSIC=tools/osic NT=1 python3 sim/top/tb_tile.py --cw sch c rc` (whole tile, the full
  GDS extraction). It is within 0.5 dB of the model; the block extractions are 2.4 dB lower (open, finding #5: the two flows disagree).
- **Closed loop on the extracted chain:** `PEX=1 NT=2 ../sim/rx/joined.sh` from `build/`. Too slow (~10 000 s per
  simulated µs); not run to a burst.
- **Seeds:** `python3 sim/rx/gen_det.py --seed=N <lvl>`, `python3 sim/mixed/gen_mixed.py --seed=N [--pex] <lvl> <tstop>`,
  `python3 sim/mixed/plot_mixed.py <lvl>[_pex]_sN`. −92 dBm 5/5 on the schematic and on the extracted baseband.
- **Corners with real bias:** `BIAS=real OUT=… sim/corners/rx_corners.sh`; extracted tile at a corner:
  `OSIC=tools/osic NT=2 python3 sim/top/tb_tile.py --corner=ss --temp=10 rc`. At 85 °C ff, −92 dBm is 4/12 in e2e.
- **Overload:** `python3 sim/rx/gen_det.py --overload=<gap ms> -90` + `gen_mixed.py --tag=ov<gap> -90 <tstop>`
  (−10 dBm burst, then −90 dBm: no dead time, but ~2–3 dB desensitisation for ~1 ms, back to normal by ~5 ms; read it with `sim/mixed/replay_corr.py`, not one run's event pin: finding #13, restated 2026-11-06 in [verify_lna_lo.md](verify_lna_lo.md) item 2); `OSIC=tools/osic python3 sim/top/tb_pad_overload.py
  --dbm=6 sch` (pads clamp at ±0.59 V, everything recovers).
- **Power-up:** `OSIC=tools/osic NT=4 python3 sim/top/tb_powerup.py --ramp=10u|10m --corner= --temp= c`, and
  `--off` for one supply missing. Ready ~3 ms after `rx_en`; with VDPWR missing and VAPWR up, tx_p = tx_n = 3.3 V
  (open).

## Not covered by simulation
- The pad and antenna model is rough, so absolute noise figure and out-of-band rejection are estimates.
- Silicon speed: the ring frequency uses a ×0.845 correction measured on ttsky25b's blocks (×0.866 whole tile).
- Real-world interferers and indoor fading; these are only in the model.
