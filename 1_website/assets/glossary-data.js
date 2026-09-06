/* =====================================================================
   glossary-data.js — every term and symbol this project uses, defined.

   WHY THIS FILE EXISTS
   A reader who does not already know what a "labelled quotient graph" is
   cannot learn it from a sentence that uses the phrase in passing. The site
   is meant to take someone from no background to understanding the result,
   and that is only possible if every term is defined AT THE POINT it first
   appears rather than in an appendix nobody reaches.

   HOW IT IS USED
   glossary.js scans each page, finds the first occurrence of each term in the
   prose, and marks it up so the definition is one hover or tap away. It also
   builds the notation table at the top of the mathematical pages, and the
   full A-Z on glossary.html. One source, three surfaces — so a definition
   cannot say different things in different places.

   WRITING RULES FOR THE DEFINITIONS BELOW
   1. No circularity. "A quotient graph is a graph formed by taking a
      quotient" teaches nothing.
   2. Define in terms of things defined EARLIER in the reading order. Each
      entry declares its prerequisites so the ordering can be checked.
   3. Say what it is FOR, not only what it is. A reader needs to know why the
      concept was invented before the formal definition will stick.
   4. Where a symbol has a typical value in this project, give it. Abstract
      quantities become concrete the moment you see a real number.
   ===================================================================== */

