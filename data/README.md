# Data

| Folder | Contents | Used by |
|---|---|---|
| [`structures/`](structures/) | Crystal structures: the 77 hMOF and 61 CoRE MOF 2019 CIF files used by every analysis | `code/spectrum_pipeline/code_13`–`code_18`, `code/spectrum_shape_relation/run_03`, `code/morphology/run_core.py` |
| [`spectrum_descriptors/`](spectrum_descriptors/) | The released spectrum descriptor dataset (CC BY 4.0), the convergence, slope and size-strata results, and an independent 76-structure run | Part 1, the Results page |
| [`experimental_morphology/`](experimental_morphology/) | 134 laboratory crystal-shape records with synthesis conditions (35 papers, 12 MOFs), kinetics and CO<sub>2</sub> uptake tables, and the comparison of every shape model with experiment | Part 2, the Experiment page |
| [`chgnet_morphograph_runs/`](chgnet_morphograph_runs/) | Output of the MorphoGraph-MOF (CHGNet) notebook for MOF-5, HKUST-1, UiO-66 and hMOF-0 | `code/morphology/run_chgnet_cleavage.py`, `slab_check.py` |

The four demonstration structures (HKUST-1, MOF-5, UiO-66, ZIF-8) are kept with the code that reads
them, in [`code/spectrum_pipeline/`](../code/spectrum_pipeline/), and in [`website/`](../website/) for the browser.
