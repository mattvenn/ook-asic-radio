// Seed placer for the floorplan variants: anneals the movable blocks of each variant spec
// around its fixed anchors, fills the leftover space with decap and picks clear strap lanes.
//   node layout/floorplan/page/place.js        -> writes layout/floorplan/variants.json
// The variants are starting points for the page; Matt refines them there.
const fs = require('fs');
const path = require('path');
require('./engine.js');
const FP = globalThis.FP;
const dir = path.join(__dirname, '..');
const data = {
  tile: JSON.parse(fs.readFileSync(path.join(dir, 'tile.json'))),
  cells: JSON.parse(fs.readFileSync(path.join(dir, 'blocks.json'))),
};
const CAT = FP.buildCatalog(data), W = data.tile.w, H = data.tile.h, S = FP.DEFAULT_SETTINGS, K = S.keepout;
const ORS = Object.keys(FP.ORIENTS);

let seed = 12345;
const rnd = () => ((seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff);
const gauss = () => Math.sqrt(-2 * Math.log(rnd() + 1e-12)) * Math.cos(2 * Math.PI * rnd());

// per instance and orientation: placed size and pin offsets from the placed lower-left
function geom(n, est) {
  const c = CAT[n], w = est ? est.w : c.w, h = est ? est.h : c.h, g = {};
  for (const o of ORS) {
    const pl = { x: 0, y: 0, orient: o }, [pw, ph] = FP.placedSize(o, w, h), pins = {};
    const sx = est ? w / c.w : 1, sy = est ? h / c.h : 1;
    for (const [pn, p] of Object.entries(c.pins)) pins[pn] = FP.mapPt(pl, w, h, p.x * sx, p.y * sy);
    g[o] = { w: pw, h: ph, pins };
  }
  return g;
}

const TXLOGIC = ['xtx.xring', 'xtx.xls', 'xtx.xlse_p', 'xtx.xlse_n'];
const WEIGHT = {
  det: 3, lpf: 3, 'lpf comp': 3, avg: 4, 'det dbg': 1.5, dbg: 0.1, trim: 4, dac: 1,
  comp_in: 1.5, sc_phi1: 1, sc_phi2: 1, rx_en: 0.05, dbg_en: 0.05, 'tx_en key': 0.3, tx_en: 0.3, tx_en_n: 0.3,
  ib_chain: 3, vcm: 3, ib_det: 0.4, ib_comp: 0.4, ring: 2, a: 2, b: 2, enh_p: 1, enh_n: 1, tx_p: 4, tx_n: 4,
};
for (let i = 0; i < 8; i++) WEIGHT[`trim[${i}]`] = 0.4;

function solve(spec, iters) {
  const est = spec.est || {};
  const G = {};
  for (const n of Object.keys(CAT)) G[n] = geom(n, est[n]);
  const fixed = spec.fixed, mov = spec.movable;
  const st = {};
  for (const [n, p] of Object.entries(fixed)) st[n] = Object.assign({}, p);
  for (const n of mov) st[n] = spec.start && spec.start[n] ? Object.assign({}, spec.start[n]) : { x: rnd() * 200, y: rnd() * 200, orient: ORS[(rnd() * 8) | 0] };
  const allowed = spec.orients || {};
  const macro = st.macro, mg = G.macro.R0;
  const halo = [macro.x - 5, macro.y - 5, mg.w + 10, mg.h + 10];
  const chan = [15, H - S.channel, macro.x + 135 - 15, S.channel];
  const keepouts = [halo, chan].concat(spec.keepouts || []);
  const rect = (n) => { const g = G[n][st[n].orient]; return [st[n].x, st[n].y, g.w, g.h]; };
  const pin = (ref) => {
    if (ref.startsWith('pad:')) { const p = data.tile.pins[ref.slice(4)]; return [(p.x0 + p.x1) / 2, p.y0 < 1 ? 0 : H]; }
    const i = ref.lastIndexOf('.'), n = ref.slice(0, i), q = G[n][st[n].orient].pins[ref.slice(i + 1)];
    return [st[n].x + q[0], st[n].y + q[1]];
  };
  const nets = FP.NETS.filter(([nm, , a, b]) => {
    const own = (r) => r.startsWith('pad:') ? null : r.slice(0, r.lastIndexOf('.'));
    return mov.includes(own(a)) || mov.includes(own(b));
  });
  const inside = (r, area) => { const w = Math.max(0, Math.min(r[0] + r[2], area[0] + area[2]) - Math.max(r[0], area[0])), h = Math.max(0, Math.min(r[1] + r[3], area[1] + area[3]) - Math.max(r[1], area[1])); return w * h; };
  function cost() {
    let c = 0;
    const names = Object.keys(st).filter(n => n !== 'macro');
    const R = {}; for (const n of names) R[n] = rect(n);
    for (const n of mov) {
      const r = R[n];
      // stay inside the tile (with the keep-out from the edge only at the top/bottom pins: none)
      c += 5000 * ((r[2] * r[3]) - inside(r, [0, 0, W, H]));
      for (const k of keepouts) c += 5000 * inside(r, k);
      for (const m of names) {
        if (m === n || (mov.indexOf(m) !== -1 && mov.indexOf(m) < mov.indexOf(n))) continue;
        const e = [R[m][0] - K, R[m][1] - K, R[m][2] + 2 * K, R[m][3] + 2 * K];
        c += 5000 * inside(r, e);
      }
      for (const z of spec.zones && spec.zones[n] ? [spec.zones[n]] : []) c += 5000 * ((r[2] * r[3]) - inside(r, z));
    }
    for (const [nm, cls, a, b] of nets) {
      const pa = pin(a), pb = pin(b);
      c += (WEIGHT[nm] || 0.5) * (Math.abs(pa[0] - pb[0]) + Math.abs(pa[1] - pb[1]));
      if (cls === 'clk' || cls === 'trim' || cls === 'rx' || cls === 'late') {
        const ownA = a.startsWith('pad:') ? '' : a.slice(0, a.lastIndexOf('.')), ownB = b.startsWith('pad:') ? '' : b.slice(0, b.lastIndexOf('.'));
        const segs1 = [[pa[0], pa[1], pb[0], pa[1]], [pb[0], pa[1], pb[0], pb[1]]], segs2 = [[pa[0], pa[1], pa[0], pb[1]], [pa[0], pb[1], pb[0], pb[1]]];
        const hits = (segs) => names.filter(m => m !== ownA && m !== ownB).filter(m => segs.some(s => crosses(s, R[m]))).length;
        c += (cls === 'clk' ? 250 : cls === 'trim' ? 40 : 120) * Math.min(hits(segs1), hits(segs2));
      }
    }
    return c;
  }
  function crosses(s, r) {
    const q = [r[0] + 0.6, r[1] + 0.6, r[2] - 1.2, r[3] - 1.2];
    const x0 = Math.min(s[0], s[2]), x1 = Math.max(s[0], s[2]), y0 = Math.min(s[1], s[3]), y1 = Math.max(s[1], s[3]);
    return x0 < q[0] + q[2] && x1 > q[0] && y0 < q[1] + q[3] && y1 > q[1];
  }
  let cur = cost(), best = Infinity, bestSt = JSON.parse(JSON.stringify(st));
  const T0 = 400, T1 = 0.05;
  for (let it = 0; it < iters; it++) {
    const t = it / iters, T = T0 * Math.pow(T1 / T0, t), sig = 60 * Math.pow(0.5 / 60, t);
    const n = mov[(rnd() * mov.length) | 0], old = Object.assign({}, st[n]);
    let other = null, oldO = null;
    const r = rnd();
    if (r < 0.12) { const os = allowed[n] || ORS; st[n].orient = os[(rnd() * os.length) | 0]; }
    else if (r < 0.17 && mov.length > 1) {
      other = mov[(rnd() * mov.length) | 0]; if (other === n) other = null;
      if (other) { oldO = Object.assign({}, st[other]); [st[n].x, st[other].x] = [st[other].x, st[n].x]; [st[n].y, st[other].y] = [st[other].y, st[n].y]; }
    } else if (r < 0.2 && t < 0.6) { st[n].x = rnd() * (W - 20); st[n].y = rnd() * (H - 20); }
    else { st[n].x += gauss() * sig; st[n].y += gauss() * sig; }
    if (t > 0.85) { st[n].x = Math.round(st[n].x * 2) / 2; st[n].y = Math.round(st[n].y * 2) / 2; }
    const c = cost();
    if (c <= cur || rnd() < Math.exp((cur - c) / T)) {
      cur = c;
      if (t > 0.85 && c < best) { best = c; bestSt = JSON.parse(JSON.stringify(st)); }
    } else { st[n] = old; if (other) st[other] = oldO; }
  }
  return { place: bestSt, cost: best };
}

// Fill free space with decap rectangles (1 um grid), largest first.
function fillDecap(spec, v) {
  const R = FP.resolve(CAT, v), G = 1, nx = Math.floor(W / G), ny = Math.floor(H / G);
  const occ = new Uint8Array(nx * ny);
  const mark = (r, pad) => {
    const x0 = Math.max(0, Math.floor((r[0] - pad) / G)), x1 = Math.min(nx, Math.ceil((r[0] + r[2] + pad) / G));
    const y0 = Math.max(0, Math.floor((r[1] - pad) / G)), y1 = Math.min(ny, Math.ceil((r[1] + r[3] + pad) / G));
    for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) occ[y * nx + x] = 1;
  };
  for (const i of Object.values(R.inst)) mark(i.halo || i.rect, i.halo ? 0 : K);
  mark([15, H - S.channel, R.inst.macro.rect[0] + 120, S.channel], 0);
  for (const k of spec.keepouts || []) mark(k, 0);
  for (const k of spec.wireKeepouts || []) mark(k, 0);
  mark([0, 0, W, 1.5], 0); mark([0, H - 1.5, W, 1.5], 0);    // tile pins
  const rects = [];
  for (;;) {
    // largest empty rectangle by the histogram method
    const hgt = new Int32Array(nx); let best = null;
    for (let y = 0; y < ny; y++) {
      for (let x = 0; x < nx; x++) hgt[x] = occ[y * nx + x] ? 0 : hgt[x] + 1;
      const stack = [];
      for (let x = 0; x <= nx; x++) {
        const hh = x < nx ? hgt[x] : 0; let start = x;
        while (stack.length && stack[stack.length - 1][1] >= hh) {
          const [sx, sh] = stack.pop(); const w = x - sx;
          if (sh >= 8 && w >= 8 && (!best || w * sh > best[2] * best[3])) best = [sx, y - sh + 1, w, sh];
          start = sx;
        }
        stack.push([start, hh]);
      }
    }
    if (!best || best[2] * best[3] < 200) break;
    rects.push(best.map(q => q * G));
    mark(best.map(q => q * G), K);
  }
  // VDPWR decap (RX supply) from the rectangles nearest the RX, the rest VAPWR
  const rxc = R.inst['xdet'].rect, cx = rxc[0] + rxc[2] / 2, cy = rxc[1] + rxc[3] / 2;
  rects.sort((a, b) => Math.hypot(a[0] + a[2] / 2 - cx, a[1] + a[3] / 2 - cy) - Math.hypot(b[0] + b[2] / 2 - cx, b[1] + b[3] / 2 - cy));
  const decaps = { xdeca: [], xdecd: [] }; let dA = 0;
  for (const r of rects) {
    const box = { x: r[0], y: r[1], w: r[2], h: r[3] };
    if (dA < S.decd && r[2] * r[3] <= 1.6 * (S.decd - dA) + 400 && r[0] < R.inst.macro.rect[0]) { decaps.xdecd.push(box); dA += r[2] * r[3]; }
    else decaps.xdeca.push(box);
  }
  return decaps;
}

