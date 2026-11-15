"""MOF crystal habit from machine-learned surface energies (pipeline steps 1-8).

Step 1  standardize()        read CIF, disorder/overlap/guest policy, symmetry, conv + working cell
Step 2  building_blocks()    metal nodes vs organic linkers, unwrapped, periodic-node detection
Step 3  face_families()      symmetry-unique {hkl} families + distinct block terminations
Step 4  block_slabs()        whole-block, stoichiometric slabs (asserted), vacuum
Step 5  heal()               heterolytic H2O capping of every broken metal-ligand bond (H+ to ligand, OH- to metal)
Step 6  CHGNet energies      bulk relaxed at fixed cell; static screen of all terminations, relax lowest K
Step 7  validation helpers   independent-model (MACE-MP-0) re-scoring, CP2K PBE-D3 inputs, DFT comparison
Step 8  wulff()              Wulff polyhedron from true point-group symmetry, area fractions, habit name, 3D render

Every rule that discards or caps something is written in a docstring and logged in the outputs.
"""
import hashlib, itertools, json, math, re, time, warnings
from collections import Counter
from math import gcd
from pathlib import Path

import networkx as nx
import numpy as np
from pymatgen.core import Element, Lattice, Molecule, Structure
from pymatgen.core.surface import SlabGenerator
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

warnings.filterwarnings("ignore")
EV_A2_TO_J_M2 = 16.0218

# ----------------------------------------------------------------------------- bonding rules
# One set of rules, used by every step (blocks, slabs, healing, coordination counts).
ORGANIC = {("C", "C"): 1.65, ("C", "O"): 1.50, ("C", "H"): 1.20, ("C", "N"): 1.60, ("N", "H"): 1.15,
           ("O", "H"): 1.15, ("N", "N"): 1.50, ("C", "S"): 1.90, ("C", "F"): 1.45, ("C", "Cl"): 1.85,
           ("C", "Br"): 2.00, ("B", "O"): 1.60, ("B", "C"): 1.70, ("P", "O"): 1.70, ("S", "O"): 1.60}
DONORS = {"O", "N", "S", "F", "Cl"}       # atoms that can bind a metal
M_X = 2.55                                # metal-donor bond cutoff, A
M_M = 2.80                                # metal-metal bond cutoff, A (Cu2 paddlewheel 2.6; Mg...Mg in MOF-74 rods ~2.9 is not a bond)
OUT_REACH = 3.0                           # neighbour search radius, A


def is_metal(el):
    e = Element(el)
    return e.is_metal or el in {"Ge", "Sb"}  # Element.is_metal covers alkali..post-transition


def _org(a, b):
    return ORGANIC.get((a, b), ORGANIC.get((b, a)))


def bond_kind(a, b, d, lig_a=False, lig_b=False):
    """Classify a pair: 'org', 'MM', 'ML' (metal-ligand donor), 'MO' (metal-oxo/hydroxo/aqua donor) or None."""
    ma, mb = is_metal(a), is_metal(b)
    if ma and mb:
        return "MM" if d <= M_M else None
    if ma or mb:
        x, lx = (b, lig_b) if ma else (a, lig_a)
        if x in DONORS and d <= M_X:
            return "ML" if lx else "MO"
        return None
    r = _org(a, b)
    return "org" if r is not None and d <= r else None


def ligand_donors(s, nbs=None):
    """Indices of donor atoms bonded to C (carboxylate O, imidazolate N, ...): they belong to linkers."""
    nbs = nbs if nbs is not None else s.get_all_neighbors(OUT_REACH)
    sym = [x.specie.symbol for x in s]
    return {i for i in range(len(s)) if sym[i] in DONORS
            and any(n.specie.symbol == "C" and n.nn_distance <= _org(sym[i], "C") for n in nbs[i])}


def bond_counts(s, lig, nbs=None):
    """Per-site Counter of bond kinds. lig = set of ligand donor indices of s."""
    nbs = nbs if nbs is not None else s.get_all_neighbors(OUT_REACH)
    sym = [x.specie.symbol for x in s]
    out = []
    for i in range(len(s)):
        c = Counter()
        for n in nbs[i]:
            k = bond_kind(sym[i], sym[n.index], n.nn_distance, i in lig, n.index in lig)
            if k:
                c[k] += 1
        out.append(c)
    return out


# ----------------------------------------------------------------------------- step 1
def standardize(cif, symprec=0.1, disorder="majority", remove_guests=True, overlap_tol=0.6):
    """Read and clean a CIF.

    Disorder policy (documented, logged in notes):
      'reject'   : any partial occupancy -> error.
      'majority' : each disordered site keeps its highest-occupancy species; sites with total
                   occupancy < 0.5 are removed. Pairs of sites closer than overlap_tol (split
                   positions written as full occupancy) are merged, keeping the first.
    Guests: connected components with no metal and no bond to the framework (free solvent)
            are removed when remove_guests is True.
    Symmetry: tried on (a) full structure, (b) without H, (c) metals + C only. The highest
            space group found defines the point group used for face families. If (a) has it,
            conventional + primitive standard cells are used (slabs from the primitive cell).
            If only a skeleton has it (ordered H / ordered OH breaking symmetry in the CIF),
            the input cell is used as both cells, with the skeleton's operations.
    """
    notes = []
    s = Structure.from_file(cif)
    if not s.is_ordered:
        n_dis = sum(1 for site in s if not site.is_ordered)
        if disorder == "reject":
            raise ValueError(f"{n_dis} partially occupied sites; disorder policy is 'reject'")
        sp, fc, drop = [], [], 0
        for site in s:
            occ = site.species.num_atoms
            if occ < 0.5:
                drop += 1
                continue
            el = max(site.species.items(), key=lambda kv: kv[1])[0]
            sp.append(el.symbol if hasattr(el, "symbol") else str(el)); fc.append(site.frac_coords)
        s = Structure(s.lattice, sp, fc)
        notes.append(f"disorder: {n_dis} partial sites -> majority species, {drop} low-occupancy sites removed")
    # overlapping split sites
    dm = s.distance_matrix
    np.fill_diagonal(dm, 99)
    close = sorted({max(i, j) for i, j in zip(*np.where(dm < overlap_tol))})
    if close:
        s.remove_sites(close)
        notes.append(f"overlap: {len(close)} sites closer than {overlap_tol} A to another site removed")
    # free guests
    if remove_guests:
        nbs = s.get_all_neighbors(OUT_REACH)
        lig = ligand_donors(s, nbs)
        sym = [x.specie.symbol for x in s]
        G = nx.Graph(); G.add_nodes_from(range(len(s)))
        for i in range(len(s)):
            for n in nbs[i]:
                if bond_kind(sym[i], sym[n.index], n.nn_distance, i in lig, n.index in lig):
                    G.add_edge(i, n.index)
        guests = [c for c in nx.connected_components(G) if not any(is_metal(sym[i]) for i in c)]
        if guests:
            idx = sorted(i for c in guests for i in c)
            formulas = Counter(Structure(s.lattice, [sym[i] for i in c], [s[i].frac_coords for i in c])
                               .composition.reduced_formula for c in guests)
            s.remove_sites(idx)
            notes.append(f"guests removed: {dict(formulas)}")
    # symmetry
    def sg(st):
        try:
            a = SpacegroupAnalyzer(st, symprec=symprec)
            return a.get_space_group_number(), a
        except Exception:
            return 1, None
    full_n, full_a = sg(s)
    noH = s.copy(); noH.remove_species(["H"])
    mc = s.copy(); mc.remove_species([e for e in {x.specie.symbol for x in s} if not (is_metal(e) or e == "C")])
    cands = [("full", full_n, full_a, s), ("no_H", *sg(noH), noH), ("metal+C", *sg(mc), mc)]
    best = max(cands, key=lambda c: c[1])
    if best[0] == "full" or full_n == best[1]:
        conv = full_a.get_conventional_standard_structure()
        # primitive cell in the SAME cartesian frame as conv (needed for exact Miller conversion)
        prim = conv.get_primitive_structure(tolerance=0.25)
        if len(prim) != len(full_a.get_primitive_standard_structure()):
            prim = conv
            notes.append("primitive reduction in the conventional frame failed; conventional cell used for slabs")
        ops = SpacegroupAnalyzer(conv, symprec=symprec).get_symmetry_operations()
        sym_src, cs, sgsym = "full", full_a.get_crystal_system(), full_a.get_space_group_symbol()
    else:
        conv = prim = s
        ops = best[2].get_symmetry_operations()
        sym_src, cs, sgsym = best[0], best[2].get_crystal_system(), best[2].get_space_group_symbol()
        notes.append(f"symmetry: full structure is SG {full_n}; skeleton '{best[0]}' is {sgsym}; "
                     f"input cell used, skeleton point group used for face families")
    rots = []
    for op in ops:
        R = np.round(op.rotation_matrix).astype(int)
        if not any(np.array_equal(R, q) for q in rots):
            rots.append(R)
    # full operations (R, t) in the basis of conv, for the systematic-absence test of face_families (K7)
    sym_ops = [(np.round(op.rotation_matrix).astype(int), np.array(op.translation_vector, float)) for op in ops]
    return dict(structure=s, conv=conv, prim=prim, rotations=rots, ops=sym_ops, space_group=sgsym,
                symmetry_source=sym_src, crystal_system=cs, formula=s.composition.reduced_formula,
                n_atoms_conv=len(conv), n_atoms_prim=len(prim), notes=notes)


