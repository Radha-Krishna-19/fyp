# Phase A audit under the master supervision prompt (13 November 2026)

Project: MOF Graphs and Crystal Morphology (23CSE498, G070). This is the read-only audit that the
master prompt requires before any fix. It extends the audit of 12 November
(`2026-11-12_audit_of_completed_work.md`), whose fixes stand, and covers the work added on 13 November
(benchmark of ten MOFs, steering, shape to gas access, the 138-structure run, the Shape Advisor page).

Nothing in the project's results was changed while writing this audit.

**Scope decision by the team (13 November, 19:46): Part I (the spectrum) is closed and is not to be
reworked.** Part I appears here only as one recorded finding (section 3) for the team's preparation;
no Part I file, page or result is changed.

Format of every finding: what was checked, the evidence (file, command or number), the impact, the
proposed fix, an owner, and the validation the fix needs. Owners use the initials of
`docs/defence/panel_defence.md`: RK Radha Krishna, KV Kshitij, KS Keerthi, RA Rohith, IS Isha.

---

## 0. Corrections to the prompt itself

The prompt was checked against the repository before it was followed. Each item below is a statement
in the prompt that is wrong or cannot be acted on as written, with the evidence.

| # | The prompt says | What the repository shows | Consequence for this audit |
|---|---|---|---|
| P1 | The panel raised a concern that a spectrum or band classification may not be justified by the chemistry or physics. | No record of such a remark exists in the repository. The only recorded panel request is the handwritten morphology question after Panel Review 1 (`morphology.html`, quoted; `README.md` line 31). The bands were withdrawn by the team itself on finite-size grounds. | The exact criticism must come from the team's own notes of the review. Section 3 investigates the concern independently, as the prompt also asks. **Owner RK: ask the team who attended Review 1 to write down what the panel said.** |
| P2 | Review against "the Phase II review rubric". | Only the Panel Review 1 rubric is in the project (gap 21 of 12 November is still open). | Section 8 maps against the Review 1 rubric and the panel's question; the Phase II and final rubrics must be obtained from Dr. Ramraj. |
| P3 | "Fix K1, K2 and K4. K3 and K11 are already done." | K5–K10 are also open (`morphology_map.html#map-steps`; `docs/project_notes.md` line 391). K5 is the dehydroxylated UiO-66 node. | K5–K10 are listed in the gap list as well. |
| P4 | "Calculate at least one shape-dependent adsorption quantity for the four MOFs." | Done on 13 November for eight MOFs (`run_shape_adsorption.py`), but as geometric indicators (open fraction of each face, L = V/A), not as adsorption. | Reviewed in section 4.6; the wording "adsorption quantity" must not be used for it. |
| P5 | "Extend the scored benchmark from four to at least eight MOFs." | Done on 13 November: eight MOFs with structure files, two with stand-ins (`run_benchmark_mofs.py`). | Reviewed in section 4.5. |
| P6 | Machine learning: "dataset leakage, cross-validation, overfitting, ML training". | The project trains no model. CHGNet is used as a pre-trained potential; the "condition model" and baselines are majority rules evaluated leave-one-paper-out. | Section 4.8 applies the statistical part of D6 to what exists; there is nothing to train or overfit. |
| P7 | "Every `code_*` script" in a ten-minute rerun. | Several `code_0x` modules are libraries with a demonstration `main`; `code_07a` needs the external `mofid` package; `run_chgnet_cleavage.py` and the steps 1–8 driver need CHGNet and GPU time for real runs. | Recorded per script in section 1. |
| P8 | Repository at `C:\Dev\fyp\04_Repository\fyp`. | Not reachable from this session (the link to the computer failed to connect). The audit used the working copy that holds every commit up to `7e1a413`. | Nothing in this audit depends on files only on the PC, except the secondary material under `C:\Dev\fyp`. |
| P9 | "Six disputed slabs". | The plan names MOF-5 and UiO-66 (where CHGNet and UFF disagree) with HKUST-1 as a control (`code/morphology/DFT_CHECK_PLAN.md`, Progress page row 4e). | Consistent; noted only so the six are named the same way everywhere. |
| P10 | The dataset size used in my own new page on 13 November ("144 records"). | `experimental_morphology.csv` has 134 records from 35 papers on 12 MOFs. | Corrected before commit; recorded here because the wrong figure came from me, not from the prompt. |

