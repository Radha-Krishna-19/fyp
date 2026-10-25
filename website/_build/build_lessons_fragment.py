#!/usr/bin/env python3
"""Writes fragments/lessons.before.html: every mistake the team made, in plain words and in
technical words. The content is the list ENTRIES below; each entry has the same six rows so a
reader can compare them. Evidence for each entry is in the file named in `where`."""
import os, html

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'fragments', 'lessons.before.html')

# (id, title, plain, why_chosen, why_wrong, technical, fix, where)
SPECTRUM = [
 ('l-tau', 'The straight-line fit that flattened every spectrum',
  'We drew a best-fit line through the data in the usual way. The paper we were copying draws it differently, and our way hid the very feature we were looking for.',
  'A free-intercept least-squares line is the default in every library, and it fits the points well.',
  'The source paper defines &tau;(q) as the slope of a line forced through the origin. A free intercept absorbs part of the signal, so the apex of the spectrum was flattened and no spectrum passed the validity test (0 of 77).',
  'The correct estimator is &tau; = &Sigma;xy / &Sigma;x&sup2; (through the origin). With it 77 of 77 spectra were valid. A good R&sup2; on the wrong model says nothing about whether the model is the right one.',
  'Refit through the origin; keep a separate free-intercept R&sup2; only as a test of whether a power law exists at all.',
  '<code>code/spectrum_pipeline/code_12_converged_band.py</code>, defect D in its header'),
 ('l-induced', 'Analysing only the "important" nodes',
  'We picked the most connected building blocks and studied only those. But in a MOF the important blocks never touch each other directly, so there was nothing to study.',
  'It is natural to take the influential nodes and look at the graph they form.',
  'Metal clusters are joined to each other only through linkers. The subgraph induced on the influential nodes therefore has no edges, and every distance in it is infinite.',
  'Cover the whole graph with boxes and read the probability measure only at the influential nodes (the paper\'s procedure).',
  'Rewrote the box covering to run on the full graph.',
  '<code>docs/project_notes.md</code> defect 2; <code>code_12_converged_band.py</code>'),
 ('l-order', 'Averaging in the wrong order',
  'We averaged first and took the logarithm afterwards. Doing it the other way round gives a different number, and ours was far too small.',
  'Averaging before transforming looks harmless and is cheaper.',
  'ln of an average is not the average of ln. Averaging p<sub>i</sub>(r) over trials before taking logs biased the spectrum narrow by more than a factor of 10.',
  'Build Z(q, r) per trial, take ln Z per trial, then average the logarithms (Jensen\'s inequality gives the direction of the bias).',
  'Changed the order and kept a test that fails if it is reversed.',
  '<code>docs/project_notes.md</code> defect 3'),
 ('l-period', 'Forgetting that a crystal repeats',
  'We built the graph of one unit cell only. A crystal is that cell repeated in all directions, so bonds that leave the cell and re-enter on the other side were lost.',
  'One cell is small and easy to handle.',
  'Without the periodic images, UiO-66\'s 12-connected zirconium cluster appeared with the wrong number of neighbours, or the whole cell collapsed to a star.',
  'Use the labelled quotient graph: each edge carries the integer lattice translation t it crosses, so the infinite graph is recovered exactly by tiling.',
  'Added the translation label to every edge; both the Python and the browser versions use it.',
  '<code>code_09_network_analysis.py</code>; the <a href="network.html">Network</a> page'),
 ('l-classes', 'Three classes narrower than the measurement error',
  'We split the structures into "Narrow", "Medium" and "Wide" by cutting the list of numbers into three parts. Two identical structures ended up in different classes, because the cut was finer than the noise in the number.',
  'Cutting at the 25th and 75th percentiles is a quick, common way to make classes.',
  'The Medium class was 0.032 wide while each structure\'s error bar was 0.013 to 0.098. hMOF-94 and hMOF-96 are the same graph yet fell in different classes, so the labels described the random seed.',
  'A class boundary is meaningful only if the class width exceeds the uncertainty of the quantity being cut.',
  'The function that assigns classes now refuses to run when the class width is smaller than the error bar.',
  '<code>assign_classes()</code> in <code>code_12_converged_band.py</code>; <a href="results.html">Results</a> page'),
 ('l-size', 'A result that was really just "bigger graph"',
  'The spectrum width grew whenever the graph was bigger. We first read this as a property of the chemistry (for example pore size). Bigger graphs simply give bigger numbers, so the claim fell apart.',
  'The correlation was strong (r about +0.7) and a strong correlation looks like a finding.',
  'The width &Delta;&alpha; rises almost exactly linearly in ln(diameter) (R&sup2; at least 0.998 on all four nets) with a different slope on each net, so size explains most of the variation and was never held fixed. The pore-size claim and the four-structure real-MOF claim were withdrawn.',
  'Always report the size-controlled (partial) correlation next to the raw one, and compare structures only at a size where the quantity has stopped moving. It never stopped moving here.',
  'Both published bands are marked withdrawn on the Results page with their reasons; the numbers stay visible.',
  '<a href="results.html">Results</a> page; <code>data/spectrum_descriptors/size_scaling/</code>'),
 ('l-graph', 'Describing one graph and computing on another',
  'The text said the spectrum was computed on the simplified building-block graph. The published numbers were actually computed on the full atom graph. The words and the numbers did not match.',
  'The coarse-grained graph was the intended method, and the notebooks ran without error, so the mismatch was not noticed.',
  'Both notebooks called the spectrum on the atomic supercell. The coarse graph only supplied counts. A first correction then wrongly stated "diameter 8 to 12", which belongs to a different run (the atomic graphs have diameters 34 to 104).',
  'Four different estimators exist in the project; each is listed with its graph, influential set and radii in <code>docs/project_notes.md</code> so that they are not mixed again.',
  'Documented which graph each published number used and withdrew both bands.',
  '<code>docs/project_notes.md</code>, "Which graph each published number was computed on"'),
 ('l-small', 'Graphs that were too small to measure a scaling law',
  'To keep the computer fast we capped the number of atoms. That made the graphs so small that there was hardly any range over which a "scaling" could be measured.',
  'A cap on atoms keeps memory low.',
  'The cap allowed only about 430 building blocks, a diameter of 8 to 12, less than one decade of radii. One structure was fitted over four points.',
  'Tile the quotient graph combinatorially instead of building atoms. Verified that coarse-graining first and replicating second gives the identical graph (full isomorphism check on five cases) while being 48 to 675 times cheaper.',
  'Coarse-grain first; a diameter gate (at least 8) refuses spectra on graphs that are too small.',
  '<code>code/spectrum_pipeline/_prove_ordering_equivalence.py</code>'),
 ('l-degenerate', 'A sample where most structures were the same graph',
  'Most of our 77 test MOFs turned out to be the same net with different organic parts. Because the simplified graph deletes the organic detail, they looked identical.',
  'The structures came from one database sample and looked varied by name.',
  '48 of 76 share 256 nodes, 384 edges and diameter 12 (a 4&times;4&times;4 pcu net). A band over such a set is narrow for a trivial reason.',
  'Sub-band work needs a deliberate spread of nets (pcu, tbo, sod, fcu, rht), not random sampling.',
  'A guard refuses to report a band unless the sample holds more than one net. One net (rht) could not be found with the tools available, and this is stated.',
  '<code>require_topological_diversity()</code> in <code>code_12</code>; <code>code_16_topological_diversity.py</code>'),
]

