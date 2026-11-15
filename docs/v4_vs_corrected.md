# Isha's v4 notebook and the corrected notebook: what differs, and whether to merge

16 November 2026. Written for the team meeting before the Phase II review.

## 1. Are the two the same?

No. They started from the same notebook (the team notebook of 14 November) and changed different things.

| | Isha's v4 (`nb_2026-11-15_v4_isha/MOF_Wulff_steps1-8_plus_GNN_v4.ipynb`) | Corrected notebook (`nb_2026-11-14/MOF_Wulff_steps1_8_plus_GNN_corrected.ipynb`) |
|---|---|---|
| New feature | **Morphology spectrum** (`morphspec.py`, cells 14, 14a, 14b, 14c): every shape class the face set can reach and the smallest change in a γ ratio that reaches each one | none |
| `wulff()` | new option `bounded=` that skips the closed-shape check when it is already known (speed only, same result) | unchanged |
| Water reference in γ | free molecule at 0 K (as on 14 November) | water at a stated chemical potential; default liquid water, 298 K |
| Capping of a bridging oxygen | can put two H on one O (C–OH₂⁺) | at most one H per donor; the surplus H turns a metal–OH into bound water |
| Mg-MOF-74 slab | cut from the unrelaxed conventional cell; metal–oxygen rod split | relaxed cell, rod kept whole |
| Face ranking | interplanar spacing only | effective spacing with exact absences from the space group |
| Shape names | coarse | exact names (cuboctahedron, open shapes called "open") |
| GNN labels | γ ≤ 0 used as training labels | moved to the stated water condition; γ ≤ 0 dropped and listed |
| DFT input files | slab normal not along z, no dipole correction | rotated, dipole correction, correct spin |
| Slab-thickness check | none | cell 5b |

Everything else is the same code. Isha's v4 changes 4 lines of `mofwulff.py` and adds one module; the corrected
notebook changes about 150 lines of `mofwulff.py` and 20 of `mofgnn.py`.

## 2. What happens if v4 is used exactly as it is

The morphology spectrum itself is correct. Its 20 built-in self-tests pass when run here on a CPU (ZIF-8, IRMOF-1,
Mg-MOF-74 and HKUST-1 CIFs included), and its definition (distance = largest minus smallest log-change of the γ
ratios, refined by bisection and re-checked) is sound.

The problem is the γ values it is fed. In v4 they still come from the 14 November energy formula, so:

1. **Negative surface energies come back.** With the 0 K water reference, 6 relaxed slabs of the 15 November GPU run are
   below zero (MIL-140A {111} twice, Mg-MOF-74 {2̅10}, ZnBDC three faces). The spectrum then refuses to give a favoured shape for those MOFs (its own
   docstring names Mg-MOF-74 as an example). At liquid-water conditions none of the 98 relaxed slabs of the corrected
   GPU run is negative.
2. **Shapes can change with the water condition.** For ZnBDC, MIL-47 and MOF-70 the main face changes between the
   0 K reference and real conditions. Spectrum distances computed at 0 K are therefore for an unphysical condition.
3. **Mg-MOF-74 gives no rod** without the rod-cell fix; with it, the corrected run gives the laboratory habit (a
   hexagonal rod along c, {2̅10} 77 %).
4. **26 of 118 slabs** (Cd3BTB2, Mg-MOF-74, Ni-DOBDC) carry an impossible C–OH₂⁺ group under the old capping rule.
5. The numbers in the report, website and slides come from the corrected run. If v4 is presented as the code that
   produced them, a panel member who runs v4 will get different numbers.

## 3. What a merge means, concretely

A merge does **not** rewrite Isha's work. It copies her cells 14–14c and `morphspec.py` unchanged (only the file
paths `/content/...` become the notebook's own folder) into the corrected notebook, and adds her 4-line `bounded=`
change to the corrected `wulff()`.

This has been done as a proposal, not as the final code:
`nb_2026-11-15_v4_isha/merge_proposal/MOF_Wulff_v4_spectrum_plus_corrections_PROPOSAL.ipynb`
(built by `make_merged_notebook.py` in the same folder). Her self-tests run on the merged modules: 22 of 22 pass
(the 20 built-in checks plus four real CIFs instead of two).

