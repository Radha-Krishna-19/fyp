# Project context for Claude

23CSE498 Final Year Project, Phase II. Amrita Vishwa Vidyapeetham, Coimbatore.
Guide: Dr. T. Ramraj. Owner: P. M. Radha Krishna (and four teammates).

**The question.** Can a descriptor computed from a MOF's connectivity alone, in
seconds and without molecular simulation, carry enough structural information
to decide which frameworks merit hours of simulation? The intended pipeline is
CIF → bond perception → metal-oxo decomposition → labelled quotient graph →
supercell → multifractal spectrum → Δα.

---

## Proof: coarse-grain-first and atomic-first give the IDENTICAL graph (2026-09-16)

A teammate disputed the ordering claim below ("CG won't repeat as atoms do").
Settled empirically, not just argued: `2_python/_prove_ordering_equivalence.py`
builds the same n×n×n supercell two ways for five real cases, using this
project's own bond-perception and decomposition code in both routes (so any
difference found is about order, not about two implementations disagreeing).

Route A: decompose the unit cell into blocks, then replicate the small block
graph using the stored lattice translations (`code_12`'s `quotient_graph_from_cif`
+ `replicate`). Route B: replicate every atom n×n×n first (scaling the cell),
run bond perception and metal-oxo decomposition on the whole enlarged
periodic cell, then coarse-grain that.

| Structure | n | Nodes/edges | Degree sequence | `nx.is_isomorphic` | Route B / Route A time |
|---|---|---|---|---|---|
| HKUST-1 | 2 | 112/192 | match | **True** | 134.7× |
| MOF-5 | 2 | 256/384 | match | **True** | 57.6× |
| ZIF-8 | 2 | 288/384 | match | **True** | 56.7× |
| UiO-66 | 2 | 56/96 | match | **True** | 47.7× |
| UiO-66 | 3 | 189/324 | match | **True** | 675.0× |

All five: identical graph, confirmed by full isomorphism check, not just
matching summary statistics. This holds because the metal-oxo decomposition
is a purely local, translation-invariant rule (cut bonds touching a metal,
take connected components) applied to a periodic bond graph found the same
way (27-image search) on whichever cell it is handed — such a rule commutes
with taking the periodic extension, so decomposing then replicating and
replicating then decomposing are the same operation. The two routes differ
only in cost, by 48×–675× in this test, growing with n (Route B pays for
atoms it immediately discards; Route A never builds them). **Do not revisit
this as an open question** — it is closed, with a reproducible script.

## Which graph each published number was computed on (settled 2026-09-15)

The site and the dataset README describe the spectrum as computed on the
coarse-grained building-block graph. **The two published bands were not
computed that way.** Both notebooks (`3_notebooks/mof_band_analysis.ipynb`,
`3_notebooks/real_mof_band.ipynb`) call `inmfa(s["G"])`, where `G` is the
**atomic** supercell bond graph. Coarse-graining ran only to supply the
`n_nodes` and `n_linkers` counts. The saved outputs confirm this:

| Evidence in `results.json` / `real_results.json` | hMOF (77) | CoRE MOF (61) |
|---|---|---|
| `N`, the number of vertices analysed (= atoms) | 3024–6592 | 1160–7000 |
| building blocks (`n_nodes + n_linkers`) | 97–432 | 1–1297 |
| `diameter` of the analysed graph | 35–64 | 34–104 |
| `n_influential` = ⌈0.10·N⌉ atoms | 77/77 | 61/61 |
| `n_influential` larger than the block count | 77/77 | 47/61 |
| largest radius / diameter | 0.33–0.35 | 0.33–0.35 |

Four different estimators exist in the project and must not be conflated:

| Run | Graph | Influential set | Radii fitted |
|---|---|---|---|
| hMOF-77 and CoRE-61 bands (CSV files, Results page) | atomic supercell, ASE distance cutoffs, 48 Å rule capped at 7000 atoms | top 10 % of atoms by degree, then closeness | 1 … round(0.34·D) |
| Teammate's Narrow/Medium/Wide run (`~/Downloads/mof_cg_spectrum.ipynb`) | coarse graph cut from the atomic supercell | top 20 % by degree, then closeness | 1 … min(round(0.5·D), D−1) |
| `code_10`, `code_12`, browser engine (`mof_multifractal.js`) | coarse-grained labelled quotient graph, replicated n×n×n | top 30 % by degree | 1 … D |
| Paper-faithful box-growing (`code_11`, `analysePaper` in JS) | coarse-grained quotient supercell | top 10 % | deterministic box-growing |

