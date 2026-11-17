# Copyright 2026 Karlos Marden Maia
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files.
"""Prime-Ulam v2: melhora cada matriz H (64x256) em três etapas.
 1) remove ciclos-4 por troca de arestas (mantém graus 16/4)
 2) paridade em acumulador; ordem das linhas minimiza palavras-código de peso baixo
 3) ordem de transmissão dos 320 bits: maximiza o comprimento de rajada sempre recuperável
uso: python3 improve.py matrizes.xlsx dir_scripts saida.json [T]"""
import os, sys, random, json, time, itertools, numpy as np, openpyxl
from multiprocessing import Pool
sys.path.insert(0, sys.argv[2])
from sim import K, M, N, full_rank, cols_identity
Q = 0.15
SC = float(os.environ.get('SC', '1'))

def load(path):
    wb = openpyxl.load_workbook(path, data_only=True); out = {}
    for s in wb.sheetnames[1:]:
        if "_opt_" in s:
            out[s] = np.array([[int(v or 0) for v in r] for r in wb[s].iter_rows(values_only=True)], dtype=np.int64)
    return out

def c4col(H, c):
    o = H[:, c] @ H; o[c] = 0
    return int((o * (o - 1) // 2).sum())
def c4tot(H): return sum(c4col(H, c) for c in range(K)) // 2

def reduce_c4(H, rng, budget=150 * SC):
    H = H.copy(); tot = c4tot(H); t0 = time.time()
    while tot > 0 and time.time() - t0 < budget:
        c1, c2 = rng.sample(range(K), 2)
        r1 = rng.choice(np.flatnonzero(H[:, c1])); r2 = rng.choice(np.flatnonzero(H[:, c2]))
        if r1 == r2 or H[r2, c1] or H[r1, c2]: continue
        o = int(H[:, c1] @ H[:, c2]); b = c4col(H, c1) + c4col(H, c2) - o * (o - 1) // 2
        H[r1, c1] = 0; H[r2, c1] = 1; H[r2, c2] = 0; H[r1, c2] = 1
        o = int(H[:, c1] @ H[:, c2]); a = c4col(H, c1) + c4col(H, c2) - o * (o - 1) // 2
        if a < b or (a == b and rng.random() < 0.05): tot += a - b
        else: H[r1, c1] = 1; H[r2, c1] = 0; H[r2, c2] = 1; H[r1, c2] = 0
    return H, tot

def row_order(H, rng, iters=int(6000 * SC)):
    """order[pos] = linha original; minimiza soma Q^peso das palavras geradas por 1 ou 2 bits de dados."""
    G = H.T @ H
    pairs = [(a, b) for a, b in itertools.combinations(range(K), 2) if G[a, b] > 0]
    S = np.concatenate([H.T, np.array([(H[:, a] + H[:, b]) % 2 for a, b in pairs])]).astype(np.int64)
    win = np.array([1] * K + [2] * len(pairs))
    def cost(order):
        w = win + (np.cumsum(S[:, order], axis=1) % 2).sum(1)
        return float((Q ** w.astype(float)).sum()), int(w.min())
    order = list(range(M)); rng.shuffle(order); best, _ = cost(order)
    for _ in range(iters):
        i, j = rng.sample(range(M), 2); order[i], order[j] = order[j], order[i]
        c, _ = cost(order)
        if c < best: best = c
        else: order[i], order[j] = order[j], order[i]
    return order, cost(order)

def cols_acc(H, order):
    Hp = H[order, :]
    data = [sum(1 << int(r) for r in np.flatnonzero(Hp[:, c])) for c in range(K)]
    par = [(1 << j) | ((1 << (j + 1)) if j + 1 < M else 0) for j in range(M)]
    return data + par

def layout(cols, rng, budget=240 * SC):
    """tx[t] = coluna transmitida na posição t. Sobe L enquanto todas as 320 rajadas cíclicas forem recuperáveis."""
    d = list(range(K)); rng.shuffle(d); tx = []; di = 0
    for t in range(N):
        if t % 5 == 4: tx.append(K + (t // 5))
        else: tx.append(d[di]); di += 1
    def ok(s, L): return full_rank(cols, [tx[(s + i) % N] for i in range(L)])
    t0 = time.time(); guaranteed = 0; best_tx = list(tx); L = 48
    while L <= 64 and time.time() - t0 < budget:
        bad = {s for s in range(N) if not ok(s, L)}
        while bad and time.time() - t0 < budget:
            s = rng.choice(sorted(bad)); i = (s + rng.randrange(L)) % N; j = rng.randrange(N)
            if i == j: continue
            aff = {(p - k) % N for p in (i, j) for k in range(L)}
            before = len(bad & aff)
            tx[i], tx[j] = tx[j], tx[i]
            nb = {w for w in aff if not ok(w, L)}
            if len(nb) <= before: bad = (bad - aff) | nb
            else: tx[i], tx[j] = tx[j], tx[i]
        if bad: break
        guaranteed = L; best_tx = list(tx); L += 2
    return best_tx, guaranteed

def evaluate(cols, tx, T, seed):
    r = random.Random(seed); out = {}
    for e in (48, 56, 64):
        out[f"rand{e}"] = 100 * sum(full_rank(cols, r.sample(range(N), e)) for _ in range(T)) / T
    for L in (48, 56, 64):
        out[f"burst{L}"] = sum(full_rank(cols, [tx[(s + i) % N] for i in range(L)]) for s in range(N)) / 3.2
    return out

def work(args):
    name, H0, T = args; rng = random.Random(hash(name) % 9999 + 1)
    res = {"name": name, "c4_antes": c4tot(H0)}
    res["antes"] = evaluate(cols_identity([[int(r) for r in np.flatnonzero(H0[:, c])] for c in range(K)]), list(range(N)), T, 999)
    H, c4 = reduce_c4(H0, rng); res["c4_depois"] = c4
    res["arestas_mantidas"] = float((H & H0).sum() / H0.sum())
    order, (cst, wmin) = row_order(H, rng); res["peso_min_1ou2bits"] = wmin
    cols = cols_acc(H, order)
    tx, g = layout(cols, rng); res["rajada_garantida"] = g
    res["depois"] = evaluate(cols, tx, T, 999)
    res["H"] = H[order, :].tolist(); res["tx"] = tx
    return res

def show(r):
    print(r["name"], "C4", r["c4_antes"], "->", r["c4_depois"], "arestas mantidas %.0f%%" % (100 * r["arestas_mantidas"]),
          "wmin", r["peso_min_1ou2bits"], "rajada garantida", r["rajada_garantida"])
    print("   antes ", {k: round(v, 2) for k, v in r["antes"].items()})
    print("   depois", {k: round(v, 2) for k, v in r["depois"].items()}, flush=True)

if __name__ == "__main__":
    mats = load(sys.argv[1]); mats = dict(list(mats.items())[:int(os.environ.get('NM', '8'))]); T = int(sys.argv[4]) if len(sys.argv) > 4 else 20000
    out = []
    with Pool(2) as p:
        for r in p.imap_unordered(work, [(n, H, T) for n, H in mats.items()]):
            out.append(r); json.dump(out, open(sys.argv[3], "w")); show(r)
