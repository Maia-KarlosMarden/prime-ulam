/* Copyright 2026 Karlos Marden Maia
 * SPDX-License-Identifier: Apache-2.0
 * Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files. */
/* Prime-Ulam LDPC - JavaScript port of the reference implementation (primeulam/*.py).
 * Works in the browser (window.PU) and in Node (module.exports). No dependencies.
 * Same formulas as paper Sections 3.2-3.6; peeling on the sparse equations, then GF(2) elimination. */
(function (root) {
  "use strict";
  const A = 32, RD = 16;
  const mod = (x, m) => ((x % m) + m) % m;

  function build(p, D) {
    const MB = D.MB, K = A * p, M = MB * p, n = 40 * p, R = M + RD, V = K + M + RD;
    const cols = Array.from({ length: V }, () => new Set());
    for (let i = 0; i < A; i++)
      for (let j = 0; j < p; j++)
        for (const c of D.masks[i])
          cols[i * p + j].add(MB * mod(D.a[c] * mod(j + D.passos[c] * i, p) + D.b[c], p) + c);
    for (let q = 0; q < M; q++) cols[K + q] = q === 0 ? new Set([0, M >> 1, M - 1]) : new Set([q - 1, q]);
    const punctPar = [];
    for (let q = 0; q < RD; q++) punctPar.push(K + Math.floor((q * M) / RD) + Math.floor(M / (2 * RD)));
    const qr = new Set();
    for (let x = 1; x < p; x++) qr.add((x * x) % p);
    for (let k = 0; k < RD; k++) {
      const a = (5 * k) % p, b = (7 * k + 1) % p;
      for (let i = 0; i < A; i++) for (let j = 0; j < p; j++)
        if (qr.has(((i - a) ** 2 + (j - b) ** 2) % p)) cols[i * p + j].add(M + k);
      cols[K + M + k] = new Set([M + k]);
    }
    const always = [];
    for (const i of D.punct) for (let j = 0; j < p; j++) always.push(i * p + j);
    for (const v of punctPar) always.push(v);
    const tarms = []; for (let i = 0; i < A; i++) if (!D.punct.includes(i)) tarms.push(i);
    const tx = []; let t = 0, q = 0;
    for (let x = 0; x < n; x++) {
      if (Math.floor(((x + 1) * M) / n) > Math.floor((x * M) / n)) { tx.push(K + ((D.h * q) % M)); q++; }
      else { tx.push(tarms[t % tarms.length] * p + ((D.g * t) % p)); t++; }
    }
    const pos = new Map(tx.map((v, s) => [v, s]));
    punctPar.forEach((v, k) => { tx[pos.get(v)] = K + M + k; });
    const colsA = cols.map(s => Array.from(s).sort((x, y) => x - y));
    const rows = Array.from({ length: R }, () => []);
    colsA.forEach((cs, v) => cs.forEach(r => rows[r].push(v)));
    return { p, D, K, M, n, R, V, cols: colsA, rows, tx, always };
  }

  /* Generic code from explicit columns: data variables 0..K-1, parities K..K+M-1 (one per equation).
   * dataRows[v] / parityRows[q]: equation indices of each variable. Every equation is peelable (M = R). */
  function fromLists(K, M, dataRows, parityRows, tx, label) {
    const R = M, V = K + M, n = tx.length;
    const cols = [];
    for (let v = 0; v < K; v++) cols.push(Array.from(new Set(dataRows[v])).sort((a, b) => a - b));
    for (let q = 0; q < M; q++) cols.push(Array.from(new Set(parityRows[q])).sort((a, b) => a - b));
    const rows = Array.from({ length: R }, () => []);
    cols.forEach((cs, v) => cs.forEach(r => rows[r].push(v)));
    return { p: null, label, K, M, n, R, V, cols, rows, tx: tx.slice(), always: [] };
  }

  function toCFormat(c) {
    const out = [`${c.V} ${c.K} ${c.R} ${c.n} ${c.always.length} ${c.M}`, c.always.join(" "), c.tx.join(" ")];
    for (const cs of c.cols) out.push(`${cs.length} ${cs.join(" ")}`);
    return out.join("\n") + "\n";
  }

  /* Resolve unknowns. unk: Uint8Array(V) (1 = unknown). vals: Array(V) of Uint8Array or null (structure only).
   * how (optional Uint8Array(V)) receives 1 = peeled, 2 = Gaussian. Returns {ok, peeled, residual, rank}. */
  function solve(c, unk, vals, how) {
    const { V, R, M, rows, cols } = c;
    const S = vals ? vals.find(x => x).length : 0;
    const xor = (d, s) => { for (let i = 0; i < S; i++) d[i] ^= s[i]; };
    const unknown = []; for (let v = 0; v < V; v++) if (unk[v]) unknown.push(v);
    const cnt = new Int32Array(R);
    for (const v of unknown) for (const r of cols[v]) cnt[r]++;
    const rhs = new Array(R).fill(null);
    if (vals) for (let r = 0; r < M; r++) if (cnt[r]) {
      const acc = new Uint8Array(S); for (const v of rows[r]) if (!unk[v]) xor(acc, vals[v]); rhs[r] = acc;
    }
    const stack = []; for (let r = 0; r < M; r++) if (cnt[r] === 1) stack.push(r);
    let peeled = 0;
    while (stack.length) {
      const r = stack.pop(); if (cnt[r] !== 1) continue;
      const v = rows[r].find(x => unk[x]);
      if (vals) vals[v] = rhs[r].slice();
      unk[v] = 0; peeled++; if (how) how[v] = 1;
      for (const r2 of cols[v]) { cnt[r2]--; if (r2 < M) { if (vals) xor(rhs[r2], vals[v]); if (cnt[r2] === 1) stack.push(r2); } }
    }
    const left = unknown.filter(v => unk[v]);
    const res = { ok: true, peeled, residual: left.length, rank: 0 };
    if (!left.length) return res;
    const u = left.length, W = (u + 31) >>> 5, uidx = new Map(left.map((v, i) => [v, i]));
    const pivMask = new Array(u).fill(null), pivPay = new Array(u).fill(null);
    let rank = 0;
    for (let r = 0; r < R; r++) {
      if (!cnt[r]) continue;
      const mask = new Uint32Array(W);
      for (const v of rows[r]) if (unk[v]) { const i = uidx.get(v); mask[i >>> 5] |= 1 << (i & 31); }
      let pay = null;
      if (vals) { pay = rhs[r] ? rhs[r].slice() : new Uint8Array(S); if (!rhs[r]) for (const v of rows[r]) if (!unk[v]) xor(pay, vals[v]); }
      for (;;) {
        let w = 0; while (w < W && mask[w] === 0) w++;
        if (w === W) break;
        const bit = (w << 5) + (31 - Math.clz32(mask[w] & -mask[w]));
        if (pivMask[bit] === null) { pivMask[bit] = mask; pivPay[bit] = pay; rank++; break; }
        const pm = pivMask[bit]; for (let k = w; k < W; k++) mask[k] ^= pm[k];
        if (vals) xor(pay, pivPay[bit]);
      }
    }
    res.rank = rank;
    if (rank < u) { res.ok = false; return res; }
    for (let bit = u - 1; bit >= 0; bit--) {
      const mask = pivMask[bit], pay = pivPay[bit];
      if (vals) for (let w = bit >>> 5; w < W; w++) {
        let m = mask[w]; if (w === bit >>> 5) m &= ~(1 << (bit & 31));
        while (m) { const lo = m & -m; const i = (w << 5) + (31 - Math.clz32(lo)); xor(pay, vals[left[i]]); m ^= lo; }
        // note: bits below `bit` are never set (lowest set bit is the pivot)
      }
      if (vals) vals[left[bit]] = pay;
    }
    for (const v of left) { unk[v] = 0; if (how) how[v] = 2; }
    return res;
  }

  function encode(c, data, S) {            /* data: Uint8Array(K*S) -> Array(n) of Uint8Array(S) */
    const vals = new Array(c.V).fill(null), unk = new Uint8Array(c.V);
    for (let v = 0; v < c.K; v++) vals[v] = data.slice(v * S, (v + 1) * S);
    for (let v = c.K; v < c.V; v++) { unk[v] = 1; vals[v] = new Uint8Array(S); }
    const r = solve(c, unk, vals);
    if (!r.ok) throw new Error("encoding failed");
    return c.tx.map(v => vals[v]);
  }

  function decode(c, packets, received, S) {   /* packets: Array(n) of Uint8Array|null; received: Uint8Array(n) */
    const vals = new Array(c.V).fill(null), unk = new Uint8Array(c.V).fill(1), how = new Uint8Array(c.V);
    for (let s = 0; s < c.n; s++) if (received[s]) { vals[c.tx[s]] = packets[s]; unk[c.tx[s]] = 0; }
    for (let v = 0; v < c.V; v++) if (!vals[v]) vals[v] = new Uint8Array(S);
    const r = solve(c, unk, vals, how);
    const data = new Uint8Array(c.K * S);
    if (r.ok) for (let v = 0; v < c.K; v++) data.set(vals[v], v * S);
    return Object.assign(r, { data: r.ok ? data : null, how, unk });
  }

  function analyze(c, lostSlots, how) {         /* structure only */
    const unk = new Uint8Array(c.V);
    for (const v of c.always) unk[v] = 1;
    for (const s of lostSlots) unk[c.tx[s]] = 1;
    const r = solve(c, unk, null, how);
    return Object.assign(r, { unk });
  }

  function mulberry32(a) {
    return function () { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  function sampleLost(n, e, rnd) {              /* exactly e distinct slots, uniformly */
    const idx = Array.from({ length: n }, (_, i) => i);
    for (let i = 0; i < e; i++) { const j = i + Math.floor(rnd() * (n - i)); const t = idx[i]; idx[i] = idx[j]; idx[j] = t; }
    return idx.slice(0, e);
  }
  function wilson(f, t, z = 1.96) {
    if (!t) return [0, 1];
    const ph = f / t, d = 1 + z * z / t, c0 = (ph + z * z / (2 * t)) / d;
    const h = z * Math.sqrt(ph * (1 - ph) / t + z * z / (4 * t * t)) / d;
    return [Math.max(0, c0 - h), Math.min(1, c0 + h)];
  }
  function simulate(c, loss, trials, seed) {
    const rnd = mulberry32(seed), e = Math.round(loss * c.n);
    let fail = 0, peelOnly = 0;
    for (let t = 0; t < trials; t++) { const r = analyze(c, sampleLost(c.n, e, rnd)); if (!r.ok) fail++; else if (!r.residual) peelOnly++; }
    const [lo, hi] = wilson(fail, trials);
    return { loss, erased: e, trials, failures: fail, rate: fail / trials, lo, hi, peelOnly: peelOnly / trials };
  }

  const PU = { build, fromLists, toCFormat, encode, decode, analyze, simulate, sampleLost, mulberry32, wilson };
  if (typeof module !== "undefined" && module.exports) module.exports = PU; else root.PU = PU;
})(typeof window !== "undefined" ? window : globalThis);
