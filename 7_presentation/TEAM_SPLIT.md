# Panel Review — Team Split & Speaking Script

**23CSE498 Project Phase 2 · Panel Review 1**
**Guide: Dr. T. Ramraj**, M.E, Ph.D — Assistant Professor (Sl.Gd.), Dept. of CSE, School of Computing, Coimbatore
Total: **20 minutes presentation + 10 minutes questions**

Audience is mixed — **CSE faculty** (who will probe the algorithms, complexity and
engineering) and **Chemistry faculty** (who will probe whether the chemistry is real and
whether the claims are defensible). Every section below flags which audience the material
is aimed at.

---

## Speaking order at a glance

| # | Speaker | Slides | Time | Focus |
|---|---|---|---|---|
| 1 | **P. M. Radha Krishna** (CB.SC.U4CSE23134) | Title, 0, 1 | 5 min | Problem, motivation, methodology |
| 2 | **P. Kshitij Varma** (CB.SC.U4CSE23122) | 1b | 3 min | The mathematical model |
| 3 | **G. Rohith Abhinav** (CB.SC.U4CSE23141) | 2, 3b | 4 min | Implementation status + the platform |
| 4 | **J. Keerthi Sree** | 2b | 4 min | Results, validation, the band |
| 5 | **Isha** | 3, 5 | 4 min | Design decisions, the τ defect, next steps |
| — | All | 4, references | — | MOOCs, Q&A |

> **Rule for everyone:** if you do not know an answer, say *"I don't know — that's
> [name]'s section"* or *"we haven't tested that yet."* Do **not** invent a number. The
> whole project is built on reporting what we actually measured, and one made-up figure
> undoes that.

---

## 1 · P. M. Radha Krishna — Problem & Methodology (5 min)

**Slides: Title, 0 (Problem Context), 1 (Methodology)**

### Opening (30 sec)

> "Good morning. Our project asks whether we can predict something useful about a
> metal–organic framework **from its structure alone**, without running an expensive
> simulation."

### Slide 0 — the problem (2 min) · *aimed at both audiences*

> "MOFs are crystals built by joining metal clusters — we call them **nodes** — to organic
> molecules called **linkers**. They're extremely porous; a single gram can have the surface
> area of a football pitch. That makes them candidates for gas storage, carbon capture and
> separation."

> "The problem is scale. There are **hundreds of thousands** of known and hypothetical MOFs.
> Evaluating one properly — a GCMC adsorption simulation — takes **hours**. You cannot screen
> the design space that way."

**The key sentence — say it slowly:**

> "So our question is: can a **structural descriptor**, computed in **seconds** from just the
> connectivity, group MOFs into families well enough to decide **which ones are worth
> simulating**? We're not replacing simulation. We're building the filter in front of it."

### Slide 1 — methodology (2.5 min) · *aimed at CSE*

Walk down the flowchart. One sentence per box.

> "A CIF file gives us the unit cell and atom positions — and, importantly, **no bonds**.
> Bonds have to be inferred from distance, using covalent radii, and it has to be done
> **periodically**, because a crystal repeats forever."

> "Then we split the structure into building blocks using the published MOFid metal-oxo
> algorithm. We use it **unmodified** — this part of the project is a visualisation of the
> standard method, not a change to it."

> "Then each block becomes a **vertex** and each bond between blocks becomes an **edge**. That
> gives us a graph, and we compute a multifractal spectrum on it."

**Hand-off:** *"Kshitij will take you through the mathematics."*

---

## 2 · P. Kshitij Varma — Mathematical Model (3 min)

**Slide: 1b** · *aimed at CSE, but keep it interpretable for Chemistry*

Do **not** read the equations aloud symbol by symbol. Explain what each step is *doing*.

> "The descriptor is built in four steps."

> "**Step one** — pick a block and ask: how much network is within *r* steps of it? Call that
> count M-i-of-r, and divide by the total network size. That's a probability measure."

> "**Step two** — sum those measures raised to a power *q*. Varying *q* is a zoom control:
> large positive *q* emphasises the densest regions, negative *q* emphasises the sparsest."

> "**Step three** — the mass exponent tau. It's the log of that sum divided by the log of the
> radius ratio. This is the definition **straight from the paper**, and it matters — I'll come
> back to why."

> "**Step four** — a Legendre transform gives alpha and f-of-alpha, which is the spectrum."

**Then the interpretation table — this is the part Chemistry faculty will care about:**

> "Alpha is how fast the network grows around one block — a **local dimension**. f-of-alpha is
> how much of the framework shares that growth rate. And **delta-alpha, the width, is how
> varied the framework is** — narrow means uniform pores throughout, wide means a mix of tight
> and open regions."

