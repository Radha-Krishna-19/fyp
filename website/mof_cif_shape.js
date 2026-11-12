/* =====================================================================
   mof_cif_shape.js — from the text of a CIF file to a crystal shape, in
   the browser, keeping every intermediate number so the page can show the
   working.

   This is an independent implementation of the steps that the Python
   script code/morphology/run_cif_to_shape.py performs; the test
   tests/test_cif_to_shape.js checks that the two agree number by number,
   and that both agree with spglib and with results/phase1_results.json.

   STEPS (the same numbering as the page)
     1  read a, b, c, alpha, beta, gamma and the atoms
     2  lattice vectors A (rows) and metric tensor G = A A^T, volume sqrt(det G)
     3  is the lattice cubic?  find M with M G M^T = a_c^2 I
     4  centring from the atoms (I: +(1/2,1/2,1/2); F: + the three face centres)
     5  point group from the atoms (inversion, 3-fold, 4-fold, -4)
     6  structure factors F(hkl) = sum_j Z_j exp(2 pi i h.x_j); space-group type
     7  face families, spacings d, first allowed order n, d_eff = d/n
     8  BFDH distances R_f = d_eff,max / d_eff,f
     9  the shape: cut space by every plane n.x <= R, family by family
    10  which faces survive, and by how much the others miss
    11  measure: face areas, volume, area, sphericity, name

   No DOM access, so the same file runs under node for the tests. Shape
   description and naming reuse MORPH.describe and MORPH.name from
   mof_morphology.js, so this page and the Morphology page name shapes by
   one rule.
   ===================================================================== */
