# Presentation Script — Start to Finish

**Audience assumption:** zero background. Every term is defined the first time it appears.
**Total time:** ~20 minutes talking + questions.
**What to have open:** the project site — a ten-page portal, not one long page. Start on
`index.html` (Overview) and move forward through `methodology.html`, `decomposition.html`,
`network.html`, `spectrum.html`, `results.html` as you talk; the nav bar at the top jumps to
any page directly. One terminal in `2_python/` for the "prove it" moment.

> **Before you start:** confirm `1_website/three.min.js` is present (see README) so the 3D
> views work with no internet. Open the site and click through it once beforehand so nothing
> loads slowly in front of the panel. If you can, run `python 1_website/_build/build_site.py`
> and `cd 1_website/tests && npm test` the morning of, so you know every page is current.

---

## PART 0 — The one-sentence version (30 seconds)

> "There are hundreds of thousands of MOFs and simulating each one takes hours, so we asked
> whether a **cheap structural descriptor** — computed from the framework's connectivity in
> seconds — can group them into useful families instead. We built the pipeline correctly,
> ran it on 138 real and hypothetical frameworks, and found a genuine negative result: the
> descriptor the published method proposes does not converge as the analysed graph grows,
> which we can show directly, on the correct graph, on the complete data. That negative
> result — not a positive band — is the headline finding."

Then stop and go to Part 1. Don't front-load detail.

---

## PART 1 — What is the problem? (2 minutes)

**Show: `index.html` — the Overview page.**

Say this, in this order:

1. **What a MOF is.** "A metal–organic framework is a crystal built like scaffolding. There are metal clusters — we call them **nodes** — and organic molecules connecting them — **linkers**. Change the node or the linker and you get a different material with different pore size, stability, and behaviour."

2. **Why identification matters.** "So if someone hands you a MOF structure file, the first question is: *what is it built from?* Every downstream use depends on that answer — database search, similarity matching, machine learning, designing new MOFs. If the software reports the wrong building block, everything built on top of it is reasoning about a material that doesn't exist."

3. **The complication that shapes everything.** "A crystal structure file — a `.cif` — contains where the atoms are, and nothing else. **It contains no bonds at all.** The format has no field for them. So every bond the software uses is *inferred* from how close atoms are. That single fact causes several of the problems we found."

**If he asks "so what does the existing software do?"** — that's your cue for Part 2.

---

## PART 2 — The existing method, and how it works (4 minutes)

**Show: `decomposition.html` — the pipeline walkthrough. Step through the module tabs as you talk.**

> "The standard tool is MOFid, from the Snurr group at Northwestern. It's a seven-stage pipeline. We reimplemented all of it in Python so we could see inside it — this page walks through it stage by stage, with the real code on the left and a live 3D model on the right."

Click each tab and say one line:

| Tab | One line to say |
|---|---|
| **1 CIF Input** | "Read the file. Atoms and the box they repeat in. Notice — **no bonds on screen**. That's correct, not a bug." |
| **2 Bond Assignment** | "Now bonds appear. Every one of them was *computed* by distance, not read." |
| **3 Element Classification** | "Each atom is labelled metal or non-metal. It's a lookup table of 23 non-metals; anything else is called a metal." |
| **4a Metal-Oxo** ★ | "This is the algorithm we studied. **Cut every bond that touches a metal, see what falls off, and label the pieces.**" |
| 4b / 4c | "Two later variants that cut in different places." |
| **5 Centroid** | "Every building block shrinks to a single point." |
| **6 Systre / 7 MOFid** | "The points become an abstract network, which gets a name — like `tbo` or `fcu` — and the whole thing becomes an identifier string." |

**The key moment — click Module 4a, step "4 · Classify fragments".**

> "Look at how the decision is made. Three questions. Is the piece a single atom? Then it's a node. Otherwise — is every atom in it oxygen or hydrogen? Then it's a node. Otherwise it's a linker. **That's the entire chemical reasoning of the algorithm.** One test. That simplicity is why it's fast enough to run across a whole database — and why it's worth being able to see exactly what it decided."

---

## PART 3 — Why a graph? (4 minutes)

**Show: `methodology.html` — the "Why This Path" section.**

> "The obvious question is why we're attacking a chemistry problem with network theory. Here's the reasoning, and it's short."

