"""Compare the project's predicted crystal shapes with the experimental dataset.

    python compare_with_project.py

Reads   ../dataset/experimental_morphology.csv
        <repo>/code/morphology/results/phase1_results.json  (BFDH, graph rule)
        <repo>/code/morphology/results/phase3_results.json  (attachment, broken-bond Wulff)
        <repo>/code/morphology/results/phase4_results.json  (UFF surface-energy Wulff)
Writes  COMPARISON.md, comparison.csv

The benchmark for each MOF is a hand-picked list of additive-free, phase-pure
experimental records (BENCHMARK below), each with the reason it was chosen.
A predicted shape is scored on two things:
  name   - does the predicted shape name equal the experimental one
  facet  - is the predicted shape's largest face family the face family the
           experimental crystals expose
"""
import csv
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
REPO = TASK.parent.parent          # repository root (data/experimental_morphology -> data -> repo)
RES = REPO / "code" / "morphology" / "results"

# Experimental shape -> face family it exposes (as the papers state it)
SHAPE_FACET = {
    "cube": "{100}", "octahedron": "{111}", "rhombic_dodecahedron": "{110}",
}

BENCHMARK = {
    "MOF-5": {
        "ids": ["MOF-5-suresh2021-1", "MOF-5-suresh2021-2", "MOF-5-suresh2021-3", "MOF-5-suresh2021-4",
                "MOF-5-suresh2022-1", "MOF-5-mulyati2015-1", "MOF-5-mulyati2015-2", "MOF-5-mulyati2015-3"],
        "why": "No additive, 12-144 h at 100-140 C, two independent laboratories (DEF and DMF).",
    },
    "HKUST-1": {
        "ids": ["HKUST-1-ediati2019-1", "HKUST-1-rubio2014-1", "HKUST-1-rubio2014-2", "HKUST-1-rubio2014-3",
                "HKUST-1-zelenka2024-1"],
        "why": "No additive: EtOH/DMF/H2O at 100 C for 10 h, and EtOH in flow at 80-140 C. "
               "Flow runs are minutes long, so they are short-time, not equilibrium, shapes. "
               "zelenka2024 (added 2026-10-14): DMF/EtOH/H2O at 85 C for 12 h, octahedra of a few micrometres.",
    },
    "UiO-66": {
        "ids": ["UiO-66-cao2018-1", "UiO-66-rahmawati2014-1"],
        "why": "WEAK BENCHMARK. No modulator, DMF, 120-140 C. cao2018 says 'same cubic structure as UiO-66', which may "
               "mean the lattice rather than the shape; rahmawati2014 says 'clusters of square morphology'. Neither shows "
               "well-faceted crystals. "
               "Modulated UiO-66 is octahedral in two primary open-access papers (butova2023: benzoic acid, DMF, "
               "120 C, TEM; morelli2020: acetic acid in GVL or propylene carbonate, 120 C, SEM); these are listed "
               "below, not used as the benchmark, because no prediction contains a modulator.",
    },
    "ZIF-8": {
        "ids": ["ZIF-8-zhang2018-4", "ZIF-8-zhang2018-5", "ZIF-8-tezerjani2021-1", "ZIF-8-tezerjani2021-2",
                "ZIF-8-tezerjani2021-4", "ZIF-8-tezerjani2021-5", "ZIF-8-tezerjani2021-7", "ZIF-8-tezerjani2021-8",
                "ZIF-8-cravillon2012-4", "ZIF-8-oh2023-2"],
        "why": "No additive in MeOH or DMF at Hmim/Zn >= 8 (by-product-free), plus the 4 h end point of "
               "the formate series, which the authors identify as the equilibrium shape; oh2023-2 (MeOH, 70 C, "
               "no additive) added 2026-10-14.",
    },
}

ALSO = {
    "UiO-66": ["UiO-66-butova2023-1", "UiO-66-morelli2020-1", "UiO-66-morelli2020-2", "UiO-66-schaate2011-2"],
    "HKUST-1": ["HKUST-1-umemura2011-1", "HKUST-1-klemba2025-1"],
}


def load_exp():
    with open(TASK / "dataset" / "experimental_morphology.csv", encoding="utf-8") as f:
        return {r["record_id"]: r for r in csv.DictReader(f)}


def dominant(fractions):
    """Largest face family, with {111}+ and {111}- merged."""
    merged = Counter()
    for k, v in fractions.items():
        merged[k.rstrip("+-")] += v
    fam, frac = merged.most_common(1)[0]
    return fam, frac


