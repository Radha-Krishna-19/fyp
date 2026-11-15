"""K2 check: building blocks of 11 MOFs with and without joining metals that share a linker donor, and the
static (unrelaxed) shape of Mg-MOF-74 from the corrected module.

Run:  python k2_check.py <cif dir> <static run dir of the corrected module, containing Mg-MOF-74> <out.json>
(the static run: python run_static.py <cif dir> <dir> Mg-MOF-74). Static energies only: indicative, not a result."""
import sys, os, json, warnings
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); warnings.filterwarnings("ignore")
import pandas as pd
import mofwulff as mw, mofgnn as G
cifs, run, out = sys.argv[1:4]
res = dict(script="k2_check.py", blocks={}, mg_mof_74_static={})
for c in ['MgMOF-74', 'Ni-DOBDC', 'Cu-BTC', 'ZIF-8', 'UIO-66', 'IRMOF-1', 'ZnBDC', 'Cd3BTB2', 'MIL-47', 'MOF-70', 'CoBDP']:
    info = mw.standardize(os.path.join(cifs, c + ".cif"), 0.1, "majority")
    res["blocks"][c] = {("with_K2" if f else "notebook"): mw.summarize_blocks(mw.building_blocks(info["prim"], join_shared_donors=f)[0])
                        for f in (False, True)}
meta = G.load_meta(run, "Mg-MOF-74")
recs = pd.read_csv(os.path.join(run, "static_Mg-MOF-74.csv"), dtype={"family": str}).to_dict("records")
for name, mu in [("0K_molecule", 0.0), ("liquid_298K", mw.WATER_DMU_EV["liquid_298K"])]:
    best = mw.choose_gamma(recs, "water", need_relaxed=False, dmu=mu)
    h, d, w = G.habit_from_gammas(meta, {k: b["gamma"] for k, b in best.items()})
    res["mg_mof_74_static"][name] = dict(gamma={b["face"]: round(b["gamma"], 4) for b in best.values()}, habit=h, main_face=d)
json.dump(res, open(out, "w"), indent=1, default=str)
print(json.dumps(res["mg_mof_74_static"], indent=1))
