# Copyright 2026 Karlos Marden Maia
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files.
"""Prime-Ulam v6: repolimento dos coeficientes da cadeia por aprendizado ativo.
 A cada rodada: (1) sorteia apagamentos a 19%, (2) coleta as palavras-código de baixo peso que causaram falha (qualquer nº de bits de dados),
 (3) reotimiza (a,b) para afastar TODAS as coletadas até agora + palavras de 1-2 bits, (4) repete. No fim, reprojeta a ordem de envio.
uso: python3 -I v6.py <dir v4> <dir 5G> <p> <rodadas> <padrões por rodada> <fração> <iterações de polimento>"""
import sys, random, json, time, math
HERE, BG, P, ROUNDS, TS, FR, POL = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), float(sys.argv[6]), int(sys.argv[7])
sys.argv = [sys.argv[0], HERE, BG]; sys.path.insert(0, HERE)
from v5 import build, prep, ml_ok, lowweight, burst_guarantee, reduce, coprime, c4_count
Q = 0.15; D = json.load(open(f"{HERE}/v5_p{P}.json")); MB = D["MB"]; M = MB * P; K = 32 * P; n = 40 * P; mid = M // 2
masks, punct, passos = D["masks"], D["punct"], D["passos"]; a, b = list(D["a"]), list(D["b"]); g, h = D["g"], D["h"]
mk = lambda a, b, g=1, h=1: build(P, MB, masks, punct, passos, a, b, g, h)
def syn(Dbits, a, b):
    s = set()
    for v in Dbits:
        i, j = divmod(v, P)
        for c in masks[i]: s ^= {MB * ((a[c] * ((j + passos[c] * i) % P) + b[c]) % P) + c}
    return s
def weight(Dbits, a, b):
    s = syn(Dbits, a, b); base = sum(1 for v in Dbits if v // P not in punct)
    if len(s) & 1: s = s ^ {0, mid, M - 1}; base += 1
    tot = acc = prev = 0
    for r in sorted(s): tot += (r - prev) * acc; acc ^= 1; prev = r
    return base + tot
def dependencies(code, Ev):
    order = list(code["always"]) + Ev; basis = {}; deps = []
    for idx, v in enumerate(order):
        w = code["cols"][v]; cb = 1 << idx
        while w:
            hb = w.bit_length() - 1
            if hb in basis: bw, bc = basis[hb]; w ^= bw; cb ^= bc
            else: basis[hb] = (w, cb); break
        if not w: deps.append([order[i] for i in range(len(order)) if (cb >> i) & 1])
    return deps
def objective(a, b, sets):
    return lowweight(mk(a, b), M)[0] + sum(Q ** weight(S, a, b) for S in sets)

sets = set(); t0 = time.time()
for rd in range(ROUNDS):
    code = mk(a, b, g, h); prep(code); r = random.Random(1000 + rd); e = round(FR * n); nf = 0; new = 0
    for _ in range(TS):
        Ev = [code["tx"][t] for t in r.sample(range(n), e)]
        if not ml_ok(code, Ev):
            nf += 1
            for d in dependencies(code, Ev):
                S = tuple(sorted(v for v in d if v < K))
                if S and weight(S, a, b) <= 16 and S not in sets: sets.add(S); new += 1
    wmin = min(weight(S, a, b) for S in sets) if sets else -1
    cost = objective(a, b, sets); c0 = cost
    for it in range(POL):
        a2, b2 = list(a), list(b); c = random.randrange(MB)
        if random.random() < 0.5: a2[c] = random.randrange(1, P)
        else: b2[c] = random.randrange(P)
        c2 = objective(a2, b2, sets)
        if c2 < cost: cost, a, b = c2, a2, b2
    wmin2 = min(weight(S, a, b) for S in sets)
    print(f"rodada {rd}: falhas {nf}/{TS} a {FR:.0%}, conjuntos novos {new}, total {len(sets)}, peso mínimo coletado {wmin}->{wmin2}, custo {c0:.2e}->{cost:.2e}, {time.time()-t0:.0f}s", flush=True)
    json.dump(dict(D, a=a, b=b), open(f"{HERE}/v6tmp_p{P}.json", "w"))
st = range(n) if n <= 2000 else random.Random(3).sample(range(n), 150); bl = (0, g, h); rng = random.Random(P + 9)
for _ in range(40):
    gg = rng.randrange(1, P); hh = coprime(M, rng); cand = mk(a, b, gg, hh); cand["base"] = {}
    assert all(reduce(cand["base"], cand["cols"][v]) for v in cand["always"])
    G = burst_guarantee(cand, st)
    if G > bl[0]: bl = (G, gg, hh)
code = mk(a, b, bl[1], bl[2]); print("v6 c4", c4_count(code["rows"]), "rajada garantida", bl[0], "g,h", bl[1:], flush=True)
json.dump(dict(D, a=a, b=b, g=bl[1], h=bl[2]), open(f"{HERE}/v6_p{P}.json", "w"))
