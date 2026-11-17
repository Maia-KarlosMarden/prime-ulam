# Copyright 2026 Karlos Marden Maia
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files.
"""Encoder and decoder: peeling on the sparse equations, then Gaussian elimination over GF(2).

The encoder is the decoder with every parity symbol treated as an unknown (as in
``src/decoder/pudec.c``): the data symbols are known, so the system is solved for the parities.

Everything is XOR of packets. Success means *every* unknown variable is determined,
i.e. the erased columns of H are linearly independent (the criterion used in the paper).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class Stats:
    unknowns: int = 0          # unknown variables at the start (erased + never-transmitted)
    peeled: int = 0            # solved by peeling
    residual: int = 0          # unknowns left for Gaussian elimination
    rank: int = 0              # rank reached in the residual system
    xors: int = 0              # packet XORs performed (payload mode only)

    @property
    def peeling_only(self) -> bool:
        return self.residual == 0


@dataclass
class DecodeResult:
    ok: bool
    data: Optional[np.ndarray]            # (K, S) when ok, else None
    stats: Stats = field(default_factory=Stats)
    recovered_data: int = 0               # data symbols known at the end (even when not ok)


def _xor(dst: np.ndarray, src: np.ndarray, st: Stats) -> None:
    np.bitwise_xor(dst, src, out=dst)
    st.xors += 1


def _solve(code, unk: bytearray, vals: Optional[np.ndarray]):
    """Resolve unknown variables. ``unk[v]=1`` marks unknowns; ``vals`` (V,S) holds known values
    and receives the solution (None -> structure only). Returns (ok, Stats)."""
    V, R, M = code.V, code.R, code.M
    rows, cols = code.rows, code.cols
    st = Stats()
    unknown = [v for v in range(V) if unk[v]]
    st.unknowns = len(unknown)
    cnt = [0] * R
    for v in unknown:
        for r in cols[v]:
            cnt[r] += 1

    rhs = {}
    if vals is not None:
        for r in range(M):                                  # sparse equations with unknowns
            if cnt[r]:
                acc = np.zeros(vals.shape[1], dtype=np.uint8)
                for v in rows[r]:
                    if not unk[v]:
                        _xor(acc, vals[v], st)
                rhs[r] = acc

    # ---- peeling on the sparse equations only
    stack = [r for r in range(M) if cnt[r] == 1]
    while stack:
        r = stack.pop()
        if cnt[r] != 1:
            continue
        v = next(x for x in rows[r] if unk[x])
        if vals is not None:
            vals[v] = rhs[r]
        unk[v] = 0
        st.peeled += 1
        for r2 in cols[v]:
            cnt[r2] -= 1
            if r2 < M:
                if vals is not None and r2 in rhs:
                    _xor(rhs[r2], vals[v], st)
                if cnt[r2] == 1:
                    stack.append(r2)
    left = [v for v in unknown if unk[v]]
    st.residual = len(left)
    if not left:
        return True, st

    # ---- Gaussian elimination over GF(2) on the residual system
    uidx = {v: i for i, v in enumerate(left)}
    pivots = {}                                              # lowest set bit -> (mask, payload)
    rank = 0
    for r in range(code.R):
        if cnt[r] == 0:
            continue
        mask = 0
        for v in rows[r]:
            if unk[v]:
                mask |= 1 << uidx[v]
        pay = None
        if vals is not None:
            pay = rhs[r].copy() if r in rhs else np.zeros(vals.shape[1], dtype=np.uint8)
            if r not in rhs:                                 # dense equation: known part now
                for v in rows[r]:
                    if not unk[v]:
                        _xor(pay, vals[v], st)
        while mask:
            low = mask & -mask
            piv = pivots.get(low)
            if piv is None:
                pivots[low] = (mask, pay)
                rank += 1
                break
            mask ^= piv[0]
            if pay is not None:
                _xor(pay, piv[1], st)
    st.rank = rank
    if rank < len(left):
        return False, st
    if vals is not None:                                     # back-substitution, highest pivot first
        for low in sorted(pivots, reverse=True):
            mask, pay = pivots[low]
            i = low.bit_length() - 1
            rest = mask ^ low
            while rest:
                lb = rest & -rest
                _xor(pay, vals[left[lb.bit_length() - 1]], st)
                rest ^= lb
            vals[left[i]] = pay
    for v in left:
        unk[v] = 0
    return True, st


def encode(code, data: np.ndarray, *, stats: Optional[Stats] = None) -> np.ndarray:
    """Encode ``K`` data symbols (shape (K, S), uint8) into the ``n`` transmitted symbols (n, S)."""
    data = np.ascontiguousarray(data, dtype=np.uint8)
    if data.ndim != 2 or data.shape[0] != code.K:
        raise ValueError(f"data must have shape ({code.K}, S)")
    vals = np.zeros((code.V, data.shape[1]), dtype=np.uint8)
    vals[: code.K] = data
    unk = bytearray(code.V)
    for v in range(code.K, code.V):
        unk[v] = 1
    ok, st = _solve(code, unk, vals)
    if not ok:                                               # cannot happen for the shipped parameter sets
        raise RuntimeError("encoding failed: parity system is rank deficient")
    if stats is not None:
        stats.__dict__.update(st.__dict__)
    return vals[np.asarray(code.tx)]


def decode(code, symbols: np.ndarray, received: Sequence[bool]) -> DecodeResult:
    """Decode from transmitted symbols ``symbols`` (n, S) and a boolean mask ``received`` (n,)."""
    symbols = np.asarray(symbols, dtype=np.uint8)
    received = np.asarray(received, dtype=bool)
    if symbols.shape[0] != code.n or received.shape != (code.n,):
        raise ValueError(f"expected {code.n} symbols and a mask of the same length")
    vals = np.zeros((code.V, symbols.shape[1]), dtype=np.uint8)
    unk = bytearray(b"\x01" * code.V)
    for s in np.flatnonzero(received):
        v = code.tx[s]
        vals[v] = symbols[s]
        unk[v] = 0
    ok, st = _solve(code, unk, vals)
    rec = sum(1 for v in range(code.K) if not unk[v])
    return DecodeResult(ok, vals[: code.K].copy() if ok else None, st, rec)


def analyze(code, lost_slots: Sequence[int]):
    """Structure-only success test (no payloads): used by the Monte-Carlo simulator."""
    unk = bytearray(code.V)
    for v in code.always:
        unk[v] = 1
    for s in lost_slots:
        unk[code.tx[s]] = 1
    return _solve(code, unk, None)