MORPH = [
 ('m-cubic', 'Code that only knew cubic crystals',
  'Our first notebook gave wrong shapes when we gave it a MOF that is not cubic. It silently assumed every crystal is a cube-like box.',
  'The four demonstration MOFs are all cubic, so the labels (100), (110), (111) were hard-wired.',
  'For other crystal systems the face names and the symmetry-equivalence rule are different. The notebook printed cubic-style names and the wrong shape for the hMOF-0 test.',
  'Faces must be grouped by the crystal\'s own point-group operations. The package now finds the symmetry with spglib, converts primitive-cell indices to conventional ones, and names families by that rule.',
  'Added a guard that stops when there is no cell, then wrote the general version (<code>hybrid.py</code>), checked on eight CoRE MOFs of six crystal systems.',
  '<code>mofmorph/hybrid.py</code>; <a href="experiment.html">Experiment</a>, "Any framework"'),
 ('m-hydrogen', 'Leaving out the hydrogen atoms in the energy',
  'For ZIF-8 we computed the energy of a face without the hydrogen atoms. The face looked cheaper than it is, by half.',
  'The symmetry of ZIF-8 is only found when hydrogens are left out, so the helper dropped them, and the energy code reused that atom list.',
  'The {111} cleavage energy of ZIF-8 was 0.312 J/m&sup2; and is 0.619 J/m&sup2; with hydrogens. The shape did not change, but the number was wrong.',
  'Symmetry and energy need different atom lists. <code>atoms_for_energy</code> rebuilds the full cell for the energy calculation.',
  'Found in the independent review of 2026-10-14; fixed and covered by a test.',
  '<code>REVIEW_2026-10-14.md</code>; <code>mofmorph/hybrid.py</code>'),
 ('m-never', 'Saying CHGNet "will never" give a shape',
  'We told the team the machine-learning notebook could never give a Wulff shape for MOFs. That was too strong. It gives no shape as written, and there are ways to fix it.',
  'The notebook returned no surface energies and we generalised from that.',
  'Each slab gives only &gamma;<sub>top</sub> + &gamma;<sub>bottom</sub>, and a MOF face has more termination unknowns than independent equations (MOF-5 {111}: 37 unknowns, rank 20). That is a limit of this notebook\'s procedure, not of CHGNet.',
  'Cleavage energy &gamma;<sub>cl</sub> = min p/2 is an upper bound on the lowest termination energy and does give shapes. Other fixes (capped slabs, symmetric slabs) are listed as untested options.',
  'Reworded the message, implemented the cleavage workaround, and tested whether symmetric slabs help (they are high-energy terminations, so they do not).',
  '<a href="experiment.html">Experiment</a>, sections 4 and 5'),
 ('m-trustuff', 'Trusting the force-field cube because it matched experiment',
  'Our force-field model gave a cube for MOF-5, which is what experiments show, so we treated it as validated. But the cube disappears if one setting is changed.',
  'It matched the experimental shape, and the machine-learning route disagreed, so the simple model looked better.',
  'The Phase 4 energy uses one flat cost of 70 kcal/mol for every bond. At half or a quarter of that cost for metal&ndash;ligand bonds the MOF-5 shape becomes a truncated cube or a truncated octahedron. A match found with a free setting is weak evidence.',
  'Run a sensitivity test on every free constant before quoting the result. The decisive test is a DFT calculation on a few faces.',
  'Added the bond-cost sensitivity test, quote the cube only with this caveat, and wrote the DFT plan for Kshitij.',
  '<a href="experiment.html">Experiment</a> section 6; <code>code/morphology/DFT_CHECK_PLAN.md</code>'),
 ('m-oneshape', 'One "correct" shape per MOF',
  'We compared our shapes with a single experimental shape per MOF. In the laboratory the same MOF gives different shapes depending on what it is grown in and for how long.',
  'A short table of expected shapes is easy to use.',
  'ZIF-8 changes from cubes to rhombic dodecahedra over about four hours; HKUST-1 changes from octahedron to cube as modulator is added. UiO-66 forms clean octahedra only with a modulator, and our first source for it was a citation, not a primary image.',
  'The dataset must record solvent, additive, temperature and time. Benchmarks use additive-free crystals because no model here contains an additive.',
  'Rohith built a dataset of 134 records from 35 papers with every condition; UiO-66 was then confirmed from two primary papers; eleven records with no identifiable source are held out.',
  '<code>data/experimental_morphology/</code>; <a href="experiment.html">Experiment</a> section 2'),
 ('m-fragment', 'Misreading broken pieces in the CHGNet slabs',
  'Some computed slabs contained loose pieces. We first thought a metal cluster had been torn in two. It was the organic linker that had been cut.',
  'Our bond-distance rule said the pieces were fragments and we assumed the weakest part is the metal cluster.',
  'The loose pieces are H, O, CH or C<sub>2</sub>H<sub>2</sub> and CO<sub>2</sub> released from cut linkers. Removing the fragmented slabs changes no shape.',
  'Count the connected pieces before and after relaxation and look at what they are, instead of inferring from the bond rule.',
  'Corrected the statement on the site; the slab check is a script that can be rerun.',
  '<code>slab_check.py</code>; <a href="experiment.html">Experiment</a> section 5'),
 ('m-shapes', 'Small wrong statements about shapes',
  'We said HKUST-1 is "a cube with cut corners" and that MOF-5 would have cut corners. Neither was right.',
  'Remembered descriptions of typical shapes.',
  'The force-field Wulff shape of HKUST-1 is a truncated octahedron (about 77% {111}); the MOF-5 Wulff shape is a clean cube.',
  'Always read the shape from the computed face fractions, not from memory.',
  'Corrected on the site and in the handoff notes.',
  '<a href="surface_energy.html">Surface Energy</a> page'),
 ('m-tune', 'A free weight that can be tuned to the test',
  'The hybrid rule has one dial, the weight w between BFDH and Wulff. With only four MOFs, any "best" setting is simply the one that happens to suit those four.',
  'It is tempting to report the weight that scores best.',
  'With four test structures and one free parameter, the best w is fitted to the test set, so it says nothing about new MOFs.',
  'Choose w on one set of MOFs and judge it on others (held-out), and show it at a fixed w until then.',
  'The site shows w = 0.5 only and does not rank it. Held-out testing is the next step.',
  '<a href="hybrid.html">Hybrid</a> page'),
]

