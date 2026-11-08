#!/usr/bin/env python3
"""
build_journey_fragment.py  ->  fragments/journey.before.html  (page journey.html, "How We Got Here")

The whole project as one ordered story: which papers were read, what was built from them, which
code and notebooks produced which results, which mistakes were found at each step and how each was
corrected, and why each method was chosen over the alternatives a panel might suggest.

Sources for every statement: the git history of the repository (dates), docs/project_notes.md, the References
page, the result files named in each stage, and the Mistakes page (lessons.html), whose entries
are linked by their anchors. No number appears here that is not on another page with its source.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'fragments', 'journey.before.html')

# Each stage: id, title, when, read, did, code, out, mistakes (list of (text, lessons-anchor)), fix, why (list of (question, answer))
STAGES = [
 dict(id='j1', purpose="Screening MOFs for gas separation (xenon/krypton, then CO<sub>2</sub>) by simulation costs hours per framework. A number computed from connectivity alone, in seconds, could decide which frameworks are worth simulating. We read [1] because a MOF must first be cut into its chemical building units before any graph can be built, and [1] is the published, widely used rule for that. We read [2] because it gives a single curve (the spectrum) that summarises how a network is organised across all scales, which is what a fast screening number needs.", title='Stage 1. The question and the first two papers', when='August 2026',
  read='Bucior et al. 2019 [1] (MOFid / MOFkey and the metal-oxo decomposition: how to cut a MOF into metal clusters and organic linkers). Xiao, Wang and Li 2021 [2] (NMFA / iNMFA: the multifractal spectrum of a network). Song, Havlin and Makse 2005 [3] (box covering).',
  did='Asked whether one number computed from a MOF\'s connectivity alone can decide which frameworks deserve hours of simulation. Translated the published decomposition into Python, built the building-block graph, and computed its multifractal spectrum width &Delta;&alpha;.',
  code='<code>code/spectrum_pipeline/code_01</code> &hellip; <code>code_07</code> (CIF reading, bond perception with Cordero covalent radii [10], metal-oxo decomposition, MOFid/MOFkey assembly), <code>code_09</code> (network), <code>code_10</code> (spectrum); first notebook on 8 frameworks.',
  out='A working decomposition and a first spectrum for 8 frameworks.',
  mistakes=[('Probabilities were averaged before taking logarithms, which made every spectrum more than ten times too narrow.', 'l-order')],
  fix='Build Z per trial, take ln Z, then average (commit of 31 Aug 2026).',
  why=[('Why the metal-oxo decomposition and not single-node or all-node?', 'It is the published MOFid rule [1] used to identify MOFs; it keeps each metal-oxo cluster as one node, which is the chemical unit that decides connectivity. The other two variants are implemented too (<code>code_04b</code>, <code>code_04c</code>) for comparison.'),
       ('Why a multifractal spectrum and not simple graph statistics?', 'Degree, clustering and diameter describe one scale; the spectrum describes how mass is spread across all scales in one curve, which was the reason for testing it. Whether that adds anything over simple statistics is exactly what later stages tested.')]),
 dict(id='j2', purpose="A result is only meaningful if it uses the published method exactly and if we know what data it was computed on. This stage made both true.", title='Stage 2. Matching the paper exactly, and the data we actually received', when='1 September 2026',
  read='Re-read [2] line by line; MOFX-DB [7]; hMOF [8]; CoRE MOF 2019 [9].',
  did='Compared our formulas with the paper and rebuilt the band of &Delta;&alpha; values on 77 frameworks fetched from MOFX-DB.',
  code='<code>notebooks/spectrum/mof_band_analysis.ipynb</code>; <code>code/spectrum_pipeline/code_10_multifractal_spectrum.py</code>.',
  out='A band of 77 widths; a first claim that the width tracks pore size.',
  mistakes=[('&tau;(q) had been fitted with a free intercept; the paper fits through the origin. No spectrum was valid (0 of 77).', 'l-tau'),
            ('The influential nodes were analysed on their own subgraph, which has no edges in a MOF.', 'l-induced'),
            ('We asked MOFX-DB for CoRE MOF 2019 (real crystals) and received hMOF (hypothetical, all Zn<sub>4</sub>O) without noticing.', ''),
            ('The pore-size claim.', 'l-size')],
  fix='&tau; = &Sigma;xy/&Sigma;x&sup2; (77 of 77 valid); cover the whole graph and read the measure at influential nodes; the dataset was relabelled as hMOF; the pore-size claim was retracted the same day.',
  why=[('Why follow the paper\'s through-origin fit?', 'Because &tau;(q) is defined that way in [2]; a free intercept changes the quantity, so results would not be comparable with the published method.')]),
 dict(id='j3', purpose="A crystal is infinite and periodic; a graph of one unit cell is not. Without periodicity the connectivity of real MOFs is wrong, so every later number would be wrong. The website and textbook exist so that a newcomer, the guide and the panel can check every step themselves.", title='Stage 3. Making it periodic and making it teachable', when='2&ndash;7 September 2026',
  read='RCSR nets [5], Systre [4], the SBU concept [6]; HKUST-1, MOF-5, ZIF-8 and UiO-66 structure papers [11]&ndash;[14].',
  did='Built the labelled quotient graph (every edge carries the lattice translation it crosses), checked it on the four demonstration MOFs (nets tbo, pcu, sod, fcu), and wrote the website, the textbook and the panel deck. Obtained 61 real CoRE MOF structures.',
  code='<code>code_09_network_analysis.py</code> (<code>build_periodic_block_graph</code>), the browser engine <code>website/mof_*.js</code> (a second, independent implementation), <code>notebooks/spectrum/real_mof_band.ipynb</code>, <code>docs/textbook/</code>.',
  out='Correct coordination for all four nets (UiO-66 12-connected), the site, 61 real spectra.',
  mistakes=[('Without the translation labels, UiO-66\'s cluster got the wrong number of neighbours.', 'l-period'),
            ('A claim built on four real structures.', '')],
  fix='Quotient graph with translations everywhere; the four-structure claim was withdrawn (7 Sep).',
  why=[('Why write a second implementation in JavaScript?', 'Two independent implementations from one specification catch each other\'s mistakes; the site also lets a reader compute every number in the browser.')]),
 dict(id='j4', purpose="Before ranking MOFs by a number, the number must describe the MOF and not the size of the computer model. This stage tested exactly that, because a ranking built on graph size would be meaningless.", title='Stage 4. Is the number about the MOF or about the size of the graph?', when='14&ndash;16 September 2026',
  read='Finite-size scaling practice (the spectrum must stop changing as the graph grows before it can be compared).',
  did='Swept &Delta;&alpha; over supercell sizes on four nets, re-ran the full bands on the correct graph (72 of 77 hMOF, 55 of 61 CoRE MOF), and proved that coarse-graining first or replicating first gives the identical graph.',
  code='<code>code_12_converged_band.py</code>, <code>code_13</code> &hellip; <code>code_18</code>, <code>_run_size_scaling.py</code>, <code>_prove_ordering_equivalence.py</code>; results in <code>data/spectrum_descriptors/size_scaling/</code>.',
  out='&Delta;&alpha; grows linearly in ln(diameter) on every net (R&sup2; &ge; 0.998, slope 0.69&ndash;0.89) and never converges; class tracks graph size (r = +0.69 hMOF, +0.72 CoRE MOF).',
  mistakes=[('The Narrow/Medium/Wide classes were narrower than the error bar; two identical graphs fell in different classes.', 'l-classes'),
            ('The published bands had been computed on the atomic graph while the text described the coarse-grained graph.', 'l-graph'),
            ('Graphs were capped too small to measure any scaling.', 'l-small'),
            ('48 of 76 hMOF structures were the same graph.', 'l-degenerate'),
            ('The size effect itself: what looked like structure was graph size.', 'l-size')],
  fix='Both bands withdrawn (kept visible with reasons); a refusal rule for classes narrower than their error; coarse-grain first (48&ndash;675&times; cheaper, proved identical); a diversity guard on samples.',
  why=[('Why withdraw instead of tuning the method until a band appeared?', 'A number that changes with graph size cannot be compared between MOFs of different size; tuning parameters until it looks stable would hide that.')]),
 dict(id='j5', purpose="The panel asked for several crystal shapes from one established unit cell. Shape matters for the original aim: it decides which faces are exposed to the gas, how far a molecule travels into the pores and how the crystals pack, so it changes adsorption in practice. BFDH was built first because it needs only the cell and the symmetry, so it works for any MOF.", title='Stage 5. The panel changes the question', when='after Panel Review 1',
  read='Chen et al. 2020 [20] (one MOF chemistry, many crystal shapes), Hartman&ndash;Perdok theory [22], the Wulff construction [23], spglib [28].',
  did='The panel asked: from an established MOF\'s unit cell, can several crystal morphologies be generated, mathematically and computationally? Built the chain CIF &rarr; symmetry &rarr; allowed faces (systematic absences removed) &rarr; BFDH shape &rarr; shape descriptors.',
  code='<code>code/morphology/</code> (<code>mofmorph/structure.py, faces.py, shape.py, models.py</code>, <code>run_phase1.py</code>, 14 checks in <code>tests.py</code>); browser engine <code>mof_morphology.js</code>.',
  out='BFDH: truncated octahedron for MOF-5, HKUST-1 and UiO-66; rhombic dodecahedron for ZIF-8. Cube, cuboctahedron and octahedron reached by the ratio R<sub>111</sub>/R<sub>100</sub>.',
  mistakes=[('CSS colour tokens that referred to themselves blanked colours on every page.', '')],
  fix='Fixed the tokens (9 Oct).',
  why=[('Why BFDH first?', 'It needs only the lattice and the space group, so it gives a shape for any CIF in seconds and is the standard first estimate in crystal-morphology work.'),
       ('Why not jump to molecular dynamics of crystal growth?', 'Growth simulations of MOFs in solvent need force fields and time far beyond this project, and would not answer the mathematical question the panel asked.')]),
 dict(id='j6', purpose="A picture of a shape is not a proof. The propositions show that the shapes follow mathematically from the unit cell. Changing the cell answers the second reading of the panel's question (one cell, controlled changes, many shapes). Counting the links each face cuts reuses the periodic graph of the first half for the second.", title='Stage 6. Proving it, deforming the cell, and the graph view of faces', when='October 2026',
  read='Wulff and BFDH theory, Hartman&ndash;Perdok F/S/K faces [22], Chen et al. link counting [20].',
  did='Wrote 16 propositions with proofs (each checked numerically). Changed the cell lengths and angles and showed which shapes follow (plates and rods). Counted, on the MOF\'s own periodic graph, how many links each face cuts, and ranked faces from that.',
  code='<code>morph_math_page.js</code>; <code>mofmorph/deform.py</code>, <code>run_deform.py</code>, <code>tests_deform.py</code> (11 checks); <code>mofmorph/graphfaces.py</code>, <code>run_phase3.py</code>, <code>tests_phase3.py</code> (11 checks).',
  out='Propositions 1&ndash;16; plate, equant and rod shapes from cell deformation; attachment numbers pcu 1/2/3 (cube) and fcu 4/5/3 (octahedron, matching [20]).',
  mistakes=[],
  fix='&mdash;',
  why=[('Why change the cell at all?', 'It is the second reading of the panel\'s question: one established cell, changed in a controlled way, gives a family of shapes with exact thresholds.')]),
 dict(id='j7', purpose="BFDH uses geometry only and ignores chemistry. Real faces differ in how many bonds they break and how strong those bonds are, so an energy-based shape (Wulff) is needed as a second, independent prediction.", title='Stage 7. Face energies from atoms', when='October 2026',
  read='UFF [29]; Wu and Jiang 2024 [21] (UFF workflow for MOFs).',
  did='Computed the cleavage energy of every face from the atoms with a force field and built Wulff shapes.',
  code='<code>mofmorph/forcefield.py</code>, <code>run_phase4.py</code>, <code>tests_phase4.py</code> (4 checks); <code>results/phase4_results.json</code>.',
  out='UFF Wulff: cube for MOF-5, octahedron for UiO-66, rhombic dodecahedron for ZIF-8, truncated octahedron for HKUST-1.',
  mistakes=[('HKUST-1 was first described as a cube with cut corners; it is a truncated octahedron.', 'm-shapes')],
  fix='Read shapes from the computed face fractions only.',
  why=[('Why UFF and not DFT?', 'UFF covers every element in these MOFs and costs seconds per face; DFT on MOF slabs costs hours each. UFF is the baseline; a DFT spot check is planned (Kshitij, <code>DFT_CHECK_PLAN.md</code>).'),
       ('Why unrelaxed energies?', 'Relaxation needs a reliable potential for MOF surfaces, which UFF is not; unrelaxed cleavage energies keep the comparison simple and are stated as such.')]),
 dict(id='j8', purpose="Each teammate's task fed one question: which shape method agrees with real crystals? The blend tests whether geometry and energy together do better than either alone. CHGNet gives a second, machine-learned set of energies to compare with UFF. Rohith's dataset gives the real crystals to compare against, with the conditions they were grown under.", title='Stage 8. The team\'s tasks: combine the methods, machine-learned energies, real crystals', when='12&ndash;14 October 2026',
  read='CHGNet [Deng et al. 2023]; pymatgen slab generation; experimental morphology papers (Cravillon 2012 ZIF-8, Liu 2016 HKUST-1, Cubillas 2012 MOF-5, Umemura 2011, Butova 2023).',
  did='Combined BFDH and Wulff into one rule with a weight w; wrote a Colab notebook for any CIF; post-processed Keerthi\'s CHGNet notebook runs (done by Rohith) for MOF-5, HKUST-1 and UiO-66; Rohith collected real crystal shapes with their growth conditions.',
  code='<code>mofmorph/hybrid.py</code>, <code>run_hybrid.py</code>, <code>MorphoGraph_hybrid.ipynb</code>; <code>mofmorph/chgnet_post.py</code>, <code>run_chgnet_cleavage.py</code>, <code>slab_check.py</code>; <code>data/experimental_morphology/</code>.',
  out='The blend changes the shape only for MOF-5 and UiO-66. CHGNet slabs give only &gamma;<sub>top</sub>+&gamma;<sub>bottom</sub>, too few equations for individual face energies; the cleavage energy (half the cheapest cut) gives shapes that disagree with experiment for MOF-5 and UiO-66.',
  mistakes=[('The first notebook assumed every crystal is cubic and gave wrong shapes for others.', 'm-cubic'),
            ('A statement that CHGNet "will never" give a shape was too strong.', 'm-never'),
            ('Loose pieces in slabs were first read as split metal clusters; they were linker fragments.', 'm-fragment')],
  fix='A general version for any crystal system; the cleavage-energy workaround with its limits; the slab pieces identified.',
  why=[('Why combine BFDH and Wulff?', 'BFDH uses geometry only and Wulff uses energy only; a blend tests whether both carry information. With four MOFs no best weight can be chosen without fitting the test set, so none is claimed.'),
       ('Why the cleavage energy and not separate face energies?', 'The slabs give one equation per cut with two unknown faces; the cleavage energy is the standard, well-defined quantity those slabs do determine.')]),
 dict(id='j9', purpose="Work checked only by its author is not checked. A second reviewer re-ran every script, tested the chemistry, and looked for weak points before the guide review.", title='Stage 9. An independent review of the code and the chemistry', when='14&ndash;15 October 2026',
  read='The 35 open-access papers behind the experimental dataset; CoRE MOF 2019 [9].',
  did='A second reviewer re-ran and checked everything, built the experimental dataset (134 records, 35 papers, 12 MOFs), confirmed from two primary papers that the UiO-66 octahedra are grown with modulators, tested the force field\'s sensitivity, and ran the pipeline on 8 CoRE MOFs of six crystal systems.',
  code='<code>tests_review.py</code> (the review checks), <code>run_bond_sensitivity.py</code>, <code>run_core.py</code>, <code>slab_options_check.py</code>, <code>tests_review.py</code>, <code>dataset/build_dataset.py</code>.',
  out='The Experiment page: every method scored against additive-free crystals.',
  mistakes=[('Hydrogen atoms were dropped from the ZIF-8 energy cell ({111}: 0.312 instead of 0.619 J/m&sup2;).', 'm-hydrogen'),
            ('The MOF-5 cube had been trusted because it matched experiment; it depends on the flat bond cost.', 'm-trustuff'),
            ('One "correct" shape per MOF, while real shapes depend on solvent, additive and time.', 'm-oneshape'),
            ('The hybrid weight could be tuned to the four test MOFs.', 'm-tune')],
  fix='Energies rebuilt with all atoms; the MOF-5 cube quoted only with its caveat; conditions recorded for every record; the weight shown fixed at w = 0.5.',
  why=[('Why keep only additive-free crystals in the benchmark?', 'No model here contains a solvent or modulator, so comparing with crystals grown with additives would test something the models do not represent.')]),
 dict(id='j10', purpose="The first half should not be wasted if it can be used. This stage tested, with a notebook that Radha Krishna ran, whether the spectrum of the first half carries any information about crystal shape, and so whether the two halves form one project.", title='Stage 10. Joining the two halves', when='16 October 2026',
  read='Our own first-half results.',
  did='Asked whether the first-half spectrum is related to the second-half shapes. Built finite crystal particles (no wrap-around) of chosen shapes and measured &Delta;&alpha;; compared &Delta;&alpha; with predicted BFDH shapes on 55 CoRE MOFs. The notebook was run by Radha Krishna in Google Colab; all 15 checks passed.',
  code='<code>code/spectrum_shape_relation/</code> (<code>Spectrum_Shape_Relation.ipynb</code> and the scripts it calls), <code>code_19_spectrum_vs_shape.py</code>.',
  out='&Delta;&alpha; of a finite MOF-5 particle separates flat and long particles from compact ones, but not compact shapes from each other; across 55 CoRE MOFs the periodic &Delta;&alpha; carries no shape information once graph size is held fixed.',
  mistakes=[],
  fix='&mdash;',
  why=[('Why compare at equal block count and not equal diameter?', 'In a pcu net graph distance behaves like the taxicab distance, so an octahedron has a much smaller diameter than a cube with the same number of blocks; equal block count compares the same amount of crystal.'),
       ('Why Spearman and a size-controlled (partial) correlation?', 'Spearman is robust to outliers and non-linear links; controlling size was necessary because size had produced every earlier false result.')]),
 dict(id='j11', purpose="Before the next phase the record itself had to be reliable: one copy of every file, every page consistent with the result files and with every other page, every figure traceable to its script, and the courses completed by the team tied to the work.", title='Stage 11. Audit, reorganisation and certifications', when='23&ndash;25 October 2026',
  read='Our own website, repository and result files; the five online courses completed by the team (Team page).',
  did='Merged the work held only on one computer with the GitHub copy after comparing every file; reorganised the repository into code/, data/, notebooks/, docs/ and website/; compared every page with the result files; added a Source line to every figure, a Resources page and a test for both; enabled publication to GitHub Pages.',
  code='<code>website/_build/figure_sources.py</code>, <code>website/_build/update_code_sources.py</code>, <code>website/tests/run_all_tests.js</code>, <code>code/morphology/mofmorph/chgnet_runs.py</code>.',
  out='One consistent record. Five contradictions and several smaller slips were found and fixed (Mistakes page, Part C).',
  mistakes=[('UiO-66 was called a match although the additive-free crystals are cubes.', 'l-uio66'),
            ('Status tables lagged behind the work.', 'l-status'),
            ('Figures did not name their source.', 'l-provenance'),
            ('The footer claimed every number was computed in the browser.', 'l-footer'),
            ('Work existed in several copies.', 'l-copies')],
  fix='See the Mistakes page, Part C.',
  why=[('Why audit before new work?', 'A new result is only as credible as the record it joins; contradictions between pages are the first thing a reviewer finds.')]),
 dict(id='j12', purpose="Stage 10 left one question open: the spectrum width separates plates and rods but not the compact shapes the methods predict. The Fractals and Scaling course suggested keeping the whole scaling curve instead of one number.", title='Stage 12. The dimension profile of a crystal particle', when='25 October 2026',
  read='Song, Havlin and Makse, Nature 433, 392 (2005) (cluster growing); the Fractals and Scaling course (Santa Fe Institute), units on box counting and scaling.',
  did='Measured the mass&ndash;radius curve M(r) and the local dimension d(r) of MOF-5 boxes of about 1000 cells and of the seven polyhedra of stage 10 at two sizes, and calibrated the method on a path, a square grid and a cubic grid.',
  code='<code>code/spectrum_shape_relation/run_04_dimension_profile_of_crystal_particles.py</code>, six new checks in <code>check_spectrum_shape_relation.py</code>, step 4 of <code>Spectrum_Shape_Relation.ipynb</code>.',
  out='Cube, plate and rod have the local dimension of a 3D, 2D and (nearly) 1D lattice; r&frac12;/D separates the cube, truncated cube and truncated octahedron predicted for MOF-5 (<a href="relation.html#dimension-profile">Spectrum &harr; Shape, Test 4</a>).',
  mistakes=[('The first draft explained the local dimension staying below 3 by the linkers, which add a step without branching. The cubic grid, which has no linkers, also peaks at 2.64, so the cause is the finite size of the graph and the lattice itself.', None)],
  fix='Reference lattices were added to the calculation, and particles are compared with them rather than with the ideal 1, 2 and 3.',
  why=[('Why calibrate on lattices of known dimension?', 'On a finite graph d(r) never reaches its ideal value; only a reference computed the same way shows what a 1D, 2D or 3D object gives at that size.'),
       ('Does this predict crystal shape?', 'No. It identifies a shape from a particle graph; which shape a MOF grows still comes from the morphology models.')]),
]

OPEN = [
 ('DFT check of MOF-5 and UiO-66 face energies', 'Kshitij', 'Decides between UFF and CHGNet, which disagree for these two MOFs.'),
 ('ZIF-8 CHGNet run', 'Rohith', 'The notebook does not find ZIF-8\'s symmetry with hydrogens; needs a CIF or code fix first.'),
 ('Choose the hybrid weight on some MOFs and test it on others', 'Radha', 'Only then can the blend be called better or worse than either method.'),
 ('More MOFs with known crystal shapes', 'Rohith, Radha', 'Four MOFs cannot rank methods.'),
 ('Solvent, modulator and temperature in the energies', 'Isha', 'Real shapes depend on them; no model here contains them.'),
 ('Spectrum of the deformed-cell plates and rods', 'Radha', 'The one place where the spectrum did respond to shape.'),
 ('One reproducible notebook per topic', 'Radha', 'Every result already has a script; notebooks make each one runnable in one place.'),
]

UNUSED = [
 ('MOFid / MOFkey string assembly (<code>code_07a/b</code>) and the Systre export (<code>code_06</code>)', 'Built in Stage 1 as part of the faithful translation of [1]; not used by any morphology result. Kept because the decomposition they belong to is used.'),
 ('Laplacian fingerprint and defect pages', 'First-half explorations; not part of the current argument. Kept as teaching material.'),
 ('Two withdrawn bands', 'Kept visible with the reasons, as required for an honest record; not used for any conclusion.'),
]

# ---- Why each paper was read: (paper, what we needed from it, where it is used) -----------------
PAPERS = [
 ('[1] Bucior et al. 2019, MOFid / metal-oxo', 'A published, reproducible rule to cut a MOF into metal clusters and linkers', 'Every graph in the project (<code>code_01</code>&ndash;<code>code_07</code>)'),
 ('[2] Xiao, Wang, Li 2021, NMFA / iNMFA', 'A method that summarises a network across all scales in one curve; its exact &tau;(q) definition', 'The spectrum (<code>code_10</code>, <code>code_12</code>)'),
 ('[3] Song, Havlin, Makse 2005', 'Box covering, the way the spectrum measures mass at each scale', 'Box covering in <code>code_12</code>'),
 ('[4] Systre, [5] RCSR, [6] SBUs', 'Names and checks for the nets (pcu, tbo, sod, fcu) and the building-unit idea', 'Checking the four demonstration graphs'),
 ('[7] MOFX-DB, [8] hMOF, [9] CoRE MOF 2019', 'Real and hypothetical structures to test on, and the difference between them', 'The bands; the 55 CoRE MOFs of the relation test'),
 ('[10] Cordero 2008 covalent radii', 'Distances at which two atoms count as bonded', 'Bond perception (<code>code_02</code>)'),
 ('[11]&ndash;[14] HKUST-1, MOF-5, ZIF-8, UiO-66', 'The four well-known MOFs with known structures and four different nets', 'Every test in both halves'),
 ('[20] Chen et al. 2020', 'Evidence that one MOF chemistry gives many shapes, and the link-counting argument', 'The panel question; Phase 3 attachment numbers'),
 ('[22] Hartman&ndash;Perdok, [23] Wulff', 'How face growth rates and face energies decide a crystal\'s shape', 'BFDH, graph rule, Wulff (Phases 1&ndash;4)'),
 ('[28] spglib', 'The space group of each CIF, needed to know which faces exist', 'Allowed faces (Phase 1)'),
 ('[29] UFF, [21] Wu and Jiang 2024', 'A force field covering every element in MOFs, and a MOF workflow using it', 'Face energies (Phase 4)'),
 ('Deng et al. 2023, CHGNet; pymatgen', 'A machine-learned potential and a slab builder, for a second set of face energies', 'Keerthi\'s notebook, <code>chgnet_post.py</code>'),
 ('Cravillon 2012, Liu 2016, Cubillas 2012, Umemura 2011, Butova 2023 and the other dataset papers', 'What real crystals of these MOFs look like, and under which conditions', 'The benchmark on the Experiment page'),
]

# ---- Why each notebook exists: (notebook, purpose, what it produces, status) -------------------------
NOTEBOOKS = [
 ('<code>notebooks/spectrum/pipeline_walkthrough_full.ipynb</code>', 'Teach the decomposition: every module of the MOFid pipeline with its real code beside a 3D model', 'A self-contained walkthrough for newcomers and the guide', 'Current, teaching'),
 ('<code>notebooks/spectrum/mof_band_analysis.ipynb</code>', 'First spectrum band on database MOFs relevant to xenon separation, chosen objectively instead of by hand', 'The 77-framework band', 'Withdrawn result, kept for the record'),
 ('<code>notebooks/spectrum/real_mof_band.ipynb</code>', 'The same band on 61 real CoRE MOFs', 'The 61-framework band', 'Withdrawn result, kept for the record'),
 ('<code>notebooks/morphograph_mof/MorphoGraph_hybrid.ipynb</code>', 'Give any teammate BFDH, Wulff and blended shapes for any CIF in seconds, without a GPU', 'Shapes and face energies for one CIF', 'Current'),
 ('<code>notebooks/morphograph_mof/MorphoGraph_MOF_revised.ipynb</code> (Keerthi)', 'Machine-learned (CHGNet) face energies from relaxed slabs, as a second energy source', 'Slab energies and the result folders in <code>data/chgnet_morphograph_runs/</code>', 'Run for MOF-5, HKUST-1, UiO-66 and hMOF-0'),
 ('Coarse-grained spectrum, Wulff-shape and morphology notebooks in Google Colab (Keerthi)', 'Working copies of the spectrum and morphology calculations, linked on the <a href="resources.html#notebooks">Resources</a> page', 'Spectra and shapes for single MOFs', 'Current working copies'),
 ('<code>notebooks/morphograph_mof/MorphoGraph_MOF_colab_4MOFs.ipynb</code> (Rohith)', 'The same science with the prompts replaced by settings, so the four MOFs run unattended on a GPU', 'The three result folders used on the Experiment page', 'Run; ZIF-8 missing'),
 ('<code>notebooks/morphograph_mof/MorphoGraph_MOF_colab_symmetric_slabs.ipynb</code>', 'Test whether symmetric slabs give individual face energies', 'Nothing yet', 'Written, not run; a dry run showed the symmetric slabs are high-energy, so it is optional'),
 ('<code>code/spectrum_shape_relation/Spectrum_Shape_Relation.ipynb</code>', 'Test whether the first-half spectrum is related to the second-half shapes', 'The three results on the Spectrum &harr; Shape page', 'Run by Radha Krishna, 15/15 checks passed'),
]

# ---- Defending the key decisions: (decision, purpose, likely objection, answer) -------------------------
DECISIONS = [
 ('Use the building-block graph, not the atom graph', 'Connectivity of clusters and linkers is what defines a MOF\'s framework', 'You throw away chemistry', 'Chemistry returns in the second half through face energies; the graph is used where connectivity is the question.'),
 ('Withdraw the spectrum bands', 'Only publish numbers that describe the MOF', 'You could have tuned the parameters', 'The width grows with graph size on every net and never converges; tuning would hide that, not fix it.'),
 ('Start the shape work with BFDH', 'Get a shape for any MOF from the cell alone', 'BFDH ignores chemistry', 'That is why Wulff (energies) and the graph rule (bonds) were added as independent second and third methods.'),
 ('Prove propositions, not only draw shapes', 'The panel asked for a mathematical demonstration', 'The shapes are well known', 'Known for simple crystals; here each rule is stated for the MOF case and checked numerically in the browser.'),
 ('Use UFF for face energies', 'Energies for every face of every MOF in seconds', 'Why not DFT?', 'DFT costs hours per slab; UFF is the baseline and a DFT spot check on the faces that matter is planned.'),
 ('Combine BFDH and Wulff with a weight w', 'Test whether geometry and energy together beat either alone', 'Any weight can be tuned to fit', 'True, so no best weight is claimed; it must be chosen on some MOFs and tested on others.'),
 ('Use the cleavage energy from the CHGNet slabs', 'Get one usable energy per face from slabs that only give pairs of faces', 'It is not a true surface energy', 'Correct, it is an upper bound on the lowest termination energy, and it is reported as such.'),
 ('Benchmark only additive-free crystals', 'Compare like with like', 'Most real crystals use additives', 'No model here contains an additive; comparing with additive-grown crystals would test something the models do not represent.'),
 ('Hold graph size fixed in every comparison', 'Avoid the mistake that killed the first-half results', 'You may remove real signal', 'Both raw and size-controlled numbers are reported side by side, so nothing is hidden.'),
 ('Keep withdrawn results and mistakes visible', 'An honest, checkable record', 'It makes the project look weaker', 'It shows which results survived checking, which is what makes the surviving ones trustworthy.'),
]


def stage_html(st):
    mist = ''.join(
        f'<li>{t}' + (f' <a href="lessons.html#{a}">(details)</a>' if a else '') + '</li>' for t, a in st['mistakes'])
    rows = [('Purpose of this step', st['purpose']), ('What we read', st['read']), ('What we did', st['did']), ('Code and notebooks', st['code']),
            ('What came out', st['out']),
            ('Mistakes found here', f'<ul class="tight">{mist}</ul>' if mist else 'None recorded at this stage.'),
            ('How they were corrected', st['fix'])]
    body = ''.join(f'<tr><td class="dt-label" style="width:11rem">{a}</td><td class="dt-note">{b}</td></tr>' for a, b in rows)
    why = ''.join(f'<dt>{q}</dt><dd>{a}</dd>' for q, a in st['why'])
    return (f'      <h2 class="section-title" id="{st["id"]}" data-toc="{st["title"].split(". ", 1)[0]}"><span class="stitle-num">0</span>{st["title"]}</h2>\n'
            f'      <p class="section-sub"><b>When:</b> {st["when"]}</p>\n'
            f'      <div class="table-wrap"><table class="data-table journey"><tbody>{body}</tbody></table></div>\n'
            + (f'      <h3 class="sub-head">Why this and not something else</h3>\n      <dl class="qa">{why}</dl>\n' if why else ''))


def main():
    parts = ['''      <h2 class="section-title" id="j0" data-toc="How to read this page"><span class="stitle-num">0</span>How to Read This Page</h2>
      <dl class="bridge"><dt>You know</dt><dd>Nothing yet. This page is the shortest route through the whole project.</dd><dt>This page</dt><dd>Follows the work in the order it happened: the papers we read, what we built from them, which code and notebooks produced which results, every mistake found on the way and how it was corrected, and why each method was chosen over the alternatives.</dd><dt>Which lets us</dt><dd>See how each result depends on the ones before it, and answer "why did you do it this way?" for every step.</dd></dl>
      <p class="sd">The project has two halves. The <b>first half</b> (Stages 1&ndash;4) asked whether a number computed from a MOF\'s connectivity can rank MOFs. After Panel Review 1 the <b>second half</b> (Stages 5&ndash;9) answers the panel\'s question about crystal shapes. Stage 10 joins the two. Reference numbers in square brackets point to the <a href="references.html">References</a> page; every mistake links to its full entry on the <a href="lessons.html">Mistakes</a> page.</p>
      <div class="table-wrap"><table class="data-table"><thead><tr><td>Stage</td><td>When</td><td>In one line</td></tr></thead><tbody>''' +
             ''.join(f'<tr><td class="dt-label"><a href="#{s["id"]}">{s["title"].split(". ", 1)[0]}</a></td><td class="dt-note">{s["when"]}</td><td class="dt-note">{s["title"].split(". ", 1)[1]}</td></tr>' for s in STAGES) +
             '</tbody></table></div>\n']
    parts += [stage_html(s) for s in STAGES]
    parts.append('''      <h2 class="section-title" id="j-papers" data-toc="Why each paper"><span class="stitle-num">0</span>Why We Read Each Paper</h2>
      <div class="table-wrap"><table class="data-table" id="j-papers-table"><thead><tr><td>Paper</td><td>What we needed from it</td><td>Where it is used</td></tr></thead><tbody>''' +
                 ''.join(f'<tr><td class="dt-label">{a}</td><td class="dt-note">{b}</td><td class="dt-note">{c}</td></tr>' for a, b, c in PAPERS) +
                 '''</tbody></table></div>
      <h2 class="section-title" id="j-notebooks" data-toc="Why each notebook"><span class="stitle-num">0</span>Why Each Notebook Exists</h2>
      <div class="table-wrap"><table class="data-table" id="j-notebooks-table"><thead><tr><td>Notebook</td><td>Purpose</td><td>What it produces</td><td>Status</td></tr></thead><tbody>''' +
                 ''.join(f'<tr><td class="dt-label">{a}</td><td class="dt-note">{b}</td><td class="dt-note">{c}</td><td class="dt-note">{d}</td></tr>' for a, b, c, d in NOTEBOOKS) +
                 '''</tbody></table></div>
      <h2 class="section-title" id="j-decisions" data-toc="Defending each decision"><span class="stitle-num">0</span>Defending Each Key Decision</h2>
      <div class="table-wrap"><table class="data-table" id="j-decisions-table"><thead><tr><td>Decision</td><td>Purpose</td><td>A panel might say</td><td>Our answer</td></tr></thead><tbody>''' +
                 ''.join(f'<tr><td class="dt-label">{a}</td><td class="dt-note">{b}</td><td class="dt-note">{c}</td><td class="dt-note">{d}</td></tr>' for a, b, c, d in DECISIONS) +
                 '''</tbody></table></div>
''')
    parts.append('''      <h2 class="section-title" id="j-now" data-toc="Where we are now"><span class="stitle-num">0</span>Where We Are Now</h2>
      <ul class="sd">
        <li><b>Answered:</b> the panel\'s question. From one established unit cell the project generates several morphologies, by growth rates (BFDH, graph rule), by energies (Wulff with UFF or CHGNet) and by changing the cell, with the mathematics proved and checked.</li>
        <li><b>Not yet answered:</b> which method predicts real crystals best. Only MOF-5 separates the methods, the force-field cube depends on one constant, and the machine-learned energies are unvalidated for MOF surfaces.</li>
        <li><b>Carried over from the first half:</b> the periodic quotient graph (used for face counting) and the habit of controlling size. The spectrum itself responds only to flat or long particles, not to compact crystal shapes.</li>
      </ul>
      <h3 class="sub-head">Open work, in order of importance</h3>
      <div class="table-wrap"><table class="data-table"><thead><tr><td>Task</td><td>Who</td><td>Why it matters</td></tr></thead><tbody>''' +
                 ''.join(f'<tr><td class="dt-label">{a}</td><td class="dt-note">{b}</td><td class="dt-note">{c}</td></tr>' for a, b, c in OPEN) +
                 '''</tbody></table></div>
      <h3 class="sub-head">Built but not used by the current argument</h3>
      <div class="table-wrap"><table class="data-table"><thead><tr><td>Item</td><td>Why it exists and why it stays</td></tr></thead><tbody>''' +
                 ''.join(f'<tr><td class="dt-label">{a}</td><td class="dt-note">{b}</td></tr>' for a, b in UNUSED) +
                 '''</tbody></table></div>
''')
    open(OUT, 'w', encoding='utf-8').write(''.join(parts))
    print('wrote', OUT, len(STAGES), 'stages')


if __name__ == '__main__':
    main()
