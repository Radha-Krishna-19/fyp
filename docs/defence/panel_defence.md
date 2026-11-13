# Panel defence: completed work

MOF Graphs and Crystal Morphology (23CSE498, G070). Prepared 12 November 2026, updated 13 November, for the Phase II review,
the final review and the demonstration. Covers only work that is finished; future work is named as such.

**How to use this document.** Each question has a short model answer, the evidence in the repository, the
follow-up an examiner is likely to ask, a rating, and two people who must be able to answer it. The model
answers are a check, not a script: in the mock viva (section 12) each answer must be given in your own words
and then defended against the follow-up. If you cannot explain *why* an answer is true from the evidence
listed, the question is not yet defensible for you.

**Ratings.** DEFENSIBLE: supported by evidence that reproduces, and the reasoning is complete.
PARTIALLY DEFENSIBLE: the explanation is sound but the evidence is thin (few MOFs, one seed, no second
check). NOT DEFENSIBLE: no evidence, or an unresolved technical problem. A question is only DEFENSIBLE *for
a team member* once that person passes it in the mock viva; the ratings below are about the evidence.

**Owners.** RK Radha Krishna, KV Kshitij, KS Keerthi, RA Rohith, IS Isha. The first name owns the answer;
the second must be able to give it too, so that no part is understood by one person only.

**Repository paths** are relative to the repository root (`C:\Dev\fyp\04_Repository\fyp`, GitHub
Radha-Krishna-19/fyp). Website pages are in `website/` and online at radha-krishna-19.github.io/fyp.

---

## 1. The problem and the change of question

**Q1. What problem does the project solve, in one minute?**
A metal–organic framework (MOF) is a porous crystal of metal clusters joined by organic linkers. Part 1
asked whether a number computed from a MOF's connectivity alone, in seconds, could decide which MOFs are
worth hours of adsorption simulation. Part 2, set by the panel at Review 1, asks: given an established MOF's
unit cell, which crystal shapes (morphologies) can it take, shown mathematically and computationally? The
project answers Part 1 with a negative result (the number measures graph size, not structure) and Part 2
with a method that lists the allowed shapes of a cubic MOF from its CIF, in a predicted order, tested
against laboratory data.
Evidence: `README.md`, `PROJECT_MAP.md`, Overview page.
Follow-up: "So Part 1 failed?" It answered its question: no, as defined. A negative result that is
measured, explained and kept visible is a result; the tools it built (decomposition, periodic graph) are
reused in Part 2.
Rating: DEFENSIBLE. Owners: RK, IS.

**Q2. Why does crystal shape matter for adsorption, the original aim?**
Shape decides which faces are exposed to the gas, which pore windows open onto the surface, how far a
molecule must diffuse into the crystal, and how crystals pack in a bed. These change uptake rate and
practical selectivity even when the framework is the same.
Evidence: "Why shape" page (`website/bridge.html`).
Follow-up: "Did you compute any adsorption quantity from shape?" Not adsorption itself. For eight MOFs
we compute two geometric indicators per shape (13 November): the fraction of each face open to a CO₂ or
N₂ probe at the face's lowest-energy termination, and the diffusion length L = V/A. No isotherm, uptake or
diffusion coefficient is computed (Q47).
Evidence: Shape advisor page; `code/morphology/run_shape_adsorption.py`.
Rating: PARTIALLY DEFENSIBLE (indicators, not adsorption). Owners: IS, RK.

**Q3. Why did you not simply run adsorption simulations (GCMC)?**
Part 1's premise was to avoid them: GCMC costs hours per framework. Part 2 is about shape, which GCMC on a
periodic cell does not see at all.
Rating: DEFENSIBLE. Owners: KS, RA.

**Q4. What is genuinely yours, and what is existing work?**
Existing and used unchanged: the metal-oxo decomposition (Bucior et al. 2019), the iNMFA spectrum (Xiao,
Wang, Li 2021), box covering (Song, Havlin, Makse 2005), BFDH, Wulff, UFF, CHGNet, spglib, pymatgen.
Ours: the Python translation of the decomposition checked against the paper; the labelled-quotient-graph
pipeline and the proof that coarse-graining first and atomic-first give the same graph; the convergence
analysis that withdrew the descriptor; the 16 propositions stated for MOFs and checked numerically; two
independent implementations (Python, browser) that agree; the exact cubic morphology map with every model
placed on it and tested against laboratory series; the 134-record laboratory dataset with conditions; the
dimension-profile read-out of particle shape; and the record of every mistake.
Evidence: Journey page, "Why we read each paper"; Maths page, "Classical results cited".
Follow-up: "Is the map new?" Wulff shapes of cubic crystals are textbook; the closed-form region
boundaries in (γ110/γ100, γ111/γ100), the placement of every model of one project on it, and the test of
laboratory series against its predicted order are ours. Say exactly that, no more.
Rating: DEFENSIBLE. Owners: RK, KV.

---

## 2. Part 1: from a CIF to a periodic graph

