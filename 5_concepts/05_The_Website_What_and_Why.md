# The Website

**What it is, why it was built this way, and what every section does**

> A guide to the interactive site: the reasoning behind building it instead of writing a report, an explanation of all sixteen sections, the moments worth demonstrating live, and how the whole thing is assembled.

*Part of the MOF Building-Block Analysis final year project — see the [main README](../README.md).*

---

## 1 · Why a website at all


This project could have been submitted as a report and a folder of code. It was built as an interactive site instead, for reasons that are specific to what is being argued.

1. **The central claim is visual.** "The published algorithm reports an incomplete node" is a sentence. Two 3D models side by side — the same structure, the same camera, one missing its carboxylates — is a demonstration. The reader does not have to take the claim on trust.
2. **The claim must survive an arbitrary input.** Anyone can produce a figure that supports their argument. The site accepts an uploaded `.cif` and runs the real algorithm on it live, so the behaviour can be tested on a structure the author never saw.
3. **Every number should be traceable to the code that produced it.** Clicking any filename anywhere on the page opens the actual source, with line numbers. Nothing is quoted from a slide.
4. **The pipeline is a sequence, and a sequence should be steppable.** The walkthrough advances one stage at a time, showing the code, the algorithm, and the 3D state after that stage — so it is clear which stage causes which effect.

> **The design rule the site follows**
>
> Every claim on the page is computed in the browser, from the structure currently loaded, at the moment you look at it. No number is typed into the HTML.
>
> This is why the site is worth more than a report: a report asserts, the site recomputes.


## 2 · How to open it


```
metal_oxo_deep_dive/1_website/index.html

   double-click it. That is the whole procedure.
```
*One page. No web server, no build step, no install. Everything is self-contained.*


> **Before presenting: make the 3D work without internet**
>
> The 3D views need the Three.js library, which by default loads from a CDN — **with no internet, every 3D panel is blank**.
>
> Fix it once: open `https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js` and save it into `1_website/` as exactly `three.min.js`.
>
> The page prefers a local copy and falls back to the CDN. If neither is available, each panel explains itself rather than showing a black box.


---


## 3 · The page, section by section


Sixteen sections, in a deliberate order: the problem, then what was built, then the algorithm in detail, then the analysis, then the source. The sticky navigation at the top tracks where you are.


### Part I — Framing

| # | Section | What it does and why it is there |
|---|---|---|
| 1 | The Problem | What a MOF is, what nodes and linkers are, and why the decomposition matters. Establishes the stakes before any code appears. |
| 2 | The Question We Were Asked | The brief — find and highlight the influential nodes — stated verbatim, followed by the honest answer. Placed early because the finding is counter-intuitive and everything after it is easier to follow once you know where it lands. |
| 3 | Everything We Built | Four components, each with: what it does, why it exists, what it achieved, and where on the page to see it. The orientation map. |
| 4 | Implementation Map | Every code file, what stage it implements, and whether it is a translation of the published work or this project's own. **Every filename here is clickable and opens the real source.** |
| 5 | Roadmap | The order the work was done in, and why each step had to precede the next. |


### Part II — The algorithm

| # | Section | What it does and why it is there |
|---|---|---|
| 6 | The Full Pipeline — Code + 3D | The core of the site. Nine modules, eighteen steps, advanced one at a time. Each step shows the published algorithm in words, the exact code that implements it, and the 3D structure as it stands after that step. Structures can be swapped or uploaded. |
| 7 | Limitations — and How We Fix Them | Four limitation cards. Each states the drawback, shows **live evidence computed from the currently loaded structure**, gives the proposed fix, and reports the measured effect — including where that effect is zero. |
| 8 | Before and After the Fixes — in 3D | Two 3D panels, same structure, same coordinates: the published output on the left, the fixed output on the right. The atoms are in identical positions in both, so the only visible difference is the one the fix causes. |
| 8b | The Complete Pipeline, Interactive | All seven published stages on one screen for any uploaded structure — the pipeline as a tool rather than as a lesson. |


> **Why the before/after panels use identical coordinates**
>
> An earlier version unwrapped each block independently for display, which moved up to 88 atoms by as much as 20.5 Å between the two panels. The panels then differed in two ways at once — the fix, and the drawing — which made the comparison worthless.
>
> A `no_unwrap` option now forces both panels to share coordinates. Verified: maximum atom displacement between panels is **0.000000 Å**. Any difference you see is caused by the fix and by nothing else.


### Part III — The analysis

