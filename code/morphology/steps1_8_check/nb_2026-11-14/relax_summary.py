"""Summarise the relaxations of the slabs with gamma <= 0 (relax_cases.py output).

Run:  python relax_summary.py <relax_nb dir> <relax_fixed dir> <out.json>

For each relaxed slab it records gamma before and after relaxation, and what the water caps became
(cap_chemistry.classify on the unrelaxed and relaxed CIF): M-OH, H2O bound to a metal, free H2O that has
left the surface, protonated ligand O (C-O-H), and C-O with two H. A free molecule sitting in the vacuum
gap is not part of the surface: at a water chemical potential dmu it should leave, so
    gamma(dmu) = gamma_0K - (n_H2O - n_free) dmu / 2A
is used for those slabs (the free molecule's energy in the box is taken as E_H2O; its interaction with the
slab is part of gamma_0K and is small when it is far from the surface).
"""
import json, sys, os, glob
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from pymatgen.core import Structure
import cap_chemistry as cc
import water_mu_analysis as W

J = 16.0218


def load(d, variant):
    p = os.path.join(d, f"relax_cases_{variant}.csv")
    if not os.path.exists(p):
        return []
    df = pd.read_csv(p, dtype={"family": str})
    df = df[df["gamma_relaxed_J_m2"].notna()]
    out = []
    for r in df.to_dict("records"):
        before = cc.classify(Structure.from_file(r["unrelaxed_cif"]))[0] if isinstance(r.get("unrelaxed_cif"), str) else {}
        after = cc.classify(Structure.from_file(r["relaxed_cif"]))[0] if isinstance(r.get("relaxed_cif"), str) else {}
        n_w = int(r.get("n_water") or 0)
        n_free = int(after.get("H2O free", 0))
        slope_all = n_w / (2 * r["area_A2"]) * J
        slope_bound = (n_w - n_free) / (2 * r["area_A2"]) * J
        rec = dict(variant=variant, mof=r["mof"], face=r["face"], termination=int(r["termination"]), cap=r["cap"],
                   status=r.get("status"), n_atoms=int(r["n_atoms"]) if r.get("n_atoms") == r.get("n_atoms") else None,
                   n_water=n_w, area_A2=r["area_A2"], gamma_static=r["gamma_static_J_m2"],
                   gamma_relaxed=r["gamma_relaxed_J_m2"], steps=int(r["steps"]), converged=bool(r["converged"]),
                   caps_before=before, caps_after=after, n_free_water_after=n_free,
                   gamma_relaxed_at={})
        for c, mu in W.CONDITIONS.items():
            rec["gamma_relaxed_at"][c] = dict(all_caps_bound=round(r["gamma_relaxed_J_m2"] - slope_all * mu, 4),
                                             free_water_left=round(r["gamma_relaxed_J_m2"] - slope_bound * mu, 4))
        out.append(rec)
    return out


if __name__ == "__main__":
    nb_dir, fixed_dir, out = sys.argv[1:4]
    rows = load(nb_dir, "notebook") + load(fixed_dir, "fixed")
    json.dump(dict(script="relax_summary.py", conditions_dmu_eV=W.CONDITIONS, slabs=rows), open(out, "w"), indent=1)
    for r in rows:
        print(f"{r['variant']:8s} {r['mof']:10s} {r['face']:6s} t{r['termination']} {r['cap']:5s} n_w={r['n_water']:2d} "
              f"static {r['gamma_static']:.3f} relaxed {r['gamma_relaxed']:.4f} conv {r['converged']} free H2O {r['n_free_water_after']} "
              f"| liquid: {r['gamma_relaxed_at']['liquid water, 298 K']} | {r['caps_before']} -> {r['caps_after']}")
