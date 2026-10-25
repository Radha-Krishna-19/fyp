# What changed from the original notebook

`mof_band_analysis.ipynb` is built directly on `mof_multi_block_spectrum_50plus.ipynb`.

**18 of your 20 cells are untouched.** The download, the CIF parsing, the PBC bond graph,
the coarse-graining, the box covering, the supercell logic, the validation steps — all
unchanged. Two cells were edited and seven appended.

| | Cells |
|---|---|
| Unchanged | 18 of 20 |
| Edited | 2 (cell 4, cell 12) |
| Appended | 7 (Steps 9–12) |

---

## Edit 1 — cell 12, `inmfa()` : the τ(q) definition

**This is the important one. It's why the spectra weren't parabolic.**

A multifractal spectrum `f(α)` has to be an **inverted parabola** peaking at `q = 0`, where
`f(α₀) = D₀`, the fractal dimension. Ours sloped downhill instead.

The paper defines the mass exponent as a **ratio**:

```
τ(q) = ln 𝒫_q(r) / ln(r/r_N)
```

Over several radii that is a straight-line fit **through the origin** — the relation
`𝒫_q ~ (r/r_N)^τ` has no prefactor, so there is no intercept term. The code did:

```python
slope, icept = np.polyfit(x, y, 1)
tau.append(slope)
```

which is `y = mx + c` — a **free intercept**. For most `q` the two barely differ, which is
why nothing looked broken. At `q = 0` they differ catastrophically:

- at `q = 0` every term is `pr_i⁰ = 1`, so `𝒫₀ = Σ 1 = |I|` — just the **count** of
  influential nodes
- the radius `r` has dropped out entirely, so **`ln 𝒫₀` is the same at every radius**
- a free-intercept fit through a flat line has **slope 0**, so `τ(0) = 0`
- therefore `f(α₀) = 0·α − 0 = **0**`

`f(α₀)` is supposed to *be* the peak. Pinning it to zero flattens the apex into the ground
and leaves a monotonically falling curve.

With the paper's ratio, `ln(r/r_N) < 0` (because `r < r_N`), so `τ(0) = ln|I| / negative`
is **negative**, and `f(α₀) = −τ(0) > 0` — the peak comes back.

**Verified**, identical data, only the definition swapped:

| τ definition | τ(0) | f(0) | peak at | parabola? |
|---|---|---|---|---|
| free-intercept slope | 0.0000 | 0.0000 | q = −4 | no |
| paper: `ln 𝒫_q / ln(r/r_N)` | −3.5028 | +3.5028 | **q = 0** | **yes** |

*(verification figures above are from a synthetic test graph. On the real 77-framework run: τ(0) = −2.5669, f(α₀) = +2.5669, and **77/77 peak at q = 0**.)*

Checked across the pre-fix `results.json`: **τ(0) = 0 in all 77 frameworks, and not one of
them peaked at q = 0.** After the fix, **all 77 peak at q = 0.**

**The change is one branch**, and both modes are kept so the correction can be shown:

```python
if tau_mode == "paper":                      # now the default
    t = float(np.sum(x * y) / np.sum(x * x))     # through the origin
else:
    t, icept = np.polyfit(x, y, 1)               # the old behaviour
```

Same cell, smaller fix: **α₀ is now taken where `f(α)` is maximum** (the paper's
definition) rather than assumed to be the `q = 0` index. With the τ fix those coincide, as
they should — but taking `argmax` makes the asymmetry metric `A` correct either way.

---

## Edit 2 — cell 4 : check what the server actually returned

`params = {"database": "CoREMOF 2019"}` is a **request**, not a guarantee. The cell printed
*"real CoRE MOF 2019 structures"*, but every structure that came back is named `hMOF-###` —
the **hypothetical MOF** database. Those are computer-generated candidates that have never
been synthesised.

Nothing was verifying the response, so the cell now counts the databases actually returned
and warns on a mismatch. It also reports the metal composition, because:

**all 77 have a Zn₄O node.** The set is effectively single-metal.

Two consequences for how we describe the work:

- nothing from this set may be called **"experimental"** or **"real"**
- **no cross-metal claims** — including the zirconium question

What the set *is* genuinely good for: one node type with many different linkers, which
makes it a clean same-node, varied-linker family.

*(If you want the experimental set, the fix is to check `m.database` on each record and
re-query. A real CoRE MOF set would also give actual metal diversity.)*

---

## Appended — Steps 9 to 12, the band

Your notebook computed the spectra but stopped before building a band. These add it.

**Step 9 — shape check.** Runs `inmfa()` both ways on the same graph and prints τ(0), f(0)
and where the peak lands, so the fix above is demonstrated rather than asserted.

**Step 10 — the band, and whether it means anything.** Builds the Δα band (interquartile
range across the 77 = **1.11 – 1.25**), then tests what Δα is actually tracking.

This is where a claim had to be withdrawn. Δα correlates with pore diameter, which looks
like a real structural result — but it does not survive controlling for graph size:

| Test | r |
|---|---|
| Δα vs pore diameter (LCD), raw | −0.497 |
| Δα vs LCD, **controlling for graph size** | **+0.101** — vanishes |
| Δα vs graph size, **controlling for LCD** | **+0.621** — survives |

Linear model: graph size alone gives R² = 0.533; adding pore diameter takes it to 0.538.
**Pore size buys +0.005.**

So Δα is mostly tracking **how many atoms are in the supercell** — and that is set by
`MIN_CELL_LENGTH` and the `MAX_ATOMS` cap, which are computational parameters, not
chemistry. This is the finite-size dependence your Step 7 already warned about, now
measured across a whole dataset instead of three structures.

On 8 frameworks the pore reading was plausible. On 77 it isn't supported.

**Step 11 — figures.** Six panels: the τ fix, the spectra, the band, and the confound shown
three ways.

**Step 12 — written conclusions**, including what is retracted and what would make the pore
question answerable:

1. compare only frameworks of **comparable graph size**, holding the confound fixed; or
2. **normalise the fit window** per structure so Δα stops growing with the graph, then
   re-test the correlation.

---

## Summary

| Change | Why |
|---|---|
| τ(q) fitted through the origin | matches the paper; restores the inverted parabola |
| α₀ taken at max f(α) | the paper's definition; makes `A` correct |
| verify returned database + metals | the data is hMOF and single-metal, not what was claimed |
| Steps 9–12 | build the band, and test what it actually measures |

Nothing was removed and no results were transcribed. `results.json` is the corrected run —
all 77 spectra peak at q = 0. The size-confound finding is independent of the τ fix and is
stronger on the corrected data.
