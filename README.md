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
implemented the method from **Xiao et al., Scientific Reports 11, 22964 (2021)**.

Every framework gets a curve, `f(α)`, describing how unevenly its connectivity is spread
out. The **width of that curve, Δα**, is a single number for how structurally
heterogeneous the pore network is. Plot several MOFs' curves together, and if a group of
them overlaps, the shaded region they trace out is a **band**. A new MOF whose curve
falls inside the band belongs to that group.

A teammate extended this to **8 real frameworks downloaded live** from the RASPA2
structure library, on full atomic graphs of 3,400–6,100 atoms:

| Framework | Metal | Δα | Group |
|---|---|---|---|
| Co-MOF-74 | Co | 0.941 ± 0.054 | in the band |
| ZIF-8 | Zn | 0.897 ± 0.077 | in the band |
| Mg-MOF-74 | Mg | 0.857 ± 0.070 | in the band |
| Zn-MOF-74 | Zn | 0.857 ± 0.070 | in the band |
| HKUST-1 | Cu | 0.844 ± 0.063 | in the band |
| Ni-MOF-74 | Ni | 0.835 ± 0.057 | in the band |
| **IRMOF-1 (MOF-5)** | Zn | **0.375 ± 0.064** | **outside** |
| **UMCM-1** | Zn | **0.203 ± 0.028** | **outside** |

**What this shows:** six frameworks with completely different metals (Cu, Ni, Co, Mg, Zn)
and different chemistry (carboxylate vs imidazolate) land in the same band, while two
others separate cleanly. The grouping is by **pore-network architecture**, and it cuts
across metal and chemistry. The gap between the groups is **0.46**, about **four times**
the noise floor — so the split is a property of the frameworks, not of the method.

**Two different things get called "the band" — only one of them works:**

| Version | What it is | Does it work? |
|---|---|---|
| **Δα band** (1-D) | The range of spectrum *widths* the group spans | ✅ **Yes.** Holding out each framework and re-testing classifies all of them correctly |
| **f(α) envelope** (2-D) | Shade between the highest and lowest curve, ask if a candidate falls inside | ❌ **No.** Held out, HKUST-1 (a real member) scores 9.4% while UMCM-1 (a non-member) scores **15.4%** |

The envelope fails because the two narrow curves are short arcs sitting *inside* the wide
group's α range but far below it in f(α) — so the test is dominated by where a curve sits
in α, not by how wide it is. **We report this as a measured negative result** rather than
quoting the envelope as though it worked. You can reproduce it yourself with the "hold
out" buttons in Section 15b of the website.

**What this does *not* show — and this matters when presenting:**

- The four MOF-74 analogues overlapping is *not* evidence. They are the same graph
  (proved isomorphic), so they must overlap. They are the **reproducibility control**.
- That control measures a noise floor of **0.106**. HKUST-1 (0.844) and ZIF-8 (0.897) sit
  *inside* the range that identical structures already span, so the honest statement is
  "six frameworks are indistinguishable within noise", not "six frameworks match".
- **Δα is not a stability or gas-uptake predictor.** Nothing here measures stability. The
  graph is unweighted — it does not even know which element an atom is. Δα describes
  architecture only.
- Δα is **finite-size dependent** — it grows with graph size, so only comparisons at
  similar graph size are meaningful. The ranking survives because the bias runs the *wrong
  way*: the two narrowest spectra come from the two *largest* graphs.

**Two versions of "the band" exist, and only one works.** Everything is tested by holding
a framework out and rebuilding the band without it:

| Version | Result |
|---|---|
| **Δα band** (spectrum width) | ✅ classifies **8/8 correctly** |
| **f(α) envelope** (whole curve) | ❌ **fails** — held out, ZIF-8 (a member) scores 0.0% while UMCM-1 (a non-member) scores 44.7% |

We report the envelope failure as a measured negative result rather than quoting it as
though it worked.

**Where:** `3_notebooks/mof_band_analysis.ipynb` (the band, with saved outputs),
`2_python/code_10`, `code_11`, Sections 14–15b of the website

---

## 4 · The headline results, in one place

| # | Finding | Evidence |
|---|---|---|
| 1 | The published algorithm reports chemically incomplete nodes | +12 / +36 / +18 atoms recovered on three structures; ZIF-8 correctly unchanged |
| 2 | The block network must be built **periodically** | UiO-66 reports 12-connected (correct) vs 6 (naive). All four structures match published crystallography |
| 3 | Influence cannot be ranked inside a perfect crystal | Only 2 distinct degree values in every structure — a top-k list is sorting ties |
| 4 | Defects make influence measurable | Remove 1 linker: 2 → 4 distinct centralities, λ₂ 1.44 → 1.19 |
| 5 | Frameworks group by pore architecture, not by metal | 6 of 8 frameworks share a band across 5 different metals; 2 separate cleanly |
| 6 | Two estimator bugs found and fixed | Edgeless-subgraph defect, and the log-space averaging bug (found independently by two people on two datasets) |

**What we have NOT established:** "all Zr-MOFs fall in one band." We have one Zr
structure. That is a demonstration of mechanism, not a result. It needs a few hundred
MOFs grouped by metal (CoRE MOF / QMOF). Every module runs per-CIF, so scaling up is a
loop — but it has not been done.

---

## 5 · Where everything lives

```
1_website/     ← START HERE. Open index.html. One page, everything, interactive.
2_python/      One runnable module per pipeline stage
3_notebooks/   Notebooks -- start with mof_band_analysis.ipynb (Colab, Run All)
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
