# Handoff: comparator trim redesign (finding 1), on sim-0

Prompt for a new session (written 2026-10-13 on the Linux host, where this ran out of CPU). Paste it as is.

---

Finding 1 of [verify_system_2.md](verify_system_2.md) is the biggest yield loss in the receiver: comparator mismatch
against a trim that is only fine on one side. Your job: **finish choosing a `comp_ct` trim design (options 2 + 3 of
[verify_supply_mc.md](verify_supply_mc.md) §2.2), stop at the decision gate for Matt, then implement it** if he picks
one. Commit and push to `main` as you go (small commits; other sessions push to `main` too).

## Read first
- `docs/agent_start.md`, `STATUS.md`, `docs/sim_learnings.md` (ngspice traps, **including the Monte Carlo seed
  trap added 2026-10-13**).
- [verify_supply_mc.md](verify_supply_mc.md) §2.2, "Rerun (2026-10-13)" and the options below it.
- [verify_system_2.md](verify_system_2.md) "Findings", row 1.

## sim-0
- New pod: `bash tools/pod_setup.sh`, then check `/sys/fs/cgroup/cpu.max` (28 CPUs expected). The threads of all
  running ngspice add up to ≤ 28. Everything here is small single-threaded decks, so `--jobs 24` is fine with
  nothing else running.
- Analysis Python with numpy: system `python3` on sim-0 (on the Linux host it was `~/work/asic-workshop/venv/bin/python`).
- Run long jobs in the background and end the turn, so Matt can keep talking. Don't edit a script while it runs.
- Timing: one Monte Carlo sample with `--step` is ~40 s on one core, so 200 samples at `--jobs 24` is ~6 min.
  `trim_curve.py` is ~1 min per curve.

## Where it stands