def predictions(mof, p1, p3, p4):
    out = []
    b = p1[mof]["bfdh"]
    out.append(("BFDH (Phase 1)", b["name"], b["face_area_fraction"]))
    if mof in p1.get("graph_rule", {}):
        series = p1["graph_rule"][mof]["beta_series"]
        names = ", ".join(f"beta={s['beta']}: {s['name']}" for s in series)
        last = series[-1]
        out.append((f"Graph attachment rule (Phase 1), largest beta [{names}]", last["name"], last["face_area_fraction"]))
    a = p3[mof]["shape_attachment"]
    out.append(("Attachment-energy Wulff (Phase 3)", a["name"], a["face_area_fraction"]))
    w = p3[mof]["shape_wulff_broken_bond"]
    out.append(("Broken-bond Wulff (Phase 3)", w["name_major_faces"], w["face_area_fraction"]))
    u = p4[mof]["shape_wulff_uff"]
    bs = json.loads((RES / "bond_sensitivity.json").read_text(encoding="utf-8")) if (RES / "bond_sensitivity.json").exists() else {}
    tag = ""
    if mof in bs:
        byf = bs[mof]["by_factor"]
        alt = ", ".join(f"f={k}: {v['shape']}, largest {dominant(v['faces'])[0]}" for k, v in byf.items() if k != "1.0")
        same_face = len({dominant(v["faces"])[0] for v in byf.values()}) == 1
        if bs[mof]["shape_robust"]:
            tag = " [shape unchanged when metal-ligand bonds cost 0.5x or 0.25x]"
        elif same_face:
            tag = f" [largest face unchanged, shape name changes: metal-ligand bond cost x {alt}]"
        else:
            tag = f" [NOT robust, largest face changes: metal-ligand bond cost x {alt}]"
    out.append(("UFF surface-energy Wulff (Phase 4)" + tag, u["name"], u["face_area_fraction"]))
    hy = RES / "hybrid_results.json"
    if hy.exists():
        h = json.loads(hy.read_text(encoding="utf-8")).get(mof)
        if h:
            s = h["shapes"]["0.5"]
            out.append(("BFDH x UFF hybrid, w=0.5 (one free parameter)", s["name"], s["faces"]))
    cc = RES / "chgnet_cleavage_results.json"
    if cc.exists():
        c = json.loads(cc.read_text(encoding="utf-8")).get(mof)
        if c:
            v = c.get("intact_only") or c.get("all_slabs")
            s = v["shapes"]["1"]
            out.append(("CHGNet cleavage-energy Wulff (proxy, intact slabs only)", s["name"], s["faces"]))
    ch = HERE / "chgnet_shapes.json"
    if ch.exists():
        c = json.loads(ch.read_text(encoding="utf-8")).get(mof)
        if c and c.get("shape"):
            out.append(("CHGNet Wulff (MorphoGraph notebook)", c["shape"], c["face_area_fraction"]))
        elif c:
            out.append(("CHGNet Wulff (MorphoGraph notebook)", "no shape: " + c.get("shape_error", "?"), {"none": 0.0}))
    return out


def norm(name):
    return name.replace(" ", "_").replace("-", "_")


