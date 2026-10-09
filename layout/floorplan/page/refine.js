// Refine a variant: keep some blocks fixed, anneal the rest assuming pins will be moved to facing
// edges (block-to-block gaps, not GDS pin positions), refill decap, re-pick strap lanes.
//   node layout/floorplan/page/refine.js in.json out.json [--decap-only]
// in.json: a variant document. The spec below names the fixed and movable blocks for Matt layout 3.
// Floorplanning only: run pinfit.js on the result to move the pins.
require('./engine.js');
const fs = require('fs'), path = require('path'), FP = globalThis.FP;
const dir = path.join(__dirname, '..');
const data = { tile: JSON.parse(fs.readFileSync(path.join(dir, 'tile.json'))), cells: JSON.parse(fs.readFileSync(path.join(dir, 'blocks.json'))) };
const cat = FP.buildCatalog(data), W = data.tile.w, H = data.tile.h, S = FP.DEFAULT_SETTINGS, K = S.keepout;
const src = JSON.parse(fs.readFileSync(process.argv[2]));

const MOVE = ['xdet', 'xavg', 'xcomp', 'xdac', 'xctrim', 'xdbg', 'xtx.xring', 'xtx.xls', 'xtx.xlse_p', 'xtx.xlse_n'];
const ORS = { xdet: ['R0', 'MX', 'MY', 'R180'] };
const ALL8 = Object.keys(FP.ORIENTS);
const ZONE = {                                   // where each movable block may go
  'xtx.xring': [0, 0, 85, 100], 'xtx.xls': [0, 0, 85, 100], 'xtx.xlse_p': [0, 0, 85, 100], 'xtx.xlse_n': [0, 0, 85, 100],
};
// pins that can move (facing-edge assumption); everything else is at its GDS position
const MOVABLE_PIN = (n, p) => ['macro', 'xbias', 'xcomp', 'xavg', 'xlpf', 'xdac', 'xctrim', 'xdbg'].includes(n)
  || (n === 'xdet' && (p === 'det' || p === 'ibias_det')) || (n === 'xchain' && (p === 'vcm' || p === 'ibias'));
const WT = { det: 3, lpf: 2, 'lpf comp': 2, avg: 4, dac: 2, trim: 4, comp_in: 1.5, sc_phi1: 1, sc_phi2: 1, 'det dbg': 1, dbg: 0.3,
  rx_en: 0.3, dbg_en: 0.3, 'tx_en key': 0.5, tx_en: 0.5, tx_en_n: 0.5, ib_chain: 3, vcm: 3, ib_det: 0.5, ib_comp: 0.5,
  ring: 2, a: 2, b: 2, enh_p: 1, enh_n: 1, tx_p: 4, tx_n: 4, o1: 3, o2: 2, o3: 1, o4: 1, o5: 1, out: 1 };
for (let i = 0; i < 8; i++) WT[`trim[${i}]`] = 0.3;

const gapM = (a, b) => Math.max(0, b[0] - (a[0] + a[2]), a[0] - (b[0] + b[2])) + Math.max(0, b[1] - (a[1] + a[3]), a[1] - (b[1] + b[3]));
const ptRect = (p, r) => gapM([p[0], p[1], 0, 0], r);
const ovl = (a, b) => Math.max(0, Math.min(a[0] + a[2], b[0] + b[2]) - Math.max(a[0], b[0])) * Math.max(0, Math.min(a[1] + a[3], b[1] + b[3]) - Math.max(a[1], b[1]));
const grow = (r, k) => [r[0] - k, r[1] - k, r[2] + 2 * k, r[3] + 2 * k];

