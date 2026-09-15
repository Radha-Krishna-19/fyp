# MOF Multifractal Structural Descriptors — v1.0

Graph-theoretic structural descriptors for metal–organic frameworks, computed
from crystal structure alone with no molecular simulation.

**Version 1.0 · 2026-09-06 · CC BY 4.0**
23CSE498 Final Year Project · Amrita Vishwa Vidyapeetham, Coimbatore

---

## What this is

Each row is one MOF reduced to a small set of numbers describing **how its
building-block network is organised**. The descriptors come from the
multifractal singularity spectrum of the framework's periodic quotient graph.

The point of the dataset is that these numbers cost **seconds per framework**,
where the molecular simulations normally used to characterise a MOF cost
**hours**. That makes them usable as a pre-filter over large candidate sets — if
they carry real structural information. Testing that is what the project does,
including where it fails.

## Files

| File | Rows | What |
|---|---|---|
| `mof_multifractal_descriptors_v1.csv` | 77 | hMOF frameworks — **hypothetical**, computer-generated, never synthesised |
| `mof_multifractal_descriptors_real_v2.csv` | 61 | **Experimentally synthesised** MOFs from CoRE MOF 2019, same schema, same pipeline |
| `mof_multifractal_descriptors_real_v1.csv` | 4 | *Superseded.* The four structures behind a withdrawn claim; kept so the withdrawal is auditable |

The two are kept in separate files on purpose. They are not interchangeable and
should never be pooled without saying so — see *Provenance* below.

---

## Schema

| Column | Type | Units | Description |
|---|---|---|---|
| `framework_id` | string | — | Identifier within its source database |
| `n_blocks` | int | count | Building blocks (nodes + linkers) in the analysed supercell |
| `n_nodes` | int | count | Inorganic blocks — metal clusters |
| `n_linkers` | int | count | Organic blocks — the struts between them |
| `n_atoms_supercell` | int | count | Atoms after supercell expansion |
| `graph_diameter` | int | hops | Longest shortest path in the block graph |
| `n_influential` | int | count | Blocks in the top decile by degree; the spectrum is read at these |
| **`delta_alpha`** | float | — | **Δα, spectrum width.** How unevenly connectivity is distributed. The primary descriptor. |
| `delta_alpha_sd` | float | — | Standard deviation of Δα over repeated trials — the stability estimate |
| `alpha_min`, `alpha_max` | float | — | Endpoints of the singularity spectrum; Δα is their difference |
| **`asymmetry_A`** | float | — | **A**, spectrum skew. A > 0 frequent structures dominate; A < 0 rare ones do |
| `asymmetry_sd` | float | — | Standard deviation of A over trials |
| `lcd_angstrom` | float | Å | Largest cavity diameter, from the source database |
| `pld_angstrom` | float | Å | Pore-limiting diameter, from the source database |
| `mofid` | string | — | MOFid chemical identifier (linker SMILES + metal node + topology) |
| `source_url` | string | — | Record in the source database, or the publication for a synthesised structure |
| `provenance` | string | — | Whether the structure is hypothetical or synthesised |

`lcd_angstrom` and `pld_angstrom` are **taken from the source database**, not
computed here. They are included so others can reproduce the confound analysis
below.

---

## How the descriptors were computed

1. **Parse the CIF.** Cell parameters, symmetry operators, atom positions. A CIF
   contains no bonds — every bond in this dataset was inferred.
2. **Infer bonds periodically.** Two atoms bond if separated by less than the sum
   of their covalent radii (×1.30 if either is a metal, ×1.15 otherwise), searched
   across all **27 periodic images** so bonds crossing a cell boundary are found.
3. **Decompose.** The published metal-oxo algorithm (`snurr-group/mofid`), used
   unmodified: sever every bond touching a metal; each surviving connected
   component is a block. Blocks containing a metal are nodes, the rest linkers.
4. **Build the labelled quotient graph.** One vertex per block, one edge per
   inter-block bond, each edge carrying the lattice translation it crosses.
   Dropping those labels collapses UiO-66's twelve connections to one.
5. **Expand to a supercell** until every lattice direction exceeds **48 Å**. A
   primitive cell has too few distinct radii to fit a power law over.
6. **Box-grow** from each influential block, sweep the distortion exponent
   *q* ∈ [−10, 10], fit τ(q) **through the origin**, and Legendre-transform to
   α = dτ/dq and f(α) = qα − τ.

