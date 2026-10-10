// matt layout 5: "matt layout 4 (handoff, chain folded)" with the routing review of 2026-10-09
// applied (orientation / pin changes, same block positions). Writes variant_layout5.json; then
//   node layout/floorplan/page/pinreport.js layout/floorplan/variant_layout5.json
// regenerates floorplan.json and pins.md.
const fs = require('fs'), path = require('path');
require('./page/engine.js'); const FP = globalThis.FP;
const dir = __dirname;
const data = { tile: JSON.parse(fs.readFileSync(path.join(dir, 'tile.json'))), cells: JSON.parse(fs.readFileSync(path.join(dir, 'blocks.json'))) };
const cat = FP.buildCatalog(data);
const base = JSON.parse(fs.readFileSync(path.join(dir, process.argv[2] || 'floorplan.json')));
const v = FP.importJSON(cat, base);
v.name = 'matt layout 5 (routing review)';
v.note = 'matt layout 4 (handoff, chain folded) with the 2026-10-09 routing review, and every block laid out to it (pins from the GDS). comp_ct MYR90 (out at its tile-south-east corner; inp = avg / inn = lpf on the west face; ibias over the corridor west of Ctrim, trim over Ctrim); r2r MYR90 (out level with Ctrim, a straight met2 run over r2r); avg_sc clocks on its north edge (leave over the top, away from comp inp / inn), in on its south edge; Ctrim laid out (1 pF shunt cap trim -> VGND, 22.4 um). Macro pins: trim_out[i] level with r2r b_i, comp_in in the gap under r2r, sc_phi then dbg_en / tx_en_n / tx_en just under the TT group (the enables run west in the TT channel). Block positions unchanged.';
const P = (i, p, x, y) => { v.pins[i] = v.pins[i] || {}; v.pins[i][p] = { x, y }; };
// The blocks are laid out to this floorplan (2026-10-09): their pins are in the GDS
// (blocks.json, tools/floorplan_blocks.py), so only the macro has moved pins.
v.pins = {};
// comp_ct MYR90: own N faces west (inp = avg / inn = lpf), E south (ibias, trim), S east (out)
v.place.xcomp.orient = 'MYR90';
// r2r MYR90: its S edge (b0..b7, out) still faces east, reversed: out (own x 62.1) lands at
// tile y ~100.6, level with Ctrim's E-edge trim pin (one straight met2 run west over r2r,
// under the MIM decap; r2r stays met1-only and its N edge is a met1 VGND rail)
v.place.xdac.orient = 'MYR90';
// west VAPWR strap (2026-10-09, top-level session): the TX at the west end draws ~11 mA from
// VAPWR, 215-270 um from the mid strap; x 0-5.5 is clear of blocks (the west decaps keep their
// MIM out of this column)
if (!v.straps.some(st => st.net === 'VAPWR' && st.x < 50)) v.straps.push({ net: 'VAPWR', x: 2.5, w: 1.2 });
// wider straps (2026-10-10, docs/power.md what-if W): the west VAPWR strap carried the TX's VAPWR
// at 2x the EM limit (via4 / met4); 3 via4 columns per met5 landing at 5 um. West VGND keeps its
// east edge (15.1: the TT bus drops at x 15.6); 10.8 would short VDPWR. (Keyed by the old x too,
// so re-running on an already widened floorplan.json is a no-op.)
const WIDE = { VAPWR: { 2.5: [0.3, 5.0], 0.3: [0.3, 5.0], 488.02: [481.0, 8.22], 481: [481.0, 8.22] },
  VDPWR: { 9.3: [5.8, 4.7], 5.8: [5.8, 4.7] }, VGND: { 13.9: [12.0, 3.1], 12: [12.0, 3.1] } };
for (const st of v.straps) { const k = (WIDE[st.net] || {})[st.x]; if (k) [st.x, st.w] = k; }
if (v.est) delete v.est.xctrim;                       // laid out: 22.435 x 22.435 (layout/gen/ctrim_1p.py)
// macro: east edge (own frame), met3 slots at 0.34 + 1.36 i (pin_order.cfg)
const s = i => +(0.34 + 1.36 * i).toFixed(2);
// trim_out[i] level with r2r b_i (r2r MYR90: b0 at the top, b7 at the bottom)
const M = { rx_en: 5, comp_in: 63, 'trim_out[7]': 69, 'trim_out[6]': 75, 'trim_out[5]': 80, 'trim_out[4]': 86,
  'trim_out[3]': 91, 'trim_out[2]': 97, 'trim_out[1]': 102, 'trim_out[0]': 113, sc_phi2: 114, sc_phi1: 115,
  dbg_en: 116, tx_en_n: 117, tx_en: 118 };
const tt = ['clk'].concat(...['uio_oe', 'uio_out', 'uo_out', 'uio_in', 'ui_in'].map(b => [7, 6, 5, 4, 3, 2, 1, 0].map(k => `${b}[${k}]`)), ['rst_n']);
tt.forEach((n, k) => { M[n] = 119 + k; });
for (const [n, i] of Object.entries(M)) P('macro', n, 199.75, s(i));
fs.writeFileSync(path.join(dir, 'variant_layout5.json'), JSON.stringify(v, null, 1) + '\n');
console.log('wrote variant_layout5.json');
