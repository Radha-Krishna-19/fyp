# G070 Phase II review, 16 November 2026: presentation notes

These notes follow the deck slide by slide (`presentation.pdf` from LaTeX and `G070_Phase2_Review.pptx` have the same
order). For each slide: what to say (about one minute), the numbers to have ready, and the questions a panel member is
likely to ask. Every number here is in a result file named in `HANDOFF.md`.

Suggested split: Radha Krishna slides 1–7 and 13–14; Rohith slides 8 and 12 (dataset and benchmark); Kshitij slides 9–11
and 15 (pipeline and GPU run); Isha slides 16–18 (GNN and morphology spectrum); Keerthi slides 19–20. Change it as
the team decides.

---

## Title and guide approval

**Say.** "We are G070. After Review 1 the panel asked: given the unit cell of an established MOF, can we generate the
crystal shapes it can take, mathematically and computationally? This review answers that question and says how far
the answer can be trusted."

Insert the guide's approval e-mail screenshot on slide 2 before the review.

## Slide 3. Problem definition

**Say.** A MOF is used as a powder of small crystals. Gas enters a crystal only through its surface, so two crystals of
the same material and volume can fill at very different speeds.

**Worked example (have it ready).** Volume 1000 µm³ in each case. The diffusion length is L = V/A.

| Shape | Size (µm) | A (µm²) | L (µm) | Fill time relative to the cube (∝ L²) |
|---|---|---|---|---|
| cube | 10 × 10 × 10 | 600 | 1.67 | 1.00 |
| plate | 20 × 20 × 2.5 | 1000 | 1.00 | 0.36 |
| needle | 2.5 × 2.5 × 160 | 1613 | 0.62 | 0.14 |

**Gap.** For ordinary crystals one computes surface energies with DFT and draws the Wulff shape. A MOF slab has
200–600 atoms and each MOF needs tens of slabs, so DFT is out of reach for screening. MOF shape papers are
experimental, one MOF and one additive at a time.

**Likely question:** "Why not just use DFT?" Answer: we prepared the CP2K inputs (slab normal along z, dipole
correction, correct spin) but did not have HPC time; DFT is the first item of future work.

## Slide 4. Objectives and status

Read the status column. Be direct about O7: a model that maps synthesis conditions to shape is not feasible with
laboratory data for only 12 MOFs; when each MOF is held out in turn, predicting from the other MOFs gets 5 of 32
additive-free records. We report that rather than claim a model.

## Slide 5. Workflow

**Say.** Two tracks.

- **Track A** works from symmetry alone and runs on any CIF in seconds: space group, allowed faces, BFDH shape, position
  on the morphology map, steering and gas-access numbers.
- **Track B** is the team's machine-learned pipeline (steps 1–8). It reads a CIF, cuts surfaces that keep each metal
  cluster and linker whole, caps the cut bonds with water, computes each surface energy with CHGNet and builds the
  Wulff shape.
- Steps 9–13 train a graph neural network to replace the slow relaxation.
- Step 14, new in the version 4 notebook, is the morphology spectrum.

Both tracks are checked against 134 laboratory records.

## Slide 6. Formulation (1): faces and shapes

**Key maths.**

- d_hkl = 1/‖h G⁻¹‖. For a cubic cell, d = a/√(h²+k²+l²).
- **Absence rule.** A reflection n·h is extinct if some symmetry operation (R, t) has hR = h and h·t not an integer.
  The first allowed order n gives d_eff = d/n.
- **Worked example: ZIF-8** (I-43m, a = 16.99 Å, body-centred, so h+k+l must be even).
  - (110): 1+1+0 = 2, even, so n = 1 and d_eff = 16.99/√2 = 12.0 Å.
  - (100): needs n = 2, so d_eff = 8.5 Å.
  - (111): needs n = 2, so d_eff = 4.9 Å.
  - {110} is by far the widest, so ZIF-8 grows as a rhombic dodecahedron, which is what every ZIF-8 paper shows.
- **BFDH.** Each face sits at a distance ∝ 1/d_eff. For an F-centred cube, {100} sits 1.155 times further out than
  {111}. That is a truncated octahedron with 78 % of its area on {111}.
- **Wulff.** The crystal minimises Σ γᵢAᵢ at fixed volume. The shape is the intersection of the half-spaces
  n̂ᵢ·x ≤ γᵢ, and it depends only on the energy ratios x = γ110/γ100 and y = γ111/γ100.
  - cube: y ≥ √3 and x ≥ √2
  - octahedron: y ≤ 1/√3
  - cuboctahedron: y = 2/√3

**Likely question:** "Where do √3 and 1/√3 come from?" A cube with faces at distance γ100 from the centre has its
corners at distance √3·γ100 along ⟨111⟩, so a {111} plane at γ111 ≥ √3·γ100 misses the cube entirely: that is the cube
border, y ≥ √3. In the same way an octahedron with faces at γ111 has its vertices at √3·γ111 along ⟨100⟩, so the {100}
planes vanish when γ100 ≥ √3·γ111, i.e. y ≤ 1/√3.

