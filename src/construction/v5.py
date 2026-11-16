"""Prime-Ulam v5: fórmula irregular + braços NÃO transmitidos + cadeia de paridade fechada.
 A braços x p posições radiais (p primo > A); todos são dados (K = A*p), mas os braços 'punct' não são transmitidos.
 MB famílias de espirais -> M = MB*p equações e M paridades. Transmitidos: n = (A - |punct| + MB)*p = 40p; taxa 0,80.
 Paridade: coluna 0 nas equações {0, M/2, M-1}; coluna q >= 1 nas equações {q-1, q} (sem ponta solta no fim da cadeia)."""
import sys, random, json, time, itertools, math
HERE = sys.argv[1]; BG = sys.argv[2]; ARGS = sys.argv[3:]; sys.argv = [sys.argv[0], "0", "0", HERE, BG]; sys.path.insert(0, HERE)
import os as _os; sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "benchmarks")); sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "construction"))  # BENCH_DIR
from compare import prep, ml_ok, peel, burst_guarantee, build_5g, build_peg, reduce

def assign(cfg, rng):
    MB = cfg["MB"]; degs = cfg["punct_deg"] + cfg["degs"]; w = [0] * MB; masks = []
    for d in degs:
        fam = sorted(range(MB), key=lambda c: w[c] + 2.5 * rng.random())[:d]
        for c in fam: w[c] += 1
        masks.append(sorted(fam))
    arms = list(range(len(degs))); rng.shuffle(arms)          # braço geométrico de cada perfil
    out = [None] * len(degs)
    for k, i in enumerate(arms): out[i] = masks[k]
    return out, sorted(arms[:len(cfg["punct_deg"])])

