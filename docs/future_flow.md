# A future analog layout flow (notes for next time)

Written 2026-10-09 after floorplanning this tile by hand with the floorplan page (`layout/floorplan/page/`). This is Matt's proposed flow, with what this round taught us about where it will work and where it will hurt. It's a plan, not something that exists yet.

## The flow

1. **Schematic → block layouts.** Lay out each block early, so its real size is known and guard rings and sensitive "avoid" zones can be drawn. The schematic phase also writes down the design's dos and don'ts as a machine-readable constraints file (see below).
2. **Floorplan.** All blocks on the tile with airwires. The rules come from the constraints file and update live as blocks move; errors and warnings are drawn on the blocks where the problem is, with a hover saying why. Blocks can be resized roughly by area (and aspect). Iterate until the warnings are as few as possible or accepted.
3. **Rework.** Export the floorplan to a tool that re-generates each block with its new pin positions and outline. Every block is re-extracted, passes LVS, and is run against its regression.
4. **Reload and nudge.** Reworked blocks come back a few µm different: reload the real outlines into the floorplan, re-run the rules, nudge.
5. **Final route.** A router places everything and routes it with attention to power, electromigration and the avoid zones.
6. **Top-level verification.** Top-level LVS and PEX, then the regression and a full-tile simulation on the extracted top level. Problems are reported back onto the floorplan view.

## What worked this round (keep)
- **Real block sizes before floorplanning.** Estimates would have misled us: the chain's 268 µm length drove the whole layout.
- **Pins free during floorplanning.** Pins treated as "which edge, which order", then fitted to the edge facing their connection (`pinfit.js`), rather than taken from the GDS. Most rule failures (short analog path, bias next to the chain) were fixed by pin moves alone. This should be a standard step.
- **Power on the floorplan.** Straps, decap areas and MIM-only decap on top of met1-only blocks (r2r) were planned on the floorplan, not left to the router.
- **Live rules with a reason on hover.** The reason is what lets the designer overrule a rule with judgement.
- **Block diagram toggle and group select/drag** were both useful while rearranging.

## What to change

### 1. Rules from data, not code
This round's rules 1–9 were hand-written in `engine.js` with net names built in (`FP.NETS`, `NET_CLASSES`). Next time, the schematic phase writes a constraints file that tags nets and blocks. The floorplan derives generic rules from the tags: aggressor ↔ sensitive distance, wire width from current, length limit per net class, layer keep-outs. Then the tool carries over to the next chip.

### 2. Rules need conditions and a way to accept them
- Rule 5 (TX driver → pad length) failed only because the tool didn't know the radio isn't duplex: the TX is off whenever the RX is on. Operating modes belong in the constraints, so a rule between two blocks only applies in modes where both are active.
- The TT-pin-channel check kept failing after we'd decided it didn't matter (the TT wires end on the macro's own pins). A warning must be acceptable with a reason, and the reason kept in the record, so the list shows only open problems.

### 3. The rework step is easy only if blocks are generators
Most blocks here already are (`layout/gen/*.py`). If every generator takes an **aspect ratio** and a **pin spec** (edge, order, rough position) as inputs, the rework step is just re-running the generators with the floorplan's export, then the existing `layout/check.sh`, `layout/pex.sh` and `tb_<block>` per block. Hand-drawn layout breaks this: avoid it for anything that might move. The digital macro is the same idea through LibreLane (`DIE_AREA` + `pin_order.cfg` generated from the floorplan).

### 4. The final router is the hard part
No off-the-shelf open-source router does analog-aware routing in sky130 (shielding, differential pairs routed as one, EM-sized widths, avoid zones). But the net count is small (~60 inter-block nets + the 42-wire TT bus here), so a scripted router is realistic:
- avoid zones and block keep-outs become blockages
- net class picks width, layer and shielding (e.g. TX driver → pad ≥ 5 µm; slow high-impedance nodes shielded with VSS; clock lines kept off the RX)
- pairs (rx_p/rx_n, tx_p/tx_n, the chain taps) routed together
- power stays the straps and decap planned on the floorplan, not the router's job

### 5. Add a full-tile simulation with dangerous-mode stimulus
Per-block regressions won't catch interactions between blocks. After routing, simulate the extracted tile with stimulus that hits the risky modes: the TX switching on or off while the RX settles, the switched-cap clocks running during detection, the trim DAC changing.

## Draft constraints file (this design's nets)

A sketch of the format, using this tile's real nets (from `FP.NETS` in `engine.js`). YAML, written in the schematic phase, read by the floorplan and the router.

```yaml
modes:                       # which blocks are active together
  rx:  [xchain, xbias, xdet, xlpf, xavg, xcomp, xdac, xctrim, macro]
  tx:  [xtx, macro]
  dbg: [xdbg]                # with rx

net_classes:
  rx_input:  {sensitive: high, max_len: 50,  pair: true}
  rx_signal: {sensitive: med}
  slow_node: {sensitive: med, shield: VSS}           # high-impedance, slow: length doesn't matter, coupling does
  clock:     {aggressor: high, keep_from: [rx_input, rx_signal], min_gap: 20}
  enable:    {static_in: [rx]}                       # not an aggressor while receiving
  bias:      {sensitive: med, max_len: 60}
  tx_power:  {aggressor: high, current_mA: 10, width_um: 5, pair: true, active_in: [tx]}
  trim:      {aggressor: low, static_in: [rx]}

nets:
  rx_p/rx_n:  {class: rx_input, from: pad:ua[0]/ua[1], to: xchain.inp/inn}
  o1..o3:     {class: rx_signal, from: xchain, to: xdet}
  o4..out:    {class: rx_signal, keep_from: [xchain.input, xchain.stage1], min_gap: 60}   # rule 2
  det, lpf:   {class: slow_node}
  avg:        {class: rx_signal}
  sc_phi1/2, comp_in, clk: {class: clock}
  ib_chain, vcm, ib_det, ib_comp: {class: bias}
  tx_p/tx_n:  {class: tx_power, to: pad:ua[3]/ua[4]}
  trim[0..7], dac: {class: trim}

blocks:
  xchain: {avoid_zone: {zones: [input, stage1], from: [clock, tx_power, macro], min_gap: 100}}   # rule 1
  xdac:   {layers_used: [met1], allow_on_top: mim_decap}
  xcomp, xavg, xdac: {aggressor: switching, keep_from: [xchain.input, xchain.stage1], min_gap: 100}
  macro:  {aggressor: high, halo: 5}

power:
  VAPWR: {decap_pF: 50}
  VDPWR: {decap_pF: 30}

accepted:                    # warnings the designer has decided about, with the reason
  - {rule: tx_power.max_len, reason: "TX off in RX; route ≥ 5 µm wide instead"}
  - {rule: tt_channel, reason: "TT wires end on the macro's own pins"}
```

## Where things are now
- Floorplan page and tools: `layout/floorplan/page/` (engine, placer, pinfit, refine, pinreport, check); spec in `docs/floorplan_spec.md`.
- The chosen floorplan and the handoff for step 3 done by hand: `layout/floorplan/pins.md`, `floorplan.json`, `docs/handoff_pins_reharden.md`.
- Still open in this design: the `lna_chain` fold (rule 2).
