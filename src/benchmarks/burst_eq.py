# Copyright 2026 Karlos Marden Maia
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files.
"""Equaliza a comparação de rajadas: os 3 códigos recebem a MESMA busca de ordem de envio.
 Família G1: intercalador de passo único   tx[t] = base[(s*t) mod n]            (1 inteiro)
 Família G2: dados e paridades em fluxos separados, passos g e h, mesclados na proporção do código (2 inteiros; mesma forma da v5)
uso: python3 -I burst_eq.py <dir v4> <dir 5G csv> <p> <tentativas> <inícios na triagem>"""
import sys, random, json, time, math
HERE, BG, P, TR, NS = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
sys.argv = [sys.argv[0], HERE, BG]; sys.path.insert(0, HERE)
from v5 import build, reduce, prep, build_5g, build_peg
K, n = 32 * P, 40 * P

def build_v5(p):
    D = json.load(open(f"{HERE}/v5_p{p}.json"))
    return build(p, D["MB"], D["masks"], D["punct"], D["passos"], D["a"], D["b"], D["g"], D["h"])

def guarantee(code, tx, starts, floor=0):
    cols = code["cols"]; nn = len(tx); g = nn
    for s in starts:
        basis = dict(code["base"]); L = 0
        while L < g and reduce(basis, cols[tx[(s + L) % nn]]): L += 1
        g = min(g, L)
        if g <= floor: return g
    return g

def g1(base, s): return [base[(s * t) % len(base)] for t in range(len(base))]
def g2(base, g, h):
    D = sorted(v for v in base if v < K); Pl = sorted(v for v in base if v >= K); nD, nP = len(D), len(Pl); nn = nD + nP
    Dp = [D[(g * t) % nD] for t in range(nD)]; Pp = [Pl[(h * q) % nP] for q in range(nP)]; tx = []; t = q = 0
    for x in range(nn):
        if (x + 1) * nP // nn > x * nP // nn: tx.append(Pp[q]); q += 1
        else: tx.append(Dp[t]); t += 1
    return tx

def search(code, rng, kind, tries, ns):
    base = list(code["tx"]); nn = len(base); starts = list(range(nn)); rng.shuffle(starts); sample = starts[:ns]
    nD = sum(v < K for v in base); nP = nn - nD; top = []; best = 0
    for _ in range(tries):
        if kind == "G1":
            s = rng.randrange(1, nn)
            if math.gcd(s, nn) != 1: continue
            par = (s,); tx = g1(base, s)
        else:
            g = rng.randrange(1, nD); h = rng.randrange(1, nP)
            if math.gcd(g, nD) != 1 or math.gcd(h, nP) != 1: continue
            par = (g, h); tx = g2(base, g, h)
        G = guarantee(code, tx, sample, best)
        if G > best: best = G; top.append((G, par, tx)); top = sorted(top, key=lambda x: -x[0])[:4]
    full = starts if nn <= 2000 else starts[:300]
    ver = [(guarantee(code, tx, full), par) for G, par, tx in top]
    return max(ver) if ver else (0, None)

if __name__ == "__main__":
    full_starts = lambda nn: list(range(nn)) if nn <= 2000 else random.Random(3).sample(range(nn), 300)
    out = {"p": P, "n": n}
    for mk in (lambda: build_v5(P), lambda: build_5g(K, n, BG), lambda: build_peg(K, 8 * P, random.Random(P))):
        c = mk(); prep(c); t0 = time.time(); nm = c["nome"]; rng = random.Random(P)
        allc = dict(c["base"]); rk = len(c["base"])
        for v in range(len(c["cols"])): reduce(allc, c["cols"][v])
        bound = len(allc) - len(c["always"])                    # incógnitas <= equações independentes
        r = {"limite": bound, "como_construido": guarantee(c, c["tx"], full_starts(n))}
        if nm.startswith("Prime"):
            r["v5_formula_original"] = r["como_construido"]
            c0 = build(P, json.load(open(f"{HERE}/v5_p{P}.json"))["MB"], json.load(open(f"{HERE}/v5_p{P}.json"))["masks"], json.load(open(f"{HERE}/v5_p{P}.json"))["punct"], json.load(open(f"{HERE}/v5_p{P}.json"))["passos"], json.load(open(f"{HERE}/v5_p{P}.json"))["a"], json.load(open(f"{HERE}/v5_p{P}.json"))["b"], 1, 1)
            c["tx"] = c0["tx"]; r["como_construido"] = guarantee(c, c["tx"], full_starts(n))   # ordem sem projeto (g=h=1)
        r["G1"] = search(c, rng, "G1", TR, NS); r["G2"] = search(c, rng, "G2", TR, NS); r["seg"] = round(time.time() - t0)
        out[nm] = r; print(nm, json.dumps(r), flush=True)
    json.dump(out, open(f"burst_eq_{P}.json", "w"))
