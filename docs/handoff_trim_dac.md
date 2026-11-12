# Handoff: trim DAC linearity (r2r driven by the macro's output buffers), on sim-0

Prompt for a new session (written 2026-11-12). Paste it as is.

---

Matt's scope capture of the reused R2R DAC on an earlier tapeout (`mattvenn/tt08-analog-r2r-dac-3v3`) shows a clean
staircase except at mid-scale, where the output **steps down**: non-monotonic at the 127 → 128 carry. This chip
reuses the same ladder layout (`layout/src/r2r/`, `xschem/gen/dac.py`) as the comparator's offset trim. Your job:
**find out whether that error is present here and whether it costs any sensitivity, then stop at the gate for
Matt.** The expected answer is "no action needed". **Avoid rebuilding the `radio_digital` macro**: any fix must
be on the analog side of the tile, or not done at all.

**Git: work on a branch, `trim-dac`** (`git switch -c trim-dac` from an up-to-date `main`). Commit there at the end
of each step. **Don't push and don't touch `main`** unless Matt asks. Other sessions keep pushing to `main`, so
rebase onto it before handing back.

## Read first
- `docs/agent_start.md`, `STATUS.md`, `docs/sim_learnings.md` (ngspice traps, **especially the Monte Carlo
  seed trap**).
- [slicer.md](slicer.md) (how the servo works), [verify_supply_mc.md](verify_supply_mc.md) §2.2 (H135, the trim
  window, code spread), `docs/layout.md` "r2r".
- `sim/dac/tb_r2r.py` (block bench), `sim/dac/ladder_model.py` (numpy model, below), `sim/mixed/gen_mixed.py`
  (RTL servo → real r2r → real comp_ct).

## sim-0
- New pod: `bash tools/pod_setup.sh`, then check `/sys/fs/cgroup/cpu.max` (28 CPUs expected). The threads of all
  running ngspice processes must add up to ≤ 28.
- Run long jobs in the background and end the turn, so Matt can keep talking. Don't edit a script while it runs.
- The DAC decks are tiny (resistors plus 8 cells). Only the mixed-signal runs are long (hours each, see
  [verify_system_2.md](verify_system_2.md)), so start those as early as you can.

## Where it stands (analysis 2026-11-12, no simulations yet)

**Which codes matter.** With H135, the nominal chip balances near **code 180** (184 extracted, CM 1.0 V). Offsets
spread that by σ ≈ 19 codes, so nearly every chip sits in **codes 140–255** (DAC 0.98–1.79 V). The 127 → 128 carry
is about 2.7σ below nominal. The other carries in the band are 159/160 (bit 5), 175/176, **191/192 (bit 6)**,
207/208 and 223/224.

**Likely cause: bit-driver resistance, not resistor mismatch.** Each bit's 2R leg is driven through a cell's
output resistance, but the termination 2R to VGND has no driver. So every bit is a little weak, and the MSB is the
weakest. That gives a *negative* DNL (output steps down) at 127/128, smaller ones at 63/64 and 191/192, and a
smooth staircase everywhere else, which matches the scope. Random mismatch of the unit resistors would give errors
of both signs at every carry. `python3 sim/dac/ladder_model.py`:

| driver R hi / lo | DNL 127→128 | 63→64 | 191→192 | 159→160 | codes overlapped at 128 |
|---|---|---|---|---|---|
| 0 (every sim so far) | 0 | 0 | 0 | 0 | 0 |
| 500 / 300 Ω | −1.5 LSB | −0.8 | −0.7 | −0.35 | 1 |
| 1.5 k / 800 Ω | −4.3 | −2.2 | −1.9 | −1.0 | 4 |
| 3 k / 1.5 k | −8.1 | −4.3 | −3.7 | −1.9 | 7 |

