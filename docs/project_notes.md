# Project notes: verified findings, decisions and conventions

This file is the technical record of the project: what was verified, with which script, which
numbers may be quoted, which defects were found and fixed, and the conventions the code and the
website follow. The website ([`website/`](../website/)) and the folder READMEs summarise it; this
file keeps the details.

23CSE498 Final Year Project, Phase II. Amrita Vishwa Vidyapeetham, Coimbatore.
Guide: Dr. T. Ramraj. Owner: P. M. Radha Krishna (and four teammates).

**The question.** Can a descriptor computed from a MOF's connectivity alone, in
seconds and without molecular simulation, carry enough structural information
to decide which frameworks merit hours of simulation? The intended pipeline is
CIF → bond perception → metal-oxo decomposition → labelled quotient graph →
supercell → multifractal spectrum → Δα.

---

## Proof: coarse-grain-first and atomic-first give the IDENTICAL graph (2026-09-16)

Verified empirically, not just argued: `code/spectrum_pipeline/_prove_ordering_equivalence.py`
builds the same n×n×n supercell two ways for five real cases, using this
project's own bond-perception and decomposition code in both routes (so any
difference found is about order, not about two implementations disagreeing).

Route A: decompose the unit cell into blocks, then replicate the small block
graph using the stored lattice translations (`code_12`'s `quotient_graph_from_cif`
+ `replicate`). Route B: replicate every atom n×n×n first (scaling the cell),
run bond perception and metal-oxo decomposition on the whole enlarged
periodic cell, then coarse-grain that.

| Structure | n | Nodes/edges | Degree sequence | `nx.is_isomorphic` | Route B / Route A time |
|---|---|---|---|---|---|
| HKUST-1 | 2 | 112/192 | match | **True** | 134.7× |
| MOF-5 | 2 | 256/384 | match | **True** | 57.6× |
| ZIF-8 | 2 | 288/384 | match | **True** | 56.7× |
| UiO-66 | 2 | 56/96 | match | **True** | 47.7× |
| UiO-66 | 3 | 189/324 | match | **True** | 675.0× |

All five: identical graph, confirmed by full isomorphism check, not just
matching summary statistics. This holds because the metal-oxo decomposition
is a purely local, translation-invariant rule (cut bonds touching a metal,
take connected components) applied to a periodic bond graph found the same
way (27-image search) on whichever cell it is handed — such a rule commutes
with taking the periodic extension, so decomposing then replicating and
replicating then decomposing are the same operation. The two routes differ
only in cost, by 48×–675× in this test, growing with n (Route B pays for
atoms it immediately discards; Route A never builds them). **Do not revisit
this as an open question** — it is closed, with a reproducible script.

## Which graph each published number was computed on (settled 2026-09-15)

The site and the dataset README describe the spectrum as computed on the
coarse-grained building-block graph. **The two published bands were not
computed that way.** Both notebooks (`notebooks/spectrum/mof_band_analysis.ipynb`,
`notebooks/spectrum/real_mof_band.ipynb`) call `inmfa(s["G"])`, where `G` is the
**atomic** supercell bond graph. Coarse-graining ran only to supply the
`n_nodes` and `n_linkers` counts. The saved outputs confirm this:

| Evidence in `results.json` / `real_results.json` | hMOF (77) | CoRE MOF (61) |
|---|---|---|
| `N`, the number of vertices analysed (= atoms) | 3024–6592 | 1160–7000 |
| building blocks (`n_nodes + n_linkers`) | 97–432 | 1–1297 |
| `diameter` of the analysed graph | 35–64 | 34–104 |
| `n_influential` = ⌈0.10·N⌉ atoms | 77/77 | 61/61 |
| `n_influential` larger than the block count | 77/77 | 47/61 |
| largest radius / diameter | 0.33–0.35 | 0.33–0.35 |

Four different estimators exist in the project and must not be conflated:

