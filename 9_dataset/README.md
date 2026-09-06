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
| `mof_multifractal_descriptors_real_v1.csv` | 4 | **Experimentally synthesised** MOFs, same schema, same pipeline |

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

**The 4-framework file contains real materials** — HKUST-1, UiO-66, MOF-5 and
ZIF-8, all long synthesised, from published CIFs, with coordination numbers
verified against the crystallographic literature before their spectra were
computed.

---

## Known results, including a negative one

**The band.** Across the 77 hypothetical frameworks, Δα falls in
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

**Synthesised frameworks sit outside the hypothetical band.** Size-matched under
the same supercell rule, the four real MOFs span Δα = 1.66 – 2.26, clear of the
hypothetical range with a gap of 0.25. Not a size artefact: MOF-5 has the same
Zn₄O node as all 77 and the same 256 blocks as 48 of them, and still lands at
1.70. Across the 77, Δα correlates with block count at only *r* = +0.11.

Four archetypal structures are not a sample, and two readings remain open —
either the descriptor is detecting that generated frameworks are unusually
regular, or four famous MOFs are unrepresentative. Deciding needs ~50 real
structures; `../3_notebooks/real_mof_band.ipynb` is set up to do it.

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
cd fyp/metal_oxo_deep_dive

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
             Abhinav, G. Rohith and Keerthi Sree, J. and Isha},
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

**v1.0 — 2026-09-06.** First release. 77 hypothetical + 4 synthesised
frameworks. τ fitted through the origin (all 77 spectra valid). Pore-size
correlation withdrawn after confound analysis.