# ----------------------------------------------------------------------------- step 2
def building_blocks(s, join_shared_donors=True):
    """Split a periodic structure into building blocks.

    node   = metal atoms + donors bonded only to metals (oxo/hydroxo/aqua), joined by M-M and M-oxo bonds
    linker = connected organic piece (ORGANIC bonds), including its donor atoms
    Only 'ML' bonds (metal - ligand donor) are ever cut between blocks.
    A block that wraps onto itself through a lattice translation is an infinite (rod/sheet)
    inorganic unit; it is cut at the cell boundary and flagged (periodic_dirs, cartesian).
    """
    nbs = s.get_all_neighbors(OUT_REACH)
    lig = ligand_donors(s, nbs)
    sym = [x.specie.symbol for x in s]
    G = nx.MultiGraph(); G.add_nodes_from(range(len(s)))
    for i in range(len(s)):
        for n in nbs[i]:
            k = bond_kind(sym[i], sym[n.index], n.nn_distance, i in lig, n.index in lig)
            if k and k != "ML" and i <= n.index:
                G.add_edge(i, n.index, img=np.array(n.image, int))
    if join_shared_donors:
        # K2 (15 Nov 2026): two metals bonded to the same linker donor (a bridging phenolate or carboxylate O,
        # as along the Mg-O rod of Mg-MOF-74) belong to one inorganic unit. They are joined by a virtual
        # metal-metal edge; the donor stays in its linker, so only metal-donor bonds are still cut between blocks.
        for d in lig:
            ms = [(n.index, np.array(n.image, int)) for n in nbs[d]
                  if is_metal(n.specie.symbol) and bond_kind(sym[d], n.specie.symbol, n.nn_distance, True, False) == "ML"]
            for (a, ia), (b, ib) in itertools.combinations(ms, 2):
                if a == b and np.array_equal(ia, ib):
                    continue
                i, j, t = (a, b, ib - ia) if a <= b else (b, a, ia - ib)
                if i == j and not np.any(t):
                    continue
                G.add_edge(i, j, img=t)
    frac = s.frac_coords
    blocks = []
    for comp in nx.connected_components(G):
        comp = sorted(comp); root = comp[0]
        off = {root: np.zeros(3, int)}; stack = [root]
        while stack:
            u = stack.pop()
            for _, v, data in G.edges(u, data=True):
                img = data["img"] if u <= v else -data["img"]
                if u == v:
                    continue
                if v not in off:
                    off[v] = off[u] + img; stack.append(v)
        per = set()
        for u, v, data in G.subgraph(comp).edges(data=True):
            i, j = min(u, v), max(u, v)
            t = off[i] + data["img"] - off[j]
            if np.any(t):
                per.add(tuple(int(x) for x in t))
        f = np.array([frac[i] + off[i] for i in comp])
        cart = s.lattice.get_cartesian_coords(f)
        blocks.append(dict(atoms=comp, species=[sym[i] for i in comp], cart=cart, centroid=cart.mean(0),
                           kind="node" if any(is_metal(sym[i]) for i in comp) else "linker",
                           formula=Structure(s.lattice, [sym[i] for i in comp], f).composition.formula.replace(" ", ""),
                           periodic_dirs=[s.lattice.get_cartesian_coords(np.array(t)).tolist() for t in per]))
    return blocks, lig


def summarize_blocks(blocks):
    c = Counter((b["kind"], b["formula"]) for b in blocks)
    per = any(b["periodic_dirs"] for b in blocks)
    return {"blocks": {f"{k}:{f}": n for (k, f), n in c.items()}, "infinite_inorganic_unit": per}


