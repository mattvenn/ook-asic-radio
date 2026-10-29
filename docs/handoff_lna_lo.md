# Handoff: verify the LNA low-gain strap (branch `lna-lo-shunt`)

Prompt for a verification session on the big computer (sim-0), written 2026-10-29 by the session that designed the strap on the Mac. Paste it as is.

---

Branch `lna-lo-shunt` adds a reset-strapped low-gain mode to the RX chain, a fallback in case the manufactured chain oscillates. The design, the layout, a re-hardened macro and a re-routed tile are done and checked on the Mac (below). Your job:
**run the full verification on this branch, compare against the reference numbers, and report.** Don't redesign. If something fails, find out why and report it with numbers, then stop for Matt. Commit results to the branch (small commits), not to `main`.

## Read first
- `docs/agent_start.md`, `STATUS.md`, `docs/sim_learnings.md` (ngspice traps), `docs/verification.md` (how every check runs, sim-0 notes: CPU quota, extract with magic 8.3.642).
- `docs/stability_2026-10-17.md` (the chain's stability bench) and `docs/substrate_2026-10-29.md` (coupling measured through the wires and the substrate).

## Setup
- `git fetch && git checkout lna-lo-shunt`. A fresh checkout needs the gitignored inputs (`docs/layout.md`, top): `build/pyold` (gdsfactory 8.5 for the pcells) and `mag/tt_analog_3x2_3v3.def`.
- The exported tile is in `gds/` + `lef/`. Its build output is `build/top/`: rebuild with `tools/osic klayout -b -r layout/gen/top.py && tools/osic python3 layout/gen/route.py` (~5 min).

## What changed (commits on the branch, oldest first)
1. **RTL** (`verilog/rtl/radio_digital.v`).
   - The strap magic is `uio[7:5]` = `101`, so `1010` or `1011`; both enable the existing straps.
   - `lna_lo` latches `magic & uio[4]` at reset release, so `1011` means low gain.
   - New output `lna_lo_n` (active low: 0 = low gain), 1 (full gain) out of reset.
   - cocotb `test_lna_lo_strap`: RTL 16/16 pass on the Mac. **GL not run.**
2. **Schematic** (`xschem/gen/chain.py` → `lna_shunt.sch/.sym`, `lna_chain`, `tb_chain`; `xschem/gen/top.py` → `radio_analog`, `tt_um_mattvenn_radio`, `tb_radio_analog`, `radio_digital.sym`).
   - `lna_shunt` sits across **o2p / o2n** (stage 2's outputs): o2p – Rh_a – Msw – Rh_b – o2n.
     - Rh: res_high_po_1p41, L 0.62 µm, 421 Ω each. 0.62 is the pcell's shortest, which is why it's 421 and not 393.
     - Msw: pfet_01v8, W 18, L 0.15, nf 6, body VDD.
     - Gate: Rg (xhigh_po_0p35, 20 kΩ) plus Mcap (pfet W 5 / L 5, ~210 fF, gate to VDD), a ~40 MHz low-pass at the switch.
   - New pin `lna_lo_n` on lna_chain / radio_analog. In the tb benches it's driven by `.param vglo` (1.8 = full gain, 0 = low gain).
   - **Why o2 and not o1 (the LNA's own output):** at o1 the low-gain NF rises ~6 dB, at o2 ~0.7 dB.
   - **Why ~10 dB and not more:** in low gain, the noise at the detector drops into its square-law tail, so further gain cuts cost sensitivity (see "Sensitivity").
3. **Layout** (`layout/gen/lna_chain.py`, function `shunt()`).
   - The shunt is at the moat's turn end, beside the o2 columns: Mcap, Rg, Msw (in its own n-tap ring on the moat's VDD met3), then Rh_a / Rh_b.
   - o2n reaches it by a met2 stub, o2p by met1 under the o2n column.
   - `lna_lo_n` enters at the block's west edge in the tile (its own east edge) on met2, then crosses the turn columns on met3 at the bottom of the moat.
   - The moat's n-well stripe now ends before the zone. The block size is unchanged (145.36 × 70.47).
   - DRC (magic, KLayout) 0, antenna 0, LVS match.
4. **Macro** (`openlane/radio_digital/pin_order.cfg`, `macros/radio_digital/*`).
   - Re-hardened with LibreLane 3.0.3 (run `lnalo`). `lna_lo_n` is at E-edge slot 2 (macro y 3.06); every other pin is unchanged.
   - Magic DRC 0, LVS 0, route DRC 0, antenna 0.
   - Setup WS 27.11 ns, hold WS 0.109 ns, 237 max-slew warnings (shipped macro: 27.05 / 0.107 / 245).
   - A full re-harden, so the layout differs from the shipped macro.
5. **Tile route** (`layout/gen/top_nets.py`, net `lna_lo`).
   - From the macro along the very bottom of the tile, up the tile's west edge outside the chain (west of `dbg`), into the chain's pin at tile (13.1, 54.7). 338 µm, 112/112 nets routed.
6. **Router via fix** (`layout/gen/route.py`, its own commit so it can be cherry-picked to `main` alone).
   - A via that misses the global cut grid now gets a local 2 × 2 array when it fits, not one cut.
   - Single-cut via3 on ≥ 0.9 µm metal outside the macro: 15 → 0. via2: 18 → 7: one next to a MIM, where an array would break capm.8, and the rest inside block cells.
   - The array's cuts keep the router's single-cut MIM margins. A first version that used only the rules' 0.1 / 0.08 µm gave 3 magic capm.8 errors.
   - Fixes the decaps' strap links at (277.1, 3.7) and (278.7, 29.3), which are single cuts on `main` too.
7. **Tile re-routed and exported** (`gds/`, `lef/`): see "Checks done".
8. **Docs:**
   - `docs/substrate_2026-10-29.md` (with the scripts in `sim/kpex/`, `sim/substrate/`);
   - the strap in `docs/bringup.md` (R0 oscillation check, R13, D6b), `docs/info.md`, `info.yaml`, `docs/how_it_works.md` specs and `STATUS.md`.

## Results so far (Mac)

**Chain, `tb_chain` (no supply L), gain at 434 MHz, full / low gain, dB.** The schematic is from `sim/chain/lna_lo.sh`, the extracted chain from `layout/pex/lna_chain.spice` swapped into `tb_chain`:

| corner | no shunt, sch | shunt, sch | old extracted (main) | extracted, strap off | extracted, strap on | step | NF off / on |
|---|---|---|---|---|---|---|---|
| tt 27 °C | 80.37 | 80.10 / 68.05 | 76.21 | 75.48 | 65.31 | 10.2 | 11.20 / 11.91 |
| ss 10 °C | 84.75 | 84.43 / 72.85 | 80.47 | 79.67 | 70.21 | 9.5 | 10.79 / 11.25 |
| ff 50 °C | 74.99 | 74.75 / 62.71 | 70.83 | 70.18 | 59.75 | 10.4 | 11.69 / 12.75 |

- **Full-gain cost of the shunt (off): 0.65–0.8 dB extracted** (0.25–0.3 dB in the schematic). The extra comes from o2's parasitics; o2 has a 4 kΩ load. NF is unchanged (+0.01 dB). Matt chose to keep W 18 (2026-10-29).
- **Extracted o2 load:** the shunt wiring adds +3.3 fF on o2p and +2.7 fF on o2n. Every other port is within 0.2 fF of `main`'s extraction.

**Stability, extracted chain** (`sim/chain/stability.sh` with the new `VGLO=0` option, 2 nH, real decap, Ccpl out_p → pad_p):

| Ccpl | ss 10 °C full | ss 10 °C low | tt full | tt low |
|---|---|---|---|---|
| 0 | decays (79.66 / 80.94) | decays (70.22 / 70.50) | decays (75.47 / 76.83) | decays (65.32 / 65.62) |
| 0.5 fF | decays, peak 94.97 (+14 dB) | decays (71.27 / 72.09) | | |
| 1 fF | **oscillates** (2.2 V pp) | decays, peak 76.73 (+5 dB) | **oscillates** | decays (66.54 / 67.66) |
| 2 fF | | **oscillates** | | |
| 3 fF | | **oscillates** | | |

The threshold at ss 10 °C moves from ~0.6 fF to ~1.5 fF (×2.5).

**Coupling** (`docs/substrate_2026-10-29.md`, on `main`'s chain):
- **Wires (kpex 2.5D):** ≤ 0.3 aF asymmetric from the output wires; 13–20 aF from the st5 / st6 Cs plates (an upper bound).
- **Substrate (3D solve):** an out_p → pad_p equivalent of ~1e-5 fF.

Both are orders of magnitude below the budget. The strap covers what isn't modelled: bond wires, package, PCB, the antenna.

**Sensitivity in low gain** (link model `model/e2e.py`, comparator noise 0.45 mV, trim 0.14 mV, noise case, 8–12 sends per level).
- **The effect:** the chain noise sits on the detector's CW curve (`sim/logdet/transfer_cw.txt`) where a −80.3 dBm carrier would; the detector's local slope there is ~12 mV/dB at full gain. Low gain puts it at ~−90 dBm-equivalent, where the slope is only ~3.4 mV/dB, so the post-detector errors in mV weigh ~3.5× more.
- **The numbers:**
  - full gain ≈ −93 dBm (8/8 at −92, 2/8 at −94);
  - o2 low gain ≈ **−88.5 dBm** (12/12 at −86, 8/12 at −88, 1/12 at −90);
  - o1 low gain (not built) would be ≈ −85 dBm.
- This is a model estimate with one local slope; item 5 below checks it at transistor level.

## Checks done (Mac)
- **Blocks:** lna_chain DRC / antenna / LVS clean (`layout/check.sh lna_chain`). The antenna "feedback 1" is magic's extraction warning on Mcap's gate (`docs/layout.md`: the feedback count includes extraction warnings), not a violation.
- **Tile** (`layout/check_top.sh`, re-routed tile with the via fix, as exported): precheck PASS, KLayout DRC 0, magic DRC 0, LVS match.
- **Antenna:** 7 violations, all inside the re-hardened macro. `main`'s tile also has 7 there (`docs/history.md`); still open whether the TT precheck accepts them.
- **The flow reproduces `main`'s committed tile** (XOR: < 1 µm² of poly / implant slivers, no metal differences), so `top.py` + `route.py` is the right flow to update.

## Verification to run here
In order. Each item: the command, what passes, the reference.

1. **Gate-level cocotb** on the re-hardened netlist.
   - `cd verilog/test && make GL=1` (`build/gl_models` per the Makefile). Check `results.xml` for `<failure`.
   - Pass: 16/16, including `test_lna_lo_strap`.
2. **Full rerun** of the verification set: `sim/rerun/sched.py sim/rerun/jobs_2026-10-13.py` (~10 h on sim-0), against `docs/verify_2026-10-13.md`.
   - **Expect port-order fallout:** radio_analog, lna_chain and the TT top have a new pin (`lna_lo_n`, after `dbg_en` / `vcm`). Netlists made by xschem pick it up. Scripts that hard-code instance lines or swap extracted subckts by position may not: fix them so the strap is off (`vglo` 1.8 / `lna_lo_n` tied high).
   - Pass: everything within the 2026-10-13 tolerances, except the chain and RX numbers, which should drop by the shunt's 0.65–0.8 dB.
3. **Chain stability on the final extraction**, both strap states (this extends the table above):
   - `VGLO=0 CORNER=ss TEMP=10 CASES='2n:0 2n:0.5f 2n:1f 2n:1.5f 2n:2f' bash ../../sim/chain/stability.sh` (from a directory with the extracted `tb_chain`: see the note at the end);
   - the same for `VGLO=1.8`;
   - tt and ff in both states;
   - VSUP 1.62 / 1.98.
   - Pass: low gain decays to ≥ 1 fF at every corner.
4. **Monte Carlo on the step.** `sim/chain/mc_chain.py` (mismatch) in both strap states; add a `vglo` sweep.
   - Pass: step ≥ 9 dB in ≥ 99 % of samples; strap-off gain within 1 dB of the nominal.
5. **Low-gain sensitivity at transistor level** (the important new number).
   - `sim/logdet/noise_tran.sh` with the strap on: det with noise alone vs full gain (1.439 V). Then the joined RX pair (`sim/top/tb_tile_joined.py pair -92` and `-88`), or the mixed-signal run (`sim/mixed/`), with `vglo=0`.
   - Pass: low gain detects at −88 dBm; record the det off − on against full gain.
   - If it's much worse than the model's ~−88.5 dBm, report it: it decides whether the strap is worth shipping as is.
6. **Extracted tile** (`layout/pex_tile.sh c|rc`, `sim/top/tb_tile.py`) with `vglo` 1.8 and 0.
   - Pass: RX current unchanged (the shunt draws no DC); det idle and −60 dBm levels within the tolerances in full gain; in low gain the −60 dBm det shifts by ~10 dB of detector slope.
7. **FasterCap** on the st5 / st6 Cs plates ↔ g1 corner.
   - kpex `--fastercap` on a cut of `build/kpex/lna_chain_flat.gds` (`docs/substrate_2026-10-29.md` §1).
   - Pass: the 13–20 aF kpex upper bound comes down, or at least stays < 50 aF.
8. **Substrate study on the final layout:** the §2 rerun in `docs/substrate_2026-10-29.md`, re-flattened from this branch's `layout/lna_chain.gds`.
   - Pass: the equivalent Ccpl stays ≤ 1e-4 fF.
9. **TT precheck** on the exported `gds/` (the GitHub `gds` action, or the TT precheck locally).
   - Pass: precheck passes, including how it treats the 7 macro antenna violations.

Write the results into `docs/verify_lna_lo.md` (one table per item, pass / fail, numbers next to the references above). Update `STATUS.md`, and stop for Matt before merging anything to `main`.

### Note: the extracted-chain bench
`sim/chain/mk_pex_tb.py <tb_chain.spice> layout/pex/lna_chain.spice <out>` swaps the extracted chain into a netlisted `tb_chain`: it replaces the `.subckt lna_chain` … `.ends`, drops the `amp_dp` / `amp_dpc` / `lna_shunt` subckts, and strips the parameters from the `x1 … lna_chain` line. `sim/chain/stability.sh` and `sim/chain/lna_lo.sh` then run from that directory (`build/pexsim` on the Mac).
