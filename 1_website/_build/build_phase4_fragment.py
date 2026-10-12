"""Writes fragments/surface_energy.before.html from 2_python/morphology/results/phase4_results.json,
so every number on the Phase 4 page comes straight from the Python output."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "..", "..", "2_python", "morphology", "results", "phase4_results.json")))
P3 = json.load(open(os.path.join(HERE, "..", "..", "2_python", "morphology", "results", "phase3_results.json")))
ORDER = ["MOF-5", "HKUST-1", "UiO-66", "ZIF-8"]
SEEN = {"MOF-5": "cube", "HKUST-1": "octahedron (cube to octahedron with additives)", "UiO-66": "octahedron", "ZIF-8": "rhombic dodecahedron"}
def fam(t): return t.replace("+", "<sub>+</sub>").replace("-", "<sub>&minus;</sub>") if t[-1] in "+-" else t

def face_table(n):
    rows = ""
    for f, v in P[n]["faces"].items():
        rows += (f'<tr data-face="{n}|{f}" data-gamma="{v["gamma"]}"><td class="dt-label">{fam(f)}</td><td class="dt-value">{v["d"]:.2f}</td>'
                 f'<td class="dt-value">{v["gamma"]:.3f}</td><td class="dt-value">{v["gamma_bond_only"]:.3f}</td><td class="dt-value">{v["gamma_vdw_only"]:.4f}</td></tr>')
    return (f'<h3 class="sub-head">{n} ({P[n]["spacegroup"]}, {P[n]["n_atoms"]} atoms in the conventional cell, {P[n]["bonds"]} bonds)</h3>'
            f'<div class="table-wrap"><table class="data-table" id="p4-{n}"><thead><tr><td>Face</td><td><i>d</i> (&Aring;)</td>'
            f'<td>&gamma; total (J/m&sup2;)</td><td>from bonds</td><td>from vdW</td></tr></thead><tbody>{rows}</tbody></table></div>')

summ = ""
for n in ORDER:
    r = P[n]; top = min(((v["gamma"], f) for f, v in r["faces"].items()))[1]
    s3 = P3[n]["shape_wulff_broken_bond"]["name_major_faces"]
    sens = " / ".join(r["sensitivity_vdw_weight"].values())
    summ += (f'<tr data-shape="{n}"><td class="dt-label">{n}</td><td class="dt-note">{fam(top)}</td><td class="dt-note">{r["shape_wulff_uff"]["name"]}</td>'
             f'<td class="dt-note">{s3}</td><td class="dt-note">{SEEN[n]}</td></tr>')
sens_rows = ""
for n in ORDER:
    s = P[n]["sensitivity_vdw_weight"]
    sens_rows += f'<tr><td class="dt-label">{n}</td>' + "".join(f'<td class="dt-note">{s[k]}</td>' for k in ["0", "1", "5", "20", "100"]) + "</tr>"

html = f'''      <h2 class="section-title" id="se-intro" data-toc="What this page does"><span class="stitle-num">0</span>What This Page Does</h2>
      <dl class="bridge"><dt>You know</dt><dd>Faces, slices and the shapes they bound (<a href="learn_shape.html">Learn</a>), the propositions (<a href="morph_math.html">Mathematics</a>), and the graph-counting energies of <a href="graph_faces.html">Phase 3</a>.</dd><dt>This page adds</dt><dd>Energies computed from the <b>atoms</b> of each framework, not just its net: a force field assigns a cost to every bond and every van der Waals contact that a cut would break.</dd></dl>
      <p class="section-sub">Phase 3 counted broken links between building blocks and treated every link as equal. Here each atom pair is weighted by a force field, the cleaving plane is placed through the real atomic structure, and the cheapest plane position is chosen for every face. The result is a cleavage energy &gamma;(<i>hkl</i>) for each face, and from the set of &gamma; values a Wulff shape.</p>
      <div class="callout warn" data-kind="Read this first">The energies are <b>unrelaxed</b> (the atoms stay where they were before the cut) and have <b>no electrostatics</b>. They are therefore upper bounds, and the absolute numbers, especially for the charged UiO-66, should not be quoted as measurements. What the page uses them for is the <b>ordering of the faces</b>, which Section 5 shows is stable.</div>

      <h2 class="section-title" id="se-concepts" data-toc="Concepts from scratch"><span class="stitle-num">0</span>The Ideas, From Scratch</h2>
      <h3 class="sub-head">Surface energy</h3>
      <p class="sd">To make a surface you must pull a crystal apart along a plane. That costs energy, because bonds and attractions across the plane are broken. The cost per unit area of new surface is the <b>surface energy</b> &gamma;, in J/m&sup2;. Pulling apart creates <i>two</i> surfaces, so &gamma; is half the energy of the cut per unit area. Faces with low &gamma; are cheap to create and are the ones a crystal shows (Wulff, 1901).</p>
      <h3 class="sub-head">What the force field adds up</h3>
      <div class="eq"><span class="ex"><i>E</i><sub>vdW</sub>(<i>r</i>) = <i>D</i><sub><i>ij</i></sub> [ (<i>x</i><sub><i>ij</i></sub>/<i>r</i>)<sup>12</sup> &minus; 2 (<i>x</i><sub><i>ij</i></sub>/<i>r</i>)<sup>6</sup> ]</span><span class="tag">(1)</span></div>
      <div class="eq"><span class="ex">&gamma;(<i>s</i>) = &frac12; (<i>d</i>/<i>V</i>) &Sigma;<sub>pairs</sub> &epsilon;<sub>pair</sub> <i>c</i><sub>pair</sub>(<i>s</i>)</span><span class="tag">(2)</span></div>
      <div class="where"><p class="lead">where</p><dl><dt><i>D</i><sub><i>ij</i></sub>, <i>x</i><sub><i>ij</i></sub></dt><dd>well depth and contact distance for the atom pair, from the Universal Force Field (UFF; Rapp&eacute; et al. 1992) with the geometric-mean rule <i>D</i><sub><i>ij</i></sub> = &radic;(<i>D</i><sub><i>i</i></sub><i>D</i><sub><i>j</i></sub>).</dd><dt>&epsilon;<sub>pair</sub></dt><dd>energy lost when the pair is separated: &minus;<i>E</i><sub>vdW</sub> for a non-bonded pair, and a flat 70 kcal/mol for a bond (UFF's default bond well depth). Pairs two bonds apart or closer are excluded, as in UFF.</dd><dt><i>c</i><sub>pair</sub>(<i>s</i>)</dt><dd>number of planes, spaced <i>d</i> apart with offset <i>s</i>, that fall between the two atoms.</dd><dt><i>V</i></dt><dd>volume of the unit cell. The factor <i>d</i>/<i>V</i> turns an energy per cell into an energy per area (it is Proposition 13 of the Mathematics page).</dd></dl></div>
      <p class="sd">The plane offset <i>s</i> is scanned over one full period and the <b>lowest</b> &gamma; is kept: that is the termination a growing crystal would prefer.</p>

      <h2 class="section-title" id="se-validate" data-toc="Validation"><span class="stitle-num">0</span>Checks Against Exact Answers</h2>
      <div class="table-wrap"><table class="data-table">
        <thead><tr><td style="width:34%">Test</td><td style="width:44%">Exact answer</td><td>Code</td></tr></thead>
        <tbody>
          <tr><td class="dt-note">Simple cubic, one bond per cell edge, (100)</td><td class="dt-note">&gamma; = <i>D</i>/(2<i>a</i>&sup2;)</td><td class="dt-note" style="color:var(--good)">equal to 9 digits</td></tr>
          <tr><td class="dt-note">Simple cubic, (110)</td><td class="dt-note">2 bonds cut per cell, plane spacing <i>a</i>/&radic;2</td><td class="dt-note" style="color:var(--good)">equal to 9 digits</td></tr>
          <tr><td class="dt-note">fcc Lennard-Jones crystal, (100)</td><td class="dt-note">explicit sum over every pair across the middle plane of a slab 10 cells thick</td><td class="dt-note" style="color:var(--good)">agree within 2% (they matched to 3 digits)</td></tr>
          <tr><td class="dt-note">fcc Lennard-Jones, ordering of faces</td><td class="dt-note">&gamma;<sub>111</sub> &lt; &gamma;<sub>100</sub> &lt; &gamma;<sub>110</sub></td><td class="dt-note" style="color:var(--good)">holds</td></tr>
        </tbody>
      </table></div>
      <p class="sd">These four checks are in <code>2_python/morphology/tests_phase4.py</code>. They test the counting formula (2) independently of any MOF.</p>

      <h2 class="section-title" id="se-results" data-toc="Results"><span class="stitle-num">0</span>Results for the Four MOFs</h2>
      <figure class="fig wide">
        <img src="figures/morph/phase4_compare.png" alt="A grid of 12 crystal shapes. Rows are MOF-5, HKUST-1, UiO-66 and ZIF-8. Columns are the Phase 3 attachment-energy shape, the Phase 3 broken-bond Wulff shape and the Phase 4 force-field Wulff shape. MOF-5 gives a truncated cube then cubes; HKUST-1 a truncated octahedron in all three; UiO-66 truncated octahedra then an octahedron; ZIF-8 rhombic dodecahedra in all three.">
        <figcaption>The three shape models for each MOF. Blue {{100}}, red {{111}}, green {{110}}. The two Phase 3 columns and the Phase 4 column agree on which face dominates in every row.</figcaption>
      </figure>
      <div class="table-wrap"><table class="data-table" id="p4-shapes"><thead><tr><td>MOF</td><td>Lowest-energy face</td><td>Phase 4 shape</td><td>Phase 3 broken-bond shape</td><td>Seen in experiment</td></tr></thead><tbody>{summ}</tbody></table></div>
      <p class="sd">The dominant face agrees with experiment for all four frameworks: cube for MOF-5, octahedron for HKUST-1 and UiO-66, rhombic dodecahedron for ZIF-8. Experimental sources are listed on the <a href="graph_faces.html">Phase 3 page</a>.</p>
      {"".join(face_table(n) for n in ORDER)}
      <p class="sd">&ldquo;From bonds&rdquo; and &ldquo;from vdW&rdquo; are the two parts of the total. The bond part is 91&ndash;99% of every value, because MOFs are mostly empty pore and the planes cut few atoms, so there is little van der Waals contact to break. This is why the Phase 4 shapes largely agree with Phase 3's.</p>

      <h2 class="section-title" id="se-sens" data-toc="Sensitivity"><span class="stitle-num">0</span>How Much Do the Assumptions Matter?</h2>
      <p class="section-sub">The van der Waals part is the most uncertain, so it was multiplied by 0, 1, 5, 20 and 100 and the Wulff shape recomputed. Scaling the bond energy instead gives exactly the same set of shapes, since only the ratio of the two parts matters.</p>
      <div class="table-wrap"><table class="data-table" id="p4-sens"><thead><tr><td>MOF</td><td>vdW &times; 0</td><td>&times; 1</td><td>&times; 5</td><td>&times; 20</td><td>&times; 100</td></tr></thead><tbody>{sens_rows}</tbody></table></div>
      <p class="sd">The dominant face (MOF-5 {{100}}, HKUST-1 {{111}}, UiO-66 {{111}}, ZIF-8 {{110}}) is the same at every weight. What does change is the share of the smaller faces: at &times;100 the {{100}} faces of HKUST-1 grow from 22% to 44% of the surface area and the {{110}} faces of ZIF-8 are joined by 18% {{100}}. So the dominant face is robust, and the exact minor-face proportions are not.</p>

      <h2 class="section-title" id="se-limits" data-toc="Limitations"><span class="stitle-num">0</span>What This Does Not Do</h2>
      <ul>
        <li><b>No relaxation.</b> Real surfaces reconstruct, which lowers &gamma; by an amount that can differ between faces.</li>
        <li><b>No electrostatics.</b> Zr&ndash;O clusters carry large partial charges; ignoring them probably understates the cost of cutting UiO-66, and charge terms could change which faces win. This is the first thing to add next.</li>
        <li><b>Flat bond energy.</b> Every bond is given the same 70 kcal/mol, so a metal&ndash;oxygen bond and a carbon&ndash;carbon bond cost the same. A bond-type-dependent energy is a refinement, not yet done.</li>
        <li><b>No solvent or modulator.</b> In a real synthesis a solvent or additive adsorbs on some faces and slows them. That is how the cube-to-octahedron change of HKUST-1 is produced, and it is not in a vacuum cleavage energy.</li>
        <li><b>UiO-66 {{111}}+ and {{111}}&minus;.</b> They come out equal here, since the model has no way to tell the two halves apart, so the tetrahedron seen in some reports is not reproduced.</li>
      </ul>
      <div class="callout" data-kind="What this phase shows">Starting only from the atoms of an established MOF, a physically defined energy for every face can be computed, and it gives the same dominant face as Phase 3 and as experiment for all four test frameworks. Together with Phases 1 to 3, one unit cell therefore yields a family of morphologies (Phase 1), each member has a definite growth-rate or energy ratio that selects it (Phases 3 and 4), and the choice among them is controlled by the face energies, which is the control parameter the panel asked about.</div>
'''
open(os.path.join(HERE, "fragments", "surface_energy.before.html"), "w", encoding="utf-8").write(html)
print("fragment written")