---

## 1. Reproducibility (A1)

All 52 test and `run_*`/`code_*`/`check_*` Python files were run from the file-system root (`cd /`) on a clean checkout of `7e1a413`, each with a 10-minute limit, and their result files compared value by value with the committed ones. Three other jobs ran at the same time, so runtimes are upper bounds. The website suites (15) were run separately and all pass.

**50 of 52 exit 0.** The 2 that do not:

| Script | Exit | Reason |
|---|---|---|
| `code/morphology/steps1_8_check/run_nb.py` | 1 | needs four arguments and CHGNet (by design; usage in its README) |
| `code/spectrum_pipeline/code_07a_mofid_assembly.py` | 1 | needs the external `mofid` package (by design) |

**Runtime above one minute:**

| Script | Seconds |
|---|---|
| `code/spectrum_pipeline/code_20_diverse_set.py` | 570 |
| `code/spectrum_pipeline/_test_window_frac.py` | 423 |
| `code/spectrum_shape_relation/run_02_spectrum_of_predicted_crystal_shapes_MOF5.py` | 321 |
| `code/spectrum_pipeline/_run_size_scaling.py` | 317 |
| `code/spectrum_shape_relation/run_01_spectrum_of_box_particles_same_cell_count.py` | 262 |
| `code/spectrum_shape_relation/run_03_core_mof_spectrum_width_vs_bfdh_shape.py` | 176 |
| `code/spectrum_pipeline/code_17_full_correct_band.py` | 155 |
| `code/morphology/run_dataset_shapes.py` | 124 |
| `code/spectrum_pipeline/code_19_spectrum_vs_shape.py` | 110 |
| `code/morphology/run_shape_adsorption.py` | 94 |
| `code/spectrum_pipeline/_prove_ordering_equivalence.py` | 74 |
| `code/morphology/tests_deform.py` | 65 |

**Result files that change on rerun** (compared value by value; timings ignored):

| File | What changes | Meaning |
|---|---|---|
| All 16 other JSON results of `code/morphology/` and `data/spectrum_descriptors/` | Nothing | Reproduce exactly |
| `convergence_sweep.json`, `full_band_core_cg.json`, `subband_explain_core.json` | Only `r2_linearity_mean` | Known non-deterministic diagnostic, quoted nowhere (12 November, gap 16) |
| `spectrum_vs_shape_MOF5.json` | Only the `sec` timing fields | None |
| `code/spectrum_shape_relation/results/03_core_mof_spectrum_vs_bfdh_shape.json` | Every quantity that uses the BFDH sphericity or aspect ratio, by up to 0.008 (for example the size-controlled ρ of width vs aspect ratio, +0.0013 → −0.0066; p 0.99 → 0.96); quantities that use only the spectrum or the cell are identical | **Stale**: the BFDH code changed after this file was written (any-lattice work of 12 November), so a few CoRE MOF shapes moved slightly. The conclusion (no relation beyond size; every size-controlled p above 0.35) is unchanged. **Gap G15.** |

PNG figures are rewritten on every run (matplotlib metadata), so they show as changed; their content was
not compared pixel by pixel. Six figure files in `code/morphology/results/figs/` are written by the
scripts but not committed; the committed copies used by the site are in `website/figures/`.


---

## 2. Summary of the most important findings

1. **Everything runs** from a folder other than its own (section 1); the only failures are the two
   scripts that need arguments or an external package by design. All result files reproduce, except one
   known non-deterministic diagnostic and one stale file of the spectrum-and-shape study (G15), whose
   conclusion is unchanged.
