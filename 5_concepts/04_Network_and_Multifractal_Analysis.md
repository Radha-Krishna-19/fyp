# Network and Spectrum

**Influential nodes, the Laplacian, and the multifractal spectrum**

> The theory behind the extension: how the periodic block graph is built, why influence is undefined in a perfect crystal, what the multifractal spectrum measures, and exactly how far the zirconium-family claim can honestly be taken.

*Part of the MOF Building-Block Analysis final year project — see the [main README](../README.md).*

---

## 1 · The brief


The extension to the project was set as: **highlight the influential nodes, find the spectrum, and deduce something like "all zirconium-based MOFs fall under this spectrum"**.


That is three separate tasks, and each one turned out to have a specific technical obstacle that had to be cleared before it could be answered. This document covers the theory behind all three, what was found, and — for the third — exactly what was and was not established.

| The brief | The obstacle | The outcome |
|---|---|---|
| Highlight influential nodes | The graph must be periodic, or the degrees are wrong | Done — and the answer is more interesting than expected |
| Find the spectrum | The original computation ran on a graph with zero edges | Fixed; the spectrum is now defined for every structure |
| Deduce a family band | One Zr structure cannot establish a family claim | Mechanism demonstrated; the claim itself needs more data |


---


## 2 · The periodic block graph


Everything in this document is computed on a graph whose **vertices are building blocks** and whose **edges are the connections between them**. Building that graph correctly is not optional detail — it is where the analysis is most easily invalidated.


### 2.1 · The labelled quotient graph


A crystal is infinite, so its block graph is infinite too. The standard finite representation is the **labelled quotient graph**: one vertex per block in the unit cell, and each edge labelled with the lattice translation it crosses.


```
edge = (block_A, block_B, t)        # t = (tx, ty, tz), integer translation

# t = (0, 0, 0)   both blocks are in the same unit cell
# t = (1, 0, 0)   block B is in the cell one step along a
# t = (0,-1, 1)   and so on
```
*The translation label is what makes a finite graph represent an infinite crystal exactly.*


Two blocks can be connected by several edges with *different* translation labels, and those are genuinely different connections in the material. Discard the labels and they collapse into one, which is precisely how coordination numbers come out too low.


> **The measurement that proves this matters**
>
> UiO-66's Zr₆ cluster is 12-connected — this is published and not in dispute.
>
> Built as a labelled quotient graph: **12**. Built without translation labels: **6**. Exactly half the connections vanish, and the reported structure is not UiO-66.


### 2.2 · Validation against published crystallography


The graph construction is checked against known answers before anything is computed on it. All four structures pass:

| Structure | Node coordination | Linker coordination | Published | Net | Result |
|---|---|---|---|---|---|
| HKUST-1 | 4 | 3 | (4, 3) | tbo | PASS |
| MOF-5 | 6 | 2 | (6, 2) | pcu | PASS |
| ZIF-8 | 4 | 2 | (4, 2) | sod | PASS |
| UiO-66 | 12 | 2 | (12, 2) | fcu | PASS |


This is the anchor for the whole extension. Any spectrum computed on a graph that fails this table is describing a material that does not exist.


---


## 3 · Influential nodes


### 3.1 · The three measures

- **Degree** — how many other blocks a block connects to. In this graph the degree *is* the coordination number, which is why it is the most meaningful of the three.
- **Eigenvector centrality** — a block is important if its neighbours are important. The leading eigenvector of the adjacency matrix, computed here by power iteration.
- **Betweenness centrality** — how many shortest paths pass through a block. Computed with Brandes' algorithm.

### 3.2 · The finding: influence cannot be ranked in a perfect crystal


The brief asked for the influential nodes to be highlighted, with the natural implication of a top-k list. Running the measures gives a result that makes such a list meaningless:


> **Every one of the four structures has exactly TWO distinct degree values**
>
> One value for all nodes, one value for all linkers. Nothing else.
>
> This is not a defect in the calculation — it is what a perfect crystal *is*. Every metal cluster in HKUST-1 is related to every other by a symmetry operation, so they are genuinely, exactly identical. There is no "most influential" cluster because they cannot be told apart.
>
> A top-12 list from such a graph is not a ranking. It is the first twelve entries of a tie, and its content depends entirely on the order the blocks happened to be indexed in.


