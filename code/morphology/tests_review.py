"""Checks added in the 2026-10-14 review (hydrogen fix, CHGNet post-processing, bond-cost run).

  1. hybrid.atoms_for_energy keeps the hydrogens of ZIF-8 (whose symmetry is found only without
     them) and hybrid.uff_gammas then reproduces the Phase 4 energies, which were computed with H.
  2. The cleavage energy is an upper bound on every termination energy known exactly: for each
     slab that was symmetric as cut, gamma_cl(face) <= gamma(that termination) (Section ex-chgnet).
  3. Excluding fragmented slabs can only raise or keep a cleavage energy (a minimum over fewer slabs).
  4. run_bond_sensitivity at f = 1 reproduces Phase 4 exactly (same model, same faces).

Run:  python -I tests_review.py
"""
import os, sys, json, warnings
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); warnings.filterwarnings("ignore")
from mofmorph.structure import load
from mofmorph.hybrid import atoms_for_energy, uff_gammas

RES = os.path.join(HERE, "results")
CIF = os.path.join(HERE, "..", "..", "website")
fails = 0


def ok(cond, msg):
    global fails
    print(("PASS " if cond else "FAIL ") + msg)
    fails += 0 if cond else 1


# 1 -----------------------------------------------------------------------------------------
zif = os.path.join(CIF, "ZIF-8.cif")
c = load(zif, "ZIF-8"); at = atoms_for_energy(zif, c)
ok(not c.used_hydrogen and at.get_chemical_symbols().count("H") > 0,
   f"ZIF-8: symmetry found without H, energy cell still has {at.get_chemical_symbols().count('H')} H atoms")
_, _, _, g, _ = uff_gammas(zif, "ZIF-8", n_families=7, max_index=3, verbose=False)
p4 = json.load(open(os.path.join(RES, "phase4_results.json")))["ZIF-8"]["faces"]
dev = max(abs(g[k] - p4[k]["gamma"]) for k in g if k in p4)
ok(dev < 1e-4, f"ZIF-8: general pipeline equals Phase 4 on every shared face (max difference {dev:.1e} J/m2)")

# 2, 3 --------------------------------------------------------------------------------------
cc = json.load(open(os.path.join(RES, "chgnet_cleavage_results.json")))
n = 0
for m, v in cc.items():
    allf = v["all_slabs"]["faces_info"]
    for face, lst in v.get("symmetric_slab_gammas", {}).items():
        for s in lst:
            n += 1
            ok(allf[face]["gamma_cleavage_J_m2"] <= s["gamma_J_m2"] + 1e-6,
               f"{m} {face}: cleavage bound {allf[face]['gamma_cleavage_J_m2']:.3f} <= exact termination energy {s['gamma_J_m2']:.3f}")
    if "intact_only" in v:
        for face, x in v["intact_only"]["faces_info"].items():
            ok(x["gamma_cleavage_J_m2"] >= allf[face]["gamma_cleavage_J_m2"] - 1e-9,
               f"{m} {face}: dropping fragmented slabs does not lower the cleavage energy")
ok(n > 0, f"{n} exact termination energies checked against the bound")

# 4 -----------------------------------------------------------------------------------------
bs = json.load(open(os.path.join(RES, "bond_sensitivity.json")))
p4all = json.load(open(os.path.join(RES, "phase4_results.json")))
dev = max(abs(gv - p4all[m]["faces"][k]["gamma"]) for m in bs for k, gv in bs[m]["by_factor"]["1.0"]["gamma_J_m2"].items())
ok(dev < 1e-4, f"bond-cost run at f = 1 equals Phase 4 on all four MOFs (max difference {dev:.1e} J/m2)")
ok(bs["MOF-5"]["by_factor"]["1.0"]["shape"] == "cube", "Phase 4 MOF-5 shape is a cube at the flat bond cost")

print("\nALL PASS" if not fails else f"\n{fails} FAILED")
sys.exit(1 if fails else 0)
