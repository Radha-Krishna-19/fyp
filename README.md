# MOF Building-Block Analysis — Final Year Project

Identifying what a metal–organic framework is built from, correcting the algorithm the
field uses to do it, and analysing the resulting network.

---

## Start here

| I want to… | Open |
|---|---|
| **See the whole project** | `1_website/index.html` — one page, everything |
| **Present it to someone** | `PRESENTATION_SCRIPT.md` — the full talk |
| **Understand the concepts properly** | `5_concepts/` — five Word documents, read in order |
| **Run the code** | `2_python/` — see below |
| **Run the analysis in Colab** | `3_notebooks/spectrum_corrected.ipynb` — self-contained |

The website is now a **single page**. There used to be three; they were merged, so
`index.html` is the only file you need to open.

### ⚠ Before presenting: make the 3D work offline

The 3D views need Three.js, which by default loads from a CDN — **with no internet every
3D panel is blank**.

1. Open <https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js>
2. Save it into **`1_website/`** as exactly `three.min.js`

The page prefers a local copy and falls back to the CDN. If neither is available each
panel explains itself instead of showing a black box.

---

## Folder layout

```
1_website/     the site — open index.html, that is the only entry point
2_python/      one runnable module per pipeline stage, CIFs beside them
3_notebooks/   the corrected notebook (runs anywhere) + the original, for comparison
4_reference/   figures
5_concepts/    five Word documents explaining the whole project
PRESENTATION_SCRIPT.md
README.md      (this file)
```

Each folder carries its own copy of the four `.cif` files so it works standalone.

### `5_concepts/` — read in this order

| # | Document | Covers |
|---|---|---|
| 1 | MOF and Crystallography Fundamentals | What a MOF is, the CIF format, why bonds must be inferred, periodicity, coordination number |
| 2 | The Published Decomposition Algorithm | The MOFid pipeline stage by stage, and the metal-oxo rule |
| 3 | Drawbacks and the Proposed Fixes | The four limitations, the evidence, the fixes, the measured effect |
| 4 | Network and Multifractal Analysis | The quotient graph, influential nodes, the Laplacian, the multifractal spectrum |
| 5 | The Website — What and Why | Why the site exists, what all sixteen sections do, what to demo live |

---

## What the project establishes

**1 · The published decomposition algorithm reports chemically incomplete nodes.**
It cuts every bond touching a metal, which severs the metal from the carboxylate that
chemically belongs to it. HKUST-1's node comes out as bare `Cu2` — two copper atoms —
when the real building unit is a Cu₂(COO)₄ paddlewheel.

| Structure | Published node | With our fix | Change |
|---|---|---|---|
| HKUST-1 | `Cu2` | `Cu2 C4 O8` | **+12 atoms** |
| UiO-66 | `Zr6 O8 H4` | `Zr6 O32 C12 H4` | **+36 atoms** |
| MOF-5 | `Zn4 O` | `Zn4 O13 C6` | **+18 atoms** |
| ZIF-8 | `Zn` | `Zn` | no change — correctly, it has no carboxylate |

**2 · The block network must be built periodically.** A MOF repeats forever; discard the
lattice translations and UiO-66's Zr₆ cluster reports as 6-connected instead of 12, or
collapses into a star. Built correctly, all four match published crystallography:

| | HKUST-1 | MOF-5 | ZIF-8 | UiO-66 |
|---|---|---|---|---|
| Node coordination | 4 | 6 | 4 | **12** |
| Net | `tbo` | `pcu` | `sod` | `fcu` |

**3 · "Influential nodes" cannot be ranked inside a perfect crystal.** Every structure has
only **two** distinct degree values — one for nodes, one for linkers — because
symmetry-equivalent blocks are genuinely identical. A "top-k" list is sorting ties. The
degree *value* is still the most useful number in the analysis: it is the coordination
number, which determines the topology.

**4 · Defects make influence measurable.** Remove one linker and the symmetry breaks:
HKUST-1 goes from 2 to 4 distinct centrality values, and λ₂ falls 1.44 → 1.19,
quantifying how much the framework was weakened.