Unit-resistor mismatch with ideal drivers: at σ 0.2 %, the DNL σ is 0.23 LSB at 127/128 and 0.11 at 191/192. The
model only produces a gap (DNL > +0.5) somewhere in codes 140–230 for about 5 % of chips at σ 0.5 %, and 22 % at 1 %.

**What drives the bits here.** `trim_out[7:0]` are `sky130_fd_sc_hd__clkdlybuf4s25_1` output buffers
(`macros/radio_digital/radio_digital.nl.v:11335`), a weak delay buffer. Their output resistance hasn't been
measured; ~1 kΩ is a guess. `PL_RESIZER_BUFFER_OUTPUT_PORTS` is 0 in `openlane/radio_digital/config.tcl`, so these
cells come from the flow's IO buffering, not the resizer. **Every sim so far drives the ladder from ideal
sources**: `tb_r2r.py` uses ideal V sources, and `gen_mixed.py` uses XSPICE `dac_bridge`s with no output
resistance.

**Why it should be harmless:**
1. **The servo only cares about voltage.** It steps the code up while the comparator says 1 and down while it says
   0, so it settles where the voltage crosses the threshold, whichever code that takes. A downward step makes some
   voltages reachable from two codes (an overlap); it doesn't create a range the servo can't reach. The cost is a
   few extra 13 µs ticks while settling.
2. **Gaps would hurt; overlaps don't.** A *positive* DNL (a missing range of voltage) makes the code dither across
   a step larger than one LSB, and the e2e margin on the step is thin (0.142 mV fails at fs 50 °C vs H135's p95
   of 0.135). Driver resistance causes no gaps; only mismatch could.
3. **Comparator noise blurs it anyway.** The noise is ~0.45 mV rms, about 3.5 trim steps, so the code already
   wanders over several LSB.
4. **The usable range is unchanged.** The top code is still 1.79 V with driver resistance (1.7915 V at 1.5 k vs
   1.7930 V ideal), and the top end is where H135 is tight (+4σ = code 256). Mid-codes sag by ≤ 17 mV, which moves
   a chip's balance up only a few codes.

## Steps

**0. Pin down the silicon result** (ask Matt, no sim). Get these from Matt: how the bits were driven on the tt08
chip (TT `uo_out` through the mux? its 3.3 V level shifters?), what code range the capture covers, and how many
codes each step is. If `mattvenn/tt08-analog-r2r-dac-3v3` is useful, attach it with `add_repo`. Put the drive
resistance it implies into `ladder_model.py` and check that it gives the size of drop seen. If the drop can't be
explained by drive resistance, say so before going on: the cause would then be the ladder itself (mismatch or
layout), and step 3 becomes the main step.

**1. Measure the driver.** Write a small DC bench, `sim/dac/tb_drv.py`, for `sky130_fd_sc_hd__clkdlybuf4s25_1`
from `$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice`. Input tied high or low, with the
output sourcing or sinking 0–100 µA (the most a bit leg draws is 1.8 V / 21 kΩ ≈ 86 µA). Report R_hi and R_lo at
tt / ss / ff / sf / fs, at 10, 27, 50 and 85 °C. Also take the routed wire resistance from each macro pin to its
r2r `b_i` from the tile extraction, if it isn't negligible (it should be < 50 Ω).

**2. Block bench with real drivers.** Add `--drv` to `sim/dac/tb_r2r.py`. Drive each `b_i` through one
`clkdlybuf4s25_1` instance whose input comes from the ideal bit source, with the cells on the same 1.8 V and 0 V
rails as the ladder. Add a **full 256-code DC sweep** (one `op` per code; 256 small ops are seconds) and report:
INL / DNL per code, whether it's monotonic, the DNL at every carry in codes 120–255, V(255), and the overlap at
127/128. Run it on the schematic and `--pex`, at the step-1 corners. Check that the result matches
`ladder_model.py` given step 1's R_hi / R_lo; if it doesn't, find out why before going on.

