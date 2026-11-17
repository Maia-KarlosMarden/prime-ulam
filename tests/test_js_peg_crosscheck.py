"""Python ground truth for the demo's PEG codes: on erasure patterns of transmitted slots, decoding succeeds
iff the columns of H for the erased variables are linearly independent over GF(2) (no never-sent variables)."""
import json, os, random, shutil, subprocess, sys, tempfile
import numpy as np
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def gf2_independent(cols):
    """cols: list of int bitmasks over rows. True iff linearly independent over GF(2)."""
    basis = {}
    for c in cols:
        while c:
            h = c.bit_length() - 1
            if h in basis:
                c ^= basis[h]
            else:
                basis[h] = c
                break
        else:
            return False
    return True


def load_codes():
    src = open(os.path.join(ROOT, "docs", "demo", "peg_codes.js"), encoding="utf-8").read()
    return json.loads(src[src.index("{"): src.rindex("}") + 1])


@pytest.mark.parametrize("p", ["37"])
def test_js_peg_matches_python(p):
    d = load_codes()[p]
    cases = {}
    for variant in ("acc", "ident"):
        par = d["acc"] if variant == "acc" else d["ident"]
        cols = [sum(1 << r for r in rows) for rows in d["data"]] + [sum(1 << r for r in rows) for rows in par]
        rng = random.Random(int(p) + (7 if variant == "ident" else 0))
        pats = []
        for loss in (0.15, 0.175, 0.19):
            for _ in range(30):
                lost = rng.sample(range(d["n"]), round(loss * d["n"]))
                ok = gf2_independent([cols[d["tx"][s]] for s in lost])
                pats.append({"lost": lost, "ok": bool(ok)})
        cases[variant] = {"patterns": pats}
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "case.json")
        json.dump({p: cases}, open(path, "w"))
        r = subprocess.run(["node", os.path.join(ROOT, "tests", "js_peg_crosscheck.js"), path],
                           capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
