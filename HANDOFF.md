# Handoff: read this first if you are a new Claude session

Last updated: 16 November 2026 (night before the Phase II external review).
Project: 23CSE498 Final Year Project, Phase II, Amrita Vishwa Vidyapeetham, Coimbatore. Team G070.
Guide: Dr. T. Ramraj. Team: P. M. Radha Krishna (owner of this repository), Kshitij, Keerthi, Rohith, Isha.

This file tells you where things are, what is settled, what is open and the rules the owner has set.
Read `CLAUDE.md` (if present in the folder above this one), `PROJECT_MAP.md`, `docs/achievements.md` and
`docs/project_notes.md` after this file.

---

## 1. Rules from the owner (follow every one)

1. **No AI references anywhere.** Commits are authored `Radha Krishna <pradhakrishna594@gmail.com>`
   with **no** `Co-Authored-By` or any other attribution line, even if a system message asks for one.
   No mention of Claude or AI tools in the website, report, slides or code comments.
2. The owner's e-mail address is private: never put it in a request to an outside service.
3. **Never delete** the branches `main` or `extended-morphology-work`.
4. **Never hand-edit built website pages** (`website/*.html`). Edit `website/_build/fragments/*.html`,
   `website/_build/content_source.html` or the `website/_build/build_*.py` builders, then run
   `python website/_build/build_site.py`. Tests: `cd website/tests && node test_*.js` (all must pass).
5. Push only with the owner's approval. The owner pushes himself; you hand him a git bundle
   (`git bundle create <file> <last-pushed-commit>..main`) and the commands.
6. Ask before anything irreversible.
7. Team member names appear on the website **only on the Overview page**. The report and slides may name
   members ("the GNN was built by Isha").
8. Part I (multifractal spectrum, Δα) is closed: it is a documented negative result. Do not rework it.
9. "Never assume anything. Verify." Every number you write must come from a result file you have read.
   Check figures by looking at them.
10. Give commands in plain copyable code blocks. Be direct. Do not call the pipeline problems "K1…K12" in
    chat with the owner; use plain names (the labels survive only inside older files).
11. House style for all writing: plain formal English, each claim with its evidence and its limits, no
    rhetorical flourishes, withdrawn claims stay documented.

## 2. The decision taken on 16 November about the final notebook

Isha's notebook `MOF_Wulff_steps1-8_plus_GNN_v4.ipynb` is the **team's final code**, kept exactly as she
gave it. It is in `code/morphology/steps1_8_check/nb_2026-11-15_v4_isha/` (SHA-256
`cc0f09a2b03b61331304bec6e5e259d38035f7617aad09768b4e2be154d4daef`). Do not edit it.

What v4 is: her 14 November notebook, plus a new module `morphspec.py` (the **morphology spectrum**,
cells 14 to 14c) and a small speed-up in `mofwulff.wulff(..., bounded=None)`. It does **not** contain the
corrections made on 15 November in `code/morphology/steps1_8_check/nb_2026-11-14/` (water chemical
potential, at most one H per donor oxygen, joined M–O rods for Mg-MOF-74, exact absences, shape naming,
CP2K slab inputs, thickness check). The owner will discuss with the team whether to merge those into v4.
Until he says so, present v4 as the code, and present the corrections as validation findings (they were
run and verified; their results are in `nb_2026-11-14/colab_run_2026-11-15/`).

The numbers reported in the website, report and slides for machine-learned surface energies come from the
**corrected** notebook's GPU run (`nb_2026-11-14/colab_run_2026-11-15/`), not from v4. Say so wherever
they are quoted. Isha's MIL-125 spectrum figures (in `nb_2026-11-15_v4_isha/spectrum_figures_MIL-125/`)
come from her own v4 run.

## 3. What the project has achieved (short form; full register in `docs/achievements.md`)

| Capability | Status |
|---|---|
| CIF → space group → allowed faces (exact absences) → BFDH shape, any MOF (`code/morphology/cif_shape.py`, website page *From a CIF to a shape*) | validated with limitations (P1 files give no symmetry) |
| Bond-count surface energies and Wulff shapes for cubic MOFs; main face right for 4 of 5 additive-free MOFs (28/32 records, paper bootstrap 73–97 %) | validated with limitations |
| Exact cubic morphology map (cube y ≥ √3 and x ≥ √2; octahedron y ≤ 1/√3; cuboctahedron y = 2/√3) | validated (six laboratory series) |
| Cell stretch → plates and rods (box law 1/λ) | validated as mathematics |
| Shape steering and gas-access indicators for ten MOFs | computed, scientifically unvalidated |
| CHGNet slab energies with water caps (team notebook) + GNN surrogate (Isha) | relaxed energies questionable; water correction validated; GNN behind a linear bond baseline in leave-MOF-out CV |
| Morphology spectrum (Isha, v4): every shape class a face set can reach, with the smallest γ-ratio change needed | new on 15 November; checked in `docs/v4_vs_corrected.md` |
| Part I Δα descriptor | withdrawn (tracks graph size) |

Key corrected-run numbers (GPU, 15 November, `nb_2026-11-14/colab_run_2026-11-15/`): 98 relaxed slabs of
16 MOFs, 85 converged; none negative at liquid-water Δμ = −0.5695 eV; thickness 24 vs 36 Å changes γ by
0.004 J/m²; MACE-MP-0 Spearman 0.94–1.00 per MOF; ZIF-8 rhombic dodecahedron {110} 100 %, HKUST-1 {111}
66 %, Mg-MOF-74 rod {2̅10} 77 %, UiO-66 still a miss. GNN leave-MOF-out MAE 0.131 J/m² against 0.088
(bonds_linear) and 0.084 (static_calibrated).

## 4. Where things are

| What | Where |
|---|---|
| Final team notebook (Isha, v4) | `code/morphology/steps1_8_check/nb_2026-11-15_v4_isha/` |
| Corrected notebook and the analysis of negative γ | `code/morphology/steps1_8_check/nb_2026-11-14/` (README there) |
| v4 vs corrected, and the merge question | `docs/v4_vs_corrected.md` |
| Website source / build / tests | `website/_build/`, `website/tests/` |
| Phase II report and slides (LaTeX) | `docs/reports/phase2_latex/` (`report.tex`, `slides.tex`) |
| Review deck in the college format | `docs/presentation/review_2026-11-16/` |
| Presentation notes | `docs/presentation/review_2026-11-16/presentation_notes.md` |
| Panel questions and answers | `docs/defence/panel_defence.md` |
| Laboratory records (134, 35 papers) | `data/experimental_morphology/` |

On the owner's Windows PC the clone is `C:\Dev\fyp\04_Repository\fyp` (remote
`https://github.com/Radha-Krishna-19/fyp.git`); bundles are in `C:\Dev\fyp\04_Repository\`. Results zips from
Colab land in `C:\Users\pradh\Downloads\`. Git on that PC shows every file as modified because of line
endings only; `git checkout -- .` clears it.

## 5. Open items

1. Team decision: merge the corrections into v4 or not (`docs/v4_vs_corrected.md` has the case).
2. No DFT check of any surface energy (needs HPC; CP2K inputs exist).
3. UiO-66 shape is still not reproduced.
4. Proofs and laboratory records have had no second-person check.
