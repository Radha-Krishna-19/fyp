# MOF Building-Block Analysis — Final Year Project

> **Read this page first.** It explains what the project is, why each part exists,
> and what we found. Everything else is detail.

---

## 1 · The one-paragraph version

Metal–organic frameworks (MOFs) are sponge-like crystals built by joining metal clusters
to organic molecules. To design them, you first have to be able to look at a crystal
structure and say *what it is made of*. The software the field uses to do that
automatically has a flaw: it reports metal clusters with their chemistry stripped off.
**We found the flaw, measured it, fixed it, and then analysed the resulting framework
networks to see whether MOFs can be grouped by their structure alone.**

---

## 2 · Why this matters at all

A MOF is two things repeated forever on a lattice:

- a **node** — a small metal cluster (the joint)
- a **linker** — a rigid organic molecule (the strut)

Change the node or the linker and you get a different material with different properties.
So *node identity and linker identity are the design variables of the entire field.*

Databases of 100,000+ MOFs are annotated by running a decomposition algorithm
automatically over every structure. If that algorithm is systematically wrong, **every
entry in those databases inherits the same error**, and every model trained on them
learns it too. That is the problem we set out to work on.

---

## 3 · What we actually did — the four parts

### Part 1 — Reproduce the published algorithm honestly

We took the decomposition pipeline from **MOFid** (Snurr group, Northwestern — the
standard tool) and translated all of it from C++ into readable, runnable Python, one
module per stage. No shortcuts, no "close enough": each module cites the upstream source
file it came from.

**Why:** you cannot credibly criticise an algorithm you have not reproduced. This gives
us a baseline that is unarguably *their* algorithm, not our paraphrase of it.

**Where:** `2_python/code_01` … `code_07`

---

### Part 2 — Find and fix what is wrong with it

The published rule is: **cut every bond that touches a metal atom; whatever stays
connected is a building block.** It is fast, deterministic, and never crashes — which is
exactly why it became the default.

The problem: the carboxylate group (`–COO⁻`), which is how most linkers actually bind
metals, has *both* its oxygens bonded to metal. So the rule cuts them both, and the whole
group gets pushed onto the linker side. The node that gets reported is the real cluster
with its binding chemistry amputated.

| Structure | What the published algorithm reports | What the node chemically is | Missing |
|---|---|---|---|
| HKUST-1 | `Cu2` | Cu₂(COO)₄ paddlewheel | **12 atoms** |
| UiO-66 | `Zr6 O8 H4` | Zr₆O₄(OH)₄(COO)₁₂ | **36 atoms** |
| MOF-5 | `Zn4 O` | Zn₄O(COO)₆ | **18 atoms** |
| ZIF-8 | `Zn` | single Zn²⁺ | nothing — it is correct |

The ZIF-8 row is the control that proves the fix is chemically targeted: ZIF-8 binds
through nitrogen, has no carboxylate, and our fix correctly leaves it alone.

**We proposed four fixes**, each independently switchable so its effect can be measured
separately. Critically, they change *what the blocks contain*, not *which blocks connect
to which* — so every published coordination number and topology still comes out correct
after the fix.

**Where:** `2_python/code_08_proposed_fixes.py`, and Sections 7–8 of the website

---

### Part 3 — Analyse the framework as a network

Our supervisor asked us to go further: **"highlight the influential nodes, find the
spectrum, and deduce something like *all zirconium MOFs fall under this spectrum*."**

Once a MOF is decomposed, the framework *is* a graph — blocks are dots, bonds between
them are lines. That let us ask which blocks matter most.

**What we found was not what we expected.** In a perfect crystal there are only **two**
distinct connection counts — one for all nodes, one for all linkers — because every metal
cluster is related to every other by symmetry. They are genuinely identical. So:

> **"Which node is most influential?" is an ill-posed question for a perfect crystal.**
> A "top 10 most influential" list is just the first 10 entries of a tie.

That is a real, defensible finding, not a failure. And it points at the fix: **break the
symmetry**. Remove a single linker (a real, well-documented MOF defect) and influence
becomes measurable — HKUST-1 goes from 2 to 4 distinct centrality values, and its
algebraic connectivity λ₂ falls 1.44 → 1.19, quantifying how much that one missing linker
weakened the framework.

**Where:** `2_python/code_09_network_analysis.py`, Sections 10–12 of the website

---

### Part 4 — The multifractal spectrum, and the "band"

The last part of the brief was to find a *spectrum* that groups MOFs into families. We
implemented the method from **Xiao et al., Scientific Reports 11, 22964 (2021)**, and scaled
it to **77 frameworks** from MOFX-DB with published pore diameters.

