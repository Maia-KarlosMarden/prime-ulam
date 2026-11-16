# Prime-Ulam LDPC — Technical Report

November 16, 2026 · Karlos Marden Maia (Independent Researcher)

## Executive summary

Prime-Ulam LDPC is a family of erasure-correcting codes generated entirely by formula: a prime number, 34 small integers and one 32-row incidence table (106 memberships) describe a complete code, with no stored parity-check matrix. In the final version, on the erasure channel at rate 0.80, the code recovers the data with a failure rate below 1 in 150,000 at 17.5% loss, outperforms the 5G NR LDPC code in the moderate-loss regime at 1,480 symbols (and ties it up to 19% loss at 5,080 symbols), and decodes at 2.5 to 3.7 GB/s at losses up to 15%, using only XOR operations.

The idea began as a geometric question: could the Ulam spiral, which arranges the integers in a plane and reveals alignments among the prime numbers, also organize the equations of an error-correcting code? The answer the research found was more precise than the question: what matters is not the position of the primes on the spiral, but the prime as the modulus of the arithmetic that defines the connections. With that principle, the geometry came to guarantee, by construction, the absence of the short cycles that degrade any LDPC code.

This report presents the evolution of the idea, the final construction, the results measured against 5G NR, PEG, Reed–Solomon and RaptorQ, and the scientific and commercial positioning. The conclusion is balanced: Prime-Ulam does not reach the recovery guarantee of RaptorQ and Reed–Solomon, which are optimal on that metric, but it occupies a space of its own where simplicity, decoding speed at moderate loss and a compact description matter more than the last tenth of a percentage point of recovery.

## 1. The problem: recovering what was lost without asking again

In many communication and storage systems, data does not arrive corrupted: it arrives missing. A network packet is dropped, a disk sector fails, a satellite leaves line of sight for a few milliseconds. The receiver knows exactly what is missing, but not its content. This is the erasure channel, and the codes that serve it are called erasure codes.

The classical solution is to send redundancy: besides the k data blocks, m parity blocks are sent, each computed as the XOR sum of a subset of the data. If some blocks are lost, the ones that arrived form a system of linear equations over the binary field, and solving that system reconstructs what was missing. The code rate is k divided by k + m; in this work it is fixed at 0.80, that is, 20% redundancy.

The theoretical limit is simple: with m parities, it is impossible to recover more than m lost blocks. A code is good when it comes close to that limit with three properties at the same time:

1. **High recovery**, so that almost every loss pattern below the limit is resolved.
2. **Cheap decoding**, preferably by "peeling": find an equation with a single unknown, solve it, substitute and repeat, never assembling a matrix.
3. **Compact description**, so that the code fits in simple hardware and can be generated for any block size.

LDPC (sparse-matrix) codes meet the first two when the matrix is well designed. What degrades an LDPC code is short cycles: two data symbols that take part in the same two equations form a cycle of length four, and such cycles create dependencies that prevent recovery. Designing the matrix is, to a large extent, the art of avoiding these cycles. The central contribution of Prime-Ulam lies exactly there: a geometric rule that eliminates them by construction.

## 2. How the idea was born and evolved

The idea started from a known observation in number theory. When the integers are written in a spiral from the center of a grid, the primes line up along diagonals and arms, a pattern discovered by Stanislaw Ulam in 1963. The question that started the project was: if the primes are organized in the plane in a way that is so far from random and so far from regular, could that organization be used to choose which data symbols enter each parity equation?

The evolution went through five stages, each preserving what the previous one had established:

| Stage | What was done | Result |
| --- | --- | --- |
| 1. Geometry as a connection rule | Ulam-spiral coordinates define the equations | 97.4% recovery at 15% loss |
| 2. The prime as modulus | with a prime side, two spirals cross at a single point | zero 4-cycles, by theorem |
| 3. Everything by formula | 14 integers describe the code; accumulator parity | matches PEG, with no stored matrix |
| 4. Irregularity and untransmitted arms | 32 arms, 10 spiral families, closed chain | 5G NR level |
| 5. Gaussian precode | norm of Gaussian integers mod p defines the dense equations | beats 5G NR at identical rate |

Each stage preserved the previous one: the geometry became a theorem, the theorem became a formula, and the formula received irregularity and a precode.

