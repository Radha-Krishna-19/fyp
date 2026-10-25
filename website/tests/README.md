# Website test suites

Twelve Node.js suites that load the built pages in [jsdom](https://github.com/jsdom/jsdom), run the
real page scripts and check the content they produce. Most numbers on the site are computed in the
browser or generated from result files, so a broken script does not raise a visible error; it leaves
an empty panel. These suites detect that, and they also check that the text of each page agrees
with the Python result files it was generated from.

## Running

```bash
cd website/tests
npm install      # once; installs jsdom
npm test         # runs run_all_tests.js: every test_*.js, then a pass/fail summary
node test_pages.js   # or any single suite
```

Each suite exits with status 0 on success and 1 on failure. The GitHub workflow
[`.github/workflows/pages.yml`](../../.github/workflows/pages.yml) runs `npm test` on every push and
pull request, and deploys the site only when all suites pass.

## What each suite checks

| Suite | Checks |
|---|---|
| [`test_pages.js`](test_pages.js) | Every one of the 24 pages loads, its engine scripts fill their containers, every internal link and `#anchor` resolves, every figure file exists and every figure carries a source line naming the script that produced it |
| [`test_engines.js`](test_engines.js) | The browser engines (decomposition, network, spectrum, morphology) produce computed content on the pages that use them |
| [`test_decompose.js`](test_decompose.js) | The CIF parser and metal-oxo decomposition on HKUST-1: atom count, cell parameters, building blocks, formula |
| [`test_network_page.js`](test_network_page.js) | The periodic graph reproduces literature coordination numbers, the non-periodic construction fails as expected, centrality degeneracy is reported, a simulated defect lowers λ<sub>2</sub> |
| [`test_block_inspector.js`](test_block_inspector.js) | The inspector of a coarse-grained vertex draws the correct atoms and only bonds that exist inside that building block |
| [`test_maths.js`](test_maths.js) | Every symbol in a displayed equation is defined before use; equations are numbered consecutively; stated values agree with the data files |
| [`test_real_band_numbers.js`](test_real_band_numbers.js) | Every statistic stated about the CoRE MOF and hMOF spectra is recomputed from `notebooks/spectrum/real_results.json` and `results.json` |
| [`test_morphology.js`](test_morphology.js) | The JavaScript morphology engine agrees with the independent Python package (`code/morphology/`) number by number, and the Morphology page draws its shapes |
| [`test_morph_pages.js`](test_morph_pages.js) | Learn, Maths and Graph Faces pages: figures exist, every live check on the Maths page holds, Phase 3 tables equal the Python output |
| [`test_bridge_pages.js`](test_bridge_pages.js) | Hybrid, Spectrum ↔ Shape, Mistakes and How We Got Here: every number equals the result files; entry and stage counts |
| [`test_glossary.js`](test_glossary.js) | Glossary entries are defined, ordered, and annotate pages without altering their text |
| [`test_render_robustness.js`](test_render_robustness.js) | The 3D renderer draws on demand, recovers from a lost WebGL context, pauses off-screen panels and tolerates degenerate input |

Python checks are separate: `code/morphology/tests*.py`,
`code/spectrum_shape_relation/check_spectrum_shape_relation.py` and
`code/spectrum_pipeline/_ci_smoke_test.py`.
