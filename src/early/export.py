# Copyright 2026 Karlos Marden Maia
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files.
import json, sys, random, openpyxl
from openpyxl.styles import Font
sys.path.insert(0, sys.argv[1])
from sim import K, M, N, full_rank
out = sorted(json.load(open(sys.argv[2])), key=lambda r: r["name"])
wb = openpyxl.Workbook(); ws = wb.active; ws.title = "LEIA-ME"
for row in [("PRIME-ULAM v2 | MATRIZES MELHORADAS", None), ("Matrizes", len(out)),
    ("Origem", "A_opt_* e H_opt_* do arquivo prime_ulam_16_matrizes.xlsx"),
    ("Abas *_v2", "H_full 64 x 320, colunas JA na ordem de transmissao"),
    ("Aba ordem_tx", "o que cada coluna transmitida e: D0..D255 = dado, P0..P63 = paridade"),
    ("Paridade", "acumulador: P_j entra nas equacoes j e j+1 (P63 so na 63)"),
    ("Graus", "dados: 4 por coluna, 16 por linha (inalterado)"),
    ("Etapa 1", "ciclos-4 removidos por troca de arestas"),
    ("Etapa 2", "ordem das linhas otimizada para o acumulador"),
    ("Etapa 3", "ordem de transmissao otimizada contra rajadas"),
    ("Medida", "recuperacao integral dos 320 bits por posto em GF(2); 20.000 padroes aleatorios; 320 rajadas ciclicas")]:
    ws.append(row)
ws["A1"].font = Font(bold=True); ws.column_dimensions["A"].width = 16; ws.column_dimensions["B"].width = 90
rs = wb.create_sheet("Resultados")
rs.append(["Matriz", "Ciclos-4 antes", "Ciclos-4 depois", "Arestas mantidas", "Rajada garantida (bits)",
           "Aleat. 15% antes", "Aleat. 15% depois", "Aleat. 17,5% antes", "Aleat. 17,5% depois", "Aleat. 20% antes", "Aleat. 20% depois",
           "Rajada 48 antes", "Rajada 48 depois", "Rajada 56 antes", "Rajada 56 depois", "Rajada 64 antes", "Rajada 64 depois"])
for c in rs[1]: c.font = Font(bold=True)
ot = wb.create_sheet("ordem_tx"); ot.append(["posicao"] + [r["name"] + "_v2" for r in out])
for c in ot[1]: c.font = Font(bold=True)
for t in range(N): ot.append([t] + [("D%d" % r["tx"][t]) if r["tx"][t] < K else ("P%d" % (r["tx"][t] - K)) for r in out])
for r in out:
    a, d = r["antes"], r["depois"]
    rs.append([r["name"] + "_v2", r["c4_antes"], r["c4_depois"], round(r["arestas_mantidas"], 3), r["rajada_garantida"]] +
              [round(x / 100, 4) for k in ("rand48", "rand56", "rand64", "burst48", "burst56", "burst64") for x in (a[k], d[k])])
    H = r["H"]; full = [row + [1 if (i == j or i == j + 1) else 0 for j in range(M)] for i, row in enumerate(H)]
    s = wb.create_sheet(r["name"] + "_v2")
    for row in full: s.append([row[c] for c in r["tx"]])
for row in rs.iter_rows(min_row=2):
    row[3].number_format = "0%"
    for c in row[5:]: c.number_format = "0.00%"
for i in range(1, 18): rs.column_dimensions[openpyxl.utils.get_column_letter(i)].width = 19
rs.freeze_panes = "B2"
wb.save(sys.argv[3])
# verificação independente a partir do arquivo salvo
wb = openpyxl.load_workbook(sys.argv[3]); rng = random.Random(4242)
for r in out:
    g = [[int(v) for v in row] for row in wb[r["name"] + "_v2"].iter_rows(values_only=True)]
    cols = [sum(1 << i for i in range(M) if g[i][c]) for c in range(N)]
    rw = {sum(row) for row in g}
    res = [100 * sum(full_rank(cols, rng.sample(range(N), e)) for _ in range(20000)) / 20000 for e in (48, 56)]
    b = {L: sum(full_rank(cols, [(s + i) % N for i in range(L)]) for s in range(N)) for L in (48, 56, 60, 62, 63, 64)}
    print(r["name"], "pesos de linha", sorted(rw), "aleat 15%% %.2f 17.5%% %.2f" % tuple(res), "rajadas ok/320", b)
