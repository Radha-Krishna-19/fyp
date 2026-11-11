# Crystal morphology from the unit cell

Part 2 of the project. Given the unit cell of an established MOF, this folder generates the crystal
morphologies the cell allows and the models that choose among them. The results are on the website
pages [Morphology](https://radha-krishna-19.github.io/fyp/morphology.html),
[Cell Deform](https://radha-krishna-19.github.io/fyp/deform.html),
[Graph Faces](https://radha-krishna-19.github.io/fyp/graph_faces.html),
[Surface Energy](https://radha-krishna-19.github.io/fyp/surface_energy.html),
[Hybrid](https://radha-krishna-19.github.io/fyp/hybrid.html) and
[Experiment](https://radha-krishna-19.github.io/fyp/experiment.html); the theory is in the
[morphology primer](../../docs/reports/MOF_morphology_primer.pdf) and on the
[Learn](https://radha-krishna-19.github.io/fyp/learn_shape.html) and
[Maths](https://radha-krishna-19.github.io/fyp/morph_math.html) pages.

Requirements: `numpy scipy matplotlib ase spglib` (see the root [`requirements.txt`](../../requirements.txt));
`pymatgen` only for `slab_options_check.py`. Input structures are the four CIFs in
[`code/spectrum_pipeline/`](../spectrum_pipeline/) and the CoRE MOF 2019 CIFs in
[`data/structures/core_mof_2019/`](../../data/structures/core_mof_2019/).

## The package `mofmorph/`

| Module | What it does |
|---|---|
| [`structure.py`](mofmorph/structure.py) | Reads a CIF, finds the space group with spglib (with and without hydrogen), returns the conventional cell and symmetry operations |
| [`faces.py`](mofmorph/faces.py) | Systematic-absence rule for every symmetry operation, effective spacings d<sub>eff</sub>, symmetry families ({111}± in −43m) |
| [`shape.py`](mofmorph/shape.py) | Crystal shape as a convex polytope: exact volume, area, sphericity, gyration tensor, κ², Q<sub>3</sub>/Q<sub>4</sub>/Q<sub>6</sub> |
| [`models.py`](mofmorph/models.py) | Growth-rate models: BFDH, user rates (morph families), graph rule R = exp(βc), growth in time from a seed |
| [`graphrule.py`](mofmorph/graphrule.py) | Attachment numbers on the ideal pcu and fcu nets |
| [`graphfaces.py`](mofmorph/graphfaces.py) | Phase 3: slices of the real periodic net, attachment and broken-bond energies, F/S/K classes |
| [`forcefield.py`](mofmorph/forcefield.py) | Phase 4: UFF cleavage energy of every face from the atoms (unrelaxed, no electrostatics) |
| [`deform.py`](mofmorph/deform.py) | Phase 1b: changed cell parameters with the original symmetry used for the absence test |
| [`hybrid.py`](mofmorph/hybrid.py) | UFF face energies for any crystal system (all atoms) and the blend R = R<sub>BFDH</sub><sup>1−w</sup> R<sub>Wulff</sub><sup>w</sup> |
| [`chgnet_post.py`](mofmorph/chgnet_post.py) | CHGNet slab energies to cleavage-energy upper bounds and Wulff shapes |
| [`chgnet_runs.py`](mofmorph/chgnet_runs.py) | Access to the CHGNet result folders in [`data/chgnet_morphograph_runs/`](../../data/chgnet_morphograph_runs/) |
| [`render.py`](mofmorph/render.py) | Drawing of shapes for the figures |

## Run scripts, in order

| Script | Produces | Website page |
|---|---|---|
| [`run_phase1.py`](run_phase1.py) | `results/phase1_results.json`, morph-family and graph-rule figures | Morphology |
| [`run_cif_to_shape.py`](run_cif_to_shape.py) | `results/cif_to_shape.json`: every step from each CIF to its BFDH shape, symmetry found by direct search and checked with spglib | CIF to Shape |
| [`run_phase3.py`](run_phase3.py), [`figs_phase3.py`](figs_phase3.py) | `results/phase3_results.json`, slice and shape figures | Graph Faces |
| [`run_phase4.py`](run_phase4.py), [`figs_phase4.py`](figs_phase4.py) | `results/phase4_results.json`, Wulff shapes | Surface Energy |
| [`run_deform.py`](run_deform.py), [`figs_deform.py`](figs_deform.py) | `results/deform_results.json`, 52 deformed cells | Cell Deform |
| [`run_hybrid.py`](run_hybrid.py) | `results/hybrid_results.json` | Hybrid |
| [`run_bond_sensitivity.py`](run_bond_sensitivity.py) | `results/bond_sensitivity.json` (metal–ligand cost ×1, ×0.5, ×0.25) | Experiment |
| [`run_core.py`](run_core.py) | `results/core_results.json`, shapes of eight CoRE MOFs of six crystal systems | Experiment |
| [`slab_check.py`](slab_check.py) | `results/slab_pieces.json`: detached pieces in every CHGNet slab | Experiment |
| [`run_chgnet_cleavage.py`](run_chgnet_cleavage.py) | `results/chgnet_cleavage_results.json` | Experiment |
| [`slab_options_check.py`](slab_options_check.py) | `results/slab_options.json` (needs pymatgen) | Experiment |
| [`figs_experiment.py`](figs_experiment.py) | The methods-versus-experiment figure | Experiment |

Then [`data/experimental_morphology/compare/compare_with_project.py`](../../data/experimental_morphology/compare/compare_with_project.py)
scores every model against the benchmark, and `python website/_build/build_site.py` rebuilds the pages
(after the matching `website/_build/build_*_fragment.py`).

## Checks

| Script | Checks |
|---|---|
| [`tests.py`](tests.py) | 14 checks: lattice absences, exact shape thresholds, known solids |
| [`tests_phase3.py`](tests_phase3.py) | Phase 3 against textbook nets |
| [`tests_phase4.py`](tests_phase4.py) | Phase 4 against exact surface energies |
| [`tests_deform.py`](tests_deform.py) | Phase 1b: subgroup symmetry and the box criterion |
| [`tests_review.py`](tests_review.py) | The fixes made in the review of 14 October 2026 |

The browser engines `website/mof_morphology.js`, `website/mof_deform.js` and `website/mof_cif_shape.js`
are independent second implementations; `website/tests/test_morphology.js`, `test_morph_pages.js` and
`test_cif_to_shape.js` check them against the JSON files in `results/`.

## Other folders

* [`chgnet_wulff/`](chgnet_wulff/): CHGNet surface energies to Wulff shapes, compared with a laboratory table, with its Colab notebook.
* [`tools/`](tools/): builders of the hybrid and symmetric-slab notebooks in [`notebooks/morphograph_mof/`](../../notebooks/morphograph_mof/).
* [`DFT_CHECK_PLAN.md`](DFT_CHECK_PLAN.md): the six CHGNet slabs to recompute with DFT and how to read the answer.
* `data/hMOF-0.cif`: the hMOF-0 structure used for the first CHGNet run.

## Limits

The force-field energies are unrelaxed and have no solvent, charges or temperature; the CHGNet
energies are upper bounds (cleavage energies) and have not been checked against DFT; the MOF-5 cube of
the force-field model depends on the flat bond cost; with four MOFs no model can be ranked.
