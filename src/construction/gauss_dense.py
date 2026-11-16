"""Equações densas por FÓRMULA (ideia do Karlos, traduzida para GF(2)):
 ponto (braço i, raio j) -> inteiro gaussiano z = i + j·I mod p.  Equação k tem centro c_k = a_k + b_k·I.
 bit entra na equação k  <=>  Norma(z - c_k) = (i-a_k)^2 + (j-b_k)^2 é resíduo quadrático (não nulo) mod p.
 Compara com r equações densas aleatórias (mesmo r), mesmos padrões de apagamento.
uso: python3 -I gauss_dense.py <dir v4> <dir 5G> <p> <padrões> <r> <fração>"""
import sys, random, json
HERE, BG, P, T, R_, FS = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), [float(x) for x in sys.argv[6].split(",")]; sys.argv = [sys.argv[0], HERE, BG]; sys.path.insert(0, HERE)
from v5 import build, prep, ml_ok, peel
D = json.load(open(f"{HERE}/v5_p{P}.json")); K, n, M = 32 * P, 40 * P, D["MB"] * P
QR = {(x * x) % P for x in range(1, P)}
def base():
    c = build(P, D["MB"], D["masks"], D["punct"], D["passos"], D["a"], D["b"], D["g"], D["h"]); return c, list(c["cols"]), list(c["tx"])
def finish(c, cols, tx, r, nome):
    b0 = len(c["cols"])
    for k in range(r): cols.append(1 << (M + k)); tx.append(b0 + k)
    c["cols"], c["tx"], c["R"], c["nome"] = cols, tx, M + r, nome; prep(c); return c
def gauss(r, centers):
    c, cols, tx = base()
    for k, (a, b) in enumerate(centers):
        for i in range(32):
            for j in range(P):
                if ((i - a) ** 2 + (j - b) ** 2) % P in QR: cols[i * P + j] |= 1 << (M + k)
    dens = [bin(cols[v] >> M).count("1") for v in range(K)]
    return finish(c, cols, tx, r, f"gaussiana r={r}")
def rnd(r, seed):
    c, cols, tx = base(); rr = random.Random(seed)
    for k in range(r):
        for v in range(K):
            if rr.random() < 0.5: cols[v] |= 1 << (M + k)
    return finish(c, cols, tx, r, f"aleatória r={r}")
rng = random.Random(3)
cands = [("gauss. centros aleatórios", gauss(R_, [(rng.randrange(P), rng.randrange(P)) for _ in range(R_)])),
         ("gauss. centros na diagonal", gauss(R_, [((5 * k) % P, (7 * k + 1) % P) for k in range(R_)])),
         ("aleatória", rnd(R_, 1))]
for F in FS:
    r = random.Random(int(F * 1000) + 7); e = round(F * n); n2 = n + R_
    pats = [r.sample(range(n2), e) for _ in range(T)]
    for nome, c in cands:
        tx = c["tx"]; fail = 0
        for E in pats: fail += not ml_ok(c, [tx[t] for t in E])
        print(f"p={P} {nome:28s} r={R_} apagamentos={e}/{n2} ({F:.1%}): falhas {fail}/{T} = {fail/T:.2e}", flush=True)
