"""From crystal shape to gas access: what each face exposes, and how far gas must travel.

Run from anywhere:  python3 code/morphology/run_shape_adsorption.py
Reads  code/morphology/results/benchmark_mofs.json (structures and predicted shapes);
writes code/morphology/results/shape_adsorption.json.

1. Open area of a face. A face of family (hkl) is a lattice plane. We sample points on that plane over
   one 2D surface cell, at 24 positions spread through one interplanar spacing (a crystal can end at
   any of them), and call a point open if a probe sphere of radius r_p fits there:
       clearance(x) = min over atoms j ( |x - x_j| - R_j )  >  r_p
   R_j is the van der Waals radius (Bondi; 2.0 A for metals Bondi does not list, as in CCDC Mercury),
   r_p = 1.65 A (CO2, kinetic diameter 3.3 A) and 1.82 A (N2, 3.64 A). Per face we report, at the
   termination where the crystal is most likely to end (the plane offset with the lowest UFF cleavage
   energy, mofmorph.forcefield.surface_energy), the open fraction of the plane, the number of separate
   openings per nm^2, and the largest opening, 2 x max(clearance): the diameter of the largest sphere
   centred on the plane. Averaged over all 24 positions the open fraction equals the porosity of the
   bulk and is the same for every face, so only the termination value carries face information; the
   range over the 24 positions is reported alongside.
2. Open surface of a crystal = sum over families of (share of surface) x (open fraction).
3. Diffusion length. At a fixed crystal volume V, the characteristic diffusion length is L = V/A.
   For any shape A = (36 pi V^2)^(1/3) / Psi (Psi = sphericity), so
       L = Psi V^(1/3) / (36 pi)^(1/3),
   and the time to fill a crystal by diffusion scales as L^2 / D. A less round shape (lower Psi) has a
   shorter L and fills faster. The initial uptake rate per unit volume is proportional to
   (A/V) x (open surface fraction); we report it relative to the same MOF's predicted shape.
Limits: geometry only (rigid framework, no adsorption energies, no surface relaxation or capping);
the windows are 2D sections, not a full pore network; these are accessibility indicators, not uptakes.
"""
import os, sys, json, math, time, warnings
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'morphology_map'))
warnings.filterwarnings('ignore')
import numpy as np
from scipy.spatial import cKDTree
from scipy import ndimage
from ase.io import read

BENCH = os.path.join(HERE, 'results', 'benchmark_mofs.json')
OUT = os.path.join(HERE, 'results', 'shape_adsorption.json')
BONDI = {'H': 1.20, 'C': 1.70, 'N': 1.55, 'O': 1.52, 'F': 1.47, 'Cl': 1.75, 'S': 1.80, 'Mg': 1.73, 'Cu': 1.40, 'Zn': 1.39, 'Ni': 1.63}
METAL_DEFAULT = 2.0
PROBES = {'CO2': 1.65, 'N2': 1.82}
N_OFFSETS, STEP = 24, 0.3


def radii(symbols):
    return np.array([BONDI.get(s, METAL_DEFAULT) for s in symbols])


def plane_cell(hkl):
    """Two shortest independent integer lattice vectors u, v with h.u = h.v = 0 (the 2D surface cell)."""
    h = np.array(hkl)
    cand = [np.array(u) for u in np.ndindex(9, 9, 9)]
    cand = [u - 4 for u in cand]
    cand = [u for u in cand if u.any() and int(h @ u) == 0]
    return cand


def surface_cell(hkl, L):
    cand = plane_cell(hkl)
    cand.sort(key=lambda u: np.linalg.norm(u @ L))
    u = cand[0]
    for v in cand[1:]:
        if np.linalg.norm(np.cross(u @ L, v @ L)) > 1e-6:
            # the pair must span the 2D lattice: area equals the primitive 2D cell area
            return u, v
    raise ValueError('no surface cell')


def primitive_area(hkl, L):
    # area of the primitive 2D cell of the (hkl) plane = V_cell * |h B| / gcd ... = V / d for primitive h
    V = abs(np.linalg.det(L)); B = np.linalg.inv(L).T
    g = np.array(hkl) @ B
    return V * np.linalg.norm(g)


