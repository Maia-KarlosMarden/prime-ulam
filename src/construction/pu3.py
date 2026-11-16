"""Prime-Ulam v3: construção por FÓRMULA (nada armazenado), para qualquer primo p >= 17.
 Geometria: 16 braços (i = 0..15) x p posições radiais (j em Z_p)  ->  K = 16p bits de dados.
 Equações: 4 famílias de espirais; a família c com passo s_c contém os pontos com j + s_c*i = l (mod p).
           M = 4p equações, 16 dados por equação, 4 equações por dado.
 Paridade: acumulador; a equação (c, l) ocupa a posição 4*((a_c*l + b_c) mod p) + c na cadeia.
 Transmissão: n = 20p, padrão D D D D P; dado t fica no braço t mod 16, raio g*t mod p (TCR)."""
import sys, random, time, itertools, json, numpy as np
Q = 0.15

def full_rank(cols, E):
    basis = {}
    for j in E:
        v = cols[j]
        while v:
            h = v.bit_length() - 1
            if h in basis: v ^= basis[h]
            else: basis[h] = v; break
        if not v: return False
    return True

# ---------- construção por fórmula ----------
def chain_pos(p, slopes, a, b):
    """pos[i*p + j, c] = posição na cadeia da equação da família c que contém o ponto (braço i, raio j)."""
    i = np.repeat(np.arange(16), p); j = np.tile(np.arange(p), 16)
    return np.stack([4 * ((a[c] * ((j + slopes[c] * i) % p) + b[c]) % p) + c for c in range(4)], axis=1)

def cols_from_pos(pos, M):
    data = [sum(1 << int(r) for r in row) for row in pos]
    par = [(1 << q) | ((1 << (q + 1)) if q + 1 < M else 0) for q in range(M)]
    return data + par

def dense(pos, M):
    H = np.zeros((M, len(pos)), dtype=np.int64)
    for c in range(pos.shape[1]): H[pos[:, c], np.arange(len(pos))] = 1
    return H