> **Know what this dataset is.** The 77 are all named `hMOF-###` — they come from the
> **hypothetical MOF** database: computer-generated candidate structures, **not** materials
> anyone has synthesised. The notebook *requested* CoRE MOF 2019 (which is experimental) but
> the server returned hMOF records, and nothing checked. It does now. Two consequences:
> nothing here may be described as "experimental", and since **every one of the 77 has a
> Zn₄O node**, this set cannot support any claim about behaviour across different metals.

Each framework gets a curve `f(α)`. The **width of that curve, Δα**, is one number for how
unevenly connectivity is distributed. A **band** is the range of Δα a group shares, so a new
framework can be tested for membership. Across the 77, the interquartile band is
**Δα = 0.36 – 0.65**.

Scaling up exposed two errors in our own implementation, and forced one claim to be withdrawn.

**Error 1 — the spectrum had the wrong shape.** A multifractal spectrum must be an
**inverted parabola** peaking at `q = 0`, where `f(α₀) = D₀`. Ours sloped downhill. The paper
defines `τ(q) = ln 𝒫_q(r) / ln(r/r_N)` — a fit **through the origin**. Our code took a
**free-intercept slope**. At `q = 0` every term is `pr_i⁰ = 1`, so `𝒫₀ = |I|` is the same at
every radius; a flat line has slope zero, forcing `τ(0) = 0` and `f(α₀) = 0` — deleting the
peak. Measured: τ(0) = 0 in **all 77** frameworks, none peaked at q = 0. Fixed; Python and the
browser engine now agree at τ(0) = −2.6551 on HKUST-1, with the peak exactly at q = 0.

**Error 2 — the averaging order.** The partition function must be built per box-covering trial
and averaged in log space, not averaged first and then raised to the power q. Measured on
HKUST-1: 0.021 ± 0.004 (wrong) vs 0.327 ± 0.032 (correct).

**Withdrawn — "the band groups MOFs by pore architecture."**

| Test | r |
|---|---|
| Δα vs pore diameter (LCD), raw | −0.330 |
| Δα vs LCD, **controlling for graph size** | **+0.057** — vanishes |
| Δα vs graph size, **controlling for LCD** | **+0.384** — survives |

In a linear model, graph size alone gives R² = 0.237; adding pore diameter takes it to 0.240
— pore size buys **+0.002**. So Δα is tracking **how many atoms are in the supercell**, which
is set by `MIN_CELL_LENGTH` and the `MAX_ATOMS` cap — computational parameters, not chemistry.

On 8 frameworks the pore reading was plausible. On 77 it is not supported. Two routes make the
question answerable: compare only frameworks of **comparable graph size**, or **normalise the
fit window** so Δα stops growing with the graph, then re-test.

**Where:** `3_notebooks/mof_band_analysis.ipynb`, `2_python/code_10`, `code_11`,
Section 15b of the website

---

## 4 · The headline results, in one place

| # | Finding | Evidence |
|---|---|---|
| 1 | The published algorithm reports chemically incomplete nodes | +12 / +36 / +18 atoms recovered on three structures; ZIF-8 correctly unchanged |
| 2 | The block network must be built **periodically** | UiO-66 reports 12-connected (correct) vs 6 (naive). All four structures match published crystallography |
| 3 | Influence cannot be ranked inside a perfect crystal | Only 2 distinct degree values in every structure — a top-k list is sorting ties |
| 4 | Defects make influence measurable | Remove 1 linker: 2 → 4 distinct centralities, λ₂ 1.44 → 1.19 |
| 5 | A Δα band exists across 77 frameworks | Interquartile Δα = 0.36–0.65 |
| 6 | **That band does not mean pore architecture** | Pore correlation vanishes (−0.33 → +0.06) once graph size is controlled for; size survives (+0.38). Claim withdrawn. |
| 7 | Three estimator bugs found and fixed | Edgeless subgraph; log-space averaging order; and τ(q) fitted with a free intercept instead of through the origin, which had deleted the peak of every spectrum |