def face_access(atoms, hkl, term_t):
    L = np.array(atoms.cell[:]); fr = atoms.get_scaled_positions() % 1.0; R = radii(atoms.get_chemical_symbols())
    # periodic tree: atoms in the 3x3x3 block around the cell
    shifts = np.array([[i, j, k] for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)])
    allf = (fr[None, :, :] + shifts[:, None, :]).reshape(-1, 3)
    allR = np.tile(R, len(shifts))
    tree = cKDTree(allf @ L)
    h = np.array(hkl, float)
    u, v = surface_cell(hkl, L)
    # pick v so that (u, v) spans the primitive 2D lattice: area must equal V |hB|
    target = primitive_area(hkl, L)
    for cand in plane_cell(hkl):
        if abs(np.linalg.norm(np.cross(u @ L, cand @ L)) - target) < 1e-3 * target:
            v = cand
            break
    U, Vv = u @ L, v @ L
    area = np.linalg.norm(np.cross(U, Vv))
    nu, nv = max(8, int(np.linalg.norm(U) / STEP)), max(8, int(np.linalg.norm(Vv) / STEP))
    # a point on the plane h.f = t is f0 = t h / |h|^2; t = s / d for the Cartesian offset s along the normal
    a = np.arange(nu)[:, None] / nu; b = np.arange(nv)[None, :] / nv

    def sample(t):
        f0 = t * h / (h @ h)
        F = f0[None, None, :] + a[:, :, None] * u[None, None, :] + b[:, :, None] * v[None, None, :]
        X = (F.reshape(-1, 3) % 1.0) @ L
        dist, idx = tree.query(X, k=24)
        clear = (dist - allR[idx]).min(axis=1).reshape(nu, nv)
        out = {}
        for name, rp in PROBES.items():
            open_ = clear > rp
            lab, n = ndimage.label(open_)
            parent = list(range(n + 1))
            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]; x = parent[x]
                return x
            for i in range(nu):                     # merge openings that continue across the cell edge
                if lab[i, 0] and lab[i, -1]:
                    parent[find(lab[i, 0])] = find(lab[i, -1])
            for j in range(nv):
                if lab[0, j] and lab[-1, j]:
                    parent[find(lab[0, j])] = find(lab[-1, j])
            roots = {find(k) for k in range(1, n + 1)}
            out[name] = (float(open_.mean()), len(roots) / (area / 100.0), float(2 * clear.max()))
        return out

    scan = [sample((o + 0.5) / N_OFFSETS) for o in range(N_OFFSETS)]
    term = sample(term_t % 1.0)
    return dict(surface_cell_area_A2=round(float(area), 2), termination_t=round(float(term_t % 1.0), 4),
                **{name: dict(open_fraction=round(term[name][0], 4), windows_per_nm2=round(term[name][1], 4),
                              largest_opening_A=round(term[name][2], 2),
                              open_fraction_range_over_positions=[round(min(x[name][0] for x in scan), 4), round(max(x[name][0] for x in scan), 4)],
                              open_fraction_mean_over_positions=round(float(np.mean([x[name][0] for x in scan])), 4))
                   for name in PROBES})


def L_over_V13(psi):
    return psi / (36 * math.pi) ** (1 / 3)


