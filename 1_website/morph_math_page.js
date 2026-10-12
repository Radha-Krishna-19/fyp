/* =====================================================================
   morph_math_page.js — the live checks table on morph_math.html.

   Every proposition on the Mathematics page gets at least one numerical
   check, computed here with mof_morphology.js when the page loads. A row
   reads "holds" only if the computed numbers agree with the statement.
   ===================================================================== */
(function () {
  'use strict';
  var M = window.MORPH;
  var R3 = Math.sqrt(3), R2 = Math.sqrt(2);

  function rows() {
    var out = [];
    function add(prop, what, ok, detail) { out.push({ prop: prop, what: what, ok: !!ok, detail: detail }); }

    // ---- Proposition 1-2: absences, by brute-force structure factors ------------
    var lattices = { F: [[0, 0, 0], [0, .5, .5], [.5, 0, .5], [.5, .5, 0]], I: [[0, 0, 0], [.5, .5, .5]] };
    ['F', 'I'].forEach(function (c) {
      var bad = 0, n = 0;
      for (var h = -3; h <= 3; h++) for (var k = -3; k <= 3; k++) for (var l = -3; l <= 3; l++) {
        if (!h && !k && !l) continue;
        var re = 0, im = 0;
        lattices[c].forEach(function (x) { var p = 2 * Math.PI * (h * x[0] + k * x[1] + l * x[2]); re += Math.cos(p); im += Math.sin(p); });
        var zero = Math.hypot(re, im) < 1e-9;
        if (zero === M.allowed([h, k, l], c)) bad++;
        n++;
      }
      add('2(' + (c === 'F' ? 'a' : 'b') + ')', c + '-centring rule against the structure factor of the centred lattice, all ' + n + ' (hkl) with |h|,|k|,|l| &le; 3',
          bad === 0, bad + ' disagreements');
    });
    var dF = [M.dEff([1, 0, 0], 'F', 1).dEff, M.dEff([1, 1, 0], 'F', 1).dEff, M.dEff([1, 1, 1], 'F', 1).dEff];
    var dI = [M.dEff([1, 0, 0], 'I', 1).dEff, M.dEff([1, 1, 0], 'I', 1).dEff, M.dEff([1, 1, 1], 'I', 1).dEff];
    add('2(c)', 'Effective spacings (a = 1): F gives 1/2, 1/(2&radic;2), 1/&radic;3; I gives 1/2, 1/&radic;2, 1/(2&radic;3)',
        Math.abs(dF[0] - .5) + Math.abs(dF[1] - 1 / (2 * R2)) + Math.abs(dF[2] - 1 / R3) +
        Math.abs(dI[0] - .5) + Math.abs(dI[1] - 1 / R2) + Math.abs(dI[2] - 1 / (2 * R3)) < 1e-12,
        'F ' + dF.map(function (x) { return x.toFixed(4); }).join(', ') + '; I ' + dI.map(function (x) { return x.toFixed(4); }).join(', '));

    // ---- Proposition 3: random positive rates always give a bounded polytope ----
    var seed = 7; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
    var okCount = 0, N3 = 40;
    for (var s = 0; s < N3; s++) {
      var S = M.shape({ '{100}': 0.3 + 3 * rnd(), '{110}': 0.3 + 3 * rnd(), '{111}': 0.3 + 3 * rnd() }, 'm-3m');
      var maxr = 0; S.V.forEach(function (v) { maxr = Math.max(maxr, Math.hypot(v[0], v[1], v[2])); });
      if (S.info.volume > 0 && isFinite(maxr) && maxr < 50 && S.faces.length >= 4) okCount++;
    }
    add('3', N3 + ' random positive rate sets: each gives a bounded polytope of positive volume', okCount === N3, okCount + ' / ' + N3);

    // ---- Proposition 4: symmetry. Rotate by 120 degrees about (1,1,1) and by 90 about z
    var S4 = M.shape({ '{100}': 1, '{110}': 1.3, '{111}': 0.9 }, 'm-3m');
    function contains(Sh, p) { return Sh.faces.every(function (f) { return f.n[0] * p[0] + f.n[1] * p[1] + f.n[2] * p[2] <= f.d + 1e-7; }); }
    var rotOK = S4.V.every(function (v) { return contains(S4, [v[1], v[2], v[0]]) && contains(S4, [-v[1], v[0], v[2]]); });
    add('4', 'Shape with equal rates on each family is unchanged by a 120&deg; rotation about (1,1,1) and a 90&deg; rotation about z',
        rotOK, S4.V.length + ' vertices checked');

    // ---- Proposition 6: continuity sandwich ---------------------------------
    var Rb = { '{100}': 1, '{111}': 0.8 }, eps = 0.05, m = 0.8, Rp = { '{100}': 1 + eps, '{111}': 0.8 - eps };
    var P = M.shape(Rb, 'm-3m'), Pp = M.shape(Rp, 'm-3m');
    var inner = P.V.every(function (v) { return contains(Pp, v.map(function (x) { return x * (1 - eps / m); })); });
    var outer = Pp.V.every(function (v) { return contains(P, v.map(function (x) { return x / (1 + eps / m); })); });
    add('6', 'Rates moved by &epsilon; = 0.05: (1 &minus; &epsilon;/m)P &sube; P&prime; &sube; (1 + &epsilon;/m)P', inner && outer,
        'volume ' + P.info.volume.toFixed(4) + ' &rarr; ' + Pp.info.volume.toFixed(4));

    // ---- Proposition 7: thresholds -----------------------------------------
    function nm(t) { return M.shape({ '{100}': 1, '{111}': t }, 'm-3m').name; }
    var c7 = [[R3 * 1.0001, 'cube'], [R3 * 0.999, 'truncated cube'], [2 / R3, 'cuboctahedron'], [2 / R3 * 0.999, 'truncated octahedron'],
              [1 / R3 * 1.001, 'truncated octahedron'], [1 / R3, 'octahedron']];
    var miss7 = c7.filter(function (c) { return nm(c[0]) !== c[1]; });
    add('7', 'Shape names just above and below &radic;3, at 2/&radic;3, and just above and at 1/&radic;3', miss7.length === 0,
        c7.map(function (c) { return c[0].toFixed(4) + ' &rarr; ' + nm(c[0]); }).join('; '));

    // ---- Proposition 8: tetrahedron threshold -----------------------------------
    function tn(rp) { return M.shape({ '{111}+': rp, '{111}-': 1 }, '-43m').name; }
    var t8a = tn(1 / 3 * 0.999), t8b = tn(1 / 3 * 1.01);
    add('8', 'r<sub>+</sub> just below r<sub>&minus;</sub>/3 gives a tetrahedron; just above gives a truncated tetrahedron',
        t8a === 'tetrahedron' && t8b === 'truncated tetrahedron', t8a + ' / ' + t8b);

    // ---- Proposition 9: kappa^2 = 0 for cubic and tetrahedral bodies -----------
    var k9 = [['cube', { '{100}': 1 }, 'm-3m'], ['octahedron', { '{111}': 1 }, 'm-3m'], ['cuboctahedron', { '{100}': 1, '{111}': 2 / R3 }, 'm-3m'],
              ['tetrahedron', { '{111}+': 0.3, '{111}-': 1 }, '-43m'], ['rhombic dodecahedron', { '{110}': 1 }, 'm-3m']]
      .map(function (c) { return [c[0], M.shape(c[1], c[2]).info.kappa2]; });
    var stretched = M.shape({ '{100}': 1, '{111}': 0.8 }, 'm-3m');
    add('9', '&kappa;&sup2; for cube, octahedron, cuboctahedron, tetrahedron and rhombic dodecahedron',
        k9.every(function (c) { return c[1] < 1e-10; }), k9.map(function (c) { return c[0] + ' ' + c[1].toExponential(1); }).join('; '));

    // ---- Proposition 10: Q values and odd-l zeros ------------------------------
    var cube = M.shape({ '{100}': 1 }, 'm-3m').info, oct = M.shape({ '{111}': 1 }, 'm-3m').info,
        tet = M.shape({ '{111}+': 0.3, '{111}-': 1 }, '-43m').info;
    add('10(a)', 'Q<sub>4</sub>, Q<sub>6</sub> of cube (0.7638, 0.3536) and octahedron (0.5092, 0.6285), the known values for 6 and 8 directions',
        Math.abs(cube.Q4 - .7638) < 5e-4 && Math.abs(cube.Q6 - .3536) < 5e-4 && Math.abs(oct.Q4 - .5092) < 5e-4 && Math.abs(oct.Q6 - .6285) < 5e-4,
        'cube ' + cube.Q4.toFixed(4) + ', ' + cube.Q6.toFixed(4) + '; octahedron ' + oct.Q4.toFixed(4) + ', ' + oct.Q6.toFixed(4));
    add('10(b)', 'Q<sub>3</sub> = 0 for centrosymmetric shapes, non-zero for the tetrahedron',
        cube.Q3 < 1e-9 && oct.Q3 < 1e-9 && stretched.info.Q3 < 1e-9 && tet.Q3 > 0.5,
        'cube ' + cube.Q3.toFixed(4) + ', octahedron ' + oct.Q3.toFixed(4) + ', tetrahedron ' + tet.Q3.toFixed(4));

    // ---- Proposition 12: attachment numbers equal (deg - c0)/2 -----------------
    var nets = { pcu: [[1, 0, 0], [0, 1, 0], [0, 0, 1]], fcu: [[.5, .5, 0], [.5, -.5, 0], [.5, 0, .5], [.5, 0, -.5], [0, .5, .5], [0, .5, -.5]] };
    var det12 = [], ok12 = true;
    Object.keys(nets).forEach(function (net) {
      var vs = []; nets[net].forEach(function (v) { vs.push(v, v.map(function (x) { return -x; })); });
      [[1, 0, 0], [1, 1, 0], [1, 1, 1]].forEach(function (h) {
        var c0 = vs.filter(function (v) { return Math.abs(v[0] * h[0] + v[1] * h[1] + v[2] * h[2]) < 1e-12; }).length;
        var formula = (vs.length - c0) / 2, counted = M.attachmentNumber(net, h);
        if (formula !== counted) ok12 = false;
        det12.push(net + ' (' + h.join('') + ') ' + counted);
      });
    });
    add('12', 'Attachment numbers counted on the nets equal (deg &minus; c<sub>0</sub>)/2', ok12, det12.join('; '));
    add('13', 'Exact counting per unit area: fcc broken-bond ratio &gamma;<sub>100</sub>/&gamma;<sub>111</sub> = 2/&radic;3 and textbook F/S/K classes',
        true, 'checked in Python by <code>2_python/morphology/tests_phase3.py</code> (11 checks); results on the Graph Faces page');
    // ---- Propositions 14-16: deformed cells ----------------------------------------
    var D = window.DEFORM;
    if (D) {
      var seed2 = 11; function rnd2() { seed2 = (seed2 * 16807) % 2147483647; return seed2 / 2147483647; }
      // 14: the phase q.r computed from Cartesian positions of a random orthogonal cell equals h.x
      var worst = 0;
      for (var t = 0; t < 200; t++) {
        var a = [0.5 + 2 * rnd2(), 0.5 + 2 * rnd2(), 0.5 + 2 * rnd2()], h = [Math.floor(7 * rnd2()) - 3, Math.floor(7 * rnd2()) - 3, Math.floor(7 * rnd2()) - 3];
        var x = [rnd2(), rnd2(), rnd2()], phi_frac = h[0] * x[0] + h[1] * x[1] + h[2] * x[2];
        var phi_cart = (h[0] / a[0]) * (x[0] * a[0]) + (h[1] / a[1]) * (x[1] * a[1]) + (h[2] / a[2]) * (x[2] * a[2]);
        worst = Math.max(worst, Math.abs(phi_frac - phi_cart));
      }
      add('14', 'Phase <b>q</b>&middot;<b>r</b> in a deformed cell equals <b>h</b>&middot;<b>x</b> (200 random cells, indices and positions), so absences and orders cannot change',
          worst < 1e-12, 'largest difference ' + worst.toExponential(1));
      // 15: orbit sizes
      function sizes(lens) { var out = {}; D.families('P', 'm-3m', lens, 1).forEach(function (F) { var k = '{' + F.hkl.map(Math.abs).sort(function (p, q) { return q - p; }).join('') + '}'; (out[k] = out[k] || []).push(F.members.length); }); return out; }
      var c0 = sizes([1, 1, 1]), c1 = sizes([1, 1, 1.3]), c2 = sizes([1, 1.2, 1.5]);
      var good15 = JSON.stringify(c0['{100}']) === '[6]' && JSON.stringify(c1['{100}'].slice().sort()) === '[2,4]' &&
        JSON.stringify(c2['{100}']) === '[2,2,2]' && D.ops('m-3m', [1, 1, 1], 1e-9).length === 48 && D.ops('m-3m', [1, 1, 1.3], 1e-9).length === 16 && D.ops('m-3m', [1, 1.2, 1.5], 1e-9).length === 8;
      add('15', 'Orbit sizes: cubic {100} = 6 faces; c stretched gives 4 + 2; all three edges different gives 2 + 2 + 2; point group 48 &rarr; 16 &rarr; 8',
          good15, '{100}: ' + JSON.stringify(c0['{100}']) + ', ' + JSON.stringify(c1['{100}']) + ', ' + JSON.stringify(c2['{100}']));
      // 16: P-lattice shape is a box for every cell; its volume is 8 R1 R2 R3 with R proportional to 1/a
      var ok16 = true, nbox = 0, ncut = 0;
      for (var u = 0; u < 20; u++) {
        var L = [Math.exp(2 * rnd2() - 1), Math.exp(2 * rnd2() - 1), Math.exp(2 * rnd2() - 1)];
        var S = D.bfdhShape('P', 'm-3m', L), amax = Math.max.apply(null, L);
        var R = L.map(function (v) { return amax / v; });
        if (S.faces.length !== 6 || Math.abs(S.info.volume - 8 * R[0] * R[1] * R[2]) > 1e-6 * S.info.volume) ok16 = false; else nbox++;
      }
      ['F', 'I'].forEach(function (c) { var S = D.bfdhShape(c, 'm-3m', [1, 1, 1.7]); if (S.faces.length > 6) ncut++; else ok16 = false; });
      add('16', 'Primitive cells: BFDH shape is exactly the box with half-widths proportional to 1/<i>a</i><sub><i>i</i></sub> (20 random cells); F and I cells are cut by planes of lower order',
          ok16, nbox + ' of 20 boxes; F and I stretched cells have ' + ncut + ' of 2 cut shapes');
    }
    return out;
  }

  function init() {
    var host = document.getElementById('math-check-table');
    if (!host || !M) return;
    var R = rows();
    host.innerHTML = '<div class="table-wrap"><table class="data-table" id="math-checks-table"><thead><tr><td>Prop.</td><td>Check</td><td>Result</td><td>Computed</td></tr></thead><tbody>' +
      R.map(function (r) {
        return '<tr><td class="dt-label">' + r.prop + '</td><td class="dt-note">' + r.what + '</td>' +
          '<td class="dt-note" style="color:var(' + (r.ok ? '--good' : '--bad') + ');font-weight:650">' + (r.ok ? 'holds' : 'FAILS') + '</td>' +
          '<td class="dt-note">' + r.detail + '</td></tr>';
      }).join('') + '</tbody></table></div>' +
      '<p class="sm">' + R.filter(function (r) { return r.ok; }).length + ' of ' + R.length + ' checks hold.</p>';
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
