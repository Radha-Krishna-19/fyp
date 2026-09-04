"""
MODULE 1 -- CIF FILE INPUT  (Python translation of the real C++ call site)
Real file   : src/sbu.cpp, function analyzeMOF()  (see code_00_pipeline_driver.py)
Source      : https://github.com/snurr-group/mofid

TRANSLATION NOTE
The real analyzeMOF() call is just:

    OBMol orig_mol
    if not importCIF(orig_mol, filename, False):
        print("Error reading file:", filename)
        return ""

...where importCIF() is Open Babel's own CIF format reader (C++, not part of
the snurr-group/mofid repo itself, and not exposed as a small standalone
function you could copy out). This file is therefore a from-scratch, pure
Python, dependency-free CIF reader that implements exactly the same CHEMICAL
CONTRACT importCIF() guarantees -- described in full below -- so the rest of
this Python translation (code_02 onward) has real, working input to run on.
It mirrors this project's own JS engine (mof_decompose.js's parseCIF()),
which was built for the identical reason (no CIF parser available at all in
the browser).

WHAT A CIF GUARANTEES (and does not) -- the chemically important part
------------------------------------------------------------------------------
Guaranteed present : _cell_length_a/b/c, _cell_angle_alpha/beta/gamma, and a
                      loop_ block with _atom_site_fract_x/y/z plus an element
                      column, for every atom of the ASYMMETRIC UNIT. Symmetry
                      operators (_symmetry_equiv_pos_as_xyz or
                      _space_group_symop_operation_xyz) must be applied to
                      each asymmetric-unit atom to reconstruct the full cell
                      -- unless the file is already pre-expanded to P1 (every
                      atom of the full cell listed directly), as most MOF
                      databases including CoRE MOF do.
NEVER present       : any bond, bond order, or connectivity whatsoever. This
                      is the single most important fact about the CIF format
                      for this whole project -- EVERY bond used by every
                      module downstream (2 through 7) is computationally
                      INFERRED, never read from the file.

ARGUMENT / VARIABLE GLOSSARY
------------------------------------------------------------------------------
text                : raw contents of the .cif file (str).
a,b,c,alpha,beta,gamma : the 6 real-space cell parameters (Angstrom / degrees).
cell_matrix          : 3x3 matrix converting fractional -> Cartesian coords,
                        built the same way Open Babel's OBUnitCell does.
sym_ops               : list of (fx,fy,fz) -> (fx',fy',fz') functions parsed
                        from the CIF's symmetry-operator loop (or just the
                        identity operator if the file has none / is P1).
asym_atoms            : the atoms exactly as listed in the file (one entry
                        per row of the _atom_site loop) -- the "asymmetric
                        unit" mentioned above.
expanded              : asym_atoms after applying every symmetry operator and
                        removing duplicate positions (TOL = 0.01 fractional
                        units) -- i.e. the full unit cell's worth of atoms,
                        exactly what importCIF() hands back in orig_mol.
"""

from __future__ import annotations
import math
import re
from dataclasses import dataclass, field
from typing import Callable, List, Tuple

# TOL -- how close two fractional coordinates must be before we treat them as
# THE SAME ATOM. Needed because applying symmetry operations regenerates atoms
# that were already present: e.g. an atom sitting exactly on a mirror plane maps
# onto itself. 0.01 in fractional units is roughly 0.2 A in a 20 A cell -- far
# smaller than any real bond, so it cannot merge two genuinely distinct atoms.
TOL = 0.01


@dataclass
class Atom:
    """One atom, stored the way a CIF stores it.

    el          chemical symbol, e.g. 'Cu', 'O', 'C'
    fx, fy, fz  FRACTIONAL coordinates -- each is a fraction (0 to 1) of the way
                along the corresponding cell edge, NOT a distance. Fractional
                coordinates are what a CIF stores, and they stay meaningful when
                the cell is non-cubic. To get real distances in angstroms you
                must multiply by the cell matrix (see ParsedCIF.cell_matrix).
    """
    el: str
    fx: float
    fy: float
    fz: float


@dataclass
class ParsedCIF:
    """Everything a CIF file actually contains -- and nothing more.

    a, b, c              the three unit-cell edge LENGTHS, in angstroms
    alpha, beta, gamma   the three angles BETWEEN those edges, in degrees
                         (alpha is between b and c, beta between a and c,
                         gamma between a and b -- the standard convention)
    cell_matrix          3x3 matrix whose ROWS are the cell edge vectors in
                         ordinary Cartesian space. Multiplying a fractional
                         coordinate by this converts it to angstroms.
    atoms                every atom in the cell, after symmetry expansion.

    NOTE WHAT IS ABSENT: there is no bond list. A CIF does not contain one.
    Every bond used anywhere in this project is INFERRED from distance in
    code_02. That is the single most important fact about this data format.
    """
    a: float; b: float; c: float
    alpha: float; beta: float; gamma: float
    cell_matrix: List[List[float]]
    atoms: List[Atom] = field(default_factory=list)