**Q5. A CIF has no bonds. How do you get a graph?**
Bonds are inferred from distances with periodic boundaries: two atoms are bonded if closer than a cutoff,
searched over the 27 neighbouring cell images so bonds that cross the cell edge are found. The reference
pipeline (`code_02`) uses covalent radii × 1.30 (if a metal is involved) or × 1.15. The two band notebooks
used fixed element-pair cutoffs (2.80 / 2.45 / 1.70 / 1.45 / 1.90 Å).
Evidence: `code/spectrum_pipeline/code_02_bond_assignment_pbc.py`; `notebooks/spectrum/*.ipynb` step 4;
`data/spectrum_descriptors/README.md`.
Follow-up: "Why two rules?" The notebooks were written separately; their bands are withdrawn anyway
(Q11). The audit of 12 November corrected the dataset description, which had named the wrong rule.
Rating: DEFENSIBLE. Owners: IS, RK.

**Q6. What is the metal-oxo decomposition?**
Cut every bond that touches a metal atom; each remaining connected piece is a building block. Pieces that
contain a metal (with their oxo/hydroxo atoms) are nodes, the rest are linkers. It is the published rule of
the MOFid project, translated and used unchanged.
Evidence: `code_04a_metal_oxo_algorithm.py`; Decomposition page; HKUST-1 gives Cu₂ paddlewheel nodes.
Follow-up: "What fails?" Guest or solvent molecules that are not removed become extra "linkers"; several
CoRE MOF classes average more than one connected component for this reason (Results page).
Rating: DEFENSIBLE. Owners: IS, RA.

**Q7. What is a labelled quotient graph, and why not just the graph of one unit cell?**
One vertex per building block in the unit cell, one edge per inter-block bond, and on each edge the lattice
translation it crosses. Without the translation, bonds to the next cell fold back onto the same cell:
UiO-66's twelve-connected Zr₆ cluster then looks like a node with one neighbour repeated. With it, any
supercell can be built exactly without atoms.
Evidence: Network page; `code_09_network_analysis.py`, `code_12_converged_band.py` (`quotient_graph_from_cif`,
`replicate`); Mistakes page, "periodicity discarded".
Follow-up: "Prove that coarse-graining first gives the same graph as building the atomic supercell first."
The decomposition is a local, translation-invariant rule, so it commutes with periodic extension. Checked
directly: five cases, full isomorphism test, identical graphs; the atomic route is 48–675 times slower.
Evidence: `code/spectrum_pipeline/_prove_ordering_equivalence.py` (prints "All cases match: True").
Rating: DEFENSIBLE. Owners: RK, KV.

**Q8. What is the multifractal spectrum, and what is Δα?**
Cover the graph with boxes of radius r; let p_i(r) be the fraction of influential vertices in box i. The
partition function Z(q, r) = Σ p_i^q weights dense boxes (q > 0) or sparse boxes (q < 0). If
Z ∝ (r/D)^τ(q), the mass exponent τ(q) gives α = dτ/dq and f(α) = qα − τ. Δα = α_max − α_min is the
width of the spectrum: how unevenly the influential vertices are spread across scales.
Evidence: Spectrum page; `code_10_multifractal_spectrum.py`, `code_11_nmfa_paper.py`, `code_12`.
Follow-up: "Why fit τ through the origin?" The source paper defines τ = ln Z / ln(r/D), a line through
the origin; a free intercept absorbed the signal and flattened every spectrum (0 of 77 valid before the
fix, 77 of 77 after). τ = Σxy/Σx².
Rating: DEFENSIBLE. Owners: KV, RK.

**Q9. Box covering is NP-hard. How do you compute it, and how much does randomness matter?**
Greedy random covering (Song, Havlin, Makse): centres in random order, 40 trials. ln Z is averaged across
trials, not p_i (averaging before the log biased the spectrum narrow by more than ten times). The spread of
Δα across seeds is about ±0.03.
Evidence: `code_12_converged_band.py` (`box_covering`, `probability_measures`); Mistakes page.
Follow-up: "Is the result deterministic?" With fixed seeds the widths reproduce to 1e-4. One diagnostic,
`r2_linearity_mean`, does not reproduce run to run; nothing quoted uses it (`docs/project_notes.md`).
Rating: DEFENSIBLE. Owners: KV, RK.

**Q10. Which vertices are "influential", and why does that choice matter?**
The top fraction by degree (10 % in the band notebooks, 20 % in the coarse-grained run, 30 % in
`code_10`/`code_12`). Four estimators exist and are recorded side by side so they are never confused.
Evidence: `docs/project_notes.md`, "Which graph each published number was computed on".
Follow-up: "Then which Δα is right?" None is a property of the MOF, because none converges with size
(Q11). That is why the choice does not rescue the descriptor.
Rating: DEFENSIBLE. Owners: KV, KS.

---

## 3. Part 1: results and the withdrawal

**Q11. Why was the Δα band withdrawn?**
Two reasons. First, the published bands were computed on the atomic graph, where one power law is fitted
across two length scales (inside a linker, and across the framework); that is not a valid scaling
measurement. Second, on the correct block graph Δα still grows linearly with ln(diameter) on every net
tested and never settles: slopes 0.782 (tbo), 0.732 (pcu), 0.886 (sod), 0.692 (fcu), R² ≥ 0.998.
Narrowing the q range (|q| ≤ 10 down to 2) does not stop the drift.
Evidence: `data/spectrum_descriptors/size_scaling/convergence_sweep.json` (`_run_size_scaling.py`);
Results page; figure `fig13_convergence.png`.
Follow-up: "UiO-66 has only three points." True: diameters 8, 12, 16; its line says little on its own.
The other three nets have five sizes each and show the same behaviour.
Rating: DEFENSIBLE. Owners: RK, KV.