AUDIT = [
 ('l-uio66', 'Claiming a UiO-66 match that the benchmark does not support',
  'Several pages said our methods "match" UiO-66 because they give an octahedron. Our own experimental dataset says that UiO-66 grown without additives forms poorly faceted cubes; octahedra appear only when a modulator is added.',
  'The octahedron is the UiO-66 shape most often shown in the literature, and the first comparison was made with one shape per MOF, before the dataset recorded the conditions.',
  'A model with no solvent and no modulator must be compared with crystals grown without them. The octahedra in the literature are grown with acetic or benzoic acid, so they are not a test of a bare-crystal model.',
  'The benchmark is the most frequent shape among additive-free records (<code>data/experimental_morphology/compare/comparison.csv</code>): cube (2 records) for UiO-66, octahedron (5) for HKUST-1, cube (8) for MOF-5, rhombic dodecahedron (10) for ZIF-8. No model gives the UiO-66 cube, so UiO-66 confirms nothing.',
  'The Overview, Morphology and Hybrid pages now take the experimental shape from <code>comparison.csv</code>, the same file the Experiment page uses, and state that the UiO-66 benchmark is weak.',
  '<a href="experiment.html">Experiment</a>, <a href="hybrid.html">Hybrid</a>'),
 ('l-status', 'Status tables that fell behind the work',
  'The Morphology page still listed the surface-energy work as "Not started" a week after it was finished, and said the spectrum was not used in the morphology half after a page testing exactly that had been added.',
  'Each page was written when its phase was done; earlier pages were not revisited.',
  'A reader who opens the Morphology page first sees a project that stopped at Phase 3, and a statement that contradicts the Spectrum &harr; Shape page.',
  'Status was recorded in three places (Morphology page, Team page, project notes) with no single source.',
  'All phase tables were rewritten with one numbering (Phases 0 to 6, with 4b to 4h), and the audit below checks every page against the result files.',
  '<a href="morphology.html">Morphology</a>, <a href="team.html">Team</a>'),
 ('l-provenance', 'Figures that did not say where they came from',
  'Most pictures on the site had a caption saying what they show but not which program drew them or from which data, so a reader could not check them.',
  'The figures were drawn by the same scripts that produced the numbers, so the link seemed obvious to the people who made them.',
  'It is not obvious to anyone else, and four early figures had in fact been drawn by scripts that were not kept.',
  'A figure is evidence only if its producing script and input data are named and can be rerun.',
  'One table (<code>website/_build/figure_sources.py</code>) names the script and data of every image; the build adds a Source line under each figure, and <code>tests/test_pages.js</code> fails if an image has none. The four figures whose scripts were lost say so.',
  'every page with a figure'),
 ('l-footer', 'A footer that claimed more than was true',
  'Every page ended with "every number on this site is computed in your browser". That was true for the first pages and became false when the morphology pages were added, whose numbers come from the Python results.',
  'The sentence was written for the original single-page site and copied into the shared page template.',
  'A false general statement on every page undermines the true specific ones.',
  'The morphology, experiment and relation pages are generated from JSON and CSV result files by the build scripts; only the network, spectrum and shape-explorer pages compute in the browser.',
  'The footer now states both routes and that the test suites check every page against the result files.',
  'the footer of every page'),
 ('l-copies', 'Work kept in more than one place',
  'Recent work existed only on one computer, an older copy of the experimental dataset was on GitHub, and the same CHGNet results were stored twice (as zip files and as folders). It was not clear which copy was the latest.',
  'Work was done in Colab and on a laptop under deadline, and files were copied rather than committed.',
  'Two copies of a result can disagree without anyone noticing; here the GitHub copy of the dataset lacked the verified/unverified split that the website already used.',
  'Each file of the local copy was compared with GitHub by size and content before merging; the CHGNet folders were checked to be identical to the zips (1,118 files) before the zips were removed, and every script was rerun to confirm identical results.',
  'One repository layout (<code>code/</code>, <code>data/</code>, <code>notebooks/</code>, <code>docs/</code>, <code>website/</code>), one copy of every file, and GitHub as the only shared copy.',
  'root <code>README.md</code>'),
]