def _cell_par_to_matrix(a, b, c, alpha_deg, beta_deg, gamma_deg):
    """Convert the six cell parameters into a 3x3 matrix of edge vectors.

    WHY THIS IS NEEDED: fractional coordinates are convenient for storage but
    useless for measuring distance, because the cell may not be a cube. This
    matrix is what turns '0.28 of the way along edge a' into 'x = 12.3 A'.

    WHY THIS PARTICULAR FORM: there are infinitely many ways to orient a cell in
    space; we pick the standard LOWER-TRIANGULAR convention, which fixes the
    freedom by choosing:
        - edge a to lie along the x axis            -> a has no y or z component
        - edge b to lie in the xy plane             -> b has no z component
        - edge c takes whatever is left
    Open Babel's OBUnitCell uses the same construction, so our matrix matches
    the reference implementation exactly.

    Returns rows = [a_vector, b_vector, c_vector], each in angstroms.
    """
    # Trigonometry works in radians; CIF stores degrees.
    alpha, beta, gamma = (math.radians(x) for x in (alpha_deg, beta_deg, gamma_deg))

    # Edge a: along x by construction, so its whole length is the x component.
    ax, ay, az = a, 0.0, 0.0

    # Edge b: in the xy plane, at angle gamma to a. Standard resolution of a
    # vector into components -- length b, angle gamma from the x axis.
    bx, by, bz = b * math.cos(gamma), b * math.sin(gamma), 0.0

    # Edge c: the general case. Its x component follows from the angle beta
    # (between c and a). The y component is fixed by requiring the angle between
    # c and b to come out as alpha -- that requirement rearranges to this
    # expression. The z component is then whatever is left to make |c| correct.
    cx = c * math.cos(beta)
    cy = (c * (math.cos(alpha) - math.cos(beta) * math.cos(gamma))) / math.sin(gamma)

    # max(..., 0.0) guards against a tiny negative from floating-point error
    # when the cell is degenerate or the parameters are slightly inconsistent;
    # sqrt of a negative would crash for what is physically a rounding artefact.
    cz = math.sqrt(max(c * c - cx * cx - cy * cy, 0.0))

    return [[ax, ay, az], [bx, by, bz], [cx, cy, cz]]


def _parse_sym_op(op_str: str) -> Callable[[float, float, float], Tuple[float, float, float]]:
    """Turns a CIF symmetry string like 'x, -y+1/2, z+1/2' into a callable."""
    parts = [p.strip() for p in op_str.split(',')]

    def component(expr, x, y, z):
        expr = expr.replace(' ', '')
        value = 0.0
        for m in re.finditer(r'([+-]?)((?:\d+/\d+)|(?:\d*\.\d+)|(?:\d+))?(\*)?([xyzXYZ])?', expr):
            if m.group(0) == '':
                continue
            sign = -1.0 if m.group(1) == '-' else 1.0
            coef = 1.0
            if m.group(2):
                coef = (float(m.group(2).split('/')[0]) / float(m.group(2).split('/')[1])
                        if '/' in m.group(2) else float(m.group(2)))
            var = m.group(4).lower() if m.group(4) else None
            if var == 'x':
                value += sign * coef * x
            elif var == 'y':
                value += sign * coef * y
            elif var == 'z':
                value += sign * coef * z
            elif m.group(2):
                value += sign * coef
        return value

    def op(x, y, z):
        return component(parts[0], x, y, z), component(parts[1], x, y, z), component(parts[2], x, y, z)
    return op


def _wrap(v: float) -> float:
    """Fold a fractional coordinate back into the range [0, 1).

    WHY: applying a symmetry operation can push a coordinate outside the cell --
    'z + 1/2' applied to z = 0.7 gives 1.2, which is the same physical position
    as 0.2 one cell over. Because the crystal repeats, those are the same atom,
    so we normalise every coordinate into a single canonical cell.

    The final clamp handles the boundary case: 0.9999999 and 0.0 are the same
    position to within floating-point error, and if we left one at ~1.0 the
    de-duplication step below would treat it as a different atom and we would
    end up with a spurious duplicate on every cell face.
    """
    v = v % 1.0            # Python's % already returns non-negative for positive modulus,
    if v < 0:              # but be explicit -- this is cheap and the intent is clearer.
        v += 1.0
    if v > 1 - 1e-6:       # treat 0.999999... as exactly 0.0
        v -= 1.0
    return v


