import sys, numpy as np; sys.path.insert(0, sys.argv[1]); import mofwulff as mw
from pymatgen.core import Structure
info = mw.standardize(sys.argv[2], 0.1, "majority")
pr = Structure.from_file(sys.argv[3])
print("relaxed prim", len(pr), pr.lattice.abc, pr.lattice.angles, "| orig prim", info["prim"].lattice.abc, info["prim"].lattice.angles)
dm = pr.distance_matrix; np.fill_diagonal(dm, 9); print("relaxed prim min dist", dm.min().round(3))
for src, P in (("orig", info["prim"]), ("relaxed", pr)):
    for m in mw.block_slabs(info["conv"], P, (1, 1, 1), 15, 15, 0.3):
        miss, tot = mw.broken_bonds(m); st, nw, status = mw.heal(m, miss)
        d = st.distance_matrix; np.fill_diagonal(d, 9)
        print(src, "z0", m["z0"], "atoms", len(st), "lattice", np.round(st.lattice.abc, 2), np.round(st.lattice.angles, 1), "min dist", d.min().round(3), "pairs<0.8", int((d < 0.8).sum() / 2), status, tot)
print("conv matrix\n", np.round(info["conv"].lattice.matrix, 3))
print("orig prim matrix\n", np.round(info["prim"].lattice.matrix, 3))
print("relaxed prim matrix (after CIF round trip)\n", np.round(pr.lattice.matrix, 3))
for fam in [(1, 0, 0), (1, 1, 0), (1, 1, 1)]:
    print(fam, "orig ->", mw.primitive_miller(info["conv"], info["prim"], fam), " relaxed ->", mw.primitive_miller(info["conv"], pr, fam))
