# MOF Graphs and Crystal Morphology

**23CSE498 Final Year Project, Phase II (research-based)**
Department of Computer Science and Engineering, School of Computing, Amrita Vishwa Vidyapeetham, Coimbatore
**Guide:** Dr. T. Ramraj, M.E., Ph.D., Assistant Professor (Sl. Gd.)

| | |
|---|---|
| **Project website** | <https://radha-krishna-19.github.io/fyp/> (also opens offline from [`website/index.html`](website/index.html)) |
| **Team paper** | [Topology-Based Coarse-Graining for Multifractal Spectrum Analysis in Metal-Organic Frameworks](docs/paper/G070_Paper.pdf) |
| **Project notes** | [`docs/project_notes.md`](docs/project_notes.md): verified findings, quotable numbers, defects fixed |
| **Mistakes and corrections** | [Mistakes page](https://radha-krishna-19.github.io/fyp/lessons.html): every mistake, why it was made, how it was fixed |

---

## Summary

A metal–organic framework (MOF) is a porous crystal of metal clusters joined by organic linkers.
The project has two parts.

**Part 1: a connectivity descriptor.** Each MOF is cut into building blocks (the published
metal-oxo decomposition), turned into a periodic graph (the labelled quotient graph), and summarised
by the width Δα of the multifractal spectrum of that graph. The question was whether Δα, computed in
seconds without simulation, carries enough structural information to pre-select MOFs for
simulation. On 77 hypothetical (hMOF) and 61 synthesised (CoRE MOF 2019) frameworks the answer is
**no, as currently defined**: Δα grows linearly in the logarithm of the graph diameter on every net
tested and never converges, and classes formed from it follow graph size (r = +0.69 and +0.72).
The two published bands are therefore withdrawn as structural results; the pipeline itself is
verified and reused.

**Part 2: crystal morphology** (the question set at Panel Review 1). From the unit cell of an
established MOF the project generates several crystal morphologies, mathematically and
computationally:

* the space group fixes which faces may exist; from them MOF-5, HKUST-1 and UiO-66 admit the family
  cube → cuboctahedron → octahedron and ZIF-8 the family cube → rhombic dodecahedron (16 propositions,
  each proved and checked numerically);
* changing the cell parameters adds plates and rods;
* seven growth models select a member of the family: BFDH, the graph attachment rule, two graph-energy
  Wulff models, a force-field (UFF) Wulff model, a BFDH × Wulff blend and a CHGNet cleavage-energy model;
* the models are scored against 134 laboratory records from 35 papers (12 MOFs). ZIF-8 is reproduced
  by every model; the MOF-5 cube by the graph rule, the broken-bond Wulff model and the force-field
  model (the last only at the default bond cost); the HKUST-1 octahedron only as the dominant {111}
  face of a truncated octahedron; additive-free UiO-66 (poorly faceted cubes) by none. Four MOFs are
  too few to rank the models.

**Linking the parts.** The periodic Δα carries no shape information beyond graph size
(size-controlled ρ = +0.001, p = 0.99, 55 CoRE MOFs), but the spectrum and the box-counting
(mass–radius) dimension of a *finite* crystal particle do respond to its shape.

---

## Repository structure

| Folder | Contents |
|---|---|
| [`code/spectrum_pipeline/`](code/spectrum_pipeline/) | Part 1: decomposition pipeline (`code_00`–`code_07`, Python translation of the published method), spectrum analysis (`code_09`–`code_19`), the four demonstration CIFs |
| [`code/morphology/`](code/morphology/) | Part 2: the `mofmorph` package, one run script per phase, tests, result files and figures; [`chgnet_wulff/`](code/morphology/chgnet_wulff/) CHGNet Wulff pipeline |
| [`code/spectrum_shape_relation/`](code/spectrum_shape_relation/) | The link between the parts: finite crystal particles, their spectrum and dimension profile, notebook and results |
| [`data/`](data/) | [Structures](data/structures/) (77 hMOF, 61 CoRE MOF CIFs), [spectrum descriptors](data/spectrum_descriptors/), [experimental morphology dataset](data/experimental_morphology/), [CHGNet runs](data/chgnet_morphograph_runs/) |
| [`notebooks/`](notebooks/) | [Spectrum notebooks](notebooks/spectrum/) and [MorphoGraph-MOF notebooks](notebooks/morphograph_mof/) |
| [`docs/`](docs/) | [Paper](docs/paper/), [reports](docs/reports/), [slides](docs/presentation/), [textbook](docs/textbook/), [concept notes](docs/concepts/), [references](docs/references/), [certifications](docs/technical_enrichment/), [report figures](docs/report_figures/), [project notes](docs/project_notes.md) |
| [`website/`](website/) | The project website: pages, browser engines, build scripts ([`_build/`](website/_build/)), test suites ([`tests/`](website/tests/)) |

---

## Getting started

### Read the website

Online at <https://radha-krishna-19.github.io/fyp/>, or offline:

```bash
git clone https://github.com/Radha-Krishna-19/fyp.git
cd fyp/website        # open index.html in a browser; no server or internet connection needed
```

### Run the Python code

```bash
pip install -r requirements.txt

# Part 1: decompose one framework and compute its spectrum
cd code/spectrum_pipeline
python code_00_pipeline_driver.py HKUST-1.cif
python code_12_converged_band.py

# Part 2: shapes of the four demonstration MOFs, and the checks
cd ../morphology
python run_phase1.py          # symmetry, allowed faces, BFDH, morph families
python run_phase4.py          # force-field face energies and Wulff shapes
python tests.py               # Phase 1 checks (also tests_phase3/4, tests_deform, tests_review)

# The link between the parts
cd ../spectrum_shape_relation
python run_04_dimension_profile_of_crystal_particles.py
python check_spectrum_shape_relation.py
```

Every script names its inputs and outputs in its header. The notebook
[`Spectrum_Shape_Relation.ipynb`](code/spectrum_shape_relation/Spectrum_Shape_Relation.ipynb) runs the
whole spectrum–shape study in Google Colab and writes a run report.

### Rebuild and test the website

```bash
python website/_build/update_code_sources.py   # refresh the embedded source browser
python website/_build/build_site.py            # rebuild every page from website/_build/
cd website/tests && npm install && npm test     # 12 suites
```

The pages are built from `website/_build/content_source.html`, `website/_build/fragments/` and the
result files; built pages are never edited by hand (the GitHub workflow checks this). Every figure
names the script and data that produced it.

---

## Notebooks

| Notebook | Purpose |
|---|---|
| [`notebooks/spectrum/mof_band_analysis.ipynb`](notebooks/spectrum/mof_band_analysis.ipynb) | Spectrum band of 77 hMOF frameworks (atomic graph, withdrawn) |
| [`notebooks/spectrum/real_mof_band.ipynb`](notebooks/spectrum/real_mof_band.ipynb) | The same for 61 CoRE MOF 2019 frameworks |
| [`notebooks/spectrum/pipeline_walkthrough_full.ipynb`](notebooks/spectrum/pipeline_walkthrough_full.ipynb) | The decomposition pipeline module by module |
| [`notebooks/morphograph_mof/MorphoGraph_MOF_revised.ipynb`](notebooks/morphograph_mof/MorphoGraph_MOF_revised.ipynb) | CHGNet bulk and slab relaxation, surface energies, atomistic particles |
| [`notebooks/morphograph_mof/MorphoGraph_MOF_colab_4MOFs.ipynb`](notebooks/morphograph_mof/MorphoGraph_MOF_colab_4MOFs.ipynb) | The same, unattended, for the four demonstration MOFs |
| [`notebooks/morphograph_mof/MorphoGraph_MOF_colab_symmetric_slabs.ipynb`](notebooks/morphograph_mof/MorphoGraph_MOF_colab_symmetric_slabs.ipynb) | Symmetric-slab variant (prepared, not yet run) |
| [`notebooks/morphograph_mof/MorphoGraph_hybrid.ipynb`](notebooks/morphograph_mof/MorphoGraph_hybrid.ipynb) | BFDH, blended and force-field Wulff shapes for any CIF |
| [`code/morphology/chgnet_wulff/MOF_Wulff_Colab.ipynb`](code/morphology/chgnet_wulff/MOF_Wulff_Colab.ipynb) | CHGNet Wulff shapes compared with a laboratory shape table |
| [`code/spectrum_shape_relation/Spectrum_Shape_Relation.ipynb`](code/spectrum_shape_relation/Spectrum_Shape_Relation.ipynb) | Spectrum and crystal shape |
| Google Colab working copies (Keerthi): [coarse-grained MOF spectrum](https://colab.research.google.com/drive/1lnWFEl2flCUrFI-n3BJurn_ICbJaNpPy), [Wulff shapes](https://colab.research.google.com/drive/1A4wcRz-HMCVbwJ7zgqPqCQv-NQeTumUb), [morphologies](https://colab.research.google.com/drive/1dWTwj7SkIVFL2EHxg1cDPOqwMOtS8Mny) | Working copies edited by the team |

---

## Defects found and corrected

Each was a silent wrong answer rather than a crash. The full list, with plain and technical
explanations, is on the [Mistakes page](https://radha-krishna-19.github.io/fyp/lessons.html).

| Defect | Consequence | Correction |
|---|---|---|
| τ(q) fitted with a free intercept | No spectrum had its apex at q = 0 (0 of 77 valid) | Fit through the origin, τ = Σxy / Σx² (77 of 77 valid) |
| Spectrum computed on the subgraph of influential nodes | Metal clusters never bond directly, so that subgraph has no edges | Cover the whole graph; read the measure at the influential nodes |
| Averaging p<sub>i</sub>(r) over trials before taking logarithms | Spectra biased narrow by more than a factor of ten | Build Z per trial, take ln Z per trial, then average |
| Periodicity discarded | UiO-66's 12-connected cluster reported with the wrong connectivity | Labelled quotient graph with lattice translations on the edges |
| Bands computed on the atomic graph | One power law fitted across two length scales | Re-run on the coarse-grained graph; the size dependence remains, so the bands are withdrawn |
| Database returned hMOF records for a CoRE MOF query | Every early result was on hypothetical structures | Each record filtered on its own `database` field |
| Hydrogen atoms dropped from the ZIF-8 energy cell | {111} energy 0.312 instead of 0.619 J/m² | Energies computed on the full cell |
| UiO-66 counted as a match | The additive-free benchmark reports cubes, not octahedra | Every page reads the benchmark from one file |

## What the project does not claim

* Δα, as defined, is not a converged property of a framework; neither published band is a structural finding.
* Nothing here computes or predicts gas adsorption.
* The 77 hMOF structures are hypothetical and share one metal (Zn₄O); the 61 CoRE MOF structures are synthesised.
* The force-field face energies are unrelaxed, without solvent, charge or temperature; the CHGNet energies are upper bounds and are not yet checked against DFT.
* With four MOFs no morphology model can be ranked as best; the blend weight is shown at a fixed value and never tuned.

## Future work

1. DFT check of the MOF-5 and UiO-66 faces on which the force field and CHGNet disagree (Kshitij).
2. Solvent, modulator and temperature in the face energies (Isha); more MOFs with known shapes (Rohith).
3. Choose the blend weight on some MOFs and test it on others (held-out validation).
4. Dimension profile and spectrum of the plates and rods of the deformed cells, and of the CHGNet atomistic particles.
5. Final paper on the morphology work.

---

## Team

| Member | Roll number | Certification (October 2026) |
|---|---|---|
| Pasupuleti Meena Radha Krishna | CB.SC.U4CSE23134 | [Fractals and Scaling](docs/technical_enrichment/certificates/G070_23134_OnlineCourse.pdf), Santa Fe Institute |
| Kshitij Varma Pinnamaraju | CB.SC.U4CSE23122 | [Graph Theory](docs/technical_enrichment/certificates/G070_23122_OnlineCourse.pdf), Udemy |
| Rohith Abhinav Sai Komal Gullolla | CB.SC.U4CSE23141 | [Advanced Algorithms (Graph Algorithms) in Java; Social Network Analysis](docs/technical_enrichment/certificates/G070_23141_OnlineCourse.pdf), Udemy |
| Keerthi Sree Jonnakuti | CB.SC.U4CSE23031 | [Introduction to Complexity](docs/technical_enrichment/certificates/G070_23031_OnlineCourse.pdf), Santa Fe Institute |
| Isha Sri Prakash | CB.SC.U4CSE23029 | [Graph Algorithms for Machine Learning](docs/technical_enrichment/certificates/G070_23029_OnlineCourse.pdf), TigerGraph University |

Responsibilities in each part are listed on the [Team page](https://radha-krishna-19.github.io/fyp/team.html);
how each course supports the project is in [`docs/technical_enrichment/`](docs/technical_enrichment/).

## Principal references

* Bucior et al., *Cryst. Growth Des.* **19**, 6682 (2019): MOFid and the metal-oxo decomposition.
* Xiao, Wang and Li, *Sci. Rep.* **11**, 22964 (2021): multifractal analysis of networks (NMFA, iNMFA).
* Song, Havlin and Makse, *Nature* **433**, 392 (2005): box covering of complex networks.
* Hartman and Perdok (1955); Wulff (1901): crystal growth and equilibrium shapes.
* Deng et al., *Nat. Mach. Intell.* **5**, 1031 (2023): CHGNet.

The annotated bibliography is in [`docs/references/`](docs/references/) and on the
[References page](https://radha-krishna-19.github.io/fyp/references.html).

## Licence

The spectrum descriptor dataset is released under CC BY 4.0
([`data/spectrum_descriptors/LICENSE`](data/spectrum_descriptors/LICENSE)). `three.min.js` is included
under the MIT licence of the three.js project.
