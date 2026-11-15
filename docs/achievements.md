# What the project has achieved: the achievements register

15 November 2026. Each entry is a capability that has been run and checked, written in the form set by the master prompt (version 3, section 2A). The verdicts are those of section D9. Numbers are taken from the result files named; re-verify them there before quoting them.

---

## 1. From a CIF to the faces and shapes a MOF crystal can take (the main deliverable)

| | |
|---|---|
| **Capability** | Given the CIF file of a MOF, the program finds its symmetry, lists the crystal faces that symmetry allows, and draws the BFDH shape. For a cubic crystal it also gives the whole family of shapes the crystal can take, as a map. |
| **Input** | Any CIF file readable by ASE. A hydrogen-free skeleton is also tried, because hydrogen positions often break the symmetry. |
| **Output** | Space group, lattice system, allowed face families with interplanar and effective spacings, area fraction of each face, BFDH habit (equant, rod, plate or lath), and for cubic crystals the position on the morphology map. |
| **How to run it** | `python3 code/morphology/cif_shape.py <file.cif>`, or the website page *From a CIF to a shape* (`cif_to_shape.html`), which accepts an uploaded file. |
| **How it was checked** | Two independent implementations (Python `run_general_shape.py`, JavaScript `mof_general_shape.js`) agree number by number (`website/tests/test_general_shape.js`). The rules are 16 proved propositions (*The mathematics* page). The program was run on all 138 dataset CIFs (`results/dataset_shapes.json`), and on 15 November on three files not used in its development: ZIF-8 (I-43m, {110} only, a rhombic dodecahedron), MIL-47 (Pnma, a rod) and ZnBDC (P2₁/c, equant). |
| **Status** | VALIDATED WITH LIMITATIONS |
| **Where it stops working** | Files stored without symmetry (P1; 71 of 77 hMOF files) give only a triclinic cell. Disordered or partly occupied files depend on the disorder policy. |
| **What it is not** | A prediction of which shape a laboratory will grow: it gives the shapes that symmetry and plane spacings imply. |

## 2. Surface energies and the Wulff shape of a cubic MOF

| | |
|---|---|
| **Capability** | Given a cubic MOF, the program computes the cleavage energy of every face and the Wulff shape that follows. |
| **Input** | CIF (cubic). |
| **Output** | γ per face (J/m²), the Wulff shape and its area fractions. |
| **How to run it** | `python3 code/morphology/run_phase4.py` |
| **How it was checked** | Exact results for simple lattices (`tests_phase4.py`). Convergence in pair cutoff and offset bins: at most 0.4 % change, with no change in face order (`check_energy_convergence.py`). Benchmark against 134 laboratory records (`run_benchmark_mofs.py` → `results/benchmark_mofs.json`): without additives, the predicted main face is right for 4 of 5 MOFs (32 records, 13 papers; 95 % paper-bootstrap interval 0.727–0.973). |
| **Status** | VALIDATED WITH LIMITATIONS (the main face); the energies themselves are COMPUTATIONALLY VALID BUT SCIENTIFICALLY UNVALIDATED |
| **Where it stops working** | The energy is in effect a broken-bond count (93–98 % of γ), so it cannot tell strong bonds from weak ones. It does not work for crystals grown with additives. Non-cubic lattices get BFDH only. |
| **What it is not** | An absolute surface energy. No value has been checked against DFT. |

## 3. Changing the unit cell gives plates and rods

| | |
|---|---|
| **Capability** | Given a MOF and a stretch or shear of its cell (atoms at fixed fractional coordinates), the program gives the shape the changed cell would form. |
| **How to run it** | `python3 code/morphology/run_deform.py`; `cif_shape.py <file> --stretch a b c`; the website page *Changing the cell*. |
| **How it was checked** | Propositions 14–16. 52 cases compared between Python and JavaScript (`website/tests/test_morph_pages.js`). |
| **Status** | VALIDATED (as mathematics) |
| **What it is not** | A synthesised framework: the changed cells are hypothetical. |

## 4. The morphology map of cubic crystals

| | |
|---|---|
| **Capability** | Given the three surface energies of a cubic crystal, the program places it on one exact map of every cubic shape. |
| **How it was checked** | The boundaries were derived by hand and in code. All six laboratory series that change shape follow the predicted order. |
| **Status** | VALIDATED WITH LIMITATIONS (six series is a small sample) |

## 5. Shape steering and gas access for ten MOFs