Full implementation: `../2_python/` (reference) and `../1_website/` (browser
engine). The two were written independently from the same specification and
cross-check each other.

### The τ definition matters

τ(q) must be fitted **through the origin** — τ = ln 𝒫_q / ln(r/r_N) — not as a
free-intercept least-squares slope. Using a free intercept produced spectra with
no apex for **every one of the 77 frameworks**. After the correction, all 77 are
proper inverted parabolas peaking at q = 0. If you reimplement this, that is the
step to get right.

---

## Provenance — read this before using the data

**The 77-framework file contains hypothetical structures.** They are hMOF
entries: assembled computationally from real building blocks under real bonding
rules, chemically reasonable, and the same class of structure generative models
such as MOFDiff are trained on — but **nobody has made them**. Any sentence
describing this file as "experimental" is false.

They also share **one metal**. Every one is a Zn₄O framework. The band below is
therefore a band *within* one chemical family and says nothing about separating
families.

This was not intended. The analysis requested CoRE MOF 2019 from MOFX-DB and
received hMOF records, because on that endpoint the `database=` parameter is
advisory and loses to the `gases[]` filter. A provenance check caught it. The
query now filters each returned record on its own `database` field.

**The 61-framework file contains real materials** — CSD refcodes from CoRE MOF
2019, retrieved from the Zenodo archive at DOI `10.5281/zenodo.3370236` rather
than from a live API, sampled with a cap per metal composition so no single
metal dominates. An archived record is the same bytes for every reader,
permanently, which is a stronger provenance guarantee than a query.

---

## Known results, including two negative ones

> **Withdrawn (2026-09-14, corrected 2026-09-15): both bands below are
> diameter artefacts, not structural findings.** Both were computed by running
> the multifractal analysis on the **atomic** supercell bond graph — not on
> the coarse-grained building-block graph this README describes above.
> Coarse-graining only supplied the `n_nodes`/`n_linkers` counts; the
> `graph_diameter` and `n_influential` columns describe the atomic graph
> (diameters 35–64 for the hMOF set, 34–104 for the CoRE MOF set — not 8–12,
> which was this project's own earlier misreading of the evidence, since
> corrected in `CLAUDE.md`). An atomic MOF graph spans two length scales —
> molecular, inside one linker or metal cluster, and framework, above one
> linker length — and fitting a single power law across that crossover is not
> a valid scaling measurement regardless of graph size.
>
> Independently of that, a finite-size sweep on four demonstration frameworks
> run on the *correctly* coarse-grained quotient graph (HKUST-1, MOF-5, ZIF-8,
> UiO-66 — tbo, pcu, sod and fcu nets) shows Δα growing with supercell diameter
> at every q range tested (|q| ≤ 10 down to |q| ≤ 2), with no plateau. The
> mechanism: at the extremes of q the partition function is dominated by a
> single box, the smallest possible box is one vertex, and that term grows
> with graph size without bound. Fitted slopes of Δα against ln(diameter),
> full q range: HKUST-1 (tbo) 0.782, MOF-5 (pcu) 0.732, ZIF-8 (sod) 0.886,
> UiO-66 (fcu) 0.692 — all R² ≥ 0.998, so the divergence is not net-specific,
> though the rate is. See `size_scaling/convergence_figure.png` in this
> folder, `CLAUDE.md`, and `2_python/code_12_converged_band.py` /
> `2_python/_run_size_scaling.py` for the sweep and its full numbers.
>
> **The sub-bands (Narrow/Medium/Wide) an independent coarse-grained
> run cut the hMOF set into are size strata, not chemistry.** Of 14 distinct
> coarse-grained graph signatures across 76 structures, 13 are entirely one
> class — class is a deterministic function of graph size wherever the graph
> actually differs. The 14th signature (256 nodes, 384 edges, diameter 12 —
> the 4×4×4 pcu tiling) accounts for 48 of the 76 structures (63%) and spans
> **all three classes** (36 Medium, 6 Wide, 6 Narrow), because coarse-graining
> cannot see the linker-chemistry difference between them; the split there is
> box-covering trial noise on an already non-converged descriptor. See
> `size_scaling/size_strata_figure.png` and `2_python/code_14_size_strata.py`.
>
> **A proposal, not a result: does the Δα(D) divergence slope itself vary
> between frameworks?** A capped check (20 structures per dataset, size-spread
> sample, supercell capped at 5000 nodes, `2_python/code_15_dataset_sweeps.py`)
> found the fitted slope's spread across 15 CoRE MOF structures (sd 0.333,
> range 0.224–1.474) about 2.5× that across 19 hMOF structures (sd 0.134,
> range 0.407–0.818) — consistent with the slope carrying real structural
> signal, but equally consistent with sampling noise at this small, one-seed
> sample size. Not established either way; see
> `size_scaling/slope_sweep_figure.png`.
>
> **The full, correct band, on the complete datasets.** Both datasets were
> then re-fetched in full (all 77 hMOF, all 61 CoRE MOF) and run on the
> correct coarse-grained supercell graph
> (`2_python/code_17_full_correct_band.py`, `9_dataset/size_scaling/full_band_hmof_cg.json`,
> `full_band_core_cg.json`). 72/77 hMOF and 55/61 CoRE MOF produced a usable
> spectrum. Spectrum-fitting parameters (top 20% of vertices by degree as
> "influential", radii capped at half the diameter) keep every fitted point
> inside the structural core and away from the largest radii, where
> box-covering has only one or two boxes left to average over; tested
> directly (`2_python/_test_window_frac.py`), this keeps the divergence with
> supercell size gentler at every step tested, though it does not stop the
> divergence outright. Class
> (Narrow/Medium/Wide terciles) still correlates with coarse-grained node
> count at r = +0.69 (hMOF) and r = +0.72 (CoRE MOF), independently — using
> the right graph fixes the graph, not the descriptor. A nine-category
> comparison per class (chemistry, features, degree, edges, higher-order
> structure, assortativity, heterogeneity, components —
> `2_python/code_18_subband_explain.py`) is on the project's Results page.
> This also surfaced an undocumented decomposition behaviour: several
> classes on both datasets average more than one connected component after
> replication, meaning the metal-oxo decomposition is retaining disconnected
> guest/solvent fragments as small linker blocks on a real fraction of
> structures.
>
> Practically: **every `delta_alpha` value in both CSV files below is a
> function of the atomic graph it was measured on, not of the framework it is
> attributed to, for two independent reasons.** The band widths, the
> pore-size confound analysis, and the real-vs-hypothetical comparison quoted
> below are kept for audit — exactly as the four-structure claim was kept in
> `..._real_v1.csv` after its own withdrawal — but none of them should be read
> as a structural or chemical finding.

