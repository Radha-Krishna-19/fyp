"""Validate records.jsonl against SCHEMA.md and write the combined outputs.

    python build_dataset.py

Reads   records/*.jsonl (one file per source), sources.jsonl, mofs.json
Writes  experimental_morphology.csv   one row per record, provenance merged in
        aligned_by_mof.md             per-MOF tables: condition -> shape, grouped
                                      by the variable the source changed
Exits non-zero if a record breaks the schema, so a bad row cannot slip into the CSV.
"""
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent

RECORD_FIELDS = [
    "record_id", "mof", "method", "metal_salt", "metal_conc_mM", "linker_to_metal",
    "solvent", "additive", "additive_amount", "additive_role", "temperature_C", "time_h",
    "heating", "stirring", "morphology", "morphology_as_written", "facets", "size_um",
    "size_basis", "evidence", "regime", "kinetics", "mechanism_as_written", "source_id",
    "locator", "varied", "notes",
]
MOF_FIELDS = ["metal", "linker", "net", "space_group"]
SOURCE_FIELDS = ["doi", "citation", "title", "access"]
CSV_FIELDS = (RECORD_FIELDS[:2] + MOF_FIELDS + RECORD_FIELDS[2:] + SOURCE_FIELDS)

MORPHOLOGY = {
    "cube", "truncated_cube", "cube_truncated_edges", "cuboctahedron",
    "truncated_octahedron", "octahedron", "rhombic_dodecahedron",
    "truncated_rhombic_dodecahedron", "tetrahedron", "truncated_tetrahedron",
    "sphere", "plate", "rod", "needle", "intergrown", "irregular",
    "hexagonal_prism", "hexagonal_rod", "hexagonal_plate", "bipyramid",
    "spindle", "star", "hollow", "other",
}
METHOD = {
    "solvothermal", "room_temperature", "microwave", "hydrothermal", "microfluidic",
    "electrochemical", "hot_injection", "sonochemical", "mechanochemical",
    "layering", "reflux", "continuous_flow", "spray", "other",
}
ROLE = {"coordination_modulator", "deprotonation_base", "capping_agent",
        "surfactant", "other", None}
REGIME = {"thermodynamic", "kinetic", "unknown"}
ACCESS = {"full_text", "abstract", "secondary"}
HEATING = {"oven", "oil_bath", "microwave", "none", "autoclave_oven", "other", None}
NUMERIC = {"metal_conc_mM", "linker_to_metal", "temperature_C", "time_h"}
RANGE = re.compile(r"-?\d+(\.\d+)?--?\d+(\.\d+)?")  # a reported range such as "110-150"


def load_jsonl(path):
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                sys.exit(f"{path.name}:{n}: {e}")
    return rows


def validate(records, sources, mofs):
    errs = []
    seen = set()
    for r in records:
        rid = r.get("record_id", "?")
        for k in r:
            if k not in RECORD_FIELDS:
                errs.append(f"{rid}: unknown field {k!r}")
        for k in ("record_id", "mof", "morphology", "source_id", "regime", "locator"):
            if r.get(k) in (None, ""):
                errs.append(f"{rid}: missing {k}")
        if rid in seen:
            errs.append(f"{rid}: duplicate record_id")
        seen.add(rid)
        if r.get("mof") not in mofs:
            errs.append(f"{rid}: mof {r.get('mof')!r} not in mofs.json")
        if r.get("source_id") not in sources:
            errs.append(f"{rid}: source {r.get('source_id')!r} not in sources.jsonl")
        if r.get("morphology") not in MORPHOLOGY:
            errs.append(f"{rid}: morphology {r.get('morphology')!r} not in vocabulary")
        if r.get("method") is not None and r["method"] not in METHOD:
            errs.append(f"{rid}: method {r['method']!r} not in vocabulary")
        if r.get("additive_role") not in ROLE:
            errs.append(f"{rid}: additive_role {r.get('additive_role')!r}")
        if r.get("regime") not in REGIME:
            errs.append(f"{rid}: regime {r.get('regime')!r}")
        if r.get("heating") not in HEATING:
            errs.append(f"{rid}: heating {r.get('heating')!r}")
        for k in NUMERIC:
            v = r.get(k)
            if v is not None and not isinstance(v, (int, float)) and not RANGE.fullmatch(str(v)):
                errs.append(f"{rid}: {k} must be a number, an 'a-b' range or null, got {v!r}")
        if r.get("stirring") not in (True, False, None):
            errs.append(f"{rid}: stirring must be true/false/null")
    for s in sources.values():
        if s.get("access") not in ACCESS:
            errs.append(f"source {s['source_id']}: access {s.get('access')!r}")
    return errs


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def condition_label(r):
    parts = []
    if r.get("solvent"):
        parts.append(r["solvent"])
    if r.get("temperature_C") is not None:
        parts.append(f"{fmt(r['temperature_C'])} °C")
    if r.get("time_h") is not None:
        parts.append(f"{fmt(r['time_h'])} h")
    if r.get("linker_to_metal") is not None:
        parts.append(f"L:M {fmt(r['linker_to_metal'])}")
    if r.get("additive") and r["additive"] != "none":
        amt = f" ({r['additive_amount']})" if r.get("additive_amount") else ""
        parts.append(f"{r['additive']}{amt}")
    elif r.get("additive") == "none":
        parts.append("no additive")
    return "; ".join(parts)


