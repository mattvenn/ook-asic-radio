// Floorplan engine: instances, orientations, pins, nets and the ranked-rule checks.
// Pure functions, no DOM: the page inlines this file, and `node layout/floorplan/page/check.js`
// runs the same checks on layout/floorplan/variants.json.
// Units: um, tile origin at its lower-left. A placement {x, y, orient} puts the lower-left
// corner of the transformed bbox at (x, y), as in floorplan.json.
(function (root) {
  'use strict';

  // GDS orientations as (rotation k * 90 deg CCW, mirror about the x axis first), the same
  // decomposition as KLayout's DCplxTrans(mag, rot, mirror, u).
  const ORIENTS = {
    R0: [0, false], R90: [1, false], R180: [2, false], R270: [3, false],
    MX: [0, true], MXR90: [1, true], MY: [2, true], MYR90: [3, true],
  };
  const ORIENT_OF = {};
  for (const [n, [k, m]] of Object.entries(ORIENTS)) ORIENT_OF[k + (m ? 'm' : '')] = n;

  function rotPt(k, m, x, y) {
    if (m) y = -y;
    for (let i = 0; i < k; i++) [x, y] = [-y, x];
    return [x, y];
  }
  // Placed size of a w x h cell.
  function placedSize(orient, w, h) { return ORIENTS[orient][0] % 2 ? [h, w] : [w, h]; }
  // Map a cell-local point (cell bbox lower-left = 0,0) to tile coordinates.
  function mapPt(pl, w, h, x, y) {
    const [k, m] = ORIENTS[pl.orient];
    const cs = [[0, 0], [w, 0], [0, h], [w, h]].map(([a, b]) => rotPt(k, m, a, b));
    const mx = Math.min(...cs.map(c => c[0])), my = Math.min(...cs.map(c => c[1]));
    const [px, py] = rotPt(k, m, x, y);
    return [pl.x + px - mx, pl.y + py - my];
  }
  function mapRect(pl, w, h, r) {
    const a = mapPt(pl, w, h, r[0], r[1]), b = mapPt(pl, w, h, r[0] + r[2], r[1] + r[3]);
    return [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.abs(a[0] - b[0]), Math.abs(a[1] - b[1])];
  }
  // Orientation after rotating 90 CCW / mirroring top-bottom (MX) / left-right (MY) on screen.
  function compose(orient, op) {
    let [k, m] = ORIENTS[orient];
    if (op === 'rot') k = (k + 1) % 4;
    else if (op === 'mx') { k = (4 - k) % 4; m = !m; }
    else if (op === 'my') { k = (6 - k) % 4; m = !m; }
    return ORIENT_OF[k + (m ? 'm' : '')];
  }

  // ---- the netlist of the tile (docs/floorplan_spec.md, "What goes in the tile" + "Nets")
  function buildCatalog(data) {
    const C = data.cells, cat = {};
    const ch = C.lna_chain;
    // zones of the real chain, for the rule checks: the input section (Cin, Rb, Mref), stage 1,
    // and stages 4-6 (from the o3 tap gap to the output end)
    const chainZones = { input: [0, 0, 69.5, ch.h], stage1: [69.5, 0, 37, ch.h], late: [171.5, 0, +(ch.w - 171.5).toFixed(2), ch.h] };
    const real = (inst, cell, extra) => Object.assign({ inst, cell, w: C[cell].w, h: C[cell].h, pins: C[cell].pins, m4: C[cell].m4 || [], group: 'rx' }, extra || {});
    // macro pins: even spread of pin_order.cfg slots (LibreLane), an estimate until the DEF is read
    const W = ['$', '$', 'tx_en', 'tx_en_n', '$', '$', '$', 'rx_en', 'dbg_en', '$', '$', '$', 'comp_in', 'sc_phi1', 'sc_phi2', '$', '$']
      .concat([0, 1, 2, 3, 4, 5, 6, 7].map(i => `trim_out[${i}]`)).concat(Array(25).fill('$'));
    const mpins = {};
    W.forEach((n, i) => { if (n !== '$') mpins[n] = { layer: 'met3', x: 0, y: +((i + 1) * 190 / (W.length + 1)).toFixed(2), est: true }; });
    const N = [];
    for (const b of ['uio_oe', 'uio_out', 'uo_out', 'uio_in', 'ui_in']) for (let i = 7; i >= 0; i--) N.push(`${b}[${i}]`);
    N.push('rst_n', 'clk');
    N.forEach((n, i) => { mpins[n] = { layer: 'met2', x: +((i + 1) * 260 / 83).toFixed(2), y: 190, est: true }; });
    const list = [
      { inst: 'macro', cell: 'radio_digital', w: 260, h: 190, reshape: true, halo: 5, pins: mpins, m4: [[0, 0, 260, 190]], group: 'dig', label: 'radio_digital' },
      real('xchain', 'lna_chain', { zones: chainZones }),
      real('xdet', 'log_det'), real('xlpf', 'lpf_rc'),
      real('xavg', 'avg_sc'),
      real('xcomp', 'comp_ct'),
      real('xdac', 'r2r', { group: 'trim', overDecap: true }),   // met1-only: a MIM decap may sit on top
      { inst: 'xctrim', cell: 'ctrim_1p', w: 23.5, h: 23.5, estimate: true, group: 'trim', label: 'Ctrim 1 pF',
        pins: { p: { layer: 'met3', x: 0.5, y: 11.75 }, n: { layer: 'met4', x: 23, y: 11.75 } }, m4: [[0, 0, 23.5, 23.5]] },
      real('xbias', 'bias_gen', { group: 'bias' }), real('xdbg', 'dbg_tg'),
      real('xtx.xring', 'tx_ring', { group: 'tx' }), real('xtx.xls', 'tx_ls', { group: 'tx' }),
      real('xtx.xlse_p', 'tx_ls_en', { group: 'tx' }), real('xtx.xlse_n', 'tx_ls_en', { group: 'tx' }),
      real('xtx.xdrv_p', 'tx_drv', { group: 'tx' }), real('xtx.xdrv_n', 'tx_drv', { group: 'tx' }),
    ];
    for (const b of list) cat[b.inst] = b;
    return cat;
  }
  const MIM_FF = 2.06;                 // fF / um2, cap_mim_m3_1 (xschem/gen/chain.py)
  const DECAPS = {
    xdeca: { cell: 'decap_vapwr', net: 'VAPWR', pf: 50, target: 18000, label: 'decap VAPWR' },
    xdecd: { cell: 'decap_vdpwr', net: 'VDPWR', pf: 30, target: 4100, label: 'decap VDPWR' },
  };

  // [name, class, from, to]; endpoints are "inst.pin" or "pad:<tile pin>"
  const NETS = [
    ['rx_p', 'rxin', 'pad:ua[0]', 'xchain.inp'], ['rx_n', 'rxin', 'pad:ua[1]', 'xchain.inn'],
    ['o1', 'rx', 'xchain.o1p', 'xdet.t1p'], ['o2', 'rx', 'xchain.o2p', 'xdet.t2p'], ['o3', 'rx', 'xchain.o3p', 'xdet.t3p'],
    ['o4', 'late', 'xchain.o4p', 'xdet.t4p'], ['o5', 'late', 'xchain.o5p', 'xdet.t5p'], ['out', 'late', 'xchain.outp', 'xdet.t6p'],
    ['det', 'rx', 'xdet.det', 'xlpf.in'], ['det dbg', 'rx', 'xdet.det', 'xdbg.a'], ['dbg', 'rx', 'xdbg.b', 'pad:ua[2]'],
    ['lpf', 'rx', 'xlpf.out', 'xavg.in'], ['lpf comp', 'rx', 'xlpf.out', 'xcomp.inp'], ['avg', 'rx', 'xavg.out', 'xcomp.inn'],
    ['comp_in', 'clk', 'xcomp.out', 'macro.comp_in'],
    ['sc_phi1', 'clk', 'macro.sc_phi1', 'xavg.phi1'], ['sc_phi2', 'clk', 'macro.sc_phi2', 'xavg.phi2'],
    ['rx_en', 'en', 'macro.rx_en', 'xbias.en'], ['dbg_en', 'en', 'macro.dbg_en', 'xdbg.en'],
    ['tx_en key', 'en', 'macro.tx_en', 'xtx.xring.en'], ['tx_en', 'en', 'macro.tx_en', 'xtx.xlse_p.in'], ['tx_en_n', 'en', 'macro.tx_en_n', 'xtx.xlse_n.in'],
    ['clk', 'clk', 'pad:clk', 'macro.clk'],
  ].concat([0, 1, 2, 3, 4, 5, 6, 7].map(i => [`trim[${i}]`, 'trim', `macro.trim_out[${i}]`, `xdac.b${i}`])).concat([
    ['dac', 'trim', 'xdac.out', 'xctrim.p'], ['trim', 'trim', 'xctrim.n', 'xcomp.trim'],
    ['ib_chain', 'bias', 'xbias.ib_chain', 'xchain.ibias'], ['vcm', 'bias', 'xbias.vcm', 'xchain.vcm'],
    ['ib_det', 'bias', 'xbias.ib_det', 'xdet.ibias_det'], ['ib_comp', 'bias', 'xbias.ib_comp', 'xcomp.ibias'],
    ['ring', 'tx', 'xtx.xring.out', 'xtx.xls.in'], ['a', 'tx', 'xtx.xls.A', 'xtx.xdrv_p.in'], ['b', 'tx', 'xtx.xls.B', 'xtx.xdrv_n.in'],
    ['enh_p', 'tx', 'xtx.xlse_p.A', 'xtx.xdrv_p.en'], ['enh_n', 'tx', 'xtx.xlse_n.A', 'xtx.xdrv_n.en'],
    ['tx_p', 'tx', 'xtx.xdrv_p.out', 'pad:ua[3]'], ['tx_n', 'tx', 'xtx.xdrv_n.out', 'pad:ua[4]'],
  ]);
  const NET_CLASSES = {
    rxin: 'RX input', rx: 'RX signal', late: 'RX late stages', clk: 'clock / switching', en: 'enable (static in RX)', bias: 'bias', tx: 'TX', trim: 'trim',
  };

  const DEFAULT_SETTINGS = {
    keepout: 2.5,          // um between blocks (guard rings)
    channel: 12,           // um: TT digital pins -> macro north pins routing channel along the top
    strapY: 5,             // straps run from strapY to H - strapY
    r1: 100, r2: 60, r3: 20, r4: 320, r5: 40, r6: 60, r8: 40,
    deca: 18000, decd: 4100,
  };

  // ---- geometry
  const area = r => r[2] * r[3];
  function rectGap(a, b) {         // Euclidean gap between two rects (0 if touching/overlapping)
    const dx = Math.max(0, b[0] - (a[0] + a[2]), a[0] - (b[0] + b[2]));
    const dy = Math.max(0, b[1] - (a[1] + a[3]), a[1] - (b[1] + b[3]));
    return Math.hypot(dx, dy);
  }
  function overlap(a, b) {
    const w = Math.min(a[0] + a[2], b[0] + b[2]) - Math.max(a[0], b[0]);
    const h = Math.min(a[1] + a[3], b[1] + b[3]) - Math.max(a[1], b[1]);
    return w > 1e-6 && h > 1e-6 ? w * h : 0;
  }
  const segRect = (s) => [Math.min(s[0], s[2]), Math.min(s[1], s[3]), Math.abs(s[2] - s[0]), Math.abs(s[3] - s[1])];
  function segCrosses(s, r, margin) {   // axis-aligned segment passes through rect interior (shrunk by margin)
    const m = margin || 0, q = [r[0] + m, r[1] + m, r[2] - 2 * m, r[3] - 2 * m];
    if (q[2] <= 0 || q[3] <= 0) return false;
    const sr = segRect(s);
    return sr[0] < q[0] + q[2] && sr[0] + sr[2] > q[0] && sr[1] < q[1] + q[3] && sr[1] + sr[3] > q[1];
  }
  const manhattan = (a, b) => Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]);
  // Two L-shaped candidate routes; pick the one crossing fewer obstacles (ties: horizontal first).
  function lRoute(a, b, obstacles) {
    const r1 = [[a[0], a[1], b[0], a[1]], [b[0], a[1], b[0], b[1]]];
    const r2 = [[a[0], a[1], a[0], b[1]], [a[0], b[1], b[0], b[1]]];
    if (!obstacles || !obstacles.length) return r1;
    const hits = r => obstacles.filter(o => r.some(s => segCrosses(s, o, 0.6))).length;
    return hits(r2) < hits(r1) ? r2 : r1;
  }

  // ---- placement
  // A variant: {name, note, place: {inst: {x, y, orient}}, decaps: {xdeca: [{x,y,w,h}], ...},
  //             straps: [{net, x, w}], est: {xctrim: {w, h}}}
  function resolve(cat, v) {
    const inst = {};
    for (const [n, c] of Object.entries(cat)) {
      const p = (v.place || {})[n];
      if (!p) continue;
      let w = c.w, h = c.h;
      const scaled = c.estimate || c.reshape;      // estimated blocks, and the macro (re-hardened at a new aspect ratio, same area)
      if (scaled && v.est && v.est[n]) { w = v.est[n].w; h = c.reshape ? (v.est[n].area || c.w * c.h) / w : v.est[n].h; }   // macro: est.area overrides the hardened area
      const pl = { x: p.x, y: p.y, orient: p.orient || 'R0' };
      const [pw, ph] = placedSize(pl.orient, w, h);
      const rect = [pl.x, pl.y, pw, ph];
      const pins = {};
      const sx = scaled ? w / c.w : 1, sy = scaled ? h / c.h : 1;
      const src = n === 'macro' ? macroPins(c, v) : c.pins;
      // moved pins (floorplanning): v.pins[inst][pin] = {x, y} in the block's own frame at its
      // placed size; they need a block re-layout (or, for the macro, a new pin_order.cfg)
      const mv = (v.pins || {})[n] || {};
      for (const [pn, pp] of Object.entries(src)) {
        const m = mv[pn];
        pins[pn] = Object.assign({}, pp, m ? { x: m.x, y: m.y, moved: true, at: mapPt(pl, w, h, m.x, m.y) } : { at: mapPt(pl, w, h, pp.x * sx, pp.y * sy) });
      }
      const m4 = (c.m4 || []).map(r => scaled ? [0, 0, w, h] : r).map(r => mapRect(pl, w, h, r));
      const zones = {};
      for (const [zn, z] of Object.entries(c.zones || {})) zones[zn] = mapRect(pl, w, h, z);
      inst[n] = { name: n, cat: c, pl, w, h, rect, pins, m4, zones,
        halo: c.halo ? [rect[0] - c.halo, rect[1] - c.halo, rect[2] + 2 * c.halo, rect[3] + 2 * c.halo] : null };
    }
    const decaps = [];
    for (const [n, d] of Object.entries(DECAPS)) ((v.decaps || {})[n] || []).forEach((r, i) =>
      decaps.push({ name: `${n}.${i + 1}`, base: n, idx: i, def: d, mim: !!r.mim, rect: [r.x, r.y, r.w, r.h] }));
    return { inst, decaps };
  }

  // The r2r trim drive (trim_out[7:0]) can move to another macro edge (a pin_order.cfg change
  // and a re-harden): W as hardened; S at the west end of the south edge; N after the 42 TT pins;
  // E at the same heights as on W. Coordinates in the 260 x 190 frame (scaled when reshaped).
  const TRIM_SIDES = { W: 'west (as hardened)', S: 'south', N: 'north', E: 'east' };
  function macroPins(c, v) {
    const side = (v.macroPins && v.macroPins.trim) || 'W';
    if (side === 'W') return c.pins;
    const p = Object.assign({}, c.pins);
    for (let i = 0; i < 8; i++) {
      const k = `trim_out[${i}]`, o = c.pins[k];
      const at = side === 'S' ? { x: +((i + 1) * 260 / 83).toFixed(2), y: 0 }
        : side === 'N' ? { x: +((i + 43) * 260 / 83).toFixed(2), y: 190 } : { x: 260, y: o.y };
      p[k] = Object.assign({}, o, at);
    }
    return p;
  }

  function pinAt(tile, R, ref) {
    if (ref.startsWith('pad:')) {
      const p = tile.pins[ref.slice(4)];
      if (!p) return null;
      return [(p.x0 + p.x1) / 2, p.y0 < 1 ? 0 : tile.h];
    }
    const i = ref.lastIndexOf('.');
    const ins = R.inst[ref.slice(0, i)];
    if (!ins) return null;
    const p = ins.pins[ref.slice(i + 1)];
    return p ? p.at : null;
  }

  function channelRect(tile, R, s) {
    const m = R.inst.macro;
    if (!s.channel || !m) return null;
    const x1 = Math.max(m.rect[0] + 3, m.pins.clk.at[0] + 3);    // to the last north pin (clk)
    return [15, tile.h - s.channel, Math.max(0, x1 - 15), s.channel];
  }

  function routeNets(tile, R) {
    const obst = Object.values(R.inst).map(i => i.rect);
    const out = [];
    for (const [name, cls, a, b] of NETS) {
      const pa = pinAt(tile, R, a), pb = pinAt(tile, R, b);
      if (!pa || !pb) { out.push({ name, cls, a, b, missing: true }); continue; }
      const ownA = a.startsWith('pad:') ? null : a.slice(0, a.lastIndexOf('.'));
      const ownB = b.startsWith('pad:') ? null : b.slice(0, b.lastIndexOf('.'));
      const others = Object.values(R.inst).filter(i => i.name !== ownA && i.name !== ownB).map(i => i.rect);
      out.push({ name, cls, a, b, pa, pb, len: manhattan(pa, pb), segs: lRoute(pa, pb, others) });
    }
    return out;
  }

  const fmt = (x, d) => (x === Infinity ? '-' : x.toFixed(d === undefined ? 0 : d));
  function minGapShapes(A, B) {     // A, B: arrays of rects or segments (as rects)
    let d = Infinity;
    for (const a of A) for (const b of B) d = Math.min(d, rectGap(a, b));
    return d;
  }

  // ---- checks: [{id, rule, title, status: pass|warn|fail|info, value, detail}]
  function evaluate(data, cat, v, settings) {
    const s = Object.assign({}, DEFAULT_SETTINGS, settings || {});
    const tile = data.tile, R = resolve(cat, v), nets = routeNets(tile, R);
    const I = R.inst, res = [];
    const add = (rule, title, status, value, detail) => res.push({ rule, title, status, value, detail: detail || '' });
    const netBy = n => nets.find(x => x.name === n);
    const segsOf = list => list.filter(n => n && !n.missing).flatMap(n => n.segs.map(segRect));
    const lvl = (x, pass, warn, higher) => higher ? (x >= pass ? 'pass' : x >= warn ? 'warn' : 'fail') : (x <= pass ? 'pass' : x <= warn ? 'warn' : 'fail');
    const chan = channelRect(tile, R, s);
    const missing = Object.keys(cat).filter(n => !I[n]);

    // inputs: chain input section + pad wires; late: stages 4-6, log_det's t4-t6 row and their tap wires
    const A = I.xchain, D = I.xdet, M = I.macro;
    const inputZone = A ? [A.zones.input].concat(segsOf([netBy('rx_p'), netBy('rx_n')])) : [];
    const stage1 = A ? [A.zones.stage1] : [];

    // 1. chain input far from the digital macro and the TT digital wires
    if (A && M) {
      const dM = minGapShapes(inputZone, [M.halo]);
      const dig = segsOf([netBy('clk')]).concat(chan ? [chan] : []);
      const dC = minGapShapes(inputZone, dig);
      const d = Math.min(dM, dC);
      const crossers = nets.filter(n => !n.missing && (n.cls === 'clk' || n.cls === 'trim') &&
        n.segs.some(sg => [A.rect].some(r => segCrosses(sg, r, 0.6))));
      add(1, 'Chain input far from the macro', crossers.length ? 'fail' : lvl(d, s.r1, s.r1 / 2, true),
        `${fmt(dM)} µm`, `input ↔ macro halo ${fmt(dM)} µm, ↔ TT channel / clk ${fmt(dC)} µm (want ≥ ${s.r1}).` +
        (crossers.length ? ` Digital wires over the chain: ${crossers.map(n => n.name).join(', ')}.` : ' No macro wire over the chain.'));
    } else add(1, 'Chain input far from the macro', 'info', '-', 'Place the chain and the macro.');

    // 2. late stages / detector t4-t6 away from the input
    if (A && D) {
      const tLate = ['t4p', 't5p', 't6p', 't4n', 't5n', 't6n'].map(p => D.pins[p].at).map(q => [q[0] - 1, q[1] - 1, 2, 2]);
      const late = [A.zones.late].concat(tLate, segsOf([netBy('o4'), netBy('o5'), netBy('out')]));
      const d = minGapShapes(late, inputZone.concat(stage1));
      const dOut = minGapShapes([[A.pins.outp.at[0] - 1, A.pins.outp.at[1] - 1, 2, 2]], inputZone);
      const cross = segsOf([netBy('o4'), netBy('o5'), netBy('out')]).some(sg => inputZone.concat(stage1).some(z => rectGap(sg, z) === 0));
      add(2, 'Late stages away from the input', cross ? 'fail' : lvl(d, s.r2, s.r2 / 2, true), `${fmt(d)} µm`,
        `closest late-stage shape (stages 4-6, t4-t6, their tap wires) to the input section, pad wires or stage 1: ${fmt(d)} µm; ` +
        `stage 6 output ↔ input ${fmt(dOut)} µm (want ≥ ${s.r2}).`);
    } else add(2, 'Late stages away from the input', 'info', '-', 'Place the chain and log_det.');

    // 3. clock edges off the RX
    {
      const ck = ['sc_phi1', 'sc_phi2', 'comp_in', 'clk'].map(netBy).filter(n => n && !n.missing);
      const rxr = [A, D].filter(Boolean).map(i => i.rect);
      const crossing = ck.filter(n => n.segs.some(sg => rxr.some(r => segCrosses(sg, r, 0.6))));
      const d = minGapShapes(segsOf(ck), rxr);
      add(3, 'Clock edges off the RX', crossing.length ? 'fail' : lvl(d, s.r3, s.r3 / 2, true), crossing.length ? 'crosses' : `${fmt(d)} µm`,
        (crossing.length ? `Crossing the chain / log_det: ${crossing.map(n => n.name).join(', ')}. ` : 'phi lines cross RX: no. ') +
        `phi1/2, comp_in, clk ↔ chain / log_det ${fmt(d)} µm (want ≥ ${s.r3}).`);
    }

    // 4. short analog path
    {
      const p = ['det', 'lpf', 'lpf comp', 'avg', 'dac', 'trim'].map(netBy).filter(n => n && !n.missing);
      const sum = p.reduce((a, n) => a + n.len, 0), avg = netBy('avg');
      add(4, 'Short analog path', p.length < 6 ? 'info' : lvl(sum, s.r4, s.r4 * 1.5), `${fmt(sum)} µm`,
        p.map(n => `${n.name} ${fmt(n.len)}`).join(', ') + (avg && !avg.missing ? `; avg_sc.out → comp_ct.inn ${fmt(avg.len)} µm` : ''));
    }

    // 5. TX at the pads
    {
      const tp = netBy('tx_p'), tn = netBy('tx_n');
      if (tp && tn && !tp.missing && !tn.missing) {
        const m = Math.max(tp.len, tn.len), en = ['tx_en', 'tx_en_n', 'tx_en key'].map(netBy).filter(n => n && !n.missing);
        add(5, 'TX at ua[3] / ua[4]', lvl(m, s.r5, s.r5 * 2), `${fmt(m)} µm`,
          `driver → pad: tx_p ${fmt(tp.len)}, tx_n ${fmt(tn.len)} µm (met3, 2.5 µm wide; want ≤ ${s.r5}). Enables from the macro: ${en.map(n => fmt(n.len)).join(' / ')} µm.`);
      } else add(5, 'TX at ua[3] / ua[4]', 'info', '-', 'Place the TX drivers.');
    }

    // 6. bias near the chain
    {
      const c = ['ib_chain', 'vcm'].map(netBy).filter(n => n && !n.missing), o = ['ib_det', 'ib_comp'].map(netBy).filter(n => n && !n.missing);
      if (c.length === 2) {
        const m = Math.max(...c.map(n => n.len));
        add(6, 'Bias next to the chain', lvl(m, s.r6, s.r6 * 2), `${fmt(m)} µm`,
          `ib_chain ${fmt(c[0].len)}, vcm ${fmt(c[1].len)} µm (want ≤ ${s.r6}); ` + o.map(n => `${n.name} ${fmt(n.len)}`).join(', ') + ' µm.');
      } else add(6, 'Bias next to the chain', 'info', '-', 'Place bias_gen and the chain.');
    }

    // 7. decaps
    for (const [n, d] of Object.entries(DECAPS)) {
      // decap tiles at the estimate's density (d.pf per target area); MIM-only rectangles over a block at 2.06 fF/um2
      const ds = R.decaps.filter(x => x.base === n), tgt = s[n === 'xdeca' ? 'deca' : 'decd'];
      const a = ds.filter(x => !x.mim).reduce((t, x) => t + area(x.rect), 0), am = ds.filter(x => x.mim).reduce((t, x) => t + area(x.rect), 0);
      const pf = d.pf * a / tgt + MIM_FF * am / 1000;
      add(7, `Decap ${d.net}`, lvl(pf / d.pf, 1, 0.7, true), `${fmt(100 * pf / d.pf)} %`,
        `≈ ${fmt(pf, 1)} of ${d.pf} pF: ${fmt(a)} µm² of decap tiles (of ${fmt(tgt)})` + (am ? ` + ${fmt(am)} µm² MIM over blocks` : '') + `, ${ds.length} rectangle(s).`);
    }

    // 8. TX vs RX (soft)
    {
      const tx = Object.values(I).filter(i => i.cat.group === 'tx');
      if (tx.length && A) {
        const d = minGapShapes(tx.map(i => i.rect), [A.zones.input].concat(stage1));
        add(8, 'TX away from the RX input', d >= s.r8 ? 'pass' : 'warn', `${fmt(d)} µm`,
          `TX blocks ↔ chain input section and stage 1: ${fmt(d)} µm (soft, want ≥ ${s.r8}; the TX is idle in RX).`);
      }
    }

    // 9. spacing, bounds, macro halo, routing channel
    {
      const boxes = Object.values(I).map(i => ({ n: i.name, r: i.rect, halo: i.halo, over: i.cat.overDecap })).concat(R.decaps.map(d => ({ n: d.name, r: d.rect, mim: d.mim })));
      const inside = (q, r) => q[0] >= r[0] - 1e-6 && q[1] >= r[1] - 1e-6 && q[0] + q[2] <= r[0] + r[2] + 1e-6 && q[1] + q[3] <= r[1] + r[3] + 1e-6;
      const stacked = (a, b) => (a.over && b.mim && inside(b.r, a.r)) || (b.over && a.mim && inside(a.r, b.r));   // MIM decap on top of a met1-only block
      const over = [], tight = [], outside = [], inChan = [];
      for (let i = 0; i < boxes.length; i++) {
        const a = boxes[i], r = a.r;
        if (r[0] < -1e-6 || r[1] < -1e-6 || r[0] + r[2] > tile.w + 1e-6 || r[1] + r[3] > tile.h + 1e-6) outside.push(a.n);
        if (chan && a.n !== 'macro' && overlap(r, chan) > 0) inChan.push(a.n);
        for (let j = i + 1; j < boxes.length; j++) {
          const b = boxes[j];
          const ra = a.halo || r, rb = b.halo || b.r;
          if (stacked(a, b)) continue;
          if (overlap(ra, rb) > 0.01) over.push(`${a.n} / ${b.n}`);
          else if (!a.halo && !b.halo && rectGap(r, b.r) < s.keepout - 1e-3) tight.push(`${a.n} / ${b.n} ${fmt(rectGap(r, b.r), 1)}`);
        }
      }
      add(9, 'Overlaps and spacing', over.length || outside.length ? 'fail' : tight.length ? 'warn' : 'pass',
        over.length ? `${over.length} overlap${over.length > 1 ? 's' : ''}` : tight.length ? `${tight.length} tight` : 'none',
        (over.length ? `Overlapping (halo counts): ${over.join(', ')}. ` : 'overlaps: none. ') +
        (outside.length ? `Outside the tile: ${outside.join(', ')}. ` : '') +
        (tight.length ? `Closer than ${s.keepout} µm: ${tight.join(', ')}.` : `All gaps ≥ ${s.keepout} µm.`));
      if (chan) {
        const above = M ? tile.h - (M.rect[1] + M.rect[3]) : 0;
        const st = inChan.length ? 'fail' : above + 1e-6 < s.channel ? 'fail' : 'pass';
        add(9, 'TT pin channel clear', st, `${fmt(above, 1)} µm`,
          `42 TT pins (x 15-131) to the macro's north pins need a ~${s.channel} µm channel along the top; ${fmt(above, 1)} µm above the macro body.` +
          (inChan.length ? ` Blocks in the channel: ${inChan.join(', ')}.` : '') +
          (above + 1e-6 < s.channel ? ' The north pins can only be reached from above: move the macro down, or re-harden with these pins on the west edge.' : ''));
      }
    }

    // straps: full-height met4 lanes must clear every met4 / MIM shape and the macro
    {
      const ys = s.strapY, obs = Object.values(I).flatMap(i => i.m4.map(r => ({ n: i.name, r }))).concat(R.decaps.filter(d => d.mim).map(d => ({ n: d.name, r: d.rect })));
      const issues = [], nets = new Set();
      (v.straps || []).forEach((st, i) => {
        nets.add(st.net);
        const lane = [st.x - 0.3, ys, st.w + 0.6, tile.h - 2 * ys];
        const hit = [...new Set(obs.filter(o => overlap(lane, o.r) > 0).map(o => o.n))];
        if (hit.length) issues.push(`${st.net} @ ${fmt(st.x, 1)} blocked by ${hit.join(', ')} met4`);
        if (st.w < 1.2) issues.push(`${st.net} @ ${fmt(st.x, 1)} narrower than 1.2 µm`);
        (v.straps || []).slice(i + 1).forEach(o => { if (rectGap([st.x, 0, st.w, 1], [o.x, 0, o.w, 1]) < 0.3) issues.push(`${st.net} / ${o.net} straps touch`); });
      });
      const miss = ['VDPWR', 'VAPWR', 'VGND'].filter(n => !nets.has(n));
      add('P', 'Power straps', issues.length ? 'fail' : miss.length ? 'warn' : 'pass',
        issues.length ? `${issues.length} blocked` : miss.length ? `missing ${miss.join(', ')}` : `${(v.straps || []).length} clear`,
        issues.length ? issues.join('; ') + '.' : `${(v.straps || []).length} strap(s), every lane clear of met4 and MIM.` + (miss.length ? ` No strap for ${miss.join(', ')}.` : ''));
    }
    if (missing.length) add('-', 'Unplaced blocks', 'warn', `${missing.length}`, missing.join(', '));

    // area panel
    const macroBox = M ? M.halo : [0, 0, 0, 0];
    const tileA = tile.w * tile.h;
    const sig = Object.values(I).filter(i => i.name !== 'macro').reduce((t, i) => t + i.w * i.h, 0);
    const dec = R.decaps.filter(d => !d.mim).reduce((t, d) => t + area(d.rect), 0);   // MIM over blocks uses no extra area
    const decTarget = s.deca + s.decd;
    const areaInfo = { tile: tileA, macro: area(macroBox), free: tileA - area(macroBox), signal: sig, decap: dec, decapTarget: decTarget,
      spacing: 0.1 * (sig + dec), need: 1.1 * (sig + decTarget) };
    return { checks: res, nets, R, area: areaInfo, settings: s, channel: chan };
  }

  // floorplan.json (docs/floorplan_spec.md, "Export/import")
  function exportJSON(data, cat, v) {
    const R = resolve(cat, v), blocks = [];
    for (const i of Object.values(R.inst)) {
      const [k, m] = ORIENTS[i.pl.orient];
      const b = { inst: i.name, cell: i.cat.cell, x: +i.rect[0].toFixed(2), y: +i.rect[1].toFixed(2), orient: i.pl.orient,
        rot: k * 90, mirror: m, estimate: !!i.cat.estimate };
      if (i.cat.estimate || (i.cat.reshape && (Math.abs(i.w - i.cat.w) > 1e-6 || Math.abs(i.h - i.cat.h) > 1e-6))) { b.w = +i.w.toFixed(3); b.h = +i.h.toFixed(3); }
      if (i.cat.reshape && Math.abs(i.w - i.cat.w) < 1e-6 && Math.abs(i.h - i.cat.h) > 1e-6) b.note = `re-harden at ${b.w} x ${b.h} um`;
      if (i.cat.reshape && Math.abs(i.w - i.cat.w) > 1e-6) b.note = `re-harden at ${b.w} x ${b.h} um (${(i.w * i.h).toFixed(0)} um2; hardened ${i.cat.w} x ${i.cat.h} = ${i.cat.w * i.cat.h} um2)`;
      blocks.push(b);
    }
    for (const d of R.decaps) blocks.push(Object.assign({ inst: d.base, part: d.idx + 1, cell: d.def.cell, x: d.rect[0], y: d.rect[1], w: d.rect[2], h: d.rect[3], orient: 'R0', rot: 0, mirror: false, estimate: true }, d.mim ? { mim: true, note: 'MIM only (cap_mim_m3_1), on top of a met1-only block' } : {}));
    return {
      variant: v.name, note: v.note || '', tile: { w: data.tile.w, h: data.tile.h }, blocks,
      macro_pins: { 'trim_out[7:0]': (v.macroPins && v.macroPins.trim) || 'W' },
      pins_moved: Object.fromEntries(Object.entries(v.pins || {}).filter(([, ps]) => Object.keys(ps).length).map(([i, ps]) => [i, Object.fromEntries(Object.entries(ps).map(([p, q]) => [p, [+q.x.toFixed(2), +q.y.toFixed(2)]]))])),
      pins_note: 'pins_moved: [x, y] in each block\'s own frame (lower-left = 0, 0, before its orientation); they need a block re-layout, or for the macro a new pin_order.cfg.',
      straps: (v.straps || []).map(s => ({ net: s.net, x: s.x, w: s.w })),
      transform: 'x, y = lower-left of the placed bbox. KLayout: t = DCplxTrans(1, rot, mirror, 0, 0); bb = cell.dbbox().transformed(t); place with DCplxTrans(1, rot, mirror, x - bb.left, y - bb.bottom).',
    };
  }
  function importJSON(cat, j) {
    const v = { name: j.variant || 'Imported', note: j.note || '', place: {}, decaps: {}, straps: (j.straps || []).map(s => ({ net: s.net, x: +s.x, w: +s.w })), est: {} };
    const ts = j.macro_pins && j.macro_pins['trim_out[7:0]']; if (TRIM_SIDES[ts]) v.macroPins = { trim: ts };
    if (j.pins_moved) { v.pins = {}; for (const [i, ps] of Object.entries(j.pins_moved)) { if (!cat[i]) continue; v.pins[i] = {}; for (const [p, xy] of Object.entries(ps)) v.pins[i][p] = { x: +xy[0], y: +xy[1] }; } }
    for (const b of j.blocks || []) {
      if (DECAPS[b.inst]) { (v.decaps[b.inst] = v.decaps[b.inst] || []).push(Object.assign({ x: +b.x, y: +b.y, w: +b.w, h: +b.h }, b.mim ? { mim: true } : {})); continue; }
      const n = b.inst;
      if (!cat[n]) continue;
      v.place[n] = { x: +b.x, y: +b.y, orient: ORIENTS[b.orient] ? b.orient : 'R0' };
      if ((cat[n].estimate || cat[n].reshape) && b.w && b.h) { v.est[n] = { w: +b.w, h: +b.h }; if (cat[n].reshape && Math.abs(b.w * b.h - cat[n].w * cat[n].h) > 1) v.est[n].area = +b.w * +b.h; }
    }
    return v;
  }

  root.FP = { TRIM_SIDES, ORIENTS, placedSize, mapPt, mapRect, compose, buildCatalog, DECAPS, NETS, NET_CLASSES, DEFAULT_SETTINGS,
    resolve, routeNets, evaluate, exportJSON, importJSON, rectGap, overlap, channelRect };
})(typeof window !== 'undefined' ? window : globalThis);