def build(p, MB, masks, punct, slopes, a, b, g=1, h=1):
    A = len(masks); K, M = A * p, MB * p; rows = []
    for i in range(A):
        for j in range(p):
            rows.append([MB * ((a[c] * ((j + slopes[c] * i) % p) + b[c]) % p) + c for c in masks[i]])
    par = [(1 << 0) | (1 << (M // 2)) | (1 << (M - 1))] + [(1 << (q - 1)) | (1 << q) for q in range(1, M)]
    cols = [sum(1 << r for r in rs) for rs in rows] + par
    tarms = [i for i in range(A) if i not in punct]; At = len(tarms); n = (At + MB) * p; tx = []; t = q = 0
    for x in range(n):
        if (x + 1) * M // n > x * M // n: tx.append(K + (h * q) % M); q += 1
        else: tx.append(tarms[t % At] * p + (g * t) % p); t += 1
    always = [i * p + j for i in punct for j in range(p)]
    assert len(set(tx)) == n and not set(tx) & set(always)
    return dict(nome="Prime-Ulam v5 (fórmula)", cols=cols, tx=tx, always=always, R=M, rows=rows, sent=[i not in punct for i in range(A) for _ in range(p)])

def lowweight(code, M, Q=0.15, pairs=True):
    rows, sent = code["rows"], code["sent"]; mid = M // 2
    def w(s, base):
        if len(s) & 1: s = s ^ {0, mid, M - 1}; base += 1
        tot = 0; acc = 0; prev = 0
        for r in sorted(s): tot += (r - prev) * acc; acc ^= 1; prev = r
        return base + tot
    cost = 0.0; wmin = 10**9; lines = {}
    for d, rs in enumerate(rows):
        x = w(set(rs), int(sent[d])); cost += Q ** x; wmin = min(wmin, x)
        for r in rs: lines.setdefault(r, []).append(d)
    for pts in (lines.values() if pairs else ()):
        for u, v in itertools.combinations(pts, 2):
            x = w(set(rows[u]) ^ set(rows[v]), int(sent[u]) + int(sent[v])); cost += Q ** x; wmin = min(wmin, x)
    return cost, wmin

def c4_count(rows):
    seen = {}; c4 = 0
    for rs in rows:
        for xy in itertools.combinations(sorted(rs), 2): c4 += seen.get(xy, 0); seen[xy] = seen.get(xy, 0) + 1
    return c4
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
def coprime(M, rng):
    while True:
        h = rng.randrange(1, M)
        if math.gcd(h, M) == 1: return h

CFGS = {
 "a 2P7 + 30x3":        dict(MB=10, punct_deg=[7, 7], degs=[3] * 30),
 "b 2P8 + 30x3":        dict(MB=10, punct_deg=[8, 8], degs=[3] * 30),
 "c 2P8 + 4x6+26x3":    dict(MB=10, punct_deg=[8, 8], degs=[6] * 4 + [3] * 26),
 "d 2P8 + 6x8+24x3":    dict(MB=10, punct_deg=[8, 8], degs=[8] * 6 + [3] * 24),
 "e 2P9 + 4x7+26x3":    dict(MB=10, punct_deg=[9, 9], degs=[7] * 4 + [3] * 26),
 "f 2P8 + 8x4+22x3":    dict(MB=10, punct_deg=[8, 8], degs=[4] * 8 + [3] * 22),
 "g 4P8 + 28x3":        dict(MB=12, punct_deg=[8] * 4, degs=[3] * 28),
 "h 4P9 + 4x6+24x3":    dict(MB=12, punct_deg=[9] * 4, degs=[6] * 4 + [3] * 24),
 "i 2P8 + 4x6+16x3+10x2": dict(MB=10, punct_deg=[8, 8], degs=[6] * 4 + [3] * 16 + [2] * 10),
}

if __name__ == "__main__":
    mode = ARGS[0]
    if mode == "search":
        p = 37; n = 40 * p; rng = random.Random(21); pats = patterns(n, (0.165, 0.175, 0.19, 0.195), 150, 1); best = None
        for name, cfg in CFGS.items():
            if len(ARGS) > 2 and name[0] not in ARGS[2]: continue
            for k in range(int(ARGS[1])):
                MB = cfg["MB"]; masks, punct = assign(cfg, rng); slopes = rng.sample(range(-15, 16), MB)
                a = [rng.randrange(1, p) for _ in range(MB)]; b = [rng.randrange(p) for _ in range(MB)]
                try: s = score(build(p, MB, masks, punct, slopes, a, b), pats)
                except AssertionError: print(name, k, "inválido"); continue
                tot = s[0.19][0] + s[0.195][0] + s[0.165][1] + s[0.175][1]
                print(f"{name:24s} #{k} arestas/p={sum(map(len, masks)):3d} ML19={s[0.19][0]:5.1f} ML19.5={s[0.195][0]:5.1f} peel16.5={s[0.165][1]:5.1f} peel17.5={s[0.175][1]:5.1f} soma={tot:.0f}", flush=True)
                if best is None or tot > best[0]: best = (tot, name, MB, masks, punct, slopes)
        json.dump(dict(zip(("soma", "perfil", "MB", "masks", "punct", "passos"), best)), open("v5_design.json", "w")); print("escolhido:", best[1], best[0])
    else:
        p = int(mode); T = int(ARGS[1]); D = json.load(open("v5_design.json")); MB = D["MB"]; M = MB * p; n = 40 * p; K = 32 * p; rng = random.Random(p)
        mk = lambda a, b, g=1, h=1: build(p, MB, D["masks"], D["punct"], D["passos"], a, b, g, h)
        t0 = time.time(); pool = []
        for _ in range(int(ARGS[2])):
            a = [rng.randrange(1, p) for _ in range(MB)]; b = [rng.randrange(p) for _ in range(MB)]
            pool.append((lowweight(mk(a, b), M, pairs=False), a, b))
        pool.sort(key=lambda x: x[0][0]); best = None
        for _, a, b in pool[:5]:
            c = lowweight(mk(a, b), M)
            if best is None or c[0] < best[0][0]: best = (c, a, b)
        (cst, wmin), a, b = best; print("antes do polimento: custo %.3g peso_min %d" % (cst, wmin), flush=True)
        for _ in range(int(ARGS[4]) if len(ARGS) > 4 else 0):   # busca local nos coeficientes da cadeia
            a2, b2 = list(a), list(b); c = rng.randrange(MB)
            if rng.random() < 0.5: a2[c] = rng.randrange(1, p)
            else: b2[c] = rng.randrange(p)
            c2 = lowweight(mk(a2, b2), M)
            if c2[0] < cst: (cst, wmin), a, b = c2, a2, b2
        print("depois do polimento: custo %.3g peso_min %d" % (cst, wmin), flush=True)
        st = range(n) if n <= 2000 else random.Random(3).sample(range(n), 150); bl = (0, 1, 1)
        for _ in range(int(ARGS[3])):
            g = rng.randrange(1, p); h = coprime(M, rng); cand = mk(a, b, g, h); cand["base"] = {}
            assert all(reduce(cand["base"], cand["cols"][v]) for v in cand["always"])
            G = burst_guarantee(cand, st)
            if G > bl[0]: bl = (G, g, h)
        code = mk(a, b, bl[1], bl[2]); assert len(code["cols"]) - len(code["always"]) == n and K == len(code["rows"])
        json.dump(dict(D, p=p, a=a, b=b, g=bl[1], h=bl[2]), open(f"v5_p{p}.json", "w"))
        print("v5", D["perfil"], "p", p, "n", n, "K", K, "equações", M, "peso_min", wmin, "c4", c4_count(code["rows"]), "seg", round(time.time() - t0), flush=True)
        fr = (0.10, 0.15, 0.165, 0.17, 0.175, 0.19, 0.195); pats = patterns(n, fr, T, 555)
        for c in (code, build_5g(K, n, BG), build_peg(K, 8 * p, random.Random(p))):
            s = score(c, pats)
            print(json.dumps({"nome": c["nome"], "arestas": sum(len(r) for r in c["vrows"]), "equacoes": c["R"],
                              "ML": {f: round(s[f][0], 2) for f in fr}, "peel": {f: round(s[f][1], 2) for f in fr},
                              "rajada": burst_guarantee(c, st)}, ensure_ascii=False), flush=True)
