"""BFDH crystal shapes for MOFs of ANY lattice (cubic, hexagonal, trigonal, tetragonal,
orthorhombic, monoclinic, triclinic), and whether each shape is compact, a rod, a plate or a lath.

Run from anywhere:  python3 code/morphology/run_general_shape.py
Reads the CIF files in data/structures/general_lattice/ and writes
results/general_shape.json next to this file. The browser engine website/mof_general_shape.js
does the same steps independently; website/tests/test_general_shape.js compares the two.

Steps (the same as on the "CIF to Shape" page for a non-cubic file):
  1. read the cell and the atoms (ase expands the symmetry operations listed in the CIF);
  2. find the space-group operations with spglib (distance tolerance 0.05 Angstrom), in the
     file's own cell, so that Miller indices mean the same thing here and in the browser.
     The search is done with and without hydrogen, and the larger group is kept, because
     H positions are often placed by software and can break the framework's symmetry;
  3. for every primitive direction h with |h_i| <= 6: d_hkl = 1/|h B| from the metric, and
     the first allowed order n (h R = h with h.t not an integer means n*h is absent);
     d_eff = d_hkl / n;
  4. families are orbits {h R}; BFDH places each family at distance R = d_eff,max / d_eff
     and keeps the 40 families with the largest d_eff;
  5. intersect the half-spaces n.x <= R (scipy), measure the solid's gyration tensor, and
     classify the habit by Zingg's ratios of its principal radii a >= b >= c:
     compact (equant) if b/a >= 2/3 and c/b >= 2/3, rod if only b/a < 2/3,
     plate if only c/b < 2/3, lath if both;
  6. name the long axis of a rod (or the flat face of a plate) in lattice terms.

BFDH uses geometry only: no solvent, additive, temperature or supersaturation. It gives the
shape a crystal would have if each face grew at a rate set only by its interplanar spacing.
"""
import sys, os, json, math, hashlib, itertools, warnings
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
warnings.filterwarnings("ignore")
import numpy as np
import spglib
from ase.io import read
from mofmorph.structure import Crystal
from mofmorph.faces import enumerate_faces
from mofmorph.shape import Shape

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CIFDIR = os.path.join(REPO, "data", "structures", "general_lattice")
OUT = os.path.join(HERE, "results", "general_shape.json")
N_FAMILIES = 40
MAX_INDEX = 6
ZINGG = 2 / 3


SYMPREC = 0.05      # Angstrom; the browser uses the same distance tolerance


def crystal_in_file_setting(path, sp=SYMPREC):
    atoms = read(path)
    best = None
    for use_h in (True, False):
        a = atoms if use_h else atoms[[s != "H" for s in atoms.get_chemical_symbols()]]
        cell = (np.array(a.cell[:]), a.get_scaled_positions(), a.numbers)
        d = spglib.get_symmetry_dataset(cell, symprec=sp)
        key = (len(d.rotations), use_h)
        if best is None or key > best[0]:
            best = (key, d, use_h)
    _, d, use_h = best
    return Crystal(name=os.path.basename(path), lattice=np.array(atoms.cell[:]), frac=atoms.get_scaled_positions(),
                   numbers=atoms.numbers, spacegroup=d.international, sg_number=d.number,
                   rotations=np.array(d.rotations), translations=np.array(d.translations),
                   symprec=sp, used_hydrogen=use_h), len(atoms)


def lattice_system(sg_number):
    for top, name in ((2, "triclinic"), (15, "monoclinic"), (74, "orthorhombic"), (142, "tetragonal"),
                      (167, "trigonal"), (194, "hexagonal"), (230, "cubic")):
        if sg_number <= top:
            return name


def hexagonal_axes(cellpar):
    a, b, c, al, be, ga = cellpar
    return abs(a - b) < 1e-3 * a and abs(al - 90) < 0.01 and abs(be - 90) < 0.01 and abs(ga - 120) < 0.01


def fam_label(key):
    return "{" + "".join(str(x) for x in key) + "}"


def four_index(key):
    h, k, l = key
    return "{" + "".join(str(x) for x in (h, k, -(h + k), l)) + "}"


def small_integers(v, max_mult=6, tol_deg=3.0):
    """Nearest small-integer direction to v (sign chosen so the largest component is positive)."""
    v = np.asarray(v, float)
    v = v / np.abs(v).max()
    if v[np.argmax(np.abs(v))] < 0:
        v = -v
    for m in range(1, max_mult + 1):
        u = np.round(v * m)
        if not u.any():
            continue
        g = math.gcd(math.gcd(int(abs(u[0])), int(abs(u[1]))), int(abs(u[2])))
        u = u / g
        cos = abs(u @ v) / (np.linalg.norm(u) * np.linalg.norm(v))
        if math.degrees(math.acos(min(1.0, cos))) < tol_deg:
            return [int(x) for x in u]
    return None


