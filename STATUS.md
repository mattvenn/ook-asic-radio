# Where we are (2026-11-22)

The "pick up from here" note: current state, what's open, how to run things. Keep it short and current: when an entry
here is superseded, move it to **docs/history.md** (newest section first). The log this file kept until 2026-11-21 is
there under "STATUS.md as it stood on 2026-11-21".
New agents: start with **docs/agent_start.md**. Decisions and their evidence: **PLAN.md**. Open items outside chip
design: **TODO.md**. Repo: github.com/mattvenn/ook-asic-radio (`main`, the only branch).

## The design

- **Tile:** 3x2 analog, 3.3 V (VAPWR) template (`layout/floorplan/tt_analog_3x2_3v3.def`), floorplan "RX in the
  corner" (2026-11-14). Pins: RX `ua[3]` / `ua[2]`, debug `ua[1]`, TX `ua[4]` / `ua[5]`, `ua[0]` a met4 stub
  (`analog_pins: 6`). `gds/` / `lef/` exported 2026-11-15: DRC 0 (magic + KLayout), LVS match, TT precheck pass,
  antenna 7 (all inside the digital macro).
- **RX:** pad → `rx_t` = the straight tall 6-stage NMOS diff-pair limiting chain (`lna_chain_t`, low-gain strap on
  stage 2, `uio[7:4]` = `1011` at reset) + the one-row log detector → 14 kHz RC LPF → switched-cap average →
  continuous comparator (H135 trim) with the trim from the R2R ladder driven by the RTL servo.
  [docs/tall_stages_2026-11.md](docs/tall_stages_2026-11.md), [docs/how_it_works.md](docs/how_it_works.md).
- **TX:** 22-inverter ring (~448 MHz predicted on silicon), level shifters, antiphase drivers from VAPWR; about
  +3 dBm extracted.
- **Digital:** `radio_digital`, clock-gated, hardened with LibreLane at 200 × 220 µm (`openlane/radio_digital/`,
  `macros/radio_digital/`). RTL and gate-level cocotb 16/16, formal and eqy pass.
- **Operating range:** 10–50 °C, supply 1.8 / 3.3 V.

## Where verification stands

- **Last full re-verification: [docs/verify_tall.md](docs/verify_tall.md)** (2026-11-15/17, 442 jobs, all pass
  or accepted). Two accepted findings (Matt, 2026-11-18): the extracted RX is ~2 dB less sensitive than the old U
  chain (less risk of oscillation is worth it), and the full − low gain step is 7.6 dB at sf (block extraction).
- **Sensitivity, full gain, tt:** −92 dBm is the quoted figure (95 % over burst timing on the schematic baseband,
  6/6 extracted, after the `SHIFT_DB` recalibration, 2026-11-21); −94 dBm is a best case. Low gain: 50 % at about
  −88.5 dBm.
- **Device noise in transient (Harald's review action 13, 2026-11-21): those numbers are probably ~1.5 dB
  optimistic** (up to ~2 dB with 1/f). Real NF is 11.6 dB thermal / 12.5 dB with 1/f, not ngspice's 11.0 (a NaN in
  the pad switch drops 1/f), and noise from inside the chain costs ~0.9 dB more than the same NF injected at the
  antenna. [docs/verify_tall.md](docs/verify_tall.md) §5 "Device noise in transient".
- **Comparator mismatch:** H135 trim gives −92 dBm for ≥ 99 % of chips at every 1.8 V corner
  ([docs/verify_supply_mc.md](docs/verify_supply_mc.md)).
- **Trim DAC drive:** accepted (Matt, 2026-11-12). If `radio_digital` is ever re-hardened, drive `trim_out[7:0]`
  with `buf_8` ([docs/verify_trim_dac.md](docs/verify_trim_dac.md)).
- Harald Pretl's design review: [docs/review_harald_2026-11-13.md](docs/review_harald_2026-11-13.md) "Where it
  stands".

## Open

1. **Recalibrate `gen_det.py` to device noise** and rerun the −92 / −94 dBm paired check, to get the sensitivity
   cost directly (TODO.md).