**Q12. Explain the mechanism of the size drift.**
At |q| = 10 the sum Σ p_i^q is dominated by the single most extreme box. The smallest possible measure is
one vertex, p = 1/N, so α at the negative-q end carries a ln N term and moves with system size. At extreme
q the spectrum measures the extreme value of one box, not a scaling law.
Rating: DEFENSIBLE. Owners: KV, RK.

**Q13. Your classes (Narrow / Medium / Wide) differed in chemistry. Is that not a finding?**
On the correct graph the class follows graph size: r(Δα, block count) = +0.690 (72 hMOF) and +0.716
(55 CoRE MOF). In the hMOF set 48 of 76 structures are the same 4×4×4 pcu graph (256 nodes, 384 edges),
spread across all three classes, so the class within one identical graph is noise. The class width was
also narrower than the per-structure error bar.
Evidence: `full_band_*_cg.json` (`code_17`), `subband_explain_*.json` (`code_18`),
`independent_cg_run_76_hmof.csv`; Results page.
Rating: DEFENSIBLE. Owners: KS, RK.

**Q14. Δα correlated with pore size (r = −0.50). Why drop that?**
Controlling for the size of the analysed graph removes it: partial r = +0.101, while size survives at
+0.621; adding pore size to a size-only model adds 0.005 to R². The same collapse happens on the CoRE set.
Evidence: `notebooks/spectrum/results.json`; Results page; recomputed in the audit.
Rating: DEFENSIBLE. Owners: KS, RK.

**Q15. What survives from Part 1?**
The verified decomposition and periodic-graph pipeline (used in Part 2 for face counting), the habit of
controlling for size in every comparison, the slope of Δα against ln(diameter) as a *proposal* for a
size-free descriptor (varies 0.41–0.82 across 19 hMOF and 0.22–1.47 across 15 CoRE MOF, in a capped
single-seed sweep: not established), and the dimension profile used in the link study.
Rating: DEFENSIBLE (the slope proposal is explicitly unestablished). Owners: RK, KS.

**Q16. The team paper reports the 76-structure band. Is the paper wrong?**
The paper reports the band with its three limitations (size dependence, duplicate graphs, poor fits) and
says Δα was not tested against adsorption. Later work showed the size dependence is decisive. The paper is
kept as submitted; `docs/paper/README.md` explains how it relates to the later results.
Rating: DEFENSIBLE. Owners: RK, IS.

---

## 4. Part 2: the mathematics of shape

**Q17. What decides which faces a crystal can have?**
Symmetry. A family of planes (hkl) can only be a face if its structure factor does not vanish by
symmetry. Centring removes whole classes: F-centring forbids (hkl) of mixed parity, I-centring forbids
h + k + l odd (Propositions 1–2). For ZIF-8 (I-centred) this makes {110} the most widely spaced allowed
family, hence the rhombic dodecahedron.
Evidence: Maths page, Propositions 1–2; From a CIF to a shape, Steps 4–7 (computed from the atoms).
Follow-up: "Glide planes?" They remove reflections of particular orders; the space groups here are
identified with spglib and the absences are checked by computing the structure factor.
Rating: DEFENSIBLE. Owners: RK, KS.

**Q18. What is BFDH, and what does it assume?**
Bravais–Friedel–Donnay–Harker: a face grows at a rate inversely proportional to its effective interplanar
spacing d_eff = d/n (n = first allowed order), so widely spaced faces are slow and large. It uses only the
lattice and the symmetry, no chemistry. Because d_eff = a/(n√(h²+k²+l²)), the cell edge cancels and the
cubic BFDH shape depends only on the centring and point group.
Evidence: `code/morphology/mofmorph/models.py`; `run_phase1.py`; CIF to Shape Step 8.
Follow-up: "So BFDH gives the same shape for every F-centred cubic MOF?" Yes: a truncated octahedron for
MOF-5, HKUST-1 and UiO-66. That is why BFDH alone cannot be the answer and energy models were added.
Rating: DEFENSIBLE. Owners: RK, KV.