| Run | Graph | Influential set | Radii fitted |
|---|---|---|---|
| hMOF-77 and CoRE-61 bands (CSV files, Results page) | atomic supercell, ASE distance cutoffs, 48 Å rule capped at 7000 atoms | top 10 % of atoms by degree, then closeness | 1 … round(0.34·D) |
| Independent Narrow/Medium/Wide run (`~/Downloads/mof_cg_spectrum.ipynb`) | coarse graph cut from the atomic supercell | top 20 % by degree, then closeness | 1 … min(round(0.5·D), D−1) |
| `code_10`, `code_12`, browser engine (`mof_multifractal.js`) | coarse-grained labelled quotient graph, replicated n×n×n | top 30 % by degree | 1 … D |
| Paper-faithful box-growing (`code_11`, `analysePaper` in JS) | coarse-grained quotient supercell | top 10 % | deterministic box-growing |

Consequences:

- The Results page, `data/spectrum_descriptors/README.md` and the site's methods text documented
  a coarse-grained method while the published numbers came from atomic graphs.
  The CSV columns `graph_diameter` and `n_influential` describe the atomic graph,
  not the block graph.
- The withdrawal notice added in commit `11bf886` said both bands were computed
  "at diameter 8–12". That was wrong: diameter 8–12 describes the independent
  coarse-grained run above, not the CSV bands, which sit at atomic diameters 34–104.
- An atomic MOF graph is expected to contain two length scales: the molecular
  scale inside a linker or cluster, and the framework scale above one linker
  length. Fitting one power law across that crossover is not a valid scaling
  measurement. Whether the crossover is visible, and where, is measured in
  `code/spectrum_pipeline/code_13_scaling_regimes.py`; quote only the numbers that script
  reports (see the Methods section on the Spectrum page).

## Finite-size behaviour of Δα (re-run and verified 2026-09-15)

The sweep was re-run from scratch (`code/spectrum_pipeline/_run_size_scaling.py`, output in
`data/spectrum_descriptors/size_scaling/convergence_sweep.json`) on all four demonstration
nets, on the coarse-grained quotient graph. Fitted slopes of Δα against
ln(diameter), full q range [−10, 10]:

| Structure | Net | Slope | Intercept | R² | Diameter range | Δα range |
|---|---|---|---|---|---|---|
| HKUST-1 | tbo | 0.782 | −0.274 | 0.999 | 8–32 | 1.344–2.430 |
| MOF-5 | pcu | 0.732 | −0.156 | 1.000 | 12–48 | 1.664–2.681 |
| ZIF-8 | sod | 0.886 | −0.761 | 1.000 | 12–48 | 1.442–2.665 |
| UiO-66 | fcu | 0.692 | +0.794 | 0.998 | 8–16 | 2.229–2.707 |

All four fit a straight line in ln(diameter) almost exactly (R² ≥ 0.998); the
slope is not the same constant on every net (0.69–0.89), so "Δα ≈
0.78·ln(D) − 0.28" describes HKUST-1 only, not a universal law. Drift between
the two largest supercells tested, by q cap (all exceed the 5% tolerance at
every cap, on every net):

| |q| cap | HKUST-1 | MOF-5 | ZIF-8 | UiO-66 |
|---|---|---|---|---|---|
| 10 | 0.101 | 0.083 | 0.094 | 0.057 |
| 8 | 0.102 | 0.083 | 0.095 | 0.057 |
| 5 | 0.107 | 0.087 | 0.099 | 0.058 |
| 4 | 0.112 | 0.091 | 0.102 | 0.058 |
| 3 | 0.121 | 0.099 | 0.109 | 0.061 |
| 2 | 0.140 | 0.115 | 0.129 | 0.064 |

The figure is `data/spectrum_descriptors/size_scaling/convergence_figure.png`, also on the
Results page and in `docs/textbook/figures/fig13_convergence.png`. **Quote only
these numbers**, not the earlier "≈0.78·ln(D) − 0.28, within 0.01" claim from
commit `11bf886`, which was neither universal across nets nor checked against
a residual.

**Mechanism.** Δα is taken over q ∈ [−10, 10]. At |q| = 10 the partition
function Σ p_i^q is dominated by a single box. The smallest possible box is one
vertex, p = 1/N, so α at the negative-q end inherits a ln(N) term and moves with
system size. At extreme q this is the extreme-value statistics of one box, not a
scaling measurement.

**Consequence.** Neither published band is a structural finding. Both are
withdrawn on the Results page and in `data/spectrum_descriptors/README.md`, and the withdrawn
numbers stay visible with their reasons, as for the two earlier withdrawals.
Do not recompute either band "at a converged cap": none was found.

---