# ----------------------------------------------------------------------------- step 3
def _reduce(v):
    v = np.array(v, int); g = gcd(gcd(abs(v[0]), abs(v[1])), abs(v[2]))
    return tuple(int(x) for x in v // g)


def face_families(conv, rotations, max_index=1, n_keep=6, faces=None, ops=None):
    """Symmetry-unique face families.

    Miller indices transform as h' = h R^-1 for each point operation R (fractional), plus
    inversion (h and -h are the two sides of one slab, so families follow the Laue class).
    All primitive hkl with |h|,|k|,|l| <= max_index are grouped; the n_keep families with the
    largest interplanar spacing d_hkl are kept (BFDH ranking; documented, not random).
    faces: optional explicit list of hkl, which overrides the enumeration.
    """
    Rinv = [np.round(np.linalg.inv(R)).astype(int) for R in rotations]
    def orbit(h):
        out = set()
        for Ri in Rinv:
            hp = tuple(int(x) for x in np.array(h) @ Ri)
            out.add(hp); out.add(tuple(-x for x in hp))
        return sorted(out)
    if faces:
        cand = [_reduce(h) for h in faces]
    else:
        rng = range(-max_index, max_index + 1)
        cand = [h for h in itertools.product(rng, rng, rng) if any(h) and _reduce(h) == h]
    fams, seen = [], set()
    for h in cand:
        if h in seen:
            continue
        orb = orbit(h); seen.update(orb)
        rep = max(orb)                      # canonical representative: lexicographically largest
        d = conv.lattice.d_hkl(rep)
        order = 1 if faces else absence_order(conv, rep, ops)
        fams.append(dict(rep=rep, members=orb, d_hkl=d, order=order, d_eff=d / order,
                         name="{" + "".join(map(str, rep)).replace("-", "̅") + "}",
                         key="".join(str(x) for x in rep).replace("-", "m")))
    # K7 (15 Nov 2026): rank by the effective spacing d_hkl / n (Donnay-Harker), where n is the first order
    # of the reflection that symmetry does not extinguish; ranking by d_hkl kept faces that centring or
    # screw axes forbid.
    fams.sort(key=lambda f: (-f["d_eff"], -f["d_hkl"]))
    return fams if faces else fams[:n_keep]


def absence_order(conv, hkl, ops=None, n_max=6, symprec=0.1):
    """Smallest n (1..n_max) for which the reflection n*(hkl) is not a systematic absence.
    Uses the space-group operations (R, t) of the cell (fractional, same basis as hkl): a reflection h is
    extinguished when some operation leaves it fixed (h R = h) while h.t is not an integer. This is exact
    and, unlike a structure factor of the file's atoms, not disturbed by small deviations of the atoms
    from their ideal positions."""
    if ops is None:
        ops = [(o.rotation_matrix, o.translation_vector)
               for o in SpacegroupAnalyzer(conv, symprec=symprec).get_symmetry_operations(cartesian=False)]
    for n in range(1, n_max + 1):
        h = n * np.array(hkl, float)
        extinct = any(np.allclose(h @ R, h, atol=1e-6) and abs((h @ t) - round(h @ t)) > 1e-3 for R, t in ops)
        if not extinct:
            return n
    return n_max


# ----------------------------------------------------------------------------- step 4
def primitive_miller(conv, prim, hkl):
    """Conventional (hkl) -> integer Miller indices of the same plane in the primitive cell."""
    if conv is prim:
        return tuple(hkl)
    g = np.array(hkl, float) @ conv.lattice.reciprocal_lattice_crystallographic.matrix
    hp = prim.lattice.matrix @ g
    hp = hp / np.abs(hp[np.abs(hp) > 1e-6]).min()
    for m in range(1, 25):
        v = hp * m
        if np.allclose(v, np.round(v), atol=1e-3):
            return _reduce(np.round(v).astype(int))
    raise ValueError(f"cannot convert {hkl} to the primitive cell")


def _surface_fingerprint(blocks_in_slab, z, top, bottom, depth=4.0):
    t = sorted(f for f, zc in blocks_in_slab if zc > top - depth)
    b = sorted(f for f, zc in blocks_in_slab if zc < bottom + depth)
    return tuple(sorted([tuple(t), tuple(b)]))


def block_slabs(conv, prim, hkl, min_thickness=15.0, vacuum=15.0, level_tol=0.3):
    """All distinct whole-block slabs for conventional (hkl).

    Oriented unit cell (OUC) of the working cell; h = lattice repeat along the normal.
    A block copy is kept if its centroid height lies in [z0, z0 + n*h); every block type repeats
    with period h, so the slab holds exactly n copies of the OUC -> stoichiometric for any z0
    (asserted below). Terminations: one z0 just below each distinct centroid level (levels closer
    than level_tol merged). Duplicate terminations (same block formulas within 4 A of both
    surfaces) are removed.
    Returns list of dicts with slab, orig (OUC index per slab atom), OUC, metadata.
    """
    # oriented unit cell from the primitive and from the conventional cell; the smaller one is used
    opts = [(conv, tuple(hkl))]
    try:
        opts.append((prim, primitive_miller(conv, prim, hkl)))
    except ValueError:
        pass
    cells = [(SlabGenerator(cell, h_, 10, 10, primitive=False).oriented_unit_cell, h_) for cell, h_ in opts]
    # K3 fix (10 Nov 2026): on a tie prefer the working (relaxed) cell, so slab and bulk energies come
    # from the same geometry.
    ouc, hp = min(cells[::-1], key=lambda x: len(x[0]))
    a, b, c = ouc.lattice.matrix
    nrm = np.cross(a, b); nrm /= np.linalg.norm(nrm)
    h = float(np.dot(c, nrm))
    if h < 0:
        c, h = -c, -h
    n_rep = max(1, int(np.ceil(min_thickness / h)))
    blocks, lig = building_blocks(ouc)
    cuts_rod = any(abs(np.dot(np.array(d) / np.linalg.norm(d), nrm)) > 0.05
                   for bl in blocks for d in bl["periodic_dirs"])
    heights = np.sort(np.array([np.dot(bl["centroid"], nrm) for bl in blocks]) % h)
    distinct = [heights[0]]
    for zz in heights[1:]:
        if zz - distinct[-1] > level_tol:
            distinct.append(zz)
    if len(distinct) > 1 and distinct[0] + h - distinct[-1] <= level_tol:
        distinct.pop()
    out, prints = [], set()
    for z0 in [zz - level_tol / 2 for zz in distinct]:
        species, coords, orig, inslab = [], [], [], []
        for bl in blocks:
            zc = float(np.dot(bl["centroid"], nrm))
            k_lo = int(np.ceil((z0 - zc) / h))
            for k in range(k_lo, k_lo + n_rep):
                species += bl["species"]; coords += list(bl["cart"] + k * c); orig += bl["atoms"]
                inslab.append((bl["formula"], zc + k * h))
        coords = np.array(coords); zs = coords @ nrm
        top, bot = zs.max(), zs.min()
        fp = _surface_fingerprint(inslab, zs, top, bot)
        if fp in prints:
            continue
        prints.add(fp)
        coords = coords - np.outer(np.full(len(coords), bot - vacuum / 2), nrm)
        lat = Lattice([a, b, nrm * (top - bot + vacuum)])
        st = Structure(lat, species, coords, coords_are_cartesian=True)
        # Step 4 check: stoichiometry
        if len(st) != n_rep * len(ouc) or st.composition.reduced_composition != ouc.composition.reduced_composition:
            raise AssertionError(f"slab {hkl} z0={z0:.2f} is not stoichiometric")
        out.append(dict(slab=st, orig=orig, ouc=ouc, ouc_lig=lig, z0=round(float(z0), 3), n_layers=n_rep,
                        n_bulk_units=n_rep, thickness_A=round(float(top - bot), 2), repeat_A=round(h, 3),
                        primitive_hkl=hp, cuts_infinite_unit=cuts_rod,
                        area_A2=float(np.linalg.norm(np.cross(a, b)))))
    return out


def broken_bonds(sl):
    """Compare every slab atom's bonds with its bulk (OUC) image. Returns per-atom missing Counter."""
    ouc, st, orig = sl["ouc"], sl["slab"], sl["orig"]
    bulk = bond_counts(ouc, sl["ouc_lig"])
    lig_slab = {i for i, o in enumerate(orig) if o in sl["ouc_lig"]}
    now = bond_counts(st, lig_slab)
    miss = []
    for i, o in enumerate(orig):
        m = bulk[o] - now[i]                          # Counter subtraction keeps positives
        extra = now[i] - bulk[o]
        if extra:
            m["_extra"] = sum(extra.values())         # new contacts across the cut (should be 0)
        miss.append(m)
    tot = Counter()
    for m in miss:
        tot.update(m)
    return miss, dict(tot)


# ----------------------------------------------------------------------------- step 5
def _fib_sphere(n=96):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n); th = np.pi * (1 + 5 ** 0.5) * i
    return np.c_[np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)]


