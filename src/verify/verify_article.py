#!/usr/bin/env python3
# Copyright 2026 Karlos Marden Maia
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files.
"""Verificação independente das fórmulas do artigo (docs/Maia_Prime-Ulam-ldpc.md).

Reconstrói o código final (Prime-Ulam v5+G) a partir APENAS das fórmulas do artigo e dos
parâmetros em src/construction/v5_p{p}.json, e compara, variável por variável, com o código
exportado em data/codes/code_p{p}.txt (o mesmo que o decodificador em C usa).

Também verifica:
  - taxa k/n = 0,80 e n = 40p;
  - ausência de ciclos de comprimento 4 na parte esparsa (dados);
  - padrão de transmissão "3 dados, 1 paridade" (uma paridade a cada quatro slots);
  - o experimento de grade com módulo composto (16) versus primo (17).

uso (a partir da raiz do repositório):  python3 -I src/verify/verify_article.py [p ...]
          padrão: p = 37 127
"""
import json
import os
import sys
from collections import Counter
from itertools import combinations

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
A = 32          # braços
R_DENSE = 16    # equações densas
DENSE_CENTERS = lambda p: [((5 * k) % p, (7 * k + 1) % p) for k in range(R_DENSE)]


def load_params(p):
    with open(os.path.join(ROOT, "src", "construction", f"v5_p{p}.json")) as f:
        return json.load(f)


def sparse_equations(D, p):
    """Equação esparsa de cada dado (i, j): q(i,j,c) = 10*((a_c*((j+s_c*i) mod p) + b_c) mod p) + c."""
    MB = D["MB"]
    eq = {}
    for i in range(A):
        for j in range(p):
            v = i * p + j
            eq[v] = {MB * ((D["a"][c] * ((j + D["passos"][c] * i) % p) + D["b"][c]) % p) + c
                     for c in D["masks"][i]}
    return eq