This is a real and citable finding rather than a negative result. It says the question "which node is most influential?" is ill-posed for a defect-free framework, and it explains why an influence ranking computed on one is unstable. The degree *value* remains the most useful number in the analysis — it is the coordination number, and it determines the topology — but the *ranking* does not exist.


### 3.3 · A star graph is the diagnostic signature of a broken construction


A block graph in which one vertex has very high degree and essentially every other has degree 1 is not a MOF. It is what happens when periodic connections are dropped: the structure fragments, and the fragments attach to whatever single block survived. If the degree distribution has one huge value and a mass of 1s, the graph construction should be checked before the result is interpreted.


---


## 4 · The Laplacian spectrum


The Laplacian is `L = D − A`, where `D` is the diagonal matrix of degrees and `A` is the adjacency matrix. Its eigenvalues describe how well connected the network is.

- `λ₁ = 0` always. Its multiplicity is the number of disconnected components — so a second zero eigenvalue means the framework has fallen apart, which is a useful automatic check.
- **`λ₂`, the algebraic connectivity**, is the informative one. It measures how hard the network is to cut in two. A high `λ₂` means a robust, well-tied framework; a low one means the structure has a weak point.
- The largest eigenvalue is bounded by twice the maximum degree, which gives a cheap sanity check on the whole computation.

### 4.1 · Defects make influence measurable


If a perfect crystal has no distinguishable nodes, the way to recover a meaningful notion of influence is to break the symmetry — which is also what real materials do. Missing-linker defects are well documented in UiO-66 and are central to how MOFs are tuned in practice.


Removing a single linker from HKUST-1 and recomputing:

| Quantity | Perfect crystal | One linker removed | Interpretation |
|---|---|---|---|
| Distinct centrality values | 2 | **4** | Symmetry is broken; blocks become distinguishable |
| Algebraic connectivity λ₂ | 1.44 | **1.19** | The framework is measurably weaker |
| Influence ranking | undefined (all tied) | well defined | The brief's question now has an answer |


So the honest answer to "highlight the influential nodes" is: **in a perfect crystal there are none to highlight, and that is the finding; introduce a defect and influence becomes both defined and quantitative.** The 17% drop in λ₂ measures how much that single missing linker weakened the material.


---


## 5 · The multifractal spectrum


The method comes from Xiao et al., *"Deciphering the generating rules and functionalities of complex networks"*, **Scientific Reports 11, 22964 (2021)**. It characterises a network by how mass grows around its vertices, and produces a curve rather than a single number.


### 5.1 · The mathematics

| Symbol | Definition | What it means physically |
|---|---|---|
| `M_i(r)` | number of vertices within distance `r` of vertex `i` | how much network is reachable in `r` steps |
| `u_i(r)` | `M_i(r) / M` | the normalised mass around `i` — a probability |
| `U_q(r)` | `Σ_i u_i(r)^q` | the partition function; `q` reweights dense vs sparse regions |
| `τ(q)` | exponent in `U_q(r) ~ (r/d)^τ(q)` | the mass exponent, from a log–log fit |
| `α` | `dτ/dq` | the local scaling exponent — the local dimension |
| `f(α)` | `qα − τ` | how much of the network shares that local dimension |
| `D(q)` | `τ(q)/q` | generalised fractal dimension |
| `α₀` | the `α` where `f(α)` is maximum | the dominant local dimension of the network |
| `A` | `ln[(α₀−α_min)/(α_max−α₀)]` | asymmetry — which side of the spectrum dominates |
| NFD | node fractal dimension | the single-number summary of growth |


The role of `q` is the key idea. At large positive `q` the sum is dominated by vertices with the largest mass around them; at large negative `q` by the sparsest. Sweeping `q` therefore probes different parts of the network, and the resulting spread of `α` says whether the network scales uniformly (a single point — a simple fractal) or unevenly (a spread-out curve — a *multi*fractal).


