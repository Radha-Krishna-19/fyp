# Isha's notebook v4 (15 November 2026): the team's final code

`MOF_Wulff_steps1-8_plus_GNN_v4.ipynb` exactly as received (SHA-256
`cc0f09a2b03b61331304bec6e5e259d38035f7617aad09768b4e2be154d4daef`). Do not edit it.

It is the 14 November team notebook plus:
- **Morphology spectrum** (`morphspec.py`, cells 14, 14a, 14b, 14c): for one MOF, the favoured shape from its γ, every
  shape class its face set can produce when the γ ratios change, and the smallest change in a γ ratio that reaches each
  class. Structure only (no solvent, temperature or additive inputs).
- `mofwulff.wulff(..., bounded=None)`: skips the closed-shape linear programme when it is already known (speed only).

`mofwulff.py`, `mofgnn.py`, `morphspec.py` here are the modules the notebook writes (cells 3, 16 and 24), extracted
so they can be imported outside Colab.

| File | What it is |
|---|---|
| `spectrum_figures_MIL-125/` | Isha's 21 output images for MIL-125 (fig_01 GNN spectrum bars, fig_02 GNN favoured shape, fig_03–fig_10 and fig_12 GNN shape classes, fig_11 CHGNet spectrum bars, fig_13–fig_20 CHGNet shape classes, fig_21 CHGNet favoured shape) |
| `spectrum_on_corrected_run.py`, `spectrum_corrected_liquid_water.json` | `morphspec.py` unchanged, run on the corrected GPU run's energies at liquid water for ZIF-8, HKUST-1, UiO-66 and Mg-MOF-74 |
| `merge_proposal/` | A proposal only: v4's spectrum cells added to the corrected notebook (`make_merged_notebook.py` builds it) |

Checks run on 16 November (CPU): `morphspec.run_self_tests()` with v4's modules, 20/20 PASS (ZIF-8 and IRMOF-1 CIFs;
also Mg-MOF-74 and HKUST-1 in a second run); with the corrected modules plus the `bounded=` change, 22/22 PASS.

What differs from the corrected notebook, and the case for merging: `docs/v4_vs_corrected.md`.
