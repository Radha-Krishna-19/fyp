# The Published Algorithm

**How MOFid decomposes a framework, stage by stage**

> The pipeline this project studies: reading the CIF, inferring bonds, classifying elements, and the metal-oxo rule that splits the structure into nodes and linkers. This is the baseline — the algorithm as the field currently uses it.

*Part of the MOF Building-Block Analysis final year project — see the [main README](../README.md).*

---

## 1 · What the published pipeline is


The algorithm this project studies is the decomposition pipeline from **MOFid**, published by the Snurr group at Northwestern University and released as open source at `snurr-group/mofid`. It is the standard tool for this task: it is what was used to annotate the large public MOF databases, so its output is embedded in a great deal of downstream published work.


Its job is to take a `.cif` file and return a statement of what the material is made of — which atoms form the metal nodes, which form the organic linkers, and what the resulting topology is. The original implementation is C++ built on Open Babel. For this project every stage was **translated into standalone Python**, one module per stage, so that each step can be run, inspected and modified in isolation. Each module cites the upstream source file it corresponds to.

| Module | Stage | What it produces |
|---|---|---|
| `code_01_cif_input.py` | Read the CIF | Cell matrix + fractional coordinates. No bonds yet. |
| `code_02_bond_assignment_pbc.py` | Infer bonds | A bond list, from periodic distances and covalent radii. |
| `code_03_element_classification.py` | Classify elements | `is_metal()` for every atom. |
| `code_04a_metal_oxo_algorithm.py` | **Metal-oxo split** | Node blocks and linker blocks. *The subject of this project.* |
| `code_04b_single_node_algorithm.py` | Single-node split | An alternative partition that keeps the carboxylate with the metal. |
| `code_04c_all_node_algorithm.py` | All-node split | A third partition that also splits the linker at its branch points. |
| `code_05_centroid_simplification.py` | Collapse to points | One coordinate per block — the abstract net. |
| `code_06_systre_topology_export.py` | Topology export | A real `.cgd` file for Systre. |
| `code_07a_mofid_assembly.py` | MOFid | The composite identifier string. |
| `code_07b_mofkey_assembly.py` | MOFkey | The short hashed key. |


---


## 2 · Stage by stage


### 2.1 · Reading the CIF


The parser extracts the six cell parameters and the atom loop, builds the 3×3 cell matrix, and applies the symmetry operations to generate the full contents of the unit cell. The output is a list of `(element, fractional position)` pairs plus the matrix. At this point the structure is a cloud of labelled points — there is no notion of a molecule, a node, or a linker.


### 2.2 · Bond perception


This is where the structure becomes a graph. For every pair of atoms the minimum-image distance is computed over all 27 cell images, and the pair is bonded if that distance is under the covalent-radius-sum cutoff. The result is an undirected graph whose vertices are atoms and whose edges carry the lattice shift that produced them.


> **Every later stage depends on this one**
>
> Bond perception is a *heuristic*, not a measurement. Nothing in the CIF confirms it. If the cutoff is slightly wrong, or periodicity is ignored, the graph is wrong — and the split, the coordination numbers, the topology and the identifier are all wrong in ways that look perfectly plausible on screen.


### 2.3 · Element classification: `is_metal()`


The split needs to know which atoms are metals. MOFid answers this by **exclusion**: it holds a list of the 23 elements that are *not* metals, and treats everything else as a metal.


```
NONMETALS = {
    "H", "He", "B", "C", "N", "O", "F", "Ne",
    "Si", "P", "S", "Cl", "Ar",
    "Ge", "As", "Se", "Br", "Kr",
    "Sb", "Te", "I", "Xe", "At", "Rn"
}

def is_metal(element):
    """Anything not on the nonmetal list is treated as a metal."""
    return element not in NONMETALS
```
*code_03_element_classification.py — the published approach, faithfully translated.*


This design is deliberate and correct. A whitelist of metals would have to enumerate every metal that might appear in any MOF ever deposited, and would silently fail on the first one it missed. The exclusion list is short, closed and stable.


> **A concrete demonstration of why exclusion is the right choice**
>
> A hardcoded whitelist of eight common MOF metals — Zn, Cu, Ni, Co, Fe, Al, Cr, Mn — looks entirely reasonable. Run it on UiO-66 and **not a single atom is recognised as a metal**, because zirconium is not on the list.
>
> The structure then has no nodes at all, the split produces nothing, and the failure is silent: no error is raised, the output is simply empty. The published exclusion list has no such failure mode. This is shown live on the website.


---


## 3 · The metal-oxo algorithm


This is the stage the project is about. In the MOFid source it is the base `Deconstructor` class, and it is the default decomposition.


### 3.1 · The rule, stated plainly