| # | Section | What it does and why it is there |
|---|---|---|
| 9 | The Paper We Built On | Every quantity in Xiao et al. (2021) with its definition and physical meaning, split into what was used unchanged, what was initially got wrong, and what this project added that the paper does not cover. |
| 10 | The Block Graph Must Be Periodic | The labelled quotient graph, and the live validation table showing all four structures matching published coordination numbers — including UiO-66 at 12 rather than 6. |
| 11 | Which Blocks Are Influential? | Degree, eigenvector and betweenness centrality, computed live — and the finding that every structure has only two distinct values, so a ranking is a tie. |
| 12 | Defect Simulation | Remove one linker and watch the symmetry break: distinct centrality values go 2 → 4 and λ₂ falls 1.44 → 1.19. This is where influence becomes measurable. |
| 13 | The Spectrum as a Family Fingerprint | The Laplacian spectrum and what its eigenvalues say about connectivity. |
| 14 | The Multifractal Spectrum | The analysis the brief actually asked for: influential blocks, f(α) spectrum, the family band, and the candidate test. |
| 15 | Against the Published Method | The same analysis using the paper's own box-growing procedure, confirming the results are not an artefact of the implementation chosen. |


### Part IV — Source

| # | Section | What it does and why it is there |
|---|---|---|
| 16 | Every Line of Source Code | A browser for all 26 files. Filter by All, Python, Our Contributions, or JavaScript. Click any file to read it in place, with line numbers and a copy button. |


---


## 4 · Things worth demonstrating live


If you are presenting this, these are the moments where the site does something a slide cannot.

1. **Upload a structure nobody has seen.** Section 6 accepts any `.cif`. The whole pipeline runs on it in the browser. This is the strongest available answer to "does this only work on your examples?"
2. **Click a filename.** Any filename, anywhere on the page. The real source opens over the page. It shows that nothing is being quoted second-hand.
3. **Switch the engine to the published version in Section 6.** Watch the node lose its carboxylates. Then switch back.
4. **Show the hardcoded-metal-list demonstration.** With a whitelist of eight common MOF metals, UiO-66 yields zero recognised metal atoms — silently, with no error. It makes the case for the exclusion-list design immediately.
5. **Step through Section 6 slowly around the split.** The bonds are deliberately drawn neutral grey before the split is decided, so the colouring never gives away the answer before the algorithm has computed it.
6. **Run the defect simulation in Section 12.** λ₂ drops in front of the audience. It is the clearest single number in the project.

## 5 · How the site is put together


Not required to use it, but worth knowing if you are asked how it works.

| File | Responsibility |
|---|---|
| `index.html` | The single page — all sixteen sections, all styling. |
| `mof_decompose.js` | The decomposition engine: CIF parsing, periodic bond perception, all three published splits, and the fixed variant. |
| `mof_render.js` | Three.js rendering, with on-demand drawing and WebGL context recovery. |
| `mof_network.js` | Quotient graph, degrees, centralities, Laplacian spectrum. |
| `mof_multifractal.js` | Box-covering iNMFA and the paper's box-growing NMFA. |
| `pipeline_walkthrough.js` | Section 6 — the eighteen steps. |
| `metal_oxo_drawbacks.js` | Sections 7 and 8 — limitation cards and the before/after panels. |
| `code_sources.js` | Every source file, embedded, so the viewer works without a server. |
| `code_viewer.js` | The click-to-read modal: line numbers, highlighting, copy, Esc to close. |
| `single_page.js` | Sticky-nav scroll tracking, the code browser grid, and filename wiring. |


### 5.1 · Two problems that had to be solved

- **The 3D used to die after a few minutes.** Six independent 60 fps animation loops were running on scenes that never changed, exhausting the browser's WebGL contexts. Fixed by redrawing only when something actually changes, sharing one animation ticker across all views, recovering from context loss, and initialising a view only when it scrolls into sight. Verified: a static scene now issues **zero** draw calls over 120 frames.
- **The before/after comparison was misleading.** Described in the note above — fixed with `no_unwrap`, verified at 0.000000 Å displacement.

### 5.2 · Cross-validation


The engine exists twice: in Python (`2_python/`) and in JavaScript (in the browser). This was not duplicated effort — it is the check. The two implementations were written against the same published algorithm and compared on every reported quantity: bond counts, block compositions, coordination numbers, centralities, spectra. **They agree on every value.** Two independent implementations agreeing is meaningful evidence that neither has a silent bug.


## 6 · The rest of the folder

| Folder | What is in it |
|---|---|
| `1_website/` | The site. Open `index.html`. |
| `2_python/` | One runnable Python module per pipeline stage, with the test structures beside them. |
| `3_notebooks/` | The corrected notebook, with the structures embedded so it runs anywhere including Colab, and with all outputs saved so results are visible before you run anything. |
| `4_reference/` | Figures. |
| `5_concepts/` | These five documents. |
| `README.md` | Start here — the folder map and the headline results. |
| `PRESENTATION_SCRIPT.md` | A full talk, start to finish, with what to show at each point. |
