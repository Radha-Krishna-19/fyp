# Panel Review Materials

Everything needed for the **23CSE498 Phase 2, Panel Review 1** presentation.

| File | What it is |
|---|---|
| **`panel_review.tex`** | The Beamer deck source. Compile with `pdflatex` **twice**. |
| **`panel_review.pdf`** | Pre-compiled, 13 pages. Ready to present. |
| **`TEAM_SPLIT.md`** | **Who says what.** Per-member slides, exact script, timings, and a question-routing table. |
| `references.bib` | BibTeX for the deck (references are also typeset inline, so no bibtex pass is needed). |
| `band77_figure.png` | The results figure (all 77 spectra + the band + the confound), slide 3c. |
| **`panel_review_overleaf.zip`** | **Upload this straight to Overleaf.** Contains the .tex, the figure, the .bib and instructions. |
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

The deck has three placeholders:

1. **`Team Number: [XX]`** — on the title slide
2. **Two roll numbers** — `CB.SC.U4CSE23XXX` for J. Keerthi Sree and Isha

The guide is already filled in: **Dr. T. Ramraj**, M.E, Ph.D — Assistant Professor (Sl.Gd.),
Department of CSE, School of Computing, Coimbatore.

Search the `.tex` for `XX` to find all of them.

---

## Deck structure (13 pages)

| Page | Slide | Rubric |
|---|---|---|
| 1 | Title | — |
| 2 | **0 · Problem Context** — why the project exists | (framing) |
| 3 | **1 · Methodology & Solution Design** | 5 marks |
| 4 | **1b · Mathematical Model** | 5 marks |
| 5 | **2 · Implementation Progress (~60%)** | 8 marks |
| 6 | **2b · Results Obtained So Far** | 8 marks |
| 7 | **3 · Technical Knowledge & Design Decisions** | 5 marks |
| 8 | **3b · Deliverable — the platform** | 5 marks |
| 9 | **4 · Technical Enrichment (MOOCs)** | — |
| 10 | **5 · Remaining Work & Timeline** | — |
| 11–12 | References (19 entries) | — |
| 13 | Thank You | — |

Slide 0 and the "b" slides are additions to the template. They exist because the rubric
allocates **8 marks to implementation** and **5 to technical knowledge** — enough weight to
deserve a full slide of results and a full slide of design reasoning rather than bullets
squeezed onto one page.

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
| Isha | Machine Learning for Materials Informatics | edX / Coursera | 15 | Descriptor-based screening — the project's goal |

**Alternatives if any of the above are unavailable:**

- *Network Science* (NPTEL / Coursera) — for anyone on the graph side
- *Applied Data Science with Python* (Coursera, Michigan) — general
- *Python for Data Science* (NPTEL) — if a member wants fundamentals first
- *Introduction to Computational Materials Science* (NPTEL) — chemistry-facing
- *Graph Analytics for Big Data* (Coursera, UCSD) — scaling the analysis

**Pick courses you can actually finish and speak to.** A panel may well ask what you learned
and how it connects — an unfinished 40-hour course is worse than a completed 12-hour one.
