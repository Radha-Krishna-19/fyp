# DFT spot-check plan (for Kshitiz)

Written 2026-10-14. Purpose: settle the one disagreement that decides which energy model the
project can trust, using the fewest DFT calculations.

## The question

For MOF-5 the experimental crystals are cubes. A Wulff shape made of {100} and {111} faces is a
cube only when gamma(111) / gamma(100) >= sqrt(3) = 1.732.

| Model | gamma(100) J/m2 | gamma(111) J/m2 | ratio | shape |
|---|---|---|---|---|
| UFF, flat bond cost (Phase 4) | 0.148 | 0.255 | 1.72 | cube (the {111} corners are under 1 % of the area) |
| UFF, metal-ligand bonds x 0.25 | 0.079 | 0.090 | 1.14 | truncated octahedron |
| CHGNet cleavage bound | 0.127 | 0.098 | 0.77 | truncated octahedron |

So one DFT ratio for MOF-5 tells us which model is closer. UiO-66 is the second case (CHGNet
favours {100}, UFF favours {111}); HKUST-1 is a control (all models agree on {111}).

## Which slabs (all intact, lowest-energy, already relaxed by CHGNet)

Files are inside `data/chgnet_runs/<MOF>_MorphoGraph_MOF_revised_results_*.zip`, folder
`slabs_relaxed/`, named `<MOF>_hkl_<h>_<k>_<l>_term_<NNNN>.cif` (minus signs written `m1`).
The bulk reference is `<MOF>_bulk_relaxed_fixed_cell.cif` in the same zip.

| Priority | MOF | Face | Slab file (primitive hkl, termination) | Atoms | Thickness | CHGNet gamma_cl |
|---|---|---|---|---|---|---|
| 1 | MOF-5 | {100} | `MOF-5_hkl_m1_m1_0_term_0013.cif` | 212 | 25.9 A | 0.127 |
| 1 | MOF-5 | {111} | `MOF-5_hkl_m1_m1_m1_term_0022.cif` | 212 | 29.9 A | 0.098 |
| 2 | UiO-66 | {100} | `UiO-66_hkl_m1_m1_0_term_0002.cif` | 228 | 20.5 A | 0.210 |
| 2 | UiO-66 | {111} | `UiO-66_hkl_m1_m1_m1_term_0016.cif` | 228 | 23.7 A | 0.288 |
| 3 | HKUST-1 | {111} | `HKUST-1_hkl_m1_m1_m1_term_0012.cif` | 156 | 15.2 A | 0.152 |
| 3 | HKUST-1 | {100} | `HKUST-1_hkl_m1_m1_0_term_0021.cif` | 312 | 26.3 A | 0.163 |

Each slab is stoichiometric, so gamma_cl = (E_slab - N * E_bulk_per_atom) / (2 A) needs only the
slab energy and the bulk energy per atom from the SAME method.

## How

1. Bulk: PBE-D3(BJ) (or the group's usual functional with dispersion) on the bulk file, fixed cell,
   positions relaxed; take E per atom.
2. Slabs: single point on the CHGNet geometry first (cheap; already tells whether the ordering
   flips). If time allows, relax positions with the cell fixed and repeat.
3. Report gamma_cl for each pair of faces and the ratio gamma(111)/gamma(100).

## How to read the answer

- MOF-5 ratio >= about 1.7: the bond-counting models (graph rule, broken-bond, UFF) are right
  for MOF-5 and CHGNet is not reliable for MOF surfaces.
- MOF-5 ratio <= about 1.2: CHGNet is right in vacuum, and the cubic crystals must owe their
  shape to the solvent or growth kinetics, which no model here contains.
- In between: neither model is reliable; a capped (solvent- or formate-terminated) slab is
  the next step.

Limits: one slab per face, CHGNet geometry, no solvent. The slabs are one or two framework
layers thick; a single thicker slab for MOF-5 {100} would show whether DFT values are converged.
