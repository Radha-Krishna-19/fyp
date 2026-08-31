# MOFs and Crystallography

**The chemistry and file formats the project is built on**

> What a metal–organic framework is, how crystal structures are stored, why bonds have to be inferred rather than read, and what coordination number and topology mean. Read this first — everything else assumes it.

*Part of the MOF Building-Block Analysis final year project — see the [main README](../README.md).*

---

## 1 · What a metal–organic framework is


A metal–organic framework (MOF) is a crystalline solid built by connecting metal-containing clusters to organic molecules, over and over, in three dimensions. Two ingredients, repeated on a lattice:

- **Nodes** — small inorganic clusters, usually a few metal atoms bridged by oxygen. These are rigid and act as the joints of the structure. In the literature they are also called *secondary building units* (SBUs).
- **Linkers** — organic molecules, typically rigid aromatic rings terminated by groups that bind metals (most often carboxylates, `–COO⁻`). These act as the struts.

Because both pieces are rigid and bind in predictable directions, the product is not a random solid. It is a lattice with large, regular, empty channels running through it. That emptiness is the point: MOFs routinely have internal surface areas above 3,000 m² per gram, so a gram of powder has the surface area of a football pitch. That is why they are studied for gas storage, carbon capture, separation and catalysis.


The design idea behind this is called **reticular chemistry**: if you know which node geometry and which linker length you are combining, you can predict the framework you will get. A square node plus a linear linker gives one net; a 12-connected node plus a linear linker gives a different one. The consequence for this project is that **the node and linker identities are the design variables**. Get them wrong and every downstream prediction is about a material that does not exist.


> **Why this matters for the project**
>
> Everything this project does rests on one operation: taking a crystal structure and correctly splitting it into nodes and linkers. Databases of hundreds of thousands of MOFs are built by running that split automatically. If the splitting algorithm is systematically wrong, every entry in the database inherits the error.


### 1.1 · The four structures used throughout


These four are the standard benchmarks in the field. They are used here because their nodes, linkers and topologies are all published, so every algorithm can be checked against a known answer rather than against itself.

| Structure | Metal | True node (SBU) | Linker | Net | Why it is in the set |
|---|---|---|---|---|---|
| HKUST-1 | Cu | Cu₂(COO)₄ paddlewheel | benzene-1,3,5-tricarboxylate | tbo | The classic paddlewheel; shows the carboxylate problem most clearly |
| MOF-5 | Zn | Zn₄O(COO)₆ | benzene-1,4-dicarboxylate | pcu | The first famous MOF; simple cubic, easy to sanity-check |
| ZIF-8 | Zn | single Zn²⁺ | 2-methylimidazolate | sod | A control: nitrogen donors, no carboxylate at all |
| UiO-66 | Zr | Zr₆O₄(OH)₄(COO)₁₂ | benzene-1,4-dicarboxylate | fcu | The hardest case: 12-connected, and Zr is missing from naive metal lists |


ZIF-8 earns its place by being the odd one out. It has no carboxylate groups, so any fix that is really just "always grab the neighbouring carboxylate" would change ZIF-8 too — and would therefore be wrong. Throughout this project, ZIF-8 correctly comes out unchanged, which is evidence that the fixes are chemically targeted rather than blanket rules.


---


## 2 · How a crystal structure is stored: the CIF file


Crystal structures are distributed as **CIF** files (Crystallographic Information File). A CIF holds three things and, critically, only three things:

1. **The unit cell** — six numbers, `a b c α β γ`. The lengths of the three cell edges and the angles between them. This defines the box that repeats.
2. **The atoms in that box** — element symbol plus a position, given in *fractional* coordinates: three numbers between 0 and 1 expressing the position as a fraction along each cell edge.
3. **Symmetry operations** — a list of transformations that generate the rest of the atoms from a small asymmetric unit.

```
data_HKUST-1
_cell_length_a      26.343
_cell_length_b      26.343
_cell_length_c      26.343
_cell_angle_alpha   90.0
_cell_angle_beta    90.0
_cell_angle_gamma   90.0

loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
Cu1   Cu   0.28337   0.21663   0.00000
O1    O    0.31122   0.18878   0.06712
C1    C    0.36255   0.13745   0.05938
...
```
*A cubic CIF. Note what is absent: there is no line anywhere that says Cu1 is bonded to O1.*


> **The single most important fact about the CIF format**
>
> A CIF contains **no bonds**. Not one. It is a list of atomic positions and nothing else.
>
> Every bond that any MOF software talks about was *inferred* by that software from interatomic distances. Bond perception is a guess, made by an algorithm, from geometry alone — and every later stage of the pipeline is built on top of that guess.


### 2.1 · Fractional coordinates and the cell matrix


Fractional coordinates are convenient for storage but useless for measuring distance, because the cell may be non-cubic. To get real distances in ångströms, fractional coordinates are multiplied by the **cell matrix** — a 3×3 matrix built from the six cell parameters, whose rows are the cell edge vectors in Cartesian space.


```
ax = a
bx = b*cos(gamma)          by = b*sin(gamma)
cx = c*cos(beta)
cy = c*(cos(alpha) - cos(beta)*cos(gamma)) / sin(gamma)
cz = sqrt(c^2 - cx^2 - cy^2)

M = [[ax, 0,  0 ],
     [bx, by, 0 ],
     [cx, cy, cz]]

cartesian = fractional @ M
```
*The standard lower-triangular cell matrix. This is implemented in code_01_cif_input.py.*