Consequences:

- The Results page, `9_dataset/README.md` and the site's methods text documented
  a coarse-grained method while the published numbers came from atomic graphs.
  The CSV columns `graph_diameter` and `n_influential` describe the atomic graph,
  not the block graph.
- The withdrawal notice added in commit `11bf886` said both bands were computed
  "at diameter 8–12". That was wrong: diameter 8–12 describes the teammate's
  coarse-grained run. The CSV bands sit at atomic diameters 34–104.
- An atomic MOF graph is expected to contain two length scales: the molecular
  scale inside a linker or cluster, and the framework scale above one linker
  length. Fitting one power law across that crossover is not a valid scaling
  measurement. Whether the crossover is visible, and where, is measured in
  `2_python/code_13_scaling_regimes.py`; quote only the numbers that script
  reports (see the Methods section on the Spectrum page).

## Finite-size behaviour of Δα (re-run and verified 2026-09-15)

The sweep was re-run from scratch (`2_python/_run_size_scaling.py`, output in
`9_dataset/size_scaling/convergence_sweep.json`) on all four demonstration
nets, on the coarse-grained quotient graph. Fitted slopes of Δα against
ln(diameter), full q range [−10, 10]:

| Structure | Net | Slope | Intercept | R² | Diameter range | Δα range |
|---|---|---|---|---|---|---|
| HKUST-1 | tbo | 0.782 | −0.274 | 0.999 | 8–32 | 1.344–2.430 |
| MOF-5 | pcu | 0.732 | −0.156 | 1.000 | 12–48 | 1.664–2.681 |
| ZIF-8 | sod | 0.886 | −0.761 | 1.000 | 12–48 | 1.442–2.665 |
| UiO-66 | fcu | 0.692 | +0.794 | 0.998 | 8–16 | 2.229–2.707 |

All four fit a straight line in ln(diameter) almost exactly (R² ≥ 0.998); the
slope is not the same constant on every net (0.69–0.89), so "Δα ≈
0.78·ln(D) − 0.28" describes HKUST-1 only, not a universal law. Drift between
the two largest supercells tested, by q cap (all exceed the 5% tolerance at
every cap, on every net):

| |q| cap | HKUST-1 | MOF-5 | ZIF-8 | UiO-66 |
|---|---|---|---|---|---|
| 10 | 0.101 | 0.083 | 0.094 | 0.057 |
| 8 | 0.102 | 0.083 | 0.095 | 0.057 |
| 5 | 0.107 | 0.087 | 0.099 | 0.058 |
| 4 | 0.112 | 0.091 | 0.102 | 0.058 |
| 3 | 0.121 | 0.099 | 0.109 | 0.061 |
| 2 | 0.140 | 0.115 | 0.129 | 0.064 |

The figure is `9_dataset/size_scaling/convergence_figure.png`, also on the
Results page and in `8_textbook/figures/fig13_convergence.png`. **Quote only
these numbers**, not the earlier "≈0.78·ln(D) − 0.28, within 0.01" claim from
commit `11bf886`, which was neither universal across nets nor checked against
a residual.

**Mechanism.** Δα is taken over q ∈ [−10, 10]. At |q| = 10 the partition
function Σ p_i^q is dominated by a single box. The smallest possible box is one
vertex, p = 1/N, so α at the negative-q end inherits a ln(N) term and moves with
system size. At extreme q this is the extreme-value statistics of one box, not a
scaling measurement.

**Consequence.** Neither published band is a structural finding. Both are
withdrawn on the Results page and in `9_dataset/README.md`, and the withdrawn
numbers stay visible with their reasons, as for the two earlier withdrawals.
Do not recompute either band "at a converged cap": none was found.

---

## Does the Δα(D) slope vary between frameworks? (2026-09-15, capped, a proposal)

`2_python/code_15_dataset_sweeps.py`: 20 structures per dataset (size-spread
sample, not random or full), supercell capped at 5000 nodes, 3-point sweep
(n=2,3,4), one seed. hMOF (n=19 usable): slope mean 0.594, sd 0.134, range
0.407–0.818. CoRE MOF (n=15 usable): slope mean 0.871, sd 0.333, range
0.224–1.474. The slope varies ~2.5× more across CoRE MOF than across hMOF —
consistent with the slope carrying real structural signal (hMOF is dominated
by one repeated topology; see the sub-bands entry below), but also
consistent with sampling noise from this small, single-seed, single-pass
sweep. **Not established either way** — figure and numbers in
`9_dataset/size_scaling/slope_sweep_figure.png`, raw data in
`slope_sweep_hmof.json` / `slope_sweep_core.json`. Treat as a proposal for
what a size-independent descriptor might look like, not as a finding.

