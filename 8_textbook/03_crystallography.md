# Chapter 3 — Crystals and CIF Files

*How a crystal structure is stored, and why every bond in this project had to be inferred.*

---

## 3.1 · What a crystal actually is

A crystal is a small box of atoms, repeated forever in all three directions.

That box is the **unit cell**. The full material is that box tiled endlessly — like wallpaper
in 3D, with no edges anywhere.

This has a consequence that is easy to state and easy to forget:

> **A crystal has no boundary.** An atom sitting near the wall of the box is genuinely bonded
> to an atom in the *next box over*. That bond is real. If your software only looks inside one
> box, it will not see it.

This single fact causes the most important failure mode in the entire project, and Chapter 5
measures exactly how bad it gets.

---

## 3.2 · The CIF file

Crystal structures are distributed as **CIF** files (Crystallographic Information File). A
CIF contains three things — and, critically, *only* three things:

**1. The unit cell** — six numbers.

```
_cell_length_a      26.343     the three edge lengths, in ångströms
_cell_length_b      26.343
_cell_length_c      26.343
_cell_angle_alpha   90.0       the three angles between those edges
_cell_angle_beta    90.0
_cell_angle_gamma   90.0
```

**2. The atoms**, given in *fractional* coordinates — a fraction along each cell edge, so
always between 0 and 1.

```
loop_
_atom_site_type_symbol
_atom_site_fract_x  _atom_site_fract_y  _atom_site_fract_z
Cu   0.28337   0.21663   0.00000
O    0.31122   0.18878   0.06712
C    0.36255   0.13745   0.05938
...
```

**3. Symmetry operations** — a list of transformations that generate the rest of the atoms
from a small asymmetric unit, so the file does not have to list every atom explicitly.

---

## 3.3 · The single most important fact about CIF files

> **A CIF contains no bonds. Not one.**

Look at the file again. It is a list of *positions*. There is no line anywhere that says
"this copper is bonded to that oxygen".

This is not an oversight — it is what crystallography measures. X-ray diffraction tells you
where the electron density is, which gives you atom positions. It does not directly tell you
which atoms are chemically bonded.

**So every bond that any MOF software talks about was inferred by that software, from
geometry.** Bond perception is a *guess*, made by an algorithm, from distances alone. And
every later stage of our pipeline is built on top of that guess.

That is worth sitting with. If bond perception is wrong, the blocks are wrong, the graph is
wrong, and the spectrum describes a material that does not exist.

---

## 3.4 · From fractional coordinates to real distances

Fractional coordinates are convenient for storage but useless for measuring distance,
because the cell may not be a cube. To get real distances in ångströms, we multiply by the
**cell matrix** — a 3×3 matrix whose rows are the cell edge vectors in ordinary Cartesian
space.

```python
# code_01_cif_input.py — building the cell matrix from the six cell parameters
ax = a
bx = b * cos(gamma)                                    ; by = b * sin(gamma)
cx = c * cos(beta)
cy = c * (cos(alpha) - cos(beta) * cos(gamma)) / sin(gamma)
cz = sqrt(c**2 - cx**2 - cy**2)

M = [[ax,  0,  0],
     [bx, by,  0],
     [cx, cy, cz]]

cartesian = fractional @ M      # now in ångströms
```

The lower-triangular form is the standard convention. Nothing deep is happening — it is
trigonometry to convert "0.28 of the way along edge *a*" into "12.3 Å in the *x* direction".

---

## 3.5 · Inferring bonds: the minimum-image convention

Now the important part. We need to decide which atoms are bonded, and we must do it *across
cell boundaries*.

The standard approach is the **minimum-image convention**: when measuring the distance
between two atoms, do not just measure it directly. Measure it to **every periodic image** of
the second atom, and keep the shortest. In three dimensions, considering one cell step in
each direction, that is the home cell plus its 26 neighbours — **27 images**.

