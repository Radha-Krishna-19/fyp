# mofmorph: the Phase 2 Python package

Imported by every `run_*.py`, `figs_*.py` and `tests*.py` script in the parent folder. Needs numpy, scipy, ase, spglib.

| File | What it does |
|---|---|
| `structure.py` | Reads a CIF, finds the true space group, returns the conventional cell and its symmetry operations |
| `faces.py` | Allowed crystal faces (systematic absences), effective spacings d_eff, symmetry families |
| `shape.py` | A crystal shape as a convex polytope P = {x : n·x ≤ r}; volume, areas, sphericity |
| `models.py` | Growth-rate models that turn a set of faces into a shape (BFDH and others) |
| `graphrule.py` | Attachment number of each face on an idealised node net |
| `graphfaces.py` | Crystal faces read from the periodic graph |
| `deform.py` | Changes a, b, c and the angles of the cell and recomputes faces and shapes |
| `forcefield.py` | Unrelaxed cleavage energy of a plane from a pairwise force field (UFF Lennard-Jones plus a bond term) |
| `hybrid.py` | Face energies for any crystal system and the BFDH, Wulff and blended shapes |
| `chgnet_runs.py` | Reads the CHGNet result folders in `data/chgnet_morphograph_runs/` |
| `chgnet_post.py` | Turns those results into face energies and Wulff shapes |
| `render.py` | Plotting helpers |