2. **Part II stands, with a smaller unit of evidence than the pages implied.** The structure-only
   prediction is right for 4 of 5 MOFs on additive-free records (not "28 of 32 tests"); the clean test of
   the energy model on MOFs added later is one additive-free record. Fixed in Phase B (`0d8eede`).
3. **The "UFF" surface energy is a bond count** (93–98 % of γ). The face order is a broken-bond order.
   Stated on the Surface energy page since `0d8eede`.
4. **The chemistry of the inputs is sound** for every structure used for a result: composition checked for all
   21 CIF files in the repository's structure folders, and the six DFT slabs are stoichiometric and unfragmented. The known exception
   is the dehydroxylated UiO-66 input of the steps 1–8 check (K5).
5. **Relaxed CHGNet energies are physically implausible** (60 % to almost 100 % lower) and are correctly
   kept out of every conclusion.
6. **Part I**: one test shows Δα as computed is set by the algorithm and graph size, not the framework.
   Recorded only (section 3); the team decided not to rework Part I.
7. **Stale statements** on four pages and in five documents were updated (`0d8eede`, `1d24cb0`, `df269ca`).

---

## 3. Part I: one finding recorded, not acted on (team decision)

Part I is already closed as a negative result (the bands are withdrawn on finite-size grounds). The
prompt asks for a scientific verdict on it, so one test was run. It is recorded here because a panel
may ask about it; nothing in the repository was changed.

**The test.** The same box-covering estimator, with the published settings, was run on a simple cubic
lattice wrapped on a torus, a graph in which every vertex is identical. It gives Δα = 1.86 to 2.53,
growing with size (slope 0.61 per unit ln D), in the same range as the four MOF nets (1.34 to 2.71,
slopes 0.69 to 0.89). With the deterministic box-growing measure of Xiao et al. (2021) the lattice gives
exactly zero. In a periodic net every vertex has the same long-range growth (M(r) ∝ r³), so the true
spectrum of an infinite crystal is a single point.

**Meaning.** Δα as computed measures the box-covering algorithm and the graph size, not the framework.
This strengthens the existing withdrawal; it does not reopen Part I. The sentence on the Spectrum page
"Δα is a heterogeneity score" is therefore not defensible if a panel asks about it; the team should
answer with the withdrawal and this test rather than defend that sentence.

**Where the evidence is.** The script and its output were kept outside the repository, as a patch in
the session's working folder, by the team's decision. The question and answer are in the team study guide.

---

## 4. Part II: review of every major result

Each result is reviewed along the nine dimensions of the prompt. "Pass" means the check was made and
nothing wrong was found; a named problem means it was found; "not tested" means no evidence exists.

### 4.1 Symmetry, allowed faces and BFDH (Phase 1, `run_phase1.py`, `run_cif_to_shape.py`, `mof_cif_shape.js`)

