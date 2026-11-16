"""Valida minha montagem do 5G NR (compare.build_5g) contra o codificador de referência Sionna (3GPP TS 38.212)."""
import sys, numpy as np, torch
import os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.argv = [sys.argv[0], "0", "0", os.path.join(ROOT, "src", "construction"), os.path.join(ROOT, "data", "5g")]
sys.path.insert(0, os.path.join(ROOT, "src", "benchmarks"))
import os as _os; sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "benchmarks")); sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "construction"))  # BENCH_DIR
from compare import build_5g
from sionna.phy.fec.ldpc import LDPC5GEncoder
BG = os.path.join(ROOT, "data", "5g")
ok_all = True
for (K, n) in [(1184, 1480), (4064, 5080), (1072, 1340), (4112, 5140), (272, 340), (1024, 1280)]:
    e = LDPC5GEncoder(K, n); Z, kl = e.z, e.k_ldpc; pcm = e.pcm.tocsr()
    mine = build_5g(K, n, BG); R = mine["R"]; cols = mine["cols"]; always = set(mine["always"])
    kbf = 22 if "BG1" in mine["nome"] else 10
    npar = len(cols) - K
    # 1) H: mesma matriz?
    sub = pcm[:R, :].tocsc(); bad = 0
    for v in range(K + npar):
        c = v if v < K else kbf * Z + (v - K)
        ref = set(sub[:, c].indices.tolist()); got = {r for r in range(R) if (cols[v] >> r) & 1}
        bad += ref != got
    # linhas fora de R só valem se tiverem uma incógnita própria (coluna de paridade não transmitida de grau 1): então não restringem nada
    used = np.r_[np.arange(K), kbf * Z + np.arange(npar)]
    deg = np.asarray(pcm.sum(axis=0)).ravel(); usedset = set(used.tolist()); filler = set(range(K, kl))
    free = [c for c in range(pcm.shape[1]) if c not in usedset and c not in filler and deg[c] == 1]
    freeset = set(free); rest = 0
    for r in range(R, pcm.shape[0]):
        cs = set(pcm.indices[pcm.indptr[r]:pcm.indptr[r + 1]].tolist())
        rest += not (cs & freeset)
    # 2) codificação ponta a ponta
    rng = np.random.default_rng(1); U = rng.integers(0, 2, (20, K)).astype(np.float32)
    C = e(torch.tensor(U)).numpy().astype(np.int64); U = U.astype(np.int64); viol = 0; sysbad = 0
    for u, c in zip(U, C):
        sysbad += int((c[:K - 2 * Z] != u[2 * Z:]).any())
        P = n - (K - 2 * Z); x = np.r_[u, c[K - 2 * Z:]]; assert len(x) == K + P
        xs = np.r_[x, np.zeros(max(0, npar - P), dtype=np.int64)]
        s = np.zeros(R, dtype=np.int64)
        for v in range(K + npar):
            if xs[v]:
                for r in range(R):
                    if (cols[v] >> r) & 1: s[r] ^= 1
        sv = sum(1 << r for r in range(R) if s[r]); bs = {}
        for v in sorted(always):
            if v >= K: 
                w = cols[v]
                while w:
                    h = w.bit_length() - 1
                    if h in bs: w ^= bs[h]
                    else: bs[h] = w; break
        while sv:
            h = sv.bit_length() - 1
            if h in bs: sv ^= bs[h]
            else: break
        viol += int(sv != 0)   # síndrome tem que estar no espaço das paridades não transmitidas
    # 3) conjunto de colunas conhecidas/perfuradas
    punct = sorted(always)[:3]
    ok = bad == 0 and viol == 0 and sysbad == 0 and rest == 0
    ok_all &= ok
    print(f"K={K:5d} n={n:5d} {mine['nome']:18s} Z={Z:3d} R={R:5d} colunas_diferentes={bad} linhas_extra_com_incógnita_livre_faltando={rest} "
          f"palavras_com_sindrome!=0 {viol}/20  sistemática_divergente {sysbad}/20  perfurados={len(always)}  -> {'OK' if ok else 'FALHA'}", flush=True)
print("TUDO OK" if ok_all else "HÁ DIVERGÊNCIA")
