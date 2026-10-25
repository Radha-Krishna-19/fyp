# Technical Enrichment Activities (35 marks)

| Component | Marks | Status (25 October 2026) |
|---|---|---|
| Professional online certification, one per member | 20 | **Completed by all five members** ([certificates](certificates/)) |
| Group activities, at least three of eight | 15 | Four in hand: website, open-source repository, dataset release, research paper |

All activities require the guide's prior approval; the evidence for each is listed below.

## 1. Professional online certifications

| Member | Roll number | Course | Provider | Completed | Certificate |
|---|---|---|---|---|---|
| Pasupuleti Meena Radha Krishna | CB.SC.U4CSE23134 | Fractals and Scaling (lead instructor D. Feldman) | Santa Fe Institute, Complexity Explorer | 24 Oct 2026 | [G070_23134_OnlineCourse.pdf](certificates/G070_23134_OnlineCourse.pdf) |
| Keerthi Sree Jonnakuti | CB.SC.U4CSE23031 | Introduction to Complexity (lead instructor M. Mitchell) | Santa Fe Institute, Complexity Explorer | 23 Oct 2026 | [G070_23031_OnlineCourse.pdf](certificates/G070_23031_OnlineCourse.pdf) |
| Kshitij Varma Pinnamaraju | CB.SC.U4CSE23122 | Graph Theory (M. Fattah), 10 h | Udemy | 24 Oct 2026 | [G070_23122_OnlineCourse.pdf](certificates/G070_23122_OnlineCourse.pdf) |
| Rohith Abhinav Sai Komal Gullolla | CB.SC.U4CSE23141 | Advanced Algorithms (Graph Algorithms) in Java (H. Balazs), 12.5 h; Social Network Analysis (T. Khan), 3 h | Udemy | 24 Oct 2026 | [G070_23141_OnlineCourse.pdf](certificates/G070_23141_OnlineCourse.pdf) |
| Isha Sri Prakash | CB.SC.U4CSE23029 | Graph Algorithms for Machine Learning | TigerGraph University | 23 Oct 2026 | [G070_23029_OnlineCourse.pdf](certificates/G070_23029_OnlineCourse.pdf) |

The Santa Fe Institute certificates do not print the course length; the courses' own pages give
about 1–2 hours per unit for videos, quizzes and tests (10 and 9 units). The TigerGraph certificate
does not state a length.

### How each course supports the project and its next steps

* **Fractals and Scaling.** Box-counting dimension, power laws and how to fit them to data, and scaling
  with system size. These are the mathematics of the spectrum width Δα and of the size dependence that
  led to its withdrawal. Applied directly in the dimension profile of crystal particles
  ([`code/spectrum_shape_relation/run_04_dimension_profile_of_crystal_particles.py`](../../code/spectrum_shape_relation/run_04_dimension_profile_of_crystal_particles.py)),
  which separates crystal shapes that Δα could not.
* **Introduction to Complexity.** Fractals, networks (random, small-world, scale-free) and scaling in
  complex systems. Provides the reference network models against which a MOF graph is judged, and the
  growth and self-organisation ideas behind crystal habit.
* **Graph Theory.** Paths, connectivity, trees and graph parameters: the definitions behind the
  labelled quotient graph, its diameter and the connected-component checks used in both parts.
* **Graph algorithms (two courses).** Breadth-first search, shortest paths, spanning trees and
  centrality: the algorithms that make distance computation and box covering affordable on particle
  graphs of 10<sup>4</sup>–10<sup>5</sup> building blocks.
* **Graph Algorithms for Machine Learning.** Graph features, community detection and embeddings: the
  route to learning face energies from graph descriptors, the graph-neural-network step planned in the
  MorphoGraph-MOF pipeline.

## 2. Group activities

| # | Activity | Evidence |
|---|---|---|
| 4 | Project website / documentation portal | <https://radha-krishna-19.github.io/fyp/>: objectives, problem statement, methodology, team, progress, documentation, repository link ([`website/`](../../website/)) |
| 5 | Open-source technical repository | <https://github.com/Radha-Krishna-19/fyp>: source code, organised folders with READMEs, installation guide in the root [README](../../README.md), test suites and a CI workflow, version history |
| 3 | Dataset release | [`data/spectrum_descriptors/`](../../data/spectrum_descriptors/) (CC BY 4.0, with metadata and README) and the experimental morphology dataset [`data/experimental_morphology/`](../../data/experimental_morphology/) |
| 1 | Submission-ready research paper draft | [`docs/paper/G070_Paper.pdf`](../paper/G070_Paper.pdf) |

## Submission checklist

- [x] Five completion certificates
- [ ] Course details and a one-page summary per member (the sections above can be used as the basis)
- [ ] Guide approval recorded for each activity
- [x] Website published on GitHub Pages
- [ ] Zenodo DOI for the dataset (optional, recommended)
- [ ] Similarity report for the paper
