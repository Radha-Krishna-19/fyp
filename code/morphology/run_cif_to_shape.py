"""From a CIF to a crystal shape, every step written out: the reference numbers for the
"CIF to Shape" page of the website (website/cif_to_shape.html).

Run from anywhere:  python3 code/morphology/run_cif_to_shape.py
Writes results/cif_to_shape.json next to this file.

The steps are the ones the page shows, in the same order:
  1. read a, b, c, alpha, beta, gamma and the atoms from the CIF;
  2. build the lattice vectors (rows of A) and the metric tensor G = A A^T;
  3. decide whether the lattice is cubic, and find the conventional cubic cell
     (a 60-degree rhombohedral cell is the primitive cell of a face-centred cube);
  4. find the lattice centring from the atoms: does every atom have an identical
     partner at x + t for t = (1/2,1/2,1/2) (I) or the three face centres (F)?
  5. find the point group from the atoms: inversion, 3-fold, 4-fold and -4 axes;
  6. compute the structure factor F(hkl) = sum_j Z_j exp(2 pi i h.x_j) to see which
     reflections vanish, and hence the effective spacing d_eff = d_hkl / n;
  7. BFDH: face distance R proportional to 1/d_eff (leading face at 1);
  8. intersect the half-spaces n.x <= R, then measure the shape.

Steps 4 and 5 are done here by direct search, the same way the browser does them, and are
cross-checked against spglib (mofmorph.structure.load). Steps 6 to 8 are cross-checked
against results/phase1_results.json, written by run_phase1.py.
"""
import sys, os, json, math, itertools, re, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
warnings.filterwarnings("ignore")
from mofmorph.structure import load
from mofmorph.faces import enumerate_faces, families
from mofmorph.models import bfdh, describe

HERE = os.path.dirname(os.path.abspath(__file__))
CIFDIR = os.path.join(HERE, "..", "..", "website")       # the same four files the page reads
OUT = os.path.join(HERE, "results", "cif_to_shape.json")
MOFS = [("MOF-5", "MOF5.cif"), ("HKUST-1", "HKUST-1.cif"), ("UiO-66", "UiO-66.cif"), ("ZIF-8", "ZIF-8.cif")]
Z = {"H": 1, "C": 6, "N": 7, "O": 8, "Zn": 30, "Cu": 29, "Zr": 40}
TOL = 0.02          # Angstrom: two atoms closer than this are "the same position"


# ---- step 1: read the CIF ---------------------------------------------------------------
def read_cif(path):
    txt = open(path, encoding="utf-8").read()
    def num(key):
        m = re.search(r"^\s*" + key + r"\s+([-0-9.]+)", txt, re.M)
        return float(m.group(1))
    cell = [num("_cell_length_a"), num("_cell_length_b"), num("_cell_length_c"),
            num("_cell_angle_alpha"), num("_cell_angle_beta"), num("_cell_angle_gamma")]
    lines = txt.splitlines()
    atoms = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == "loop_":
            j, cols = i + 1, []
            while j < len(lines) and lines[j].strip().startswith("_"):
                cols.append(lines[j].strip()); j += 1
            if "_atom_site_fract_x" in cols:
                ix, iy, iz = (cols.index("_atom_site_fract_" + c) for c in "xyz")
                it = cols.index("_atom_site_type_symbol") if "_atom_site_type_symbol" in cols else cols.index("_atom_site_label")
                while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith(("_", "loop_")):
                    p = lines[j].split()
                    if len(p) >= len(cols):
                        el = re.match(r"[A-Z][a-z]?", p[it]).group(0)
                        atoms.append((el, [float(p[ix]), float(p[iy]), float(p[iz])]))
                    j += 1
            i = j
        else:
            i += 1
    return cell, atoms


# ---- step 2: lattice vectors and metric tensor ---------------------------------------------
def lattice(a, b, c, al, be, ga):
    al, be, ga = map(math.radians, (al, be, ga))
    ax = [a, 0, 0]
    bx = [b * math.cos(ga), b * math.sin(ga), 0]
    cx = c * math.cos(be)
    cy = c * (math.cos(al) - math.cos(be) * math.cos(ga)) / math.sin(ga)
    cz = math.sqrt(max(c * c - cx * cx - cy * cy, 0))
    return np.array([ax, bx, [cx, cy, cz]])


# ---- step 3: conventional cubic cell ----------------------------------------------------------
# Candidate transformations M (rows: new vectors as integer combinations of the old ones).
M_CANDIDATES = {
    "P": np.eye(3, dtype=int),                               # already conventional
    "F": np.array([[-1, 1, 1], [1, -1, 1], [1, 1, -1]]),     # fcc primitive (60 deg) -> cube
    "I": np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]]),        # bcc primitive (109.47 deg) -> cube
}