**The correctness test — flag it, because Isha will use it:**

> "One thing worth noting: a multifractal spectrum **must** be an inverted parabola peaking at
> q equals zero. That's not a preference, it's a mathematical property. We used it as a test,
> and it caught a real bug in our own code."

**Hand-off:** *"Rohith will cover what's built."*

---

## 3 · G. Rohith Abhinav — Implementation & Platform (4 min)

**Slides: 2 (Implementation), 3b (Platform)** · *aimed at CSE*

### Slide 2 — status (2 min)

Don't read every row. Group them.

> "Roughly 60% complete. The **entire pipeline is functional** — ingestion, decomposition,
> topology export, the network layer, and both spectrum methods. The 77-framework study runs
> end to end, and the interactive platform is integrated."

> "Two things are still in progress, and they're both about **validating the result** rather
> than building machinery: removing a confound we found, and getting a better dataset."

**The verification line — say this, it's what separates us from a demo:**

> "We implemented everything **twice** — once in Python as the reference, once in JavaScript so
> it runs in the browser. The two agree on every number we report. That's not duplicated
> effort, it's the check: two independent implementations agreeing means neither has a silent
> bug. We also have automated test suites for the decomposition, the network layer, the band
> analysis and the site structure."

### Slide 3b — the platform (2 min)

If a laptop is available, **show it live**. Otherwise describe it.

> "The deliverable is an 18-section technical site. It's a single HTML file — no server, no
> install. You can **upload any CIF file and watch the full pipeline run in your browser**."

> "Each pipeline stage shows the real source code beside a live 3D model of the structure at
> that point. And Section 10 is a **graph-theory primer** — it defines every term we use,
> vertex, degree, quotient graph, Laplacian, before any of them appear in an analysis."

**If you demo, do exactly this and nothing more:**
1. Section 7 — step through two modules of the pipeline
2. Section 11 — toggle naive vs periodic graph, **watch UiO-66 change from 6 to 12**
3. Section 17 — the band across 77 frameworks

**Hand-off:** *"Keerthi will present the results."*

---

## 4 · J. Keerthi Sree — Results & Validation (4 min)

**Slide: 2b** · *aimed at Chemistry primarily*

### Validation first (1.5 min) — this earns the right to everything after

> "Before any result, we had to prove our graph is correct. Coordination number is published
> for these materials, so it's an independent ground truth."

> "All four match. And **UiO-66 is the one that matters** — its zirconium cluster is
> 12-connected. If you build the graph without accounting for periodicity, it reports as
> **6**. Half the chemistry disappears. Getting 12 is how we know the construction is right."

### The influence finding (1 min)

> "We were asked to find the most influential nodes. What we found is that **in a perfect
> crystal, you can't** — every metal cluster is symmetry-equivalent to every other, so there
> are only **two** distinct centrality values. A 'top ten' list is just the first ten entries
> of a tie."

> "The way out is to **break the symmetry** — remove a linker. And that's not artificial:
> missing-linker defects are real, common, and deliberately engineered in UiO-66 to tune
> porosity. When we do it, the distinct values go from 2 to 4, and lambda-2 — a measure of how
> hard the network is to cut in two — drops from 1.44 to 1.19. **That drop is the weakening,
> quantified.**"

### The band (1.5 min)

> "Across 77 frameworks, all 77 spectra come out as proper inverted parabolas, and they land
> in a **tight band** — delta-alpha between 1.11 and 1.25 across the interquartile range, with
> the asymmetry negative in every single one."

**Then immediately the caveat — do not let them find it:**

> "But I have to tell you what that band does **not** mean. Delta-alpha correlates with pore
> diameter at minus 0.50, which looks like a real structural result. It isn't. Control for
> graph size and it collapses to **plus 0.10**. Meanwhile graph size *survives* controlling for
> pore diameter, at **plus 0.62**. Adding pore size to a model that already has graph size
> buys **half a percent** of R-squared."

> "So delta-alpha is mostly tracking **how big the supercell is** — which is set by two
> parameters in our own config, not by chemistry."

**Hand-off:** *"Isha will cover the design decisions and where this goes."*

---

## 5 · Isha — Design Decisions & Next Steps (4 min)

**Slides: 3 (Technical Knowledge), 5 (Next Steps)** · *aimed at both*

### Design decisions (1.5 min)

> "Three decisions worth defending."

> "**First, why a graph at all.** MOF properties follow connectivity — gas moves through the
> pore network, and the pore network is the void left by the wiring. We deliberately use an
> **unweighted** graph: it doesn't know which element an atom is. That's a real limitation, and
> it's also the point — what survives is **pure architecture**, which transfers across
> chemistries."

