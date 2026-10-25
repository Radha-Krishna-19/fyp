# Spectrum and crystal shape: joining the two parts of the project

Part 1 of the project described each MOF by the width Δα of the multifractal spectrum of its
building-block graph ([`code/spectrum_pipeline/`](../spectrum_pipeline/)). Part 2 predicts the
crystal shape from the unit cell ([`code/morphology/`](../morphology/)). Both start from the same
labelled quotient graph. This folder tests whether the two are related, as the guide asked: can
anything about morphology be concluded from the spectra? The results and their interpretation are on
the website page [Spectrum ↔ Shape](https://radha-krishna-19.github.io/fyp/relation.html).

## How to run

The notebook [`Spectrum_Shape_Relation.ipynb`](Spectrum_Shape_Relation.ipynb) is the entry point.

* **Locally (Jupyter or VS Code).** Open the notebook from this folder and run all cells. It installs
  the libraries, runs every calculation (about 20 minutes), draws the figures and runs the checks.
* **Google Colab.** Run `python make_colab_bundle_spectrum_shape_relation.py` locally; it writes
  `build/spectrum_shape_relation_bundle.zip` at the repository root. Open the notebook in Colab, run
  all cells and upload the zip when asked. Download the `results/` folder at the end.

Every line the notebook prints is also written to
[`results/RUN_REPORT_spectrum_shape_relation.md`](results/RUN_REPORT_spectrum_shape_relation.md).
The results in [`results/`](results/) are from the run of 16 October 2026 (all calculations
recomputed, 15 of 15 checks passed).

## Files, in the order they run

| File | Question | Writes |
|---|---|---|
| [`particle_graph_tools.py`](particle_graph_tools.py) | Shared tools: quotient graph with block positions, finite particles (boxes and polyhedra), spectrum width, size trend | – |
| [`run_01_spectrum_of_box_particles_same_cell_count.py`](run_01_spectrum_of_box_particles_same_cell_count.py) | At equal cell count (64), do MOF-5 cubes, slabs, plates and rods differ in Δα beyond what their diameters explain? Checked against `code_19` | [`results/01_box_particles_MOF5.json`](results/01_box_particles_MOF5.json) |
| [`run_02_spectrum_of_predicted_crystal_shapes_MOF5.py`](run_02_spectrum_of_predicted_crystal_shapes_MOF5.py) | Do the MOF-5 crystal shapes predicted by BFDH, the BFDH × Wulff blend, UFF Wulff and CHGNet, and the cube, octahedron and rhombic dodecahedron, differ in Δα at about 2000 and 4000 blocks? | [`results/02_predicted_crystal_shapes_MOF5.json`](results/02_predicted_crystal_shapes_MOF5.json) |
| [`run_03_core_mof_spectrum_width_vs_bfdh_shape.py`](run_03_core_mof_spectrum_width_vs_bfdh_shape.py) | Across 55 CoRE MOF 2019 structures, is the periodic Δα related to the BFDH shape (sphericity, aspect ratio), with and without graph size held fixed? | [`results/03_core_mof_spectrum_vs_bfdh_shape.json`](results/03_core_mof_spectrum_vs_bfdh_shape.json) |
| [`make_figures_spectrum_shape_relation.py`](make_figures_spectrum_shape_relation.py) | Draws the figures and copies them to [`website/figures/relation/`](../../website/figures/relation/) | [`figures/`](figures/) |
| [`check_spectrum_shape_relation.py`](check_spectrum_shape_relation.py) | 15 checks: known answers, agreement with `code_19`, internal consistency | prints PASS/FAIL |
| [`make_notebook_spectrum_shape_relation.py`](make_notebook_spectrum_shape_relation.py) | Writes the notebook (edit this file, not the `.ipynb`) | `Spectrum_Shape_Relation.ipynb` |
| [`make_colab_bundle_spectrum_shape_relation.py`](make_colab_bundle_spectrum_shape_relation.py) | Zip of every file the notebook needs, for Colab | `build/spectrum_shape_relation_bundle.zip` |

## Inputs from the rest of the repository

* Structures: [`code/spectrum_pipeline/MOF5.cif`](../spectrum_pipeline/MOF5.cif),
  [`ZIF-8.cif`](../spectrum_pipeline/ZIF-8.cif) and the 61 CoRE MOF 2019 CIFs in
  [`data/structures/core_mof_2019/`](../../data/structures/core_mof_2019/).
* Spectrum: [`code/spectrum_pipeline/code_12_converged_band.py`](../spectrum_pipeline/code_12_converged_band.py).
* Shapes: [`code/morphology/results/hybrid_results.json`](../morphology/results/hybrid_results.json)
  (BFDH and UFF Wulff) and
  [`chgnet_cleavage_results.json`](../morphology/results/chgnet_cleavage_results.json) (CHGNet).
* Δα of the CoRE MOFs:
  [`data/spectrum_descriptors/size_scaling/full_band_core_cg.json`](../../data/spectrum_descriptors/size_scaling/full_band_core_cg.json)
  (from `code_17`).

## Spectrum settings

Top 20 % of blocks by degree are influential; radii from 1 to half the diameter; 20 trials; seeds 0–4.
The error bars are the spread over seeds only, not the uncertainty of the method.
