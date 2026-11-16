"""Testa as 16 matrizes do xlsx: [H|I] vs [H|acumulador], padrões pareados."""
import sys, random, math, itertools, openpyxl
sys.path.insert(0, sys.argv[2])
from sim import K, M, N, full_rank, cols_identity, cols_ira, best_perm, regular_H, burst
wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
T = int(sys.argv[3])
ws = wb["LEIA-ME"]
for r in ws.iter_rows(values_only=True): print("LEIA-ME:", r)
mats = {}
for s in wb.sheetnames[1:]:
    rows = [[int(v or 0) for v in r] for r in wb[s].iter_rows(values_only=True)]
    assert len(rows) == M and all(len(r) == K for r in rows), s
    mats[s] = [[i for i in range(M) if rows[i][c]] for c in range(K)]
    rw = {sum(r) for r in rows}; cw = {len(x) for x in mats[s]}
    if rw != {16} or cw != {4}: print("  grau irregular", s, sorted(rw), sorted(cw))
rng = random.Random(7)
for i in range(4): mats[f"Rand_{i}"] = regular_H(rng)
def overlap(Hc):
    c = {}
    for a, b in itertools.combinations(range(K), 2):
        o = len(set(Hc[a]) & set(Hc[b]))
        if o >= 2: c[o] = c.get(o, 0) + 1
    return c
_pr = random.Random(100)
pats = {e: [_pr.sample(range(N), e) for _ in range(T)] for e in (48, 56, 64)}
prng = random.Random(11)
print(f"\n{T} padrões por condição (os mesmos para todas as matrizes); valores = % de recuperação integral")
print(f"{'matriz':10s} {'pares2+':>14s} | {'[H|I] 15%':>9s} {'17.5%':>6s} {'20%':>6s} {'raj48':>5s} | {'acum 15%':>8s} {'17.5%':>6s} {'20%':>6s} {'raj48':>5s} {'raj64':>5s}")
agg = {}
for name, Hc in mats.items():
    ov = overlap(Hc); c4 = sum(math.comb(o, 2) * n for o, n in ov.items())
    cI = cols_identity(Hc); p, _ = best_perm(Hc, prng, 2000); cA = cols_ira(Hc, p)
    r = []
    for cols in (cI, cA):
        for e in (48, 56, 64):
            r.append(100 * sum(full_rank(cols, E) for E in pats[e]) / T)
    bI, bA, bA64 = 320 - burst(cI, 48), 320 - burst(cA, 48), 320 - burst(cA, 64)
    print(f"{name:10s} {str(ov):>14s} | {r[0]:9.2f} {r[1]:6.2f} {r[2]:6.2f} {bI:5d} | {r[3]:8.2f} {r[4]:6.2f} {r[5]:6.2f} {bA:5d} {bA64:5d}   C4={c4}")
    g = name.rsplit("_", 1)[0]; agg.setdefault(g, []).append(r + [bI / 3.2, bA / 3.2])
print("\nMédias por família:")
for g, v in agg.items():
    m = [sum(x[i] for x in v) / len(v) for i in range(8)]
    print(f"{g:8s} [H|I]: {m[0]:.2f} {m[1]:.2f} {m[2]:.2f} raj {m[6]:.1f}% | acum: {m[3]:.2f} {m[4]:.2f} {m[5]:.2f} raj {m[7]:.1f}%")