**The problem** (rerun 2026-10-13, 200 distinct samples, each chip's own step, 27 °C, CM 1.5 V):

| corner | offset σ | −92 dBm (step ≤ 0.19) | ≈ −90 dBm (0.19–0.43) | ≈ −88 dBm (> 0.43) | can't trim |
|---|---|---|---|---|---|
| tt | 3.17 mV | 70 % | 20 % | 10 % | 0 (2 at code > 242) |
| ss | 3.35 mV | 66 % | 24 % | 10 % | 1 |
| fs | 2.79 mV | 74 % | 17 % | 8 % | 0 |

e2e against the step (`model/e2e.py`, tt 27 °C, nominal supply; the table is in verify_supply_mc.md): ≤ 0.19 mV/LSB
holds −92 dBm 12/12; 0.30 → 9/12; 0.43 → −90 dBm 11/12; 0.57 → −90 dBm 8/12.

**Why** (`sim/comp_ct/trim_curve.py nom`): the trim pair's sources sit at vref − Vgs ≈ 0.30 V (vref = VDD/2 = 0.9 V)
and each Mta tail needs ~0.2 V. So below the balance point there is only ~0.1 V of DAC travel (~14 codes, ~1 mV)
before Mta_sb leaves saturation and M4 turns off: the step blows up to 0.5 mV/LSB. Above balance it is linear
(0.061 mV/LSB) up to ~1.65 V, where M4 meets its drain (d2). The nominal chip balances at 0.79 V (code 112),
so the fine-trim window around it is −0.4 / +8.0 mV: one-sided. Offsets past the low end trim coarsely
(sensitivity loss); past the top end they can't trim at all (deaf chip).

**Candidates** (`trim_curve.py`, tt, nominal devices). Window = threshold span with a flat step, around nominal:

| tag | command args | vref | step | nominal code | window |
|---|---|---|---|---|---|
| nom | (none) | 0.90 | 0.061 | 112 | −0.4 / +8.0 mV |
| vref13 | `LR1=76 LR2=196` | 1.30 | 0.061 | 182 | −3.8 / +4.6 |
| **c_r12 (A)** | `LR1=72 LR2=200 rdeg=1.2Meg W3=8 W4=8` | 1.32 | 0.094 | 178 | −7.3 / +6.1 |
| B_r10 (B) | `LR1=76 LR2=196 rdeg=1.0Meg W3=8 W4=8` | 1.29 | 0.110 | 174 | −8.6 / +7.6 |
| D_r10_v124 | `LR1=85 LR2=187 rdeg=1.0Meg W3=8 W4=8` | 1.24 | 0.110 | 166 | −7.4 / +8.3 |
| C_r10mir (B + option 1) | B's + `WP=8 LP=2` | 1.29 | 0.110 | 171 | as B; should cut σ |

W3 / W4 = 8 lowers the knee ~0.1 V, a smaller Rdeg widens the window in mV (and coarsens the step), vref centres it.
vref alone (option 2) only centres a ±4 mV window, about ±1.3σ: not enough.

**Monte Carlo of A at tt (200 samples, 197 parsed):** median step 0.094, **99 % ≤ 0.19 mV/LSB** (today 70 %), 1 % in
0.19–0.43, none > 0.43, offset σ 3.08 mV, **4 samples at code > 242**: close to the top (hard) end, look at these.
B and C were stopped part-way; nothing else has been run.

## Steps

**1. Get set up.** Pull. The `build/trim/` files from the Linux host aren't in git; regenerate the candidates
(one first on its own, it netlists comp_ct once):

    python3 sim/comp_ct/trim_curve.py nom
    python3 sim/comp_ct/trim_curve.py c_r12 LR1=72 LR2=200 rdeg=1.2Meg W3=8 W4=8 &
    python3 sim/comp_ct/trim_curve.py B_r10 LR1=76 LR2=196 rdeg=1.0Meg W3=8 W4=8 &
    python3 sim/comp_ct/trim_curve.py C_r10mir LR1=76 LR2=196 rdeg=1.0Meg W3=8 W4=8 WP=8 LP=2 &
    wait

Check `c_r12` prints the table above (threshold −21.831 mV at 0.20 V, 0.094 mV/LSB in the middle).

**2. vref the layout can make.** vref is a tap on one 32-segment Rr1+Rr2 string (`layout/gen/comp_ct.py`,
`rr.links[15]` today). The tap has to be a bottom link, which on today's layout means after an even number of
segments: **8 → 1.35 V, 10 → 1.24 V** (9 isn't there; confirm the parity in `PolyRes` before relying on it).
A's 1.32 V isn't buildable as is. Run A's Rdeg / W at both taps (`LR1=68 LR2=204` and `LR1=85 LR2=187`) and use
those, or change the segment count. Prefer the one with more room at the top end: a chip past the top is
deaf, a chip past the bottom is only less sensitive.

**3. Monte Carlo** of each buildable candidate (and B, C if they're still interesting), tt / ss / fs at 27 °C:

    COMP_SUB=build/trim/<tag>_sub.spice COMP_PRM="$(cat build/trim/<tag>_prm)" COMP_TAG=<tag> \
        python3 sim/comp_ct/tb_comp_ct.py --mc 200 --jobs 24 --step <corner>

Results in `build/mc/comp_<corner>_27_cm1.5_step_<tag>.txt` (offset, switching trim, step per sample; NaN = no
switching point). **Check for duplicate rows after every run** (the seed trap). Bin as the table above, plus
code > 242. Then the hard cases for the best one: ss 10 °C, fs 50 °C (`--temp`), and sf 10 °C at `--cm 1.45`.

**4. Supply.** Both benches have VDD fixed at 1.8 V (`VD VDD 0 1.8` in `tb_comp_ct.py` and `trim_curve.py`). vref
(a divider on VDD) and the top end (d2 + Vth) both move with VDPWR, so add a `--vdd` / `vdd=` option and run the
chosen candidate's curve and a Monte Carlo at 1.71 and 1.89 V. The R2R DAC also runs off VDPWR, so a DAC code
is a fraction of VDD: compare in codes, not volts.

**5. e2e** at the chosen design's step (median, and the 95th / 99th percentile from step 3):

    python3 model/e2e.py --nf 11 --brf 450e6 --slope 13.4 --offset-mv 1.26 --trim-mv <step> \
        --comp-noise-mv 0.3 --cases noise --levels -94 -92 -90 -88 --trials 12

and at the worst supply corner (fs 50 °C, 1.71 V: `--nf 12 --slope 11.8 --offset-mv 1.67`). Pass: −92 dBm
≥ 11/12 for ≥ 95 % of chips at every corner, and no chip past the top end at 4σ. The typical chip's step
goes from 0.077 to ~0.094–0.11 mV/LSB, so expect to lose some of −94 dBm: report how much.

**6. Report to Matt (gate).** One table: candidate, % of chips at −92 / −90 / −88 dBm per corner, can't-trim
count, typical-chip −94 dBm, and the layout change. Add it to verify_supply_mc.md §2.2. **Stop here** until Matt
picks one, or decides to keep today's design.

**7. Implement (only after the gate).**
- Schematic: `xschem/gen/comp.py`: `COMP_PARAMS` rdeg; M3 / M4 `W=2` → the new W (line ~84); Rr1 / Rr2 both use
  `lref` today, so split it (e.g. `lref1` / `lref2`) for the new vref. Also `xschem/gen/top.py` (`xcomp`) if
  it passes params. Regenerate, netlist, and check `tb_comp_ct.py` (no `COMP_SUB`) gives the chosen curve.
- Layout: `layout/gen/comp_ct.py`: `PARAMS` (rdeg; the `write_ref` call hardcodes `rdeg=2e6`), the trim
  halves in `trim()` (`dev('n', 1.0, 1.0, ...)`: each half is W/2, so 4.0 for W 8; it fits under the main
  pair's 5 µm fingers, so the row shouldn't get longer), and the vref tap (`rr.links[15]`). Footprint and
  pins (`PIN_X`, `PIN_Y`, `OUT_X`) must not change, so the floorplan doesn't either. Then
  `layout/check.sh comp_ct` (DRC / LVS), `layout/pex.sh comp_ct` with magic 8.3.642, and
  `tb_comp_ct.py --pex` against the schematic.
- RTL: the servo resets to code 128 (`verilog/rtl/rd_rx.v:59`). Leave it: changing it means re-hardening the
  macro. The new nominal is about code 166–178, so it adds ~40–50 ticks (~0.6 ms) of settling after reset.
  Check that with the mixed-signal deck (`gen_mixed.py`, burst at 1.5 ms: is the servo settled before it?).
- Then the rebuild: phase 4 of [plan_verify_gaps.md](plan_verify_gaps.md) (decap flatten 4.1 in the same
  rebuild, tile, `check_top.sh`, `export_tt.sh`, the GitHub precheck, and the full rerun 4.2).

## Also open from the same work
- `sim/avg_sc/tb_avg_sc.py --mc` and `sim/chain/mc_chain.py` still have the seed bug (all jobs draw the same
  samples). Port the fix from `tb_comp_ct.py` (one sample per ngspice run, its own `.options seed`) and rerun
  them. Their verdicts (both fine) are unlikely to change.
- The rest of the open list (extraction disagreement, `tx_ls_en`, TT supply tolerances) is in
  [verify_system_2.md](verify_system_2.md) "Findings". The cheapest is looking up TT's supply tolerances.
