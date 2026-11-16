"""Teste: v5 + r equações densas (metade dos bits de dados cada) com r bits de paridade extras transmitidos."""
import sys, random, json, os, math
HERE, BG, P, T, R_ = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]); sys.argv = [sys.argv[0], HERE, BG]; sys.path.insert(0, HERE)
from v5 import build, prep, ml_ok
D = json.load(open(f"{HERE}/v5_p{P}.json")); K, n, M = 32 * P, 40 * P, D["MB"] * P
c = build(P, D["MB"], D["masks"], D["punct"], D["passos"], D["a"], D["b"], D["g"], D["h"]); rr = random.Random(99)
cols = list(c["cols"]); tx = list(c["tx"]); base = len(cols)
for k in range(R_):
    for v in range(K):
        if rr.random() < 0.5: cols[v] |= 1 << (M + k)
for k in range(R_): cols.append(1 << (M + k)); tx.append(base + k)
c["cols"] = cols; c["tx"] = tx; c["R"] = M + R_; prep(c); n2 = len(tx)
for f in (0.175,):
    r = random.Random(int(f * 1000) + 7); e = round(f * n); fail = 0         # mesmo número de apagamentos que antes (259)
    for _ in range(T): fail += not ml_ok(c, [tx[t] for t in r.sample(range(n2), e)])
    lo = fail / T; print(f"r={R_}: n={n2} taxa={K/n2:.4f} apagamentos={e} falhas {fail}/{T} = {fail/T:.2e}", flush=True)
