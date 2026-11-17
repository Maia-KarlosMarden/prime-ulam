// Cross-check of the demo's 5G NR code against Python verdicts (see test_js_nr_crosscheck.py).
const fs = require("fs"), path = require("path"), vm = require("vm");
const PU = require(path.join(__dirname, "..", "docs", "demo", "primeulam.js"));
const ctx = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "..", "docs", "demo", "nr_codes.js"), "utf8"), ctx);
const NR = ctx.window.NR_CODES;
const kase = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
let bad = 0; const fail = m => { console.log("MISMATCH:", m); bad++; };
for (const p of Object.keys(kase)) {
  const d = NR[p];
  const c = PU.fromRaw(d.K, d.R, d.V, d.rows, d.tx, d.always, d.label);
  kase[p].nr.patterns.forEach((pt, i) => { if (PU.analyze(c, pt.lost).ok !== pt.ok) fail(`p=${p} pattern ${i}`); });
  const S = 4, data = new Uint8Array(c.K * S); for (let i = 0; i < data.length; i++) data[i] = (i * 37 + 11) & 255;
  const pk = PU.encode(c, data, S), rec = new Uint8Array(c.n).fill(1);
  PU.sampleLost(c.n, Math.round(0.15 * c.n), PU.mulberry32(3)).forEach(s => rec[s] = 0);
  const r = PU.decode(c, pk.map((x, s) => rec[s] ? x : null), rec, S);
  if (!r.ok || Buffer.compare(Buffer.from(r.data), Buffer.from(data)) !== 0) fail(`p=${p} payload`);
  console.log(`p=${p} ${d.label}: ${kase[p].nr.patterns.length} verdicts and payload round trip checked`);
}
process.exit(bad ? 1 : 0);
