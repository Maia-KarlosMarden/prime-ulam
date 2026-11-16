# **Technical Briefing — Prime-Ulam LDPC**

Evolution of the geometric architecture for reconstructing erased bits | November 2026

*This is the starting-point briefing of the project; the final construction is described in [`technical_report.md`](technical_report.md) and in the paper.*

## **Executive summary**

Our project investigates a new family of erasure-correcting codes based on **connection geometry, Ulam Spiral arms, antipodal pairings and radial weightings**.

The goal is to develop a matrix of linear equations capable of reconstructing lost data with efficiency comparable or superior to that of conventional LDPC codes, while preserving low redundancy and computational complexity.

So far, the experiments have produced three relevant findings:

1. **Geometry matters for constructing the matrix**, but we have not shown that the geometry of the prime numbers is intrinsically superior to controlled randomness.
2. **Antipodal interleaving with shifts between layers** was one of the most competitive constructions, reaching 94.93% full recovery with 15% random erasures in one of the experiments.
3. **Excessively rigid geometric constraints can destroy performance**, as happened when we required the same distribution of arms in every equation.

Our main research hypothesis has evolved. We no longer simply look to reproduce patterns of the primes: we seek to discover whether **multiscale geometries can organize the independence of the equations more efficiently than conventional constructions**.

The available evidence does not yet allow us to claim superiority over modern LDPC codes.

## **1. The mathematical challenge**

The system uses the following experimental configuration:

| **256** | **64** | **320** | **0.80** |
| --- | --- | --- | --- |
| Original bits | Parity bits | Transmitted bits | Code rate |

We built 64 XOR equations, each involving 16 information bits. Each bit takes part in four equations.

The full parity-check matrix is:

\\[ H\_{\mathrm{full}}=[H\mid I\_{64}] \\]

If a set \\(E\\) of transmitted bits is erased, full recovery is possible when:

\\[ \boxed{\operatorname{rank}(H\_{\mathrm{full},E})=|E|} \\]

Our challenge is to construct \\(H\\) so as to maximize the frequency of this condition, especially when losses occur in bursts.

**A fundamental distinction:** our tests mainly measured full recovery of the 320 transmitted bits, not only of the 256 original bits. Recovering only the data may be possible even when some erased parity remains undetermined.

With 20% erasures, we lose 64 symbols — exactly the number of independent equations available. The system therefore operates close to the algebraic limit and becomes very sensitive to dependencies among columns.

## **2. Historical evolution of the architectures**

1. **Original Prime-Ulam — Geometry of the prime numbers**

   The first matrices used alignments associated with the coordinates of the primes on the Ulam Spiral: \\(x\\), \\(y\\), \\(x+y\\) and \\(x-y\\).

   The initial hypothesis was that the distribution of the primes could provide a natural organization of the XOR equations. The first results were competitive with random regular controls, without showing consistent superiority.
2. **Interconnections between arms**

   We began connecting bits from different angular sectors, seeking to spread the dependencies across distant regions.

   The inter-arm construction improved recovery under 15% bursts relative to the diagonal one, but remained below the random control.
3. **Multigeometric arms**

   We introduced closed, intermediate, open and hybrid arms, without requiring all positions to be prime numbers.

   Mixing curvatures outperformed the isolated geometries, but some constructions concentrated the connections excessively and generated many short cycles.
4. **Antipodes and interleaved connections**

   We introduced the rule of connecting the first bit of an arm to the last bit of the opposite arm.

   The fixed inversion generated excessive dependencies. Adding shifts between layers restored performance and made the architecture competitive.
5. **Radial weightings and the W function**

   We investigated weights proportional to \\(R\\), \\(R^2\\), \\(R^{-1}\\), \\(\Delta R\\), \\(\Delta R^{-1}\\) and \\(\Delta R^{-2}\\), as well as combinations of coefficients.

   The results indicated differences between weightings, but without a robust and reproducible advantage.