def build_article_code(p):
    """Reconstrói o código final conforme o artigo. Devolve dicionário com variáveis, tx, always, R."""
    D = load_params(p)
    MB = D["MB"]
    M, K = MB * p, A * p
    n = 40 * p
    rows = {}                              # linha (equação) -> conjunto de variáveis
    cols = {}                              # variável -> conjunto de linhas

    # 1) dados: parte esparsa
    sp = sparse_equations(D, p)
    for v, eqs in sp.items():
        cols[v] = set(eqs)
    # 2) paridades esparsas em acumulador fechado: paridade q entra em q-1 e q; paridade 0 em 0, M/2, M-1
    for q in range(M):
        cols[K + q] = {0, M // 2, M - 1} if q == 0 else {q - 1, q}
    # 3) 16 paridades esparsas perfuradas (substituídas pelas densas)
    punct_par = [K + (q * M) // R_DENSE + M // (2 * R_DENSE) for q in range(R_DENSE)]
    # 4) pré-código denso: equações M..M+15 contêm dados pela norma gaussiana e resíduo quadrático
    QR = {(x * x) % p for x in range(1, p)}
    for k, (a, b) in enumerate(DENSE_CENTERS(p)):
        for i in range(A):
            for j in range(p):
                if ((i - a) ** 2 + (j - b) ** 2) % p in QR:
                    cols[i * p + j].add(M + k)
        cols[K + M + k] = {M + k}          # variável da paridade densa
    # 5) braços não transmitidos (dados que nunca são enviados)
    always = [i * p + j for i in D["punct"] for j in range(p)] + punct_par
    # 6) ordem de transmissão
    tarms = [i for i in range(A) if i not in D["punct"]]
    At, g, h = len(tarms), D["g"], D["h"]
    tx, t, q = [], 0, 0
    for x in range(n):
        if (x + 1) * M // n > x * M // n:           # slot de paridade: 3 dados para 1 paridade
            tx.append(K + (h * q) % M); q += 1
        else:                                         # slot de dado
            tx.append(tarms[t % At] * p + (g * t) % p); t += 1
    # substitui as paridades perfuradas pelas densas nos mesmos slots
    pos = {v: s for s, v in enumerate(tx)}
    for k, v in enumerate(punct_par):
        tx[pos[v]] = K + M + k
    V = K + M + R_DENSE
    return dict(p=p, D=D, K=K, M=M, n=n, R=M + R_DENSE, V=V, cols=cols, tx=tx, always=always, sp=sp)


def read_export(p):
    path = os.path.join(ROOT, "data", "codes", f"code_p{p}.txt")
    with open(path) as f:
        head = list(map(int, f.readline().split()))
        always = list(map(int, f.readline().split()))
        tx = list(map(int, f.readline().split()))
        var_rows = []
        for _ in range(head[0]):
            parts = list(map(int, f.readline().split()))
            var_rows.append(set(parts[1:]))
    V, K, R, n, na, M = head
    return dict(V=V, K=K, R=R, n=n, always=always, tx=tx, var_rows=var_rows)


def c4_count(sets):
    """Recebe, para cada variável, o conjunto de equações que a contêm.
    Devolve quantos pares distintos de variáveis compartilham pelo menos duas equações (ciclos de comprimento 4)."""
    inv = {}
    for idx, eqs in enumerate(sets):
        for e in eqs:
            inv.setdefault(e, []).append(idx)
    shared = Counter()
    for vs in inv.values():
        for pair in combinations(sorted(vs), 2):
            shared[pair] += 1
    return sum(1 for c in shared.values() if c >= 2)


def check(p):
    print(f"=== p = {p} ===")
    art = build_article_code(p)
    exp = read_export(p)
    K, M, n = art["K"], art["M"], art["n"]
    ok = True

    # taxa e dimensões
    rate = K / n
    print(f"n = {n} (40p = {40 * p}), k = {K}, taxa k/n = {rate:.2f}")
    ok &= (n == 40 * p) and abs(rate - 0.80) < 1e-12

    # reconstrução variável por variável contra o arquivo exportado
    ok_hdr = (exp["V"] == art["V"] and exp["K"] == K and exp["R"] == art["R"]
              and exp["n"] == n and sorted(exp["always"]) == sorted(art["always"]))
    print(f"cabeçalho e lista 'always' batem com o exportado: {ok_hdr}")
    ok &= ok_hdr
    mism = 0
    for v in range(art["V"]):
        if set(art["cols"][v]) != exp["var_rows"][v]:
            mism += 1
    print(f"variáveis com linhas diferentes do exportado: {mism} de {art['V']}")
    ok &= mism == 0
    tx_ok = art["tx"] == exp["tx"]
    print(f"ordem de transmissão idêntica ao exportado: {tx_ok}")
    ok &= tx_ok

    # ciclos de comprimento 4 na parte esparsa (apenas dados)
    c4_sparse = c4_count(art["sp"].values())
    print(f"pares de dados com >= 2 equações esparsas em comum (ciclos-4 esparsos): {c4_sparse}")
    ok &= c4_sparse == 0

    # padrão de transmissão: uma paridade a cada quatro slots
    pat = ["P" if v >= K else "D" for v in art["tx"]]
    quads_ok = all(pat[s] == "P" for s in range(3, len(pat), 4)) and not any(pat[s] == "P" for s in range(0, len(pat), 4))
    print(f"padrão 3 dados / 1 paridade (uma paridade a cada quatro slots): {quads_ok}")
    ok &= quads_ok

    # equilíbrio das famílias (quantos braços por família)
    fam = Counter(c for m in art["D"]["masks"] for c in m)
    print(f"braços por família: min {min(fam.values())}, max {max(fam.values())}")

    print("RESULTADO:", "OK" if ok else "FALHOU")
    print()
    return ok


def grid_c4(m, steps):
    """Grade m x m (m braços, m radiais) com todos os braços em todas as famílias, passos dados mod m.
    Só é um teste válido de primo quando m é primo: os braços precisam ser distintos módulo m."""
    eqs = []
    for i in range(m):
        for j in range(m):
            eqs.append({c * m + ((j + steps[c] * i) % m) for c in range(len(steps))})
    return c4_count(eqs)


if __name__ == "__main__":
    ps = [int(x) for x in sys.argv[1:]] or [37, 127]
    results = [check(p) for p in ps]
    # comparação de módulo composto versus primo, com os mesmos passos (mod m)
    D = load_params(37)
    print("=== grade m x m (m braços, m radiais, 10 famílias, passos mod m) ===")
    for m in (16, 17):
        steps = [s % m for s in D["passos"]]
        print(f"m = {m}: pares de variáveis com >= 2 equações em comum = {grid_c4(m, steps)}")
    sys.exit(0 if all(results) else 1)