def write_aligned(records, sources, mofs, path):
    by_mof = defaultdict(list)
    for r in records:
        by_mof[r["mof"]].append(r)
    out = ["# Experimental morphology aligned by MOF", "",
           "Generated by `build_dataset.py` from `records/*.jsonl`. Do not edit by hand.", "",
           "Within each MOF, records are grouped by source and by the variable that",
           "source changed (`varied`), so each block reads as one controlled series.",
           "A shape is only comparable across blocks when the other conditions match.", ""]
    out.append("| MOF | records | sources | shapes seen |")
    out.append("|---|---|---|---|")
    for m in sorted(by_mof):
        rs = by_mof[m]
        shapes = sorted({r["morphology"] for r in rs})
        out.append(f"| {m} | {len(rs)} | {len({r['source_id'] for r in rs})} | {', '.join(shapes)} |")
    out.append("")
    for m in sorted(by_mof):
        info = mofs[m]
        out.append(f"## {m}")
        out.append("")
        out.append(f"{info['metal']} / {info['linker']}, net `{info['net']}`, {info['space_group']}.")
        if info.get("note"):
            out.append(info["note"])
        out.append("")
        groups = defaultdict(list)
        for r in by_mof[m]:
            groups[(r["source_id"], r.get("varied") or "single condition")].append(r)
        for (sid, varied), rs in sorted(groups.items()):
            s = sources[sid]
            out.append(f"### {s['citation']} — varied: {varied}")
            out.append("")
            out.append(f"DOI [{s['doi']}](https://doi.org/{s['doi']}); access: {s['access']}.")
            out.append("")
            out.append("| Condition | Method | Shape | Facets | Size (µm) | Regime | Where |")
            out.append("|---|---|---|---|---|---|---|")
            for r in rs:
                out.append("| " + " | ".join([
                    condition_label(r), fmt(r.get("method")), r["morphology"],
                    fmt(r.get("facets")), fmt(r.get("size_um")), r["regime"],
                    fmt(r.get("locator"))]).replace("\n", " ") + " |")
            mech = {r["mechanism_as_written"] for r in rs if r.get("mechanism_as_written")}
            for mtxt in sorted(mech):
                out.append(f"\n*Authors' mechanism:* {mtxt}")
            kin = [r for r in rs if r.get("kinetics")]
            for r in kin:
                out.append(f"\n*Kinetics ({r['record_id']}):* {r['kinetics']}")
            out.append("")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    records = [r for p in sorted((HERE / "records").glob("*.jsonl")) for r in load_jsonl(p)]
    sources = {s["source_id"]: s for s in load_jsonl(HERE / "sources.jsonl")}
    mofs = json.loads((HERE / "mofs.json").read_text(encoding="utf-8"))
    errs = validate(records, sources, mofs)
    if errs:
        print("\n".join(errs))
        sys.exit(f"{len(errs)} schema error(s); nothing written")
    with open(HERE / "experimental_morphology.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in records:
            row = {k: fmt(r.get(k)) for k in RECORD_FIELDS}
            row.update({k: mofs[r["mof"]].get(k, "") for k in MOF_FIELDS})
            row.update({k: sources[r["source_id"]].get(k, "") for k in SOURCE_FIELDS})
            w.writerow(row)
    write_aligned(records, sources, mofs, HERE / "aligned_by_mof.md")
    n_src = len({r["source_id"] for r in records})
    print(f"{len(records)} records, {n_src} sources, {len({r['mof'] for r in records})} MOFs")
    write_kinetics(sources)
    write_co2(sources)


CO2_FIELDS = [
    "co2_id", "mof", "method", "metal_salt", "linker", "solvent", "synthesis_T_C", "synthesis_time_h",
    "heating", "additive", "yield_pct", "morphology", "size_um", "BET_m2g", "co2_uptake_mmolg",
    "uptake_T_K", "uptake_P_bar", "Qst_kJmol", "selectivity_CO2_N2", "selectivity_basis",
    "measurement", "source_id", "locator", "notes",
]


def write_co2(sources):
    """co2_adsorption.jsonl -> co2_adsorption.csv: measured CO2 uptake against the
    synthesis conditions of the sample it was measured on."""
    path = HERE / "co2_adsorption.jsonl"
    if not path.exists():
        return
    rows = load_jsonl(path)
    errs = []
    for r in rows:
        rid = r.get("co2_id")
        for k in r:
            if k not in CO2_FIELDS:
                errs.append(f"{rid}: unknown field {k!r}")
        for k in ("co2_uptake_mmolg", "uptake_T_K", "uptake_P_bar", "source_id", "locator"):
            if r.get(k) in (None, ""):
                errs.append(f"{rid}: missing {k}")
        if r.get("source_id") not in sources:
            errs.append(f"{rid}: source {r.get('source_id')!r} not in sources.jsonl")
        if r.get("morphology") is not None and r["morphology"] not in MORPHOLOGY:
            errs.append(f"{rid}: morphology {r['morphology']!r} not in vocabulary")
    if errs:
        print("\n".join(errs))
        sys.exit(f"{len(errs)} CO2 error(s); co2_adsorption.csv not written")
    with open(HERE / "co2_adsorption.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CO2_FIELDS + ["doi"])
        w.writeheader()
        for r in rows:
            row = {k: fmt(r.get(k)) for k in CO2_FIELDS}
            row["doi"] = sources[r["source_id"]]["doi"]
            w.writerow(row)
    print(f"{len(rows)} CO2 adsorption rows")


KINETIC_FIELDS = [
    "kinetics_id", "mof", "model", "k_per_min", "avrami_n", "A_per_min", "Ea_kJmol",
    "k_n_per_min", "k_g_per_min", "A_n_per_min", "A_g_per_min", "Ea_n_kJmol", "Ea_g_kJmol",
    "heating", "conditions", "mapping", "raw_row", "notes", "primary_ref", "source_id", "locator",
]


def write_kinetics(sources):
    """kinetics.jsonl -> kinetics.csv. Rate data has no shape, so it is kept apart
    from the morphology records and joined to them by MOF name."""
    path = HERE / "kinetics.jsonl"
    if not path.exists():
        return
    rows = load_jsonl(path)
    errs = []
    for r in rows:
        for k in r:
            if k not in KINETIC_FIELDS:
                errs.append(f"{r.get('kinetics_id')}: unknown field {k!r}")
        if r.get("source_id") not in sources:
            errs.append(f"{r.get('kinetics_id')}: source {r.get('source_id')!r} not in sources.jsonl")
        if r.get("mapping") not in ("unambiguous", "inferred"):
            errs.append(f"{r.get('kinetics_id')}: mapping must be unambiguous or inferred")
    if errs:
        print("\n".join(errs))
        sys.exit(f"{len(errs)} kinetics error(s); kinetics.csv not written")
    with open(HERE / "kinetics.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=KINETIC_FIELDS + ["doi"])
        w.writeheader()
        for r in rows:
            row = {k: fmt(r.get(k)) for k in KINETIC_FIELDS}
            row["doi"] = sources[r["source_id"]]["doi"]
            w.writerow(row)
    print(f"{len(rows)} kinetics rows")


if __name__ == "__main__":
    main()
