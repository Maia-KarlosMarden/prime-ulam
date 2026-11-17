# Copyright 2026 Karlos Marden Maia
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0; see the LICENSE and NOTICE files.
"""Prime-Ulam LDPC: erasure codes generated from modular spirals.

Reference implementation of the construction in the paper (Sections 3.1-3.6).
Quick start::

    import numpy as np
    from primeulam import PrimeUlamCode

    code = PrimeUlamCode(37)                      # n = 1480 symbols, k = 1184, rate 0.80
    data = np.random.default_rng(0).integers(0, 256, (code.K, 1024), dtype=np.uint8)
    packets = code.encode(data)                   # (n, 1024) transmitted symbols
    received = np.random.default_rng(1).random(code.n) > 0.15   # lose ~15 %
    result = code.decode(packets, received)
    assert result.ok and (result.data == data).all()
"""
from .code import PrimeUlamCode, available_primes, is_prime
from .codec import DecodeResult, Stats
from .sim import simulate, wilson_interval

__all__ = ["PrimeUlamCode", "DecodeResult", "Stats", "available_primes",
           "is_prime", "simulate", "wilson_interval"]
__version__ = "0.1.0"
