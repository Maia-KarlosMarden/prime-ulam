"""Python ground truth for the demo's 5G NR codes (docs/demo/nr_codes.js).
Unknowns = never-transmitted variables plus erased transmitted ones; decoding succeeds iff their columns
of H are linearly independent over GF(2)."""
import json, os, random, shutil, subprocess, tempfile
import numpy as np
import pytest
from test_js_peg_crosscheck import gf2_independent

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def load():
    src = open(os.path.join(ROOT, "docs", "demo", "nr_codes.js"), encoding="utf-8").read()
    return json.loads(src[src.index("{"): src.rindex("}") + 1])


def test_js_nr_matches_python():
    codes = load()
    d = codes["37"]
    cols = [sum(1 << r for r in rows) for rows in d["rows"]]
    rng = random.Random(37)
    pats = []
    for loss in (0.15, 0.175, 0.19, 0.195):
        for _ in range(30):
            lost = rng.sample(range(d["n"]), round(loss * d["n"]))
            unknown = [cols[v] for v in d["always"]] + [cols[d["tx"][s]] for s in lost]
            pats.append({"lost": lost, "ok": bool(gf2_independent(unknown))})
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "case.json")
        json.dump({"37": {"nr": {"patterns": pats}}}, open(path, "w"))
        r = subprocess.run(["node", os.path.join(ROOT, "tests", "js_nr_crosscheck.js"), path],
                           capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
