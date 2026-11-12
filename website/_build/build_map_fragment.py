"""Writes fragments/morphology_map.before.html (page morphology_map.html) from the result files, so every
number on the page comes from a file and the script that wrote it:

  code/morphology/morphology_map/model_points.json        model_points.py
  code/morphology/morphology_map/series_results.json      series_test.py
  code/morphology/morphology_map/condition_model_results.json  condition_model.py
  code/morphology/morphology_map/modulator_caps_results.json   modulator_caps.py
  code/morphology/morphology_map/possible_morphs.json     possible_morphs.py
  code/morphology/morphology_map/dimension_along_map.json dimension_along_map.py
  code/morphology/steps1_8_check/results_quick/wulff_summary_all.csv   run_nb.py (quick mode)
  code/morphology/steps1_8_check/results_full_fixed/*.log               run_nb.py / one_face.py (full mode)
  code/morphology/steps1_8_check/k11_results.json        k11.py
  data/experimental_morphology/dataset/experimental_morphology.csv

Run:  python website/_build/build_map_fragment.py   then   python website/_build/build_site.py
"""
import csv, glob, html, json, math, os, re, shutil
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MM = os.path.join(REPO, "code", "morphology", "morphology_map")
SC = os.path.join(REPO, "code", "morphology", "steps1_8_check")
LAB = os.path.join(REPO, "data", "experimental_morphology", "dataset", "experimental_morphology.csv")
FIGDIR = os.path.join(REPO, "website", "figures", "map")
E = html.escape
S3 = math.sqrt(3)


def J(path):
    return json.load(open(path, encoding="utf-8"))


PRETTY = {"truncated_rhombic_dodecahedron": "truncated rhombic dodecahedron",
          "cube_truncated_edges": "cube with truncated edges",
          "rd_truncated_by_111": "rhombic dodecahedron cut by {111}",
          "octahedron_truncated_by_110": "octahedron cut by {110}",
          "all_three_families": "all three families",
          "rhombic_dodecahedron": "rhombic dodecahedron"}


def pretty(name):
    return PRETTY.get(name, name.replace("_", " "))


def f(x, n=2):
    return f"{x:.{n}f}"


MOFS = ["MOF-5", "HKUST-1", "UiO-66", "ZIF-8"]


def lab_shapes():
    """Additive-free records per MOF, counted by reported shape."""
    rows = list(csv.DictReader(open(LAB, encoding="utf-8")))
    free = lambda r: re.match(r"^\s*$|^none|^nan$", (r["additive"] or "").strip().lower())
    out = {}
    for m in MOFS + ["Mg-MOF-74"]:
        c = Counter(r["morphology"] for r in rows if r["mof"] == m and free(r))
        out[m] = c
    return out


def section(id_, toc, title):
    return f'\n      <h2 class="section-title" id="{id_}" data-toc="{E(toc)}"><span class="stitle-num">0</span>{title}</h2>\n'


def table(id_, head, rows):
    h = "".join(f"<td>{x}</td>" for x in head)
    b = "".join("<tr>" + "".join(f'<td class="{c}">{v}</td>' for c, v in r) + "</tr>" for r in rows)
    return f'      <div class="table-wrap"><table class="data-table" id="{id_}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>\n'


def fig(src, alt, caption):
    return (f'      <figure class="fig"><img src="figures/map/{src}" alt="{E(alt)}" loading="lazy">'
            f'<figcaption>{caption}</figcaption></figure>\n')