> "A MOF isn't a molecule — it's a repeating framework. What makes one MOF different from another isn't only *which* atoms it has, it's **how they're wired together**. And wiring is exactly what a graph describes: collapse each building block to a point, each bond between blocks to a line, and you're left with pure connectivity."

> "That matters because the properties follow the wiring. Gas moves through the pore network, and the pore network **is** the empty space left by that wiring. So describing the connectivity describes what the material can do."

**The scale argument — this is the one that justifies the whole project:**

> "A gas-uptake simulation takes **hours** per structure. There are **hundreds of thousands** of MOFs. You cannot screen them all. A graph descriptor takes **seconds**. If a cheap structural number can narrow a hundred thousand candidates down to a few hundred worth simulating properly — that's the value. We're not replacing simulation. We're deciding what to simulate."

**Then explain the spectrum in plain terms — do not start with equations.**

> "Ask a simple question: how much network is near a given block? Draw a ball of radius r around it and count what's inside. Do that for every important block and you get a set of growth curves."

> "If the framework were perfectly uniform, every block would grow at the same rate and one number would describe the whole thing. Real frameworks aren't uniform — some regions are tightly tied, others open into big voids. So you need a **distribution** of growth rates, and that distribution is the spectrum."

> "α is how fast the network grows around one block. **Δα, the width, is how varied the framework is** — narrow means uniform, wide means a mix of tight and open regions. That single number was intended as the fingerprint, and it's what a 'band' is a range of. Whether it actually behaves as a fingerprint is exactly what Parts 5 and 6 are about."

**If asked "isn't that throwing away the chemistry?" — answer immediately, don't defend:**

> "Yes, deliberately. The graph doesn't know which element an atom is. That's a real limitation and we say so on the page. It's also the point: whatever survives that stripping is **pure architecture**, and architecture transfers across chemistries in a way an element-specific descriptor can't."

---

## PART 4 — What you asked us to do (5 minutes)

**Show: `network.html`.**

> "You asked us to highlight the influential nodes, find the spectrum, and see whether a family of MOFs falls under one spectrum. We did all three. All three produced a result we didn't expect, so I want to show you them honestly, in order."

### 4a. First we had to fix the graph itself

**On `network.html`, click the "Naive simple graph" toggle.**

> "To do any of this you first turn the framework into a network — blocks are dots, bonds are lines. But a MOF is *infinite*, it repeats forever. If you build the network the straightforward way, you lose that, and blocks connected in several different directions collapse into one connection."

**Toggle to naive on UiO-66:**

> "Here's UiO-66 built the straightforward way. Its zirconium cluster reports as **1-connected**. The published crystallography says **12**. Almost the entire coordination environment disappears. And in the first version we had, the whole thing collapsed into a **star** — one hub joined to everything else."

**Toggle back to "Labelled quotient graph (correct)":**

> "Built correctly — carrying the repeat direction on every connection — we get 12. And all four structures now match published crystallography exactly."

| Structure | We compute | Published | Net |
|---|---|---|---|
| HKUST-1 | 4-connected | 4 | `tbo` |
| MOF-5 | 6 | 6 | `pcu` |
| ZIF-8 | 4 | 4 | `sod` |
| UiO-66 | **12** | 12 | `fcu` |

> "That table is our proof the decomposition is right. These aren't our numbers — they're the numbers the field already published, and we reproduce all four. This check is also now automated: it runs in CI on every push, so it can never silently regress."

### 4b. The influential nodes — and an unexpected result

**Still on `network.html`, click "★ Highlight the highest-degree blocks".**

> "You asked for the influential nodes — the ones with highest degree. We implemented it. Here they are highlighted in the actual 3D crystal."

> "Now look at what happened. Every copper paddlewheel lit up at once, all with exactly the same degree. And that's not a coincidence — in a perfect crystal, every copper paddlewheel is *identical* to every other one by symmetry. There is no 'most influential' one."

| Structure | Blocks | Distinct degree values | Tied at max |
|---|---|---|---|
| HKUST-1 | 14 | **2** | 6 of 14 |
| MOF-5 | 32 | **2** | 8 of 32 |
| ZIF-8 | 36 | **2** | 12 of 36 |

> "Every structure has only **two** degree values — one for nodes, one for linkers. So a 'top-k most influential' list isn't discovering anything; it's sorting tied values, and which ones come out on top depends only on the order the atoms happened to be numbered in the file."

