# Structural Descriptors for Metal–Organic Frameworks

**Can a descriptor computed from connectivity alone — in seconds, with no
molecular simulation — carry enough structural information to group metal–organic
frameworks usefully?**

23CSE498 Final Year Project · Phase II · Research-based
Amrita Vishwa Vidyapeetham, School of Computing, Coimbatore

**Guide:** Dr. T. Ramraj, Assistant Professor (Sl. Gd.), Department of Computer
Science and Engineering · M.E., Ph.D.

| | |
|---|---|
| **Project site** | [`1_website/index.html`](1_website/index.html) — open it directly, no server needed |
| **Dataset** | [`9_dataset/`](9_dataset/) — 81 frameworks, CC BY 4.0 |
| **Panel deck** | [`7_presentation/panel_review.pdf`](7_presentation/panel_review.pdf) |
| **Textbook** | [`8_textbook/`](8_textbook/) — 12 chapters, zero background assumed |

---

## The problem in one paragraph

A metal–organic framework is a crystal built from metal clusters ("nodes")
joined by organic struts ("linkers"). Change the parts and you change the pore
network, and with it everything useful — surface area, gas capacity, stability,
catalytic behaviour. Hundreds of thousands of candidate structures exist on
paper. Deciding whether one is worth making means running a molecular simulation
that takes **hours per structure**. At that rate the candidate space cannot be
searched, only sampled.

So we ask a narrower question that can actually be answered: build the
framework's **periodic graph** from its crystal structure, compute the
**multifractal spectrum** of that graph, and reduce each framework to three
numbers. Does that compression retain anything real?

## What we found

**A band exists.** Across 77 frameworks, the spectrum width Δα falls in
**1.11 – 1.25** (interquartile range). All 77 spectra are mathematically valid.

**One claim was withdrawn.** Δα correlates with pore diameter at *r* = −0.497,
which looked like a result. Controlling for the number of blocks in the graph
collapses it to **+0.101**, while graph size survives at +0.621, and adding pore
size to a size-only model improves R² by **0.005**. The descriptor was largely
measuring how big the graph was. We removed the claim from the project rather
than reporting it.

**Synthesised frameworks sit outside the band.** Size-matched under the same
supercell rule, four real MOFs span Δα = 1.66 – 2.26 — clear of the hypothetical
range with a gap of 0.25, and not explained by graph size or by metal. Four
archetypal structures are not a sample; the run that would settle it is
[`3_notebooks/real_mof_band.ipynb`](3_notebooks/real_mof_band.ipynb).

## Three defects we found and fixed

These are the substance of the work, and each was a silent wrong answer rather
than a crash.

| # | Defect | Consequence | Fix |
|---|---|---|---|
| 1 | τ(q) fitted with a free intercept instead of through the origin | **Every one of the 77 spectra had no apex.** Mathematically invalid, but each individual curve looked plausible | Fit τ = ln 𝒫_q / ln(r/r_N) through the origin. 0/77 → **77/77** valid |
| 2 | Spectrum computed on the induced subgraph of influential nodes only | In a MOF the high-degree blocks are metal clusters, and metal clusters never bond to each other — they connect *through* linkers. That subgraph has **zero edges**, so no distances exist | Box-cover the full block graph; read the measure only *at* the influential nodes |
| 3 | Averaging in the wrong order — mean of ln Z instead of ln of mean Z | Jensen's inequality makes this biased, not noisy. HKUST-1: 0.021 → **0.327** | Exponentiate per trial, then average |

A fourth is a data-provenance defect: the analysis requested CoRE MOF 2019 and
received hMOF records, because on that endpoint `database=` is advisory and
loses to the `gases[]` filter. Every quantitative result in the project was
computed on hypothetical structures as a result. A provenance check caught it;
the query now filters each returned record on its own `database` field.

---

## Repository layout

```
metal_oxo_deep_dive/
├── 1_website/        The documentation portal. Open index.html — no server needed.
├── 2_python/         Reference implementation, 12 annotated modules
├── 3_notebooks/      The 77-framework analysis + the real-MOF twin
├── 4_reference/      Generated figures
├── 5_concepts/       Five long-form background documents
├── 6_references/     Annotated bibliography + BibTeX
├── 7_presentation/   Beamer deck, PDF, Overleaf archive, speaking script, 5-way split
├── 8_textbook/       Twelve chapters, zero background assumed
└── 9_dataset/        The released dataset, CC BY 4.0
```

## Getting started

### Read the site — no installation

```bash
git clone https://github.com/Radha-Krishna-19/fyp.git
cd fyp/metal_oxo_deep_dive/1_website
# open index.html in any browser
```

