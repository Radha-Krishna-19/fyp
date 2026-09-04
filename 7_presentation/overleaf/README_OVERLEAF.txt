UPLOADING TO OVERLEAF
=====================

1. Go to overleaf.com -> New Project -> Upload Project
2. Upload the ZIP file (panel_review_overleaf.zip)
3. Overleaf will detect panel_review.tex as the main file automatically.
   If it does not: Menu -> Main document -> panel_review.tex
4. Compiler: pdfLaTeX  (Menu -> Compiler). This is the default.
5. Press Recompile. It should build with no errors, 14 pages.

FILES
-----
panel_review.tex    the deck
band77_figure.png   the results figure used on slide 3c
references.bib      BibTeX (optional -- references are typeset inline in the
                    .tex, so the deck compiles without a bibtex pass)

ADD YOUR LOGO
-------------
Upload logo.png into the project root. The title slide loads it with
\IfFileExists, so it compiles fine without one and picks it up automatically
once present.

STILL TO FILL IN
----------------
Search the .tex for "XX" -- three placeholders:
  1. Team Number: [XX]              (title slide)
  2. CB.SC.U4CSE23XXX               (J. Keerthi Sree)
  3. CB.SC.U4CSE23XXX               (Isha)
