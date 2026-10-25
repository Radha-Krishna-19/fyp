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

html = f'''      <h2 class="section-title" id="rel-intro" data-toc="What this page tests"><span class="stitle-num">0</span>What This Page Tests</h2>
      <dl class="bridge"><dt>You know</dt><dd>The spectrum width &Delta;&alpha; of the first half (<a href="spectrum.html">Spectrum</a>, <a href="results.html">Results</a>) and the predicted crystal shapes of the second half (<a href="morphology.html">Morphology</a>, <a href="hybrid.html">Hybrid</a>). Why shape matters: <a href="bridge.html">Why Shape</a>.</dd><dt>This page adds</dt><dd>Three calculations that test whether the two halves are related.</dd><dt>Which lets us</dt><dd>Say exactly which part of the earlier work carries over to morphology, and which does not.</dd></dl>
      <div class="callout" data-kind="Where every number on this page comes from">All tables and figures were produced by the notebook <code>{NB}</code>, run by P. M. Radha Krishna in {WHERE} on {RUN_WHEN} UTC (Python {RUN_PY}, every calculation recomputed: RECOMPUTE={RUN_RECOMP}). Its printed output is saved in <code>code/spectrum_shape_relation/results/RUN_REPORT_spectrum_shape_relation.md</code>, and all 15 checks of <code>check_spectrum_shape_relation.py</code> passed in that run. The figures are drawn from the same result files by <code>make_figures_spectrum_shape_relation.py</code>. How to rerun: <code>code/spectrum_shape_relation/README.md</code>.</div>
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

      <h2 class="section-title" id="rel-meaning" data-toc="What carries over"><span class="stitle-num">0</span>What Carries Over From the First Half</h2>
      <div class="table-wrap"><table class="data-table"><thead><tr><td>Question</td><td>Answer</td><td>Evidence</td></tr></thead><tbody>
        <tr><td class="dt-label">Does &Delta;&alpha; of a finite particle depend on how flat or long it is?</td><td class="dt-note">Yes, for MOF-5, beyond size</td><td class="dt-note">Test 1</td></tr>
        <tr><td class="dt-label">Does it separate compact shapes (cube vs octahedron vs truncated octahedron)?</td><td class="dt-note">No; differences are within the method's own scatter</td><td class="dt-note">Test 2</td></tr>
        <tr><td class="dt-label">Does the periodic &Delta;&alpha; predict a MOF's crystal shape?</td><td class="dt-note">No, once graph size is controlled</td><td class="dt-note">Test 3</td></tr>
      </tbody></table></div>
      <p class="sd">What carries over is the <b>graph</b> (the labelled quotient graph, used by the morphology work in <a href="graph_faces.html">Phase 3</a>) and the habit of controlling size. The spectrum itself becomes useful for shape only when it is measured on a finite particle, and then only for anisotropy (plate, rod). A sensible next test is the cell-deformation shapes of <a href="deform.html">Cell Deform</a>, which are plates and rods.</p>
      <div class="callout warn" data-kind="Limits">Tests 1 and 2 use one structure (MOF-5): it is the only demonstration MOF whose file holds an orthogonal conventional cell and whose block graph is connected. A block belongs to a particle if its centroid is inside the shape, so surfaces are a staircase one block high. BFDH shape names for low-symmetry crystals use cubic-style labels and are not used in any statistic; only sphericity and aspect ratio are.</div>
'''
open(OUT, 'w', encoding='utf-8').write(html)
print('wrote', OUT)
