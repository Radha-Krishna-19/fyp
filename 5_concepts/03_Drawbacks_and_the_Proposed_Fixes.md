# Drawbacks and Fixes

**What the published metal-oxo rule gets wrong, and how to correct it**

> The four limitations of the published decomposition, each with live evidence from the four test structures, and the fix proposed for each — with a measured effect and an honest statement of what is not demonstrated.

*Part of the MOF Building-Block Analysis final year project — see the [main README](../README.md).*

---

## 1 · The problem statement


The metal-oxo rule — cut every bond touching a metal — is simple enough to run unattended on hundreds of thousands of structures, and that is why it became the default. The cost of that simplicity is that it cuts through chemistry it should not cut through.


The carboxylate group `–COO⁻` is the standard way an organic linker binds a metal cluster. Both of its oxygens bond to metal. So the rule severs both, and the entire carboxylate ends up on the linker side of the split. The node that is reported is not the chemical building unit — it is that unit with its binding groups stripped off.


> **The claim being made, stated precisely**
>
> The published algorithm is not buggy. It implements its stated rule correctly and it never crashes.
>
> The claim is that **the rule itself reports chemically incomplete nodes**, that the error is systematic rather than random, that it is largest exactly where the chemistry is most interesting, and that it can be corrected without giving up the properties that made the rule attractive.


---


## 2 · Limitation 1 — incomplete nodes


### 2.1 · What goes wrong


HKUST-1 is the clearest case. Its node is the copper paddlewheel: two copper atoms held together by four carboxylate bridges, `Cu₂(COO)₄`. It is one of the most-cited building units in the field, and its four-fold symmetry is what makes HKUST-1 adopt the `tbo` net.


The published algorithm reports the node as `Cu2`. Two copper atoms. All four carboxylates have been cut away because their oxygens touch metal.

| Structure | Published node | With the fix applied | Atoms recovered |
|---|---|---|---|
| HKUST-1 | `Cu2` | `Cu2 C4 O8` | **+12** |
| UiO-66 | `Zr6 O8 H4` | `Zr6 O32 C12 H4` | **+36** |
| MOF-5 | `Zn4 O` | `Zn4 O13 C6` | **+18** |
| ZIF-8 | `Zn` | `Zn` | no change — correctly |


The ZIF-8 row is the important control. ZIF-8 binds through nitrogen, not carboxylate, so a correctly targeted fix must leave it alone — and it does. A fix that changed ZIF-8 as well would be a blanket rule rather than a chemical one.


### 2.2 · Why it matters

- The reported node is not a species that exists. `Cu2` on its own is not a stable building unit; the carboxylates are what hold it together.
- Node identity is used to group and search MOF databases. Materials with genuinely different clusters can collapse onto the same stripped-down formula.
- The carboxylate carries the charge that balances the metal oxidation state. Removing it makes any charge or electronic analysis meaningless.
- The error is largest for the most important structures — the ones with the most carboxylate bridges. UiO-66, the most-studied Zr MOF, loses 36 atoms from its node.

### 2.3 · The fix — `complete_nodes`


After the published split has run, look at each linker block. If a carboxylate carbon in that block has both of its oxygens bonded to metal atoms of a single node, reassign that `COO` group to the node. The bond that is cut moves outward by one atom: instead of cutting metal–oxygen, cut the carboxylate-carbon–ring-carbon bond, which is where the inorganic and organic parts genuinely meet.


```
def complete_nodes(geom, nodes, linkers):
    """Move each bridging carboxylate from the linker side to the node side."""
    for node in nodes:
        metals = {a for a in node if is_metal(geom.elements[a])}

        for c in carbons_in(linkers):
            oxygens = [o for o in neighbours(geom, c)
                       if geom.elements[o] == "O"]
            if len(oxygens) != 2:
                continue                       # not a carboxylate carbon

            # both oxygens must bind THIS node - that is what makes it bridging
            if all(any(m in neighbours(geom, o) for m in metals) for o in oxygens):
                move_to_node(node, [c] + oxygens)

    return nodes, linkers
```
*code_08_proposed_fixes.py. The condition is deliberately strict: exactly two oxygens, both bound to the same node. ZIF-8 has no carbon that satisfies it, so ZIF-8 is untouched.*


---


## 3 · Limitation 2 — the rule is written around carboxylates


MOFs bind through many chemistries: carboxylate, imidazolate, phosphonate, sulfonate, tetrazolate, pyridyl. The metal-oxo rule handles carboxylates implicitly, because oxygen is what it cuts through, but it has no notion of a donor atom in general. Any completion logic bolted on afterwards inherits the same narrowness.


**The fix — `donor_agnostic`.** State the rule in terms of *donor atoms* rather than oxygen specifically. A donor is any N, O, S or P bonded to a metal. The bridging test then becomes: a small group whose donor atoms all bind the same node belongs to that node. Written this way the same code handles imidazolates and phosphonates without a new special case, and the carboxylate behaviour is unchanged because a carboxylate is simply the case where both donors are oxygen.


