#!/usr/bin/env python3
"""
build_real_csv.py — writes mof_multifractal_descriptors_real_v2.csv from the
61-framework CoRE MOF run in 3_notebooks/real_results.json.

Schema is identical to mof_multifractal_descriptors_v1.csv (the 77 hypothetical
frameworks) so the two files concatenate without reconciliation. Columns the
real run does not supply are left empty rather than filled with a placeholder:
an empty cell reads as "not measured", whereas a 0 or an "NA" string gets
silently averaged by someone in a hurry.

v2 supersedes v1 of this file, which held the four withdrawn structures. See
9_dataset/README.md for why they were withdrawn.

Run:  python build_real_csv.py
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SRC = os.path.join(ROOT, "3_notebooks", "real_results.json")
OUT = os.path.join(HERE, "mof_multifractal_descriptors_real_v2.csv")

COLUMNS = [
    "framework_id", "n_blocks", "n_nodes", "n_linkers", "n_atoms_supercell",
    "graph_diameter", "n_influential", "delta_alpha", "delta_alpha_sd",
    "alpha_min", "alpha_max", "asymmetry_A", "asymmetry_sd",
    "lcd_angstrom", "pld_angstrom", "mofid", "source_url", "provenance",
]


def main():
    data = json.load(open(SRC))
    rows = []
    for name, r in sorted(data.items()):
        alpha = r["alpha"]
        rows.append({
            "framework_id": name,
            "n_blocks": r["n_nodes"] + r["n_linkers"],
            "n_nodes": r["n_nodes"],
            "n_linkers": r["n_linkers"],
            "n_atoms_supercell": r["N"],
            "graph_diameter": r["diameter"],
            "n_influential": r["n_influential"],
            "delta_alpha": round(r["width"], 4),
            "delta_alpha_sd": round(r["width_sd"], 4),
            "alpha_min": round(min(alpha), 4),
            "alpha_max": round(max(alpha), 4),
            "asymmetry_A": round(r["asymmetry"], 4),
            "asymmetry_sd": round(r["asymmetry_sd"], 4),
            "lcd_angstrom": r.get("lcd", ""),
            "pld_angstrom": r.get("pld", ""),
            "mofid": r.get("mofid") or "",
            "source_url": ("https://mof.tech.northwestern.edu" + r["url"]) if r.get("url") else "",
            "provenance": "experimentally synthesised (CoRE MOF 2019, Zenodo 10.5281/zenodo.3370236)",
        })

    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    print(f"wrote {OUT} — {len(rows)} frameworks")


if __name__ == "__main__":
    main()
