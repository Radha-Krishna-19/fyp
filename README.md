# MOF Framework Analysis — Final Year Project

Visualising how a metal–organic framework is decomposed into building blocks, then
analysing the resulting framework as a network to see whether MOFs can be grouped by
structure alone.

> **Read this page first.** It explains what the project is, why we chose this approach,
> and what we found. Everything else is detail.

---

## 1 · The one-paragraph version

Metal–organic frameworks (MOFs) are sponge-like crystals built by joining metal clusters to
organic molecules. There are hundreds of thousands of them, and simulating each one to find
out what it can do takes hours per structure. **We ask whether a cheap, purely structural
descriptor — computed from the framework's connectivity in seconds — can group MOFs into
useful families instead.** We built a visualisation of how the decomposition works, then
computed multifractal spectra for 77 frameworks and tested what those spectra actually mean.

---

## 2 · Why this path — and what a graph has to do with a MOF

This is the question everyone asks first, so here is the chain of reasoning.

1. **A MOF is not a molecule — it is a repeating framework.** What distinguishes one MOF
   from another is not only *which atoms* it contains but **how they are wired together**.
2. **Wiring is exactly what a graph describes.** Collapse each building block to a point and
   each bond between blocks to a line, and the chemistry reduces to pure connectivity.
3. **The useful properties follow the wiring.** Gas moves through the pore network, and the
   pore network *is* the empty space left by that wiring. Describing the wiring describes
   what the material can do.
4. **Networks can be measured.** Once it is a graph, network science applies — coordination
   number, centrality, the Laplacian, fractal measures.
5. **A spectrum compresses a whole framework into a few numbers**, so you can compare two
   MOFs, or ten thousand, without simulating any of them.

### Why bother, when simulation exists?

Because simulation does not scale. A GCMC gas-uptake calculation takes **hours** per
structure; there are **hundreds of thousands** of MOFs. A graph descriptor takes **seconds**.

If a cheap structural number can narrow 100,000 candidates to a few hundred worth simulating
properly, that is the whole value: **not replacing simulation, but deciding what to simulate.**

### What the multifractal spectrum actually measures

Start simple: **how much network is near a given block?** Grow a ball of radius `r` around it
and count what falls inside. Do that for every influential block and you have a set of growth
curves.

A perfectly uniform framework would have one growth rate — a single fractal dimension. Real
frameworks are not uniform: some regions are tightly tied, others open into voids. So you
need a **distribution** of growth rates, and that distribution is the spectrum `f(α)`.

| Quantity | What it means |
|---|---|
| `α` | how fast the network grows around one block — a *local* dimension |
| `f(α)` | how much of the framework shares that growth rate |
| `α₀` (the apex) | the *typical* growth rate — the framework's dominant dimension |
| **`Δα`** (the width) | **how varied the framework is.** Narrow = uniform. Wide = a mix of tight and open regions |
| `A` (asymmetry) | which side dominates — mostly dense with voids, or mostly open with dense knots |

A spectrum is a **fingerprint of pore-network heterogeneity**. `Δα` is that fingerprint as a
single number, which is what makes a *band* possible.

### The goal

> Establish whether a purely structural, simulation-free descriptor can group MOFs into
> meaningful families — so a new framework can be placed against a known band and triaged
> without expensive calculation.

---

## 3 · What we built

### Part 1 — A visualisation of the decomposition

Before any network analysis, you have to turn a crystal structure into building blocks. The
field does this with the **MOFid** pipeline (Snurr group, Northwestern). We translated all of
it from C++ into readable Python, one module per stage, and built an interactive walkthrough
that shows the real code beside a live 3D model at each stage.

**Nothing in the algorithm is modified.** This is a visualisation of the published pipeline —
its purpose is to make the node/linker assignments inspectable, because everything downstream
depends on them being right.

Upload any `.cif` and the whole pipeline runs on it live in the browser.

**Where:** `2_python/code_01` … `code_07`, Sections 7–8 of the website

---

### Part 2 — The framework as a network

Once decomposed, the framework *is* a graph. Two things had to be right before anything could
be computed on it.