## Does the Δα(D) slope vary between frameworks? (2026-09-15, capped, a proposal)

`code/spectrum_pipeline/code_15_dataset_sweeps.py`: 20 structures per dataset (size-spread
sample, not random or full), supercell capped at 5000 nodes, 3-point sweep
(n=2,3,4), one seed. hMOF (n=19 usable): slope mean 0.594, sd 0.134, range
0.407–0.818. CoRE MOF (n=15 usable): slope mean 0.871, sd 0.333, range
0.224–1.474. The slope varies ~2.5× more across CoRE MOF than across hMOF —
consistent with the slope carrying real structural signal (hMOF is dominated
by one repeated topology; see the sub-bands entry below), but also
consistent with sampling noise from this small, single-seed, single-pass
sweep. **Not established either way** — figure and numbers in
`data/spectrum_descriptors/size_scaling/slope_sweep_figure.png`, raw data in
`slope_sweep_hmof.json` / `slope_sweep_core.json`. Treat as a proposal for
what a size-independent descriptor might look like, not as a finding.

## Sub-bands (Narrow/Medium/Wide) are size strata, not chemistry

`code/spectrum_pipeline/code_14_size_strata.py`, run on the 34 hMOF CIFs available locally
plus the full 76-row `teammate_cg_run.csv`. Of 14 distinct coarse-grained
graph signatures across the 76 structures, **13 are entirely one class** —
class is a deterministic function of graph size wherever the graph actually
differs between structures. The 14th signature (256 nodes, 384 edges,
diameter 12 — the 4×4×4 pcu tiling already flagged above) accounts for
**48 of the 76 structures (63%)** and spans **all three classes** (36
Medium, 6 Wide, 6 Narrow; Δα 1.171–1.235 within that one identical graph).
Independently rebuilding the correct coarse-grained graph for a 34-structure
subset and computing real network statistics (degree mean/CV, assortativity,
clustering, component count, degree entropy) confirms 28 of 34 give
identical values on every statistic, because they are the same graph.
Figure: `data/spectrum_descriptors/size_scaling/size_strata_figure.png`.

## A topologically diverse comparison set (capped, 2026-09-15)

`code/spectrum_pipeline/code_16_topological_diversity.py`: classifies structures by
coordination signature (node degree, linker degree) — a heuristic that only
resolves the four simple, single-node-type nets already discussed on this
site (pcu 6+2, tbo 4+3, sod 4+2, fcu 12+2), not general net assignment,
because that needs Systre (Java, not installed here). Built a 6-structure
set: the four demonstration structures (tbo, pcu, sod, fcu — ground truth)
plus 2 more pcu-signature hMOF structures (the only net this heuristic could
match in the locally available 34-hMOF/20-CoRE-MOF pool, capped at 2
duplicates so the set does not silently pad itself). **rht was not found by
any method available in this environment — a genuine gap, reported as one.**
Of the 20 CoRE MOF structures classified, 34 pcu + 1 fcu matched a simple
signature and 8 had a multi-connectivity signature this heuristic cannot
resolve at all (real chemical diversity the heuristic cannot see, not
necessarily rht). This does not contradict the earlier finding that the
hMOF-77 sample is topologically degenerate; it extends it — the additional
34 hMOF CIFs fetched for other tasks are *also* all pcu-
signature or unclassifiable, so the degeneracy is not an artefact of which
48 structures happened to land in the original CSV.

## The full, correct band on both complete datasets (2026-09-15, parameters matched 2026-09-16)

All 77 hMOF and all 61 CoRE MOF CIFs were fetched (previously only 34 and 20
were available locally) and run through `code/spectrum_pipeline/code_17_full_correct_band.py`,
which uses the correct graph: coarse-grained quotient graph of the unit cell,
replicated to 48 Å per axis, no atoms built at any point. 72/77 hMOF and
55/61 CoRE MOF produced a usable spectrum (the rest fell below the
diameter-8 scaling gate at this sizing rule). Results:
`data/spectrum_descriptors/size_scaling/full_band_hmof_cg.json`, `full_band_core_cg.json`.