DIRS = _fib_sphere()


def _best_dirs(center, occupied, k, length, others, min_clear):
    """k directions from center, each as far as possible (angle) from occupied directions,
    with the new atom at least min_clear from all other atoms."""
    chosen = []
    occ = [o / np.linalg.norm(o) for o in occupied if np.linalg.norm(o) > 1e-6]
    for _ in range(k):
        best, bscore = None, -9
        for d in DIRS:
            cos = max([np.dot(d, o) for o in occ + chosen] or [-1])
            p = center + length * d
            clear = np.min(np.linalg.norm(others - p, axis=1)) if len(others) else 9
            score = -cos + (0 if clear >= min_clear else -5)
            if score > bscore:
                best, bscore = d, score
        chosen.append(best)
    return chosen


def heal(sl, miss, ML_only=True, one_proton_per_donor=True):
    """Heal broken metal-donor bonds with heterolytic water (documented chemistry):
         each missing bond on a metal          -> +OH  (O at 2.0 A, H at 0.97 A)
         each missing bond on a donor atom     -> +H   (0.98 A)
    n_water = number of broken bonds. Balanced iff metal-side and donor-side counts match.
    Slabs with broken organic or M-M bonds, or unbalanced counts, are rejected.

    one_proton_per_donor (added 15 Nov 2026): a donor atom that loses two or more metal bonds (a bridging
    phenolate or carboxylate O, as in MOF-74) used to receive one H per lost bond, i.e. an O bonded to C and
    two H (C-OH2+), which is not a stable group. Now it receives at most one H in total (counting any H it
    already had), and every surplus proton goes to the nearest metal-side OH cap, which becomes a water
    molecule bound to the metal (O at 2.1 A, H-O-H 104.5 degrees, both H pointing away from the metal).
    The atoms added, the charge balance and n_water are unchanged; only where the protons sit changes.
    Returns (structure or None, n_water, status)."""
    st = sl["slab"]
    tot = Counter()
    for m in miss:
        tot.update(m)
    if tot.get("org", 0) or tot.get("MM", 0):
        return None, 0, "rejected: organic or metal-metal bond broken"
    if tot.get("_extra", 0):
        return None, 0, "rejected: new contacts across the cut"
    m_side = sum(m.get("ML", 0) + m.get("MO", 0) for i, m in enumerate(miss) if is_metal(st[i].specie.symbol))
    x_side = sum(m.get("ML", 0) + m.get("MO", 0) for i, m in enumerate(miss) if not is_metal(st[i].specie.symbol))
    if m_side != x_side:
        return None, 0, f"rejected: unbalanced ({m_side} metal-side vs {x_side} donor-side)"
    if m_side == 0:
        return st.copy(), 0, "intact (nothing to heal)"
    species = [x.specie.symbol for x in st]
    coords = [x.coords.copy() for x in st]
    nbs = st.get_all_neighbors(2.6)
    caps = []                                    # metal-side caps: [metal index, unit direction, O index, H index]
    surplus = []                                 # donor atoms whose extra protons must move to a cap
    for i, m in enumerate(miss):
        k = m.get("ML", 0) + m.get("MO", 0)
        if not k:
            continue
        x = st[i].coords
        occ = [n.coords - x for n in nbs[i] if n.nn_distance < 2.6]
        others = np.array(coords)
        others = others[np.linalg.norm(others - x, axis=1) > 0.1]
        if is_metal(species[i]):
            for d in _best_dirs(x, occ, k, 2.0, others, 1.6):
                o = x + 2.0 * d; species += ["O", "H"]; coords += [o, o + 0.97 * d]; occ.append(d)
                caps.append([i, d, len(species) - 2, len(species) - 1])
        else:
            if one_proton_per_donor:
                have = sum(1 for n in nbs[i] if n.specie.symbol == "H" and n.nn_distance < 1.2)
                n_h = max(0, min(k, 1 - have))
                surplus += [i] * (k - n_h)
            else:
                n_h = k
            for d in _best_dirs(x, occ, n_h, 0.98, others, 1.3) if n_h else []:
                species.append("H"); coords.append(x + 0.98 * d); occ.append(d)
    # surplus protons: turn the nearest still-OH cap into a bound water (same atoms, same charge balance)
    free = list(range(len(caps)))
    half = math.radians(104.5) / 2
    for i in surplus:
        x = st[i].coords
        j = min(free, key=lambda c: np.linalg.norm(coords[caps[c][2]] - x))
        free.remove(j)
        mi, d, oi, hi = caps[j]
        o = st[mi].coords + 2.1 * d
        p0 = np.cross(d, [1.0, 0, 0]); p0 = p0 if np.linalg.norm(p0) > 0.1 else np.cross(d, [0, 1.0, 0])
        p0 /= np.linalg.norm(p0); q0 = np.cross(d, p0)
        rest = np.array([c for n, c in enumerate(coords) if n not in (oi, hi)])
        best = None                                  # orientation of the H-O-H plane: farthest from other atoms
        for a in np.linspace(0, np.pi, 12, endpoint=False):
            p = math.cos(a) * p0 + math.sin(a) * q0
            h1 = o + 0.97 * (math.cos(half) * d + math.sin(half) * p)
            h2 = o + 0.97 * (math.cos(half) * d - math.sin(half) * p)
            clear = min(np.min(np.linalg.norm(rest - h1, axis=1)), np.min(np.linalg.norm(rest - h2, axis=1)))
            if best is None or clear > best[0]:
                best = (clear, h1, h2)
        coords[oi] = o
        coords[hi] = best[1]
        species.append("H"); coords.append(best[2])
    status = "healed" + (f" ({len(surplus)} bound H2O)" if surplus else "")
    return Structure(st.lattice, species, coords, coords_are_cartesian=True), m_side, status


