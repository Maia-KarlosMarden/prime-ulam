# Copyright 2026 Karlos Marden Maia
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files.
"""Prime-Ulam v4: fórmula com graus IRREGULARES.
 32 braços x p posições radiais (p primo >= 37)  ->  K = 32p dados;  8 famílias de espirais -> M = 8p equações; taxa 0,80.
 Cada braço participa de um subconjunto das famílias (seu grau). Família c, passo s_c: pontos com j + s_c*i = l (mod p).
 Duas espirais de famílias diferentes cruzam-se em no máximo um braço  ->  zero ciclos-4, por construção."""
import sys, random, json, time, itertools
HERE = sys.argv[1]; BG = sys.argv[2]; sys.argv = [sys.argv[0], "0", "0", HERE, BG] + sys.argv[3:]
sys.path.insert(0, HERE)
import os as _os; sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "benchmarks")); sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "construction"))  # BENCH_DIR
from compare import prep, ml_ok, peel, burst_guarantee, build_5g, build_peg
A, MB = 32, 8
PROFILES = {"A 4x8+28x3": [8]*4 + [3]*28, "B 6x8+26x3": [8]*6 + [3]*26, "C 4x8+12x4+16x3": [8]*4 + [4]*12 + [3]*16,
            "D 8x6+24x3": [6]*8 + [3]*24, "E 2x8+30x3": [8]*2 + [3]*30, "F 4x8+4x5+24x3": [8]*4 + [5]*4 + [3]*24,
            "G regular 32x4": [4]*32, "H 8x8+24x3": [8]*8 + [3]*24, "I 6x8+6x4+20x3": [8]*6 + [4]*6 + [3]*20,
            "J 8x8+24x4": [8]*8 + [4]*24, "K 6x8+26x4": [8]*6 + [4]*26}
ONLY = None

def assign(degs, rng):
    w = [0] * MB; masks = [None] * A; arms = list(range(A)); rng.shuffle(arms)
    for i, d in zip(arms, sorted(degs, reverse=True)):
        fam = sorted(range(MB), key=lambda c: (w[c], rng.random()))[:d]
        for c in fam: w[c] += 1
        masks[i] = sorted(fam)
    return masks

def build(p, masks, slopes, a, b, g=1, h=1):
    K, M = A * p, MB * p; rows = []
    for i in range(A):
        for j in range(p):
            rows.append([MB * ((a[c] * ((j + slopes[c] * i) % p) + b[c]) % p) + c for c in masks[i]])
    cols = [sum(1 << r for r in rs) for rs in rows] + [(1 << q) | ((1 << (q + 1)) if q + 1 < M else 0) for q in range(M)]
    tx = []
    for q in range(M):
        tx += [(t % A) * p + (g * t) % p for t in range(4 * q, 4 * q + 4)] + [K + (h * q) % M]
    assert sorted(tx) == list(range(K + M))
    return dict(nome="Prime-Ulam v4 (fórmula irregular)", cols=cols, tx=tx, always=[], R=M, rows=rows)

def c4_count(rows, limit=None):
    seen = {}; c4 = 0
    for d, rs in enumerate(rows[:limit]):
        for x, y in itertools.combinations(sorted(rs), 2):
            c4 += seen.get((x, y), 0); seen[(x, y)] = seen.get((x, y), 0) + 1
    return c4

def lowweight(rows, M, Q=0.15, pairs=True):
    def w(mask_rows, base):
        acc = 0; tot = 0; s = set(mask_rows); prev = 0
        for r in sorted(s): tot += (r - prev) * acc; acc ^= 1; prev = r
        return base + tot + (M - prev) * acc
    cost = 0.0; wmin = 10**9; lines = {}
    for d, rs in enumerate(rows):
        x = w(rs, 1); cost += Q ** x; wmin = min(wmin, x)
        for r in rs: lines.setdefault(r, []).append(d)
    for pts in (lines.values() if pairs else ()):
        for u, v in itertools.combinations(pts, 2):
            x = w(set(rows[u]) ^ set(rows[v]), 2); cost += Q ** x; wmin = min(wmin, x)
    return cost, wmin

