# Presentation Script — Start to Finish

**Audience assumption:** zero background. Every term is defined the first time it appears.
**Total time:** ~20 minutes talking + questions.
**What to have open:** `1_website/index.html` — one page, everything is on it — and one terminal in the project folder.

The sticky navigation bar at the top jumps to any section, so you never need to scroll hunting for something.

> **Before you start:** save `three.min.js` into the folder (see README) so the 3D works without internet. Open the page and scroll through it once beforehand, so nothing loads slowly in front of him.

---

## PART 0 — The one-sentence version (30 seconds)

> "We took the standard software the field uses to identify what a MOF is built from, showed exactly where it gets the chemistry wrong, fixed it, and then built on top of it the network analysis you asked for — including the influential nodes and the spectrum."

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

> "Look at how the decision is made. Three questions. Is the piece a single atom? Then it's a node. Otherwise — is every atom in it oxygen or hydrogen? Then it's a node. Otherwise it's a linker. **That's the entire chemical reasoning of the algorithm.** One test. That simplicity is why it's fast and predictable — and it's also where the problems come from."

---

## PART 3 — What we found wrong, and fixed (4 minutes)

**Show: Section 7 — Limitations of the Published Algorithm.**

> "We found four limitations in the published algorithm. Every number on this page is computed live from the real crystal files — nothing is typed in."

**Limitation 1 is the one to spend time on.**

> "The algorithm cuts every bond touching a metal. But a carboxylate group — the `–COO–` that binds the metal — attaches *through* its oxygen. So the cut falls **between the metal and the group that chemically belongs to it**. The carboxylate gets filed as linker, and the node is left as bare metal."

**Show the number:**

> "HKUST-1's node comes out as **`Cu2`** — two copper atoms and nothing else. But the actual building unit is a copper *paddlewheel*: two coppers plus four carboxylates. The software is reporting a species that doesn't exist in the crystal."

**Our fix:**

> "We extend the node across its coordinating groups — but only when the chemistry checks out. We verify the carbon really is a carboxylate carbon before absorbing it."

**Show: Section 8 — Before and After the Fixes, in 3D. Click through all four structures.**

| Structure | Published | With our fix | Change |
|---|---|---|---|
| HKUST-1 | `Cu2` | `Cu2 C4 O8` | **+12 atoms** |
| UiO-66 | `Zr6 O8 H4` | `Zr6 O32 C12 H4` | **+36 atoms** |
| MOF-5 | `Zn4 O` | `Zn4 O13 C6` | **+18 atoms** |
| ZIF-8 | `Zn` | `Zn` | **no change** |

**Say the ZIF-8 line out loud — do not skip it:**

> "ZIF-8 doesn't change, and that's the correct result. It has no carboxylate for the fix to act on. **A fix that changed ZIF-8 would be a fix that was wrong.** We show it precisely because it's the honest test."

*(Mention the other three limitations briefly: oxygen-only bridge chemistry; bonds being guessed so a borderline contact can flip the answer; rod clusters and solvent handled by silent convention. Say "these are documented with measured evidence on the page" and move on.)*

---

## PART 4 — What you asked us to do (5 minutes)

**Show: Section 10 — The Block Graph Must Be Periodic.**

> "You asked us to highlight the influential nodes, find the spectrum, and see whether a family of MOFs falls under one spectrum. We did all three. Two of them produced a result we didn't expect, so I want to show you those honestly."

### 4a. First we had to fix the graph itself

**Show Section 1, and click the "Naive simple graph" toggle.**

> "To do any of this you first turn the framework into a network — blocks are dots, bonds are lines. But a MOF is *infinite*, it repeats forever. If you build the network the straightforward way, you lose that, and blocks connected in several different directions collapse into one connection."

**Toggle to naive on UiO-66:**

> "Here's UiO-66 built the straightforward way. Its zirconium cluster reports as **6-connected**. The published crystallography says **12**. And in the first version we had, the whole thing collapsed into a **star** — one hub joined to everything else."

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

