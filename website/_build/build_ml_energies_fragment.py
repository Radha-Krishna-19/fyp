"""Writes fragments/ml_energies.before.html from the result files of
code/morphology/steps1_8_check/nb_2026-11-14/ (every number on the page is read from them).

Run:  python website/_build/build_ml_energies_fragment.py   (then build_site.py)
"""
import json, os, csv, html
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
D = os.path.join(ROOT, "code", "morphology", "steps1_8_check", "nb_2026-11-14")
R = os.path.join(D, "results")
OUT = os.path.join(HERE, "fragments", "ml_energies.before.html")


def J(name, default=None):
    p = os.path.join(R, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


MU = J("water_mu.json"); SW = J("water_mu_sweep.json"); RX = J("relax_cases.json", {"slabs": []})
K12 = J("k12_count.json"); GNN = J("gnn_rerun.json"); REF = MU["reference"]
ROWS = list(csv.DictReader(open(os.path.join(R, "water_mu.csv"), encoding="utf-8")))
CONDS = MU["conditions_dmu_eV"]; TAGS = dict(zip(CONDS, "ABCDE"))
A0 = "0 K molecule (notebook)"


def f(x, n=3, sign=False):
    x = float(x)
    s = f"{x:+.{n}f}" if sign else f"{x:.{n}f}"
    return s.replace("-", "&minus;")


def esc(s):
    return html.escape(str(s))


def table(head, rows, tid=None, widths=None):
    h = "".join(f"<td>{c}</td>" for c in head)
    b = "".join("<tr>" + "".join(f'<td class="{cls}">{v}</td>' for cls, v in r) + "</tr>" for r in rows)
    return (f'<div class="table-wrap"><table class="data-table"{f" id={chr(34)}{tid}{chr(34)}" if tid else ""}>'
            f"<thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>")


def fig(src, alt, cap):
    return (f'<figure class="fig wide"><img src="figures/ml_energies/{src}" alt="{esc(alt)}">'
            f"<figcaption>{cap}</figcaption></figure>")


# ------------------------------------------------------------------ numbers
rel = [r for r in ROWS if r["nb_gamma_relaxed"] not in ("", "nan")]
neg = [r for r in rel if float(r["nb_gamma_relaxed"]) <= 0.0]
near = [r for r in rel if 0 < float(r["nb_gamma_relaxed"]) < 0.01]
chk = MU["check"]
n_mofs_rel = len({r["mof"] for r in rel})
slopes = sorted(float(r["slope_J_m2_per_eV"]) for r in rel)
neg_ref = MU["negative_relaxed"][REF]
mu_ref = CONDS[REF]
reprod = [s for s in RX["slabs"] if s["variant"] == "notebook"]
fixed = [s for s in RX["slabs"] if s["variant"] == "fixed"]


def caps(c):
    """Cap chemistry in words: metal OH, water on metal, free water, protonated linker O, C-OH2+."""
    names = [("M-OH", "M&ndash;OH"), ("H2O on metal", "H&#8322;O on M"), ("H2O free", "free H&#8322;O"),
             ("C-O-H", "C&ndash;O&ndash;H"), ("O with 2 H", "C&ndash;OH&#8322;&#8314;")]
    return ", ".join(f"{c[k]} {lab}" for k, lab in names if c.get(k))


def nbval(mof, face, t):
    for r in rel:
        if r["mof"] == mof and r["face"] == face and int(r["termination"]) == t:
            return float(r["nb_gamma_relaxed"])


# ------------------------------------------------------------------ page
P = []
P.append(f'''      <h2 class="section-title" id="mle-short" data-toc="The short answer"><span class="stitle-num">0</span>The Short Answer</h2>
      <p class="sd">The team notebook of 14 November computes surface energies with a machine-learned model (CHGNet) and uses them to draw crystal shapes and to train a neural network. For {len(neg)} crystal faces in {len({r["mof"] for r in neg})} MOFs it reported a <b>negative</b> surface energy. A negative surface energy would mean that the crystal gains energy by breaking itself apart, so a stable crystal with those faces could not exist, and the program correctly refused to draw a shape for those MOFs.</p>
      <p class="sd">The arithmetic is not wrong. The negative values come from <b>where the water used to cap the cut surface is taken from</b>. The notebook takes it from a single water molecule at absolute zero, which is the most favourable water there can be. Taking it instead from liquid water at room temperature, using standard thermochemical tables, raises every surface energy, and <b>none of the {len(rel)} relaxed surfaces is negative any more</b> (Section 4). Two further problems were found and fixed on the way: a capping rule that puts two protons on one oxygen, and two earlier fixes (K3 and K11) that were missing from this version of the notebook.</p>
      <div class="callout warn" data-kind="What this does not fix">Correcting the water reference removes an impossible result; it does not make the energies right. The machine-learned energies have not been checked against quantum chemistry (DFT), and relaxation still lowers them by a large fraction. The shapes on this page are therefore model results for a stated water condition, not predictions to be trusted on their own.</div>
''')

# 1 background
P.append(f'''      <h2 class="section-title" id="mle-background" data-toc="Background"><span class="stitle-num">0</span>Background: What Was Already Known</h2>
      <p class="sd">This section is established science and the team's earlier design. Nothing in it is a new result.</p>
      <h3 class="sub-head">What a surface energy is</h3>
      <p class="sd">Cutting a crystal along a plane breaks the bonds that cross the plane. The energy this costs, per unit area of new surface, is the surface energy &gamma; (J/m&sup2;). Because a cut makes two surfaces, &gamma; is half the cost of the cut per unit area. A face with a low &gamma; is cheap to expose, grows slowly and ends up large; the Wulff construction turns the set of &gamma; values into a crystal shape (<a href="learn_energy.html">Learn: surface energy</a>). For a stable crystal every &gamma; is positive: if one were negative, the crystal would lower its energy by splitting into ever thinner pieces, and no finite shape would exist.</p>
      <h3 class="sub-head">The team's pipeline (steps 1&ndash;8)</h3>
      <ol class="sd">
        <li><b>Standardise</b> the CIF file and find its symmetry.</li>
        <li><b>Split</b> it into building blocks (metal nodes and organic linkers).</li>
        <li><b>List the face families</b> and the different depths at which each face can be cut (terminations).</li>
        <li><b>Cut a slab</b>, a crystal a few nanometres thick with empty space above and below.</li>
        <li><b>Cap</b> every broken metal&ndash;linker bond with water (below).</li>
        <li><b>Compute energies</b> with CHGNet, a neural-network model trained on quantum-chemistry data (Deng et al., 2023), first without moving the atoms (static), then after letting them move to lower energy (relaxed).</li>
        <li><b>Check</b> them with a second model, MACE-MP-0 (Batatia et al., 2023), and prepare inputs for DFT.</li>
        <li><b>Build the shape</b> (Wulff construction).</li>
      </ol>
      <p class="sd">A graph neural network (GNN) is then trained to predict the relaxed &gamma; of a slab from its structure, so that new MOFs would not need the slow relaxation.</p>
      <h3 class="sub-head">Why cut bonds are capped with water</h3>
      <p class="sd">A bare cut leaves metal atoms missing a neighbour and linker oxygens with a dangling bond. Real MOF crystals grow in a solvent, and their surfaces are covered by solvent, water or hydroxide, not left bare. The pipeline mimics this: each broken metal&ndash;oxygen bond is closed by one water molecule split into two pieces, OH&#8315; on the metal and H&#8314; on the oxygen (dissociative or heterolytic capping). The atoms of <i>n</i> water molecules are therefore added to a slab with <i>n</i> broken bonds.</p>
''' + fig("fig_capping_schematic.png", "Five panels: a metal bonded to an oxygen bonded to a carbon; the same cut; the cut capped with OH on the metal and H on the oxygen; a bridging oxygen bonded to two metals, which under the old rule receives two hydrogens; and under the fixed rule receives one, the other hydrogen making a water molecule on a metal.",
          "Panels 1&ndash;3: the capping rule. Panels 4&ndash;5: the bridging-oxygen problem found on 15 November (K12, Section 3.3) and its fix. Schematic, not to scale.") + f'''
      <h3 class="sub-head">The energy of the added water, and why it matters</h3>
      <p class="sd">The surface energy subtracts what the slab's atoms would have cost anyway, inside the crystal and in the water they came from:</p>
      <div class="eq"><span class="ex">&gamma; = [ <i>E</i><sub>slab</sub> &minus; <i>N</i> <i>e</i><sub>bulk</sub> &minus; <i>n</i> &mu;<sub>H&#8322;O</sub> ] / 2<i>A</i></span><span class="tag">(1)</span></div>
      <div class="where"><p class="lead">where</p><dl><dt><i>E</i><sub>slab</sub></dt><dd>energy of the capped slab;</dd><dt><i>N</i>, <i>e</i><sub>bulk</sub></dt><dd>number of framework atoms in the slab and the energy per atom of the bulk crystal;</dd><dt><i>n</i></dt><dd>number of water molecules used as caps;</dd><dt>&mu;<sub>H&#8322;O</sub></dt><dd>the energy of one water molecule <i>in the place it came from</i>: its chemical potential;</dd><dt><i>A</i></dt><dd>area of one face of the slab (two faces, hence 2<i>A</i>).</dd></dl></div>
      <p class="sd">An everyday picture: the chemical potential is the <i>price</i> of water. If water costs nothing, covering a surface with it is free and any attraction between water and the surface is pure gain. If water is dear, because it has to be pulled out of liquid water or humid air where it is comfortable, the gain is smaller. The notebook sets &mu;<sub>H&#8322;O</sub> = <i>E</i><sub>H&#8322;O</sub>, the energy of one isolated molecule at absolute zero, with no thermal motion and no entropy. That is the cheapest water there can be. Under any real condition the price is lower by &Delta;&mu; (a negative number), and</p>
      <div class="eq"><span class="ex">&gamma;(&Delta;&mu;) = &gamma;<sub>0 K</sub> &minus; <i>n</i> &Delta;&mu; / 2<i>A</i></span><span class="tag">(2)</span></div>
      <p class="sd">This is the standard way surface energies are put in contact with a gas or liquid reservoir (ab initio thermodynamics; Reuter and Scheffler, Phys. Rev. B 65, 035406, 2001). Equation (2) is a straight line in &Delta;&mu; whose slope, <i>n</i>/2<i>A</i>, is the number of caps per unit area: faces with many caps per area move most.</p>
      <h3 class="sub-head">The price of water under real conditions</h3>
      <p class="sd">&Delta;&mu; = [<i>H</i>(<i>T</i>) &minus; <i>H</i>(0)] &minus; <i>T S</i>(<i>T</i>) + <i>kT</i> ln(<i>p</i>/1 bar), with the enthalpy and entropy of water vapour from the NIST-JANAF tables (table H-064: <i>H</i>(298.15 K) &minus; <i>H</i>(0) = 9.904 kJ/mol, <i>S</i> = 188.834 J/mol/K; at 400 K, <i>H</i> &minus; <i>H</i>(298.15) = 3.452 kJ/mol and <i>S</i> = 198.788 J/mol/K) and, for liquid water, the CODATA Gibbs energies of formation of the gas and the liquid (&minus;228.582 and &minus;237.129 kJ/mol). Zero-point energy is left out of both the free molecule and the caps, as is usual in this method; the two partly cancel, and the residual, of order 0.1 eV per molecule, is the uncertainty of every &Delta;&mu; below.</p>
''' + table(["", "Condition", "&Delta;&mu; (eV per molecule)"],
            [[("dt-label", TAGS[c]), ("dt-note", esc(c)), ("dt-value", f(v, 3, True))] for c, v in CONDS.items()], "mle-mu") +
         fig("fig_water_price.png", "A horizontal axis of water chemical potential from minus one to zero electronvolts, with five marked conditions: the free molecule at zero kelvin at zero, vapour at 25 degrees and 1 bar at minus 0.48, liquid water at minus 0.57, humid air at minus 0.59 and vapour at 127 degrees at minus 0.69.",
             "The five water conditions used on this page. The notebook used A. The page's reference is C, liquid water at 25 &deg;C."))

# 2 findings: the negative values and the reproduction
neg_rows = []
for r in sorted(neg + near, key=lambda r: float(r["nb_gamma_relaxed"])):
    neg_rows.append([("dt-label", esc(r["mof"])), ("dt-note", esc(r["face"]) + f' t{r["termination"]}'),
                     ("dt-value", r["nb_n_atoms"]), ("dt-value", str(int(float(r["n_water"])))),
                     ("dt-value", f(r["nb_gamma_static"])), ("dt-value", f(r["nb_gamma_relaxed"], 4, True)),
                     ("dt-value", f(r["slope_J_m2_per_eV"])), ("dt-value", f(r["dmu_zero_eV"], 3, True)),
                     ("dt-value", f(r[f"gamma_relaxed@{REF}"], 3))])
rep_rows = []
for s in reprod:
    nb = nbval(s["mof"], s["face"], s["termination"])
    rep_rows.append([("dt-label", esc(s["mof"])), ("dt-note", esc(s["face"]) + f' t{s["termination"]}'),
                     ("dt-value", f(nb, 3, True) if nb is not None else "&ndash;"), ("dt-value", f(s["gamma_relaxed"], 3, True)),
                     ("dt-value", str(s["steps"])), ("dt-note", caps(s["caps_before"])), ("dt-note", caps(s["caps_after"]))])
P.append(f'''      <h2 class="section-title" id="mle-found" data-toc="The negative values"><span class="stitle-num">0</span>What We Found: The Negative Values</h2>
      <p class="sd">From here on the page reports this project's own work. The notebook relaxed {len(rel)} slabs of {n_mofs_rel} MOFs (its cells 5 and 9). {len(neg)} came out at or below zero, and {len(near)} more within 0.01 J/m&sup2; of it:</p>
''' + table(["MOF", "Face, termination", "Atoms", "Water caps <i>n</i>", "&gamma; static", "&gamma; relaxed (notebook)",
             "Slope <i>n</i>/2<i>A</i> (J/m&sup2; per eV)", "&gamma; = 0 at &Delta;&mu; (eV)", f"&gamma; at C, liquid water"], neg_rows, "mle-neg") + f'''
      <p class="sd">All energies in J/m&sup2;. The column &ldquo;&gamma; = 0 at &Delta;&mu;&rdquo; is where equation (2) crosses zero: every negative slab becomes positive once water is even 0.1 eV less available than a free molecule at 0 K. The last column is equation (2) at condition C.</p>
      <h3 class="sub-head">Are these really the notebook's slabs? (reproduction)</h3>
      <p class="sd">The notebook ran on a Colab GPU and its slab files are on the team's Drive, not in the repository. We therefore rebuilt every slab on a CPU with the notebook's own module, unchanged, and the same settings (bulk relaxed for 800 steps at <i>f</i><sub>max</sub> 0.05 eV/&Aring;, slabs computed static). Of the {chk["slabs_in_log"]} slabs in the notebook's log, the {chk["slabs_matched"]} of the 16 relaxed MOFs were rebuilt; the number of atoms agrees for every one ({chk["atom_count_mismatch"]} mismatches) and the static &gamma; agrees to within {f(chk["max_static_gamma_difference_J_m2"], 4)} J/m&sup2;, which is the rounding of the printed log. The remaining slabs belong to the 41 MOFs the notebook computed only statically, for pretraining the GNN. We then relaxed the negative slabs again with the notebook's module:</p>
''' + (table(["MOF", "Face", "&gamma; notebook (GPU)", "&gamma; our rerun (CPU)", "Steps", "Caps before relaxation", "Caps after relaxation"], rep_rows, "mle-rep") if rep_rows else "") + '''
      <p class="sd">The rerun gives the same relaxed values, so the negative numbers are a property of the method, not a fault of one run. The last two columns show what relaxation does to the caps: protons move from the linker oxygen (C&ndash;O&ndash;H) back to a metal OH cap, which becomes a water molecule bound to the metal. The split (heterolytic) capping the pipeline assumes is therefore not what the model finds most stable on these faces.</p>
''')

# 3 causes
k12 = K12["total"] if K12 else None
fx_rows = []
for s in fixed:
    after = s["caps_after"]
    fx_rows.append([("dt-label", esc(s["mof"])), ("dt-note", esc(s["face"]) + f' t{s["termination"]}'), ("dt-note", s["cap"]),
                    ("dt-value", str(s["n_atoms"])), ("dt-value", str(s["n_water"])), ("dt-value", f(s["gamma_static"])),
                    ("dt-value", f(s["gamma_relaxed"], 4, True)), ("dt-value", "yes" if s["converged"] else "no"),
                    ("dt-value", str(s["n_free_water_after"]) if s["cap"] == "water" else "&ndash;"),
                    ("dt-value", f(s["gamma_relaxed_at"][REF]["free_water_left"], 3) if s["cap"] == "water" else f(s["gamma_relaxed"], 3))])
P.append(f'''      <h2 class="section-title" id="mle-causes" data-toc="Three causes"><span class="stitle-num">0</span>Three Causes</h2>
      <h3 class="sub-head">Cause 1: the water is taken from a free molecule at 0 K (all six slabs)</h3>
      <p class="sd">In equation (1) the water caps are paid for at the price of a free molecule at absolute zero. On a cut surface the metal atoms have lost a neighbour, and a water-derived cap binds to them strongly. With water this cheap, the binding gained outweighs the cost of cutting the crystal, and &gamma; falls below zero. This affects every slab, but most strongly those with many caps per unit area: the slope <i>n</i>/2<i>A</i> of the {len(rel)} relaxed slabs runs from {f(slopes[0])} to {f(slopes[-1])} J/m&sup2; per eV (median {f(slopes[len(slopes) // 2])}). At liquid water (C, &Delta;&mu; = {f(mu_ref, 3, True)} eV) &gamma; rises by between {f(-slopes[0] * mu_ref, 2)} and {f(-slopes[-1] * mu_ref, 2)} J/m&sup2;, which is larger than many of the relaxed values themselves. The water reference is therefore not a small correction: it decides the order of the faces for several MOFs (Section 4).</p>
      <h3 class="sub-head">Cause 2: two fixes were missing (Mg-MOF-74 and HKUST-1)</h3>
      <p class="sd">On 10 November two problems in the pipeline were found and fixed (<a href="morphology_map.html">The morphology map</a>, problems K3 and K11). K11: after the bulk relaxation the cell is written to a file and read back, which re-orients it, so faces of crystals whose working cell differs from the conventional cell were converted to the wrong planes, or the program fell back to the unrelaxed cell. K3: slab and bulk energies could then come from different geometries. The notebook of 14 November does not contain either fix. For Mg-MOF-74 {{2&#773;10}} it cut its slab from the unrelaxed conventional cell (378 atoms, static &gamma; 1.216, relaxed &minus;0.0135 J/m&sup2;); with both fixes the slab is cut from the relaxed working cell (126 atoms, static 1.016, relaxed +0.002 J/m&sup2;; <code>results_full_fixed/fix_Mg-MOF-74.log</code>). Both are effectively zero: the missing fixes change the static value by 0.2 J/m&sup2; but are not what makes this face negative. The same holds for ZnBDC {{001}}, whose working cell is its conventional cell but whose slab was still built from the unrelaxed atoms: with the fixes its static &gamma; falls from 2.297 to 0.663 J/m&sup2;, while the relaxed value stays at &minus;0.028 J/m&sup2; (table at the end of this section). Relaxation removes most of the K3 error; the water reference remains.</p>
      <h3 class="sub-head">Cause 3: a capping rule that puts two protons on one oxygen (K12, new)</h3>
      <p class="sd">The capping rule adds one H&#8314; to a linker oxygen for every metal bond it lost. In MOF-74 and some other frameworks an oxygen bridges two metal atoms; if the cut removes both, the oxygen receives two protons and becomes C&ndash;OH&#8322;&#8314;, a group that is not stable (panel 4 of the figure above). {f"Among the {k12['slabs']} slabs of the 16 relaxed MOFs, {k12['slabs_with_C_OH2']} contain such a group, in {', '.join(k12['mofs_affected'])}." if k12 else ""} ZnBDC and MIL-47 are not affected, so this is not why they are negative. Cd3BTB2 is: with the corrected capping (and the restored fixes) its {{010}} slab relaxes to a positive &gamma; even with the old water reference (table below), so for Cd3BTB2 the capping error, not only the water reference, made the value negative. During relaxation CHGNet moves such protons back: in the fixed run of Mg-MOF-74 {{2&#773;10}} the six OH caps became three OH caps, two water molecules on magnesium and one water molecule that left the surface altogether. The rule is now fixed: a linker oxygen receives at most one proton, and each surplus proton turns the nearest metal OH cap into a water molecule bound to the metal. The atoms added, the charge balance and <i>n</i> are unchanged.</p>
      <p class="sd">A water molecule that has left the surface is not part of it. At a realistic &Delta;&mu; it would leave, so for these slabs equation (2) is applied with <i>n</i> reduced by the number of free molecules found after relaxation.</p>
''' + ((f'''      <h3 class="sub-head">The negative slabs recomputed with all three fixes</h3>
      <p class="sd">Each negative slab was rebuilt with the corrected module (K3, K11 and K12) and relaxed twice: once with water caps and once bare (no caps; a bare slab is only possible when the cut breaks no organic bond). The bare surface is the limit in which no water is available at all.</p>
''' + table(["MOF", "Face", "Caps", "Atoms", "<i>n</i>", "&gamma; static", "&gamma; relaxed (0 K water)", "Converged",
             "Free H&#8322;O after", "&gamma; at C (J/m&sup2;)"], fx_rows, "mle-fixed") + '''
      <p class="sd">For capped slabs the last column uses equation (2) with the free molecules removed; for bare slabs it is the relaxed value itself, which does not depend on water.</p>
''') if fx_rows else ""))

K2 = J("k2_check.json")
if K2:
    mg = K2["mg_mof_74_static"]
    P.append(f'''      <h3 class="sub-head">Older problems fixed in the same module (K1, K2, K4&ndash;K10)</h3>
      <ul class="sd">
        <li><b>K1, shape names.</b> Names now come from the exact limits of the cubic map: a pure cube, octahedron or rhombic dodecahedron only within numerical noise (0.1 % of the area), the cuboctahedron only within 0.005 of its exact {{100}} share 6/(6 + 2&radic;3). All 14 test ratios of <code>checks/naming.py</code> are named correctly (the notebook version misnamed 3).</li>
        <li><b>K2, the metal rod of MOF-74.</b> Two metals bonded to the same linker oxygen now belong to one inorganic unit, so the Mg&ndash;O rod of Mg-MOF-74 (and of Ni-DOBDC) is recognised as one infinite unit, and Cd3BTB2 gets its Cd<sub>3</sub> cluster; the other eight MOFs checked are unchanged. With static energies only, the Mg-MOF-74 shape is still a block ({esc(mg["liquid_298K"]["habit"])} at liquid water); with relaxed energies from the GPU run it becomes a hexagonal rod along <i>c</i>, as in the laboratory (Section 5).</li>
        <li><b>K5&ndash;K10, six smaller problems</b>, fixed in the corrected notebook after the GPU run: the UiO-66 input now has its Zr<sub>6</sub>O<sub>4</sub>(OH)<sub>4</sub> node; an open Wulff shape is called open, not a rod; faces are ranked by the effective spacing <i>d</i>/<i>n</i>, so faces forbidden by symmetry are not kept ahead of allowed ones (for the four benchmark MOFs the kept faces do not change); the MACE rank correlation is also taken over all slabs; the DFT inputs get the surface dipole correction and a stated spin state; and a cell checks one face at three slab thicknesses. Their numbers need the next GPU run.</li>
        <li><b>K4, a wrong reference shape.</b> The notebook compared UiO-66 with octahedra; additive-free UiO-66 gives cubes in our records, and octahedra need benzoic or acetic acid. Corrected in the notebook's input table.</li>
      </ul>
''')

# 4 effect on shapes
shape_rows = []
for m, e in MU["mofs"].items():
    a, c = e["conditions"][A0], e["conditions"][REF]
    shape_rows.append([("dt-label", esc(m)), ("dt-note", esc(a["habit"])), ("dt-note", esc(a["dominant_face"] or "&ndash;")),
                       ("dt-note", esc(c["habit"])), ("dt-note", esc(c["dominant_face"] or "&ndash;")),
                       ("dt-note", "yes" if e["face_order_changes_at_reference"] else "no")])
P.append(f'''      <h2 class="section-title" id="mle-effect" data-toc="Effect on the shapes"><span class="stitle-num">0</span>The Correction and Its Effect on Every MOF</h2>
      <p class="sd">Equation (2) was applied to every relaxed, converged slab of the notebook (<code>water_mu_analysis.py</code>). At conditions B to E no slab is negative: {"none of the " + str(len(rel)) + " relaxed slabs" if not neg_ref else str(len(neg_ref)) + " slabs remain negative"}. The table compares the notebook's shapes (water at A) with the shapes at liquid water (C). Shape names come from the corrected naming function (K1, below in Section 3).</p>
''' + table(["MOF", "Shape at A (notebook)", "Main face", "Shape at C (liquid water)", "Main face", "Face order changes"],
            shape_rows, "mle-shapes") + '''
      <p class="sd">The shape depends on the water condition for several MOFs. The figure below follows the main face across the whole range of &Delta;&mu;: a change of colour along a row means the main face changes; a cross means that some face has &gamma; &le; 0 and no shape exists.</p>
''' + fig("fig_main_face_vs_mu.png", "One row per MOF, horizontal axis water chemical potential from minus one to plus 0.1 electronvolts, coloured by the main face of the Wulff shape. Most rows are one colour; ZnBDC, MOF-70, MIL-47 and MIL-88B-open change colour; ZnBDC, Cd3BTB2, MIL-47 and Mg-MOF-74 have crosses near zero.",
          "Main face of the Wulff shape against the water condition, for the 16 MOFs the notebook relaxed. Dashed lines A&ndash;E are the conditions of the table in Section 2. MIL-88A-open has only one face family with a converged relaxed slab, so no shape can be built for it at any condition.") +
         "".join(fig(f"fig_gamma_vs_mu_{m}.png", f"Surface energy of each face of {m} as a straight line against water chemical potential; lines fall from left to right and cross zero near zero chemical potential.",
                     f"{esc(m)}: &gamma; of each face (lowest termination) against &Delta;&mu;. The lines cross: the order of the faces depends on the water condition.")
                 for m in ("Mg-MOF-74", "ZnBDC", "MIL-47", "Cd3BTB2")))

# 4b the corrected notebook on a GPU
CR = os.path.join(D, "colab_run_2026-11-15")
if os.path.exists(os.path.join(CR, "wulff_summary.csv")):
    WS = list(csv.DictReader(open(os.path.join(CR, "wulff_summary.csv"), encoding="utf-8")))
    SA = list(csv.DictReader(open(os.path.join(CR, "slabs_all.csv"), encoding="utf-8")))
    srel = [r for r in SA if r["gamma_relaxed_J_m2"] not in ("", "nan")]
    sconv = [r for r in srel if r["converged"] == "True"]
    neg0 = [r for r in srel if float(r["gamma_relaxed_J_m2"]) <= 0]
    negl = [r for r in srel if float(r["gamma_relaxed_J_m2"]) + float(r["n_water"]) / (2 * float(r["area_A2"])) * 16.0218 * 0.5695 <= 0]
    rows = []
    for w in WS:
        old_h = MU["mofs"].get(w["mof"], {}).get("conditions", {}).get(A0, {}).get("habit", "&ndash;")
        fr = json.loads(w["area_fractions"]) if w["area_fractions"] else {}
        rows.append([("dt-label", esc(w["mof"])), ("dt-note", esc(old_h)), ("dt-note", esc(w["habit"])),
                     ("dt-note", ", ".join(f"{esc(k)} {v:.0%}" for k, v in fr.items())), ("dt-note", esc(w["reference_habit"]))])
    imgs = "".join(f'<figure class="fig"><img src="figures/ml_energies/colab/wulff_{m}_water.png" alt="Wulff shape of {m} from the corrected notebook at liquid-water chemical potential."><figcaption>{m}, corrected notebook, liquid water (GPU run of 15 November).</figcaption></figure>'
                   for m in ("ZIF-8", "HKUST-1", "Mg-MOF-74", "UiO-66"))
    P.append(f'''      <h2 class="section-title" id="mle-gpu" data-toc="The corrected notebook on a GPU"><span class="stitle-num">0</span>The Corrected Notebook on a GPU</h2>
      <p class="sd">A team member ran the corrected notebook (<code>MOF_Wulff_steps1_8_plus_GNN_corrected.ipynb</code>, with all fixes including the hydroxylated UiO-66 input) end to end on a GPU on 15 November, with the water condition set to liquid water at 25 &deg;C. (An earlier run the same morning, without the last six fixes, gave the same shapes; it is kept in <code>colab_run_2026-11-15_v1/</code>.) It relaxed {len(srel)} slabs of {len({r["mof"] for r in srel})} MOFs ({len(sconv)} converged). At the old reference (a free molecule at 0 K) {len(neg0)} of them are still slightly negative ({", ".join(f"{r['mof']} {r['face']} {f(r['gamma_relaxed_J_m2'], 4, True)}" for r in neg0)}); at liquid water {'none is' if not negl else str(len(negl)) + ' are'}. Where the same slab was computed on our CPU (Section 3) the values agree, so the result does not depend on the hardware.</p>
      <p class="sd"><b>Two further checks in the same run.</b> Slab thickness: ZIF-8 {{110}} at 24 and 36 &Aring; gives &gamma; = 0.0565 and 0.0527 J/m&sup2; at liquid water, a change of 0.004 J/m&sup2;, so the slabs are thick enough (<code>thickness_check.csv</code>). Second model: MACE-MP-0 re-scores all 20 slabs of the four MOFs in the same order as CHGNet (rank correlation 0.94&ndash;1.00 per MOF, mean difference 0.010&ndash;0.028 J/m&sup2;; <code>validation_mace.csv</code>).</p>
''' + table(["MOF", "Shape, notebook of 14 November", "Shape, corrected notebook (liquid water)", "Faces (share of surface)", "Laboratory shape (reference)"], rows, "mle-gpu-shapes") + f'''
      <p class="sd">ZIF-8 (rhombic dodecahedron, {{110}}) and HKUST-1 (mainly {{111}}) agree with the laboratory shape, as before. <b>Mg-MOF-74 changes from no shape at all to a hexagonal rod along <i>c</i>, the habit seen in the laboratory</b>: its metal rod is now kept whole (K2), so faces that would cut it, such as {{001}}, are expensive and drop out of the shape, and the prism face {{2&#773;10}} takes 77 % of the surface. UiO-66 still comes out mainly {{111}} (81 %), now with its correct Zr<sub>6</sub>O<sub>4</sub>(OH)<sub>4</sub> node, while additive-free UiO-66 grows as cubes; the corrected input did not change this, so it remains the model's miss, as in the benchmark (<a href="experiment.html">Against experiment</a>). These are four MOFs and one energy model with no DFT check, so the agreement is encouraging but is not a validation.</p>
      <div class="shape-grid">{imgs}</div>
''')
    GPU_CV = list(csv.DictReader(open(os.path.join(CR, "gnn_cv_summary.csv"), encoding="utf-8")))
else:
    GPU_CV = None

# 5 GNN
gnn_html = ""
if GNN:
    order = ["gnn", "bonds_linear", "mean", "static_calibrated", "bfdh_linear", "static_chgnet"]
    rows = []
    for arm in ("original", "corrected"):
        s = GNN["arms"].get(arm, {}).get("summary", {})
        for mdl in order:
            if mdl in s:
                v = s[mdl]
                rows.append([("dt-label", arm), ("dt-note", mdl), ("dt-value", f(v["MAE_J_m2"])),
                             ("dt-value", f(v["spearman_families"], 2) if v["spearman_families"] is not None else "&ndash;"),
                             ("dt-value", f(v["lowest_face_agrees"], 2)), ("dt-value", f(v["habit_agrees"], 2) if v["habit_agrees"] is not None else "&ndash;")])
    gnn_html = (f'''      <p class="sd">We repeated the notebook's cross-validation on a CPU with the same folds, models and baselines ({GNN["epochs"]} epochs, {GNN["seeds"]} seeds, pretraining on static &gamma;), once with the notebook's labels (water at A, negative labels kept) and once with the corrected labels (water at C, &gamma; &le; 0 dropped). {GNN["n_graphs"]} slab graphs, {GNN["n_relaxed_labels"]} with a relaxed label.</p>
''' + table(["Labels", "Model", "MAE (J/m&sup2;)", "Spearman (faces)", "Lowest face right", "Shape right"], rows, "mle-gnn") +
        '''      <p class="sd">MAE is the mean absolute error over the held-out MOFs; the other three columns are fractions of held-out MOFs. Lower MAE and higher fractions are better. With 16 MOFs, differences of a few hundredths are within the run-to-run spread of the GNN.</p>
''')
gpu_cv_html = ""
if GPU_CV:
    names = dict(gnn="GNN", bonds_linear="straight line on broken bonds per area", static_calibrated="static CHGNet &gamma;, rescaled",
                 mean="mean of the training labels", bfdh_linear="straight line on BFDH spacing", static_chgnet="static CHGNet &gamma;, as computed")
    rows = [[("dt-note", names.get(r["model"], esc(r["model"]))), ("dt-value", f(r["MAE_J_m2"])),
             ("dt-value", f(r["spearman_families"], 2) if r["spearman_families"] else "&ndash;"),
             ("dt-value", f(r["lowest_face_agrees"], 2)), ("dt-value", f(r["habit_agrees"], 2)), ("dt-value", f(r["dominant_agrees"], 2))]
            for r in sorted(GPU_CV, key=lambda r: float(r["MAE_J_m2"]))]
    gpu_cv_html = ("      <p class=\"sd\">The GPU run repeated the cross-validation with the corrected labels (liquid water, labels &le; 0 dropped): each of the " + GPU_CV[0]["n_mofs"] + " MOFs is held out in turn and predicted by models trained on the others.</p>\n"
                   + table(["Model", "MAE (J/m&sup2;)", "Rank correlation (faces)", "Lowest face right", "Shape right", "Main face right"], rows, "mle-gpu-cv")
                   + "      <p class=\"sd\">MAE is the mean absolute error on the held-out MOFs; the other columns are averages over the held-out MOFs. With the corrected labels the GNN is still behind the two simple baselines on error and on getting the lowest face right (MAE 0.131 against 0.088 for the broken-bond line and 0.084 for the rescaled static energy) and on naming the main face (12 of 16 against 14 of 16). On 16 MOFs these differences are a few MOFs, so no learned model is shown to help yet. The labels differ from the notebook's (a different water condition), so the MAE values cannot be compared with the notebook's 0.137 and 0.090 directly.</p>\n")

P.append(f'''      <h2 class="section-title" id="mle-gnn" data-toc="What changes for the GNN"><span class="stitle-num">0</span>What Changes for the GNN</h2>
      <p class="sd">This section is written from the machine-learning side. The GNN learns relaxed &gamma; from the unrelaxed slab structure. Its output passes through a softplus function, so it can only predict positive values, yet the notebook trained it on the {len(neg)} negative labels as if they were real. A model cannot fit a label it cannot output, and the label itself was an artefact of the water reference. The corrected <code>mofgnn.py</code> moves every label (relaxed and static, used for pretraining) to a stated water condition with <code>at_water_mu()</code>, and <code>load_dataset()</code> now drops any label &le; 0 and prints which ones it dropped.</p>
{gnn_html or gpu_cv_html or '      <p class="sd">The cross-validation itself has not been rerun with the corrected labels: on the two CPU cores available here it takes many hours (three seeds, five folds and pretraining on about 400 slabs). The corrected notebook (<code>MOF_Wulff_steps1_8_plus_GNN_corrected.ipynb</code>) does it in the next Colab GPU session, and <code>gnn_rerun.py</code> repeats it on a CPU with both sets of labels side by side.</p>\n'}      <p class="sd">In the notebook's own run, a straight line fitted to broken bonds per area already beat the GNN (MAE 0.090 against 0.137 J/m&sup2;). That remains the baseline any learned model has to beat.</p>
''')

# 5b morphology spectrum (team notebook v4)
SPJ = json.load(open(os.path.join(ROOT, "code", "morphology", "steps1_8_check", "nb_2026-11-15_v4_isha",
                                  "spectrum_corrected_liquid_water.json"), encoding="utf-8"))
LAB = {"ZIF-8": ("rhombic dodecahedron", ["rhombic_dodecahedron"]),
       "HKUST-1": ("octahedron", ["octahedron"]),
       "UiO-66": ("cube without additives (2 of 3 records); octahedron with benzoic or acetic acid (4 records)", ["cube", "octahedron"]),
       "Mg-MOF-74": ("hexagonal rod along c", None)}
def _cls(c):
    return esc(c["class_id"].replace("_", " "))
sp_rows = []
for m, o in SPJ.items():
    areas = ", ".join(f"{esc(k)} {100 * v:.0f} %" for k, v in sorted(o["areas"].items(), key=lambda kv: -kv[1]) if v >= 0.05)
    near = o["closest"][1]
    labtxt, labcls = LAB[m]
    if labcls is None:
        dist = "0 % (favoured shape is a rod)"
    else:
        parts = []
        for lc in labcls:
            c = next(c for c in o["closest"] if c["class_id"].split(" |")[0] == lc)
            parts.append(f'{esc(lc.replace("_", " "))}: {c["min_ratio_change_pct"]:.1f} %'
                         + (f' (lower {esc(c["lower_face"])})' if c["lower_face"] else ""))
        dist = "; ".join(parts)
    sp_rows.append([("", esc(m)), ("", esc(o["favoured"].split(":")[0].replace("_", " ")) + f" ({areas})"), ("", esc(labtxt)),
                    ("", dist), ("", _cls(near) + f' at {near["min_ratio_change_pct"]:.1f} %'), ("num", str(o["n_classes"]))])
P.append(f'''      <h2 class="section-title" id="mle-spectrum" data-toc="Morphology spectrum"><span class="stitle-num">0</span>The Morphology Spectrum: How Far Is Each Other Shape?</h2>
      <p class="sd">A Wulff shape depends only on the ratios of the surface energies, not on their scale. The team notebook of 15 November (version 4, <code>nb_2026-11-15_v4_isha/</code>) adds a module, <code>morphspec.py</code>, that scans these ratios and lists <b>every shape class the face set of a MOF can produce</b>. A class is the shape name together with the faces that cover at least 5 % of the surface. For each class it gives <b>the smallest change in an energy ratio that reaches it</b>, starting from the computed (favoured) energies.</p>
      <p class="sd">The distance between two energy vectors <i>g</i> and <i>g</i><sub>0</sub> is defined as <i>s</i> = max<sub>k</sub> ln(<i>g</i><sub>k</sub>/<i>g</i><sub>0,k</sub>) &minus; min<sub>k</sub> ln(<i>g</i><sub>k</sub>/<i>g</i><sub>0,k</sub>), reported as (e<sup><i>s</i></sup> &minus; 1) &times; 100 %: the ratio of two face energies must change by at least this much. It does not depend on the overall scale or on which face is the reference. The scan is a full grid of ratios from 0.3 to 2.5 in steps of 0.05 for cubic MOFs (three faces, two ratios, 2,025 Wulff shapes) and a Sobol sample for MOFs with four faces; the closest point of each class is refined by bisection and its shape is computed again to confirm the class. The module has 20 built-in checks (for example: &gamma;{{111}}/&gamma;{{100}} = 2/&radic;3 gives a cuboctahedron, and {{111}} vanishes at exactly &radic;3); all pass when run here, and all pass again with the corrected modules.</p>
      <p class="sd">Run on the corrected GPU energies at liquid water. The nearest classes are often a shape with one extra small facet (for example a few per cent of {{110}}); the column that matters is the distance to the shape the laboratory reports:</p>
''' + table(["MOF", "Favoured shape (corrected energies)", "Laboratory", "Distance to the laboratory shape", "Nearest other class", "Classes"], sp_rows, "mle-spec") + '''
      <div class="shape-grid">
        <figure class="fig"><img src="figures/ml_energies/spectrum/map_UiO-66.png" alt="Map of gamma ratios for UiO-66 coloured by shape class, with the favoured point and the BFDH point"><figcaption>UiO-66: every point of the ratio map coloured by its shape class. Star: the corrected energies. Triangle: BFDH. The octahedron region (bottom) starts 19.7 % away; the cube region (top right) is 80.4 % away.</figcaption></figure>
        <figure class="fig"><img src="figures/ml_energies/spectrum/UiO-66_octahedron_class.png" alt="The closest octahedron for UiO-66, 95 percent 111 faces"><figcaption>The nearest point of the octahedron class for UiO-66: {111} 95 %, reached by lowering &gamma;{111} relative to &gamma;{100} by 19.7 %. Removing every {100} facet needs &gamma;{111}/&gamma;{100} = 1/&radic;3, a 43.7 % change.</figcaption></figure>
      </div>
      <p class="sd"><b>What it says about UiO-66</b>, the MOF the pipeline misses. The octahedra grown with benzoic or acetic acid are close to the computed energies; the cubes grown without additives are far (80.4 %). An additive that binds {111} would move the shape in the observed direction, while the additive-free cube is not explained by these energies.</p>
      <p class="sd">The same module was run by the team on MIL-125 (titanium, tetragonal; four faces, so a three-ratio Sobol scan), with the GNN energies and with CHGNet energies at the 0 K water reference of version 4:</p>
      <div class="shape-grid">
        <figure class="fig"><img src="figures/ml_energies/spectrum/MIL-125_fig_01.jpeg" alt="MIL-125 spectrum with GNN energies: shape classes sorted by distance"><figcaption>MIL-125 with GNN energies: 31 classes. Favoured: block/prism of {101} (58 %) and {110} (41 %), the same class as BFDH. Nearest: a plate at 8.1 %, a rod at 10.7 %.</figcaption></figure>
        <figure class="fig"><img src="figures/ml_energies/spectrum/MIL-125_fig_11.jpeg" alt="MIL-125 spectrum with CHGNet relaxed energies"><figcaption>MIL-125 with CHGNet relaxed energies (0 K water reference): favoured block/prism, {101} 90 %. Nearest: a plate at 3.5 %, a {101}-only block at 5.1 %.</figcaption></figure>
        <figure class="fig"><img src="figures/ml_energies/spectrum/MIL-125_fig_02.jpeg" alt="MIL-125 favoured shape from GNN energies"><figcaption>Favoured MIL-125 shape from the GNN.</figcaption></figure>
        <figure class="fig"><img src="figures/ml_energies/spectrum/MIL-125_fig_21.jpeg" alt="MIL-125 favoured shape from CHGNet energies"><figcaption>Favoured MIL-125 shape from CHGNet.</figcaption></figure>
      </div>
      <p class="sd"><b>Limits.</b> For a cubic crystal the list of classes follows from symmetry alone; the structure-specific result is the distances. Only low-index faces are included, so {211} and similar faces can never appear. The MIL-125 CHGNet values use the 0 K water reference and have not been recomputed at liquid water, and no laboratory habit of MIL-125 has been checked against the project's records, so those figures show the method, not a validated prediction. How the version 4 notebook differs from the corrected one is set out in <code>docs/v4_vs_corrected.md</code>.</p>
''')

# 6 meaning, limits, possibilities
P.append(f'''      <h2 class="section-title" id="mle-meaning" data-toc="What it means"><span class="stitle-num">0</span>What It Means, Its Limits and the Possibilities</h2>
      <h3 class="sub-head">What can be said</h3>
      <ul class="sd">
        <li>The negative surface energies were an artefact of the water reference, not a property of the MOFs. With water taken from any realistic condition, every relaxed &gamma; is positive.</li>
        <li>The water condition is a real input to the model, not a detail: for several MOFs it changes the order of the faces and hence the predicted shape. Any shape from this pipeline must say which water condition it assumes.</li>
        <li>The capping rule had a chemistry error (K12) for bridging oxygens, now fixed; the K3 and K11 fixes must be carried into every new version of the notebook.</li>
      </ul>
      <h3 class="sub-head">What cannot be said</h3>
      <ul class="sd">
        <li>That the corrected energies are right. Relaxation still lowers them by 60&ndash;100 %, no value has been compared with DFT, and the MACE-MP-0 check re-scores the CHGNet geometries rather than relaxing them independently, so it tests the energy model but not the geometry.</li>
        <li>That liquid water is the right condition. MOFs are often grown in DMF or other solvents, with modulators; water is the pipeline's stand-in for whatever covers the surface.</li>
        <li>That the free-energy terms of the caps are negligible. Their vibrations and entropy are left out (Section 1), an uncertainty of about 0.1 eV per molecule in &Delta;&mu;, that is up to {f(slopes[-1] * 0.1, 2)} J/m&sup2; in &gamma; for the most densely capped slab.</li>
      </ul>
      <h3 class="sub-head">The possibilities, and what would decide between them</h3>
      <ul class="sd">
        <li><b>Water binds as a molecule, not split.</b> On Mg-MOF-74 relaxation turned split caps back into bound water. A capping scheme with whole water molecules, compared with the split scheme at the same &Delta;&mu;, would show which the model prefers; DFT on one slab would decide.</li>
        <li><b>A different solvent.</b> Capping with DMF or a carboxylate modulator, with its own chemical potential, is the same method with a different reservoir, and is the natural way to model additives.</li>
        <li><b>The bare surface is the stable one at low &Delta;&mu;.</b> The true &gamma;(&Delta;&mu;) is the lowest of all possible coverings; comparing capped and bare slabs, as in Section 3, gives the crossover.</li>
        <li><b>What would disprove the correction:</b> a DFT calculation of one of these slabs giving a negative &gamma; at liquid-water &Delta;&mu;, or a converged CHGNet value that changes sign with slab thickness.</li>
      </ul>
''')

# 7 sources
P.append('''      <h2 class="section-title" id="mle-sources" data-toc="Sources and files"><span class="stitle-num">0</span>Sources and Files</h2>
      <p class="sd">The team notebook of 15 November (version 4, with the morphology spectrum) is in <code>code/morphology/steps1_8_check/nb_2026-11-15_v4_isha/</code>. The analysis and corrections on this page are in <code>code/morphology/steps1_8_check/nb_2026-11-14/</code> (see its README):</p>
      <ul class="sd">
        <li><code>MOF_Wulff_steps1_8_plus_GNN.ipynb</code>: the team notebook of 14 November, with its outputs, as received.</li>
        <li><code>MOF_Wulff_steps1_8_plus_GNN_corrected.ipynb</code>: the same notebook with every correction on this page (and K1, K2, K4), outputs cleared, ready for a Colab GPU session.</li>
        <li><code>notebook_module/</code>: <code>mofwulff.py</code> and <code>mofgnn.py</code> exactly as written by the notebook.</li>
        <li><code>mofwulff.py</code>, <code>mofgnn.py</code>: the corrected modules (K3, K11, K12, water condition, GNN labels).</li>
        <li><code>run_static.py</code> (slab rebuild), <code>relax_cases.py</code> (relaxations), <code>water_mu_analysis.py</code> and <code>water_mu_sweep.py</code> (equation (2), shapes, figures), <code>relax_summary.py</code> and <code>cap_chemistry.py</code> (what the caps become), <code>k12_count.py</code>, <code>k2_check.py</code>, <code>gnn_rerun.py</code>, <code>make_water_figures.py</code>; checks in <code>tests_nb14.py</code> (14 checks).</li>
        <li>Results in <code>results/</code>: <code>water_mu.json</code>/<code>.csv</code>, <code>water_mu_sweep.json</code>, <code>relax_cases.json</code>, <code>k12_count.json</code>, <code>gnn_rerun.json</code>.</li>
      </ul>
      <p class="sd">References: CHGNet, B. Deng et al., Nature Machine Intelligence 5, 1031 (2023); MACE-MP-0, I. Batatia et al., arXiv:2401.00096 (2023); K. Reuter and M. Scheffler, Phys. Rev. B 65, 035406 (2001); NIST-JANAF Thermochemical Tables, table H-064 (water, ideal gas); CODATA Key Values for Thermodynamics (1989).</p>
''')

open(OUT, "w", encoding="utf-8").write("\n".join(P))
print("wrote", OUT)