**Stage 1 — Geometry as a connection rule.** The first matrices used the coordinates of the points on the spiral (x, y, x + y, x − y) to define the equations, with arms, antipodal pairings and radial weightings. This phase established the working thesis: the topology of the matrix, not the weights, decides performance. A single rearrangement of the antipodal pairs took recovery from 4% to 95%, while weight adjustments moved tenths of a point. Algebraic optimization of these matrices (removal of short cycles) reached 97.4% recovery at 15% loss on 320-bit blocks.

**Stage 2 — The prime as modulus.** The decisive advance came from asking why the geometry worked. The answer: when the grid has a prime side, two lines with different slopes cross in at most one point, modulo p. With side 16, the same rule produces 256 pairs of data symbols sharing two equations (length-4 cycles) in the stage-2 test; with side 17, none. (The final construction repeats the test with ten families: 3,584 pairs for side 16, none for 17.) What the Ulam spiral suggested by image, modular arithmetic guarantees by theorem. The construction became: 16 arms with p radial positions, four spiral families with distinct steps, and each equation gathers the points where radius + step × arm gives the same value modulo p.

**Stage 3 — Everything by formula.** With the algebraic rule, the matrix stopped being stored. One prime, four steps, eight coefficients for the position of the equations in the parity chain and two integers for the transmission order describe the whole code. The parity took the accumulator form (each parity enters two consecutive equations), which doubles the protection of each parity bit at no cost. This version matched the best generic design method (PEG) at all sizes, with 14 integers instead of thousands of indices.

**Stage 4 — Irregularity and untransmitted arms.** The best modern codes give different degrees to different bits: some take part in many equations, most in few. The construction was extended to 32 arms and 10 spiral families, with two high-degree arms that are not transmitted (the receiver reconstructs them) and 30 light arms of degree 3. The parity chain was closed to eliminate the loose end. With this, the code reached the 5G NR level in the 15% to 19.5% loss range.

**Stage 5 — The Gaussian precode.** The last piece was born from a new geometric idea: treat each point of the spiral as a complex number and use the product by the conjugate, which is a real number, as the connection criterion. Translated to the binary field, the idea took this form: each point (arm i, radius j) is the Gaussian integer i + j·I modulo p; for each dense equation a center is chosen, and the point enters the equation if the norm of the difference, (i − a)² + (j − b)² modulo p, is a quadratic residue. Sixteen such equations, with centers in arithmetic progression, replace sixteen sparse parities and eliminate the residual error floor, at identical rate. This was the stage that took the code past 5G NR.

## 3. The final construction

The final code, called here Prime-Ulam v5+G, is defined by a prime p greater than 32 and by a fixed set of small integers. For p = 37 the block has 1,480 transmitted symbols; for p = 127, 5,080. Any prime will do, and the same parameter set generates the whole family.

| Element | Definition | Count |
| --- | --- | --- |
| Data | 32 arms × p radial positions | k = 32p |
| Untransmitted arms | 2 arms of degree 8, reconstructed by the receiver | 2p symbols |
| Spiral families | 10 families, each with its own step s_c | 10 |
| Sparse equations | One per value of radius + s_c × arm (modulo p), per family | 10p |
| Sparse parities | Closed-chain accumulator; 16 of them untransmitted | 10p − 16 transmitted |
| Dense equations | Gaussian norm and quadratic residue, centers in arithmetic progression | 16 |
| Transmitted | 30p data + (10p − 16) sparse parities + 16 dense | n = 40p |
| Rate | k / n | 0.80 |

**Sparse part.** Arm i takes part in a subset F_i of the ten families: the two untransmitted arms take part in eight, the remaining thirty in three, distributed so that each family receives the same number of arms. The data symbol at position (i, j) enters, for each family c in F_i, the equation with index

```
q(i, j, c) = 10 · ( a_c · ((j + s_c · i) mod p) + b_c  mod p ) + c
```

where a_c and b_c are the coefficients that position the equation in the parity chain. The central guarantee follows from p being prime: two spirals of distinct families have at most one arm in common, so two data symbols never share two equations, and the matrix has no cycles of length four. This was verified numerically for p = 37 and p = 127.