**5 · The multifractal spectrum separates the frameworks.**

| Structure | Metal | α range (iNMFA) | Node fractal dimension (NMFA) |
|---|---|---|---|
| HKUST-1 | Cu | 1.84 – 1.86 | 1.68 |
| MOF-5 | Zn | 1.91 – 2.00 | 1.81 |
| ZIF-8 | Zn | 1.98 – 1.99 | 1.93 |
| **UiO-66** | **Zr** | **2.29 – 2.65** | **2.30** |

**Not established:** with exactly one Zr structure, "all Zr-MOFs occupy this band" is a
demonstration of mechanism, not a result. It needs a few hundred MOFs grouped by metal
(CoRE MOF / QMOF). Every module runs per-CIF, so scaling up is a loop.

---

## Running the code

```bash
cd 2_python
python3 code_00_pipeline_driver.py HKUST-1.cif   # the full published pipeline
python3 code_08_proposed_fixes.py                # before/after our fixes
python3 code_09_network_analysis.py              # coordination numbers, centrality, Laplacian
python3 code_10_multifractal_spectrum.py         # iNMFA spectrum + reference band
python3 code_11_nmfa_paper.py                    # NMFA exactly as published (box-growing)
```

Requires `numpy`, `networkx`, `matplotlib`. Every number on the website comes out of
these; the Python and the browser JavaScript were cross-checked and agree.

### The notebook

`3_notebooks/spectrum_corrected.ipynb` has the four structures **embedded inside it** and
unpacks them on run, so it works in Colab or anywhere else with no files to supply. Its
outputs are also saved, so you can read the results without running it. Upload it to
Colab, Runtime → Run all, and every table fills in.

### Module map

| File | Stage |
|---|---|
| `code_00_pipeline_driver.py` | runs the whole chain |
| `code_01_cif_input.py` | read the CIF — no bonds exist yet |
| `code_02_bond_assignment_pbc.py` | infer bonds, periodic minimum-image search |
| `code_03_element_classification.py` | `is_metal()` |
| `code_04a/b/c` | metal-oxo · single-node · all-node splitting |
| `code_05_centroid_simplification.py` | collapse each block to a point |
| `code_06_systre_topology_export.py` | write a real `.cgd` for Systre |
| `code_07a/07b` | MOFid / MOFkey assembly |
| **`code_08_proposed_fixes.py`** | **our four fixes to the published algorithm** |
| **`code_09_network_analysis.py`** | **periodic graph, centrality, Laplacian spectrum** |
| **`code_10_multifractal_spectrum.py`** | **iNMFA, reference band, candidate test** |
| **`code_11_nmfa_paper.py`** | **NMFA exactly as published — box-growing** |

Modules 00–07 are faithful translations of the published `snurr-group/mofid` C++ source;
each docstring cites the upstream file. Modules 08–11 are this project's own work.

Every one of these files can also be read **inside the website** — click any filename
anywhere on the page and the source opens with line numbers.

---

## Honest limitations

- **Systre is not reimplemented.** Module 06 writes a genuine `.cgd` file, but the
  topology tool itself is external. Quoted RCSR names are the published ones.
- **InChIKeys are placeholders** in Module 07b — real InChI needs a separate library.
  Stated in the code and on the page.
- **The donor-agnostic fix has zero measured effect on this test set**, because none of
  the four structures has a bridging non-oxygen donor. Its justification is generality.
- **Rod SBUs are detected, not handled.**
- **One Zr structure**, so no family-level claim (see above).
- **iNMFA is degenerate on a perfect crystal.** The influential blocks are
  symmetry-equivalent, so they share a single growth curve and the spectrum collapses to
  a point. NMFA over all blocks does not have this problem, and defects remove it.

---

## Source

The decomposition algorithm: `snurr-group/mofid` (Northwestern).
The multifractal method: Xiao et al., *"Deciphering the generating rules and
functionalities of complex networks"*, **Scientific Reports 11, 22964 (2021)** —
<https://www.nature.com/articles/s41598-021-02203-4>
