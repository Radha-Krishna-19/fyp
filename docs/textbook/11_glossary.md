# Chapter 11 — Glossary

*Every term used anywhere in the project, in one place. Alphabetical within groups.*

---

## Chemistry & crystallography

| Term | Meaning |
|---|---|
| **Ångström (Å)** | 10⁻¹⁰ m. The natural unit for interatomic distances; a C–C bond is ~1.5 Å |
| **Bond perception** | Inferring which atoms are bonded from distance, because CIF files do not store bonds |
| **Carboxylate** | `–COO⁻`. The most common group by which an organic linker grabs a metal cluster |
| **CIF** | Crystallographic Information File. Stores cell + atom positions + symmetry. **Never bonds** |
| **Coordination number (c.n.)** | How many linkers a metal node connects to |
| **Covalent radius** | Tabulated per-element size; two radii summed give the bond-length cutoff |
| **Defect** | A departure from the ideal repeating pattern. Here: a **missing linker** |
| **Fractional coordinates** | Position as a fraction (0–1) along each cell edge |
| **hMOF** | Hypothetical MOF database — computer-generated candidates, never synthesised |
| **CoRE MOF** | A database of experimentally-reported, computation-ready structures |
| **LCD** | Largest cavity diameter — the biggest sphere that fits inside a pore |
| **Linker** | The organic molecule; the *strut* of the framework |
| **Minimum-image convention** | Measuring distance to the nearest periodic copy, over 27 cell images |
| **MOF** | Metal–organic framework — a porous crystal of metal clusters joined by organic molecules |
| **MOFid / MOFkey** | Identifier strings summarising composition and topology |
| **Net** | The abstract repeating pattern a framework follows (`tbo`, `pcu`, `sod`, `fcu`) |
| **Node** *(chemistry)* | The metal cluster; the *joint* of the framework |
| **PBC** | Periodic boundary conditions — treating the unit cell as repeating forever |
| **PLD** | Pore limiting diameter — the narrowest constriction along a pore channel |
| **Pore network** | The connected empty space inside the framework; what gas moves through |
| **RCSR** | Reticular Chemistry Structure Resource — the database of net names |
| **Reticular chemistry** | Designing frameworks by choosing node and linker geometry |
| **SBU** | Secondary building unit — another name for the node |
| **Systre** | External tool that identifies a net from a periodic graph |
| **Unit cell** | The small repeating box a CIF stores |

---

## Graph theory

| Term | Meaning |
|---|---|
| **Adjacency matrix (A)** | Matrix recording which vertices are joined |
| **Algebraic connectivity** | See **λ₂** |
| **Betweenness centrality** | How many shortest paths pass *through* a vertex |
| **Centrality** | Any measure of how structurally important a vertex is |
| **Connected component** | A group of vertices all reachable from each other |
| **Degree** | How many edges touch a vertex. **In this project, = the coordination number** |
| **Diameter** | The largest number of steps between any two vertices |
| **Edge** | A connection between two vertices; here, a bond between two blocks |
| **Eigenvector centrality** | Importance by association — you matter if your neighbours matter |
| **Labelled quotient graph** | A finite graph whose edges carry lattice translations; represents an infinite crystal exactly |
| **Laplacian (L = D − A)** | Matrix built from the graph; its eigenvalues describe connectivity |
| **λ₂ (lambda-two)** | Second-smallest Laplacian eigenvalue. **How hard the network is to cut in two** |
| **Naive graph** | A graph built by discarding lattice translations. **Wrong for crystals** |
| **Star graph** | One hub joined to everything, all else degree 1. The signature of a broken construction |
| **Supercell** | n×n×n copies of the unit cell, stacked, to give a bigger graph |
| **Translation (t)** | Three integers recording which copy of the cell an edge reaches |
| **Vertex** *(graph theory)* | A dot in the graph; here, one building block |

> ⚠ **"Node" is ambiguous.** In graph theory it means *vertex*; in MOF chemistry it means *the
> metal cluster*. This textbook uses **vertex** for the graph sense.

---

## Multifractal analysis

| Term | Meaning |
|---|---|
| **α (alpha)** | Local scaling exponent — how fast the network grows around **one** block |
| **α₀ (alpha-zero)** | The α at the peak of f(α); the **typical** dimension of the framework |
| **A (asymmetry)** | `ln[(α₀−α_min)/(α_max−α₀)]` — which side of the spectrum dominates |
| **Box covering** | Tiling the network with randomly-seeded boxes. **Stochastic** |
| **Box growing** | Centring a ball on a block and growing *r*. **Deterministic** |
| **D₀** | The fractal (box) dimension. Equals `f(α₀)`, the **peak** of the spectrum |
| **D(q)** | Generalised dimension, `τ(q)/q` |
| **Δα (delta-alpha)** | Spectrum **width**. How varied the framework's pore network is |
| **f(α)** | How much of the framework shares a given local dimension α |
| **iNMFA** | Influential-node multifractal analysis — the measure restricted to the top 10% by degree |
| **Legendre transform** | The step converting τ(q) into α and f(α) |
| **M_i(r)** | Number of vertices within *r* steps of block *i* |
| **Multifractal** | Having *many* local dimensions rather than one |
| **NMFA** | Node-based multifractal analysis — over all nodes, not just influential ones |
| **p_i(r)** | `M_i(r)/N` — the normalised measure |
| **𝒫_q(r)** | Partition function, `Σ p_i(r)^q` |
| **q** | Distortion exponent; a zoom control between dense (q>0) and sparse (q<0) regions |
| **r_N** | Network radius (diameter), used to make the box radius dimensionless |
| **τ(q) (tau)** | Mass exponent, `ln 𝒫_q(r) / ln(r/r_N)`. **A ratio — a fit through the origin** |

---

## Statistics

| Term | Meaning |
|---|---|
| **Confound** | A third variable driving an apparent relationship between two others |
| **Correlation (r)** | −1 to +1. How linearly two quantities move together |
| **Partial correlation** | Correlation between two variables **with a third held fixed**. The tool that exposed our confound |
| **R²** | Fraction of variance a model explains, 0 to 1 |

---

## Project-specific

| Term | Meaning |
|---|---|
| **The band** | The range of Δα shared by a group of frameworks |
| **Metal-oxo algorithm** | The default MOFid split: cut every metal-containing bond |
| **Single-node / all-node** | The two alternative MOFid splits |
| **`tau_mode`** | Our switch: `"paper"` (through the origin, correct) vs `"slope"` (free intercept, the old bug) |
| **`MIN_CELL_LENGTH` / `MAX_ATOMS`** | Config parameters setting supercell size. **The source of the size confound** |
| **`WINDOW_FRAC`** | Fit τ(q) over `r ≤ 0.34 × diameter`, to stay inside the scaling region |

---

## The numbers worth memorising

| Fact | Value |
|---|---|
| Structures analysed | **77** |
| Spectra with the correct shape | **77 / 77** |
| The band (interquartile Δα) | **1.112 – 1.250** |
| UiO-66 coordination: naive / correct / published | **1 / 12 / 12** |
| Distinct degree values in a perfect crystal | **2** |
| λ₂ on removing one linker (HKUST-1, unit cell) | **1.438 → 1.186 (−18%)** |
| Δα vs pore size — raw, then controlling for graph size | **−0.497 → +0.101** |
| Δα vs graph size, controlling for pore size | **+0.621** |
| R² added by pore size over graph size alone | **+0.005** |
| τ(0) before / after the fix | **0.0000 / −2.5669** |
| Python ↔ JavaScript agreement (τ(0), HKUST-1) | **−2.6551 in both** |

---

**Back to:** [the index](README.md)