> "**Second, the labelled quotient graph.** Every edge carries a lattice translation. Without
> it, UiO-66 reports 6-connected instead of 12, or the whole cell degenerates into a star."

> "**Third, supercell expansion.** A single unit cell has a graph diameter of about 2 — far too
> small to fit a power law across. Expanding is exact, because the edges already carry their
> translations."

### The τ defect (1.5 min) — *the strongest thing we have; take your time*

> "I mentioned we had a correctness test. Our spectra weren't parabolic — they just sloped
> downhill. The cause was **one line**."

> "The paper defines tau as a **ratio** — log P over log r. That's a fit **through the origin**.
> Our code used a least-squares **slope**, which has a free intercept. For most values of q
> those are nearly identical, which is why nothing looked broken."

> "At **q equals zero** they're completely different. Every term becomes one, so the partition
> function is just the **count** of nodes — identical at every radius. A flat line has slope
> zero. So tau-of-zero was forced to zero, which forced f-of-alpha-zero to zero — and
> f-of-alpha-zero is supposed to *be* the peak of the parabola. **We were deleting the peak.**"

> "One branch fixed it. All 77 frameworks now peak correctly at q equals zero."

### Next steps (1 min)

> "Three things remain, and none of them are open research questions."

> "**One** — remove the size confound, by normalising the fit window or comparing only
> frameworks at matched graph size. That decides whether the band means anything chemically."

> "**Two** — get a genuinely diverse dataset. Our 77 structures are all hypothetical MOFs, and
> all of them have zinc-oxide nodes. We requested the experimental database and the server
> returned these; nothing was checking, and now it is."

> "**Three** — test the descriptor against measured adsorption data."

### Closing (30 sec)

> "To summarise: the machinery works and is verified — the decomposition, the periodic graph,
> the centrality analysis, the spectrum. Two of our findings weren't what we expected:
> influence can't be ranked in a perfect crystal, and the band we found is driven by graph
> size rather than chemistry. **We measured both rather than presenting around them.** Thank
> you."

---

## Questions — who answers what

| Question | Answer | Who |
|---|---|---|
| *"What does a graph have to do with a MOF?"* | Properties follow connectivity; gas moves through the pore network, which is the void the wiring leaves. Connectivity is what a graph describes. | Radha Krishna |
| *"Why not just simulate them?"* | Hours per structure × hundreds of thousands. We're deciding what to simulate, not replacing it. | Radha Krishna |
| *"Isn't an unweighted graph throwing away the chemistry?"* | Yes, deliberately. It's stated as a limitation. What survives is pure architecture, which transfers across chemistries. | Isha |
| *"Does Δα predict gas uptake?"* | **No, and we never claim it.** Nothing here computes adsorption. | Keerthi Sree |
| *"Are these real materials?"* | **No** — all 77 are hMOF entries, computer-generated, never synthesised. We requested the experimental set; the server returned these. A check now catches it. | Keerthi Sree |
| *"Why only the top 10% of nodes?"* | That's the paper's iNMFA definition. It has a catch in a perfect crystal — all degrees tie — and we report the ambiguity. | Kshitij |
| *"How do I know your numbers are right?"* | Two independent implementations agree on every value; coordination numbers match published crystallography; test suites cover every layer. | Rohith |
| *"What's your computational complexity?"* | Bond perception O(N²) over 27 images; all-pairs shortest path O(N²) memory, which is why `MAX_ATOMS` is capped at 7,000. | Rohith |
| *"Why is the band confounded — did you do something wrong?"* | No — it's the known finite-size dependence of the method. 77 structures was enough to measure it for the first time. | Isha |
| *"What would make this publishable?"* | Remove the size confound, run on CoRE MOF for metal diversity, validate against measured properties. | Isha |

---

## Preparation checklist

- [ ] Compile `panel_review.tex` twice (`pdflatex`), check it's 13 pages
- [ ] Fill in **Team Number** and the two missing roll numbers (guide is already in)
- [ ] Save `three.min.js` into `1_website/` so the 3D works **without internet**
- [ ] Open `index.html` once beforehand so nothing loads slowly in front of the panel
- [ ] Each member: read your own section aloud once, timed
- [ ] Each member: register for your MOOC and have the enrolment screenshot ready
- [ ] Agree who holds the laptop and who advances slides

## Timing discipline

If you are running long, cut in this order:

1. The pipeline demo in Section 3b (describe instead of showing)
2. The three design decisions in Slide 3 (keep only the quotient graph)
3. The MOOC slide (it's a table; let them read it)

**Never cut:** the validation table (2b), the τ defect (3), or the confound (2b). Those three
are what make this a research project rather than a demo.