## Sub-bands (Narrow/Medium/Wide) are size strata, not chemistry

`2_python/code_14_size_strata.py`, run on the 34 hMOF CIFs available locally
plus the full 76-row `teammate_cg_run.csv`. Of 14 distinct coarse-grained
graph signatures across the 76 structures, **13 are entirely one class** —
class is a deterministic function of graph size wherever the graph actually
differs between structures. The 14th signature (256 nodes, 384 edges,
diameter 12 — the 4×4×4 pcu tiling already flagged above) accounts for
**48 of the 76 structures (63%)** and spans **all three classes** (36
Medium, 6 Wide, 6 Narrow; Δα 1.171–1.235 within that one identical graph).
Independently rebuilding the correct coarse-grained graph for a 34-structure
subset and computing real network statistics (degree mean/CV, assortativity,
clustering, component count, degree entropy) confirms 28 of 34 give
identical values on every statistic, because they are the same graph.
Figure: `9_dataset/size_scaling/size_strata_figure.png`.

## A topologically diverse comparison set (capped, 2026-09-15)

`2_python/code_16_topological_diversity.py`: classifies structures by
coordination signature (node degree, linker degree) — a heuristic that only
resolves the four simple, single-node-type nets already discussed on this
site (pcu 6+2, tbo 4+3, sod 4+2, fcu 12+2), not general net assignment,
because that needs Systre (Java, not installed here). Built a 6-structure
set: the four demonstration structures (tbo, pcu, sod, fcu — ground truth)
plus 2 more pcu-signature hMOF structures (the only net this heuristic could
match in the locally available 34-hMOF/20-CoRE-MOF pool, capped at 2
duplicates so the set does not silently pad itself). **rht was not found by
any method available in this environment — a genuine gap, reported as one.**
Of the 20 CoRE MOF structures classified, 34 pcu + 1 fcu matched a simple
signature and 8 had a multi-connectivity signature this heuristic cannot
resolve at all (real chemical diversity the heuristic cannot see, not
necessarily rht). This does not contradict the earlier finding that the
hMOF-77 sample is topologically degenerate; it extends it — the additional
34 hMOF CIFs fetched for other tasks this session are *also* all pcu-
signature or unclassifiable, so the degeneracy is not an artefact of which
48 structures happened to land in the original CSV.

## The full, correct band on both complete datasets (2026-09-15)

All 77 hMOF and all 61 CoRE MOF CIFs were fetched (previously only 34 and 20
were available locally) and run through `2_python/code_17_full_correct_band.py`,
which uses the correct graph: coarse-grained quotient graph of the unit cell,
replicated to 48 Å per axis, no atoms built at any point. 72/77 hMOF and
55/61 CoRE MOF produced a usable spectrum (the rest fell below the
diameter-8 scaling gate at this sizing rule). Results:
`9_dataset/size_scaling/full_band_hmof_cg.json`, `full_band_core_cg.json`.

**Class still tracks graph size, even on the correct graph, on the full
datasets.** r(Δα, coarse-grained node count) = +0.70 on hMOF and +0.70 on
CoRE MOF, independently. `code_18_subband_explain.py` sorts each dataset
into Narrow/Medium/Wide terciles and reports chemistry, graph features,
degree stats, edges, clustering, assortativity, heterogeneity and component
count per class (`subband_explain_hmof.json`, `subband_explain_core.json`):

- hMOF Narrow and Medium (65 of 72) are the same metal (Zn), same net (pcu),
  same block count (4), same node count (~260), same assortativity to 3
  decimals — indistinguishable by anything except Δα itself. The 7-structure
  Wide class differs on graph size, pore geometry (LCD 3.6 vs 9.3 Å) and
  component count (1.86 vs 1.00, see below) — all confounded with size.
- CoRE MOF's three classes differ on chemistry (void fraction, LCD), graph
  size, assortativity and heterogeneity — a real, non-degenerate spread this
  time — but every one of those differences moves in lock-step with graph
  size, so none is shown here to be an independent driver.
- **New finding: several classes on both datasets average >1 connected
  component** on the replicated quotient graph, which should always be one
  piece if the decomposition found only periodic-framework blocks. This
  means the metal-oxo decomposition is retaining disconnected guest/solvent
  fragments as small "linker" blocks on a meaningful fraction of real CoRE
  MOF structures (and a few hMOF ones). Not previously documented; worth its
  own follow-up, not further investigated here.