# ----------------------------------------------------------------------------- step 6
class Engine:
    """CHGNet wrapper: static energies (batched) and fixed-cell relaxations."""
    def __init__(self, device=None):
        import torch
        from chgnet.model import CHGNet
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = CHGNet.load(use_device=self.device, verbose=False)

    def static(self, structs):
        # batches of 4 on a GPU; one at a time on a CPU, where a batch of large slabs can exhaust the memory
        preds = self.model.predict_structure(list(structs), task="e", batch_size=4 if self.device == "cuda" else 1)
        preds = preds if isinstance(preds, list) else [preds]
        return [float(p["e"]) * len(s) for p, s in zip(preds, structs)]

    def relax(self, s, fmax, steps):
        from chgnet.model import StructOptimizer
        r = StructOptimizer(model=self.model, use_device=self.device).relax(
            s, fmax=fmax, steps=steps, relax_cell=False, verbose=False)
        tr = r["trajectory"]
        f = float(np.linalg.norm(np.array(tr.forces[-1]), axis=1).max())
        return float(tr.energies[-1]), r["final_structure"], len(tr.energies), f

    def water(self, fmax=0.02):
        mol = Molecule(["O", "H", "H"], [[0, 0, 0], [0.757, 0.586, 0], [-0.757, 0.586, 0]])
        e, _, _, _ = self.relax(mol.get_boxed_structure(15, 15, 15), fmax, 300)
        return e


def gamma_J_m2(E, n_bulk_atoms, e_bulk_atom, n_water, e_water, area, dmu_water=0.0):
    """gamma = (E_slab - N e_bulk - n_H2O (E_H2O + dmu)) / 2A, in J/m^2.

    dmu_water = mu_H2O - E_H2O (eV per molecule). dmu = 0 takes the water from an isolated molecule at 0 K
    (no thermal energy, no entropy), which is the most favourable water there can be and makes strongly
    hydrated faces come out too low, even negative. Stored columns gamma_*_J_m2 keep dmu = 0 so they stay
    comparable with earlier runs; the shape (step 8) uses the condition in config["water_dmu_eV"]."""
    return (E - n_bulk_atoms * e_bulk_atom - n_water * (e_water + dmu_water)) / (2 * area) * EV_A2_TO_J_M2


# Water chemical potential relative to the 0 K molecule, eV per molecule (no zero-point energy on either
# side, as usual in ab initio thermodynamics). NIST-JANAF H-064: H(298.15)-H(0) = 9.904 kJ/mol,
# S(298.15) = 188.834 J/mol/K, S(400) = 198.788, H(400)-H(298.15) = 3.452; CODATA: Gibbs energy of
# vaporisation at 298.15 K = 8.547 kJ/mol. dmu(T, p) = [H(T) - H(0)] - T S(T) + kT ln(p / 1 bar).
WATER_DMU_EV = {
    "0K_molecule": 0.0,
    "vapour_298K_1bar": -0.4809,
    "liquid_298K": -0.5695,
    "vapour_298K_RH50": -0.5874,
    "vapour_400K_1bar": -0.6857,
}


def water_slope(n_water, area):
    """d gamma / d dmu = -n_H2O / 2A, returned as a positive number in J/m^2 per eV."""
    return n_water / (2 * area) * EV_A2_TO_J_M2


def gamma_at_mu(r, key, dmu):
    """gamma of a slab record at water chemical potential dmu, from its stored dmu = 0 value."""
    g = r.get(key)
    if g is None or (isinstance(g, float) and math.isnan(g)):
        return None
    return g - water_slope(r.get("n_water") or 0, r["area_A2"]) * dmu


# ----------------------------------------------------------------------------- step 8
def wulff(conv, families, gammas, rotations):
    """Wulff polyhedron from the true point group (not the lattice symmetry).

    families: list of family dicts (members include every symmetry-equivalent hkl and -hkl)
    gammas:   {family key: gamma}. Each member plane: n.x <= gamma, n = unit reciprocal vector.
    Returns dict with vertices, faces [(polygon, family key)], area fractions, volume,
    principal extents, bounded flag (False -> open along a direction: needle/rod limit).
    """
    from scipy.optimize import linprog
    from scipy.spatial import ConvexHull, HalfspaceIntersection
    R = conv.lattice.reciprocal_lattice_crystallographic
    planes = []
    for f in families:
        if f["key"] not in gammas or not np.isfinite(gammas[f["key"]]):
            continue
        g = gammas[f["key"]]
        for h in f["members"]:
            n = R.get_cartesian_coords(h); n = n / np.linalg.norm(n)
            planes.append((n, g, f["key"]))
    if not planes:
        return None
    gmax = max(p[1] for p in planes)
    A = np.array([p[0] for p in planes]); bvec = np.array([p[1] for p in planes])
    open_dirs = []
    for d in DIRS[::4]:
        res = linprog(-d, A_ub=A, b_ub=bvec, bounds=[(None, None)] * 3, method="highs")
        if res.status == 3:
            open_dirs.append(d)
    bounded = not open_dirs
    if not bounded:   # clip with a box so it can be drawn; clipped faces are labelled 'open'
        L = 6 * gmax
        for n in np.eye(3):
            for s in (1, -1):
                planes.append((s * n, L, "open"))
    hs = np.array([[*n, -g] for n, g, _ in planes])
    V = HalfspaceIntersection(hs, np.zeros(3)).intersections
    V = np.unique(np.round(V, 8), axis=0)
    hull = ConvexHull(V)
    faces, area = [], Counter()
    for n, g, key in planes:
        on = V[np.abs(V @ n - g) < 1e-5 * max(1, g)]
        if len(on) < 3:
            continue
        ctr = on.mean(0); u = on[0] - ctr; u /= np.linalg.norm(u); w = np.cross(n, u)
        poly = on[np.argsort(np.arctan2((on - ctr) @ w, (on - ctr) @ u))]
        a = 0.5 * np.linalg.norm(sum(np.cross(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))))
        if a < 1e-9:
            continue
        faces.append((poly, key)); area[key] += a
    tot = sum(v for k, v in area.items() if k != "open")
    frac = {k: v / sum(area.values()) for k, v in area.items()}
    ext = np.linalg.svd(V - V.mean(0), compute_uv=False)
    axes = np.linalg.svd(V - V.mean(0))[2]
    return dict(vertices=V, faces=faces, area_fractions=frac, volume=hull.volume, extents=ext, axes=axes,
                bounded=bounded, open_dirs=[d.tolist() for d in open_dirs])


