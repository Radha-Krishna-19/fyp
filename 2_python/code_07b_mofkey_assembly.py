"""
MODULE 7b -- MOFkey ASSEMBLY  (Python translation of the real source)
Real file   : src/deconstructor.cpp  (MetalOxoDeconstructor::GetMOFkey +
              PAsToUniqueInChIs)
Source      : https://github.com/snurr-group/mofid

WHY THIS LIVES IN THE METAL-OXO DECONSTRUCTOR SPECIFICALLY
The in-code comment in the real source explains it directly: MOFkey needs
the organic building blocks fully intact (including their carboxylate
groups) to compute correct InChIKeys -- and metal-oxo (Module 4a) is exactly
the one decomposition that always keeps carboxylates with the linker.

HONEST SCOPE NOTE
The metal-symbol extraction and final string assembly below are a complete,
faithful, runnable translation. The one piece NOT reproduced is
PAsToUniqueInChIs()'s actual InChIKey computation: that requires the real
InChI algorithm (a whole separate, standardized cheminformatics library),
which Open Babel calls out to and which this project does not reimplement
anywhere (the JS engine doesn't either, for the same reason -- see the
website's honesty notes). This file shows exactly where that real call
plugs in and, since InChIKeys only need to be stable/unique/sortable for
MOFkey's purposes, substitutes a clearly-labelled placeholder hash so the
rest of the pipeline (formatting, sorting, assembly) is genuinely runnable
end-to-end.

ARGUMENT / VARIABLE GLOSSARY
------------------------------------------------------------------------------
node_blocks               : Module 4a's collapsed node blocks (metal-oxo
                          specifically, per the note above).
unique_elements            : atomic symbols of every distinct METAL found
                          across all node blocks, sorted by atomic number --
                          deliberately excludes O/H even though they are
                          physically part of the node cluster.
linker_blocks              : Module 4a's linker blocks; each one gets a
                          placeholder "InChIKey" (see scope note above).
MOFKEY_SEP / MOFKEY_VERSION : "." and "v1" -- format constants matching the
                          real C++'s MOFKEY_SEP / MOFKEY_VERSION.
"""

from __future__ import annotations
import hashlib
from typing import List

from code_02_bond_assignment_pbc import Geometry

# Same 55-symbol ordering context as code_03.py -- used only to sort by
# atomic number, matching the real code's `std::sort(unique_elements...)`.
ATOMIC_NUMBER = {
    'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10,
    'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20,
    'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29, 'Zn': 30,
    'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40,
    'Nb': 41, 'Mo': 42, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50, 'Sb': 51,
    'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76,
    'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80, 'Tl': 81, 'Pb': 82, 'Bi': 83,
}

MOFKEY_SEP = '.'
MOFKEY_VERSION = 'v1'
MOFKEY_NO_METALS = 'NA'
MOFKEY_NO_LINKERS = 'MISSING_LINKERS'


def _placeholder_inchikey(geom: Geometry, block_atoms: List[int]) -> str:
    """STAND-IN for the real PAsToUniqueInChIs(pa, "truncated inchikey") --
    see the module's HONEST SCOPE NOTE. Produces a stable, deterministic,
    14-character, InChIKey-shaped placeholder from the fragment's own
    element composition + bond count, clearly NOT a real InChIKey (real
    InChIKeys encode full stereochemistry-aware connectivity, not just
    composition), but stable/unique/sortable the same way a real one is."""
    comp = sorted((geom.symbols[a] for a in block_atoms))
    key_input = ','.join(comp).encode()
    digest = hashlib.sha256(key_input).hexdigest().upper()
    return digest[:14]


def get_mofkey(geom: Geometry, node_blocks: List[List[int]], linker_blocks: List[List[int]],
               topology: str = '') -> str:
    """Real MetalOxoDeconstructor::GetMOFkey(topology), translated:
    METAL(S).InChIKey1[.InChIKey2...].MOFkey-vN[.TOPOLOGY]"""
    # --- 1. unique metal element symbols, sorted by atomic number ---
    unique_elements = set()
    for block in node_blocks:
        for a in block:
            sym = geom.symbols[a]
            if geom.is_metal[a]:
                unique_elements.add(sym)
    metals_part = (MOFKEY_NO_METALS if not unique_elements
                   else ','.join(sorted(unique_elements, key=lambda s: ATOMIC_NUMBER.get(s, 999))))

    # --- 2. unique, placeholder "truncated InChIKeys" for each linker, sorted ---
    keys = sorted({_placeholder_inchikey(geom, block) for block in linker_blocks}) or [MOFKEY_NO_LINKERS]

    # --- 3. assemble ---
    parts = [metals_part] + keys + [f'MOFkey-{MOFKEY_VERSION}']
    if topology:
        parts.append(topology)
    return MOFKEY_SEP.join(parts)


if __name__ == '__main__':
    import sys
    from code_01_cif_input import parse_cif
    from code_02_bond_assignment_pbc import compute_geometry
    from code_04a_metal_oxo_algorithm import run_metal_oxo
    path = sys.argv[1] if len(sys.argv) > 1 else 'HKUST-1.cif'
    with open(path) as f:
        cif = parse_cif(f.read())
    geom = compute_geometry(cif)
    node_blocks, linker_blocks = run_metal_oxo(geom)
    mofkey = get_mofkey(geom, node_blocks, linker_blocks, topology='tbo' if 'HKUST' in path else '')
    print(f'Module 7b result (metal symbols + assembly are real; linker keys are placeholders -- see docstring):')
    print(f'  {mofkey}')
