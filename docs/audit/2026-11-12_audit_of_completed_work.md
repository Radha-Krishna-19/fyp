# Audit of the completed work: gap list and what was fixed

Project: MOF Graphs and Crystal Morphology (23CSE498, G070). Audit of 12 November 2026.
Scope, as agreed: only work already done. Nothing new was computed except re-runs of existing scripts.

Repository state after the fixes: main as of this file (12 November 2026). GitHub still has c6aaca7 until the update is
pushed (`C:\Dev\fyp\04_Repository\fyp_update_2026-11-12.bundle`, five commits).

## How the audit was done

1. **Reproduce.** All 136 Python files in `code/`, `data/`, `docs/` and `website/_build/` were run from the
   file-system root, not from their own folders. For each: exit code, runtime, and which committed result
   files changed, compared value by value (not byte by byte). All Python tests and all 13 website suites
   were also run from the root.
2. **Provenance.** The most-quoted numbers were recomputed from their result files and compared with the
   website, the complete report, the team paper, the panel slides, the READMEs and the project notes.
3. **Consistency, scientific review, coverage, history, rubric.** As in the prompt; results below.

## Summary

The results hold. Every headline number checked reproduces from its result file and from a fresh
re-run: r(Δα, graph size) = +0.690 and +0.716; 72 of 77 and 55 of 61 usable; convergence slopes
0.782 / 0.732 / 0.886 / 0.692; size-controlled ρ = +0.001 (p = 0.99); 134 records from 35 papers on 12 MOFs;
48 of 76 hMOF structures on one graph; the pore-size correlation −0.497 → +0.101; the withdrawn band
1.11–1.25; the paper's range 1.032–1.582; all morphology results; the map tests; the steps 1–8 quick run.

What was wrong was mostly around the results, not in them: two statements that described the method
wrongly, three Phase 1 analyses that could no longer be regenerated, scripts that only worked from their
own folder (one of which silently dropped data), missing inputs, and a report that lagged behind.
All of those are fixed. What remains open needs a person other than the author, or is future work.

## Status of every gap

Severity: **1** wrong as written; **2** not reproducible; **3** evidence weaker than stated, or undocumented;
**4** cosmetic.

### Fixed