**3. Monte Carlo of the ladder.** Run 200 samples of the step-2 bench with mismatch on (resistors and driver cells),
**distinct seeds** (sim_learnings). Report the DNL distribution and the share of chips with any gap (DNL > +0.5
LSB) in codes 120–255, at tt and at the worst corner from step 2. This is the only effect that could cost
sensitivity.

**4. Mixed-signal check at the bad carries.** Add `--drv` to `sim/mixed/gen_mixed.py`. Each `trim_out_i_a` bridge
output goes through a real `clkdlybuf4s25_1` (or, if XSPICE makes that awkward, a series resistor of step 1's
worst-case R_hi / R_lo, switched with the bit) before `xdac`. Add `--vos=<mV>`, a DC source in series with `inp`,
so the servo can be pushed to any code. Pick vos from `tb_comp_ct.py`'s trim curve so the chip balances **at code
127/128**, then do the same for **191/192**. At each, run −92 dBm with and without `--drv`, schematic first, plus
`--pex` for the 127/128 case. Compare detection, score, servo settle time and the code wander (from `v(trim)`).
Pass if detection and score match the ideal-driver run within seed-to-seed spread (run 2–3 `--seed`s if a single
run is borderline). These are the long jobs, so start them as soon as step 2 has numbers.

**5. Optional: e2e sweep.** Only if step 3 shows gaps in more than ~1 % of chips. Add `--dac-curve <json>` to
`model/e2e.py` so `radio.AfeModel`'s trim uses a measured code → voltage curve instead of a uniform step. Then
run −92 dBm at the worst corner with the worst-percentile curve from step 3.

**6. Report to Matt (gate).** One short table: driver R per corner; worst DNL at 127/128 and 191/192; the share of
chips with gaps; the mixed-signal result at 127/128 and 191/192 against ideal drivers. Then one of these
recommendations:
- **No action** (expected). Add a line to `STATUS.md` and to [verify_system_2.md](verify_system_2.md)
  "Findings", note the bring-up check below in [bringup.md](bringup.md), and stop.
- **Fix on the analog side, keeping the macro unchanged**, only if step 4 or 5 shows a real loss. Options, cheapest
  first; don't implement until Matt picks one:
  - **(a) Stronger re-drivers in the analog area.** Put 8 × `sky130_fd_sc_hd__buf_4` (or `inv_4` pairs) on VDPWR /
    VGND between the macro pins and r2r `b0..b7`. Model at ~150–250 Ω: DNL at 127/128 ≈ −0.5 LSB. This adds a
    small std-cell block in the gap between the macro and r2r, plus routing; it needs top-level DRC / LVS, the
    tile re-export and the mixed-signal reruns.
  - **(b) Match the termination.** Add a poly resistor equal to the average driver R in series with r2r's 2R
    termination to VGND. That cancels the *average* error but not the hi / lo difference or its spread across
    corners and temperature, so it's worse than (a) unless (a) won't fit.
  - Not an option: swapping the output buffer cells in the macro, which is a macro rebuild (Matt wants to avoid
    that).

## Bring-up check (for bringup.md, either way)
The servo can be frozen or its code set by register (slicer.md "Overrides"). On silicon, sweep the trim code
0–255 with the comparator inputs held fixed and record the comparator's 1s density per code. A non-monotonic carry
shows as a dip in the density curve. This measures the real DAC + comparator transfer on our chip, including any
driver effect, with no extra pins.

## Files you'll touch
- `sim/dac/tb_r2r.py` (`--drv`, full sweep), new `sim/dac/tb_drv.py`, `sim/dac/ladder_model.py` (fit to silicon).
- `sim/mixed/gen_mixed.py` (`--drv`, `--vos`), maybe `sim/mixed/plot_mixed.py` (code-wander plot).
- `model/e2e.py`, `model/radio.py` only for step 5.
- Results go in a new `docs/verify_trim_dac.md`; add a pointer to it in `STATUS.md`.
