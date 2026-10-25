# Reports

| File | Pages | Content |
|---|---|---|
| [`MOF_morphology_primer.pdf`](MOF_morphology_primer.pdf) | 23 | *From Unit Cell to Crystal Shape*: a primer on MOF morphology written for the start of Part 2: crystals and symmetry, systematic absences, growth models (BFDH, attachment energy, Wulff), shape measures, periodic graphs, and the papers behind the plan |
| [`Phase1_morphology_report.pdf`](Phase1_morphology_report.pdf) | 7 | *Phase 1 Report: Crystal Morphologies Generated from the Unit Cell* for MOF-5, HKUST-1, UiO-66 and ZIF-8: the answer to the panel's question whether an established MOF's unit cell can generate crystal morphologies, shown mathematically and computationally |

Both reports are dated October 2026 and record the state of the work at that time. Later results,
including the comparison with laboratory crystals, are on the website pages
[Experiment](https://radha-krishna-19.github.io/fyp/experiment.html) and
[Mistakes](https://radha-krishna-19.github.io/fyp/lessons.html); where a later page corrects a
statement in a report, the page is the current record.

## Primer source

[`morphology_primer_source/`](morphology_primer_source/) holds the LaTeX source
([`primer.tex`](morphology_primer_source/primer.tex)) and the scripts that draw its figures into
[`fig/`](morphology_primer_source/fig/):

| Script | Figures |
|---|---|
| [`figs1.py`](morphology_primer_source/figs1.py) – [`figs4.py`](morphology_primer_source/figs4.py) | The primer's figures (several are reused on the Learn page, each with its source line) |
| [`poly.py`](morphology_primer_source/poly.py) | Symmetry families and polyhedra used by the figure scripts |
| [`attach.py`](morphology_primer_source/attach.py) | Attachment numbers on the pcu, fcu and sod nets (`fig/attach.json`, `fig/attach.png`) |

Run the scripts from inside `morphology_primer_source/`; `figs3.py` reads the CIF files in
[`code/spectrum_pipeline/`](../../code/spectrum_pipeline/).