## Slide 7. Formulation (2): energy, water, spectrum, GNN

**Surface energy.** γ = (E_slab − N·e_bulk − n·μ_H₂O)/2A. To convert, multiply eV/Å² by 16.02 to get J/m².

**Why the water term matters.** Each cut metal–oxygen bond is capped with one water molecule, split into OH⁻ on the
metal and H⁺ on the oxygen. The water has to come from somewhere, so its price is a chemical potential:

    γ(Δμ) = γ₀K − n·Δμ/2A

Δμ for liquid water at 25 °C is −0.570 eV (NIST-JANAF and CODATA). The 14 November notebook used Δμ = 0, a free
molecule at 0 K, which is the cheapest water can ever be.

**Spectrum distance.** s = max_k ln(g_k/g₀k) − min_k ln(g_k/g₀k), reported as (eˢ − 1) × 100 %. It is the smallest
percentage by which the ratio of two face energies must change to reach a given shape. It does not depend on the
overall scale or on which face is the reference.

**GNN.**
- Message passing on the atom graph of the unrelaxed slab, with a softplus output (always positive).
- Loss: Huber (δ = 0.3) plus 0.5 × a pairwise ranking loss within each MOF.
- Pretrained on unrelaxed (static) energies.

## Slide 8. Datasets and metrics

The 134 laboratory records come from 35 papers on 12 MOFs. Each record has the additive, solvent, temperature, the
shape and faces seen, and a page or figure locator. The scoring is set up so that a learned model cannot cheat:

- the baseline is the per-MOF laboratory majority with the scored paper held out;
- the GNN is tested by holding out one whole MOF at a time.

## Slides 9–10. Implementation overview

Walk through steps 1–14 in one sentence each. Points to stress:

- Slabs are cut only through metal–ligand bonds, so no linker is broken.
- Every slab that is not a whole number of formula units is rejected.
- The final team notebook is version 4.

## Slide 11. Core modules

**Capping rule.** A bridging oxygen that loses two metals must not receive two protons, because that would make an
impossible C–OH₂⁺. The rule gives at most one H per donor, and turns the surplus proton into a water molecule bound to
the metal. It matters for MOFs with bridging oxygens (Cd3BTB2, Mg-MOF-74, Ni-DOBDC).

## Slide 12. Results against laboratory records

**Say.** Without additives, the structure-only bond-count Wulff model gets the main face of 28 of 32 records. That is
as many as the laboratory majority gets, and the model never sees laboratory data. By MOF:

- MOF-5 9/9
- ZIF-8 11/12
- HKUST-1 7/8
- IRMOF-3 1/1
- UiO-66 0/2

So 4 of 5 MOFs are right. Re-sampling whole papers gives a 95 % range of 73–97 %. With additives no structure-only
model is reliable, and we do not claim one is.

**Likely question:** "Isn't 32 records small?" Yes. It is five independent tests, one per MOF, which is why we report
the paper bootstrap and the per-MOF counts.

## Slide 13. Shape space

**Say.** For a cubic MOF every possible shape is a region of one map with exact borders. The strip shows the family
from cube to octahedron.

**Attachment numbers.** Count how many bonds a newly arriving node can make on each face.

- MOF-5 (pcu net): 1 on {100}, 2 on {110}, 3 on {111}. The {100} face grows slowest, so the crystal is a cube.
- UiO-66 (fcu net): 3 on {111}, 4 on {100}, 5 on {110}. The crystal is an octahedron, as Chen et al. (Matter 2020)
  report.

**Steering example: MOF-5.** Our energies put MOF-5 at x = 2.81, y = 1.73, a cube. To turn it into an octahedron, an
additive must lower γ{111} by 66.6 %; for {111} faces merely to dominate, by 38.1 %. The laboratory records agree in
direction: tricarboxylate additives give {111} faces.

## Slide 14. The surface energy depends on the water condition

**Say.** Each cut metal–oxygen bond is capped with one water molecule, split into OH⁻ on the metal and H⁺ on the
oxygen. That water comes from a reservoir (the synthesis solution), so the surface energy depends on its chemical
potential: γ(Δμ) = γ₀K − n·Δμ/2A. We report every shape at liquid water, 298 K (Δμ = −0.5695 eV, from NIST-JANAF and
CODATA).

**Worked example: ZnBDC {001}.**
- n = 4 caps on A = 104.08 Å².
- n/2A = 0.0192 eV/Å² per eV, which is 0.308 J/m² per eV.
- With water taken as a free molecule at 0 K: γ = −0.024 J/m². At liquid water: −0.024 + 0.308 × 0.5695 = +0.151 J/m².

So the water condition is an input that must be stated; a free molecule at 0 K is not a physical reference for a
crystal grown in solution.

**Capping rules used:** at most one H per donor oxygen; metal–oxygen rods (Mg-MOF-74) kept whole; slab and bulk from
the same relaxed cell; the UiO-66 node with its OH groups.