def main():
    t0 = time.time()
    B = json.load(open(BENCH))
    import run_phase4 as P4
    from cubic_wulff import wulff_areas
    out = {}
    for mof, p in B['predictions'].items():
        if not p.get('file') or p['structure'] == 'stand-in':
            continue
        path = os.path.join(REPO, p['file'])
        rec = dict(structure=p['structure'])
        if 'uff' in p:
            atoms, _ = P4.conventional_atoms(path)
            faces = {'100': (1, 0, 0), '110': (1, 1, 0), '111': (1, 1, 1)}
        else:
            atoms = read(path)
            from run_general_shape import run_one
            r = run_one(path)
            faces = {F['label'].strip('{}'): tuple(F['hkl']) for F in r['families'] if F['area_fraction'] > 0.01}
            rec['bfdh_shares'] = {F['label'].strip('{}'): F['area_fraction'] for F in r['families'] if F['area_fraction'] > 0.01}
            rec['bfdh_sphericity'] = r['sphericity']
        from mofmorph.forcefield import pair_list, pair_energies, surface_energy
        atoms.wrap()
        i, j, d, D, bonded, excl = pair_list(atoms, rcut=12.0)
        cost = pair_energies(atoms, i, j, d, bonded, excl)
        rec['faces'] = {}
        # independent check of the plane sampling: the bulk open fraction from random 3D points must equal
        # each face's open fraction averaged over all plane positions
        rng = np.random.default_rng(20261113)
        Lc = np.array(atoms.cell[:]); frc = atoms.get_scaled_positions() % 1.0; Rr = radii(atoms.get_chemical_symbols())
        sh = np.array([[a, b, c] for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)])
        tr3 = cKDTree(((frc[None] + sh[:, None]).reshape(-1, 3)) @ Lc); RR = np.tile(Rr, len(sh))
        pts = rng.random((40000, 3)) @ Lc
        dd, ii = tr3.query(pts, k=24); cl = (dd - RR[ii]).min(axis=1)
        rec['bulk_open_fraction_3D'] = {name: round(float((cl > rp).mean()), 4) for name, rp in PROBES.items()}
        rec['largest_cavity_3D_A'] = round(float(2 * cl.max()), 2)
        for k, hkl in faces.items():
            gmin, s_off, dsp, _ = surface_energy(atoms, hkl, pairs=(i, j, D, cost))
            rec['faces'][k] = dict(hkl=list(hkl), uff_gamma=round(gmin, 5), **face_access(atoms, hkl, s_off / dsp))
        # crystal level
        shapes = {}
        if 'uff' in p:
            g = {}
            for lab, v in p['uff']['gamma'].items():
                k = lab.replace('{', '').replace('}', '').rstrip('+-')
                if k in ('100', '110', '111'):
                    g[k] = min(v, g.get(k, v))
            pure = {'cube': (1.0, 10.0, 10.0), 'octahedron': (10.0, 10.0, 1.0), 'rhombic dodecahedron': (10.0, 1.0, 10.0)}
            cand = dict(predicted_UFF=(g['100'], g['110'], g['111']), **pure)
            for name, (a, b, c) in cand.items():
                fr = wulff_areas(a, b, c)
                psi = sphericity_cubic(a, b, c)
                shapes[name] = dict(shares={k: round(v, 4) for k, v in fr.items()}, sphericity=round(psi, 4))
        else:
            shapes['predicted_BFDH'] = dict(shares=rec['bfdh_shares'], sphericity=rec['bfdh_sphericity'])
            shapes['sphere_of_same_volume'] = dict(shares=None, sphericity=1.0)
        ref = None
        for name, s in shapes.items():
            s['diffusion_length_per_V13'] = round(L_over_V13(s['sphericity']), 4)
            s['diffusion_length_um_for_1um3'] = s['diffusion_length_per_V13']
            if s['shares']:
                for probe in PROBES:
                    s[f'open_surface_{probe}'] = round(sum(s['shares'][k] * rec['faces'][k][probe]['open_fraction'] for k in s['shares'] if k in rec['faces']), 4)
                s['relative_initial_uptake_CO2'] = None
        base = next(iter(shapes.values()))
        for name, s in shapes.items():
            if s['shares'] and base['shares'] and base.get('open_surface_CO2'):
                # initial uptake per volume ~ (A/V) * open surface ; A/V = 1/L
                s['relative_initial_uptake_CO2'] = round((s['open_surface_CO2'] / s['diffusion_length_per_V13']) /
                                                         (base['open_surface_CO2'] / base['diffusion_length_per_V13']), 3)
                s['relative_fill_time'] = round((s['diffusion_length_per_V13'] / base['diffusion_length_per_V13']) ** 2, 3)
        rec['shapes'] = shapes
        out[mof] = rec
        print(mof, {k: {pr: (v[pr]['open_fraction'], v[pr]['windows_per_nm2'], v[pr]['largest_opening_A']) for pr in PROBES} for k, v in rec['faces'].items()}, flush=True)
        for name, s in shapes.items():
            print('    ', name, {k: v for k, v in s.items() if k != 'shares'})
    json.dump(dict(script='code/morphology/run_shape_adsorption.py', probes_A=PROBES, vdw_radii='Bondi; 2.0 A for unlisted metals',
                   offsets=N_OFFSETS, grid_A=STEP, mofs=out, seconds=round(time.time() - t0, 1)), open(OUT, 'w'), indent=1)
    print('wrote', OUT)


def sphericity_cubic(a, b, c):
    """Sphericity of the cubic Wulff shape with surface energies (a, b, c) for {100}, {110}, {111}."""
    from scipy.spatial import HalfspaceIntersection, ConvexHull
    from cubic_wulff import NORMALS
    pl = []
    for k, g in (('100', a), ('110', b), ('111', c)):
        for n in NORMALS[k]:
            pl.append(np.r_[n, -g])
    hs = HalfspaceIntersection(np.array(pl), np.zeros(3))
    hull = ConvexHull(hs.intersections)
    return math.pi ** (1 / 3) * (6 * hull.volume) ** (2 / 3) / hull.area


if __name__ == '__main__':
    main()
