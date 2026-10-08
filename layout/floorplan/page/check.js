// Run the floorplan page's rule checks from the command line:
//   node layout/floorplan/page/check.js [variants.json | floorplan.json]
// Default: layout/floorplan/variants.json (the variants Claude seeds into the page).
const fs = require('fs');
const path = require('path');
require('./engine.js');
const FP = globalThis.FP;
const dir = path.join(__dirname, '..');
const data = {
  tile: JSON.parse(fs.readFileSync(path.join(dir, 'tile.json'))),
  cells: JSON.parse(fs.readFileSync(path.join(dir, 'blocks.json'))),
};
const cat = FP.buildCatalog(data);
const file = process.argv[2] || path.join(dir, 'variants.json');
let j = JSON.parse(fs.readFileSync(file));
const variants = j.blocks ? [FP.importJSON(cat, j)] : j.variants;
const mark = { pass: 'ok  ', warn: 'WARN', fail: 'FAIL', info: '  - ' };
for (const v of variants) {
  const r = FP.evaluate(data, cat, v, j.settings);
  console.log(`\n== ${v.name}`);
  for (const c of r.checks) console.log(`${mark[c.status]} ${String(c.rule).padEnd(2)} ${c.title.padEnd(34)} ${String(c.value).padEnd(12)} ${c.detail}`);
  const a = r.area;
  console.log(`area: signal ${(a.signal / 1e3).toFixed(1)}k, decap ${(a.decap / 1e3).toFixed(1)}k of ${(a.decapTarget / 1e3).toFixed(1)}k, free beside the macro ${(a.free / 1e3).toFixed(1)}k`);
}