**Closed accumulator parity.** Parity q enters equations q − 1 and q; parity 0 enters equations 0, M/2 and M − 1, closing the chain. Every parity is thus protected by two equations and encoding remains sequential.

**Dense precode.** Dense equation k, with center (a_k, b_k) = (5k mod p, 7k + 1 mod p), contains the data symbol (i, j) when

```
(i − a_k)² + (j − b_k)²  mod p  ∈  { x² mod p : 1 ≤ x < p }
```

Each dense equation contains about half of the data and generates a transmitted parity in place of a punctured sparse parity. It is the binary translation of the idea of the complex product by the conjugate: the norm of the Gaussian integer decides the connection.

**Transmission order.** Symbols are sent in a repeating pattern of four slots, three data and one parity; the t-th data symbol occupies arm t mod 32 and radius g·t mod p, and the q-th parity is the one with index h·q mod M. The integers g and h are chosen to maximize the length of the burst that is always recoverable.

**Decoding.** First peeling on the sparse equations; when it stalls, the remaining unknowns form a small system, solved by elimination over GF(2) with the dense equations included. Everything is XOR of packets.

**Full parameters.** The values of s_c, a_c, b_c, F_i, g and h used in the tests are in `data/codes/v5_p37.json` and `data/codes/v5_p127.json`, and the code exported for the decoder is in `data/codes/code_p37.txt` and `data/codes/code_p127.txt`. Besides p there are 34 integers (ten steps, ten coefficients a_c, ten coefficients b_c, the two untransmitted arms, g and h) plus the 32-row incidence table F_i, which is the one ingredient not given by a formula (it was found by a seeded search and is recorded as data).

## 4. Results

All numbers below come from simulation on the erasure channel, with exact decoding by rank over GF(2), the same loss patterns applied to all codes compared, and rate 0.80 throughout. "Failure" means that at least one symbol could not be reconstructed.

**Recovery at identical rate.** The table compares Prime-Ulam v5+G with the 5G NR standard LDPC code (TS 38.212, assembled from the official tables and validated against the Sionna reference encoder), at the same k and n.

| Block | Loss | Patterns | Prime-Ulam v5+G | 5G NR |
| --- | --- | --- | --- | --- |
| 1,480 symbols | 17.5% | 150,000 | 0 failures | 10 failures (6.7e-5) |
| 1,480 symbols | 19.0% | 150,000 | 19 failures (1.3e-4) | 285 failures (1.9e-3) |
| 1,480 symbols | 19.5% | 150,000 | 2.4% failures | 10.7% failures |
| 5,080 symbols | 17.5% | 15,000 | 0 failures | 0 failures |
| 5,080 symbols | 19.0% | 15,000 | 0 failures | 0 failures |
| 5,080 symbols | 19.5% | 15,000 | 0 failures | 9 failures (6.0e-4) |

The theoretical loss limit is 20%. At 19% loss with 1,480 symbols, Prime-Ulam fails 15 times less often than 5G NR; at 19.5%, 4.5 times less often.

**Error floor.** With 400,000 patterns at 15% and 17.5% loss with 1,480 symbols, the version without the precode showed a floor of about 1e-4 to 5e-4, caused by low-weight codewords formed by degree-3 data symbols. The Gaussian precode eliminated this floor: 0 failures in 150,000 at 17.5% and 0 in 100,000 at 19% and 19.5% in the version with 16 added equations. It is worth stating plainly that, without the precode, the floor of the Prime-Ulam construction is higher than that of the two reference codes: in the same 400,000-pattern measurement the failure rate is 1.35e-4 at 15% loss and 5.0e-4 at 17.5% for Prime-Ulam v5 alone, against 2.25e-5 and 9.75e-5 for 5G NR, and 5e-6 and 7.5e-6 for PEG. The precode is what brings the final code to 0 failures in 150,000 patterns at 17.5%, below the 5G NR rate measured on the same patterns (6.7e-5); the PEG floor (7.5e-6 at 17.5%) is below what 150,000 patterns can resolve, so these data do not establish that the final code beats PEG at that loss. (The final code was not run at 400,000 patterns.) Whether the geometric centers are better than random dense equations is not established: with 16 equations, random centers, the diagonal centers used in the final code and fully random dense equations all show zero failures in 100,000 patterns at 19% and 19.5%, so at this sample size the variants are indistinguishable. An earlier comparison with 8 equations favored the geometric version, but its log is not in the repository, so it is not relied on here.