**The band (superseded — see withdrawal above).** Across the 77 hypothetical frameworks, Δα falls in
**1.11 – 1.25** (interquartile range; full range 1.02 – 1.41). Asymmetry A is
negative for all 77, between −1.51 and −1.04.

**Δα does not predict pore size.** The raw correlation between Δα and largest
cavity diameter is *r* = −0.497, which looks like a finding. Controlling for the
number of blocks in the graph collapses it to *r* = **+0.101**, while graph size
survives at +0.621. Adding pore size to a size-only model improves R² by 0.005.

> **The descriptor was largely measuring how big the graph was.** The claim was
> withdrawn from the project. Anyone using this dataset should control for
> `n_blocks` and `n_atoms_supercell` before reporting a correlation with
> anything. This is the most useful thing in this README.

**Synthesised frameworks sit on the same band.** The 61 real frameworks span
Δα = 0.95 – 1.47 against the hypothetical set's 1.02 – 1.41. Means differ by
0.018 (Welch *p* = 0.38, Mann–Whitney *p* = 0.39), and mean asymmetry is −1.31
in both sets: the same width and the same spectrum shape. A descriptor
calibrated on generated structures transfers to structures that exist.

One difference is statistically real: the synthesised set is **more variable**
(sd 0.132 vs 0.095, Levene *p* = 0.010). Frameworks people actually made are
more structurally varied than frameworks one algorithm generated.

**The pore-size confound reproduces on real data.** Across the 61, Δα correlates
with LCD at *r* = −0.198; hold graph size constant and it falls to +0.097, while
size holds at +0.488. The same correlation fails the same way, for the same
reason, on structures that exist.

