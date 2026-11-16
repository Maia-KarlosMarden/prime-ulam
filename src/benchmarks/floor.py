"""Piso de erro com amostras grandes: só decodificação por posto (ML), mesmos padrões para os 3 códigos, intervalo de Wilson 95%.
uso: python3 -I floor.py <dir v4> <dir 5G> <p> <T> <frações separadas por vírgula> <código: 0=v5 1=5G 2=PEG>"""
import sys, os, random, json, time, math
HERE, BG, P, T, FR, WHICH = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), [float(x) for x in sys.argv[5].split(",")], int(sys.argv[6])
sys.argv = [sys.argv[0], HERE, BG]; sys.path.insert(0, HERE)
from v5 import build, prep, ml_ok, build_5g, build_peg
K, n = 32 * P, 40 * P
def build_v5(p):
    D = json.load(open(f"{HERE}/{os.environ.get('VER', 'v5')}_p{p}.json"))
    return build(p, D["MB"], D["masks"], D["punct"], D["passos"], D["a"], D["b"], D["g"], D["h"])
def wilson(k, N, z=1.96):
    ph = k / N; d = 1 + z * z / N; c = (ph + z * z / (2 * N)) / d; h = z * math.sqrt(ph * (1 - ph) / N + z * z / (4 * N * N)) / d
    return max(0, c - h), c + h
code = [lambda: build_v5(P), lambda: build_5g(K, n, BG), lambda: build_peg(K, 8 * P, random.Random(P))][WHICH]()
prep(code); out = {"nome": code["nome"], "T": T}
for f in FR:
    r = random.Random(int(f * 1000) + 7); e = round(f * n); fail = 0; t0 = time.time()
    for _ in range(T):
        E = r.sample(range(n), e)                      # mesma semente por fração: mesmos padrões nos 3 códigos
        fail += not ml_ok(code, [code["tx"][t] for t in E])
    lo, hi = wilson(fail, T); out[str(f)] = {"falhas": fail, "taxa": fail / T, "ic95": [lo, hi]}
    print(code["nome"], f, f"falhas {fail}/{T}  taxa {fail/T:.2e}  IC95% [{lo:.1e}, {hi:.1e}]  ({time.time()-t0:.0f}s)", flush=True)
json.dump(out, open(f"floor_{P}_{WHICH}.json", "w"))