**Q19. How do you turn face distances into a shape?**
The crystal is the convex polytope P = {x : n_f·x ≤ R_f for every face f} (Wulff construction, R_f ∝
growth rate or surface energy). It is built by cutting a large block with one plane at a time; a corner is
the solution of three plane equations (Cramer's rule). Propositions 3–5 show the shape is well defined, has
the crystal's symmetry, and is the long-time shape of any seed growing at those speeds.
Evidence: `mofmorph/shape.py`; `website/mof_cif_shape.js`; CIF to Shape Step 9 (every cut shown).
Rating: DEFENSIBLE. Owners: RK, RA.

**Q20. What exactly do Propositions 7 and 8 say?**
Prop. 7: with {100} at distance 1 and {111} at distance t, the shape is a cube for t ≥ √3, a truncated cube
for 2/√3 < t < √3, a cuboctahedron at t = 2/√3, a truncated octahedron for 1/√3 < t < 2/√3, and an
octahedron for t ≤ 1/√3. Prop. 8: in point group −43m {111} splits into two sets of four, so a tetrahedron
is possible; this applies to the ordered UiO-66 file (F-43m) and is forbidden in Fm-3m.
Follow-up: "Is the UiO-66 tetrahedron a prediction?" No. It is allowed by the ordered structure in our
file; real UiO-66 is usually described as Fm-3m. We never present it as a prediction.
Rating: DEFENSIBLE. Owners: RK, KS.

**Q21. Why do you not use the gyration tensor (κ²) to measure shape?**
Proposition 9: any body with cubic or tetrahedral symmetry has an isotropic gyration tensor, so κ² = 0 for
the cube, octahedron and every shape between. Sphericity and the face-normal order parameters Q3, Q4, Q6
(Prop. 10) separate them.
Rating: DEFENSIBLE. Owners: KV, RK.

**Q22. How do you get faces from the graph rather than the lattice?**
Count how many periodic-graph bonds each one-layer slice cuts per unit area (the attachment number,
Props. 11–13). Faces that cut few bonds grow slowly. On a pcu net the counts for {100}/{110}/{111} are
1/2/3 per node, giving a cube; on fcu they are 4/5/3, giving an octahedron, consistent with Chen et al.
(Matter 2020).
Evidence: `mofmorph/graphrule.py`, `graphfaces.py`; Graph Faces page.
Follow-up: "Why does MOF-5 give a truncated cube with the attachment-*energy* model but a cube with the
attachment *rule*?" They are different models: the rule ranks faces by bond count; the energy model
weights broken bonds by their cost. Both are reported, separately named.
Rating: DEFENSIBLE. Owners: RK, KS.

**Q23. What changes when the unit cell is deformed?**
Changing a, b, c or the angles at fixed fractional coordinates keeps the allowed faces (the structure
factor's zeros are unchanged, Prop. 14) but breaks symmetry, so faces that were equivalent separate (Prop.
15). Stretching gives rods, compressing gives plates; Prop. 16 gives the exact condition for a box.
Evidence: `mofmorph/deform.py`; Changing the cell page; 52 stretched cases checked browser against Python.
Follow-up: "Do real MOFs deform like this?" This answers the second reading of the panel's question (one
cell, controlled changes); it shows what geometry alone allows, not that a particular MOF does it.
Rating: DEFENSIBLE. Owners: RK, RA.

**Q24. Have the proofs been checked by anyone else?**
They were written by one author and every proposition is checked numerically in the browser
(`tests/test_maths.js`). No second person has yet checked the proofs line by line.
Rating: PARTIALLY DEFENSIBLE until the check sheet (`docs/defence/check_sheet_proofs.md`) is completed.
Owners: KS, IS (checkers).

---

## 5. Part 2: energies and shapes

**Q25. How are surface energies computed from a force field?**
Cleave the crystal along a plane and sum the broken pair interactions per area: UFF Lennard-Jones terms
plus a flat cost for each broken covalent bond (70 kcal/mol for organic bonds), unrelaxed, no
electrostatics, no solvent. The Wulff shape uses the lowest-energy termination of each face.
Evidence: `mofmorph/forcefield.py`; `run_phase4.py`; Surface Energy page.
Follow-up: "MOF-5 comes out a cube. Is that robust?" Only at the default bond cost: scaling metal–ligand
bonds by 0.5 gives a truncated cube, by 0.25 a truncated octahedron (`run_bond_sensitivity.py`); the
dominant face stays {100}. We say so on the Experiment page.
Follow-up: "So is this really a force-field energy?" Mostly not: 93–98 % of γ is the flat bond cost, so the
face order is the number of bonds cut per area, a broken-bond count; UFF van der Waals adds 2–7 %
(`phase4_results.json`, columns from bonds and from vdW). Say "bond-count surface energy".
Rating: PARTIALLY DEFENSIBLE (unrelaxed, one constant decides MOF-5). Owners: RK, KV.

**Q26. What is the CHGNet "cleavage energy" and why is it only a bound?**
CHGNet is a machine-learned interatomic potential. From a stoichiometric slab,
γ_cl = (E_slab − N·E_bulk,atom)/(2A) is the average of the two exposed faces. When the two faces differ it
is not the energy of either one; for the lowest termination it bounds the face's energy from above.
Evidence: `mofmorph/chgnet_post.py`; `run_chgnet_cleavage.py`; Experiment page; `slab_check.py`
(fragments, released molecules, thickness).
Follow-up: "Is CHGNet accurate for MOF surfaces?" Not shown; it has not been checked against DFT for
these surfaces. The DFT plan (six slabs) exists but has not been run.
Rating: PARTIALLY DEFENSIBLE. Owners: KS, RA.

**Q27. What does Kshitij's steps 1–8 pipeline add, and what did the check find?**
It cuts slabs of whole building blocks, caps every broken metal–linker bond with dissociated water, and
relaxes the lowest termination. Run outside Colab: ZIF-8 matches the lab in static and relaxed modes;
HKUST-1 stops at a truncated octahedron; UiO-66 and Mg-MOF-74 do not match. Eleven problems were found
(K1–K11); K11 (the relaxed cell is re-oriented by a CIF round trip, so the wrong planes are cut) and K3 were
fixed. Relaxation lowers γ by 60 % to almost 100 %, so face order rests on small differences.
Evidence: `code/morphology/steps1_8_check/` (quick mode reproduces exactly from the committed CIFs);
Morphology map page, section on the pipeline.
Rating: PARTIALLY DEFENSIBLE (relaxed run incomplete; K1, K2, K4–K10 open). Owners: KV, RK.

