UPLOADING TO OVERLEAF
=====================
1. overleaf.com -> New Project -> Upload Project -> this ZIP
2. Overleaf detects panel_review.tex as the main file automatically.
   If not: Menu -> Main document -> panel_review.tex
3. Compiler: pdfLaTeX (the default). Press Recompile. 14 pages, no errors.

FILES
  panel_review.tex    the deck
  band77_figure.png   results figure (slide 3c)
  references.bib      BibTeX (optional -- refs are typeset inline too)

ADD YOUR LOGO: upload logo.png to the project root. The title slide loads it
with \IfFileExists, so it compiles fine without one and picks it up once added.

STILL TO FILL IN -- search the .tex for "XX":
  1. Team Number: [XX]        (title slide)
  2. CB.SC.U4CSE23XXX         (J. Keerthi Sree)
  3. CB.SC.U4CSE23XXX         (Isha)
