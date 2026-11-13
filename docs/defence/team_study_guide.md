# Team study guide: the basic questions, in plain words

For the five of us only. It is not linked from the website. Read it before `panel_defence.md`, which has
the full model answers, evidence and follow-ups; the numbers in brackets (Q12) point there.

The rule for every answer: say what we did, why, what the evidence is, and where it stops. If you do not
know, say so and say what would decide it. Never defend a sentence you cannot explain.

---

## 1. The story in five minutes

1. A MOF is a porous crystal: metal clusters joined by organic linkers. Its use (storing or separating
   gases) depends on its pores and on the crystals the powder is made of.
2. **Part I** asked whether one number from a MOF's connectivity, the spectrum width Δα, could pick which
   MOFs deserve hours of simulation. We built the pipeline (CIF → bonds → building blocks → periodic graph
   → spectrum), tested it, and found that Δα grows with the size of the graph and never settles. So the
   answer is **no, as defined**, and the bands are withdrawn. That is a result, not a failure (Q1, Q11).
3. At Panel Review 1 the panel asked: from the unit cell of an established MOF, can you generate a few
   crystal shapes (morphologies), mathematically and by computer? **Part II** answers yes:
   - the space group decides which faces may exist;
   - those faces give a family of shapes (cube, cuboctahedron, octahedron, rhombic dodecahedron, plates
     and rods when the cell is changed);
   - a growth model (BFDH, bond-count surface energy, CHGNet) picks one member;
   - the prediction is checked against 134 laboratory records from 35 papers.
4. On 13 November it was extended to ten MOFs, with how to steer the shape and what each shape exposes
   to a gas (the Shape advisor page).

---

## 2. The "why" questions an examiner asks first

**Why does crystal shape matter at all?** A gas enters a crystal through its surface. The shape decides
which faces form the surface (some faces show more open pores than others) and how much surface the
crystal has for its volume (how far a molecule must diffuse). Two batches of the same MOF with different
shapes can take up gas at different rates although their pores are identical. (Q2, Q47)

**Why do we want the possible shapes, not just one?** Because chemists can change the shape with
additives, solvent or temperature. Knowing the possible shapes, and how hard it is to reach each, tells
them what is worth trying before weeks of synthesis. (Q36, Q46)

**The panel said "unit cell". Why did we work on the whole crystal?** The unit cell is the input and the
crystal shape is the output. A unit cell has no morphology; a crystal of millions of cells does. The
panel's own words: "generate at least a few morphologies from the given unit cell structure". Their remark
that CIF values can be changed is the "Changing the cell" page. (Q43)

**Why BFDH first?** It needs only the lattice and the symmetry, gives a shape for any CIF in seconds,
and is the standard first estimate. It contains no energy, so we add one. (Q18)

**Why a surface energy, and which one?** A face that costs less energy to expose grows slower and
becomes larger (Wulff). Our main energy counts the bonds each plane cuts (every bond 70 kcal/mol) plus a
small van der Waals part (2–7 %). Call it a **bond-count surface energy**, not a force-field energy. (Q25)

**Why not DFT?** It is the reference, but one MOF slab is hundreds of atoms; we have no HPC time. Six
slabs are prepared for a DFT check through the guide. Until then the energies rank faces; they are not
validated. (Q26, `code/morphology/DFT_CHECK_PLAN.md`)

**Why not GCMC adsorption simulations?** A periodic GCMC cell has no shape, so it cannot answer a shape
question. (Q3)

**Why not a machine-learning model or a GNN?** Laboratory shapes exist for 12 MOFs. A learned model would
memorise them. The structure already determines the allowed faces; learning from other MOFs gives 5 of 32
on additive-free records, far below the structure-only model. (Q48)

**Why only these MOFs?** Only MOFs with grown and imaged crystals can be scored; the dataset has 12, and
two have no structure file here. Part I used 138 because it asked a screening question. (Q32, Q45)

**What is ours and what is existing work?** Existing: the decomposition rule, BFDH, Wulff, UFF numbers,
CHGNet, spglib. Ours: the periodic-graph pipeline and its proof, the convergence study, the 16
propositions applied to MOFs, two independent implementations that agree, the exact cubic morphology map,
the laboratory dataset, the ten-MOF benchmark, steering and gas-access indicators, and the record of
every mistake. (Q4)

---

## 3. Numbers to know, with where they come from

| Number | Meaning | Source |
|---|---|---|
| 134 records, 35 papers, 12 MOFs | Laboratory dataset | `data/experimental_morphology/dataset/experimental_morphology.csv` |
| 4 of 5 MOFs | Dominant face right on additive-free records (UiO-66 wrong) | `benchmark_mofs.json`, `evidence_units` |
| 28 of 32 records, 73–97 % | Same result counted by record; paper bootstrap | same |
| 5 of 32 | Baseline for a MOF never grown (majority of the other MOFs) | `face_scores` |
| 13–21 of 44 | Every model with additives: not reliable | `face_scores` |
| 9 of 10 | Mg-MOF-74 crystals elongated, as BFDH predicts | `per_mof` |
| 93–98 % | Share of the surface energy that is bond counting | `phase4_results.json` |
| 1.72 vs √3 = 1.732 | MOF-5 γ111/γ100: its "cube" sits on a boundary | `DFT_CHECK_PLAN.md` |
| r = +0.69, +0.72 | Δα class against graph size (why Part I is negative) | Results page |

---

## 4. Things not to say

| Do not say | Say instead |
|---|---|
| "We predicted the shape of MOFs" | "We predict the dominant face from the structure alone; it is right for 4 of 5 MOFs without additives" |
| "UFF energy" (as if it were a force field) | "bond-count surface energy" |
| "Our method improves adsorption" | "We compute geometric access indicators; adsorption itself is not computed" |
| "Accuracy 88 %" | "4 of 5 MOFs; 28 of 32 records" |
| "Δα measures heterogeneity" | "Δα as computed follows graph size; Part I is a negative result" (Q51) |
| "CHGNet validates the result" | "CHGNet is not validated for MOF surfaces; DFT is planned" |
| "The model predicts additive effects" | "With additives no model is reliable" |

---

## 5. Who answers what

Each part has an owner and a second person; both must be able to answer it (full table in
`panel_defence.md`, section 13).

| Part | Owner | Second |
|---|---|---|
| The story, unit cell vs crystal, symmetry and BFDH, maths | Radha Krishna | Keerthi |
| Spectrum mathematics, CHGNet pipeline, DFT plan | Kshitij | Radha Krishna |
| Morphology map, steering, gas access | Keerthi | Isha |
| Laboratory dataset, benchmark, missing data | Rohith | Isha |
| Graph construction, design decisions, mistakes | Isha | Rohith |

Practise in pairs: one reads only the question, the other answers without notes, then the first asks
"how do you know?" until the answer reaches a file or a number.