(function (global) {
  'use strict';

  var TOL = 0.02;                                   // Angstrom: "the same position"
  var Z = { H: 1, C: 6, N: 7, O: 8, Zn: 30, Cu: 29, Zr: 40, Mg: 12, Co: 27, Ni: 28, Fe: 26, Cr: 24, Al: 13, Cd: 48, Mn: 25, Ti: 22, V: 23, Sc: 21, In: 49, Ga: 31, Ca: 20, S: 16, P: 15, F: 9, Cl: 17, Br: 35, Si: 14, B: 5 };

  // ---- small linear algebra --------------------------------------------------
  function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
  function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
  function add(a, b) { return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]; }
  function scale(a, s) { return [a[0] * s, a[1] * s, a[2] * s]; }
  function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
  function norm(a) { return Math.sqrt(dot(a, a)); }
  function unit(a) { return scale(a, 1 / norm(a)); }
  function det3(m) { return dot(m[0], cross(m[1], m[2])); }
  function matmul(A, B) {
    var C = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
    for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) for (var k = 0; k < 3; k++) C[i][j] += A[i][k] * B[k][j];
    return C;
  }
  function transpose(A) { return [[A[0][0], A[1][0], A[2][0]], [A[0][1], A[1][1], A[2][1]], [A[0][2], A[1][2], A[2][2]]]; }
  function inv3(A) {
    var d = det3(A), c0 = cross(A[1], A[2]), c1 = cross(A[2], A[0]), c2 = cross(A[0], A[1]);
    // inverse = (columns c0 c1 c2) / det
    return [[c0[0] / d, c1[0] / d, c2[0] / d], [c0[1] / d, c1[1] / d, c2[1] / d], [c0[2] / d, c1[2] / d, c2[2] / d]];
  }
  function vecmat(v, M) {                            // row vector times matrix
    return [v[0] * M[0][0] + v[1] * M[1][0] + v[2] * M[2][0],
            v[0] * M[0][1] + v[1] * M[1][1] + v[2] * M[2][1],
            v[0] * M[0][2] + v[1] * M[1][2] + v[2] * M[2][2]];
  }
  function matvec(M, v) { return [dot(M[0], v), dot(M[1], v), dot(M[2], v)]; }
  function mod1(x) { return x - Math.floor(x); }
  function wrap(x) { return x - Math.round(x); }   // to [-1/2, 1/2]
  function gcd(a, b) { a = Math.abs(a); b = Math.abs(b); while (b) { var t = b; b = a % b; a = t; } return a; }

  // ---- 1. read the CIF ---------------------------------------------------------
  function parseCIF(text) {
    function num(key) {
      var m = new RegExp('^\\s*' + key + '\\s+([-0-9.]+)', 'm').exec(text);
      if (!m) throw new Error('the CIF has no ' + key);
      return parseFloat(m[1]);
    }
    var cell = ['_cell_length_a', '_cell_length_b', '_cell_length_c', '_cell_angle_alpha', '_cell_angle_beta', '_cell_angle_gamma'].map(num);
    var lines = text.split(/\r?\n/), atoms = [], i = 0, cellLines = [];
    lines.forEach(function (l) { if (/^\s*_cell_(length|angle)_/.test(l)) cellLines.push(l.trim().replace(/\s+/g, ' ')); });
    while (i < lines.length) {
      if (lines[i].trim() === 'loop_') {
        var j = i + 1, cols = [];
        while (j < lines.length && /^\s*_/.test(lines[j])) { cols.push(lines[j].trim().split(/\s+/)[0]); j++; }
        var ix = cols.indexOf('_atom_site_fract_x');
        if (ix >= 0) {
          var iy = cols.indexOf('_atom_site_fract_y'), iz = cols.indexOf('_atom_site_fract_z');
          var it = cols.indexOf('_atom_site_type_symbol'); if (it < 0) it = cols.indexOf('_atom_site_label');
          var io = cols.indexOf('_atom_site_occupancy');
          while (j < lines.length && lines[j].trim() && !/^\s*(_|loop_|data_)/.test(lines[j])) {
            var p = lines[j].trim().split(/\s+/);
            if (p.length >= cols.length) {
              var em = /[A-Z][a-z]?/.exec(p[it] || '');
              if (!em) { j++; continue; }                  // a row that does not name an element: skip it
              var el = em[0];
              var f = function (s) { return parseFloat(s.replace(/\(.*\)$/, '')); };
              atoms.push({ el: el, x: [f(p[ix]), f(p[iy]), f(p[iz])], label: p[cols.indexOf('_atom_site_label')] || el,
                           occ: io >= 0 ? f(p[io]) : 1, line: lines[j].trim().replace(/\s+/g, ' ') });
            }
            j++;
          }
        }
        i = j;
      } else i++;
    }
    if (!atoms.length) throw new Error('no atom loop with _atom_site_fract_x was found');
    var sg = /^\s*_symmetry_space_group_name_H-M\s+'([^']*)'/m.exec(text) || /^\s*_space_group_name_H-M_alt\s+'([^']*)'/m.exec(text);
    var comp = {};
    atoms.forEach(function (a) { comp[a.el] = (comp[a.el] || 0) + 1; });
    return { cell: cell, atoms: atoms, cellLines: cellLines, spaceGroupInFile: sg ? sg[1].trim() : null, composition: comp };
  }

  // ---- 2. lattice vectors and metric tensor ------------------------------------
  function latticeVectors(cell) {
    var a = cell[0], b = cell[1], c = cell[2], r = Math.PI / 180;
    var al = cell[3] * r, be = cell[4] * r, ga = cell[5] * r;
    var cx = c * Math.cos(be), cy = c * (Math.cos(al) - Math.cos(be) * Math.cos(ga)) / Math.sin(ga);
    var cz = Math.sqrt(Math.max(c * c - cx * cx - cy * cy, 0));
    return [[a, 0, 0], [b * Math.cos(ga), b * Math.sin(ga), 0], [cx, cy, cz]];
  }
  function metric(A) { return matmul(A, transpose(A)); }

  // ---- 3. conventional cubic cell ----------------------------------------------
  var M_CANDIDATES = [
    { key: 'P', M: [[1, 0, 0], [0, 1, 0], [0, 0, 1]], why: 'the file already holds a cube' },
    { key: 'F', M: [[-1, 1, 1], [1, -1, 1], [1, 1, -1]], why: 'a 60° rhombohedral cell is the primitive cell of a face-centred cube' },
    { key: 'I', M: [[0, 1, 1], [1, 0, 1], [1, 1, 0]], why: 'a 109.47° rhombohedral cell is the primitive cell of a body-centred cube' }
  ];
  function conventional(G) {
    for (var c = 0; c < M_CANDIDATES.length; c++) {
      var M = M_CANDIDATES[c].M, Gc = matmul(matmul(M, G), transpose(M));
      var a2 = (Gc[0][0] + Gc[1][1] + Gc[2][2]) / 3, dev = 0;
      for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) dev = Math.max(dev, Math.abs(Gc[i][j] - (i === j ? a2 : 0)));
      if (dev < 2e-4 * a2) return { key: M_CANDIDATES[c].key, M: M, Gc: Gc, a: Math.sqrt(a2), deviation: dev / a2, why: M_CANDIDATES[c].why };
    }
    return null;
  }

  // atoms in conventional fractional coordinates, every lattice copy included
  function toConventional(A, atoms, M) {
    var Ac = matmul(M, A), AcI = inv3(Ac), els = [], X = [];
    atoms.forEach(function (at) {
      var cart = vecmat(at.x, A), seen = [];
      for (var s0 = -1; s0 <= 1; s0++) for (var s1 = -1; s1 <= 1; s1++) for (var s2 = -1; s2 <= 1; s2++) {
        var c = add(cart, vecmat([s0, s1, s2], A)), y = vecmat(c, AcI);
        y = [mod1(y[0]), mod1(y[1]), mod1(y[2])];
        var dup = seen.some(function (z) { return norm(vecmat([wrap(y[0] - z[0]), wrap(y[1] - z[1]), wrap(y[2] - z[2])], Ac)) < TOL; });
        if (!dup) seen.push(y);
      }
      seen.forEach(function (y) { els.push(at.el); X.push(y); });
    });
    return { Ac: Ac, els: els, X: X };
  }

  // ---- 4 and 5. symmetry by direct search --------------------------------------
  function byElement(C, skipH) {
    var by = {};
    C.els.forEach(function (e, i) { if (skipH && e === 'H') return; (by[e] = by[e] || []).push(C.X[i]); });
    return by;
  }
  // how many atoms x have an atom of the same element at R x + t (mod 1)?
  function mapsOnto(C, by, R, t, skipH, stopAtFirstMiss) {
    var good = 0, tot = 0, Ac = C.Ac, tol2 = TOL * TOL;
    for (var i = 0; i < C.els.length; i++) {
      var e = C.els[i];
      if (skipH && e === 'H') continue;
      tot++;
      var y = add(matvec(R, C.X[i]), t), list = by[e], hit = false;
      for (var k = 0; k < list.length && !hit; k++) {
        var d = [wrap(list[k][0] - y[0]), wrap(list[k][1] - y[1]), wrap(list[k][2] - y[2])];
        var c = vecmat(d, Ac);
        if (c[0] * c[0] + c[1] * c[1] + c[2] * c[2] < tol2) hit = true;
      }
      if (hit) good++; else if (stopAtFirstMiss) return { mapped: -1, of: -1 };
    }
    return { mapped: good, of: tot };
  }
  var IDENTITY = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  function centringTest(C, skipH) {
    var by = byElement(C, skipH);
    return {
      I: [[0.5, 0.5, 0.5]].map(function (t) { return { t: t, r: mapsOnto(C, by, IDENTITY, t, skipH) }; }),
      F: [[0, 0.5, 0.5], [0.5, 0, 0.5], [0.5, 0.5, 0]].map(function (t) { return { t: t, r: mapsOnto(C, by, IDENTITY, t, skipH) }; })
    };
  }
  var OPS = [
    { key: 'inversion', label: 'inversion', R: [[-1, 0, 0], [0, -1, 0], [0, 0, -1]], text: '(x, y, z) → (−x, −y, −z)' },
    { key: '3-fold [111]', label: '3-fold axis along [111]', R: [[0, 0, 1], [1, 0, 0], [0, 1, 0]], text: '(x, y, z) → (z, x, y)' },
    { key: '4-fold [001]', label: '4-fold axis along [001]', R: [[0, -1, 0], [1, 0, 0], [0, 0, 1]], text: '(x, y, z) → (−y, x, z)' },
    { key: '-4 [001]', label: '4-fold rotoinversion along [001]', R: [[0, 1, 0], [-1, 0, 0], [0, 0, -1]], text: '(x, y, z) → (y, −x, −z)' }
  ];
  // is there a translation t with (R, t) a symmetry? Try every t that sends the first
  // atom of the rarest element onto an atom of the same element.
  function searchOp(C, R, skipH) {
    var by = byElement(C, skipH), rare = null;
    Object.keys(by).forEach(function (e) {
      if (rare === null || by[e].length < by[rare].length || (by[e].length === by[rare].length && e < rare)) rare = e;
    });
    var x0 = by[rare][0], Rx0 = matvec(R, x0), best = { mapped: 0, of: 1, t: null };
    for (var k = 0; k < by[rare].length; k++) {
      var y = by[rare][k], t = [mod1(y[0] - Rx0[0]), mod1(y[1] - Rx0[1]), mod1(y[2] - Rx0[2])];
      var quick = mapsOnto(C, by, R, t, skipH, true);
      if (quick.mapped >= 0) return { mapped: quick.mapped, of: quick.of, t: t };
    }
    // no t works: report the best partial count, for the table
    for (var k2 = 0; k2 < by[rare].length; k2++) {
      var y2 = by[rare][k2], t2 = [mod1(y2[0] - Rx0[0]), mod1(y2[1] - Rx0[1]), mod1(y2[2] - Rx0[2])];
      var full = mapsOnto(C, by, R, t2, skipH, false);
      if (full.mapped > best.mapped) best = { mapped: full.mapped, of: full.of, t: t2 };
    }
    return best;
  }
  function pointGroup(f) {
    if (!f['3-fold [111]']) return 'not cubic';
    if (f.inversion && f['4-fold [001]']) return 'm-3m';
    if (f.inversion) return 'm-3';
    if (f['4-fold [001]']) return '432';
    if (f['-4 [001]']) return '-43m';
    return '23';
  }

  // ---- 6. structure factors -------------------------------------------------------
  function structureFactor(els, X, h) {
    var re = 0, im = 0, sum = 0;
    for (var i = 0; i < els.length; i++) {
      var w = Z[els[i]] || 6, ph = 2 * Math.PI * dot(h, X[i]);
      re += w * Math.cos(ph); im += w * Math.sin(ph); sum += w;
    }
    var mag = Math.sqrt(re * re + im * im);
    return { re: re, im: im, abs: mag, sumZ: sum, ratio: mag / sum };
  }
  // the centring sum S(h) = sum over the centring vectors t of exp(2 pi i h.t)
  function centringSum(h, centring) {
    var T = centring === 'F' ? [[0, 0, 0], [0, .5, .5], [.5, 0, .5], [.5, .5, 0]] : centring === 'I' ? [[0, 0, 0], [.5, .5, .5]] : [[0, 0, 0]];
    var terms = T.map(function (t) { return Math.round(Math.cos(2 * Math.PI * dot(h, t))); });
    return { terms: terms, value: terms.reduce(function (s, x) { return s + x; }, 0), T: T };
  }
  // space-group types with this centring and point group, and the one reflection that tells each
  // glide apart from the plain group (International Tables, reflection conditions)
  var SG_CANDIDATES = {
    'F m-3m': [{ sg: 'Fm-3m', n: 225 }, { sg: 'Fm-3c', n: 226, test: [1, 1, 1], cond: 'hhl: h, l = 2n, so (111) would vanish' },
               { sg: 'Fd-3m', n: 227, test: [2, 0, 0], cond: '0kl: k + l = 4n, so (200) would vanish' },
               { sg: 'Fd-3c', n: 228, test: [2, 0, 0], cond: '0kl: k + l = 4n, so (200) would vanish' }],
    'F -43m': [{ sg: 'F-43m', n: 216 }, { sg: 'F-43c', n: 219, test: [1, 1, 1], cond: 'hhl: h, l = 2n, so (111) would vanish' }],
    'I -43m': [{ sg: 'I-43m', n: 217 }, { sg: 'I-43d', n: 220, test: [1, 1, 0], cond: 'hhl: 2h + l = 4n, so (110) would vanish' }],
    'I m-3m': [{ sg: 'Im-3m', n: 229 }, { sg: 'Ia-3d', n: 230, test: [1, 1, 0], cond: 'hhl: 2h + l = 4n, so (110) would vanish' }],
    'P m-3m': [{ sg: 'Pm-3m', n: 221 }, { sg: 'Pn-3n', n: 222, test: [1, 0, 0], cond: '0kl: k + l = 2n, so (100) would vanish' },
               { sg: 'Pm-3n', n: 223, test: [1, 1, 1], cond: 'hhl: l = 2n, so (111) would vanish' },
               { sg: 'Pn-3m', n: 224, test: [1, 0, 0], cond: '0kl: k + l = 2n, so (100) would vanish' }]
  };
  function spaceGroupType(centring, pg, sfOf) {
    var list = SG_CANDIDATES[centring + ' ' + pg];
    if (!list) return { sg: null, reasons: [] };
    var reasons = [];
    for (var i = 1; i < list.length; i++) {
      var F = sfOf(list[i].test);
      reasons.push({ sg: list[i].sg, n: list[i].n, cond: list[i].cond, hkl: list[i].test, ratio: F.ratio, ruledOut: F.ratio > 1e-3 });
    }
    var alive = reasons.every(function (r) { return r.ruledOut; });
    return { sg: alive ? list[0].sg : null, n: alive ? list[0].n : null, reasons: reasons, plain: list[0].sg };
  }

  // ---- 7. face families -------------------------------------------------------------
  function allowed(h, centring) {
    if (centring === 'F') { var p = h.map(function (x) { return Math.abs(x) % 2; }); return p[0] === p[1] && p[1] === p[2]; }
    if (centring === 'I') return Math.abs(h[0] + h[1] + h[2]) % 2 === 0;
    return true;
  }
  function signedPerms(hkl) {
    var perms = [[0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0], [2, 0, 1], [2, 1, 0]], seen = {}, out = [];
    perms.forEach(function (p) {
      for (var s = 0; s < 8; s++) {
        var v = [hkl[p[0]] * (s & 1 ? -1 : 1), hkl[p[1]] * (s & 2 ? -1 : 1), hkl[p[2]] * (s & 4 ? -1 : 1)];
        var k = v.join(','); if (!seen[k]) { seen[k] = 1; out.push(v); }
      }
    });
    return out;
  }
  // every primitive direction with |indices| <= maxIndex, grouped into symmetry families
  function families(centring, pointGroup, a, maxIndex) {
    maxIndex = maxIndex || 6;
    var fam = {};
    for (var h = 0; h <= maxIndex; h++) for (var k = 0; k <= h; k++) for (var l = 0; l <= k; l++) {
      if (!h || gcd(gcd(h, k), l) !== 1) continue;
      var base = [h, k, l], full = signedPerms(base), split = pointGroup === '-43m' && h && k && l;
      var n = 1; while (!allowed(scale(base, n), centring)) n++;
      var d = a / Math.sqrt(h * h + k * k + l * l);
      var halves = split ? ['+', '-'] : [''];
      halves.forEach(function (half) {
        var members = full.filter(function (v) {
          if (!half) return true;
          return (v[0] * v[1] * v[2] > 0) === (half === '+');
        });
        var label = '{' + h + k + l + '}' + half;
        fam[label] = { label: label, base: '{' + h + k + l + '}', hkl: base, half: half || null, members: members,
                       multiplicity: members.length, d: d, n: n, dEff: d / n, sumSq: h * h + k * k + l * l };
      });
    }
    var out = Object.keys(fam).map(function (k) { return fam[k]; });
    out.sort(function (x, y) { return (y.dEff - x.dEff) || (y.multiplicity - x.multiplicity) || (x.label < y.label ? 1 : -1); });
    return out;
  }

  // ---- 9. the shape by cutting --------------------------------------------------------
  // A convex polyhedron as a list of faces {tag, n (unit), d, pts}. Cutting by the half-space
  // n.x <= d keeps the part of each face on the inside, and closes the hole with a new face.
  function box(L) {
    var out = [];
    [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]].forEach(function (n) {
      var u = n[0] ? [0, 1, 0] : [1, 0, 0], w = cross(n, u), c = scale(n, L);
      out.push({ tag: 'bound', n: n, d: L, pts: [add(c, add(scale(u, L), scale(w, L))), add(c, add(scale(u, -L), scale(w, L))),
                                                  add(c, add(scale(u, -L), scale(w, -L))), add(c, add(scale(u, L), scale(w, -L)))] });
    });
    return out;
  }
  function orderAround(pts, n) {
    var c = scale(pts.reduce(add, [0, 0, 0]), 1 / pts.length), u = unit(sub(pts[0], c)), w = cross(n, u);
    return pts.slice().sort(function (A, B) {
      return Math.atan2(dot(sub(A, c), w), dot(sub(A, c), u)) - Math.atan2(dot(sub(B, c), w), dot(sub(B, c), u));
    });
  }
  function dedupe(pts) {
    var out = [];
    pts.forEach(function (p) { if (!out.some(function (q) { return norm(sub(p, q)) < 1e-9; })) out.push(p); });
    return out;
  }
  function cut(faces, plane) {
    var n = plane.n, d = plane.d, eps = 1e-10, cutPts = [], out = [];
    var anyOutside = faces.some(function (f) { return f.pts.some(function (p) { return dot(n, p) > d + eps; }); });
    if (!anyOutside) return { faces: faces, changed: false };
    faces.forEach(function (f) {
      var res = [], P = f.pts;
      for (var i = 0; i < P.length; i++) {
        var A = P[i], B = P[(i + 1) % P.length], sa = dot(n, A) - d, sb = dot(n, B) - d;
        if (sa <= eps) res.push(A);
        if (Math.abs(sa) <= eps) cutPts.push(A);
        if ((sa < -eps && sb > eps) || (sa > eps && sb < -eps)) {
          var x = add(A, scale(sub(B, A), sa / (sa - sb)));
          res.push(x); cutPts.push(x);
        }
      }
      res = dedupe(res);
      if (res.length >= 3) out.push({ tag: f.tag, n: f.n, d: f.d, pts: res, hkl: f.hkl });
    });
    cutPts = dedupe(cutPts);
    if (cutPts.length >= 3) out.push({ tag: plane.tag, n: n, d: d, pts: orderAround(cutPts, n), hkl: plane.hkl });
    return { faces: out, changed: true };
  }
  function polygonArea(pts) {
    var s = [0, 0, 0];
    for (var t = 1; t + 1 < pts.length; t++) s = add(s, cross(sub(pts[t], pts[0]), sub(pts[t + 1], pts[0])));
    return 0.5 * norm(s);
  }
  // build the shape family by family; keep a snapshot after each plane for the animation
  function build(fams, rates, opts) {
    opts = opts || {};
    var faces = box(opts.L || 40), stages = [], planes = [];
    fams.forEach(function (F) {
      var R = rates[F.label];
      F.members.forEach(function (h) { planes.push({ n: unit(h), d: R, tag: F.label, hkl: h, family: F }); });
    });
    // nearest family first: that order makes the first family's own shape the first picture
    planes.sort(function (p, q) { return (p.d - q.d) || (p.tag < q.tag ? -1 : p.tag > q.tag ? 1 : 0); });
    var snaps = [];
    planes.forEach(function (p, i) {
      var r = cut(faces, p);
      faces = r.faces;
      if (opts.snapshots) snaps.push({ plane: p, changed: r.changed, faces: faces });
    });
    var S = finish(faces);
    S.planes = planes; S.snapshots = snaps;
    return S;
  }
  function finish(faces) {
    var V = [];
    faces.forEach(function (f) { f.poly = f.pts; f.area = polygonArea(f.pts); f.pts.forEach(function (p) { if (!V.some(function (q) { return norm(sub(p, q)) < 1e-7; })) V.push(p); }); });
    var S = { faces: faces, V: V, bounded: !faces.some(function (f) { return f.tag === 'bound'; }) };
    if (S.bounded && global.MORPH) { S.info = global.MORPH.describe(S); S.name = global.MORPH.name(S); }
    return S;
  }
  // the support function h_P(n) = max over vertices of n.v: the farthest the shape reaches along n
  function support(S, n) { return S.V.reduce(function (m, v) { return Math.max(m, dot(n, v)); }, -Infinity); }

  // a worked vertex: the three planes through one vertex and Cramer's rule for it
  function workedVertex(S) {
    var best = null;
    S.V.forEach(function (v) {
      var on = S.faces.filter(function (f) { return Math.abs(dot(f.n, v) - f.d) < 1e-7; });
      if (on.length < 3) return;
      var tags = {}; on.forEach(function (f) { tags[f.tag] = 1; });
      var score = Object.keys(tags).length * 100 + (v[0] >= v[1] && v[1] >= v[2] && v[2] >= -1e-9 ? 10 : 0) + v[0];
      if (!best || score > best.score) best = { v: v, on: on, score: score };
    });
    if (!best) return null;
    // choose three planes with independent normals, preferring distinct families
    var on = best.on.slice().sort(function (a, b) { return a.tag < b.tag ? -1 : 1; }), pick = null;
    for (var i = 0; i < on.length && !pick; i++) for (var j = i + 1; j < on.length && !pick; j++) for (var k = j + 1; k < on.length && !pick; k++) {
      if (Math.abs(det3([on[i].n, on[j].n, on[k].n])) > 1e-6) pick = [on[i], on[j], on[k]];
    }
    var N = pick.map(function (f) { return f.hkl; }), r = pick.map(function (f) { return f.d * norm(f.hkl); });
    // h.x = R |h| for each plane: solve N x = r by Cramer's rule
    var D = det3(N), cols = [0, 1, 2].map(function (c) {
      var Mc = N.map(function (row, i) { return row.map(function (x, j) { return j === c ? r[i] : x; }); });
      return { M: Mc, det: det3(Mc) };
    });
    return { vertex: best.v, planes: pick, N: N, rhs: r, D: D, cols: cols, x: cols.map(function (c) { return c.det / D; }),
             nOn: best.on.length };
  }

  // ---- the whole chain ---------------------------------------------------------------------
  function run(text, opts) {
    opts = opts || {};
    var R = { steps: {} }, t0 = Date.now();
    var cif = parseCIF(text);
    // a CIF that lists only the asymmetric unit: the caller may pass the atoms expanded by the
    // file's symmetry operations (mof_general_shape.js does this), so every atom of the cell is used
    if (opts.atoms && opts.atoms.length > cif.atoms.length) {
      cif.listedAtoms = cif.atoms.length; cif.atoms = opts.atoms; cif.composition = {};
      cif.atoms.forEach(function (a) { cif.composition[a.el] = (cif.composition[a.el] || 0) + 1; });
    }
    R.cif = cif;
    var A = latticeVectors(cif.cell), G = metric(A), V = Math.sqrt(det3(G));
    R.A = A; R.G = G; R.volume = V;
    var conv = conventional(G);
    R.conv = conv;
    if (!conv) { R.stop = 'The lattice is not cubic (no transformation M gives M G Mᵀ = a²I), so the cubic steps on this page do not apply. The section "Any Lattice: Rods, Plates and Compact Crystals" near the top of the page handles this file.'; return R; }
    var C = toConventional(A, cif.atoms, conv.M);
    R.C = C; R.a = conv.a;
    R.pointsPerCell = Math.round(Math.abs(det3(conv.M)));
    // centring: from the lattice if the file is primitive, from the atoms otherwise
    R.centringTest = { withH: centringTest(C, false), withoutH: centringTest(C, true) };
    function passes(tst, key) { return tst[key].every(function (x) { return x.r.mapped === x.r.of; }); }
    var useH = passes(R.centringTest.withH, 'F') || passes(R.centringTest.withH, 'I') || !(passes(R.centringTest.withoutH, 'F') || passes(R.centringTest.withoutH, 'I'));
    var T = useH ? R.centringTest.withH : R.centringTest.withoutH;
    R.centring = passes(T, 'F') ? 'F' : passes(T, 'I') ? 'I' : 'P';
    // the point group: try with H; if a cubic group is found only without H, use that and say so
    var pg = { withH: {}, withoutH: {} };
    OPS.forEach(function (o) { pg.withH[o.key] = searchOp(C, o.R, false); pg.withoutH[o.key] = searchOp(C, o.R, true); });
    R.pgTest = pg;
    function found(tag) { var f = {}; OPS.forEach(function (o) { f[o.key] = pg[tag][o.key].mapped === pg[tag][o.key].of; }); return f; }
    var pgWith = pointGroup(found('withH')), pgWithout = pointGroup(found('withoutH'));
    var rank = { 'not cubic': 0, '23': 1, 'm-3': 2, '432': 2, '-43m': 2, 'm-3m': 3 };
    R.symmetryWithH = useH && rank[pgWith] >= rank[pgWithout];
    R.pointGroup = R.symmetryWithH ? pgWith : pgWithout;
    R.pointGroupWithH = pgWith; R.pointGroupWithoutH = pgWithout;
    if (!R.symmetryWithH && useH) {           // centring passed with H but the point group did not
      T = R.centringTest.withoutH;
      R.centring = passes(T, 'F') ? 'F' : passes(T, 'I') ? 'I' : 'P';
    }
    if (R.pointGroup === 'not cubic') { R.stop = 'The lattice is cubic but the atoms have no 3-fold axis, so the crystal is not cubic.'; return R; }
    // structure factors of the framework that carries the symmetry
    var els = [], X = [];
    C.els.forEach(function (e, i) { if (R.symmetryWithH || e !== 'H') { els.push(e); X.push(C.X[i]); } });
    R.framework = { els: els, X: X };
    var sfCache = {};
    function sfOf(h) { var k = h.join(','); return sfCache[k] || (sfCache[k] = structureFactor(els, X, h)); }
    R.sfOf = sfOf;
    R.sfTable = [[1, 0, 0], [2, 0, 0], [1, 1, 0], [2, 2, 0], [1, 1, 1], [2, 2, 2], [2, 1, 0], [4, 2, 0], [2, 1, 1], [4, 2, 2], [3, 1, 1], [3, 3, 1]].map(function (h) {
      var F = sfOf(h), S = centringSum(h, R.centring);
      return { h: h, F: F, S: S, allowed: allowed(h, R.centring) };
    });
    R.sg = spaceGroupType(R.centring, R.pointGroup, sfOf);
    // faces
    var fams = families(R.centring, R.pointGroup === 'm-3m' || R.pointGroup === 'm-3' ? 'm-3m' : R.pointGroup, conv.a, opts.maxIndex || 6);
    R.families = fams;
    var dmax = fams[0].dEff, rates = {};
    fams.forEach(function (F) { F.R = dmax / F.dEff; rates[F.label] = F.R; });
    R.dmax = dmax; R.rates = rates;
    R.shape = build(fams, rates, { snapshots: !!opts.snapshots });
    var S = R.shape, area = S.faces.reduce(function (s, f) { return s + f.area; }, 0);
    fams.forEach(function (F) {
      var fs = S.faces.filter(function (f) { return f.tag === F.label; });
      F.faceCount = fs.length;
      F.areaFraction = fs.reduce(function (s, f) { return s + f.area; }, 0) / area;
      F.reach = support(S, unit(F.hkl));
      F.present = F.areaFraction > 1e-9;
      // a face whose plane passes through a vertex or edge without cutting has zero area
      F.touches = !F.present && Math.abs(F.R - F.reach) < 1e-7;
    });
    R.totalArea = area;
    R.worked = workedVertex(S);
    R.ms = Date.now() - t0;
    return R;
  }

  var API = {
    TOL: TOL, Z: Z, parseCIF: parseCIF, latticeVectors: latticeVectors, metric: metric, conventional: conventional,
    toConventional: toConventional, centringTest: centringTest, OPS: OPS, searchOp: searchOp, pointGroup: pointGroup,
    structureFactor: structureFactor, centringSum: centringSum, spaceGroupType: spaceGroupType, allowed: allowed,
    families: families, box: box, cut: cut, build: build, finish: finish, support: support, polygonArea: polygonArea,
    workedVertex: workedVertex, run: run,
    la: { dot: dot, sub: sub, add: add, scale: scale, cross: cross, norm: norm, unit: unit, det3: det3, matmul: matmul,
          transpose: transpose, inv3: inv3, vecmat: vecmat, matvec: matvec }
  };
  global.CIFSHAPE = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : this);
