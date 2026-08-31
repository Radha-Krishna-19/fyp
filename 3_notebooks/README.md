# Notebooks

| Notebook | What it does | Run it? |
|---|---|---|
| **`mof_band_analysis.ipynb`** | **The main one.** 8 real frameworks downloaded live → spectra → **the band** and its membership tests. | Colab: Run All |
| `spectrum_corrected.ipynb` | Our 4 test structures on the block quotient graph, with every fix documented inline. Structures are embedded — no files needed. | Colab: Run All |
| `results.json` | Computed spectra for the 8 frameworks. Lets the band section run without recomputing. | — |

---

## `mof_band_analysis.ipynb` — start here

Steps 1–8 are the framework analysis: download 8 experimentally reported MOFs from the
RASPA2 library, build PBC-aware bond graphs, coarse-grain, and compute a multifractal
spectrum for each. **Steps 9–11 are the band analysis.**

### What the band is

Each framework produces a spectrum. The **width** of that spectrum, Δα, says how unevenly
connectivity is spread through the pore network. A **band** is the range a group of
frameworks shares — so a new framework can be tested for membership with no chemistry
required.

### The result

| Framework | Metal | Δα | |
|---|---|---|---|
| Co-MOF-74 | Co | 0.941 ± 0.054 | in band |
| ZIF-8 | Zn | 0.897 ± 0.077 | in band |
| Mg-MOF-74 | Mg | 0.857 ± 0.070 | in band |
| Zn-MOF-74 | Zn | 0.857 ± 0.070 | in band |
| HKUST-1 | Cu | 0.844 ± 0.063 | in band |
| Ni-MOF-74 | Ni | 0.835 ± 0.057 | in band |
| **IRMOF-1 (MOF-5)** | Zn | **0.375 ± 0.064** | **outside** |
| **UMCM-1** | Zn | **0.203 ± 0.028** | **outside** |

Six frameworks across **five different metals** and **two different binding chemistries**
share one band; two separate cleanly. The gap between the groups is **0.46**, about **four
times** the 0.105 noise floor. So the grouping is neither by metal nor by chemistry — it
tracks **pore-network architecture**.

### Two bands, only one of which works

Everything is tested by **holding a framework out** and rebuilding the band without it — a
curve trivially sits inside a band it helped define.

| Version | Result |
|---|---|
| **Δα band** (width only) | ✅ classifies **8/8 correctly** |
| **f(α) envelope** (whole curve) | ❌ **fails.** Held out, ZIF-8 (a member) scores **0.0%**; UMCM-1 (a non-member) scores **44.7%** |

The envelope fails because the two narrow curves are short arcs sitting *inside* the wide
group's α range but far below it in f(α) — so the test measures where a curve sits in α,
not how wide it is. **This is reported as a measured negative result**, not quietly dropped.

### Running it

- **Full run** — Colab, Run All. Downloads the structures and recomputes everything
  (~10 minutes). Nothing to upload.
- **Band only** — Steps 9–11 fall back to `results.json` if the earlier steps have not been
  run, so you can re-run the band analysis instantly. Keep `results.json` beside the
  notebook. The saved outputs you see were produced this way.

### Honest limits

- **Δα is not a stability or gas-uptake predictor.** The graph is unweighted — it does not
  know which element an atom is. Δα describes pore architecture only.
- **The four MOF-74 curves overlapping is not evidence.** They are the same graph, proved
  isomorphic in Step 7, so they must overlap. They are the reproducibility control, and
  what they measure is the 0.105 noise floor.
- **Δα is finite-size dependent** — effective widths at a stated graph size, not asymptotic
  exponents. The ranking survives because the bias runs the wrong way: the two narrowest
  spectra come from the two *largest* graphs.
