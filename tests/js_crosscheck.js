/* Copyright 2026 Karlos Marden Maia
 * SPDX-License-Identifier: Apache-2.0
 * Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files. */
const fs = require("fs"), path = require("path");
const PU = require(path.join(__dirname, "..", "docs", "demo", "primeulam.js"));
const kase = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
let bad = 0;
const fail = m => { console.log("MISMATCH:", m); bad++; };
for (const p of Object.keys(kase)) {
  const D = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "primeulam", "params", `v5_p${p}.json`), "utf8"));
  const c = PU.build(+p, D), k = kase[p];
  if (PU.toCFormat(c) !== k.export) fail(`p=${p}: exported code differs from Python`);
  k.patterns.forEach((pt, i) => { if (PU.analyze(c, pt.lost).ok !== pt.ok) fail(`p=${p} pattern ${i}: verdict differs`); });
  const S = 8, data = Uint8Array.from(k.data), pk = PU.encode(c, data, S);
  if (Buffer.compare(Buffer.concat(pk.map(x => Buffer.from(x))), Buffer.from(k.packets)) !== 0) fail(`p=${p}: encoded packets differ`);
  const rec = new Uint8Array(c.n).fill(1); PU.sampleLost(c.n, Math.round(0.15 * c.n), PU.mulberry32(3)).forEach(s => rec[s] = 0);
  const r = PU.decode(c, pk.map((x, s) => rec[s] ? x : null), rec, S);
  if (!r.ok || Buffer.compare(Buffer.from(r.data), Buffer.from(data)) !== 0) fail(`p=${p}: payload decode wrong`);
  console.log(`p=${p}: export, ${k.patterns.length} verdicts, encode and decode checked`);
}
process.exit(bad ? 1 : 0);
