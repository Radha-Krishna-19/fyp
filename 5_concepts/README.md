# Concepts — read in this order

Five documents covering the whole project, from the chemistry up. Each is self-contained,
but they build on each other in this order.

**Each one comes in two formats.** Click the `.md` link to read it right here on GitHub;
the `.docx` is the same content as a Word file, for printing or submission. Both are
generated from one source, so they cannot drift apart.

| # | Read here | What it covers |
|---|---|---|
| 1 | [MOF and Crystallography Fundamentals](01_MOF_and_Crystallography_Fundamentals.md) | What a MOF is, nodes and linkers, the CIF format, why bonds must be inferred rather than read, periodicity and the minimum-image convention, coordination number and topology |
| 2 | [The Published Decomposition Algorithm](02_The_Published_Decomposition_Algorithm.md) | The MOFid pipeline stage by stage, `is_metal()`, the metal-oxo rule, the two alternative splits, MOFid and MOFkey |
| 3 | [Drawbacks and the Proposed Fixes](03_Drawbacks_and_the_Proposed_Fixes.md) | The four limitations of the published rule, the evidence for each, the fix proposed, and the measured effect — including where it is zero |
| 4 | [Network and Multifractal Analysis](04_Network_and_Multifractal_Analysis.md) | The quotient graph, influential nodes and why they cannot be ranked, the Laplacian, defects, the multifractal spectrum, and the 8-framework band |
| 5 | [The Website — What and Why](05_The_Website_What_and_Why.md) | Why the site was built instead of a report, what all sixteen sections do, what to demonstrate live, and how it is assembled |

**If you only read one:** Document 3 is the project's actual contribution to the
algorithm. Document 4 is the contribution to the analysis extension.

**If you are presenting:** Document 5 tells you what to click and in what order;
`../PRESENTATION_SCRIPT.md` gives you the words to say alongside it.
