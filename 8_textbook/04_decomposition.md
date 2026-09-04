# Chapter 4 — Decomposition: Cutting a Crystal Into Blocks

*The published algorithm we implement and visualise. We use it unmodified.*

---

## 4.1 · The task

After Chapter 3 we have a bonded structure: a list of atoms, and a list of which pairs are
bonded (each bond carrying the translation that produced it).

Now we need to split that into **building blocks** — metal nodes and organic linkers — because
those blocks will become the vertices of our graph.

Here is the difficulty:

> **A MOF is one continuous covalent network.** Nothing in the structure announces "the node
> ends here and the linker begins here". That boundary is a *decision made by an algorithm*,
> not a fact read off the file.

---

## 4.2 · Where the boundary is genuinely ambiguous

The hard case is the **carboxylate group**, `–COO⁻` — the standard way an organic linker
grabs a metal cluster.

```
        O
       ⁄⁄                        ← both oxygens bond to metal
  R — C
       \                         ← the carbon bonds to the organic ring
        O
```

- The carboxylate **carbon** is bonded to the benzene ring — unambiguously linker.
- Both carboxylate **oxygens** are bonded to metal atoms — unambiguously node-side.
- So the group *bridges* the two.

Assigning it to the node, to the linker, or splitting it are all defensible — and they give
three different answers to "what is this MOF made of". This is why the field has more than one
decomposition algorithm.

---

## 4.3 · The published pipeline: MOFid

The algorithm we use is from **MOFid** (Bucior *et al.*, reference [1]), released as
`snurr-group/mofid`. It is the standard tool — it is what was used to annotate the large
public MOF databases, so its output is embedded in a great deal of published work.

The original is C++ built on Open Babel. For this project we translated every stage into
standalone Python, one module per stage, so each step can be run and inspected in isolation.

| Module | Stage | What it produces |
|---|---|---|
| `code_01_cif_input.py` | Read the CIF | Cell matrix + fractional coordinates. **No bonds yet.** |
| `code_02_bond_assignment_pbc.py` | Infer bonds | Bond list, from periodic distances and covalent radii |
| `code_03_element_classification.py` | Classify elements | `is_metal()` for every atom |
| `code_04a_metal_oxo_algorithm.py` | **The split** | Node blocks and linker blocks |
| `code_04b_single_node_algorithm.py` | Alternative split | Keeps the carboxylate with the metal |
| `code_04c_all_node_algorithm.py` | Alternative split | Also splits the linker at branch points |
| `code_05_centroid_simplification.py` | Collapse to points | One coordinate per block |
| `code_06_systre_topology_export.py` | Topology export | A real `.cgd` file for Systre |
| `code_07a/07b` | Identifiers | MOFid and MOFkey strings |

> **This project does not modify the algorithm.** We implement it faithfully and build a
> visualisation of it, so that the blocks our network analysis runs on can be inspected.

---

## 4.4 · Which elements are metals?

The split needs to know which atoms are metals. MOFid answers this by **exclusion** — it holds
a list of the elements that are *not* metals, and treats everything else as one.

```python
# code_03_element_classification.py
NONMETALS = {
    "H", "He", "B", "C", "N", "O", "F", "Ne",
    "Si", "P", "S", "Cl", "Ar",
    "Ge", "As", "Se", "Br", "Kr",
    "Sb", "Te", "I", "Xe", "At", "Rn",
}

def is_metal(element):
    """Anything not on the nonmetal list is treated as a metal."""
    return element not in NONMETALS
```

This design looks lazy. It is actually the right choice, and there is a clean demonstration of
why.

> **Try the opposite.** Suppose you wrote a *whitelist* of the eight common MOF metals — Zn,
> Cu, Ni, Co, Fe, Al, Cr, Mn. Entirely reasonable-looking.
>
> Run it on **UiO-66**. Zirconium is not on the list. **Not one atom is recognised as a
> metal.** The structure has no nodes, the split produces nothing — and no error is raised.
> The output is simply empty.
>
> A whitelist fails silently on the first metal it does not know about. The exclusion list has
> no such failure mode.

---

## 4.5 · The metal-oxo rule

This is the default decomposition. The rule, in full:

> **Cut every bond that has a metal atom at one end. Whatever remains connected is a building
> block.** Blocks containing a metal are nodes; blocks without one are linkers.

