# Spectrum pipeline (Part 1)

From a CIF file to the multifractal spectrum of the MOF's building-block graph. The method, the
results and their withdrawal are explained on the website pages
[Decomposition](https://radha-krishna-19.github.io/fyp/decomposition.html),
[Network](https://radha-krishna-19.github.io/fyp/network.html),
[Spectrum](https://radha-krishna-19.github.io/fyp/spectrum.html) and
[Results](https://radha-krishna-19.github.io/fyp/results.html), and in the
[team paper](../../docs/paper/G070_Paper.pdf). Requirements: `numpy networkx` (and `matplotlib` for figures).

## The published decomposition (Python translation, used unmodified)

| File | Step |
|---|---|
| [`code_00_pipeline_driver.py`](code_00_pipeline_driver.py) | Runs the chain end to end for one CIF: `python code_00_pipeline_driver.py HKUST-1.cif` |
| [`code_01_cif_input.py`](code_01_cif_input.py) | Reads the cell, symmetry and atoms |
| [`code_02_bond_assignment_pbc.py`](code_02_bond_assignment_pbc.py) | Bonds from covalent radii with a 27-image periodic search |
| [`code_03_element_classification.py`](code_03_element_classification.py) | Metal / non-metal classification |
| [`code_04a_metal_oxo_algorithm.py`](code_04a_metal_oxo_algorithm.py) | The metal-oxo decomposition into nodes and linkers (used throughout); `code_04b`, `code_04c` are the single-node and all-node variants |
| [`code_05_centroid_simplification.py`](code_05_centroid_simplification.py) | Each building block collapsed to one point |
| [`code_06_systre_topology_export.py`](code_06_systre_topology_export.py) | Export to Systre (`.cgd`); outputs in [`topology_exports/`](topology_exports/) |
| [`code_07a_mofid_assembly.py`](code_07a_mofid_assembly.py), [`code_07b_mofkey_assembly.py`](code_07b_mofkey_assembly.py) | MOFid and MOFkey strings |

## The project's analysis

| File | What it establishes | Output |
|---|---|---|
| [`code_09_network_analysis.py`](code_09_network_analysis.py) | Labelled quotient graph, coordination numbers, centrality, Laplacian spectrum | printed |
| [`code_10_multifractal_spectrum.py`](code_10_multifractal_spectrum.py) | Influential-node multifractal spectrum (iNMFA) and the reference band | printed |
| [`code_11_nmfa_paper.py`](code_11_nmfa_paper.py) | NMFA exactly as published (box growing) | printed |
| [`code_12_converged_band.py`](code_12_converged_band.py) | Coarse-grained quotient graph replicated without atoms; the convergence test | used by 13–19 |
| [`code_13_scaling_regimes.py`](code_13_scaling_regimes.py) | Two scaling regimes in the atomic graph | `size_scaling/scaling_regimes.json` |
| [`code_14_size_strata.py`](code_14_size_strata.py) | Narrow/Medium/Wide classes follow graph size | `size_scaling/size_strata.json` |
| [`code_15_dataset_sweeps.py`](code_15_dataset_sweeps.py) | Slope of Δα against ln D on both datasets (capped) | `size_scaling/slope_sweep_*.json` |
| [`code_16_topological_diversity.py`](code_16_topological_diversity.py) | Nets present in the datasets | `size_scaling/topological_diversity.json` |
| [`code_17_full_correct_band.py`](code_17_full_correct_band.py) | The band of all 77 hMOF and 61 CoRE MOF on the coarse-grained graph | `size_scaling/full_band_*_cg.json` |
| [`code_18_subband_explain.py`](code_18_subband_explain.py) | Nine-category comparison of the classes | `size_scaling/subband_explain_*.json` |
| [`code_19_spectrum_vs_shape.py`](code_19_spectrum_vs_shape.py) | Spectrum of finite MOF-5 particles (cube, slab, plate, rod) | `size_scaling/spectrum_vs_shape_*.json` |

Outputs go to [`data/spectrum_descriptors/size_scaling/`](../../data/spectrum_descriptors/size_scaling/);
the structure sets are read from [`data/structures/`](../../data/structures/). Run each module from this folder.

## Checks and drivers

| File | Purpose |
|---|---|
| [`_ci_smoke_test.py`](_ci_smoke_test.py) | Coordination-number checks run by GitHub Actions on every push |
| [`_prove_ordering_equivalence.py`](_prove_ordering_equivalence.py) | Coarse-grain-then-replicate gives the same graph as replicate-then-coarse-grain (five cases, full isomorphism) |
| [`_run_size_scaling.py`](_run_size_scaling.py) | Finite-size and q-range convergence sweep on four nets |
| [`_test_window_frac.py`](_test_window_frac.py) | Effect of a half-diameter fitting window |
| [`_make_strata_figure.py`](_make_strata_figure.py) | Size-strata figure |

The four demonstration structures (`HKUST-1.cif`, `MOF5.cif`, `UiO-66.cif`, `ZIF-8.cif`; nets tbo, pcu,
fcu, sod) are in this folder. Spectrum settings used everywhere since 16 September 2026: top 20 %
of vertices by degree are influential; radii fitted up to half the diameter; τ(q) fitted through the
origin; ln Z averaged over trials.