> **Why this fix produces no visible change on the four test structures**
>
> Three of the four are carboxylate MOFs, and ZIF-8 has a nitrogen donor that is not bridging — its imidazolate binds one Zn per nitrogen rather than chelating a single cluster.
>
> So the measured effect on this test set is zero, and that is reported honestly on the website rather than hidden. Its value is in generality, not in the four numbers here; the effect would show on phosphonate and tetrazolate frameworks, which this test set does not contain.


## 4 · Limitation 3 — the bond cutoff is a hard threshold on a continuum


Whether two atoms are bonded is decided by `distance < (r₁ + r₂) × tolerance`. Real coordination bonds do not respect a sharp line: a Zr–O contact 2% inside the cutoff and one 2% outside are chemically almost the same, but the algorithm treats one as a bond and the other as nothing. Since the split is computed from the bond graph, a borderline bond can move an entire group of atoms between node and linker.


**The fix — report the uncertainty instead of hiding it.** The `assess_quality` function flags every bond within 10% of its cutoff, so a user can see exactly which decisions were marginal and how many atoms depend on them. This does not remove the arbitrariness — no threshold can — but it converts a silent guess into a visible one.


```
def assess_quality(geom, partition):
    """Report where the split rests on a marginal decision."""
    borderline = []
    for (i, j, shift) in geom.bonds:
        cutoff = radius_sum(geom, i, j)
        d = distance(geom, i, j, shift)
        if 0.90 * cutoff < d < 1.10 * cutoff:
            borderline.append((i, j, d, cutoff, d / cutoff))

    return {
        "borderline_bonds":    borderline,
        "rod_candidates":      find_metal_metal_chains(geom),
        "discarded_fragments": blocks_with_no_connections(partition),
    }
```
*code_08_proposed_fixes.py*


## 5 · Limitation 4 — rod and chain SBUs


Not every MOF has discrete clusters. In **rod MOFs** the inorganic component is a continuous one-dimensional chain of metal polyhedra running through the crystal. Cutting every metal bond does not produce a node — it produces a row of isolated metal atoms, and the fact that they formed a connected rod is lost entirely.


**The fix — detect and report, do not silently mangle.** `assess_quality` looks for chains of metal atoms connected through bridging donors that extend across a periodic boundary. Where such a chain is found, the output says so, because a rod SBU needs a different treatment rather than a patched-up version of the discrete-cluster rule. None of the four test structures is a rod MOF, so the detector correctly reports none — which is at least evidence it does not produce false positives.


---


## 6 · The fixes together


All four are implemented as independent switches, so each can be turned on alone and its effect measured separately. That matters: a bundle of changes evaluated only as a bundle cannot be attributed.


```
from code_08_proposed_fixes import run_fixed

# the published baseline
base  = run_fixed("UiO-66.cif", complete_nodes=False, donor_agnostic=False)

# one fix at a time
fix1  = run_fixed("UiO-66.cif", complete_nodes=True,  donor_agnostic=False)
fix2  = run_fixed("UiO-66.cif", complete_nodes=False, donor_agnostic=True)

# everything on
all_  = run_fixed("UiO-66.cif", complete_nodes=True,  donor_agnostic=True)
```
*Each configuration is a separate, reproducible run.*


### 6.1 · What is preserved


The fixes were designed so that the properties that made the published rule useful survive:

| Property of the published rule | Still true after the fixes? |
|---|---|
| Deterministic — same input, same output | Yes |
| No chemical knowledge base or lookup table required | Yes — only `is_metal()` and donor elements |
| Never fails or hangs on an unusual structure | Yes — a structure with no bridging group is simply unchanged |
| Runs unattended at database scale | Yes — one extra pass over the linker blocks |
| Topology and coordination numbers unaffected | Yes — verified for all four structures |


That last row is worth emphasising. Moving the carboxylate from the linker to the node changes *what the blocks contain*, not *which blocks connect to which*. Every published coordination number and net symbol still comes out correct after the fix — the framework connectivity is untouched, only the chemical identity of the node is repaired.


## 7 · Honest scope

- **The donor-agnostic fix is not demonstrated on this test set.** Its effect here is zero, because none of the four structures has a bridging non-oxygen donor. Its justification is generality, and that is how it is presented.
- **Rod SBUs are detected, not handled.** Reporting that a structure needs different treatment is not the same as treating it.
- **The threshold problem is surfaced, not solved.** Any distance-based bond perception has a grey zone; the contribution is making it visible.
- **These fixes have not been run at database scale.** They are demonstrated on four structures with published ground truth. Scaling to CoRE MOF or QMOF is a loop over the same functions, but it has not been done here.