def name_habit(w, families, crystal_system, conv):
    """Shape name from area fractions (cubic: polyhedron names; others: habit + dominant faces)."""
    if w is None:
        return "no faces"
    fam_name = {f["key"]: f["name"] for f in families}
    fr = {fam_name.get(k, k): v for k, v in w["area_fractions"].items()}
    if not w["bounded"]:
        d = np.array(w["open_dirs"][0]); fd = conv.lattice.get_fractional_coords(d)
        # K6 (15 Nov 2026): an unbounded Wulff shape means a face family that would close the crystal is
        # missing from the list (too few families kept, or no energy for it); it is not a rod.
        return f"open: no face closes the crystal along [{', '.join(f'{x:.2f}' for x in fd / np.abs(fd).max())}] (a face family is missing)"
    if crystal_system == "cubic":
        f = lambda k: fr.get(k, 0.0)
        # K1 (15 Nov 2026): the pure shapes and the cuboctahedron are single points of the map, so the names
        # are given only within numerical noise (PURE), not within 5 %; everything else is named by its family.
        PURE = 1e-3
        if f("{100}") > 1 - PURE: return "cube"
        if f("{111}") > 1 - PURE: return "octahedron"
        if f("{110}") > 1 - PURE: return "rhombic_dodecahedron"
        if f("{110}") < PURE and f("{100}") + f("{111}") > 1 - PURE:
            # {100} + {111} only: one-parameter series cube -> octahedron (project note, Step 11).
            # The cuboctahedron is the single point with 6 squares + 8 triangles of equal edge:
            # {100} share = 6 / (6 + 2*sqrt(3)) = 0.634. Below it: truncated octahedron; above: truncated cube.
            c = f("{100}") / (f("{100}") + f("{111}"))
            if abs(c - 6 / (6 + 2 * 3 ** 0.5)) < 0.005: return "cuboctahedron"
            return "truncated_octahedron" if c < 0.634 else "truncated_cube"
        top = max(fr, key=fr.get)
        if top == "{110}": return "truncated_rhombic_dodecahedron"
        return f"mixed_dominant_{top}"
    # Zingg (1935) classes, as in the project note (Part B, Step 10): b/a < 2/3 -> elongated, c/b < 2/3 -> flat
    e1, e2, e3 = w["extents"]
    long_, flat = e2 / e1 < 2 / 3, e3 / e2 < 2 / 3
    habit = "lath" if long_ and flat else "needle/rod" if long_ else "plate" if flat else "block/prism"
    top = sorted(fr.items(), key=lambda kv: -kv[1])[:3]
    return f"{habit}: " + ", ".join(f"{k} {v:.0%}" for k, v in top)


COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#b04fd1", "#d4a017", "#5b6770", "#e0457b", "#2bb3c0"]


def render(w, families, title, path):
    import matplotlib; import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    keys = [f["key"] for f in families]; names = {f["key"]: f["name"] for f in families}
    col = {k: COLORS[i % len(COLORS)] for i, k in enumerate(keys)}; col["open"] = "#d9d9d9"
    fig = plt.figure(figsize=(5, 5)); ax = fig.add_subplot(111, projection="3d")
    s = np.abs(w["vertices"]).max()
    for poly, k in w["faces"]:
        ax.add_collection3d(Poly3DCollection([poly / s], facecolor=col[k], edgecolor="#2b2b29", lw=0.6, alpha=0.95))
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_zlim(-1, 1); ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=22, azim=35); ax.set_axis_off(); ax.set_title(title, fontsize=9)
    used = sorted({k for _, k in w["faces"]}, key=lambda k: -w["area_fractions"].get(k, 0))
    ax.legend([plt.Rectangle((0, 0), 1, 1, color=col[k]) for k in used],
              [f"{names.get(k, 'open (not computed)')} {w['area_fractions'][k]:.0%}" for k in used],
              loc="lower left", fontsize=7, frameon=False)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)
    return path


def write_obj(w, path):
    lines, k = [], 1
    for poly, key in w["faces"]:
        lines.append(f"g {key}")
        for v in poly:
            lines.append("v " + " ".join(f"{x:.6f}" for x in v))
        lines.append("f " + " ".join(str(k + i) for i in range(len(poly)))); k += len(poly)
    Path(path).write_text("\n".join(lines))


# ----------------------------------------------------------------------------- step 7 helpers
# unpaired d electrons of the usual MOF oxidation states (high spin); K9 (15 Nov 2026)
UNPAIRED = {"Cu": 1, "Co": 3, "Ni": 2, "Fe": 5, "Mn": 5, "Cr": 3, "V": 1, "Ti": 0, "Zn": 0, "Zr": 0, "Hf": 0,
            "Mg": 0, "Ca": 0, "Al": 0, "Cd": 0, "In": 0, "Sc": 0}


def cp2k_input(struct, project, charge=0, slab=False):
    """Minimal CP2K PBE-D3(BJ) single-point input (DZVP-MOLOPT-SR, GTH) for a slab or bulk cell.

    K9 (15 Nov 2026): a slab is turned so that its normal (the third lattice vector, perpendicular to the
    first two) lies along z, and the surface dipole correction is switched on, because a slab with two
    different terminations carries a dipole that the periodic cell would otherwise repeat. Open-shell
    metals get a ferromagnetic high-spin multiplicity from UNPAIRED (Cu2+ d9: one unpaired electron each).
    The true ground state of the Cu2 paddlewheel is antiferromagnetic; using the same ferromagnetic state
    for bulk and slab makes most of that difference cancel in gamma. A metal not in UNPAIRED is flagged."""
    if slab:
        L = struct.lattice
        struct = Structure(Lattice.from_parameters(*L.abc, *L.angles), struct.species, struct.frac_coords)
    els = sorted({x.specie.symbol for x in struct})
    unknown = sorted({e for e in els if is_metal(e) and e not in UNPAIRED})
    n_up = sum(UNPAIRED.get(x.specie.symbol, 0) for x in struct)
    spin = f"    MULTIPLICITY {n_up + 1}\n" if n_up else ""
    if unknown:
        spin += f"    ! unpaired electrons of {', '.join(unknown)} not known: set MULTIPLICITY by hand\n"
    dip = "    SURFACE_DIPOLE_CORRECTION .TRUE.\n    SURF_DIP_DIR Z\n" if slab else ""
    kinds = "\n".join(f"    &KIND {e}\n      BASIS_SET DZVP-MOLOPT-SR-GTH\n      POTENTIAL GTH-PBE\n    &END KIND" for e in els)
    a, b, c = struct.lattice.matrix
    xyz = "\n".join(f"      {x.specie.symbol} {x.coords[0]:.6f} {x.coords[1]:.6f} {x.coords[2]:.6f}" for x in struct)
    return f"""&GLOBAL
  PROJECT {project}
  RUN_TYPE ENERGY
&END GLOBAL
&FORCE_EVAL
  METHOD Quickstep
  &DFT
    BASIS_SET_FILE_NAME BASIS_MOLOPT
    POTENTIAL_FILE_NAME GTH_POTENTIALS
    CHARGE {charge}
    UKS .TRUE.
{spin}{dip}    &MGRID
      CUTOFF 500
      REL_CUTOFF 50
    &END MGRID
    &SCF
      EPS_SCF 1.0E-6
      MAX_SCF 50
      &OT
        MINIMIZER DIIS
      &END OT
      &OUTER_SCF
        MAX_SCF 20
      &END OUTER_SCF
    &END SCF
    &XC
      &XC_FUNCTIONAL PBE
      &END XC_FUNCTIONAL
      &VDW_POTENTIAL
        POTENTIAL_TYPE PAIR_POTENTIAL
        &PAIR_POTENTIAL
          TYPE DFTD3(BJ)
          PARAMETER_FILE_NAME dftd3.dat
          REFERENCE_FUNCTIONAL PBE
        &END PAIR_POTENTIAL
      &END VDW_POTENTIAL
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      A {a[0]:.6f} {a[1]:.6f} {a[2]:.6f}
      B {b[0]:.6f} {b[1]:.6f} {b[2]:.6f}
      C {c[0]:.6f} {c[1]:.6f} {c[2]:.6f}
    &END CELL
    &COORD
{xyz}
    &END COORD
{kinds}
  &END SUBSYS
&END FORCE_EVAL
"""


