"""Checks of the corrections in mofwulff.py / mofgnn.py (15 November 2026). Run: python tests_nb14.py"""
import os, sys, math, warnings
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import mofwulff as mw, mofgnn as G
ok = 0
def check(c, msg):
    global ok
    assert c, msg; ok += 1; print("PASS", msg)
# 1 gamma(dmu) = gamma_0K - n dmu / 2A, both through gamma_J_m2 and gamma_at_mu
E, N, eb, n, ew, A = -100.0, 10, -9.0, 4, -14.8, 50.0
g0 = mw.gamma_J_m2(E, N, eb, n, ew, A)
for mu in (0.0, -0.4809, -0.5695):
    g = mw.gamma_J_m2(E, N, eb, n, ew, A, dmu_water=mu)
    check(abs(g - (g0 - n * mu / (2 * A) * mw.EV_A2_TO_J_M2)) < 1e-12, f"gamma_J_m2 linear in dmu ({mu})")
    check(abs(mw.gamma_at_mu(dict(g=g0, n_water=n, area_A2=A), "g", mu) - g) < 1e-12, f"gamma_at_mu agrees ({mu})")
# 2 the water chemical potentials from the tables in the docstring
R = 8.314462618e-3; kj = 1 / 96.4853
dmu_gas = (9.904 - 298.15 * 0.188834) * kj
check(abs(dmu_gas - mw.WATER_DMU_EV["vapour_298K_1bar"]) < 1e-4, "vapour 298 K, 1 bar from JANAF")
check(abs(dmu_gas - 8.547 * kj - mw.WATER_DMU_EV["liquid_298K"]) < 1e-4, "liquid 298 K from CODATA")
check(abs(dmu_gas + R * 298.15 * math.log(0.5 * 0.03169) * kj - mw.WATER_DMU_EV["vapour_298K_RH50"]) < 1e-4, "50 % RH")
check(abs((9.904 + 3.452 - 400 * 0.198788) * kj - mw.WATER_DMU_EV["vapour_400K_1bar"]) < 1e-4, "vapour 400 K")
# 3 GNN labels: at_water_mu shifts, load_dataset drops <= 0
idx = pd.DataFrame(dict(mof=["a", "a", "b"], face=["{100}"] * 3, termination=[0, 1, 0], n_water=[4, 4, 0], area_A2=[50.0] * 3,
                        gamma_static_J_m2=[1.0, 1.0, 1.0], gamma_relaxed_J_m2=[-0.02, 0.1, 0.2], converged=[True] * 3, graph=["x", "y", "z"]))
sh = G.at_water_mu(idx, -0.5695)
check(abs(sh["gamma_relaxed_J_m2"][0] - (-0.02 + 4 / 100 * 16.0218 * 0.5695)) < 1e-9 and sh["gamma_relaxed_J_m2"][2] == 0.2, "at_water_mu")
import torch
G.torch.load = lambda p, weights_only=False: {}
lab, _ = G.load_dataset(idx)
check(len(lab) == 2 and (lab["y"] > 0).all(), "load_dataset drops gamma <= 0")
# 4 K12: no O bonded to C carries two H after healing (Mg-MOF-74 needs the CIF; skipped if absent)
cif = os.path.join(HERE, "..", "input_cifs", "MgMOF-74.cif")
if os.path.exists(cif):
    info = mw.standardize(cif, 0.1, "majority")
    bad = 0
    for f in mw.face_families(info["conv"], info["rotations"], 1, 4):
        for m in mw.block_slabs(info["conv"], info["prim"], f["rep"], 15.0, 15.0, 0.3):
            m["miss"], m["broken"] = mw.broken_bonds(m)
            st, nw, status = mw.heal(m, m["miss"])
            if st is None: continue
            for site in st:
                if site.specie.symbol != "O": continue
                nb = st.get_neighbors(site, 1.6)
                if sum(x.specie.symbol == "H" and x.nn_distance < 1.2 for x in nb) >= 2 and any(x.specie.symbol == "C" for x in nb):
                    bad += 1
    check(bad == 0, "K12: no C-OH2+ in any healed Mg-MOF-74 slab")
    b = mw.summarize_blocks(mw.building_blocks(info["prim"])[0])
    check(b["infinite_inorganic_unit"], "K2: the Mg-O rod is one infinite inorganic unit")
print(ok, "checks passed")