**Likely question:** "Isn't choosing Δμ a way to make numbers positive?" No. It is the standard ab initio
thermodynamics treatment of an open system (Reuter and Scheffler, 2001), with Δμ taken from tables, not fitted. We also
show how the face energies change with Δμ (the ZnBDC plot), so the condition is visible, not hidden.

## Slide 15. GPU run (Kshitij's laptop, 15 November)

**Run.** 98 relaxed slabs of 16 MOFs, 85 of them converged. At liquid water every surface energy is positive.

**Checks.**
- Slab thickness: ZIF-8 {110} at 24 Å gives 0.0565 J/m² and at 36 Å gives 0.0527 J/m², so the slabs are thick enough.
- MACE-MP-0, an independent model, ranks the slabs like CHGNet: Spearman 0.94–1.00, MAE 0.010–0.028 J/m².

**Shapes.**
- ZIF-8: rhombic dodecahedron, matches the laboratory.
- HKUST-1: main face {111}, matches.
- Mg-MOF-74: hexagonal rod along c, {2̅10} 77 %, matches.
- UiO-66: still a miss.

**Likely question:** "Does MACE agreeing prove CHGNet right?" No. It re-scores CHGNet's geometries, and both models are
trained on similar DFT data. It shows the ranking is not an artefact of one model; DFT is still needed.

## Slide 16. GNN surrogate

**Say.** The GNN predicts the relaxed γ from the unrelaxed slab in seconds instead of minutes of relaxation.

**Result (leave-one-MOF-out MAE).**

| Model | MAE (J/m²) | Main face right |
|---|---|---|
| GNN | 0.131 | 12 of 16 |
| straight line on broken bonds per area | 0.088 | 14 of 16 |
| rescaled static CHGNet energy | 0.084 | – |

We report this as it is. Broken bonds per area already carry most of the surface energy (93–98 % in the bond-count
model), so a one-parameter line is hard to beat with only 16 MOFs. The GNN is the right tool once there are more MOFs.

**Likely question:** "Then why keep the GNN?" It needs no relaxation, so it can screen thousands of CIFs. The CV says
how far it can be trusted today.

## Slide 17. Morphology spectrum on the CHGNet energies at liquid water

**Say.** The morphology spectrum asks: if the energy ratios were changed, which other shapes could this MOF take, and how
big a change is needed for each? It was run on the CHGNet energies at liquid water.

| MOF | Distance from the computed shape to the laboratory shape |
|---|---|
| ZIF-8 | 0 (already the laboratory shape) |
| Mg-MOF-74 | 0 (already the laboratory shape) |
| HKUST-1 | octahedron 37.2 % |
| UiO-66 | octahedron (grown with benzoic or acetic acid) 19.7 %; cube (grown without additives) 80.4 % |

**What it means for UiO-66.** An additive that binds {111} pushes the shape the way the experiments see. The cube
grown without additives is far away, so our energies do not explain it. We say so.

"Octahedron" in the table means at least 95 % {111}. A perfect octahedron for UiO-66 needs 43.7 %.

**Likely question:** "For a cube, isn't the list of shapes fixed by symmetry?" Yes, and the module says so in its own
documentation. The structure-specific part is the distances.

## Slide 18. MIL-125 spectrum

**Say.** MIL-125 is a tetragonal titanium MOF with four face families, so the module samples a three-dimensional
ratio space (Sobol points).

- With CHGNet energies, the favoured shape is a {101} block (90 %), and a plate is only 3.5 % away.
- With GNN energies, it is a {101}+{110} block (the same class as BFDH), and a rod is 10.7 % away.
- These CHGNet values are at the 0 K water reference.

## Slides 19–20. Justification and limits

**Points to make.**
- Symmetry first, because it is exact and free.
- Water as a chemical potential, because capped surfaces are open systems.
- Block-intact cuts, because MOFs grow by whole units.
- Spectrum distances, because they turn "which additive" into "how much must one ratio change".

**Limits, in this order.**
1. No DFT check.
2. The UiO-66 additive-free cube is not reproduced.
3. Wulff is equilibrium; laboratory crystals are grown.
4. Records and proofs need a second-person check.

## If the panel asks about Part I (the connectivity spectrum Δα)

It was tested and withdrawn. Δα grows in a straight line with ln(diameter) on all four test nets (R² ≥ 0.998), and the
"Narrow/Medium/Wide" classes follow graph size: 13 of 14 distinct graphs fall in one class each. It is documented on
the Results page as a negative result.

## What each member did (for the "who did what" question)

| Member | Contribution |
|---|---|
| Radha Krishna | symmetry and face mathematics, BFDH, morphology map, laboratory benchmark, website, checking and correcting the ML pipeline (water reference, capping) |
| Kshitij | steps 1–8 of the notebook; the GPU runs |
| Isha | the GNN surrogate and the morphology spectrum (notebook v4) |
| Keerthi | the first CHGNet notebook (cleavage energies) and the proposal to place every model on one morphology map |
| Rohith | the experimental morphology dataset (`data/experimental_morphology/`) |

Taken from `docs/project_notes.md` and `docs/defence/panel_defence.md`; confirm it with the team before the review.