# ----------------------------------------------------------------------------- driver
def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


DEFAULTS = dict(symprec=0.1, disorder="majority", max_index=1, n_families=6, faces=None,
                thickness=15.0, vacuum=15.0, level_tol=0.3, max_terms=8, cap="water",
                relax_steps=800, fmax=0.05, relax_top_k=2,
                water_dmu_eV=WATER_DMU_EV["liquid_298K"], one_proton_per_donor=True)   # water reference used for the shape (step 8)


def _hkey(st):
    return hashlib.md5(st.to(fmt="poscar").encode()).hexdigest()[:10]


def run_mof(engine, name, cif, out, **cfg):
    """Steps 1-6 and 8 for one MOF. Everything is cached under out/cache/<name>/."""
    c = {**DEFAULTS, **{k: v for k, v in cfg.items() if v is not None}}
    out = Path(out); cdir = out / "cache" / re.sub(r"[^\w.-]", "_", name); cdir.mkdir(parents=True, exist_ok=True)
    sdir = out / "structures" / re.sub(r"[^\w.-]", "_", name); sdir.mkdir(parents=True, exist_ok=True)
    get = lambda k: json.loads((cdir / f"{k}.json").read_text()) if (cdir / f"{k}.json").exists() else None
    put = lambda k, v: (cdir / f"{k}.json").write_text(json.dumps(v, indent=1, default=str))

    # Step 1
    info = standardize(cif, c["symprec"], c["disorder"])
    log(f"{name}: {info['formula']}  SG {info['space_group']} ({info['symmetry_source']})  "
        f"conv {info['n_atoms_conv']} / working {info['n_atoms_prim']} atoms")
    for n in info["notes"]:
        log("   step1:", n)
    # Step 2
    blocks, _ = building_blocks(info["prim"])
    bs = summarize_blocks(blocks)
    log("   step2 blocks:", bs["blocks"], "| infinite inorganic unit" if bs["infinite_inorganic_unit"] else "")
    # Step 3 (families)
    fams = face_families(info["conv"], info["rotations"], c["max_index"], c["n_families"], c["faces"], ops=info["ops"])
    log("   step3 families:", ", ".join(f"{f['name']}(d={f['d_hkl']:.1f})" for f in fams))
    meta = dict(mof=name, cif=str(cif), formula=info["formula"], space_group=info["space_group"],
                crystal_system=info["crystal_system"], symmetry_source=info["symmetry_source"],
                conv_lattice=info["conv"].lattice.matrix.tolist(), notes=info["notes"], **bs,
                families=[{k: f[k] for k in ("key", "name", "rep", "d_hkl")} | {"n_members": len(f["members"])} for f in fams],
                config=c, _rotations=[R.tolist() for R in info["rotations"]])
    put("meta", meta)

    # Step 6a: bulk reference (same model, same settings)
    bkey = f"bulk_r{c['relax_steps']}_f{c['fmax']}"
    bulk = get(bkey)
    prim = info["prim"]
    if bulk is None:
        t = time.time()
        if c["relax_steps"] > 0:
            e, prim_r, n, fm = engine.relax(prim, c["fmax"], c["relax_steps"])
        else:
            e, prim_r, n, fm = engine.static([prim])[0], prim, 0, None
        prim_r.to(filename=str(sdir / f"{bkey}.cif"))
        bulk = dict(n_atoms=len(prim), energy_eV=e, e_per_atom_eV=e / len(prim), steps=n, final_fmax=fm,
                    converged=fm is None or fm <= c["fmax"] + 1e-9, seconds=round(time.time() - t, 1))
        put(bkey, bulk)
    prim_r = Structure.from_file(str(sdir / f"{bkey}.cif")) if c["relax_steps"] > 0 else prim
    # K11 fix (10 Nov 2026): the CIF round trip re-orients the lattice; put the relaxed fractional
    # coordinates back on the original lattice matrix so conv and prim share one frame.
    if c["relax_steps"] > 0:
        prim_r = Structure(prim.lattice, [x.species for x in prim_r], prim_r.frac_coords)
    bulk["cif"] = str(sdir / f"{bkey}.cif")
    conv = prim_r if info["conv"] is info["prim"] else info["conv"]
    e_bulk = bulk["e_per_atom_eV"]
    log(f"   step6 bulk: {e_bulk:.4f} eV/atom, converged {bulk['converged']}")
    modes = ["bare", "water"] if c["cap"] == "both" else (["water"] if c["cap"] == "water" else ["bare"])
    e_w = 0.0
    if "water" in modes:
        w = get("water") or {"E_H2O_eV": engine.water()}
        put("water", w); e_w = w["E_H2O_eV"]

    recs = []
    for f in fams:
        # Steps 3-4: terminations and slabs
        try:
            made = block_slabs(conv, prim_r, f["rep"], c["thickness"], c["vacuum"], c["level_tol"])
        except Exception as exc:
            log(f"   {f['name']}: slab construction failed: {exc}"); continue
        for m in made:
            miss, tot = broken_bonds(m)
            m["miss"], m["broken"] = miss, tot
            m["bond_density"] = sum(v for k, v in tot.items() if k in ("ML", "MO")) / 2 / m["area_A2"]
        n_all = len(made)
        made.sort(key=lambda m: m["bond_density"])
        made = made[: c["max_terms"]]            # rule: keep the terminations that break fewest bonds per area
        log(f"   {f['name']}: {n_all} distinct terminations, kept {len(made)}"
            + (" (cuts infinite inorganic unit)" if made and made[0]["cuts_infinite_unit"] else ""))
        for mode in modes:
            todo = []
            for ti, m in enumerate(made):
                if mode == "water":
                    st, n_w, status = heal(m, m["miss"], one_proton_per_donor=c["one_proton_per_donor"])
                else:
                    bad = m["broken"].get("org", 0) + m["broken"].get("MM", 0) + m["broken"].get("_extra", 0)
                    st, n_w, status = (None, 0, "rejected: non metal-donor bond broken") if bad else (m["slab"], 0, "bare")
                base = dict(mof=name, family=f["key"], face=f["name"], hkl=str(f["rep"]), termination=ti,
                            z0_A=m["z0"], cap=mode, status=status, n_slab_atoms=len(m["slab"]),
                            n_atoms=len(st) if st else None, n_water=n_w, area_A2=round(m["area_A2"], 2),
                            thickness_A=m["thickness_A"], n_layers=m["n_layers"],
                            broken_bonds=json.dumps(m["broken"]), bonds_per_A2=round(m["bond_density"], 5),
                            cuts_infinite_unit=m["cuts_infinite_unit"])
                if st is None:
                    recs.append(base); continue
                key = f"slab_{f['key']}_{mode}_{_hkey(st)}"
                todo.append((key, st, base, m))
            # static screen (batched)
            need = [t for t in todo if get(t[0] + "_static") is None]
            if need:
                es = engine.static([t[1] for t in need])
                for (key, st, base, m), e in zip(need, es):
                    put(key + "_static", {"E": e})
            for key, st, base, m in todo:
                e = get(key + "_static")["E"]
                base["gamma_static_J_m2"] = round(gamma_J_m2(e, len(m["slab"]), e_bulk, base["n_water"], e_w, m["area_A2"]), 4)
                base["_key"] = key; base["_st"] = st; base["_m"] = m
            # Step 6b: relax the K lowest static terminations (rule documented in DEFAULTS / README)
            # ranked at the water reference of step 8, so the terminations relaxed are the ones the shape uses
            dmu_rank = c["water_dmu_eV"] if mode == "water" else 0.0
            for t in todo:
                t[2]["water_slope_J_m2_per_eV"] = round(water_slope(t[2]["n_water"], t[3]["area_A2"]), 5)
            todo.sort(key=lambda t: gamma_at_mu(t[2], "gamma_static_J_m2", dmu_rank))
            for rank, (key, st, base, m) in enumerate(todo):
                if c["relax_steps"] > 0 and rank < c["relax_top_k"]:
                    rk = f"{key}_r{c['relax_steps']}_f{c['fmax']}"
                    r = get(rk)
                    if r is None:
                        t = time.time()
                        try:
                            E, fin, n, fm = engine.relax(st, c["fmax"], c["relax_steps"])
                        except Exception as exc:
                            log(f"      relax failed {key}: {exc}"); continue
                        fin.to(filename=str(sdir / f"{rk}.cif"))
                        r = dict(E=E, steps=n, final_fmax=fm, converged=fm <= c["fmax"] + 1e-9,
                                 seconds=round(time.time() - t, 1))
                        put(rk, r)
                    base.update(gamma_relaxed_J_m2=round(gamma_J_m2(r["E"], len(m["slab"]), e_bulk, base["n_water"], e_w, m["area_A2"]), 4),
                                steps=r["steps"], final_fmax=round(r["final_fmax"], 4), converged=r["converged"],
                                relax_seconds=r["seconds"], relaxed_cif=str(sdir / f"{rk}.cif"))
                    if not r["converged"]:
                        log(f"      NOT converged: {f['name']} t{base['termination']} {mode} fmax {r['final_fmax']:.3f}")
                st.to(filename=str(sdir / f"{key}_unrelaxed.cif"))
                base["unrelaxed_cif"] = str(sdir / f"{key}_unrelaxed.cif")
                log(f"      {f['name']} t{base['termination']} {mode:5s}: {base['n_atoms']} atoms, "
                    f"gamma static {base['gamma_static_J_m2']:.3f}"
                    + (f", relaxed {base['gamma_relaxed_J_m2']:.3f} ({base['steps']} steps)" if 'gamma_relaxed_J_m2' in base else ""))
                recs.append({k: v for k, v in base.items() if not k.startswith("_")})
    return meta, fams, recs, bulk


