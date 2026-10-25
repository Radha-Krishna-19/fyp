# Work log: experimental morphology task and CHGNet runs

Last updated 2026-10-14. This file records what was done, in order, with the
result of each step and its limits. Folder layout and how to rebuild the
dataset are in `README.md`.

## 1. The task

Given by Keerthi: find real laboratory results for CO2-adsorbing MOFs and
align them by solvent, temperature, kinetics, additives and other synthesis
conditions, combining many sources. It supplies the experimental side of the
MorphoGraph-MOF pipeline (step 8, "test on known experimental morphologies").

## 2. Experimental dataset (done, about 75 % of the full task)

| Table | Rows | File |
|---|---|---|
| Crystal shape with synthesis conditions | 104 | `dataset/experimental_morphology.csv` |
| Crystallisation kinetics (rate constants, Avrami exponents, activation energies) | 25 | `dataset/kinetics.csv` |
| Measured CO2 uptake, tied to how the sample was made | 18 | `dataset/co2_adsorption.csv` |
| Results grouped per MOF and per controlled series | | `dataset/aligned_by_mof.md` |

- 28 papers, 14 MOFs (list and DOIs in `PAPERS_USED.md`).
- Only open-access copies were used (journal OA, PubMed Central, university
  repositories, OSTI). No paywall bypass was used.
- Gaps: solvent alignment is complete only for ZIF-8; Mg-MOF-74 shape data is
  abstract-only; CALF-20 and MIL-101(Cr) have CO2 data but no shape data; no
  paper measures CO2 uptake on two shapes of the same MOF. Details in
  `README.md` under "To do".

## 3. Project predictions compared with experiment (done)

`compare/compare_with_project.py` writes `compare/COMPARISON.md` and
`compare/comparison.csv`. It compares the project's own morphology methods
(BFDH, graph attachment rule, attachment-energy Wulff, broken-bond Wulff, UFF
Wulff, from `2_python/morphology/`) with a hand-picked experimental benchmark
for four MOFs:

| MOF | Experimental benchmark | Strength |
|---|---|---|
| MOF-5 | cube, {100} | strong: 8 of 8 records, two laboratories |
| HKUST-1 | octahedron, {111} | 4 of 4 records |
| UiO-66 | cube | weak: 2 records, poorly faceted; modulated UiO-66 is octahedral |
| ZIF-8 | rhombic dodecahedron, {110} | strong: 9 of 9 records |

The benchmark uses additive-free crystals only, because every method models a
bare crystal in vacuum.

## 4. Keerthi's notebook (MorphoGraph-MOF, CHGNet)

Notebook: `notebook/MorphoGraph_MOF_revised.ipynb` (unchanged copy).

What it does for each MOF:
1. Reads the CIF, finds symmetry (spglib), reduces to the primitive cell.
2. Relaxes the bulk with CHGNet at fixed cell; records energy per atom.
3. Lists Miller directions up to |h|,|k|,|l| ≤ 1 (26 directions) and groups
   symmetry-equivalent ones into face classes.
4. Cuts slabs for every possible termination of each face class.
5. Relaxes each slab with CHGNet (fmax < 0.05 eV/Å) and computes the pair
   excess (E_slab − N·E_bulk)/A = γ_top + γ_bottom.
6. Solves the pair equations for individual surface energies γ.
7. Builds a Wulff shape from the γ values, only if every face has one.
8. Draws two geometry-only shapes (equal γ, and BFDH by d_hkl), both labelled
   by the notebook as not predictions, plus 3D viewers, and zips the results.

### 4a. How it was run

- A Colab version was built: `notebook/MorphoGraph_MOF_colab_4MOFs.ipynb`. It
  embeds the CIFs from the repository's `2_python/` folder, fixes the Miller
  limit at 1 (other settings are the notebook defaults) and adds a driver cell
  that runs each MOF and downloads its zip. The science cell is the original.
- Structures: MOF-5, HKUST-1, UiO-66. ZIF-8 was dropped because its CIF is P1
  when hydrogens are included, so spglib finds no symmetry.
- CIF sources: MOF-5, HKUST-1 and UiO-66 are VESTA exports (P1) with no source
  in the header; ZIF-8 is from the RASPA library (Park et al., PNAS 2006).
- Hardware: Colab GPU. A local CPU run of MOF-5 (Python 3.12, CPU torch) was
  used as a cross-check: its first face class matched Colab exactly. It was
  stopped at class 3 of 4 once Colab had finished.