**Then immediately give the positive half — this is important, don't leave it on a negative:**

> "But the *number itself* is the most valuable thing in the analysis. A block's degree **is its coordination number** — 4-connected, 6-connected, 12-connected. That's the number reticular chemistry is organised around, because it determines which net can form at all. So the ranking is empty, but the measurement is exactly what validates our decomposition and identifies the topology."

### 4c. Where influence becomes real

**Still on `network.html`, click "Remove one linker (simulate a defect)".**

> "Symmetry is what flattens it. Break the symmetry and influence becomes measurable. So we simulate a **missing-linker defect** — which is real MOF chemistry, UiO-66 is famous for tolerating them."

```
HKUST-1   distinct centrality values  2 → 4      λ₂ 1.44 → 1.19
ZIF-8     distinct centrality values  2 → 10     λ₂ 0.35 → 0.30
```

> "Now the blocks are genuinely different from each other, so ranking means something. And λ₂ — that's a number measuring how hard the framework is to pull apart — **drops**, which quantifies how much that one missing linker weakened the structure. That turns 'which node is influential' into 'which node costs the most when you remove it', which is a question with a physical answer."

---

## PART 5 — The spectrum, the withdrawal, and the corrected result (7 minutes)

This is the part that changed most since the last review. Slow down here.

**Show: `spectrum.html` — the method.**

> "My teammate implemented the method you described — influential-node multifractal analysis. You cover the network with 'boxes' of increasing size and measure how the box sizes seen by the influential nodes grow as you zoom out. A uniform framework gives one number; a real one gives a **curve**, and the shape and width of that curve is a fingerprint of how connectivity is spread through the material."

> "The first implementation had a specific, fixable bug: the paper defines the mass exponent as a ratio — a fit **through the origin**. Our code used a free-intercept least-squares slope instead. At q equals zero every term becomes one, so the partition function is the same at every radius; a flat line has slope zero, which forced the peak of the spectrum to zero and deleted it. One branch fixed it, and every spectrum we've computed since is a proper inverted parabola peaking at q = 0."

**Now the graph question — a panel is very likely to ask this, so state it before being asked:**

> "There's a second, separate question: which graph do you actually run this on? There are four candidates — the unit cell alone, the atomic supercell, the coarse-grained unit cell alone, or the coarse-grained supercell. We answer this explicitly on the Methodology page now. The right answer is the coarse-grained supercell: decompose the unit cell into blocks first, then replicate *that* small block graph using the lattice translation already on each edge. No atoms are ever built during replication, so it's cheap to reach a real diameter. The unit cell alone is too small — diameter about 2, no range of radii to fit a power law over. The atomic graph mixes two length scales, molecular and framework, into one fit."

> "We found out the hard way that our own two published bands — 77 hypothetical frameworks, 61 real ones — were computed on the **atomic** graph, not the coarse-grained one our own method description calls for."

**Show: `results.html` — the withdrawal notice at the top of the Band section.**

> "So we redid the finite-size behaviour properly. We grew the coarse-grained supercell of four demonstration frameworks — different nets, tbo, pcu, sod, fcu — out past diameter 30, on the correct graph this time. Δα never plateaus. It grows as roughly 0.7 to 0.9 times the log of the diameter, cleanly, on every net, at every range of the exponent q we tried, from ±10 down to ±2. **That is the headline result of this phase of the project: the published descriptor does not converge, and we can show it on the graph the method actually specifies, not just the wrong one.**"

**Then the scale of the correction:**

> "We didn't stop at four demonstration structures. We re-fetched both full datasets — all 77 hypothetical frameworks, all 61 real ones — and reran the analysis on the correct coarse-grained supercell graph, in full, not a sample. 72 of 77 and 55 of 61 produced a usable spectrum."

**Show: the grouped-spectra band figure on the Results page.**

> "Using the right graph fixes the graph. It does not fix the descriptor. Sorting each dataset into Narrow, Medium and Wide by Δα — the same split a teammate's separate run used — the class still correlates with coarse-grained node count at **r = +0.70, independently, on both datasets.** We checked nine categories per class — chemistry, graph features, degree, edges, clustering, assortativity, heterogeneity, connected components — and on both datasets, everything that differs between classes moves in lock-step with graph size. On the hMOF set specifically, two of the three classes are, in every category we can measure, the **same graph** — same metal, same net, same block count — differing only in which random box-covering trial happened to produce a slightly larger or smaller width."

