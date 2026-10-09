// Write the chosen floorplan for the re-layout / re-harden work:
//   node layout/floorplan/page/pinreport.js variant.json
// -> layout/floorplan/floorplan.json (placements, straps, decap, moved pins)
// -> layout/floorplan/pins.md (per block: placement, and every pin by edge in the block's own frame)
require('./engine.js');
const fs = require('fs'), path = require('path'), FP = globalThis.FP;
const dir = path.join(__dirname, '..');
const data = { tile: JSON.parse(fs.readFileSync(path.join(dir, 'tile.json'))), cells: JSON.parse(fs.readFileSync(path.join(dir, 'blocks.json'))) };
const cat = FP.buildCatalog(data);
const v = JSON.parse(fs.readFileSync(process.argv[2]));
const R = FP.resolve(cat, v), r = FP.evaluate(data, cat, v);
fs.writeFileSync(path.join(dir, 'floorplan.json'), JSON.stringify(FP.exportJSON(data, cat, v), null, 1) + '\n');

const f = (x) => (+x).toFixed(2);
const edgeOf = (x, y, w, h) => { const d = { W: x, E: w - x, S: y, N: h - y }; return Object.entries(d).sort((a, b) => a[1] - b[1])[0][0]; };
const SIDE_IN_TILE = (ins, e) => {            // which way a block's own edge faces once placed
  const c = [ins.w / 2, ins.h / 2], p = { W: [0, c[1]], E: [ins.w, c[1]], S: [c[0], 0], N: [c[0], ins.h] }[e];
  const a = FP.mapPt(ins.pl, ins.w, ins.h, c[0], c[1]), b = FP.mapPt(ins.pl, ins.w, ins.h, p[0], p[1]);
  const dx = b[0] - a[0], dy = b[1] - a[1];
  return Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'east' : 'west') : (dy > 0 ? 'north' : 'south');
};
const out = [];
out.push(`# Floorplan: block positions and pin positions`);
out.push('');
out.push(`Generated from the floorplan page's variant **${v.name}** by \`layout/floorplan/page/pinreport.js\`; the placements are also in \`floorplan.json\` next to this file.`);
out.push('');
out.push('- Coordinates in µm. **Placement**: lower-left of the placed (transformed) bbox in the tile, and the GDS orientation (KLayout `DCplxTrans(1, rot, mirror, …)`, mirror about x first).');
out.push('- **Pins**: in each block\'s *own* frame (its bbox lower-left = 0, 0, before the orientation), grouped by the block\'s own edge. "moved" = a new position for the re-layout / re-harden; the others are where the GDS has them now. The tile direction each edge faces after placement is given in brackets.');
out.push('- Moved pins sit on the edge facing what they connect to (`pinfit.js`). Positions along an edge are targets: pins closer than ~1 µm were spread to 1 µm.');
out.push('');
out.push('## Checks (with the moved pins)');
out.push('');
out.push('| rule | status | value |'); out.push('|---|---|---|');
for (const c of r.checks) out.push(`| ${c.rule}. ${c.title} | ${c.status} | ${c.value} |`);
out.push('');
const order = ['macro', 'xchain', 'xbias', 'xdet', 'xlpf', 'xavg', 'xcomp', 'xdac', 'xctrim', 'xdbg', 'xtx.xring', 'xtx.xls', 'xtx.xlse_p', 'xtx.xlse_n', 'xtx.xdrv_p', 'xtx.xdrv_n'];
for (const n of order) {
  const ins = R.inst[n]; if (!ins) continue;
  const c = ins.cat, [k, m] = FP.ORIENTS[ins.pl.orient];
  out.push(`## ${n} (${c.cell})`);
  out.push('');
  const reshaped = c.reshape && (Math.abs(ins.w - c.w) > 1e-6 || Math.abs(ins.h - c.h) > 1e-6);
  out.push(`- Size: ${f(ins.w)} × ${f(ins.h)}${reshaped ? ` (reshaped from ${c.w} × ${c.h}, ${Math.abs(ins.w * ins.h - c.w * c.h) > 1 ? f(ins.w * ins.h) + ' µm² vs ' + c.w * c.h : 'same area'}: re-harden at this size)` : c.estimate ? ' (estimate: not laid out yet)' : ' (GDS)'}`);
  out.push(`- Placement: x ${f(ins.rect[0])}, y ${f(ins.rect[1])}, ${ins.pl.orient} (rot ${k * 90}, mirror ${m})`);
  const moved = Object.entries(ins.pins).filter(([, p]) => p.moved);
  out.push(`- Pins moved: ${moved.length ? moved.length : 'none'}`);
  out.push('');
  const groups = {};
  for (const [pn, p] of Object.entries(ins.pins)) {
    if (n === 'macro' && !p.moved) continue;
    const x = p.moved ? p.x : p.x * (reshaped || c.estimate ? ins.w / c.w : 1), y = p.moved ? p.y : p.y * (reshaped || c.estimate ? ins.h / c.h : 1);
    const e = edgeOf(x, y, ins.w, ins.h);
    (groups[e] = groups[e] || []).push([pn, x, y, p.moved]);
  }
  for (const e of ['N', 'S', 'W', 'E']) {
    if (!groups[e]) continue;
    const along = e === 'N' || e === 'S' ? 1 : 2;
    groups[e].sort((a, b) => a[along] - b[along]);
    out.push(`**${e} edge** (faces ${SIDE_IN_TILE(ins, e)} in the tile; ${along === 1 ? 'left → right, x' : 'bottom → top, y'}):`);
    out.push('');
    out.push('| pin | x | y | |'); out.push('|---|---|---|---|');
    for (const [pn, x, y, mv] of groups[e]) out.push(`| ${pn} | ${f(x)} | ${f(y)} | ${mv ? 'moved' : ''} |`);
    out.push('');
  }
}
out.push('## Straps and decap');
out.push('');
for (const s of v.straps || []) out.push(`- ${s.net} strap: x ${f(s.x)}, w ${f(s.w)} (met4, full height)`);
for (const [b, rs] of Object.entries(v.decaps || {})) rs.forEach((q, i) => out.push(`- ${b} ${i + 1}: x ${f(q.x)}, y ${f(q.y)}, ${f(q.w)} × ${f(q.h)}${q.mim ? ' (MIM only, on top of r2r)' : ''}`));
out.push('');
fs.writeFileSync(path.join(dir, 'pins.md'), out.join('\n'));
console.log('wrote floorplan.json and pins.md');