### 5.2 · Box-growing, not box-covering


The paper uses **box growing**: for each vertex, grow a ball of radius `r` and count what it contains. An alternative in the literature is **box covering**, which tiles the whole network with boxes and is randomised — different runs give different answers.


> **Why the distinction mattered here**
>
> The first implementation used box covering. With the small number of trials typically used, the same structure gave a noticeably different spectrum on every run — measured spread in `α_max` of **0.171** for HKUST-1 across random seeds. Any band built from numbers that unstable is meaningless.
>
> Raising the trial count to 40 cuts that spread to **0.006**, but at real cost in runtime.
>
> Box growing, the method the paper actually specifies, is **deterministic**: the measured spread across seeds is exactly **0.00e+00**. Switching to the published method removed the reproducibility problem entirely rather than managing it.


### 5.3 · Results — the published NMFA method

| Structure | Metal | Node fractal dimension | α₀ |
|---|---|---|---|
| HKUST-1 | Cu | 1.68 | 1.63 |
| MOF-5 | Zn | 1.81 | 1.61 |
| ZIF-8 | Zn | 1.93 | 1.82 |
| **UiO-66** | **Zr** | **2.30** | 1.67 |


### 5.4 · Results — iNMFA over the influential blocks

| Structure | Metal | Blocks | Influential | α range | Width |
|---|---|---|---|---|---|
| HKUST-1 | Cu | 112 | 34 | 1.59 – 1.89 | 0.29 ± 0.06 |
| MOF-5 | Zn | 256 | 77 | 1.47 – 1.95 | 0.49 ± 0.05 |
| ZIF-8 | Zn | 288 | 87 | 1.19 – 1.99 | 0.80 ± 0.05 |
| UiO-66 | Zr | 189 | 57 | 1.80 – 2.57 | 0.77 ± 0.06 |


> **These widths are approximate, and the reason is the tie degeneracy**
>
> In a perfect crystal there are only two distinct degrees, so "the top 30% by degree" is **a tie**. Which blocks get selected depends on the order the blocks happen to be labelled in — and two implementations that build the *same graph* (identical edge sets, verified) can label it differently and report widths differing by more than 0.07.
>
> This is the same degeneracy that makes influence unrankable (Section 3.2), reappearing in the spectrum. **iNMFA widths from a defect-free crystal should therefore be quoted with an error bar, not to three decimals.**
>
> Two things remove it, and both are used here: the **box-growing NMFA** of Section 5.3 is deterministic, so there is no covering randomness and no selection tie to begin with; and **defects** break the symmetry, after which the selection is well defined. The 8-framework band study of Section 8 is also unaffected, because it runs on full atomic graphs where degrees genuinely vary.


On the box-growing NMFA (5.3) the Zr structure separates cleanly: its node fractal dimension is the highest by a clear margin, which is what a 12-connected cluster should give, since more connections per node means mass grows faster with radius.


> **An earlier version of this table was wrong, and the correction changed the conclusion**
>
> The iNMFA widths above used to read 0.03, 0.09, 0.01 and 0.36, and were presented as showing Zr separating from Cu and Zn. **That separation was an artefact of an estimator bug** (Section 5.5). With the bug fixed, ZIF-8 (0.80, Zn) and UiO-66 (0.77, Zr) overlap almost completely, so **iNMFA alone does not separate the metals**.
>
> The box-growing NMFA in 5.3 is computed differently and is not affected by the bug; its separation stands. Reporting both, and saying which one changed, is the honest presentation.


### 5.5 · The averaging-order bug


Box covering is random, so it is repeated many times and the results averaged. **The order of those two operations matters.** The partition function must be built per realisation and then averaged in log space. Averaging the probability measure `p_i(r)` across trials *first*, and only then raising it to the power `q`, exponentiates an already-smoothed quantity — which suppresses exactly the fluctuation that multifractality exists to measure, and biases every spectrum narrow.

| Estimator | HKUST-1 width | Seed-to-seed scatter |
|---|---|---|
| Average `p(r)` first, then raise to `q` (wrong) | 0.021 ± 0.004 | 17% |
| Raise to `q` per trial, average `ln Z` (correct) | 0.327 ± 0.032 | 10% |


