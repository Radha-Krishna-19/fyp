# Phase 2 result files

Each file is written by one script in the parent folder. Do not edit them by hand; rerun the script. The website tests compare
the browser engines against these files.

| Result file | Written by | Content |
|---|---|---|
| `phase1_results.json` | `run_phase1.py` | Space group, allowed faces, BFDH shapes and morph families of the four demonstration MOFs |
| `cif_to_shape.json` | `run_cif_to_shape.py` | Every step from CIF to BFDH shape (the CIF to Shape page) |
| `deform_results.json` | `run_deform.py` | Shapes of stretched and sheared cells (plates and rods) |
| `phase3_results.json` | `run_phase3.py` | Faces from the periodic graph |
| `phase4_results.json` | `run_phase4.py` | Force-field face energies and Wulff shapes |
| `hybrid_results.json` | `run_hybrid.py` | BFDH, Wulff and blended shapes for any CIF |
| `core_results.json` | `run_core.py` | The same applied to CoRE MOF structures |
| `bond_sensitivity.json` | `run_bond_sensitivity.py` | Effect of the bond-energy cost on the force-field result |
| `chgnet_cleavage_results.json` | `run_chgnet_cleavage.py` | CHGNet cleavage energies |
| `slab_pieces.json` | `slab_check.py` | Slab pieces used for the CHGNet energies |
| `slab_options.json` | `slab_options_check.py` | Comparison of slab choices |
| `figs/` | `figs_*.py` | Figures (named by MOF and model, for example `MOF-5_bfdh.png`) |