**Spectrum-fitting parameters:** the top 20% of vertices by degree count as
"influential", and radii are fitted only out to half the diameter, via
`code_12.spectrum(..., window_frac=0.50)`. The narrower window keeps every
fitted radius inside the range where box-covering still has several boxes
to average against, rather than running the fit out to where the graph is
covered by only one or two giant boxes. Checked directly on all four
demonstration nets (`_test_window_frac.py`): this keeps Δα's growth with
supercell size gentler at every step tested (slope vs ln(diameter) 0.63–0.79,
against 0.73–0.91 at the full diameter), though the quantity still grows
with size under either window rather than settling to a constant. The
graph-ordering question (does coarse-grain-first vs atomic-first change the
graph) is separate and was already settled — see the empirical proof entry
above; it is unaffected by this parameter choice.

**Class still tracks graph size, even on the correct graph, on the full
datasets.** r(Δα, coarse-grained node count) =
+0.69 on hMOF and +0.72 on CoRE MOF, independently. `code_18_subband_explain.py`
sorts each dataset into Narrow/Medium/Wide terciles and reports chemistry,
graph features, degree stats, edges, clustering, assortativity, heterogeneity
and component count per class (`subband_explain_hmof.json`,
`subband_explain_core.json`):

- hMOF Narrow and Medium (63 of 72) are the same metal (Zn), same net (pcu),
  same block count (4), same node count (~255), same assortativity to 3
  decimals — indistinguishable by anything except Δα itself. The 9-structure
  Wide class differs on graph size, pore geometry (LCD 3.8 vs 9.5 Å) and
  component count (1.67 vs 1.00, see below) — all confounded with size.
- CoRE MOF's three classes differ on chemistry (void fraction, LCD), graph
  size, assortativity and heterogeneity — a real, non-degenerate spread this
  time — but every one of those differences moves in lock-step with graph
  size, so none is shown here to be an independent driver.
- **New finding: several classes on both datasets average >1 connected
  component** on the replicated quotient graph, which should always be one
  piece if the decomposition found only periodic-framework blocks. This
  means the metal-oxo decomposition is retaining disconnected guest/solvent
  fragments as small "linker" blocks on a meaningful fraction of real CoRE
  MOF structures (and a few hMOF ones). Not previously documented; worth its
  own follow-up, not further investigated here.
- MOFX-DB supplied no MOFid for any CoRE MOF record in this fetch, so metal
  and RCSR net are unknown for that dataset here — reported as unavailable,
  not guessed.

This supersedes the earlier 34-structure/20-structure capped analyses (D, E,
F in the task list) as the authoritative version; those are kept on the
Results page as a second, smaller, independently-consistent check, not
replaced.

## Morphology direction: the panel's second question (2026-10-09)

After Panel Review 1 the panel asked: given an established MOF's unit cell, generate at
least a few crystal morphologies, mathematically and computationally. Phase 1 is done.

- Python: `code/morphology/` (`tests.py`: 14 checks, all pass; `run_phase1.py` writes
  `results/phase1_results.json` and the figures). Needs numpy, scipy, matplotlib, ase, spglib.
- Browser: `website/mof_morphology.js` (engine, no DOM) and `morphology_page.js`, page
  `morphology.html` from `_build/fragments/morphology.before.html`.
  `tests/test_morphology.js` checks the JS engine against the Python JSON number by number.
- Symmetry found by spglib: MOF-5 Fm-3m a=25.866; HKUST-1 Fm-3m a=26.297 (file is the
  primitive cell); UiO-66 F-43m a=20.518 (ordered mu3-OH; literature Fm-3m); ZIF-8 I-43m
  a=16.991 only WITHOUT hydrogens (with H the file is P1).
- Results: BFDH gives a truncated octahedron for all three F-centred MOFs and a rhombic
  dodecahedron for ZIF-8. Varying R111/R100 gives cube (>= sqrt3), cuboctahedron (2/sqrt3),
  octahedron (<= 1/sqrt3). Attachment numbers: pcu 1/2/3 on (100)/(110)/(111) gives a
  cube; fcu 4/5/3 gives an octahedron (matches Chen et al., Matter 2020).
- kappa^2 is zero for every cubic-symmetric shape; use sphericity and Q3/Q4/Q6.
- The tetrahedral shape for UiO-66 depends on the F-43m ordering in our file and is
  forbidden in Fm-3m. Report it as "allowed by the ordered structure", never as a prediction.
- Open: sod (ZIF-8) is not resolved by single-node counting; tbo needs a two-node count.

