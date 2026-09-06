# Presentation Script — Start to Finish

**Audience assumption:** zero background. Every term is defined the first time it appears.
**Total time:** ~20 minutes talking + questions.
**What to have open:** `1_website/index.html` — one page, everything is on it — and one terminal in the project folder.

The sticky navigation bar at the top jumps to any section, so you never need to scroll hunting for something.

> **Before you start:** save `three.min.js` into the folder (see README) so the 3D works without internet. Open the page and scroll through it once beforehand, so nothing loads slowly in front of him.

---

## PART 0 — The one-sentence version (30 seconds)

> "There are hundreds of thousands of MOFs and simulating each one takes hours, so we asked whether a **cheap structural descriptor** — computed from the framework's connectivity in seconds — can group them into useful families instead. We built a visualisation of how a MOF is decomposed into building blocks, then computed multifractal spectra for 77 frameworks and tested what those spectra actually mean."

Then stop and go to Part 1. Don't front-load detail.

---

## PART 1 — What is the problem? (2 minutes)

**Show: Section 1 — The Problem.**

Say this, in this order:

1. **What a MOF is.** "A metal–organic framework is a crystal built like scaffolding. There are metal clusters — we call them **nodes** — and organic molecules connecting them — **linkers**. Change the node or the linker and you get a different material with different pore size, stability, and behaviour."

2. **Why identification matters.** "So if someone hands you a MOF structure file, the first question is: *what is it built from?* Every downstream use depends on that answer — database search, similarity matching, machine learning, designing new MOFs. If the software reports the wrong building block, everything built on top of it is reasoning about a material that doesn't exist."

3. **The complication that shapes everything.** *(Point at the blue box.)* "A crystal structure file — a `.cif` — contains where the atoms are, and nothing else. **It contains no bonds at all.** The format has no field for them. So every bond the software uses is *guessed* from how close atoms are. That single fact causes several of the problems we found."

**If he asks "so what does the existing software do?"** — that's your cue for Part 2.

---

## PART 2 — The existing method, and how it works (4 minutes)

**Show: Section 6 — The Full Pipeline. Step through the modules as you talk.**

> "The standard tool is MOFid, from the Snurr group at Northwestern. It's a seven-stage pipeline. We reimplemented all of it in Python so we could see inside it — and this page walks through it stage by stage, with the real code on the left and a live 3D model on the right."

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

**Show: Section 3 — Why This Path.**

> "The obvious question is why we're attacking a chemistry problem with network theory. Here's the reasoning, and it's short."

> "A MOF isn't a molecule — it's a repeating framework. What makes one MOF different from another isn't only *which* atoms it has, it's **how they're wired together**. And wiring is exactly what a graph describes: collapse each building block to a point, each bond between blocks to a line, and you're left with pure connectivity."

> "That matters because the properties follow the wiring. Gas moves through the pore network, and the pore network **is** the empty space left by that wiring. So describing the connectivity describes what the material can do."

**The scale argument — this is the one that justifies the whole project:**

> "A gas-uptake simulation takes **hours** per structure. There are **hundreds of thousands** of MOFs. You cannot screen them all. A graph descriptor takes **seconds**. If a cheap structural number can narrow a hundred thousand candidates down to a few hundred worth simulating properly — that's the value. We're not replacing simulation. We're deciding what to simulate."

**Then explain the spectrum in plain terms — do not start with equations.**

> "Ask a simple question: how much network is near a given block? Draw a ball of radius r around it and count what's inside. Do that for every important block and you get a set of growth curves."

> "If the framework were perfectly uniform, every block would grow at the same rate and one number would describe the whole thing. Real frameworks aren't uniform — some regions are tightly tied, others open into big voids. So you need a **distribution** of growth rates, and that distribution is the spectrum."

**Show the table on screen and read only the middle two rows:**

> "α is how fast the network grows around one block. **Δα, the width, is how varied the framework is** — narrow means uniform, wide means a mix of tight and open regions. That single number is the fingerprint, and it's what makes a band possible."

**If asked "isn't that throwing away the chemistry?" — answer immediately, don't defend:**

> "Yes, deliberately. The graph doesn't know which element an atom is. That's a real limitation and we say so on the page. It's also the point: whatever survives that stripping is **pure architecture**, and architecture transfers across chemistries in a way an element-specific descriptor can't."

---

## PART 4 — What you asked us to do (5 minutes)

**Show: Section 10 — The Block Graph Must Be Periodic.**

> "You asked us to highlight the influential nodes, find the spectrum, and see whether a family of MOFs falls under one spectrum. We did all three. Two of them produced a result we didn't expect, so I want to show you those honestly."

### 4a. First we had to fix the graph itself

**Show Section 1, and click the "Naive simple graph" toggle.**

> "To do any of this you first turn the framework into a network — blocks are dots, bonds are lines. But a MOF is *infinite*, it repeats forever. If you build the network the straightforward way, you lose that, and blocks connected in several different directions collapse into one connection."

**Toggle to naive on UiO-66:**

> "Here's UiO-66 built the straightforward way. Its zirconium cluster reports as **1-connected**. The published crystallography says **12**. Almost the entire coordination environment disappears. And in the first version we had, the whole thing collapsed into a **star** — one hub joined to everything else."

