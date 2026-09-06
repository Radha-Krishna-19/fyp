# Website test suite

Five Node + jsdom suites that run the real site headlessly. They exist because
this site computes its numbers live in the browser rather than displaying
transcribed results — so a broken script does not throw a visible error, it
silently shows a blank panel. These catch that.

## Running them

```bash
cd 1_website/tests
npm install jsdom          # the only dependency
node test_stage.js
node test_single_page.js
node test_network_page.js
node test_decompose.js
node test_render_robustness.js
```

Each exits `0` on success and `1` on the first failure, so they drop into CI
unchanged.

## What each one guards

| Suite | Guards against |
|---|---|
| `test_stage.js` | The presentation layer. Checks `stage.css`/`stage.js` are wired in, the hero canvas and its three CTAs exist and point at real sections, every `data-count` parses as a number, the scrollytelling block has one pipeline stage per step, all 19 nav links resolve **and appear in document order with matching numbers**, no duplicate `id`s, and that booting `stage.js` actually injects the progress bar, theme button, back-to-top and section anchors. |
| `test_single_page.js` | The merged single page. All 19 sections present, every engine (walkthrough, overview tables, network validation, multifractal table, published-method table, code browser) renders real content rather than an empty shell. |
| `test_network_page.js` | The chemistry. The periodic graph must reproduce literature coordination numbers, the naive non-periodic construction must demonstrably fail, centrality degeneracy must be reported honestly, and a simulated defect must lower λ₂. |
| `test_decompose.js` | The CIF parser and decomposition on HKUST-1 — atom count, cell parameters, and the recovered formula. |
| `test_render_robustness.js` | The 3D renderer surviving degenerate input (empty structures, single atoms, missing elements) instead of throwing. |

## Why the nav-order test matters

The sticky nav was hand-maintained at one point and drifted to
`1 3 2 3 4 5 6 10 11`. `test_stage.js` now asserts that link *n* is labelled
*n* and that the targets appear in the same order in the document, so that
class of drift cannot come back unnoticed.
