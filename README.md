# Prime-Ulam LDPC

A family of erasure-correcting codes generated entirely by formula: one prime number, 34 small integers and one 32-row incidence table describe a complete code, with no stored parity-check matrix. The construction started from the geometry of the Ulam spiral and evolved into an algebraic structure modulo a prime, with zero length-4 cycles guaranteed by theorem.

**Status (November 2026):** final construction (v5+G) defined and measured against 5G NR, PEG, Reed–Solomon and RaptorQ. Intellectual-property decision made: no patent filing, released under CC0 1.0 (see [License](#license)). Full report in [`docs/technical_report.md`](docs/technical_report.md); paper in [`docs/artigo_zenodo.pdf`](docs/artigo_zenodo.pdf).

## Result in one table (rate 0.80, erasure channel)

| Criterion | Prime-Ulam v5+G | 5G NR LDPC | RaptorQ |
| --- | --- | --- | --- |
| Failure at 19% loss, 1,480-symbol block | 1.3e-4 | 1.9e-3 | ~0 |
| Failure at 17.5% loss, 150,000 patterns | 0 | 10 | not measured |
| Decoding up to 15% loss (1 KB symbols) | 2.5 to 3.7 GB/s, XOR only | similar | ~1 GB/s native, published |
| Decoding at 19% loss | 0.3 to 0.85 GB/s | slower | ~1 GB/s |
| Code description | one prime + 34 integers + one 32-row table | standardized tables | tables + generator |
| Recovery at the exact limit (20%) | fails | fails | 99.5% |

Prime-Ulam beats 5G NR in recovery and simplicity; it loses to RaptorQ and Reed–Solomon in recovery guarantee near the limit. The niche is moderate loss (up to ~15%), modest processors and block sizes outside the standards: small satellites, IoT, edge storage.

## The construction in five lines

- **Data:** 32 arms × p radial positions (p prime > 32); 2 arms are not transmitted.
- **Sparse equations:** 10 spiral families; data symbol (i, j) enters equation `10·((a_c·((j + s_c·i) mod p) + b_c) mod p) + c` for each family c of its arm. Zero 4-cycles because p is prime.
- **Parity:** closed-chain accumulator; 16 sparse parities are not transmitted.
- **Dense precode:** 16 equations; data symbol (i, j) enters equation k if `(i − a_k)² + (j − b_k)² mod p` is a quadratic residue (norm of a Gaussian integer).
- **Transmission:** n = 40p symbols, rate 0.80, order given by two integers g and h.

## Repository layout

```
primeulam/   Python package of the prototype (construction, encoder, decoder, CLI)
docs/demo/   in-browser demo (HTML + JavaScript, no dependencies)
tests/       tests (pytest) and Python x JavaScript cross-check
docs/        technical_report.md (+ .pdf), artigo_zenodo (paper, .md + .pdf),
             briefing_november_2026.md (starting point)
src/
  construction/  pu3.py (regular v3), v4.py, v5.py (irregular), fair.py (v5+G, final construction), gauss_dense.py
  benchmarks/    compare.py (5G NR + PEG), validate5g.py (against Sionna), floor.py, burst_eq.py,
                 cost_ops.py, rq_bench.py, rq_time.py (RaptorQ), diag.py, dense16.py, v6.py
  decoder/       pudec.c (C decoder), export_code.py, xorbw.c
  early/         first generation (stored 64×256 matrices): sim.py, test16.py, ctrl.py, improve.py
data/
  codes/     parameters of each version (v5_p37.json, v5_p127.json, ...) and exported codes (code_p37.txt, code_p127.txt)
  5g/        5G NR base graphs (TS 38.212), extracted from the Sionna package
  matrices/  first-generation matrices (xlsx, English README sheet)
results/     raw outputs (json and log) of all experiments cited in the report
```

## Quick test for third parties (prototype)

Besides the original scripts, the repository ships a prototype for anyone who wants to test the model without reading the old code:

- **In the browser, nothing to install:** open `docs/demo/index.html` (or publish `docs/` on GitHub Pages). It simulates losses, shows the decoder at work and reproduces the failure rate of the paper.
- **Command line (Python):** `pip install -e .`, then `primeulam selftest`, `primeulam simulate --p 37 --loss 0.175 0.195`, or the full cycle with a real file: `primeulam encode` → `primeulam lose` → `primeulam decode`.
- **Python API:** `from primeulam import PrimeUlamCode` (real encoder and decoder, XOR only).
- **Automated tests and CI:** `pytest` checks the rate, absence of 4-cycles, byte-for-byte equality with `data/codes/`, data round trips and the published failure rate.

The full guide, with "what the paper claims → how to check it", is in [`TESTING.md`](TESTING.md). Test reports (including those that disagree with the paper) go in as issues using the *Test report* template.

## Reproduce

Requirements: Python 3.10+, `numpy`, `openpyxl`; optional `sionna` (5G validation) and `raptorq` (RaptorQ benchmark); gcc for the decoder.

```bash
pip install numpy openpyxl            # base
pip install sionna raptorq            # optional

# independent check: rebuilds the code from the formulas of the paper and compares with data/codes/
python3 -I src/verify/verify_article.py 37 127

# final construction at identical rate, p = 37, 2,000 patterns
python3 -I src/construction/fair.py src/construction data/5g 37 2000 0.175,0.19,0.195

# error floor (code 0 = Prime-Ulam, 1 = 5G NR, 2 = PEG)
python3 -I src/benchmarks/floor.py src/construction data/5g 37 20000 0.15,0.175 0

# C decoder: time and XORs per symbol
gcc -O3 -march=native -o pudec src/decoder/pudec.c
./pudec data/codes/code_p37.txt 1024 200 0.10,0.15,0.17,0.19

# validate the 5G NR assembly against Sionna
python3 -I src/benchmarks/validate5g.py
```

The scripts take as first argument the construction folder (`src/construction`, which holds copies of the parameter JSON files) and as second the folder of the 5G tables (`data/5g`). All seeds are fixed. The three commands above were verified from the repository root.

Note: code comments and console output of the research scripts in `src/` (and the raw logs in `results/`) are in Portuguese; the documentation is in English.

## License

Code, data, report and paper are dedicated to the public domain under [CC0 1.0 Universal](LICENSE), a single license for everything (the same as the paper, `pyproject.toml` and the prototype). No copyright is reserved; use is free, including commercial use.

Two clarifications: (1) CC0 neither grants nor removes patent rights: the author declares that the author **does not intend to file a patent** (paper, section 9), and the dated publication also serves as prior art; (2) the license grants no rights over trademarks or third-party patents (for example, those essential to 5G NR cited in the comparison).