def conventional(G, rel=2e-4):
    """Return (key, M, a_c) for the first M with M G M^T = a_c^2 I, else None."""
    for key, M in M_CANDIDATES.items():
        Gc = M @ G @ M.T
        a2 = np.trace(Gc) / 3
        if np.max(np.abs(Gc - a2 * np.eye(3))) < rel * a2:
            return key, M, math.sqrt(a2)
    return None


# ---- steps 4 and 5: symmetry by direct search ----------------------------------------------
def to_conventional_frac(A, atoms, M):
    """Fractional coordinates of the atoms in the conventional cell, filled with every
    lattice-equivalent copy (for a primitive file there are 4 (F) or 2 (I) copies per atom)."""
    Ac = M @ A
    X = np.array([p for _, p in atoms])
    cart = X @ A
    Xc = cart @ np.linalg.inv(Ac)
    k = int(round(abs(np.linalg.det(M))))
    shifts = [np.array(s) for s in itertools.product(range(-1, 2), repeat=3)]
    els, pos = [], []
    for e, x in zip([e for e, _ in atoms], Xc):
        seen = []
        for s in shifts:     # primitive-lattice translations, expressed in conventional coordinates
            y = (x + (np.array(s) @ A) @ np.linalg.inv(Ac)) % 1.0
            if all(np.linalg.norm(((y - z + 0.5) % 1.0 - 0.5) @ Ac) > TOL for z in seen):
                seen.append(y)
        for y in seen:
            els.append(e); pos.append(y)
    return Ac, els, np.array(pos), k


def maps_onto(els, X, Ac, R, t, skip_H=False):
    """Fraction of atoms x for which R x + t is (mod 1) an atom of the same element."""
    good = tot = 0
    by = {}
    for e, x in zip(els, X):
        by.setdefault(e, []).append(x)
    for e in by:
        by[e] = np.array(by[e])
    for e, x in zip(els, X):
        if skip_H and e == "H":
            continue
        tot += 1
        y = (R @ x + t) % 1.0
        dif = (by[e] - y + 0.5) % 1.0 - 0.5
        if np.min(np.linalg.norm(dif @ Ac, axis=1)) < TOL:
            good += 1
    return good, tot


def search_op(els, X, Ac, R, skip_H=False):
    """Is there a translation t that makes (R, t) a symmetry? Try every t that sends the first
    atom of the rarest element onto an atom of that element."""
    pool = [(e, x) for e, x in zip(els, X) if not (skip_H and e == "H")]
    counts = {}
    for e, _ in pool:
        counts[e] = counts.get(e, 0) + 1
    rare = min(counts, key=lambda e: (counts[e], e))
    xs = [x for e, x in pool if e == rare]
    best = (0, 1, None)
    for y in xs:
        t = (y - R @ xs[0]) % 1.0
        g, tot = maps_onto(els, X, Ac, R, t, skip_H)
        if g > best[0]:
            best = (g, tot, t)
        if g == tot:
            break
    return best


OPS = {
    "inversion":   -np.eye(3),
    "3-fold [111]": np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]]),      # (x,y,z) -> (z,x,y)
    "4-fold [001]": np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]]),     # (x,y,z) -> (-y,x,z)
    "-4 [001]":     np.array([[0, 1, 0], [-1, 0, 0], [0, 0, -1]]),    # (x,y,z) -> (y,-x,-z)
}

def point_group(found):
    inv, c3, c4, s4 = (found[k] for k in OPS)
    if not c3:
        return "not cubic"
    if inv and c4:
        return "m-3m"
    if inv:
        return "m-3"
    if c4:
        return "432"
    if s4:
        return "-43m"
    return "23"


# ---- step 6: structure factors -------------------------------------------------------------
def structure_factor(els, X, h):
    ph = np.exp(2j * np.pi * (X @ np.array(h, float)))
    w = np.array([Z[e] for e in els], float)
    return complex(np.sum(w * ph)), float(np.sum(w))


# ---- steps 7 and 8: BFDH shape -------------------------------------------------------------------
def r(x, n=4):
    return float(round(float(x), n))


