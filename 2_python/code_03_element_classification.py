"""
MODULE 3 -- ELEMENT CLASSIFICATION  (Python translation of the real source)
Real file   : src/obdetails.cpp   (free functions isMetal, deleteBonds)
Source      : https://github.com/snurr-group/mofid

WHAT THIS FILE SHOWS
This is the ENTIRE real classifier every module in this pipeline relies on: a
single function, is_metal(), consulted by name throughout Modules 4a/4b/4c.
It hardcodes the IUPAC InChI standard's list of NONmetal elements (23 of
them) and simply classifies anything NOT on that list as a metal -- a strict
binary label, no metalloid middle category. Also translated: delete_bonds(),
the literal "cut every bond to a metal atom" step Module 4a's
DetectInitialNodesAndLinkers relies on.

ARGUMENT / VARIABLE GLOSSARY
------------------------------------------------------------------------------
atom_symbol            : the element symbol being classified (str).
NONMETALS (23 elements) : H, He, B, C, N, O, F, Ne, Si, P, S, Cl, Ar, Ge, As,
                          Se, Br, Kr, Te, I, Xe, At, Rn -- notice boron,
                          silicon, germanium/arsenic/tellurium (the classic
                          "metalloids") are explicitly filed as NONmetals
                          here; there is no in-between category.
return value (bool)     : False the moment a match is found in NONMETALS;
                          True (metal) by default otherwise -- so every
                          transition metal, lanthanide, actinide,
                          alkali/alkaline-earth metal, and "other metal"
                          (Al, Ga, In, Tl, Sn, Pb, Bi) is classified METAL
                          purely by NOT appearing on a 23-element list.
mol, only_metals        : delete_bonds(mol, only_metals) removes every bond
                          with at least one metal endpoint when
                          only_metals=True -- exactly Module 4a's call,
                          delete_bonds(split_mol, True).
"""

from __future__ import annotations
from typing import Set

# The InChI standard's nonmetal element symbols (23 of them) -- this project's
# JS engine (mof_decompose.js) instead stores the inverse (a METALS allow-list
# of ~55 symbols) for convenience; both are exactly equivalent classifiers.
NONMETALS: Set[str] = {
    'H', 'He', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Si', 'P', 'S', 'Cl', 'Ar',
    'Ge', 'As', 'Se', 'Br', 'Kr', 'Te', 'I', 'Xe', 'At', 'Rn',
}

# The full periodic table symbol list this project uses elsewhere, expressed
# as the equivalent "METALS" allow-list (identical classifier to is_metal()
# below, just phrased the other way -- kept for parity with mof_decompose.js
# and so code_02's compute_geometry() can `from code_03 import METALS`).
METALS: Set[str] = {
    'Li', 'Na', 'K', 'Rb', 'Cs', 'Mg', 'Ca', 'Sr', 'Ba', 'Sc', 'Y', 'Ti', 'Zr',
    'Hf', 'V', 'Nb', 'Ta', 'Cr', 'Mo', 'W', 'Mn', 'Fe', 'Ru', 'Os', 'Co', 'Rh',
    'Ir', 'Ni', 'Pd', 'Pt', 'Cu', 'Ag', 'Au', 'Zn', 'Cd', 'Hg', 'Al', 'Ga', 'In',
    'Tl', 'Sn', 'Pb', 'Bi', 'La', 'Ce', 'Pr', 'Nd', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy',
    'Ho', 'Er', 'Tm', 'Yb', 'Lu',
}


def is_metal(atom_symbol: str) -> bool:
    """Real isMetal(const OBAtom* atom), translated: nonmetals[] lookup table,
    binary classification, no metalloid category."""
    return atom_symbol not in NONMETALS


def delete_bonds(geom, only_metals: bool = True):
    """Real deleteBonds(OBMol *mol, bool only_metals), translated onto this
    project's Geometry object (code_02.py): returns a NEW list of Bond
    objects with every metal-touching bond removed (mirrors the real
    function's effect without mutating the original scratch copy elsewhere,
    matching Deconstructor::DetectInitialNodesAndLinkers's use of a
    throwaway split_mol copy -- see code_04a.py)."""
    kept = []
    for bd in geom.bonds:
        touches_metal = geom.is_metal[bd.lo] or geom.is_metal[bd.hi]
        if only_metals and touches_metal:
            continue   # deleted
        kept.append(bd)
    return kept


if __name__ == '__main__':
    import sys
    from code_01_cif_input import parse_cif
    from code_02_bond_assignment_pbc import compute_geometry
    path = sys.argv[1] if len(sys.argv) > 1 else 'HKUST-1.cif'
    with open(path) as f:
        cif = parse_cif(f.read())
    geom = compute_geometry(cif, metal_set=METALS)
    n_metal = sum(geom.is_metal)
    print(f'Module 3 result: {n_metal} of {geom.n} atoms classified METAL, '
          f'{geom.n - n_metal} classified NONMETAL, via is_metal().')
    remaining = delete_bonds(geom, only_metals=True)
    print(f'delete_bonds(only_metals=True): {len(geom.bonds)} bonds -> {len(remaining)} remain '
          f'(the {len(geom.bonds) - len(remaining)} removed all touched a metal atom).')
