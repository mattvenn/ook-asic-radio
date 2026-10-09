// Floorplanning: move block pins to the block edge facing what they connect to.
//   node layout/floorplan/page/pinfit.js variant.json out.json   (a variant document from the page's store)
// Moves the pins of the macro, bias_gen, comp_ct, avg_sc, lpf_rc, r2r, Ctrim, dbg_tg, log_det det / ibias_det
// and the chain's vcm / ibias; prints the checklist before and after. The moved pins need block re-layouts
// (the macro: a new pin_order.cfg); nothing here changes a layout.
require('./engine.js');
const fs = require('fs'); const FP = globalThis.FP;
const root = require('path').join(__dirname, '..') + '/';
const data = { tile: JSON.parse(fs.readFileSync(root + 'tile.json')), cells: JSON.parse(fs.readFileSync(root + 'blocks.json')) };
const cat = FP.buildCatalog(data);
const src = JSON.parse(fs.readFileSync(process.argv[2]));
const v = JSON.parse(JSON.stringify(src)); v.pins = {};
const MOV = new Set(['macro', 'xbias', 'xcomp', 'xavg', 'xlpf', 'xdac', 'xctrim', 'xdbg', 'xdet']);
const movable = (ref) => { if (ref.startsWith('pad:')) return false; const i = ref.lastIndexOf('.'), n = ref.slice(0, i), p = ref.slice(i + 1);
  return (MOV.has(n) && (n !== 'xdet' || p === 'det' || p === 'ibias_det')) || (n === 'xchain' && (p === 'vcm' || p === 'ibias')); };
