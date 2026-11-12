# The morphology map (10 November 2026)

For a cubic crystal bounded by {100}, {110} and {111}, the Wulff shape depends only on
x = γ110/γ100 and y = γ111/γ100. This folder computes that map exactly, places every model of the
project on it, tests it against the laboratory dataset, and lists the possible morphologies of a
given CIF. Proposed by Keerthi (steps 9 and 10 of the team plan); made exact and tested here.
Written up on the website page "The morphology map" (`website/morphology_map.html`).

Every script runs from any folder and writes its result next to itself. Defaults point at the
repository's own data, so no arguments are needed.

| Script | What it does | Writes |
|---|---|---|
| `cubic_wulff.py` | Exact Wulff shape and area fractions for given γ100, γ110, γ111; shape class from the closed-form limits. Self-test: `python cubic_wulff.py` | (prints) |
| `phase_grid.py` | Shape class on a 150 × 150 grid of (x, y), about 50 s | `phase_grid.npz` |
| `model_points.py` | Every model of the project as a point per MOF (reads `../results/` and `../steps1_8_check/`) | `model_points.json` |
| `series_test.py` | Test 1: laboratory series placed on the map; do they move monotonically? | `series_results.json` |
| `condition_model.py` | Test 2: leave-one-paper-out prediction of the dominant face, four models | `condition_model_results.json`, `condition_model_predictions.csv` |
| `modulator_caps.py` | Test 3: water caps against formate caps (static, first attempt). Needs CHGNet and pymatgen; by default reads the steps 1–8 module, the four input CIFs and the quick results from `../steps1_8_check/` | `modulator_caps_results.json` |
| `possible_morphs.py` | Possible morphologies of a CIF: lower one face energy at a time from the structure's point | `possible_morphs.json` |
| `dimension_along_map.py` | Link to Part 1: r½/D of MOF-5 crystals cut along both map axes (uses `code/spectrum_shape_relation/`) | `dimension_along_map.json` |
| `figures.py` | The three figures (copied to `website/figures/map/` by `website/_build/build_map_fragment.py`) | `fig_map_regions.png`, `fig_map_models.png`, `fig_conditions.png` |

Order to regenerate everything: `phase_grid.py`, `model_points.py`, `series_test.py`,
`condition_model.py`, `possible_morphs.py`, `dimension_along_map.py`, `figures.py`; then
`python website/_build/build_map_fragment.py` and `python website/_build/build_site.py`.

Requirements beyond `requirements.txt`: pandas (for `series_test.py`, `condition_model.py`,
`possible_morphs.py`).

Limits: cubic crystals only; plates, rods and intergrown crystals are outside any Wulff model;
`modulator_caps.py` uses unrelaxed caps and is not physical for UiO-66.

## Reproducibility check (12 November 2026)

Every script above was rerun from another folder. `phase_grid.py`, `model_points.py`, `series_test.py`,
`condition_model.py`, `possible_morphs.py` and `dimension_along_map.py` reproduce their result files
exactly. `modulator_caps.py` (CHGNet, static) reproduces to within 0.003 eV per site: HKUST-1 ε{110}
came out −1.3596 eV against −1.3573 eV in `modulator_caps_results.json`, which moves a few points of the
HKUST-1 and UiO-66 paths across a region boundary (for example truncated octahedron → octahedron at the
far end of the HKUST-1 path). The values quoted on the website (two decimals) and the direction of each
shift are unchanged. The committed file is the 10 November run.
