# Notebook builders (Phase 2)

Scripts that generate Colab notebooks. They are not needed to run the analysis.

| File | What it does |
|---|---|
| `make_nb.py` | Builds `notebooks/morphograph_mof/MorphoGraph_hybrid.ipynb` (BFDH, Wulff and blended shapes for any CIF) |
| `make_symmetric_nb.py` | Builds the symmetric-slab Colab notebook from `MorphoGraph_MOF_colab_4MOFs.ipynb` |
| `nb_test.py` | Checks that the generated notebook cell runs (creates a throwaway `mofmorph/` folder in the folder it is started from) |