def run_one(path, stretch=(1.0, 1.0, 1.0)):
    c, n_atoms = crystal_in_file_setting(path)
    absence_ops = (c.rotations, c.translations)
    if tuple(stretch) != (1.0, 1.0, 1.0):
        # Phase 1b: scale a, b, c with the atoms at fixed fractional coordinates; the absences
        # stay those of the original operations (Proposition 14), the families come from the
        # operations that still keep the new metric (Proposition 15)
        L2 = c.lattice * np.asarray(stretch, float)[:, None]
        G2 = L2 @ L2.T
        keep = [k for k, R in enumerate(c.rotations) if np.allclose(R.T @ G2 @ R, G2, atol=2e-3 * G2.diagonal().max())]
        c = Crystal(name=c.name, lattice=L2, frac=c.frac, numbers=c.numbers, spacegroup=c.spacegroup, sg_number=c.sg_number,
                    rotations=c.rotations[keep], translations=c.translations[keep], symprec=c.symprec,
                    used_hydrogen=c.used_hydrogen)
    L = c.lattice
    cellpar = [float(x) for x in np.r_[np.linalg.norm(L, axis=1),
               [math.degrees(math.acos(np.clip(L[i] @ L[j] / np.linalg.norm(L[i]) / np.linalg.norm(L[j]), -1, 1)))
                for i, j in ((1, 2), (0, 2), (0, 1))]]]
    faces = enumerate_faces(c, MAX_INDEX, absence_ops=absence_ops)
    groups = {}
    for f in faces.values():
        groups.setdefault(f.family, []).append(f)
    fams = [dict(key=k, members=v, d=v[0].d, order=v[0].order, d_eff=v[0].d_eff, mult=len(v)) for k, v in groups.items()]
    fams.sort(key=lambda F: (-round(F["d_eff"], 6), -F["mult"], tuple(-x for x in F["key"])))
    fams = fams[:N_FAMILIES]
    dmax = fams[0]["d_eff"]
    normals, dists, tags = [], [], []
    for F in fams:
        F["R"] = dmax / F["d_eff"]
        for f in F["members"]:
            normals.append(f.normal); dists.append(F["R"]); tags.append(fam_label(F["key"]))
    s = Shape(normals, dists, tags)
    total = sum(f["area"] for f in s.faces)
    frac = {}
    for f in s.faces:
        frac[f["tag"]] = frac.get(f["tag"], 0.0) + f["area"] / total
    lam, vec = np.linalg.eigh(s.gyration())
    order = np.argsort(lam)[::-1]
    lam, vec = lam[order], vec[:, order]
    w = np.sqrt(lam)
    ba, cb = w[1] / w[0], w[2] / w[1]
    habit = ("equant" if cb >= ZINGG else "plate") if ba >= ZINGG else ("rod" if cb >= ZINGG else "lath")
    Linv = np.linalg.inv(L)
    long_uvw = small_integers(vec[:, 0] @ Linv)        # r = u L  ->  u = r L^-1
    flat_hkl = small_integers(L @ vec[:, 2])           # n = h B  ->  h = n B^-1 = L n
    hexa = hexagonal_axes(cellpar)
    out_fams = []
    for F in fams:
        out_fams.append(dict(label=fam_label(F["key"]), four_index=four_index(F["key"]) if hexa else None,
                             hkl=list(F["key"]), multiplicity=F["mult"], d=round(F["d"], 5), order=F["order"],
                             d_eff=round(F["d_eff"], 5), R=round(F["R"], 6),
                             area_fraction=round(frac.get(fam_label(F["key"]), 0.0), 6)))
    return dict(file=os.path.basename(path), stretch=list(stretch), sha256=hashlib.sha256(open(path, "rb").read()).hexdigest(),
                n_atoms=n_atoms, cell=[round(x, 4) for x in cellpar], spacegroup=c.spacegroup, sg_number=int(c.sg_number),
                lattice_system=lattice_system(c.sg_number), operations=int(len(c.rotations)),
                symmetry_with_hydrogen=bool(c.used_hydrogen), hexagonal_axes=hexa,
                families=out_fams, n_faces=len(s.faces), habit=habit,
                radii=[round(float(x), 6) for x in w / w[0]], b_over_a=round(float(ba), 6), c_over_b=round(float(cb), 6),
                long_axis_uvw=long_uvw, flat_face_hkl=flat_hkl,
                sphericity=round(float(s.sphericity()), 6))


# Phase 1b cases: the same file with one axis scaled, to show rods and plates from one framework
STRETCHED = [("MOF5", (1, 1, 0.25)), ("MOF5", (1, 1, 2.5)), ("MgMOF-74", (1, 1, 3.0))]


def main():
    names = sorted(f for f in os.listdir(CIFDIR) if f.endswith(".cif"))
    jobs = [(n, (1.0, 1.0, 1.0)) for n in names] + [(n + ".cif", tuple(float(x) for x in st)) for n, st in STRETCHED]
    res = {}
    for n, st in jobs:
        r = run_one(os.path.join(CIFDIR, n), st)
        key = n[:-4] if st == (1.0, 1.0, 1.0) else n[:-4] + "@" + "x".join(f"{x:g}" for x in st)
        res[key] = r
        n = key
        top = ", ".join(f"{F['label']} {F['area_fraction']:.2f}" for F in r["families"] if F["area_fraction"] > 0.01)
        print(f"{n:22s} {r['spacegroup']:9s} {r['lattice_system']:12s} {r['habit']:6s} b/a={r['b_over_a']:.3f} "
              f"c/b={r['c_over_b']:.3f} long[uvw]={r['long_axis_uvw']} flat(hkl)={r['flat_face_hkl']}  {top}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w"), indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
