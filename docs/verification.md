# Testing and verification

How we check that the chip does what [how_it_works.md](how_it_works.md) says. Every check traces back to one reference, the bit-exact Python model in [`model/`](../model).

```
model (Python) ──vectors──► RTL ──► gate level ──► mixed signal (RTL + transistor-level analog)
                                                          ▲
schematic blocks ──► per-block tests (schematic vs layout) ┘──► system level (joined RX, TX, extracted tile)
```

## Digital

### Reference model
[`model/radio.py`](../model/radio.py) is the TX and RX digital written as plain Python, bit for bit. [`model/export_vectors.py`](../model/export_vectors.py) runs it on 9 RX scenarios (clean, weak, strong, fading, bursty interferer, wrong code, no signal, two sends, holdoff) plus the TX code table. It records the comparator bits it saw and everything the digital must output: trim codes, detection events and LED toggles. The format and timing contract are in [vectors/README.md](../verilog/test/vectors/README.md).

### RTL
The cocotb tests in [`verilog/test/test_radio.py`](../verilog/test/test_radio.py) run on Icarus:
- **RX:** each scenario replays the model's comparator bits into the RTL. Every trim code, event and toggle must match the model exactly, sample for sample.
- **TX:** each code's chip sequence and the 3-burst timing; a code change triggers a send.
- **Straps and modes:** raw TX and raw RX, monopole fallback, the debug switch, and the switched-capacitor clock phases.

Result: **15/15 pass**. Run with `cd verilog/test && make`.

### Gate level (GL)
The same 15 tests run on the hardened netlist ([`macros/radio_digital/`](../macros/radio_digital)) with `make GL=1`. This checks that synthesis, clock gating and place and route didn't change the behaviour. Result: **15/15 pass**.

LibreLane signoff ([`openlane/radio_digital`](../openlane/radio_digital)) is clean: DRC, LVS, antenna, and timing at all corners.

## Analog, per block

Each block has its own small testbench (`tb_<block>`). It applies an ideal stimulus with the block's real load and measures only what that block has to do. Each one runs twice: on the **schematic**, and on the **extracted layout** (the layout's transistors plus the resistance and capacitance of its wiring). The layout passes if it is close enough to the schematic.

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
| `tx_ls` | [tb_tx_ls](../sim/tx/tb_tx_ls.py) | edges, delay, arm duty 39 / 44 % (schematic 44 / 48 %) |
| `tx_drv` | [tb_tx_drv](../sim/tx/tb_tx_drv.py) | output power −0.32 dB |
| decaps | [decap_ac.sh](../sim/decap/decap_ac.sh) | capacitance flat to 434 MHz |

Every block layout is also DRC and LVS clean ([layout/check.sh](../layout/check.sh)).

**Corners:** [sim/corners/rx_corners.sh](../sim/corners/rx_corners.sh) runs the RX blocks at all 5 process corners and 10–50 °C. The worst corner (fs 50 °C) still decodes −92 dBm, which sets the worst-case sensitivity spec.

## Mixed signal
[`sim/mixed/`](../sim/mixed) compiles the RTL with Verilator and runs it inside ngspice, next to the transistor-level `lpf_rc`, `avg_sc`, `comp_ct` and `r2r`. This closes the real trim-servo loop: digital → DAC → comparator → digital. The test checks the bus order end to end, then runs a −94 dBm burst. The servo settles, dithers by about ±8 codes, and the burst is detected ([plot](../sim/plots/mixed_-94.png)).

## System level
- **Joined RX** ([sim/rx/joined.sh](../sim/rx/joined.sh)): the whole receiver at transistor level, antenna to comparator, with RF noise. It matches the block-by-block model ([plot](../sim/plots/rx_joined.png)).
- **TX** ([sim/tx/tb_tx.py](../sim/tx/tb_tx.py)): ring to dipole, giving +3.7…+3.9 dBm at every corner, and both arms low when off.
- **Analog top** ([xschem/tb_radio_analog.sch](../xschem/tb_radio_analog.sch)): every analog block together: RX operating point and supply current, all-off current, detector at −60 dBm, and the TX.
- **Extracted tile** ([sim/top/tb_tile.py](../sim/top/tb_tile.py)): `tb_radio_analog` on the routed tile's extraction ([layout/pex_tile.sh](../layout/pex_tile.sh)). RX currents and detector levels match the schematic. **Open:** with wiring capacitance included, two DC levels move and the TX loses 1.7 dB. This is being worked on ([handoff_sim.md](handoff_sim.md)).
- **Power delivery** ([sim/power/](../sim/power)): supply resistance, IR drop, and coupling from the TX into the RX supplies on the routed tile ([power.md](power.md)).
- **Tile checks** ([layout/check_top.sh](../layout/check_top.sh)): magic and KLayout DRC 0, LVS "Circuits match uniquely", TT power-pin precheck pass. The GitHub actions ([.github/workflows](../.github/workflows)) re-run the TT GDS, docs and LVS checks on every push.

## Not covered by simulation
- The pad and antenna model is rough, so absolute noise figure and out-of-band rejection are estimates.
- Silicon speed: the ring frequency uses a ×0.866 correction measured on ttsky25b.
- Real-world interferers and indoor fading; these are only in the model.
