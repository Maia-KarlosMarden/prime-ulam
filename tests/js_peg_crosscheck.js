// Cross-check of the demo's PEG codes (docs/demo/peg_codes.js) against Python verdicts.
const fs = require("fs"), path = require("path");
const PU = require(path.join(__dirname, "..", "docs", "demo", "primeulam.js"));
const vm = require("vm");
const ctx = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "..", "docs", "demo", "peg_codes.js"), "utf8"), ctx);
const PEG = ctx.window.PEG_CODES;
const kase = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
let bad = 0; const fail = m => { console.log("MISMATCH:", m); bad++; };
for (const p of Object.keys(kase)) {
  for (const variant of ["acc", "ident"]) {
    const d = PEG[p];
    const par = variant === "acc" ? d.acc : d.ident;
    const c = PU.fromLists(d.K, d.M, d.data, par, d.tx, variant);
    const k = kase[p][variant];
    k.patterns.forEach((pt, i) => { if (PU.analyze(c, pt.lost).ok !== pt.ok) fail(`p=${p} ${variant} pattern ${i}`); });
    const S = 4, data = new Uint8Array(c.K * S); for (let i = 0; i < data.length; i++) data[i] = (i * 37 + 11) & 255;
    const pk = PU.encode(c, data, S), rec = new Uint8Array(c.n).fill(1);
    PU.sampleLost(c.n, Math.round(0.15 * c.n), PU.mulberry32(3)).forEach(s => rec[s] = 0);
    const r = PU.decode(c, pk.map((x, s) => rec[s] ? x : null), rec, S);
    if (!r.ok || Buffer.compare(Buffer.from(r.data), Buffer.from(data)) !== 0) fail(`p=${p} ${variant} payload`);
    console.log(`p=${p} ${variant}: ${k.patterns.length} verdicts and a payload round trip checked`);
  }
}
process.exit(bad ? 1 : 0);
