# MOF Graphs and Crystal Morphology: what we did, what we found, what we could not do

23CSE498 Phase II, team G070, Amrita Vishwa Vidyapeetham, Coimbatore. Guide: Dr. T. Ramraj. 12 November 2026.
Repository: github.com/Radha-Krishna-19/fyp. Website: radha-krishna-19.github.io/fyp.

**Part 1. Can a number from a MOF's connectivity replace hours of simulation?** We built the published
metal-oxo decomposition, a periodic (labelled quotient) graph of building blocks, and the influential-node
multifractal spectrum, and measured its width Δα for 77 hypothetical and 61 synthesised MOFs.
*Found:* Δα grows with the size of the graph on every net tested (slope 0.69–0.89 per unit ln diameter,
R² ≥ 0.998) and never settles; classes made from it follow graph size (r = +0.69 and +0.72). The published
bands are withdrawn, with the reasons kept visible. The pipeline itself is verified and reused.

**Part 2. From an established unit cell, which crystal shapes, mathematically and computationally?**
(the panel's question). From the CIF we find the space group, the faces symmetry allows, and the shapes
they form; 16 propositions are proved and checked numerically. MOF-5, HKUST-1 and UiO-66 admit the family
cube → cuboctahedron → octahedron, ZIF-8 cube → rhombic dodecahedron; deforming the cell adds plates and
rods. Seven growth models (BFDH, graph rule, two graph-energy Wulff models, force-field Wulff, a blend,
CHGNet) pick a member of the family. An exact map of all cubic shapes places every model on one plane and
lists the possible morphologies of a CIF in the order an additive should produce them.
*Found, against 134 laboratory records from 35 papers:* ZIF-8 is reproduced by every model; the MOF-5 cube
by three models (one only at its default bond cost); HKUST-1 only as the dominant {111} face of a truncated
octahedron; additive-free UiO-66 by none. All 6 laboratory series whose shapes stay on the map follow the
predicted order (chance 2.7 × 10⁻⁴ if orders were random).

**Linking the parts.** The periodic Δα carries no shape information beyond size (ρ = +0.001). On a
finite crystal particle, the mass–radius dimension profile identifies the shape (cube, plate, rod; and
the compact shapes predicted for MOF-5) and changes monotonically along the morphology map.

**How we know it is right.** Two independent implementations (Python and the browser) agree number by
number; 14 test suites (3,115 checks) and Python tests pass from any folder; an audit on 12 November
re-ran every script and recomputed every quoted number from its result file. Every mistake (26) is
recorded with how it was found and fixed.

**What we could not do.** Rank the models (only MOF-5 separates them); validate machine-learned surface
energies against DFT; predict shapes set by growth kinetics (plates, rods, intergrown crystals); predict
the size of an additive's effect; compute any adsorption property from shape. A second-person check of
the laboratory records and of the proofs is prepared but not yet done.

**What we need.** HPC time for a DFT check of six slabs; a laboratory contact for a small controlled
synthesis series; library access to about five paywalled papers; the Phase II review rubric.
