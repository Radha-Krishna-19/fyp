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


### 5.5 · Two bugs in the estimator, both found by checking against the paper


#### Bug A — the spectrum had the wrong shape


A multifractal spectrum `f(α)` must be an **inverted parabola** whose peak sits at `q = 0`, where `f(α₀) = D₀`, the fractal dimension. Ours sloped downhill instead — which is a mathematics problem, not a property of the materials.


The paper defines the mass exponent as a **ratio**, `τ(q) = ln 𝒫_q(r) / ln(r/r_N)`. Over several radii that is a straight-line fit **through the origin**, because the relation `𝒫_q ~ (r/r_N)^τ` carries no prefactor. Our code used a **free-intercept** least-squares slope. At `q = 0` the difference is fatal:

- at `q = 0` every term is `pr_i⁰ = 1`, so `𝒫₀ = |I|` — the *count* of influential nodes;
- that count is **identical at every radius**, so a free-intercept fit sees a flat line;
- a flat line has slope zero, so `τ(0) = 0`, and therefore `f(α₀) = 0·α − 0 = 0`.

The peak is pinned to zero and the parabola vanishes. Measured across 77 frameworks: **τ(0) = 0 and f(0) = 0 in every one, and not one peaked at q = 0.** With the paper's definition `ln(r/r_N) < 0`, so `τ(0) = ln|I| / negative < 0` and `f(α₀) = −τ(0) > 0` — the peak returns.


> **Fixed, and re-measured on the full dataset**
>
> With `tau_mode="paper"` the recomputed spectra give τ(0) = −2.5669 and f(α₀) = +2.5669, and **all 77 of 77 frameworks now peak at q = 0** — proper inverted parabolas.
>
> Everything downstream of τ changed with it: α₀, the asymmetry A and D(q) are meaningful quantities for the first time, and the Δα values roughly quadrupled (median 1.20, previously ~0.3).

| τ definition | τ(0) | f(0) | peak at | inverted parabola? |
|---|---|---|---|---|
| free-intercept slope (ours) | 0.0000 | 0.0000 | q = −4 | **no** |
| paper: `ln 𝒫_q / ln(r/r_N)` | −3.5028 | +3.5028 | **q = 0** | **yes** |


Verified on a network built from scratch with identical data and only the τ definition swapped, then re-verified in both implementations: Python and the browser engine now agree at τ(0) = −2.6551 on HKUST-1. Selectable as `tau_mode="paper"` (the default) or `"slope"` to reproduce the old behaviour.


#### Bug B — the averaging order


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


## 8 · The band across 77 real frameworks


The band work was scaled from 8 frameworks to **77**, drawn from MOFX-DB, analysed on full atomic graphs and accompanied by published pore diameters (PLD, the pore-limiting diameter, and LCD, the largest cavity diameter). That was enough data to ask a question 8 structures could not answer.


> **Know what this dataset is before quoting anything from it**
>
> All 77 structures are named `hMOF-###`. They come from the **hypothetical MOF** database — **computer-generated candidate structures that have never been synthesised**. The notebook requested `CoREMOF 2019`, which *is* experimental, but the server returned hMOF records and nothing verified it. A check was added so this cannot recur silently.
>
> **Consequence 1:** nothing computed on this set may be described as "experimental" or "real". It is a computational screening library.
>
> **Consequence 2:** every one of the 77 has a **Zn₄O node**, so this set is effectively single-metal. It cannot support any claim about behaviour across different metals — including the supervisor's zirconium question.
>
> **What it is genuinely good for:** one node type combined with many different linkers, which makes it a real same-node, varied-linker family — arguably a cleaner test of linker effects than a mixed-metal set would be.


### 8.1 · What a band is


A band is the range of spectrum width Δα that a group of frameworks shares, so a new framework can be tested for membership. Across the 77 the interquartile band is **Δα = 1.11 – 1.25**, with the asymmetry `A` negative in every single framework — a consistent family signature.


### 8.2 · Does the band mean pore architecture? No.


On 8 frameworks it looked as though it did: the narrow spectra belonged to frameworks with large open pores. On 77, with pore diameters available, that reading does not survive.

| Test | Correlation with Δα |
|---|---|
| pore diameter (LCD), raw | −0.497 |
| pore diameter (LCD), **controlling for graph size** | **+0.101** — vanishes |
| graph size, raw | +0.730 |
| graph size, **controlling for pore diameter** | **+0.621** — survives |

| Linear model of Δα | R² |
|---|---|
| graph size alone | 0.533 |
| pore diameter alone | 0.247 |
| both together | 0.538 |
| **what pore diameter adds over size** | **+0.005** |


> **Retracted: "the band groups MOFs by pore architecture"**
>
> The partial correlation collapses from −0.50 to +0.10 once graph size is held fixed, while graph size survives holding pore size fixed. Adding pore diameter to a model that already contains graph size buys about 0.005 of R².
>
> **Δα is tracking how many atoms are in the supercell**, and supercell size is set by `MIN_CELL_LENGTH` and the `MAX_ATOMS` cap — computational parameters, not chemistry. This is the finite-size dependence flagged earlier, now measured across a whole dataset instead of three structures.
>
> Two routes make the question answerable: compare only frameworks of **comparable graph size**, or **normalise the fit window** per structure so Δα stops growing with the graph, then re-test the correlation. Reporting the confound is the result; a band built on an uncontrolled size effect would not survive the first person who checked it.


### 8.3 · What still stands

- **The method is now implemented correctly.** τ(q) matches the paper, the spectrum is a proper inverted parabola, and α₀, the asymmetry A and D(q) are meaningful quantities for the first time.
- **The band exists as a descriptive range.** What it lacks is a demonstrated physical meaning.
- **Δα is not a stability or gas-uptake predictor.** The graph is unweighted — it does not know which element an atom is, let alone its binding energy.
- **The influential-node degeneracy still applies** (Section 3.2): in a defect-free crystal the top-k selection is a tie, so iNMFA widths carry an implementation sensitivity on top of everything above.