**Q28. Why blend BFDH and Wulff, and which weight is best?**
The blend tests whether geometry and energy together beat either alone. No best weight is claimed: any
weight can be tuned to fit four MOFs; it would have to be chosen on some MOFs and tested on others.
Evidence: Hybrid page; `run_hybrid.py`.
Rating: DEFENSIBLE (as a stated non-claim). Owners: RK, KS.

---

## 6. Validation against experiment

**Q29. Where do the experimental shapes come from?**
134 records from 35 open-access papers on 12 MOFs, each with the shape as written, faces where given, all
reported synthesis conditions, the evidence (SEM/TEM) and the figure it came from. 11 records whose source
could not be identified are held apart.
Evidence: `data/experimental_morphology/` (README, SCHEMA, `dataset/experimental_morphology.csv`).
Follow-up: "Who checked the extraction?" One person extracted all records; a blind second extraction of 20
random records is prepared (`docs/defence/check_sheet_records.md`) but not yet done.
Rating: PARTIALLY DEFENSIBLE. Owners: RA, IS.

**Q30. How well do the models match the laboratory shapes?**
Benchmark on additive-free crystals: ZIF-8 (rhombic dodecahedron) is matched by every model; the MOF-5 cube
by the graph rule, the broken-bond Wulff and the UFF Wulff models (the last only at the default bond cost);
the HKUST-1 octahedron only as the dominant {111} face of a truncated octahedron; the poorly faceted
additive-free UiO-66 cubes by none.
Evidence: `data/experimental_morphology/compare/comparison.csv` (`compare_with_project.py`); Experiment page.
Update, 13 November: the structure-only model was scored on ten MOFs (Q44). On additive-free records it
gets the dominant face for 4 of 5 MOFs.
Follow-up: "So which model is best?" We cannot say: ZIF-8 is matched by everything (its I-centring makes
{110} widest-spaced), HKUST-1 by nothing exactly, UiO-66's target rests on two records; only MOF-5
separates the models, and there one constant decides. Four MOFs cannot rank models.
Rating: DEFENSIBLE as stated (the limitation is the claim). Owners: RA, RK.

**Q31. Why only additive-free crystals in the benchmark?**
No model here contains an additive; comparing with additive-grown crystals would test something the models
do not represent. The additive records are used separately, on the morphology map (Q34–Q35).
Rating: DEFENSIBLE. Owners: RA, KS.

**Q32. Why only four MOFs in Part 2, when Part 1 used 138?** (Now ten; see Q44.)
A shape prediction can only be checked against a crystal that has been grown and imaged. The hMOF
structures are hypothetical and most CoRE MOFs have no reported shape; laboratory shapes exist for about
12 MOFs, mostly five. The method itself (symmetry → allowed faces → shapes) runs on any CIF and was run on 8
CoRE MOFs of six crystal systems to test the code; accuracy is claimed for none of those.
Evidence: `run_core.py`, `core_results.json`; audit record, coverage table.
Follow-up: "Then your conclusions may not generalise." Correct, and we do not generalise them; every
result is stated per MOF.
Rating: DEFENSIBLE. Owners: RK, RA.

---

## 7. The morphology map and conditions

**Q33. What is the morphology map?**
For a cubic crystal with {100}, {110}, {111} faces, the Wulff shape depends only on x = γ110/γ100 and
y = γ111/γ100. Every shape has a region with closed-form boundaries (cube: y ≥ √3 and x ≥ √2;
cuboctahedron: the line y = 2/√3; octahedron: y ≤ 1/√3 and x ≥ √(3/2)·y; rhombic dodecahedron: x ≤ 1/√2
and y ≥ √(3/2)·x). Every model becomes one point per MOF. Proposed by Keerthi, made exact here.
Evidence: `code/morphology/morphology_map/cubic_wulff.py`, `phase_grid.py`, `model_points.py`; Morphology
map page; CIF to Shape Step 12 (derivation).
Follow-up: "Derive the cube boundary." The cube corner (1, 1, 1)γ100 lies at distance √3·γ100 along
[111], so {111} touches the cube only if γ111 < √3·γ100.
Rating: DEFENSIBLE. Owners: KS, RK.

**Q34. What does Test 1 show, and how strong is it?**
An additive that binds one face lowers that face's energy (Gibbs adsorption equation), moving the crystal's
point toward that face's corner through a fixed order of shapes. All 6 laboratory series whose shapes stay
on the map move one way along one axis. If each order were equally likely, the joint chance is
2.7 × 10⁻⁴. This counts only the 6 of 10 series that stay on the map; the other 4 go to plates, spheres,
needles or intergrown crystals, which no Wulff model describes. Shape names are the papers' own.
Evidence: `series_test.py`, `series_results.json`.
Follow-up: "Isn't 1/3 per series a weak null?" It is the right null for "is the order monotone?"; it says
nothing about *which* direction an additive pushes, which Test 2 addresses.
Rating: DEFENSIBLE as stated. Owners: KS, RK.

**Q35. Can you predict the effect of an additive?**
Not yet. Test 2 predicted the dominant face of 82 records (25 papers, leave one paper out): the
structure-only model is right for 86 % of additive-free records, as good as knowing the usual answer for
that MOF (89 %). Adding "this additive type gives face F" made records with additives worse (15 % against
36 %); the difference is significant but small (exact McNemar p = 0.041; 95 % interval over papers +0.02
to +0.50). A first modulator-energy calculation (formate caps) gives a direction for HKUST-1 and ZIF-8 and
an unphysical result for UiO-66; it is not a result.
Evidence: `condition_model.py`, `condition_model_results.json`, `condition_model_predictions.csv`;
`modulator_caps.py`.
Rating: DEFENSIBLE as a negative/partial finding. Owners: KS, RA.