**Bursts.** The transmission order designed by formula guarantees recovery of any cyclic burst of up to 285 consecutive symbols out of 1,480 (theoretical limit 296) and of up to 1,006 out of 5,080 (limit 1,016, measured on a sample of starting positions). When 5G NR and PEG are given the same send-order search, they reach equivalent values (287 and 282 at 1,480), which shows that burst robustness is a property of the interleaver, available to any good code, and not an exclusive differentiator.

**Decoding cost.** A C decoder, without explicit SIMD, with 1 KB symbols, on a virtual machine with a 2.1 GHz Xeon:

| Loss | 1,480 symbols (1.2 MB) | 5,080 symbols (4.2 MB) | XORs per data symbol |
| --- | --- | --- | --- |
| 10% | 0.33 ms (3.7 GB/s) | 1.5 ms (2.8 GB/s) | 4.7 |
| 15% | 0.46 ms (2.6 GB/s) | 1.7 ms (2.5 GB/s) | 5.2 to 5.6 |
| 17% | 0.99 ms (1.2 GB/s) | 5.4 ms (0.77 GB/s) | 15 to 19 |
| 19% | 1.43 ms (0.85 GB/s) | 13.4 ms (0.31 GB/s) | 28 to 55 |

Up to 15% loss, peeling resolves almost everything with five XORs per symbol. Near the limit, elimination over GF(2) dominates and the cost rises by an order of magnitude.

**Scalability.** Performance improves with block size: at 5,140 symbols the regular by-formula version (p = 257) already recovered 99.7% of 300 patterns at 19%, and the final version showed no failures up to 19.5% in 15,000 patterns. The cost of generating the code for a new size is changing the prime.

## 5. Positioning against established codes

Four references were measured under the same protocol: the 5G NR LDPC code, PEG (the best generic method for designing sparse matrices), Reed–Solomon and RaptorQ (RFC 6330, Rust reference library). The table summarizes what each offers.

| Criterion | Prime-Ulam v5+G | 5G NR LDPC | PEG regular | Reed–Solomon | RaptorQ |
| --- | --- | --- | --- | --- | --- |
| Recovery at 19% (1,480 symb.) | 1.3e-4 failure | 1.9e-3 | 5.7e-2 | 0 (optimal) | ~0 (1/256 per overhead symbol) |
| Recovery at the exact limit (20%) | fails | fails | fails | 100% | 99.5% |
| Decoding up to 15% loss | 2.5 to 3.7 GB/s, XOR only | similar, XOR only | similar | GF(256) arithmetic, slower | ~1 GB/s native, published |
| Decoding at 19% loss | 0.3 to 0.85 GB/s | slower than Prime-Ulam | similar | same as at 15% | ~1 GB/s, independent of loss |
| Code description | one prime + 34 integers + one 32-row table | standardized tables | stored matrix | one generator polynomial | tables + pseudo-random generator |
| Block sizes | 40p, p prime | 51 values of Z, two base graphs | any | up to 255 symbols in GF(256) | any k |
| Rate | fixed 0.80 (generalizable) | adjustable by puncturing | fixed | adjustable | rateless (generates symbols on demand) |
| 4-cycles | zero, by theorem | zero, by design | zero, by algorithm | not applicable | not applicable |
| Hardware | XOR and a small linear system | XOR; ASICs available | XOR | finite-field multipliers | XOR + GF(256) in the dense part |
| Intellectual property | open, known constructions | 3GPP standard, essential patents | open | open | Qualcomm patents involved |

**Scientific reading.** In pure recovery, Reed–Solomon and RaptorQ are optimal or nearly so: they recover any pattern up to the theoretical limit. No binary LDPC code, including Prime-Ulam and 5G NR, reaches that, because sparse equations over the binary field admit dependencies that a larger field avoids. Within the class of binary LDPC codes, Prime-Ulam v5+G is the best of the three measured, with a margin of 4 to 15 times over 5G NR near the limit.

