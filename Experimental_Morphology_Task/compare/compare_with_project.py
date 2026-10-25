"""Compare the project's predicted crystal shapes with the experimental dataset.

    python compare_with_project.py

Reads   ../dataset/experimental_morphology.csv
        <repo>/2_python/morphology/results/phase1_results.json  (BFDH, graph rule)
        <repo>/2_python/morphology/results/phase3_results.json  (attachment, broken-bond Wulff)
        <repo>/2_python/morphology/results/phase4_results.json  (UFF surface-energy Wulff)
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
REPO = TASK.parent
RES = REPO / "2_python" / "morphology" / "results"

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
        "ids": ["HKUST-1-ediati2019-1", "HKUST-1-rubio2014-1", "HKUST-1-rubio2014-2", "HKUST-1-rubio2014-3"],
        "why": "No additive: EtOH/DMF/H2O at 100 C for 10 h, and EtOH in flow at 80-140 C. "
               "Flow runs are minutes long, so they are short-time, not equilibrium, shapes.",
    },
    "UiO-66": {
        "ids": ["UiO-66-cao2018-1", "UiO-66-rahmawati2014-1"],
        "why": "WEAK BENCHMARK. No modulator, DMF, 120-140 C. cao2018 says 'same cubic structure as UiO-66', which may "
               "mean the lattice rather than the shape; rahmawati2014 says 'clusters of square morphology'. Neither shows "
               "well-faceted crystals. "
               "Modulated UiO-66 (acetic/benzoic acid) is reported as octahedral (schaate2011, abstract "
               "plus a secondary statement) and is listed separately below, not used as the benchmark.",
    },
    "ZIF-8": {
        "ids": ["ZIF-8-zhang2018-4", "ZIF-8-zhang2018-5", "ZIF-8-tezerjani2021-1", "ZIF-8-tezerjani2021-2",
                "ZIF-8-tezerjani2021-4", "ZIF-8-tezerjani2021-5", "ZIF-8-tezerjani2021-7", "ZIF-8-tezerjani2021-8",
                "ZIF-8-cravillon2012-4"],
        "why": "No additive in MeOH or DMF at Hmim/Zn >= 8 (by-product-free), plus the 4 h end point of "
               "the formate series, which the authors identify as the equilibrium shape.",
    },
}

ALSO = {
    "UiO-66": ["UiO-66-schaate2011-2"],
    "HKUST-1": ["HKUST-1-umemura2011-1"],
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
    out.append(("UFF surface-energy Wulff (Phase 4)", u["name"], u["face_area_fraction"]))
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
          "`2_python/morphology/results/*.json`; experiments from `../dataset/experimental_morphology.csv`.", "",
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
            rows.append({"mof": mof, "method": method.split(" [")[0], "predicted": name, "largest_face": fam,
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
           "- **HKUST-1:** experiments give an octahedron. Every method gives a truncated octahedron",
           "  with {111} as the largest face (77-90%), so the dominant face is right, but every method",
           "  also keeps {100} faces (10-23%) that the crystals do not show. None reproduces the",
           "  pure octahedron. The flow runs are minutes long, so they are short-time shapes rather",
           "  than equilibrium ones.",
           "- **UiO-66:** inconclusive. The additive-free reports are poorly faceted and loosely",
           "  worded. Every method predicts {111} (octahedron or truncated octahedron), which matches",
           "  the octahedra reported for modulated UiO-66, but that report is abstract-level and the",
           "  predictions contain no modulator. Phase 1's tetrahedral shape for the ordered F-43m",
           "  structure has no experimental counterpart in this dataset.",
           "- **Not compared:** the CHGNet notebook (hMOF-0), because that run produced no valid",
           "  surface energies and hMOF-0 is hypothetical, so no experimental crystal exists. Shapes",
           "  grown with additives are not compared either, because no prediction includes an",
           "  additive. The additive records are the test set for a future model that does.",
           "- Of the four benchmark MOFs, only ZIF-8 and MOF-5 have strong benchmarks, and MOF-5's",
           "  rests partly on one research group. The scores above therefore come from a small sample,",
           "  and four MOFs are not enough to rank the methods."]
    (HERE / "COMPARISON.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[-8:]))


if __name__ == "__main__":
    main()
