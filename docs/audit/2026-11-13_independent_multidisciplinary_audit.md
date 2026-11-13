# Independent Multidisciplinary Scientific and Computational Audit

MOF Graphs and Crystal Morphology (23CSE498, G070). 13 November 2026, after the Phase B fixes
(`0d8eede`, `1d24cb0`, `df269ca`). Written as a reviewer, not as an author. The detailed evidence is in
`2026-11-13_phase_A_multidisciplinary_audit.md` (cited below as "Phase A, section n").

Scope set by the team: Part I (the spectrum) is closed and was not reworked; it is reviewed only so the
team can answer questions about it.

## 1. Executive summary

The project's Part II answers the panel's question with a correct mathematical chain (symmetry → allowed
faces → shape family → selected shape), implemented twice and checked number by number. Its predictive
evidence is modest and is now stated as such: the dominant face of additive-free crystals is right for 4
of 5 MOFs, and the energy model behind it is in effect a broken-bond count. Nothing in the project
predicts additive effects, and adsorption is not computed; geometric access indicators are. Part I is a
negative result whose underlying quantity, on inspection, does not measure the framework at all.
No result in the repository was found to be computationally wrong (one result file is stale by less than 0.01, G15); three interpretations were stronger
than their evidence and have been corrected.

## 2. Review by discipline

| Discipline | What was checked | Finding |
|---|---|---|
| Mathematics | Absence rule, BFDH, Wulff map boundaries (re-derived), steering closed forms, L = V/A (re-derived), τ through the origin, Legendre transform | Correct. The spectrum's measure is unnormalised and D(q) = τ/q is non-standard; Δα is unaffected (Phase A, 3) |
| Numerical methods | Surface-energy bins and cutoff; grid of the access calculation; box-covering seeds | Access grid checked against a 3D estimate (within 0.003). Surface energies converged in bins and cutoff (at most 0.4 %, no face order changes; `check_energy_convergence.py`) |
| Computer science | Python vs JavaScript, tests from any folder, determinism | Two implementations agree; 15 website suites (over 3,400 checks) and all Python tests pass; 50 of 52 scripts run from any folder (two need arguments or an external package by design); results regenerate except one stale file of the spectrum-and-shape study (G15: ρ +0.001 → −0.007, conclusion unchanged) (Phase A, 1) |
| Chemistry | Stoichiometry and charge of 21 CIFs; six DFT slabs | Sound, except the dehydroxylated UiO-66 input of steps 1–8 (K5) and two files without hydrogens or guests used only for geometry |
| Physics | Unrelaxed energies, no electrostatics, CHGNet relaxation | Bond count dominates (93–98 %). Relaxed CHGNet γ falls by 60 % to ~100 %: not credible; correctly excluded |
| Crystallography | Space groups, conventional cells, ordered substituents | Correct for the files; IRMOF-3/IRMOF-8 and 71 of 77 hMOF files have broken symmetry from ordering or P1 storage, flagged |
| Materials science | Equilibrium shape vs observed habit | Pages keep prediction and observation apart; plates and intergrowths (kinetics) are outside every model |
| Statistics | Benchmark design, intervals, leakage | No leakage. Records were treated as independent; corrected to 4 of 5 MOFs plus a paper bootstrap (G5) |
| Interpretation | Each claim against its evidence | Three over-statements found and corrected (section 3) |

## 3. Cross-disciplinary contradictions

| # | Disciplines | Contradiction | Which is right | Correction |
|---|---|---|---|---|
| C1 | Physics vs chemistry | "UFF force-field surface energy" vs every bond costing 70 kcal/mol, 93–98 % of γ | The energy is a broken-bond count | Named so on the Surface energy and Advisor pages (`0d8eede`, `df269ca`) |
| C2 | Statistics vs computer science | 28 of 32 records scored correctly vs one prediction per MOF | 5 independent tests, 4 right | MOF-level counts and paper bootstrap added (`0d8eede`) |
| C3 | Numerics vs physics | CHGNet relaxation converges vs γ near zero for a coordination framework | Physics: the relaxed values are not surface energies | Already excluded; DFT planned |
| C4 | Mathematics vs chemistry (Part I) | A correct spectrum computation vs a quantity a structureless lattice reproduces | Δα as computed is not a framework property | Recorded; Part I not reworked by team decision |
| C5 | Crystallography vs chemistry | Correct symmetry of the IRMOF-8 file vs the ideal Fm-3m framework | Both: the file is correct for an ordered model | Prediction flagged on the Advisor page |
| C6 | Theory vs experiment | Equilibrium Wulff shape vs crystals grown with additives | The model does not represent additives | With-additive scores reported as unreliable for every model |