**Commercial reading.** The code with the lowest failure rate is not necessarily the most widely adopted. The 5G NR LDPC code is the most widely used in the world not because it is the best on the erasure channel, but because it was standardized, has dedicated hardware, was optimized for noisy channels (its real use) and offers guaranteed interoperability. RaptorQ dominates file distribution and streaming because it is rateless and has a recovery guarantee, despite licensing. Reed–Solomon dominates storage because it is optimal and old enough to be free of patents.

In this picture, Prime-Ulam positions itself through the properties that the other three do not combine at once:

- **Description by formula.** No tables, no matrices; the code for a new block is a new prime. This matters on devices without memory for tables and in systems that need block sizes outside the standards.
- **XOR decoding with dominant peeling.** At losses up to 15%, five XORs per symbol suffice. Simple processors, without a finite-field multiplier, decode at memory speed.
- **Guarantees by theorem.** The absence of 4-cycles is provable, not checked case by case. This simplifies certification and analysis.
- **No known licensing.** The constructions used have been in the public domain for decades.

**Pros and cons, in short.** Prime-Ulam beats 5G NR in recovery and in simplicity of description; it loses to it in ecosystem, ready-made hardware and rate flexibility. It beats RaptorQ in speed at low loss and in the absence of a license; it loses to it in recovery guarantee, in flexibility (fixed rate versus rateless) and in speed near the limit. It beats Reed–Solomon in decoding cost and block size; it loses in recovery guarantee.

## 6. Originality: what is known and what is new

Honesty on this point is what gives credibility to the rest of the report. Every piece of the construction has a relative in the literature, and the technical reader will recognize them.

| Prime-Ulam piece | Relative in the literature | What Prime-Ulam adds |
| --- | --- | --- |
| Spirals modulo p without 4-cycles | Array codes (Fan, 2000); finite-geometry LDPC (Kou, Lin, Fossorier, 2001) | Geometric derivation from the Ulam spiral; integration with the other pieces |
| Parity accumulator | IRA codes (Jin, Khandekar, McEliece, 2000) | Closed chain and placement by affine formula |
| Irregular degrees and untransmitted bits | Irregular LDPC (Luby et al., 1998); 5G NR | Irregularity per arm, described by formula |
| Dense precode | HDPC of RaptorQ (RFC 6330) | Dense equations by Gaussian norm and quadratic residue (Paley construction), instead of GF(256) |
| Interleaver by formula | Affine and QPP interleavers | Joint choice with the code geometry |

None of these pieces is new. What is original is the synthesis: a single geometric object, the plane of integers modulo a prime viewed as a spiral, generates all the pieces at once. The spirals give the sparse part, affine arithmetic positions the equations in the chain, the Gaussian norm gives the dense part, and the geometric progression gives the transmission order. In existing codes, these pieces come from different sources and are tuned separately; here they are functions of the same prime.

Three contributions deserve to be named:

1. **The Gaussian precode.** Using the norm of Gaussian integers modulo p with the quadratic-residue criterion to define the dense equations of an erasure code is, as far as this research could reach, an undocumented combination. It was born from a geometric intuition (the product by the conjugate as a real coefficient) and, in the tests, was indistinguishable from random dense equations at the sample sizes used (Section 4).
2. **The methodological trajectory.** The project started from a hypothesis about the primes, tested it against random controls, identified the real mechanism (the prime as modulus) and rebuilt the code from it. This path, documented with code and data, has didactic value of its own.
3. **The rigorous comparison.** Few independent works compare a new construction with 5G NR validated against a reference implementation, with PEG, with real RaptorQ and with Reed–Solomon, at identical rate and with the same loss patterns. The protocol is reproducible and is part of the contribution.

In terms of creativity, the merit lies in having reached a competitive construction by a path that is not the literature's: the literature starts from algebra and arrives at the code; this project started from an image, the spiral, and discovered the algebra behind it.

## 7. Application niches

The Prime-Ulam profile is clear: predictable and moderate losses (up to about 15%), a modest processor, little memory, block sizes outside the standards and a need for open code. Where the loss approaches the limit or an absolute recovery guarantee is mandatory, RaptorQ and Reed–Solomon remain the right choice. The table ranks the niches from most to least promising.