**Q36. What are the "possible morphologies of a CIF"?**
Starting from a structure's point on the map and lowering one face energy at a time lists the shapes it
can take, in order. For the four MOFs, 15 of the 16 polyhedral laboratory shapes are generated. The count
is high partly by construction (single-face moves reach the cube, octahedron and rhombic dodecahedron from
almost anywhere); the testable content is the order along each path, and shapes not yet reported (for
example a rhombic dodecahedron of HKUST-1 with an additive that binds {110}).
Evidence: `possible_morphs.py`, `possible_morphs.json`.
Rating: DEFENSIBLE as stated. Owners: KS, RK.

---

## 8. Linking the two parts

**Q37. Does the Part 1 spectrum say anything about crystal shape?**
The periodic Δα carries no shape information beyond graph size (size-controlled ρ = +0.001, p = 0.99,
55 CoRE MOFs). On a finite MOF-5 particle, Δα separates plates and rods from compact shapes but not compact
shapes from each other.
Evidence: `code/spectrum_shape_relation/run_01`–`run_03`; Spectrum and shape page.
Rating: DEFENSIBLE. Owners: RK, KV.

**Q38. What is the dimension profile, and what does it show?**
Grow clusters of increasing graph radius r from random centres; M(r) blocks within r gives a local
dimension d(r). Calibrated against path, square and cubic lattices of known dimension (a finite graph never
reaches 1, 2, 3). The cube, plate and rod have the d of a 3D, 2D and nearly 1D lattice; r½/D separates the
cube, truncated cube and truncated octahedron predicted for MOF-5 by at least 3.6 seed spreads, and changes
monotonically along both axes of the morphology map.
Evidence: `run_04_dimension_profile_of_crystal_particles.py`, `check_spectrum_shape_relation.py` (21 checks);
`morphology_map/dimension_along_map.py`.
Follow-up: "Does it predict shape?" No: it identifies a particle's shape from its graph. One MOF net,
3–5 seeds; a rhombic dodecahedron and a truncated cube can have similar r½/D.
Rating: PARTIALLY DEFENSIBLE (one net). Owners: RK, KV.

---

## 9. Implementation and reproducibility

**Q39. How do you know the code is correct?**
Two independent implementations (Python in `code/`, JavaScript in `website/`) written from the same
specification agree number by number; 14 website test suites (3,115 checks) compare them and load every
page; Python tests cover each phase; every proposition is checked numerically; known closed forms are
reproduced (the regular truncated octahedron at 2/√3, the rhombic dodecahedron face area).
Evidence: `website/tests/`, `code/morphology/tests*.py`, `_ci_smoke_test.py`; CI on every push.
Rating: DEFENSIBLE. Owners: RA, RK.

**Q40. Can someone else reproduce every number?**
Yes, from the repository alone, checked on 12 November: every script was rerun from another folder and the
quoted numbers recomputed from their result files. The audit found and fixed scripts that depended on the
working folder, three Phase 1 analyses whose input sample had drifted, and inputs that were missing. One
diagnostic is not deterministic and is quoted nowhere.
Evidence: `docs/audit/2026-11-12_audit_of_completed_work.md`; `docs/project_notes.md`.
Rating: DEFENSIBLE. Owners: RK, RA.

**Q41. What were your biggest mistakes, and how were they found?**
The τ fit with a free intercept (found when no spectrum had an apex); the spectrum on the subgraph of
influential nodes (no edges); averaging before the logarithm; discarding periodicity; the bands computed on
the atomic graph; classes narrower than their error bar; the pore-size correlation that was graph size;
the CHGNet cell re-oriented by a file round trip (K11). Each is on the Mistakes page with how it was found
and fixed; withdrawn claims stay visible.
Evidence: Mistakes page (`website/lessons.html`, 26 entries).
Rating: DEFENSIBLE. Owners: IS, RK.

---

## 10. Team and contribution

**Q42. Who did what?**
RK: problem framing, Part 1 analyses (code_12–19), morphology Phases 0–4, blend, link study, website and
tests. KV: the spectrum mathematics (code_10, code_11); the steps 1–8 CHGNet pipeline; DFT plan. RA:
browser platform; the 134-record laboratory dataset; ran the CHGNet notebook; added the CHGNet Wulff
pipeline. KS: band validation and provenance checks; the MorphoGraph-MOF CHGNet notebook; the morphology-map
idea. IS: design decisions, the τ defect, network construction; solvent and modulator effects (planned).
Evidence: Team page.
Rating: DEFENSIBLE. Owners: each member for their own part.

---

## 11. Known weaknesses and honest answers

