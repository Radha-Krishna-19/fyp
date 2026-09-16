# Panel Review Materials

Everything needed for the **23CSE498 Phase 2, Panel Review 1** presentation.

| File | What it is |
|---|---|
| **`panel_review.tex`** | The Beamer deck source. Compile with `pdflatex` **twice**. |
| **`panel_review.pdf`** | Ready to present, but must be recompiled after the 2026-09-16 rewrite below — the checked-in copy predates it. |
| **`TEAM_SPLIT.md`** | **Who says what.** Per-member slides, exact script, timings, and a question-routing table — also predates the rewrite, check against the new slide list before using. |
| `references.bib` | BibTeX for the deck (references are also typeset inline, so no bibtex pass is needed). |
| `fig15_full_band.png`, `fig16_full_band_vs_size.png`, `fig17_grouped_spectra.png` | The current, correct results figures (complete 138-framework dataset, coarse-grained graph), slides 3c–3e. |
| `fig17b_xenon_core_raw_reference.png`, `fig17c_xenon_core_bands_reference.png` | Reference figures from an independent run, reproduced as-is, slide 3f. |
| **`panel_review_overleaf.zip`** | **Upload this straight to Overleaf.** Contains the .tex, all figures, the .bib and instructions. |
| `overleaf/` | The same files unzipped, if you prefer to upload individually. |

---

## Compiling

```bash
cd 7_presentation
pdflatex panel_review.tex
pdflatex panel_review.tex      # second pass for section numbering
```

Needs `beamer`, `tikz`, `booktabs`, `amsmath`, `xcolor`. All standard TeX Live.
The deck compiles with **no content overflow** — verified.

`logo.png` and `band_analysis.png` are loaded with `\IfFileExists`, so the deck still
compiles if they are missing (it leaves a placeholder box instead).

---

## Before you present — fill these in

The deck has one placeholder left:

1. **`Team Number: [XX]`** — on the title slide

Roll numbers are all filled in (Keerthi Sree CB.SC.U4CSE23031, Isha Sri Prakash
CB.SC.U4CSE23029).

The guide is already filled in: **Dr. T. Ramraj**, M.E, Ph.D — Assistant Professor (Sl.Gd.),
Department of CSE, School of Computing, Coimbatore.

Search the `.tex` for `XX` to find all of them.

---

## Deck structure (16 pages, rewritten 2026-09-16)

| Page | Slide | Rubric |
|---|---|---|
| 1 | Title | — |
| 2 | **0 · Problem Context** — why the project exists | (framing) |
| 3 | **1 · Methodology & Solution Design** | 5 marks |
| 4 | **1b · Mathematical Model** | 5 marks |
| 5 | **2 · Implementation Progress & Module Functionality** | 8 marks |
| 6 | **2b · Results Obtained So Far** | 8 marks |
| 7 | **3 · Technical Knowledge & Design Decisions** | 5 marks |
| 8 | **3b · Deliverable — the platform** | 5 marks |
| 9 | **3c · Principal Result** — both complete datasets, correct graph | 5 marks |
| 10 | **3d · Does Class Track Chemistry, or Graph Size?** | 5 marks |
| 11 | **3e · Every Spectrum, Both Our Datasets** | 5 marks |
| 12 | **3f · The Same Plotting Convention, an Independent Reference** | 5 marks |
| 13 | **4 · Remaining Work & Timeline** | — |
| 14–15 | References (19 entries) | — |
| 16 | Thank You | — |

Slide 0 and the "b"/"c"/"d"/"e"/"f" slides are additions to the template. They exist because
the rubric allocates **8 marks to implementation** and **5 to technical knowledge** — enough
weight to deserve full slides of results and design reasoning rather than bullets squeezed
onto one page. **The MOOC slide was removed** from the deck at the presenter's request; the
MOOC assignments themselves are still tracked below, since the certification requirement is
unaffected by whether it gets its own slide.

---

## MOOC recommendations, and why

Each student needs one approved **10–20 hour** certification relevant to the project. These
map onto components the project actually uses:

| Student | Suggested course | Platform | Hrs | Maps to |
|---|---|---|---|---|
| P. M. Radha Krishna | **Algorithms on Graphs** — BFS, shortest paths, connected components | Coursera (UC San Diego) | 20 | **The most CSE-facing option.** These are the exact algorithms the project runs: BFS for box growing, shortest paths for the distance matrix, connected components for block extraction |
| P. Kshitij Varma | Introduction to Complex Network Analysis | NPTEL | 20 | Fractal/multifractal network characterisation |
| G. Rohith Abhinav | Chemoinformatics *or* Computational Materials Science | NPTEL | 16 | CIF handling, bond perception, MOF structure |
| J. Keerthi Sree | Data Visualization with Python | Coursera (IBM) | 15 | The interactive platform and figures |
| Isha Sri Prakash | Machine Learning for Materials Informatics | edX / Coursera | 15 | Descriptor-based screening — the project's goal |

**Alternatives if any of the above are unavailable:**

- *Network Science* (NPTEL / Coursera) — for anyone on the graph side
- *Applied Data Science with Python* (Coursera, Michigan) — general
- *Python for Data Science* (NPTEL) — if a member wants fundamentals first
- *Introduction to Computational Materials Science* (NPTEL) — chemistry-facing
- *Graph Analytics for Big Data* (Coursera, UCSD) — scaling the analysis

**Pick courses you can actually finish and speak to.** A panel may well ask what you learned
and how it connects — an unfinished 40-hour course is worse than a completed 12-hour one.
