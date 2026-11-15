# Team notebook of 14 November 2026: negative surface energies, checked and corrected

Note (16 November): the team's final notebook is version 4 in `../nb_2026-11-15_v4_isha/`. It adds the morphology spectrum and does not contain the corrections below; see `docs/v4_vs_corrected.md`.

`MOF_Wulff_steps1_8_plus_GNN.ipynb` is the team's CIF-to-Wulff notebook (steps 1–8, a MACE-MP-0 check, CP2K inputs, and a GNN surrogate for relaxed surface energies), with its outputs, as received on 15 November 2026 (SHA-256 `518c5d90…4c33c53a117f1856a5cf0f2ea05da74c4be9`). It reported negative relaxed surface energies for six slabs. This folder records what caused them, the fixes, and the corrected results. The explanation for a general reader is on the website page *ML energies and water* (`ml_energies.html`).

## Findings

1. **The water reference.** γ = (E_slab − N·e_bulk − n·E_H2O)/2A uses one water molecule at 0 K, so the caps are paid for at the highest possible chemical potential. With Δμ_H2O from NIST-JANAF and CODATA, γ(Δμ) = γ₀K − n·Δμ/2A. At liquid water, 298 K (Δμ = −0.5695 eV), none of the 109 relaxed slabs is negative. The face order, and so the shape, changes with Δμ for several MOFs.
2. **K3 and K11 are missing** from this version of the notebook (they were fixed on 10 November in `../kshitij_k11fix/`). For Mg-MOF-74 {2̅10} the slab is cut from the unrelaxed conventional cell: 378 atoms, relaxed γ −0.0135 J/m². With the fixes it has 126 atoms and γ = +0.002 J/m² (`../results_full_fixed/fix_Mg-MOF-74.log`).
3. **K12 (new).** `heal()` puts one proton on a linker O for every metal bond it lost, so a bridging O that loses two bonds becomes C–OH₂⁺. This happens in 26 of the 118 slabs of the 16 relaxed MOFs (Cd3BTB2, Mg-MOF-74 and Ni-DOBDC; `results/k12_count.json`). Fixed: at most one H per donor atom, and each surplus proton turns the nearest metal–OH cap into a water molecule bound to the metal. Atoms, charge balance and n are unchanged.
4. **GNN labels.** The six γ ≤ 0 values were used as training labels for a model whose output is softplus, and therefore always positive. The corrected `mofgnn.py` provides `at_water_mu()`, which moves every label to a stated water condition. `load_dataset(..., drop_nonpositive=True)` now drops labels ≤ 0 and prints which ones it dropped.

## Files

| File | What it is |
|---|---|
| `notebook_module/mofwulff.py`, `notebook_module/mofgnn.py` | The modules exactly as the notebook writes them (cells 3 and 16) |
| `notebook_module/run_static.py` | Rebuilds every slab with the notebook module: bulk relaxed as in the notebook, slabs static |
| `mofwulff.py` | Corrected module: K3, K11, K12 (`heal(..., one_proton_per_donor=True)`), `gamma_J_m2(..., dmu_water)`, `WATER_DMU_EV`, `gamma_at_mu()`, and step 8 at `config["water_dmu_eV"]` (default liquid water, 298 K). Stored `gamma_*_J_m2` columns stay at Δμ = 0, so they remain comparable with older runs |
| `MOF_Wulff_steps1_8_plus_GNN_corrected.ipynb`, `make_corrected_notebook.py` | The team notebook with every correction, outputs cleared; runs on Colab or any Jupyter and puts a results zip in the Downloads folder after each stage. Rebuild it with `python make_corrected_notebook.py`. Checked on 15 November by running it end to end in quick mode with nbclient (ZIF-8, and after the K5–K10 fixes UiO-66): no errors, four zips written |
| `mofgnn.py` | Corrected GNN module: `at_water_mu()`, `load_dataset(drop_nonpositive=True)`, and pretraining on positive static γ only |
| `run_static.py`, `relax_cases.py` | The slab rebuild; the relaxations of the negative slabs (`notebook` = the notebook module; `fixed` = corrected module, water caps and bare) |
| `water_mu_analysis.py` | Joins the notebook's printed γ with the rebuilt slabs (n, A), checks that they are the same slabs, applies γ(Δμ) and recomputes the shapes. Writes `results/water_mu.json` and `.csv` |
| `water_mu_sweep.py` | Main face against Δμ for every MOF; figures in `figs/` |
| `relax_summary.py`, `cap_chemistry.py` | What the caps become after relaxation: M–OH, bound H₂O, free H₂O, C–O–H. Writes `results/relax_cases.json` |
| `k12_count.py` | How many slabs contain C–OH₂⁺ |
| `gnn_rerun.py` | Cross-validation of the GNN and baselines with the original and the corrected labels. Writes `results/gnn_rerun.json` |
| `make_water_figures.py` | Schematic figures (capping, water conditions) |

## Reproduce (CPU; about an hour in total, longer for the GNN)

```
cd code/morphology/steps1_8_check/nb_2026-11-14
python notebook_module/run_static.py <cif dir> work/static16
python notebook_module/run_static.py <cif dir> work/static41 <41 names, comma separated> static_bulk
python water_mu_analysis.py MOF_Wulff_steps1_8_plus_GNN.ipynb work/static16 results/water_mu.json
python water_mu_sweep.py results/water_mu.csv work/static16 figs
python relax_cases.py notebook_module <cif dir> work/relax_nb notebook
python relax_cases.py . <cif dir> work/relax_fixed fixed
python relax_summary.py work/relax_nb work/relax_fixed results/relax_cases.json
python k12_count.py work/static16 results/k12_count.json
python gnn_rerun.py MOF_Wulff_steps1_8_plus_GNN.ipynb work/static16 work/static41 work/gnn
```

The CIFs are the RASPA2 files that the notebook downloads, from `https://raw.githubusercontent.com/iRASPA/RASPA2/master/structures/mofs/cif/<name>.cif`. The first four are also in `../input_cifs/`, with checksums.

## Water chemical potential (eV per molecule, relative to the 0 K molecule)

| Condition | Δμ |
|---|---|
| A: free molecule, 0 K (the notebook) | 0 |
| B: vapour, 298.15 K, 1 bar | −0.4809 |
| C: liquid water, 298.15 K (reference) | −0.5695 |
| D: vapour, 298.15 K, 50 % relative humidity | −0.5874 |
| E: vapour, 400 K, 1 bar | −0.6857 |

Sources:

- NIST-JANAF table H-064 (H₂O, ideal gas): H(298.15) − H(0) = 9.904 kJ/mol, S(298.15) = 188.834 J/mol/K; at 400 K, H − H(298.15) = 3.452 kJ/mol and S = 198.788 J/mol/K.
- CODATA: ΔfG°(gas) = −228.582 kJ/mol and ΔfG°(liquid) = −237.129 kJ/mol, so ΔG_vap = 8.547 kJ/mol.

Zero-point and vibrational energies are left out of both the free molecule and the caps (they partly cancel). The remaining uncertainty is about 0.1 eV per molecule.
