#!/usr/bin/env python3
"""Writes fragments/hybrid.before.html (page 'Hybrid') from code/morphology/results/hybrid_results.json."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
D = json.load(open(os.path.join(ROOT, 'code', 'morphology', 'results', 'hybrid_results.json')))
OUT = os.path.join(HERE, 'fragments', 'hybrid.before.html')
EXPECT = {'MOF-5': 'cube', 'HKUST-1': 'octahedron', 'UiO-66': 'octahedron (with modulator)', 'ZIF-8': 'rhombic dodecahedron'}
WS = ['0', '0.25', '0.5', '0.75', '1']

rows = ''
for m in ['MOF-5', 'HKUST-1', 'UiO-66', 'ZIF-8']:
    sh = D[m]['shapes']
    cells = ''.join(f'<td class="dt-note">{sh[w]["name"]}</td>' for w in WS)
    changed = len({sh[w]['name'] for w in WS}) > 1
    rows += (f'<tr data-mof="{m}"><td class="dt-label">{m}</td>{cells}'
             f'<td class="dt-note">{EXPECT[m]}</td>'
             f'<td class="dt-value">{"yes" if changed else "no"}</td></tr>')
ex = D['MOF-5']
rb, rw = ex['R_bfdh'], ex['R_wulff']
ex_rows = ''
for f in ['{100}', '{111}']:
    mid = (rb[f] ** 0.5) * (rw[f] ** 0.5)
    ex_rows += (f'<tr><td class="dt-label">{f}</td><td class="dt-value">{rb[f]:.3f}</td><td class="dt-value">{rw[f]:.3f}</td>'
                f'<td class="dt-value">{mid:.3f}</td></tr>')
same = [m for m in D if len({D[m]['shapes'][w]['name'] for w in WS}) == 1]

html = f'''      <h2 class="section-title" id="hy-intro" data-toc="What this page does"><span class="stitle-num">0</span>What This Page Does</h2>
      <dl class="bridge"><dt>You know</dt><dd>Two ways to turn a MOF into a shape: BFDH from the face spacing (<a href="morphology.html">Morphology</a>) and Wulff from the face energies (<a href="surface_energy.html">Phase 4</a>).</dd><dt>This page adds</dt><dd>One rule that blends the two, what it gives for four MOFs, and the notebook that runs it on any crystal file.</dd><dt>Which lets us</dt><dd>Ask whether the blend is better, worse or the same as either method alone, which was the team's question for the guide review.</dd></dl>
      <h3 class="sub-head">In simple words</h3>
      <p class="sd">There are two ways to guess the outside shape of a crystal. The first (BFDH) says that faces whose layers are far apart are slow to grow, so they end up large. It looks only at the geometry. The second (Wulff) says that the faces that cost the least energy to create end up large. It looks at the chemistry. The idea is to blend them with a dial: at 0 we use only the geometry, at 1 only the energy, and in between a mixture. We then see whether the mixture gives a shape closer to the one seen in the laboratory.</p>
      <h3 class="sub-head">In technical words</h3>
      <p class="sd">Each face family <i>f</i> has a distance to the centre of the crystal <i>R<sub>f</sub></i> and the shape is the convex region {{<b>x</b> : <b>n</b><sub><i>f</i></sub>&middot;<b>x</b> &le; <i>R<sub>f</sub></i>}}. BFDH gives <i>R<sub>f</sub></i> &prop; 1/<i>d</i><sub>eff</sub> and Wulff gives <i>R<sub>f</sub></i> &prop; &gamma;<sub><i>f</i></sub>. Both are scaled so that the smallest value is 1, so neither dominates because of its units. The blend is the weighted geometric mean</p>
      <p class="sd" style="text-align:center"><i>R<sub>f</sub></i>(<i>w</i>) = <i>R</i><sub>BFDH,<i>f</i></sub><sup>1&minus;<i>w</i></sup> &middot; <i>R</i><sub>Wulff,<i>f</i></sub><sup><i>w</i></sup>, &nbsp; 0 &le; <i>w</i> &le; 1.</p>
      <p class="sd">Taking logarithms, ln <i>R<sub>f</sub></i>(<i>w</i>) = (1&minus;<i>w</i>) ln <i>R</i><sub>BFDH</sub> + <i>w</i> ln <i>R</i><sub>Wulff</sub>, so the blend moves along a straight line between the two methods in log space, and <i>w</i> = 0 and <i>w</i> = 1 give exactly the two original shapes. The same list of faces is used for both so that the comparison is fair. The set of face families and their energies come from the same pipeline as Phase 4 (UFF, unrelaxed, flat bond cost).</p>
      <h3 class="sub-head">A worked example (MOF-5)</h3>
      <div class="table-wrap"><table class="data-table" id="hy-example"><thead><tr><td>Face</td><td><i>R</i> from BFDH</td><td><i>R</i> from Wulff</td><td><i>R</i> at <i>w</i> = 0.5</td></tr></thead><tbody>{ex_rows}</tbody></table></div>
      <p class="sd">BFDH makes {{111}} the closest face (<i>R</i> = 1) and {{100}} further out, so {{111}} is large and the crystal is a truncated octahedron. Wulff reverses it: {{100}} is the cheapest face and {{111}} lies further out. At <i>w</i> = 0.5 the ratio <i>R</i><sub>111</sub>/<i>R</i><sub>100</sub> passes through an intermediate value and the shape is a truncated cube; the name for each <i>w</i> is in the table below.</p>

      <h2 class="section-title" id="hy-results" data-toc="Results"><span class="stitle-num">0</span>Results for Four MOFs</h2>
      <div class="table-wrap"><table class="data-table" id="hy-table"><thead><tr><td>MOF</td><td><i>w</i> = 0 (BFDH)</td><td><i>w</i> = 0.25</td><td><i>w</i> = 0.5</td><td><i>w</i> = 0.75</td><td><i>w</i> = 1 (Wulff)</td><td>Crystals show</td><td>Shape changes with <i>w</i>?</td></tr></thead><tbody>{rows}</tbody></table></div>
      <ul class="sd">
        <li><b>Blending adds nothing for {', '.join(same)}.</b> BFDH and Wulff already give the same shape, so every blend does too.</li>
        <li><b>It matters for MOF-5 and UiO-66.</b> There the two methods disagree and the blend passes through intermediate shapes. This is a transition, not a new shape.</li>
        <li><b>Against experiment,</b> Wulff matches MOF-5 (cube), UiO-66 (octahedron) and ZIF-8, BFDH matches only ZIF-8, and HKUST-1 is a truncated octahedron in every column while crystals show an octahedron (additive-dependent). The experimental shapes are those of Rohith's notebook; the conditions behind them are on the <a href="experiment.html">Experiment</a> page.</li>
      </ul>
      <div class="callout warn" data-kind="Why no best weight is given">The dial <i>w</i> is a free parameter and there are four MOFs. Picking the weight that scores best would fit it to the test set, so the table shows all five values and no ranking. The honest reading today is that the blend has not been shown to beat either method. To show that, <i>w</i> must be chosen on some MOFs and tested on others, and the energies must first be checked by DFT. If the blend does win on held-out MOFs, that would be a new model worth writing up; today it is an idea with a working implementation.</div>

      <h2 class="section-title" id="hy-nb" data-toc="The notebook"><span class="stitle-num">0</span>The Notebook: Any Crystal File</h2>
      <p class="sd">The Colab notebook <code>code/morphology/MorphoGraph_hybrid.ipynb</code> (generated by <code>tools/make_nb.py</code>) runs the whole chain on any CIF that contains a unit cell, with no machine-learning model and no GPU:</p>
      <ol class="sd">
        <li>Upload the CIF in the upload cell (any crystal system; a file without a cell is refused).</li>
        <li>Set <code>NAME</code> so the plot titles carry the right name.</li>
        <li>The notebook finds the symmetry, lists the allowed faces, computes the UFF energy of each face family with all atoms including hydrogen, and draws the BFDH, blended and Wulff shapes.</li>
        <li>An optional cell accepts energies from another source (for example CHGNet or DFT) and recomputes the same shapes from them.</li>
      </ol>
      <p class="sd">The notebook differs from Keerthi's CHGNet notebook: it uses the force-field energies and needs seconds, whereas the CHGNet notebook relaxes slabs and needs a GPU for hours. Its limits are those of Phase 4 (no solvent, no charges, no temperature).</p>
'''
open(OUT, 'w', encoding='utf-8').write(html)
print('wrote', OUT, 'same:', same)
