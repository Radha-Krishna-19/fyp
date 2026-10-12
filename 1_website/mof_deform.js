/* =====================================================================
   mof_deform.js - BFDH crystal shape for a unit cell whose edges a, b, c are changed.
   Same rule as 2_python/morphology/mofmorph/deform.py (orthogonal axes only):
     * allowed faces and their orders n depend only on the centring (fractional coordinates), Prop. 14
     * faces stay equivalent only if related by an operation that is still an isometry, Prop. 15:
       the cubic point group (m-3m, or -43m) restricted to the permutations of axes of EQUAL length
     * d_hkl = 1 / sqrt(h^2/a^2 + k^2/b^2 + l^2/c^2), d_eff = d / n, R proportional to 1 / d_eff, Prop. 16
   Uses MORPH.polytope / describe / name from mof_morphology.js.
   ===================================================================== */
(function (global) {
  'use strict';
  var M = global.MORPH || (typeof require !== 'undefined' ? require('./mof_morphology.js') : null);
  var PERMS = [[0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0], [2, 0, 1], [2, 1, 0]];
  function parity(p) { var s = 0; for (var i = 0; i < 3; i++) for (var j = i + 1; j < 3; j++) if (p[i] > p[j]) s++; return s % 2; }

  // point operations as {p: perm, s: signs}: h' [i] = s[i] * h[p[i]]
  function ops(pointGroup, lens, tol) {
    var out = [];
    PERMS.forEach(function (p) {
      for (var e = 0; e < 8; e++) {
        var s = [(e & 1) ? -1 : 1, (e & 2) ? -1 : 1, (e & 4) ? -1 : 1];
        var minus = (s[0] < 0) + (s[1] < 0) + (s[2] < 0);
        if (pointGroup === '-43m' && (minus % 2) !== 0) continue;           // Td: perms x even sign changes
        var ok = true;
        for (var i = 0; i < 3; i++) if (Math.abs(lens[p[i]] - lens[i]) > tol * lens[i]) ok = false;
        if (ok) out.push({ p: p, s: s });
      }
    });
    return out;
  }
  function act(op, h) { return [op.s[0] * h[op.p[0]], op.s[1] * h[op.p[1]], op.s[2] * h[op.p[2]]]; }
  function gcd(a, b) { a = Math.abs(a); b = Math.abs(b); while (b) { var t = a % b; a = b; b = t; } return a; }

  // all families up to max index, with d_eff; returns sorted list
  function families(centring, pointGroup, lens, maxIndex) {
    var O = ops(pointGroup, lens, 1e-9), seen = {}, fams = [];
    for (var h = -maxIndex; h <= maxIndex; h++) for (var k = -maxIndex; k <= maxIndex; k++) for (var l = -maxIndex; l <= maxIndex; l++) {
      if (!h && !k && !l) continue;
      if (gcd(gcd(h, k), l) !== 1) continue;
      var key = h + ',' + k + ',' + l;
      if (seen[key]) continue;
      var orbit = {}, members = [];
      O.forEach(function (op) { var v = act(op, [h, k, l]); var kk = v.join(','); if (!orbit[kk]) { orbit[kk] = 1; members.push(v); } });
      members.forEach(function (v) { seen[v.join(',')] = true; });
      var n = 1; while (!M.allowed([h * n, k * n, l * n], centring)) n++;
      var d = 1 / Math.sqrt(h * h / (lens[0] * lens[0]) + k * k / (lens[1] * lens[1]) + l * l / (lens[2] * lens[2]));
      fams.push({ hkl: [h, k, l], members: members, d: d, n: n, dEff: d / n });
    }
    fams.sort(function (a, b) { return (b.dEff - a.dEff) > 1e-12 ? 1 : (a.dEff - b.dEff) > 1e-12 ? -1 : b.members.length - a.members.length; });
    return fams;
  }

  // BFDH shape of the deformed cell. lens = [a, b, c]; the polytope is the intersection of the planes of the
  // nFam (default 40) families with largest d_eff, as in Python. Planes that do not cut the current polytope are
  // redundant, so they are added only when they do (exactly the same result, far fewer planes to intersect).
  function bfdhShape(centring, pointGroup, lens, nFam) {
    var fams = families(centring, pointGroup, lens, 6).slice(0, nFam || 40), dmax = fams[0].dEff;
    function planesOf(F) {
      var label = '{' + F.hkl.map(Math.abs).sort(function (x, y) { return y - x; }).join('') + '}';
      return F.members.map(function (v) {
        // Cartesian normal of plane (hkl) in an orthogonal cell: (h/a, k/b, l/c)
        var n = [v[0] / lens[0], v[1] / lens[1], v[2] / lens[2]], L = Math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]);
        return { n: n, u: [n[0] / L, n[1] / L, n[2] / L], d: dmax / F.dEff, tag: label };
      });
    }
    var planes = [], used = {};
    function isAxial(F) { var z = F.hkl.filter(function (x) { return x === 0; }).length; return z === 2 || F.members.some(function (m) { return m.filter(function (x) { return x === 0; }).length === 2; }); }
    fams.forEach(function (F, i) { if (i < 6 || isAxial(F)) { planes = planes.concat(planesOf(F)); used[i] = true; } });
    var S = M.polytope(planes);
    for (var pass = 0; pass < 6; pass++) {
      var add = [];
      fams.forEach(function (F, i) {
        if (used[i]) return;
        var P = planesOf(F), cuts = P.some(function (q) { return S.V.some(function (v) { return q.u[0] * v[0] + q.u[1] * v[1] + q.u[2] * v[2] > q.d * (1 + 1e-9); }); });
        if (cuts) { add = add.concat(P); used[i] = true; }
      });
      if (!add.length) break;
      planes = planes.concat(add); S = M.polytope(planes);
    }
    S.info = M.describe(S); S.name = M.name(S);
    S.families = fams.length; S.operations = ops(pointGroup, lens, 1e-9).length;
    return S;
  }

  // Zingg habit from the principal radii of gyration a >= b >= c. For an orthogonal cell every shape has the
  // sign-change symmetry, so its gyration tensor is diagonal and the radii are the square roots of the diagonal.
  function habit(S) {
    var G = S.info.gyration, w = [Math.sqrt(G[0][0]), Math.sqrt(G[1][1]), Math.sqrt(G[2][2])].sort(function (x, y) { return y - x; });
    var e = [0, 0, 0];
    S.V.forEach(function (v) { for (var i = 0; i < 3; i++) e[i] = Math.max(e[i], Math.abs(v[i])); });
    var ba = w[1] / w[0], cb = w[2] / w[1], r = 2 / 3;
    var type = (ba >= r && cb >= r) ? 'equant' : (ba < r && cb >= r) ? 'rod' : (ba >= r && cb < r) ? 'plate' : 'lath';
    return { type: type, ba: ba, cb: cb, halfWidths: e };
  }
  global.DEFORM = { ops: ops, families: families, bfdhShape: bfdhShape, habit: habit };
  if (typeof module !== 'undefined' && module.exports) module.exports = global.DEFORM;
})(typeof window !== 'undefined' ? window : this);