## 4. Independent replication

| Result | How it was replicated |
|---|---|
| Allowed faces, BFDH shapes, Wulff areas | Separate Python and JavaScript code, compared in `test_cif_to_shape.js`, `test_general_shape.js`, `test_advisor.js` |
| Map boundaries and steering factors | Re-derived by hand in this audit; `check_new_analyses.py` confirms each factor gives the pure shape |
| Diffusion length | L = Ψ V^(1/3)/(36π)^(1/3) shown to equal V/A; unit cube gives 1/6, as in the result file |
| Open fraction per face | Plane average over offsets equals an independent 3D random-point estimate (51 checks) |
| Benchmark counts | Recomputed from the CSV in this audit before the script was extended; identical |
| Input chemistry | Element counts of every CIF and slab recomputed with ASE; connectivity of the six slabs checked |

Not replicated independently: the surface energies themselves (no second energy method has been run to
completion); this is what the DFT plan is for.

## 5. Final verdict per major claim

| Claim | Verdict |
|---|---|
| Symmetry decides the allowed faces; one cell gives a family of shapes (16 propositions) | VALIDATED (proofs not yet checked by a second member) |
| Changing the cell gives plates and rods | VALIDATED (as hypothetical frameworks, as stated) |
| The structure-only model gives the dominant face of additive-free crystals for 4 of 5 MOFs | VALIDATED WITH LIMITATIONS (5 MOFs; clean test of one record) |
| BFDH gives the rod habit of Mg-MOF-74 | VALIDATED WITH LIMITATIONS (one MOF, 10 records) |
| The bond-count Wulff model is better than BFDH | COMPUTATIONALLY VALID BUT SCIENTIFICALLY UNVALIDATED (intervals overlap; true only without additives) |
| Steering percentages | COMPUTATIONALLY VALID BUT SCIENTIFICALLY UNVALIDATED (relative to unvalidated energies) |
| Geometric access indicators per shape | VALIDATED WITH LIMITATIONS (geometry only; pore-network connection not tested) |
| Any statement that shape improves adsorption | UNSUPPORTED (not claimed by the project) |
| CHGNet relaxed surface energies | CHEMICALLY OR PHYSICALLY QUESTIONABLE |
| Laboratory series follow the map order (6 of 6) | VALIDATED WITH LIMITATIONS (selection stated; small) |
| Part I bands and classes | WITHDRAWN |
| Part I "Δα is a heterogeneity score" | UNSUPPORTED (recorded; wording left on the site by team decision) |
| 138-structure run | COMPUTATIONALLY VALID BUT SCIENTIFICALLY UNVALIDATED (no laboratory shapes) |

## 6. Simulated panel

Each question was answered from the repository only; the rating is about the evidence.

| Area | Question | Rating |
|---|---|---|
| Correctness | "How do you know the allowed faces are right?" | DEFENSIBLE (proofs, two implementations, spglib) |
| Mathematics | "Derive the octahedron boundary on your map." | DEFENSIBLE (Q46) |
| Implementation | "What does your surface energy actually count?" | DEFENSIBLE after `0d8eede` (Q25) |
| Validity | "Is 28 of 32 really 32 tests?" | DEFENSIBLE after `0d8eede` (Q44) |
| Design | "Why no GNN?" | DEFENSIBLE (Q48) |
| Critical reading | "With additives your model is wrong. Why show it?" | DEFENSIBLE (the limit is the claim) |
| Limits | "Which energy model is best?" | We do not know; DEFENSIBLE as a stated unknown |
| Objective | "Did you improve adsorption?" | PARTIALLY DEFENSIBLE: indicators only (Q47) |
| Part I | "Does Δα measure the MOF?" | DEFENSIBLE as a negative result (Q51) |
| Data | "Who checked the laboratory records?" | PARTIALLY DEFENSIBLE: blind second extraction prepared, not done |
| Validation | "Is any energy validated against DFT?" | PARTIALLY DEFENSIBLE: plan and slabs ready; needs HPC |

No critical question is NOT DEFENSIBLE. The project is panel-ready once every member passes the mock viva
for the questions they own (`docs/defence/panel_defence.md`, section 13) and the two second-person checks
are done.

## 7. Remaining limitations

DFT on the six prepared slabs (needs HPC through the guide); the relaxed steps 1–8 rerun with K1, K2,
K4–K10 fixed (needs a GPU); additive binding energies per face; pore-network accessibility (Zeo++);
the stale Test 3 file of the spectrum-and-shape study (G15); a blind second extraction of 20 laboratory records; a
second check of the 16 proofs; the Phase II and final rubrics; the panel's exact remark on Part I.