## 4. What her spectrum gives on the corrected energies

`nb_2026-11-15_v4_isha/spectrum_on_corrected_run.py` runs her `morphspec.py`, unchanged, on the corrected GPU run's
energies at liquid water (result: `spectrum_corrected_liquid_water.json`).

| MOF | Favoured shape (corrected energies) | Laboratory | Distance to the laboratory shape | Nearest other class |
|---|---|---|---|---|
| ZIF-8 | rhombic dodecahedron, {110} 100 % | rhombic dodecahedron | 0 % (same class) | truncated rhombic dodecahedron with {111}, 11.7 % |
| HKUST-1 | truncated octahedron, {111} 66 %, {100} 33 % | octahedron | octahedron 37.2 % (lower {111} relative to {100}) | same shape plus a small {110} facet, 3.0 % |
| UiO-66 | truncated octahedron, {111} 81 %, {100} 18 % | without additives: cube (2 of 3 records); with benzoic or acetic acid: octahedron (4 records) | octahedron 19.7 % (lower {111}); cube 80.4 % (lower {100}) | same shape plus a small {110} facet, 1.8 % |
| Mg-MOF-74 | hexagonal rod, {2̅10} 77 %, {101} 23 % | rod along c | 0 % (same class) | rod with {001} end faces, 29.2 % |

"Change" is the smallest change in the ratio of two face energies that reaches the class (Isha's definition). The
nearest classes are often the same shape with one extra small facet; the distance to the laboratory shape is the
number that matters.

"Octahedron" here is the spectrum's class name, which follows the project's naming rule: {111} covers at least 95 % of
the surface. For every {100} facet to vanish, γ{111}/γ{100} must fall to 1/√3 = 0.577; from the corrected values
(0.829 for UiO-66, 0.951 for HKUST-1) that is a change of 43.7 % and 64.7 %.

What this says about UiO-66, the one MOF the pipeline misses: the octahedra grown with benzoic or acetic acid are
close (a 19.7 % change in γ{111}/γ{100}, 44 % for a perfect octahedron), but the cubes grown without additives are
far (80.4 %). An additive that binds {111} would push the shape in the observed direction; the additive-free cube is
not explained by these energies. This is stated as it is, not as a near miss.

## 5. Recommendation

Merge. Present the morphology spectrum as Isha's contribution, run on the corrected energies. The arguments, in
the order to give them:

1. Nothing of Isha's is changed; her code is copied in as it is and her tests pass.
2. Without the corrections, the spectrum has no favoured point for three MOFs and gives 0 K numbers for the rest.
3. Every number the team will present was produced by the corrected code. Presenting v4 alone means presenting code
   that does not reproduce our own slides.
4. If the team still prefers v4 alone, say clearly in the review that the reported surface energies come from the
   corrected run, and show the spectrum figures as computed by v4 (MIL-125).

## 6. Isha's MIL-125 figures (from her own v4 run)

21 images in `nb_2026-11-15_v4_isha/spectrum_figures_MIL-125/`. MIL-125 is tetragonal with four face families
({001}, {100}, {101}, {110}), so the scan is a 3-axis Sobol scan.

- GNN γ (fig_01, fig_02): favoured shape block/prism, {101} 58 %, {110} 41 %; it is in the same class as BFDH.
  Nearest other classes: plate {101}+{110} at 8.1 %, needle/rod {101}+{110} at 10.7 %.
- CHGNet relaxed γ (fig_11, fig_21): favoured block/prism, {101} 90 %, {110} 6 %, {001} 3 %. Nearest other classes:
  plate {101}+{110} at 3.5 %, block/prism {101} at 5.1 %, plate {101} at 6.3 %.
- These CHGNet values use the 0 K water reference of v4. MIL-125 was not in the corrected run, so they have not been
  recomputed at liquid water.
- No laboratory habit for MIL-125 has been checked against the project's records, so these figures are shown as a
  demonstration of the method, not as a validated prediction.
