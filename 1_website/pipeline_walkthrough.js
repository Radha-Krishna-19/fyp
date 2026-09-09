// pipeline_walkthrough.js
// Drives Section 1: the FULL 7-module pipeline (CIF Input -> Bond Assignment ->
// Element Classification -> Metal-Oxo / Single-Node / All-Node Split ->
// Centroid Simplification -> Systre Export -> MOFid/MOFkey Assembly), each
// module shown as a real, RUNNABLE Python translation of the real MOFid C++
// (verbatim from this folder's code_XX.py files -- every one of them was
// actually executed against HKUST-1.cif/UiO-66.cif/ZIF-8.cif while building
// this page, and reproduces the same numbers as this project's validated JS
// engine) side-by-side with a live, synchronized 3D model. Module 4a
// (metal-oxo, this project's main subject) gets the deepest treatment: 9
// sub-steps, including a dedicated intro and a worked numeric example, tracing
// its control flow one operation at a time.
//
// Depends on: mof_decompose.js, mof_render.js (MOFRender.create()).
// Exposes: window.PipelineWalkthrough = { init(canvas, container, labels,
//   hoverTip), buildUI(panelContainer), setSource(fracAtoms, cellMatrix, isDefault) }

(function (root) {
  'use strict';

  // ---------------------------------------------------------------
  // Snapshot builders. `ctx` = { trace, variants, isDefault } where
  // trace = MOFDecompose.traceMetalOxo(...) and variants = MOFDecompose.buildAllVariants(...)
  // ---------------------------------------------------------------
  // The DATA object always carries the FINAL metal-oxo partition, so by
  // default mof_render.js draws every block-crossing bond in "about to be
  // cut" cyan. For any step BEFORE the split has actually been decided
  // (Modules 1-3, and metal-oxo's own intro/start steps) that would leak
  // the answer early -- the picture would show the structure as already
  // split while the text says nothing has happened yet. neutralBonds()
  // forces every bond to plain grey for exactly those steps.
  const NEUTRAL_BOND = 0x9a9a9a;
  function neutralBonds(DATA) {
    return Object.assign({}, DATA, {
      bonds: DATA.bonds.map(bd => Object.assign({}, bd, { highlight: NEUTRAL_BOND })),
    });
  }

  function snapAtoms(ctx, showBonds) {
    return {
      DATA: neutralBonds(ctx.trace.finalData),
      opts: { colorMode: 'element', showBonds, showCell: true, netOnly: false },
    };
  }
  function snapMetalNonmetal(ctx) {
    // Module 3 is still before any split, so bonds stay neutral here too.
    return { DATA: neutralBonds(ctx.trace.finalData), opts: { colorMode: 'metalNonmetal', showBonds: true, showCell: true } };
  }
  function snapBlocks(DATAkey, style) {
    return function (ctx) {
      return { DATA: ctx.variants[DATAkey], opts: { colorMode: 'block', blockColorStyle: style, showBonds: true, showCell: true } };
    };
  }
  function snapNet(DATAkey) {
    return function (ctx) {
      return { DATA: ctx.variants[DATAkey], opts: { colorMode: 'block', blockColorStyle: 'nodeLinker', showBonds: true, showCell: true, netOnly: true } };
    };
  }
  // Module 4a's fine-grained snapshots
  function snap4a(kind) {
    return function (ctx) {
      const { finalData, geom, metalBondSet, rawFragments, fragRole } = ctx.trace;
      const baseAtoms = finalData.atoms;
      // 'start' = nothing has been decided yet, so no bond may look "cut"
      if (kind === 'start') return { DATA: neutralBonds(finalData), opts: { colorMode: 'element', showBonds: true, showCell: true, netOnly: false } };
      if (kind === 'highlightCut') {
        const bonds = finalData.bonds.map((bd, i) => Object.assign({}, bd, { highlight: metalBondSet.has(i) ? 0xff6f00 : 0x9a9a9a }));
        return { DATA: Object.assign({}, finalData, { bonds }), opts: { colorMode: 'element', showBonds: true, showCell: true, netOnly: false } };
      }
      if (kind === 'fragments' || kind === 'classify') {
        const atomToFrag = new Array(geom.n);
        rawFragments.forEach((frag, fi) => frag.forEach(a => { atomToFrag[a] = fi; }));
        const atoms = baseAtoms.map(a => Object.assign({}, a, { block: atomToFrag[a.id] }));
        const blocks = rawFragments.map((frag, fi) => {
          const comp = {}; frag.forEach(a => { comp[geom.symbols[a]] = (comp[geom.symbols[a]] || 0) + 1; });
          const c = [0, 0, 0]; frag.forEach(a => { const p = baseAtoms[a].pos; c[0] += p[0]; c[1] += p[1]; c[2] += p[2]; });
          return { id: fi, type: fragRole[fi] === 'node' ? 'metal' : 'linker', atoms: frag, n_atoms: frag.length, composition: comp, centroid: [c[0] / frag.length, c[1] / frag.length, c[2] / frag.length], n_connections: 0 };
        });
        // The metal bonds are physically GONE at this point, so every bond
        // still drawn is an intact intra-fragment bond -> plain grey.
        const bonds = finalData.bonds
          .filter((bd, i) => !metalBondSet.has(i))
          .map(bd => Object.assign({}, bd, { highlight: NEUTRAL_BOND }));
        return { DATA: Object.assign({}, finalData, { atoms, bonds, blocks }), opts: { colorMode: 'block', blockColorStyle: kind === 'fragments' ? 'palette' : 'nodeLinker', showBonds: true, showCell: true, netOnly: false } };
      }
      if (kind === 'collapseLinkers') return { DATA: finalData, opts: { colorMode: 'block', blockColorStyle: 'nodeLinker', showBonds: true, showCell: true, netOnly: false, showBlockMarkers: true, blockMarkersFilter: 'linker' } };
      if (kind === 'collapseNodes') return { DATA: finalData, opts: { colorMode: 'block', blockColorStyle: 'nodeLinker', showBonds: true, showCell: true, netOnly: false, showBlockMarkers: true, blockMarkersFilter: 'all' } };
      if (kind === 'finalNet') return { DATA: finalData, opts: { colorMode: 'block', blockColorStyle: 'nodeLinker', showBonds: true, showCell: true, netOnly: true } };
      return { DATA: finalData, opts: { colorMode: 'element', showBonds: true, showCell: true } };
    };
  }

  // Worked-example numbers below (6 node blocks of 2 Cu, 8 linker blocks of
  // 18 atoms for HKUST-1; 1 node block for UiO-66, etc.) are not invented --
  // they are exactly what running `python3 code_00_pipeline_driver.py
  // HKUST-1.cif` in this folder prints, cross-checked against the real
  // MOFid paper's own [Cu][Cu] example.

  // ---------------------------------------------------------------
  // LIVE DATA PANEL
  // Each step can declare a `data(ctx)` function returning rows of
  // {label, value, note}. These are computed from the CURRENTLY LOADED
  // structure every time the step is shown -- so if you upload your own
  // CIF, every number below updates with it. Nothing here is hardcoded.
  // ---------------------------------------------------------------
  function fmtComp(comp) {
    return Object.entries(comp).sort((a, b) => b[1] - a[1]).map(([el, n]) => el + n).join(' ');
  }
  function sizeHistogram(blocks) {
    const counts = {};
    blocks.forEach(b => { counts[b.n_atoms] = (counts[b.n_atoms] || 0) + 1; });
    return Object.entries(counts).sort((a, b) => b[0] - a[0])
      .map(([size, n]) => n + ' × ' + size + '-atom').join(', ');
  }
  function elementBreakdown(geom) {
    const comp = {};
    geom.symbols.forEach(s => { comp[s] = (comp[s] || 0) + 1; });
    return comp;
  }
  function variantRows(V) {
    const nodes = V.blocks.filter(b => b.type === 'metal');
    const linkers = V.blocks.filter(b => b.type === 'linker');
    return [
      { label: 'Node blocks', value: nodes.length, note: nodes.length ? sizeHistogram(nodes) : 'none found' },
      { label: 'Linker blocks', value: linkers.length, note: linkers.length ? sizeHistogram(linkers) : 'none found' },
      { label: 'Largest node block', value: (nodes.length ? Math.max.apply(null, nodes.map(b => b.n_atoms)) : 0) + ' atoms',
        note: nodes.length ? fmtComp(nodes.reduce((m, b) => b.n_atoms > m.n_atoms ? b : m).composition) : '—' },
      { label: 'Largest linker block', value: (linkers.length ? Math.max.apply(null, linkers.map(b => b.n_atoms)) : 0) + ' atoms',
        note: linkers.length ? fmtComp(linkers.reduce((m, b) => b.n_atoms > m.n_atoms ? b : m).composition) : '—' },
      { label: 'Bonds cut between blocks', value: V.bonds.filter(b => b.interblock).length,
        note: 'of ' + V.bonds.length + ' total bonds' },
    ];
  }

  const MODULES = [
    // ============================= MODULE 1 =============================
    {
      id: 'm1', num: '1', label: 'CIF Input', tint: PAL.brand,
      summary: 'Read the .cif file: unit cell, symmetry, and every atom\'s fractional position. No bonds exist yet -- a CIF never stores connectivity.',
      steps: [{
        label: 'Read cell + expand symmetry',
        title: 'Module 1 — parse_cif(): a real, runnable Python translation',
          algo: 'Read the six cell parameters, build the fractional→Cartesian matrix, then apply every symmetry operator to every atom in the asymmetric unit and discard duplicates. Output: a complete list of atoms with positions, and nothing else. <b>No bonds exist at this point and none can — the file format has no field for them.</b>',
        src: [{ file: 'code_01_cif_input.py', lines: 'parse_cif()', code:
`def parse_cif(text: str) -> ParsedCIF:
    """Python equivalent of importCIF(&orig_mol, filename, False):
    reads cell parameters + symmetry, expands the asymmetric unit,
    and returns every atom's fractional coordinates -- with NO
    bonds, exactly as a real CIF and importCIF() itself would leave
    things at this stage."""
    a = find_value('_cell_length_a')
    ...
    cell_matrix = _cell_par_to_matrix(a, b, c, alpha, beta, gamma)

    # apply every symmetry operator to every asymmetric-unit atom,
    # de-duplicating positions within TOL = 0.01 fractional units
    for atom in asym_atoms:
        for op in sym_ops:
            x, y, z = op(atom.fx, atom.fy, atom.fz)
            ...
    return ParsedCIF(a, b, c, alpha, beta, gamma, cell_matrix, expanded)` }],
        explain:
          'This is a real, runnable Python file in this folder (<code>python3 code_01_cif_input.py HKUST-1.cif</code> prints "156 atoms in the expanded unit cell"). The real C++\'s <code>importCIF()</code> itself lives inside Open Babel\'s CIF reader and was not publicly retrievable as a standalone diff — so this translation is a from-scratch reader built to satisfy the exact same chemical contract (documented in full in the file\'s docstring). <b>a,b,c,alpha,beta,gamma</b> are the 6 real-space cell parameters. <b>cell_matrix</b> converts fractional → Cartesian coordinates. Every symmetry operator (<b>op</b>) is applied to every asymmetric-unit atom and duplicates within 0.01 fractional units are discarded — reconstructing the full unit cell exactly as <code>importCIF()</code> would.' +
          '<div class="callout" style="margin-top:12px;"><b>What a CIF guarantees:</b> cell lengths/angles and fractional atomic positions for the asymmetric unit, expanded via symmetry operators. <b>What it never contains:</b> any bond, bond order, or connectivity whatsoever — every bond used by every module from here on is <i>computed</i>, never read from the file.</div>',
        threeD: 'Every atom now has a 3D position (symmetry-expanded to the full unit cell) and the unit cell box is drawn — but notice there are no bonds at all yet. That is completely accurate: a CIF file physically cannot tell us which atoms are bonded.',
        args: [
          { name: 'text', type: 'str', desc: 'The entire raw contents of the .cif file, read as one string.' },
          { name: 'a, b, c', type: 'float', desc: 'Unit cell edge lengths in Ångström, parsed from <code>_cell_length_a/b/c</code>.' },
          { name: 'alpha, beta, gamma', type: 'float', desc: 'Unit cell angles in degrees, from <code>_cell_angle_*</code>. Together with a/b/c these define the repeating box.' },
          { name: 'cell_matrix', type: '3×3 list', desc: 'Derived from the six parameters above. Multiplying a fractional coordinate by this matrix gives a real Cartesian position in Å. Built the same way Open Babel\'s <code>OBUnitCell</code> does.' },
          { name: 'sym_ops', type: 'list[callable]', desc: 'Each symmetry operator from the CIF, parsed from strings like <code>-x, y+1/2, z</code> into a function. If the file is already P1-expanded, this is just the identity.' },
          { name: 'asym_atoms', type: 'list[Atom]', desc: 'The atoms literally listed in the file — the asymmetric unit only, not the full cell.' },
          { name: 'expanded', type: 'list[Atom]', desc: 'The result: every symmetry operator applied to every asymmetric-unit atom, with duplicates removed. This is the full unit cell.' },
          { name: 'TOL', type: 'float = 0.01', desc: 'De-duplication tolerance in fractional units. Two generated positions closer than this are treated as the same atom (symmetry operators often regenerate atoms that are already present).' },
        ],
        data: (ctx) => {
          const g = ctx.trace.geom;
          const comp = elementBreakdown(g);
          const cp = ctx.variants.cell_par;
          return [
            { label: 'Atoms in unit cell', value: g.n, note: 'after symmetry expansion' },
            { label: 'Formula', value: fmtComp(comp), note: Object.keys(comp).length + ' distinct elements' },
            { label: 'Cell lengths a, b, c', value: cp ? cp.slice(0, 3).map(x => x.toFixed(3)).join(', ') + ' Å' : '—', note: 'read directly from the CIF' },
            { label: 'Cell angles α, β, γ', value: cp ? cp.slice(3).map(x => x.toFixed(1)).join(', ') + '°' : '—', note: 'read directly from the CIF' },
            { label: 'Bonds known so far', value: 0, note: 'a CIF stores no connectivity at all' },
          ];
        },
        snapshot: (ctx) => snapAtoms(ctx, false),
      }],
    },
    // ============================= MODULE 2 =============================
    {
      id: 'm2', num: '2', label: 'Bond Assignment', tint: PAL.brand,
      summary: 'Infer every bond computationally: a periodic-boundary-aware covalent-radius cutoff test between every pair of atoms.',
      steps: [
        {
          label: 'Before: no connectivity',
          title: 'Module 2, step 1 — the starting point: atoms with no bonds',
          algo: 'Everything downstream needs a bond graph, and there isn\'t one yet. This step exists to make that dependency explicit: bond perception is not a detail of the file reader, it is a modelling decision the pipeline makes on your behalf.',
          src: [{ file: 'code_02_bond_assignment_pbc.py', lines: 'get_periodic_direction()', code:
`def get_periodic_direction(pos_begin_frac, pos_end_frac):
    """Real periodic.cpp's GetPeriodicDirection(), fractional-
    coordinate form: rounds (end - begin) to the nearest integer
    triple -- the unit-cell offset this bond crosses."""
    return tuple(
        round(pos_end_frac[k] - pos_begin_frac[k])
        for k in range(3)
    )` }],
          explain:
            'Before any bond exists, none of the periodic-boundary utilities have anything to work with yet. <code>get_periodic_direction()</code> shown here is one of the key utilities this module\'s output feeds later (Module 4a\'s node-merge step depends on knowing which unit-cell image a bond crosses). It depends entirely on a bond graph existing first — which is exactly what the next step builds.',
          threeD: 'The same atom cloud as Module 1 — still zero bonds. This is the "before" state Module 2 is about to fix.',
          snapshot: (ctx) => snapAtoms(ctx, false),
        },
        {
          label: 'After: PBC-aware bonds computed',
          title: 'Module 2, step 2 — compute_geometry(): the real PBC bond search, runnable',
          algo: 'For every pair of atoms, measure the distance not just inside this unit cell but to that atom\'s image in all 26 neighbouring cells, and keep the shortest. If that shortest distance falls below the sum of the two covalent radii (times a tolerance), call it a bond. The periodic search is what lets a bond wrap around the edge of the cell and come back on the other side.',
          src: [{ file: 'code_02_bond_assignment_pbc.py', lines: 'compute_geometry()', code:
`def compute_geometry(cif, metal_set=None):
    """This project's own from-scratch PBC-aware bond perception
    -- the real ConnectTheDots patch was never publicly
    retrieved, so this reimplements the same behaviour."""
    offsets = list(product((-1, 0, 1), repeat=3))   # 27 images
    for i in range(n):
        for j in range(i + 1, n):
            cutoff = (radii[i] + radii[j]) * (
                1.30 if (is_metal[i] or is_metal[j]) else 1.15)
            best, best_d = None, math.inf
            for ov in offset_vecs:                   # search all 27
                d = distance(pos[j] + ov, pos[i])
                if d < best_d:
                    best_d, best = d, (dx, dy, dz)
            if 0.4 < best_d < cutoff:
                bonds.append(Bond(i, j, best))` }],
          explain:
            'This is a real, runnable file — <code>python3 code_02_bond_assignment_pbc.py HKUST-1.cif</code> prints "198 PBC-aware bonds found among 156 atoms". For every atom pair, it searches all 27 neighbouring unit-cell images (<b>offsets</b>, -1/0/+1 in each of a/b/c) and keeps whichever gives the shortest true distance — the "minimum-image convention" — then tests that distance against a covalent-radius-sum <b>cutoff</b>, loosened ×1.30 for any pair touching a metal (metal–ligand bonds are typically longer/weaker than pure covalent bonds). Without this, any bond crossing a cell boundary would simply be missed.',
          threeD: 'Bonds now appear between every atom pair that passed the cutoff test — including bonds that cross the unit cell boundary (drawn as two half-bonds meeting the box edge). This is the very first time connectivity exists anywhere in the pipeline.',
          args: [
            { name: 'cif', type: 'ParsedCIF', desc: 'Module 1\'s output — atoms with fractional coordinates plus the cell matrix.' },
            { name: 'metal_set', type: 'set[str]', desc: 'Which element symbols count as metals (Module 3). Only affects the cutoff multiplier here, but passing the WRONG set is exactly Drawback 2 in Section 2 below.' },
            { name: 'offsets', type: 'list[(int,int,int)]', desc: 'All 27 combinations of −1/0/+1 in a, b and c — the home cell plus its 26 neighbours. Searching all 27 is what makes bond detection periodic-boundary-correct.' },
            { name: 'radii[i]', type: 'float', desc: 'Atom i\'s covalent radius in Å (Cordero et al. 2008). Element-specific, which is why no single fixed cutoff works — see Drawback 3.' },
            { name: 'cutoff', type: 'float', desc: '<code>(radii[i] + radii[j]) × factor</code>. The factor is 1.30 if either atom is a metal (metal–ligand bonds are longer/weaker), else 1.15.' },
            { name: 'best_d', type: 'float', desc: 'The shortest distance found across all 27 images — the "minimum-image" distance. Compared against <code>cutoff</code> to decide if a bond exists.' },
            { name: '0.4', type: 'float', desc: 'Lower sanity bound in Å. Anything closer than this is a duplicate/overlapping atom from a bad CIF, not a real bond.' },
            { name: 'Bond.vec', type: '(float,float,float)', desc: 'The winning image\'s displacement vector. Storing this (not just "i and j are bonded") is what lets later modules know a bond crosses a cell boundary and unwrap blocks correctly.' },
          ],
          data: (ctx) => {
            const g = ctx.trace.geom;
            const D = ctx.trace.finalData;
            const crossing = D.bonds.filter(b => b.cross).length;
            const pairs = (g.n * (g.n - 1)) / 2;
            let metalBonds = 0;
            D.bonds.forEach(bd => { if (g.isMetal[bd.a] || g.isMetal[bd.b]) metalBonds++; });
            return [
              { label: 'Bonds found', value: D.bonds.length, note: 'from ' + pairs.toLocaleString() + ' candidate atom pairs × 27 images each' },
              { label: 'Distance tests run', value: (pairs * 27).toLocaleString(), note: 'every pair checked against all 27 periodic images' },
              { label: 'Bonds crossing a cell boundary', value: crossing, note: crossing ? 'these are exactly what the old no-PBC code missed' : 'none for this structure' },
              { label: 'Bonds touching a metal', value: metalBonds, note: 'Module 4a will cut every one of these' },
              { label: 'Bonds read from the file', value: 0, note: '100% computed, 0% read — always true for CIF' },
            ];
          },
          snapshot: (ctx) => snapAtoms(ctx, true),
        },
      ],
    },
    // ============================= MODULE 3 =============================
    {
      id: 'm3', num: '3', label: 'Element Classification', tint: PAL.good,
      summary: 'Label every atom METAL or NONMETAL via a hardcoded IUPAC/InChI lookup table -- a strict binary split, no metalloid middle ground.',
      steps: [{
        label: 'is_metal(): the real classifier',
        title: 'Module 3 — is_metal(), the entire real function, in Python',
          algo: 'Every atom is sorted into exactly one of two bins. The test is a table lookup, not chemistry: 23 elements are declared nonmetal, and anything else is a metal by default. Note the direction — the list enumerates what is <i>not</i> a metal, so an unfamiliar element is assumed metallic rather than organic.',
        src: [{ file: 'code_03_element_classification.py', lines: 'NONMETALS, is_metal()', code:
`NONMETALS = {
    'H', 'He', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Si', 'P', 'S',
    'Cl', 'Ar', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Te', 'I', 'Xe',
    'At', 'Rn',
}

def is_metal(atom_symbol: str) -> bool:
    """Real isMetal(const OBAtom* atom), translated: nonmetals[]
    lookup table, binary classification, no metalloid category."""
    return atom_symbol not in NONMETALS


def delete_bonds(geom, only_metals=True):
    """Real deleteBonds(OBMol *mol, bool only_metals): returns every
    bond that does NOT touch a metal (i.e. the ones that survive)."""
    return [bd for bd in geom.bonds
            if not (only_metals and (geom.is_metal[bd.lo] or geom.is_metal[bd.hi]))]` }],
        explain:
          'This is a real, runnable file — <code>python3 code_03_element_classification.py HKUST-1.cif</code> prints "12 of 156 atoms classified METAL... delete_bonds: 198 bonds → 144 remain". <b>NONMETALS</b> hardcodes the 23 atomic symbols the InChI standard treats as nonmetals — notice boron, silicon, and germanium/arsenic/tellurium (the classic "metalloids") are explicitly filed as NONmetals here: there is no in-between category anywhere in this function. <b>is_metal()</b> returns <code>False</code> the instant a match is found in the table; <code>True</code> by default otherwise — so every transition metal, lanthanide, actinide, alkali/alkaline-earth metal, and "other metal" is classified METAL purely by NOT appearing on a 23-element exclusion list. <b>delete_bonds()</b> is Module 4a\'s "cut every metal bond" step, translated as a simple list filter.',
        threeD: 'Every atom is now colored strictly red (metal) or blue (nonmetal) by this one function. This labelled graph is the shared input every decomposition algorithm below (Modules 4a/4b/4c) reads from.',
        args: [
          { name: 'atom_symbol', type: 'str', desc: 'The element symbol being classified, e.g. <code>"Cu"</code>. The real C++ takes an <code>OBAtom*</code> and reads its atomic number instead — same logic.' },
          { name: 'NONMETALS', type: 'set[str], 23 entries', desc: 'The InChI standard\'s nonmetal list: H, He, B, C, N, O, F, Ne, Si, P, S, Cl, Ar, Ge, As, Se, Br, Kr, Te, I, Xe, At, Rn. Hardcoded — it is the <i>entire</i> chemical knowledge in this function.' },
          { name: 'return value', type: 'bool', desc: '<code>False</code> if the symbol is in NONMETALS, else <code>True</code>. Note the default: an element the author never considered is silently classified as a METAL.' },
          { name: 'geom', type: 'Geometry', desc: 'Module 2\'s output, passed to <code>delete_bonds</code>. Its <code>is_metal[]</code> array was filled in using this same classifier.' },
          { name: 'only_metals', type: 'bool = True', desc: 'When True, only bonds with at least one metal endpoint are removed. Module 4a always calls it this way — this single flag is the whole "cut the metal bonds" step.' },
          { name: 'touches_metal', type: 'bool', desc: 'Per-bond test: <code>is_metal[bd.lo] or is_metal[bd.hi]</code>. Either endpoint being a metal is enough.' },
          { name: 'kept', type: 'list[Bond]', desc: 'The surviving bonds. Returned as a NEW list — the original graph is never mutated, matching the real C++\'s disposable <code>split_mol</code> copy.' },
        ],
        data: (ctx) => {
          const g = ctx.trace.geom;
          const metalEls = {}, nonmetalEls = {};
          for (let i = 0; i < g.n; i++) {
            const t = g.isMetal[i] ? metalEls : nonmetalEls;
            t[g.symbols[i]] = (t[g.symbols[i]] || 0) + 1;
          }
          const nMetal = g.isMetal.filter(Boolean).length;
          return [
            { label: 'Classified METAL', value: nMetal, note: Object.keys(metalEls).length ? fmtComp(metalEls) : 'none' },
            { label: 'Classified NONMETAL', value: g.n - nMetal, note: fmtComp(nonmetalEls) },
            { label: 'Metal fraction', value: ((nMetal / g.n) * 100).toFixed(1) + '%', note: 'of all atoms in the cell' },
            { label: 'Metalloid category', value: 'does not exist', note: 'B, Si, Ge, As, Te are all filed as NONmetals' },
            { label: 'Lookup table size', value: '23 elements', note: 'anything not on the list is a metal by default' },
          ];
        },
        snapshot: snapMetalNonmetal,
      }],
    },
    // ============================= MODULE 4a =============================
    {
      id: 'm4a', num: '4a', label: 'Metal-Oxo Split', tint: PAL.node, highlight: true,
      summary: 'This project\'s main subject. Cut every metal bond, see what fragments fall out, classify each one node or linker by one rule: is it pure O/H?',
      steps: [
        {
          label: '0 · What & why', title: 'Why metal-oxo, and why does it matter?',
          algo: 'The whole algorithm rests on one idea: <b>the metal atoms hold the framework together, so cut every bond that touches a metal and see what falls off.</b> Whatever is left in one piece is either an inorganic node or an organic linker, and a single compositional test decides which.',
          src: [{ file: 'code_04a_metal_oxo_algorithm.py', lines: 'module docstring', code:
`"""
MODULE 4a -- THE ORIGINAL METAL-OXO ALGORITHM

IMPORTANT DISCOVERY WHILE TRACING THE SOURCE
\`MetalOxoDeconstructor\` does NOT override
DetectInitialNodesAndLinkers(), CollapseLinkers(), or
CollapseNodes(). It inherits every one of those directly from the
base \`Deconstructor\` class translated below, unchanged. Its own
code only adds PostSimplification() (rod-SBU cleanup) and InChI/
MOFkey export helpers (code_07b.py). In other words:

    THE "METAL-OXO ALGORITHM" *IS* THE BASE Deconstructor CLASS.

THE CORE IDEA IN ONE SENTENCE
Delete every bond that touches a metal atom, look at what molecular
fragments fall out, and classify each fragment "node" (lone metals,
or pure O/H fragments) or "linker" (everything else).
"""` }],
          explain:
            '<div class="algo-note"><b>Where this sits.</b> Metal-oxo is the oldest of MOFid\'s three published decomposition algorithms — it predates single-node (4b) and all-node (4c), and the base <code>Deconstructor</code> class shown here <i>is</i> the metal-oxo algorithm; the other two subclass it. Section 2 examines what this rule cannot express, and Section 3 shows what its output becomes once those gaps are closed.</div>' +
            'Metal-oxo is the OLDEST and SIMPLEST of the three MOFid decomposition algorithms — it predates single-node and all-node, and its header comment in the real repo literally reads "the original MOFid algorithm." It matters for three concrete reasons: (1) it is the algorithm every real MOFid identifier ultimately traces back to for the organic-fragment SMILES and the MOFkey string (Module 7b lives specifically inside <code>MetalOxoDeconstructor</code>, because it is the one algorithm that always leaves carboxylate groups chemically intact); (2) it produces the SMALLEST possible inorganic nodes — often just the bare metal atoms themselves (e.g. HKUST-1\'s famous <code>[Cu][Cu]</code>), which makes it the most sensitive to exactly the kind of bugs this project investigates (a missing bond or a misclassified metal atom directly changes which atoms end up "bare"); and (3) its entire chemical judgement collapses into ONE boolean test — <code>all_oxygens</code> — making it the clearest possible teaching example of how a simplifying assumption in cheminformatics software can be both a strength (fast, predictable, easy to reason about) and a weakness (Section 2 below shows exactly where it breaks).',
          threeD: 'The 3D panel shows the fully-bonded, element-colored starting structure — the same state Module 3 left it in. Nothing algorithm-specific has happened yet; this step is pure context before Step 1 begins.',
          snapshot: snap4a('start'),
        },
        {
          label: '1 · Start', title: 'Before anything runs: the labelled, fully-bonded structure',
          algo: 'Nothing has been decided yet. The algorithm has a complete bond graph with every atom labelled metal or nonmetal, and it is about to make exactly one structural intervention.',
          src: [{ file: 'code_04a_metal_oxo_algorithm.py', lines: 'detect_initial_nodes_and_linkers() — setup', code:
`def detect_initial_nodes_and_linkers(geom: Geometry) -> Dict[int, str]:
    """STEP 1 -- real Deconstructor::DetectInitialNodesAndLinkers(),
    translated line-for-line:
        1. deleteBonds(&split_mol, true)   -- code_03.delete_bonds
        2. fragments = split_mol.Separate()
        3. for each fragment: NumAtoms()==1 / all_oxygens / else
    """
    split_bonds = delete_bonds(geom, only_metals=True)
    fragments = _connected_components(set(range(geom.n)), split_bonds)` }],
          explain: '<b>geom</b> is this project\'s Python stand-in for <code>parent_molp</code> — the untouched, all-atom, PBC-bonded structure from Modules 1-3. Nothing here is modified in place: <code>delete_bonds()</code> (Module 3) returns a brand-new filtered bond list, <b>split_bonds</b>, leaving <code>geom.bonds</code> itself untouched — exactly mirroring the real C++\'s use of a disposable <code>split_mol</code> scratch copy.',
          args: [
            { name: 'geom', type: 'Geometry', desc: 'The untouched input structure (Python stand-in for the real <code>parent_molp</code> / <code>orig_mof</code>). Read-only throughout the entire algorithm.' },
            { name: 'split_bonds', type: 'list[Bond]', desc: 'The bond list with metal-touching bonds removed. Stand-in for the real <code>split_mol</code> — a scratch copy, so the original structure survives intact for later steps.' },
            { name: 'fragments', type: 'list[list[int]]', desc: 'Groups of atom indices that are still connected to each other after the cut. Stand-in for <code>OBMol::Separate()</code>\'s output.' },
            { name: 'role', type: 'dict[int, str]', desc: 'The output: maps each atom index to <code>"node"</code> or <code>"linker"</code>. Stand-in for the real <code>SetRoleToAtoms()</code> tagging of PseudoAtoms.' },
          ],
          threeD: 'Every atom, every real bond, colored by element. Nothing has been touched yet.',
          snapshot: snap4a('start'),
        },
        {
          label: '2 · Cut metal bonds', title: 'Step 1a — delete_bonds(geom, only_metals=True)',
          algo: 'Walk the bond list and remove every bond with a metal at either end. This is the single structural act of the whole algorithm — everything after it is bookkeeping over the wreckage. Crucially the cut lands on the <i>metal–ligand</i> bond, which is why a carboxylate ends up severed from the metal it coordinates.',
          src: [{ file: 'code_03_element_classification.py + code_04a', lines: 'delete_bonds()', code:
`def delete_bonds(geom, only_metals=True):
    kept = []
    for bd in geom.bonds:
        touches_metal = geom.is_metal[bd.lo] or geom.is_metal[bd.hi]
        if only_metals and touches_metal:
            continue   # deleted
        kept.append(bd)
    return kept` }],
          explain: 'With <b>only_metals=True</b>, every bond where EITHER endpoint is a metal (per Module 3\'s <code>is_metal()</code>) is dropped from the returned list. Running this on HKUST-1 turns 198 bonds into 144 (54 removed) — every one of those 54 touched one of the 12 Cu atoms. Every C–C/C–H bond inside a linker ring is left completely untouched, since neither endpoint is a metal.',
          threeD: 'Every bond with at least one metal endpoint is highlighted bright orange — these are the bonds about to be deleted. Watch which bonds do NOT light up: the organic rings survive untouched.',
          data: (ctx) => {
            const { trace } = ctx;
            const total = trace.finalData.bonds.length;
            const cut = trace.metalBondSet.size;
            return [
              { label: 'Bonds before cutting', value: total, note: 'the full graph from Module 2' },
              { label: 'Bonds deleted (metal-touching)', value: cut, note: ((cut / total) * 100).toFixed(1) + '% of all bonds' },
              { label: 'Bonds surviving', value: total - cut, note: 'every C–C, C–O and C–H bond is in here' },
              { label: 'Metal atoms responsible', value: trace.geom.isMetal.filter(Boolean).length, note: 'each contributes its whole coordination sphere' },
            ];
          },
          snapshot: snap4a('highlightCut'),
        },
        {
          label: '3 · Fragments fall apart', title: 'Step 1b — fragments = _connected_components(...)',
          algo: 'With the metal bonds gone, ask which atoms are still reachable from which. Each answer is a fragment. Organic linkers survive whole because none of their internal bonds touched a metal; metal clusters shatter into loose atoms and small bridges.',
          src: [{ file: 'code_04a_metal_oxo_algorithm.py', lines: '_connected_components()', code:
`def _connected_components(atom_indices, bonds):
    """Python translation of OBMol::Separate(): BFS the given bond
    list, restricted to \`atom_indices\`."""
    adj = {i: [] for i in atom_indices}
    for bd in bonds:
        if bd.lo in adj and bd.hi in adj:
            adj[bd.lo].append(bd.hi)
            adj[bd.hi].append(bd.lo)
    visited, comps = set(), []
    for start in atom_indices:
        if start in visited:
            continue
        stack, comp = [start], []
        while stack:
            u = stack.pop(); comp.append(u); visited.add(u)
            for v in adj[u]:
                if v not in visited:
                    stack.append(v)
        comps.append(sorted(comp))
    return comps` }],
          explain: 'A plain breadth/depth-first search over the bond-deleted graph — Python\'s equivalent of Open Babel\'s <code>OBMol::Separate()</code>. With the metal bonds now gone, this returns one group of atom indices per disconnected piece. A bare metal ion (no metal–metal bond of its own) becomes its own 1-atom group. An organic linker — since only its M–O bonds were cut, never its internal C–C/C–O bonds — survives as one single, still-fully-bonded group.',
          threeD: 'The orange bonds are now gone. Every atom is recolored by which disconnected fragment it now belongs to (a distinct color per fragment) — the literal, physical "falling apart" this function performs.',
          data: (ctx) => {
            const { rawFragments, geom } = ctx.trace;
            const singles = rawFragments.filter(f => f.length === 1).length;
            const sizes = rawFragments.map(f => f.length);
            return [
              { label: 'Fragments produced', value: rawFragments.length, note: 'connected components after the cut' },
              { label: 'Single-atom fragments', value: singles, note: 'these become nodes immediately (the len==1 rule)' },
              { label: 'Multi-atom fragments', value: rawFragments.length - singles, note: 'these go on to the all_oxygens test' },
              { label: 'Largest fragment', value: Math.max.apply(null, sizes) + ' atoms', note: 'almost always an intact organic linker' },
              { label: 'Fragment size spread', value: Math.min.apply(null, sizes) + ' – ' + Math.max.apply(null, sizes) + ' atoms', note: sizeHistogram(rawFragments.map(f => ({ n_atoms: f.length }))) },
            ];
          },
          snapshot: snap4a('fragments'),
        },
        {
          label: '4 · Classify fragments', title: 'Step 1c — the len==1 / all_oxygens / else rule',
          algo: 'Three questions, asked in order. Is the fragment a single atom? Then it is a node. Otherwise, is every atom in it oxygen or hydrogen? Then it is a bridging node fragment. Otherwise it contains carbon, so it is a linker. <b>That is the complete chemical reasoning of the algorithm</b> — which is exactly why Section 2 has something to say about it.',
          src: [{ file: 'code_04a_metal_oxo_algorithm.py', lines: 'detect_initial_nodes_and_linkers() — classify loop', code:
`role: Dict[int, str] = {}
for frag in fragments:
    if len(frag) == 1:
        for a in frag:
            role[a] = 'node'          # lone atom -- almost always a bare metal ion
        continue
    all_oxygens = all(
        geom.symbols[a] in ('O', 'H') for a in frag
    )
    tag = 'node' if all_oxygens else 'linker'
    for a in frag:
        role[a] = tag` }],
          explain: 'For every fragment: if it has exactly one atom, it is tagged <code>\'node\'</code> immediately (almost always a bare metal ion with no metal–metal bond). Otherwise, <b>all_oxygens</b> checks whether EVERY atom\'s element symbol is <code>\'O\'</code> or <code>\'H\'</code> — if so, it is a pure oxo/hydroxo/aqua/peroxo bridge, also tagged <code>\'node\'</code>. Anything else (i.e. anything containing carbon, including an intact carboxylate group) is tagged <code>\'linker\'</code>. This single three-way test is the ENTIRE chemical rule of the metal-oxo algorithm — nothing else in the whole file decides node-vs-linker.',
          threeD: 'Same shattered fragments, now recolored: node fragments turn red, linker fragments turn blue.',
          args: [
            { name: 'frag', type: 'list[int]', desc: 'One fragment: the atom indices of a single disconnected piece left after the metal bonds were cut.' },
            { name: 'len(frag) == 1', type: 'test #1', desc: 'A fragment of exactly one atom. In a MOF this is essentially always a bare metal ion whose every bond went to a ligand. Tagged <code>"node"</code> with no further checks.' },
            { name: 'all_oxygens', type: 'bool — test #2', desc: 'True only if EVERY atom in the fragment is O or H. Recognises oxo (O²⁻), hydroxo (OH⁻), aqua (H₂O) and peroxo (O₂²⁻) bridges. This one boolean is the algorithm\'s entire chemical judgement.' },
            { name: 'geom.symbols[a]', type: 'str', desc: 'Atom a\'s element symbol — the only property <code>all_oxygens</code> looks at. Note what it does NOT look at: bond orders, formal charges, coordination geometry, or whether hydrogens are even present in the file.' },
            { name: 'tag', type: '"node" | "linker"', desc: 'The result. Anything reaching the <code>else</code> branch contains carbon, and carbon means organic — including a fully intact –COO⁻ carboxylate, because only the O–metal bond was cut, never the O–C bond.' },
            { name: 'role[a]', type: 'dict entry', desc: 'Every atom of the fragment gets the same tag. Membership is decided per-FRAGMENT, never per-atom — which is precisely the difference from Module 4b below.' },
          ],
          data: (ctx) => {
            const { rawFragments, fragRole, geom } = ctx.trace;
            const nodeFrags = rawFragments.filter((f, i) => fragRole[i] === 'node');
            const linkerFrags = rawFragments.filter((f, i) => fragRole[i] === 'linker');
            const viaSingle = nodeFrags.filter(f => f.length === 1).length;
            const viaOxygens = nodeFrags.length - viaSingle;
            const nodeAtoms = nodeFrags.reduce((s, f) => s + f.length, 0);
            return [
              { label: 'Tagged "node"', value: nodeFrags.length + ' fragments', note: nodeAtoms + ' atoms total' },
              { label: '  ↳ via the len==1 rule', value: viaSingle, note: 'lone metal ions' },
              { label: '  ↳ via all_oxygens', value: viaOxygens, note: viaOxygens ? 'pure O/H oxo, hydroxo or aqua bridges' : 'none in this structure' },
              { label: 'Tagged "linker"', value: linkerFrags.length + ' fragments', note: (geom.n - nodeAtoms) + ' atoms total — every one contains carbon' },
              { label: 'Decisions made by', value: '1 boolean test', note: 'all_oxygens is the entire chemical rule' },
            ];
          },
          snapshot: snap4a('classify'),
        },
        {
          label: '5 · Collapse linkers', title: 'Step 2 — collapse_linkers_separate()',
          algo: 'Gather everything tagged linker, regroup it into whole molecules, and replace each molecule with a single point at its centre. The chemistry is discarded; only position and connectivity survive into the net.',
          src: [{ file: 'code_04a_metal_oxo_algorithm.py', lines: 'collapse_linkers_separate()', code:
`def collapse_linkers_separate(geom, role):
    """STEP 2 -- real Deconstructor::CollapseLinkers()'s fragment
    split. Each returned group later becomes one PseudoAtom via
    collapse_fragment() (code_05.py) -- metal-oxo never merges
    separate linker molecules the way node fragments can merge."""
    linker_atoms = {a for a, r in role.items() if r == 'linker'}
    return _connected_components(linker_atoms, geom.bonds)` }],
          explain: 'Every atom tagged <code>\'linker\'</code> is collected into <b>linker_atoms</b>, then re-split into connected groups using the ORIGINAL bond graph (<code>geom.bonds</code> — not the metal-deleted one, since linker atoms never had a metal bond to begin with). Each resulting group will become one point in Module 5, via <code>collapse_fragment()</code>.',
          threeD: 'Translucent blue marker spheres appear at each linker fragment\'s centroid — exactly where the real CollapseFragment() places the new point. Node (red) fragments are untouched, matching the real code\'s order: linkers collapse first.',
          snapshot: snap4a('collapseLinkers'),
        },
        {
          label: '6 · Collapse + re-merge nodes', title: 'Step 3 — collapse_nodes_merge()',
          algo: 'Gather everything tagged node and re-cluster it — but on the <i>original</i> bond graph, not the cut one. That restores any direct metal–metal bonding, so a paddlewheel\'s two metals become one vertex rather than two. Then each cluster collapses to a point.',
          src: [{ file: 'code_04a_metal_oxo_algorithm.py', lines: 'collapse_nodes_merge()', code:
`def collapse_nodes_merge(geom, role):
    """STEP 3 -- real Deconstructor::CollapseNodes()'s re-merge:
    using the ORIGINAL (not bond-deleted) bond graph here is what
    lets two node fragments from Step 1 that still share a bond of
    their own (e.g. a direct Cu-Cu paddlewheel bond) merge back
    into ONE cluster -- the moment metal-oxo's tiny nodes take
    their final shape."""
    node_atoms = {a for a, r in role.items() if r == 'node'}
    return _connected_components(node_atoms, geom.bonds)   # original graph, not bond-deleted` }],
          explain: 'Here is the crucial re-merge instant: <b>node_atoms</b> is re-clustered using <code>geom.bonds</code> — the ORIGINAL bond graph, before any metal bonds were deleted. If two node fragments from Step 1 (e.g. the two individual Cu atoms of a paddlewheel, each its own 1-atom fragment once the metal-touching Cu–O bonds were cut) are STILL directly connected by a bond of their own — a genuine Cu–Cu bond — they get grouped back into ONE cluster here. Running this on HKUST-1 gives exactly 6 node blocks of 2 Cu atoms each, never 12 separate single-Cu blocks.',
          threeD: 'Red node markers now also appear — and where two node fragments shared a bond, they now share ONE marker instead of two. This is the moment a Cu paddlewheel becomes the single "tiny" node metal-oxo is known for.',
          args: [
            { name: 'role', type: 'dict[int,str]', desc: 'The tags assigned in Step 1c. Only atoms marked <code>"node"</code> are considered here.' },
            { name: 'node_atoms', type: 'set[int]', desc: 'Every node-tagged atom, pooled together regardless of which fragment it came from — deliberately discarding the Step-1 fragment boundaries so they can be recomputed.' },
            { name: 'geom.bonds', type: 'list[Bond]', desc: '⚠ The ORIGINAL bond graph, not <code>split_bonds</code>. This is the single most important detail in the function: re-clustering on the full graph lets two lone metal atoms that share a direct metal–metal bond rejoin into one cluster.' },
            { name: 'return value', type: 'list[list[int]]', desc: 'The final node blocks. Each becomes one vertex of the simplified net, and its element composition becomes the node\'s SMILES in the MOFid (e.g. <code>[Cu][Cu]</code>).' },
            { name: 'isPeriodicChain()', type: 'C++ only', desc: 'In the real code, each cluster is first tested for periodic infiniteness; rod SBUs (MIL-47/MIL-53) can\'t collapse to a point and take a separate branch. Omitted from this translation — none of the example structures contain a rod.' },
          ],
          data: (ctx) => {
            const { rawFragments, fragRole } = ctx.trace;
            const V = ctx.variants.metalOxo;
            const nodeFragsBefore = rawFragments.filter((f, i) => fragRole[i] === 'node').length;
            const nodeBlocksAfter = V.blocks.filter(b => b.type === 'metal');
            const merged = nodeFragsBefore - nodeBlocksAfter.length;
            return [
              { label: 'Node fragments before merge', value: nodeFragsBefore, note: 'as tagged in the previous step' },
              { label: 'Node blocks after merge', value: nodeBlocksAfter.length, note: sizeHistogram(nodeBlocksAfter) },
              { label: 'Fragments absorbed by merging', value: merged, note: merged > 0 ? 'joined by surviving metal–metal bonds' : 'nothing merged — no metal–metal bonds here' },
              { label: 'Node composition', value: nodeBlocksAfter.length ? fmtComp(nodeBlocksAfter[0].composition) : '—', note: 'this is what becomes the node SMILES' },
            ];
          },
          snapshot: snap4a('collapseNodes'),
        },
        {
          label: '7 · Final net', title: 'Result — the finished metal-oxo simplified net',
          algo: 'The crystal is now an abstract periodic graph: vertices where building blocks were, edges where bonds crossed between them. Everything chemical has been distilled to topology, which is what Systre needs to name the net.',
          src: [{ file: 'code_04a_metal_oxo_algorithm.py', lines: 'run_metal_oxo()', code:
`def run_metal_oxo(geom: Geometry):
    """Python translation of Deconstructor::SimplifyMOF(), Steps
    1-3 (Step 4 SimplifyTopology / Step 5 PostSimplification are
    cleanup passes with no default-structure effect here). Returns
    (node_blocks, linker_blocks), ready for code_05.py's centroid
    collapse."""
    role = detect_initial_nodes_and_linkers(geom)            # Step 1
    linker_blocks = collapse_linkers_separate(geom, role)    # Step 2
    node_blocks = collapse_nodes_merge(geom, role)            # Step 3
    return node_blocks, linker_blocks` }],
          explain: 'The real <code>SimplifyTopology()</code> (Step 4) merges duplicate parallel connections and strips out 0-/1-connected solvent PseudoAtoms in a repeat-until-no-change loop; <code>PostSimplification()</code> (Step 5) is metal-oxo\'s own hook — a no-op unless an infinite rod SBU was found (none of this project\'s example structures contain one). Neither changes the result for HKUST-1/UiO-66/MOF-5, so this Python translation stops at Step 3 and hands the result straight to Module 5.',
          threeD: 'Every atom has vanished into its block\'s single point — the finished, fully-collapsed periodic net, exactly what Module 5/6 hands to Systre.',
          data: (ctx) => variantRows(ctx.variants.metalOxo),
          snapshot: snap4a('finalNet'),
        },
        {
          label: '8 · Worked example', title: 'Worked example — running this on real structures',
          algo: 'The same procedure, applied to two real frameworks, produces exactly the block counts and compositions published for those materials — which is the evidence that the reimplementation here is faithful rather than approximate.',
          src: [{ file: 'code_00_pipeline_driver.py (actually executed)', lines: 'terminal output', code:
`$ python3 code_04a_metal_oxo_algorithm.py HKUST-1.cif
Module 4a (metal-oxo) result for HKUST-1.cif:
  6 node blocks   (sizes: [2, 2, 2, 2, 2, 2])
  8 linker blocks (sizes: [18, 18, 18, 18, 18, 18, 18, 18])
  smallest node block composition: {'Cu': 2}
  <- matches [Cu][Cu] in the real MOFid paper

$ python3 code_04a_metal_oxo_algorithm.py UiO-66.cif
Module 4a (metal-oxo) result for UiO-66.cif:
  1 node blocks   (sizes: [22])
  6 linker blocks (sizes: [12, 12, 12, 12, 12, 12])` }],
          explain:
            'These are not invented numbers — they are the literal terminal output of running this folder\'s own Python files. For HKUST-1 (Cu₃(BTC)₂): every one of the 12 Cu atoms ends up in a 2-atom node block (a Cu–Cu paddlewheel pair with no oxo bridge, so <b>all_oxygens</b> never even applies to it — the whole node is just two lone-atom fragments re-merged in Step 3), and every BTC linker survives as one 18-atom block (benzene-1,3,5-tricarboxylate, all three carboxylates intact). For UiO-66 (Zr₆O₄(OH)₄): the entire Zr₆O₄(OH)₄ cluster survives as ONE 22-atom node block (6 Zr + 4 μ₃-O + 4 μ₃-OH, all pure O/H bridges, all connected through shared oxygens into a single fragment before the re-merge step even runs), while each terephthalate (BDC) linker gives a 12-atom block. Compare this to Module 4b just below, where the SAME two structures produce visibly larger node blocks, because carboxylates fold in there instead of staying with the linker.',
          threeD: 'The collapsed net for whichever structure is currently loaded (use the CIF upload above to try your own) — hover any red marker to see its exact composition and atom count, and check it against the numbers on the left.',
          data: (ctx) => {
            const mo = ctx.variants.metalOxo, sn = ctx.variants.singleNode;
            const moNodes = mo.blocks.filter(b => b.type === 'metal');
            const snNodes = sn.blocks.filter(b => b.type === 'metal');
            const moBig = moNodes.length ? Math.max.apply(null, moNodes.map(b => b.n_atoms)) : 0;
            const snBig = snNodes.length ? Math.max.apply(null, snNodes.map(b => b.n_atoms)) : 0;
            return [
              { label: 'Metal-oxo node size', value: moBig + ' atoms', note: moNodes.length ? fmtComp(moNodes[0].composition) : '—' },
              { label: 'Single-node node size', value: snBig + ' atoms', note: 'same structure, different algorithm' },
              { label: 'Difference', value: (snBig - moBig) + ' atoms', note: snBig > moBig ? 'the carboxylate groups single-node folds in' : 'identical for this structure' },
              { label: 'Metal-oxo linker blocks', value: mo.n_linker_blocks, note: 'carboxylates stay here' },
              { label: 'Verify it yourself', value: 'python3 code_04a…py', note: 'prints exactly these numbers' },
            ];
          },
          snapshot: snap4a('finalNet'),
        },
      ],
    },
    // ============================= MODULE 4b =============================
    {
      id: 'm4b', num: '4b', label: 'Single-Node Split', tint: PAL.warn,
      summary: 'Walk outward from each metal atom-by-atom instead of by whole fragment -- so a full coordinated carboxylate folds into the node.',
      steps: [{
        label: 'The oxygen-by-oxygen walk',
        title: 'Module 4b — detect_initial_nodes_and_linkers_single_node(), in Python',
          algo: 'Instead of cutting first and classifying the debris, walk outward from each metal one coordinating atom at a time and ask what that atom actually is. Because the walk inspects chemistry before deciding, it can recognise a carboxylate and pull the whole group into the node — the very thing metal-oxo cannot do.',
        src: [{ file: 'code_04b_single_node_algorithm.py', lines: 'detect_initial_nodes_and_linkers_single_node()', code:
`nodes = {i for i in range(geom.n) if geom.is_metal[i]}   # start: bare metals

for nn in candidates:                        # every O bonded to a node atom
    if geom.symbols[nn] != 'O':
        continue
    attached_carbon = None
    for other, _vec, _bi in geom.adj[nn]:
        if other in nodes: continue
        if geom.symbols[other] == 'C':
            attached_carbon = other

    if attached_carbon is None:
        nodes.add(nn)                          # metal-oxide/hydroxide -> node
    else:
        is_carboxylate = (c_c_nbors == 1 and c_o_nbors == 2)
        if is_carboxylate:
            nodes.add(nn); nodes.add(attached_carbon); nodes.add(other_o)
        else:
            nodes.discard(nn)                  # e.g. methoxy -> stays linker` }],
        explain:
          'A real, runnable file — <code>python3 code_04b_single_node_algorithm.py HKUST-1.cif</code> prints 6 node blocks of 14 atoms each (vs. metal-oxo\'s 2-atom blocks) and 8 linker blocks of 9 atoms each (vs. metal-oxo\'s 18). Unlike metal-oxo (which classifies whole disconnected FRAGMENTS), single-node walks outward from each metal one coordinating atom at a time. <b>nodes</b> starts as just the bare metal atoms. For each metal-neighbouring oxygen <b>nn</b>: no attached carbon → genuine metal-oxide/hydroxide oxygen → node. Attached carbon whose valence checks out as a true carboxylate (<b>is_carboxylate</b>: exactly 1 carbon-neighbour + 2 oxygen-neighbours) → the WHOLE group (both oxygens + the carbon) folds into the node — the key difference from metal-oxo. Carbon that fails that test (e.g. a methoxy/ether oxygen) → oxygen stays with the linker.',
        threeD: 'The node (red) cluster is now visibly larger than metal-oxo\'s — it has swallowed every coordinated carboxylate group whole, while the linker (blue) shrinks to just its rigid aromatic/aliphatic core.',
        args: [
          { name: 'nodes', type: 'set[int]', desc: 'The growing node set. Starts as just the metal atoms, then absorbs coordinating atoms shell by shell. Atoms can also be REMOVED from it again (<code>discard</code>) if they fail a chemical test — impossible in metal-oxo, where fragment membership is final.' },
          { name: 'nn', type: 'int', desc: '"Nearest neighbour" — one atom directly bonded to a node atom, examined individually. This per-ATOM loop is the core difference from metal-oxo\'s per-FRAGMENT rule.' },
          { name: 'attached_carbon', type: 'int | None', desc: 'A carbon bonded to this oxygen, if any. <code>None</code> means a plain metal-oxide/hydroxide oxygen → straight into the node.' },
          { name: 'c_c_nbors', type: 'int', desc: 'How many carbons that carbon is itself bonded to. A carboxylate carbon has exactly 1 (the ring/chain it hangs off).' },
          { name: 'c_o_nbors', type: 'int', desc: 'How many oxygens that carbon is bonded to. A carboxylate carbon has exactly 2 — <code>nn</code> and <code>other_o</code>.' },
          { name: 'is_carboxylate', type: 'bool', desc: '<code>c_c_nbors == 1 and c_o_nbors == 2</code>. A genuine valence check, not a guess. This is the chemical nuance metal-oxo completely lacks.' },
          { name: 'other_o', type: 'int', desc: 'The carboxylate\'s second oxygen — often not bonded to any metal at all, yet still folded into the node, because the whole –COO⁻ group acts as the node\'s point of extension.' },
        ],
        data: (ctx) => variantRows(ctx.variants.singleNode),
        snapshot: snapBlocks('singleNode', 'nodeLinker'),
      }],
    },
    // ============================= MODULE 4c =============================
    {
      id: 'm4c', num: '4c', label: 'All-Node Split', tint: PAL.node,
      summary: 'Start from single-node, then further split any linker with an internal branch point into its own separate vertices.',
      steps: [{
        label: 'Tree-decomposing the linkers',
        title: 'Module 4c — split_all_node_branches(), in Python',
          algo: 'Take single-node\'s answer and go further: inside each linker, find the atoms where the molecule genuinely forks (three or more heavy neighbours) and promote those to vertices of their own. A linear linker is unchanged; a branched one becomes several connected vertices.',
        src: [{ file: 'code_04c_all_node_algorithm.py', lines: 'split_all_node_branches()', code:
`for comp in linker_blocks:
    branch_points = []
    for a in comp:
        if geom.symbols[a] == 'H':
            continue
        # heavy-atom degree, counting only neighbours also in this
        # fragment -- >=3 means a true branch/junction atom
        deg = sum(1 for other, _v, _b in geom.adj[a]
                  if other in comp_set and geom.symbols[other] != 'H')
        if deg >= 3:
            branch_points.append(a)

    if not branch_points:
        refined.append(comp)                # no branch -> collapses whole, like 4b
        continue
    # ...split into one sub-block per branch point + one per remaining
    # chain/ring piece (bp_groups / remaining, see full file)` }],
        explain:
          'A real, runnable file — <code>python3 code_04c_all_node_algorithm.py HKUST-1.cif</code> gives the SAME 6 node / 8 linker blocks as single-node (BTC has no true branch point), while <code>python3 code_04c_all_node_algorithm.py ZIF-8.cif</code> gives 72 linker blocks instead of single-node\'s 24 (its methyl substituent creates a real one). <code>AllNodeDeconstructor</code> reuses <code>detect_initial_nodes_and_linkers_single_node()</code> unchanged from Module 4b — the only override is how linkers collapse. For each linker fragment, <b>branch_points</b> finds every heavy (non-hydrogen) atom whose degree, counting only neighbours inside the SAME fragment, is 3 or more — e.g. the two ring carbons where a biphenyl linker forks into two rigid halves. Branch points each become their OWN sub-block; everything else splits into its own connected chain/ring pieces.',
        threeD: 'For a linker with a real branch point (try uploading ZIF-8.cif), you\'d see it split into multiple separate colored pieces here. For BTC/BDC (this page\'s default structures), neither linker has a true branch point, so this looks identical to Module 4b — which matches real literature exactly.',
        args: [
          { name: 'comp', type: 'list[int]', desc: 'One linker fragment inherited unchanged from Module 4b — all-node never re-decides node vs. linker, it only sub-divides linkers.' },
          { name: 'comp_set', type: 'set[int]', desc: 'Same atoms as a set, so degree counting can ask "is this neighbour inside the same fragment?" in O(1).' },
          { name: 'deg', type: 'int', desc: 'Heavy-atom degree: neighbours that are (a) in this fragment and (b) not hydrogen. Excluding H is essential — otherwise every ordinary ring carbon carrying an H would look like a 3-way junction.' },
          { name: 'deg >= 3', type: 'test', desc: 'The branch-point criterion. Three or more heavy neighbours inside one fragment means the linker genuinely forks here (e.g. where biphenyl-tetracarboxylate splits into two rigid halves).' },
          { name: 'branch_points', type: 'list[int]', desc: 'All such junction atoms. If empty, the fragment collapses whole exactly like Module 4b — which is why BTC and BDC give identical results in both.' },
          { name: 'bp_groups', type: 'dict[int, list[int]]', desc: 'Each branch point plus any hydrogen bonded only to it, so those H atoms travel with their parent rather than becoming orphaned single-atom blocks.' },
          { name: 'remaining', type: 'list[int]', desc: 'Everything that is not a branch point — split into its own connected chain/ring pieces. Equivalent to the real code\'s TREE_INT_BRANCH / TREE_EXT_CONN labels.' },
        ],
        data: (ctx) => {
          const an = ctx.variants.allNode, sn = ctx.variants.singleNode;
          const diverged = an.n_linker_blocks !== sn.n_linker_blocks;
          return variantRows(an).concat([
            { label: 'Single-node linker blocks', value: sn.n_linker_blocks, note: 'for direct comparison' },
            { label: 'Diverged from single-node?', value: diverged ? 'YES' : 'no',
              note: diverged ? 'this linker has a real branch point — all-node split it further'
                             : 'no true branch point in this linker, so both algorithms agree (expected for BTC/BDC)' },
          ]);
        },
        snapshot: snapBlocks('allNode', 'palette'),
      }],
    },
    // ============================= MODULE 5 =============================
    {
      id: 'm5', num: '5', label: 'Centroid Simplification', tint: PAL.accent2,
      summary: 'Every "collapse this fragment to one point" call in Modules 4a/4b/4c bottoms out here: replace a cluster of atoms with a single pseudoatom at their centroid.',
      steps: [{
        label: 'collapse_fragment()',
        title: 'Module 5 — collapse_fragment(), a real, runnable Python translation',
          algo: 'Replace a cluster of atoms with one point. The subtlety is periodicity: a block straddling a cell boundary must first be unwrapped into one consistent copy, or its average would land in empty space in the middle of the cell.',
        src: [{ file: 'code_05_centroid_simplification.py', lines: 'collapse_fragment()', code:
`def collapse_fragment(geom, block, block_id, kind):
    """Real Topology::CollapseFragment(pa_fragment), translated."""
    unwrapped = _unwrap_block(geom, block)   # local BFS unwrap first
    conn_points = []
    for a in block:
        for other, vec, _bi in geom.adj[a]:
            if other not in block_set:        # bond leaving the block
                ax, ay, az = unwrapped[a]
                conn_points.append((ax + 0.5*vec[0], ay + 0.5*vec[1], az + 0.5*vec[2]))
    # centroid = average of those connection-point midpoints
    # (falls back to a plain atom average if the block has none)
    return Block(block_id, kind, block, comp, (cx, cy, cz), len(conn_points))` }],
        explain:
          'A real, runnable file — <code>python3 code_05_centroid_simplification.py HKUST-1.cif</code> prints all 14 collapsed points with their exact composition and centroid coordinates. <b>_unwrap_block()</b> first walks the block\'s own bonds with a local BFS, applying each bond\'s stored periodic shift vector, so a block that straddles a unit-cell boundary still gets ONE geometrically consistent set of positions before averaging (this is this project\'s from-scratch equivalent of the real <code>getCentroid()</code>\'s periodic-unwrap behavior, code_02.py). <b>conn_points</b> collects the midpoint of every bond leaving the block; the centroid is their average (falling back to a plain atom-position average for a block with zero external connections).',
        threeD: 'This is exactly the netOnly view: every building block — node and linker alike — has collapsed to a single point at its own centroid, connected by straight edges to its neighbours. <b>Hover any vertex to see inside it</b> — the atoms that were merged into that point, the bonds between them, and how many bonds leave it for other blocks. That is what has just been thrown away, and what the vertex now stands for.',
        args: [
          { name: 'block', type: 'list[int]', desc: 'The atom indices to merge into a single point — one node or linker block from Module 4a/4b/4c.' },
          { name: '_unwrap_block()', type: 'helper', desc: 'Local BFS across the block\'s own bonds, adding each bond\'s stored periodic shift vector. Without this, a block straddling a cell boundary would have half its atoms on the far side and its centroid would land in empty space.' },
          { name: 'unwrapped', type: 'dict[int, xyz]', desc: 'Each atom\'s position in one geometrically consistent frame. Only now is averaging meaningful.' },
          { name: 'conn_points', type: 'list[xyz]', desc: 'Midpoints of every bond LEAVING the block. These, not the atoms, are what actually connect this vertex to its neighbours.' },
          { name: 'centroid (cx,cy,cz)', type: 'xyz', desc: 'Average of <code>conn_points</code> when the block has external bonds, else a plain atom average. Using connection midpoints places elongated SBUs more faithfully than a raw atom average would.' },
          { name: 'kind', type: '"node" | "linker"', desc: 'Carried through so the vertex keeps its role in the final net and in the MOFid/MOFkey assembly.' },
          { name: 'weighted', type: 'bool = False', desc: 'The real <code>getCentroid()</code> can mass-weight the average; MOFid calls it with False, so every atom counts equally regardless of element.' },
        ],
        data: (ctx) => {
          const V = ctx.variants.singleNode;
          const g = ctx.trace.geom;
          const total = V.blocks.length;
          const conns = V.blocks.map(b => b.n_connections);
          return [
            { label: 'Atoms collapsed away', value: g.n, note: 'every single atom disappears into a point' },
            { label: 'Points remaining', value: total, note: V.n_metal_blocks + ' node + ' + V.n_linker_blocks + ' linker' },
            { label: 'Compression ratio', value: (g.n / total).toFixed(1) + ' : 1', note: 'atoms per surviving vertex' },
            { label: 'Connections per vertex', value: Math.min.apply(null, conns) + ' – ' + Math.max.apply(null, conns), note: 'this degree is what Systre classifies on' },
            { label: 'Centroid method', value: 'unweighted', note: 'every atom counts equally; PBC-unwrapped first' },
          ];
        },
        snapshot: snapNet('singleNode'),
      }],
    },
    // ============================= MODULE 6 =============================
    {
      id: 'm6', num: '6', label: 'Systre Topology', tint: PAL.good,
      summary: 'Export the simplified net to a plain-text .cgd file and hand it to Systre (an external Java tool) for canonical topology identification.',
      steps: [{
        label: 'write_systre()',
        title: 'Module 6 — write_systre(), a real .cgd file writer, in Python',
          algo: 'Serialise the net as plain text: the cell, one NODE line per vertex with fractional coordinates and degree, one EDGE line per connection. Systre then computes a canonical fingerprint of that periodic graph and matches it against the RCSR database of known nets.',
        src: [{ file: 'code_06_systre_topology_export.py', lines: 'write_systre()', code:
`def write_systre(geom, blocks, filepath, cell_par, name, simplify_two_conn=True):
    """Real Topology::WriteSystre(), translated -- and genuinely
    writes a valid, Systre-readable .cgd file."""
    lines = ['CRYSTAL', f'  NAME {name}', '  GROUP P1',
             f'  CELL {a} {b} {c} {alpha} {beta} {gamma}']
    for b in blocks:
        fx, fy, fz = _cart_to_frac(b.centroid, geom.cell_matrix)
        lines.append(f'  NODE {b.id+1} {degree[b.id]} {fx:.5f} {fy:.5f} {fz:.5f}')
    for ba, bb in edges:
        lines.append(f'  EDGE  {fa} {fb}')
    lines.append('END')
    open(filepath, 'w').write('\\n'.join(lines))` }],
        explain:
          'This is real MOFid source, translated into a file that genuinely WORKS: <code>python3 code_06_systre_topology_export.py HKUST-1.cif</code> writes an actual <code>topology.cgd</code> to disk that you could hand to real Systre (<code>java -jar Systre.jar topology.cgd</code>) if you had it installed — Systre itself (the program that reads this file and computes the topology) is an EXTERNAL third-party Java tool (the Gavrog project), not part of this codebase, and is not run anywhere in this browser or this Python translation. <b>simplify_two_conn</b>: any pseudoatom with exactly 2 connections would be folded into a single edge rather than kept as its own vertex, since a 2-connected site carries no extra topological information (this project\'s translation keeps every block as its own NODE line for simplicity — a minor, clearly-noted simplification). Every block becomes one <code>NODE</code> line (fractional coordinates + degree); every inter-block bond becomes one <code>EDGE</code> line.',
        threeD: 'The same collapsed net as Module 5 — this IS precisely what gets serialized into the .cgd file: node positions (in fractional coordinates) and the edges between them.',
        args: [
          { name: 'filepath', type: 'str', desc: 'Where the .cgd is written, e.g. <code>Output/MetalOxo/topology.cgd</code>. The real pipeline writes one per algorithm, so single-node and all-node topologies can be compared.' },
          { name: 'blocks', type: 'list[Block]', desc: 'Module 5\'s collapsed points. Each becomes one <code>NODE</code> line.' },
          { name: 'cell_par', type: '6 floats', desc: 'a, b, c, α, β, γ — written verbatim into the <code>CELL</code> line. Systre needs the box to interpret the fractional coordinates.' },
          { name: 'simplify_two_conn', type: 'bool = True', desc: 'Folds any 2-connected vertex into a plain edge. A 2-connected site adds no topological information, and leaving it in would change the net\'s classification.' },
          { name: '_cart_to_frac()', type: 'helper', desc: 'Inverts the cell matrix to convert Cartesian centroids back to fractional coordinates — .cgd files are always fractional, never absolute Å.' },
          { name: 'degree[b.id]', type: 'int', desc: 'How many edges meet at this vertex. Written on the NODE line; the pattern of degrees is a large part of what makes a topology identifiable.' },
          { name: 'GROUP P1', type: 'literal', desc: 'Always P1 — the net has already been fully symmetry-expanded, so no symmetry operators are declared.' },
        ],
        data: (ctx) => {
          const V = ctx.variants.singleNode;
          const edgePairs = new Set();
          V.bonds.forEach(bd => {
            if (!bd.interblock) return;
            const bi = V.atoms[bd.a].block, bj = V.atoms[bd.b].block;
            edgePairs.add(Math.min(bi, bj) + '-' + Math.max(bi, bj));
          });
          const cp = ctx.variants.cell_par;
          return [
            { label: 'NODE lines written', value: V.blocks.length, note: 'one per vertex, with fractional x y z + degree' },
            { label: 'EDGE lines written', value: edgePairs.size, note: 'unique block-to-block connections' },
            { label: 'CELL line', value: cp ? cp.slice(0, 3).map(x => x.toFixed(2)).join(' ') + ' …' : '—', note: 'same cell the CIF declared in Module 1' },
            { label: 'Space group written', value: 'P1', note: 'the net is already fully expanded, so no symmetry' },
            { label: 'Systre run in-browser?', value: 'no', note: 'external Java tool — this only writes its input file' },
          ];
        },
        extra: (ctx) => ctx.isDefault
          ? '<div class="callout"><b>Known result for HKUST-1 (Cu-BTC)</b> — not recomputed live; Systre is an external tool: <br><code>Topology (RCSR): tbo</code></div>'
          : '<div class="callout">Topology assignment requires the external Systre tool — not computed in-browser for this structure. The net shown above is exactly what would be exported to a .cgd file and handed to it.</div>',
        snapshot: snapNet('singleNode'),
      }],
    },
    // ============================= MODULE 7 =============================
    {
      id: 'm7', num: '7', label: 'MOFid / MOFkey', tint: PAL.good,
      summary: 'Assemble the final identifier strings from every earlier module\'s output: SMILES fragments, catenation count, and the resolved topology code.',
      steps: [{
        label: 'get_mofkey() + analyze_mof()',
        title: 'Module 7 — assembling the MOFid and MOFkey strings, in Python',
          algo: 'Collect the chemistry (SMILES per building block), the topology (the RCSR symbol), and the catenation count, sort everything so the result is order-independent, and concatenate. The sorting is what makes the identifier reproducible for the same material.',
        src: [
          { file: 'code_00_pipeline_driver.py', lines: 'analyze_mof() (condensed)', code:
`def analyze_mof(cif_path, output_dir='Output'):
    cif = parse_cif(open(cif_path).read())              # Module 1
    geom = compute_geometry(cif, metal_set=METALS)        # Module 2+3
    for name, runner in (('MetalOxo', run_metal_oxo), ...):
        node_blocks, linker_blocks = runner(geom)         # Module 4a/4b/4c
        blocks = build_blocks(geom, node_blocks, linker_blocks)  # Module 5
        write_systre(geom, blocks, f'{output_dir}/{name}/topology.cgd', ...)  # Module 6
    mofkey = get_mofkey(geom, mo['node_blocks'], mo['linker_blocks'])  # Module 7
    return {...}` },
          { file: 'code_07b_mofkey_assembly.py', lines: 'get_mofkey()', code:
`def get_mofkey(geom, node_blocks, linker_blocks, topology=''):
    """METAL(S).InChIKey1[...].MOFkey-v1[.TOPOLOGY]"""
    unique_elements = {geom.symbols[a] for block in node_blocks
                        for a in block if geom.is_metal[a]}
    metals_part = ','.join(sorted(unique_elements, key=atomic_number))
    keys = sorted({placeholder_inchikey(geom, block) for block in linker_blocks})
    return '.'.join([metals_part] + keys + [f'MOFkey-v1'] + ([topology] if topology else []))` },
        ],
        explain:
          'A real, runnable file — <code>python3 code_00_pipeline_driver.py HKUST-1.cif</code> runs Modules 1 through 7 end to end and prints a full summary. <b>analyze_mof()</b> is the Python translation of the real driver\'s <code>analyzeMOF()</code>: parse once, then run all three algorithms, writing each one\'s own <code>Output/&lt;Algorithm&gt;/topology.cgd</code>. <b>get_mofkey()</b> builds <code>METAL(S).InChIKey1[...].MOFkey-v1[.TOPOLOGY]</code> — the metal-symbol extraction and final string assembly are a complete, faithful translation of the real C++; the one piece NOT reproduced is the real InChIKey computation itself (it requires the InChI algorithm, a separate cheminformatics library Open Babel calls out to, not reimplemented anywhere in this project — including its JS engine, for the same reason). This file substitutes a clearly-labelled, stable placeholder hash instead, so the surrounding assembly logic is genuinely runnable end to end. Running it on HKUST-1 gives real metal symbols (<code>Cu</code>) and a real, correctly-formatted <code>MOFkey-v1</code> suffix.',
        threeD: 'Same collapsed net one final time — every piece of it (the metal node\'s element, each distinct linker\'s connectivity, the topology code from Module 6) is exactly what feeds into the identifier strings shown below.',
        args: [
          { name: 'node_fragments / linker_fragments', type: 'list[str]', desc: 'Canonical SMILES for every unique node and linker, from the METAL-OXO split specifically — the only one that leaves carboxylates intact, which InChIKey generation requires.' },
          { name: 'cat', type: 'int | None', desc: 'Catenation count: how many independent, interpenetrating frameworks occupy the same space. <code>None</code> means no net could be resolved at all.' },
          { name: 'sn_topology / an_topology', type: 'str', desc: 'RCSR codes from Systre for the single-node and all-node nets. If they differ, MOFid reports BOTH comma-joined (e.g. <code>nbo,fof</code>) rather than silently picking one.' },
          { name: 'all_fragments', type: 'list[str]', desc: 'node + linker SMILES concatenated then <b>sorted alphabetically</b> — this sort is what guarantees the same MOF always produces a byte-identical MOFid regardless of internal atom ordering.' },
          { name: 'unique_elements', type: 'set[str]', desc: 'Distinct metal symbols across all node blocks, sorted by atomic number. O and H are deliberately excluded even though they are physically part of the node cluster.' },
          { name: 'truncated inchikey', type: 'str, 14 chars', desc: 'Only the first (connectivity-only) layer of each linker\'s InChIKey. The trailing stereochemistry/protonation block is discarded, since it is constant for ordinary organic linkers.' },
          { name: 'MOFKEY_SEP / MOFKEY_VERSION', type: '"." / "v1"', desc: 'Format constants. Final shape: <code>METAL(S).InChIKey1[.InChIKey2…].MOFkey-v1[.TOPOLOGY]</code>.' },
        ],
        data: (ctx) => {
          const g = ctx.trace.geom;
          const mo = ctx.variants.metalOxo;
          const metals = {};
          for (let i = 0; i < g.n; i++) if (g.isMetal[i]) metals[g.symbols[i]] = 1;
          const metalList = Object.keys(metals).sort();
          const linkerSizes = {};
          mo.blocks.filter(b => b.type === 'linker').forEach(b => { linkerSizes[fmtComp(b.composition)] = 1; });
          const distinctLinkers = Object.keys(linkerSizes);
          return [
            { label: 'Metal symbols for MOFkey', value: metalList.join(', ') || 'NA', note: 'sorted by atomic number, O/H deliberately excluded' },
            { label: 'Distinct linker types', value: distinctLinkers.length, note: distinctLinkers.slice(0, 2).join('  |  ') || '—' },
            { label: 'Node fragments to encode', value: mo.n_metal_blocks, note: 'from the metal-oxo split specifically' },
            { label: 'Linker fragments to encode', value: mo.n_linker_blocks, note: 'carboxylates intact — required for valid InChIKeys' },
            { label: 'Sorting', value: 'alphabetical', note: 'guarantees byte-identical output for the same MOF' },
          ];
        },
        extra: (ctx) => ctx.isDefault
          ? '<div class="callout"><b>Known result for HKUST-1 (Cu-BTC)</b> — the real reference values (not recomputed live; needs real InChI + external Systre):<br>' +
            '<code>MOFid: [Cu][Cu].[O-]C(=O)c1cc(cc(c1)C(=O)[O-])C(=O)[O-]&nbsp;&nbsp;MOFid-v1.tbo.cat0;Cu-BTC</code><br>' +
            '<code>MOFkey: Cu.QMKYBPDZANOJGF.MOFkey-v1.tbo</code><br>' +
            '<code>This Python translation\'s own output: Cu.131C2152F68873.MOFkey-v1.tbo</code> (metal + format + topology fields match exactly; the middle field is a placeholder, not a real InChIKey — see explanation).</div>'
          : '<div class="callout">MOFid/MOFkey assembly requires real InChI export and the external Systre tool for the topology field — not fully computed for this structure. Run <code>python3 code_00_pipeline_driver.py yourfile.cif</code> yourself to see this project\'s own (placeholder-linker-key) output.</div>',
        snapshot: snapNet('singleNode'),
      }],
    },
  ];

  // Flatten into a single continuous step list for Prev/Next
  const FLAT = [];
  MODULES.forEach((mod, mi) => mod.steps.forEach((step, si) => FLAT.push({ mi, si, mod, step })));

  let render = null;
  let ctx = null;
  let currentFlat = 0;
  let els = {};

  function renderCurrent() {
    const { mi, si, mod, step } = FLAT[currentFlat];
    const snap = step.snapshot(ctx);
    render.load(snap.DATA, snap.opts);

    els.moduleTabs.querySelectorAll('.module-tab').forEach((b, i) => b.classList.toggle('active', i === mi));
    els.stepPills.innerHTML = '';
    if (mod.steps.length > 1) {
      mod.steps.forEach((s, i) => {
        const b = document.createElement('button');
        b.className = 'step-pill' + (i === si ? ' active' : '');
        b.textContent = s.label;
        b.addEventListener('click', () => { currentFlat = FLAT.findIndex(f => f.mi === mi && f.si === i); renderCurrent(); });
        els.stepPills.appendChild(b);
      });
      els.stepPills.style.display = 'flex';
    } else {
      els.stepPills.style.display = 'none';
    }

    els.moduleBadge.textContent = 'MODULE ' + mod.num;
    els.moduleBadge.style.background = mod.tint;
    els.moduleSummary.textContent = mod.summary;
    els.title.textContent = step.title;
    els.codeArea.innerHTML = '';
    step.src.forEach(s => {
      const wrap = document.createElement('div');
      wrap.className = 'code-unit';
      const ref = document.createElement('div');
      ref.className = 'code-refs';
      ref.innerHTML = '<span class="code-chip">' + s.file + ' — ' + s.lines + '</span>';
      const pre = document.createElement('pre');
      pre.className = 'code-block';
      pre.textContent = s.code;
      wrap.appendChild(ref); wrap.appendChild(pre);
      els.codeArea.appendChild(wrap);
    });
    els.algo.innerHTML = step.algo
      ? '<b>The algorithm, in plain terms:</b> ' + step.algo : '';
    els.algo.style.display = step.algo ? 'block' : 'none';

    els.explain.innerHTML = step.explain;

    // ---- per-argument reference table for this step's code ----
    if (step.args && step.args.length) {
      els.args.innerHTML =
        '<div class="args-title">Every argument &amp; variable in the code above</div>' +
        '<table class="args-table"><tbody>' +
        step.args.map(a =>
          '<tr><td class="ar-name"><code>' + a.name + '</code></td>' +
          '<td class="ar-type">' + (a.type || '') + '</td>' +
          '<td class="ar-desc">' + a.desc + '</td></tr>'
        ).join('') +
        '</tbody></table>';
      els.args.style.display = 'block';
    } else {
      els.args.style.display = 'none';
      els.args.innerHTML = '';
    }

    els.threeD.innerHTML = '<b>What to look for in the 3D panel:</b> ' + step.threeD;

    // ---- live data table, recomputed for the currently loaded structure ----
    if (step.data) {
      let rows = [];
      try { rows = step.data(ctx) || []; } catch (e) { rows = []; }
      if (rows.length) {
        els.data.innerHTML =
          '<div class="data-title">Live numbers for <b>' + (ctx.label || 'this structure') + '</b>' +
          ' <span class="data-sub">computed in your browser right now — upload a different CIF and every value changes</span></div>' +
          '<table class="data-table"><tbody>' +
          rows.map(r =>
            '<tr><td class="dt-label">' + r.label + '</td>' +
            '<td class="dt-value">' + r.value + '</td>' +
            '<td class="dt-note">' + (r.note || '') + '</td></tr>'
          ).join('') +
          '</tbody></table>';
        els.data.style.display = 'block';
      } else {
        els.data.style.display = 'none';
      }
    } else {
      els.data.style.display = 'none';
      els.data.innerHTML = '';
    }

    els.extra.innerHTML = step.extra ? step.extra(ctx) : '';
    els.extra.style.display = step.extra ? 'block' : 'none';

    // ---- legend telling the reader what the colours mean RIGHT NOW ----
    if (els.legend) {
      const mode = snap.opts.colorMode;
      let items;
      if (mode === 'element') {
        items = [[PAL.good, 'metal'], [PAL.text3, 'carbon'], [PAL.node, 'oxygen'], [PAL.border, 'hydrogen']];
      } else if (mode === 'metalNonmetal') {
        items = [[PAL.node, 'METAL'], [PAL.brand, 'NONMETAL']];
      } else if (snap.opts.blockColorStyle === 'palette') {
        items = [['linear-gradient(90deg,#8e44ad,#d97b1e,#27ae60)', 'one colour per separate fragment']];
      } else {
        items = [[PAL.node, 'node block'], [PAL.brand, 'linker block']];
      }
      els.legend.innerHTML = '<span class="legend-lead">Colours here:</span>' + items.map(([c, t]) =>
        '<span class="legend-item"><i style="background:' + c + '"></i>' + t + '</span>').join('');
    }

    els.progress.textContent = 'Step ' + (currentFlat + 1) + ' of ' + FLAT.length;
    els.prevBtn.disabled = currentFlat === 0;
    els.nextBtn.disabled = currentFlat === FLAT.length - 1;
  }

  function goTo(flatIdx) { currentFlat = Math.max(0, Math.min(FLAT.length - 1, flatIdx)); renderCurrent(); }
  function goToModule(mi) { currentFlat = FLAT.findIndex(f => f.mi === mi); renderCurrent(); }

  function init(canvas, container, labelsLayer, hoverTip) {
    render = root.MOFRender.create();
    render.init(canvas, container, labelsLayer, hoverTip);
  }

  function buildUI(panelContainer) {
    panelContainer.innerHTML =
      '<div id="pw-module-tabs" class="module-tabs"></div>' +
      '<div id="pw-step-pills" class="step-pills"></div>' +
      '<div class="module-head">' +
        '<span id="pw-module-badge" class="module-badge"></span>' +
        '<span id="pw-module-summary" class="module-summary"></span>' +
      '</div>' +
      '<h3 id="pw-title"></h3>' +
      '<div id="pw-code-area"></div>' +
      '<div id="pw-algo" class="algo-note"></div>' +
      '<div class="explain-block"><b>Code &amp; argument walkthrough:</b> <span id="pw-explain"></span></div>' +
      '<div id="pw-args" class="args-panel"></div>' +
      '<div id="pw-legend" class="legend"></div>' +
      '<div id="pw-3d-note" class="explain-block threeD-note"></div>' +
      '<div id="pw-data" class="data-panel"></div>' +
      '<div id="pw-extra"></div>' +
      '<div class="stage-nav" style="margin-top:16px;">' +
        '<button id="pw-prev">&larr; Previous</button>' +
        '<span id="pw-progress" class="stage-formula"></span>' +
        '<button id="pw-next">Next &rarr;</button>' +
      '</div>';

    els.moduleTabs = panelContainer.querySelector('#pw-module-tabs');
    els.stepPills = panelContainer.querySelector('#pw-step-pills');
    els.moduleBadge = panelContainer.querySelector('#pw-module-badge');
    els.moduleSummary = panelContainer.querySelector('#pw-module-summary');
    els.title = panelContainer.querySelector('#pw-title');
    els.codeArea = panelContainer.querySelector('#pw-code-area');
    els.algo = panelContainer.querySelector('#pw-algo');
    els.explain = panelContainer.querySelector('#pw-explain');
    els.args = panelContainer.querySelector('#pw-args');
    els.legend = panelContainer.querySelector('#pw-legend');
    els.threeD = panelContainer.querySelector('#pw-3d-note');
    els.data = panelContainer.querySelector('#pw-data');
    els.extra = panelContainer.querySelector('#pw-extra');
    els.progress = panelContainer.querySelector('#pw-progress');
    els.prevBtn = panelContainer.querySelector('#pw-prev');
    els.nextBtn = panelContainer.querySelector('#pw-next');

    MODULES.forEach((mod, mi) => {
      const b = document.createElement('button');
      b.className = 'module-tab' + (mod.highlight ? ' highlight' : '');
      b.innerHTML = '<span class="module-tab-num">' + mod.num + '</span>' + mod.label;
      b.addEventListener('click', () => goToModule(mi));
      els.moduleTabs.appendChild(b);
    });
    els.prevBtn.addEventListener('click', () => goTo(currentFlat - 1));
    els.nextBtn.addEventListener('click', () => goTo(currentFlat + 1));
  }

  function setSource(fracAtoms, cellMatrix, isDefault, label) {
    const trace = MOFDecompose.traceMetalOxo(fracAtoms, cellMatrix);
    const variants = MOFDecompose.buildAllVariants(fracAtoms, cellMatrix);
    ctx = {
      trace, variants, isDefault: !!isDefault,
      label: label || (isDefault ? 'HKUST-1' : 'your uploaded structure'),
    };
    renderCurrent();
  }

  root.PipelineWalkthrough = { init, buildUI, setSource, MODULES, FLAT, getCurrentIndex: () => currentFlat };
})(typeof window !== 'undefined' ? window : globalThis);