SMALL = [
 ('Plot title said "MOF-5" for a different structure', 'The title was a fixed name, not read from the file.', 'Set the NAME field; titles now follow the input.'),
 ('Primitive-cell indices mapped to nothing', 'HKUST-1\'s file is a primitive cell, so (hkl) are not the usual cubic indices.', 'Convert through the transformation matrix between the primitive and the conventional cell.'),
 ('Crash looking up a face in the opposite direction', 'A face and its negative are different keys.', 'One canonical family key (<code>family_of</code>).'),
 ('"Max relax steps" typed as 4', 'The first hMOF-0 CHGNet run stopped after 4 steps because a prompt default was overtyped.', 'Re-ran with the default of 500 steps.'),
 ('Wrong zip uploaded (an older copy)', 'Two project folders looked alike.', 'Noticed because the folder showed no changes in git, then asked for the right zip.'),
 ('CSS tokens that referred to themselves', 'Custom properties such as <code>--node:var(--node)</code> form a cycle and resolve to nothing, so colours vanished on every page.', 'Never alias a token to itself.'),
 ('Sideways scrolling on every page', 'Wide tables and hidden pop-ups stretched the page.', '<code>min-width:0</code> on the content grid and <code>overflow-x:clip</code>.'),
 ('"Grows as 0.78 ln D" on the Team page', 'The slope of HKUST-1 was quoted as if it held for every net.', 'Now 0.69&ndash;0.89 depending on the net, as on the Results page.'),
 ('<code>npm test</code> called two test files that no longer existed', 'The test list in <code>package.json</code> was written before the site was split into pages.', 'A runner (<code>run_all_tests.js</code>) now runs every <code>test_*.js</code> file.'),
 ('A temperature range printed as "125&ndash;125 &deg;C"', 'The range was formatted without checking whether its ends were equal.', 'A single value is printed when both ends are equal.'),
 ('A team member\'s name spelt two ways', 'The name was typed from memory on some pages.', 'Every page now uses the spelling in the paper and the certificate (Kshitij).'),
 ('Website still said 104 records, 28 papers, 14 MOFs', 'The Team page was not updated when the dataset grew.', 'Now 134 records from 35 papers for 12 MOFs, as on the Experiment page.'),
]