let seed = 7;
const rnd = () => ((seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff);
const gauss = () => Math.sqrt(-2 * Math.log(rnd() + 1e-12)) * Math.cos(2 * Math.PI * rnd());

function cost(v) {
  const R = FP.resolve(cat, v), I = R.inst, M = I.macro;
  let c = 0;
  const chanSh = FP.channelShapes(data.tile, R, S);
  const names = Object.keys(I);
  for (const n of MOVE) {
    const r = I[n].rect;
    c += 5000 * (r[2] * r[3] - ovl(r, [0, 0, W, H]));
    c += 5000 * ovl(r, M.halo) + chanSh.reduce((t, q) => t + 5000 * ovl(r, q), 0);
    if (ZONE[n]) c += 5000 * (r[2] * r[3] - ovl(r, ZONE[n]));
    for (const m of names) if (m !== n && m !== 'macro' && !(MOVE.indexOf(m) !== -1 && MOVE.indexOf(m) < MOVE.indexOf(n))) c += 5000 * ovl(r, grow(I[m].rect, K));
  }
  for (const [nm, cls, a, b] of FP.NETS) {
    const end = (ref) => {
      if (ref.startsWith('pad:')) { const p = data.tile.pins[ref.slice(4)]; return { pt: [(p.x0 + p.x1) / 2, p.y0 < 1 ? 0 : H] }; }
      const i = ref.lastIndexOf('.'), n = ref.slice(0, i), p = ref.slice(i + 1), ins = I[n];
      if (!ins) return null;
      return MOVABLE_PIN(n, p) ? { rect: ins.rect } : { pt: ins.pins[p].at };
    };
    const A = end(a), B = end(b);
    if (!A || !B) continue;
    const d = A.pt && B.pt ? Math.abs(A.pt[0] - B.pt[0]) + Math.abs(A.pt[1] - B.pt[1]) : A.pt ? ptRect(A.pt, B.rect) : B.pt ? ptRect(B.pt, A.rect) : gapM(A.rect, B.rect);
    c += (WT[nm] || 0.5) * d;
  }
  // rule 2: log_det's late inputs (t4-t6) >= 60 um from the input section and stage 1
  const ch = I.xchain, D = I.xdet, z = [ch.zones.input, ch.zones.stage1];
  for (const t of ['t4p', 't5p', 't6p', 't4n', 't5n', 't6n']) { const d = Math.min(...z.map(r => ptRect(D.pins[t].at, r))); if (d < 62) c += 300 * (62 - d); }
  // the stage-1 tap must not run over the late stages: penalise o1/o2 pins past the stage-3 tap
  const lateX0 = ch.zones.late[0];
  for (const t of ['t1p', 't2p']) { const x = D.pins[t].at[0]; if (x > lateX0) c += 40 * (x - lateX0); }
  // switching blocks (r2r, comp_ct, avg_sc) away from the input and stage 1
  for (const n of ['xdac', 'xcomp', 'xavg']) { const d = Math.min(...z.map(r => gapM(I[n].rect, r))); if (d < 100) c += 20 * (100 - d); }
  return c;
}

function anneal(v0, iters) {
  let v = JSON.parse(JSON.stringify(v0)), cur = cost(v), best = cur, bestV = JSON.parse(JSON.stringify(v));
  for (let it = 0; it < iters; it++) {
    const t = it / iters, T = 300 * Math.pow(0.05 / 300, t), sig = 40 * Math.pow(0.5 / 40, t);
    const n = MOVE[(rnd() * MOVE.length) | 0], old = Object.assign({}, v.place[n]);
    const r = rnd();
    if (r < 0.15) { const os = ORS[n] || ALL8; v.place[n].orient = os[(rnd() * os.length) | 0]; }
    else if (r < 0.2 && t < 0.5) { v.place[n].x = rnd() * (W - 20); v.place[n].y = rnd() * 100; }
    else { v.place[n].x += gauss() * sig; v.place[n].y += gauss() * sig; }
    if (t > 0.85) { v.place[n].x = Math.round(v.place[n].x * 2) / 2; v.place[n].y = Math.round(v.place[n].y * 2) / 2; }
    const c = cost(v);
    if (c <= cur || rnd() < Math.exp((cur - c) / T)) { cur = c; if (t > 0.85 && c < best) { best = c; bestV = JSON.parse(JSON.stringify(v)); } }
    else v.place[n] = old;
  }
  return { v: bestV, cost: best };
}

// decap: largest free rectangles (1 um grid), VDPWR first near the RX, the rest VAPWR
function fillDecap(v) {
  const R = FP.resolve(cat, v), nx = Math.floor(W), ny = Math.floor(H), occ = new Uint8Array(nx * ny);
  const mark = (r, pad) => { const x0 = Math.max(0, Math.floor(r[0] - pad)), x1 = Math.min(nx, Math.ceil(r[0] + r[2] + pad)), y0 = Math.max(0, Math.floor(r[1] - pad)), y1 = Math.min(ny, Math.ceil(r[1] + r[3] + pad));
    for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) occ[y * nx + x] = 1; };
  for (const i of Object.values(R.inst)) mark(i.halo || i.rect, i.halo ? 0 : K);
  for (const q of FP.channelShapes(data.tile, R, S)) mark(q, 0);
  mark([0, 0, W, 1.5], 0); mark([0, H - 1.5, W, 1.5], 0);
  // keep the RX pad wires and the chain input free: no decap below the chain's input end
  const ch = R.inst.xchain; mark([ch.rect[0] - 10, 0, 90, ch.rect[1]], 0);
  const rects = [];
  for (;;) {
    const hgt = new Int32Array(nx); let best = null;
    for (let y = 0; y < ny; y++) {
      for (let x = 0; x < nx; x++) hgt[x] = occ[y * nx + x] ? 0 : hgt[x] + 1;
      const st = [];
      for (let x = 0; x <= nx; x++) { const hh = x < nx ? hgt[x] : 0; let s0 = x;
        while (st.length && st[st.length - 1][1] >= hh) { const [sx, sh] = st.pop(), w = x - sx; if (sh >= 6 && w >= 6 && (!best || w * sh > best[2] * best[3])) best = [sx, y - sh + 1, w, sh]; s0 = sx; }
        st.push([s0, hh]); }
    }
    if (!best || best[2] * best[3] < 120) break;
    rects.push(best); mark(best, K);
  }
  const rx = R.inst.xchain.rect, cx = rx[0] + rx[2] / 2, cy = rx[1] + rx[3];
  rects.sort((a, b) => Math.hypot(a[0] + a[2] / 2 - cx, a[1] + a[3] / 2 - cy) - Math.hypot(b[0] + b[2] / 2 - cx, b[1] + b[3] / 2 - cy));
  const out = { xdeca: [], xdecd: [] }; let dd = 0;
  for (const r of rects) { const b = { x: r[0], y: r[1], w: r[2], h: r[3] }; if (dd < S.decd) { out.xdecd.push(b); dd += r[2] * r[3]; } else out.xdeca.push(b); }
  return out;
}

let v = JSON.parse(JSON.stringify(src));
if (!process.argv.includes('--decap-only')) {      // --decap-only: keep the placement, refill decap
  let best = null;
  for (let run = 0; run < 6; run++) { seed = 101 + run * 7919; const r = anneal(src, 120000); if (!best || r.cost < best.cost) best = r; console.error('run', run, r.cost.toFixed(0)); }
  v = best.v;
}
v.decaps = fillDecap(v);
fs.writeFileSync(process.argv[3], JSON.stringify(v));