Every asset is relative and `three.min.js` is vendored into the repository, so
this works from a `file://` URL with **no web server and no internet
connection**. Every number is computed in your browser at page load from the CIF
files in the folder; none is hardcoded.

### Run the pipeline

Requires Python 3.9+ and NumPy. Nothing else.

```bash
cd metal_oxo_deep_dive/2_python
pip install numpy

# decompose one framework end to end
python code_00_pipeline_driver.py HKUST-1.cif

# its multifractal spectrum
python code_10_multifractal_spectrum.py

# against the published method
python code_11_nmfa_paper.py
```

### Reproduce the 77-framework band

```bash
jupyter notebook 3_notebooks/mof_band_analysis.ipynb
```

Also runs unchanged in Google Colab; it installs its own dependencies. Writes
`results.json`, which `1_website/band_data.js` is generated from. Roughly 20
minutes.

### Run the tests

```bash
cd metal_oxo_deep_dive/1_website/tests
npm install jsdom
npm test
```

Five suites, 200+ assertions. They boot the real pages headlessly and assert on
**computed output**, because this site's failure mode is a silently blank panel
rather than a visible error.

---

## Architecture

Eight modules, each independently runnable and independently testable. Modules
1–4 are a faithful translation of the published `snurr-group/mofid` metal-oxo
decomposition, used **unmodified**. Modules 5–8 are this project's work.

```
  CIF ──▶ bond perception ──▶ metal-oxo split ──▶ quotient graph
          (27 images,          (nodes and         (edges carry the
           covalent radii)      linkers)           lattice translation)
                                                          │
                                                          ▼
   Δα, α₀, A  ◀── spectrum ◀── box growing ◀── supercell expansion
                  τ(q) → f(α)   (influential      (past 48 Å per
                                 nodes)            lattice direction)
```

**Two independent implementations.** The Python modules and the JavaScript
engine were written from the same specification but not from each other. Where
they disagree, one is wrong — and that disagreement is loud, whereas a single
implementation is silently self-consistent even when it is wrong. Two of the
three defects above were caught exactly this way.

## Implementation status

| Module | State | Weight | Credit |
|---|---|---|---|
| CIF ingestion and symmetry expansion | Complete | 10% | 10% |
| Periodic bond perception | Complete | 10% | 10% |
| Metal-oxo decomposition | Complete | 15% | 15% |
| Quotient graph + supercell expansion | Complete | 15% | 15% |
| Box growing and the multifractal spectrum | Complete | 15% | 15% |
| Descriptor extraction and band construction | Complete | 10% | 10% |
| Confound analysis and hold-out validation | Complete | 10% | 10% |
| Validation on synthesised structures at scale | Not started | 10% | 0% |
| Cross-family separation (multiple metals) | Not started | 5% | 0% |
| **Total** | | **100%** | **85%** |

Seven of nine modules complete and integrated. The two outstanding are both
external validation, not core function — a data task rather than a development
task.

---

## What this project does *not* claim

Stated plainly, because a reviewer will ask.

- **Δα does not predict gas uptake.** Nothing here computes adsorption.
- **The main dataset is not experimental.** All 77 are hypothetical, generated
  structures. Any sentence calling them experimental is false.
- **No cross-family claim.** All 77 share one metal (Zn₄O), so the band is a band
  *within* one family.
- **The graph is unweighted and untyped.** Bond order and element identity are
  discarded by design. What survives is pure architecture.
- **This does not replace simulation.** It is a pre-filter for deciding *what* to
  simulate.

## Team

| Member | Roll number | Owns |
|---|---|---|
| P. M. Radha Krishna | CB.SC.U4CSE23134 | Problem framing, methodology, integration, documentation portal |
| P. Kshitij Varma | CB.SC.U4CSE23122 | The mathematical model — partition function, τ(q), Legendre transform |
| G. Rohith Abhinav | CB.SC.U4CSE23141 | Implementation status, 3D viewer, decomposition engine |
| J. Keerthi Sree | — | Results, validation, the band, dataset provenance |
| Isha | — | Design decisions, the τ defect, network construction, roadmap |

## Built on

- Xiao *et al.*, *Scientific Reports* **11**, 22964 (2021) — the multifractal method
- Bucior *et al.*, *CrystEngComm* **21**, 3777 (2019) — MOFid decomposition
- Wilmer *et al.*, *Nature Chemistry* **4**, 83 (2012) — the hMOF structures

Full annotated bibliography in [`6_references/`](6_references/).

## Licence

Dataset: CC BY 4.0 ([`9_dataset/LICENSE`](9_dataset/LICENSE)).
`three.min.js` is vendored under the MIT licence of the three.js project.
