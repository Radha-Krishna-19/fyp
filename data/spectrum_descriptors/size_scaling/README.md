# Phase 1 size-scaling results

Results of the finite-size and band analyses, each written by one script in `code/spectrum_pipeline/` (the figure scripts here
read the JSON files and draw the figures).

| File | Written by | Content |
|---|---|---|
| `convergence_sweep.json`, `convergence_figure.png` | `_run_size_scaling.py`, `make_convergence_figure.py` | Δα against supercell size on four nets (never converges) |
| `scaling_regimes.json` | `code_13_scaling_regimes.py` | Molecular and framework scaling regimes |
| `size_strata.json`, `size_strata_figure.png` | `code_14_size_strata.py` | Are the Narrow, Medium and Wide classes chemistry or size? |
| `slope_sweep_hmof.json`, `slope_sweep_core.json`, `slope_sweep_figure.png` | `code_15_dataset_sweeps.py`, `make_slope_figure.py` | Slope of Δα against ln(diameter) across frameworks |
| `topological_diversity.json` | `code_16_topological_diversity.py` | A topologically diverse comparison set |
| `full_band_hmof_cg.json`, `full_band_core_cg.json`, `full_band_figure.png`, `full_band_vs_size.png` | `code_17_full_correct_band.py`, `make_full_band_figure.py` | The band on the coarse-grained graph for both datasets |
| `subband_explain_hmof.json`, `subband_explain_core.json` | `code_18_subband_explain.py` | What distinguishes the three classes |
| `grouped_spectra_figure.png` | `make_grouped_spectra_figure.py` | Spectra grouped by class |
| `spectrum_vs_shape_MOF5.json`, `spectrum_vs_shape_ZIF8.json`, `spectrum_vs_shape_figure.png` | `code_19_spectrum_vs_shape.py`, `make_spectrum_vs_shape_figure.py` | Spectrum against particle shape |

`capped_pool_hmof.txt` and `capped_pool_core.txt` list the 34 hMOF and 20 CoRE MOF CIFs that `code_14`,
`code_15` and `code_16` first ran on (15 September 2026). The scripts use these lists by default so that
`size_strata.json`, `slope_sweep_*.json` and `topological_diversity.json` regenerate exactly; pass `--all`
to run on every CIF in `data/structures/`, which gives a different sample (for example a CoRE MOF slope
mean of 0.812 instead of 0.871).
