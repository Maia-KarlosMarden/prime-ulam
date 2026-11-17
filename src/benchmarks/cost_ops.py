# Copyright 2026 Karlos Marden Maia
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files.
"""Custo de decodificação (em XORs de pacote) para v5, v5+densas e 5G NR: peeling + eliminação gaussiana na parte residual.
 1 'XOR de pacote' = XOR de dois pacotes de T bytes (o mesmo vale para qualquer T).
uso: python3 -I cost_ops.py <dir v4> <dir 5G> <p> <padrões> <r densas>"""
import sys, random, json, time
HERE, BG, P, NP, RD = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]); sys.argv = [sys.argv[0], HERE, BG]; sys.path.insert(0, HERE)
from v5 import build, prep, ml_ok, build_5g
D = json.load(open(f"{HERE}/v5_p{P}.json")); K, n, M = 32 * P, 40 * P, D["MB"] * P
def v5code(r):
    c = build(P, D["MB"], D["masks"], D["punct"], D["passos"], D["a"], D["b"], D["g"], D["h"]); rr = random.Random(99); cols = list(c["cols"]); tx = list(c["tx"]); base = len(cols)
    for k in range(r):
        for v in range(K):
            if rr.random() < 0.5: cols[v] |= 1 << (M + k)
    for k in range(r): cols.append(1 << (M + k)); tx.append(base + k)
    c["cols"] = cols; c["tx"] = tx; c["R"] = M + r; c["nome"] = "Prime-Ulam v5" + (f" + {r} densas" if r else ""); return c
def decode_count(c, Ev):
    unk = set(Ev) | set(c["always"]); vr, rv = c["vrows"], c["rvars"]; cnt = {}
    for v in unk:
        for r in vr[v]: cnt[r] = cnt.get(r, 0) + 1
    stack = [r for r, k in cnt.items() if k == 1]; peel = 0
    while stack:
        r = stack.pop()
        if cnt[r] != 1: continue
        v = next(x for x in rv[r] if x in unk); unk.discard(v); peel += len(rv[r]) - 1
        for r2 in vr[v]:
            cnt[r2] -= 1
            if cnt[r2] == 1: stack.append(r2)
    if not unk: return True, peel, 0, 0, 0
    idx = {v: i for i, v in enumerate(sorted(unk))}; rows = []; rhs = 0
    for r in {r for v in unk for r in vr[v]}:
        m = 0
        for v in rv[r]:
            if v in unk: m |= 1 << idx[v]
        rhs += len(rv[r]) - bin(m).count("1"); rows.append(m)              # XORs para formar o lado direito: conhecidos da equação
    ge = 0; u = len(idx); rk = 0
    for col in range(u):
        bit = 1 << col; piv = next((i for i in range(rk, len(rows)) if rows[i] & bit), None)
        if piv is None: return False, peel, rhs, ge, u
        rows[rk], rows[piv] = rows[piv], rows[rk]; pr = rows[rk]
        for i in range(len(rows)):
            if i != rk and rows[i] & bit: rows[i] ^= pr; ge += 1
        rk += 1
    return True, peel, rhs, ge, u
if __name__ == "__main__":
    for c in (v5code(0), v5code(RD), build_5g(K, n, BG)):
        prep(c); nn = len(c["tx"])
        for f in (0.15, 0.17, 0.19):
            r = random.Random(int(f * 1000) + 3); e = round(f * n); S = []; ok = 0
            for _ in range(NP):
                Ev = [c["tx"][t] for t in r.sample(range(nn), e)]; good, pe, rh, ge, u = decode_count(c, Ev); assert good == ml_ok(c, Ev)
                if good: ok += 1; S.append((pe, rh, ge, u))
            if S:
                m = [sum(x[i] for x in S) / len(S) for i in range(4)]; tot = m[0] + m[1] + m[2]
                print(f"{c['nome']:24s} {f:.0%}: sucesso {ok}/{NP}  XORs de pacote por pacote de dados: peeling {m[0]/K:.2f} + lado direito {m[1]/K:.2f} + eliminação {m[2]/K:.2f} = {tot/K:.2f}  (incógnitas após peeling {m[3]:.0f})", flush=True)