| Niche | Why Prime-Ulam fits | Typical loss | Competitor to beat | Fit |
| --- | --- | --- | --- | --- |
| Small satellites (CubeSats, LEO) and ground–satellite links | Weak, radiation-tolerant on-board processors; a code by formula fits in a small FPGA; losses from blockage and scintillation are moderate | 5% to 15% | CCSDS (Reed–Solomon, standardized LDPC), RaptorQ in DVB | High |
| Free-space optical and inter-satellite links | Burst losses from turbulence; interleaver by formula with no table memory; fast decoding at high rate | 5% to 15% | Reed–Solomon, DVB-S2 LDPC | High |
| IoT and sensor networks (LoRa, mesh networks, industrial) | Microcontrollers without a finite-field multiplier; pure XOR; small blocks generated by the prime | 5% to 15% | Lightweight Reed–Solomon, repetition | High |
| Distributed and edge storage with heterogeneous nodes | Reconstruction by XOR is cheap on weak nodes; blocks of any size; no license | 5% to 10% | Reed–Solomon (Ceph, HDFS), local repair codes | Medium to high |
| Video and data transport over UDP in private networks | Moderate, predictable packet loss; decoding at 2.5 GB/s on a common CPU; no royalties | 1% to 10% | RaptorQ, FlexFEC (RTP) | Medium |
| Embedded and automotive devices | Guarantees by theorem ease certification; auditable description in a few lines | low | Reed–Solomon, CRC with retransmission | Medium |
| Research and teaching | Complete code in one formula; each property has a short proof; reproducible comparison protocol | any | none | High |
| Cellular telephony and Wi-Fi | Closed standards with dedicated hardware; noisy channel, not erasure | not applicable | 5G NR, 802.11 | Low |
| Mass file distribution and broadcast | Requires rateless and a guarantee close to 100% | up to the limit | RaptorQ | Low |

**The low-Earth-orbit satellite case.** This is the niche where all the advantages add up. A CubeSat has a processor of a few tens of MHz, memory of hundreds of kilobytes and severe energy constraints. Prime-Ulam fits this profile: the whole code is generated from a prime, decoding at losses up to 15% is only XOR, and the transmission order by formula protects against bursts of hundreds of symbols with no interleaving table. The competitor is the well-established CCSDS standard; the way in is small university and commercial missions that are not tied to it.

**The IoT case.** A 32-bit microcontroller decodes a block of 1,480 symbols of 32 bytes at 15% loss with about 8,000 XORs of 32 bytes, on the order of a millisecond. No table needs to be in flash. For sensor networks that send telemetry in small packets over lossy links, this replaces retransmissions, which cost energy.

**The edge storage case.** On weak storage nodes (gateways, cameras, industrial equipment), reconstructing a lost block by XOR is much cheaper than by GF(256) arithmetic. Prime-Ulam allows blocks of any size (the prime is enough) and comes with no license. The drawback is the fixed rate of 0.80; generalizing the rate is future work.

## 8. Limitations and future work

The limitations below delimit what the results support. None of them invalidates the conclusions; all of them indicate what is missing for a product or a revised publication.

**Of the code**

- **Single rate.** Only rate 0.80 was built and measured. The structure admits other rates (more spiral families, more arms), but this was not done.
- **Discrete lengths.** The block has 40p symbols with p prime. Intermediate sizes require shortening, which was not tested.
- **No absolute guarantee.** At 19% loss with 1,480 symbols there is still a 1.3e-4 failure rate; RaptorQ and Reed–Solomon do not fail there.
- **Cost near the limit.** Above 17% loss, elimination over GF(2) dominates and the decoder becomes 3 to 10 times slower.
- **Erasure channel only.** Nothing was measured on a noisy channel (belief-propagation decoding), which is the main use of 5G NR.

**Of the measurement**

- **Samples.** Failure rates below 1e-5 were not measured; "0 failures in 150,000" means less than about 2e-5 with 95% confidence.
- **Decoder.** The C decoder is a direct implementation, without SIMD or inactivation. RaptorQ was measured through the Python interface, which is slower than the native library; the timing comparison uses the library's published numbers as a reference.
- **Bursts.** The guarantee at 5,080 symbols was measured on a sample of starting positions, not on all of them.
- **Parameters.** Coefficients, centers and punctured parities were chosen by short random search; there is no proof that they are optimal.

**Future work, in order of value**