**Then the result:**

| Structure | Metal | α range |
|---|---|---|
| HKUST-1 | Cu | 1.84 – 1.87 |
| MOF-5 | Zn | 1.92 – 1.99 |
| ZIF-8 | Zn | 1.98 – 1.98 |
| **UiO-66** | **Zr** | **2.31 – 2.65** |

> "And this is the result you were looking for. **The zirconium framework sits in its own region — 2.31 to 2.65 — completely above every copper and zinc framework, which stop at 1.99.** The band test agrees: members of the same family land inside the band, and unrelated frameworks don't reach it at all."

---

## PART 6 — What we proved, and what we did not (2 minutes)

**Show: Section 5 — Roadmap.**

Say all of this. Don't let him find the gap himself.

> **"What we can claim:**
> - The published algorithm reports chemically incomplete nodes, and we can show exactly where and by how much.
> - Our fix recovers the correct building unit on three of four structures, and correctly leaves the fourth alone.
> - Our network is right — all four coordination numbers match published crystallography.
> - Ranking blocks inside a perfect crystal is mathematically empty, and we can show why.
> - The multifractal method now works, and it does separate the zirconium framework from the copper and zinc ones.
>
> **What we cannot claim yet:**
> - We have **one** zirconium structure. 'All Zr-MOFs fall in this band' cannot be established from a single example, no matter how clean the separation looks. That needs a few hundred MOFs grouped by metal — from CoRE MOF or QMOF. Our code already runs one file at a time, so running it over a database is a loop, not a rewrite. **That's the next step, and it's the thing standing between a demonstration and a result.**"

---

## The questions he will ask — and your answers

**"Isn't your node fix just the single-node algorithm that already exists?"**
> "It's close for carboxylates, and I should say that directly. The difference is that single-node is a *separate* algorithm with its own topology output, whereas we repair metal-oxo *in place* — which matters because MOFkey, the identifier, is built specifically on metal-oxo."

**"Why does ZIF-8 not change?"**
> "It has no carboxylate group, so the node-completion fix has nothing to act on. Its node was already chemically complete. We kept it in deliberately — a fix that changed it would be wrong."

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
> python3 code_08_proposed_fixes.py                  # before/after our fixes
> python3 code_09_network_analysis.py                # coordination numbers
> python3 code_10_multifractal_spectrum.py           # the spectrum
> ```
> "Every number on every page comes out of these. And the Python and the JavaScript in the browser were cross-checked — they agree on every value."

---

## Closing line

> "So: the algorithm the field uses has a specific, measurable chemistry problem, and we fixed it. On top of that we built the network analysis you asked for — and it gave us one result we expected, the spectrum separating the zirconium framework, and one we didn't, that influence can't be ranked inside a perfect crystal. The next step is scale: run it across a real database so the family claim can actually be tested."

---

## Quick reference — where each thing lives

| What | Where on the page |
|---|---|
| Problem statement | Section 1 — The Problem |
| The influential-nodes answer | Section 2 — The Question We Were Asked |
| The 7-stage algorithm + 3D | Section 6 — The Full Pipeline |
| Limitations + our fixes | Section 7 — Limitations |
| Before/after in 3D | Section 8 — Before and After the Fixes |
| Correct vs broken network | Section 10 — The Block Graph Must Be Periodic |
| Influential nodes highlighted in 3D | Section 11 — Which Blocks Are Influential (★ button) |
| The tie / degeneracy result | Section 11 — Which Blocks Are Influential |
| Defect simulation | Section 12 — Defect Simulation |
| The multifractal spectrum | Section 14 — The Multifractal Spectrum |
| The published box-growing method | Section 15 — Against the Published Method |
| Any source file | Section 16 — Every Line of Source Code, or click any filename anywhere |
| Roadmap and honest limits | Section 5 — Roadmap |