**The graph must be periodic.** A crystal has no edges. Drop the lattice translations and
every bond crossing a cell face disappears, the framework fragments, and coordination numbers
come out wrong — UiO-66 reports 6-connected instead of the published 12. Built as a labelled
quotient graph, all four test structures match published crystallography.

**Influence cannot be ranked in a perfect crystal.** The brief was to find the most
influential nodes. But a perfect crystal has only **two** distinct connection counts — one for
all nodes, one for all linkers — because every metal cluster is symmetry-equivalent to every
other. A "top 10" list is the first 10 entries of a tie.

That is a real finding, and it points at its own fix: **break the symmetry.** Remove a single
linker (a well-documented real MOF defect) and influence becomes measurable — HKUST-1 goes
from 2 to 4 distinct centrality values, and λ₂ falls 1.44 → 1.19.

**Where:** `2_python/code_09_network_analysis.py`, Sections 10–12

---

### Part 3 — The spectrum and the band

We implemented the method from **Xiao et al., Scientific Reports 11, 22964 (2021)** and
applied it to **77 frameworks** from MOFX-DB with published pore diameters.

> **Know what this dataset is.** All 77 are named `hMOF-###` — from the **hypothetical MOF**
> database: computer-generated candidates, **not** materials anyone has synthesised. The
> notebook requested CoRE MOF 2019 but the server returned hMOF records; a check now catches
> this. And **every one has a Zn₄O node**, so the set cannot support claims about different
> metals. What it *is* good for: one node type with many linkers — a clean varied-linker family.

#### The spectrum is now computed correctly

A multifractal spectrum must be an **inverted parabola** peaking at `q = 0`, where
`f(α₀) = D₀`. Ours sloped downhill.

The paper defines `τ(q) = ln 𝒫_q(r) / ln(r/r_N)` — a fit **through the origin**. Our code used
a **free-intercept slope**. At `q = 0` every term is `pr_i⁰ = 1`, so `𝒫₀ = |I|` is identical
at every radius; a flat line has slope zero, forcing `τ(0) = 0` and `f(α₀) = 0` — deleting the
peak.

**Fixed. All 77 frameworks now peak at q = 0.**

| | before | after |
|---|---|---|
| τ(0) | 0.0000 | −2.5669 |
| f(α₀) | 0.0000 | +2.5669 |
| spectra peaking at q = 0 | 0 / 77 | **77 / 77** |

#### The band

| | |
|---|---|
| Δα range | 1.016 – 1.410 |
| Interquartile band | **1.112 – 1.250** |
| Asymmetry A | −1.51 to −1.04 (**all 77 negative**) |

All 77 land in a tight band with a consistent asymmetry sign — a genuinely well-defined
family signature for this node type.

#### But the band is not yet a chemical statement

| Test | r |
|---|---|
| Δα vs pore diameter (LCD), raw | −0.497 |
| Δα vs LCD, **controlling for graph size** | **+0.101** — vanishes |
| Δα vs graph size, **controlling for LCD** | **+0.621** — survives |

Linear model: graph size alone R² = 0.533; adding pore diameter → 0.538. **Pore size buys
+0.005.**

So Δα is mostly tracking **how many atoms are in the supercell** — set by `MIN_CELL_LENGTH`
and the `MAX_ATOMS` cap, which are computational parameters, not chemistry.

**Where:** `3_notebooks/mof_band_analysis.ipynb`, `2_python/code_10`, `code_11`, Section 16

---

## 4 · The headline results

| # | Finding | Evidence |
|---|---|---|
| 1 | The block network must be built **periodically** | UiO-66 reports 12-connected (correct) vs 6 (naive); all four structures match published crystallography |
| 2 | Influence cannot be ranked inside a perfect crystal | Only 2 distinct degree values — a top-k list is sorting ties |
| 3 | Defects make influence measurable | Remove 1 linker: 2 → 4 distinct centralities, λ₂ 1.44 → 1.19 |
| 4 | The spectrum is now computed to the paper's definition | 77/77 proper inverted parabolas; τ(0) = −2.57, f(α₀) = +2.57 |
| 5 | 77 frameworks share a tight Δα band | 1.11 – 1.25 interquartile, asymmetry negative in all 77 |
| 6 | **That band is confounded by graph size** | Pore correlation −0.50 → +0.10 controlling for size; size survives at +0.62; pore adds R² +0.005 |
| 7 | Three estimator bugs found and fixed | Edgeless subgraph; log-space averaging order; τ fitted with a free intercept |