**Toggle back to periodic:**

> "Built correctly — carrying the repeat direction on every connection — we get 12. And all four structures now match published crystallography exactly."

| Structure | We compute | Published | Net |
|---|---|---|---|
| HKUST-1 | 4-connected | 4 | `tbo` |
| MOF-5 | 6 | 6 | `pcu` |
| ZIF-8 | 4 | 4 | `sod` |
| UiO-66 | **12** | 12 | `fcu` |

> "That table is our proof the decomposition is right. These aren't our numbers — they're the numbers the field already published, and we reproduce all four."

### 4b. The influential nodes — and an unexpected result

**Show Section 2, then the ★ Highlight button in Section 1.**

> "You asked for the influential nodes — the ones with highest degree. We implemented it. Here they are highlighted in the actual 3D crystal."

**Click ★ Highlight the highest-degree blocks.**

> "Now look at what happened. **Six blocks lit up at once**, all with exactly the same degree. And that's not a coincidence — in a perfect crystal, every copper paddlewheel is *identical* to every other one by symmetry. There is no 'most influential' one."

**Show the tie table in Section 2:**

| Structure | Blocks | Distinct degree values | Tied at max |
|---|---|---|---|
| HKUST-1 | 14 | **2** | 6 of 14 |
| MOF-5 | 32 | **2** | 8 of 32 |
| ZIF-8 | 36 | **2** | 12 of 36 |

> "Every structure has only **two** degree values — one for nodes, one for linkers. So a 'top 12 most influential' list isn't discovering anything; it's sorting tied values, and which ones come out on top depends only on the order the atoms happened to be numbered in the file."

**Then immediately give the positive half — this is important, don't leave it on a negative:**

> "But the *number itself* is the most valuable thing in the analysis. A block's degree **is its coordination number** — 4-connected, 6-connected, 12-connected. That's the number reticular chemistry is organised around, because it determines which net can form at all. So the ranking is empty, but the measurement is exactly what validates our decomposition and identifies the topology. **We computed what you asked for, and found its value is as a descriptor, not as a ranking.**"

### 4c. Where influence becomes real

**Show Section 3, click "Remove one linker".**

> "Symmetry is what flattens it. Break the symmetry and influence becomes measurable. So we simulate a **missing-linker defect** — which is real MOF chemistry, UiO-66 is famous for tolerating them."

```
HKUST-1   distinct centrality values  2 → 4      λ₂ 1.44 → 1.19
ZIF-8     distinct centrality values  2 → 10     λ₂ 0.35 → 0.30
```

> "Now the blocks are genuinely different from each other, so ranking means something. And λ₂ — that's a number measuring how hard the framework is to pull apart — **drops**, which quantifies how much that one missing linker weakened the structure. That turns 'which node is influential' into 'which node costs the most when you remove it', which is a question with a physical answer."

---

## PART 5 — The spectrum (4 minutes)

**Show: Section 14 — The Multifractal Spectrum.**

> "Then the spectrum. My teammate implemented the method you described — it's called influential-node multifractal analysis."

**Explain it simply:**

> "You cover the network with 'boxes' of increasing size, and measure how the box sizes seen by the influential nodes grow as you zoom out. If the framework were uniform you'd get a single number. Because it isn't, you get a **curve** — and the shape and width of that curve is a fingerprint of how connectivity is spread through the material."

**Be straight about the state it was in:**

> "The method was right, but the first implementation returned nothing usable for half our structures, and we found six specific reasons. The main one: the spectrum was being computed on a network containing **only** the influential nodes. But in a MOF, the high-degree blocks are the metal clusters — **and metal clusters are never bonded to each other**, they connect *through* linkers. So that network had **zero connections**. No connections means no distances, which means no spectrum. We measured it: zero edges for HKUST-1 and for ZIF-8."