// Strap lanes: clear of every met4 / MIM shape over the strap's height
function straps(spec, v) {
  const R = FP.resolve(CAT, v), obs = Object.values(R.inst).flatMap(i => i.m4);
  const clear = (x, w) => !obs.some(r => r[0] < x + w + 0.3 && r[0] + r[2] > x - 0.3 && r[1] < H - S.strapY && r[1] + r[3] > S.strapY)
    && !(spec.strapAvoid || []).some(([a, b]) => x < b && x + w > a);
  const out = [];
  for (const [net, want] of spec.straps) {
    let bx = null;
    for (let d = 0; d < 60 && bx === null; d += 0.1) for (const x of [want + d, want - d]) if (x >= 0.3 && x + 1.2 <= W - 0.3 && clear(x, 1.2) && !out.some(s => Math.abs(s.x - x) < 1.6)) { bx = Math.round(x * 10) / 10; break; }
    if (bx !== null) out.push({ net, x: bx, w: 1.2 });
  }
  return out;
}

const SPECS = [
  {
    id: 'A', name: 'A: RX left, TX middle, macro right', runs: 10, iters: 250000,
    fixed: {
      macro: { x: 228.12, y: 23.76, orient: 'R0' },
      'xchain.a': { x: 51.6, y: 3, orient: 'MXR90' }, 'xchain.b': { x: 89.36, y: 176, orient: 'R0' },
      xdet: { x: 89.36, y: 142.4, orient: 'MX' }, xbias: { x: 0, y: 3, orient: 'R270' },
      'xtx.xdrv_n': { x: 102.7, y: 3, orient: 'MYR90' }, 'xtx.xdrv_p': { x: 131.9, y: 3, orient: 'R270' },
    },
    movable: ['xlpf', 'xavg', 'xcomp', 'xctrim', 'xdac', 'xdbg'].concat(TXLOGIC),
    zones: Object.assign({}, ...['xlpf', 'xavg', 'xcomp', 'xctrim', 'xdac', 'xdbg'].map(n => ({ [n]: [89.36, 0, 131.26, 211.26] })),
      ...TXLOGIC.map(n => ({ [n]: [89.36, 0, 403, 18.76] }))),
    keepouts: [[86.86, 0, 15.8, 50]],         // the ua[2]/ua[3] input wires
    straps: [['VGND', 49.6], ['VDPWR', 87.6], ['VAPWR', 221.4], ['VGND', 488.6], ['VDPWR', 490.1], ['VAPWR', 491.6]],
  },
  {
    id: 'B', name: 'B: A with the macro at the top edge', runs: 10, iters: 250000,
    fixed: {
      macro: { x: 228.12, y: 35.76, orient: 'R0' },
      'xchain.a': { x: 51.6, y: 3, orient: 'MXR90' }, 'xchain.b': { x: 89.36, y: 176, orient: 'R0' },
      xdet: { x: 89.36, y: 142.4, orient: 'MX' }, xbias: { x: 0, y: 3, orient: 'R270' },
      'xtx.xdrv_n': { x: 102.7, y: 3, orient: 'MYR90' }, 'xtx.xdrv_p': { x: 131.9, y: 3, orient: 'R270' },
    },
    movable: ['xlpf', 'xavg', 'xcomp', 'xctrim', 'xdac', 'xdbg'].concat(TXLOGIC),
    zones: Object.assign({}, ...['xlpf', 'xavg', 'xcomp', 'xctrim', 'xdac', 'xdbg'].map(n => ({ [n]: [89.36, 0, 131.26, 211.26] })),
      ...TXLOGIC.map(n => ({ [n]: [89.36, 0, 403, 30.76] }))),
    keepouts: [[86.86, 0, 15.8, 50]],
    straps: [['VGND', 49.6], ['VDPWR', 87.6], ['VAPWR', 221.4], ['VGND', 488.6], ['VDPWR', 490.1], ['VAPWR', 491.6]],
  },
  {
    id: 'C', name: 'C: chain far left, signal path along the top', runs: 8, iters: 150000,
    fixed: {
      macro: { x: 228.12, y: 23.76, orient: 'R0' },
      'xchain.a': { x: 2, y: 3, orient: 'MXR90' }, 'xchain.b': { x: 39.76, y: 176, orient: 'R0' },
      xdet: { x: 39.76, y: 142.4, orient: 'MX' },
      'xtx.xdrv_n': { x: 102.7, y: 3, orient: 'MYR90' }, 'xtx.xdrv_p': { x: 131.9, y: 3, orient: 'R270' },
    },
    movable: ['xbias', 'xlpf', 'xavg', 'xcomp', 'xctrim', 'xdac', 'xdbg'].concat(TXLOGIC),
    zones: { xlpf: [100, 113, 123, 113], xavg: [100, 113, 123, 113], xcomp: [100, 100, 123, 126] },
    keepouts: [[37.26, 0, 65.4, 45]],         // the input wires from ua[2]/ua[3] along the bottom
    straps: [['VGND', 38.5], ['VDPWR', 0.6], ['VAPWR', 221.4], ['VGND', 488.6], ['VDPWR', 490.1], ['VAPWR', 491.6]],
  },
];