| | |
|---|---|
| **Capability** | For ten MOFs, the program computes how far each face's energy must fall to become the main face and to give its pure shape. It also computes how open each face is to CO₂ (radius 1.65 Å) and N₂ (radius 1.82 Å), and the diffusion length L = V/A at equal volume. |
| **How to run it** | `run_shape_steering.py`, `run_shape_adsorption.py`; the website page *The shape advisor*. |
| **How it was checked** | Closed-form steering factors checked numerically (`check_new_analyses.py`). Open fractions agree with an independent 3D estimate (51 checks). |
| **Status** | COMPUTATIONALLY VALID BUT SCIENTIFICALLY UNVALIDATED (relative to unvalidated energies; geometric indicators only) |
| **What it is not** | An adsorption or diffusion calculation. |

## 6. Machine-learned surface energies (team CHGNet notebook and GNN)

| | |
|---|---|
| **Capability** | Given a CIF, the notebook cuts slabs of whole building blocks, caps them with water and computes CHGNet energies (static and relaxed), then gives the Wulff shape. A GNN is trained to predict the relaxed γ without relaxation. |
| **How to run it** | `code/morphology/steps1_8_check/nb_2026-11-14/` (README there) or the notebook on Colab. |
| **How it was checked** | Every slab was rebuilt independently on CPU: atom counts identical, static γ within 0.0005 J/m². The negative relaxed values were reproduced and traced to the water reference, the missing K3/K11 fixes and a capping error (K12), all corrected. The MACE-MP-0 re-scoring gives the same face order for all four benchmark MOFs. |
| **Status** | CHEMICALLY OR PHYSICALLY QUESTIONABLE (the relaxed energies); the correction is VALIDATED as thermodynamics |
| **Corrected run (GPU, 15 November)** | At liquid-water conditions none of 98 relaxed slabs is negative (final run, all fixes); slab thickness 24 vs 36 Å changes γ by 0.004 J/m²; MACE-MP-0 ranks all slabs as CHGNet does (0.94–1.00). ZIF-8 (rhombic dodecahedron), HKUST-1 (mainly {111}) and now Mg-MOF-74 (a hexagonal rod along c) match the laboratory habit; UiO-66 (a truncated octahedron) does not. In leave-MOF-out cross-validation the GNN (MAE 0.131 J/m²) is behind a straight line on broken bonds per area (0.088) and rescaled static energies (0.084). Results: `nb_2026-11-14/colab_run_2026-11-15/`. |
| **Where it stops working** | No DFT check. Relaxation lowers γ by 60–100 %. The result depends on the water condition. In cross-validation the GNN does not beat a linear fit on broken bonds per area. |

## 6b. Morphology spectrum: every shape a MOF's faces can make, and how far each is (team notebook v4)

| | |
|---|---|
| **Capability** | Given the surface energies of a MOF's faces (CHGNet, GNN or BFDH), the program lists every shape class the face set can produce when the energy ratios change, and the smallest change in an energy ratio that reaches each class, starting from the computed shape. |
| **Input** | A CIF (and a γ source), or the cached results of the pipeline. No solvent, temperature or additive inputs. |
| **Output** | Favoured shape; per class: name, faces present, area-fraction ranges, minimum ratio change (%), which face must become cheaper or dearer; ratio map and Wulff images. |
| **How to run it** | Notebook v4, cells 14a–14c (`code/morphology/steps1_8_check/nb_2026-11-15_v4_isha/`); `spectrum_on_corrected_run.py` there applies it to the corrected energies. |
| **How it was checked** | 20 built-in checks (analytic boundaries such as {111} vanishing at γ111/γ100 = √3, the cuboctahedron at 2/√3, bisection distance ≤ a direct 1-D walk, every reported γ vector re-checked): 20/20 pass with the v4 modules and 22/22 (with four real CIFs) with the corrected modules. |
| **Result** | On the corrected energies at liquid water: ZIF-8 and Mg-MOF-74 sit in the laboratory class (distance 0); HKUST-1's octahedron is 37.2 % away; UiO-66's modulated octahedron is 19.7 % away but its additive-free cube is 80.4 % away (`spectrum_corrected_liquid_water.json`). MIL-125 (team run, 0 K water reference): block/prism of {101}, with a plate 3.5 % away. |
| **Status** | COMPUTATIONALLY VALID (the scan and its distances); the distances inherit the unvalidated energies |
| **What it is not** | A prediction of which additive gives which shape. It gives how much an energy ratio must change, not what changes it. |

## 7. Part I: the multifractal spectrum width Δα

| | |
|---|---|
| **Capability** | Given a MOF graph, the program computes the spectrum width Δα. |
| **Status** | WITHDRAWN as a framework descriptor: Δα tracks system size and is reproduced by a structureless lattice. It is a documented negative result. |

---

## What is not achieved

- No energy has been validated against DFT; this needs HPC.
- No additive effect is predicted.
- No adsorption is computed.
- The laboratory records have had no blind second extraction.
- The proofs have not been checked by a second team member.
