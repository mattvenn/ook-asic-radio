// node tools/floorplan_dump.js [overrides.json] -> JSON: placed rects + pins + nets for the chosen floorplan
const path = require('path'), fs = require('fs');
const dir = path.resolve(__dirname, '../layout/floorplan');
require(path.join(dir, 'page/engine.js'));
const FP = globalThis.FP;
const data = { tile: JSON.parse(fs.readFileSync(path.join(dir, 'tile.json'))), cells: JSON.parse(fs.readFileSync(path.join(dir, 'blocks.json'))) };
const cat = FP.buildCatalog(data);
const f = JSON.parse(fs.readFileSync(path.join(dir, 'floorplan.json')));
const v = FP.importJSON(cat, f);
const ov = process.argv[2] ? JSON.parse(fs.readFileSync(process.argv[2])) : {};
for (const [i, p] of Object.entries(ov.place || {})) Object.assign(v.place[i], p);
for (const [i, ps] of Object.entries(ov.pins || {})) v.pins[i] = Object.assign(v.pins[i] || {}, ps);
const R = FP.resolve(cat, v), nets = FP.routeNets(data.tile, R);
const ev = FP.evaluate(data, cat, v);
const out = { tile: data.tile, inst: {}, decaps: R.decaps.map(d => ({ name: d.name, rect: d.rect, mim: d.mim })), nets: nets.map(n => ({ name: n.name, cls: n.cls, pa: n.pa, pb: n.pb, len: n.len })),
  checks: ev.checks.map(c => [c.id || c.rule, c.title, c.status, c.value]) };
for (const [n, i] of Object.entries(R.inst)) out.inst[n] = { rect: i.rect, orient: i.pl.orient, cell: i.cat.cell || n, pins: Object.fromEntries(Object.entries(i.pins).filter(([k, p]) => !/^(r\d|rd|rt|rdeg|t[1-6]|o[1-6]|y\d)/.test(k)).map(([k, p]) => [k, [p.at[0], p.at[1], !!p.moved]])) };
console.log(JSON.stringify(out));
