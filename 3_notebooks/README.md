# Notebook

One notebook: compute multifractal spectra for 77 MOFs and build the band.

| File | What it is | Run it? |
|---|---|---|
| **`mof_band_analysis.ipynb`** | 77 frameworks downloaded live → spectra → **the band**, plus the shape check and the size-confound test. | Colab: Run All |
| `results.json` | Computed spectra for all 77. Lets Steps 9–12 run without recomputing. | — |
| `CHANGES.md` | **What changed from the original notebook, and why.** | — |

> ## ⚠ What this dataset actually is
>
> All 77 structures are named `hMOF-###` — they are from the **hypothetical MOF** database:
> **computer-generated candidates that have never been synthesised.** The notebook requests
> `TARGET_DATABASE = "CoREMOF 2019"` (experimental) but the server returned hMOF records and
> nothing verified it. Step 2 now checks and warns.
>
> - **Do not call these "experimental" or "real" structures.**
> - **Every one has a Zn₄O node**, so this set cannot support any claim about different metals.
> - What it *is* good for: one node type with many different linkers — a genuine
>   same-node, varied-linker family.


---

## What it does

Steps 1–8 download 77 MOFs from MOFX-DB, build PBC-aware bond graphs,
coarse-grain them, and compute a multifractal spectrum for each.
**Steps 9–12 are the band analysis**, and they report two corrections and one retraction.

## Correction 1 — the spectrum had the wrong shape

A multifractal spectrum `f(α)` must be an **inverted parabola** peaking at `q = 0`, where
`f(α₀) = D₀`, the fractal dimension. Ours sloped downhill.

The paper defines `τ(q) = ln 𝒫_q(r) / ln(r/r_N)` — a straight-line fit **through the
origin**, because `𝒫_q ~ (r/r_N)^τ` has no prefactor. The code used `np.polyfit(x, y, 1)`
and took the **slope**, a fit with a **free intercept**. At `q = 0`:

- every term is `pr_i⁰ = 1`, so `𝒫₀ = |I|`, the count of influential nodes
- that count is the **same at every radius** → the fit sees a flat line
- a flat line has slope 0 → `τ(0) = 0` → `f(α₀) = 0`

The peak is pinned to zero and the parabola disappears. **Before the fix: τ(0) = 0 in all 77 frameworks and none peaked at q = 0.
After: all 77 peak at q = 0.** Fixed via `inmfa(..., tau_mode="paper")`, now the default;
`tau_mode="slope"` reproduces the old behaviour so the correction is demonstrable.

| τ definition | τ(0) | f(0) | peak at | parabola? |
|---|---|---|---|---|
| free-intercept slope (old) | 0.0000 | 0.0000 | q = −4 | no |
| paper: `ln 𝒫_q / ln(r/r_N)` | −3.5028 | +3.5028 | **q = 0** | **yes** |

*(verification figures above are from a synthetic test graph. On the real 77-framework run: τ(0) = −2.5669, f(α₀) = +2.5669, and **77/77 peak at q = 0**.)*

## Correction 2 — the averaging order

The partition function must be built **per box-covering trial** and averaged in log space.
Averaging `p(r)` first and then raising to the power `q` exponentiates an already-smoothed
quantity. Measured on HKUST-1: 0.021 ± 0.004 (wrong) vs 0.327 ± 0.032 (correct).

## Retraction — the band does not mean pore architecture

| Test | r |
|---|---|
| Δα vs pore diameter (LCD), raw | −0.497 |
| Δα vs LCD, **controlling for graph size** | **+0.101** — vanishes |
| Δα vs graph size, **controlling for LCD** | **+0.621** — survives |

Linear model: graph size alone R² = 0.533; adding pore diameter → 0.538. Pore size buys
**+0.005**. Δα is tracking **supercell size**, which is set by `MIN_CELL_LENGTH` and the
`MAX_ATOMS` cap — computational parameters, not chemistry.

On 8 frameworks the pore reading was plausible. On 77 it is not supported.

**What would make it testable:** compare only frameworks of comparable graph size, or
normalise the fit window per structure so Δα stops growing with the graph, then re-test.

## Running it

- **Full run** — Colab, Run All. Downloads the structures and recomputes everything.
- **Band only** — Steps 9–12 fall back to `results.json` if the earlier steps have not run,
  so the band analysis executes in seconds. Keep `results.json` beside the notebook.

> **`results.json` here is the corrected run:** all 77 spectra are proper inverted parabolas
> peaking at q = 0 (τ(0) = −2.5669, f(α₀) = +2.5669). Re-running the notebook reproduces it.
