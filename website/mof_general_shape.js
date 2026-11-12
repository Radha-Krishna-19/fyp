/* BFDH crystal shape for a CIF of ANY lattice, in the browser. No DOM.
   Python reference: code/morphology/run_general_shape.py (results/general_shape.json);
   website/tests/test_general_shape.js compares the two number by number.

   Steps:
     1. read the cell, the atoms and the symmetry operations listed in the CIF, and expand the
        atoms by those operations (a CIF often lists only the asymmetric unit);
     2. lattice vectors A (rows) and reciprocal vectors B = (A^-1)^T, so 1/d_hkl = |h B|;
     3. which reflections vanish: with the file's operations (x' = R x + t), reflection h is
        absent when h R = h and h.t is not an integer. A file stored in P1 carries no operations;
        then the structure factor of the atoms (without H, weighted by atomic number) decides,
        |F(h)| / sum Z < 1e-3 counting as zero;
     4. d_eff = d_hkl / n, n the first allowed order; families are orbits {h R} (in P1: equal
        d_eff and equal |F|, a grouping that changes labels but never the shape);
     5. BFDH: the 40 families of largest d_eff, family f at distance R_f = d_eff,max / d_eff,f;
        the shape is a large box cut by every plane n.x <= R_f;
     6. gyration tensor of the solid, its principal radii a >= b >= c, and Zingg's habit:
        compact (b/a and c/b >= 2/3), rod (b/a < 2/3), plate (c/b < 2/3), lath (both).
   Requires mof_cif_shape.js (window.CIFSHAPE) for the CIF reader and the polyhedron cutter. */