**Not established:** that the band carries chemical meaning. It is currently a descriptive
range whose main driver is supercell size. **What would fix it:** compare only frameworks at
comparable graph size, or normalise the fit window so Δα stops growing with the graph — then
re-test. Both are concrete next steps, not open research questions.

---

## 5 · Anticipated questions

**"Isn't this throwing away the chemistry?"**
Deliberately. The graph is unweighted — it does not know which element an atom is. That is a
real limitation and we say so. It is also the point: whatever survives is **pure
architecture**, which transfers across chemistries in a way an element-specific descriptor
cannot.

**"Does Δα predict gas uptake?"**
**No, and we never claim it.** Nothing here computes adsorption. Δα describes pore-network
architecture only.

**"Why only the influential nodes?"**
The paper's iNMFA restricts the measure to the top-connected 10%. Section 11 shows the catch:
in a perfect crystal every node ties, so "top 10%" is ambiguous. We report it.

**"Why a periodic graph?"**
Because a crystal has no edges — see Part 2.

**"What would make this genuinely useful?"**
Remove the size confound, then test against measured properties on a set with real metal
diversity.

---

## 6 · Where everything lives

```
1_website/     ← START HERE. Open index.html. One page, everything, interactive.
2_python/      One runnable module per pipeline stage + the analysis modules
3_notebooks/   mof_band_analysis.ipynb — the 77-framework spectrum study
4_reference/   Figures
5_concepts/    Deep-dive documents
PRESENTATION_SCRIPT.md
```

**The website is the main deliverable.** `1_website/index.html` — just double-click it. No
server, no install. Seventeen sections, live 3D, the real algorithm running in your browser on
any structure you upload, and every source file readable by clicking its name.

> **Before presenting:** save
> <https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js> into `1_website/` as
> exactly `three.min.js`, or the 3D panels will be blank without internet.

### Module map

| File | Stage |
|---|---|
| `code_01_cif_input.py` | Read the CIF — no bonds exist yet |
| `code_02_bond_assignment_pbc.py` | Infer bonds, periodic minimum-image search |
| `code_03_element_classification.py` | `is_metal()` |
| `code_04a/b/c` | metal-oxo · single-node · all-node decomposition |
| `code_05_centroid_simplification.py` | Collapse each block to a point |
| `code_06_systre_topology_export.py` | Write a real `.cgd` for Systre |
| `code_07a/07b` | MOFid / MOFkey assembly |
| **`code_09_network_analysis.py`** | **periodic graph, centrality, Laplacian spectrum** |
| **`code_10_multifractal_spectrum.py`** | **iNMFA, reference band, candidate test** |
| **`code_11_nmfa_paper.py`** | **NMFA exactly as published — box-growing** |

Modules 01–07 are faithful translations of published work, used unmodified. **09–11 are ours.**

---

## 7 · Honest limitations

- **Systre is not reimplemented.** We write a genuine `.cgd`, but the topology tool is external.
- **InChIKeys are placeholders** in `code_07b`. Nothing downstream uses them.
- **The dataset is hypothetical and single-metal** (see Part 3).
- **Δα is finite-size dependent** and is not a stability or uptake predictor.
- **Nothing here is an adsorption calculation.**
- **The influential-node tie** means iNMFA widths carry an implementation sensitivity on a
  defect-free crystal.

---

## 8 · Sources

- Decomposition: [`snurr-group/mofid`](https://github.com/snurr-group/mofid) (Northwestern)
- Multifractal method: Xiao et al., *"Deciphering the generating rules and functionalities of
  complex networks"*, **Scientific Reports 11, 22964 (2021)** —
  <https://www.nature.com/articles/s41598-021-02203-4>
- Structures: [MOFX-DB](https://mof.tech.northwestern.edu) (Northwestern)
