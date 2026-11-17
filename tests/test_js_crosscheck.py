# Copyright 2026 Karlos Marden Maia
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files.
"""Cross-check the JavaScript port (docs/demo/primeulam.js) against the Python reference.

Python draws erasure patterns and computes the verdict; Node must reproduce the C-format export
byte for byte and the verdict (and recovered data) on the very same patterns."""
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from primeulam import PrimeUlamCode  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def test_js_matches_python():
    case = {}
    for p in (37, 127):
        c = PrimeUlamCode(p)
        rng = random.Random(p)
        pats = []
        for loss in (0.10, 0.17, 0.19, 0.195, 0.205):
            for _ in range(15):
                lost = rng.sample(range(c.n), round(loss * c.n))
                pats.append({"lost": lost, "ok": bool(c.decodable(lost)[0])})
        data = np.random.default_rng(p).integers(0, 256, (c.K, 8), dtype=np.uint8)
        case[str(p)] = {"export": c.to_c_format(), "patterns": pats,
                        "data": data.flatten().tolist(), "packets": c.encode(data).flatten().tolist()}
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "case.json")
        json.dump(case, open(path, "w"))
        r = subprocess.run(["node", os.path.join(ROOT, "tests", "js_crosscheck.js"), path],
                           capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