def choose_gamma(recs, mode, need_relaxed=True, dmu=0.0):
    """Lowest gamma per family at water chemical potential dmu: relaxed + converged if available
    (required when need_relaxed), otherwise static (flagged). The lowest termination can change with dmu,
    because terminations differ in water per area."""
    best = {}
    for r in recs:
        if r.get("cap") != mode or r.get("gamma_static_J_m2") is None:
            continue
        d = dmu if mode == "water" else 0.0
        if r.get("gamma_relaxed_J_m2") is not None and r.get("converged"):
            g, src = gamma_at_mu(r, "gamma_relaxed_J_m2", d), "relaxed"
        elif need_relaxed:
            continue
        else:
            g, src = gamma_at_mu(r, "gamma_static_J_m2", d), "static"
        k = r["family"]
        if k not in best or g < best[k]["gamma"]:
            best[k] = dict(gamma=g, source=src, termination=r["termination"], face=r["face"])
    return best


def wulff_report(meta, fams, recs, out, mode, need_relaxed=True, dmu=None):
    conv = Structure(Lattice(meta["conv_lattice"]), ["H"], [[0, 0, 0]])
    dmu = meta.get("config", {}).get("water_dmu_eV", 0.0) if dmu is None else dmu
    best = choose_gamma(recs, mode, need_relaxed, dmu)
    best0 = choose_gamma(recs, mode, need_relaxed, 0.0)
    row = dict(mof=meta["mof"], cap=mode, space_group=meta["space_group"], n_families_with_gamma=len(best),
               water_dmu_eV=dmu if mode == "water" else None,
               **{f"gamma0K_{k}": round(b["gamma"], 4) for k, b in best0.items()},
               gamma_source=",".join(sorted({b["source"] for b in best.values()})) or "none",
               **{f"gamma_{k}": round(b["gamma"], 4) for k, b in best.items()})
    if len(best) < 2:
        row["habit"] = "not enough faces"; return row, None
    if any(b["gamma"] <= 0 for b in best.values()):
        row["habit"] = "undefined: gamma <= 0 for " + ",".join(b["face"] for b in best.values() if b["gamma"] <= 0) \
                       + f" at water dmu = {dmu:+.3f} eV (hydrating the cut is downhill at this water reference)"
        return row, None
    rots = [np.array(r) for r in meta["_rotations"]]
    w = wulff(conv, fams, {k: b["gamma"] for k, b in best.items()}, rots)
    name = name_habit(w, fams, meta["crystal_system"], conv)
    fr = {next(f["name"] for f in fams if f["key"] == k) if k != "open" else "open": round(v, 3)
          for k, v in sorted(w["area_fractions"].items(), key=lambda kv: -kv[1])}
    e = w["extents"]
    row.update(habit=name, area_fractions=json.dumps(fr), dominant_face=max(fr, key=fr.get),
               bounded=w["bounded"], aspect_e1_e2=round(e[0] / e[1], 3), aspect_e2_e3=round(e[1] / e[2], 3))
    tag = re.sub(r"[^\w.-]", "_", meta["mof"])
    png = render(w, fams, f"{meta['mof']} ({mode})\n{name}", Path(out) / f"wulff_{tag}_{mode}.png")
    write_obj(w, Path(out) / f"wulff_{tag}_{mode}.obj")
    row["png"] = str(png)
    return row, w
