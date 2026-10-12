# Crystal morphology from the unit cell (Phase 1)

Answers the panel's second question: given an established MOF's unit cell, generate
several crystal morphologies, mathematically and computationally. Theory: the project
primer *From Unit Cell to Crystal Shape*. Results: `morphology.html` on the site and
`Phase1_morphology_report.pdf`.

| File | What it does |
|---|---|
| `mofmorph/structure.py` | Reads a CIF, finds the space group with spglib (with and without H), returns the conventional cell and symmetry operations |
| `mofmorph/faces.py` | Systematic-absence rule with every symmetry operation, effective spacings d_eff, symmetry families ({111}+/- in -43m) |
| `mofmorph/shape.py` | Crystal shape as a convex polytope; exact volume, area, sphericity, gyration tensor, kappa^2, Q_3/Q_4/Q_6 |
| `mofmorph/models.py` | Growth-rate models: BFDH, user rates (morph families), graph rule R = exp(beta*c), growth in time from a seed |
| `mofmorph/graphrule.py` | Attachment numbers on the ideal pcu and fcu node nets |
| `tests.py` | 14 checks against known answers (P/I/F lattices, diamond glide absences, exact solids) |
| `run_phase1.py` | Produces every number and figure in `results/` |

Run: `python3 2_python/morphology/tests.py`, then `python3 2_python/morphology/run_phase1.py`.
Requirements: numpy, scipy, matplotlib, ase, spglib.

The browser engine `1_website/mof_morphology.js` is a second, independent implementation;
`1_website/tests/test_morphology.js` checks it against `results/phase1_results.json`.
