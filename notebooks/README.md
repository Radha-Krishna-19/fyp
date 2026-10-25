# Notebooks

| Folder | Part | Content |
|---|---|---|
| [`spectrum/`](spectrum/) | 1, multifractal spectrum | The hMOF and CoRE MOF band analyses and the walkthrough of the published decomposition pipeline ([README](spectrum/README.md)) |
| [`morphograph_mof/`](morphograph_mof/) | 2, crystal morphology | The MorphoGraph-MOF CHGNet pipeline in three versions and the BFDH × Wulff hybrid notebook ([README](morphograph_mof/README.md)) |

Two further notebooks sit beside the code they drive:
[`code/spectrum_shape_relation/Spectrum_Shape_Relation.ipynb`](../code/spectrum_shape_relation/Spectrum_Shape_Relation.ipynb)
(the relation between the spectrum and crystal shape) and
[`code/morphology/chgnet_wulff/MOF_Wulff_Colab.ipynb`](../code/morphology/chgnet_wulff/MOF_Wulff_Colab.ipynb)
(CHGNet surface energies to Wulff shapes).

## Working copies in Google Colab

Most notebook development is done in Google Colab. The working copies of Keerthi Sree Jonnakuti are:

| Notebook | Link | Related repository material |
|---|---|---|
| Coarse-grained MOF spectrum | [Colab](https://colab.research.google.com/drive/1lnWFEl2flCUrFI-n3BJurn_ICbJaNpPy) | [`code/spectrum_pipeline/code_12_converged_band.py`](../code/spectrum_pipeline/code_12_converged_band.py), [`data/spectrum_descriptors/independent_cg_run/`](../data/spectrum_descriptors/independent_cg_run/) |
| MOF morphology from Wulff shapes | [Colab](https://colab.research.google.com/drive/1A4wcRz-HMCVbwJ7zgqPqCQv-NQeTumUb) | [`code/morphology/chgnet_wulff/`](../code/morphology/chgnet_wulff/) |
| MOF morphologies | [Colab](https://colab.research.google.com/drive/1dWTwj7SkIVFL2EHxg1cDPOqwMOtS8Mny) | [`morphograph_mof/`](morphograph_mof/) |

The Colab copies change independently of this repository. A result is quoted on the website only
when the notebook version that produced it, or its output files, are in the repository.

## Conventions

* The results a notebook produced are stored as data files next to it or in [`data/`](../data/)
  (for example [`spectrum/results.json`](spectrum/results.json) and
  [`spectrum/real_results.json`](spectrum/real_results.json)); the website reads those files, not
  notebook outputs. [`spectrum/pipeline_walkthrough_full.ipynb`](spectrum/pipeline_walkthrough_full.ipynb)
  keeps its outputs as a worked example.
* Outputs of the CHGNet runs are stored as data, in
  [`data/chgnet_morphograph_runs/`](../data/chgnet_morphograph_runs/), not inside the notebooks.