---

## PART 6 — What we proved, and what we did not (3 minutes)

**Show: `team.html` — Implementation Progress.**

Say all of this. Don't let him find the gap himself.

> **"What we can claim:**
> - The decomposition is correct and visualised end to end, live on any structure you hand it.
> - Our network is right — all four coordination numbers match published crystallography, including UiO-66 at 12 where the naive construction gives 1. This check now runs automatically in CI.
> - Ranking blocks inside a perfect crystal is mathematically empty, and we can show why. Introduce a defect and it becomes measurable — λ₂ drops from 1.44 to 1.19 for one missing linker.
> - The multifractal spectrum is computed to the paper's exact definition, on the graph the method specifies.
> - We identified that the published descriptor, Δα, does not converge with supercell size — at any tested q range, on four different nets — and that this is a stronger, more useful result than the band we originally reported, because it rules out a whole approach rather than asserting one.
>
> **What we cannot claim:**
> - That Δα, as currently defined, is a property of a framework at all. It is a function of how large a graph happened to be analysed, and we have now shown that twice — on four demonstration structures, and again on the complete 77 plus 61 real datasets.
> - That either published band — the 77-framework or the 61-framework one — is a chemical or structural finding. Both are withdrawn, kept only for audit, with the reasons stated in full on the Results page and in `CLAUDE.md`.
>
> **The engineering is close to complete — about 88%; the scientific validation is not — about 35%, because the headline descriptor doesn't converge; overall, weighting that as a gate rather than an average, about 55%.** We report it that way on purpose: a single blended number would let 'we built a lot' stand in for 'we established something', and those are different claims.
>
> **The next steps are concrete, not open research:**
> - Either define a size-independent Δα — a fixed a-priori q range (narrowing q alone does not work, we checked), a different partition-function normalisation, or reporting the Δα(D) growth *slope* itself as the descriptor instead of the width. A capped check suggests the slope varies more across real structures than across the degenerate hypothetical set, which is a plausible direction, stated as a proposal, not a result.
> - Or retire Δα as the headline descriptor and say so, rather than patch around a number that has not been shown to mean what it was supposed to mean."

---

## Closing line

> "So: we asked whether structure alone can group MOFs cheaply enough to be useful at database scale. The machinery works correctly — the spectra are proper parabolas, the network reproduces published crystallography, and we know precisely which graph the method requires and why. What we found is that the descriptor itself, Δα, does not converge with the size of the analysed graph — not on four demonstration structures, and not on the complete 138-framework dataset, computed on the correct graph. That's a negative result about a published method, established carefully rather than asserted, and it's a stronger position than the band we originally thought we had. The next steps are specific: either fix the descriptor's definition, or replace it, and say clearly which."

---

## The questions he will ask — and your answers

**Read this section last, right before you go in. These are ordered roughly by how likely and how important they are.**

**"Which graph did you actually run the spectrum on — unit cell, supercell, coarse-grained unit cell, or coarse-grained supercell?"**
> "Coarse-grained supercell: decompose the unit cell into blocks, then replicate that small block graph using the lattice translation on each edge. It's on the Methodology page in full, as its own section, because it's exactly the kind of question a reviewer should ask and we didn't originally answer it in writing."

**"Why not build the atomic supercell and coarse-grain that afterward?"**
> "Because it wastes atoms you immediately throw away, and it caps how big a graph you can afford — you're limited by atom memory, not block memory. That's exactly what happened to both our own published bands and to a teammate's separate run: capped around diameter 8 to 12. Coarse-graining the unit cell first means replication is pure combinatorics, no atoms exist at that step, so we reach diameter 20 to 35 for a few hundred megabytes instead."

**"If you'd used the correct graph from the start, would the band have been fine?"**
> "No — and we checked that directly rather than assuming it. We redid both full datasets on the correct graph, and class still tracks graph size at r = +0.70 on both, independently. Using the right graph fixes the graph. It does not fix the descriptor."

**"So what is Δα actually measuring, if not chemistry?"**
> "On the evidence we have, mostly how large the analysed graph is. At extreme values of the distortion exponent q, the partition function is dominated by a single box, and the smallest possible box is one vertex — so the tail of the spectrum inherits a term that grows with graph size without bound. We can show that mechanism directly on four nets and it's consistent with everything we see on the full datasets."

