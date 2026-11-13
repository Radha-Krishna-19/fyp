#!/usr/bin/env python3
"""
build_relation_fragment.py  ->  fragments/relation.before.html  (page relation.html, "Spectrum <-> Shape")

Every number on the page is read from the results of the notebook
    code/spectrum_shape_relation/Spectrum_Shape_Relation.ipynb
i.e. from code/spectrum_shape_relation/results/*.json. Nothing in a table is typed by hand.
The figures are website/figures/relation/*.png, drawn by make_figures_spectrum_shape_relation.py
from the same files. The run that produced the results is named in the provenance box, taken from
results/RUN_REPORT_spectrum_shape_relation.md.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SSR = os.path.join(ROOT, 'code', 'spectrum_shape_relation')
RES = os.path.join(SSR, 'results')
OUT = os.path.join(HERE, 'fragments', 'relation.before.html')

R1 = json.load(open(os.path.join(RES, '01_box_particles_MOF5.json')))
Z1 = json.load(open(os.path.join(RES, '01_box_particles_ZIF8.json')))
R2 = json.load(open(os.path.join(RES, '02_predicted_crystal_shapes_MOF5.json')))
R3 = json.load(open(os.path.join(RES, '03_core_mof_spectrum_vs_bfdh_shape.json')))
R4 = json.load(open(os.path.join(RES, '04_dimension_profile_MOF5.json')))
report = open(os.path.join(RES, 'RUN_REPORT_spectrum_shape_relation.md'), encoding='utf-8').read()
m = re.search(r'run at (\S+ \S+) on (\S+), Python (\S+), RECOMPUTE=(\w+)', report)
RUN_WHEN, RUN_WHERE, RUN_PY, RUN_RECOMP = m.groups() if m else ('?', '?', '?', '?')
WHERE = 'Google Colab (Linux)' if 'Linux' in RUN_WHERE else RUN_WHERE

NB = 'code/spectrum_shape_relation/Spectrum_Shape_Relation.ipynb'


def produced(script, outfile):
    return (f'<p class="provenance"><b>Produced by:</b> <code>{NB}</code> (step calling <code>{script}</code>), '
            f'output <code>{outfile}</code>.</p>')


# ---- step 1 tables -----------------------------------------------------------------------------
rows1 = ''.join(
    f'<tr data-shape="{r["label"]}"><td class="dt-label">{r["label"]}</td><td class="dt-value">{r["cells"]}</td>'
    f'<td class="dt-value">{r["nodes"]}</td><td class="dt-value">{r["diameter"]}</td>'
    f'<td class="dt-value">{r["width_mean"]:.3f} &plusmn; {r["width_sd"]:.3f}</td>'
    f'<td class="dt-value">{r["trend_prediction"]:.3f}</td><td class="dt-value">{r["excess_over_trend"]:+.3f}</td></tr>'
    for r in R1['shapes'])
cubes1 = ''.join(
    f'<tr data-cube="{r["box"][0]}"><td class="dt-label">{r["box"][0]}&times;{r["box"][1]}&times;{r["box"][2]}</td>'
    f'<td class="dt-value">{r["nodes"]}</td><td class="dt-value">{r["diameter"]}</td>'
    f'<td class="dt-value">{r["width_mean"]:.3f} &plusmn; {r["width_sd"]:.3f}</td></tr>' for r in R1['cubes'])
w1 = {r['label'].split()[0]: r for r in R1['shapes']}
zc = [c['components'] for c in Z1['cubes']]

# ---- step 2 table ------------------------------------------------------------------------------
rows2 = ''.join(
    f'<tr data-shape="{r["shape"]}|{r["target_blocks"]}"><td class="dt-label">{r["shape"]}</td>'
    f'<td class="dt-value">{r["target_blocks"]}</td><td class="dt-value">{r["blocks_in_largest_piece"]}</td>'
    f'<td class="dt-value">{r["diameter"]}</td><td class="dt-value">{r["width_mean"]:.3f} &plusmn; {r["width_sd"]:.3f}</td>'
    f'<td class="dt-value">{r["difference_from_cube_trend_at_equal_blocks"]:+.3f}</td>'
    f'<td class="dt-value">{r["difference_from_cube_trend"]:+.3f}</td></tr>' for r in R2['shapes'])
t2 = R2['cube_trend']
eqN = [r['difference_from_cube_trend_at_equal_blocks'] for r in R2['shapes']]
eqD = [r['difference_from_cube_trend'] for r in R2['shapes']]

# ---- step 3 table ------------------------------------------------------------------------------
rows3 = ''
for subset, tests in R3['tests'].items():
    for k, v in tests.items():
        if 'partial_p' not in v:
            continue
        rows3 += (f'<tr data-test="{subset}|{k}"><td class="dt-label">{subset}</td><td class="dt-note">{k}</td>'
                  f'<td class="dt-value">{v["n"]}</td><td class="dt-value">{v["spearman"]:+.3f} (p {v["spearman_p"]:.4f})</td>'
                  f'<td class="dt-value">{v["partial_spearman_size_controlled"]:+.3f} (p {v["partial_p"]:.3f})</td>'
                  f'<td class="dt-value">{v["partial_ci95"][0]:+.2f} to {v["partial_ci95"][1]:+.2f}</td></tr>')
A = R3['tests']['all usable']
ar = A['width vs aspect ratio']

# ---- step 4 tables -----------------------------------------------------------------------------
REF = {v['dimension']: (k, v) for k, v in R4['reference_lattices'].items()}
BX = {k.split()[0]: (k, v) for k, v in R4['boxes'].items()}
rows4a = ''.join(
    f'<tr data-ref="{d}"><td class="dt-label">{k}</td><td class="dt-note">ideal {d}D lattice</td>'
    f'<td class="dt-value">{v["blocks"]}</td><td class="dt-value">{v["d_peak"]:.2f}</td>'
    f'<td class="dt-value">{v["d_at_r_half_mean"]:.2f}</td></tr>' for d, (k, v) in sorted(REF.items(), reverse=True))
rows4a += ''.join(
    f'<tr data-box="{s}"><td class="dt-label">MOF-5 {k}</td><td class="dt-note">{s}</td>'
    f'<td class="dt-value">{v["blocks"]}</td><td class="dt-value">{v["d_peak"]:.2f}</td>'
    f'<td class="dt-value">{v["d_at_r_half_mean"]:.2f} &plusmn; {v["d_at_r_half_sd"]:.2f}</td></tr>'
    for s, (k, v) in BX.items())
P4 = {(p['shape'], p['target_blocks']): p for p in R4['polyhedra']}
SH4 = list(dict.fromkeys(p['shape'] for p in R4['polyhedra']))
rows4b = ''.join(
    f'<tr data-shape="{n}"><td class="dt-label">{n}</td>'
    + ''.join(f'<td class="dt-value">{P4[(n, t)]["blocks"]}</td><td class="dt-value">{P4[(n, t)]["diameter"]}</td>'
              f'<td class="dt-value">{P4[(n, t)]["r_half_over_D_mean"]:.3f} &plusmn; {P4[(n, t)]["r_half_over_D_sd"]:.3f}</td>'
              for t in (4000, 8000)) + '</tr>' for n in SH4)
def rh(n, t):
    return P4[(n, t)]['r_half_over_D_mean']
UFF, BL, BF, CH = 'UFF Wulff prediction', 'BFDH x Wulff blend w=0.5', 'BFDH prediction', 'CHGNet cleavage Wulff prediction'
gaps = []
for t in (4000, 8000):
    sd = max(P4[(n, t)]['r_half_over_D_sd'] for n in (UFF, BL, BF))
    gaps += [(rh(BL, t) - rh(UFF, t)) / sd, (rh(BF, t) - rh(BL, t)) / sd]
NCHK = 21

html = f'''      <h2 class="section-title" id="rel-intro" data-toc="What this page tests"><span class="stitle-num">0</span>What This Page Tests</h2>
      <dl class="bridge"><dt>You know</dt><dd>The spectrum width &Delta;&alpha; of the first half (<a href="spectrum.html">Spectrum</a>, <a href="results.html">Results</a>) and the predicted crystal shapes of the second half (<a href="morphology.html">Morphology</a>, <a href="hybrid.html">Hybrid</a>). Why shape matters: <a href="bridge.html">Why Shape</a>.</dd><dt>This page adds</dt><dd>Three calculations that test whether the two halves are related, and a fourth that applies the scaling idea behind the spectrum in a different form.</dd><dt>Which lets us</dt><dd>Say exactly which part of the earlier work carries over to morphology, and which does not.</dd></dl>
      <div class="callout" data-kind="Where every number on this page comes from">All tables and figures were produced by the notebook <code>{NB}</code>, run in {WHERE} on {RUN_WHEN} UTC (Python {RUN_PY}, every calculation recomputed: RECOMPUTE={RUN_RECOMP}). Its printed output is saved in <code>code/spectrum_shape_relation/results/RUN_REPORT_spectrum_shape_relation.md</code>, and all 15 checks of <code>check_spectrum_shape_relation.py</code> that existed then passed. Test 4 was added afterwards: it is produced by <code>run_04_dimension_profile_of_crystal_particles.py</code> (about one minute on a laptop), is included in the notebook, and brings the checks to {NCHK}, all of which pass. The figures are drawn from the same result files by <code>make_figures_spectrum_shape_relation.py</code>. How to rerun: <code>code/spectrum_shape_relation/README.md</code>.</div>
      <h3 class="sub-head">In simple words</h3>
      <p class="sd">Before the panel we described each MOF by one number from how its building blocks are connected. After the panel we predicted the outside shape of its crystals. Here we ask three questions. If we build small MOF crystals of different shapes, does that number change? Does it change between the shapes our different methods predict? And across many real MOFs, does the number tell us anything about the predicted shape?</p>
      <h3 class="sub-head">In technical words</h3>
      <p class="sd">Every earlier spectrum was measured on a torus (the labelled quotient graph tiled with wrap-around), which has no surface and no shape. Here the quotient graph is tiled <b>without</b> wrap-around, every block is placed at its Cartesian centroid, and the graph is cut to a finite particle: a box of unit cells, or a polyhedron {{<b>x</b> : <b>n</b><sub><i>f</i></sub>&middot;<b>x</b> &le; <i>s R<sub>f</sub></i>}} with the face distances <i>R<sub>f</sub></i> of a morphology prediction. &Delta;&alpha; uses the settings of the full bands: top 20% of blocks by degree as influential, radii to half the diameter, 20 trials, seeds 0&ndash;4. Error bars are the seed spread only.</p>

      <h2 class="section-title" id="rel-boxes" data-toc="1: boxes of equal size"><span class="stitle-num">0</span>Test 1: Same Number of Cells, Four Box Shapes (MOF-5)</h2>
      <p class="sd">MOF-5 (32 blocks per cubic cell) is built from 64 unit cells as a cube, a slab, a plate and a rod. Cubes of side 2 to 6 give the size trend &Delta;&alpha; = {R1['trend']['a']:.3f} + {R1['trend']['b']:.3f} ln D, where D is the graph diameter.</p>
      <figure class="fig wide"><img src="figures/relation/01_box_particles_MOF5.png" alt="Left: spectrum width against particle diameter; cubes on a rising curve, slab, plate and rod below it. Right: widths of the four 64-cell boxes, cube highest, rod lowest."><figcaption>Left: cubes follow a size trend; slab, plate and rod lie below it. Right: the width at 64 cells for each shape.</figcaption></figure>
      <div class="table-wrap"><table class="data-table" id="rel-cubes"><thead><tr><td>Cube</td><td>Blocks</td><td>Diameter</td><td>&Delta;&alpha;</td></tr></thead><tbody>{cubes1}</tbody></table></div>
      <div class="table-wrap"><table class="data-table" id="rel-boxes-table"><thead><tr><td>Shape</td><td>Cells</td><td>Blocks</td><td>Diameter</td><td>&Delta;&alpha;</td><td>Cube trend at that D</td><td>Difference</td></tr></thead><tbody>{rows1}</tbody></table></div>
      {produced('run_01_spectrum_of_box_particles_same_cell_count.py', 'results/01_box_particles_MOF5.json')}
      <p class="sd"><b>Result.</b> With the same {w1['cube']['nodes']} blocks, &Delta;&alpha; is {w1['cube']['width_mean']:.2f} (cube), {w1['slab']['width_mean']:.2f} (slab), {w1['plate']['width_mean']:.2f} (plate) and {w1['rod']['width_mean']:.2f} (rod), with seed spread below 0.01. The plate and rod have <i>larger</i> diameters than the cube yet lie below the cube trend by {abs(w1['plate']['excess_over_trend']):.2f} and {abs(w1['rod']['excess_over_trend']):.2f}, so the effect is not just the diameter. The numbers are identical to those of the separate script <code>code/spectrum_pipeline/code_19_spectrum_vs_shape.py</code> (checked in the run). ZIF-8 was also run but its block graph is in {min(zc)} to {max(zc)} disconnected pieces, so it is not used.</p>

      <h2 class="section-title" id="rel-predicted" data-toc="2: the predicted crystal shapes"><span class="stitle-num">0</span>Test 2: The Crystal Shapes Our Methods Predict (MOF-5)</h2>
      <p class="sd">For MOF-5 the methods disagree: BFDH predicts a truncated octahedron, the blend (w = 0.5) a truncated cube, UFF Wulff a cube, and the CHGNet cleavage energies a truncated octahedron. Each is built from about 2000 and about 4000 blocks, with a cube, an octahedron and a rhombic dodecahedron as references. Size is controlled in two ways: by the cube trend in block count N (&Delta;&alpha; = {t2['c_blocks']:.3f} + {t2['d_blocks']:.3f} ln N, largest residual {t2['max_abs_residual_blocks']:.3f}) and by the cube trend in diameter D.</p>
      <figure class="fig wide"><img src="figures/relation/02_predicted_crystal_shapes_MOF5.png" alt="Spectrum width against number of blocks for each predicted MOF-5 crystal shape and three reference polyhedra, with the cube trend as a dashed line; all points lie close to the line."><figcaption>Every compact shape lies close to the cube trend when compared at equal block count.</figcaption></figure>
      <div class="table-wrap"><table class="data-table" id="rel-predicted-table"><thead><tr><td>Shape</td><td>Target</td><td>Blocks N</td><td>Diameter D</td><td>&Delta;&alpha;</td><td>vs cube trend, same N</td><td>vs cube trend, same D</td></tr></thead><tbody>{rows2}</tbody></table></div>
      {produced('run_02_spectrum_of_predicted_crystal_shapes_MOF5.py', 'results/02_predicted_crystal_shapes_MOF5.json')}
      <p class="sd"><b>Result.</b> At equal block count every compact shape lies within {min(eqN):+.3f} to {max(eqN):+.3f} of the cube trend, which is the same size as the scatter of the cubes about their own trend ({t2['max_abs_residual_blocks']:.3f}), and the order of the shapes changes between 2000 and 4000 blocks. Compared at equal <i>diameter</i> they differ by up to {max(eqD):+.2f}, but only because an octahedron has a much smaller graph diameter than a cube of the same N (in a pcu net, graph distance behaves like the taxicab distance, and the octahedron is the taxicab ball). <b>So the spectrum does not tell apart the compact shapes our methods predict for MOF-5.</b> Test 1 showed that it does tell apart flat and elongated particles.</p>

      <h2 class="section-title" id="rel-core" data-toc="3: across 55 real MOFs"><span class="stitle-num">0</span>Test 3: Across 55 Real MOFs</h2>
      <p class="sd">For the {R3['n_with_shape']} CoRE MOF structures that have a first-half &Delta;&alpha; (periodic graph, <code>data/spectrum_descriptors/size_scaling/full_band_core_cg.json</code> from <code>code_17</code>), the BFDH shape was computed (faces up to index 4, 40 widest-spaced families) and described by its sphericity and aspect ratio. Spearman &rho; was computed raw and with ln(node count) held fixed; p-values are from 10 000 permutations and intervals from 5 000 bootstrap resamples.</p>
      <figure class="fig wide"><img src="figures/relation/03_core_mof_spectrum_vs_bfdh_shape.png" alt="Left: spectrum width against BFDH aspect ratio for 55 CoRE MOFs, coloured by graph size; a positive trend. Right: spectrum width against graph size; a strong positive trend."><figcaption>Left: the raw link between &Delta;&alpha; and predicted shape. Right: the link of both with graph size, which explains it.</figcaption></figure>
      <div class="table-wrap"><table class="data-table" id="rel-core-table"><thead><tr><td>Structures</td><td>Pair</td><td>n</td><td>Raw &rho;</td><td>&rho; with size held fixed</td><td>95% interval (size fixed)</td></tr></thead><tbody>{rows3}</tbody></table></div>
      {produced('run_03_core_mof_spectrum_width_vs_bfdh_shape.py', 'results/03_core_mof_spectrum_vs_bfdh_shape.json')}
      <p class="sd"><b>Result.</b> The raw links are real (&Delta;&alpha; against aspect ratio &rho; = {ar['spearman']:+.2f}, p = {ar['spearman_p']:.4f}), but with graph size held fixed they vanish (&rho; = {ar['partial_spearman_size_controlled']:+.3f}, p = {ar['partial_p']:.2f}). Size explains them: &Delta;&alpha; rises with node count (&rho; = {A['width vs ln(node count)']['spearman']:+.2f}) and more stretched predicted shapes come with bigger periodic graphs (sphericity against node count &rho; = {A['sphericity vs ln(node count)']['spearman']:+.2f}). <b>The periodic &Delta;&alpha; of the first half carries no information about predicted shape beyond size.</b></p>

      <h2 class="section-title" id="dimension-profile" data-toc="4: the dimension profile"><span class="stitle-num">0</span>Test 4: The Dimension Profile of a Crystal Particle (MOF-5)</h2>
      <p class="sd"><b>Why this test.</b> Tests 1 to 3 compress the whole scaling behaviour of a particle into one number, &Delta;&alpha;. This test keeps the whole curve. It uses the mass&ndash;radius form of box counting (cluster growing; Song, Havlin and Makse, <i>Nature</i> 433, 392, 2005), the method of the Fractals and Scaling course: M(r) is the average number of blocks within graph distance r of a block, and the local dimension is d(r) = d ln M / d ln r. An object that is three-, two- or one-dimensional at a given scale has d(r) near 3, 2 or 1 at that scale.</p>
      <p class="sd"><b>Method.</b> The particles are the MOF-5 boxes of Test 1 enlarged to about 1000 unit cells (cube 10&times;10&times;10, slab 16&times;16&times;4, plate 32&times;32&times;1, rod 64&times;4&times;4), and the seven polyhedra of Test 2 at about 4000 and 8000 blocks. Distances are computed from 64 random centre blocks by breadth-first search, with five seeds. Two read-outs: d at the half-mass radius r<sub>&frac12;</sub> (the radius that holds half the particle), and r<sub>&frac12;</sub>/D, where D is the largest distance found. A finite graph never reaches the ideal 1, 2 and 3, so the same calculation is done on three lattices of known dimension, and the particles are compared with them.</p>
      <figure class="fig wide"><img src="figures/relation/04_dimension_profile_MOF5.png" alt="Left: local dimension against radius divided by diameter for the MOF-5 cube, slab, plate and rod and for a path, a square grid and a cubic grid; the cube follows the cubic grid, the plate the square grid, the rod approaches the path. Right: r_half over D for seven compact shapes at two sizes; cube and UFF Wulff near 0.36, rhombic dodecahedron and blend near 0.44, BFDH, CHGNet and octahedron between 0.51 and 0.56."><figcaption>Left: the local dimension of the four boxes against the three reference lattices (grey). Right: r<sub>&frac12;</sub>/D of the compact shapes at two sizes; error bars are the spread over five seeds.</figcaption></figure>
      <div class="table-wrap"><table class="data-table" id="rel-dim-boxes"><thead><tr><td>Graph</td><td>Shape</td><td>Blocks</td><td>Peak d(r)</td><td>d at r<sub>&frac12;</sub></td></tr></thead><tbody>{rows4a}</tbody></table></div>
      <div class="table-wrap"><table class="data-table" id="rel-dim-poly"><thead><tr><td>Shape</td><td>N (&asymp;4000)</td><td>D</td><td>r<sub>&frac12;</sub>/D</td><td>N (&asymp;8000)</td><td>D</td><td>r<sub>&frac12;</sub>/D</td></tr></thead><tbody>{rows4b}</tbody></table></div>
      <p class="provenance"><b>Produced by:</b> <code>code/spectrum_shape_relation/run_04_dimension_profile_of_crystal_particles.py</code>, run directly (it is also step 4 of <code>{NB}</code>), output <code>results/04_dimension_profile_MOF5.json</code>.</p>
      <p class="sd"><b>Result 1: plates and rods are lower-dimensional objects, quantitatively.</b> At the half-mass radius the MOF-5 cube gives d = {BX['cube'][1]['d_at_r_half_mean']:.2f} against {REF[3][1]['d_at_r_half_mean']:.2f} for the cubic lattice, the plate {BX['plate'][1]['d_at_r_half_mean']:.2f} against {REF[2][1]['d_at_r_half_mean']:.2f} for the square lattice, and the rod {BX['rod'][1]['d_at_r_half_mean']:.2f} against {REF[1][1]['d_at_r_half_mean']:.2f} for the path; the slab lies between ({BX['slab'][1]['d_at_r_half_mean']:.2f}). The left panel shows where each particle stops being three-dimensional: the plate, one cell thick, follows the square lattice almost from the start; the rod, four cells wide, is three-dimensional at short range and approaches the path beyond about a third of its diameter. This is consistent with Test 1: the spectrum is fitted over radii up to half the diameter, where the plate and the rod have a lower local dimension than the cube.</p>
      <p class="sd"><b>Result 2: the fill profile separates the compact shapes that &Delta;&alpha; could not.</b> r<sub>&frac12;</sub>/D is {rh('cube {100} (reference)', 4000):.2f} for the cube, {rh('rhombic dodecahedron {110} (reference)', 4000):.2f} for the rhombic dodecahedron and {rh('octahedron {111} (reference)', 4000):.2f} for the octahedron (about 4000 blocks). The three different MOF-5 predictions fall in that order at both sizes: UFF Wulff (cube) {rh(UFF, 4000):.2f} and {rh(UFF, 8000):.2f}, the blend (truncated cube) {rh(BL, 4000):.2f} and {rh(BL, 8000):.2f}, BFDH (truncated octahedron) {rh(BF, 4000):.2f} and {rh(BF, 8000):.2f}. Each gap is at least {min(gaps):.1f} times the largest seed spread. CHGNet, which also predicts a truncated octahedron, gives {rh(CH, 4000):.2f} and {rh(CH, 8000):.2f}, close to BFDH. The reason is geometric: graph distance in the pcu net behaves like taxicab distance. A cube has far corners in that metric, so its diameter is large compared with the radius that holds half its blocks; the octahedron is the taxicab ball and has no far corners, so half its blocks are reached only at a larger fraction of its diameter. Truncation moves a shape between these two limits, which is why the ratio orders the cube, truncated cube and truncated octahedron.</p>
      <div class="callout" data-kind="What this does and does not show">The dimension profile <b>identifies</b> the shape of a particle from its graph alone; it does not <b>predict</b> which shape a MOF grows, and it adds no evidence for or against any morphology model. Its value for the project is a graph descriptor that is sensitive to crystal shape, computed with the same machinery as the spectrum, for use on particles produced by any method (a growth simulation, a generative model). Limits: one MOF; one rule for building a particle (block centroid inside the polyhedron, so surfaces are a staircase one block high; four of the fourteen polyhedra leave detached blocks at their corners (at most 2.5% of the blocks, the octahedron at about 4000), and only the largest connected piece is used); r<sub>&frac12;</sub> is an integer radius, so r<sub>&frac12;</sub>/D moves in steps of 1/D (about 0.02); D is the largest distance found from the sampled centres, a lower bound on the true diameter.</div>

      <h2 class="section-title" id="rel-meaning" data-toc="What carries over"><span class="stitle-num">0</span>What Carries Over From the First Half</h2>
      <div class="table-wrap"><table class="data-table"><thead><tr><td>Question</td><td>Answer</td><td>Evidence</td></tr></thead><tbody>
        <tr><td class="dt-label">Does &Delta;&alpha; of a finite particle depend on how flat or long it is?</td><td class="dt-note">Yes, for MOF-5, beyond size</td><td class="dt-note">Test 1</td></tr>
        <tr><td class="dt-label">Does it separate compact shapes (cube vs octahedron vs truncated octahedron)?</td><td class="dt-note">No; differences are within the method's own scatter</td><td class="dt-note">Test 2</td></tr>
        <tr><td class="dt-label">Does the periodic &Delta;&alpha; predict a MOF's crystal shape?</td><td class="dt-note">No, once graph size is controlled</td><td class="dt-note">Test 3</td></tr>
        <tr><td class="dt-label">Does the mass&ndash;radius curve of a finite particle carry shape information?</td><td class="dt-note">Yes: dimensionality (cube, plate, rod) and the compact shapes (cube, truncated cube, truncated octahedron)</td><td class="dt-note">Test 4</td></tr>
        <tr><td class="dt-label">Does r&frac12;/D follow a crystal along the morphology map?</td><td class="dt-note">Yes for MOF-5: it changes in one direction along both axes of the map (3 seeds; one number cannot name a point of a two-dimensional map)</td><td class="dt-note"><a href="morphology_map.html#map-dimension">Morphology map</a></td></tr>
      </tbody></table></div>
      <p class="sd">What carries over is the <b>graph</b> (the labelled quotient graph, used by the morphology work in <a href="graph_faces.html">Faces from the graph</a>) and the habit of controlling size. The spectrum width itself becomes useful for shape only when it is measured on a finite particle, and then only for anisotropy (plate, rod). The full mass&ndash;radius curve (Test 4) carries more: it also separates the compact shapes. The next tests are the cell-deformation shapes of <a href="deform.html">Changing the cell</a>, which are plates and rods, and a second MOF with a connected block graph.</p>
      <div class="callout warn" data-kind="Limits">Tests 1, 2 and 4 use one structure (MOF-5): it is the only demonstration MOF whose file holds an orthogonal conventional cell and whose block graph is connected. A block belongs to a particle if its centroid is inside the shape, so surfaces are a staircase one block high. BFDH shape names for low-symmetry crystals use cubic-style labels and are not used in any statistic; only sphericity and aspect ratio are.</div>
'''
open(OUT, 'w', encoding='utf-8').write(html)
print('wrote', OUT)
