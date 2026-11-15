"""Surface energies of the 14 November notebook against the chemical potential of water.

Run:  python water_mu_analysis.py <notebook.ipynb> <static run dir> <out.json>

Why. The notebook computes gamma = (E_slab - N e_bulk - n_H2O E_H2O) / 2A with E_H2O the energy of one
isolated water molecule at 0 K. That fixes the water chemical potential at mu = E_H2O, i.e. water with no
thermal energy and no entropy. Under any real condition mu_H2O is lower, and

    gamma(dmu) = gamma_0 - n_H2O * dmu / (2A),     dmu = mu_H2O - E_H2O   (eV per molecule)

(ab initio thermodynamics, Reuter and Scheffler, Phys. Rev. B 65, 035406 (2001)). The vibrational free
energy of the surface OH/H caps and the zero-point energy of the free molecule are both neglected, as is
usual in this formalism (they partly cancel; a residual of order 0.1 eV per molecule is the uncertainty).

Inputs
  * relaxed and static gamma for every slab, read from the notebook's printed log (cells 7 and 18);
  * n_H2O, area and family key of every slab, from a CPU rerun of steps 1-6 of the same module
    (bulk relaxed as in the notebook, slabs static) -- n_H2O and area do not depend on the slab relaxation.
    The rerun's static gamma is compared with the notebook's to show that the slabs are the same.

Water chemical potential (dmu relative to the 0 K molecule, eV), from NIST-JANAF table H-064
(H2O gas: H(298.15)-H(0) = 9.904 kJ/mol, S(298.15) = 188.834 J/mol/K; at 400 K H-H(298.15) = 3.452 kJ/mol,
S = 198.788 J/mol/K) and CODATA (formation Gibbs energies at 298.15 K: gas -228.582, liquid -237.129 kJ/mol):
    dmu(T, p) = [H(T) - H(0)] - T S(T) + kT ln(p / 1 bar)
"""
import json, math, re, sys, os
from pathlib import Path
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mofwulff as mw
import mofgnn as G

KJ_PER_MOL_TO_EV = 1 / 96.4853
J_M2 = mw.EV_A2_TO_J_M2

# --------------------------------------------------------------------------- water chemical potential
H0_298, S_298 = 9.904, 188.834e-3            # kJ/mol, kJ/mol/K  (JANAF H-064)
H0_400, S_400 = 9.904 + 3.452, 198.788e-3
DG_VAP_298 = -228.582 - (-237.129)           # kJ/mol: mu(liquid) = mu(gas, 1 bar) - 8.547 kJ/mol
R = 8.314462618e-3                           # kJ/mol/K


def dmu_gas(H, S, T, p_bar=1.0):
    return (H - T * S + R * T * math.log(p_bar)) * KJ_PER_MOL_TO_EV


CONDITIONS = {
    "0 K molecule (notebook)": 0.0,
    "vapour, 298 K, 1 bar": dmu_gas(H0_298, S_298, 298.15),
    "liquid water, 298 K": dmu_gas(H0_298, S_298, 298.15) - DG_VAP_298 * KJ_PER_MOL_TO_EV,
    "vapour, 298 K, 50 % RH": dmu_gas(H0_298, S_298, 298.15, 0.5 * 0.03169),
    "vapour, 400 K, 1 bar": dmu_gas(H0_400, S_400, 400.0),
}
REFERENCE = "liquid water, 298 K"

# --------------------------------------------------------------------------- notebook log
LINE = re.compile(r"(\{[^}]+\}) t(\d+) (\w+)\s*: (\d+) atoms, gamma static ([-\d.]+)(?:, relaxed ([-\d.]+) \((\d+) steps\))?")
HEAD = re.compile(r"^\d\d:\d\d:\d\d (\S+): \S+\s+SG")
NOTC = re.compile(r"NOT converged: (\{[^}]+\}) t(\d+) (\w+) fmax ([\d.]+)")


def parse_notebook(path):
    nb = json.load(open(path))
    rows, notconv = [], set()
    for ci in (7, 18):
        text = "".join("".join(o.get("text", "")) for o in nb["cells"][ci].get("outputs", []) if "text" in o)
        mof = None
        for line in text.splitlines():
            h = HEAD.match(line)
            if h:
                mof = h.group(1); continue
            m = NOTC.search(line)
            if m:
                notconv.add((mof, m.group(1), int(m.group(2)))); continue
            m = LINE.search(line)
            if m:
                rows.append(dict(mof=mof, face=m.group(1), termination=int(m.group(2)), cap=m.group(3),
                                 nb_n_atoms=int(m.group(4)), nb_gamma_static=float(m.group(5)),
                                 nb_gamma_relaxed=float(m.group(6)) if m.group(6) else np.nan, cell=ci))
    df = pd.DataFrame(rows)
    df["nb_converged"] = [np.nan if np.isnan(g) else (m, f, t) not in notconv
                          for m, f, t, g in zip(df.mof, df.face, df.termination, df.nb_gamma_relaxed)]
    return df


