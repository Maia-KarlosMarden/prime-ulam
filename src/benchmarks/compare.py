# Copyright 2026 Karlos Marden Maia
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files.
"""Comparação no mesmo (k, n): Prime-Ulam v3 (fórmula)  x  5G NR LDPC (TS 38.212)  x  PEG + acumulador.
uso: python3 -I compare.py <p> <T> <dir pu3> <dir com 5G_bg*.csv>"""
import sys, json, random, time
sys.path.insert(0, sys.argv[3])
from pu3 import chain_pos, cols_from_pos, tx_formula

# ---------- 5G NR ----------
SETS = [[2,4,8,16,32,64,128,256],[3,6,12,24,48,96,192,384],[5,10,20,40,80,160,320],[7,14,28,56,112,224],
        [9,18,36,72,144,288],[11,22,44,88,176,352],[13,26,52,104,208],[15,30,60,120,240]]
def load_bg(path, ils):
    bm = {}; r = 0
    for ln in open(path).read().splitlines()[2:]:
        f = ln.split(";")
        if len(f) < 3 or f[1] == "": continue
        if f[0] != "": r = int(f[0])
        bm[(r, int(f[1]))] = int(float(f[2 + ils]))
    return bm
def build_5g(K, n, d):
    bg2 = K <= 292 or (K <= 3824 and K / n <= 0.67) or K / n <= 0.25
    kb = 22 if not bg2 else (10 if K > 640 else 9 if K > 560 else 8 if K > 192 else 6)
    Z, ils = min((s, i) for i, S in enumerate(SETS) for s in S if kb * s >= K)
    kbf = 10 if bg2 else 22
    bm = load_bg(f"{d}/5G_bg{2 if bg2 else 1}.csv", ils)
    P = n - (K - 2 * Z); npar = max(P, 4 * Z); R = 4 * Z + max(0, P - 4 * Z)
    cols = [0] * (K + npar)
    for (r, c), v in bm.items():
        for i in range(Z):
            row = r * Z + i
            if row >= R: continue
            col = c * Z + (i + v) % Z
            if col < kbf * Z:
                if col >= K: continue          # bits de enchimento (conhecidos)
                var = col
            else:
                var = K + col - kbf * Z
                if var >= K + npar: continue
            cols[var] ^= 1 << row
    tx = list(range(2 * Z, K)) + list(range(K, K + P))
    always = list(range(2 * Z)) + list(range(K + P, K + npar))
    return dict(nome=f"5G NR BG{2 if bg2 else 1} (Z={Z})", cols=cols, tx=tx, always=always, R=R)

# ---------- PEG + acumulador ----------
def build_peg(K, M, rng):
    nb = [0] * M                      # vizinhança (distância 2) entre equações, como bitmask
    for q in range(M - 1): nb[q] |= 1 << (q + 1); nb[q + 1] |= 1 << q
    deg = [0] * M; data = []; full = (1 << M) - 1
    for v in range(K):
        mine = []
        for k in range(4):
            okmask = 0
            for c in range(M):
                if deg[c] < 16 and c not in mine: okmask |= 1 << c
            if k == 0: cand = okmask
            else:
                reached = 0
                for c in mine: reached |= 1 << c
                frontier = reached; cand = 0
                while True:
                    nxt = 0; f = frontier
                    while f:
                        b = f & -f; nxt |= nb[b.bit_length() - 1]; f ^= b
                    new = nxt & ~reached
                    if (full & ~reached) & okmask and not new: cand = (full & ~reached) & okmask; break
                    if new & okmask: cand = new & okmask
                    if not new: break
                    reached |= new; frontier = new
                    if (full & ~reached) & okmask: cand = (full & ~reached) & okmask
                if not cand: cand = okmask
            best = []; bd = 99; f = cand
            while f:
                b = f & -f; c = b.bit_length() - 1; f ^= b
                if deg[c] < bd: bd = deg[c]; best = [c]
                elif deg[c] == bd: best.append(c)
            c = rng.choice(best)
            for o in mine: nb[o] |= 1 << c; nb[c] |= 1 << o
            mine.append(c); deg[c] += 1
        data.append(mine)
    cols = [sum(1 << c for c in m) for m in data] + [(1 << q) | ((1 << (q + 1)) if q + 1 < M else 0) for q in range(M)]
    tx = []
    for q in range(M): tx += list(range(4 * q, 4 * q + 4)) + [K + q]
    c4 = sum(1 for a in range(min(K, 400)) for b in range(a) if len(set(data[a]) & set(data[b])) > 1)
    return dict(nome="PEG + acumulador", cols=cols, tx=tx, always=[], R=M, c4_amostra=c4, graus=sorted(set(deg)))