| Dimension | Finding |
|---|---|
| Mathematics | d_eff = d/n with n the smallest order that is not systematically absent; absences from the operations themselves (hR = h and h·t non-integer). Standard; 16 propositions proved in the Maths page. Pass. |
| Numerical | Exact rational arithmetic on Miller indices; spglib tolerance 0.1 Å; tested in `tests.py` (14 checks) and `test_cif_to_shape.js`. Pass. |
| Computer science | Python and JavaScript agree number by number (`test_cif_to_shape.js`, `test_general_shape.js`). Pass. |
| Chemistry | The four demonstration CIFs were checked for stoichiometry and charge in this audit: MOF-5 Zn₃₂O₁₀₄C₁₉₂H₉₆ = 8 Zn₄O(BDC)₃; HKUST-1 primitive Cu₁₂C₇₂O₄₈H₂₄ = 4 Cu₃(BTC)₂; UiO-66 Zr₆O₃₂C₄₈H₂₈ = Zr₆O₄(OH)₄(BDC)₆; ZIF-8 Zn₁₂N₄₈C₉₆H₁₂₀ = 12 Zn(mIm)₂. All charge balanced (Zn²⁺, Cu²⁺, Zr⁴⁺). The steps 1–8 input `UIO-66.cif` from RASPA2 is Zr₆O₆(BDC)₆ per node: the dehydroxylated form (K5, already documented). Of the other 17 files (benchmark and general-lattice folders, steps 1–8 inputs), all match their formula; MIL-88A has no hydrogens on its terminal water and hydroxide, so its charge cannot be checked, and MIL-53(Cr) lt has no guest water. Both are used only for BFDH geometry. |
| Crystallography | ZIF-8 gives I-43m only without H; UiO-66 gives F-43m because the μ₃-OH are ordered in the file (literature: Fm-3m on average). IRMOF-3 (P1, F-centring only) and IRMOF-8 (P2₁/c, no centring) have broken symmetry from ordered substituents. These are stated on the pages. Pass, with stated limits. |
| Physics | BFDH is a geometric rule (growth rate ∝ 1/d_eff); it contains no energy, solvent or supersaturation. Stated. |
| Materials science | BFDH is a first estimate in crystal-growth practice; it is not a prediction of the observed habit. Stated. |
| Statistics | Not applicable to the rule; its accuracy is scored in 4.5. |
| Interpretation | "Allowed faces" and "BFDH shape" are presented as predictions, not observations. Pass. |

### 4.2 Surface energies (Phase 4, `mofmorph/forcefield.py`, `run_phase4.py`)

| Dimension | Finding |
|---|---|
| Mathematics | γ(s) = ½ (d/V) Σ ε_pair c_pair(s), exact plane counting; the minimum over the offset s gives the termination. Pass. |
| Numerical | 400 offset bins; cutoff 12 Å for the van der Waals part. Checked after the audit (G12, closed): 1600 bins change nothing; 15 Å changes γ by at most 0.4 % and no face order. |
| Computer science | Reproduces exactly on rerun (12 November). Pass. |
| Chemistry | **Every bond costs the same 70 kcal/mol**, whether Zn–O, Zr–O or C–C. In `results/phase4_results.json` the bond part is 93–98 % of γ for all four MOFs (for example MOF-5 {100}: 0.145 of 0.148 J/m²). The face order is therefore set by the number of bonds cut per unit area. That is a broken-bond (Hartman–Perdok-type) model, not a force-field energy. The name "UFF Wulff" overstates the physics. **Gap G6.** |
| Physics | Unrelaxed, no electrostatics, no solvent: stated on the page as an upper bound with only relative meaning. MOF-5's ratio γ111/γ100 = 1.72 lies 0.7 % below the cube boundary √3 = 1.732, so its "cube" prediction sits on a boundary (stated in `DFT_CHECK_PLAN.md`; `bond_sensitivity.json` shows the shape changes when metal–ligand bonds are scaled, while the dominant face stays {100}). |
| Crystallography | Terminations are whole-plane cuts at the minimum; UiO-66 {111}+ and {111}− are equal, as they should be for the ordered F-43m file. Pass. |
| Materials science | Bond-counting models are an accepted first approximation for strongly bonded faces; they cannot see modulator or solvent binding. Stated. |
| Statistics | One value per face; no uncertainty can be attached without a second method. DFT is the planned check. |
| Interpretation | Used only for ordering faces. Acceptable if the page states that the order is a bond-count order (G6). |

### 4.3 CHGNet slab energies (`chgnet_wulff/`, steps 1–8)

