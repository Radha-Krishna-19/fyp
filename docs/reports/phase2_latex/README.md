# Phase II report and slides (LaTeX, department template)

Built from the department's `Presentation_Report_Guideline_LaTeX_Source`, case 1 (research project):
`report.tex` follows `1_report.tex` (eight sections) and `slides.tex` follows `1_presentation.tex`.
Compile with `pdflatex`, `bibtex`, `pdflatex`, `pdflatex` (or upload the folder to Overleaf).

| File | What it is |
|---|---|
| `report.tex`, `report.pdf` | The report (5 pages with references) |
| `slides.tex`, `slides.pdf` | The slides (13 frames); frame 2 waits for the guide's approval screenshot |
| `ref.bib` | References |
| `logo.png`, `logo_square.png` | From the department template |
| `figures/` | `phase4_compare.png` (`code/morphology/figs_phase4.py`), `fig_map_models.png` (`code/morphology/morphology_map/`), `advisor_hkust1.png` (screenshot of `website/advisor.html`) |

Where the numbers come from:

| Number | Source |
|---|---|
| 134 records, 35 papers, 12 MOFs | `data/experimental_morphology/dataset/experimental_morphology.csv` |
| Benchmark table, 4 of 5 MOFs, 73–97 %, clean test, habit 85/97, Mg-MOF-74 9/10 | `code/morphology/results/benchmark_mofs.json` (`run_benchmark_mofs.py`) |
| Bond share 93–98 %, van der Waals 2–7 % | `code/morphology/results/phase4_results.json` |
| MOF-5 γ111/γ100 = 1.72 | `phase4_results.json` (0.25542 / 0.14786) |
| Map boundaries | `code/morphology/morphology_map/cubic_wulff.py`; derivation in the audit of 13 November |
| 27 pages, over 3,400 checks | `website/_build/build_site.py`; `website/tests/` |

If a result file changes, change the number here and in both `.tex` files, then recompile.