def max_overlap(H):
    G = H.T @ H; np.fill_diagonal(G, 0); return int(G.max()), int((G * (G - 1) // 2).sum() // 2)

def lowweight_cost(pos, M, with_pairs=True):
    """soma Q^peso das palavras-código geradas por 1 bit (e por 2 bits que partilham equação)."""
    K = len(pos); S = np.zeros((K, M), dtype=np.int8); S[np.arange(K)[:, None], pos] = 1
    w = 1 + (np.cumsum(S, axis=1) % 2).sum(1); cost = float((Q ** w.astype(float)).sum()); wmin = int(w.min())
    if with_pairs:
        lines = {}
        for d in range(K):
            for r in pos[d]: lines.setdefault(int(r), []).append(d)
        pr = np.array([ab for pts in lines.values() for ab in itertools.combinations(pts, 2)])
        for k in range(0, len(pr), 20000):
            blk = pr[k:k + 20000]; w2 = 2 + (np.cumsum(S[blk[:, 0]] ^ S[blk[:, 1]], axis=1) % 2).sum(1)
            cost += float((Q ** w2.astype(float)).sum()); wmin = min(wmin, int(w2.min()))
    return cost, wmin

def search_formula(p, rng, tries, with_pairs):
    best = None; M = 4 * p
    for _ in range(tries):
        slopes = sorted(rng.sample(range(-7, 8), 4))
        a = [rng.randrange(1, p) for _ in range(4)]; b = [rng.randrange(p) for _ in range(4)]
        c, w = lowweight_cost(chain_pos(p, slopes, a, b), M, with_pairs)
        if best is None or c < best[0]: best = (c, w, slopes, a, b)
    return best

def tx_formula(p, g, h):
    """ordem de transmissão: 4 dados + 1 paridade; dado t -> (braço t mod 16, raio g*t mod p); paridade q -> h*q mod M."""
    K, M = 16 * p, 4 * p; tx = []
    for q in range(M):
        for t in range(4 * q, 4 * q + 4): tx.append((t % 16) * p + (g * t) % p)
        tx.append(K + (h * q) % M)
    return tx

def burst_guarantee(cols, tx, starts=None, floor=0):
    """maior L tal que TODA rajada cíclica de L posições é recuperável (mínimo sobre os inícios testados)."""
    n = len(tx); g = None
    for s in (starts if starts is not None else range(n)):
        basis = {}; L = 0
        while L < n:
            v = cols[tx[(s + L) % n]]
            while v:
                hb = v.bit_length() - 1
                if hb in basis: v ^= basis[hb]
                else: basis[hb] = v; break
            if not v: break
            L += 1
        g = L if g is None else min(g, L)
        if g < floor: return g
    return g

def search_layout(p, cols, rng, tries):
    M = 4 * p; best = (0, None, None)
    for _ in range(tries):
        g = rng.randrange(1, p); h = rng.choice([x for x in range(1, M, 2) if x % p])
        G = burst_guarantee(cols, tx_formula(p, g, h), floor=best[0])
        if G > best[0]: best = (G, g, h)
    return best

# ---------- referência: matriz armazenada (pipeline v2) ----------
def regular_H(K, M, rng):
    lay = []
    for l in range(4):
        rows = [r for r in range(M) for _ in range(K // M)]; rng.shuffle(rows); lay.append(rows)
    while True:
        bad = [c for c in range(K) if len({lay[l][c] for l in range(4)}) < 4]
        if not bad: break
        l = rng.randrange(1, 4); d = rng.randrange(K); c = bad[0]
        lay[l][c], lay[l][d] = lay[l][d], lay[l][c]
    return np.array([[lay[l][c] for l in range(4)] for c in range(K)])

def reduce_c4(pos, M, rng, budget):
    K = len(pos); H = dense(pos, M)
    def c4col(c):
        o = H[:, c] @ H; o[c] = 0; return int((o * (o - 1) // 2).sum())
    tot = sum(c4col(c) for c in range(K)) // 2; start = tot; t0 = time.time()
    while tot > 0 and time.time() - t0 < budget:
        c1, c2 = rng.sample(range(K), 2)
        r1 = rng.choice(np.flatnonzero(H[:, c1])); r2 = rng.choice(np.flatnonzero(H[:, c2]))
        if r1 == r2 or H[r2, c1] or H[r1, c2]: continue
        o = int(H[:, c1] @ H[:, c2]); bf = c4col(c1) + c4col(c2) - o * (o - 1) // 2
        H[r1, c1] = 0; H[r2, c1] = 1; H[r2, c2] = 0; H[r1, c2] = 1
        o = int(H[:, c1] @ H[:, c2]); af = c4col(c1) + c4col(c2) - o * (o - 1) // 2
        if af < bf or (af == bf and rng.random() < 0.05): tot += af - bf
        else: H[r1, c1] = 1; H[r2, c1] = 0; H[r2, c2] = 1; H[r1, c2] = 0
    return np.array([np.flatnonzero(H[:, c]) for c in range(K)]), start, tot

def optimize_rows(pos, M, rng, budget):
    order = np.arange(M); rng.shuffle(order); best, _ = lowweight_cost(order[pos], M); t0 = time.time()
    while time.time() - t0 < budget:
        i, j = rng.sample(range(M), 2); order[[i, j]] = order[[j, i]]
        c, _ = lowweight_cost(order[pos], M)
        if c < best: best = c
        else: order[[i, j]] = order[[j, i]]
    return order[pos], lowweight_cost(order[pos], M)[1]

def rand_eval(cols, n, fracs, T, seed):
    r = random.Random(seed)
    return {f: 100 * sum(full_rank(cols, r.sample(range(n), round(f * n))) for _ in range(T)) / T for f in fracs}

if __name__ == "__main__":
    p = int(sys.argv[1]); T = int(sys.argv[2]); tries = int(sys.argv[3]); base_budget = float(sys.argv[4])
    K, M, n = 16 * p, 4 * p, 20 * p; rng = random.Random(1000 + p); fr = (0.15, 0.175, 0.19); res = {"p": p, "K": K, "M": M, "n": n}
    t0 = time.time(); c, w, slopes, a, b = search_formula(p, rng, tries, with_pairs=(p <= 100))
    pos = chain_pos(p, slopes, a, b); cols = cols_from_pos(pos, M)
    if p <= 100: res["formula_overlap_max_c4"] = max_overlap(dense(pos, M))
    res["formula"] = {"passos": slopes, "a": a, "b": b, "peso_min": w}
    res["formula_rand"] = rand_eval(cols, n, fr, T, 77)
    if p <= 100:
        G, g, h = search_layout(p, cols, rng, max(4, tries // 10)); res["formula_layout"] = {"g": g, "h": h, "rajada_garantida": G}
    else:
        st = random.Random(3).sample(range(n), 120); bl = (0, None, None)
        for _ in range(6):
            g = rng.randrange(1, p); h = rng.choice([x for x in range(1, M, 2) if x % p])
            G = burst_guarantee(cols, tx_formula(p, g, h), starts=st, floor=bl[0])
            if G > bl[0]: bl = (G, g, h)
        res["formula_layout"] = {"g": bl[1], "h": bl[2], "rajada_garantida_amostra120": bl[0]}
    res["formula_seg"] = round(time.time() - t0)
    print(json.dumps(res), flush=True)
    if base_budget > 0:
        t0 = time.time(); bp, c0, c1 = reduce_c4(regular_H(K, M, rng), M, rng, base_budget)
        bp, bw = optimize_rows(bp, M, rng, base_budget)
        res["base"] = {"c4_inicial": c0, "c4_final": c1, "peso_min": bw, "rand": rand_eval(cols_from_pos(bp, M), n, fr, T, 77), "seg": round(time.time() - t0)}
    print(json.dumps(res), flush=True)
    json.dump(res, open(f"res_{p}.json", "w"))