**What we have NOT established:** that the band carries physical meaning. It is currently a
descriptive range whose main driver is supercell size. The metal-family claim ("all Zr-MOFs
fall in one band") is also unestablished — it needs many MOFs *per metal* at matched graph
size. Every module runs per-CIF, so scaling up is a loop; controlling the size confound is
the real work.

---

## 5 · Where everything lives

```
1_website/     ← START HERE. Open index.html. One page, everything, interactive.
2_python/      One runnable module per pipeline stage
3_notebooks/   mof_band_analysis.ipynb -- the band (Colab, Run All)
4_reference/   Figures
5_concepts/    Five deep-dive documents — read these to actually understand the work
PRESENTATION_SCRIPT.md   The full talk, start to finish
```

### The website is the main deliverable

`1_website/index.html` — **just double-click it.** No server, no install. Sixteen
sections covering the whole project, with live 3D models, the real algorithm running in
your browser on any structure you upload, and every source file readable by clicking its
name anywhere on the page.

> **Before presenting:** save
> <https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js>
> into `1_website/` as exactly `three.min.js`, or the 3D panels will be blank without
> internet.

### `5_concepts/` — read in this order

| # | Document | Covers |
|---|---|---|
| 1 | [Fundamentals](5_concepts/01_MOF_and_Crystallography_Fundamentals.md) | What a MOF is, the CIF format, why bonds must be inferred, coordination number |
| 2 | [The Published Algorithm](5_concepts/02_The_Published_Decomposition_Algorithm.md) | MOFid stage by stage, and the metal-oxo rule |
| 3 | [Drawbacks and Fixes](5_concepts/03_Drawbacks_and_the_Proposed_Fixes.md) | The four limitations, evidence, fixes, measured effect |
| 4 | [Network and Spectrum](5_concepts/04_Network_and_Multifractal_Analysis.md) | Influential nodes, the Laplacian, the multifractal spectrum, the band |
| 5 | [The Website](5_concepts/05_The_Website_What_and_Why.md) | Why it exists, what all 16 sections do, what to demo live |

---

## 6 · Running the code

```bash
cd 2_python
python3 code_00_pipeline_driver.py HKUST-1.cif   # the full published pipeline
python3 code_08_proposed_fixes.py                # before/after our fixes
python3 code_09_network_analysis.py              # coordination, centrality, Laplacian
python3 code_10_multifractal_spectrum.py         # iNMFA spectrum + band test
python3 code_11_nmfa_paper.py                    # NMFA exactly as published
```

Needs `numpy`, `networkx`, `matplotlib`. The notebooks in `3_notebooks/` need nothing —
the structures are embedded inside them, so they run in Colab with Run All.

### Module map

| File | Stage |
|---|---|
| `code_01_cif_input.py` | Read the CIF — no bonds exist yet |
| `code_02_bond_assignment_pbc.py` | Infer bonds, periodic minimum-image search |
| `code_03_element_classification.py` | `is_metal()` |
| `code_04a/b/c` | metal-oxo · single-node · all-node splitting |
| `code_05_centroid_simplification.py` | Collapse each block to a point |
| `code_06_systre_topology_export.py` | Write a real `.cgd` for Systre |
| `code_07a/07b` | MOFid / MOFkey assembly |
| **`code_08_proposed_fixes.py`** | **our four fixes to the published algorithm** |
| **`code_09_network_analysis.py`** | **periodic graph, centrality, Laplacian spectrum** |
| **`code_10_multifractal_spectrum.py`** | **iNMFA, reference band, candidate test** |
| **`code_11_nmfa_paper.py`** | **NMFA exactly as published — box-growing** |

Modules 01–07 are faithful translations of published work. **08–11 are ours.**

---

## 7 · Honest limitations

Stating these up front is deliberate — they are the questions a examiner will ask.

- **Systre is not reimplemented.** We write a genuine `.cgd` input file, but the topology
  tool itself is external. Quoted RCSR net names are the published ones.
- **InChIKeys are placeholders** in `code_07b` — real InChI needs a chemistry library.
  Nothing downstream uses them.
- **The donor-agnostic fix has zero measured effect on our four structures**, because
  none has a bridging non-oxygen donor. Its justification is generality, not these results.
- **Rod SBUs are detected, not handled.**
- **One Zr structure**, so no metal-family claim.
- **Δα is finite-size dependent** and is not a stability or uptake predictor.
- **Nothing here is an adsorption calculation.** No gas uptake is computed anywhere.

---

## 8 · Sources

- Decomposition algorithm: [`snurr-group/mofid`](https://github.com/snurr-group/mofid) (Northwestern)
- Multifractal method: Xiao et al., *"Deciphering the generating rules and functionalities
  of complex networks"*, **Scientific Reports 11, 22964 (2021)** —
  <https://www.nature.com/articles/s41598-021-02203-4>
- Structures for the 8-MOF band: [RASPA2 structure library](https://github.com/numat/RASPA2/tree/master/structures/mofs/cif)
