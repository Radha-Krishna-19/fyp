# Project map: Phase 1 and Phase 2

This page says where everything lives. The project has two phases of work and one piece that joins them.

| | Phase 1: connectivity descriptor | Phase 2: crystal morphology |
|---|---|---|
| Question | Does a number computed from a MOF's connectivity (the width of a multifractal spectrum, Δα) carry enough structure to pre-select MOFs for simulation? | Given the unit cell of an established MOF, which crystal shapes can it take, computed mathematically and by program? |
| Outcome | Answer: no, as currently defined. Δα grows with graph size and never converges. The published bands are withdrawn. The pipeline is verified and reused. | Allowed faces from the space group (16 proved propositions), shapes from seven growth models, scored against 134 laboratory records. |
| Code | [`code/spectrum_pipeline/`](code/spectrum_pipeline/) | [`code/morphology/`](code/morphology/), including [`morphology_map/`](code/morphology/morphology_map/) and [`steps1_8_check/`](code/morphology/steps1_8_check/) (10 November) |
| Data | [`data/structures/`](data/structures/), [`data/spectrum_descriptors/`](data/spectrum_descriptors/) | [`data/experimental_morphology/`](data/experimental_morphology/), [`data/chgnet_morphograph_runs/`](data/chgnet_morphograph_runs/) |
| Notebooks | [`notebooks/spectrum/`](notebooks/spectrum/) | [`notebooks/morphograph_mof/`](notebooks/morphograph_mof/), [`code/morphology/chgnet_wulff/`](code/morphology/chgnet_wulff/) |
| Website pages | Spectrum, Network, Decomposition, Results, Methodology | Learn, Maths, CIF to Shape, Morphology, Graph Faces, Deform, Surface Energy, Experiment, Morphology map |
| Written | [`docs/paper/`](docs/paper/), [`docs/concepts/`](docs/concepts/) | [`docs/reports/`](docs/reports/) (complete report, CIF to Shape reports, primer, Phase 1 morphology report) |

**The link between the phases:** [`code/spectrum_shape_relation/`](code/spectrum_shape_relation/) computes the spectrum and the
dimension profile of finite crystal particles of the shapes found in Phase 2. It reads Phase 1 code and Phase 2 code and is
written up on the website page "Spectrum and shape".

**Shared:** [`docs/`](docs/) (reports, slides, textbook, references, certificates, project notes), [`website/`](website/) (every page,
the browser engines, the build and the tests), [`requirements.txt`](requirements.txt).

## Naming note

The word "phase" is used in two ways. In this map, Phase 1 and Phase 2 are the two halves of the project above. Inside
`code/morphology/` the scripts `run_phase1.py` to `run_phase4.py` are the four stages of the morphology work (symmetry and faces,
cell deformation, graph faces, force-field surface energy). They are all part of Phase 2 here.

## Running anything

Every script finds its inputs from its own location, so it can be started from any folder:

```bash
pip install -r requirements.txt
python code/spectrum_pipeline/code_13_scaling_regimes.py        # from the repository root
python /full/path/to/code/morphology/run_phase1.py              # or from anywhere else
```

Website: open `website/index.html` (no server needed). Rebuild with `python website/_build/build_site.py`; tests with
`cd website/tests && npm install && npm test`.