Same graph, same random seeds, same box coverings — only the averaging order differs. The bug was present in both this project's implementation and, independently, in a teammate's separate notebook working on a different set of structures and a different graph construction. Two people found it on two datasets, which is reasonable evidence it is a genuine methodological trap rather than a typo. The browser implementation and the Python implementation were both corrected and re-cross-validated (0.317 vs 0.327, agreeing within seed scatter).


---


## 6 · The defect that made the spectrum undefined


The single most consequential correction in this part of the work. The iNMFA computation was being run on the **induced subgraph of the influential blocks** — take the high-degree blocks, keep only the edges between them, compute the spectrum on that.


In a MOF, the high-degree blocks are the metal clusters. And metal clusters are **never bonded to each other** — they connect *through* linkers. So that induced subgraph has no edges at all.


```
Edges inside the influential-node induced subgraph:

  HKUST-1        0 edges     <-- the spectrum was being computed on THIS
  MOF5           4 edges
  ZIF-8          0 edges     <-- and THIS
  UiO-66         4 edges
```
*Measured, and reproduced in the notebook. With no edges there are no distances, so no mass function, so no spectrum.*


**The correction:** compute the growth curves on the **full** block graph, and use the influential set only to select *which* curves enter the analysis. The influential blocks are still the subject; they are simply measured in the network they actually live in. With that change the spectrum is defined for all four structures.


## 7 · The family band — what was and was not established


The final part of the brief was to deduce something like "all Zr MOFs fall in this band". A band is the min–max envelope of a set of reference spectra; a candidate is scored by how much of its own spectrum falls inside.


The mechanism works, and can be demonstrated on a genuine same-topology family — UiO-66 plus a set of missing-linker defect variants:

| Candidate | Fraction of its spectrum inside the band |
|---|---|
| Held-out member of the same family | 53.3% |
| Second held-out same-family member | 87.3% |
| HKUST-1 (different framework) | outside the band entirely |
| MOF-5 (different framework) | outside the band entirely |
| ZIF-8 (different framework) | outside the band entirely |


Members of the family land inside; unrelated frameworks land outside. The method separates what it should separate.


> **The claim that is NOT established**
>
> "All zirconium MOFs fall under this spectrum" **has not been demonstrated**, and the reason is simple: there is exactly one zirconium structure in this test set.
>
> One structure cannot define a family band. What has been shown is that the machinery works, that it separates a real family from non-members, and that Zr separates from Cu and Zn on the box-growing measure.
>
> Establishing the actual claim needs a few hundred MOFs grouped by metal — CoRE MOF or QMOF. Every module runs per-CIF, so scaling up is a loop over the same functions, not new research. Saying this plainly is stronger than overclaiming from n = 1.


---


## 8 · The band across eight real frameworks


The band work above uses our block quotient graph on four structures. It was extended to **eight experimentally reported frameworks**, downloaded at run time from the RASPA2 structure library, and analysed on **full atomic graphs** of 3,400–6,100 atoms rather than coarse-grained block graphs. The eight were chosen because they all appear in the xenon/krypton separation literature.

| Framework | Metal | Atoms | Diameter | Δα | Group |
|---|---|---|---|---|---|
| Co-MOF-74 | Co | 5184 | 38 | 0.941 ± 0.054 | in band |
| ZIF-8 | Zn | 4968 | 40 | 0.897 ± 0.077 | in band |
| Mg-MOF-74 | Mg | 4536 | 36 | 0.857 ± 0.070 | in band |
| Zn-MOF-74 | Zn | 4536 | 36 | 0.857 ± 0.070 | in band |
| HKUST-1 | Cu | 4992 | 50 | 0.844 ± 0.063 | in band |
| Ni-MOF-74 | Ni | 5184 | 38 | 0.835 ± 0.057 | in band |
| **IRMOF-1 (MOF-5)** | Zn | 3392 | 56 | **0.375 ± 0.064** | **outside** |
| **UMCM-1** | Zn | 6120 | 63 | **0.203 ± 0.028** | **outside** |


