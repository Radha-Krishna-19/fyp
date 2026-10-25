"""Water-capped surfaces: the step from a vacuum cut to a surface that meets solvent.

Cutting a MOF slab breaks metal-carboxylate (or metal-imidazolate) bonds. In vacuum the
two new faces carry bare metal sites and bare carboxylate O (or imidazolate N). In a
synthesis those sites are capped by water, acid or solvent; the laboratory data show that
this capping is what selects the crystal shape. Here every broken bond is healed with one
water molecule, split heterolytically:
    dangling carboxylate O (or imidazolate N)  ->  O-H (N-H)
    under-coordinated metal                     ->  M-OH
so a slab with n broken bonds gains n H2O and
    gamma_water = (E_capped - N_bulk * e_bulk - n * E_H2O) / (2 A).
E_H2O is the CHGNet energy of one relaxed isolated water molecule. A negative value means
hydrolysing that face releases energy. The capping positions are rough guesses; CHGNet
relaxation fixes the geometry.

Only slabs in which the number of dangling O/N equals the number of missing metal bonds
are capped; otherwise the slab is reported as 'unbalanced' and skipped.
"""
import numpy as np
from pymatgen.core import Lattice, Molecule, Structure

METALS = {"Zn", "Cu", "Zr", "Mg", "Co", "Ni", "Fe"}
M_X_CUT = 2.5          # metal-O / metal-N bond length cutoff, A
OH, MO = 0.97, 1.95    # O-H and metal-O(H) distances placed before relaxation


def _neighbors(struct, cutoff=2.6):
    return struct.get_all_neighbors(cutoff)


def metal_coordination(struct):
    """Number of O/N within M_X_CUT for each metal site."""
    nbs = _neighbors(struct)
    out = {}
    for i, s in enumerate(struct):
        if s.specie.symbol in METALS:
            out[i] = [n for n in nbs[i] if n.specie.symbol in ("O", "N") and n.nn_distance <= M_X_CUT]
    return out


def bulk_reference_counts(bulk):
    """Typical metal coordination number (per element) and whether ligand O/N bind metals."""
    coord = metal_coordination(bulk)
    cn = {}
    for i, lst in coord.items():
        cn.setdefault(bulk[i].specie.symbol, []).append(len(lst))
    return {el: int(round(np.median(v))) for el, v in cn.items()}


def cap_with_water(slab, bulk):
    """Return (capped Structure, n_water, info) or (None, 0, info) if unbalanced."""
    cn_ref = bulk_reference_counts(bulk)
    nbs = _neighbors(slab)
    coord = metal_coordination(slab)
    missing = {i: cn_ref[slab[i].specie.symbol] - len(lst) for i, lst in coord.items()}
    missing = {i: m for i, m in missing.items() if m > 0}
    # dangling ligand atoms: carboxylate O bonded to C but to no metal; imidazolate N likewise
    dangling = []
    for i, s in enumerate(slab):
        el = s.specie.symbol
        if el not in ("O", "N"):
            continue
        has_c = [n for n in nbs[i] if n.specie.symbol == "C" and n.nn_distance <= 1.6]
        has_m = [n for n in nbs[i] if n.specie.symbol in METALS and n.nn_distance <= M_X_CUT]
        has_h = [n for n in nbs[i] if n.specie.symbol == "H" and n.nn_distance <= 1.15]
        if has_c and not has_m and not has_h:
            # imidazolate N has two C neighbours and one metal in bulk; carboxylate O has one C
            dangling.append((i, has_c))
    n_missing = int(sum(missing.values()))
    info = {"missing_metal_bonds": n_missing, "dangling_ligand_atoms": len(dangling)}
    if n_missing != len(dangling) or n_missing == 0:
        info["status"] = "unbalanced" if n_missing != len(dangling) else "nothing_to_cap"
        return None, 0, info
    species = [s.specie.symbol for s in slab]
    coords = [s.coords.copy() for s in slab]
    # H on each dangling O/N, pointing away from its carbon neighbour(s)
    for i, cs in dangling:
        x = slab[i].coords
        away = sum((x - c.coords) / np.linalg.norm(x - c.coords) for c in cs)
        away /= np.linalg.norm(away)
        species.append("H"); coords.append(x + OH * away)
    # OH on each missing metal site, opposite the remaining ligands
    for i, m in missing.items():
        x = slab[i].coords
        rest = coord[i]
        base = -sum((n.coords - x) / np.linalg.norm(n.coords - x) for n in rest) if rest else np.array([0, 0, 1.0])
        base /= np.linalg.norm(base)
        for k in range(m):
            # spread several missing sites by a small rotation about z
            ang = 0.6 * k
            rot = np.array([[np.cos(ang), -np.sin(ang), 0], [np.sin(ang), np.cos(ang), 0], [0, 0, 1]])
            d = rot @ base
            o = x + MO * d
            species += ["O", "H"]; coords += [o, o + OH * d]
    capped = Structure(slab.lattice, species, coords, coords_are_cartesian=True)
    info["status"] = "capped"
    return capped, n_missing, info


def water_energy(model):
    """CHGNet energy (eV) of one relaxed H2O in a 15 A box."""
    from chgnet.model import StructOptimizer
    mol = Molecule(["O", "H", "H"], [[0, 0, 0], [0.757, 0.586, 0], [-0.757, 0.586, 0]])
    box = mol.get_boxed_structure(15, 15, 15)
    res = StructOptimizer(model=model).relax(box, fmax=0.02, steps=300, relax_cell=False, verbose=False)
    return float(res["trajectory"].energies[-1])
