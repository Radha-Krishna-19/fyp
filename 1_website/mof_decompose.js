// mof_decompose.js
// Portable (no-DOM) JS decomposition engine. Parses a CIF, infers a PBC-aware
// bond graph, and partitions it into node/linker building blocks under THREE
// different real MOFid decomposition rules (metal-oxo / single-node /
// all-node — see code_04a/04b/04c.py for the published algorithms these
// mirror), plus the proposed fixes in buildMetalOxoVariant().
//
// Exposed API (window.MOFDecompose / module.exports):
//   parseCIF(text)                        -> {cellMatrix, cellPar, atoms:[{el,fx,fy,fz}]}
//   buildStructure(atoms, cellMatrix)      -> legacy single-variant DATA (unchanged behavior)
//   buildAllVariants(atoms, cellMatrix)    -> {formula, n_atoms, cell_matrix, cell_par,
//                                              metalOxo: DATA, singleNode: DATA, allNode: DATA}
//   COVALENT_RADII, METALS
//
// Each "DATA" object (whether from buildStructure or one of the three variants
// inside buildAllVariants) has the same shape:
//   {formula, n_atoms, cell_matrix, cell_par, atoms:[{id,el,pos,block}],
//    bonds:[{a,b,vec,cross,interblock}],
//    blocks:[{id,type,atoms,n_atoms,composition,centroid,n_connections}],
//    n_metal_blocks, n_linker_blocks}

