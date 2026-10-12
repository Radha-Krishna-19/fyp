/* =====================================================================
   mof_morphology.js — crystal morphology from the unit cell, in the browser.

   This is the second, independent implementation of the Phase 1 morphology
   method. The first is the Python package in 2_python/morphology/. Both were
   written from the same specification (the primer, "From Unit Cell to
   Crystal Shape"); test_morphology.js checks that they agree.

   WHAT IT COMPUTES
   1. Which crystal faces a cubic lattice allows, and their effective
      spacings d_eff, from the centring rule (systematic absences).
   2. The crystal shape for a given set of face growth rates R_f: the convex
      polytope  P = { x : n_f . x <= R_f }.
   3. Descriptors of that shape: faces, vertices, volume, area, sphericity,
      the gyration tensor, asphericity kappa^2, and the face-normal order
      parameters Q_3, Q_4, Q_6.
   4. The graph attachment number c_hkl on the pcu and fcu node nets.

   The space group itself is found in Python with spglib; the browser takes
   the lattice centring (P, I or F) and the point group as input.
   No DOM access here, so the same file runs under node for the tests.
   ===================================================================== */
(function (global) {
  'use strict';

  var EPS = 1e-9;

  // ---- small vector helpers -------------------------------------------
  function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
  function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
  function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
  function norm(a) { return Math.sqrt(dot(a, a)); }
  function scale(a, s) { return [a[0] * s, a[1] * s, a[2] * s]; }
  function unit(a) { return scale(a, 1 / norm(a)); }
  function det3(a, b, c) { return dot(a, cross(b, c)); }

  // ---- 1. faces of a cubic crystal ------------------------------------
  // Systematic absences from centring alone (primer, Proposition 1 with R = I):
  //   F: h, k, l all even or all odd.   I: h + k + l even.   P: always allowed.
  function allowed(h, centring) {
    if (centring === 'F') {
      var p = [Math.abs(h[0]) % 2, Math.abs(h[1]) % 2, Math.abs(h[2]) % 2];
      return p[0] === p[1] && p[1] === p[2];
    }
    if (centring === 'I') return (Math.abs(h[0] + h[1] + h[2]) % 2) === 0;
    return true;
  }

  // Effective spacing of the primitive direction hkl in a cubic cell of edge a:
  // the first allowed reflection n*(hkl) sets d_eff = d_hkl / n.
  function dEff(hkl, centring, a) {
    var n = 1;
    while (!allowed(scale(hkl, n), centring)) n++;
    var d = a / Math.sqrt(dot(hkl, hkl));
    return { d: d, n: n, dEff: d / n };
  }

  // All members of a cubic face family. pointGroup 'm-3m' gives the full
  // set (signed permutations). '-43m' (no inversion) splits families with no
  // zero index into two halves, told apart by the sign of h*k*l.
  function members(hkl, pointGroup, half) {
    var seen = {}, out = [];
    var perms = [[0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0], [2, 0, 1], [2, 1, 0]];
    perms.forEach(function (p) {
      for (var s = 0; s < 8; s++) {
        var v = [hkl[p[0]] * ((s & 1) ? -1 : 1), hkl[p[1]] * ((s & 2) ? -1 : 1), hkl[p[2]] * ((s & 4) ? -1 : 1)];
        var key = v.join(',');
        if (seen[key]) continue;
        seen[key] = true;
        if (pointGroup === '-43m' && v[0] && v[1] && v[2] && half) {
          var sign = v[0] * v[1] * v[2] > 0 ? '+' : '-';
          if (sign !== half) continue;
        }
        out.push(v);
      }
    });
    return out;
  }

  function splits(hkl, pointGroup) { return pointGroup === '-43m' && hkl[0] && hkl[1] && hkl[2]; }

  // Family labels used everywhere: '{100}', '{110}', '{111}', and in -43m
  // the halves '{111}+' and '{111}-'.
  function familyList(pointGroup, families) {
    var out = [];
    (families || [[1, 0, 0], [1, 1, 0], [1, 1, 1]]).forEach(function (f) {
      var base = '{' + f.join('') + '}';
      if (splits(f, pointGroup)) {
        out.push({ label: base + '+', base: base, hkl: f, half: '+' });
        out.push({ label: base + '-', base: base, hkl: f, half: '-' });
      } else out.push({ label: base, base: base, hkl: f, half: null });
    });
    return out;
  }

  // ---- 2. the polytope -------------------------------------------------
  // planes: [{n: unit normal, d: distance > 0, tag: family label}]
  function polytope(planes) {
    var P = planes.map(function (p) { return { n: unit(p.n), d: p.d, tag: p.tag }; });
    var m = P.length, V = [];
    for (var i = 0; i < m; i++) for (var j = i + 1; j < m; j++) for (var k = j + 1; k < m; k++) {
      var a = P[i].n, b = P[j].n, c = P[k].n, D = det3(a, b, c);
      if (Math.abs(D) < 1e-10) continue;
      // Cramer's rule: x = (d_i (b x c) + d_j (c x a) + d_k (a x b)) / det
      var x = scale(cross(b, c), P[i].d);
      x = [x[0] + cross(c, a)[0] * P[j].d + cross(a, b)[0] * P[k].d,
           x[1] + cross(c, a)[1] * P[j].d + cross(a, b)[1] * P[k].d,
           x[2] + cross(c, a)[2] * P[j].d + cross(a, b)[2] * P[k].d];
      x = scale(x, 1 / D);
      var inside = true;
      for (var q = 0; q < m && inside; q++) if (dot(P[q].n, x) > P[q].d + 1e-7) inside = false;
      if (!inside) continue;
      var dup = false;
      for (var r = 0; r < V.length && !dup; r++) if (norm(sub(V[r], x)) < 1e-7) dup = true;
      if (!dup) V.push(x);
    }
    // faces: planes that touch at least three vertices
    var faces = [];
    P.forEach(function (p) {
      var on = V.filter(function (v) { return Math.abs(dot(p.n, v) - p.d) < 1e-7; });
      if (on.length < 3) return;
      var c = scale(on.reduce(function (s, v) { return [s[0] + v[0], s[1] + v[1], s[2] + v[2]]; }, [0, 0, 0]), 1 / on.length);
      var u = unit(sub(on[0], c)), w = cross(p.n, u);
      on.sort(function (A, B) {
        return Math.atan2(dot(sub(A, c), w), dot(sub(A, c), u)) - Math.atan2(dot(sub(B, c), w), dot(sub(B, c), u));
      });
      var area = 0;
      for (var t = 1; t + 1 < on.length; t++) area += 0.5 * norm(cross(sub(on[t], on[0]), sub(on[t + 1], on[0])));
      faces.push({ tag: p.tag, n: p.n, d: p.d, poly: on, area: area });
    });
    return { V: V, faces: faces };
  }

  // ---- 3. descriptors ----------------------------------------------------
  function legendre(l, x) {
    var p0 = 1, p1 = x;
    if (l === 0) return 1;
    for (var n = 2; n <= l; n++) { var p2 = ((2 * n - 1) * x * p1 - (n - 1) * p0) / n; p0 = p1; p1 = p2; }
    return p1;
  }

  function describe(S) {
    var area = 0, vol = 0, M2 = [[0, 0, 0], [0, 0, 0], [0, 0, 0]], m1 = [0, 0, 0];
    S.faces.forEach(function (f) {
      area += f.area;
      vol += f.area * f.d / 3;                       // pyramid from the origin
      // exact second moment: fan tetrahedra (origin, v0, vt, vt+1)
      for (var t = 1; t + 1 < f.poly.length; t++) {
        var T = [[0, 0, 0], f.poly[0], f.poly[t], f.poly[t + 1]];
        var tv = Math.abs(det3(T[1], T[2], T[3])) / 6;
        var Ssum = [0, 0, 0];
        T.forEach(function (v) { for (var i = 0; i < 3; i++) Ssum[i] += v[i]; });
        for (var i = 0; i < 3; i++) {
          m1[i] += tv * Ssum[i] / 4;
          for (var j = 0; j < 3; j++) {
            var s = 0;
            T.forEach(function (v) { s += v[i] * v[j]; });
            M2[i][j] += tv / 20 * (s + Ssum[i] * Ssum[j]);
          }
        }
      }
    });
    var com = scale(m1, 1 / vol), G = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
    for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) G[i][j] = M2[i][j] / vol - com[i] * com[j];
    var lam = eig3(G);
    var tr = lam[0] + lam[1] + lam[2];
    var kappa2 = 1.5 * (lam[0] * lam[0] + lam[1] * lam[1] + lam[2] * lam[2]) / (tr * tr) - 0.5;
    // Q_l by the spherical-harmonic addition theorem:
    //   Q_l^2 = sum_ij w_i w_j P_l(n_i . n_j),  w = face area fraction
    var w = S.faces.map(function (f) { return f.area / area; });
    function Q(l) {
      var s = 0;
      for (var a = 0; a < S.faces.length; a++) for (var b = 0; b < S.faces.length; b++)
        s += w[a] * w[b] * legendre(l, Math.max(-1, Math.min(1, dot(S.faces[a].n, S.faces[b].n))));
      return Math.sqrt(Math.max(0, s));
    }
    var frac = {};
    S.faces.forEach(function (f, k) { frac[f.tag] = (frac[f.tag] || 0) + w[k]; });
    return {
      faces: S.faces.length, vertices: S.V.length, volume: vol, area: area,
      sphericity: Math.pow(Math.PI, 1 / 3) * Math.pow(6 * vol, 2 / 3) / area,
      kappa2: Math.max(0, kappa2), aspect: Math.sqrt(lam[0] / lam[2]),
      Q3: Q(3), Q4: Q(4), Q6: Q(6), fraction: frac, gyration: G
    };
  }

  // eigenvalues of a symmetric 3x3 matrix (closed form), descending
  function eig3(A) {
    var p1 = A[0][1] * A[0][1] + A[0][2] * A[0][2] + A[1][2] * A[1][2];
    var q = (A[0][0] + A[1][1] + A[2][2]) / 3;
    if (p1 < 1e-30) return [A[0][0], A[1][1], A[2][2]].sort(function (x, y) { return y - x; });
    var p2 = Math.pow(A[0][0] - q, 2) + Math.pow(A[1][1] - q, 2) + Math.pow(A[2][2] - q, 2) + 2 * p1;
    var p = Math.sqrt(p2 / 6), B = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
    for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) B[i][j] = (A[i][j] - (i === j ? q : 0)) / p;
    var r = det3(B[0], B[1], B[2]) / 2, phi;
    if (r <= -1) phi = Math.PI / 3; else if (r >= 1) phi = 0; else phi = Math.acos(r) / 3;
    var e1 = q + 2 * p * Math.cos(phi), e3 = q + 2 * p * Math.cos(phi + 2 * Math.PI / 3);
    return [e1, 3 * q - e1 - e3, e3];
  }

  // ---- naming --------------------------------------------------------------
  function name(S) {
    var fr = {}, cnt = {};
    S.faces.forEach(function (f) { fr[f.tag] = (fr[f.tag] || 0) + f.area; cnt[f.tag] = (cnt[f.tag] || 0) + 1; });
    var tot = 0, k; for (k in fr) tot += fr[k];
    var keys = Object.keys(fr).filter(function (t) { return fr[t] / tot > 1e-9; });
    // named by face SHAPE, not by which family has more area: a {111} face that is a
    // triangle means the corners of a cube were cut (truncated cube); a hexagon means
    // the corners of an octahedron were cut (truncated octahedron)
    function corners(tagBase) {
      var c = 0;
      S.faces.forEach(function (f) { if (f.tag.replace(/[+-]$/, '') === tagBase) c = Math.max(c, f.poly.length); });
      return c;
    }
    var has = function (t) { return keys.indexOf(t) >= 0; };
    var plus = (fr['{111}+'] || 0) / tot, minus = (fr['{111}-'] || 0) / tot;
    if (keys.length === 1 && (has('{111}+') || has('{111}-')) && S.faces.length === 4) return 'tetrahedron';
    var tetra = (has('{111}+') || has('{111}-')) && Math.abs(plus - minus) > 0.02;
    if (tetra && keys.every(function (t) { return t === '{111}+' || t === '{111}-'; })) return 'truncated tetrahedron';
    // merge the halves and name the centrosymmetric shape
    var base = {}, vcount = S.V.length;
    keys.forEach(function (t) { var b = t.replace(/[+-]$/, ''); base[b] = (base[b] || 0) + fr[t] / tot; });
    var bk = Object.keys(base).sort().join(' ');
    var n;
    if (bk === '{100}') n = 'cube';
    else if (bk === '{111}') n = 'octahedron';
    else if (bk === '{110}') n = 'rhombic dodecahedron';
    else if (bk === '{100} {111}') n = vcount === 12 ? 'cuboctahedron' : (corners('{111}') >= 6 ? 'truncated octahedron' : 'truncated cube');
    // {100}+{110} is one combinatorial type throughout (6 squares, 12 hexagons, also called
    // a chamfered cube), so here the larger family names it
    else if (bk === '{100} {110}') n = base['{110}'] > base['{100}'] ? 'truncated rhombic dodecahedron' : 'chamfered cube';
    else if (bk === '{100} {110} {111}') n = 'rhombicuboctahedron-like';
    else n = Object.keys(base).sort().join(' + ');
    return tetra ? 'tetrahedral ' + n : n;
  }

  // ---- shape from rates -----------------------------------------------------
  // rates: {'{100}': 1, '{111}': 0.8, ...}; a half label falls back to its base.
  function shape(rates, pointGroup) {
    var planes = [];
    familyList(pointGroup).forEach(function (F) {
      var r = rates[F.label] !== undefined ? rates[F.label] : rates[F.base];
      if (r === undefined || r === null) return;
      members(F.hkl, pointGroup, F.half).forEach(function (v) { planes.push({ n: v, d: r, tag: F.label }); });
    });
    var S = polytope(planes);
    S.info = describe(S);
    S.name = name(S);
    return S;
  }

  // BFDH rates for a cubic lattice: R proportional to 1/d_eff, leading face at 1.
  function bfdhRates(centring, a, pointGroup) {
    var fams = familyList(pointGroup), best = 0, out = {};
    fams.forEach(function (F) { F.e = dEff(F.hkl, centring, a); best = Math.max(best, F.e.dEff); });
    fams.forEach(function (F) { out[F.label] = best / F.e.dEff; });
    return out;
  }

  // ---- 4. graph attachment numbers -----------------------------------------
  // c_hkl = largest number of links a node in the next layer forms with the
  // crystal below a plane parallel to (hkl). Ideal node nets: pcu, fcu.
  function net(kind) {
    var P = [], R = 4;
    for (var x = -R; x <= R; x++) for (var y = -R; y <= R; y++) for (var z = -R; z <= R; z++) {
      if (kind === 'pcu') P.push([x, y, z]);
      else {
        [[0, 0, 0], [0, .5, .5], [.5, 0, .5], [.5, .5, 0]].forEach(function (o) { P.push([x + o[0], y + o[1], z + o[2]]); });
      }
    }
    return { P: P.filter(function (p) { return norm(p) < 3.5; }), nn: kind === 'pcu' ? 1 : Math.SQRT1_2 };
  }

  function attachmentNumber(kind, hkl) {
    var N = net(kind), n = unit(hkl);
    var crystal = N.P.filter(function (p) { return dot(p, n) <= 1e-9; });
    var next = N.P.filter(function (p) {
      var h = dot(p, n), lat = norm(sub(p, scale(n, h)));
      return h > 1e-9 && h <= 1.01 && lat < 1.5;
    });
    var best = 0;
    next.forEach(function (s) {
      var c = 0;
      crystal.forEach(function (q) { if (Math.abs(norm(sub(q, s)) - N.nn) < 1e-6) c++; });
      if (c > best) best = c;
    });
    return best;
  }

  function graphRates(kind, beta) {
    var out = {};
    [[1, 0, 0], [1, 1, 0], [1, 1, 1]].forEach(function (f) {
      out['{' + f.join('') + '}'] = Math.exp(beta * attachmentNumber(kind, f));
    });
    return out;
  }

  // ---- the four structures (input, from spglib in Python) -------------------
  var STRUCTURES = {
    'MOF-5':   { spacegroup: 'Fm-3m', number: 225, centring: 'F', pointGroup: 'm-3m', a: 25.866, net: 'pcu' },
    'HKUST-1': { spacegroup: 'Fm-3m', number: 225, centring: 'F', pointGroup: 'm-3m', a: 26.297, net: 'tbo' },
    'UiO-66':  { spacegroup: 'F-43m', number: 216, centring: 'F', pointGroup: '-43m', a: 20.518, net: 'fcu' },
    'ZIF-8':   { spacegroup: 'I-43m', number: 217, centring: 'I', pointGroup: '-43m', a: 16.991, net: 'sod' }
  };

  var API = {
    allowed: allowed, dEff: dEff, members: members, familyList: familyList,
    polytope: polytope, describe: describe, name: name, shape: shape,
    bfdhRates: bfdhRates, attachmentNumber: attachmentNumber, graphRates: graphRates,
    STRUCTURES: STRUCTURES
  };
  global.MORPH = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : this);