const NOTES = {
  A: `The spec's A with the chain folded into two GDS-true parts. Stages 1-3 run up from the pads (input end at ua[2]/ua[3], ` +
    `bias_gen beside it for short ib_chain / vcm), stages 4-6 turn right along the top, so the stage-6 output ends ~150 µm from the input. ` +
    `log_det sits in the corner of the L and takes taps from both legs. TX drivers sit on ua[0]/ua[1], between the RX input and the macro. ` +
    `The macro sits 12 µm below the top edge to leave the TT-pin channel to its north pins.\n` +
    `Open: the chain fold needs a lna_chain re-layout (the straight 268 µm chain fits nowhere in the tile); decap is short of 50 + 30 pF.`,
  B: `A with the macro body on the top edge, so the strip under the macro becomes one ~31 µm decap band (easier to tile).\n` +
    `Fails as hardened: the macro's 42 north pins can then only be reached from outside the tile. B needs the macro re-hardened ` +
    `with those pins moved to the top of its west edge (pin_order.cfg #W), which also shortens the TT-pin wiring.`,
  C: `The chain at the far left edge, its late stages along the top-left, and the detector -> LPF -> avg -> comp path in the upper middle, ` +
    `away from the chain input. bias_gen is free to move, so ib_chain / vcm get longer.\n` +
    `The macro's comp_in / sc_phi pins are low on its west edge (y ~72-80), so those wires climb along the macro in the halo gap; ` +
    `moving them up the west edge (pin_order.cfg) would shorten them.`,
};

const out = [];
for (const spec of SPECS) {
  let best = null;
  for (let run = 0; run < (spec.runs || 6); run++) {
    seed = 1000 + run * 7919 + spec.id.charCodeAt(0);
    const r = solve(spec, spec.iters || 60000);
    if (!best || r.cost < best.cost) best = r;
  }
  const v = { id: spec.id, name: spec.name, note: NOTES[spec.id], order: out.length, place: best.place, est: spec.est || {}, decaps: {}, straps: [] };
  v.decaps = fillDecap(spec, v);
  v.straps = straps(spec, v);
  out.push(v);
  console.error(spec.id, 'cost', best.cost.toFixed(0));
}
fs.writeFileSync(path.join(dir, 'variants.json'), JSON.stringify({ variants: out }, null, 1) + '\n');