PATTERNS = [
 ('A number that looks good is trusted before it is stressed.', 'The size correlation, the force-field cube and the "best" weight all looked like results. Each fell when one more thing was varied (size, bond cost, test set).', 'Vary the thing you did not control, then report what survived.'),
 ('Code written for the examples at hand.', 'Cubic labels, hydrogens dropped, one-cell graphs. All four demonstration MOFs share properties that real MOFs do not.', 'Test on a deliberately different case (eight CoRE MOFs of six crystal systems).'),
 ('One value per thing that varies.', 'One shape per MOF, one class per structure. In both cases the real quantity depends on conditions or noise.', 'Record the conditions and the error bar next to every value.'),
 ('Words and numbers drifting apart.', 'The text described one graph and the code used another; the Team page lagged behind the dataset; status tables and shape claims lagged behind the results.', 'Numbers on this site are generated from the data files and checked by tests; claims that summarise results (the experimental shapes, the phase status) are read from the same files or checked in an audit.'),
]


def e(s):
    return s


def entry(x):
    i, title, plain, why, wrong, tech, fix, where = x
    rows = [('In simple words', plain), ('Why we chose it', why), ('Why it was wrong', wrong),
            ('The technical reason', tech), ('How we fixed it', fix), ('Where to see it', where)]
    body = ''.join(f'<tr><td class="dt-label" style="width:11rem">{a}</td><td class="dt-note">{b}</td></tr>' for a, b in rows)
    return (f'      <h3 class="sub-head" id="{i}">{title}</h3>\n'
            f'      <div class="table-wrap"><table class="data-table lesson"><tbody>{body}</tbody></table></div>\n')


