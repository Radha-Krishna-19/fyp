# Crystal morphology from the unit cell (Phase 1)

Answers the panel's second question: given an established MOF's unit cell, generate
several crystal morphologies, mathematically and computationally. Theory: the project
primer *From Unit Cell to Crystal Shape*. Results: `morphology.html` on the site and
`Phase1_morphology_report.pdf`.

| File | What it does |
|---|---|
| `mofmorph/structure.py` | Reads a CIF, finds the space group with spglib (with and without H), returns the conventional cell and symmetry operations |
| `mofmorph/faces.py` | Systematic-absence rule with every symmetry operation, effective spacings d_eff, symmetry families ({111}+/- in -43m) |
| `mofmorph/shape.py` | Crystal shape as a convex polytope; exact volume, area, sphericity, gyration tensor, kappa^2, Q_3/Q_4/Q_6 |
| `mofmorph/models.py` | Growth-rate models: BFDH, user rates (morph families), graph rule R = exp(beta*c), growth in time from a seed |
| `mofmorph/graphrule.py` | Attachment numbers on the ideal pcu and fcu node nets |
| `tests.py` | 14 checks against known answers (P/I/F lattices, diamond glide absences, exact solids) |
| `run_phase1.py` | Produces every number and figure in `results/` |

Run: `python3 code/morphology/tests.py`, then `python3 code/morphology/run_phase1.py`.
Requirements: numpy, scipy, matplotlib, ase, spglib.

The browser engine `website/mof_morphology.js` is a second, independent implementation;
`website/tests/test_morphology.js` checks it against `results/phase1_results.json`.

## Later phases and the 2026-10-14 additions

| File | What it does |
|---|---|
| `run_phase3.py`, `run_phase4.py`, `run_deform.py` | Graph faces (Phase 3), UFF cleavage energies (Phase 4), changed unit cells (Phase 1b) |
| `mofmorph/hybrid.py`, `run_hybrid.py` | UFF face energies for any crystal system (all atoms, H included); BFDH x Wulff blend R = R_BFDH^(1-w) R_Wulff^w |
| `mofmorph/chgnet_post.py`, `run_chgnet_cleavage.py` | CHGNet notebook results to cleavage energies (upper bounds), Wulff shapes, all slabs vs intact slabs, exact energies of symmetric-as-cut slabs |
| `slab_check.py` | Detached pieces (by formula) and bulk-equivalent thickness of every CHGNet slab |
| `slab_options_check.py` | Dry run of pymatgen slab generation (as cut / linker-preserving / symmetrized); needs pymatgen |
| `run_bond_sensitivity.py` | Phase 4 with metal-ligand bonds at 1, 0.5, 0.25 of the flat cost |
| `run_core.py` | BFDH, hybrid and UFF Wulff shapes for 8 CoRE MOF 2019 structures (`data/core_mof/`) |
| `figs_experiment.py` | The methods-vs-experiment figure for the website |
| `tests_phase3.py`, `tests_phase4.py`, `tests_deform.py`, `tests_review.py` | Exact checks for each phase and for the review fixes |
| `DFT_CHECK_PLAN.md` | Which six CHGNet slabs to recompute with DFT and how to read the answer |
| `data/chgnet_runs/` | The CHGNet result zips, Keerthi's notebook, the Colab notebook that was run, and the revised (not yet run) notebook; `tools/make_symmetric_nb.py` builds the revised one |

Order for the Experiment page: `slab_check.py`, `run_chgnet_cleavage.py`, `slab_options_check.py`,
`run_bond_sensitivity.py`, `run_core.py`, `figs_experiment.py`, then
`../../data/experimental_morphology/compare/compare_with_project.py`,
`../../website/_build/build_experiment_fragment.py`, `../../website/_build/build_site.py`.