def parse_cif(text: str) -> ParsedCIF:
    """The Python equivalent of importCIF(&orig_mol, filename, False): reads
    cell parameters + symmetry, expands the asymmetric unit, and returns
    every atom's fractional coordinates -- with NO bonds, exactly as a real
    CIF and importCIF() itself would leave things at this stage."""
    lines = text.splitlines()

    def find_value(tag):
        for line in lines:
            if line.strip().lower().startswith(tag):
                return float(line.split()[1])
        return None

    a = find_value('_cell_length_a')
    b = find_value('_cell_length_b')
    c = find_value('_cell_length_c')
    alpha = find_value('_cell_angle_alpha')
    beta = find_value('_cell_angle_beta')
    gamma = find_value('_cell_angle_gamma')
    if None in (a, b, c, alpha, beta, gamma):
        raise ValueError('Could not find cell parameters in CIF (Module 1 contract violated).')

    sym_ops: List[Callable] = []
    atom_headers, atom_rows = None, []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.lower().startswith('loop_'):
            j = i + 1
            headers = []
            while j < len(lines) and lines[j].strip().startswith('_'):
                headers.append(lines[j].strip().lower())
                j += 1
            is_sym = any('_symmetry_equiv_pos_as_xyz' in h or '_space_group_symop_operation_xyz' in h for h in headers)
            is_atoms = any('_atom_site_fract_x' in h for h in headers)
            if is_sym:
                while j < len(lines):
                    t = lines[j].strip()
                    if t == '' or t.lower().startswith('loop_') or t.startswith('_') or t.lower().startswith('data_'):
                        break
                    if ',' in t:
                        candidate = t.split("'")[-2] if "'" in t else t
                        sym_ops.append(_parse_sym_op(candidate))
                    j += 1
            elif is_atoms:
                atom_headers = headers
                while j < len(lines):
                    t = lines[j].strip()
                    if t == '' or t.lower().startswith('loop_') or t.startswith('_') or t.lower().startswith('data_'):
                        break
                    atom_rows.append(t.split())
                    j += 1
            i = j
            continue
        i += 1

    if not atom_headers or not atom_rows:
        raise ValueError('Could not find an _atom_site loop with fractional coordinates in CIF.')

    idx = {h: k for k, h in enumerate(atom_headers)}
    i_type = idx.get('_atom_site_type_symbol')
    i_label = idx.get('_atom_site_label')
    i_x, i_y, i_z = idx['_atom_site_fract_x'], idx['_atom_site_fract_y'], idx['_atom_site_fract_z']

    def element_from_label(label: str) -> str:
        clean = re.sub(r'[^A-Za-z]', '', label)
        return (clean[:2].capitalize() if len(clean) > 1 and clean[1].islower() else clean[:1].upper()) or 'X'

    asym_atoms = []
    for row in atom_rows:
        if len(row) <= max(i_x, i_y, i_z):
            continue
        try:
            fx, fy, fz = float(row[i_x]), float(row[i_y]), float(row[i_z])
        except ValueError:
            continue
        el = element_from_label(row[i_type]) if i_type is not None else element_from_label(row[i_label])
        asym_atoms.append(Atom(el, fx, fy, fz))

    ops = sym_ops or [lambda x, y, z: (x, y, z)]
    expanded: List[Atom] = []
    for atom in asym_atoms:
        for op in ops:
            x, y, z = op(atom.fx, atom.fy, atom.fz)
            wx, wy, wz = _wrap(x), _wrap(y), _wrap(z)
            dup = False
            for s in expanded:
                if s.el != atom.el:
                    continue
                dx = min(abs(s.fx - wx), 1 - abs(s.fx - wx))
                dy = min(abs(s.fy - wy), 1 - abs(s.fy - wy))
                dz = min(abs(s.fz - wz), 1 - abs(s.fz - wz))
                if dx < TOL and dy < TOL and dz < TOL:
                    dup = True
                    break
            if not dup:
                expanded.append(Atom(atom.el, wx, wy, wz))

    cell_matrix = _cell_par_to_matrix(a, b, c, alpha, beta, gamma)
    return ParsedCIF(a, b, c, alpha, beta, gamma, cell_matrix, expanded)


if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else 'HKUST-1.cif'
    with open(path) as f:
        parsed = parse_cif(f.read())
    print(f'Module 1 result: {len(parsed.atoms)} atoms in the expanded unit cell, '
          f'cell = {parsed.a:.3f} {parsed.b:.3f} {parsed.c:.3f} A, '
          f'{parsed.alpha:.1f} {parsed.beta:.1f} {parsed.gamma:.1f} deg. No bonds yet -- see code_02.')
