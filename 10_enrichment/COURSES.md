# Certification recommendations — one per team member

**Technical Enrichment Activities, Component 1 · 20 marks · mandatory, individual**

The requirement, from the rubric:

> Each student must individually complete one approved **10–20 hour** online
> certification relevant to the project domain, from a recognised platform
> (NPTEL, Coursera, edX, Udemy, Google, Microsoft, AWS, IBM, Oracle, Cisco,
> MATLAB Academy, etc.). **The course must be approved by the project guide.**
> Submit the completion certificate, course details, and a **one-page summary
> explaining how the course supports the project.**

Each recommendation below is matched to what that person actually owns in the
codebase, so the one-page summary writes itself — you point at your own module.

> **Two things to check before enrolling.** Get Dr. Ramraj's approval in writing
> first; a course completed without prior approval may not be counted. And
> confirm the stated duration on the course page yourself — platforms revise
> these, and the figures below were correct when checked but are not guaranteed.

---

## Quick reference

| Member | Owns in this project | Recommended course | Platform | ~Hours |
|---|---|---|---|---|
| P. M. Radha Krishna | Methodology, integration, the portal | Data Engineering Foundations / Python for Data Science | IBM (Coursera) | 15–20 |
| P. Kshitij Varma | τ(q), the Legendre transform, the maths | Applied Social Network Analysis in Python | Coursera (Michigan) | ~29 |
| G. Rohith Abhinav | 3D viewer, decomposition engine | Introduction to Computer Graphics / WebGL | Udemy or edX | 15–20 |
| J. Keerthi Sree | Results, validation, confound analysis | Inferential Statistics / Data Analysis with Python | Coursera or IBM | 15–20 |
| Isha Sri Prakash | Network construction, defects, roadmap | Materials Data Sciences and Informatics | Coursera (Georgia Tech) | 15–20 |

---

## 1 · P. M. Radha Krishna — CB.SC.U4CSE23134

**Owns:** problem framing, methodology, pipeline integration, the documentation
portal, the build and test tooling.

### Recommended — [Python for Data Science, AI & Development](https://www.coursera.org/learn/python-for-applied-data-science-ai) (IBM, Coursera)

**~15–20 hours.** Python fundamentals through to working with data files and
APIs.

**Why it fits.** You wrote the pipeline driver that chains twelve modules
together, and the build script that generates the nine-page site. The API
section is directly relevant: the MOFX-DB provenance bug — where `database=` was
silently ignored — is exactly the class of problem this course covers when it
deals with reading and validating API responses.