def main(nb_path, static_dir, out_json):
    nb = parse_notebook(nb_path)
    st = pd.concat([pd.read_csv(p, dtype={"family": str}) for p in sorted(Path(static_dir).glob("static_*.csv"))], ignore_index=True)
    st = st[st["cap"] == "water"]
    df = nb.merge(st[["mof", "face", "termination", "family", "n_atoms", "n_water", "area_A2", "bonds_per_A2",
                      "gamma_static_J_m2"]], on=["mof", "face", "termination"], how="left")
    missing = df[df["n_water"].isna()]
    df["static_diff"] = (df["gamma_static_J_m2"] - df["nb_gamma_static"]).abs()
    df["atoms_match"] = df["n_atoms"] == df["nb_n_atoms"]
    # slope of gamma against dmu, J/m^2 per eV of water chemical potential
    df["slope_J_m2_per_eV"] = df["n_water"] / (2 * df["area_A2"]) * J_M2
    df["dmu_zero_eV"] = df["nb_gamma_relaxed"] / df["slope_J_m2_per_eV"]      # gamma_relaxed(dmu) = 0 here
    for c, mu in CONDITIONS.items():
        df[f"gamma_relaxed@{c}"] = df["nb_gamma_relaxed"] - df["slope_J_m2_per_eV"] * mu
        df[f"gamma_static@{c}"] = df["nb_gamma_static"] - df["slope_J_m2_per_eV"] * mu

    rel = df[df["nb_gamma_relaxed"].notna()]
    res = dict(script="water_mu_analysis.py", notebook=os.path.basename(nb_path),
               conditions_dmu_eV={k: round(v, 4) for k, v in CONDITIONS.items()}, reference=REFERENCE,
               check=dict(slabs_in_log=int(len(df)), slabs_matched=int(len(df) - len(missing)),
                          unmatched=missing[["mof", "face", "termination"]].to_dict("records"),
                          atom_count_mismatch=int((~df["atoms_match"] & df["n_atoms"].notna()).sum()),
                          max_static_gamma_difference_J_m2=float(df["static_diff"].max()),
                          median_static_gamma_difference_J_m2=float(df["static_diff"].median())),
               relaxed_slabs=int(len(rel)), negative_relaxed={}, mofs={})
    for c in CONDITIONS:
        neg = rel[rel[f"gamma_relaxed@{c}"] <= 0]
        res["negative_relaxed"][c] = [dict(mof=r.mof, face=r.face, termination=int(r.termination),
                                           gamma=round(r[f"gamma_relaxed@{c}"], 4)) for _, r in neg.iterrows()]
    for mof, g in df.groupby("mof", sort=False):
        try:
            meta = G.load_meta(static_dir, mof)
        except FileNotFoundError:
            continue
        entry = dict(space_group=meta["space_group"], crystal_system=meta["crystal_system"], conditions={})
        for c in CONDITIONS:
            ok = g[g["nb_gamma_relaxed"].notna() & (g["nb_converged"] == True)]
            best = {}
            for _, r in ok.iterrows():
                v = r[f"gamma_relaxed@{c}"]
                if r.family not in best or v < best[r.family][0]:
                    best[r.family] = (v, r.face, int(r.termination))
            gam = {k: v[0] for k, v in best.items()}
            habit, dom, w = G.habit_from_gammas(meta, gam)
            fr = None
            if w is not None:
                names = {f["key"]: f["name"] for f in G._families_from_meta(meta)[1]}
                fr = {names.get(k, k): round(v, 3) for k, v in sorted(w["area_fractions"].items(), key=lambda kv: -kv[1])}
            entry["conditions"][c] = dict(
                gamma_per_face={v[1]: round(v[0], 4) for v in best.values()},
                termination_per_face={v[1]: v[2] for v in best.values()},
                face_order=[v[1] for v in sorted(best.values())], habit=habit, dominant_face=dom, area_fractions=fr)
        o0 = entry["conditions"]["0 K molecule (notebook)"]
        oref = entry["conditions"][REFERENCE]
        entry["face_order_changes_at_reference"] = o0["face_order"] != oref["face_order"]
        entry["termination_changes_at_reference"] = o0["termination_per_face"] != oref["termination_per_face"]
        entry["dominant_face_changes_at_reference"] = o0["dominant_face"] != oref["dominant_face"]
        res["mofs"][mof] = entry
    cols = ["mof", "face", "termination", "family", "nb_n_atoms", "n_water", "area_A2", "nb_gamma_static",
            "gamma_static_J_m2", "nb_gamma_relaxed", "nb_converged", "slope_J_m2_per_eV", "dmu_zero_eV"] + \
           [f"gamma_relaxed@{c}" for c in CONDITIONS]
    df[cols].to_csv(Path(out_json).with_suffix(".csv"), index=False)
    json.dump(res, open(out_json, "w"), indent=1, default=lambda x: None if x is None else float(x))
    print(json.dumps(res["check"], indent=1))
    print({k: round(v, 3) for k, v in CONDITIONS.items()})
    for c in CONDITIONS:
        print(c, "negative:", [(d["mof"], d["face"], d["gamma"]) for d in res["negative_relaxed"][c]])
    for m, e in res["mofs"].items():
        a, b = e["conditions"]["0 K molecule (notebook)"], e["conditions"][REFERENCE]
        print(f"{m:20s} 0K: {a['habit'][:60]:60s} | liquid: {b['habit'][:60]}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
