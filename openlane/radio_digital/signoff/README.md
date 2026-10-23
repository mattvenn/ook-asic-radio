# Signoff of the shipped digital macro

Reports for the views in [`macros/radio_digital/`](../../../macros/radio_digital) (hardened 2026-10-09, run
`l5b_200x220`). The original run folder wasn't kept, so these were made on 2026-10-23 by running LibreLane's own
signoff steps directly on the shipped GDS, DEF and netlists. Nothing was re-hardened to make them.

## Results
| Check | Result | Report |
|---|---|---|
| Magic DRC on the shipped GDS | 0 errors | [drc.magic.rpt](drc.magic.rpt) |
| Magic extraction of the shipped GDS, netgen LVS against `radio_digital.pnl.v` | Circuits match uniquely | [lvs.netgen.rpt](lvs.netgen.rpt) |
| OpenRCX on the shipped DEF (min / nom / max RC), STA at 9 corners | 0 setup and 0 hold violations; worst setup slack 27.05 ns (max_ss), worst hold slack 0.107 ns (min_ff) | [sta/summary.rpt](sta/summary.rpt) |
| Max slew | 245 warnings at max_ss (11–24 at tt, 0 at ff), see below | `sta/<corner>/checks.rpt` |

These match the numbers recorded for the original run in `docs/history.md` ("Final run": setup 27.05 ns, hold
0.107 ns, 245 max-slew warnings).

- **Clock gating** (`rd_cg.v`, one `dlclkp_1` per 127-bit chip register). The gate enables are timing
  endpoints: hold ≥ 0.53 ns (ff), setup ≥ 43 ns (ss). The clock is propagated through each gate into its own
  tree, and the hold paths into all 508 gated flops are checked, worst 0.19 ns (min_ff). The full path
  reports for the two worst corners: `sta/min_ff_n40C_1v95/min.rpt.gz` (hold) and `sta/max_ss_100C_1v60/max.rpt.gz`
  (setup).
- **Max slew:** data nets only, driven by the resizer's weak delay cells (`clkdlybuf4s25_1` fanout buffers,
  `dlygate4sd3_1` hold buffers), worst ~1.4 ns against the flow's 0.75 ns limit. That's inside the cells'
  characterised range (1.5 ns), so the delays are still calculated within the library tables, and the clock is
  50 ns. None are on the clock tree.
- **Unannotated drivers (17)**: the CTS dummy clock loads (`clkload*`) and the tie-high cells. None of them
  drives a routed net, and LibreLane's own run reports the same 17.

## Why not just re-harden
A re-harden of the same RTL and config (LibreLane 3.0.3, image `hpretl/iic-osic-tools:2026.05`, 2026-10-23)
doesn't give the shipped layout. The logic netlist is identical (the same cells, once diodes, decap and fill
are left out). But the antenna repair puts 126 diodes where the shipped macro has 140, so 36 cells move and the
routing differs. The flow itself is deterministic: two re-hardens gave identical DEF, netlists and LEF, and their
GDS differ only in timestamps. So the shipped macro was made with another tool setup.

The STA method was checked on that re-harden first: running these steps on its DEF gives LibreLane's own
post-route STA table digit for digit.

## Reproduce
```
tools/osic bash openlane/radio_digital/signoff/repro/run.sh      # from the repo root, ~1 min
```
It writes to `openlane/radio_digital/runs/signoff_check/` (git-ignored) and prints the STA summary, the DRC count
and the LVS result. `repro/` holds the step configs taken from the re-harden run (`ext.json` sets
`MAGIC_EXT_USE_GDS` so LVS extracts the GDS, not the DEF) and the SDC LibreLane wrote for this config.
Tools: LibreLane 3.0.3, OpenROAD 26Q2-1164-g08f67ee5e, magic 8.3.642, image 2026.05.