- Output: the three result folders are in `Desktop\fyp\OUTPUTSSSSSSS\`
  (zips also in Downloads). MOF-5 took 37.0 min; HKUST-1 started about 07:01
  and UiO-66 about 08:00.

### 4b. Result: no CHGNet shape for any of the three MOFs

Every face class of every MOF ended `underdetermined_surface_energies`. The
individual surface energy table is empty for all three, so the notebook built
no Wulff shape.

| MOF | Face classes | Matrix rank / unknowns, per class |
|---|---|---|
| MOF-5 | 4 | 20/37, 8/15, 35/67, 13/22 |
| HKUST-1 | 4 | 15/28, 17/31, 23/46, 21/41 |
| UiO-66 | 6 | 21/42, 17/32, 17/34, 21/42, 15/30, 16/32 |

Why: almost every slab has a different termination on top and bottom, and each
slab also appears flipped (top and bottom fingerprints swapped, same pair
excess). A slab gives only the sum γ_top + γ_bottom, and the flipped copies
repeat the same equation, so there are about half as many independent equations
as unknowns.

Correction (later on 2026-10-14): an earlier version of this log said
`symmetric_diagnostic` was False for every slab. That was wrong. 2 HKUST-1,
6 MOF-5 and 2 UiO-66 slabs were symmetric as cut; relaxation broke their
symmetry, so the notebook (which tests symmetry after relaxation) still counted
two unknowns for each. Section 6 uses them.

### 4c. Rough diagnostic (not a CHGNet prediction)

Half of the lowest pair excess per face, in J/m² (1 eV/Å² = 16.02 J/m²). This
is the average of two different terminations, not either one's energy, and it
was not run through a Wulff construction.

| Face (conventional) | MOF-5 | HKUST-1 | UiO-66 |
|---|---|---|---|
| {100} | 0.127 | 0.163 | **0.210** |
| {111} | **0.098** | **0.151** | 0.287 |
| {110} | 0.184 | 0.181 | 0.551 |
| {311} | 0.222 | 0.210 | 0.533 |

| MOF | Shape these numbers suggest | Experiment | Agreement |
|---|---|---|---|
| MOF-5 | truncated octahedron ({111} lowest) | cube | no |
| HKUST-1 | truncated octahedron or cuboctahedron | octahedron | partial |
| UiO-66 | truncated cube ({100} lowest) | cube (weak benchmark) | partial |

Primitive-to-conventional face mapping used: h_conv = P⁻¹ h_prim with
P⁻¹ = [[-1,1,1],[1,-1,1],[1,1,-1]], checked against slab areas
(a²√3/4, a²/2, a²/√2, a²√11/4).

### 4d. Proposed fix (to be agreed with Keerthi)

Build symmetric slabs (same termination on both sides). Then γ = pair excess
/ 2 exactly and the Wulff shape can be built. This changes Keerthi's
notebook, so it has not been done without her agreement.

## 5. Revised notebook (written, not yet run)

`notebook/MorphoGraph_MOF_colab_symmetric_slabs.ipynb`, built by
`tools/make_symmetric_nb.py` from the Colab notebook. Every change is marked
`SYMMETRIC-SLAB CHANGE`: linkers kept whole where pymatgen can (no loose H,
CH or CO2 pieces); a slab symmetric as cut counts as one termination; any
termination energy the equations do fix is kept (null-space test); remaining
facets get the cleavage bound, labelled as an upper bound. A dry run without
CHGNet (`2_python/morphology/slab_options_check.py`) showed pymatgen's
symmetrize option gives nothing new for these MOFs, so expect mostly
upper-bound estimates and a shorter run than before.

## 6. Review and integration into the project (2026-10-14, in `fyp (4)`)

All of the above was copied into the project repository copy in
`Desktop\fyp (4)\fyp\metal_oxo_deep_dive` (nothing committed). Findings, with
the script that shows each:

| Finding | Evidence |
|---|---|
| CHGNet cleavage proxy: MOF-5 truncated octahedron, HKUST-1 truncated octahedron, UiO-66 truncated cube | `run_chgnet_cleavage.py` |
| Most CHGNet slabs, as cut, hold loose H, O, CH, C2H2 pieces (linkers cut); some release CO2 on relaxation | `slab_check.py` |
| Dropping those slabs changes no shape | `run_chgnet_cleavage.py` (intact_only) |
| The few symmetric slabs are high-energy terminations, 1.4-9x the cleavage bound | `chgnet_post.symmetric_slab_gammas` |
| Slabs are 15-30 A thick (1-2 framework layers); not thickness-converged | `slab_check.py` |
| UFF MOF-5 cube depends on the flat bond cost (0.25x Zn-O gives a truncated octahedron) | `run_bond_sensitivity.py` |
| Bug fixed: the general UFF pipeline dropped H when symmetry was found without H (ZIF-8 {111} energy half its value) | `tests_review.py` |
| Pipeline runs on 8 CoRE MOF structures of six crystal systems | `run_core.py` |
| Primary open-access source for octahedral modulated UiO-66 | butova2023 record |
| 11 records with unidentifiable sources moved out of the main CSV | `build_dataset.py` |

## 7. Still open

1. Run the revised notebook on Colab (HKUST-1 first) and add its zips to
   `2_python/morphology/data/chgnet_runs/`.
2. DFT check of MOF-5 and UiO-66 faces (Kshitiz): `2_python/morphology/DFT_CHECK_PLAN.md`.
3. ZIF-8 with a CIF that keeps its symmetry, so all four benchmark MOFs run.
4. Identify the 11 unverified records' sources.
5. A fifth MOF if the team wants one (ZIF-67 or CALF-20); needs a CIF and shape records.
6. Optional papers listed in `README.md` "To do".
