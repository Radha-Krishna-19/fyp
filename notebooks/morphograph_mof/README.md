# MorphoGraph-MOF notebooks (Part 2)

Notebooks that turn a MOF unit cell into crystal surfaces, surface energies and crystal shapes. The
analysis of their results is on the website pages
[Experiment](https://radha-krishna-19.github.io/fyp/experiment.html) and
[Hybrid](https://radha-krishna-19.github.io/fyp/hybrid.html).

| Notebook | Method | Hardware | Status |
|---|---|---|---|
| [`MorphoGraph_MOF_revised.ipynb`](MorphoGraph_MOF_revised.ipynb) | CHGNet relaxation of the bulk and of every slab; pair-fitted surface energies; atomistic particles. Interactive: twelve settings are prompted for, and the CIF is uploaded | Google Colab, GPU recommended | Run on hMOF-0, 12 October 2026 |
| [`MorphoGraph_MOF_colab_4MOFs.ipynb`](MorphoGraph_MOF_colab_4MOFs.ipynb) | The same science code with the settings in one cell and the four benchmark CIFs embedded (MOF-5, HKUST-1, UiO-66, ZIF-8) | Google Colab, GPU recommended | Run on MOF-5, HKUST-1 and UiO-66, 14 October 2026 |
| [`MorphoGraph_MOF_colab_symmetric_slabs.ipynb`](MorphoGraph_MOF_colab_symmetric_slabs.ipynb) | Four changes, each marked `SYMMETRIC-SLAB CHANGE` in the code: slabs symmetric as cut count as one termination, so each gives one face energy directly | Google Colab, GPU recommended | Prepared, not yet run |
| [`MorphoGraph_hybrid.ipynb`](MorphoGraph_hybrid.ipynb) | BFDH, force-field (UFF) Wulff and the blend R = R<sub>BFDH</sub><sup>1−w</sup> R<sub>Wulff</sub><sup>w</sup> for a CIF of any crystal system; optional external (CHGNet or DFT) energies | CPU, seconds | Used for the Hybrid page |

## Outputs

The run outputs (cells, initial and relaxed slabs, slab energies, pair fits, metadata, particles) are
in [`data/chgnet_morphograph_runs/`](../../data/chgnet_morphograph_runs/), one folder per run. They
are read through [`code/morphology/mofmorph/chgnet_runs.py`](../../code/morphology/mofmorph/chgnet_runs.py)
by [`run_chgnet_cleavage.py`](../../code/morphology/run_chgnet_cleavage.py) and
[`slab_check.py`](../../code/morphology/slab_check.py).

## How the notebooks are produced

The two Colab variants and the hybrid notebook are generated, so that their science code stays
identical to the source:

| Builder | Writes |
|---|---|
| [`code/morphology/tools/make_nb.py`](../../code/morphology/tools/make_nb.py) | `MorphoGraph_hybrid.ipynb`, with the `mofmorph` modules written into the notebook |
| [`code/morphology/tools/make_symmetric_nb.py`](../../code/morphology/tools/make_symmetric_nb.py) | `MorphoGraph_MOF_colab_symmetric_slabs.ipynb` from the four-MOF notebook |
| [`code/morphology/tools/nb_test.py`](../../code/morphology/tools/nb_test.py) | Runs the hybrid notebook's code outside Jupyter as a check |

## Known limits of the CHGNet results

* A slab has two faces, and the pair equations were underdetermined for every face, so individual
  face energies could not be separated. The project uses the cleavage energy (half the smallest slab
  excess), an upper bound on the lowest termination energy.
* Some slabs contain detached fragments (cut linkers); the shapes are reported both with all slabs and
  with intact slabs only.
* The energies have not been checked against DFT; the plan is
  [`code/morphology/DFT_CHECK_PLAN.md`](../../code/morphology/DFT_CHECK_PLAN.md).
