# Testing Prime-Ulam LDPC (for third parties)

This repository ships a small prototype so you can check the claims of the paper
(`docs/artigo_zenodo.pdf`) yourself, without trusting the authors' numbers.
Pick the path that fits you; each takes minutes.

| You want to... | Do this |
| --- | --- |
| Poke at it with no installation | Open `docs/demo/index.html` (or the GitHub Pages site, see below) |
| Run the real thing on your files | `pip install -e .` then the `primeulam` CLI (section 2) |
| Use it from your own code | the Python API (section 3) |
| Reproduce the paper's exact tables | the original scripts in `src/` (section 5) |
| Check the speed claims | the C decoder (section 6) |

## 1. What is being claimed, and how to check each claim

| Claim in the paper | Check |
| --- | --- |
| Rate 0.80; n = 40p, k = 32p | `primeulam selftest` |
| The sparse part has **no length-4 cycles** (theorem, needs p prime) | `primeulam selftest`; `pytest -k composite` shows the modulus-16 grid has 3,584 bad pairs while modulus 17 has 0 |
| The code is described by a prime + 34 integers + one 32-row table | `primeulam info`; the parameters are in `primeulam/params/*.json` |
| The formulas reproduce the released code exactly | `python3 -I src/verify/verify_article.py 37 127` and `pytest` (the export is compared byte for byte with `data/codes/code_p*.txt`) |
| p=37: 0 failures at 17.5% loss, ~2.4% at 19.5% (150,000 patterns) | `primeulam simulate --p 37 --loss 0.175 0.19 0.195 --trials 5000` (or in the browser demo). The 19.5% row converges quickly; the 17.5% and 19% rows need many patterns |
| It really recovers data, not just "success" flags | `primeulam encode` / `lose` / `decode` on a real file (section 2) |
| It does **not** reach the information-theoretic limit | try `--loss 0.20`: most patterns fail (the paper says so too) |

Honest scope, as in the paper (Section 8): only rate 0.80, only the erasure channel, binary sparse code
(no recovery guarantee at the limit, unlike Reed-Solomon / RaptorQ). The comparison with 5G NR, PEG, RS and
RaptorQ is *not* re-run by the prototype; use the scripts in `src/benchmarks/` for that (section 5).

## 2. Command line

```bash
pip install -e .            # needs Python >= 3.10 and numpy
primeulam selftest
primeulam info --p 127
primeulam simulate --p 37 --loss 0.17 0.19 0.195 --trials 2000 --seed 1

# end to end with a real file: packets are plain files, so "loss" is just deleting some
primeulam encode some_file.bin packets/ --p 37 --symbol-size 1024
primeulam lose   packets/ --loss 0.15 --seed 7      # or: rm a random 15% of packets/*.pkt yourself
primeulam decode packets/ restored.bin              # prints per-block stats and checks the SHA-256
cmp some_file.bin restored.bin
```

`decode` exits with status 2 when a block cannot be recovered and says how many data symbols were determined.
A block holds k = 32p symbols (about 1.2 MB with p = 37 and 1 KB symbols); larger files use several blocks.

## 3. Python API

```python
import numpy as np
from primeulam import PrimeUlamCode, simulate

code = PrimeUlamCode(37)                                   # or 127
data = np.random.default_rng(0).integers(0, 256, (code.K, 1024), dtype=np.uint8)
packets = code.encode(data)                                # (n, 1024)
received = np.random.default_rng(1).random(code.n) > 0.15
res = code.decode(packets, received)                       # res.ok, res.data, res.stats
assert res.ok and (res.data == data).all()

print(simulate(code, loss=0.195, trials=1000, seed=1))     # failure rate with Wilson 95% interval
```

Success criterion = the paper's: *every* symbol is recovered, i.e. the erased columns of the parity-check
matrix are linearly independent (peeling on the sparse equations first, Gaussian elimination on the residue).

## 4. Browser demo

`docs/demo/index.html` is self-contained (`primeulam.js` is a dependency-free port, cross-checked against the
Python code by `pytest tests/test_js_crosscheck.py`, which needs Node). It can be served by GitHub Pages
(Settings -> Pages -> Deploy from a branch -> `main` / `docs`; the demo is then at `/demo/`).

## 5. Reproducing the paper's tables

The original scripts are untouched; see the README ("Reproduce") and Section 10 of the paper.
`results/` has the raw logs the paper quotes.

## 6. Speed (C decoder)

```bash
gcc -O3 -march=native -o pudec src/decoder/pudec.c
./pudec data/codes/code_p37.txt 1024 200 0.10,0.15,0.17,0.19
```

Python and JavaScript are for correctness, not speed. Absolute timings depend on the machine; compare ratios.

## 7. Other primes

Only p = 37 and p = 127 have validated parameter sets (the paper built and measured only those).
For another prime p > 32 you must supply a parameter set (`PrimeUlamCode(p, params=...)`, same JSON schema as
`primeulam/params/v5_p37.json`); the steps must be distinct modulo p. The no-C4 theorem will still hold, but
nothing is claimed about the failure rate of an untuned parameter set. Results for new primes are very welcome
as test reports.

## 8. License

Everything here (code, data, paper, prototype) is released under the Apache License 2.0, see `LICENSE` and `NOTICE`: use it freely, including commercially, keeping the copyright notice. The author does not intend to file a patent (paper, Section 9). The license includes an express patent grant from contributors, but grants no rights over third-party patents, e.g. those essential to 5G NR, or over the project's names and trademarks.

## 9. Reporting

Open an issue with the **Test report** template. Disagreements with the paper are the most useful reports.