> **Withdrawn: the second version of this section.** It previously reported that
> four synthesised MOFs sat *clear* of the hypothetical band at Δα = 1.66 – 2.26,
> "not a size artefact". It was a size artefact. Those four were expanded to
> 256–972 atoms while the 77 hMOFs occupy 3024–6592 — not one hMOF is as small as
> the largest of the four — and Δα correlates with **atom** count at *r* = +0.73.
> The *r* = +0.11 quoted in defence of that claim was against **block** count, a
> different quantity, and the wrong one to rule out a size confound with. The
> four rows remain in `..._real_v1.csv` so the error can be inspected rather than
> taken on trust.

---

## Limitations

- **Unweighted, untyped graph.** Bond strength, bond order and element identity
  are discarded. What survives is pure connectivity. That is deliberate — it is
  what makes the descriptor transfer across chemistries — but it means the
  descriptor cannot distinguish two frameworks with identical topology and
  different chemistry.
- **Δα scales with graph size.** Control for it. See above.
- **No adsorption data.** Nothing here predicts gas uptake, and the project does
  not claim it does.
- **Single metal in the main file.** No cross-family claim is supportable.
- **Stochastic in the trial average**, deterministic in the box growing.
  `*_sd` columns quantify the residual variation; it is roughly an order of
  magnitude below the spread between frameworks.

---

## Reproducing

```bash
git clone https://github.com/Radha-Krishna-19/fyp.git
cd fyp

# one framework, from the command line
python 2_python/code_00_pipeline_driver.py 2_python/HKUST-1.cif
python 2_python/code_10_multifractal_spectrum.py

# the full 77-framework run
jupyter notebook 3_notebooks/mof_band_analysis.ipynb
```

`3_notebooks/results.json` is the raw output this CSV is derived from; it keeps
the full α, f(α) and τ(q) curves, which the CSV summarises.

---

## Citation

```bibtex
@dataset{mof_multifractal_2026,
  title   = {MOF Multifractal Structural Descriptors},
  author  = {Radha Krishna, P. M. and Varma, P. Kshitij and
             Abhinav, G. Rohith and Keerthi Sree, J. and Isha Sri Prakash},
  year    = {2026},
  version = {1.0},
  note    = {23CSE498 Final Year Project, Amrita Vishwa Vidyapeetham, Coimbatore.
             Guide: Dr. T. Ramraj},
  url     = {https://github.com/Radha-Krishna-19/fyp}
}
```

**Please cite the upstream work too** — this dataset is derived from both:

- Xiao *et al.*, "Deciphering the generating rules and functionalities of complex
  networks", *Scientific Reports* **11**, 22964 (2021). The multifractal method.
- Bucior *et al.*, "Identification schemes for metal–organic frameworks to enable
  rapid search and cheminformatics analysis", *CrystEngComm* **21**, 3777 (2019).
  The MOFid decomposition.
- Wilmer *et al.*, "Large-scale screening of hypothetical metal–organic
  frameworks", *Nature Chemistry* **4**, 83 (2012). The hMOF structures.

## Licence

**CC BY 4.0.** Use it, change it, build on it — commercially or not — with
attribution. See `LICENSE`.

Structures come from MOFX-DB / the hMOF database under their own terms; the
descriptors computed here are ours.

## Changelog

**Unreleased — 2026-09-15.** Corrected the 2026-09-14 entry below: both bands
were computed on the **atomic** supercell graph, not the coarse-grained graph
described in this README (diameters 35–64 and 34–104, not 8–12). This sharpens
rather than reverses the withdrawal — an atomic graph spans a molecular and a
framework length scale, and fitting one power law across that crossover is
invalid independently of the finite-size problem below. See `CLAUDE.md`.

**2026-09-14.** Finite-size convergence testing
(`2_python/code_12_converged_band.py`) shows Δα does not converge with
supercell diameter at any q range from ±10 down to ±2, on any of four
demonstration nets. **Both bands below are withdrawn as structural findings**
and kept only for audit; see the notice at the top of *Known results*. No
band was recomputed, because there is no converged q cap to recompute at.

**v2.0 — 2026-09-07.** 77 hypothetical + **61 synthesised** frameworks
(`..._real_v2.csv`). The synthesised set now comes from the CoRE MOF 2019 Zenodo
archive rather than a live API. The four-structure "band separation" claim is
**withdrawn** — it was a graph-size artefact; see *Known results*. The
four-row v1 file is retained for audit.

**v1.0 — 2026-09-06.** First release. 77 hypothetical + 4 synthesised
frameworks. τ fitted through the origin (all 77 spectra valid). Pore-size
correlation withdrawn after confound analysis.