## Defects already found and fixed (do not reintroduce)

1. **τ(q) fitted with a free intercept** instead of through the origin. This
   flattened every spectrum's apex (0/77 valid before, 77/77 after). τ must be
   `Σxy/Σx²`.
2. **Spectrum computed on the induced subgraph of influential nodes.** Metal
   clusters bond to each other only through linkers, so that subgraph has no
   edges. Cover the full graph and read the measure only at influential nodes.
3. **Averaging order.** Build Z per trial, take logarithms, then average ln Z.
   Averaging p_i(r) first biases the spectrum narrow by more than a factor of 10.
4. **Periodicity discarded.** Use the labelled quotient graph, whose edges carry
   the lattice translation t. Without it UiO-66's 12-connected Zr₆ cluster is
   reported with the wrong connectivity or the cell degenerates to a star.
5. **Classes narrower than the error bar.** An independent run cut Δα at its
   25th and 75th percentiles (Narrow ≤ 1.1901 < Medium ≤ 1.2218 < Wide). The
   Medium class is 0.032 wide against per-structure error bars of 0.013–0.098.
   Its isomorphism check (on unit-cell atom graphs) listed hMOF-94 and hMOF-96
   as the same graph; they landed in different classes. Never classify when the
   class width is below the error bar; `assign_classes()` refuses.
6. **`nx.diameter()` and all-pairs shortest paths** are O(N²) in pure Python and
   stall above about 3000 vertices. Use `fast_diameter()` (double sweep) and the
   BFS box covering in `code_12`, or a compiled distance matrix where N is small
   enough to store one.

7. **Self-referencing CSS tokens** (fixed 2026-10-09). `assets/base.css` had aliases such as
   `--node:var(--node)` and `--text:var(--text)`. A custom property defined in terms of itself
   is a cycle, which CSS treats as invalid, so those tokens resolved to nothing: red drawn
   black and the active `.mode-btn` invisible on every page. Never alias a token to itself.

## Known traps

- **MOFX-DB provenance.** `database=` is advisory on that endpoint and loses to
  the `gases[]` filter. It has returned hMOF records for a CoRE MOF 2019 request
  (one such request received 150/150 hMOF). Filter each record on its own
  `database` field, or work from CIFs on disk.
- **The hMOF sample is topologically degenerate.** In one independent run, 48 of
  76 structures share 256 coarse nodes, 384 edges and diameter 12: a 4×4×4 pcu
  net of 64 six-connected Zn₄O nodes and 192 two-connected linkers. They differ
  only in linker chemistry, which coarse-graining removes by design. A band over
  these structures is narrow for a trivial reason. Sub-band work needs deliberate
  spread across nets (pcu, tbo, sod, fcu, rht), not random sampling.
- **Coarse-grain before replicating.** Building an atomic supercell and then
  coarse-graining caps the graph at MAX_ATOMS and hence at diameter about 12.
  The quotient graph replicates combinatorially with no atoms.
- **`metal_oxo_deep_dive` is not a path inside the repository.** It is the local
  folder containing `.git`; the repository root holds `website/`, `code/spectrum_pipeline/`
  and so on directly.

## Conventions

- **The website is built, not hand-edited.** Edit
  `website/_build/fragments/*.html` or `_build/content_source.html`, then run
  `python website/_build/build_site.py`. Never edit `website/index.html` and
  the other built pages directly.
- **Tests:** `cd website/tests && node test_*.js`. They load the real pages in
  jsdom and assert on computed output, because this site's typical failure is a
  silently blank panel rather than an error.
- **CI** (`.github/workflows/pages.yml`) runs the suites on push. The deploy job
  is manual-only (`workflow_dispatch`) because GitHub Pages is not enabled.
- **Two independent implementations** (Python in `code/spectrum_pipeline/`, JavaScript in
  `website/`) were written from the same specification. Where they disagree,
  one of them is wrong. Keep both.

## House style

State each claim with its evidence and its limits. Withdrawn claims are
documented on the site, not deleted. Do not describe a motivation as a result.
If a number is not converged, say so. Write in plain, formal English: avoid
rhetorical inversions, sentence fragments used for effect, aphorisms and heavy
use of dashes.

## Outstanding work

The open items, with owners, are listed on the website Team page (Completion section) and in the
root README under "Future work".

