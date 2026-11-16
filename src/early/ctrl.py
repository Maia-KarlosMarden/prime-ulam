"""Controle: matriz regular aleatória + redução de ciclos-4 por troca de arestas (sem geometria)."""
import sys, random, numpy as np
sys.path.insert(0, sys.argv[1])
from sim import K, M, N, full_rank, cols_identity, cols_ira, best_perm, regular_H, burst
T = int(sys.argv[2])
def c4col(H, c):
    o = H[:, c] @ H; o[c] = 0
    return int((o * (o - 1) // 2).sum())
def optimize(Hc, rng, target, iters=400000):
    H = np.zeros((M, K), dtype=np.int64)
    for c, rs in enumerate(Hc): H[rs, c] = 1
    tot = sum(c4col(H, c) for c in range(K)) // 2
    for _ in range(iters):
        if tot <= target: break
        c1, c2 = rng.sample(range(K), 2)
        r1 = rng.choice(np.flatnonzero(H[:, c1])); r2 = rng.choice(np.flatnonzero(H[:, c2]))
        if r1 == r2 or H[r2, c1] or H[r1, c2]: continue
        o12 = int(H[:, c1] @ H[:, c2]); before = c4col(H, c1) + c4col(H, c2) - o12 * (o12 - 1) // 2
        H[r1, c1] = 0; H[r2, c1] = 1; H[r2, c2] = 0; H[r1, c2] = 1
        n12 = int(H[:, c1] @ H[:, c2]); after = c4col(H, c1) + c4col(H, c2) - n12 * (n12 - 1) // 2
        if after <= before: tot += after - before
        else: H[r1, c1] = 1; H[r2, c1] = 0; H[r2, c2] = 1; H[r1, c2] = 0
    return [list(np.flatnonzero(H[:, c])) for c in range(K)], tot
_pr = random.Random(100)
pats = {e: [_pr.sample(range(N), e) for _ in range(T)] for e in (48, 56, 64)}
rng = random.Random(5); prng = random.Random(11)
for target in (300, 0):
    acc = []
    for i in range(4):
        Hc, c4 = optimize(regular_H(rng), rng, target)
        Hc = [[int(r) for r in rs] for rs in Hc]
        cI = cols_identity(Hc); p, _ = best_perm(Hc, prng, 2000); cA = cols_ira(Hc, p)
        r = [100 * sum(full_rank(c, E) for E in pats[e]) / T for c in (cI, cA) for e in (48, 56, 64)]
        acc.append(r); print(f"alvo C4={target} matriz {i}: C4={c4} [H|I] {r[0]:.2f} {r[1]:.2f} {r[2]:.2f} | acum {r[3]:.2f} {r[4]:.2f} {r[5]:.2f} | raj48 {320-burst(cI,48)} {320-burst(cA,48)}", flush=True)
    print("  média:", [round(sum(x[j] for x in acc) / 4, 2) for j in range(6)])
