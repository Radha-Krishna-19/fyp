"""What the water caps look like before and after relaxation: per O, number of H (< 1.2 A), Mg (< 2.4 A), C (< 1.6 A).
Classes: O-H on metal (cap OH-), C-O-H (protonated carboxylate/phenolate), H2O bound to metal, free H2O, other."""
import sys, collections
from pymatgen.core import Structure
def classify(s):
    out = collections.Counter(); hosts = collections.Counter()
    for i, site in enumerate(s):
        if site.specie.symbol != "O": continue
        nb = s.get_neighbors(site, 2.4)
        nH = sum(1 for n in nb if n.specie.symbol == "H" and n.nn_distance < 1.2)
        nM = sum(1 for n in nb if n.specie.is_metal and n.nn_distance < 2.4)
        nC = sum(1 for n in nb if n.specie.symbol == "C" and n.nn_distance < 1.6)
        key = ("H2O free" if nH == 2 and nM == 0 and nC == 0 else "H2O on metal" if nH == 2 and nM > 0 else
               "M-OH" if nH == 1 and nM > 0 and nC == 0 else "OH free" if nH == 1 and nM == 0 and nC == 0 else
               "C-O-H" if nH == 1 and nC else "C-O(-M)" if nC and nH == 0 else "O other" if nH == 0 else f"O with {nH} H")
        out[key] += 1
    for site in s:
        if site.specie.symbol != "H": continue
        nb = sorted(s.get_neighbors(site, 1.6), key=lambda n: n.nn_distance)
        hosts[nb[0].specie.symbol if nb else "none"] += 1
    return dict(out), dict(hosts)
if __name__ == "__main__":
    for p in sys.argv[1:]:
        s = Structure.from_file(p); print(p.split('/')[-1], classify(s))