## Cell deformation (Phase 1b) and surface energy (Phase 4)
- `code/morphology/mofmorph/deform.py` changes the lattice (a, b, c, angles) with atoms at fixed fractional coordinates; `faces.enumerate_faces(..., absence_ops=)` keeps the ORIGINAL space-group operations for the absence test (Prop. 14) while families come from the surviving isometric subgroup (Prop. 15). Box law and exact box criterion: Prop. 16. BFDH uses the 40 largest-d_eff families (10 can leave a strongly anisotropic shape unbounded).
- `website/mof_deform.js` is the browser version (orthogonal cells only) and must agree with `results/deform_results.json`; `tests/test_morph_pages.js` compares all 52 stretched cases. Page `deform.html` is built from `_build/fragments/deform.before.html`, written by `_build/build_deform_fragment.py`.
- `mofmorph/forcefield.py` (UFF Lennard-Jones plus a flat bond energy, unrelaxed, no electrostatics) gives the Phase 4 cleavage energies; page `surface_energy.html` is written by `_build/build_phase4_fragment.py`. Regenerate both fragments, then `build_site.py`, after rerunning `run_deform.py` / `run_phase4.py`.
- `assets/academic.css` (loaded last) is the plain academic look; the site defaults to light.

## Experiment, CHGNet and the review of 2026-10-14
- Page `experiment.html` is written by `_build/build_experiment_fragment.py` from `code/morphology/results/{chgnet_cleavage_results,slab_pieces,slab_options,bond_sensitivity,core_results}.json`, the CHGNet zips in `code/morphology/data/chgnet_runs/`, and `data/experimental_morphology/{dataset/experimental_morphology.csv,compare/comparison.csv}`. Order to regenerate: `slab_check.py`, `run_chgnet_cleavage.py`, `slab_options_check.py` (needs pymatgen), `run_bond_sensitivity.py`, `run_core.py`, `figs_experiment.py`, `compare/compare_with_project.py`, the fragment builder, `build_site.py`. `tests/test_morph_pages.js` checks the page against the JSON; `code/morphology/tests_review.py` checks the new Python.
- `data/experimental_morphology/` (Rohith) is the experimental dataset: build with `dataset/build_dataset.py`. Sources with `access: unverified` go to `experimental_morphology_unverified.csv`, never into the benchmark. Paper PDFs are not in the repository.
- CHGNet notebook (Keerthi): each slab gives only gamma_top + gamma_bottom, so individual gammas were underdetermined for every facet. `chgnet_post.py` uses the cleavage energy min p/2, an UPPER bound on the lowest termination energy; for F-43m UiO-66 the + and - {111}/{311} halves cannot be separated. Do not present it as a fitted surface energy.
- Most CHGNet slabs cut through linkers (loose H, O, CH, C2H2; CO2 released on relaxation). Dropping them changes no shape. Slabs are 15-30 A, not thickness-converged. Symmetric-as-cut slabs exist but are high-energy terminations (1.4-9x the bound), so symmetric slabs do not fix the problem.
- The Phase 4 MOF-5 cube depends on the flat 70 kcal/mol bond cost: at 0.5x / 0.25x metal-ligand cost it becomes a truncated cube / truncated octahedron. HKUST-1 and UiO-66 shapes do not change. Quote the MOF-5 cube only with this caveat. The decisive check is `code/morphology/DFT_CHECK_PLAN.md`.
- Fixed: `hybrid.uff_gammas` dropped all H atoms when `structure.load` found the symmetry only without H (ZIF-8 {111} came out 0.312 instead of 0.619 J/m2). `hybrid.atoms_for_energy` now rebuilds the full cell. Never compute energies on `Crystal.numbers` directly when `used_hydrogen` is False.
- The BFDH x Wulff hybrid has one free weight w; with four MOFs, a best w is fitted to the test set. Show it at a fixed w, never rank it.
- `academic.css` now has `.with-toc > *{min-width:0}` and `html{overflow-x:clip}`: wide tables and hidden glossary pop-ups had made every page scroll sideways.

