# Project website

The documentation portal of the project, published at
<https://radha-krishna-19.github.io/fyp/>. It is a static site: every asset is relative and
`three.min.js` is included, so the pages also open directly from this folder with no web server and
no internet connection (open [`index.html`](index.html) in a browser).

Two kinds of content are on the pages, and each page says which is which:

* **Computed in the browser.** The decomposition, network, spectrum and morphology explorers compute
  their numbers at page load from the CIF files in this folder (`HKUST-1.cif`, `MOF5.cif`,
  `UiO-66.cif`, `ZIF-8.cif`) with the engines `mof_*.js`.
* **Generated from result files.** The other tables and figures are written by the scripts in
  [`_build/`](_build/) from the JSON and CSV files produced by the Python code. Under every figure a
  source line names the script that produced it, with a link to that script.

## Pages

| Page | File | Content |
|---|---|---|
| [Overview](https://radha-krishna-19.github.io/fyp/index.html) | `index.html` | What a metal-organic framework is, the question this project asks, and the honest answer so far. |
| [How We Got Here](https://radha-krishna-19.github.io/fyp/journey.html) | `journey.html` | From the papers we read to where the project is now: what was built from each, which code and notebooks produced which results, every mistake and its correction, and why each method was chosen over the alternatives. |
| [Methodology](https://radha-krishna-19.github.io/fyp/methodology.html) | `methodology.html` | The full workflow, the system architecture, the datasets, the evaluation strategy, and the justification for each choice. |
| [Decomposition](https://radha-krishna-19.github.io/fyp/decomposition.html) | `decomposition.html` | The published metal-oxo decomposition, module by module, with the real code beside a live 3D model. |
| [Network](https://radha-krishna-19.github.io/fyp/network.html) | `network.html` | Every graph-theory term defined from scratch, the periodic quotient graph, centrality, defects, and the Laplacian spectrum. |
| [Spectrum](https://radha-krishna-19.github.io/fyp/spectrum.html) | `spectrum.html` | What the parabola on every chart here actually means, the published method we build on, the mathematics, and all 61 real spectra as computed. |
| [Results](https://radha-krishna-19.github.io/fyp/results.html) | `results.html` | The multifractal band across 77 frameworks, the size confound that killed the pore-size claim, and what survives. |
| [Learn](https://radha-krishna-19.github.io/fyp/learn_shape.html) | `learn_shape.html` | Everything needed to follow the morphology work, from scratch and with a picture for each idea: unit cells, Miller planes, symmetry, how crystals grow, shape rules, measuring shape, and periodic graphs. |
| [Learn 2](https://radha-krishna-19.github.io/fyp/learn_energy.html) | `learn_energy.html` | Just enough, from scratch, to follow the rest of the project: surface and cleavage energy, slabs and terminations, where energies come from (force field, CHGNet, DFT), combining two shape methods, the statistics used, finite particles, and the software tools. |
| [Maths](https://radha-krishna-19.github.io/fyp/morph_math.html) | `morph_math.html` | Every rule used by the morphology work stated as a proposition and proved, with each proposition checked numerically in your browser. |
| [Morphology](https://radha-krishna-19.github.io/fyp/morphology.html) | `morphology.html` | The panel's second question: from one established unit cell, generate several crystal morphologies, mathematically and computationally. Method, live shape explorer, results for four MOFs, and the comparison with experiment. |
| [Cell Deform](https://radha-krishna-19.github.io/fyp/deform.html) | `deform.html` | The second reading of the panel's question: change the unit-cell parameters of an established MOF and see which shapes follow, with the exact rules and a live explorer. |
| [Graph Faces](https://radha-krishna-19.github.io/fyp/graph_faces.html) | `graph_faces.html` | Which faces are flat, how fast each grows, and which shape results, computed from each framework's own periodic graph and compared with experiment. |
| [Surface Energy](https://radha-krishna-19.github.io/fyp/surface_energy.html) | `surface_energy.html` | Cleavage energy of every crystal face computed from the atoms of each framework with a force field, the Wulff shapes that follow, and how robust they are. |
| [Hybrid](https://radha-krishna-19.github.io/fyp/hybrid.html) | `hybrid.html` | One rule that blends the geometric (BFDH) and energetic (Wulff) shape methods, what it gives for four MOFs, why no best weight is claimed, and the notebook that runs it on any crystal file. |
| [Experiment](https://radha-krishna-19.github.io/fyp/experiment.html) | `experiment.html` | Real crystals of these MOFs and the conditions they were grown under, the machine-learned (CHGNet) surface energies, the chemistry problems found in the slabs, every shape method scored against experiment, and the pipeline run on CoRE MOF structures. |
| [Why Shape](https://radha-krishna-19.github.io/fyp/bridge.html) | `bridge.html` | Why the project changes the shape of MOFs, how the earlier spectrum-based classification relates to morphology, a new test of whether the spectrum sees particle shape, and how the first half can be reused. |
| [Spectrum ↔ Shape](https://radha-krishna-19.github.io/fyp/relation.html) | `relation.html` | Three calculations that test whether the spectrum width of the first half of the project is related to the crystal shapes predicted in the second half, all produced by one notebook. |
| [Mistakes](https://radha-krishna-19.github.io/fyp/lessons.html) | `lessons.html` | Every mistake made so far, in plain words and in technical words: what we did, why we chose it, why it was wrong, and what we did to fix it. |
| [Source](https://radha-krishna-19.github.io/fyp/code.html) | `code.html` | Every source file of the project, readable in the browser with no download and no web server. |
| [Resources](https://radha-krishna-19.github.io/fyp/resources.html) | `resources.html` | The team paper, the reports and slides, every notebook (in the repository and in Google Colab), the datasets, the certifications and a map of the repository. |
| [References](https://radha-krishna-19.github.io/fyp/references.html) | `references.html` | Every paper, dataset and tool this project builds on. |
| [Glossary](https://radha-krishna-19.github.io/fyp/glossary.html) | `glossary.html` | Every term and symbol used anywhere on this site, defined from first principles and ordered so each one only depends on earlier ones. |
| [Team](https://radha-krishna-19.github.io/fyp/team.html) | `team.html` | Who did what, how far the implementation has actually got, and where every deliverable lives. |

## Building

The built pages (`*.html` in this folder) are never edited by hand. They are produced from
[`_build/content_source.html`](_build/content_source.html), the fragments in
[`_build/fragments/`](_build/fragments/) and the result files:

```bash
python website/_build/build_relation_fragment.py   # and any other build_*_fragment.py whose inputs changed
python website/_build/update_code_sources.py       # refreshes code_sources.js for the Source page
python website/_build/build_site.py                # writes every page
```

| Script | Writes |
|---|---|
| [`build_site.py`](_build/build_site.py) | All pages: navigation, section numbering, cross-page links, figure source lines |
| [`figure_sources.py`](_build/figure_sources.py) | The table that maps every figure to the script that produced it |
| `build_*_fragment.py` | One generated fragment each (deform, experiment, hybrid, journey, lessons, Phase 3 data, Phase 4, relation, bridge) |
| [`build_real_band_data.py`](_build/build_real_band_data.py), [`build_real_band.js`](_build/build_real_band.js) | `real_band_data.js` from the CoRE MOF notebook results |
| [`make_learn_energy_figures.py`](_build/make_learn_energy_figures.py) | The figures of the Learn 2 page |
| [`update_code_sources.py`](_build/update_code_sources.py) | `code_sources.js`, the source files shown on the Source page |

## Folders

| Folder | Content |
|---|---|
| [`assets/`](assets/) | Style sheets, site script, glossary data |
| [`figures/`](figures/) | Spectrum-part figures (`fig*.png`), [`learn/`](figures/learn/), [`morph/`](figures/morph/), [`relation/`](figures/relation/) |
| [`tests/`](tests/) | Twelve headless test suites; see its [README](tests/README.md) |

## Publication

[`.github/workflows/pages.yml`](../.github/workflows/pages.yml) runs the test suites and a Python
smoke test on every push, checks that the committed pages equal a fresh build, and on `main` deploys
this folder to GitHub Pages. One-time repository setting: *Settings → Pages → Build and deployment →
Source: GitHub Actions*.
