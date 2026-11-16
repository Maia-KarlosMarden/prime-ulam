"""Construction of the Prime-Ulam LDPC code from the formulas of the paper.

Nothing here stores a parity-check matrix: ``rows``/``cols`` are *derived* from the
prime ``p`` and the small parameter set (steps, coefficients, incidence table, g, h).

Variable numbering (same as the exported files read by ``src/decoder/pudec.c``):

* ``0 .. K-1``            data symbols, variable ``i*p + j`` = arm ``i``, radius ``j``
* ``K .. K+M-1``          sparse (accumulator) parity symbols
* ``K+M .. K+M+15``       the 16 dense parity symbols

Equations (rows): ``0 .. M-1`` are the sparse equations, ``M .. M+15`` the dense ones.
Every equation says "XOR of its variables = 0".
"""
from __future__ import annotations

import json
import os
from collections import Counter
from itertools import combinations
from typing import Dict, List, Optional, Sequence

A = 32          # arms
R_DENSE = 16    # dense equations
RATE_NUM = 4    # rate 4/5 -> n = 40 p, k = 32 p

_PARAMS_DIR = os.path.join(os.path.dirname(__file__), "params")


def is_prime(x: int) -> bool:
    if x < 2:
        return False
    i = 2
    while i * i <= x:
        if x % i == 0:
            return False
        i += 1
    return True


def available_primes() -> List[int]:
    """Primes for which a validated parameter set ships with the package (37 and 127)."""
    out = []
    for name in os.listdir(_PARAMS_DIR):
        if name.startswith("v5_p") and name.endswith(".json"):
            out.append(int(name[4:-5]))
    return sorted(out)


def load_params(p: int) -> dict:
    path = os.path.join(_PARAMS_DIR, f"v5_p{p}.json")
    if not os.path.exists(path):
        raise ValueError(
            f"no bundled parameter set for p={p}. Validated primes: {available_primes()}. "
            "Pass params=... to experiment with another prime (see TESTING.md, 'Other primes')."
        )
    with open(path) as f:
        return json.load(f)