**"Are the Narrow/Medium/Wide sub-bands real?"**
> "As chemistry, no. We checked nine categories — chemistry, graph size, degree statistics, edges, clustering, assortativity, heterogeneity, components — and on the hypothetical set, two of the three classes are the same graph in every category except the width itself. On the real set, everything that differs between classes differs because it's correlated with graph size, not because we've shown it matters on its own."

**"What would it take to fix this?"**
> "Two options, both concrete. One: define Δα a different way that doesn't inherit a size term — a fixed a-priori q range doesn't work, we tested that specifically; a different normalisation of the partition function might. Two: report the *slope* of Δα against log-diameter as the descriptor instead of a single width, since the slope is a well-defined property even where the width itself isn't. We have a first, capped look at whether that slope varies between frameworks — it does, more on real structures than on the degenerate hypothetical set — but we're presenting that as a proposal, not a finding."

**"What does a graph have to do with a MOF?"**
> "A MOF is a repeating framework, and what distinguishes one from another is how the blocks are wired together. Gas moves through the pore network, and the pore network is the empty space that wiring leaves behind. So the connectivity *is* the thing that determines behaviour — and connectivity is what a graph describes."

**"Why not just simulate them?"**
> "Hours per structure, hundreds of thousands of structures. We're not replacing simulation — we're trying to decide which few hundred are worth simulating."

**"Isn't an unweighted graph throwing away the chemistry?"**
> "Yes, deliberately, and it's a real limitation we state on the page. It's also the point — whatever survives is pure architecture, which transfers across chemistries in a way an element-specific descriptor can't."

**"Does Δα predict gas uptake?"**
> "No, and we never claim it does. Nothing here computes adsorption. Δα describes pore-network architecture only — and right now we can't even say it reliably describes that."

**"Did you run Systre?"**
> "No. Systre is an external Java tool we didn't have available. We write a genuine `.cgd` file it could read, but we don't run it. Where we need a net label for a real structure and don't have one from the published literature, we say so rather than guess — some of our real-MOF net assignments are stated as unavailable for exactly this reason."

**"Why do UiO-66 and MOF-5 get the same linker key?"**
> "Because they genuinely have the same linker — both are terephthalate. That's correct behaviour, not a collision."

**"How do I know any of this is right?"**
> Open a terminal:
> ```
> python3 code_00_pipeline_driver.py HKUST-1.cif        # the full pipeline
> python3 code_09_network_analysis.py                   # coordination numbers
> python3 code_12_converged_band.py                      # the convergence test
> python3 _ci_smoke_test.py                               # the same checks CI runs
> ```
> "Every number on every page comes out of these. The Python and the JavaScript in the browser were cross-checked and agree. And as of this review, GitHub Actions runs all nine JS test suites, a Python smoke test, and a check that the built site matches its source, on every push — so none of this can silently regress between now and the next review."

**"Why does the completion percentage look lower than last time?"**
> "Because we tested something we hadn't tested before — whether the descriptor converges at all — and it doesn't. That's not new bad news, it was always true of every number we'd published; we just hadn't measured it. We'd rather report 55% honestly, gated on the part that actually failed, than 85% averaged in a way that hides the failure."

---

## Quick reference — where each thing lives

| What | Where |
|---|---|
| Problem statement | `index.html` |
| Why a graph at all | `methodology.html#why` |
| **Which graph the spectrum uses, and why** | **`methodology.html#graph-choice`** |
| What we built, implementation map, roadmap | `methodology.html` |
| The pipeline, visualised, module by module | `decomposition.html` |
| Correct vs broken (periodic) network, the tie/degeneracy result, defect simulation | `network.html` |
| The multifractal method, the τ fix | `spectrum.html` |
| **The withdrawal, the corrected full-dataset band, sub-bands explained** | **`results.html`** |
| Completion percentages, re-derived honestly | `team.html` |
| Every source file, readable in the browser | `code.html` |
| Every term defined | `glossary.html` |
| The finite-size sweep and its numbers | `CLAUDE.md`, `2_python/code_12_converged_band.py` |
| The full correct band on both datasets | `2_python/code_17_full_correct_band.py`, `9_dataset/size_scaling/` |
