# Why This Approach

**What a graph has to do with a MOF, and what a spectrum is for**

> The reasoning behind attacking a chemistry problem with network theory: why simulation does not scale, what the multifractal spectrum actually measures, why the decomposition has to come first, and what was and was not achieved.

*Part of the MOF Building-Block Analysis final year project — see the [main README](../README.md).*

---

## 1 · The question this project asks


There are **hundreds of thousands** of known and hypothetical metal-organic frameworks. Finding out what any one of them can do — how much gas it holds, how selectively it separates a mixture — normally means a molecular simulation that takes **hours per structure**. Screening a database that size directly is not feasible.


> **The question**
>
> Can a **purely structural, simulation-free descriptor** — computed from a framework's connectivity in seconds — group MOFs into meaningful families, so that a new framework can be placed against a known band and triaged without any expensive calculation?


The value of an answer is not that it replaces simulation. It is that it decides **what to simulate**. Narrowing 100,000 candidates to a few hundred worth simulating properly is the entire point.


---


## 2 · Why a graph


The step from "crystal structure" to "network" is the one that needs justifying, so here is the chain in full.

1. **A MOF is not a molecule — it is a repeating framework.** What distinguishes one MOF from another is not only which atoms it contains, but **how those atoms are wired together**. Two frameworks built from identical components can behave completely differently if the connectivity differs.
2. **Wiring is exactly what a graph describes.** Collapse each building block to a point and each bond between blocks to a line. What remains is pure connectivity, with the chemistry deliberately stripped away.
3. **The useful properties follow the wiring.** Gas moves through the pore network, and the pore network *is* the empty space left behind by that wiring. A description of the connectivity is therefore a description of the pore system, which is what determines behaviour.
4. **Networks can be measured.** Once the framework is a graph, decades of network science become applicable: coordination number, centrality, the Laplacian spectrum, fractal and multifractal measures.
5. **A spectrum compresses a whole framework into a few numbers.** That is what makes comparison at scale possible — two MOFs or ten thousand, without simulating any of them.

> **What is deliberately lost**
>
> The graph is **unweighted**. It does not know which element an atom is, let alone its polarisability or binding energy. That is a genuine limitation and it is stated plainly wherever results are quoted.
>
> It is also the point. Whatever survives that stripping is **pure architecture**, and architecture transfers across chemistries in a way an element-specific descriptor cannot. A result that holds for a copper framework and a zinc framework alike is telling you something structural.


---


## 3 · What the multifractal spectrum measures


### 3.1 · Start with a simpler question


**How much network is near a given block?** Centre a ball of radius `r` on it and count what falls inside. Do that for a range of radii and you have a growth curve for that block; do it for every influential block and you have a set of curves.


If a framework were perfectly uniform, every block would grow at the same rate, and a **single number** — an ordinary fractal dimension — would describe the whole thing. Real frameworks are not uniform. Some regions are tightly tied together; others open out into large voids. So instead of one number you need a **distribution** of growth rates, and that distribution is the multifractal spectrum `f(α)`.


### 3.2 · Reading the spectrum

| Quantity | Formal definition | What it means physically |
|---|---|---|
| `α` | `dτ/dq` | how fast the network grows around one particular block — a **local** dimension |
| `f(α)` | `qα − τ` | how much of the framework shares that growth rate |
| `α₀` | the α at which f(α) peaks | the **typical** growth rate — the framework's dominant dimension |
| **`Δα`** | `α_max − α_min` | **how varied the framework is.** Narrow means uniform throughout; wide means a mix of tight regions and open ones |
| `A` | `ln[(α₀−α_min)/(α_max−α₀)]` | which side dominates — mostly dense with a few voids, or mostly open with a few dense knots |


So a spectrum is a **fingerprint of pore-network heterogeneity**, expressed as a curve. `Δα` reduces that fingerprint to one number, which is what makes a *band* — a range shared by a family — possible in the first place.


> **The shape is not optional**
>
> `f(α)` **must** be an inverted parabola whose peak sits at `q = 0`, where `f(α₀) = D₀`, the fractal dimension. If a computed spectrum slopes downhill instead, that is a mathematics error, not a property of the material.
>
> This project had exactly that error — the mass exponent was extracted with a free-intercept fit rather than the paper's through-the-origin ratio, which forced `τ(0) = 0` and deleted the peak. It is documented in Document 4, Section 5.5. All 77 spectra are now proper parabolas.


---


## 4 · Why the decomposition has to come first


None of the above can be computed until the framework has been split into building blocks. That step decides what the vertices of the graph *are*, so an error there propagates into everything downstream — coordination numbers, centralities, the spectrum, the band.


The field does this with the **MOFid** pipeline (Snurr group, Northwestern), which is used to annotate the large public MOF databases. This project translates that pipeline into Python module by module and presents it as an **interactive visualisation**: the real code beside a live 3D model of the structure at each stage.


> **This is a visualisation, not a modification**
>
> The published algorithm is used **unmodified**. Nothing about it is changed, corrected or replaced.
>
> The purpose is inspectability. The decomposition is normally a black box that turns a CIF into a list of blocks; making each stage visible is what lets anyone confirm that the blocks the network analysis runs on are the right ones. Any `.cif` can be uploaded and the whole pipeline runs on it live.


---


## 5 · What was achieved, and what was not


### 5.1 · Achieved

- **A working visualisation** of the published decomposition, running live in a browser on any uploaded structure.
- **A correct periodic block graph.** All four test structures reproduce published coordination numbers, including UiO-66 at 12 where a naive construction gives 6.
- **A real finding about influence:** in a defect-free crystal, influence cannot be ranked, because every node is symmetry-equivalent and "top-k by degree" is a tie. Introducing a defect makes it measurable — λ₂ falls 1.44 → 1.19 for a single missing linker in HKUST-1.
- **A correctly computed multifractal spectrum.** All 77 frameworks give proper inverted parabolas peaking at `q = 0`.
- **A tight, well-defined band** across 77 frameworks: Δα interquartile 1.11 – 1.25, with the asymmetry negative in every single one.

### 5.2 · Not achieved — and why that is the result


The band exists, but it cannot yet be read as a chemical statement. Testing it against published pore diameters shows the correlation is confounded by graph size:

| Test | Correlation with Δα |
|---|---|
| pore diameter (LCD), raw | −0.497 |
| pore diameter, **controlling for graph size** | **+0.101** — vanishes |
| graph size, **controlling for pore diameter** | **+0.621** — survives |
| R² added by pore diameter over graph size alone | **+0.005** |


Δα is mostly tracking **how many atoms are in the supercell**, which is set by `MIN_CELL_LENGTH` and the `MAX_ATOMS` cap — computational parameters, not chemistry.


> **Why reporting this is the stronger position**
>
> A band built on an uncontrolled size effect would not survive the first person who checked it. Identifying the confound, quantifying it, and stating exactly what would remove it is a more defensible outcome than a correlation presented without that test.
>
> **Two concrete next steps, neither of them open research:** compare only frameworks at comparable graph size so the confound is held fixed; or normalise the fit window per structure so Δα stops growing with the graph, then re-test the correlation.
