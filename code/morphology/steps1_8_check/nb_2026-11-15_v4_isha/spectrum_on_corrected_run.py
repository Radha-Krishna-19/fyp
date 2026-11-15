"""Isha's morphology spectrum (morphspec.py from the v4 notebook, unchanged) applied to the surface energies of
the corrected GPU run of 15 November, taken at liquid water, 298 K (delta mu = -0.5695 eV).

gamma(mu) = gamma_relaxed - water_slope * delta_mu, lowest converged water-capped termination per family.
Run from this folder:  python spectrum_on_corrected_run.py   (CPU, about 30 s; needs pymatgen, spglib, scipy,
networkx, torch for the mofgnn import). Writes spectrum_corrected_liquid_water.json.
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pandas as pd
import mofwulff as mw, mofgnn as G, morphspec as MS

RUN = HERE.parent / "nb_2026-11-14" / "colab_run_2026-11-15"
CIFS = HERE.parent / "input_cifs"
DMU = -0.5695
df = pd.read_csv(RUN / "slabs.csv", dtype={"family": str})
df["g_mu"] = df.gamma_relaxed_J_m2 - df.water_slope_J_m2_per_eV * DMU
out = {}
for mof, cif in [("ZIF-8", "ZIF-8.cif"), ("HKUST-1", "Cu-BTC.cif"), ("UiO-66", "UIO-66.cif"), ("Mg-MOF-74", "MgMOF-74.cif")]:
    info = mw.standardize(str(CIFS / cif), 0.1, "majority")
    fams = mw.face_families(info["conv"], info["rotations"], 1, 4)
    keys = {f["key"]: f["name"] for f in fams}
    d = df[(df.mof == mof) & (df.cap == "water") & (df.converged == True)]
    gam = {k: v for k, v in d.groupby("family").g_mu.min().items() if k in keys}
    tbl = G.d_eff_table(info, fams)
    gb = {k: 1 / v["d_eff"] for k, v in tbl.items()}
    conv = MS._dummy_conv(info["conv"].lattice.matrix.tolist())
    res = MS.scan_morphology_map(conv, fams, info["rotations"], info["crystal_system"], gam, gb)
    fav = res["favoured"]
    out[mof] = dict(gamma_liquid_water={keys[k]: round(v, 4) for k, v in gam.items()}, favoured=fav.get("habit"),
                    areas=fav.get("area_fractions"),
                    bfdh=res["bfdh"] and {k: res["bfdh"].get(k) for k in ("habit", "ratio_change_from_favoured_pct", "lower_face", "raise_face")},
                    n_classes=len(res["classes"]),
                    closest=[{k: c[k] for k in ("rank", "class_id", "min_ratio_change_pct", "lower_face", "raise_face", "map_fraction")}
                             for c in res["classes"][:8]])
json.dump(MS._clean(out), open(HERE / "spectrum_corrected_liquid_water.json", "w"), indent=1)
print(json.dumps(MS._clean({m: (o["favoured"], o["closest"][1]) for m, o in out.items()}), indent=1))