const split = (ref) => { const i = ref.lastIndexOf('.'); return [ref.slice(0, i), ref.slice(i + 1)]; };
// TT north pins: each macro N pin connects to its TT pin
const nets = FP.NETS.map(n => [n[2], n[3]]);
for (const k of Object.keys(cat.macro.pins)) if (data.tile.pins[k] && k !== 'clk') nets.push(['pad:' + k, 'macro.' + k]);
const peers = {};
for (const [a, b] of nets) { (peers[a] = peers[a] || []).push(b); (peers[b] = peers[b] || []).push(a); }
const pos = (R, ref) => { if (ref.startsWith('pad:')) { const p = data.tile.pins[ref.slice(4)]; return [(p.x0 + p.x1) / 2, p.y0 < 1 ? 0 : data.tile.h]; } const [n, p] = split(ref); return R.inst[n].pins[p].at; };
function toLocal(ins, pt) {           // inverse of the placement transform
  const o = FP.mapPt(ins.pl, ins.w, ins.h, 0, 0), ex = FP.mapPt(ins.pl, ins.w, ins.h, 1, 0), ey = FP.mapPt(ins.pl, ins.w, ins.h, 0, 1);
  const a = ex[0] - o[0], b = ey[0] - o[0], c = ex[1] - o[1], d = ey[1] - o[1], det = a * d - b * c;
  const dx = pt[0] - o[0], dy = pt[1] - o[1];
  return [(d * dx - b * dy) / det, (-c * dx + a * dy) / det];
}
for (let pass = 0; pass < 4; pass++) {
  for (const ref of Object.keys(peers)) {
    if (!movable(ref)) continue;
    const R = FP.resolve(cat, v);
    const [n, p] = split(ref), ins = R.inst[n]; if (!ins) continue;
    const ts = peers[ref].filter(q => q.startsWith('pad:') || R.inst[split(q)[0]]).map(q => pos(R, q));
    if (!ts.length) continue;
    const t = [ts.reduce((s, q) => s + q[0], 0) / ts.length, ts.reduce((s, q) => s + q[1], 0) / ts.length];
    // nearest boundary point of the block to t, in the block's own frame
    const [lx, ly] = toLocal(ins, t), w = ins.w, h = ins.h, in_ = 0.25;
    // the edge facing the target: beyond the top / bottom (and no further out sideways) -> N / S edge;
    // beyond a side -> W / E edge; inside the block -> the nearest edge
    const ox = lx < 0 ? -lx : lx > w ? lx - w : 0, oy = ly < 0 ? -ly : ly > h ? ly - h : 0;
    const cm = 1.0;                                 // keep pins >= 1 um from the corners (no edge ambiguity)
    let x = Math.min(w - cm, Math.max(cm, lx)), y = Math.min(h - cm, Math.max(cm, ly));
    if (oy > 0 && oy >= ox) y = ly < 0 ? in_ : h - in_;
    else if (ox > 0) x = lx < 0 ? in_ : w - in_;
    else { const m = Math.min(lx, w - lx, ly, h - ly); if (m === lx) x = in_; else if (m === w - lx) x = w - in_; else if (m === ly) y = in_; else y = h - in_; }
    v.pins[n] = v.pins[n] || {}; v.pins[n][p] = { x, y, tx: lx, ty: ly };      // tx/ty: the unclamped target, for ordering
  }
}
// spread pins that land on top of each other along their edge (>= 1 um apart)
for (const [n, ps] of Object.entries(v.pins)) {
  const ins = FP.resolve(cat, v).inst[n], groups = {};
  for (const [p, q] of Object.entries(ps)) { const e = q.y <= 0.3 ? 'S' : q.y >= ins.h - 0.3 ? 'N' : q.x <= 0.3 ? 'W' : 'E'; (groups[e] = groups[e] || []).push([p, q]); }
  for (const [e, arr] of Object.entries(groups)) {
    const k = e === 'W' || e === 'E' ? 'y' : 'x', L = k === 'x' ? ins.w : ins.h;
    const tk = k === 'x' ? 'tx' : 'ty';
    arr.sort((a, b) => (a[1][k] - b[1][k]) || (a[1][tk] - b[1][tk]));
    for (let i = 1; i < arr.length; i++) if (arr[i][1][k] < arr[i - 1][1][k] + 1) arr[i][1][k] = arr[i - 1][1][k] + 1;
    const over = arr.length ? arr[arr.length - 1][1][k] - (L - 1) : 0;
    if (over > 0) for (const a of arr) a[1][k] -= over;
    for (const a of arr) { a[1][k] = +a[1][k].toFixed(2); a[1][k === 'x' ? 'y' : 'x'] = +a[1][k === 'x' ? 'y' : 'x'].toFixed(2); delete a[1].tx; delete a[1].ty; }
  }
}
// uncross: on each edge, give the moved pins the same order as the pins they connect to (projected
// onto that edge), keeping the slot positions; repeat until nothing changes
for (let pass = 0; pass < 6; pass++) {
  let changed = false;
  for (const [n, ps] of Object.entries(v.pins)) {
    const R = FP.resolve(cat, v), ins = R.inst[n], groups = {};
    for (const [p, q] of Object.entries(ps)) { const e = q.y <= 0.3 ? 'S' : q.y >= ins.h - 0.3 ? 'N' : q.x <= 0.3 ? 'W' : 'E'; (groups[e] = groups[e] || []).push(p); }
    for (const [e, arr] of Object.entries(groups)) {
      if (arr.length < 2) continue;
      const k = e === 'N' || e === 'S' ? 'x' : 'y', ki = k === 'x' ? 0 : 1;
      const key = (p) => { const ts = (peers[`${n}.${p}`] || []).filter(q => q.startsWith('pad:') || R.inst[split(q)[0]]).map(q => toLocal(ins, pos(R, q))[ki]); return ts.length ? ts.reduce((a, b) => a + b, 0) / ts.length : ps[p][k]; };
      const slots = arr.map(p => ps[p][k]).sort((a, b) => a - b);
      const order = arr.slice().sort((a, b) => key(a) - key(b));
      order.forEach((p, i) => { if (ps[p][k] !== slots[i]) { ps[p][k] = slots[i]; changed = true; } });
    }
  }
  if (!changed) break;
}
const show = (t, vv) => { const r = FP.evaluate(data, cat, vv); console.log('\n' + t); for (const c of r.checks) console.log(c.status.padEnd(5), String(c.rule).padEnd(2), c.title.padEnd(32), c.value);
  const g = (n) => { const x = r.nets.find(q => q.name === n); return x && !x.missing ? x.len.toFixed(0) : '-'; };
  console.log('ib_chain', g('ib_chain'), 'vcm', g('vcm'), 'trim[0..7]', g('trim[0]') + '..' + g('trim[7]'), 'tx_en', g('tx_en'), 'tx_en_n', g('tx_en_n'), 'key', g('tx_en key'), 'rx_en', g('rx_en'), 'dbg_en', g('dbg_en'), 'comp_in', g('comp_in'), 'phi', g('sc_phi1'), 'det dbg', g('det dbg')); };
show('BEFORE (Matt layout 2)', src); show('AFTER (pins moved)', v);
const moved = Object.entries(v.pins).map(([n, ps]) => `${n}: ${Object.keys(ps).length}`).join(', ');
console.log('\nmoved:', moved);
v.name = (src.name || 'Variant') + ' + pins'; v.order = (src.order || 0) + 0.5;
v.note = `Copy of ${src.name || 'the variant'} with the pins of the macro, bias_gen, comp_ct, avg_sc, lpf_rc, r2r, Ctrim, dbg_tg, log_det det / ibias_det and the chain's vcm / ibias moved to the block edge facing what they connect to (orange rings). Floorplanning only: the blocks need a re-layout and the macro a new pin_order.cfg to match.`;
v.updatedAt = new Date().toISOString(); delete v.updatedBy; delete v.id;
fs.writeFileSync(process.argv[3], JSON.stringify(v));
