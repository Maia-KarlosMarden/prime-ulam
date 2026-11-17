# Copyright 2026 Karlos Marden Maia
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files.
"""Command line interface: ``primeulam <command>`` (or ``python -m primeulam <command>``).

Typical third-party test, end to end with real files::

    primeulam selftest
    primeulam encode photo.jpg packets/ --p 37
    primeulam lose packets/ --loss 0.15 --seed 1      # deletes random packet files
    primeulam decode packets/ photo_restored.jpg
    cmp photo.jpg photo_restored.jpg
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time

import numpy as np

from . import __version__
from .code import PrimeUlamCode, available_primes
from .sim import simulate

# Reference values published in the paper (Section 4.1, p = 37, 150,000 patterns)
PAPER_REF_37 = {0.175: "0 failures / 150,000", 0.19: "1.3e-4 (19/150,000)", 0.195: "2.4% (3,531/150,000)"}


def _packet_name(block: int, slot: int) -> str:
    return f"b{block:04d}_s{slot:04d}.pkt"


def cmd_info(a) -> int:
    c = PrimeUlamCode(a.p)
    d = c.description_size()
    print(c)
    print(f"  data symbols k = {c.K}   transmitted n = {c.n}   sparse parities M = {c.M}   dense equations = 16")
    print(f"  never transmitted: {len(c.always)} variables (2 arms x p data + 16 replaced parities)")
    print(f"  description: prime p + {d['integers_besides_p']} integers + incidence table "
          f"({d['incidence_memberships']} memberships)")
    print(f"  length-4 cycles in the sparse part: {c.sparse_c4_pairs()}  (theorem: 0)")
    print(f"  validated primes: {available_primes()}")
    return 0


def cmd_selftest(a) -> int:
    ok = True
    for p in a.p or available_primes():
        c = PrimeUlamCode(p)
        c4 = c.sparse_c4_pairs()
        rng = np.random.default_rng(2026)
        data = rng.integers(0, 256, (c.K, 32), dtype=np.uint8)
        pk = c.encode(data)
        mask = np.ones(c.n, dtype=bool)
        mask[rng.choice(c.n, round(0.15 * c.n), replace=False)] = False
        r = c.decode(pk, mask)
        good = r.ok and bool((r.data == data).all())
        checks = {"rate 0.80": abs(c.rate - 0.8) < 1e-12 and c.n == 40 * p,
                  "no length-4 cycle (sparse part)": c4 == 0,
                  "encode/decode round trip at 15% loss": good}
        print(f"p = {p}  (n = {c.n}, k = {c.K})")
        for k, v in checks.items():
            print(f"  [{'OK' if v else 'FAIL'}] {k}")
        ok &= all(checks.values())
    print("SELFTEST", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


def cmd_simulate(a) -> int:
    c = PrimeUlamCode(a.p)
    print(f"{c}; {a.trials} random erasure patterns per loss, seed {a.seed}")
    print(f"{'loss':>7} {'erased':>7} {'failures':>9} {'rate':>10}  {'95% CI (Wilson)':>22}  {'peeling only':>12}")
    for L in a.loss:
        t0 = time.time()
        r = simulate(c, L, a.trials, a.seed)
        print(f"{L:7.1%} {r['erased']:7d} {r['failures']:9d} {r['failure_rate']:10.2e}  "
              f"[{r['ci_low']:.1e}, {r['ci_high']:.1e}]  {r['peeling_only_rate']:11.1%}"
              f"   ({time.time() - t0:.1f}s)")
        if a.p == 37 and L in PAPER_REF_37:
            print(f"        paper (p=37): {PAPER_REF_37[L]}")
    return 0


def cmd_encode(a) -> int:
    c = PrimeUlamCode(a.p)
    with open(a.input, "rb") as f:
        raw = f.read()
    S = a.symbol_size
    cap = c.K * S
    nblocks = max(1, -(-len(raw) // cap))
    os.makedirs(a.outdir, exist_ok=True)
    for b in range(nblocks):
        chunk = raw[b * cap:(b + 1) * cap]
        buf = np.zeros(cap, dtype=np.uint8)
        buf[:len(chunk)] = np.frombuffer(chunk, dtype=np.uint8)
        pk = c.encode(buf.reshape(c.K, S))
        for s in range(c.n):
            with open(os.path.join(a.outdir, _packet_name(b, s)), "wb") as f:
                f.write(pk[s].tobytes())
    meta = {"format": "primeulam-packets-1", "version": __version__, "p": a.p, "symbol_size": S,
            "blocks": nblocks, "n": c.n, "k": c.K, "length": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(), "source": os.path.basename(a.input)}
    with open(os.path.join(a.outdir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"{len(raw)} bytes -> {nblocks} block(s) x {c.n} packets of {S} bytes in {a.outdir}/ "
          f"(rate 0.80 = 1.25x nominal overhead; the last block is zero-padded)")
    return 0


def cmd_lose(a) -> int:
    with open(os.path.join(a.dir, "meta.json")) as f:
        meta = json.load(f)
    rng = random.Random(a.seed)
    total = 0
    for b in range(meta["blocks"]):
        present = [s for s in range(meta["n"]) if os.path.exists(os.path.join(a.dir, _packet_name(b, s)))]
        e = round(a.loss * meta["n"])
        for s in rng.sample(present, min(e, len(present))):
            os.remove(os.path.join(a.dir, _packet_name(b, s)))
            total += 1
    print(f"deleted {total} packet files ({a.loss:.1%} of each block)")
    return 0


def cmd_decode(a) -> int:
    with open(os.path.join(a.dir, "meta.json")) as f:
        meta = json.load(f)
    c = PrimeUlamCode(meta["p"])
    S = meta["symbol_size"]
    out = bytearray()
    for b in range(meta["blocks"]):
        sym = np.zeros((c.n, S), dtype=np.uint8)
        mask = np.zeros(c.n, dtype=bool)
        for s in range(c.n):
            path = os.path.join(a.dir, _packet_name(b, s))
            if os.path.exists(path):
                with open(path, "rb") as f:
                    sym[s] = np.frombuffer(f.read(), dtype=np.uint8)
                mask[s] = True
        r = c.decode(sym, mask)
        print(f"block {b}: received {int(mask.sum())}/{c.n} ({1 - mask.mean():.1%} lost) -> "
              f"{'recovered' if r.ok else 'FAILED'}  [peeled {r.stats.peeled}, "
              f"Gaussian residual {r.stats.residual}, packet XORs {r.stats.xors}]")
        if not r.ok:
            print(f"  only {r.recovered_data}/{c.K} data symbols determined; "
                  "the erased columns of H are linearly dependent (loss too close to, or above, the 20% limit)")
            return 2
        out += r.data.tobytes()
    out = bytes(out[:meta["length"]])
    ok = hashlib.sha256(out).hexdigest() == meta["sha256"]
    with open(a.output, "wb") as f:
        f.write(out)
    print(f"wrote {len(out)} bytes to {a.output}; sha256 {'matches' if ok else 'DOES NOT MATCH'} the original")
    return 0 if ok else 3


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="primeulam", description="Prime-Ulam LDPC erasure code prototype")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("info", help="describe the code for a prime")
    s.add_argument("--p", type=int, default=37)
    s.set_defaults(fn=cmd_info)

    s = sub.add_parser("selftest", help="rate, no-C4 theorem and a round trip, for every shipped prime")
    s.add_argument("--p", type=int, nargs="*")
    s.set_defaults(fn=cmd_selftest)

    s = sub.add_parser("simulate", help="Monte-Carlo failure rate on the erasure channel")
    s.add_argument("--p", type=int, default=37)
    s.add_argument("--loss", type=float, nargs="+", default=[0.15, 0.175, 0.19, 0.195])
    s.add_argument("--trials", type=int, default=1000)
    s.add_argument("--seed", type=int, default=1)
    s.set_defaults(fn=cmd_simulate)

    s = sub.add_parser("encode", help="encode a file into packet files")
    s.add_argument("input")
    s.add_argument("outdir")
    s.add_argument("--p", type=int, default=37)
    s.add_argument("--symbol-size", type=int, default=1024)
    s.set_defaults(fn=cmd_encode)

    s = sub.add_parser("lose", help="delete a random fraction of the packet files (simulates the channel)")
    s.add_argument("dir")
    s.add_argument("--loss", type=float, required=True)
    s.add_argument("--seed", type=int, default=1)
    s.set_defaults(fn=cmd_lose)

    s = sub.add_parser("decode", help="reconstruct the file from the surviving packet files")
    s.add_argument("dir")
    s.add_argument("output")
    s.set_defaults(fn=cmd_decode)

    a = ap.parse_args(argv)
    try:
        return a.fn(a)
    except (ValueError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