| # | Sev. | Gap | Fix |
|---|---|---|---|
| 1 | 1 | The released dataset (`data/spectrum_descriptors`, CC BY 4.0) said its numbers came from the building-block quotient graph with covalent-radius bonds. They came from the atomic supercell graph with fixed distance cutoffs (2.80 / 2.45 / 1.70 / 1.45 / 1.90 Å by element pair, from the notebooks' code). | README and `metadata.json` state the real method and the withdrawal at the top; data unchanged. |
| 2 | 1 | Overview page: the control variable of the pore-size correlation was called "the number of blocks"; it is the analysed graph's vertex count (atoms). | Reworded. |
| 3 | 1 | Complete report: 24 pages (now 26), obsolete push instructions, "not yet in the repository", a DFT plan described as covering only MOF-5 and UiO-66. | Report updated to 12 November: Stage 14, section 13.9 (this audit), publishing section, Appendix B, page lists. |
| 4 | 2 | Three Phase 1 analyses (`code_14`, `code_15`, `code_16`) ran on the 34 hMOF and 20 CoRE MOF CIFs on disk on 15 September; with all 138 now in the repository they picked a different sample (CoRE slope mean 0.812 instead of the quoted 0.871). | The original pools are recorded (`capped_pool_*.txt`) and used by default; all three now regenerate their committed results exactly. |
| 5 | 2 | `code_16` looked for the four demonstration CIFs in the current folder and **silently left them out** when run from anywhere else. | Fixed; paths now recorded relative to the repository. |
| 6 | 2 | `code_18` read MOFX-DB metadata (pore sizes, void fractions, MOFids) from an untracked `.cache/`, so the class-chemistry numbers could not be regenerated. | A trimmed copy of the metadata for all 138 structures is committed (`mofxdb_metadata/`); `code_18` reproduces. |
| 7 | 2 | Seventeen spectrum-pipeline scripts (`code_00`–`code_11`, `code_18`, `code_19`, `_prove_ordering_equivalence.py`, `_test_window_frac.py`) only worked from their own folder. | All find their inputs from any folder; the ordering-equivalence proof still reports all cases identical. |
| 8 | 2 | `chgnet_wulff/diag.py` and `frag.py` imported names that never existed in `chgnet_wulff.py`. | Fixed and tested on MOF-5. |
| 9 | 2 | The four input CIFs of the steps 1–8 check were not in the repository (downloaded at run time). | Committed with source URL and SHA-256; quick mode reproduces `results_quick/` exactly; the notebook copy added. |
| 10 | 2 | `modulator_caps.py` needed four arguments and outside files. | Runs with no arguments; rerun agrees to within 0.003 eV per site (recorded; committed file kept). |
| 11 | 3 | Morphology map, Test 2: "the additive label makes it worse" had no test. | Page now gives the exact McNemar test (p = 0.041) and a paper-level bootstrap interval (+0.02 to +0.50): real but only just. |
| 12 | 3 | Morphology map, Test 1: the joint chance 2.7 × 10⁻⁴ did not state its selection or null. | Now stated (6 of 10 series that stay on the map; every order equally likely). |
| 13 | 3 | UiO-66's convergence slope rests on three supercells, not five. | Stated on the Results page. |
| 14 | 3 | Mistakes page missed the dataset description error (commit 6ec48fd and today). | Added. |
| 15 | 4 | "2,300+ assertions" (now 2,857 checks); optional dependencies (pandas, nbformat, torch) not listed. | Updated. |

### Documented, not changed

| # | Sev. | Gap | Why not changed |
|---|---|---|---|
| 16 | 3 | `r2_linearity_mean`, the fit-quality diagnostic of `code_12`, is not deterministic: it changes between runs by up to 0.3 for single structures while the widths agree to 1e-4. | No quoted number or conclusion uses it. Changing the estimator would touch every Phase 1 result; recorded in the project notes with a warning not to quote it. |
| 17 | 4 | Some result files were committed with Windows line endings, so a rerun shows every line changed although the values are identical. | Cosmetic; rewriting line endings would churn many files. |
| 18 | — | `code_07a` needs the upstream `mofid` package; the steps 1–8 scripts and `chgnet_wulff.py` need arguments. | By design; usage is in their READMEs. |

### Open: needs a person other than the author (check sheets in `docs/defence/`)

| # | Sev. | Gap | Proposed action | Owner |
|---|---|---|---|---|
| 19 | 3 | All 134 laboratory records were extracted by one person; 11 remain unverified. The benchmark rests on them. | A second member re-extracts 20 random records blind; report agreement. | Isha (check), Rohith |
| 20 | 3 | The 16 propositions were proved and checked numerically by one author; no one else has checked the proofs. | Two members check eight proofs each; record who checked what. | Keerthi, Isha |
| 21 | 3 | Only the Panel Review 1 rubric is in the project; the Phase II and final rubrics are not. | Ask Dr. Ramraj. | Radha |
| 22 | 3 | The only slide deck (16 September) covers Part 1 only. | Done 12 November: a 15-slide Phase II deck of the completed work from the same numbers (Claude Slides; downloadable as PowerPoint or PDF). The team should rehearse it with `docs/defence/panel_defence.md`. | Team |

### Future work, not started (out of the agreed scope)

DFT check of the six slabs; fixing K1, K2, K4 and the relaxed rerun of the steps 1–8 pipeline; more scored
MOFs and the structure-only run on all 138 CIFs; a model of growth conditions; the link to adsorption; a
held-out choice of the hybrid weight; the morphology paper. These limit how far the existing results
generalise (below) but are not defects in them.

## Coverage: which analyses use which structures

| Analysis | Structures | Why |
|---|---|---|
| Decomposition, periodic graph, spectrum, band, size strata, class explanation | 77 hMOF + 61 CoRE MOF = 138 (capped analyses: 34 + 20) | Part 1 asked a screening question, so it needs a population |
| Convergence of Δα with size | 4 demonstration nets (tbo, pcu, sod, fcu) | The same net at several sizes |
| Space group, faces, BFDH, morph families, deformation, graph faces, UFF energies | 4 demonstration MOFs; BFDH and UFF also on 8 CoRE MOFs of six crystal systems | Shapes need lab data to compare with; the 8 test the code's generality, not its accuracy |
| CHGNet slab energies | MOF-5, HKUST-1, UiO-66, hMOF-0 (October); ZIF-8, HKUST-1, UiO-66, Mg-MOF-74 (steps 1–8, partly relaxed) | GPU hours per MOF |
| Benchmark against experiment | 4 MOFs, additive-free records | Lab shapes exist for about 12 MOFs, mostly 5 |
| Morphology map, possible morphologies | 4 cubic MOFs | The map is exact for cubic crystals |
| Conditions (Tests 1 and 2) | 10 series; 82 records from 25 papers | All usable records |
| Spectrum and shape | MOF-5 (and ZIF-8) particles; 55 CoRE MOFs for Test 3 | One net for particles; every usable CoRE MOF for Test 3 |

**Cannot be generalised from the existing work:** which energy model is best (only MOF-5 separates
them); the dimension profile's separation of compact shapes (one net, 3–5 seeds); anything about
non-cubic crystals from the map.

## History and the Mistakes page

The 58 commits since 6 September and the Mistakes page now agree. Every withdrawal in the history (the
four-structure band, both atomic-graph bands, the pore-size correlation, the sub-band classes) is on the
site with its reason.

## Against the Panel Review 1 rubric and the panel's questions

| Item | State | Evidence |
|---|---|---|
| Methodology and solution design | Done | Methodology, From a CIF to a shape, Morphology pages |
| Mathematical model | Done; proofs not yet checked by a second person (20) | Maths page; numeric checks in `test_maths.js` |
| Implementation | Done; Python and browser implementations agree | 13 website suites, Python tests, all from any folder |
| Results | Part 1: a negative result, documented. Part 2: shapes for 4 MOFs, benchmark, map tests | Results, Experiment, Morphology map pages |
| Technical knowledge and design decisions | Documented | How we got here, "Defending each key decision" |
| Panel question 1: several morphologies from one unit cell, mathematically | Done | Maths, Morphology, Changing the cell, Morphology map |
| Panel question 2: computationally | Done for 4 MOFs; matches the lab for ZIF-8, partly for HKUST-1 and MOF-5 | Experiment, Morphology map |
| Original aim (adsorption selectivity and capacity) | Not reached by the completed work | Future work |
