"""Connected pieces of each relaxed slab (bonds: metal-O/N <=2.5, organic as LINKER_BONDS), 2D periodic."""
import sys, glob, json, warnings, numpy as np, networkx as nx
warnings.filterwarnings("ignore")
from collections import Counter
from pymatgen.core import Structure
from chgnet_wulff import LINKER_BONDS
MET = {"Zn","Cu","Zr","Mg","Co"}
def bonded(a,b,d):
    if a in MET or b in MET: return (a in ("O","N") or b in ("O","N")) and d<=2.5
    r = LINKER_BONDS.get((a,b), LINKER_BONDS.get((b,a)))
    return r is not None and d<=r
for f in sorted(glob.glob(sys.argv[1])):
    s = Structure.from_file(f); G = nx.Graph(); G.add_nodes_from(range(len(s)))
    for i, nbs in enumerate(s.get_all_neighbors(2.6)):
        for n in nbs:
            if bonded(s[i].specie.symbol, n.specie.symbol, n.nn_distance): G.add_edge(i, n.index)
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    z = s.cart_coords[:,2]
    desc = [f"{len(c)} atoms {dict(Counter(s[i].specie.symbol for i in c))} z={z[list(c)].mean():.1f}" for c in comps[:6]]
    print(f"{f.split('/')[-1]}: {len(comps)} pieces, slab z {z.min():.1f}-{z.max():.1f}"); [print("    ", d) for d in desc]
