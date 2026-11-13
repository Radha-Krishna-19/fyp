"""Writes fragments/experiment.before.html (page experiment.html) from the Python results, so every
number on the page comes straight from a JSON or CSV file:

  code/morphology/results/chgnet_cleavage_results.json   run_chgnet_cleavage.py
  code/morphology/results/slab_pieces.json               slab_check.py
  code/morphology/results/slab_options.json              slab_options_check.py (optional)
  code/morphology/results/bond_sensitivity.json          run_bond_sensitivity.py
  code/morphology/results/core_results.json              run_core.py
  data/chgnet_morphograph_runs/<MOF>_<date>/          the CHGNet notebook runs (fit summaries)
  data/experimental_morphology/dataset/experimental_morphology.csv
  data/experimental_morphology/compare/comparison.csv        compare_with_project.py

Run:  python website/_build/build_experiment_fragment.py   then   python website/_build/build_site.py
"""
import csv, glob, html, io, json, os, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
RES = os.path.join(REPO, "code", "morphology", "results")
EXP = os.path.join(REPO, "data/experimental_morphology")


def J(name):
    p = os.path.join(RES, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


CC, PIECES, OPTS, BS, CORE = (J("chgnet_cleavage_results.json"), J("slab_pieces.json"), J("slab_options.json"),
                              J("bond_sensitivity.json"), J("core_results.json"))
EXP_ROWS = list(csv.DictReader(open(os.path.join(EXP, "dataset", "experimental_morphology.csv"), encoding="utf-8")))
CMP = list(csv.DictReader(open(os.path.join(EXP, "compare", "comparison.csv"), encoding="utf-8")))
E = html.escape


def fam(t):
    t = E(t)
    return t[:-1] + "<sub>+</sub>" if t.endswith("+") else (t[:-1] + "<sub>&minus;</sub>" if t.endswith("-") else t)


def table(head, rows, tid=None, widths=None):
    th = "".join(f"<td>{h}</td>" for h in head)
    return (f'<div class="table-wrap"><table class="data-table"{f" id={chr(34)}{tid}{chr(34)}" if tid else ""}>'
            f"<thead><tr>{th}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>")


# ---------- 1. the experimental dataset ------------------------------------------------------
by_mof = defaultdict(list)
for r in EXP_ROWS:
    by_mof[r["mof"]].append(r)
papers = {r["source_id"] for r in EXP_ROWS}
ds_rows = []
for m in sorted(by_mof, key=lambda m: -len(by_mof[m])):
    rs = by_mof[m]
    shapes = Counter(r["morphology"].replace("_", " ") for r in rs if r["morphology"])
    solv = Counter(r["solvent"].split(" (")[0] for r in rs if r["solvent"])
    temps = [float(r["temperature_C"]) for r in rs if r["temperature_C"].replace(".", "", 1).isdigit()]
    trange = ("not stated" if not temps else f"{min(temps):g} &deg;C" if min(temps) == max(temps)
              else f"{min(temps):g}&ndash;{max(temps):g} &deg;C")
    add = sum(1 for r in rs if r["additive"] and r["additive"].lower() not in ("none", ""))
    ds_rows.append(f'<tr data-mof="{E(m)}"><td class="dt-label">{E(m)}</td><td class="dt-value">{len(rs)}</td>'
                   f'<td class="dt-value">{len({r["source_id"] for r in rs})}</td>'
                   f'<td class="dt-note">{E(", ".join(f"{k} ({v})" for k, v in shapes.most_common(4)))}</td>'
                   f'<td class="dt-note">{E(", ".join(k for k, _ in solv.most_common(3))) or "not stated"}</td>'
                   f'<td class="dt-note">{trange}</td><td class="dt-value">{add}</td></tr>')

# ---------- 2. comparison table ----------------------------------------------------------------
cmp_rows = []
for r in CMP:
    ok = lambda v: '<span style="color:var(--good)">yes</span>' if v == "True" else '<span style="color:var(--bad)">no</span>'
    note = f'<br><small>{E(r.get("robustness_note", ""))}</small>' if r.get("robustness_note") else ""
    cmp_rows.append(f'<tr data-cmp="{E(r["mof"])}|{E(r["method"])}"><td class="dt-label">{E(r["mof"])}</td>'
                    f'<td class="dt-note">{E(r["method"])}{note}</td><td class="dt-note">{E(r["predicted"])}</td>'
                    f'<td class="dt-note">{fam(r["largest_face"])} ({float(r["largest_face_fraction"]):.2f})</td>'
                    f'<td class="dt-note">{E(r["experiment"].replace("_", " "))}</td><td class="dt-value">{ok(r["name_match"])}</td>'
                    f'<td class="dt-value">{ok(r["facet_match"])}</td></tr>')
score = defaultdict(lambda: [0, 0, 0])
for r in CMP:
    s = score[r["method"]]; s[0] += r["name_match"] == "True"; s[1] += r["facet_match"] == "True"; s[2] += 1
score_rows = [f'<tr><td class="dt-note">{E(m)}</td><td class="dt-value">{a} / {n}</td><td class="dt-value">{b} / {n}</td></tr>'
              for m, (a, b, n) in score.items()]

# ---------- 3. CHGNet: why the notebook gave no shape --------------------------------------------
rank_rows = []
sys.path.insert(0, os.path.join(REPO, "code", "morphology"))
from mofmorph.chgnet_runs import runs
for Z in runs():
    name = Z.mof
    fit = [n for n in Z.namelist() if n.endswith("_surface_pair_fit_summary.csv")]
    rows = list(csv.DictReader(io.StringIO(Z.read(fit[0]).decode()))) if fit else []
    if not rows:
        rank_rows.append(f'<tr><td class="dt-label">{E(name)}</td><td class="dt-note" colspan="3">no slab energies '
                         f'(the run stopped before the slab stage)</td></tr>')
        continue
    pairs = ", ".join(f'{r["matrix_rank"]}/{r["matrix_columns"]}' for r in rows)
    status = Counter(r["fit_status"] for r in rows).most_common(1)[0][0].replace("_", " ")
    rank_rows.append(f'<tr data-rank="{E(name)}"><td class="dt-label">{E(name)}</td><td class="dt-value">{len(rows)}</td>'
                     f'<td class="dt-note">{pairs}</td><td class="dt-note">{E(status)}</td></tr>')

# ---------- 4. CHGNet cleavage proxy ----------------------------------------------------------
cl_rows = []
for name, v in CC.items():
    a, b = v.get("all_slabs", {}), v.get("intact_only", {})
    faces = sorted(set(a.get("faces_info", {})) | set(b.get("faces_info", {})))
    for f in faces:
        ga = a.get("faces_info", {}).get(f, {}).get("gamma_cleavage_J_m2")
        gb = b.get("faces_info", {}).get(f, {}).get("gamma_cleavage_J_m2")
        split = a.get("faces_info", {}).get(f, {}).get("split_equal")
        cl_rows.append(f'<tr data-gamma-cl="{E(name)}|{E(f)}" data-gamma="{ga}"><td class="dt-label">{E(name)}</td>'
                       f'<td class="dt-note">{fam(f)}{" *" if split else ""}</td>'
                       f'<td class="dt-value">{ga:.3f}</td><td class="dt-value">{"&ndash;" if gb is None else f"{gb:.3f}"}</td></tr>')
cl_shape_rows = []
for name, v in CC.items():
    a, b = v["all_slabs"], v.get("intact_only", v["all_slabs"])
    cl_shape_rows.append(f'<tr data-cl-shape="{E(name)}"><td class="dt-label">{E(name)}</td>'
                         f'<td class="dt-value">{a["n_slabs_used"]}</td><td class="dt-note">{E(a["shapes"]["1"]["name"])}</td>'
                         f'<td class="dt-value">{b["n_slabs_used"]}</td><td class="dt-note">{E(b["shapes"]["1"]["name"])}</td>'
                         f'<td class="dt-note">{E(a["shapes"]["0"]["name"])}</td></tr>')

# ---------- 5. chemistry checks on the slabs ----------------------------------------------------
frag_rows = []
for name, v in PIECES.items():
    cut = sum(1 for x in v if x["small_initial"]); rel = sum(1 for x in v if x["small_relaxed"])
    kinds = Counter(f for x in v for f in x["small_initial"]).most_common(4)
    after = Counter(f for x in v for f in x["small_relaxed"] if f not in {k for x2 in v for k in x2["small_initial"]}).most_common(2)
    th = [x["thickness_A"] for x in v]
    frag_rows.append(f'<tr data-frag="{E(name)}" data-n="{len(v)}" data-cut="{cut}"><td class="dt-label">{E(name)}</td>'
                     f'<td class="dt-value">{len(v)}</td><td class="dt-value">{cut}</td><td class="dt-value">{rel}</td>'
                     f'<td class="dt-note">{E(", ".join(f"{k} &times;{n}" for k, n in kinds))}</td>'
                     f'<td class="dt-note">{E(", ".join(k for k, _ in after)) or "none"}</td>'
                     f'<td class="dt-value">{min(th):.0f}&ndash;{max(th):.0f}</td></tr>')
frag_rows = [r.replace("&amp;times;", "&times;") for r in frag_rows]

sym_rows = []
for name, v in CC.items():
    cl = v.get("intact_only", v["all_slabs"])["faces_info"]
    for f, lst in v.get("symmetric_slab_gammas", {}).items():
        g = lst[0]["gamma_J_m2"]
        ref = cl.get(f, v["all_slabs"]["faces_info"].get(f, {})).get("gamma_cleavage_J_m2")
        sym_rows.append(f'<tr data-sym="{E(name)}|{E(f)}" data-gamma="{g}"><td class="dt-label">{E(name)}</td><td class="dt-note">{fam(f)}</td>'
                        f'<td class="dt-value">{len(lst)}</td><td class="dt-value">{g:.3f}</td>'
                        f'<td class="dt-value">{ref:.3f}</td><td class="dt-value">{g / ref:.1f}&times;</td>'
                        f'<td class="dt-note">{"intact" if lst[0]["intact"] else "has loose pieces"}</td></tr>')

opt_rows = []
for name, faces in OPTS.items():
    if name not in CC:          # hMOF-0: hypothetical, and its run produced no slab energies
        continue
    for miller, res in faces.items():
        def cell(k):
            x = res.get(k, {})
            return ("error" if "error" in x else f'{x["n"]} / {x["stoichiometric"]} / {x["stoich_and_symmetric"]}')
        opt_rows.append(f'<tr data-opt="{E(name)}|{E(miller)}"><td class="dt-label">{E(name)}</td><td class="dt-note">{E(miller)}</td>'
                        f'<td class="dt-value">{cell("as_cut")}</td><td class="dt-value">{cell("intact")}</td>'
                        f'<td class="dt-value">{cell("symmetrized")}</td></tr>')

bs_rows = []
for name, v in BS.items():
    cells = "".join(f'<td class="dt-note">{E(v["by_factor"][f]["shape"])}</td>' for f in ("1.0", "0.5", "0.25"))
    g = {f: v["by_factor"][f]["gamma_J_m2"] for f in ("1.0", "0.25")}
    k1 = min(g["1.0"], key=g["1.0"].get); k2 = min(g["0.25"], key=g["0.25"].get)
    bs_rows.append(f'<tr data-bs="{E(name)}"><td class="dt-label">{E(name)}</td>{cells}'
                   f'<td class="dt-note">{fam(k1)} &rarr; {fam(k2)}</td></tr>')

core_rows = []
for code, v in CORE.items():
    b, h, u = v["shapes"]["BFDH"], v["shapes"]["hybrid w=0.5"], v["shapes"]["UFF Wulff"]
    top = lambda s: ", ".join(f"{fam(k)} {x:.2f}" for k, x in sorted(s["faces"].items(), key=lambda t: -t[1])[:2])
    core_rows.append(f'<tr data-core="{E(code)}"><td class="dt-label">{E(code)}</td><td class="dt-note">{E(v["spacegroup"])}<br><small>{E(v["crystal_system"])}</small></td>'
                     f'<td class="dt-note">{E(", ".join(v["metals"]))}</td>'
                     f'<td class="dt-note">{top(b)}<br><small>aspect {b["aspect_ratio"]}</small></td>'
                     f'<td class="dt-note">{top(u)}<br><small>aspect {u["aspect_ratio"]}</small></td></tr>')

n_exp, n_pap, n_mof = len(EXP_ROWS), len(papers), len(by_mof)
mof5 = CC.get("MOF-5", {}).get("intact_only", {}).get("shapes", {}).get("1", {})

H = []
H.append('''      <h2 class="section-title" id="ex-intro" data-toc="What this page does"><span class="stitle-num">0</span>What This Page Does</h2>
      <dl class="bridge"><dt>You know</dt><dd>How a set of face energies or growth rates becomes a shape (<a href="learn_shape.html">Learn</a>, <a href="morph_math.html">Maths</a>), and the three energy models of <a href="graph_faces.html">Faces from the graph</a> and <a href="surface_energy.html">Surface energy</a>.</dd><dt>This page adds</dt><dd>What real crystals of these MOFs look like, with the synthesis conditions that produced them; the machine-learned (CHGNet) surface-energy runs; a check of every method against experiment; the chemistry problems found in the slab calculations; and the same pipeline run on CoRE MOF structures of every crystal system.</dd></dl>
      <p class="section-sub">A predicted shape means little until it is compared with crystals grown in a laboratory. This page collects those crystals, states the conditions they were grown under, scores each method against them, and records what limits the comparison.</p>
      <div class="callout warn" data-kind="Read this first">Every prediction on this site is for a bare crystal in vacuum: no solvent, no modulator, no temperature. Real crystals are grown in solvent, often with additives, and their shape can depend on those conditions more than on the framework. A match or mismatch below is therefore evidence about the method under that assumption, not a final verdict on it. The four MOFs on this page are too few to rank methods; the <a href="advisor.html">Shape advisor</a> extends the comparison to ten MOFs.</div>
''')
H.append(f'''      <h2 class="section-title" id="ex-data" data-toc="The experimental dataset"><span class="stitle-num">0</span>The Experimental Dataset</h2>
      <p class="sd">{n_exp} crystal-shape records from {n_pap} open-access papers covering {n_mof} MOFs were collected (files in <code>data/experimental_morphology/dataset/</code>). Each record states the MOF, the shape as the authors wrote it, the exposed faces where given, and every synthesis condition the paper reports: metal salt, linker ratio, solvent, additive and its role, temperature, time, heating and stirring, plus the evidence (SEM, TEM) and the exact figure or table it came from. Only open-access copies were used, and a record built from an abstract alone is marked as such.</p>
      {table(["MOF", "Records", "Papers", "Shapes reported (count)", "Main solvents", "Temperature", "With additive"], ds_rows, "ex-dataset")}
      <p class="sd">Two series in the data show why conditions must be recorded. ZIF-8 grown with sodium formate passes from cubes with truncated edges to rhombic dodecahedra over about four hours (Cravillon et al. 2012), so the time of sampling decides the shape. HKUST-1 changes from octahedron to cuboctahedron to cube as the amount of a monocarboxylic acid modulator rises (Umemura et al. 2011). A single &ldquo;experimental shape&rdquo; per MOF is therefore a simplification, and the benchmark below uses only additive-free crystals, because no model here contains an additive.</p>
''')
H.append(f'''      <h2 class="section-title" id="ex-compare" data-toc="Methods against experiment"><span class="stitle-num">0</span>Every Method Against Experiment</h2>
      <figure class="fig wide">
        <img src="figures/morph/methods_vs_experiment.png" alt="A grid of crystal shapes. Rows MOF-5, HKUST-1, UiO-66, ZIF-8. Columns BFDH, UFF Wulff with a flat bond cost, UFF Wulff with metal-ligand bonds at a quarter of the cost, CHGNet cleavage energy, and a text column saying what crystals show. MOF-5 is a cube only in the flat-bond UFF column; HKUST-1 is a truncated octahedron in every column; UiO-66 is an octahedron in both UFF columns and a truncated cube from CHGNet; ZIF-8 is a rhombic dodecahedron.">
        <figcaption>Each method's shape beside what the crystals show. Blue {{100}}, red {{111}} (pink {{111}}&minus;), green {{110}}, brown {{311}}. The CHGNet shapes are drawn in the notebook's primitive-cell orientation, so they appear rotated.</figcaption>
      </figure>
      <p class="sd"><b>name</b>: the predicted shape has the same name as the experimental one. <b>facet</b>: the predicted shape's largest face family is the family the crystals expose. The benchmark records and the reason each was chosen are listed in <code>data/experimental_morphology/compare/COMPARISON.md</code>.</p>
      {table(["MOF", "Method", "Predicted", "Largest face (area fraction)", "Experiment", "name", "facet"], cmp_rows, "ex-cmp")}
      {table(["Method", "name matches", "facet matches"], score_rows, "ex-score")}
      <ul>
        <li><b>ZIF-8</b> is the one clean validation: every method gives the rhombic dodecahedron that additive-free crystals show and that Cravillon et al. identify as the equilibrium shape. Since BFDH, which uses geometry alone, already gives it, this case does not distinguish the energy models.</li>
        <li><b>MOF-5</b> separates the methods. The crystals are cubes in 8 of 8 records from two laboratories. The bond-counting energies (graph rule, broken-bond Wulff, UFF Wulff) give a cube and BFDH does not. The UFF cube, however, depends on charging a Zn&ndash;O bond the same as a C&ndash;C bond (Section 5), and the CHGNet proxy gives a truncated octahedron. So the MOF-5 success rests on the bond-counting assumption, which is the next thing to test.</li>
        <li><b>HKUST-1</b>: every method makes {{111}} the largest face, as in the octahedral crystals, but every method also keeps {{100}} faces that the crystals do not show.</li>
        <li><b>UiO-66</b> is the weakest benchmark. Additive-free reports describe poorly faceted &ldquo;clusters of square morphology&rdquo;, which the records list as cubes; the octahedra usually quoted for UiO-66 are grown with a modulator (Butova et al. 2023: benzoic acid, DMF, 120 &deg;C, TEM; Morelli Venturi et al. 2020: acetic acid in green solvents, 120 &deg;C, SEM). No model here gives a cube for UiO-66. The ten-MOF benchmark on the <a href="advisor.html">Shape advisor</a> counts this as a miss rather than leaving it out, which is the cautious choice.</li>
        <li><b>The hybrid</b> (BFDH and UFF Wulff blended with weight <i>w</i>) has one free parameter. With four MOFs, choosing the <i>w</i> that scores best would fit the test set, so it is shown at <i>w</i> = 0.5 only and is not ranked.</li>
      </ul>
''')
H.append(f'''      <h2 class="section-title" id="ex-chgnet" data-toc="CHGNet surface energies"><span class="stitle-num">0</span>Machine-Learned Surface Energies (CHGNet)</h2>
      <h3 class="sub-head">What the notebook does</h3>
      <p class="sd">The team's MorphoGraph-MOF notebook uses CHGNet, a machine-learned interatomic potential trained on DFT data, to relax the bulk framework and then a set of slabs: layers about 15 &Aring; thick cut parallel to each low-index face, with 20 &Aring; of vacuum. pymatgen generates every distinct termination of each face. It was run on Colab (T4 GPU) for MOF-5, HKUST-1 and UiO-66 with Miller indices up to 1; ZIF-8 was left out because its CIF has no symmetry when the hydrogens are kept.</p>
      <h3 class="sub-head">Why it produced no shape</h3>
      <p class="sd">A slab has two faces, a top one and a bottom one, and its energy gives only their sum:</p>
      <div class="eq"><span class="ex"><i>p</i> = (<i>E</i><sub>slab</sub> &minus; <i>N</i> <i>E</i><sub>bulk</sub>) / <i>A</i> = &gamma;<sub>top</sub> + &gamma;<sub>bottom</sub></span><span class="tag">(1)</span></div>
      <div class="where"><p class="lead">where</p><dl><dt><i>E</i><sub>slab</sub></dt><dd>energy of the relaxed slab of <i>N</i> atoms</dd><dt><i>E</i><sub>bulk</sub></dt><dd>energy per atom of the relaxed bulk</dd><dt><i>A</i></dt><dd>area of one face of the slab</dd><dt>&gamma;<sub>top</sub>, &gamma;<sub>bottom</sub></dt><dd>surface energies of the two terminations the slab exposes.</dd></dl></div>
      <p class="sd">The notebook collects one equation (1) per slab and solves for every termination's own &gamma;. In these MOFs every slab had a different termination on each side, and each slab appeared twice (once flipped), so the system has about half as many independent equations as unknowns. The notebook correctly refused to guess, and made no Wulff shape.</p>
      {table(["Run", "Face classes", "Rank / unknowns, per face class", "Fit status"], rank_rows, "ex-rank")}
      <h3 class="sub-head">A usable number: the cleavage energy</h3>
      <p class="sd">Cutting a crystal makes two faces at once, so (1) is exactly the energy of a cut. Taking the cheapest cut for each plane and giving each face half of it defines the cleavage energy, a standard quantity in surface science:</p>
      <div class="eq"><span class="ex">&gamma;<sub>cl</sub>(<i>hkl</i>) = min<sub>terminations</sub> <i>p</i> / 2</span><span class="tag">(2)</span></div>
      <p class="sd">Because <i>p</i>/2 = (&gamma;<sub>top</sub> + &gamma;<sub>bottom</sub>)/2 &ge; min(&gamma;<sub>top</sub>, &gamma;<sub>bottom</sub>), &gamma;<sub>cl</sub> is an <b>upper bound</b> on the lowest termination energy of that plane, never an underestimate. When the crystal has a centre of inversion (Fm-3m: MOF-5, HKUST-1) the two faces of a cut belong to one family, and (2) is the usual cleavage surface energy. When it does not (F-43m UiO-66), a cut gives &gamma;(+) + &gamma;(&minus;) for two different families, which cannot be separated; both get <i>p</i>/2, marked * below. This post-processing is in <code>code/morphology/mofmorph/chgnet_post.py</code>.</p>
      {table(["MOF", "Face", "&gamma;<sub>cl</sub> all slabs (J/m&sup2;)", "intact slabs only"], cl_rows, "ex-cl")}
      {table(["MOF", "Slabs used", "Wulff shape", "Intact slabs", "Wulff shape (intact)", "BFDH on the same faces"], cl_shape_rows, "ex-cl-shape")}
      <p class="sd">MOF-5 comes out as a {E(mof5.get("name", "?"))} with {{111}} the largest face, against cubic crystals. HKUST-1 is a truncated octahedron with {{111}} largest, which fits the octahedral crystals in its dominant face. UiO-66 is a truncated cube. Removing the slabs with broken linkers (next section) changes only the energies of the minor faces {{110}} and {{311}} and none of the three shapes.</p>
''')
H.append(f'''      <h2 class="section-title" id="ex-chem" data-toc="Chemistry checks"><span class="stitle-num">0</span>Chemistry Checks on the Slabs</h2>
      <h3 class="sub-head">Most slabs cut through linkers</h3>
      <p class="sd">A real MOF surface ends at a metal&ndash;ligand bond or at a capped cluster; it does not end halfway through a benzene ring. pymatgen's slab cutter knows nothing about molecules, however, and places the cut by atom position alone. Every relaxed slab was split into connected pieces (bonds from covalent radii &times; 1.15, long enough to keep Zn&ndash;O, Cu&ndash;O and Zr&ndash;O clusters whole) and each piece smaller than 5% of the slab was named by its formula (<code>slab_check.py</code>).</p>
      {table(["MOF", "Relaxed slabs", "With loose pieces as cut", "After relaxation", "Pieces as cut (count)", "New pieces after relaxation", "Bulk-equivalent thickness (&Aring;)"], frag_rows, "ex-frag")}
      <p class="sd">The loose pieces are hydrogen atoms, oxygen atoms and CH or C<sub>2</sub>H<sub>2</sub> fragments of linkers: the cutter sliced through C&ndash;H and C&ndash;C bonds in most slabs. During relaxation CHGNet then released whole CO<sub>2</sub> molecules from some broken carboxylates. Neither is a surface a crystal would have. An earlier note guessed that the bond cut-off was splitting metal clusters; the formulas show that it almost never does, the exception being two CuO<sub>4</sub> pieces in HKUST-1 (a copper atom cut away with its four carboxylate oxygens). The lowest-energy slabs of MOF-5 and UiO-66 are intact, and HKUST-1's {{111}} value moves from 0.151 to 0.152 J/m&sup2; when only intact slabs are used, so the results above survive this check.</p>
      <h3 class="sub-head">The slabs are thin</h3>
      <p class="sd">The bulk-equivalent thickness (the slab's atoms packed at bulk density) is 15&ndash;30 &Aring;, one or two layers of building blocks for cells 18&ndash;26 &Aring; across, and it differs between faces because pymatgen rounds each slab up to whole layers. Surface energies are trusted only once they stop changing with thickness; that test has not been run, so the CHGNet numbers are not converged.</p>
''')
if opt_rows:
    H.append(f'''      <h3 class="sub-head">Can better slabs be built?</h3>
      <p class="sd">A dry run of pymatgen's slab generator, without CHGNet (<code>slab_options_check.py</code>), counted for every face class how many slabs each option gives, in the form <i>all / stoichiometric / stoichiometric and symmetric</i>. Only a slab that is both stoichiometric and symmetric gives a termination's own &gamma; directly. &ldquo;Intact&rdquo; keeps only terminations that break no C&ndash;C, C&ndash;H, C&ndash;O or C&ndash;N bond; &ldquo;symmetrized&rdquo; is pymatgen's option that removes atoms until both faces match.</p>
      {table(["MOF", "Face (primitive)", "As cut", "Intact linkers", "Symmetrized"], opt_rows, "ex-opt")}
      <p class="sd">Two things follow. pymatgen's symmetrize option returns exactly the slabs of the plain cut for these frameworks, so it adds nothing here. Keeping linkers whole leaves a few terminations on the main faces and none on the higher-index ones, and none of those few is symmetric.</p>
''')
H.append(f'''      <h3 class="sub-head">The symmetric slabs that do exist</h3>
      <p class="sd">A few slabs in the runs were symmetric as cut. Each gives its termination's own energy exactly, &gamma; = <i>p</i>/2, with no equation to solve. The notebook did not use them, because it merges the two faces only when the slab is still symmetric after relaxation, and the unconstrained relaxation broke the symmetry of every one. They are recovered here (<code>symmetric_slab_gammas</code> in <code>chgnet_post.py</code>):</p>
      {table(["MOF", "Face", "Symmetric slabs", "Exact &gamma; of that termination (J/m&sup2;)", "Cleavage bound &gamma;<sub>cl</sub>", "Ratio", "Slab"], sym_rows, "ex-sym")}
      <p class="sd">Every symmetric termination costs 1.4 to 9 times the cleavage bound of its face. The terminations a crystal would actually show are the cheap ones, and in these frameworks the cheap cuts are asymmetric: a plane that breaks few metal&ndash;ligand bonds leaves different groups on its two sides. Symmetric slabs therefore give exact numbers for the wrong terminations and cannot by themselves recover the low-energy faces that decide the shape. For the Wulff shape the cleavage bound remains the more useful quantity. This was found after the symmetric-slab version of the notebook was written, and it lowers what that notebook can be expected to deliver.</p>
''')
H.append(f'''      <h2 class="section-title" id="ex-bond" data-toc="Bond-cost sensitivity"><span class="stitle-num">0</span>Is the Flat Bond Cost Safe?</h2>
      <p class="sd">The Phase 4 force field charges every cut bond 70 kcal/mol. The bonds a MOF surface actually breaks are mostly metal&ndash;ligand coordination bonds, which are weaker than the C&ndash;C and C&ndash;H bonds inside a linker, so a flat cost may favour the wrong planes. <code>run_bond_sensitivity.py</code> keeps organic bonds at 70 kcal/mol and multiplies every bond to a metal by <i>f</i>.</p>
      {table(["MOF", "<i>f</i> = 1 (Phase 4)", "<i>f</i> = 0.5", "<i>f</i> = 0.25", "Lowest-&gamma; face, <i>f</i> = 1 &rarr; 0.25"], bs_rows, "ex-bs")}
      <p class="sd">UiO-66 (octahedron) and HKUST-1 (truncated octahedron) do not change. ZIF-8 keeps {{110}} as its largest face and gains small {{100}} faces. MOF-5 moves from a cube to a truncated cube and, at <i>f</i> = 0.25, to a truncated octahedron close to a cuboctahedron, with {{100}} still the largest face. The MOF-5 cube is therefore a consequence of the flat bond cost, and a bond-type-specific cost (or a DFT check of a few MOF-5 faces) is needed before it is quoted as a prediction.</p>
''')
H.append(f'''      <h2 class="section-title" id="ex-core" data-toc="Any framework: CoRE MOF"><span class="stitle-num">0</span>Any Framework: CoRE MOF Structures</h2>
      <p class="sd">Eight structures from CoRE MOF 2019, the experimental structure set this project screens for CO<sub>2</sub>, were run through the same pipeline: symmetry, the 12 widest-spaced face families, Phase 4 UFF energies with every atom including hydrogen, then BFDH, hybrid and Wulff shapes (<code>run_core.py</code>). They cover six crystal systems and six metals. No experimental shapes are known to us for them, so this shows only that the method runs on any framework.</p>
      <figure class="fig wide"><img src="figures/morph/core_shapes.png" alt="Eight rows of three shapes each, for eight CoRE MOF structures from triclinic to cubic. Low-symmetry structures give plates, prisms and rods; the cubic one gives a truncated octahedron.">
      <figcaption>BFDH, hybrid (<i>w</i> = 0.5) and UFF Wulff shapes for eight CoRE MOF structures. In low-symmetry crystals the colours only separate face families within one row; the labels are not comparable between rows.</figcaption></figure>
      {table(["CoRE code", "Space group", "Metal", "BFDH: largest faces", "UFF Wulff: largest faces"], core_rows, "ex-core-table")}
      <p class="sd">Aspect ratios reach about 2 (rods and plates) for the monoclinic, tetragonal, trigonal and hexagonal frameworks, and the force-field energies change which faces dominate in most of them (for example the trigonal ACAJIY goes from an almost isometric BFDH rhombohedron to a plate). Whether either is right cannot be said without crystals to compare against.</p>
''')
H.append('''      <h2 class="section-title" id="ex-next" data-toc="Limits and next steps"><span class="stitle-num">0</span>Limits and Next Steps</h2>
      <ul>
        <li><b>A DFT check</b> of two or three faces of MOF-5 and UiO-66, where CHGNet and UFF disagree, is the decisive test. The relaxed slab files are in the CHGNet result zips; the intact lowest-energy slabs listed above are the ones to use.</li>
        <li><b>A revised CHGNet notebook</b> (<code>notebooks/morphograph_mof/MorphoGraph_MOF_colab_symmetric_slabs.ipynb</code>) keeps linkers whole where possible, treats a slab symmetric as cut as one termination, keeps any termination energy the equations do fix, and fills the rest with the cleavage bound, labelled as an upper bound. It is prepared for a GPU session. The dry run and the symmetric-slab table above say what to expect: cleaner slabs, but a shape still set mostly by the cleavage bound.</li>
        <li><b>A better route to individual &gamma;</b> is to make the cheap asymmetric slab symmetric by hand: cut at the cheap plane on both sides and cap the exposed metal sites with a solvent or formate molecule, as real surfaces are capped. This needs chemical potentials for the capping group and is a separate piece of work.</li>
        <li><b>Thickness convergence.</b> One face of one MOF at 15, 30 and 45 &Aring; would show whether the CHGNet energies are converged.</li>
        <li><b>Solvent and modulator.</b> No model here contains them. The additive records in the dataset are the test set for a model that does.</li>
        <li><b>ZIF-8 in CHGNet</b> needs a CIF whose symmetry survives with hydrogens, or a notebook option to find symmetry without them.</li>
        <li><b>UiO-66 benchmark</b> needs a primary, open-access source showing well-faceted additive-free crystals; the modulated octahedra are now confirmed from two primary papers.</li>
        <li><b>Eleven records</b> whose source could not be identified (no DOI, no copy, not found by search) are held in <code>experimental_morphology_unverified.csv</code> and kept out of every table above until their source is confirmed.</li>
      </ul>
''')
open(os.path.join(HERE, "fragments", "experiment.before.html"), "w", encoding="utf-8").write("\n".join(H))
print("wrote fragments/experiment.before.html:", sum(len(h) for h in H) // 1024, "KB;",
      len(cmp_rows), "comparison rows,", len(cl_rows), "cleavage rows,", len(opt_rows), "slab-option rows")
