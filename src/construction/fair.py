# Copyright 2026 Karlos Marden Maia
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files.
"""Comparação em taxa IDÊNTICA (k=32p, n=40p): v5 pura  x  v5 + 16 densas gaussianas com 16 paridades esparsas NÃO transmitidas  x  5G NR.
As 16 paridades perfuradas ficam espaçadas uniformemente na cadeia e viram incógnitas (como os braços perfurados).
uso: python3 -I fair.py <dir v4> <dir 5G> <p> <padrões> <frações>"""
import sys, random, json
HERE, BG, P, T, FS = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), [float(x) for x in sys.argv[5].split(",")]
sys.argv = [sys.argv[0], HERE, BG]; sys.path.insert(0, HERE)
from v5 import build, prep, ml_ok, peel, build_5g, reduce
D = json.load(open(f"{HERE}/v5_p{P}.json")); K, n, M = 32 * P, 40 * P, D["MB"] * P; R_ = 16
QR = {(x * x) % P for x in range(1, P)}
def v5(): return build(P, D["MB"], D["masks"], D["punct"], D["passos"], D["a"], D["b"], D["g"], D["h"])
def fair():
    c = v5(); cols = list(c["cols"]); tx = list(c["tx"]); b0 = len(cols)
    for k in range(R_):
        a, b = (5 * k) % P, (7 * k + 1) % P
        for i in range(32):
            for j in range(P):
                if ((i - a) ** 2 + (j - b) ** 2) % P in QR: cols[i * P + j] |= 1 << (M + k)
    for k in range(R_): cols.append(1 << (M + k))
    punct_par = [K + (q * M) // R_ + M // (2 * R_) for q in range(R_)]          # 16 paridades esparsas espaçadas
    pos = {v: t for t, v in enumerate(tx)}
    for q, v in enumerate(punct_par): tx[pos[v]] = b0 + q                       # a paridade densa ocupa o lugar da perfurada
    c["cols"], c["tx"], c["R"] = cols, tx, M + R_; c["always"] = list(c["always"]) + punct_par
    c["nome"] = "v5 + 16 densas, 16 paridades perfuradas"; assert len(tx) == n and len(set(tx)) == n; return c
codes = [v5(), fair(), build_5g(K, n, BG)]
for c in codes: prep(c); assert len(c["tx"]) == n
for F in FS:
    r = random.Random(int(F * 1000) + 11); e = round(F * n); pats = [r.sample(range(n), e) for _ in range(T)]
    for c in codes:
        tx = c["tx"]; fail = 0; pe = 0
        for E in pats:
            Ev = [tx[t] for t in E]; ok = ml_ok(c, Ev); fail += not ok; pe += ok and peel(c, Ev) == 0
        print(f"p={P} {c['nome']:40s} n={n} e={e} ({F:.1%}): falhas {fail}/{T} = {fail/T:.1e}   só peeling {100*pe/T:.1f}%", flush=True)