| Weakness | Honest answer |
|---|---|
| Only MOF-5 separates the energy models, and one constant decides it | Stated on the Experiment page; a DFT check of six slabs is planned, not done. |
| CHGNet and UFF energies are not validated against DFT | Correct; they are compared with each other and with laboratory shapes only. |
| Relaxed water-capped energies are near zero | Face order from that run is not used for any conclusion. |
| One person extracted all laboratory records | A blind second extraction of 20 records is prepared (check sheet). |
| Proofs checked by one author | Numerical checks pass; a second-person proof check is prepared. |
| The map is exact only for cubic crystals | Mg-MOF-74 and other non-cubic MOFs are outside it; stated. |
| No computed adsorption | Two geometric access indicators are computed for eight MOFs (Q47); uptake and selectivity are not. |
| The clean test of the energy model is small | MOFs added after the model was fixed have one additive-free face record (right); with additives 1 of 7 (Q44). |
| "28 of 32 records" is 5 MOFs | Quote "4 of 5 MOFs"; the paper bootstrap gives 73–97 % (Q44). |
| Plates, rods, intergrown crystals are not predicted | They are set by growth kinetics; no Wulff model can produce them. |

## 12. Questions we cannot yet answer with evidence

- Which energy model predicts real MOF crystals best. (NOT DEFENSIBLE as a claim; we do not make it.)
- Whether CHGNet surface energies are accurate for MOFs.
- The size of a modulator's effect on a given face, from first principles.
- Whether the dimension profile works on nets other than MOF-5.

If asked, say that we do not know, why the existing evidence cannot decide it, and what would.

## 13. Mock viva

Run it in pairs; the examiner reads only the question and the follow-up, never the model answer. Pass =
the answer is correct, names its evidence, and survives the follow-up without changing its claim.

| Round | Questions | Rule |
|---|---|---|
| 1. Concepts | Q1, Q5, Q6, Q8, Q17, Q18, Q19 | Explain to a non-specialist in two minutes |
| 2. Methods | Q7, Q9, Q22, Q25, Q26, Q33 | Draw it on paper; point to the file |
| 3. Results | Q11, Q13, Q30, Q34, Q35, Q37 | Give the number, its source and its limit |
| 4. Hard follow-ups | Q7 (prove it), Q12, Q20 (UiO-66), Q32, Q38, Q40 | Examiner pushes until the answer stops at evidence |
| 5. Weaknesses | Section 11, section 12 | Say "we do not know" correctly |

**Preparation duties** (each person must pass every question they own or second):

| Member | Owns | Seconds |
|---|---|---|
| Radha Krishna | Q1, Q4, Q7, Q11, Q12 (second), Q15, Q16, Q17, Q18, Q19, Q20, Q23, Q25, Q28, Q32, Q37, Q38, Q40 | Q2, Q22, Q33, Q34, Q36, Q39, Q41 |
| Kshitij | Q8, Q9, Q10, Q12, Q21, Q27 | Q4, Q7, Q11, Q18, Q25, Q37, Q38 |
| Keerthi | Q13, Q14, Q24 (checker), Q33, Q34, Q35, Q36 | Q10, Q15, Q17, Q20, Q22, Q26, Q28, Q31 |
| Rohith | Q29, Q30, Q31, Q39 | Q3, Q6, Q19, Q23, Q32, Q35, Q40 |
| Isha | Q2, Q5, Q6, Q24 (checker), Q41 | Q1, Q16, Q29 |

## 14. Readiness

| Area | State |
|---|---|
| Scientific correctness | Defensible; every quoted number reproduces (audit of 12 November). |
| Mathematical understanding | Defensible on evidence; a second-person proof check is pending. |
| Implementation understanding | Defensible on evidence; to be shown in the mock viva. |
| Validity and reproducibility | Defensible; one non-deterministic diagnostic, quoted nowhere. |
| Design justification | Defensible (Journey page, "Defending each key decision"). |
| Critical reading of results | Defensible: the limits are the claims. |
| Limits and failure cases | Defensible (sections 11–12). |
| Original objective ↔ deliverables | Partly: geometric access indicators are computed for eight MOFs; adsorption itself is not. |

No question is rated NOT DEFENSIBLE for a claim the project makes. The project is not panel-ready until
every member passes the mock viva for the questions they own and second, and the two second-person checks
(records, proofs) are done.

---

## 15. Added 13 November: ten MOFs, steering, gas access, and questions the team asked

