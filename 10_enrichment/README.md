# Technical Enrichment Activities — 35 marks

| Component | Nature | Marks | Status |
|---|---|---|---|
| Professional online certification (individual) | Mandatory | 20 | Recommendations ready — see [`COURSES.md`](COURSES.md) |
| Group activities — any 3 of 8 | Optional, min. 3 | 15 (5 each) | 4 selected, 3 substantially done |

**Everything below needs the guide's prior approval before it counts.** The
rubric is explicit: *"Activities completed without prior approval from the guide
may not be considered for evaluation."* Get it in writing, for all four.

---

## Group activities — what we selected and why

We picked four rather than three, so one can fail without costing marks.

| # | Activity | Why this one | State |
|---|---|---|---|
| **4** | Project Website / Documentation Portal | Already built. Nine pages, computed live. | ✅ Complete |
| **5** | Open-source Technical Repository | Already exists, with history. | ✅ Complete |
| **3** | Dataset Release | The descriptor table was already computed; releasing it is packaging. | ✅ Complete |
| **1** | Submission-ready Research Paper Draft | The withdrawn claim and the real-MOF gap make a genuine short paper. | ⏳ To write |

Activities 2 (patent), 6 (competition), 7 (user study) and 8 (working
demonstration) were considered and set aside. Activity 8 is the closest
near-miss and is worth reconsidering if the paper stalls — the pipeline already
runs end to end, so it is a screen recording plus instructions.

---

## Activity 4 — Project Website / Documentation Portal ✅

**Required deliverables**, and where each lives:

| Required | Where |
|---|---|
| Project objectives | [`index.html`](../1_website/index.html) — "In one paragraph" |
| Problem statement | `index.html` §1 — The Problem |
| Methodology | [`methodology.html`](../1_website/methodology.html) — workflow, architecture, datasets, evaluation strategy |
| Team details | [`team.html`](../1_website/team.html) — five members, roll numbers, ownership |
| Project progress | `team.html` — module-by-module audit, 85% |
| Documentation | Nine pages, plus [`8_textbook/`](../8_textbook/) (12 chapters) |
| GitHub repository link | Site header and footer, on every page |
| Demonstration videos | ⏳ **Outstanding** — see below |

**What is left:** a demonstration video. Two to three minutes is enough:
open the site from a fresh clone, switch a structure in the 3D viewer, step
through the pipeline walkthrough, show the band on the Results page. Screen
recording with narration. This is also most of Activity 8 if you add it later.

**Evidence to submit:** the live Pages URL, a repository link, and the video.

---

## Activity 5 — Open-source Technical Repository ✅

| Required | Where |
|---|---|
| Source code | `1_website/`, `2_python/`, `3_notebooks/` |
| Well-structured organisation | Nine numbered top-level folders, each with a README |
| README | [Root README](../README.md) — problem, findings, defects, architecture, status |
| Installation guide | Root README, "Getting started" — three routes, all tested |
| Documentation | Per-folder READMEs, textbook, in-code comments explaining *why* |
| Regular commits with version history | `git log` — the history is real, not squashed |

**Notable for a reviewer:** the repository ships a **test suite** (five jsdom
suites, 200+ assertions) and a **CI workflow** that gates publication on those
tests passing. Most student repositories have neither.

**Before submitting:** push the outstanding commits, enable GitHub Pages
(Settings → Pages → Source: GitHub Actions), and add a repository description
and topics.

---

## Activity 3 — Dataset Release ✅

Located in [`9_dataset/`](../9_dataset/).

| Required | Where |
|---|---|
| Public repository link | GitHub; **Zenodo DOI recommended** — see below |
| Dataset documentation (README) | [`9_dataset/README.md`](../9_dataset/README.md) — schema, methodology, limitations |
| Metadata and annotation guidelines | [`metadata.json`](../9_dataset/metadata.json) — Frictionless Data schema, typed and described per column |
| Licence information | [`LICENSE`](../9_dataset/LICENSE) — CC BY 4.0, with a note on upstream terms |
| Version details | v1.0.0, dated, with a changelog |
| Organised dataset repository | Two CSVs — hypothetical and synthesised, deliberately separate |

**Strongly recommended:** mint a **Zenodo DOI**. Link the GitHub repository to
Zenodo, cut a release, and Zenodo issues a permanent citable DOI. It takes ten
minutes and turns "we put a CSV on GitHub" into a citable research output. The
rubric names Zenodo explicitly.

**What makes this dataset defensible rather than filler:** the README documents
a **negative result** — that Δα's apparent correlation with pore size is a
graph-size confound, and that anyone reusing the data must control for
`n_blocks`. A dataset that tells you how it can mislead you is more useful than
one that does not.

---

## Activity 1 — Research Paper Draft ⏳

**Required:** complete manuscript, figures and tables, references, similarity
report.

**The paper has a real argument**, which is why this is worth attempting rather
than padding:

1. A simulation-free structural descriptor for MOFs, from the periodic quotient
   graph.
2. A **definition error in the τ estimator** that silently invalidates every
   spectrum — free-intercept fit versus through-origin — with a before/after on
   77 frameworks (0/77 → 77/77 valid). This is a genuine methodological
   contribution and is reusable by anyone applying the method.
3. A **negative result**: the descriptor's apparent correlation with pore size is
   a graph-size confound.
4. A **preliminary finding**: synthesised frameworks sit outside the band
   computed from generated ones, size-matched.

Target: a short paper or a workshop track. Format in IEEE conference style.
References are already in [`6_references/references.bib`](../6_references/references.bib) (19 entries).

**Similarity report:** run it through Turnitin via the institution before
submitting. Text reused from this repository's own READMEs will flag — rewrite
rather than paste.

---

## Submission checklist

- [ ] Guide approval, in writing, for all four group activities
- [ ] Guide approval for each member's individual certification
- [ ] Five completion certificates + course details + one-page summaries
- [ ] Demonstration video recorded and linked from the site
- [ ] GitHub Pages enabled; live URL noted
- [ ] Zenodo DOI minted for the dataset
- [ ] Paper draft + similarity report
- [ ] Everything organised per-activity in one folder for the guide to upload

**Deadline:** one week before the last working day of the 7th semester.