(function (root) {
  'use strict';

  // ---------------------------------------------------------------
  // Covalent radii (Angstrom), Cordero et al. 2008 values.
  // ---------------------------------------------------------------
  const COVALENT_RADII = {
    H: 0.31, He: 0.28, Li: 1.28, Be: 0.96, B: 0.84, C: 0.76, N: 0.71, O: 0.66,
    F: 0.57, Ne: 0.58, Na: 1.66, Mg: 1.41, Al: 1.21, Si: 1.11, P: 1.07, S: 1.05,
    Cl: 1.02, Ar: 1.06, K: 2.03, Ca: 1.76, Sc: 1.70, Ti: 1.60, V: 1.53, Cr: 1.39,
    Mn: 1.39, Fe: 1.32, Co: 1.26, Ni: 1.24, Cu: 1.32, Zn: 1.22, Ga: 1.22, Ge: 1.20,
    As: 1.19, Se: 1.20, Br: 1.20, Kr: 1.16, Rb: 2.20, Sr: 1.95, Y: 1.90, Zr: 1.75,
    Nb: 1.64, Mo: 1.54, Tc: 1.47, Ru: 1.46, Rh: 1.42, Pd: 1.39, Ag: 1.45, Cd: 1.44,
    In: 1.42, Sn: 1.39, Sb: 1.39, Te: 1.38, I: 1.39, Xe: 1.40, Cs: 2.44, Ba: 2.15,
    La: 2.07, Ce: 2.04, Pr: 2.03, Nd: 2.01, Sm: 1.98, Eu: 1.98, Gd: 1.96, Tb: 1.94,
    Dy: 1.92, Ho: 1.92, Er: 1.89, Tm: 1.90, Yb: 1.87, Lu: 1.87, Hf: 1.75, Ta: 1.70,
    W: 1.62, Re: 1.51, Os: 1.44, Ir: 1.41, Pt: 1.36, Au: 1.36, Hg: 1.32, Tl: 1.45,
    Pb: 1.46, Bi: 1.48,
  };

  const METALS = new Set([
    'Li', 'Na', 'K', 'Rb', 'Cs', 'Mg', 'Ca', 'Sr', 'Ba', 'Sc', 'Y', 'Ti', 'Zr',
    'Hf', 'V', 'Nb', 'Ta', 'Cr', 'Mo', 'W', 'Mn', 'Fe', 'Ru', 'Os', 'Co', 'Rh',
    'Ir', 'Ni', 'Pd', 'Pt', 'Cu', 'Ag', 'Au', 'Zn', 'Cd', 'Hg', 'Al', 'Ga', 'In',
    'Tl', 'Sn', 'Pb', 'Bi', 'La', 'Ce', 'Pr', 'Nd', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy',
    'Ho', 'Er', 'Tm', 'Yb', 'Lu',
  ]);

  const ELEMENT_SYMBOLS = Object.keys(COVALENT_RADII).sort((a, b) => b.length - a.length);

  function elementFromLabel(label) {
    const clean = label.replace(/[^A-Za-z]/g, '');
    for (const el of ELEMENT_SYMBOLS) {
      if (clean.slice(0, el.length).toLowerCase() === el.toLowerCase()) {
        return el.length === 1 ? el.toUpperCase() : el[0].toUpperCase() + el.slice(1).toLowerCase();
      }
    }
    return clean.slice(0, 1).toUpperCase() || 'X';
  }

  // ---------------------------------------------------------------
  // CIF parsing (unchanged from the original engine)
  // ---------------------------------------------------------------
  function tokenizeLine(line) {
    const tokens = [];
    let i = 0;
    while (i < line.length) {
      while (i < line.length && /\s/.test(line[i])) i++;
      if (i >= line.length) break;
      if (line[i] === "'" || line[i] === '"') {
        const q = line[i];
        let j = i + 1;
        while (j < line.length && line[j] !== q) j++;
        tokens.push(line.slice(i + 1, j));
        i = j + 1;
      } else {
        let j = i;
        while (j < line.length && !/\s/.test(line[j])) j++;
        tokens.push(line.slice(i, j));
        i = j;
      }
    }
    return tokens;
  }

  function parseNumber(tok) {
    const m = String(tok).match(/^-?\d*\.?\d+/);
    return m ? parseFloat(m[0]) : NaN;
  }

  function evalSymComponent(expr, x, y, z) {
    expr = expr.replace(/\s+/g, '');
    let value = 0;
    let idx = 0;
    while (idx < expr.length) {
      const rest = expr.slice(idx);
      const m = rest.match(/^([+-]?)((?:\d+\/\d+)|(?:\d*\.\d+)|(?:\d+))?(\*)?([xyzXYZ])?/);
      if (!m || (m[0] === '')) { idx++; continue; }
      const sign = m[1] === '-' ? -1 : 1;
      let coef = 1;
      if (m[2]) {
        if (m[2].indexOf('/') >= 0) {
          const parts = m[2].split('/');
          coef = parseFloat(parts[0]) / parseFloat(parts[1]);
        } else {
          coef = parseFloat(m[2]);
        }
      }
      const varName = m[4] ? m[4].toLowerCase() : null;
      if (varName === 'x') value += sign * coef * x;
      else if (varName === 'y') value += sign * coef * y;
      else if (varName === 'z') value += sign * coef * z;
      else if (m[2]) value += sign * coef;
      idx += m[0].length;
      if (m[0].length === 0) break;
    }
    return value;
  }

  function parseSymOp(opStr) {
    const parts = opStr.split(',').map(s => s.trim());
    if (parts.length !== 3) return null;
    return function (x, y, z) {
      return [
        evalSymComponent(parts[0], x, y, z),
        evalSymComponent(parts[1], x, y, z),
        evalSymComponent(parts[2], x, y, z),
      ];
    };
  }

  function cellParToMatrix(a, b, c, alphaDeg, betaDeg, gammaDeg) {
    const alpha = alphaDeg * Math.PI / 180, beta = betaDeg * Math.PI / 180, gamma = gammaDeg * Math.PI / 180;
    const ax = a, ay = 0, az = 0;
    const bx = b * Math.cos(gamma), by = b * Math.sin(gamma), bz = 0;
    const cx = c * Math.cos(beta);
    const cy = (c * (Math.cos(alpha) - Math.cos(beta) * Math.cos(gamma))) / Math.sin(gamma);
    const cz2 = c * c - cx * cx - cy * cy;
    const cz = Math.sqrt(Math.max(cz2, 0));
    return [[ax, ay, az], [bx, by, bz], [cx, cy, cz]];
  }

  function fracToCart(f, M) {
    return [
      f[0] * M[0][0] + f[1] * M[1][0] + f[2] * M[2][0],
      f[0] * M[0][1] + f[1] * M[1][1] + f[2] * M[2][1],
      f[0] * M[0][2] + f[1] * M[1][2] + f[2] * M[2][2],
    ];
  }

  function parseCIF(text) {
    const lines = text.split(/\r?\n/);
    let a, b, c, alpha, beta, gamma;
    const symOps = [];
    let i = 0;

    for (i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (/^_cell_length_a/i.test(line)) a = parseNumber(line.split(/\s+/)[1]);
      else if (/^_cell_length_b/i.test(line)) b = parseNumber(line.split(/\s+/)[1]);
      else if (/^_cell_length_c/i.test(line)) c = parseNumber(line.split(/\s+/)[1]);
      else if (/^_cell_angle_alpha/i.test(line)) alpha = parseNumber(line.split(/\s+/)[1]);
      else if (/^_cell_angle_beta/i.test(line)) beta = parseNumber(line.split(/\s+/)[1]);
      else if (/^_cell_angle_gamma/i.test(line)) gamma = parseNumber(line.split(/\s+/)[1]);
    }
    if ([a, b, c, alpha, beta, gamma].some(v => v === undefined || isNaN(v))) {
      throw new Error('Could not find cell parameters in CIF.');
    }
    const cellMatrix = cellParToMatrix(a, b, c, alpha, beta, gamma);

    let atomHeaders = null;
    let atomRows = [];

    i = 0;
    while (i < lines.length) {
      const line = lines[i].trim();
      if (/^loop_/i.test(line)) {
        let j = i + 1;
        const headers = [];
        while (j < lines.length && /^_/.test(lines[j].trim())) {
          headers.push(lines[j].trim().toLowerCase());
          j++;
        }
        const isSym = headers.some(h => /_symmetry_equiv_pos_as_xyz|_space_group_symop_operation_xyz/.test(h));
        const isAtomSite = headers.some(h => /_atom_site_fract_x/.test(h));

        if (isSym) {
          while (j < lines.length) {
            const t = lines[j].trim();
            if (t === '' || /^loop_/i.test(t) || /^_/.test(t) || /^data_/i.test(t)) break;
            const toks = tokenizeLine(t);
            const candidate = toks[toks.length - 1];
            if (candidate && candidate.indexOf(',') >= 0) {
              const op = parseSymOp(candidate);
              if (op) symOps.push(op);
            }
            j++;
          }
        } else if (isAtomSite) {
          atomHeaders = headers;
          while (j < lines.length) {
            const t = lines[j].trim();
            if (t === '' || /^loop_/i.test(t) || (/^_/.test(t)) || /^data_/i.test(t)) break;
            atomRows.push(tokenizeLine(t));
            j++;
          }
        }
        i = j;
        continue;
      }
      i++;
    }

    if (!atomHeaders || atomRows.length === 0) {
      throw new Error('Could not find an _atom_site loop with fractional coordinates in CIF.');
    }

    const idx = {};
    atomHeaders.forEach((h, k) => { idx[h] = k; });
    const iLabel = idx['_atom_site_label'];
    const iType = idx['_atom_site_type_symbol'];
    const iX = idx['_atom_site_fract_x'];
    const iY = idx['_atom_site_fract_y'];
    const iZ = idx['_atom_site_fract_z'];

    const asymAtoms = [];
    for (const row of atomRows) {
      if (row.length <= Math.max(iX, iY, iZ)) continue;
      const fx = parseNumber(row[iX]), fy = parseNumber(row[iY]), fz = parseNumber(row[iZ]);
      if ([fx, fy, fz].some(v => isNaN(v))) continue;
      let el;
      if (iType !== undefined && row[iType]) el = elementFromLabel(row[iType]);
      else if (iLabel !== undefined && row[iLabel]) el = elementFromLabel(row[iLabel]);
      else continue;
      asymAtoms.push({ el, fx, fy, fz });
    }

    const ops = symOps.length > 0 ? symOps : [(x, y, z) => [x, y, z]];
    const expanded = [];
    const seen = [];
    const TOL = 0.01;
    function wrap(v) { v = v % 1; if (v < 0) v += 1; if (v > 1 - 1e-6) v -= 1; return v; }

    for (const atom of asymAtoms) {
      for (const op of ops) {
        const [x, y, z] = op(atom.fx, atom.fy, atom.fz);
        const wx = wrap(x), wy = wrap(y), wz = wrap(z);
        let dup = false;
        for (const s of seen) {
          if (s.el !== atom.el) continue;
          let dx = Math.abs(s.fx - wx); dx = Math.min(dx, 1 - dx);
          let dy = Math.abs(s.fy - wy); dy = Math.min(dy, 1 - dy);
          let dz = Math.abs(s.fz - wz); dz = Math.min(dz, 1 - dz);
          if (dx < TOL && dy < TOL && dz < TOL) { dup = true; break; }
        }
        if (!dup) {
          seen.push({ el: atom.el, fx: wx, fy: wy, fz: wz });
          expanded.push({ el: atom.el, fx: wx, fy: wy, fz: wz });
        }
      }
    }

    return { cellMatrix, cellPar: [a, b, c, alpha, beta, gamma], atoms: expanded };
  }

  // ---------------------------------------------------------------
  // Shared geometry: parse positions + infer the PBC-aware bond graph ONCE.
  // Every variant (metal-oxo / single-node / all-node) partitions this same
  // graph differently -- see code_02/code_03.py for the real analogs.
  // ---------------------------------------------------------------
  function computeGeometry(fracAtoms, cellMatrix) {
    const n = fracAtoms.length;
    const pos = fracAtoms.map(a => fracToCart([a.fx, a.fy, a.fz], cellMatrix));
    const symbols = fracAtoms.map(a => a.el);
    const radii = symbols.map(el => COVALENT_RADII[el] !== undefined ? COVALENT_RADII[el] : 0.75);
    const isMetal = symbols.map(el => METALS.has(el));

    const offsets = [];
    for (let oa = -1; oa <= 1; oa++)
      for (let ob = -1; ob <= 1; ob++)
        for (let oc = -1; oc <= 1; oc++)
          offsets.push([oa, ob, oc]);
    function latticeVec(oa, ob, oc) {
      return [
        oa * cellMatrix[0][0] + ob * cellMatrix[1][0] + oc * cellMatrix[2][0],
        oa * cellMatrix[0][1] + ob * cellMatrix[1][1] + oc * cellMatrix[2][1],
        oa * cellMatrix[0][2] + ob * cellMatrix[1][2] + oc * cellMatrix[2][2],
      ];
    }
    const offsetVecs = offsets.map(([oa, ob, oc]) => latticeVec(oa, ob, oc));

    const bonds = [];
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const cutoff = (radii[i] + radii[j]) * ((isMetal[i] || isMetal[j]) ? 1.30 : 1.15);
        let best = null, bestD = Infinity;
        for (const ov of offsetVecs) {
          const dx = pos[j][0] + ov[0] - pos[i][0];
          const dy = pos[j][1] + ov[1] - pos[i][1];
          const dz = pos[j][2] + ov[2] - pos[i][2];
          const d = Math.sqrt(dx * dx + dy * dy + dz * dz);
          if (d < bestD) { bestD = d; best = [dx, dy, dz]; }
        }
        if (bestD > 0.4 && bestD < cutoff) {
          bonds.push({ lo: i, hi: j, vec: best });
        }
      }
    }

    const adj = Array.from({ length: n }, () => []);
    bonds.forEach((bd, bi) => {
      adj[bd.lo].push({ other: bd.hi, vec: bd.vec, bondIdx: bi });
      adj[bd.hi].push({ other: bd.lo, vec: [-bd.vec[0], -bd.vec[1], -bd.vec[2]], bondIdx: bi });
    });

    const formula = (() => {
      const comp = {};
      symbols.forEach(s => { comp[s] = (comp[s] || 0) + 1; });
      return Object.entries(comp).map(([el, c]) => el + c).join('');
    })();

    return { n, pos, symbols, radii, isMetal, adj, bonds, formula };
  }

  function connectedComponents(atomSet, adj) {
    const visited = new Set();
    const components = [];
    for (const start of atomSet) {
      if (visited.has(start)) continue;
      const comp = [];
      const stack = [start];
      visited.add(start);
      while (stack.length) {
        const u = stack.pop();
        comp.push(u);
        for (const nb of adj[u]) {
          if (atomSet.has(nb.other) && !visited.has(nb.other)) {
            visited.add(nb.other);
            stack.push(nb.other);
          }
        }
      }
      components.push(comp.sort((a, b) => a - b));
    }
    return components;
  }

  // ---------------------- Module 4a: metal-oxo classifier ----------------------
  // Node = metal atoms + PURE oxo/hydroxo/aqua/peroxo oxygens (bonded to a
  // metal but NOT to any carbon). Carboxylate oxygens ARE bonded to carbon,
  // so they -- and the whole carboxylate group -- are excluded here and stay
  // with the organic linker. Mirrors code_04a.py's real "all_oxygens"
  // fragment rule at the level of individual coordinating atoms.
  function classifyMetalOxo(geom) {
    const { n, symbols, isMetal, adj } = geom;
    const nodeSet = new Set();
    for (let i = 0; i < n; i++) if (isMetal[i]) nodeSet.add(i);
    for (let i = 0; i < n; i++) {
      if (symbols[i] !== 'O') continue;
      let bondedToMetal = false, bondedToCarbon = false;
      for (const nb of adj[i]) {
        if (isMetal[nb.other]) bondedToMetal = true;
        if (symbols[nb.other] === 'C') bondedToCarbon = true;
      }
      if (bondedToMetal && !bondedToCarbon) nodeSet.add(i);
    }
    // hydroxide/aqua hydrogens follow their oxygen
    for (let i = 0; i < n; i++) {
      if (symbols[i] !== 'H') continue;
      for (const nb of adj[i]) if (nodeSet.has(nb.other)) nodeSet.add(i);
    }
    return nodeSet;
  }

  // -------------------- Module 4b: single-node classifier --------------------
  // Node = metal atoms + the ENTIRE coordinated carboxylate group (both
  // oxygens + the carbon) whenever a metal-bound oxygen turns out to belong
  // to a genuine -COO- group; plain metal-oxide/hydroxide oxygens (no
  // attached carbon) also join the node. Mirrors code_04b.py's atom-by-atom
  // oxygen coordination-environment walk (the N-N bridged-ring case from the
  // real algorithm is simplified away here for tractability).
  function classifySingleNode(geom) {
    const { n, symbols, isMetal, adj } = geom;
    const nodeSet = new Set();
    for (let i = 0; i < n; i++) if (isMetal[i]) nodeSet.add(i);

    const candidates = new Set();
    for (let i = 0; i < n; i++) {
      if (!isMetal[i]) continue;
      for (const nb of adj[i]) candidates.add(nb.other);
    }

    for (const nn of candidates) {
      if (symbols[nn] !== 'O') continue;
      let attachedCarbon = -1;
      let metalOxideOrCarboxylate = true;
      const attachedH = [];
      for (const nb of adj[nn]) {
        const m = nb.other;
        if (isMetal[m]) continue;
        if (symbols[m] === 'H') attachedH.push(m);
        else if (symbols[m] === 'C') { if (attachedCarbon === -1) attachedCarbon = m; }
        else metalOxideOrCarboxylate = false;   // bonded to some other nonmetal -> not a clean SBU oxygen
      }
      if (!metalOxideOrCarboxylate) continue;

      if (attachedCarbon === -1) {
        nodeSet.add(nn);
        attachedH.forEach(h => nodeSet.add(h));
      } else {
        let cC = 0, cO = 0, otherO = -1;
        for (const cnb of adj[attachedCarbon]) {
          if (symbols[cnb.other] === 'C') cC++;
          else if (symbols[cnb.other] === 'O') { cO++; if (cnb.other !== nn) otherO = cnb.other; }
        }
        const isCarboxylate = (cC === 1 && cO === 2);
        if (isCarboxylate) {
          nodeSet.add(nn);
          nodeSet.add(attachedCarbon);
          if (otherO !== -1) {
            nodeSet.add(otherO);
            for (const nb of adj[otherO]) if (symbols[nb.other] === 'H') nodeSet.add(nb.other);
          }
          attachedH.forEach(h => nodeSet.add(h));
        }
        // else: e.g. a methoxy oxygen -- leave it and its carbon with the linker
      }
    }
    return nodeSet;
  }

  // -------------------- Module 4c: all-node branch splitting --------------------
  // Starting from single-node's linker fragments, further split any fragment
  // that has an internal branch point (a heavy atom with degree >= 3 counted
  // only within that fragment) into: one singleton sub-block per branch point,
  // plus one sub-block per remaining chain/ring piece between branch points.
  // This is a simplified structural analog of AllNodeDeconstructor's real
  // ring-aware tree decomposition (code_04c.py) -- it captures the same
  // core idea (rigid branch points become their own vertices) without
  // reproducing every ring-fusion edge case of the original C++.
  function splitAllNodeBranches(linkerComponents, geom) {
    const { symbols, adj } = geom;
    const refined = [];
    for (const comp of linkerComponents) {
      if (comp.length <= 2) { refined.push(comp); continue; }
      const compSet = new Set(comp);
      const branchPoints = [];
      for (const a of comp) {
        if (symbols[a] === 'H') continue;
        // Count only HEAVY-atom neighbours within this fragment -- a ring
        // carbon that simply carries an explicit hydrogen is NOT a branch
        // point; only a genuine 3-heavy-neighbour junction (e.g. the two
        // ring carbons joining the phenyl rings of a biphenyl linker) is.
        let deg = 0;
        for (const nb of adj[a]) {
          if (compSet.has(nb.other) && symbols[nb.other] !== 'H') deg++;
        }
        if (deg >= 3) branchPoints.push(a);
      }
      if (branchPoints.length === 0) { refined.push(comp); continue; }

      const bpSet = new Set(branchPoints);
      // Any hydrogen bonded ONLY to a branch-point atom travels with that
      // branch point's own sub-block (rather than becoming an orphaned,
      // disconnected 1-atom fragment of its own).
      const bpGroups = new Map(branchPoints.map(bp => [bp, [bp]]));
      const remaining = [];
      for (const a of comp) {
        if (bpSet.has(a)) continue;
        if (symbols[a] === 'H') {
          const heavyNbors = adj[a].filter(nb => compSet.has(nb.other));
          if (heavyNbors.length === 1 && bpSet.has(heavyNbors[0].other)) {
            bpGroups.get(heavyNbors[0].other).push(a);
            continue;
          }
        }
        remaining.push(a);
      }
      const remSet = new Set(remaining);
      const visited = new Set();
      for (const start of remaining) {
        if (visited.has(start)) continue;
        const piece = [];
        const stack = [start];
        visited.add(start);
        while (stack.length) {
          const u = stack.pop();
          piece.push(u);
          for (const nb of adj[u]) {
            if (remSet.has(nb.other) && !visited.has(nb.other)) { visited.add(nb.other); stack.push(nb.other); }
          }
        }
        refined.push(piece.sort((x, y) => x - y));
      }
      bpGroups.forEach(group => refined.push(group.sort((x, y) => x - y)));
    }
    return refined;
  }

  // ---------------------------------------------------------------
  // Turn a node/linker atom partition into the full DATA object the 3D
  // viewer consumes: local per-block unwrapping, connection points,
  // centroids, and JSON-friendly atoms/bonds/blocks arrays.
  // ---------------------------------------------------------------
  // opts.noUnwrap: skip the per-block local unwrapping and draw every atom at
  // its raw home-unit-cell position. Needed for honest BEFORE/AFTER comparison
  // panels: unwrapping is done per BLOCK, so two different partitions of the
  // SAME crystal would otherwise be drawn with atoms in visibly different
  // places (up to ~20 A apart), making it look like the structure itself
  // changed when only the classification did.
  function finalizePartition(geom, nodeSet, cellMatrix, cellPar, linkerSplitter, opts) {
    opts = opts || {};
    const { n, pos, symbols, adj, bonds, formula } = geom;

    const metalComponents = connectedComponents(nodeSet, adj);
    const organicSet = new Set();
    for (let i = 0; i < n; i++) if (!nodeSet.has(i)) organicSet.add(i);
    let linkerComponents = connectedComponents(organicSet, adj);
    if (linkerSplitter) linkerComponents = linkerSplitter(linkerComponents, geom);

    const buildingBlocks = metalComponents.concat(linkerComponents);
    const bbTypes = metalComponents.map(() => 'metal').concat(linkerComponents.map(() => 'linker'));
    const K = buildingBlocks.length;

    const atomToBB = new Array(n);
    buildingBlocks.forEach((atoms, bbId) => atoms.forEach(a => { atomToBB[a] = bbId; }));

    const unwrapped = pos.map(p => p.slice());
    if (!opts.noUnwrap) buildingBlocks.forEach(atoms => {
      const blockSet = new Set(atoms);
      const root = atoms[0];
      const visited = new Set([root]);
      const stack = [root];
      while (stack.length) {
        const u = stack.pop();
        for (const nb of adj[u]) {
          if (!blockSet.has(nb.other) || visited.has(nb.other)) continue;
          unwrapped[nb.other] = [
            unwrapped[u][0] + nb.vec[0],
            unwrapped[u][1] + nb.vec[1],
            unwrapped[u][2] + nb.vec[2],
          ];
          visited.add(nb.other);
          stack.push(nb.other);
        }
      }
    });

    const connectionPoints = Array.from({ length: K }, () => []);
    bonds.forEach(bd => {
      const bi = atomToBB[bd.lo], bj = atomToBB[bd.hi];
      if (bi !== bj) {
        connectionPoints[bi].push([
          unwrapped[bd.lo][0] + 0.5 * bd.vec[0],
          unwrapped[bd.lo][1] + 0.5 * bd.vec[1],
          unwrapped[bd.lo][2] + 0.5 * bd.vec[2],
        ]);
        connectionPoints[bj].push([
          unwrapped[bd.hi][0] - 0.5 * bd.vec[0],
          unwrapped[bd.hi][1] - 0.5 * bd.vec[1],
          unwrapped[bd.hi][2] - 0.5 * bd.vec[2],
        ]);
      }
    });

    const blocksJson = [];
    buildingBlocks.forEach((atoms, bbId) => {
      const comp = {};
      atoms.forEach(a => { comp[symbols[a]] = (comp[symbols[a]] || 0) + 1; });
      const cps = connectionPoints[bbId];
      let centroid;
      if (cps.length === 0) {
        const c = [0, 0, 0];
        atoms.forEach(a => { c[0] += unwrapped[a][0]; c[1] += unwrapped[a][1]; c[2] += unwrapped[a][2]; });
        centroid = [c[0] / atoms.length, c[1] / atoms.length, c[2] / atoms.length];
      } else {
        const c = [0, 0, 0];
        cps.forEach(p => { c[0] += p[0]; c[1] += p[1]; c[2] += p[2]; });
        centroid = [c[0] / cps.length, c[1] / cps.length, c[2] / cps.length];
      }
      blocksJson.push({
        id: bbId, type: bbTypes[bbId], atoms, n_atoms: atoms.length,
        composition: comp, centroid, n_connections: cps.length,
      });
    });

    const atomsJson = [];
    for (let i = 0; i < n; i++) {
      atomsJson.push({ id: i, el: symbols[i], pos: unwrapped[i], block: atomToBB[i] });
    }

    const bondsJson = bonds.map(bd => {
      const dRaw = Math.sqrt(
        Math.pow(pos[bd.hi][0] - pos[bd.lo][0], 2) +
        Math.pow(pos[bd.hi][1] - pos[bd.lo][1], 2) +
        Math.pow(pos[bd.hi][2] - pos[bd.lo][2], 2)
      );
      const dTrue = Math.sqrt(bd.vec[0] * bd.vec[0] + bd.vec[1] * bd.vec[1] + bd.vec[2] * bd.vec[2]);
      return {
        a: bd.lo, b: bd.hi, vec: bd.vec,
        cross: Math.abs(dRaw - dTrue) > 0.15,
        interblock: atomToBB[bd.lo] !== atomToBB[bd.hi],
      };
    });

    return {
      formula, n_atoms: n, cell_matrix: cellMatrix, cell_par: cellPar || null,
      atoms: atomsJson, bonds: bondsJson, blocks: blocksJson,
      n_metal_blocks: metalComponents.length, n_linker_blocks: linkerComponents.length,
    };
  }

  // ---------------------------------------------------------------
  // Legacy single-variant entry point (used by the earlier standalone MOF
  // viewer / CIF-upload feature). Behavior UNCHANGED from the original
  // engine: node = metal + any oxygen directly bonded to a metal (no
  // carbon-attachment distinction). Kept as-is for backward compatibility.
  // ---------------------------------------------------------------
  function buildStructure(fracAtoms, cellMatrix) {
    const geom = computeGeometry(fracAtoms, cellMatrix);
    const { n, symbols, isMetal, adj } = geom;
    const nodeAtomSet = new Set();
    for (let i = 0; i < n; i++) if (isMetal[i]) nodeAtomSet.add(i);
    for (let i = 0; i < n; i++) {
      if (!isMetal[i]) continue;
      for (const nb of adj[i]) if (symbols[nb.other] === 'O') nodeAtomSet.add(nb.other);
    }
    return finalizePartition(geom, nodeAtomSet, cellMatrix, fracAtoms.cellPar, null);
  }

  // ---------------------------------------------------------------
  // New: compute all three named MOFid variants from one shared geometry,
  // for the pipeline-stage 3D visualization (mof_stages.js).
  // ---------------------------------------------------------------
  function buildAllVariants(fracAtoms, cellMatrix, engineOpts) {
    const geom = geometryFor(fracAtoms, cellMatrix, engineOpts);
    const cellPar = fracAtoms.cellPar;

    const metalOxoSet = classifyMetalOxo(geom);
    const singleNodeSet = classifySingleNode(geom);

    const metalOxo = finalizePartition(geom, metalOxoSet, cellMatrix, cellPar, null);
    const singleNode = finalizePartition(geom, singleNodeSet, cellMatrix, cellPar, null);
    const allNode = finalizePartition(geom, singleNodeSet, cellMatrix, cellPar, splitAllNodeBranches);

    return {
      formula: geom.formula,
      n_atoms: geom.n,
      cell_matrix: cellMatrix,
      cell_par: cellPar || null,
      metalOxo, singleNode, allNode,
    };
  }

  // ---------------------------------------------------------------
  // NEW: step-by-step trace of the metal-oxo algorithm for the line-by-line
  // code+3D walkthrough. Mirrors, in order, the REAL C++ control flow of
  // Deconstructor::DetectInitialNodesAndLinkers() (code_04a_metal_oxo_algorithm.py,
  // lines 135-182): cut every bond touching a metal, take connected components
  // of what's left ("fragments"), then classify each fragment by the same
  // NumAtoms()==1 / all_oxygens / else rule the real code uses. Also returns
  // the final merged partition (equivalent to the real CollapseNodes() +
  // CollapseLinkers() result) so later steps can show the re-merge/collapse.
  // ---------------------------------------------------------------
  // Shared geometry selector so the SAME walkthrough can be driven by either
  // the corrected engine or a deliberately restricted one (used by the "which
  // engine?" toggle in Section 1, so the restricted behaviour can be seen in the
  // full module-by-module walkthrough, not just in the Section 2 demos).
  function geometryFor(fracAtoms, cellMatrix, opts) {
    opts = opts || {};
    // NOTE: the two bugs are INDEPENDENT and must be combinable -- the original
    // reference table had both at once. Applying only whichever was checked first
    // would silently under-report how broken the original code actually was.
    let geom = opts.noPBC
      ? computeGeometryNoPBC(fracAtoms, cellMatrix)
      : computeGeometry(fracAtoms, cellMatrix);
    if (opts.restrictedMetals) {
      const ms = opts.restrictedMetals;
      geom = Object.assign({}, geom, { isMetal: geom.symbols.map(el => ms.has(el)) });
    }
    return geom;
  }

  function traceMetalOxo(fracAtoms, cellMatrix, engineOpts) {
    const geom = geometryFor(fracAtoms, cellMatrix, engineOpts);
    const { n, symbols, bonds, isMetal } = geom;

    // "deleteBonds(&split_mol, true)" -- mark every bond touching a metal
    const metalBondSet = new Set();
    bonds.forEach((bd, i) => { if (isMetal[bd.lo] || isMetal[bd.hi]) metalBondSet.add(i); });

    // "fragments = split_mol.Separate()" -- connected components of what's left
    const fragAdj = Array.from({ length: n }, () => []);
    bonds.forEach((bd, i) => {
      if (metalBondSet.has(i)) return;
      fragAdj[bd.lo].push(bd.hi);
      fragAdj[bd.hi].push(bd.lo);
    });
    const visited = new Set();
    const rawFragments = [];
    for (let i = 0; i < n; i++) {
      if (visited.has(i)) continue;
      const comp = []; const stack = [i]; visited.add(i);
      while (stack.length) {
        const u = stack.pop(); comp.push(u);
        for (const v of fragAdj[u]) if (!visited.has(v)) { visited.add(v); stack.push(v); }
      }
      rawFragments.push(comp.sort((a, b) => a - b));
    }

    // "it->NumAtoms()==1" / "all_oxygens" / else -- per-fragment classification
    const fragRole = rawFragments.map(frag => {
      if (frag.length === 1) return 'node';
      const allOxygens = frag.every(a => symbols[a] === 'O' || symbols[a] === 'H');
      return allOxygens ? 'node' : 'linker';
    });

    // Final result, equivalent to CollapseNodes()+CollapseLinkers() having run
    const nodeSet = classifyMetalOxo(geom);
    const finalData = finalizePartition(geom, nodeSet, cellMatrix, fracAtoms.cellPar, null);

    return { geom, metalBondSet, rawFragments, fragRole, nodeSet, finalData };
  }

  // ---------------------------------------------------------------
  // NEW: "restricted" geometry variants that faithfully reproduce the two real,
  // historically-documented bugs in a restricted element table
  // implementation, for the drawbacks/negatives 3D before-vs-after demos.
  // Both are otherwise identical to computeGeometry() -- only the ONE
  // specific behavior named is degraded, so the visual difference in the
  // final decomposition is attributable to exactly that bug.
  // ---------------------------------------------------------------

  // Bug 1: no periodic-boundary awareness. The original reference table ran
  // scipy.spatial.distance.pdist on raw Cartesian coordinates -- i.e. it only
  // ever checked the "home" unit cell image (0,0,0), never the 26 neighbouring
  // periodic images. Any bond that should cross a cell boundary is missed,
  // and atoms near the boundary can be wrongly perceived as bonded straight
  // across empty space to the WRONG neighbour's home-cell image instead.
  function computeGeometryNoPBC(fracAtoms, cellMatrix) {
    const n = fracAtoms.length;
    const pos = fracAtoms.map(a => fracToCart([a.fx, a.fy, a.fz], cellMatrix));
    const symbols = fracAtoms.map(a => a.el);
    const radii = symbols.map(el => COVALENT_RADII[el] !== undefined ? COVALENT_RADII[el] : 0.75);
    const isMetal = symbols.map(el => METALS.has(el));
    const bonds = [];
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const cutoff = (radii[i] + radii[j]) * ((isMetal[i] || isMetal[j]) ? 1.30 : 1.15);
        const dx = pos[j][0] - pos[i][0], dy = pos[j][1] - pos[i][1], dz = pos[j][2] - pos[i][2];
        const d = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (d > 0.4 && d < cutoff) bonds.push({ lo: i, hi: j, vec: [dx, dy, dz] });
      }
    }
    const adj = Array.from({ length: n }, () => []);
    bonds.forEach((bd, bi) => {
      adj[bd.lo].push({ other: bd.hi, vec: bd.vec, bondIdx: bi });
      adj[bd.hi].push({ other: bd.lo, vec: [-bd.vec[0], -bd.vec[1], -bd.vec[2]], bondIdx: bi });
    });
    const formula = (() => {
      const comp = {}; symbols.forEach(s => { comp[s] = (comp[s] || 0) + 1; });
      return Object.entries(comp).map(([el, c]) => el + c).join('');
    })();
    return { n, pos, symbols, radii, isMetal, adj, bonds, formula };
  }

  // Bug 2: hardcoded, incomplete metal element list. This is the EXACT
  // 8-element hardcoded set found in a restricted element table,
  // instead of the ~55-element IUPAC/InChI-based METALS set used everywhere
  // else in this engine (and by the real MOFid isMetal(), code_03.py).
  // Any metal outside this list (Zr, Mg, rare earths, ...) is silently
  // treated as an ordinary nonmetal.
  const LEGACY_HARDCODED_METALS = new Set(['Zn', 'Cu', 'Ni', 'Co', 'Fe', 'Al', 'Cr', 'Mn']);

  function computeGeometryRestrictedMetals(fracAtoms, cellMatrix, metalSet) {
    const geom = computeGeometry(fracAtoms, cellMatrix); // correct PBC bonding, only isMetal[] is degraded
    const isMetal = geom.symbols.map(el => metalSet.has(el));
    return Object.assign({}, geom, { isMetal });
  }

  // Runs the SAME metal-oxo classification rule (classifyMetalOxo) on top of
  // one of the restricted geometries above, so the resulting difference in the
  // final decomposition is caused ONLY by that one bug.
  function buildComparisonVariant(fracAtoms, cellMatrix, opts) {
    opts = opts || {};
    const geom = opts.noPBC
      ? computeGeometryNoPBC(fracAtoms, cellMatrix)
      : opts.restrictedMetals
        ? computeGeometryRestrictedMetals(fracAtoms, cellMatrix, opts.restrictedMetals)
        : computeGeometry(fracAtoms, cellMatrix);
    const nodeSet = classifyMetalOxo(geom);
    return finalizePartition(geom, nodeSet, cellMatrix, fracAtoms.cellPar, null,
                             { noUnwrap: !!opts.noUnwrap });
  }

  // =================================================================
  // THE PROPOSED FIXES
  //
  // Four limitations of the published metal-oxo algorithm, and the
  // corresponding repair implemented here. Each is independently
  // switchable so its individual effect can be measured.
  //
  //  FIX 1  completeNodes    -- the published rule cuts at the M-O bond, so a
  //                            coordinating carboxylate is filed as linker and
  //                            the node is left as bare metal (HKUST-1 -> just
  //                            [Cu][Cu]). Extending the node across the
  //                            carboxylate gives a chemically complete SBU.
  //  FIX 2  donorAgnostic    -- `all_oxygens` recognises only O/H bridges, so
  //                            nitrido / sulfido / mixed-heteroatom bridges are
  //                            misfiled as organic. Generalise the test to any
  //                            carbon-free bridging fragment.
  //  FIX 3  (reported)       -- bond perception is inferred, never given, so a
  //                            decomposition can hinge on a borderline contact.
  //                            assessQuality() reports how many bonds sit near
  //                            the cutoff instead of failing silently.
  //  FIX 4  (reported)       -- rod SBUs get an arbitrary convention and
  //                            0-/1-connected fragments are silently discarded
  //                            as "solvent". assessQuality() surfaces both.
  // =================================================================

  // FIX 2: carbon-free bridge test, generalising `all_oxygens`.
  const ORGANIC_MARKER = 'C';
  function isBridgingHeteroatom(sym) {
    return sym !== ORGANIC_MARKER && sym !== 'H';
  }

  function classifyMetalOxoFixed(geom, fixes) {
    fixes = fixes || {};
    const { n, symbols, isMetal, adj } = geom;
    const nodeSet = new Set();
    for (let i = 0; i < n; i++) if (isMetal[i]) nodeSet.add(i);

    // --- baseline + FIX 2: bridging heteroatoms bound to metal, no carbon ---
    for (let i = 0; i < n; i++) {
      if (isMetal[i]) continue;
      const sym = symbols[i];
      const eligible = fixes.donorAgnostic ? isBridgingHeteroatom(sym) : (sym === 'O');
      if (!eligible) continue;
      let bondedToMetal = false, bondedToCarbon = false;
      for (const nb of adj[i]) {
        if (isMetal[nb.other]) bondedToMetal = true;
        if (symbols[nb.other] === ORGANIC_MARKER) bondedToCarbon = true;
      }
      if (bondedToMetal && !bondedToCarbon) nodeSet.add(i);
    }
    for (let i = 0; i < n; i++) {
      if (symbols[i] !== 'H') continue;
      for (const nb of adj[i]) if (nodeSet.has(nb.other)) nodeSet.add(i);
    }

    // --- FIX 1: complete the node across its coordinating groups ---
    if (fixes.completeNodes) {
      const metalNbors = new Set();
      for (let i = 0; i < n; i++) {
        if (!isMetal[i]) continue;
        for (const nb of adj[i]) metalNbors.add(nb.other);
      }
      for (const o of metalNbors) {
        if (symbols[o] !== 'O') continue;
        let carbon = -1;
        for (const nb of adj[o]) if (symbols[nb.other] === ORGANIC_MARKER) carbon = nb.other;
        if (carbon === -1) continue;
        // verify it really is a carboxylate carbon: 1 C-neighbour, 2 O-neighbours
        let cC = 0, cO = 0, otherO = -1;
        for (const cnb of adj[carbon]) {
          if (symbols[cnb.other] === ORGANIC_MARKER) cC++;
          else if (symbols[cnb.other] === 'O') { cO++; if (cnb.other !== o) otherO = cnb.other; }
        }
        if (cC !== 1 || cO !== 2) continue;
        nodeSet.add(o); nodeSet.add(carbon);
        if (otherO !== -1) {
          nodeSet.add(otherO);
          for (const nb of adj[otherO]) if (symbols[nb.other] === 'H') nodeSet.add(nb.other);
        }
      }
    }
    return nodeSet;
  }

  // FIX 3 + FIX 4: quality signals the published algorithm never reports.
  function assessQuality(geom, partition) {
    const { n, pos, symbols, radii, isMetal, bonds, adj } = geom;

    // FIX 3 -- bonds sitting within 10% of their cutoff are "borderline":
    // a slightly different CIF refinement could add or remove them.
    let borderline = 0;
    bonds.forEach(bd => {
      const cutoff = (radii[bd.lo] + radii[bd.hi]) * ((isMetal[bd.lo] || isMetal[bd.hi]) ? 1.30 : 1.15);
      const d = Math.sqrt(bd.vec[0] * bd.vec[0] + bd.vec[1] * bd.vec[1] + bd.vec[2] * bd.vec[2]);
      if (d > cutoff * 0.90) borderline++;
    });

    // FIX 4 -- fragments the solvent heuristic would silently discard, and
    // node fragments that are periodically infinite (rod SBUs).
    let discarded = 0, rodLike = 0;
    (partition ? partition.blocks : []).forEach(b => {
      if (b.n_connections <= 1) discarded++;
      // a node block whose atom count exceeds what one cell can hold without
      // repeating is a rod-SBU candidate (crosses the cell in a closed loop)
      if (b.type === 'metal' && b.n_connections > 6 && b.n_atoms > 12) rodLike++;
    });

    let missingH = 0;
    for (let i = 0; i < n; i++) if (symbols[i] === 'H') missingH++;

    return {
      borderlineBonds: borderline,
      borderlinePct: bonds.length ? (borderline / bonds.length) * 100 : 0,
      discardedFragments: discarded,
      rodCandidates: rodLike,
      hasHydrogens: missingH > 0,
      totalBonds: bonds.length,
    };
  }

  // Single entry point for the site: published baseline vs. all fixes applied.
  //   opts.fixes  : {completeNodes, donorAgnostic} (omit for the published rule)
  //   opts.noUnwrap: draw at raw home-cell positions (for honest A/B panels)
  function buildMetalOxoVariant(fracAtoms, cellMatrix, opts) {
    opts = opts || {};
    const geom = computeGeometry(fracAtoms, cellMatrix);
    const nodeSet = classifyMetalOxoFixed(geom, opts.fixes || {});
    const data = finalizePartition(geom, nodeSet, cellMatrix, fracAtoms.cellPar, null,
                                   { noUnwrap: !!opts.noUnwrap });
    data.quality = assessQuality(geom, data);
    return data;
  }

  const api = {
    parseCIF, buildStructure, buildAllVariants, traceMetalOxo, buildComparisonVariant,
    buildMetalOxoVariant, classifyMetalOxoFixed, assessQuality,
    LEGACY_HARDCODED_METALS, COVALENT_RADII, METALS,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.MOFDecompose = api;
})(typeof window !== 'undefined' ? window : globalThis);