6. **Inverted antipode with mandatory constraints**

   In the most recent generation, the rigid requirement of two bits per arm in each equation caused a sharp increase in short cycles and a marked drop in recovery.

   This experience identified a design constraint that we should abandon, preserving only the useful geometric properties.

## **3. The best results achieved**

The table gathers the most relevant results reported throughout the research.

| Generation                                  | Random recovery, 15% | Burst recovery, 15% |
| ------------------------------------------- | -------------------- | ------------------- |
| Original diagonal Ulam                      | 96.81%               | 90.14%              |
| Inter-arm Ulam                              | 96.25%               | 92.50%              |
| Hybrid multigeometric                       | 71.00%               | 32.20%              |
| Optimized antipode                          | 97.22%               | 93.61%              |
| Optimized mixed                             | **97.83%**           | 89.08%              |
| Original mixed                              | 96.92%               | **93.25%**          |
| Interleaved inverted antipode               | 94.93%               | 91.80%              |
| Weighting by ΔR                             | 96.08%               | 87.75%              |
| Optimized random LDPC, antipode generation  | 96.94%               | **95.14%**          |

Values from earlier experiments, with different seeds, constructions, samples and procedures. The table documents the evolution but is not a statistical ranking among all the architectures.

*Recovery milestones in selected experiments (random vs. bursts; Diagonal, Inter-arm, Optimized antipode, Optimized mixed, Optimized LDPC). Illustrative historical comparison, not controlled across generations. The chart of the original briefing is not reproduced here.*

### **What can we conclude from these numbers?**

The optimized mixed architecture reached the highest reported rate among the selected geometric constructions for 15% random erasures: 97.83%.

In bursts, the optimized antipode reached 93.61%, but the optimized LDPC control from the same experiment reached 95.14%.

The most instructive result may be that of the inverted antipode: the fixed version recovered only 4.13% of cases with 15% random losses, while the interleaved version reached 94.93%. The change in how the pairs are organized produced a much larger improvement than the later weight adjustments.

This points to a priority: **first build a topology without harmful dependencies; then optimize the geometry and the coefficients**.

## **4. Proposed pipeline to rival classical codes**

1. Data and geometry

   256 bits → positions on the spiral → arms, angles and radii

2. Connection types
   - **2A. Local:** neighborhood and curvature
   - **2B. Intermediate:** connections between sectors
   - **2C. Antipodal:** interleaved radial inversion

3. Building the matrix H

   64 × 256 | 16 connections per row | 4 per column

4. Algebraic and geometric optimization

   Rank deficiency + short cycles + radial diversity + antipodal fidelity

5. Encoding and transmission

   256 data + 64 XOR parities = 320 bits

6. Channel with erasures

   Random, consecutive and clustered losses

7. Decoding

   Peeling → GF(2) elimination → bit reconstruction

8. Independent benchmark

   Recovery rate, latency, memory, cycles and confidence intervals

The intended differentiator is not in the XOR operation — which is conventional — but in the **algorithm that determines which bits should take part in each equation**.

## **5. The evolution of the optimization function**

Our most recent radial formulation is:

\\[ W\_{ij}= \alpha\Delta R+ \beta(\Delta R)^2+ \frac{\gamma}{\Delta R+\varepsilon}+ \frac{\delta}{(\Delta R+\varepsilon)^2} \\]

However, the tests showed that maximizing a geometric preference in isolation does not guarantee good recovery.

I therefore recommend that the main objective function be:

\\[ \boxed{ J(H)= \lambda_D\mathbb E[D_E] +\lambda_C C_4(H) +\lambda_G G(H) } \\]

Where:

- \\(D_E=|E|-\operatorname{rank}(H\_{\mathrm{full},E})\\) measures rank deficiency on erasure patterns.
- \\(C_4(H)\\) penalizes cycles of length four.
- \\(G(H)\\) penalizes deviations from the desired geometric properties, without imposing a rigid distribution per arm.

The function \\(W\\) should serve as a mechanism for proposing connections, while \\(J\\) decides which proposals are really advantageous.

This separation lets the geometry take part in the construction without overriding the mathematical goal of reconstruction.

## **6. How to compete with classical codes**

