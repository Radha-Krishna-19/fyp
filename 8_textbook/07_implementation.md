# Chapter 7 — What We Built

*The code, the platform and the testing. All counts below are real.*

---

## 7.1 · Overview

Three deliverables:

1. **A reference implementation in Python** — 14 modules, 2,681 lines, one per pipeline stage.
2. **A browser implementation in JavaScript** — the same logic, so the whole pipeline runs
   live in a web page with no server.
3. **An interactive platform** — an 18-section technical site built on top of both.

Plus **8 automated test suites** and a **29-cell notebook** for the 77-framework study.

---

## 7.2 · The Python reference implementation

`2_python/` — one module per stage, each runnable standalone, each citing the upstream source
it implements.

| Module | Lines | What it does |
|---|---|---|
| `code_00_pipeline_driver.py` | 76 | Runs the whole chain on one CIF |
| `code_01_cif_input.py` | 244 | Parse CIF, build the cell matrix, expand symmetry |
| `code_02_bond_assignment_pbc.py` | 168 | Bond perception over 27 periodic images |
| `code_03_element_classification.py` | 94 | `is_metal()` — the exclusion list |
| `code_04a_metal_oxo_algorithm.py` | 173 | **The default split** |
| `code_04b_single_node_algorithm.py` | 137 | Alternative split — carboxylate stays with metal |
| `code_04c_all_node_algorithm.py` | 118 | Alternative split — also splits linkers |
| `code_05_centroid_simplification.py` | 143 | Collapse each block to a point (PBC-aware) |
| `code_06_systre_topology_export.py` | 119 | Write a genuine `.cgd` for Systre |
| `code_07a_mofid_assembly.py` | 180 | MOFid identifier string |
| `code_07b_mofkey_assembly.py` | 113 | MOFkey (with a flagged placeholder InChIKey) |
| **`code_09_network_analysis.py`** | **264** | **Quotient graph, centrality, Laplacian** |
| **`code_10_multifractal_spectrum.py`** | **595** | **iNMFA, box covering, the band** |
| **`code_11_nmfa_paper.py`** | **257** | **NMFA exactly as published — box growing** |

**Modules 01–07 are faithful translations of published work, used unmodified.**
**Modules 09–11 are this project's own analysis code.**

Running any of them:

```bash
cd 2_python
python3 code_00_pipeline_driver.py HKUST-1.cif   # the full published pipeline
python3 code_09_network_analysis.py              # coordination, centrality, Laplacian
python3 code_10_multifractal_spectrum.py         # the spectrum and the band
python3 code_11_nmfa_paper.py                    # box-growing NMFA
```

Requires `numpy`, `networkx`, `matplotlib`.

---

## 7.3 · The browser implementation

`1_website/` — 15 JavaScript modules (~5,000 lines excluding embedded data).

| Module | Lines | Responsibility |
|---|---|---|
| `mof_decompose.js` | 937 | CIF parsing, PBC bonding, all three decomposition algorithms |
| `pipeline_walkthrough.js` | 1054 | The step-by-step pipeline walkthrough |
| `network_page.js` | 679 | Graph construction, centrality tables, defect simulation |
| `mof_render.js` | 519 | Three.js 3D rendering, with context-loss recovery |
| `mof_multifractal.js` | 410 | iNMFA and NMFA in the browser |
| `band_page.js` | 328 | The 77-framework band section |
| `mof_network.js` | 255 | Quotient graph, degrees, Laplacian |
| others | ~700 | Navigation, code viewer, controls |

### Why implement everything twice?

This is the question to be ready for, and the answer is not "we had spare time".

> **Two independent implementations agreeing is evidence that neither has a silent bug.**

The Python and JavaScript were written against the same published algorithms and compared on
every reported quantity — bond counts, block compositions, coordination numbers, centralities,
spectra. **They agree on every value.**

Concretely: after fixing the τ definition (Chapter 9), both give `τ(0) = −2.6551` on HKUST-1,
with the peak at exactly `q = 0`.

That is a much stronger correctness argument than either implementation alone could make.

---

## 7.4 · The interactive platform

`1_website/index.html` — **one file, no server, no installation.** Double-click it.

18 sections:

| Group | Sections |
|---|---|
| **Context** | 1 Problem · 2 The Question · 3 Why This Path · 4 What We Built · 5 Files · 6 Roadmap |
| **The Algorithm** | 7 Pipeline Walkthrough · 8 Interactive Tool · 9 The Paper |
| **Network Analysis** | 10 **Graph Primer** · 11 Building the Network · 12 Influential Blocks · 13 Defects · 14 Laplacian |
| **The Spectrum** | 15 Multifractal Spectrum · 16 Box-Growing · 17 The Band |
| **Reference** | 18 Source Code |

What makes it worth having rather than a report:

- **Upload any `.cif`** and the entire pipeline runs on it live, in your browser. This is the
  answer to *"does this only work on your examples?"*
- **Every number is computed at the moment you look at it**, from the structure currently
  loaded. Nothing is typed into the HTML.
- **Section 10 is a graph-theory primer** that defines every term before it is used — because
  the audience includes chemists who should not have to already know what a quotient graph is.
- **Click any filename anywhere** and the real source opens with line numbers.

> **Before presenting:** save
> `https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js` into `1_website/` as
> exactly `three.min.js`, or the 3D panels will be blank without internet.

---

## 7.5 · Testing

8 automated suites, run under jsdom:

| Suite | What it locks down |
|---|---|
| `test_single_page.js` | All 18 sections initialise; the code viewer opens real sources |
| `test_band.js` | The 77-framework data, the band, the confound statistics |
| `test_structure.js` | Nav/section numbering agreement, dead links, duplicate ids, SVG validity |
| `test_index.js` | The pipeline walkthrough |
| `test_network_page.js` | Graph construction and centrality tables |
| `test_overview.js` | The evidence tables |
| `test_pipeline_3d.js` | 3D rendering, lazy initialisation |
| `test_render_robustness.js` | WebGL context loss and recovery |

These exist because things broke silently more than once. `test_structure.js` in particular
was written *after* the navigation drifted out of sync with the section numbering without
anyone noticing.

---

## 7.6 · The 77-framework study

`3_notebooks/mof_band_analysis.ipynb` — 29 cells.

- **Steps 1–8** — query MOFX-DB [7] live, parse CIFs, build PBC bond graphs, coarse-grain,
  compute a spectrum for each of 77 frameworks.
- **Step 6b** — save `results.json` immediately. *(Added after a run lost ~10 minutes of
  computation because the save lived inside the plotting cell.)*
- **Steps 9–12** — the band: shape verification, band construction, the size-confound test,
  figures and conclusions.

It runs in Colab with Run All. Steps 9–12 fall back to the saved `results.json` if the earlier
steps have not been run, so the band analysis alone executes in seconds.

---

## 7.7 · Reproducibility

Everything is in version control at **github.com/Radha-Krishna-19/fyp**.

| Claim | How to check it |
|---|---|
| Coordination numbers | `python3 code_09_network_analysis.py`, or Section 11 of the site |
| The τ fix | `inmfa(..., tau_mode="slope")` reproduces the old behaviour for comparison |
| The band | Section 17 of the site, or Steps 9–12 of the notebook |
| Python ↔ JS agreement | Both print `τ(0) = −2.6551` for HKUST-1 |
| Any number on the site | Click the filename to read the source that produced it |

---

**Next:** [Chapter 8 — Results](08_results.md).