```python
# code_04a_metal_oxo_algorithm.py — the whole idea in about ten lines
def classify_metal_oxo(geom):
    """Sever every metal-containing bond, then take connected components."""
    kept = []
    for (i, j, shift) in geom.bonds:
        if is_metal(geom.elements[i]) or is_metal(geom.elements[j]):
            continue                       # cut it
        kept.append((i, j, shift))         # keep it

    blocks = connected_components(geom.n_atoms, kept)

    nodes   = [b for b in blocks if any(is_metal(geom.elements[a]) for a in b)]
    linkers = [b for b in blocks if b not in nodes]
    return nodes, linkers
```

### Why this rule, when it is so crude?

It is simple, needs no chemical knowledge beyond `is_metal()`, is deterministic, never gets
stuck, and runs on any structure regardless of chemistry.

Those properties are exactly what a tool that must process hundreds of thousands of structures
unattended requires. **The rule is not careless — it is a deliberate trade of chemical fidelity
for universality.**

### What it produces

| Structure | Node the algorithm reports | What the node chemically is |
|---|---|---|
| HKUST-1 | `Cu2` | Cu₂(COO)₄ paddlewheel |
| MOF-5 | `Zn4 O` | Zn₄O(COO)₆ |
| ZIF-8 | `Zn` | single Zn²⁺ — **correct** |
| UiO-66 | `Zr6 O8 H4` | Zr₆O₄(OH)₄(COO)₁₂ |

Because the rule cuts every metal bond, and both carboxylate oxygens touch metal, the whole
carboxylate ends up on the linker side. The reported node is the real cluster with its binding
groups stripped off.

**Is this a problem?** For chemical identity, arguably. For *our* purposes, no — and this
matters. We care about **which blocks connect to which**, not what each block contains. The
carboxylate assignment changes block *composition*; it does not change the *connectivity*. The
coordination numbers come out correct either way, which is what Chapter 5 verifies against
published crystallography.

---

## 4.6 · The two alternative splits

MOFid ships three algorithms, which is itself evidence that one rule cannot serve every
purpose:

- **Metal-oxo** (`code_04a`) — the default; cuts every metal bond.
- **Single-node** (`code_04b`) — keeps the bridging carboxylate with the metal, giving the
  chemically complete cluster. Narrower rule, generalises less cleanly.
- **All-node** (`code_04c`) — as single-node, and additionally splits the organic linker at its
  branch points, so a three-armed linker becomes a centre plus three arms. Useful for topology
  analysis of complex nets.

The website lets you run all three on the same structure and compare. None is *wrong*; they
answer different questions.

---

## 4.7 · What happens after the split

**Centroid simplification** (`code_05`) — each block is collapsed to a single point at its
centroid, computed periodically so a block straddling a cell boundary is not averaged into the
middle of the cell. What remains is the abstract net: points and connections, no chemistry.

**Topology export** (`code_06`) — the simplified net is written as a `.cgd` file, the input
format of **Systre** [4], which identifies the net and returns its RCSR symbol.

> **Honest limitation:** we do *not* reimplement Systre. `code_06` writes a genuine input file
> for it, but the topology tool itself is external Java software. The RCSR names we quote
> (`tbo`, `pcu`, `sod`, `fcu`) are the **published** ones for these materials.

**Identifiers** (`code_07a/b`) — two strings summarising the structure:

```
MOFid:   <linker SMILES> . <node SMILES> MOFid-v1.<topology>.<catenation>
MOFkey:  <metal>.<linker InChIKey>.MOFkey-v1.<topology>
```

> **A second honest limitation:** real InChIKey generation needs a dedicated cheminformatics
> library. Our module produces a **placeholder** key of the correct shape, and says so in the
> code and on the website. Nothing downstream consumes it, so no result depends on it — but it
> must not be presented as a working InChI implementation.

---

## 4.8 · Terms introduced in this chapter

| Term | Meaning |
|---|---|
| **building block** | A node or linker; becomes one vertex of the graph |
| **metal-oxo algorithm** | The default MOFid split: cut every metal-containing bond |
| **connected component** | A group of atoms all reachable from each other through kept bonds |
| **`is_metal()`** | Element classifier, built by *excluding* 23 known nonmetals |
| **centroid simplification** | Collapsing each block to a single point |
| **Systre / `.cgd`** | External tool (and its input format) that names the net |
| **MOFid / MOFkey** | Identifier strings summarising composition + topology |

---

**Next:** [Chapter 5 — Graph Theory](05_graphs.md), which turns these blocks into a network
and defines every term used from there on.
