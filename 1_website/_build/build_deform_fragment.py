"""Writes fragments/deform.before.html; tables come from 2_python/morphology/results/deform_results.json."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "..", "..", "2_python", "morphology", "results", "deform_results.json")))
ORDER = ["MOF-5", "HKUST-1", "UiO-66", "ZIF-8"]

def ctable(n):
    rows = ""
    for r in R[n]["c_stretch"]:
        hw = r["half_widths"]
        rows += (f'<tr data-case="{n}|{r["lc"]}" data-habit="{r["habit"]}"><td class="dt-value">{r["lc"]:g}</td><td class="dt-value">{r["c"]:.2f}</td><td class="dt-value">{r["operations"]}</td>'
                 f'<td class="dt-note">{r["habit"]}</td><td class="dt-note">{r["name"]}</td><td class="dt-value">{hw[2]/hw[0]:.3f}</td><td class="dt-value">{r["sphericity"]:.3f}</td><td class="dt-value">{r["kappa2"]:.3f}</td></tr>')
    return (f'<h3 class="sub-head">{n} ({R[n]["spacegroup"]}): stretch of <i>c</i></h3><div class="table-wrap"><table class="data-table" id="df-{n}"><thead><tr>'
            f'<td>&lambda;</td><td><i>c</i> (&Aring;)</td><td>Operations</td><td>Habit</td><td>Shape</td><td>Height / width</td><td>&Psi;</td><td>&kappa;&sup2;</td></tr></thead><tbody>{rows}</tbody></table></div>')

shear = ""
for n in ORDER:
    shear += f'<tr><td class="dt-label">{n}</td>' + "".join(f'<td class="dt-note">{r["name"]} ({r["operations"]} ops)</td>' for r in R[n]["shear"]) + "</tr>"
head = "".join(f'<td>&gamma; = {r["gamma_set"]}&deg;</td>' for r in R["MOF-5"]["shear"])

html = f'''      <h2 class="section-title" id="df-intro" data-toc="What this page does"><span class="stitle-num">0</span>What This Page Does</h2>
      <dl class="bridge"><dt>You know</dt><dd>One unit cell gives a family of crystal shapes by changing the growth-rate ratios (<a href="morphology.html">Morphology</a>), and the propositions behind it (<a href="morph_math.html">Mathematics</a>, 1&ndash;13).</dd><dt>This page adds</dt><dd>The other reading of the panel's question: change the <b>unit cell itself</b> (its edges <i>a, b, c</i> and angles) and see how the crystal shape follows.</dd></dl>
      <p class="section-sub">The panel said the values in the CIF file may be changed. That gives a new, hypothetical framework: the atoms keep their fractional positions and the lattice is stretched or sheared. It is no longer the measured structure, and nothing here claims that a real MOF can be deformed freely. What can be shown mathematically is exactly what carries over from the original cell and what changes (Propositions 14&ndash;16), and computationally how the shape moves.</p>

      <h2 class="section-title" id="df-concepts" data-toc="The ideas"><span class="stitle-num">0</span>The Ideas, From Scratch</h2>
      <h3 class="sub-head">The six numbers of a unit cell</h3>
      <p class="sd">A unit cell is a parallelepiped described by three edge lengths <i>a, b, c</i> and three angles &alpha;, &beta;, &gamma;. A cubic cell has <i>a</i> = <i>b</i> = <i>c</i> and all angles 90&deg;. Stretching <i>c</i> alone gives a <b>tetragonal</b> cell; making all three edges different gives an <b>orthorhombic</b> one; changing an angle gives a <b>sheared</b> (monoclinic or triclinic) one.</p>
      <h3 class="sub-head">What the CIF file stores, and what moves</h3>
      <p class="sd">A CIF stores the six cell numbers and the position of each atom <i>as a fraction</i> of the cell edges. If only the cell numbers change, every atom moves proportionally with the cell, so the arrangement of atoms keeps the same topology while all distances change. This is the model used here.</p>
      <h3 class="sub-head">Why the shape follows</h3>
      <p class="sd">The spacing between lattice planes, <i>d</i><sub><i>hkl</i></sub> = 1/&radic;(<b>h</b><sup>T</sup><b>G</b><sup>&minus;1</sup><b>h</b>) where <b>G</b> = <b>L</b><b>L</b><sup>T</sup> is the metric tensor, depends on the cell. The BFDH rule makes the distance of each face from the crystal centre proportional to 1/<i>d</i><sub>eff</sub>, so changing the cell changes every face distance and therefore the shape. A cell stretched along <i>c</i> has widely spaced (001) planes, so the (001) faces become <b>large and slow</b> and the crystal becomes a <b>plate</b>; a cell compressed along <i>c</i> gives a <b>rod</b>.</p>
      <div class="callout" data-kind="What does not change">Which faces are allowed depends only on the fractional coordinates and the space-group operations (Proposition 14). So the list of allowed faces and their orders <i>n</i> are the same for every deformation; only their spacings change.</div>
      <div class="callout" data-kind="What does change">When the cell loses a symmetry, faces that were equivalent become different (Proposition 15). A cubic {{100}} family of 6 faces splits into 4 + 2. That split is what lets a cube-like crystal become elongated.</div>

      <h2 class="section-title" id="df-explorer" data-toc="Live: change the cell"><span class="stitle-num">0</span>Change the Cell and Watch the Crystal</h2>
      <p class="section-sub">Choose a structure, then scale its three cell edges. The starting edge is the real one from the CIF (via spglib). The shape is computed in your browser by the same rule as the Python code, and the two agree on all 52 cases tested.</p>
      <div class="panel" id="df-panel">
        <div class="toolbar" id="df-structs"><span class="lbl">Structure</span></div>
        <div class="toolbar" id="df-presets"><span class="lbl">Try</span></div>
        <div id="df-sliders"></div>
        <div id="df-view"></div>
        <div id="df-readout"></div>
      </div>
      <p class="sd">Only orthogonal cells (all angles 90&deg;) are interactive here; sheared cells are in the tables below, computed by the Python code.</p>

      <h2 class="section-title" id="df-results" data-toc="Results from the Python code"><span class="stitle-num">0</span>Results for the Four MOFs</h2>
      <figure class="fig wide">
        <img src="figures/morph/MOF-5_deform_c.png" alt="Five crystal shapes from the MOF-5 cell with c scaled by 0.25, 0.5, 1.0, 1.5 and 3.0: a tall rod, a rounded equant crystal, a truncated octahedron, a slightly flattened crystal and a flat plate.">
        <figcaption>MOF-5: one cell, stretched along <i>c</i>. A rod for strong compression, the truncated octahedron at the real cell, and a plate for stretching.</figcaption>
      </figure>
      <figure class="fig wide">
        <img src="figures/morph/ZIF-8_deform_c.png" alt="Five crystal shapes from the ZIF-8 cell with c scaled by 0.25, 0.5, 1.0, 1.5 and 3.0: a thin rod, a short prism, a rhombic dodecahedron, a truncated rhombic dodecahedron with a square top face and a flat plate.">
        <figcaption>ZIF-8 (rhombic dodecahedron at the real cell) follows the same path with different shapes in between, because its lattice is body-centred.</figcaption>
      </figure>
      {"".join(ctable(n) for n in ORDER)}
      <p class="sd">Habit follows the Zingg classification from the principal radii of gyration: <b>plate</b> when the smallest radius is under 2/3 of the middle one, <b>rod</b> when the middle one is under 2/3 of the largest, <b>equant</b> otherwise. The three F-centred frameworks have identical rows because the lattice-only rule cannot tell them apart (Proposition 16, consequence iii).</p>
      <figure class="fig wide">
        <img src="figures/morph/MOF-5_deform_gamma.png" alt="Five crystal shapes from the MOF-5 cell with the angle gamma set to 60, 75, 90, 105 and 120 degrees, a symmetric truncated octahedron at 90 and progressively leaning, sheared versions on either side.">
        <figcaption>Shearing the cell (changing &gamma;) leans the crystal and lowers the symmetry further.</figcaption>
      </figure>
      <div class="table-wrap"><table class="data-table" id="df-shear"><thead><tr><td>Structure</td>{head}</tr></thead><tbody>{shear}</tbody></table></div>

      <h2 class="section-title" id="df-limits" data-toc="Limits"><span class="stitle-num">0</span>What This Does and Does Not Show</h2>
      <ul>
        <li><b>It is a hypothetical framework.</b> The edited cell is not the CIF's structure. The result says how the shape of <i>this family</i> of cells behaves; it does not say a real MOF can reach those cells (flexible MOFs can reach some).</li>
        <li><b>The shape rule is the lattice-only BFDH.</b> The graph and force-field rules (<a href="graph_faces.html">Phase 3</a>, <a href="surface_energy.html">Phase 4</a>) have not been recomputed for deformed cells. Under BFDH three of the four MOFs are indistinguishable.</li>
        <li><b>Plates are easy, rods are harder.</b> Making a plate needs stretching the cell by about 2 to 3. A rod needs compressing a cell edge to between 0.3 and 0.4 of its length, because slanted planes cap the height (Proposition 16, consequence i).</li>
        <li><b>The 40 largest-spacing families are used</b> (the earlier pages use 10). Ten families can leave the shape unbounded for strongly anisotropic cells, which the tests showed.</li>
      </ul>
      <div class="callout" data-kind="What this adds to the answer">The panel's task can be met under both readings. Reading A: one unit cell gives several morphologies by changing the growth-rate ratios (Phases 1&ndash;4). Reading B: changing the cell parameters of the same CIF gives plates, equant crystals and rods, with the exact rules of Propositions 14&ndash;16.</div>
'''
open(os.path.join(HERE, "fragments", "deform.before.html"), "w", encoding="utf-8").write(html)
print("deform fragment written")