2. **TT submission:** mark the project as dangerous; RX adapter board; EM chamber booking (TODO.md).
3. **After any layout change:** `layout/export_tt.sh`, push, and the GitHub `gds` action (TT precheck) must pass.
4. Not blocking, from before the tall chain (check they still apply before acting): the macro's max-slew warnings
   (marginal, mostly ss); layout compromises for Matt to sign off (decap as laid out ~43 pF VAPWR / 11 pF VDPWR
   against 50 / 30 targets, `sc_phi` 10–20 µm from the avg / comp inputs, det / lpf not shielded).

**Parked:** 63-chip Gold code, tnt's `rf_top` SRAM (if data mode needs buffers), dipole tuning (wait for real
radios), wire-as-matching antenna, SDR bench tests, the tunable TX ring
([docs/archive/plan_ring_tune.md](docs/archive/plan_ring_tune.md)).

## Where the docs are

- [docs/how_it_works.md](docs/how_it_works.md): theory, specs, schematics, layout. [docs/verification.md](docs/verification.md):
  how to run every check. [docs/layout.md](docs/layout.md): layout flow, rules, per-block notes.
  [docs/sim_learnings.md](docs/sim_learnings.md): xschem / ngspice traps; read before writing a testbench.
- Verification reports, newest first: `verify_tall.md`, `verify_trim_dac.md`, `verify_lna_lo.md`,
  `verify_system_2.md`, `verify_supply_mc.md`; design notes `tall_stages_2026-11.md`, `stability_ac_2026-11.md`,
  `substrate_2026-10-29.md`, `stability_2026-10-17.md`, `power.md`.
- [docs/archive/](docs/archive/): finished handoffs, plans, the 2026-10-11 / 10-13 verification reports, and the
  session transcripts (`prompts.md`).

## How to run things
- **sim-0** (k8s pod inside the image, no docker): on a new pod run `bash tools/pod_setup.sh` first (git identity + push via `$GITHUB_TOKEN` from the pod spec, magic 8.3.642, pyvisa; prints the CPU quota). `tools/osic` / `tools/osic-mac` run commands directly via `tools/osic-inimage`; system `python3` has numpy and cocotb. The pod has 28 CPUs / 64 GB: **the threads of all running ngspice add up to ≤ 28** (tile-pex decks up to 3 at once at 8 threads; small decks single-threaded, up to ~24). Long batches: `sim/rerun/sched.py`. Check `/sys/fs/cgroup/cpu.max` on a new pod. Extract with magic 8.3.642: `OSIC_MAGIC=$HOME/.local/magic642/bin tools/osic bash layout/pex.sh <block>` (the image's 8.3.684 drops substrate C).
- cocotb: `cd verilog/test && PATH=$HOME/work/asic-workshop/venv/bin:/usr/bin:/bin make` (~12 min); gate level: add `GL=1 SIM_BUILD=sim_build_gl COCOTB_RESULTS_FILE=results_gl.xml` (~35 min; the default netlist is `macros/radio_digital/radio_digital.nl.v`). On the Mac: `tools/osic-mac bash -c 'cd verilog/test && make COCOTB_CONFIG=cocotb-config ...'` (RTL ~8 min, GL ~17 min). Run it as `bash -c 'cd verilog/test && …'`: `make -C` breaks the Makefile's `$(PWD)`, and a backgrounded `cd` may not stick. With the login PATH, oss-cad-suite's python (no numpy) gets picked up and the run dies at import. `COCOTB_TEST_FILTER` takes one test name (a `|` alternative matched nothing).
- Generators: `python3 xschem/gen/<x>.py`. Netlist: `tools/osic bash -c 'xschem -n -s -q -o build xschem/<tb>.sch'` (grep the netlist for `IS MISSING`).
- Simulate in `build/` via `tools/osic`. Analysis/plots: `~/work/asic-workshop/venv/bin/python` (system python has no numpy).
- `tools/osic` copies the tracked root `.spiceinit` into `build/` each run. ngspice reads `.spiceinit` from its working directory: a deck run anywhere else without a copy picks up `~/.spiceinit` (`ngbehavior=hsa` in the image), which changes results.
- **On Matt's Mac** (repo at /Users/mattvenn/asic/ook-asic-radio): `tools/osic` only works on the Linux host. Use `tools/osic-mac <cmd>` instead (same image, sky130A via `~/asic/.designinit`). The sim scripts take `OSIC=$PWD/tools/osic-mac`; two ngspice at once is fine there. **Don't edit a script while it's running.**
