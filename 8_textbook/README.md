# The Project Textbook

**A complete, zero-to-hero explanation of what we did and why.**
Written for the five of us, assuming no prior knowledge of chemistry, crystallography or
network science.

---

## How to use this

Read it in order. Each chapter assumes only the ones before it. **No term is used before it
is defined**, and every number in here is one we actually computed — nothing is copied from a
paper or invented for illustration.

If you only have an hour before the review, read **Chapters 1, 2 and 8**.

| # | Chapter | What it gives you | Read time |
|---|---|---|---|
| [1](01_background.md) | **Background** — what a MOF is and why anyone cares | The chemistry, from zero | 12 min |
| [2](02_problem.md) | **The Problem Statement** — what we are actually trying to solve | The single most important chapter | 10 min |
| [3](03_crystallography.md) | **Crystals and CIF Files** | How structures are stored, why bonds must be guessed | 15 min |
| [4](04_decomposition.md) | **Decomposition** — cutting a crystal into blocks | The published algorithm we visualise | 15 min |
| [5](05_graphs.md) | **Graph Theory** — every term, from scratch | Vertices, degree, centrality, Laplacian, λ₂ | 20 min |
| [6](06_multifractal.md) | **The Multifractal Spectrum** | The maths, explained without assuming any | 25 min |
| [7](07_implementation.md) | **What We Built** | The code, the platform, the tests | 15 min |
| [8](08_results.md) | **Results** — what we found | Every number, with its caveat | 20 min |
| [9](09_mistakes.md) | **Mistakes We Found** | Three real bugs, and how we caught them | 15 min |
| [10](10_limitations.md) | **Limits and Next Steps** | What we cannot claim, and why | 10 min |
| [11](11_glossary.md) | **Glossary** | Every term in one place | reference |

---

## The project in five sentences

1. **MOFs** are sponge-like crystals built by joining metal clusters (**nodes**) to organic
   molecules (**linkers**); there are hundreds of thousands of them.
2. Evaluating one properly takes **hours** of simulation, so the design space cannot be
   searched exhaustively.
3. We ask whether a **structural descriptor** — computed from connectivity alone in seconds —
   can group MOFs into useful families.
4. We built the full pipeline (crystal → graph → spectrum), an interactive platform, and ran
   it across **77 frameworks**.
5. The machinery works and is verified; **the descriptor is not yet shown to mean anything
   physically**, and we identified exactly what is blocking that.

---

## The honest one-paragraph summary

> We implemented a published decomposition algorithm and a published multifractal method,
> built a browser platform that runs the whole pipeline live, and applied it to 77
> frameworks. Along the way we found and fixed **three real bugs** — one of which was
> deleting the peak of every spectrum we computed. All 77 spectra now have the correct
> mathematical shape and fall in a tight band. But we also showed that the band is
> **confounded by graph size** rather than driven by chemistry, so we withdrew the
> interpretation we had been heading towards. Reporting that confound, with the measurement
> that establishes it, is the actual scientific contribution so far.

---

## Figures

All figures in `figures/` are generated from the project's real data by the code in
`2_python/` and `3_notebooks/`. None are illustrative mock-ups.

| Figure | Shows |
|---|---|
| `fig01_mof_concept.png` | Node + linker → framework, and where the pore is |
| `fig02_pipeline.png` | The six pipeline stages |
| `fig03_periodic_vs_naive.png` | **Measured**: discarding translations destroys coordination numbers |
| `fig04_degeneracy.png` | **Measured**: only two distinct degrees exist in a perfect crystal |
| `fig05_defect.png` | **Measured**: λ₂ and centrality before/after removing one linker |
| `fig06_boxgrowing.png` | **Measured**: box growing on the real HKUST-1 graph |
| `fig07_tau_fix.png` | **Measured**: why the spectra were not parabolic |
| `fig08_band77.png` | **Measured**: all 77 spectra, the band, and the confound |

---

## Where everything else lives

```
1_website/      the interactive platform  (open index.html)
2_python/       the reference implementation, one module per stage
3_notebooks/    the 77-framework study
4_reference/    figures
5_concepts/     shorter deep-dive documents
6_references/   the papers, annotated
7_presentation/ the panel-review deck and the speaking split
8_textbook/     this
```