**Q43. The panel asked about the unit cell. Why did you work on the whole crystal?**
The unit cell is the input; the morphology is the output. A unit cell is the repeating box of atoms
(a, b, c, three angles and the atom positions); a morphology is the shape of a crystal of millions of cells,
bounded by faces such as {100} and {111}. The panel wrote: "Is it possible to generate at least a few
morphologies from the given unit cell structure?" (Morphology page). So we go from the cell to the
crystal shapes it can grow into. Their remark that the CIF values may be changed is answered separately:
the Changing the cell page keeps the fractional coordinates, changes a, b, c and the angles, and shows the
allowed faces stay the same while their spacings change, giving plates and rods from a cubic cell.
Evidence: `morphology.html` (the panel's text), `deform.html`, `mofmorph/deform.py`, `mof_deform.js`,
`test_morph_pages.js` (52 stretched cases).
Follow-up: "Is a stretched cell a real MOF?" No; it is a hypothetical framework, and the page says so.
Rating: DEFENSIBLE. Owners: RK, KS.

**Q44. How well does the prediction do on ten MOFs?**
Structure files for eight (six published, IRMOF-3 and IRMOF-8 from RASPA2, ZIF-67 built from ZIF-8 by
replacing Zn with Co); two scored with stand-ins and reported apart. On additive-free records the
dominant face is right for 4 of 5 MOFs (MOF-5 9/9, ZIF-8 11/12, HKUST-1 7/8, IRMOF-3 1/1; UiO-66 0/2), from
32 records and 13 papers, the same as the most common laboratory answer for each MOF, but without using
laboratory data. For a MOF never grown, that laboratory baseline gets 5 of 32. With additives no model is
reliable (13–21 of 44). Mg-MOF-74: BFDH predicts a rod; 9 of 10 laboratory crystals are elongated.
Evidence: `run_benchmark_mofs.py` → `benchmark_mofs.json` (`face_scores`, `evidence_units`); Shape advisor.
Follow-up: "32 records is not 32 tests." Correct: the model makes one prediction per MOF, so it is 5 tests.
We quote 4 of 5 MOFs and a paper bootstrap (73–97 %).
Follow-up: "Were the model's settings tuned on those MOFs?" The bond cost and tolerances were fixed on the
four demonstration MOFs. The MOFs added later are the clean test: one additive-free record (right), and
1 of 7 with additives. That test is small; say so.
Rating: PARTIALLY DEFENSIBLE (small clean test). Owners: RA, RK.

**Q45. Why these ten MOFs and not others?**
They are the MOFs with laboratory shape records in the 134-record dataset (12 MOFs); two (SNU-70,
Zn₄O(FMA)₃) have no structure file available here. A shape prediction can only be scored where crystals
were grown and imaged.
Evidence: `data/experimental_morphology/`; `data/structures/benchmark/README.md`.
Rating: DEFENSIBLE. Owners: RA, KS.

**Q46. How do you "steer" a shape, and what do the percentages mean?**
An additive that binds a face lowers that face's surface energy (Gibbs: dγ = −Γ dμ). On the cubic map the
shape depends only on x = γ110/γ100 and y = γ111/γ100, so for each face we compute how far its energy must
fall for it to become the main face (bisection on exact Wulff areas) and for the pure shape (closed forms:
cube needs y ≥ √3 and x ≥ √2; octahedron y ≤ 1/√3 and x ≥ √(3/2)·y; rhombic dodecahedron x ≤ 1/√2 and
y ≥ √(3/2)·x). The percentages are relative to bond-count energies: they rank how hard a change is; they
are not binding energies.
Evidence: `run_shape_steering.py`; `check_new_analyses.py` (each factor gives the pure shape).
Follow-up: "Derive the octahedron condition." The [110] support of a regular octahedron is √(3/2) times its
face distance, so {110} does not appear while γ110 ≥ √(3/2)·γ111.
Rating: DEFENSIBLE as relative indications. Owners: KS, RK.

**Q47. What does "open to CO₂" mean, and is it adsorption?**
Each face is cut at its lowest-energy termination; every point of that plane is tested for whether a
probe sphere of radius 1.65 Å (CO₂) or 1.82 Å (N₂) fits without overlapping a framework atom (Bondi
radii). The open fraction is the share of the face such a molecule can enter. For a whole crystal: open
surface (area-weighted) and L = V/A; fill time scales as L², initial uptake rate as open fraction × A/V.
It is not adsorption: no energies, no isotherm, no selectivity, no diffusion coefficient.
Evidence: `run_shape_adsorption.py`; `check_new_analyses.py` (plane average equals the 3D value).
Follow-up: "Is an open point really an entrance?" Not necessarily: connection to the pore network is not
tested (Zeo++ could not be installed). A known limit.
Rating: PARTIALLY DEFENSIBLE. Owners: KS, IS.

**Q48. Why did you not train a machine-learning model (for example a GNN) to predict shape?**
Because the structure already determines the allowed faces and, with an energy model, a shape; a learned
model would need many labelled MOFs, and the laboratory data cover 12 MOFs. A model trained on 12 would
memorise them. Our leave-whole-MOF-out baseline shows what learning from other MOFs gives: 5 of 32.
Rating: DEFENSIBLE. Owners: RK, RA.

**Q49. How did you handle missing or unclear data?**
Records without a dominant face are not scored for faces; habit is scored where given. Three records are
counted as additive-free by judgement (an amount "lowest (or none)", and two with no additive recorded);
they are listed in `benchmark_mofs.json`. MOFs without a structure file are not predicted. Nothing is filled in.
Rating: DEFENSIBLE. Owners: RA, IS.

**Q50. Your IRMOF-8 and hMOF files have broken or no symmetry. Does that matter?**
Yes. IRMOF-8's file keeps only P2₁/c because its naphthalene linkers are ordered, so planes an ideal
Fm-3m framework would cancel are kept; its prediction is flagged. 71 of 77 hMOF files are P1, so every hMOF
comes out compact: a property of the files, not of the frameworks. Nothing is concluded from it.
Evidence: `data/structures/benchmark/README.md`; `dataset_shapes.json`.
Rating: DEFENSIBLE as a stated limit. Owners: RK, KV.

**Q51. (Part I) How do you know Δα measures the MOF and not your algorithm?**
We checked it after the bands were withdrawn: the same box-covering calculation on a simple cubic lattice,
in which every vertex is identical, gives Δα = 1.86–2.53, growing with size, in the same range as the MOFs.
In a periodic net every vertex grows as r³ at long range, so a true spectrum of an infinite crystal is a
single point. So Δα as computed measures the covering algorithm and graph size, which is why Part I is a
negative result. Do not defend the old wording "Δα is a heterogeneity score".
Evidence: the audit of 13 November (section 3). The test script is kept outside the repository by team
decision; it can be rerun on request.
Rating: DEFENSIBLE as a negative result. Owners: KV, IS.