window.GLOSSARY = [

/* ---------------------------------------------------------------- chemistry */
{ term: 'metal-organic framework', aka: ['MOF', 'MOFs', 'metal–organic framework'],
  group: 'Chemistry', needs: [],
  short: 'A crystal built from metal clusters joined by organic struts, with regular holes running through it.',
  long: 'Think of a scaffold. The joints are small clusters of metal atoms; the beams are rigid organic molecules. They assemble into a repeating three-dimensional structure that is mostly empty space — a gram of some MOFs has the surface area of a football pitch. That void is the point: gases can be stored in it, separated by it, or catalysed inside it. Change the joints or the beams and you change the shape of the holes, so MOFs are designed rather than discovered.' },

{ term: 'node', aka: ['nodes', 'SBU', 'secondary building unit'],
  group: 'Chemistry', needs: ['metal-organic framework'],
  short: 'The inorganic joint of the framework — a small cluster of metal atoms plus the oxygens holding it together.',
  long: 'Also called a secondary building unit (SBU). In UiO-66 the node is Zr₆O₄(OH)₄, a cluster of six zirconium atoms; in MOF-5 it is Zn₄O. The node determines how many struts can attach and at what angles, which is what fixes the overall geometry of the crystal. Identifying nodes correctly from a crystal structure is the first hard problem in this project.' },

{ term: 'linker', aka: ['linkers'],
  group: 'Chemistry', needs: ['metal-organic framework', 'node'],
  short: 'The organic strut connecting two nodes — usually a rigid carbon molecule with a binding group at each end.',
  long: 'The commonest is terephthalate: a benzene ring with a carboxylate (–COO⁻) at each end. Each carboxylate grips a metal node. Make the linker longer and the pores get bigger; add a side group and you change the chemistry inside the pore without changing the topology.' },

{ term: 'coordination number', aka: ['coordination', 'c.n.'],
  group: 'Chemistry', needs: ['node', 'linker'],
  short: 'How many neighbours a block has — for a node, the number of linkers attached to it.',
  long: 'The single most useful check on whether a decomposition is correct, because published crystallography reports it. UiO-66 nodes have coordination 12; MOF-5 has 6; HKUST-1 paddlewheels have 4. If your computed graph disagrees with the literature, the graph is wrong and every number derived from it is meaningless. This is why the site validates coordination numbers before computing any spectrum.' },

{ term: 'CIF', aka: ['CIF file', 'crystallographic information file', '.cif'],
  group: 'Chemistry', needs: [],
  short: 'The standard file describing a crystal: cell dimensions, symmetry operations, and atom positions. It contains no bonds.',
  long: 'This is the most important fact about the format for this project. A CIF tells you where the atoms are and nothing about which are bonded to which. Every bond used anywhere here was inferred computationally from distances. That inference is a judgement call with a tolerance, which is why two depositions of the same material can produce slightly different graphs.' },

{ term: 'unit cell', aka: ['cell'],
  group: 'Chemistry', needs: ['CIF'],
  short: 'The smallest box that, repeated in all directions, reproduces the whole crystal.',
  long: 'Described by three edge lengths (a, b, c) and three angles (α, β, γ). Everything in a crystal structure file is expressed relative to this box. Because the crystal repeats, an atom near one face is a close neighbour of an atom near the opposite face — which is why bond searching has to look outside the box.' },

{ term: 'fractional coordinates',
  group: 'Chemistry', needs: ['unit cell'],
  short: 'An atom’s position given as a fraction along each cell edge rather than as a distance.',
  long: 'A position of (0.5, 0.5, 0.5) means the centre of the cell whatever its size or shape. Convenient for storage and unchanged by rescaling, but useless for measuring distance until multiplied by the cell matrix — the cell is generally not a cube, so 0.1 along one edge is not the same number of ångströms as 0.1 along another.' },

{ term: 'periodic boundary conditions', aka: ['PBC', 'periodic'],
  group: 'Chemistry', needs: ['unit cell'],
  short: 'Treating the cell as if it repeats forever, so an atom leaving one face re-enters through the opposite one.',
  long: 'A crystal is not a box of atoms floating in space; it is a pattern repeated without end. Ignoring that is the single most common way to get a MOF graph wrong: bonds that cross a cell wall simply vanish, and the framework falls apart into disconnected fragments.' },

{ term: 'minimum image convention', aka: ['minimum image'],
  group: 'Chemistry', needs: ['periodic boundary conditions'],
  short: 'When measuring a distance, use the nearest copy of the second atom across all neighbouring cells.',
  long: 'Every atom exists in infinitely many copies, one per repeat of the cell. The physically meaningful distance is to the closest one. In practice you search the 27 cells formed by offsets of −1, 0 and +1 in each direction; a chemical bond is at most about 3 Å and every cell edge here is far longer, so a bond can never reach past an immediately adjacent cell.' },

{ term: 'covalent radius', aka: ['covalent radii'],
  group: 'Chemistry', needs: [],
  short: 'Half the typical distance between two bonded atoms of the same element — the effective size of an atom for bonding.',
  long: 'Used as the bonding test: two atoms are treated as bonded if they are closer than the sum of their radii, times a tolerance. This project uses ×1.30 when either atom is a metal, because metal–ligand bonds are genuinely longer and softer, and ×1.15 otherwise. Values come from the Cordero 2008 table.' },

{ term: 'topology', aka: ['net', 'RCSR net'],
  group: 'Chemistry', needs: ['node', 'linker'],
  short: 'The connection pattern of a framework, stripped of all chemistry — the shape of the wiring diagram.',
  long: 'Standard nets have three-letter codes: **pcu** is the simple cubic pattern of MOF-5, **fcu** the face-centred pattern of UiO-66, **tbo** that of HKUST-1, **sod** the sodalite cage of ZIF-8. Two frameworks with completely different chemistry can share a topology, which is exactly why a connectivity-only descriptor might transfer between them.' },

{ term: 'hMOF', aka: ['hMOFs', 'hypothetical MOF'],
  group: 'Chemistry', needs: ['metal-organic framework'],
  short: 'A computer-generated candidate framework, assembled from a library of real building blocks but never actually made.',
  long: 'Chemically reasonable — real components, real bonding rules — and the class of structure that generative models are trained on. But nobody has synthesised one. The 77 frameworks behind the main result here are all hMOF entries, which is why this site never describes them as experimental.' },

{ term: 'CoRE MOF',
  group: 'Chemistry', needs: ['metal-organic framework'],
  short: 'A curated database of MOFs that have actually been synthesised, cleaned up so they can be computed on.',
  long: '"Computation-Ready Experimental". Structures come from the Cambridge Structural Database, with disorder resolved and solvent molecules removed so simulations see the empty framework. This is the dataset the project needs and did not get on the first attempt.' },

/* ------------------------------------------------------------------- graphs */
{ term: 'graph', aka: ['graphs'],
  group: 'Graph theory', needs: [],
  short: 'A set of things (vertices) and a set of connections between them (edges). Nothing else.',
  long: 'Deliberately impoverished, and that is the strength: a graph keeps only *what is connected to what*, discarding distances, angles and identities. Anything you can prove about a graph therefore holds for every object with that connection pattern. A road map, a friendship network and a MOF are all graphs.' },

{ term: 'vertex', aka: ['vertices', 'node (graph)'],
  group: 'Graph theory', needs: ['graph'],
  short: 'One of the things a graph connects. Here, one building block of the framework.',
  long: 'Confusingly, graph theory also calls these "nodes" — which collides with the chemical meaning of node (a metal cluster). This site says **vertex** for the graph object and **node** for the chemistry wherever the two could be confused.' },

{ term: 'edge', aka: ['edges'],
  group: 'Graph theory', needs: ['graph', 'vertex'],
  short: 'A connection between two vertices. Here, a chemical bond between two building blocks.',
  long: 'In this project every edge additionally carries a label recording which lattice translation it crosses — see labelled quotient graph. Without that label the graph of a crystal is wrong.' },

{ term: 'degree',
  group: 'Graph theory', needs: ['vertex', 'edge'],
  short: 'The number of edges attached to a vertex.',
  long: 'For a block in a MOF, its degree is its coordination number — so degree is the quantity checked against published crystallography. In UiO-66 the metal vertices have degree 12.' },

{ term: 'adjacency matrix', aka: ['A'],
  group: 'Graph theory', needs: ['graph', 'edge'],
  short: 'A square table where entry (i, j) is 1 if vertices i and j are connected and 0 otherwise.',
  long: 'The standard way to hand a graph to linear algebra. For an undirected graph it is symmetric. Everything spectral — eigenvalues, centrality, the Laplacian — starts here.' },

{ term: 'labelled quotient graph', aka: ['quotient graph'],
  group: 'Graph theory', needs: ['graph', 'periodic boundary conditions', 'edge'],
  short: 'The graph of one unit cell, where each edge records which neighbouring cell it reaches into.',
  long: 'The correct way to represent an infinite periodic structure in finite memory. One vertex per block in the cell; an edge is a triple (block A, block B, translation t) where t is an integer vector such as (1, 0, 0) meaning "one cell over". Drop the translations and UiO-66’s twelve distinct connections collapse into a single self-loop, reporting coordination 1 instead of 12. That failure is shown live on the network page.' },

{ term: 'supercell', aka: ['supercell expansion'],
  group: 'Graph theory', needs: ['unit cell', 'labelled quotient graph'],
  short: 'Several unit cells stacked together and treated as one larger cell.',
  long: 'Needed because a single cell is too small to measure how a structure grows. A primitive cell might hold seven blocks, which gives two or three usable radii — far too few to fit a power law over. This project expands every structure until each lattice direction exceeds 48 Å, which is also what makes different frameworks comparable rather than differing by size.' },

{ term: 'centrality',
  group: 'Graph theory', needs: ['graph', 'vertex'],
  short: 'Any measure of how structurally important a vertex is.',
  long: 'Several definitions exist because "important" means different things: most connections (degree), connected to well-connected others (eigenvector), lies on many shortest paths (betweenness). In a defect-free crystal all of them are degenerate — every block of the same kind is identical by symmetry, so none is more central than another. That is a genuine finding about crystals, not a bug.' },

{ term: 'eigenvector centrality',
  group: 'Graph theory', needs: ['centrality', 'adjacency matrix'],
  short: 'A vertex is important if its neighbours are important — defined self-referentially and solved as an eigenvector.',
  long: 'Formally the principal eigenvector of the adjacency matrix. Distinguishes a vertex with three well-connected neighbours from one with three isolated neighbours, which plain degree cannot.' },

{ term: 'betweenness',
  group: 'Graph theory', needs: ['centrality'],
  short: 'The fraction of all shortest paths that pass through a given vertex.',
  long: 'High betweenness marks a bottleneck: remove it and many pairs of vertices have to take a longer route. In a framework it identifies the blocks whose loss would most disrupt transport through the pore network.' },

{ term: 'Laplacian', aka: ['graph Laplacian', 'L = D − A'],
  group: 'Graph theory', needs: ['adjacency matrix', 'degree'],
  short: 'The matrix L = D − A, where D holds the degrees on its diagonal and A is the adjacency matrix.',
  long: 'Its eigenvalues describe how the graph is connected, and they do not depend on how the vertices happen to be numbered — so two structures with the same wiring give the same spectrum whatever order the atoms appear in the file. That invariance is what makes it usable as a fingerprint.' },

{ term: 'algebraic connectivity', aka: ['λ₂', 'lambda_2'],
  group: 'Graph theory', needs: ['Laplacian'],
  short: 'The second-smallest Laplacian eigenvalue. Larger means harder to break the graph into two pieces.',
  long: 'The smallest eigenvalue of a Laplacian is always exactly 0. The second one measures robustness. In this project, removing a single linker from HKUST-1 drops λ₂ from 1.438 to 1.186 — the framework is measurably weaker, and the number says by how much.' },

/* ------------------------------------------------------- fractals and maths */
{ term: 'fractal',
  group: 'Fractals', needs: [],
  short: 'An object that looks similar at many different scales, and whose size grows with a non-whole-number exponent.',
  long: 'Double the radius around a point in a solid cube and you enclose 8× the material — exponent 3, an ordinary dimension. For a fractal that exponent is not a whole number. It measures how densely the object fills the space it sits in.' },

{ term: 'multifractal',
  group: 'Fractals', needs: ['fractal'],
  short: 'An object that needs many different exponents to describe it, because different regions grow at different rates.',
  long: 'A single fractal dimension is one number for the whole object. A multifractal needs a *spectrum* of them, because a dense region and a sparse region scale differently. A framework with uniform pores everywhere is close to monofractal; one with a mix of tight and open regions is strongly multifractal. Measuring how spread out those exponents are is exactly what Δα does.' },

{ term: 'box growing', aka: ['box-growing'],
  group: 'Fractals', needs: ['graph', 'fractal'],
  short: 'Centre a ball on one vertex, grow its radius one hop at a time, and count how many vertices fall inside.',
  long: 'Written M_i(r) — the number of vertices within r hops of vertex i. How fast M grows with r is how fast the network expands as seen from that vertex. Deterministic: no randomness, so the same graph always gives the same curve. This is the published method’s alternative to box *covering*, which tries to tile the whole graph with boxes and needs random restarts.' },

{ term: 'influential nodes', aka: ['influential blocks', 'influential'],
  group: 'Fractals', needs: ['degree', 'box growing'],
  short: 'The most connected vertices — here the top 10% by degree — from which the growth measurement is taken.',
  long: 'The published method reads the spectrum only at these vertices rather than at all of them, on the argument that they dominate the structure’s behaviour. One subtlety cost this project a great deal of time: you must measure *at* the influential vertices while growing through the **whole** graph. Restricting the graph itself to influential vertices leaves zero edges, because in a MOF the high-degree blocks are metal clusters and metal clusters never bond directly to one another.' },

{ term: 'partition function', aka: ['𝒫_q', 'Z(q,r)'],
  group: 'Fractals', needs: ['box growing', 'q'],
  short: 'The sum of every measured share raised to the power q — a single number summarising the whole distribution at scale r.',
  long: 'Each influential vertex i gets a share p_i(r) = M_i(r) / N of the network at radius r. The partition function is 𝒫_q(r) = Σ p_i(r)^q. The exponent q acts as a magnifying glass: it is one number that can be tuned to emphasise crowded regions or sparse ones.' },

{ term: 'q', aka: ['distortion exponent'],
  group: 'Fractals', needs: [],
  short: 'The knob that decides which parts of the structure the measurement pays attention to.',
  long: 'Raising each share to the power q changes what dominates the sum. Large positive q makes big shares overwhelm small ones, so the result describes the densest regions. Large negative q does the reverse and describes the sparsest. At q = 0 every vertex counts equally. This project sweeps q from −10 to +10 in 41 steps; sweeping q is what turns one number into a spectrum.' },

{ term: 'τ(q)', aka: ['tau', 'tau(q)', 'mass exponent'],
  group: 'Fractals', needs: ['partition function', 'q'],
  short: 'How fast the partition function grows with scale, at each setting of q.',
  long: 'Defined by 𝒫_q(r) ∝ (r/r_N)^τ(q), so τ(q) = ln 𝒫_q(r) / ln(r/r_N). **It must be fitted through the origin.** Using an ordinary least-squares slope with a free intercept produced spectra with no apex for all 77 frameworks in this project — mathematically invalid, yet each individual curve looked plausible. If τ is linear in q the object is a simple fractal; if it curves, it is multifractal.' },

{ term: 'Legendre transform',
  group: 'Fractals', needs: ['τ(q)'],
  short: 'The standard operation converting τ(q) into the pair (α, f(α)).',
  long: 'Concretely: α = dτ/dq and f(α) = qα − τ. It re-describes the same information in a more interpretable frame — instead of "how does the sum scale at each q", you get "how much of the structure has each growth rate". The same transform relates energy and temperature in thermodynamics.' },

{ term: 'α', aka: ['alpha', 'singularity strength', 'local scaling exponent'],
  group: 'Fractals', needs: ['Legendre transform'],
  short: 'The local growth exponent — how fast the neighbourhood of a particular kind of vertex expands.',
  long: 'Small α means a densely packed neighbourhood; large α a sparse one. A simple fractal has one value of α everywhere. A multifractal has a range, and the width of that range is the descriptor this project is built on.' },

{ term: 'f(α)', aka: ['f(alpha)', 'singularity spectrum'],
  group: 'Fractals', needs: ['α'],
  short: 'How much of the structure grows at each rate α — the fractal dimension of the set of vertices with that α.',
  long: 'Plotted against α it should form an inverted parabola, peaking at the most common growth rate, which occurs at q = 0. If your curve has no apex, the τ fit is wrong — that is precisely the defect this project found and corrected.' },

{ term: 'Δα', aka: ['delta alpha', 'Delta-alpha', 'spectrum width', 'width'],
  group: 'Fractals', needs: ['α', 'f(α)'],
  short: 'The width of the spectrum, α_max − α_min. The single headline descriptor of this project.',
  long: 'How varied the framework’s connectivity is. Small Δα means every part of the pore network grows at much the same rate; large Δα means the structure mixes dense and sparse regions. Across the 77 hypothetical frameworks Δα falls in 1.11–1.25. **It rises with graph size**, which is why any correlation with Δα must be checked against graph size before it can be believed — a lesson this project learned the hard way.' },

{ term: 'α₀', aka: ['alpha_0', 'alpha zero'],
  group: 'Fractals', needs: ['α', 'f(α)'],
  short: 'The α at the peak of the spectrum — the typical growth rate of the structure.',
  long: 'Where Δα says how varied the framework is, α₀ says what it is like on average. Different metals give different node coordination, which should shift α₀ — so it is the descriptor most likely to separate chemical families.' },

{ term: 'asymmetry', aka: ['A', 'spectrum asymmetry'],
  group: 'Fractals', needs: ['α', 'α₀'],
  short: 'Whether the spectrum leans left or right: A = ln[(α₀ − α_min) / (α_max − α₀)].',
  long: 'A > 0 means common structural motifs dominate the spectrum; A < 0 means rare ones do. All 77 frameworks here have A between −1.51 and −1.04, so their spectra are consistently dominated by rare, sparse regions.' },

/* ------------------------------------------------------------- statistics */
{ term: 'confound', aka: ['confounding', 'confounded'],
  group: 'Statistics', needs: [],
  short: 'A hidden third quantity that drives two others, making them look related when neither causes the other.',
  long: 'The central cautionary tale of this project. Δα appeared to correlate with pore diameter at r = −0.497. But Δα also rises with graph size, and larger graphs tend to have different pores — so the apparent relationship was mostly the size of the graph showing through twice.' },

{ term: 'partial correlation',
  group: 'Statistics', needs: ['confound'],
  short: 'The correlation remaining between two quantities once the influence of a third has been removed from both.',
  long: 'The tool that exposed the confound here. Controlling for graph size collapsed the Δα–pore correlation from −0.497 to +0.101, while size itself survived at +0.621. That is the difference between a finding and an artefact, and it is invisible unless you deliberately go looking.' },

{ term: 'R²', aka: ['R-squared', 'R2'],
  group: 'Statistics', needs: [],
  short: 'The share of variation in one quantity explained by a model of it. 0 is nothing, 1 is everything.',
  long: 'Used here to ask whether pore size adds anything beyond graph size. A size-only model reaches R² = 0.533; adding pore size takes it to 0.538 — an improvement of 0.005, which is nothing. That number is why the claim was withdrawn.' },

{ term: 'hold-out', aka: ['hold-out test', 'held out'],
  group: 'Statistics', needs: [],
  short: 'Setting some data aside, fitting on the rest, then checking the set-aside part.',
  long: 'Guards against describing your own dataset rather than discovering something general. If a band is defined using every framework you have, of course they all fall inside it; the test is whether frameworks excluded from the definition still land in the band.' }

];