1. A family of rates (0.50 to 0.95) by the same formula, with measurements at each.
2. A decoder with inactivation and SIMD, to close the timing gap near the limit.
3. A formal proof of the minimum distance of the sparse part and of the effect of the Gaussian precode.
4. An implementation on a small FPGA and measurement of energy per symbol, aimed at the satellite niche.
5. Comparison with the CCSDS standard and with local repair codes used in storage.

## 9. Scope and release

The author does not intend to file a patent. The construction, the code, the data and this report are released under CC0 1.0 Universal (public-domain dedication), so that the method is public, documented and reproducible. Publication also serves as prior art: a public, dated description of the construction makes it harder for others to obtain a patent on the same construction later. CC0 neither grants nor removes patent rights; the statement that no patent will be filed is a declaration of intent, not a license. No legal analysis of patentability is given or implied.

The reasoning behind the decision, in short:

- Every piece of the construction has a relative published more than twenty years ago (Section 6), so a broad patent is unlikely to survive examination, and a competitor could work around a synthesis patent by swapping one piece.
- The erasure-code market is dominated by open standards and public-domain codes. RaptorQ prevailed despite its patents because it is rateless and nearly optimal, properties Prime-Ulam does not have, so royalties are improbable.
- The most realistic return is indirect: technical credibility, citations and consulting in error correction for satellites and IoT.

**What the repository contains.** Formula-based generation code, the C decoder, scripts for all benchmarks with fixed seeds, the exported codes, the raw results, the paper and this report, plus a prototype (Python package, command-line tool and in-browser demo) so that third parties can test the claims themselves; see `TESTING.md`.

## Appendix: experimental protocol and reproducibility

All experiments use plain Python 3 (plus numpy and openpyxl for generation) and a C decoder compiled with gcc -O3. Seeds are fixed in all scripts; the same erasure patterns are applied to all codes in a comparison. The success criterion is full recovery of all symbols, verified by the rank of the erased submatrix over GF(2).

| Script | What it does | Input | Main output |
| --- | --- | --- | --- |
| pu3.py | Regular construction by formula (stage 3) and parameter search | prime p | res_p.json |
| v5.py | Irregular construction with untransmitted arms and closed chain (stage 4); comparison with 5G and PEG | prime p, v5_design.json | v5_p37.json, v5_p127.json |
| fair.py | Gaussian precode with punctured parities, at identical rate (stage 5) | v5_p*.json, 5G tables | failures and peeling per loss fraction |
| gauss_dense.py | Gaussian versus random dense equations | v5_p*.json | failures per variant |
| floor.py | Error floor with large samples and Wilson interval | code and fractions | floor_p_c.json |
| burst_eq.py | Bursts with the same send-order search for the three codes | v5_p*.json | burst_eq_p.json |
| compare.py | Assembly of 5G NR (TS 38.212) and PEG; decoding by rank and by peeling | tables 5G_bg1.csv, 5G_bg2.csv | cmp_p.json |
| validate5g.py | Validation of the 5G assembly against the Sionna 2.2.0 encoder | same | matrix and encoding checked in six cases |
| export_code.py, pudec.c | Exports the final code and decodes it in C with timing | fair.py | code_p37.txt, code_p127.txt, timings |
| rq_bench.py, rq_time.py | RaptorQ recovery and timing (raptorq 2.0.0 library) | k, n, symbol size | rates and timings |

**External references used.** 5G NR base-graph tables and reference encoder: Sionna 2.2.0 package (NVIDIA). RaptorQ: raptorq 2.0.0 library (Rust implementation of RFC 6330, with Python binding); the native performance figures quoted are those published on the library's page for a Ryzen 9 9950X3D with 1,280-byte symbols.

**Measurement machine.** Virtual machine with an Intel Xeon at 2.1 GHz, 2 vCPUs; XOR of 1 KB packets at 11 GB/s, measured. Absolute times vary with the machine; the ratios between codes measured on the same machine are what should be compared.

**Sample sizes.** 1,480 symbols: 150,000 to 400,000 patterns per condition in the floor measurements, 10,000 to 20,000 in the others. 5,080 symbols: 15,000 to 40,000 on the floor, 300 to 2,000 in the others. Bursts: all 1,480 starting positions on the small block, 150 to 300 sampled starting positions on the large one. Timing: 100 to 200 decodings per condition.