def run(name, fname):
    path = os.path.join(CIFDIR, fname)
    cell, atoms = read_cif(path)
    rec = dict(file=fname, cell=cell, n_atoms=len(atoms))
    comp = {}
    for e, _ in atoms:
        comp[e] = comp.get(e, 0) + 1
    rec["composition"] = comp
    A = lattice(*cell)
    G = A @ A.T
    rec["A"] = A.round(4).tolist()
    rec["G"] = G.round(3).tolist()
    rec["volume"] = r(math.sqrt(np.linalg.det(G)), 2)
    conv = conventional(G)
    key, M, ac = conv
    rec["cubic_transform"] = key
    rec["M"] = M.tolist()
    rec["a_conv"] = r(ac, 4)
    rec["lattice_points_per_conventional_cell"] = int(round(abs(np.linalg.det(M))))
    Ac, els, X, k = to_conventional_frac(A, atoms, M)
    rec["n_atoms_conventional"] = len(els)

    # centring from the atoms
    cent = {}
    for skip in (False, True):
        tag = "without_H" if skip else "with_H"
        cent[tag] = {}
        for lab, ts in [("I", [[.5, .5, .5]]), ("F", [[0, .5, .5], [.5, 0, .5], [.5, .5, 0]])]:
            res = [maps_onto(els, X, Ac, np.eye(3), np.array(t), skip) for t in ts]
            cent[tag][lab] = [list(x) for x in res]
    rec["centring_test"] = cent
    def has(tag, lab):
        return all(g == t for g, t in cent[tag][lab])
    use_tag = "with_H" if (has("with_H", "F") or has("with_H", "I")) else "without_H"
    centring = "F" if has(use_tag, "F") else ("I" if has(use_tag, "I") else "P")
    rec["centring"] = centring
    rec["symmetry_found_with"] = use_tag

    pg = {}
    for skip in (False, True):
        tag = "without_H" if skip else "with_H"
        pg[tag] = {}
        for op, R in OPS.items():
            g, tot, t = search_op(els, X, Ac, R, skip)
            pg[tag][op] = dict(mapped=g, of=tot, t=None if t is None else np.round(t, 4).tolist())
    rec["point_group_test"] = pg
    found = {op: pg[use_tag][op]["mapped"] == pg[use_tag][op]["of"] for op in OPS}
    rec["point_group"] = point_group(found)

    # structure factors on the framework that carries the symmetry
    keep = [i for i, e in enumerate(els) if not (use_tag == "without_H" and e == "H")]
    E2 = [els[i] for i in keep]; X2 = X[keep]
    sf = {}
    for h in [(1, 0, 0), (2, 0, 0), (1, 1, 0), (2, 2, 0), (1, 1, 1), (2, 2, 2), (2, 1, 0), (4, 2, 0), (2, 1, 1), (4, 2, 2), (3, 1, 1), (3, 3, 1)]:
        F, tot = structure_factor(E2, X2, h)
        sf["".join(map(str, h))] = dict(abs=r(abs(F), 3), ratio=r(abs(F) / tot, 5))
    rec["structure_factor"] = sf
    rec["structure_factor_sumZ"] = r(sum(Z[e] for e in E2), 1)

    # spglib cross-check, and the Phase 1 BFDH construction on the spglib cell
    c = load(path, name)
    rec["spglib"] = dict(spacegroup=c.spacegroup, number=c.sg_number, a=r(c.cell_lengths[0], 4),
                         used_hydrogen=c.used_hydrogen)
    Fc = enumerate_faces(c, 6)
    fams = families(Fc)
    rec["families_all"] = len(fams)
    rec["families"] = [dict(family=f["label"], n=f["order"], d=r(f["d"], 4), d_eff=r(f["d_eff"], 4),
                            multiplicity=f["multiplicity"]) for f in fams[:10]]
    s, rate = bfdh(Fc, n_families=10)
    summ = s.summary()
    rec["bfdh_rates"] = {f["label"]: r(rate[f["family"]], 5) for f in fams[:10]}
    rec["shape"] = dict(name=describe(s), n_faces=int(summ["n_faces"]), n_vertices=int(summ["n_vertices"]),
                        sphericity=r(summ["sphericity"], 4),
                        face_area_fraction={k2: r(v, 4) for k2, v in summ["face_area_fraction"].items()},
                        volume=r(s.volume, 4), area=r(s.area, 4))
    # does any family beyond the ten reach the shape? margin R_f - max_v n.v (must be > 0)
    V = s.V
    dmax = fams[0]["d_eff"]
    margins = []
    for f in fams[10:]:
        n = f["members"][0].normal
        h = float(np.max(V @ n))
        margins.append(dmax / f["d_eff"] - h)
    rec["smallest_margin_other_families"] = r(min(margins), 4) if margins else None
    rec["other_families_checked"] = len(margins)
    return rec


def main():
    R = {}
    p1 = json.load(open(os.path.join(HERE, "results", "phase1_results.json")))
    for name, fname in MOFS:
        rec = run(name, fname)
        R[name] = rec
        sg = rec["spglib"]
        ok = rec["shape"]["name"] == p1[name]["bfdh"]["name"]
        print(f"{name:8s} file {rec['cell'][0]:.3f} A, {rec['cell'][3]:.2f} deg -> {rec['cubic_transform']} "
              f"a_c={rec['a_conv']:.3f}  centring {rec['centring']} ({rec['symmetry_found_with']})  "
              f"point group {rec['point_group']}  spglib {sg['spacegroup']}  "
              f"shape {rec['shape']['name']} ({'same as' if ok else 'DIFFERS from'} phase1)  "
              f"margin {rec['smallest_margin_other_families']}")
    json.dump(R, open(OUT, "w"), indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