*(The full six-defect table is on screen — point at it, don't read it all.)*

**Then the result — and this is where you have to be careful and precise.**

**Show: Section 16 — The Band.**

> "We ran this across **77 frameworks**. Two things came out of it, and I want to give you both."

**First, the good part:**

> "All 77 spectra are proper inverted parabolas peaking at q equals zero — which is what a multifractal spectrum has to look like. Getting there took a correction I'll mention in a second. And they land in a **tight band**: Δα from 1.11 to 1.25 across the interquartile range, with the asymmetry negative in **every single one**. That's a consistent family signature."

**The correction — say it before he asks:**

> "Our first spectra weren't parabolic at all, they just sloped downhill. The cause was one line. The paper defines the mass exponent as a **ratio** — that's a fit through the origin. Our code used a least-squares **slope**, which has a free intercept. At q equals zero every term becomes one, so the partition function is just the *count* of nodes — identical at every radius. A flat line has slope zero, so it forced the peak of the spectrum to zero and deleted it. One branch fixed it, and all 77 became parabolic."

**Now the hard part — do not let him find this himself:**

> "But I have to tell you what the band **doesn't** mean. Δα correlates with pore diameter at minus 0.50, which looks like a real structural result. It isn't. When we control for graph size, that correlation collapses to **plus 0.10** — it vanishes. Meanwhile graph size *survives* controlling for pore diameter, at **plus 0.62**. In a linear model, graph size alone gives R-squared 0.53; adding pore diameter takes it to 0.54. **Pore size buys us half a percent.**"

> "So what Δα is mostly tracking is **how many atoms are in the supercell** — and that's set by two parameters in our own config file, not by chemistry. That's the finite-size effect the method is known to have, and on 77 structures we could finally measure it."

---

## PART 6 — What we proved, and what we did not (2 minutes)

**Show: Section 6 — Roadmap.**

Say all of this. Don't let him find the gap himself.

> **"What we can claim:**
> - The decomposition is visualised end to end and runs live on any structure you hand it.
> - Our network is right — all four coordination numbers match published crystallography, including UiO-66 at 12 where the naive construction gives 6.
> - Ranking blocks inside a perfect crystal is mathematically empty, and we can show why. Introduce a defect and it becomes measurable — λ₂ drops from 1.44 to 1.19 for one missing linker.
> - The multifractal spectrum is now computed to the paper's definition, and all 77 frameworks give proper parabolas.
> - Those 77 share a tight, well-defined band.
>
> **What we cannot claim:**
> - That the band means anything chemical **yet**. It's confounded by graph size, and we've quantified exactly how badly. Reporting that is the result — a band built on an uncontrolled size effect wouldn't survive the first person who checked it.
> - Anything about different metals. Our 77 structures all have Zn₄O nodes, so the set is single-metal. And they're hypothetical MOFs — computer-generated, never synthesised. We requested the experimental database and the server returned these; nothing was checking, and now it is.
>
> **The next steps are concrete, not open research:**
> - Compare only frameworks at comparable graph size, so the confound is held fixed.
> - Or normalise the fit window per structure so Δα stops growing with the graph — then re-test.
> - Then run it on a set with real metal diversity."

---

## The questions he will ask — and your answers

**"What does a graph have to do with a MOF?"**
> "A MOF is a repeating framework, and what distinguishes one from another is how the blocks are wired together. Gas moves through the pore network, and the pore network is the empty space that wiring leaves behind. So the connectivity *is* the thing that determines behaviour — and connectivity is what a graph describes."

**"Why not just simulate them?"**
> "Hours per structure, hundreds of thousands of structures. We're not replacing simulation — we're trying to decide which few hundred are worth simulating."

**"Isn't an unweighted graph throwing away the chemistry?"**
> "Yes, deliberately, and it's a real limitation we state on the page. It's also the point — whatever survives is pure architecture, which transfers across chemistries in a way an element-specific descriptor can't."

**"Does Δα predict gas uptake?"**
> "No, and we never claim it does. Nothing here computes adsorption. Δα describes pore-network architecture only."

**"Are those InChIKeys real?"**
> "No, and it's labelled in the code and on the page. Real InChI needs a separate cheminformatics library. The metal symbols, the format, and the topology field are real; the linker hash is a clearly-marked placeholder."

**"Did you run Systre?"**
> "No. Systre is an external Java tool. We write a genuine `.cgd` file it could read, but we don't run it. The topology names we quote are the published ones for these materials."

**"Why do UiO-66 and MOF-5 get the same linker key?"**
> "Because they genuinely have the same linker — both are terephthalate. That's correct behaviour, not a collision."

**"How do I know any of this is right?"**
> Open a terminal:
> ```
> python3 code_00_pipeline_driver.py HKUST-1.cif     # the full pipeline
> python3 code_09_network_analysis.py                # coordination numbers
> python3 code_10_multifractal_spectrum.py           # the spectrum
> ```
> "Every number on every page comes out of these. And the Python and the JavaScript in the browser were cross-checked — they agree on every value."

---

## Closing line

> "So: we asked whether structure alone can group MOFs cheaply enough to be useful at database scale. The machinery now works correctly — the spectra are proper parabolas, the network reproduces published crystallography, and 77 frameworks land in a tight band. Two of the findings weren't what we expected: influence can't be ranked inside a perfect crystal, and the band we found is currently driven by graph size rather than chemistry. We measured both rather than presenting around them. The next steps are specific — control for graph size, then test against a set with real metal diversity."

---

## Quick reference — where each thing lives

| What | Where on the page |
|---|---|
| Problem statement | Section 1 — The Problem |
| The influential-nodes answer | Section 2 — The Question We Were Asked |
| **Why a graph at all** | **Section 3 — Why This Path** |
| What we built | Section 4 — Everything We Built |
| The pipeline, visualised | Section 7 — The Full Pipeline |
| Run it on any structure | Section 8 — Interactive Pipeline |
| Correct vs broken network | Section 10 — The Block Graph Must Be Periodic |
| The tie / degeneracy result | Section 11 — Which Blocks Are Influential |
| Defect simulation | Section 12 — Defect Simulation |
| The multifractal spectrum | Section 14 — The Multifractal Spectrum |
| **The band, and the confound** | **Section 16 — The Band** |
| Any source file | Section 17, or click any filename |
| Roadmap and honest limits | Section 6 — Roadmap |