**Alternative, if you want something harder:** [Software Design and
Architecture Specialisation](https://www.coursera.org/specializations/software-design-architecture)
(University of Alberta) — take just the *Object-Oriented Design* course from it.
Defensible via the two-independent-implementations decision in the architecture.

---

## 2 · P. Kshitij Varma — CB.SC.U4CSE23122

**Owns:** the mathematical model — the partition function, τ(q), the Legendre
transform, `code_10` and `code_11`.

### Recommended — [Applied Social Network Analysis in Python](https://www.coursera.org/learn/python-social-network-analysis) (University of Michigan, Coursera)

**~29 hours** — over the 20-hour guideline, so flag it when asking for approval.
It is worth it, and guides generally accept longer rather than shorter.

**Why it fits.** This is the closest formal course to what you actually did.
It covers network connectivity, node centrality measures, and network structure
in NetworkX — the same objects as `mof_network.js` and `code_09`. You will be
able to say in your summary that you implemented eigenvector centrality and the
Laplacian spectrum from scratch and then saw the standard treatment, which is a
stronger position than the reverse.

**If 29 hours is too long:** [Algorithmic Graph Theory and Data
Structures](https://onlinecourses.nptel.ac.in/noc26_cs08/preview) (NPTEL, 12
weeks) is more rigorous and carries more weight in an Indian academic context,
but is a bigger commitment. NPTEL is explicitly listed as acceptable.

---

## 3 · G. Rohith Abhinav — CB.SC.U4CSE23141

**Owns:** the 3D viewer, the decomposition engine, the interactive pipeline
walkthrough.

### Recommended — a Three.js / WebGL course on Udemy

**~15–20 hours.** Look for one covering scene graphs, geometry, materials,
lighting and camera controls. Udemy is explicitly on the approved-platform list.

**Why it fits.** You built the entire 3D crystal viewer on three.js r128 —
scene construction, instanced geometry for thousands of atoms, custom
per-block colouring, raycasting for hover, and orbit controls written by hand
rather than imported. A course gives you the vocabulary to explain those choices
to a panel, and the render-loop and context-management material maps directly
onto the WebGL-context guarding we added.

**Alternative:** [Introduction to Computer Graphics](https://www.edx.org/)
(edX) if you would rather have the theory — rasterisation, transforms,
projection — than the library.

---

## 4 · J. Keerthi Sree — CB.SC.U4CSE23031

**Owns:** results, validation, the band, the confound analysis, dataset
provenance.

### Recommended — [Data Analysis with Python](https://www.coursera.org/learn/data-analysis-with-python) (IBM, Coursera)

**~15–20 hours.** Covers exploratory analysis, correlation, regression and model
evaluation.

**Why it fits.** You ran the analysis that **withdrew** a claim from this
project: Δα against pore diameter looked like *r* = −0.497 and collapsed to
+0.101 once graph size was partialled out. This course's regression and model
evaluation sections are precisely that reasoning. Your one-page summary is
already written — you have a worked example of a confounded correlation that you
found yourself.

**Stronger alternative if you want the statistics properly:** [Inferential
Statistical Analysis with Python](https://www.coursera.org/learn/inferential-statistical-analysis-python)
(Michigan). Harder, and it covers the hypothesis-testing framing that would let
you put a confidence interval on the band rather than an interquartile range.

---

## 5 · Isha Sri Prakash — CB.SC.U4CSE23029

**Owns:** network construction, the defect simulation, the τ defect, design
decisions and the roadmap.

### Recommended — [Materials Data Sciences and Informatics](https://www.coursera.org/learn/material-informatics) (Georgia Institute of Technology, Coursera)

**5–12 weeks at 1–4 hours per week**, so roughly 15–20 hours if paced sensibly.

**Why it fits.** This is the only course on the list that sits in the actual
problem domain rather than the tooling. It covers materials informatics at the
intersection of materials science, computational science and information science
— which is a one-line description of this project. It will also give you the
standard vocabulary for structure–property relationships, which is what the
whole Δα argument is reaching for.

**Alternative:** [Introductory Materials Informatics](https://www.classcentral.com/course/swayam-introductory-materials-informatics-452123)
(NPTEL) — same subject, Indian academic framing, likely easier to get approved.

---

## Writing the one-page summary

The rubric asks for a page explaining how the course supports the project. The
strongest version is concrete, not generic. Structure it as:

1. **What the course covered** — three or four lines, no more.
2. **The specific module of this project it maps onto** — name the file. Not
   "helped me understand graphs" but "Week 3 covered eigenvector centrality;
   I had implemented it in `mof_network.js` and the course explained why it is
   degenerate on a symmetric graph, which is the finding in Section 12."
3. **One thing you would now do differently.** This is the line that shows you
   engaged with the material rather than clicking through it.

Keep the certificate PDF, the course syllabus page, and the approval email
together in one folder per person. The rubric requires all three, and the guide
has to upload a consolidated submission.

---

## Deadline

All Technical Enrichment Activities must be complete **one week before the last
working day of the 7th semester**. Courses at 15–20 hours take two to three
weeks at a realistic pace alongside the project — start them now rather than
after Panel Review 1.

**Sources:** [NPTEL Algorithmic Graph Theory](https://onlinecourses.nptel.ac.in/noc26_cs08/preview) ·
[Coursera Applied SNA in Python](https://www.coursera.org/learn/python-social-network-analysis) ·
[Coursera Materials Data Sciences and Informatics](https://www.coursera.org/learn/material-informatics) ·
[NPTEL Introductory Materials Informatics](https://www.classcentral.com/course/swayam-introductory-materials-informatics-452123)
