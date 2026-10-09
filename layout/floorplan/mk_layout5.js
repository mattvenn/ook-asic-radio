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
v.note = 'matt layout 4 (handoff, chain folded) with the 2026-10-09 routing review: comp_ct flipped to MYR90 (out at its tile-south-east corner without a long internal run; ibias / trim over the corridor west of Ctrim and over Ctrim n); avg_sc sc_phi1/2 on its north edge (clocks leave over the top, away from comp inp / inn); macro pins re-ordered: trim_out[i] level with r2r b_i (straight runs), comp_in in the gap under r2r, sc_phi then dbg_en / tx_en_n / tx_en just under the TT group (the enables run west in the TT channel). Block positions unchanged. lpf_rc, log_det, bias_gen, dbg_tg pins as laid out.';
const P = (i, p, x, y) => { v.pins[i] = v.pins[i] || {}; v.pins[i][p] = { x, y }; };
// comp_ct MYR90 (tile x = 179.47 - own y, tile y = 190.05 - own x)
v.place.xcomp.orient = 'MYR90';
v.pins.xcomp = {};
P('xcomp', 'inn', 37.85, 41.72); P('xcomp', 'inp', 42.45, 41.72);          // N -> west, at tile y 152.2 / 147.6
P('xcomp', 'out', 72.45, 0.25);                                            // S -> east, tile (179.2, 117.6)
P('xcomp', 'ibias', 73.2, 22.47); P('xcomp', 'trim', 73.2, 19.47);         // E -> south, tile x 157 / 160
// avg_sc: clocks on the north edge at the east end
P('xavg', 'phi2', 74.35, 30.15); P('xavg', 'phi1', 75.35, 30.15);
// as laid out (2026-10-09)
P('xdbg', 'a', 1.0, 0.25); P('xdbg', 'b', 5.55, 0.25);
P('xdet', 'det', 0.2, 0.25);
P('xlpf', 'out', 64.95, 33.9);
P('xbias', 'en', 2.0, 0.25); P('xbias', 'ib_comp', 80.02, 48.07);
// macro: east edge (own frame), met3 slots at 0.34 + 1.36 i (pin_order.cfg)
const s = i => +(0.34 + 1.36 * i).toFixed(2);
const M = { rx_en: 5, comp_in: 63, 'trim_out[0]': 69, 'trim_out[1]': 80, 'trim_out[2]': 85, 'trim_out[3]': 91,
  'trim_out[4]': 96, 'trim_out[5]': 102, 'trim_out[6]': 107, 'trim_out[7]': 113, sc_phi2: 114, sc_phi1: 115,
  dbg_en: 116, tx_en_n: 117, tx_en: 118 };
const tt = ['clk'].concat(...['uio_oe', 'uio_out', 'uo_out', 'uio_in', 'ui_in'].map(b => [7, 6, 5, 4, 3, 2, 1, 0].map(k => `${b}[${k}]`)), ['rst_n']);
tt.forEach((n, k) => { M[n] = 119 + k; });
for (const [n, i] of Object.entries(M)) P('macro', n, 199.75, s(i));
fs.writeFileSync(path.join(dir, 'variant_layout5.json'), JSON.stringify(v, null, 1) + '\n');
console.log('wrote variant_layout5.json');