---


## 3 · Periodicity, and why it changes everything


A crystal has no edges. The unit cell is a bookkeeping device: the real material continues in every direction, and an atom near the face of the cell is genuinely bonded to an atom in the *next* cell over. Any algorithm that treats the unit cell as an isolated object will simply miss those bonds — and in a MOF, those are exactly the bonds that hold the framework together.


### 3.1 · The minimum-image convention


The standard way to handle this: when measuring the distance between two atoms, do not just measure it directly. Measure it to every periodic image of the second atom and keep the shortest. In three dimensions, considering one cell in each direction, that means the home cell plus its 26 neighbours — **27 images**.


```
def min_image_distance(fa, fb, cell_matrix):
    """Shortest distance between atom a and any periodic image of atom b."""
    best = infinity
    best_shift = (0, 0, 0)
    for sx in (-1, 0, 1):
        for sy in (-1, 0, 1):
            for sz in (-1, 0, 1):
                shifted = fb + (sx, sy, sz)          # still fractional
                d = norm((shifted - fa) @ cell_matrix)   # now angstroms
                if d < best:
                    best, best_shift = d, (sx, sy, sz)
    return best, best_shift
```
*The 27-image search. The shift that won is remembered — Section 5 explains why that is essential.*


> **The most common bug in this whole area**
>
> Computing distances with a plain `pdist()` on raw coordinates ignores periodicity entirely. Every bond that crosses a cell boundary disappears.
>
> The structure then fragments into disconnected pieces, coordination numbers come out too low, and the network analysis that follows is analysing a different material than the one on disk.


### 3.2 · Deciding what counts as a bond


Having a distance is not the same as having a bond. The rule used across the field is the **covalent-radius sum**: two atoms are bonded if the distance between them is less than the sum of their tabulated covalent radii, times a tolerance factor.


```
cutoff = (radius[element_a] + radius[element_b]) * tolerance
bonded = (distance < cutoff)

tolerance = 1.30   if either atom is a metal   # coordination bonds are longer,
                                               # softer, and more variable
tolerance = 1.15   otherwise                   # ordinary covalent bonds
```
*Radii are from Cordero et al. (2008). Metals get a looser tolerance because coordination bonds genuinely are longer and more variable than covalent ones.*


This is a threshold on a continuum, so it has a grey zone. A Zr–O distance sitting 2% under the cutoff and one sitting 2% over are chemically almost identical, but the algorithm calls one a bond and the other nothing. The project handles this by reporting **borderline bonds** — any pair within 10% of its cutoff — rather than pretending the threshold is sharp.

| Element | Covalent radius (Å) | Element | Covalent radius (Å) |
|---|---|---|---|
| H | 0.31 | Cu | 1.32 |
| C | 0.76 | Zn | 1.22 |
| N | 0.71 | Zr | 1.75 |
| O | 0.66 | Fe | 1.32 |


---


## 4 · Nodes, linkers, and coordination number


### 4.1 · Coordination number


The **coordination number** of a building block is the number of other building blocks it connects to. It is the single most informative number in framework analysis, because it fixes the topology: a 4-connected node and a 12-connected node cannot form the same net, whatever the chemistry.

| Structure | Node coordination | Linker coordination | Net symbol | Geometry |
|---|---|---|---|---|
| HKUST-1 | 4 | 3 | tbo | square node, triangular linker |
| MOF-5 | 6 | 2 | pcu | octahedral node, linear linker |
| ZIF-8 | 4 | 2 | sod | tetrahedral node, bent linker |
| UiO-66 | 12 | 2 | fcu | cuboctahedral node, linear linker |


These are the published values, and they are the hard test used throughout the project. UiO-66 is the discriminating case: its Zr₆ cluster is 12-connected, and a construction that ignores periodicity typically reports 6. Anything reporting 6 for UiO-66 is wrong, and the error is not subtle — it is the difference between the `fcu` net and something that is not a real structure.


### 4.2 · Topology and RCSR net symbols


Once every block is reduced to a point and every connection to a line, what remains is an abstract periodic graph — the **topology** or **net**. Nets have standard three-letter names from the Reticular Chemistry Structure Resource (RCSR): `tbo`, `pcu`, `sod`, `fcu`. Two MOFs made of entirely different chemistry can share a net, and that shared net predicts shared behaviour, which is why the classification is worth doing.


The tool that determines a net from a periodic graph is **Systre**. It is not reimplemented in this project; instead the pipeline writes a genuine Systre input file (`.cgd`) that can be fed to it. The RCSR names quoted here are the published ones for these four materials, used as ground truth.


### 4.3 · Where the decomposition can go wrong


The whole difficulty is that a MOF is one continuous covalent network. Nothing in the structure announces "the node ends here and the linker begins here". That boundary is a decision made by an algorithm, and the carboxylate group sits exactly on it:

- The carboxylate carbon is bonded to the benzene ring, which is unambiguously linker.
- Both carboxylate oxygens are bonded to metal atoms, which are unambiguously node.
- So the `–COO` group bridges the two. Assigning it to the node, to the linker, or splitting it are all defensible — and they give three different answers to "what is this MOF made of".

The published algorithm resolves this by cutting every bond that touches a metal, which places the entire carboxylate on the linker side and leaves the node as bare metal atoms. Document 3 examines what that costs and what can be done about it.