### 8.1 · Two different things get called "the band"


The word "band" is used loosely for two distinct constructions, and testing both revealed that only one of them works as a membership test. Reporting both — including the one that fails — is the honest presentation.

| Version | What it is | Does it discriminate? |
|---|---|---|
| **Δα band** (1-D) | The range of spectrum *widths* spanned by the group | **Yes.** Held out and re-tested, all 8 frameworks are classified correctly |
| **f(α) envelope** (2-D) | Shade between the highest and lowest curve; score what fraction of a candidate lies inside | **No.** Held out, ZIF-8 (member) scores 0.0%; UMCM-1 (non-member) scores 44.7% |


The failure is stark rather than marginal — a non-member scores more than forty points higher than a member. The reason is visible once the curves are plotted: the two narrow spectra are **short arcs sitting inside the wide group's α range but far below it in f(α)**. An envelope test therefore measures where a curve sits in α, not how wide it is — and width is the quantity that actually separates these frameworks.


> **A measured negative result, not a hidden one**
>
> A curve trivially lies inside a band it helped define, so the only meaningful test is to **hold a framework out**, rebuild the band from the rest, and score it against that. Doing so is what exposed the failure.
>
> The website (Section 15b) has a "hold out" button on every row so anyone can reproduce this in front of you. The 1-D Δα column beside it classifies all eight correctly.


### 8.2 · What the Δα band does establish


Six of the eight frameworks land in a band spanning Δα = 0.835–0.941, and two fall far below it at 0.375 and 0.203. The gap between the two groups is **0.46 — roughly four times the 0.105 noise floor** measured on provably identical structures. That margin is what makes the split a property of the frameworks rather than of the estimator.


The six span **five different metals** (Cu, Ni, Co, Mg, Zn) and two different binding chemistries — carboxylate for HKUST-1 and MOF-74, imidazolate for ZIF-8. So the grouping is **not** by metal and **not** by chemistry.


### 8.3 · What it actually measures


Δα is the width of the singularity spectrum, and it measures how unevenly connectivity is distributed through the network — in physical terms, **how heterogeneous the pore architecture is**. A wide Δα means the framework has a structurally varied pore network; a narrow one means it is uniform.


That reading is consistent with the two outliers. IRMOF-1 and UMCM-1 both have large, regular, open pore systems, and they are the two narrow spectra. UMCM-1 is a genuine mixed-linker framework, which the coarse-graining independently confirms by finding two distinct linker sizes in it.


> **Three things this result is NOT — each of which an examiner may probe**
>
> **The four MOF-74 curves overlapping is not evidence of anything.** They are the same graph — proved isomorphic in the source notebook — so they *must* overlap. Their role is as a reproducibility control, not as band members.
>
> **That control sets a noise floor of 0.105**, measured as the spread across those isomorphic graphs. HKUST-1 (0.844) and ZIF-8 (0.897) differ by less than that floor, so the correct statement is "six frameworks are indistinguishable within the method's noise", not "six frameworks match".
>
> **Δα is not a stability or gas-uptake predictor.** Nothing in this analysis measures stability, adsorption or binding energy — the graph is unweighted, so it does not even know which element an atom is. Xe/Kr relevance is why these eight frameworks were selected; it is not something the calculation produces. Reading the band as "these MOFs are more stable" is not supported.


### 8.4 · Finite-size dependence


Δα has not converged in supercell size — it grows with the graph, because the fit window spans `ln(1/diameter)` to `ln(0.34)` and a larger graph samples a wider range of scales. These are therefore **finite-size effective widths at a stated graph size**, not asymptotic exponents, and absolute values should always be quoted with the diameter alongside.


The ranking survives this caveat, and for a specific reason worth stating: the bias runs the *wrong way* to explain the result. IRMOF-1 and UMCM-1 have among the largest graphs in the set (diameters 56 and 63) yet the smallest widths, while the wide group sits at diameters 36–50. A finite-size artefact would push the biggest graphs toward *larger* Δα, not smaller — so it cannot be what produces the split.