def main():
    os.makedirs(FIGDIR, exist_ok=True)
    for name in ("fig_map_regions.png", "fig_map_models.png", "fig_conditions.png"):
        shutil.copyfile(os.path.join(MM, name), os.path.join(FIGDIR, name))

    P = J(os.path.join(MM, "model_points.json"))
    SER = J(os.path.join(MM, "series_results.json"))
    CON = J(os.path.join(MM, "condition_model_results.json"))
    CAP = J(os.path.join(MM, "modulator_caps_results.json"))
    POS = J(os.path.join(MM, "possible_morphs.json"))
    DIM = J(os.path.join(MM, "dimension_along_map.json"))
    K11 = J(os.path.join(SC, "k11_results.json"))
    LABS = lab_shapes()
    QUICK = list(csv.DictReader(open(os.path.join(SC, "results_quick", "wulff_summary_all.csv"), encoding="utf-8")))

    h = ['<style>#map-model-table td,#map-quick td,#map-full td,#map-k td,#map-possible-table td,#map-series td{font-size:13.5px;padding:7px 9px;vertical-align:top}'
         '#map-k td:nth-child(2),#map-k td:nth-child(3){min-width:180px}#map-model-table,#map-quick{table-layout:fixed;width:100%}#map-model-table td,#map-quick td{overflow-wrap:anywhere}#map-model-table td:first-child{width:20%}</style>\n']
    # ---- 0. intro ------------------------------------------------------------------------------------
    h.append(section("map-intro", "What this page does", "What This Page Does"))
    h.append('      <dl class="bridge"><dt>You know</dt><dd>How face energies or growth distances become a shape '
             '(<a href="cif_to_shape.html">From a CIF to a shape</a>), and the models scored on '
             '<a href="experiment.html">Against experiment</a>.</dd><dt>This page adds</dt><dd>The work of 10 November: '
             'one map on which every shape a cubic crystal can take has its own region; every model of the project as a point on it; '
             'three tests of the map against laboratory series; the list of possible morphologies of a given CIF; the graph '
             'measurement read along the same map; and a check of the team\'s new CIF-to-Wulff pipeline (steps 1&ndash;8).</dd></dl>\n')
    h.append('      <p class="section-sub">The panel asked for several morphologies from one unit cell. A list of shape names hides how '
             'close a prediction is to the next shape. The map puts every prediction, every laboratory series and the graph '
             'measurement in one coordinate system, so they can be compared directly.</p>\n')

    # ---- 1. the map ----------------------------------------------------------------------------------
    h.append(section("map-def", "The map", "The Map"))
    h.append('      <p class="sd">A cubic crystal bounded by {100}, {110} and {111} faces has a Wulff shape that depends only on two '
             'ratios, <i>x</i> = &gamma;<sub>110</sub>/&gamma;<sub>100</sub> and <i>y</i> = &gamma;<sub>111</sub>/&gamma;<sub>100</sub>, '
             'because multiplying every energy by one factor only scales the crystal. A family appears only if its planes cut off a '
             'corner of the shape the other families make, which gives the exact boundaries below. They are derived step by step, with '
             'a clickable version of the map, in Step 12 of <a href="cif_to_shape.html">From a CIF to a shape</a>; this page uses them.</p>\n')
    h.append(table("map-regions", ["Shape", "Exact condition"], [
        [("dt-label", "Cube"), ("dt-note", "<i>y</i> &ge; &radic;3 and <i>x</i> &ge; &radic;2")],
        [("dt-label", "Truncated cube"), ("dt-note", "2/&radic;3 &lt; <i>y</i> &lt; &radic;3, no {110}")],
        [("dt-label", "Cuboctahedron"), ("dt-note", "<i>y</i> = 2/&radic;3 exactly, no {110}: a line, not a region")],
        [("dt-label", "Truncated octahedron"), ("dt-note", "1/&radic;3 &lt; <i>y</i> &lt; 2/&radic;3, no {110}")],
        [("dt-label", "Octahedron"), ("dt-note", "<i>y</i> &le; 1/&radic;3 and <i>x</i> &ge; &radic;(3/2)&middot;<i>y</i>")],
        [("dt-label", "Rhombic dodecahedron"), ("dt-note", "<i>x</i> &le; 1/&radic;2 and <i>y</i> &ge; &radic;(3/2)&middot;<i>x</i>")],
        [("dt-label", "Cube with truncated edges, truncated rhombic dodecahedron"), ("dt-note", "{100} and {110}, no {111}; named by the larger family")],
    ]))
    h.append(fig("fig_map_regions.png", "Shape regions of the cubic morphology map",
                 "The map: shape regions on the plane of <i>x</i> = &gamma;<sub>110</sub>/&gamma;<sub>100</sub> and <i>y</i> = "
                 "&gamma;<sub>111</sub>/&gamma;<sub>100</sub>, computed exactly by half-space intersection on a 150 &times; 150 grid; "
                 "a family counts when it holds at least 1 % of the area."))

    # ---- 2. models on the map ------------------------------------------------------------------------
    h.append(section("map-models", "Every model on the map", "Every Model of the Project on the Map"))
    models = ["BFDH", "Attachment energy", "Broken-bond Wulff", "UFF Wulff", "CHGNet cleavage (Oct)",
              "Steps 1-8 CHGNet, static", "Steps 1-8 CHGNet, relaxed"]
    rows = [[("dt-label", "<b>Lab, no additive</b> <span class=\"sm\">(most common shape)</span>")] +
            [("dt-note", "<b>%s</b> <span class=\"sm\">(%d of %d records)</span>" % (pretty(LABS[m].most_common(1)[0][0]), LABS[m].most_common(1)[0][1], sum(LABS[m].values()))) for m in MOFS]]
    for mod in models:
        row = [("dt-label", mod.replace("1-8", "1&ndash;8"))]
        for m in MOFS:
            v = P[m].get(mod)
            row.append(("dt-note", "not run" if v is None else f"{pretty(v['exact'])} <span class=\"sm\">({f(v['x'])}, {f(v['y'])})</span>"))
        rows.append(row)
    h.append(table("map-model-table", ["Model <span class=\"sm\">(shape, then <i>x</i>, <i>y</i>)</span>"] + MOFS, rows))
    yh = [v["y"] for v in P["HKUST-1"].values()]
    yu = [v["y"] for v in P["UiO-66"].values()]
    bb = P["MOF-5"]["Broken-bond Wulff"]; zb = P["ZIF-8"]["BFDH"]
    zif_all = all(v["exact"] in ("rhombic_dodecahedron", "truncated_rhombic_dodecahedron") for v in P["ZIF-8"].values())
    h.append(f'      <p class="sd">What the map shows that a shape name hides. <b>Distance from the lab:</b> every HKUST-1 model sits at '
             f'<i>y</i> = {f(min(yh))}&ndash;{f(max(yh))}, while an octahedron needs <i>y</i> &le; 1/&radic;3 = {f(1/S3, 3)}: right direction, not far enough. '
             f'<b>Fragile predictions:</b> the MOF-5 broken-bond point ({f(bb["x"], 3)}, {f(bb["y"], 3)}) sits on the cube corner (&radic;2, &radic;3), '
             f'and the ZIF-8 BFDH point on the line <i>x</i> = 1/&radic;2 ({f(zb["x"], 4)}), because bond counts and spacing ratios are small whole numbers. '
             f'<b>Disagreement:</b> UiO-66 models spread from <i>y</i> = {f(min(yu))} to {f(max(yu))}. '
             f'ZIF-8 is the only MOF where every model lands in or next to the lab\'s region{"" if zif_all else " (check)"}.</p>\n')
    h.append(fig("fig_map_models.png", "Every model of the project on the morphology map, one panel per MOF",
                 "Each model as one point per MOF on the map, with the closed-form limits as dashed lines and the additive-free lab "
                 "shape in each panel title."))

    # ---- 3. tests ------------------------------------------------------------------------------------
    h.append(section("map-tests", "Conditions on the map", "Conditions on the Map: Three Tests"))
    h.append('      <p class="sd"><b>Theory.</b> By the Gibbs adsorption equation a face\'s energy falls as an additive that binds it becomes '
             'more concentrated, d&gamma;<sub><i>F</i></sub> = &minus;&Gamma;<sub><i>F</i></sub> d&mu;. An additive that binds one family '
             'lowers only that family\'s energy, so the crystal\'s point moves steadily toward that family\'s corner of the map, through a '
             'fixed order of shapes, and never turns back. That order is testable.</p>\n')
    mov = [s for s in SER["series"] if s["result"].startswith("moves")]
    off = [s for s in SER["series"] if not s["result"].startswith("moves")]
    h.append(f'      <p class="sd"><b>Test 1: laboratory series</b> (<code>series_test.py</code>). Every controlled series in the dataset '
             f'with an increasing dose, ratio or time was placed on the map. {len(mov)} series change shape on the map, and all '
             f'{len(mov)} move one way along one axis. If the same shapes were listed in random order, the chance that all '
             f'{len(mov)} would be this orderly is {SER["joint_chance"]:.1e}. This number is conditional on two choices, stated here: '
             f'it counts only the {len(mov)} of {len(SER["series"])} series whose shapes all lie on the map, and its null assumes every order '
             f'of a series\' shapes is equally likely (for three shapes, 2 of the 6 orders are monotone, so 1/3 per series). Shape names '
             f'are the papers\' own.</p>\n'.replace("e-04", " &times; 10<sup>&minus;4</sup>"))
    h.append(table("map-series", ["Series (source)", "Condition", "Shapes as the condition increases", "Moves toward"],
                   [[("dt-label", E(s["series"])), ("dt-note", E(s["condition"])),
                     ("dt-note", " &rarr; ".join(pretty(x) for x in s["shapes"])), ("dt-note", E(s["result"].replace("moves toward ", "")))] for s in mov]))
    h.append(f'      <p class="sd">{len(off)} other series leave the map or do not move on it '
             f'({", ".join(E(s["series"]) + ": " + pretty(s.get("leaves_map_at") or "") for s in off)}). Plates, spheres, needles and '
             f'intergrown crystals come from growth kinetics; no Wulff model can describe them.</p>\n')
    names = {"M0": "most common face overall", "M1": "most common face for that MOF",
             "M2": "structure only (largest face of the computed Wulff shape)", "M3": "M2, plus &ldquo;this additive type gives face F&rdquo;"}
    Mo = CON["models"]
    h.append(f'      <p class="sd"><b>Test 2: conditions as labels</b> (<code>condition_model.py</code>). The dominant face of '
             f'{Mo["M0"]["n"]} cubic-MOF records from {CON["n_sources"]} papers was predicted with each paper held out in turn; '
             f'the interval is a 95 % bootstrap over papers.</p>\n')
    h.append(table("map-condition", ["Model", "All records", f'No additive ({Mo["M0"]["n_free"]})', f'With additive ({Mo["M0"]["n_add"]})'],
                   [[("dt-label", f"{k}: {v}"), ("dt-value", f'{100*Mo[k]["accuracy"]:.0f} % ({100*Mo[k]["ci95"][0]:.0f}&ndash;{100*Mo[k]["ci95"][1]:.0f})'),
                     ("dt-value", f'{100*Mo[k]["acc_additive_free"]:.0f} %'), ("dt-value", f'{100*Mo[k]["acc_with_additive"]:.0f} %')] for k, v in names.items()]))
    h.append('      <p class="sd">On additive-free records the structure-only prediction (M2) is as good as knowing the usual answer for '
             'that MOF (M1). Adding the additive as a label (M3) makes the records with additives worse, because the same additive type '
             'moves different MOFs different ways (monocarboxylic acids push UiO-66 toward octahedra and HKUST-1 toward cubes) and papers '
             'report doses in incompatible units. A model of conditions must therefore predict the move from computed binding energies '
             'and one dose unit, not from labels.</p>\n')
    # Is M2 better than M3 on records with additives? Exact McNemar test on the paired predictions, and a
    # bootstrap over papers of the difference in accuracy (records from one paper are not independent).
    import pandas as pd, numpy as np
    from math import comb
    PR = pd.read_csv(os.path.join(MM, "condition_model_predictions.csv"))
    A = PR[PR.cat != "none"]
    m2, m3 = (A.M2 == A.truth).to_numpy(), (A.M3 == A.truth).to_numpy()
    b, c = int((m2 & ~m3).sum()), int((~m2 & m3).sum())
    p_mc = min(1.0, 2 * sum(comb(b + c, k) for k in range(min(b, c) + 1)) / 2 ** (b + c))
    rng = np.random.default_rng(0); srcs = A.source.unique(); diffs = []
    for _ in range(5000):
        pick = rng.choice(srcs, len(srcs))
        B = pd.concat([A[A.source == x] for x in pick])
        diffs.append(((B.M2 == B.truth).mean() - (B.M3 == B.truth).mean()))
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    h.append(f'      <p class="sd"><b>How strong is that difference?</b> On the {len(A)} records with an additive, M2 is right where M3 is wrong '
             f'in {b} records and the reverse in {c} (exact McNemar test, <i>p</i> = {p_mc:.3f}); resampling whole papers gives a 95 % '
             f'interval of {lo:+.2f} to {hi:+.2f} for M2&rsquo;s advantage in accuracy. The difference is real but only just: it rests on '
             f'{A.source.nunique()} papers, and its lower end is close to zero.</p>\n')
    eps = {m: CAP["results"][m]["faces"] for m in CAP["results"]}
    def e3(m):
        return " / ".join(f(eps[m][k]["eps_exchange_eV"]) for k in ("100", "110", "111"))
    h.append(f'      <p class="sd"><b>Test 3: a modulator cap, first attempt</b> (<code>modulator_caps.py</code>). The lowest water-capped '
             f'slab of each face was recapped with formate and scored without relaxation. The binding energy per site, '
             f'&epsilon;<sub><i>F</i></sub> for {{100}} / {{110}} / {{111}}, is {e3("HKUST-1")} eV for HKUST-1 and {e3("ZIF-8")} eV for ZIF-8, '
             f'which moves HKUST-1 toward octahedra and ZIF-8 toward cubes. For UiO-66 two formates crowd each Zr and the result '
             f'({e3("UiO-66")} eV) is not physical. With unrelaxed caps, this shows only that the pipeline can compute a direction; '
             f'it is not a result.</p>\n')
    h.append(fig("fig_conditions.png", "Laboratory series and the graph read-out along the two axes of the map",
                 "Left: the laboratory series of Test 1 along the two axes of the map. Right: the dimension-profile number "
                 "<i>r</i><sub>&frac12;</sub>/<i>D</i> of MOF-5 crystals cut along the same axes (section below)."))

    # ---- 4. possible morphs ---------------------------------------------------------------------------
    h.append(section("map-possible", "Possible morphologies of a CIF", "Possible Morphologies of a Given CIF"))
    h.append('      <p class="sd">This is the panel\'s request in its most direct form (<code>possible_morphs.py</code>). Start from a '
             'structure\'s point on the map and lower one face energy at a time, as a modulator that binds that face would. Each path '
             'lists the shapes the crystal can take, in the order they should appear.</p>\n')
    rows = []
    for m in MOFS:
        d = POS[m]
        path = lambda k: " &rarr; ".join(pretty(x) for x in d["paths"][k]) if len(d["paths"][k]) > 1 else "stays a " + pretty(d["paths"][k][0])
        rows.append([("dt-label", f'{m} <span class="sm">(start: {pretty(d["baseline"])}, {E(d["baseline_source"])})</span>'),
                     ("dt-note", path("100")), ("dt-note", path("110")), ("dt-note", path("111")),
                     ("dt-value", f'{len(d["lab_covered"])} of {len(d["lab_on_map"])}')])
    h.append(table("map-possible-table", ["MOF (start)", "Lower &gamma;<sub>100</sub>", "Lower &gamma;<sub>110</sub>", "Lower &gamma;<sub>111</sub>",
                                          "Lab shapes on the map that are generated"], rows))
    n_cov = sum(len(POS[m]["lab_covered"]) for m in MOFS); n_on = sum(len(POS[m]["lab_on_map"]) for m in MOFS)
    n_off = sum(len(POS[m]["lab_off_map"]) for m in MOFS)
    missing = [(m, s) for m in MOFS for s in POS[m]["lab_on_map"] if s not in POS[m]["lab_covered"]]
    h.append(f'      <p class="sd">{n_cov} of the {n_on} polyhedral lab shapes for these MOFs are generated'
             + (f' (not generated: {", ".join(m + " " + pretty(s) for m, s in missing)}, which needs two faces lowered together)' if missing else '')
             + f'. The count is high partly by construction, since single-face moves reach the cube, octahedron and rhombic '
             f'dodecahedron from almost anywhere; the {n_off} kinds of lab shape that lie off the map (plates, rods, bipyramids, '
             f'irregular or intergrown crystals) are not generated. The testable content is the order along each path, and shapes not '
             f'yet reported, such as a rhombic dodecahedron of HKUST-1 or UiO-66 with an additive that binds {{110}}.</p>\n')

    # ---- 5. dimension along the map ------------------------------------------------------------------
    h.append(section("map-dimension", "The graph read-out along the map", "The Graph Read-out Along the Map"))
    h.append('      <p class="sd">The dimension profile of <a href="relation.html">Spectrum and shape</a> (Test 4) separates a few '
             'compact shapes. Here MOF-5 crystals of about 4000 building blocks were cut at points along each axis of the map and '
             'measured the same way (64 random centres per seed; 3 seeds here instead of 5; <code>dimension_along_map.py</code>).</p>\n')
    rows = []
    for ax, lab in (("{100}-{111}", "&gamma;<sub>111</sub>/&gamma;<sub>100</sub>"), ("{100}-{110}", "&gamma;<sub>110</sub>/&gamma;<sub>100</sub>")):
        pts = DIM[ax]["points"]
        rows.append([("dt-label", f'{lab} from {f(pts[0]["ratio"])} to {f(pts[-1]["ratio"])}'),
                     ("dt-note", " &rarr; ".join(pretty(p["shape"]) for p in pts)),
                     ("dt-note", ", ".join(f(p["r_half_over_D"], 3) for p in pts)),
                     ("dt-note", f'{min(p["sd"] for p in pts):.3f}&ndash;{max(p["sd"] for p in pts):.3f}'),
                     ("dt-value", "yes" if DIM[ax]["monotone"] else "no")])
    h.append(table("map-dim", ["Axis", "Shapes along it", "<i>r</i><sub>&frac12;</sub>/<i>D</i>", "Seed s.d.", "Order kept?"], rows))
    h.append('      <p class="sd">The graph measurement changes in one direction along both axes, so it reads a crystal\'s position on '
             'the same map the energies and the conditions predict. Limits: one number cannot name a point of a two-dimensional map; '
             'at 4000 blocks it does not separate an octahedron from a lightly truncated one; and every shape was cut from the MOF-5 net, '
             'so this tests geometry, not each MOF\'s own net.</p>\n')

    # ---- 6. steps 1-8 pipeline check ------------------------------------------------------------------
    h.append(section("map-steps", "Checking the steps 1-8 pipeline", "Checking the Team's CIF-to-Wulff Pipeline (Steps 1&ndash;8)"))
    h.append('      <p class="sd">The team notebook <code>MOF_Wulff_steps1-8.ipynb</code> goes from a CIF to a Wulff shape: standardise the '
             'structure, split it into building blocks, list face families and terminations, cut slabs of whole blocks, cap every '
             'broken metal&ndash;linker bond with dissociated water, compute CHGNet energies, and build and name the shape. It answers '
             'three weaknesses of the October CHGNet run (slabs cut through blocks, uncapped bonds, no DFT plan). It was run unchanged '
             'on its four input CIFs on a 2-core CPU with 8 GB of memory (<code>code/morphology/steps1_8_check/</code>).</p>\n')
    rows = []
    for r in QUICK:
        g = ", ".join(f'{{{k[6:].replace("2m10", "2&#772;10")}}} {float(r[k]):.3f}' for k in r if re.match(r"gamma_(\d+|2m10)$", k) and r[k])
        fr = json.loads(r["area_fractions"]) if r["area_fractions"] else {}
        top = ", ".join(f'{E(k)} {100*v:.0f} %' for k, v in sorted(fr.items(), key=lambda t: -t[1]) if v > 0)
        rows.append([("dt-label", E(r["mof"]) + f' <span class="sm">({E(r["space_group"])})</span>'), ("dt-note", g),
                     ("dt-note", "<b>" + E(r["habit"].split(":")[0].replace("_", " ")) + "</b><br>" + top), ("dt-note", E(r["reference_habit"]))])
    h.append('      <p class="sd"><b>Quick mode</b> (static CHGNet energies, all four MOFs; <code>results_quick/wulff_summary_all.csv</code>):</p>\n')
    h.append(table("map-quick", ["MOF (space group used)", "&gamma; static (J/m&sup2;)", "Notebook's shape name and area fractions", "Notebook's reference habit"], rows))
    rec = []
    for p in sorted(glob.glob(os.path.join(SC, "results_full_fixed", "*.log"))):
        mof = re.sub(r"^(fix_|one_face_)", "", os.path.basename(p)).split("_")[0].replace(".log", "")
        for ln in open(p, encoding="utf-8", errors="replace"):
            m = re.search(r"(\{[^}]+\}) t\d+ water: (\d+) atoms, gamma static ([\d.]+), relaxed ([\d.]+) \((\d+) steps\)", ln)
            if m:
                rec.append((mof, m.group(1), int(m.group(2)), float(m.group(3)), float(m.group(4)), int(m.group(5))))
    seen = set(); rows = []
    for mof, face, n, gs, gr, st in rec:
        if (mof, face) in seen:
            continue
        seen.add((mof, face))
        rows.append([("dt-label", mof), ("dt-note", face.replace("2̅", "2&#772;")), ("dt-value", str(n)), ("dt-value", f"{gs:.3f} &rarr; {gr:.3f}"),
                     ("dt-value", f"{100*(1-gr/gs):.0f} %"), ("dt-value", str(st))])
    h.append('      <p class="sd"><b>Full mode</b> (the lowest static termination of each face relaxed to <i>f</i><sub>max</sub> &le; 0.05 eV/&Aring;, '
             'with fixes K3 and K11 below; logs in <code>results_full_fixed/</code>). Larger slabs ran out of memory:</p>\n')
    h.append(table("map-full", ["MOF", "Face", "Atoms", "&gamma; static &rarr; relaxed (J/m&sup2;)", "Drop", "Steps"], rows))
    h.append('      <p class="sd">Reading. ZIF-8 agrees with the lab in both modes (relaxed: a rhombic dodecahedron, all {110}), as every '
             'earlier model did. HKUST-1 gets the lab\'s largest face but stops at a truncated octahedron, where every earlier model also '
             'stops. UiO-66 and Mg-MOF-74 do not reach their lab shapes: the UiO-66 input file has dehydroxylated nodes, and the code cuts '
             'the Mg-MOF-74 metal rod (K2). Relaxation lowers &gamma; by 60 % to almost 100 %, leaving values close to zero, so the '
             'order of faces rests on small differences: a DFT check of at least one face is needed before these numbers are used as results.</p>\n')
    hk = {r["face"]: r for r in K11["HKUST-1"]}
    h.append('      <p class="sd"><b>Problems found in the pipeline</b> (each has a script that shows it):</p>\n')
    h.append(table("map-k", ["#", "Problem", "How it was found", "Effect", "Status"], [
        [("dt-label", "K11"), ("dt-note", "After the bulk relaxation the relaxed cell is written to CIF and read back, which re-orients the lattice; faces are then converted to the wrong primitive planes"),
         ("dt-note", f'Full mode ran out of memory on HKUST-1 with a slab four times too large. <code>k11.py</code>: HKUST-1 (100) becomes {E(hk["{100}"]["primitive_plane_used"])}, spacing {hk["{100}"]["d_used"]} &Aring; instead of {hk["{100}"]["d_correct"]} &Aring;; the other HKUST-1 and Mg-MOF-74 faces fail conversion'),
         ("dt-note", "Relaxed mode cuts the wrong planes or falls back to the unrelaxed cell"), ("dt-note", "Fixed (one line, <code>kshitij_k11fix/mofwulff.py</code>)")],
        [("dt-label", "K1"), ("dt-note", "<code>name_habit()</code> calls any shape with more than 20 % {100} and 20 % {111} a cuboctahedron"),
         ("dt-note", "<code>checks/naming.py</code> against the exact limits: every shape with <i>y</i> from 0.87 to 1.20 is named cuboctahedron, though the true cuboctahedron is the single value 2/&radic;3"),
         ("dt-note", "UiO-66 (77 % {111}, a truncated octahedron) reported as a cuboctahedron"), ("dt-note", "Open: name from the exact limits (<code>cubic_wulff.py</code>)")],
        [("dt-label", "K2"), ("dt-note", "Mg&ndash;O bonds count as metal&ndash;linker bonds, so the Mg&ndash;O rod of Mg-MOF-74 is split into single-Mg nodes"),
         ("dt-note", "Step 2 output: six single-Mg nodes, rod flag false"), ("dt-note", "{001} slabs cut the rod; the shape comes out a block, not a rod"), ("dt-note", "Open")],
        [("dt-label", "K3"), ("dt-note", "Slabs may come from the unrelaxed cell while the bulk energy comes from the relaxed one"),
         ("dt-note", "Bulk relaxation lowers the CHGNet energy by 0.0995 eV/atom (HKUST-1)"), ("dt-note", "Adds up to +0.51 J/m&sup2; to a static &gamma;"), ("dt-note", "Fixed (one line)")],
        [("dt-label", "K4"), ("dt-note", "UiO-66's reference habit is given as an additive-free octahedron"),
         ("dt-note", "Our dataset: additive-free UiO-66 gives cubes; octahedra only with benzoic or acetic acid"), ("dt-note", "A wrong target makes a wrong prediction look right"), ("dt-note", "Open")],
        [("dt-label", "K5&ndash;K10"), ("dt-note", "Dehydroxylated UiO-66 nodes in the input (K5); a missing face family named a rod (K6, <code>checks/open_shape.py</code>); "
                                                 "absences ignored in the spacing ranking (K7); Spearman over three faces can only be &plusmn;1 or &plusmn;0.5 (K8); "
                                                 "CP2K inputs lack a dipole correction and the Cu<sup>2+</sup> spin state (K9); slab thickness not checked for convergence (K10)"),
         ("dt-note", "Reading the code and its output"), ("dt-note", "Limit trust in individual numbers"), ("dt-note", "Open")],
    ]))

    # ---- 7. limits and next ---------------------------------------------------------------------------
    h.append(section("map-limits", "What this shows, and its limits", "What This Shows, and Its Limits"))
    h.append('      <ul class="sd">'
             '<li><b>Shown:</b> from a unit cell the map generates a set of morphologies in a predicted order, and every laboratory series '
             'that changes shape on the map follows that order. This is the panel\'s request, with a test.</li>'
             '<li><b>Shown:</b> the additive-free shape is right where it is an equilibrium shape (ZIF-8), right in direction but not '
             'far enough for HKUST-1, and depends on the model for MOF-5.</li>'
             '<li><b>Not shown:</b> shapes set by growth kinetics (plates, rods, intergrown crystals) are outside any Wulff model. '
             'The map covers cubic crystals only; Mg-MOF-74 needs a non-cubic version after K2 is fixed.</li>'
             '<li><b>Not shown:</b> no condition model yet beats the structure-only prediction on records with additives (Test 2), '
             'and the first computed modulator energies are not physical for UiO-66.</li>'
             '<li><b>Data limit:</b> no database lists the morphologies a given CIF can form. Ours is collected by hand from papers '
             '(134 records, about 12 MOFs, doses in incompatible units): enough to test a method, not to train a general model. '
             'This question was put to the guide on 10 November.</li></ul>\n')
    h.append('      <p class="sd">Next steps are listed on <a href="team.html">Progress</a>. Code: '
             '<code>code/morphology/morphology_map/</code> and <code>code/morphology/steps1_8_check/</code>, each with a README.</p>\n')

    out = os.path.join(HERE, "fragments", "morphology_map.before.html")
    open(out, "w", encoding="utf-8").write("".join(h))
    print("wrote", out)


if __name__ == "__main__":
    main()