class PrimeUlamCode:
    """The final code (v5+G): sparse spiral equations + closed accumulator + 16 dense equations.

    Parameters
    ----------
    p : int
        Prime > 32. Block length is n = 40 p, k = 32 p.
    params : dict, optional
        Custom parameter set with keys ``MB, masks, punct, passos, a, b, g, h``
        (same schema as ``primeulam/params/v5_p37.json``). Defaults to the bundled one.
    """

    def __init__(self, p: int, params: Optional[dict] = None):
        if not is_prime(p) or p <= A:
            raise ValueError(f"p must be a prime > {A}, got {p}")
        D = params if params is not None else load_params(p)
        self._validate_params(p, D)
        self.p, self.D = p, D
        MB = D["MB"]
        self.K = A * p                       # data symbols
        self.M = MB * p                      # sparse parity symbols
        self.n = 40 * p                      # transmitted symbols
        self.R = self.M + R_DENSE            # equations
        self.V = self.K + self.M + R_DENSE   # variables
        self._build()

    # ------------------------------------------------------------------ parameters
    @staticmethod
    def _validate_params(p: int, D: dict) -> None:
        for key in ("MB", "masks", "punct", "passos", "a", "b", "g", "h"):
            if key not in D:
                raise ValueError(f"params is missing key '{key}'")
        MB = D["MB"]
        if len(D["masks"]) != A:
            raise ValueError(f"'masks' (incidence table) must have {A} rows")
        for k in ("passos", "a", "b"):
            if len(D[k]) != MB:
                raise ValueError(f"'{k}' must have MB={MB} entries")
        if any(c < 0 or c >= MB for m in D["masks"] for c in m):
            raise ValueError("family index out of range in 'masks'")
        steps = [s % p for s in D["passos"]]
        if len(set(steps)) != len(steps):
            raise ValueError("steps must be pairwise distinct modulo p "
                             "(the no-C4 theorem requires s_c - s_c' invertible mod p)")

    # ------------------------------------------------------------------ construction
    def sparse_equations(self) -> Dict[int, set]:
        """Section 3.2: q(i,j,c) = MB*((a_c*((j + s_c*i) mod p) + b_c) mod p) + c, for c in F_i."""
        D, p, MB = self.D, self.p, self.D["MB"]
        eq = {}
        for i in range(A):
            for j in range(p):
                eq[i * p + j] = {
                    MB * ((D["a"][c] * ((j + D["passos"][c] * i) % p) + D["b"][c]) % p) + c
                    for c in D["masks"][i]
                }
        return eq

    def _build(self) -> None:
        D, p, K, M, n = self.D, self.p, self.K, self.M, self.n
        cols: List[set] = [set() for _ in range(self.V)]
        # 1) sparse part on the data symbols
        self._sparse = self.sparse_equations()
        for v, eqs in self._sparse.items():
            cols[v] = set(eqs)
        # 2) closed accumulator chain (Section 3.3)
        for q in range(M):
            cols[K + q] = {0, M // 2, M - 1} if q == 0 else {q - 1, q}
        # 3) sparse parities that are replaced by dense ones (not transmitted)
        punct_par = [K + (q * M) // R_DENSE + M // (2 * R_DENSE) for q in range(R_DENSE)]
        # 4) dense precode (Section 3.4): Gaussian norm is a quadratic residue mod p
        qr = {(x * x) % p for x in range(1, p)}
        for k in range(R_DENSE):
            a, b = (5 * k) % p, (7 * k + 1) % p
            for i in range(A):
                for j in range(p):
                    if ((i - a) ** 2 + (j - b) ** 2) % p in qr:
                        cols[i * p + j].add(M + k)
            cols[K + M + k] = {M + k}
        # 5) variables that are never transmitted: two arms + the 16 replaced parities
        self.always = [i * p + j for i in D["punct"] for j in range(p)] + punct_par
        # 6) transmission order (Section 3.5)
        tarms = [i for i in range(A) if i not in D["punct"]]
        At, g, h = len(tarms), D["g"], D["h"]
        tx, t, q = [], 0, 0
        for x in range(n):
            if (x + 1) * M // n > x * M // n:       # parity slot (every 4th slot)
                tx.append(K + (h * q) % M)
                q += 1
            else:
                tx.append(tarms[t % At] * p + (g * t) % p)
                t += 1
        pos = {v: s for s, v in enumerate(tx)}
        for k, v in enumerate(punct_par):             # dense parity takes the punctured slot
            tx[pos[v]] = K + M + k
        self.tx = tx
        if len(set(tx)) != n:
            raise ValueError("transmission order is not a permutation (check g, h)")
        self.cols = [tuple(sorted(c)) for c in cols]
        rows: List[List[int]] = [[] for _ in range(self.R)]
        for v, cs in enumerate(self.cols):
            for r in cs:
                rows[r].append(v)
        self.rows = [tuple(r) for r in rows]
        self.slot_of = {v: s for s, v in enumerate(tx)}

    # ------------------------------------------------------------------ properties
    @property
    def rate(self) -> float:
        return self.K / self.n

    def description_size(self) -> dict:
        """Size of the description (Section 3.7): 34 integers besides p + 106 table memberships."""
        D = self.D
        ints = 3 * D["MB"] + len(D["punct"]) + 2          # s_c, a_c, b_c, 2 arms, g, h
        return {"integers_besides_p": ints,
                "incidence_memberships": sum(len(m) for m in D["masks"])}

    def sparse_c4_pairs(self) -> int:
        """Number of pairs of distinct data symbols sharing >= 2 sparse equations (theorem: 0)."""
        inv: Dict[int, List[int]] = {}
        for v, eqs in self._sparse.items():
            for e in eqs:
                inv.setdefault(e, []).append(v)
        shared: Counter = Counter()
        for vs in inv.values():
            for pair in combinations(sorted(vs), 2):
                shared[pair] += 1
        return sum(1 for c in shared.values() if c >= 2)

    def to_c_format(self) -> str:
        """Text format read by ``src/decoder/pudec.c`` (identical to data/codes/code_p*.txt)."""
        out = [f"{self.V} {self.K} {self.R} {self.n} {len(self.always)} {self.M}",
               " ".join(map(str, self.always)),
               " ".join(map(str, self.tx))]
        for cs in self.cols:
            out.append(f"{len(cs)} " + " ".join(map(str, cs)))
        return "\n".join(out) + "\n"

    def __repr__(self) -> str:
        return (f"PrimeUlamCode(p={self.p}, n={self.n}, k={self.K}, rate={self.rate:.2f}, "
                f"equations={self.R})")

    # ------------------------------------------------------------------ codec (see codec.py)
    def encode(self, data, *, stats=None):
        from .codec import encode
        return encode(self, data, stats=stats)

    def decode(self, symbols, received):
        from .codec import decode
        return decode(self, symbols, received)

    def decodable(self, lost_slots: Sequence[int]):
        """Structure-only decoding check (no payloads). Returns (ok, Stats)."""
        from .codec import analyze
        return analyze(self, lost_slots)