**Cut every bond that has a metal atom at one end. Whatever remains connected is a building block.** Blocks containing a metal are nodes; blocks not containing a metal are linkers.


```
def classify_metal_oxo(geom):
    """The published rule: sever every metal-containing bond, then
    take connected components of what is left."""

    kept = []
    for (i, j, shift) in geom.bonds:
        if is_metal(geom.elements[i]) or is_metal(geom.elements[j]):
            continue                       # cut it
        kept.append((i, j, shift))         # keep it

    blocks = connected_components(geom.n_atoms, kept)

    nodes   = [bl for bl in blocks if any(is_metal(geom.elements[a]) for a in bl)]
    linkers = [bl for bl in blocks if bl not in nodes]
    return nodes, linkers
```
*code_04a_metal_oxo_algorithm.py — the whole idea in about ten lines.*


The appeal of the rule is obvious. It is simple, it needs no chemical knowledge beyond `is_metal()`, it is deterministic, it never gets stuck, and it runs on any structure regardless of chemistry. Those properties are exactly what a tool that must process hundreds of thousands of structures unattended requires. The rule is not careless — it is a deliberate trade of chemical fidelity for universality.


### 3.2 · What it produces on the four test structures

| Structure | Node reported by the published algorithm | What the node chemically is |
|---|---|---|
| HKUST-1 | `Cu2` | Cu₂(COO)₄ paddlewheel |
| MOF-5 | `Zn4 O` | Zn₄O(COO)₆ |
| ZIF-8 | `Zn` | single Zn²⁺ — correct |
| UiO-66 | `Zr6 O8 H4` | Zr₆O₄(OH)₄(COO)₁₂ |


Three of the four nodes come out as bare metal, or metal plus the bridging oxygens that happen to sit between metals. In each case the carboxylate groups that chemically define the cluster have been severed and pushed onto the linker side, because both of their oxygens are bonded to metal.


### 3.3 · The two alternative decompositions


MOFid also ships two other splits, which is itself evidence that the authors knew one rule cannot serve every purpose.

- **Single-node** (`code_04b`) — cuts the metal–carboxylate-oxygen bond only where it separates the cluster from the organic part, keeping the carboxylate with the metal. This produces the chemically complete node, but the rule is narrower and does not generalise as cleanly.
- **All-node** (`code_04c`) — as single-node, and additionally splits the organic linker at its branch points, so a tritopic linker becomes a central node plus three arms. Useful for topology analysis of complex nets.

Comparing these three on the same structure is instructive, and the website lets you do exactly that: the same CIF, three partitions, three different answers to "what is this material made of". None of them is wrong as such; they answer different questions. The problem addressed in Document 3 is that the *default* answer — the one that ends up in databases — is the one that discards the most chemistry.


---


## 4 · After the split


### 4.1 · Centroid simplification


Each block is collapsed to a single point at its centroid, computed periodically: block atoms must first be "unwrapped" so a block straddling a cell boundary is not averaged into the middle of the cell. What remains is the abstract net — points and connections, no chemistry.


### 4.2 · Topology export


The simplified net is written as a `.cgd` file, the input format of **Systre**, which identifies the net and returns its RCSR symbol. Systre itself is not reimplemented here; the module writes a genuine input file and the published net names are used as ground truth.


### 4.3 · MOFid and MOFkey


The final products are two identifier strings:


```
MOFid:   <linker SMILES> . <node SMILES> MOFid-v1.<topology>.<catenation>
MOFkey:  <metal>.<linker InChIKey>.MOFkey-v1.<topology>
```
*code_07a / code_07b. Two identifiers because they serve different needs: MOFid is complete and reconstructible; MOFkey is short, hashable and database-friendly.*


> **An honest limitation of this reimplementation**
>
> Real InChIKey generation needs a dedicated chemistry library. The Python module produces a **placeholder** key of the correct shape, and says so in the code and on the website. This does not affect any result in the project, because nothing downstream consumes the key — but it should not be presented as a working InChI implementation.


## 5 · Where the project takes over


Modules 01–07 are faithful translations of the published algorithm, and are used unchanged as the baseline. The project's own contribution begins after them:

| Module | Contribution |
|---|---|
| `code_08_proposed_fixes.py` | Four independently switchable fixes to the metal-oxo split, plus a quality report that flags where the split is uncertain. |
| `code_09_network_analysis.py` | The periodic block graph, coordination numbers, centrality measures and Laplacian spectrum. |
| `code_10_multifractal_spectrum.py` | The iNMFA spectrum, the reference band and the candidate test. |
| `code_11_nmfa_paper.py` | The published NMFA method reimplemented exactly, using box-growing. |


Documents 3 and 4 cover these in detail.