## Bridge to the spectrum work, Hybrid page and Mistakes page (2026-10-16)
- New pages: `hybrid.html` (BFDH x Wulff blend, from `results/hybrid_results.json` via `_build/build_hybrid_fragment.py`), `bridge.html` (purpose of changing shape; first half of the project; spectrum-vs-shape test, via `_build/build_bridge_fragment.py`), `lessons.html` (17 mistakes, plain + technical, via `_build/build_lessons_fragment.py`). `tests/test_bridge_pages.js` checks every table number against the JSON files.
- `code/spectrum_pipeline/code_19_spectrum_vs_shape.py` (outputs `data/spectrum_descriptors/size_scaling/spectrum_vs_shape_{MOF5,ZIF8}.json`, figure by `make_spectrum_vs_shape_figure.py`): the quotient graph tiled WITHOUT wrap-around in a box. MOF-5 at 64 cells (2048 blocks): cube 1.722, slab 8x4x2 1.626, plate 8x8x1 1.591, rod 16x2x2 1.410 (seed sd <= 0.009); plates/rods lie 0.2-0.7 BELOW the cube size trend at their own diameter, so shape matters beyond diameter. One structure, boxes only, one parameter set. ZIF-8 is NOT used: its block graph is disconnected (34-238 components), cause not investigated. HKUST-1 and UiO-66 files are primitive cells and were not cut.
- Regenerate order: `code_19` (both structures), `make_spectrum_vs_shape_figure.py`, the three `build_*_fragment.py` scripts, `build_site.py`.
- Team page: dataset is 134 records / 35 papers / 12 MOFs (it said 104/28/14).

## Spectrum <-> shape relation, run by P. M. Radha Krishna (2026-10-16)
- Folder `code/spectrum_shape_relation/` (README there): `particle_graph_tools.py`, `run_01..03_*.py`, `make_figures_*.py`, `check_*.py` (15 checks), `make_notebook_*.py` -> `Spectrum_Shape_Relation.ipynb`, `make_colab_bundle_*.py`; the CoRE MOF CIFs are read from `data/structures/core_mof_2019/`. Results in `results/` came from P. M. Radha Krishna's Colab run (16 Oct 2026, RECOMPUTE=True, 15/15 checks); `results/RUN_REPORT_spectrum_shape_relation.md` is its printed output.
- Findings: (1) MOF-5 at 64 cells: cube 1.722 > slab 1.626 > plate 1.591 > rod 1.410, below the cube trend at own diameter; identical to code_19. (2) Compact predicted shapes (BFDH, blend, UFF Wulff, CHGNet, cube, octahedron, rhombic dodecahedron) at ~2000/~4000 blocks are within -0.044..+0.050 of the cube trend in ln N, the size of the trend's own scatter (0.043): NOT separated. Equal-D comparison is misleading (pcu graph distance ~ L1, octahedron has small D). (3) 55 CoRE MOFs: raw rho(width, BFDH aspect) +0.50, with ln(node count) held fixed +0.001 (p 0.99): periodic delta-alpha carries no shape information beyond size.
- Pages: `bridge.html` ("Why Shape": purpose, first half, what the halves share) and `relation.html` ("Spectrum <-> Shape", from `_build/build_relation_fragment.py`, reads only `spectrum_shape_relation/results/*.json`). Every result block has a `<p class="provenance">` "Produced by" line naming the notebook. `tests/test_bridge_pages.js` checks the page against the JSON.
- `journey.html` ("How We Got Here", from `_build/build_journey_fragment.py`): the project in 10 stages (papers read, work done, code/notebooks, outputs, mistakes linked to `lessons.html` anchors, corrections, "why this and not something else"), open work and built-but-unused items. `tests/test_bridge_pages.js` checks its structure and that every mistake link resolves. References [9] note updated: the 61 CoRE CIFs were obtained.
- `learn_energy.html` ("Learn 2", fragment `_build/fragments/learn_energy.before.html`, figures by `_build/make_learn_energy_figures.py`): just-enough teaching of surface/cleavage energy, terminations and slabs, relaxation, force field vs CHGNet vs DFT, equilibrium vs growth shapes, the blend and overfitting, Spearman/permutation/bootstrap/partial correlation (example from the 2026-10-16 relation run), torus vs finite particle and taxicab distance, hydrogen and symmetry, software tools. 12 new glossary terms in a new 'Energies' group (added to the order list in `assets/glossary.js`). `tests/test_bridge_pages.js` checks every new term is taught on the page.
