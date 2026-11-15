"""K12 prevalence: in how many healed slabs of the notebook does an O bonded to C carry two H (C-OH2+)?

Run:  python k12_count.py <static run dir> [<static run dir> ...] <out.json>
Reads every *_unrelaxed.cif written by the notebook's own module (slabs identical to the notebook's)."""
import sys, os, glob, json, collections
from pymatgen.core import Structure
dirs, out = sys.argv[1:-1], sys.argv[-1]
res = collections.OrderedDict()
for d in dirs:
    for mofdir in sorted(glob.glob(os.path.join(d, "structures", "*"))):
        mof = os.path.basename(mofdir)
        for p in sorted(glob.glob(os.path.join(mofdir, "slab_*_water_*_unrelaxed.cif"))):
            s = Structure.from_file(p)
            bad = 0
            for site in s:
                if site.specie.symbol != "O":
                    continue
                nb = s.get_neighbors(site, 1.6)
                nH = sum(1 for n in nb if n.specie.symbol == "H" and n.nn_distance < 1.2)
                nC = sum(1 for n in nb if n.specie.symbol == "C")
                if nH >= 2 and nC:
                    bad += 1
            r = res.setdefault(mof, dict(slabs=0, slabs_with_C_OH2=0, groups=0))
            r["slabs"] += 1; r["groups"] += bad; r["slabs_with_C_OH2"] += bool(bad)
tot = dict(slabs=sum(r["slabs"] for r in res.values()), slabs_with_C_OH2=sum(r["slabs_with_C_OH2"] for r in res.values()),
           mofs_affected=sorted(m for m, r in res.items() if r["slabs_with_C_OH2"]))
json.dump(dict(script="k12_count.py", total=tot, per_mof=res), open(out, "w"), indent=1)
print(tot)
