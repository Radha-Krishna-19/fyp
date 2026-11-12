"""Which bonds does each slab break? Coordination deficit per element vs bulk, per surface area."""
import sys, warnings, numpy as np
warnings.filterwarnings("ignore")
from collections import Counter
from chgnet_wulff import load_conventional
# Organic bond lengths (A) treated as linker bonds; the same table as code/morphology/slab_options_check.py.
LINKER_BONDS = {("C", "C"): 1.75, ("C", "H"): 1.25, ("C", "O"): 1.6, ("C", "N"): 1.6,
                ("N", "N"): 1.6, ("N", "H"): 1.2, ("O", "H"): 1.2}
from pymatgen.core.surface import SlabGenerator
CUT = {("Zn","O"):2.3,("Cu","O"):2.3,("Zr","O"):2.5,("Zn","N"):2.3}
CUT.update(LINKER_BONDS)
def cutoff(a,b): return CUT.get((a,b), CUT.get((b,a)))
def coord(struct, pbc_xy_only):
    nb = struct.get_all_neighbors(2.6)
    out=[]
    for i,site in enumerate(struct):
        c=Counter()
        for n in nb[i]:
            r=cutoff(site.specie.symbol, n.specie.symbol)
            if r and n.nn_distance<=r: c[n.specie.symbol]+=1
        out.append(c)
    return out
cif, faces = sys.argv[1], sys.argv[2:]
raw, conv, prim, sg = load_conventional(cif, 0.1)
bulkc = coord(conv, False)
ref = {}
for s,c in zip(conv, bulkc): ref.setdefault(s.specie.symbol, c)
for f in faces:
    hkl = tuple(int(x) for x in f)
    gen = SlabGenerator(conv, hkl, 15, 15, center_slab=True, primitive=True)
    for allow in (0, 2, 6):
        slabs = gen.get_slabs(bonds=LINKER_BONDS, max_broken_bonds=allow, symmetrize=False, tol=0.1)
        if slabs: break
    print(f"== {hkl}: {len(slabs)} slabs (max linker bonds broken allowed = {allow})")
    for k,sl in enumerate(slabs):
        A = np.linalg.norm(np.cross(sl.lattice.matrix[0], sl.lattice.matrix[1]))
        cc = coord(sl, True); deficit=Counter()
        for s,c in zip(sl,cc):
            for el,nref in ref[s.specie.symbol].items():
                d = nref - c[el]
                if d>0: deficit[f"{s.specie.symbol}-{el}"]+=d
        print(f"   term {k}: {len(sl)} atoms, A={A:.0f} A2, broken bond-ends per 100 A2 (both faces): " +
              ", ".join(f"{k2} {v*100/A:.2f}" for k2,v in sorted(deficit.items())))
