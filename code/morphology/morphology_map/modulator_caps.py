"""Condition-dependent surface energies with Kshitij's slabs: water caps vs formate (modulator) caps.

For the lowest-energy water-capped termination of each face (Kshitij's pipeline, static CHGNet),
the same slab is capped a second way: every broken metal-ligand bond gets HCOO- on the metal and
H+ on the ligand donor (formic acid split heterolytically), instead of OH- and H+.

Per-site exchange energy (water cap -> formate cap) on face F:
    eps_F = [E_slab(formate) - E_slab(water) - n_F (E_HCOOH - E_H2O)] / n_F
Langmuir sites + Gibbs adsorption equation give the surface energy as a function of the
modulator's chemical potential relative to water, dmu = kT ln(a_modulator / a_water):
    gamma_F(dmu) = gamma_F(water) - rho_F kT ln(1 + exp((dmu - eps_F)/kT)),   rho_F = n_F / (2 A_F)
so the shape at each dmu is a point on the morphology map. Static energies, unrelaxed caps:
a screening calculation, not a converged number.
usage: python modulator_caps.py <mofwulff dir> <cif dir> <quick results dir>"""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
REPO_ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..', '..'))
LAB_CSV = _os.path.join(REPO_ROOT, 'data', 'experimental_morphology', 'dataset', 'experimental_morphology.csv')
import sys, json, numpy as np, torch; torch.set_num_threads(2)
sys.path.insert(0, sys.argv[1]); import mofwulff as mw
from pymatgen.core import Structure
from ase.build import molecule
from pymatgen.io.ase import AseAtomsAdaptor
from cubic_wulff import shape

CIFD, QDIR = sys.argv[2], sys.argv[3]
eng = mw.Engine(device="cpu")


def frame(d, ref):
    p = np.cross(d, ref); p /= np.linalg.norm(p); return p


def heal_formate(sl, miss):
    st = sl["slab"]; species = [x.specie.symbol for x in st]; coords = [x.coords.copy() for x in st]
    nbs = st.get_all_neighbors(2.6); n_cap = 0
    for i, m in enumerate(miss):
        k = m.get("ML", 0) + m.get("MO", 0)
        if not k: continue
        x = st[i].coords; occ = [n.coords - x for n in nbs[i] if n.nn_distance < 2.6]
        others = np.array(coords); others = others[np.linalg.norm(others - x, axis=1) > 0.1]
        if mw.is_metal(species[i]):
            for d in mw._best_dirs(x, occ, k, 2.05, others, 1.6):
                best = None
                for t in np.linspace(0, 2 * np.pi, 12, endpoint=False):
                    a = frame(d, np.array([np.cos(t), np.sin(t), 0.37]))
                    O1 = x + 2.05 * d; C = O1 + 1.27 * (np.cos(np.radians(55)) * d + np.sin(np.radians(55)) * a)
                    u = (O1 - C) / np.linalg.norm(O1 - C); v = a - np.dot(a, u) * u; v /= np.linalg.norm(v)
                    rot = lambda ang: np.cos(ang) * u + np.sin(ang) * v
                    O2 = C + 1.25 * rot(np.radians(125)); H = C + 1.10 * rot(np.radians(-118))
                    new = np.array([O1, C, O2, H]); allo = np.array(coords)
                    allo = allo[np.linalg.norm(allo - x, axis=1) > 0.1]
                    clear = np.min(np.linalg.norm(allo[:, None, :] - new[None, 1:, :], axis=2))
                    if best is None or clear > best[0]: best = (clear, new)
                species += ["O", "C", "O", "H"]; coords += list(best[1]); occ.append(d); n_cap += 1
        else:
            for d in mw._best_dirs(x, occ, k, 0.98, others, 1.3):
                species.append("H"); coords.append(x + 0.98 * d); occ.append(d)
    return Structure(st.lattice, species, coords, coords_are_cartesian=True), n_cap


def mol_energy(name):
    a = molecule(name); a.center(vacuum=7.5); a.pbc = True
    s = AseAtomsAdaptor.get_structure(a)
    e, _, _, _ = eng.relax(s, 0.02, 300); return e


E_H2O, E_HCOOH = mol_energy("H2O"), mol_energy("HCOOH")
print("E_H2O", round(E_H2O, 4), "E_HCOOH", round(E_HCOOH, 4))
kT = 0.0353  # eV, 410 K (typical solvothermal synthesis temperature)
out = {}
for name, cif in [("HKUST-1", "Cu-BTC.cif"), ("UiO-66", "UIO-66.cif"), ("ZIF-8", "ZIF-8.cif")]:
    info = mw.standardize(f"{CIFD}/{cif}", 0.1, "majority")
    fams = mw.face_families(info["conv"], info["rotations"], 1, 4)
    e_bulk = eng.static([info["prim"]])[0] / len(info["prim"])
    res = {}
    for f in fams:
        best = None
        for m in mw.block_slabs(info["conv"], info["prim"], f["rep"], 15, 15, 0.3):
            miss, tot = mw.broken_bonds(m)
            stw, nw, status = mw.heal(m, miss)
            if stw is None: continue
            ew = eng.static([stw])[0]
            gw = mw.gamma_J_m2(ew, len(m["slab"]), e_bulk, nw, E_H2O, m["area_A2"])
            if best is None or gw < best["gamma_water"]:
                best = dict(m=m, miss=miss, gamma_water=gw, E_water=ew, n=nw)
        m = best["m"]; stf, nf = heal_formate(m, best["miss"]); ef = eng.static([stf])[0]
        n = best["n"]; assert nf == n
        eps = (ef - best["E_water"] - n * (E_HCOOH - E_H2O)) / n
        rho = n / (2 * m["area_A2"])                       # sites per A^2 (both faces)
        gf_ref = mw.gamma_J_m2(ef, len(m["slab"]), e_bulk, n, E_HCOOH, m["area_A2"])
        res[f["key"]] = dict(gamma_water_J_m2=round(best["gamma_water"], 4), gamma_formate_ref_J_m2=round(gf_ref, 4),
                             n_sites=n, area_A2=round(m["area_A2"], 1), rho_sites_per_nm2=round(rho * 100, 3),
                             eps_exchange_eV=round(eps, 4), n_atoms_formate=len(stf))
        print(name, f["name"], res[f["key"]], flush=True)
    # shape along the chemical-potential axis
    path = []
    for dmu in np.linspace(-1.5, 1.5, 61):
        g = {k: v["gamma_water_J_m2"] - v["rho_sites_per_nm2"] / 100 * kT * np.log1p(np.exp((dmu - v["eps_exchange_eV"]) / kT)) * mw.EV_A2_TO_J_M2
             for k, v in res.items()}
        if min(g.values()) <= 0:
            path.append(dict(dmu=round(float(dmu), 3), shape="gamma<=0")); continue
        c, fr = shape(g["100"], g["110"], g["111"])
        path.append(dict(dmu=round(float(dmu), 3), x=round(g["110"] / g["100"], 4), y=round(g["111"] / g["100"], 4),
                         shape=c, fractions={k: round(v, 3) for k, v in fr.items()}))
    seq = [p["shape"] for p in path]; compact = [s for i, s in enumerate(seq) if i == 0 or s != seq[i - 1]]
    print(name, "shape sequence as the modulator chemical potential rises:", " -> ".join(compact), flush=True)
    out[name] = dict(faces=res, path=path, sequence=compact)
json.dump(dict(E_H2O=E_H2O, E_HCOOH=E_HCOOH, kT_eV=kT, results=out), open(_os.path.join(HERE, "modulator_caps_results.json"), "w"), indent=1)