def main():
    exp = load_exp()
    p1 = json.loads((RES / "phase1_results.json").read_text(encoding="utf-8"))
    p3 = json.loads((RES / "phase3_results.json").read_text(encoding="utf-8"))
    p4 = json.loads((RES / "phase4_results.json").read_text(encoding="utf-8"))

    md = ["# Project predictions against experimental shapes", "",
          "Generated by `compare_with_project.py`. Predictions are read from the project's",
          "`code/morphology/results/*.json`; experiments from `../dataset/experimental_morphology.csv`.", "",
          "**name**: predicted shape name equals the experimental one. **facet**: the predicted shape's",
          "largest face family is the one the experimental crystals expose. All predictions are for",
          "a bare crystal in vacuum (no solvent, no additive), so the benchmark is additive-free crystals.", ""]
    rows = []
    summary = []
    for mof, spec in BENCHMARK.items():
        recs = [exp[i] for i in spec["ids"]]
        shapes = Counter(r["morphology"] for r in recs)
        exp_shape = shapes.most_common(1)[0][0]
        exp_facet = SHAPE_FACET.get(exp_shape, "?")
        md += [f"## {mof}", "",
               f"Experiment: **{exp_shape}** (exposes {exp_facet}) in {len(recs)} of {len(recs)} benchmark records "
               f"from {len({r['source_id'] for r in recs})} papers. {spec['why']}", "",
               "| Method | Predicted shape | Largest face (fraction) | name | facet |", "|---|---|---|---|---|"]
        for method, name, frac in predictions(mof, p1, p3, p4):
            if "none" in frac:
                md.append(f"| {method} | {name} | - | - | - |")
                continue
            fam, f = dominant(frac)
            ok_name = norm(name) == exp_shape
            ok_facet = fam == exp_facet
            md.append(f"| {method} | {name} | {fam} ({f:.2f}) | {'yes' if ok_name else 'no'} | {'yes' if ok_facet else 'no'} |")
            rows.append({"mof": mof, "method": method.split(" [")[0], "robustness_note": method.split(" [", 1)[1].rstrip("]") if " [" in method else "",
                         "predicted": name, "largest_face": fam,
                         "largest_face_fraction": round(f, 3), "experiment": exp_shape, "experiment_face": exp_facet,
                         "name_match": ok_name, "facet_match": ok_facet,
                         "benchmark_records": " ".join(spec["ids"])})
            summary.append((mof, method.split(" [")[0], ok_name, ok_facet))
        for i in ALSO.get(mof, []):
            r = exp[i]
            md.append(f"\nAlso reported (not benchmark): `{i}`: {r['morphology']} with {r['additive'] or 'unstated additive'} "
                      f"({r['access']}).")
        md.append("")
    with open(HERE / "comparison.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    md += ["## Score", "", "| Method | name matches | facet matches |", "|---|---|---|"]
    for method in dict.fromkeys(m for _, m, _, _ in summary):
        s = [x for x in summary if x[1] == method]
        md.append(f"| {method} | {sum(x[2] for x in s)} / {len(s)} | {sum(x[3] for x in s)} / {len(s)} |")
    md += ["", "## Reading", "",
           "- **ZIF-8:** every method gives the rhombic dodecahedron, which is what experiments show",
           "  without additives and what Cravillon et al. identify as the equilibrium shape. This is",
           "  the one clean validation.",
           "- **MOF-5:** experiments give a cube in all 8 benchmark records (two independent labs).",
           "  The energy-based methods (graph rule at beta >= 0.6, broken-bond Wulff, UFF Wulff) give a",
           "  cube, and attachment Wulff gives a truncated cube that is 95% {100}. BFDH gives a",
           "  truncated octahedron and is wrong: MOF-5 is a case where geometry alone fails.",
           "  Two cautions (2026-10-14). The UFF cube depends on charging a Zn-O bond the same 70",
           "  kcal/mol as a C-C bond: at 0.5x the Zn-O cost it is a truncated cube, at 0.25x a",
           "  truncated octahedron, although {100} stays the largest face at both",
           "  (`run_bond_sensitivity.py`). The CHGNet cleavage proxy gives a",
           "  truncated octahedron (88% {111}), and that does not change when slabs with broken",
           "  linkers are dropped. So the MOF-5 match rests on the bond-counting methods only.",
           "- **HKUST-1:** experiments give an octahedron. Every method gives a truncated octahedron",
           "  with {111} as the largest face (77-90%), so the dominant face is right, but every method",
           "  also keeps {100} faces (10-23%) that the crystals do not show. None reproduces the",
           "  pure octahedron. The flow runs are minutes long, so they are short-time shapes rather",
           "  than equilibrium ones.",
           "- **UiO-66:** inconclusive. The additive-free reports are poorly faceted and loosely",
           "  worded. Every method predicts {111} (octahedron or truncated octahedron), which matches",
           "  the octahedra of modulated UiO-66 (now from two primary papers, butova2023 and",
           "  morelli2020), but the predictions contain no modulator. Phase 1's tetrahedral shape for the ordered F-43m",
           "  structure has no experimental counterpart in this dataset.",
           "- **CHGNet:** the MorphoGraph notebook itself produced no shape for any MOF (every",
           "  facet's pair equations were underdetermined). The row above uses the cleavage-energy",
           "  proxy (half the lowest pair excess per plane, `chgnet_post.py`), from slabs that are",
           "  15-30 A thick (one or two framework layers, not thickness-converged), bare, in vacuum,",
           "  with no solvent or modulator. It is a diagnostic, not a validated prediction.",
           "- **Hybrid:** the BFDH x UFF blend has one free weight w. With four MOFs and one free",
           "  parameter, any w that scores best is fitted to the test set; it is shown at w=0.5 only",
           "  and must not be ranked against the other methods without held-out MOFs.",
           "- **Not compared:** hMOF-0, because it is hypothetical and has no experimental crystal.",
           "  Shapes grown with additives are not compared either, because no prediction includes an",
           "  additive. The additive records are the test set for a future model that does.",
           "- Of the four benchmark MOFs, only ZIF-8 and MOF-5 have strong benchmarks, and MOF-5's",
           "  rests partly on one research group. The scores above therefore come from a small sample,",
           "  and four MOFs are not enough to rank the methods."]
    (HERE / "COMPARISON.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[-8:]))


if __name__ == "__main__":
    main()
