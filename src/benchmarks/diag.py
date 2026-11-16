import sys, random, json
HERE, BG, P = sys.argv[1], sys.argv[2], int(sys.argv[3]); sys.argv = [sys.argv[0], HERE, BG]; sys.path.insert(0, HERE)
from v5 import build, prep
D = json.load(open(f"{HERE}/v5_p{P}.json")); c = build(P, D["MB"], D["masks"], D["punct"], D["passos"], D["a"], D["b"], D["g"], D["h"]); prep(c)
K, n, M = 32 * P, 40 * P, D["MB"] * P; cols = c["cols"]; tx = c["tx"]; always = c["always"]
arm = lambda v: v // P
degof = {i: len(D["masks"][i]) for i in range(32)}
def kind(v):
    if v >= K: return "paridade"
    return "dado grau %d" % degof[arm(v)]
def dependency(E):
    basis = {}; 
    for v in list(always) + E:
        w = cols[v]; combo = 1 << (len(basis) and 0)  # placeholder
    return None
def dep(E):
    order = list(always) + [tx[t] for t in E]; basis = {}
    for idx, v in enumerate(order):
        w = cols[v]; cb = 1 << idx
        while w:
            h = w.bit_length() - 1
            if h in basis: bw, bc = basis[h]; w ^= bw; cb ^= bc
            else: basis[h] = (w, cb); break
        if not w: return [order[i] for i in range(len(order)) if (cb >> i) & 1]
    return None
r = random.Random(5); fails = []; tried = 0
while len(fails) < 150 and tried < 400000:
    tried += 1; E = r.sample(range(n), round(0.175 * n)); d = dep(E)
    if d: fails.append(d)
from collections import Counter
print("padrões testados", tried, "falhas", len(fails))
sizes = Counter(len([v for v in d if v not in set(always)]) for d in fails); print("bits transmitidos na dependência (tamanho):", sorted(sizes.items()))
comp = Counter(); punc = Counter()
for d in fails:
    punc[len([v for v in d if v in set(always)])] += 1
    for v in d:
        if v not in set(always): comp[kind(v)] += 1
print("composição (bits transmitidos):", dict(comp)); print("perfurados na dependência:", sorted(punc.items()))
print("--- estrutura das dependências: (bits de dados, tamanho da síndrome) ---")
cnt = Counter(); rowsets = c["rows"]
for d in fails:
    D = [v for v in d if v < K]; syn = set()
    for v in D: syn ^= set(rowsets[v])
    cnt[(len(D), len(syn))] += 1
print(sorted(cnt.items(), key=lambda x: -x[1])[:14])
