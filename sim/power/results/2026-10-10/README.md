# Power benchmark results, 2026-10-10 (tile GDS built 2026-10-09 20:00)
Raw outputs of the runs summarised in docs/power.md (copied from build/power/).
- `r_mesh_<v>.json`: DC R per block and supply (mean / max over its terminals, ohm), 0.5 µm mesh (`_p1`: 1 µm).
- `ir_<v>.json`: IR drop per block at the RX op and the TX average / peak currents (V).
- `z_ac_A.json`: |Z| per block vs frequency, and the transfer from each block's supply to the others.
- `em_*.txt`, `tran_tx_A.txt`: the EM and TX-keyed transient printouts.
Variants: `A` / `B` = the TT stripe cases (sim/power/pdn.py); `A_W` widened west + east VAPWR straps,
`A_Wideal` the same with ideal straps, `A_Wtrunk` with the top-level routing x3 (docs/power.md "What-ifs").
`A_fix`: the power-fix layout (branch power-fix, 08c44d1: wider straps, the TX driver VAPWR feed, the
RX supply trunks; docs/power.md "After the fix").
