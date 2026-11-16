"""Monte-Carlo erasure simulation (same protocol as src/construction/fair.py)."""
from __future__ import annotations

import math
import random
from typing import Dict


def wilson_interval(failures: int, trials: int, z: float = 1.96):
    """95 % Wilson score interval for a binomial proportion."""
    if trials == 0:
        return (0.0, 1.0)
    ph = failures / trials
    d = 1 + z * z / trials
    c = (ph + z * z / (2 * trials)) / d
    h = z * math.sqrt(ph * (1 - ph) / trials + z * z / (4 * trials * trials)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def simulate(code, loss: float, trials: int, seed: int = 1) -> Dict[str, float]:
    """Lose exactly round(loss*n) of the n transmitted symbols, uniformly at random, ``trials`` times.
    Success = every symbol (data included) is recovered, i.e. the erased columns of H are independent."""
    rng = random.Random(seed)
    e = round(loss * code.n)
    fail = peel_only = 0
    for _ in range(trials):
        lost = rng.sample(range(code.n), e)
        ok, st = code.decodable(lost)
        fail += not ok
        peel_only += ok and st.peeling_only
    lo, hi = wilson_interval(fail, trials)
    return {"loss": loss, "erased": e, "trials": trials, "failures": fail,
            "failure_rate": fail / trials, "ci_low": lo, "ci_high": hi,
            "peeling_only_rate": peel_only / trials}
