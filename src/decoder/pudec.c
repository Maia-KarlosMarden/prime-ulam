/* Copyright 2026 Karlos Marden Maia
 * SPDX-License-Identifier: Apache-2.0
 * Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files. */
/* Decodificador de apagamentos para o código Prime-Ulam final: peeling nas equações esparsas + eliminação GF(2) no resíduo
   (densas incluídas só quando o peeling trava). Pacotes de T bytes. Implementação direta, sem SIMD explícito.
   uso: ./pudec code.txt T trials f1,f2,...  */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
static int V, K, R, N, NA, MS; static int *always, *tx; static int **vrows, *vdeg, **rvars, *rdeg;
static int T; static long xors;
static inline void pxor(uint64_t *a, const uint64_t *b) { for (int i = 0; i < T / 8; i++) a[i] ^= b[i]; xors++; }
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
static uint64_t rs = 88172645463325252ull; static uint64_t xr(void) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return rs; }

/* decodifica: val[v] (pacotes), unk[v]=1 se incógnita. devolve 1 se resolveu tudo. */
static int decode(uint64_t **val, char *unk) {
    static int *cnt = 0, *stack, *ulist, *uidx, *elist; static uint64_t **rhs; static char *rhs_ok;
    if (!cnt) { cnt = malloc(R * sizeof(int)); stack = malloc(R * sizeof(int)); ulist = malloc(V * sizeof(int)); uidx = malloc(V * sizeof(int)); elist = malloc(R * sizeof(int));
                rhs = malloc(R * sizeof(uint64_t *)); for (int r = 0; r < R; r++) rhs[r] = aligned_alloc(64, T); rhs_ok = malloc(R); }
    int nu = 0; for (int v = 0; v < V; v++) if (unk[v]) ulist[nu++] = v;
    memset(cnt, 0, R * sizeof(int)); memset(rhs_ok, 0, R);
    for (int i = 0; i < nu; i++) for (int k = 0; k < vdeg[ulist[i]]; k++) cnt[vrows[ulist[i]][k]]++;
    /* lado direito das equações esparsas que têm incógnita: XOR dos conhecidos */
    for (int r = 0; r < MS; r++) if (cnt[r]) { memset(rhs[r], 0, T); rhs_ok[r] = 1; for (int k = 0; k < rdeg[r]; k++) if (!unk[rvars[r][k]]) pxor(rhs[r], val[rvars[r][k]]); }
    int sp = 0; for (int r = 0; r < MS; r++) if (cnt[r] == 1) stack[sp++] = r;
    int solved = 0;
    while (sp) { int r = stack[--sp]; if (cnt[r] != 1) continue; int v = -1; for (int k = 0; k < rdeg[r]; k++) if (unk[rvars[r][k]]) { v = rvars[r][k]; break; }
        memcpy(val[v], rhs[r], T); unk[v] = 0; solved++;
        for (int k = 0; k < vdeg[v]; k++) { int r2 = vrows[v][k]; cnt[r2]--; if (r2 < MS) { if (rhs_ok[r2]) pxor(rhs[r2], val[v]); if (cnt[r2] == 1) stack[sp++] = r2; } } }
    if (solved == nu) return 1;
    /* resíduo: incógnitas restantes u, equações = esparsas com cnt>=1 + densas (lado direito calculado agora) */
    int u = 0; for (int i = 0; i < nu; i++) if (unk[ulist[i]]) { uidx[ulist[i]] = u; ulist[u++] = ulist[i]; }
    int ne = 0; for (int r = 0; r < R; r++) if (cnt[r] > 0) { if (!rhs_ok[r]) { memset(rhs[r], 0, T); for (int k = 0; k < rdeg[r]; k++) if (!unk[rvars[r][k]]) pxor(rhs[r], val[rvars[r][k]]); rhs_ok[r] = 1; } elist[ne++] = r; }
    int W = (u + 63) / 64; uint64_t *bits = calloc((size_t)ne * W, 8); uint64_t **prow = malloc(ne * sizeof(uint64_t *));
    for (int i = 0; i < ne; i++) { int r = elist[i]; prow[i] = rhs[r]; for (int k = 0; k < rdeg[r]; k++) { int v = rvars[r][k]; if (unk[v]) bits[(size_t)i * W + uidx[v] / 64] |= 1ull << (uidx[v] % 64); } }
    int rank = 0; int *pivrow = malloc(u * sizeof(int));
    for (int c = 0; c < u && rank < ne; c++) { int w = c / 64; uint64_t m = 1ull << (c % 64); int p = -1;
        for (int i = rank; i < ne; i++) if (bits[(size_t)i * W + w] & m) { p = i; break; }
        if (p < 0) { free(bits); free(prow); free(pivrow); return 0; }
        if (p != rank) { for (int j = 0; j < W; j++) { uint64_t t = bits[(size_t)p * W + j]; bits[(size_t)p * W + j] = bits[(size_t)rank * W + j]; bits[(size_t)rank * W + j] = t; } uint64_t *t = prow[p]; prow[p] = prow[rank]; prow[rank] = t; }
        for (int i = 0; i < ne; i++) if (i != rank && (bits[(size_t)i * W + w] & m)) { for (int j = w; j < W; j++) bits[(size_t)i * W + j] ^= bits[(size_t)rank * W + j]; pxor(prow[i], prow[rank]); }
        pivrow[c] = rank; rank++; }
    for (int c = 0; c < u; c++) { memcpy(val[ulist[c]], prow[pivrow[c]], T); unk[ulist[c]] = 0; }
    free(bits); free(prow); free(pivrow); return 1;
}
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r"); T = atoi(argv[2]); int trials = atoi(argv[3]);
    if (fscanf(f, "%d %d %d %d %d %d", &V, &K, &R, &N, &NA, &MS) != 6) return 1;
    always = malloc(NA * sizeof(int)); for (int i = 0; i < NA; i++) fscanf(f, "%d", &always[i]);
    tx = malloc(N * sizeof(int)); for (int i = 0; i < N; i++) fscanf(f, "%d", &tx[i]);
    vrows = malloc(V * sizeof(int *)); vdeg = malloc(V * sizeof(int)); rdeg = calloc(R, sizeof(int));
    for (int v = 0; v < V; v++) { fscanf(f, "%d", &vdeg[v]); vrows[v] = malloc(vdeg[v] * sizeof(int)); for (int k = 0; k < vdeg[v]; k++) { fscanf(f, "%d", &vrows[v][k]); rdeg[vrows[v][k]]++; } }
    rvars = malloc(R * sizeof(int *)); for (int r = 0; r < R; r++) { rvars[r] = malloc(rdeg[r] * sizeof(int)); rdeg[r] = 0; }
    for (int v = 0; v < V; v++) for (int k = 0; k < vdeg[v]; k++) { int r = vrows[v][k]; rvars[r][rdeg[r]++] = v; }
    uint64_t **val = malloc(V * sizeof(uint64_t *)), **ref = malloc(V * sizeof(uint64_t *)); char *unk = malloc(V);
    for (int v = 0; v < V; v++) { val[v] = aligned_alloc(64, T); ref[v] = aligned_alloc(64, T); }
    /* codificação: dados aleatórios, paridades = incógnitas */
    for (int v = 0; v < K; v++) for (int i = 0; i < T / 8; i++) ((uint64_t *)ref[v])[i] = xr();
    for (int v = 0; v < V; v++) { memcpy(val[v], ref[v], T); unk[v] = v >= K; }
    if (!decode(val, unk)) { printf("falha na codificação\n"); return 1; }
    for (int v = 0; v < V; v++) memcpy(ref[v], val[v], T);
    printf("código: k=%d n=%d símbolos de %d B (bloco de dados %.2f MB)\n", K, N, T, K * (double)T / 1e6);
    char *fr = strdup(argv[4]); int *perm = malloc(N * sizeof(int));
    for (char *tok = strtok(fr, ","); tok; tok = strtok(0, ",")) { double fx = atof(tok); int e = (int)(fx * N + 0.5); int ok = 0; double tt = 0; long xt = 0; double tmax = 0;
        for (int t = 0; t < trials; t++) {
            for (int i = 0; i < N; i++) perm[i] = i; for (int i = 0; i < e; i++) { int j = i + xr() % (N - i); int s = perm[i]; perm[i] = perm[j]; perm[j] = s; }
            for (int v = 0; v < V; v++) { unk[v] = 0; } for (int i = 0; i < NA; i++) unk[always[i]] = 1; for (int i = 0; i < e; i++) unk[tx[perm[i]]] = 1;
            for (int v = 0; v < V; v++) if (!unk[v]) memcpy(val[v], ref[v], T);
            xors = 0; double t0 = now(); int r = decode(val, unk); double dt = now() - t0; tt += dt; xt += xors; if (dt > tmax) tmax = dt;
            if (r) { int good = 1; for (int v = 0; v < K && good; v++) if (memcmp(val[v], ref[v], T)) good = 0; ok += good; } }
        printf("perda %5.1f%% (e=%4d): sucesso %d/%d  tempo médio %.2f ms (máx %.2f)  = %.0f MB/s de dados  XORs de pacote/pacote de dados %.1f\n",
               100 * fx, e, ok, trials, 1000 * tt / trials, 1000 * tmax, K * (double)T / 1e6 / (tt / trials), (double)xt / trials / K); }
    return 0;
}
