"""Cleavage-energy Wulff/hybrid shapes from the CHGNet (MorphoGraph-MOF) result folders.
Run:  python3 run_chgnet_cleavage.py      (reads data/chgnet_morphograph_runs/<MOF>_<date>/)

Two variants are computed for every MOF:
  all_slabs   - every stoichiometric, force-converged slab (the notebook's own filter);
  intact_only - additionally drops every slab that held a detached piece (H, O, CH, C2H2, CO2 ...)
                either as cut or after relaxation, using results/slab_pieces.json from slab_check.py.
A shape that changes between the two variants depends on unphysical broken-linker slabs.
It also records the exact termination energies given by the few slabs that were symmetric as cut.
Writes results/chgnet_cleavage_results.json"""
import os, sys, json, warnings
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); warnings.filterwarnings("ignore")
from mofmorph.chgnet_post import cleavage_energies, summary, symmetric_slab_gammas
from mofmorph.chgnet_runs import runs
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

pieces_path = os.path.join(HERE, "results", "slab_pieces.json")
PIECES = json.load(open(pieces_path)) if os.path.exists(pieces_path) else {}
if not PIECES:
    print("results/slab_pieces.json missing: run slab_check.py first; only all_slabs is computed.")

out = {}
for run in runs():
    name, folder = run.mof, run.path
    fragmented = {(x["miller"], x["term"]) for x in PIECES.get(name, []) if x["small_initial"] or x["small_relaxed"]}
    variants = {"all_slabs": None}
    if name in PIECES:
        variants["intact_only"] = fragmented
    try:
        out[name] = {}
        for vname, excl in variants.items():
            res = cleavage_energies(folder, exclude=excl)
            out[name][vname] = summary(res)
            out[name][vname]["n_excluded_fragmented"] = len(excl or ())
            out[name][vname]["working_cell"] = os.path.relpath(res["working_cell"], REPO).replace(os.sep, "/")
            print(f"{name} [{vname}] {res['spacegroup']} {res['n_slabs_used']} slabs ->",
                  {k: v["gamma_cleavage_J_m2"] for k, v in res["faces_info"].items()})
            for w, v in out[name][vname]["shapes"].items():
                print("   w", w, v["name"], v["faces"])
        # exact termination energies from slabs symmetric as cut (see symmetric_slab_gammas)
        out[name]["symmetric_slab_gammas"] = {k: [dict(gamma_J_m2=g, miller=m, termination=t, intact=(m, t) not in fragmented)
                                                  for g, m, t in v] for k, v in symmetric_slab_gammas(folder).items()}
        print("   exact gamma from symmetric slabs:", {k: v[0]["gamma_J_m2"] for k, v in out[name]["symmetric_slab_gammas"].items()})
    except Exception as e:
        out.pop(name, None)
        print(name, "- no usable slab energies (this run produced none; see HANDOFF):", e)
json.dump(out, open(os.path.join(HERE, "results", "chgnet_cleavage_results.json"), "w"), indent=1)
