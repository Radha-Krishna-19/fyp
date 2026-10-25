"""Slabs built from whole building blocks (metal clusters and linkers), never cutting either.

pymatgen's SlabGenerator makes flat cuts. In UiO-66 every flat {100} cut slices a
Zr6O4(OH)4 cluster, and a metal-cluster Zr-O bond cannot be told from a carboxylate Zr-O
bond by element alone. Here the crystal is first split into building blocks with the same
rule the project uses for its graphs (metal-oxo decomposition):
    node   = metal atoms + O/N/H that bond only to metal (oxo, hydroxo), plus metal-metal bonds
    linker = connected organic piece (bonds in LINKER_BONDS)
Bonds between a metal and a ligand O/N belonging to a linker are the only ones ever cut.

Slab construction for a conventional Miller index (hkl):
  1. Convert to the primitive cell, take pymatgen's oriented unit cell (a, b in the plane).
  2. h = height of that cell along the plane normal = true lattice repeat along the normal.
  3. A block is kept if its centroid height lies in [z0, z0 + n*h). Because every block
     type repeats with period h along the normal, the window holds exactly n copies of each,
     so the slab is stoichiometric for any z0.
  4. Different terminations = different z0, one just below each distinct centroid level.
"""
from math import gcd

import networkx as nx
import numpy as np
from pymatgen.core import Lattice, Structure
from pymatgen.core.surface import SlabGenerator

METALS = {"Zn", "Cu", "Zr", "Mg", "Co", "Ni", "Fe", "Al", "Cr", "Hf"}
ORGANIC = {("C", "C"): 1.65, ("C", "O"): 1.50, ("C", "H"): 1.20, ("C", "N"): 1.60,
           ("N", "H"): 1.15, ("O", "H"): 1.10, ("N", "N"): 1.50}
M_X, M_M = 2.5, 2.9


def _organic_cut(a, b):
    return ORGANIC.get((a, b), ORGANIC.get((b, a)))


def primitive_miller(conv, prim, hkl):
    """Conventional (hkl) -> integer Miller indices of the same plane in the primitive cell."""
    g = np.array(hkl, float) @ conv.lattice.reciprocal_lattice_crystallographic.matrix
    hp = prim.lattice.matrix @ g
    hp = np.round(hp / np.abs(hp[np.abs(hp) > 1e-6]).min(), 6)
    # scale to smallest integers
    for m in range(1, 13):
        v = hp * m
        if np.allclose(v, np.round(v), atol=1e-4):
            v = np.round(v).astype(int)
            d = gcd(gcd(abs(v[0]), abs(v[1])), abs(v[2]))
            return tuple(int(x) for x in v // d)
    raise ValueError(f"cannot convert {hkl}")


def building_blocks(s):
    """Connected building blocks of a periodic structure, with unwrapped cartesian coords."""
    sym = [x.specie.symbol for x in s]
    nbs = s.get_all_neighbors(3.0)
    # ligand O/N = bonded to C (carboxylate O, imidazolate N); these join linkers, not nodes
    lig = {i for i in range(len(s)) if sym[i] in ("O", "N")
           and any(n.specie.symbol == "C" and n.nn_distance <= 1.6 for n in nbs[i])}
    G = nx.Graph()
    G.add_nodes_from(range(len(s)))
    for i in range(len(s)):
        for n in nbs[i]:
            j, a, b, d = n.index, sym[i], sym[n.index], n.nn_distance
            img = tuple(int(x) for x in n.image)
            ok = False
            if a in METALS and b in METALS:
                ok = d <= M_M
            elif a in METALS or b in METALS:
                other = j if a in METALS else i
                ok = d <= M_X and sym[other] in ("O", "N") and other not in lig
            else:
                r = _organic_cut(a, b)
                ok = r is not None and d <= r
            if ok:
                G.add_edge(i, j)
                G.edges[i, j].setdefault("img", {})[(i, j)] = img
                G.edges[i, j]["img"][(j, i)] = tuple(-x for x in img)
    blocks = []
    frac = s.frac_coords
    for comp in nx.connected_components(G):
        comp = list(comp)
        root = comp[0]
        off = {root: np.zeros(3)}
        stack = [root]
        while stack:
            u = stack.pop()
            for v in G.neighbors(u):
                if v not in off:
                    off[v] = off[u] + np.array(G.edges[u, v]["img"][(u, v)])
                    stack.append(v)
        f = np.array([frac[i] + off[i] for i in comp])
        cart = s.lattice.get_cartesian_coords(f)
        kind = "node" if any(sym[i] in METALS for i in comp) else "linker"
        blocks.append({"atoms": comp, "species": [sym[i] for i in comp], "cart": cart,
                       "centroid": cart.mean(axis=0), "kind": kind})
    return blocks


def block_slabs(conv, prim, hkl, min_thickness=15.0, vacuum=15.0, level_tol=0.3):
    """All distinct block-intact stoichiometric slabs for conventional (hkl)."""
    hp = primitive_miller(conv, prim, hkl)
    ouc = SlabGenerator(prim, hp, 10, 10).oriented_unit_cell
    a, b, c = ouc.lattice.matrix
    nrm = np.cross(a, b)
    nrm /= np.linalg.norm(nrm)
    h = float(np.dot(c, nrm))
    if h < 0:
        c, h = -c, -h
    n_rep = int(np.ceil(min_thickness / h))
    T = n_rep * h
    blocks = building_blocks(ouc)
    heights = np.array([np.dot(bl["centroid"], nrm) for bl in blocks]) % h
    levels = np.sort(heights)
    distinct = [levels[0]]
    for z in levels[1:]:
        if z - distinct[-1] > level_tol:
            distinct.append(z)
    if len(distinct) > 1 and (distinct[0] + h - distinct[-1]) <= level_tol:
        distinct.pop()
    out = []
    for z0 in [z - level_tol / 2 for z in distinct]:
        species, coords = [], []
        for bl in blocks:
            zc = float(np.dot(bl["centroid"], nrm))
            k_lo = int(np.ceil((z0 - zc) / h))
            for k in range(k_lo, k_lo + n_rep):
                shift = k * c
                species += bl["species"]
                coords += list(bl["cart"] + shift)
        coords = np.array(coords)
        z = coords @ nrm
        coords = coords - np.outer(z.min() - vacuum / 2, nrm)
        extent = float(z.max() - z.min())
        lat = Lattice([a, b, nrm * (extent + vacuum)])
        st = Structure(lat, species, coords, coords_are_cartesian=True)
        out.append({"slab": st, "z0": round(float(z0), 3), "n_layers": n_rep,
                    "thickness_A": round(extent, 2), "repeat_A": round(h, 3),
                    "primitive_hkl": hp})
    return out


def is_mirror_symmetric(st, symprec=0.3):
    """True if some symmetry of the slab maps its top face onto its bottom face."""
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    try:
        ops = SpacegroupAnalyzer(st, symprec=symprec).get_symmetry_operations(cartesian=True)
    except Exception:
        return False
    nrm = st.lattice.matrix[2] / np.linalg.norm(st.lattice.matrix[2])
    return any(np.dot(op.rotation_matrix @ nrm, nrm) < -0.99 for op in ops)
