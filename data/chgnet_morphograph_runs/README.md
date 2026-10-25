# CHGNet (MorphoGraph-MOF) runs

Output of the MorphoGraph-MOF notebook
([`notebooks/morphograph_mof/`](../../notebooks/morphograph_mof/)), run in Google Colab with the
CHGNet machine-learned potential. One folder per run:

| Folder | Structure | Notebook | Slabs |
|---|---|---|---|
| [`MOF-5_2026-10-14/`](MOF-5_2026-10-14/) | MOF-5 | `MorphoGraph_MOF_colab_4MOFs.ipynb` | initial and relaxed |
| [`HKUST-1_2026-10-14/`](HKUST-1_2026-10-14/) | HKUST-1 (primitive cell) | `MorphoGraph_MOF_colab_4MOFs.ipynb` | initial and relaxed |
| [`UiO-66_2026-10-14/`](UiO-66_2026-10-14/) | UiO-66 (F-43m ordering) | `MorphoGraph_MOF_colab_4MOFs.ipynb` | initial and relaxed |
| [`hMOF-0_2026-10-12/`](hMOF-0_2026-10-12/) | hMOF-0 | `MorphoGraph_MOF_revised.ipynb` | initial only (the run stopped before relaxation) |

Each folder holds `<MOF>_working_cell.cif` and `<MOF>_bulk_relaxed_fixed_cell.cif` (the cells),
`slabs_initial_unique/` and `slabs_relaxed/` (one CIF per face and termination),
`<MOF>_surface_pair_records.csv` (energy of every slab), `<MOF>_surface_pair_fit_summary.csv`
(whether individual face energies could be separated), `<MOF>_surface_energies_individual.csv`,
`<MOF>_metadata.json` (settings and versions) and `particles/` (two reference particles).

**How the files are used.** A slab has two faces, so each slab energy gives the sum of two face
energies; the pair fits were underdetermined for every face. The project therefore uses the cleavage
energy (half the smallest slab excess), an upper bound on the lowest termination energy, computed by
[`code/morphology/run_chgnet_cleavage.py`](../../code/morphology/run_chgnet_cleavage.py); detached
fragments in the slabs are listed by [`slab_check.py`](../../code/morphology/slab_check.py). The
analysis is on the [Experiment page](https://radha-krishna-19.github.io/fyp/experiment.html).
