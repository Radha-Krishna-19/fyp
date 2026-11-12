"""Step 10 baseline: predict the dominant crystal face of a cubic MOF from MOF + additive,
evaluated leave-one-source-out (no paper is ever in its own training set).

Target: dominant face family of the reported shape:
  {100}: cube, truncated_cube, cube_truncated_edges, cuboctahedron ({100} is 63 % of its area)
  {111}: truncated_octahedron, octahedron
  {110}: rhombic_dodecahedron, truncated_rhombic_dodecahedron
Records with shapes outside the cubic map (plate, rod, irregular, other, sphere, needle,
intergrown, bipyramid, spindle) are counted but not predicted.

Additive categories are assigned by a fixed text rule (ADDITIVE_RULES), written before any model
was scored and printed in the output so it can be checked.
Models
  M0  global majority face (training sources)
  M1  majority face per MOF (training sources; M0 if the MOF is unseen)
  M2  structure only: the largest face of a computed Wulff shape, ignoring conditions
  M3  M2 for additive-free records; for records with an additive, the face that this additive
      category produced most often in the OTHER sources (any MOF); M2 if the category is unseen
"""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
REPO_ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..', '..'))
LAB_CSV = _os.path.join(REPO_ROOT, 'data', 'experimental_morphology', 'dataset', 'experimental_morphology.csv')
import re, json, sys
from collections import Counter, defaultdict
import numpy as np, pandas as pd

CSV = sys.argv[1] if len(sys.argv) > 1 else LAB_CSV
DOM = {"cube": "100", "truncated_cube": "100", "cube_truncated_edges": "100", "cuboctahedron": "100",
       "truncated_octahedron": "111", "octahedron": "111",
       "rhombic_dodecahedron": "110", "truncated_rhombic_dodecahedron": "110"}
CUBIC_MOFS = {"MOF-5", "HKUST-1", "UiO-66", "UiO-66-NH2", "ZIF-8", "ZIF-67", "IRMOF-3", "IRMOF-8", "SNU-70", "Zn4O(FMA)3"}
# structure-only predictions (largest face). From the project's UFF surface-energy Wulff (Phase 4,
# code/morphology/results/phase4_results.json) for the four MOFs it covers; IRMOF-3, IRMOF-8, SNU-70 and
# Zn4O(FMA)3 are pcu Zn4O frameworks like MOF-5 and take the MOF-5 prediction; UiO-66-NH2 takes UiO-66's;
# ZIF-67 (Co analogue of ZIF-8) takes ZIF-8's. These analogue choices are stated, not computed.
UFF = {"MOF-5": "100", "HKUST-1": "111", "UiO-66": "111", "ZIF-8": "110"}
ANALOGUE = {"IRMOF-3": "MOF-5", "IRMOF-8": "MOF-5", "SNU-70": "MOF-5", "Zn4O(FMA)3": "MOF-5",
            "UiO-66-NH2": "UiO-66", "ZIF-67": "ZIF-8"}
ADDITIVE_RULES = [  # (category, regex on the additive text, case-insensitive); first match wins
    ("none", r"^\s*$|^none|^nan$|lowest \(or none\)"),
    ("C3_tricarboxylate", r"btb|h3btb"),
    ("bent_dicarboxylate_or_terphenyl", r"terphenyl|quaterphenyl|biphenyl-3,4|^a6 or a7"),
    ("cationic_surfactant", r"ctab"),
    ("anionic_surfactant", r"sds|dodecyl sulfate|sdbs"),
    ("inorganic_salt", r"inorganic salt|nano3|nacl"),
    ("base_or_buffer", r"formate|tris|pyridine|sodium acetate"),
    ("monocarboxylic_acid_modulator", r"acetic|benzoic|formic|lauric|dodecanoic|chloroacetic|citric|hbr|hcl|oxalic|malonic|poly\(acrylic"),
]


def additive_category(a):
    s = "" if pd.isna(a) else str(a).lower()
    for cat, rx in ADDITIVE_RULES:
        if re.search(rx, s):
            return cat
    return "other_additive"


d = pd.read_csv(CSV)
d = d[d.mof.isin(CUBIC_MOFS)].copy()
d["addcat"] = [("none" if re.search(r"or none", str(am)) else additive_category(a)) for a, am in zip(d.additive, d.additive_amount)]
d["face"] = d.morphology.map(DOM)
n_all = len(d); on = d[d.face.notna()].copy()
print(f"cubic-MOF records: {n_all}; with an on-map shape: {len(on)}; off-map shapes:",
      dict(Counter(d[d.face.isna()].morphology)))
print("additive categories (records on map):", dict(Counter(on.addcat)))
print("assignment check:", sorted({(c, str(a)[:40]) for c, a in zip(on.addcat, on.additive)})[:40])


def struct_pred(m):
    return UFF.get(m, UFF.get(ANALOGUE.get(m, ""), None))


rows = []
for src in sorted(on.source_id.unique()):
    te, tr = on[on.source_id == src], on[on.source_id != src]
    glob = Counter(tr.face).most_common(1)[0][0]
    per_mof = {m: Counter(g.face).most_common(1)[0][0] for m, g in tr.groupby("mof")}
    cat_face = {c: Counter(g.face).most_common(1)[0][0] for c, g in tr[tr.addcat != "none"].groupby("addcat")}
    for _, r in te.iterrows():
        m2 = struct_pred(r.mof) or per_mof.get(r.mof, glob)
        m3 = m2 if r.addcat == "none" else cat_face.get(r.addcat, m2)
        rows.append(dict(record=r.record_id, source=src, mof=r.mof, cat=r.addcat, truth=r.face,
                         M0=glob, M1=per_mof.get(r.mof, glob), M2=m2, M3=m3))
P = pd.DataFrame(rows)
rng = np.random.default_rng(0); srcs = P.source.unique()
out = {}
for m in ["M0", "M1", "M2", "M3"]:
    acc = float((P[m] == P.truth).mean())
    boot = []
    for _ in range(2000):   # bootstrap over sources (records of one paper are not independent)
        pick = rng.choice(srcs, len(srcs))
        sub = pd.concat([P[P.source == s] for s in pick])
        boot.append((sub[m] == sub.truth).mean())
    lo, hi = np.percentile(boot, [2.5, 97.5])
    sub_free = P[P.cat == "none"]; sub_add = P[P.cat != "none"]
    out[m] = dict(accuracy=round(acc, 3), ci95=[round(lo, 3), round(hi, 3)], n=len(P),
                  acc_additive_free=round(float((sub_free[m] == sub_free.truth).mean()), 3), n_free=len(sub_free),
                  acc_with_additive=round(float((sub_add[m] == sub_add.truth).mean()), 3), n_add=len(sub_add))
    print(m, out[m])
print("\nwhich face each additive category produced (all sources):")
tab = pd.crosstab(on.addcat, on.face); print(tab.to_string())
P.to_csv(_os.path.join(HERE, "condition_model_predictions.csv"), index=False)
json.dump(dict(models=out, n_sources=int(len(srcs)), category_face_table=tab.to_dict(),
               additive_rules=ADDITIVE_RULES, n_cubic_records=n_all, n_on_map=len(on)),
          open(_os.path.join(HERE, "condition_model_results.json"), "w"), indent=1)