def build_v3(p, d):
    r = json.load(open(f"{d}/res_{p}.json")); f = r["formula"]; L = r["formula_layout"]
    pos = chain_pos(p, f["passos"], f["a"], f["b"])
    return dict(nome="Prime-Ulam v3 (fórmula)", cols=cols_from_pos(pos, 4 * p), tx=tx_formula(p, L["g"], L["h"]), always=[], R=4 * p)

# ---------- decodificação ----------
def reduce(basis, v):
    while v:
        h = v.bit_length() - 1
        if h in basis: v ^= basis[h]
        else: basis[h] = v; return True
    return False
def prep(code):
    cols = code["cols"]; code["vrows"] = [[i for i in range(code["R"]) if (c >> i) & 1] for c in cols]
    rv = [[] for _ in range(code["R"])]
    for v, rows in enumerate(code["vrows"]):
        for r in rows: rv[r].append(v)
    code["rvars"] = rv; code["base"] = {}
    assert all(reduce(code["base"], cols[v]) for v in code["always"]), "perfurados dependentes"
def ml_ok(code, E):
    basis = dict(code["base"]); cols = code["cols"]
    return all(reduce(basis, cols[v]) for v in E)
def peel(code, E):
    """devolve quantas incógnitas sobram após o peeling (0 = resolveu tudo sem eliminação gaussiana)."""
    unk = set(E) | set(code["always"]); cnt = {}; vr = code["vrows"]; rv = code["rvars"]
    for v in unk:
        for r in vr[v]: cnt[r] = cnt.get(r, 0) + 1
    stack = [r for r, c in cnt.items() if c == 1]
    while stack:
        r = stack.pop()
        if cnt[r] != 1: continue
        v = next(x for x in rv[r] if x in unk); unk.discard(v)
        for r2 in vr[v]:
            cnt[r2] -= 1
            if cnt[r2] == 1: stack.append(r2)
    return len(unk)
def burst_guarantee(code, starts):
    tx = code["tx"]; n = len(tx); cols = code["cols"]; g = n
    for s in starts:
        basis = dict(code["base"]); L = 0
        while L < g and reduce(basis, cols[tx[(s + L) % n]]): L += 1
        g = min(g, L)
    return g

if __name__ == "__main__":
    p = int(sys.argv[1]); T = int(sys.argv[2]); K, M, n = 16 * p, 4 * p, 20 * p
    codes = [build_v3(p, sys.argv[3]), build_5g(K, n, sys.argv[4]), build_peg(K, M, random.Random(p))]
    out = {"p": p, "n": n, "K": K, "T": T, "codes": []}
    pr = random.Random(555); fr = (0.10, 0.15, 0.175, 0.19)
    pats = {f: [pr.sample(range(n), round(f * n)) for _ in range(T)] for f in fr}   # posições transmitidas
    for c in codes:
        t0 = time.time(); prep(c); assert len(c["tx"]) == n
        deg = sorted(len(r) for r in c["vrows"]); r = {"nome": c["nome"], "equacoes": c["R"], "arestas": sum(deg),
             "perfurados": len(c["always"]), "extra": {k: c[k] for k in ("c4_amostra", "graus") if k in c}}
        for f in fr:
            ml = pe = 0; res = 0
            for E in pats[f]:
                Ev = [c["tx"][t] for t in E]
                ml += ml_ok(c, Ev); k = peel(c, Ev); pe += (k == 0); res += k
            r[f"ml_{f}"] = 100 * ml / T; r[f"peel_{f}"] = 100 * pe / T; r[f"resto_{f}"] = res / T
        st = range(n) if n <= 2000 else random.Random(3).sample(range(n), 150)
        r["rajada_garantida"] = burst_guarantee(c, st); r["seg"] = round(time.time() - t0)
        out["codes"].append(r); print(json.dumps(r), flush=True)
    json.dump(out, open(f"cmp_{p}.json", "w"))