def score(code, pats):
    prep(code); out = {}
    for f, P in pats.items():
        ml = pe = 0
        for E in P:
            Ev = [code["tx"][t] for t in E]; ml += ml_ok(code, Ev); pe += peel(code, Ev) == 0
        out[f] = (100 * ml / len(P), 100 * pe / len(P))
    return out

def patterns(n, fr, T, seed):
    r = random.Random(seed); return {f: [r.sample(range(n), round(f * n)) for _ in range(T)] for f in fr}

if __name__ == "__main__":
    mode = sys.argv[5]
    if mode.startswith("search"):
        ONLY = mode[6:]
        p = 37; n = 40 * p; rng = random.Random(11); pats = patterns(n, (0.165, 0.175, 0.19, 0.195), 150, 1); best = None
        for name, degs in PROFILES.items():
            if ONLY and name[0] not in ONLY: continue
            for k in range(5):
                masks = assign(degs, rng); slopes = rng.sample(range(-15, 16), MB)
                a = [rng.randrange(1, p) for _ in range(MB)]; b = [rng.randrange(p) for _ in range(MB)]
                code = build(p, masks, slopes, a, b); s = score(code, pats)
                tot = s[0.19][0] + s[0.195][0] + s[0.165][1] + s[0.175][1]
                print(f"{name:18s} #{k} arestas/p={sum(degs)}  ML19={s[0.19][0]:5.1f} ML19.5={s[0.195][0]:5.1f}  peel16.5={s[0.165][1]:5.1f} peel17.5={s[0.175][1]:5.1f}  soma={tot:.0f}", flush=True)
                if name[0] != "G" and (best is None or tot > best[0]): best = (tot, name, masks, slopes)
        json.dump({"perfil": best[1], "masks": best[2], "passos": best[3]}, open("v4_design.json", "w")); print("escolhido:", best[1], best[0])
    else:
        p = int(mode); T = int(sys.argv[6]); K, M, n = A * p, MB * p, 40 * p; D = json.load(open("v4_design.json")); rng = random.Random(p)
        t0 = time.time(); pool = []
        for _ in range(int(sys.argv[7])):                      # coeficientes da cadeia: evita palavras de peso baixo
            a = [rng.randrange(1, p) for _ in range(MB)]; b = [rng.randrange(p) for _ in range(MB)]
            pool.append((lowweight(build(p, D["masks"], D["passos"], a, b)["rows"], M, pairs=False), a, b))
        pool.sort(key=lambda x: x[0][0]); best = None
        for _, a, b in pool[:6]:
            c = lowweight(build(p, D["masks"], D["passos"], a, b)["rows"], M)
            if best is None or c[0] < best[0][0]: best = (c, a, b)
        (cst, wmin), a, b = best; code = build(p, D["masks"], D["passos"], a, b); prep(code)
        st = range(n) if n <= 2000 else random.Random(3).sample(range(n), 150); bl = (0, 1, 1)
        for _ in range(int(sys.argv[8])):                      # ordem de transmissão
            g = rng.randrange(1, p); h = rng.choice([x for x in range(1, M, 2) if x % p])
            cand = build(p, D["masks"], D["passos"], a, b, g, h); cand["base"] = {}
            G = burst_guarantee(cand, st)
            if G > bl[0]: bl = (G, g, h)
        code = build(p, D["masks"], D["passos"], a, b, bl[1], bl[2])
        print("v4", D["perfil"], "p", p, "n", n, "peso_min", wmin, "c4", c4_count(code["rows"]), "a", a, "b", b, "g,h", bl[1:], "seg", round(time.time() - t0), flush=True)
        fr = (0.15, 0.165, 0.17, 0.175, 0.19, 0.195); pats = patterns(n, fr, T, 555)
        for c in (code, build_5g(K, n, BG), build_peg(K, M, random.Random(p))):
            s = score(c, pats)
            print(json.dumps({"nome": c["nome"], "arestas": sum(len(r) for r in c["vrows"]), "equacoes": c["R"],
                              "ML": {f: round(s[f][0], 2) for f in fr}, "peel": {f: round(s[f][1], 2) for f in fr},
                              "rajada": burst_guarantee(c, st)}, ensure_ascii=False), flush=True)