(function (global) {
  'use strict';
  var CS = global.CIFSHAPE || (typeof require !== 'undefined' ? require('./mof_cif_shape.js') : null);
  var la = CS.la;
  var dot = la.dot, sub = la.sub, add = la.add, scale = la.scale, cross = la.cross, norm = la.norm, unit = la.unit;
  var N_FAMILIES = 40, MAX_INDEX = 6, ZINGG = 2 / 3, DUP = 0.05, SYM_TOL = 0.05, PHASE_TOL = 0.05;
  var Z = { H: 1, He: 2, Li: 3, Be: 4, B: 5, C: 6, N: 7, O: 8, F: 9, Na: 11, Mg: 12, Al: 13, Si: 14, P: 15, S: 16, Cl: 17,
            K: 19, Ca: 20, Sc: 21, Ti: 22, V: 23, Cr: 24, Mn: 25, Fe: 26, Co: 27, Ni: 28, Cu: 29, Zn: 30, Ga: 31, Ge: 32,
            Br: 35, Sr: 38, Y: 39, Zr: 40, Nb: 41, Mo: 42, Ru: 44, Rh: 45, Pd: 46, Ag: 47, Cd: 48, In: 49, Sn: 50, I: 53,
            Ba: 56, La: 57, Ce: 58, Nd: 60, Eu: 63, Gd: 64, Tb: 65, Dy: 66, Er: 68, Yb: 70, Hf: 72, W: 74, Pt: 78, Au: 79,
            Hg: 80, Pb: 82, Bi: 83, U: 92 };
  function zOf(e) { return Z[e] || 6; }

  // ---- 1. symmetry operations written in the CIF ------------------------------------------
  function parseTerm(s) {                        // "1/2", "0.25", "-1/3"
    if (s.indexOf('/') >= 0) { var p = s.split('/'); return parseFloat(p[0]) / parseFloat(p[1]); }
    return parseFloat(s);
  }
  function parseOp(str) {
    var parts = str.replace(/\s+/g, '').toLowerCase().split(',');
    if (parts.length !== 3) return null;
    var R = [[0, 0, 0], [0, 0, 0], [0, 0, 0]], t = [0, 0, 0];
    for (var i = 0; i < 3; i++) {
      var terms = parts[i].match(/[+-]?[^+-]+/g) || [];
      for (var k = 0; k < terms.length; k++) {
        var term = terms[k], m = /^([+-]?)([0-9./]*)\*?([xyz])$/.exec(term);
        if (m) {
          var c = m[2] ? parseTerm(m[2]) : 1;
          R[i]['xyz'.indexOf(m[3])] += (m[1] === '-' ? -1 : 1) * c;
        } else {
          var v = parseTerm(term);
          if (isNaN(v)) return null;
          t[i] += v;
        }
      }
    }
    return { R: R, t: t };
  }
  function parseSymops(text) {
    var lines = text.split(/\r?\n/), ops = [];
    for (var i = 0; i < lines.length; i++) {
      if (lines[i].trim() !== 'loop_') continue;
      var j = i + 1, cols = [];
      while (j < lines.length && /^\s*_/.test(lines[j])) { cols.push(lines[j].trim().split(/\s+/)[0]); j++; }
      var ic = cols.indexOf('_symmetry_equiv_pos_as_xyz');
      if (ic < 0) ic = cols.indexOf('_space_group_symop_operation_xyz');
      if (ic < 0) continue;
      while (j < lines.length && lines[j].trim() && !/^\s*(_|loop_|data_)/.test(lines[j])) {
        var l = lines[j].trim(), q = /'([^']*)'|"([^"]*)"/.exec(l), s;
        if (q) s = q[1] != null ? q[1] : q[2];
        else { var toks = l.split(/\s+/); s = toks.length > cols.length - 1 ? toks.slice(ic).join('') : toks[toks.length - 1]; }
        var op = parseOp(s);
        if (op) ops.push(op);
        j++;
      }
      break;
    }
    if (!ops.length) {                          // a single operation written without a loop
      var m = /^\s*_(symmetry_equiv_pos_as_xyz|space_group_symop_operation_xyz)\s+'([^']*)'/m.exec(text);
      if (m) { var o = parseOp(m[2]); if (o) ops.push(o); }
    }
    if (!ops.length) ops.push({ R: [[1, 0, 0], [0, 1, 0], [0, 0, 1]], t: [0, 0, 0] });
    return ops;
  }
  // a periodic lookup grid: find atoms of one element near a fractional position
  function Grid(atoms, A, cellLen) {
    var lens = [norm(A[0]), norm(A[1]), norm(A[2])];
    var nb = lens.map(function (L) { return Math.max(1, Math.floor(L / (cellLen || 2.5))); });
    var bins = {};
    function bin(x) { return [0, 1, 2].map(function (i) { var b = Math.floor((x[i] - Math.floor(x[i])) * nb[i]); return b >= nb[i] ? 0 : b; }); }
    function add_(a, idx) { var b = bin(a.x), k = a.el + ':' + b.join(','); (bins[k] = bins[k] || []).push(idx); }
    atoms.forEach(add_);
    return {
      add: function (a, idx) { add_(a, idx); },
      // the index of an atom of element el within tol Angstrom of x (periodic), and the offset to it
      find: function (x, el, tol, list) {
        var b = bin(x), best = -1, bestD = tol, off = null;
        for (var i = -1; i <= 1; i++) for (var j = -1; j <= 1; j++) for (var k = -1; k <= 1; k++) {
          var key = el + ':' + [(b[0] + i + nb[0]) % nb[0], (b[1] + j + nb[1]) % nb[1], (b[2] + k + nb[2]) % nb[2]].join(',');
          var L = bins[key]; if (!L) continue;
          for (var m = 0; m < L.length; m++) {
            var y = list[L[m]].x, d = [y[0] - x[0], y[1] - x[1], y[2] - x[2]];
            d = [d[0] - Math.round(d[0]), d[1] - Math.round(d[1]), d[2] - Math.round(d[2])];
            var dist = norm(la.vecmat(d, A));
            if (dist < bestD) { bestD = dist; best = L[m]; off = d; }
          }
        }
        return best < 0 ? null : { index: best, offset: off, dist: bestD };
      }
    };
  }
  function wrap01(v) { return v.map(function (x) { x = x - Math.floor(x); return x >= 1 - 1e-12 ? 0 : x; }); }
  function expand(atoms, ops, A) {
    // apply every listed operation, wrap into the cell, drop copies closer than DUP Angstrom
    var out = [], grid = Grid([], A);
    atoms.forEach(function (a) {
      ops.forEach(function (op) {
        var y = wrap01(add(la.matvec(op.R, a.x), op.t));
        if (!grid.find(y, a.el, DUP, out)) { out.push({ el: a.el, x: y, label: a.label, line: a.line, occ: a.occ }); grid.add(out[out.length - 1], out.length - 1); }
      });
    });
    return out;
  }

  // ---- 2b. find the symmetry of the atoms (as spglib does, at a distance tolerance) -------------
  // Candidate rotations are the integer matrices with entries -1, 0, 1 that keep the metric
  // (R^T G R = G). For each, a translation t is tried that sends one atom of the rarest element onto
  // each atom of that element; (R, t) is kept if EVERY non-hydrogen atom then lands within tol of an
  // atom of the same element. t is refined as the mean residual over all atoms.
  function findSymmetry(atoms, A, tol) {
    tol = tol || SYM_TOL;
    var G = la.matmul(A, la.transpose(A)), scaleG = Math.max(G[0][0], G[1][1], G[2][2]);
    var fw = atoms.filter(function (a) { return a.el !== 'H'; });
    if (!fw.length) fw = atoms;
    var grid = Grid(fw, A), rots = [], vals = [-1, 0, 1];
    for (var c = 0; c < 19683; c++) {
      var e = [], x = c;
      for (var q = 0; q < 9; q++) { e.push(vals[x % 3]); x = Math.floor(x / 3); }
      var Rm = [[e[0], e[1], e[2]], [e[3], e[4], e[5]], [e[6], e[7], e[8]]];
      if (Math.abs(la.det3(Rm)) !== 1) continue;
      var M = la.matmul(la.transpose(Rm), la.matmul(G, Rm)), ok = true;
      for (var i = 0; i < 3 && ok; i++) for (var j = 0; j < 3 && ok; j++) if (Math.abs(M[i][j] - G[i][j]) > 2e-3 * scaleG) ok = false;
      if (ok) rots.push(Rm);
    }
    var count = {};
    fw.forEach(function (a) { count[a.el] = (count[a.el] || 0) + 1; });
    var rare = Object.keys(count).sort(function (p, q) { return count[p] - count[q]; })[0];
    var rareAtoms = fw.filter(function (a) { return a.el === rare; }), x0 = rareAtoms[0].x;
    var ops = [];
    rots.forEach(function (Rm) {
      var Rx0 = la.matvec(Rm, x0), seen = [];
      for (var k = 0; k < rareAtoms.length; k++) {
        var t = sub(rareAtoms[k].x, Rx0);
        t = t.map(function (v) { return v - Math.floor(v); });
        var resid = [0, 0, 0], good = true;
        for (var m = 0; m < fw.length; m++) {
          var y = add(la.matvec(Rm, fw[m].x), t), hit = grid.find(y, fw[m].el, tol, fw);
          if (!hit) { good = false; break; }
          resid = add(resid, hit.offset);
        }
        if (!good) continue;
        t = wrap01(add(t, scale(resid, 1 / fw.length)));
        // the same (R, t) reached from two atoms is one operation
        if (seen.some(function (s) { var d = sub(s, t); return d.every(function (v) { return Math.abs(v - Math.round(v)) < 1e-3; }); })) continue;
        seen.push(t);
        ops.push({ R: Rm, t: t });
      }
    });
    return { ops: ops, rotations: rots.length, element: rare, tol: tol };
  }

  // ---- 3. absences ------------------------------------------------------------------------------
  function absentByOps(h, ops) {
    for (var i = 0; i < ops.length; i++) {
      var R = ops[i].R, hR = [h[0] * R[0][0] + h[1] * R[1][0] + h[2] * R[2][0],
                               h[0] * R[0][1] + h[1] * R[1][1] + h[2] * R[2][1],
                               h[0] * R[0][2] + h[1] * R[1][2] + h[2] * R[2][2]];
      if (Math.abs(hR[0] - h[0]) < 1e-9 && Math.abs(hR[1] - h[1]) < 1e-9 && Math.abs(hR[2] - h[2]) < 1e-9) {
        var ph = dot(h, ops[i].t);
        if (Math.abs(ph - Math.round(ph)) > PHASE_TOL) return true;
      }
    }
    return false;
  }
  function sfMagnitude(h, fw) {                    // |F(h)| / sum Z for the framework atoms
    var re = 0, im = 0;
    for (var i = 0; i < fw.X.length; i++) {
      var p = 2 * Math.PI * (h[0] * fw.X[i][0] + h[1] * fw.X[i][1] + h[2] * fw.X[i][2]);
      re += fw.w[i] * Math.cos(p); im += fw.w[i] * Math.sin(p);
    }
    return Math.sqrt(re * re + im * im) / fw.sumZ;
  }
  function gcd(a, b) { a = Math.abs(a); b = Math.abs(b); while (b) { var t = b; b = a % b; a = t; } return a; }

  // ---- small 3x3 symmetric eigen-solver (Jacobi) ------------------------------------------------
  function eigSym(M) {
    var A = M.map(function (r) { return r.slice(); }), V = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
    for (var sweep = 0; sweep < 60; sweep++) {
      var off = A[0][1] * A[0][1] + A[0][2] * A[0][2] + A[1][2] * A[1][2];
      if (off < 1e-30) break;
      for (var p = 0; p < 2; p++) for (var q = p + 1; q < 3; q++) {
        if (Math.abs(A[p][q]) < 1e-300) continue;
        var th = (A[q][q] - A[p][p]) / (2 * A[p][q]);
        var t = (th >= 0 ? 1 : -1) / (Math.abs(th) + Math.sqrt(th * th + 1)), c = 1 / Math.sqrt(t * t + 1), s = t * c;
        for (var k = 0; k < 3; k++) {             // A = J^T A J
          var akp = A[k][p], akq = A[k][q];
          A[k][p] = c * akp - s * akq; A[k][q] = s * akp + c * akq;
        }
        for (k = 0; k < 3; k++) {
          var apk = A[p][k], aqk = A[q][k];
          A[p][k] = c * apk - s * aqk; A[q][k] = s * apk + c * aqk;
        }
        for (k = 0; k < 3; k++) {
          var vkp = V[k][p], vkq = V[k][q];
          V[k][p] = c * vkp - s * vkq; V[k][q] = s * vkp + c * vkq;
        }
      }
    }
    var idx = [0, 1, 2].sort(function (i, j) { return A[j][j] - A[i][i]; });
    return { values: idx.map(function (i) { return A[i][i]; }), vectors: idx.map(function (i) { return [V[0][i], V[1][i], V[2][i]]; }) };
  }

  // ---- 6. solid measures -----------------------------------------------------------------------
  function solid(faces) {
    var all = [];
    faces.forEach(function (f) { f.pts.forEach(function (p) { all.push(p); }); });
    var c0 = scale(all.reduce(add, [0, 0, 0]), 1 / all.length);
    var M = 0, first = [0, 0, 0], S2 = [[0, 0, 0], [0, 0, 0], [0, 0, 0]], area = 0;
    faces.forEach(function (f) {
      f.area = CS.polygonArea(f.pts); area += f.area;
      for (var t = 1; t + 1 < f.pts.length; t++) {
        var T = [c0, f.pts[0], f.pts[t], f.pts[t + 1]];
        var vol = Math.abs(la.det3([sub(T[1], T[0]), sub(T[2], T[0]), sub(T[3], T[0])])) / 6;
        var s = T.reduce(add, [0, 0, 0]);
        for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) {
          var tt = 0; T.forEach(function (v) { tt += v[i] * v[j]; });
          S2[i][j] += vol / 20 * (tt + s[i] * s[j]);
        }
        first = add(first, scale(s, vol / 4)); M += vol;
      }
    });
    var com = scale(first, 1 / M), G = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
    for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) G[i][j] = S2[i][j] / M - com[i] * com[j];
    return { volume: M, area: area, gyration: G, centre: com };
  }
  function smallIntegers(v) {
    var m0 = Math.max(Math.abs(v[0]), Math.abs(v[1]), Math.abs(v[2]));
    v = scale(v, 1 / m0);
    var big = [0, 1, 2].reduce(function (b, i) { return Math.abs(v[i]) > Math.abs(v[b]) ? i : b; }, 0);
    if (v[big] < 0) v = scale(v, -1);
    for (var m = 1; m <= 6; m++) {
      var u = v.map(function (x) { return Math.round(x * m); });
      if (!u[0] && !u[1] && !u[2]) continue;
      var g = gcd(gcd(u[0], u[1]), u[2]); u = u.map(function (x) { return x / g; });
      var cos = Math.abs(dot(u, v)) / (norm(u) * norm(v));
      if (Math.acos(Math.min(1, cos)) * 180 / Math.PI < 3) return u.map(function (x) { return x + 0; });
    }
    return null;
  }
  function famLabel(k) { return '{' + k.join('') + '}'; }
  function fourIndex(k) { return '{' + [k[0], k[1], -(k[0] + k[1]), k[2]].join('') + '}'; }
  function latticeName(cell) {
    var a = cell[0], b = cell[1], c = cell[2], al = cell[3], be = cell[4], ga = cell[5];
    function eq(x, y) { return Math.abs(x - y) < 1e-3 * Math.max(x, y); }
    function r(x, y) { return Math.abs(x - y) < 0.01; }
    if (eq(a, b) && eq(b, c) && r(al, 90) && r(be, 90) && r(ga, 90)) return 'cubic';
    if (eq(a, b) && r(al, 90) && r(be, 90) && r(ga, 120)) return 'hexagonal axes (hexagonal or trigonal)';
    if (eq(a, b) && eq(b, c) && r(al, be) && r(be, ga)) return 'rhombohedral axes';
    if (eq(a, b) && r(al, 90) && r(be, 90) && r(ga, 90)) return 'tetragonal';
    if (r(al, 90) && r(be, 90) && r(ga, 90)) return 'orthorhombic';
    if ((r(al, 90) && r(ga, 90)) || (r(al, 90) && r(be, 90)) || (r(be, 90) && r(ga, 90))) return 'monoclinic';
    return 'triclinic';
  }

  // ---- the whole chain ---------------------------------------------------------------------------
  function run(text, opts) {
    opts = opts || {};
    var t0 = Date.now(), R = {};
    // opts.base: an earlier result for the same file, whose atoms and symmetry are reused;
    // opts.stretch: [sa, sb, sc] multiplies a, b, c with the atoms kept at their fractional coordinates
    // (Phase 1b). Absences depend only on fractional coordinates, so the original operations decide
    // them; faces stay equivalent only under the operations that still keep the new metric.
    var base = opts.base, cif, ops, atoms, sym;
    if (base) { cif = base.cif; ops = base.ops; atoms = base.atoms; sym = base.symmetry; }
    else {
      cif = CS.parseCIF(text); ops = parseSymops(text);
      atoms = expand(cif.atoms, ops, CS.latticeVectors(cif.cell));
      sym = findSymmetry(atoms, CS.latticeVectors(cif.cell), opts.tol);
    }
    var st = opts.stretch || [1, 1, 1];
    var cell = [cif.cell[0] * st[0], cif.cell[1] * st[1], cif.cell[2] * st[2], cif.cell[3], cif.cell[4], cif.cell[5]];
    var A = CS.latticeVectors(cell), B = la.transpose(la.inv3(A));
    R.cif = cif; R.cell = cell; R.stretch = st; R.A = A; R.B = B; R.ops = ops; R.atoms = atoms;
    R.nAsymmetric = cif.atoms.length; R.nAtoms = atoms.length;
    R.lattice = latticeName(cell);
    R.hexagonal = R.lattice.indexOf('hexagonal') === 0;
    R.symmetry = sym; R.symOps = sym.ops;
    var fw = { X: [], w: [], sumZ: 0 };
    atoms.forEach(function (a) { if (a.el !== 'H') { fw.X.push(a.x); fw.w.push(zOf(a.el)); fw.sumZ += zOf(a.el); } });
    R.framework = fw;
    var symOps = sym.ops, G2 = la.matmul(A, la.transpose(A)), g2 = Math.max(G2[0][0], G2[1][1], G2[2][2]);
    var rotOps = symOps.map(function (o) { return o.R; }).filter(function (Rm) {
      var M = la.matmul(la.transpose(Rm), la.matmul(G2, Rm));
      for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) if (Math.abs(M[i][j] - G2[i][j]) > 2e-3 * g2) return false;
      return true;
    });
    R.keptOps = rotOps.length;      // operations whose rotation still keeps the (stretched) metric
    function absent(h) { return absentByOps(h, symOps); }
    // faces
    var M = opts.maxIndex || MAX_INDEX, faces = [], famMap = {};
    for (var h = -M; h <= M; h++) for (var k = -M; k <= M; k++) for (var l = -M; l <= M; l++) {
      if (!h && !k && !l) continue;
      if (gcd(gcd(h, k), l) !== 1) continue;
      var v = [h, k, l], n = 1;
      while (absent(scale(v, n)) && n < 13) n++;
      var g = la.vecmat(v, B), d = 1 / norm(g);
      var best = null;
      rotOps.forEach(function (Rm) {
        var w = [v[0] * Rm[0][0] + v[1] * Rm[1][0] + v[2] * Rm[2][0], v[0] * Rm[0][1] + v[1] * Rm[1][1] + v[2] * Rm[2][1],
                 v[0] * Rm[0][2] + v[1] * Rm[1][2] + v[2] * Rm[2][2]];
        if (!best || w[0] > best[0] || (w[0] === best[0] && (w[1] > best[1] || (w[1] === best[1] && w[2] > best[2])))) best = w;
      });
      var key = best.join(',');
      var f = { hkl: v, order: n, d: d, dEff: d / n, normal: unit(g), key: key };
      faces.push(f);
      (famMap[key] = famMap[key] || []).push(f);
    }
    var fams = Object.keys(famMap).map(function (key) {
      var mem = famMap[key], rep = mem.reduce(function (b, f) {
        var x = f.hkl, y = b.hkl;
        return (x[0] > y[0] || (x[0] === y[0] && (x[1] > y[1] || (x[1] === y[1] && x[2] > y[2])))) ? f : b;
      }, mem[0]);
      return { key: rep.hkl, label: famLabel(rep.hkl), fourIndex: fourIndex(rep.hkl), members: mem, d: rep.d, order: rep.order,
               dEff: rep.dEff, multiplicity: mem.length };
    });
    fams.sort(function (x, y) {
      var a = Math.round(y.dEff * 1e6) - Math.round(x.dEff * 1e6);
      if (a) return a;
      if (y.multiplicity !== x.multiplicity) return y.multiplicity - x.multiplicity;
      for (var i = 0; i < 3; i++) if (x.key[i] !== y.key[i]) return y.key[i] - x.key[i];
      return 0;
    });
    R.allFamilies = fams.length;
    fams = fams.slice(0, N_FAMILIES);
    var dmax = fams[0].dEff;
    var planes = [];
    fams.forEach(function (F) {
      F.R = dmax / F.dEff;
      F.members.forEach(function (f) { planes.push({ n: f.normal, d: F.R, tag: F.label, hkl: f.hkl }); });
    });
    planes.sort(function (p, q) { return p.d - q.d; });
    var shape = CS.box(1000);
    planes.forEach(function (p) { shape = CS.cut(shape, p).faces; });
    R.bounded = !shape.some(function (f) { return f.tag === 'bound'; });
    R.families = fams; R.dmax = dmax; R.faces = shape;
    var S = solid(shape);
    R.volume = S.volume; R.area = S.area;
    R.sphericity = Math.pow(Math.PI, 1 / 3) * Math.pow(6 * S.volume, 2 / 3) / S.area;
    var frac = {};
    shape.forEach(function (f) { frac[f.tag] = (frac[f.tag] || 0) + f.area / S.area; });
    fams.forEach(function (F) { F.areaFraction = frac[F.label] || 0; });
    var E = eigSym(S.gyration);
    var w = E.values.map(function (x) { return Math.sqrt(Math.max(x, 0)); });
    R.radii = w.map(function (x) { return x / w[0]; });
    R.bOverA = w[1] / w[0]; R.cOverB = w[2] / w[1];
    R.habit = R.bOverA >= ZINGG ? (R.cOverB >= ZINGG ? 'equant' : 'plate') : (R.cOverB >= ZINGG ? 'rod' : 'lath');
    R.axes = E.vectors;                                   // Cartesian unit vectors, longest first
    var Ainv = la.inv3(A);
    R.longAxisUVW = smallIntegers(la.vecmat(E.vectors[0], Ainv));
    R.flatFaceHKL = smallIntegers(la.matvec(A, E.vectors[2]));
    // which families make the sides and which the ends (rod) or the flat faces (plate)
    var ax = R.habit === 'plate' ? E.vectors[2] : E.vectors[0];
    fams.forEach(function (F) {
      if (!F.areaFraction) return;
      var c = Math.abs(dot(F.members[0].normal, ax));
      F.role = R.habit === 'equant' ? 'face' : R.habit === 'plate' ? (c > 0.9 ? 'flat face' : 'edge') : (c < 0.2 ? 'side' : 'end');
    });
    R.ms = Date.now() - t0;
    return R;
  }

  var API = { run: run, findSymmetry: findSymmetry, parseSymops: parseSymops, parseOp: parseOp, expand: expand, absentByOps: absentByOps,
              sfMagnitude: sfMagnitude, eigSym: eigSym, solid: solid, smallIntegers: smallIntegers, latticeName: latticeName,
              fourIndex: fourIndex, N_FAMILIES: N_FAMILIES, ZINGG: ZINGG };
  global.GENSHAPE = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : this);