def main():
    p = []
    p.append('''      <h2 class="section-title" id="ls-intro" data-toc="Why this page exists"><span class="stitle-num">0</span>Why This Page Exists</h2>
      <dl class="bridge"><dt>You know</dt><dd>The earlier pages state what we found. They mention fixes in passing.</dd><dt>This page adds</dt><dd>Every mistake the team made, in one place: what we did, why we did it, why it was wrong, and how it was put right, each in plain words and in technical words.</dd><dt>Which lets us</dt><dd>Trust the surviving results because the failed ones are shown, and avoid repeating them.</dd></dl>
      <p class="section-sub">Most of these mistakes were not careless. Each was a reasonable choice that failed when one more thing was checked. Finding them is part of the method, so they are kept on the site and not deleted. Withdrawn claims stay visible with their reasons.</p>
      <div class="callout" data-kind="How to read an entry">The row <b>In simple words</b> is for anyone. The row <b>The technical reason</b> is for the reader who wants the mathematics or the code. The other rows say what we believed at the time, what was actually wrong and what changed.</div>
''')
    p.append('''      <h2 class="section-title" id="ls-patterns" data-toc="Four patterns"><span class="stitle-num">0</span>Four Patterns Behind the Mistakes</h2>
      <div class="table-wrap"><table class="data-table"><thead><tr><td>Pattern</td><td>Where it showed up</td><td>The habit that fixes it</td></tr></thead><tbody>''' +
             ''.join(f'<tr><td class="dt-label">{a}</td><td class="dt-note">{b}</td><td class="dt-note">{c}</td></tr>' for a, b, c in PATTERNS) +
             '''</tbody></table></div>
''')
    p.append('''      <h2 class="section-title" id="ls-spectrum" data-toc="Part A: the spectrum work"><span class="stitle-num">0</span>Part A: The Spectrum Work (before the panel)</h2>
      <p class="section-sub">The first half of the project tried to describe each MOF by a number computed from its connectivity (the multifractal spectrum width &Delta;&alpha;) and to sort MOFs into classes with it. Nine mistakes were found. Their net effect is that the classes and the two published bands were withdrawn, and the method itself (the periodic quotient graph and the spectrum) was kept and corrected.</p>
''')
    p.extend(entry(x) for x in SPECTRUM)
    p.append('''      <h2 class="section-title" id="ls-morph" data-toc="Part B: the morphology work"><span class="stitle-num">0</span>Part B: The Morphology Work (after the panel)</h2>
      <p class="section-sub">After the panel asked for crystal shapes from the unit cell, a second set of mistakes was made, mostly in the last two weeks while the force-field, CHGNet and experiment parts were joined. Most were found by an independent review of the code and by comparing with real crystals.</p>
''')
    p.extend(entry(x) for x in MORPH)
    p.append('''      <h2 class="section-title" id="ls-audit" data-toc="Part C: the audit of 25 October 2026"><span class="stitle-num">0</span>Part C: Found in the Audit of 25 October 2026</h2>
      <p class="section-sub">Before the next phase every page of the site was compared with the result files and with every other page, and the repository was reorganised. These are the problems that check found; each is now fixed.</p>
''')
    p.extend(entry(x) for x in AUDIT)
    p.append('''      <h2 class="section-title" id="ls-small" data-toc="Smaller slips"><span class="stitle-num">0</span>Smaller Slips</h2>
      <div class="table-wrap"><table class="data-table"><thead><tr><td>What went wrong</td><td>Why</td><td>Fix</td></tr></thead><tbody>''' +
             ''.join(f'<tr><td class="dt-label">{a}</td><td class="dt-note">{b}</td><td class="dt-note">{c}</td></tr>' for a, b, c in SMALL) +
             '''</tbody></table></div>
      <h2 class="section-title" id="ls-next" data-toc="What is still not safe"><span class="stitle-num">0</span>What Is Still Not Safe</h2>
      <ul class="sd">
        <li>The force-field energies are unrelaxed, with no solvent, charges or temperature. They are a baseline, not a measurement.</li>
        <li>CHGNet has not been checked against DFT for MOF surfaces, so its shapes are not trusted either way until Kshitij's calculation is done.</li>
        <li>Only four MOFs have a clean experimental shape; no method can yet be ranked as better.</li>
        <li>The spectrum width still depends on size (see <a href="relation.html">Spectrum &harr; Shape</a>), and across 55 CoRE MOFs it carries no shape information beyond size; it cannot yet be used as a stand-alone classifier.</li>
      </ul>
''')
    open(OUT, 'w', encoding='utf-8').write(''.join(p))
    print('wrote', OUT, len(SPECTRUM), 'spectrum entries,', len(MORPH), 'morphology entries,', len(AUDIT), 'audit entries')


if __name__ == '__main__':
    main()