- MOFX-DB supplied no MOFid for any CoRE MOF record in this fetch, so metal
  and RCSR net are unknown for that dataset here — reported as unavailable,
  not guessed.

This supersedes the earlier 34-structure/20-structure capped analyses (D, E,
F in the task list) as the authoritative version; those are kept on the
Results page as a second, smaller, independently-consistent check, not
replaced.

## Defects already found and fixed (do not reintroduce)

1. **τ(q) fitted with a free intercept** instead of through the origin. This
   flattened every spectrum's apex (0/77 valid before, 77/77 after). τ must be
   `Σxy/Σx²`.
2. **Spectrum computed on the induced subgraph of influential nodes.** Metal
   clusters bond to each other only through linkers, so that subgraph has no
   edges. Cover the full graph and read the measure only at influential nodes.
3. **Averaging order.** Build Z per trial, take logarithms, then average ln Z.
   Averaging p_i(r) first biases the spectrum narrow by more than a factor of 10.
4. **Periodicity discarded.** Use the labelled quotient graph, whose edges carry
   the lattice translation t. Without it UiO-66's 12-connected Zr₆ cluster is
   reported with the wrong connectivity or the cell degenerates to a star.
5. **Classes narrower than the error bar.** The teammate's run cut Δα at its
   25th and 75th percentiles (Narrow ≤ 1.1901 < Medium ≤ 1.2218 < Wide). The
   Medium class is 0.032 wide against per-structure error bars of 0.013–0.098.
   Its isomorphism check (on unit-cell atom graphs) listed hMOF-94 and hMOF-96
   as the same graph; they landed in different classes. Never classify when the
   class width is below the error bar; `assign_classes()` refuses.
6. **`nx.diameter()` and all-pairs shortest paths** are O(N²) in pure Python and
   stall above about 3000 vertices. Use `fast_diameter()` (double sweep) and the
   BFS box covering in `code_12`, or a compiled distance matrix where N is small
   enough to store one.

## Known traps

- **MOFX-DB provenance.** `database=` is advisory on that endpoint and loses to
  the `gases[]` filter. It has returned hMOF records for a CoRE MOF 2019 request
  (the teammate's run received 150/150 hMOF). Filter each record on its own
  `database` field, or work from CIFs on disk.
- **The hMOF sample is topologically degenerate.** In the teammate's run, 48 of
  76 structures share 256 coarse nodes, 384 edges and diameter 12: a 4×4×4 pcu
  net of 64 six-connected Zn₄O nodes and 192 two-connected linkers. They differ
  only in linker chemistry, which coarse-graining removes by design. A band over
  these structures is narrow for a trivial reason. Sub-band work needs deliberate
  spread across nets (pcu, tbo, sod, fcu, rht), not random sampling.
- **Coarse-grain before replicating.** Building an atomic supercell and then
  coarse-graining caps the graph at MAX_ATOMS and hence at diameter about 12.
  The quotient graph replicates combinatorially with no atoms.
- **`metal_oxo_deep_dive` is not a path inside the repository.** It is the local
  folder containing `.git`; the repository root holds `1_website/`, `2_python/`
  and so on directly.

## Conventions

- **The website is built, not hand-edited.** Edit
  `1_website/_build/fragments/*.html` or `_build/content_source.html`, then run
  `python 1_website/_build/build_site.py`. Never edit `1_website/index.html` and
  the other built pages directly.
- **Tests:** `cd 1_website/tests && node test_*.js`. They load the real pages in
  jsdom and assert on computed output, because this site's typical failure is a
  silently blank panel rather than an error.
- **CI** (`.github/workflows/pages.yml`) runs the suites on push. The deploy job
  is manual-only (`workflow_dispatch`) because GitHub Pages is not enabled.
- **Two independent implementations** (Python in `2_python/`, JavaScript in
  `1_website/`) were written from the same specification. Where they disagree,
  one of them is wrong. Keep both.

## House style

State each claim with its evidence and its limits. Withdrawn claims are
documented on the site, not deleted. Do not describe a motivation as a result.
If a number is not converged, say so. Write in plain, formal English: avoid
rhetorical inversions, sentence fragments used for effect, aphorisms and heavy
use of dashes.

## Outstanding work

See the task list at the end of this session's summary in the git log. Items
still open after it are recorded on the Team page under "Completion".
