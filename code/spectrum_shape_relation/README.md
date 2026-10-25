# Spectrum ↔ crystal shape: joining the two halves of the project

**Folder:** `code/spectrum_shape_relation/`  ·  **Created:** 2026-10-16

## Why this folder exists
The first half of the project (before Panel Review 1) described each MOF by the width Δα of
a multifractal spectrum of its building-block graph (`code/spectrum_pipeline/code_09` … `code_18`). The second
half (after the panel) predicts the crystal **shape** from the unit cell (`code/morphology/`).
Both start from the same labelled quotient graph. This folder tests whether the two are related.

## How to run (the notebook is the main entry point)
**On your PC:** open `Spectrum_Shape_Relation.ipynb` in Jupyter or VS Code *from this folder*
and press "Run all". It installs the libraries, runs every calculation (about 20 minutes), draws
the figures and runs the checks.

**In Google Colab:** first run `python make_colab_bundle_spectrum_shape_relation.py` on your PC
(it writes `fyp/_work/spectrum_shape_relation_bundle.zip`), open the notebook in Colab, run all,
and upload that zip when asked. At the end download the `results` folder.

Every line the notebook prints is also saved in
`results/RUN_REPORT_spectrum_shape_relation.md`, so the results can be read without screenshots.

## Files, in the order they run
| File | What it does | Writes |
|---|---|---|
| `particle_graph_tools.py` | Shared tools: quotient graph with block positions, finite particles (boxes and polyhedra), spectrum width, size trend | – |
| `run_01_spectrum_of_box_particles_same_cell_count.py` | MOF-5 (and ZIF-8, not used) cut as cube / slab / plate / rod at 64 cells; size trend on cubes; checks against `code_19` | `results/01_box_particles_MOF5.json`, `…_ZIF8.json` |
| `run_02_spectrum_of_predicted_crystal_shapes_MOF5.py` | MOF-5 crystals cut to the shapes predicted by BFDH, the BFDH×Wulff blend, UFF Wulff and CHGNet, plus cube / octahedron / rhombic dodecahedron, at ~2000 and ~4000 blocks | `results/02_predicted_crystal_shapes_MOF5.json` |
| `run_03_core_mof_spectrum_width_vs_bfdh_shape.py` | 55 CoRE MOFs: periodic Δα against the BFDH shape (sphericity, aspect ratio), raw and with graph size held fixed | `results/03_core_mof_spectrum_vs_bfdh_shape.json` |
| `make_figures_spectrum_shape_relation.py` | Draws the three figures and copies them to the website | `figures/0*.png`, `website/figures/relation/` |
| `check_spectrum_shape_relation.py` | 15 checks (known answers, agreement with `code_19`, internal consistency) | prints PASS/FAIL |
| `make_notebook_spectrum_shape_relation.py` | Writes the notebook (edit this, not the .ipynb, to change it) | `Spectrum_Shape_Relation.ipynb` |
| `make_colab_bundle_spectrum_shape_relation.py` | Zip of everything the notebook needs, for Colab | `fyp/_work/spectrum_shape_relation_bundle.zip` |
| `data/core_mof_cifs/` | Copy of the 61 CoRE MOF CIFs (from `fyp/_work/core_cifs`) so this folder is complete | – |

## Inputs from the rest of the project
`code/spectrum_pipeline/MOF5.cif`, `code/spectrum_pipeline/ZIF-8.cif`; `code/spectrum_pipeline/code_12_converged_band.py` (spectrum);
`code/morphology/results/hybrid_results.json` (BFDH and UFF Wulff distances);
`code/morphology/results/chgnet_cleavage_results.json` (CHGNet cleavage energies);
`data/spectrum_descriptors/size_scaling/full_band_core_cg.json` (Δα of the CoRE MOFs, from `code_17`).

## Spectrum settings
Top 20 % of blocks by degree as influential; radii 1 … half the diameter; 20 trials; seeds 0–4.
The error bars are the seed spread only, not the uncertainty of the method.
