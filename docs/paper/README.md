# Team paper

[`G070_Paper.pdf`](G070_Paper.pdf): *Topology-Based Coarse-Graining for Multifractal Spectrum Analysis
in Metal-Organic Frameworks*. Isha Sri Prakash, Keerthi Sree Jonnakuti, Pasupuleti Meena Radha
Krishna, Kshitij Varma Pinnamaraju, Rohith Abhinav Sai Komal Gullolla; guide Dr. T. Ramraj.
Department of Computer Science and Engineering, Amrita Vishwa Vidyapeetham, Coimbatore. Eight pages.

The file is the submitted version and is kept unmodified.

**Content.** A pipeline from a MOF crystal structure to a coarse-grained graph of metal-oxo nodes and
organic linkers, and the width Δα of its influential-node multifractal spectrum as a structural
descriptor. Of 150 structures returned by a MOFX-DB query (hypothetical hMOF structures, although
CoRE MOF 2019 entries were requested), 76 gave a usable spectrum, with Δα from 1.032 to 1.582. The
paper reports the limits found: Δα depends strongly on graph size, several structures are
topological duplicates, and many individual power-law fits are poor; whether Δα predicts an
adsorption property is not tested.

**Relation to the repository.**

* The paper's numbers come from an independent coarse-grained run; its per-structure output is
  [`data/spectrum_descriptors/independent_cg_run/independent_cg_run_76_hmof.csv`](../../data/spectrum_descriptors/independent_cg_run/independent_cg_run_76_hmof.csv)
  (see that folder's [README](../../data/spectrum_descriptors/independent_cg_run/README.md) for the
  class counts).
* The paper uses the second of the four spectrum estimators recorded in the
  [project notes](../project_notes.md) (top 20 % influential blocks, radii up to half the diameter,
  on the coarse-grained graph). The website's own band (interquartile range 1.11–1.25) was computed
  with a different estimator on the atomic graph and is withdrawn; the two sets of numbers are not
  directly comparable. The paper's percentile classes are examined in "Sub-bands, second route" on
  the [Results page](https://radha-krishna-19.github.io/fyp/results.html), where they follow graph size.
* The size dependence the paper reports is quantified in
  [`code/spectrum_pipeline/code_14_size_strata.py`](../../code/spectrum_pipeline/code_14_size_strata.py)
  and [`code_15_dataset_sweeps.py`](../../code/spectrum_pipeline/code_15_dataset_sweeps.py).
* A summary is on the [Resources page](https://radha-krishna-19.github.io/fyp/resources.html).

# Second team paper (October 2026)

[`Team_paper_quotient_graphs_and_multifractal_spectrum.pdf`](Team_paper_quotient_graphs_and_multifractal_spectrum.pdf)
(32 pages): *Periodic Quotient Graphs, Multifractal Spectra and a Dimensional Theory of Morphism for
Metal–Organic Frameworks*, manuscript draft of 1 October 2026, by the same five authors with Dr. T.
Ramraj. It sets out the voltage-graph construction, the proof that coarse-graining commutes with
supercell lifting, the through-origin τ(q) estimator, and the tail identity that explains why Δα
grows with supercell size and why the two published bands were withdrawn. Its LaTeX source, ready to
upload to Overleaf, is [`sources/Team_paper_latex_for_Overleaf.zip`](sources/Team_paper_latex_for_Overleaf.zip).

# Revision of the guide's paper

[`guide_paper_revision/`](guide_paper_revision/) holds a revision of Dr. T. Ramraj's paper
*Multifractal Spectrum Analysis of Metal-Organic Framework Networks via Topology-Based
Coarse-Graining* (7 pages):

| File | Content |
|---|---|
| `Ramraj_paper_revised_clean.pdf` | The revised text |
| `Ramraj_paper_revised_redline_red-removed_green-added.pdf` | The same revision with every change marked: red removed, green added |
| `Ramraj_paper_revision_latex_source.zip` | LaTeX source of the revision |