```python
# code_02_bond_assignment_pbc.py
def min_image_distance(frac_a, frac_b, cell_matrix):
    """Shortest distance between atom a and ANY periodic image of atom b.

    Why 27: the home cell (0,0,0) plus one step in each of the 26 surrounding
    directions. A bond can only cross one cell boundary at a time for any
    physically sensible bond length, so 27 is sufficient.
    """
    best, best_shift = infinity, (0, 0, 0)
    for sx in (-1, 0, 1):
        for sy in (-1, 0, 1):
            for sz in (-1, 0, 1):
                shifted = frac_b + (sx, sy, sz)         # still fractional
                d = norm((shifted - frac_a) @ cell_matrix)   # now ångströms
                if d < best:
                    best, best_shift = d, (sx, sy, sz)
    return best, best_shift        # the winning shift is REMEMBERED — see Ch. 5
```

**The returned shift is not a detail — it is the whole of Chapter 5.** That triple of
integers records *which copy of the cell* the bond reached into. Throw it away and the
crystal falls apart.

---

## 3.6 · Deciding what counts as a bond

Having a distance is not the same as having a bond. The rule used across the field is the
**covalent-radius sum**: two atoms are bonded if the distance between them is less than the
sum of their tabulated covalent radii, times a tolerance factor.

```python
cutoff = (radius[element_a] + radius[element_b]) * tolerance
bonded = (distance < cutoff)

tolerance = 1.30   if either atom is a metal    # coordination bonds are longer,
                                                # softer, and more variable
tolerance = 1.15   otherwise                    # ordinary covalent bonds
```

Radii come from **Cordero et al. (2008)** — reference [10]. A few, for scale:

| Element | Covalent radius (Å) | | Element | Covalent radius (Å) |
|---|---|---|---|---|
| H | 0.31 | | Cu | 1.32 |
| C | 0.76 | | Zn | 1.22 |
| N | 0.71 | | **Zr** | **1.75** |
| O | 0.66 | | Fe | 1.32 |

Metals get the looser tolerance because coordination bonds genuinely *are* longer and more
variable than ordinary covalent bonds. That is chemistry, not a fudge.

### This is a threshold on a continuum

Worth being honest about: a Zr–O contact 2% under the cutoff and one 2% over are chemically
almost identical, but the algorithm calls one a bond and the other nothing. There is a grey
zone, and a borderline bond can move a whole group of atoms between node and linker.

Our code reports **borderline bonds** — any pair within 10% of its cutoff — rather than
pretending the threshold is sharp.

---

## 3.7 · What our pipeline actually finds

These are our computed numbers for the four test structures:

| Structure | Atoms in cell | Bonds inferred | Bonds per atom |
|---|---|---|---|
| HKUST-1 | 156 | 198 | 1.27 |
| MOF-5 | 424 | 512 | 1.21 |
| ZIF-8 | 276 | 312 | 1.13 |
| UiO-66 | 114 | 184 | 1.61 |

UiO-66's higher bond density is exactly what you would expect from a 12-connected cluster —
more connections packed into a smaller cell.

---

## 3.8 · Terms introduced in this chapter

| Term | Meaning |
|---|---|
| **unit cell** | The small repeating box a CIF stores |
| **fractional coordinates** | Position as a fraction along each cell edge (0 to 1) |
| **cell matrix** | The 3×3 matrix converting fractional → ångströms |
| **periodic boundary conditions (PBC)** | Treating the cell as repeating forever |
| **minimum-image convention** | Measuring to the nearest periodic copy, over 27 images |
| **bond perception** | Inferring bonds from distance, because CIFs do not store them |
| **covalent radius** | Tabulated per-element size, used to set the bond cutoff |
| **translation / shift `t`** | Three integers recording which cell copy a bond reaches |

---

**Next:** [Chapter 4 — Decomposition](04_decomposition.md), which cuts the bonded structure
into building blocks.
