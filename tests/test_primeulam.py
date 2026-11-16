import hashlib
import json
import os
import random

import numpy as np
import pytest

from primeulam import PrimeUlamCode, available_primes, simulate
from primeulam.cli import main

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="module", params=[37, 127])
def code(request):
    return PrimeUlamCode(request.param)


def test_dimensions_and_rate(code):
    assert code.n == 40 * code.p and code.K == 32 * code.p
    assert code.rate == pytest.approx(0.8)
    assert len(code.tx) == code.n and len(set(code.tx)) == code.n
    assert len(code.always) == 2 * code.p + 16
    assert code.description_size() == {"integers_besides_p": 34, "incidence_memberships": 106}


def test_no_length4_cycle_in_sparse_part(code):
    assert code.sparse_c4_pairs() == 0


def test_composite_modulus_breaks_theorem():
    """Paper, Sec. 3.2: m=17 has no C4 on the m x m grid, m=16 has 3,584 pairs."""
    from itertools import combinations
    from collections import Counter
    steps = [s for s in PrimeUlamCode(37).D["passos"]]

    def pairs(m):
        eqs = [{c * m + ((j + (steps[c] % m) * i) % m) for c in range(10)} for i in range(m) for j in range(m)]
        inv = {}
        for v, e in enumerate(eqs):
            for x in e:
                inv.setdefault(x, []).append(v)
        sh = Counter(pr for vs in inv.values() for pr in combinations(vs, 2))
        return sum(1 for c in sh.values() if c >= 2)

    assert pairs(17) == 0
    assert pairs(16) == 3584


def test_export_matches_released_code_files(code):
    """The formulas reproduce data/codes/code_p*.txt (the file the C decoder reads) exactly."""
    with open(os.path.join(ROOT, "data", "codes", f"code_p{code.p}.txt")) as f:
        assert code.to_c_format() == f.read()


def test_bundled_params_match_repo_copies():
    for p in available_primes():
        a = open(os.path.join(ROOT, "primeulam", "params", f"v5_p{p}.json")).read()
        b = open(os.path.join(ROOT, "src", "construction", f"v5_p{p}.json")).read()
        assert json.loads(a) == json.loads(b)


def test_codeword_satisfies_every_parity_equation():
    c = PrimeUlamCode(37)
    data = np.random.default_rng(0).integers(0, 256, (c.K, 16), dtype=np.uint8)
    pk = c.encode(data)
    full = np.zeros((c.V, 16), dtype=np.uint8)
    full[:c.K] = data
    full[np.asarray(c.tx)] = pk
    # direct check on the dense equations (all their variables are data or the dense parity itself)
    for k in range(16):
        r = c.M + k
        acc = np.zeros(16, dtype=np.uint8)
        for v in c.rows[r]:
            acc ^= full[v]
        assert not acc.any()


@pytest.mark.parametrize("loss", [0.0, 0.05, 0.10, 0.15])
def test_roundtrip_random_loss(code, loss):
    rng = np.random.default_rng(int(loss * 1000) + code.p)
    data = rng.integers(0, 256, (code.K, 24), dtype=np.uint8)
    pk = code.encode(data)
    mask = np.ones(code.n, dtype=bool)
    mask[rng.choice(code.n, round(loss * code.n), replace=False)] = False
    res = code.decode(pk, mask)
    assert res.ok and np.array_equal(res.data, data)


def test_failure_is_reported_not_raised():
    c = PrimeUlamCode(37)
    data = np.random.default_rng(1).integers(0, 256, (c.K, 8), dtype=np.uint8)
    pk = c.encode(data)
    mask = np.zeros(c.n, dtype=bool)
    mask[: c.n // 2] = True                   # 50 % loss, far above capacity
    res = c.decode(pk, mask)
    assert not res.ok and res.data is None and res.recovered_data < c.K


def test_decodable_agrees_with_payload_decoder():
    c = PrimeUlamCode(37)
    rng = random.Random(5)
    data = np.random.default_rng(2).integers(0, 256, (c.K, 8), dtype=np.uint8)
    pk = c.encode(data)
    for loss in (0.18, 0.195, 0.21):
        for _ in range(20):
            lost = rng.sample(range(c.n), round(loss * c.n))
            mask = np.ones(c.n, dtype=bool)
            mask[lost] = False
            ok, _ = c.decodable(lost)
            res = c.decode(pk, mask)
            assert ok == res.ok
            if ok:
                assert np.array_equal(res.data, data)


def test_invalid_parameters_rejected():
    with pytest.raises(ValueError):
        PrimeUlamCode(36)                       # not prime
    with pytest.raises(ValueError):
        PrimeUlamCode(31)                       # prime but <= 32
    with pytest.raises(ValueError):
        PrimeUlamCode(41)                       # prime, but no bundled parameters
    D = dict(PrimeUlamCode(37).D)
    D["passos"] = [0] * 10                      # equal steps violate the theorem's hypothesis
    with pytest.raises(ValueError):
        PrimeUlamCode(37, params=D)


@pytest.mark.slow
def test_matches_published_failure_rates_p37():
    """Paper Sec. 4.1: 0 failures at 17.5 %, ~2.4 % at 19.5 % (p = 37). Fixed seed, 600 patterns."""
    c = PrimeUlamCode(37)
    assert simulate(c, 0.175, 600, seed=1)["failures"] == 0
    r = simulate(c, 0.195, 600, seed=1)
    assert 0.010 <= r["failure_rate"] <= 0.045


def test_cli_file_roundtrip(tmp_path):
    src = tmp_path / "f.bin"
    src.write_bytes(os.urandom(200_000))
    pk = tmp_path / "pk"
    out = tmp_path / "out.bin"
    assert main(["encode", str(src), str(pk), "--p", "37", "--symbol-size", "256"]) == 0
    assert main(["lose", str(pk), "--loss", "0.15", "--seed", "9"]) == 0
    assert main(["decode", str(pk), str(out)]) == 0
    assert hashlib.sha256(out.read_bytes()).digest() == hashlib.sha256(src.read_bytes()).digest()
    assert main(["lose", str(pk), "--loss", "0.2", "--seed", "10"]) == 0
    assert main(["decode", str(pk), str(tmp_path / "bad.bin")]) == 2    # reported failure, not a crash