So far, we have mainly used random regular LDPC matrices as the control. This is necessary but insufficient to demonstrate competitiveness with the state of the art.

| Reference                | What we need to compare                                              |
| ------------------------ | -------------------------------------------------------------------- |
| Random regular LDPC      | Benefit of geometry versus randomness                                |
| PEG-optimized LDPC       | Ability to avoid short cycles                                        |
| QC-LDPC                  | Structural regularity, memory and efficiency                         |
| Irregular LDPC           | Benefit of non-uniform degree distributions                          |
| Reed–Solomon             | Erasure recovery in symbols, with equivalent redundancy              |
| Raptor/RaptorQ           | Efficiency and recovery on erasure channels                          |

The comparisons must use equivalent code rate, block size, channel model and success criteria.

It is not enough to beat a random matrix. To rival modern codes, we will need to demonstrate advantages in **recovery rate, computational cost or burst robustness**.

## **7. Priority improvements**

**Priority 1 — Flexible interleaved antipode**

Preserve the inverted radial pairing, but allow the number of antipodal pairs to vary between equations. Avoid repetitions between layers.

**Priority 2 — Direct rank optimization**

Use erasure sets during training and minimize the mean deficiency of the submatrices. Reserve other sets for independent validation.

**Priority 3 — Optimize W and the antipodal proportion**

Jointly search \\(\alpha,\beta,\gamma,\delta\\), the regularization \\(\varepsilon\\), the shifts between layers and the fraction of opposite connections.

**Priority 4 — Optimize the layout of the transmitted bits**

Burst resistance also depends on the order of the 320 bits on the channel. We should compare original, shuffled and interleaved layouts, without confusing placement improvements with code improvements.

**Priority 5 — Rigorous statistical benchmark**

Use at least 20 independent matrices in the next stage, thousands of erasure patterns per condition and confidence intervals. Increase the samples according to the observed variability.

## **8. Development roadmap**

| Phase                | Deliverable                    | Criterion to advance                                   |
| -------------------- | ------------------------------ | ------------------------------------------------------ |
| I — Construction     | Flexible antipode generator    | Exact regularity and no duplicate connections          |
| II — Optimization    | Search for W and shifts        | Reduction of rank deficiency in validation             |
| III — Decoding       | Peeling + GF(2)                | Correct recovery and latency measurement               |
| IV — Benchmark       | Comparison with optimized LDPC | Reproducible gains under equivalent conditions         |
| V — Scalability      | Blocks of 1,024 and 4,096 bits | Sustainable performance and computational cost         |
| VI — Publication     | Code, data and technical paper | Fully reproducible results                             |

## **9. The strategic decision**

Our trajectory revealed an important change of approach.

**Initial conception:** find an advantage in the distribution of the prime numbers.

**Evolution:** explore the geometry of the spiral and the diversity of arms.

**Current conception:** design sparse matrices by means of interleaved antipodal connections, radial weightings and algebraic optimization.

The central scientific hypothesis can be expressed as follows:

> A sparse topology that combines local, intermediate and radially interleaved antipodal connections can reduce harmful dependencies between equations and increase the capacity to reconstruct data, compared with codes of the same redundancy and complexity.

This is a testable hypothesis, not a conclusion already demonstrated.

**My recommendation is to concentrate the next phase on a single candidate architecture: Flexible PAI-W**, combining inverted antipodes, variable shifts, non-uniform distribution of arms and direct optimization of rank deficiency.

If this architecture consistently outperforms an optimized LDPC code under the same protocol, we will have a substantial scientific result. If it does not, we can still identify which geometric properties are useful and which introduce undesirable algebraic redundancies.

The goal ceases to be proving that the Ulam Spiral is superior and becomes **discovering whether a structured and optimized geometry can offer measurable advantages over classical codes**.

Methodological note: this briefing consolidates the results reported in the earlier stages of the conversation. It is not an independent audit of the test files or the simulation code. Before a scientific publication, it will be necessary to reproduce the benchmarks from the matrices, seeds, algorithms and raw data.