| Dimension | Finding |
|---|---|
| Chemistry | The six slabs named for DFT were checked in this audit: each is a whole multiple of the bulk formula (stoichiometric, so charge neutral) and is one connected piece (no loose fragments). Other CHGNet slabs cut through linkers and release CO₂ on relaxation (`docs/project_notes.md` line 360). |
| Physics | Relaxation lowers γ by 60 % to almost 100 % (project notes line 391). A near-zero cleavage energy for a coordination framework is not physically credible; it indicates reconstruction or a bulk reference inconsistent with the slab. **Relaxed CHGNet values must not be used for any conclusion until a DFT check** (already the project's position). |
| Numerical | Slabs 15–30 Å thick, not thickness-converged. Open (C1). |
| Interpretation | The pages already treat CHGNet as unvalidated. Pass. |

### 4.4 The morphology map and steering (`morphology_map/`, `run_shape_steering.py`)

| Dimension | Finding |
|---|---|
| Mathematics | The region boundaries were re-derived in this audit. Cube: y ≥ √3 and x ≥ √2. Octahedron: y ≤ 1/√3 and x ≥ √(3/2)·y, because the support of a regular octahedron in the [110] direction is √(3/2) times its face distance. Rhombic dodecahedron: x ≤ 1/√2 and y ≥ √(3/2)·x. The closed forms in `factor_pure` follow directly. `check_new_analyses.py` confirms that each factor gives the pure shape. Pass. |
| Physics | The Gibbs relation dγ = −Γ dμ supports the direction of the change, not its size. The steering percentages are relative to bond-count energies (4.2), so they rank how hard a change is; they are not binding energies. Stated on the Advisor page. |
| Interpretation | The laboratory evidence column lists records per additive class and paper. Several MOFs have one or two records per class (for example MOF-5 monocarboxylic acid: 1 record, 1 paper). No class effect is established from these counts. **Gap G10** (state the counts as anecdotes, not evidence of an effect). |

### 4.5 Benchmark against laboratory records (`run_benchmark_mofs.py`)

| Dimension | Finding |
|---|---|
| Statistics | The structure-only models make **one prediction per MOF**, so 28 of 32 additive-free records are 5 independent predictions: MOF-5 9/9, ZIF-8 11/12, HKUST-1 7/8, IRMOF-3 1/1, UiO-66 0/2, from 13 papers. Four of five MOFs are right; UiO-66 is wrong. The Wilson interval on the page (72–95 %) treats the 32 records as independent. A bootstrap that resamples whole papers (computed in this audit, 5000 resamples, seed 0) gives 73–97 %, similar, but the honest unit of evidence is the MOF. **Gap G5.** |
| Data | Additive-free is defined by the text rule `none`, blank, or an amount containing "or none". This counts HKUST-1 umemura2011-1 (lauric acid, "lowest (or none)") and two mao2013 records with no additive recorded as additive-free. Both are judgement calls. **Gap G11.** |
| Leakage | None: the structure-only models use no laboratory data. The per-MOF majority baseline is computed leave-one-paper-out. Pass. |
| Researcher choices | The bond energy, bond tolerance 1.15 and the use of min(γ{111}+, γ{111}−) were fixed before the ten-MOF benchmark, on the four demonstration MOFs. The four demonstration MOFs are therefore not an independent test of those choices; the four new MOFs (IRMOF-3, IRMOF-8, ZIF-67, Mg-MOF-74) are. **Gap G9** (report the new four separately). |
| Interpretation | "As good as knowing the usual laboratory answer, without laboratory data" holds on additive-free records (28/32 each). With additives no model is reliable (13–21 of 44). The Advisor page was corrected before commit to say both. Pass. |

### 4.6 Shape to gas access (`run_shape_adsorption.py`)

| Dimension | Finding |
|---|---|
| Mathematics | L = Ψ V^(1/3)/(36π)^(1/3) is identically V/A, re-derived in this audit; for a cube of unit volume L = 1/6 = 0.167, as in the result file. Fill time ∝ L² and initial uptake ∝ (open fraction)·(A/V) are first-order diffusion scalings. Pass. |
| Chemistry / physics | Probe radii 1.65 Å (CO₂) and 1.82 Å (N₂) are half the kinetic diameters; Bondi radii, 2.0 Å for metals Bondi does not list. A point counts as open if a probe fits there; **whether that opening connects to the pore network is not tested** (Zeo++-type accessibility). pyzeo could not be installed here. **Gap G8.** |
| Numerical | 0.3 Å grid; plane-averaged open fraction agrees with a 3D random-point estimate within 0.002–0.003 (`check_new_analyses.py`, 51 checks). Pass. |
| Interpretation | These are geometric indicators. No uptake, isotherm, selectivity or diffusion coefficient is computed. The page says so. "Window counts" are not quoted because they depend on the grid. Pass. |

### 4.7 The 138-structure run (`run_dataset_shapes.py`)

71 of 77 hMOF files are stored in P1, so symmetry-based steps see a triclinic cell and all 77 come out
compact. That is a property of how the hypothetical files were written. Labelled unvalidated; no
laboratory shape exists for these structures. Pass as a coverage run; **nothing about hMOF
morphology may be concluded from it.**

### 4.8 Statistics and "machine learning" (D6, as far as it applies)

No model is trained. The leave-one-paper-out majority, the McNemar test (p = 0.041) and the paper-level
bootstrap on the morphology map are appropriate for clustered data. The one weakness is G5: per-record
intervals for per-MOF predictions.

---

## 5. Provenance and consistency (A2, A3)

The 12 November audit traced the most-quoted numbers; they still hold (rerun in section 1). This audit
traced the numbers added on 13 November and searched every page, README and note for statements the new
work has made stale.

**Provenance of the new numbers.** Every number on the Advisor page is read at run time from
`advisor_data.js`, which `build_advisor_data.py` writes from four result files; `test_advisor.js` checks
the data file against those files value by value and the browser Wulff shares against Python
(within 2 × 10⁻³). The 12-framework size study on the Results page traces to `code_20_diverse_set.py`.
No orphan was found among them.

**Stale or inconsistent statements found** (each is a gap in section 9):

| Where | Statement | Now true | Gap |
|---|---|---|---|
| `bridge.html` (Why shape) | "This project has not computed adsorption or diffusion for any shape." | Geometric access indicators exist for eight MOFs (Advisor page); still no adsorption or diffusion coefficient. | G3 |
| `cif_to_shape.html` | "The project's laboratory database does not yet hold records for non-cubic MOFs." | 18 Mg-MOF-74 and 3 MIL-53(Fe) records exist and are scored. | G3 |
| `docs/defence/panel_defence.md` Q2 | "Did you compute any adsorption quantity from shape? No." | As above. | G3 |
| `docs/defence/one_page_summary.md`, `README.md`, `PROJECT_MAP.md`, `code/morphology/README.md`, Progress page | Benchmark "4 MOFs"; no mention of the ten-MOF benchmark, steering, access, the 138 run or the Advisor page. | Those exist. | G4 |
| Advisor page | "Mg-MOF-74 is hexagonal (trigonal R-3)". | The lattice is hexagonal and the space group R-3 is trigonal; the wording mixes the two. | G13 |

---

## 6. Coverage (A5)

Changes since 12 November are in bold.

| Analysis | Structures | Generalises? |
|---|---|---|
| Decomposition, quotient graph, spectrum, bands, strata | 138 (77 hMOF + 61 CoRE MOF) | Negative result; see section 3 |
| Size study of Δα | 4 nets, **12 frameworks** (`code_20`) | Yes, as a negative result |
| Symmetry, faces, BFDH | 4 demonstration MOFs; 8 CoRE MOFs; **12 general-lattice files; all 138 dataset files (unvalidated)** | Geometry only; hMOF files are P1 |
| UFF (bond-count) surface energies and Wulff | 4 demonstration MOFs; **plus IRMOF-3, IRMOF-8, ZIF-67 (cubic)** | Ordering only; G6 |
| Scored benchmark | **8 MOFs with structures (5 with additive-free records), 2 stand-ins, 134 records from 35 papers** | Five independent additive-free predictions; not enough to rank energy models |
| Steering | **8 cubic MOFs** | Relative indication only |
| Shape to gas access | **8 MOFs** | Geometric indicator only; accessibility not tested (G8) |
| CHGNet | 4 MOFs, partly relaxed; not validated | No |
| Morphology map tests | 4 cubic MOFs; 10 series; 82 records from 25 papers | Cubic crystals only |

**Cannot be generalised:** which energy model is best (only MOF-5 separates them, and it sits on a
boundary); anything about non-cubic energies; any adsorption consequence of shape.

---

## 7. History and the Mistakes page (A6)

The git history (83 commits; authors Radha Krishna 81, Rohith Abhinav 2) and the Mistakes page agree up
to 12 November. Mistakes made on 13 November, all caught before the affected work was committed, and
the one found by this audit, are not yet on the page:

| Mistake | How found | Fixed in |
|---|---|---|
| Benchmark: HKUST-1 and UiO-66 got no dominant face, because the cubic check ran on primitive cells | Missing values in the first run | `cc39fcb` (conventional cell) |
| Gas access: every face had the same open fraction, because averaging over all plane offsets gives the bulk porosity, not the face | Identical values across faces | `8a7b4db` (the cleavage termination is used; the range over offsets is reported) |
| Advisor page: "144 laboratory records" (true: 134) | Count checked against the CSV before commit | `7e1a413` |
| Advisor page: diffusion length described as "mean distance from the surface to the centre" (true: V/A) | Re-derivation of the formula | `7e1a413` |
| Advisor page: "BFDH weaker" and "the baseline falls far below" stated without the with-additive exception | Numbers re-read against the result file | `7e1a413` |
| Δα described as a heterogeneity score on a periodic graph (Part I) | This audit | Not changed: team decision (section 3) |

Withdrawn claims: all earlier withdrawals are on the site. Part I wording is left as it is (team decision; section 3).

---

## 8. Rubric and the panel's question (A7)

| Item (Panel Review 1 rubric and the panel's question) | State | Evidence |
|---|---|---|
| Methodology and design | Done | Methodology, From a CIF to a shape, Morphology pages |
| Mathematical model | Done for Part II; Part I closed (section 3); proofs not yet checked by a second member | Maths page; `test_maths.js`; check sheets |
| Implementation | Done; Python and JavaScript agree; 15 website suites and all Python tests pass (section 1) | `website/tests`, `code/morphology/tests*.py` |
| Results | Part I: negative (closed). Part II: ten-MOF benchmark, steering, access indicators | Results, Experiment, Advisor pages |
| Panel question: several morphologies from one unit cell, mathematically | Done | Maths, Morphology, Changing the cell, Morphology map |
| Panel question: computationally | Done for cubic MOFs with energies; BFDH for any lattice | Advisor, CIF to shape |
| Original aim (adsorption) | Partly: geometric access indicators only | Advisor page |
| Phase II and final rubrics | Unknown: not in the project (P2) | — |

---

## 9. Severity-ranked gap list (A8)

Severity classes of the prompt: 1 scientifically incorrect, 2 chemically or physically invalid,
3 mathematically incorrect, 4 computationally incorrect, 5 unreproducible, 6 unsupported interpretation,
7 undocumented, 8 cosmetic.

| # | Sev. | Component | Evidence | Impact | Proposed fix | Owner | Validation |
|---|---|---|---|---|---|---|---|
| G3 | 6 | Why shape page, CIF to shape page, defence Q2 | Section 5 | Pages contradict newer results | Update the fragments and the defence document | RK | Build, tests |
| G4 | 7 | README, PROJECT_MAP, project notes, `code/morphology/README.md`, Progress page, one-page summary | Section 5 | New work undocumented outside its own page | Add the 13 November work | RK | Read-through |
| G5 | 6 | Benchmark intervals (Advisor, Experiment pages) | 4.5: 32 records = 5 predictions | Precision overstated | Report "4 of 5 MOFs" next to the record count, plus the paper bootstrap; keep Wilson as secondary | RA, KS | Script prints both |
| G6 | 6 | Name "UFF Wulff" | 4.2: bonds are 93–98 % of γ | Readers infer force-field physics | Say "bond-count surface energy (UFF van der Waals adds 2–7 %)" wherever the model is named; keep the file names | RK, KV | Text search |
| G8 | 6 | Gas access | 4.6 | Open points may be dead-end pockets | State the limit on the page (done in part); run Zeo++ accessibility when it can be installed | KS | Zeo++ comparison on one MOF |
| G9 | 6 | Benchmark | 4.5 | Model choices were made on the four demonstration MOFs | Report the four new MOFs separately as the clean test | RA | Separate row in the result file |
| G10 | 6 | Steering evidence | 4.4 | One-record classes read as effects | Label counts below 3 records as anecdotal | KS, RA | Page text |
| G11 | 7 | Additive-free rule | 4.5 | Three judgement calls undocumented | List them in the dataset README and the benchmark output | RA | README |
| G12 | 7 | Surface-energy numerics | 4.2 | Bin and cutoff convergence not recorded | **Closed 13 November**: `check_energy_convergence.py` → `energy_convergence.json`. 1600 bins change no value; a 15 Å cutoff changes γ by at most 0.4 % (ZIF-8) and the face order of no MOF | KV | Done |
| G13 | 8 | Advisor page wording on Mg-MOF-74 | Section 5 | Lattice vs crystal system | Reword | RK | Build |
| G14 | 7 | Mistakes page | Section 7 | 13 November slips missing | Add Part E | RK | Build |
| G15 | 5 | Spectrum and shape, Test 3 (`03_core_mof_spectrum_vs_bfdh_shape.json`) | Section 1 | The quoted ρ = +0.001 (p = 0.99) is now −0.007 (p = 0.96) on rerun; conclusion unchanged | Rerun `run_03` and the relation page builder, or state the rerun value next to the old one. Not done: the team asked not to rework Part I and its link study | KS, RK | Rerun; relation-page test |
| — | 2 | Relaxed CHGNet energies | 4.3 | Physically implausible values | Already treated as unvalidated; keep out of every conclusion | KV | DFT (needs HPC) |
| — | 2 | Steps 1–8 UiO-66 input (Zr₆O₆) | 4.1 | Wrong node for as-synthesised UiO-66 | K5, open; use the hydroxylated `website/UiO-66.cif` in the rerun | KV | Composition check |
| — | 5 | DFT on six slabs; CHGNet thickness; relaxed steps 1–8 rerun | — | Validation missing | Needs HPC and GPU time | KV, guide | — |
| — | 7 | Phase II rubric; panel's exact Phase I remark | P1, P2 | Cannot map or answer precisely | Ask the guide and the team | RK | — |

---

## 10. Decisions the team must take before Phase B

The team asked for this work to go ahead without waiting (13 November, evening). The decisions below
were therefore taken as stated, and each can be reversed from git history.

1. **Part I is not reworked** (team decision, 13 November, 19:43 and 19:46). The finding of section 3 is
   recorded for preparation only; no Part I page, script or result is changed, and no branch is kept for it.
2. If Part I is ever reopened, the established connectivity descriptor is the coordination sequence of
   each vertex type and the topological density (Grosse-Kunstleve et al. 1996), computed from the same
   labelled quotient graph. Not implemented.
3. Nothing is pushed. The user pushes from bundles after review.

Still for the team: what the panel said about the spectrum at Review 1 (P1); the Phase II and final
rubrics (P2); HPC and GPU time for the validation runs.
