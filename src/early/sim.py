# Copyright 2026 Karlos Marden Maia
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files.
"""Prime-Ulam LDPC — teste do piso de erro da estrutura [H | I] e de alternativas.
n=320, k=256, m=64; peso de coluna 4, peso de linha 16 (parte de dados)."""
import random, math, sys
K, M, N, WC = 256, 64, 320, 4

def regular_H(rng):
    """Gallager: 4 camadas, cada coluna 1 linha por camada, sem arestas duplicadas."""
    lay = []
    for l in range(WC):
        rows = [r for r in range(M) for _ in range(K // M)]
        rng.shuffle(rows)
        lay.append(rows)
    def bad(c): return len({lay[l][c] for l in range(WC)}) < WC
    for _ in range(100000):
        b = [c for c in range(K) if bad(c)]
        if not b: break
        c = b[0]; l = rng.randrange(1, WC); d = rng.randrange(K)
        lay[l][c], lay[l][d] = lay[l][d], lay[l][c]
    return [sorted(lay[l][c] for l in range(WC)) for c in range(K)]  # linhas por coluna

def cols_identity(Hc):
    return [sum(1 << r for r in rs) for rs in Hc] + [1 << r for r in range(M)]

def cols_ira(Hc, perm):
    """Paridade bidiagonal (acumulador): coluna j tem 1 nas linhas j e j+1."""
    data = [sum(1 << perm[r] for r in rs) for rs in Hc]
    par = [(1 << j) | ((1 << (j + 1)) if j + 1 < M else 0) for j in range(M)]
    return data + par

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

def w1_parity_weight(rs, perm):
    """Peso da paridade gerada por 1 bit de dados no código IRA."""
    s = 0
    for r in rs: s ^= 1 << perm[r]
    w, acc = 0, 0
    for j in range(M):
        acc ^= (s >> j) & 1
        w += acc
    return w

def best_perm(Hc, rng, tries=3000):
    best, bp = None, None
    for _ in range(tries):
        p = list(range(M)); rng.shuffle(p)
        ws = sorted(w1_parity_weight(rs, p) for rs in Hc)
        key = (ws[0], -sum(1 for w in ws if w < 12))
        if best is None or key > best: best, bp = key, p
    return bp, best

def run(cols, e, trials, rng, expl=None):
    fail = hit = 0
    for _ in range(trials):
        E = rng.sample(range(N), e)
        if not full_rank(cols, E):
            fail += 1
            if expl and expl(set(E)): hit += 1
    return fail, hit

def burst(cols, e):
    return sum(not full_rank(cols, [(s + i) % N for i in range(e)]) for s in range(N))

if __name__ == "__main__":
    rng = random.Random(2026)
    T = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    print("Piso teórico (só palavras de peso 5), e=48:",
          K * math.comb(N - 5, 48 - 5) / math.comb(N, 48))
    print("Código linear aleatório denso, falha ~ 2^-(64-48) =", 2.0 ** -16)
    for e in (48, 56):
        tot = {"I": [0, 0], "IRA": [0, 0], "IRAopt": [0, 0]}
        for mtx in range(10):
            Hc = regular_H(rng)
            cI = cols_identity(Hc)
            def expl(E, Hc=Hc):  # bit de dados + suas 4 paridades apagados
                return any(c in E and all(K + r in E for r in Hc[c]) for c in range(K) if c in E)
            f, h = run(cI, e, T // 10, rng, expl); tot["I"][0] += f; tot["I"][1] += h
            f, _ = run(cols_ira(Hc, list(range(M))), e, T // 10, rng); tot["IRA"][0] += f
            p, key = best_perm(Hc, rng)
            cO = cols_ira(Hc, p)
            f, _ = run(cO, e, T // 10, rng); tot["IRAopt"][0] += f
            if e == 48 and mtx < 3:
                print(f"  matriz {mtx}: rajadas de 48 falhas/320  [H|I]={burst(cI,48)}  IRAopt={burst(cO,48)}  (min peso-1 paridade={key[0]})")
        print(f"e={e} ({e/N:.1%}), {T} padrões, 10 matrizes:")
        print(f"  [H|I]      recuperação {1-tot['I'][0]/T:.4%}  | falhas explicadas por peso-5: {tot['I'][1]}/{tot['I'][0]}")
        print(f"  [H|acum]   recuperação {1-tot['IRA'][0]/T:.4%}")
        print(f"  [H|acum]+perm. linhas otimizada  {1-tot['IRAopt'][0]/T:.4%}")

