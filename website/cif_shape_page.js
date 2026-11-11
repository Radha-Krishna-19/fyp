/* =====================================================================
   cif_shape_page.js — drives cif_to_shape.html.

   Runs CIFSHAPE.run on the chosen CIF text (one of the four bundled files,
   or one the reader loads) and writes the working of every step into the
   page: the numbers, the matrices, the intermediate sums. Nothing here is a
   typed-in result. The Python reference values (window.CIF_SHAPE_PY) are
   printed beside the browser's numbers for the four bundled files.

   Pictures are SVG drawn from CSS variables, so they follow the site theme
   and need no graphics driver: the unit cell, the lattice planes, the shape
   forming plane by plane, the finished shape, and the morphology map.
   ===================================================================== */
(function () {
  'use strict';
  var CS = window.CIFSHAPE, M = window.MORPH, PY = window.CIF_SHAPE_PY || {};
  var la = CS.la, SVGNS = 'http://www.w3.org/2000/svg';
  var STRUCTS = ['MOF-5', 'HKUST-1', 'UiO-66', 'ZIF-8'];
  var state = { name: 'MOF-5', text: null, R: null, frame: 0, timer: null };

  // ---- formatting ------------------------------------------------------------
  function fx(x, k) {
    if (k === undefined) k = 4;
    if (!isFinite(x)) return String(x);
    if (Math.abs(x) < 0.5 * Math.pow(10, -k)) x = 0;
    var s = x.toFixed(k);
    return s.charAt(0) === '-' ? '−' + s.slice(1) : s;
  }
  function fr(x) {                                // a fraction like 1/2 for display
    x = x - Math.floor(x + 2e-3);                  // 1 and 0 are the same shift
    var t = [[0, '0'], [0.5, '½'], [1, '1'], [0.25, '¼'], [0.75, '¾']];
    for (var i = 0; i < t.length; i++) if (Math.abs(x - t[i][0]) < 2e-3) return t[i][1];
    return fx(x, 4);
  }
  function hkl(h) {
    return '(' + h.map(function (x) { return x < 0 ? '<span class="c2s-ov">' + (-x) + '</span>' : String(x); }).join('') + ')';
  }
  function famLabel(L) {
    return L.replace(/\+$/, '<sub>+</sub>').replace(/-$/, '<sub>−</sub>');
  }
  function mat(Mx, k, cls) {
    return '<span class="c2s-mat' + (cls ? ' ' + cls : '') + '"><table>' + Mx.map(function (r) {
      return '<tr>' + r.map(function (x) { return '<td>' + (typeof x === 'string' ? x : fx(x, k)) + '</td>'; }).join('') + '</tr>';
    }).join('') + '</table></span>';
  }
  function vec(v, k) { return '(' + v.map(function (x) { return fx(x, k); }).join(', ') + ')'; }
  function el(id) { return document.getElementById(id); }
  function set(id, html) { var e = el(id); if (e) e.innerHTML = html; }
  function py(name) { return PY[name] && state.bundled ? PY[name] : null; }
  function pyLine(html) { return '<p class="c2s-py"><b>Python check</b> (<code>code/morphology/run_cif_to_shape.py</code>): ' + html + '</p>'; }
  // R = sqrt(p/q) in its simplest surd form, from R^2 as an exact ratio of integers
  function surd(num, den) {
    function g(a, b) { while (b) { var t = b; b = a % b; a = t; } return a; }
    var d = g(num, den); num /= d; den /= d;
    function split(n) { var a = 1; for (var f = 2; f * f <= n; f++) while (n % (f * f) === 0) { n /= f * f; a *= f; } return [a, n]; }
    var P = split(num), Q = split(den), co = P[0], cd = Q[0], c = g(co, cd); co /= c; cd /= c;
    var top = (co === 1 && P[1] !== 1 ? '' : String(co)) + (P[1] !== 1 ? '√' + P[1] : '');
    var bot = (cd === 1 ? '' : String(cd)) + (Q[1] !== 1 ? '√' + Q[1] : '');
    if (!top) top = '1';
    return bot ? top + '/' + bot : top;
  }
  function colour(tag) {
    var b = tag.replace(/[+-]$/, '');
    if (b === '{100}') return 'var(--linker)';
    if (b === '{111}') return /-$/.test(tag) ? 'var(--node-ink)' : 'var(--node)';
    if (b === '{110}') return 'var(--good)';
    if (tag === 'bound') return 'var(--surface-2)';
    return 'var(--text3, #94a3b8)';
  }

  // ---- 3D view (SVG, drag to rotate) --------------------------------------------
  function View(host, opts) {
    opts = opts || {};
    var v = { yaw: opts.yaw || 0.62, pitch: opts.pitch || 0.38, draw: null };
    function rot(p) {
      var cy = Math.cos(v.yaw), sy = Math.sin(v.yaw), cp = Math.cos(v.pitch), sp = Math.sin(v.pitch);
      var x = cy * p[0] - sy * p[1], y = sy * p[0] + cy * p[1], z = p[2];
      return [x, cp * y - sp * z, sp * y + cp * z];
    }
    v.rot = rot;
    v.svg = function (W, H, label) {
      host.innerHTML = '';
      var s = document.createElementNS(SVGNS, 'svg');
      s.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
      s.setAttribute('role', 'img');
      s.setAttribute('aria-label', label);
      s.setAttribute('class', 'c2s-svg');
      host.appendChild(s);
      var drag = null;
      s.addEventListener('pointerdown', function (e) { drag = [e.clientX, e.clientY]; try { s.setPointerCapture(e.pointerId); } catch (x) {} });
      s.addEventListener('pointermove', function (e) {
        if (!drag) return;
        v.yaw += (e.clientX - drag[0]) * 0.01; v.pitch = Math.max(-1.4, Math.min(1.4, v.pitch + (e.clientY - drag[1]) * 0.01));
        drag = [e.clientX, e.clientY];
        if (v.draw) v.draw();
      });
      s.addEventListener('pointerup', function () { drag = null; });
      s.addEventListener('pointercancel', function () { drag = null; });
      return s;
    };
    return v;
  }
  function node(tag, attrs, parent) {
    var e = document.createElementNS(SVGNS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  // a convex polytope: visible faces only (convexity means they never overlap)
  function drawShape(view, faces, opts) {
    opts = opts || {};
    var W = 360, H = 320;
    var s = view.svg(W, H, opts.label || 'crystal shape');
    var Rm = opts.scale || 0;
    if (!Rm) faces.forEach(function (f) { f.pts.forEach(function (p) { Rm = Math.max(Rm, la.norm(p)); }); });
    var k = 0.43 * Math.min(W, H) / (Rm || 1);
    faces.forEach(function (f) {
      var n = view.rot(f.n);
      if (n[1] > -1e-9) return;                              // facing away
      var pts = f.pts.map(view.rot);
      var light = Math.max(0, -n[1] * 0.55 + n[2] * 0.45);
      var hi = opts.highlight && opts.highlight(f);
      node('polygon', {
        points: pts.map(function (p) { return (W / 2 + k * p[0]).toFixed(1) + ',' + (H / 2 - k * p[2]).toFixed(1); }).join(' '),
        style: 'fill:' + (hi ? 'var(--warn, #d97706)' : colour(f.tag)) + ';fill-opacity:' + (0.35 + 0.55 * light).toFixed(2) +
               ';stroke:var(--text);stroke-width:' + (hi ? 2.2 : 0.9) + ';stroke-linejoin:round'
      }, s);
      if (opts.labels && f.area > (opts.minLabelArea || 0)) {
        var c = pts.reduce(la.add, [0, 0, 0]);
        c = la.scale(c, 1 / pts.length);
        millerLabel(s, W / 2 + k * c[0], H / 2 - k * c[2] + 4, f.hkl);
      }
    });
    return s;
  }
  // a Miller index label in SVG, with a drawn bar over each negative index
  function millerLabel(s, cx, cy, h) {
    var w = 6.6, txt = '(' + h.map(function (x) { return String(Math.abs(x)); }).join('') + ')', x0 = cx - txt.length * w / 2;
    var t = node('text', { x: x0.toFixed(1), y: cy.toFixed(1),
      style: 'font-family:ui-monospace,Consolas,Menlo,monospace;font-size:11px;fill:var(--text)' }, s);
    t.textContent = txt;
    h.forEach(function (x, i) {
      if (x < 0) node('line', { x1: (x0 + (i + 1) * w + 0.6).toFixed(1), x2: (x0 + (i + 2) * w - 0.6).toFixed(1), y1: (cy - 9.5).toFixed(1), y2: (cy - 9.5).toFixed(1),
                                style: 'stroke:var(--text);stroke-width:1' }, s);
    });
  }

  // ---- step 1: the CIF -----------------------------------------------------------
  function step1(R) {
    var c = R.cif, comp = Object.keys(c.composition).map(function (e) { return e + '<sub>' + c.composition[e] + '</sub>'; }).join(' ');
    var shown = c.atoms.slice(0, 4).map(function (a) { return a.line; }).join('\n');
    set('c2s-s1',
      '<pre class="c2s-cif">' + c.cellLines.join('\n') + '\n\nloop_ (atoms)\n' + shown + '\n… ' + (c.atoms.length - 4) + ' more atom lines</pre>' +
      '<p>The file lists <b>' + c.atoms.length + ' atoms</b> (' + comp + '), each by element and fractional coordinates ' +
      '(<i>x</i>, <i>y</i>, <i>z</i>), and the six cell numbers above. Its stated space group is <code>' + (c.spaceGroupInFile || 'none') + '</code>' +
      (c.spaceGroupInFile === 'P 1' ? ', that is, no symmetry is written down. Every symmetry used below is found from the numbers in the file.' : '.') + '</p>');
  }

  // ---- step 2: lattice vectors and metric tensor ------------------------------------
  function step2(R) {
    var c = R.cif.cell, A = R.A, G = R.G, r = Math.PI / 180;
    var ca = Math.cos(c[3] * r), cb = Math.cos(c[4] * r), cg = Math.cos(c[5] * r), sg = Math.sin(c[5] * r);
    var d = G[0][0] * (G[1][1] * G[2][2] - G[1][2] * G[2][1]) - G[0][1] * (G[1][0] * G[2][2] - G[1][2] * G[2][0]) + G[0][2] * (G[1][0] * G[2][1] - G[1][1] * G[2][0]);
    set('c2s-s2',
      '<div class="c2s-work">' +
      '<p><b>a</b> = (<i>a</i>, 0, 0) = (' + fx(c[0]) + ', 0, 0)</p>' +
      '<p><b>b</b> = (<i>b</i> cos&gamma;, <i>b</i> sin&gamma;, 0) = (' + fx(c[1]) + ' &times; ' + fx(cg, 5) + ', ' + fx(c[1]) + ' &times; ' + fx(sg, 5) + ', 0) = ' + vec(A[1]) + '</p>' +
      '<p><i>c<sub>x</sub></i> = <i>c</i> cos&beta; = ' + fx(c[2]) + ' &times; ' + fx(cb, 5) + ' = ' + fx(A[2][0]) + '</p>' +
      '<p><i>c<sub>y</sub></i> = <i>c</i> (cos&alpha; &minus; cos&beta; cos&gamma;) / sin&gamma; = ' + fx(c[2]) + ' &times; (' + fx(ca, 5) + ' &minus; ' + fx(cb, 5) + ' &times; ' + fx(cg, 5) + ') / ' + fx(sg, 5) + ' = ' + fx(A[2][1]) + '</p>' +
      '<p><i>c<sub>z</sub></i> = &radic;(<i>c</i>&sup2; &minus; <i>c<sub>x</sub></i>&sup2; &minus; <i>c<sub>y</sub></i>&sup2;) = &radic;(' + fx(c[2] * c[2], 3) + ' &minus; ' + fx(A[2][0] * A[2][0], 3) + ' &minus; ' + fx(A[2][1] * A[2][1], 3) + ') = ' + fx(A[2][2]) + '</p>' +
      '</div>' +
      '<div class="c2s-eq"><i>A</i> = ' + mat(A, 4) + ' &Aring;&emsp; <i>G</i> = <i>A A</i><sup>T</sup> = ' + mat(G, 3) + ' &Aring;&sup2;</div>' +
      '<div class="c2s-work"><p>For example <i>G</i><sub>11</sub> = <b>a</b>&middot;<b>a</b> = ' + fx(c[0]) + '&sup2; = ' + fx(G[0][0], 3) +
      ' and <i>G</i><sub>12</sub> = <b>a</b>&middot;<b>b</b> = <i>ab</i> cos&gamma; = ' + fx(c[0]) + ' &times; ' + fx(c[1]) + ' &times; ' + fx(cg, 5) + ' = ' + fx(G[0][1], 3) + '.</p>' +
      '<p>det <i>G</i> = <i>G</i><sub>11</sub>(<i>G</i><sub>22</sub><i>G</i><sub>33</sub> &minus; <i>G</i><sub>23</sub>&sup2;) &minus; <i>G</i><sub>12</sub>(<i>G</i><sub>12</sub><i>G</i><sub>33</sub> &minus; <i>G</i><sub>23</sub><i>G</i><sub>13</sub>) + <i>G</i><sub>13</sub>(<i>G</i><sub>12</sub><i>G</i><sub>23</sub> &minus; <i>G</i><sub>22</sub><i>G</i><sub>13</sub>) = ' + fx(d, 0) + ' &Aring;<sup>6</sup></p>' +
      '<p>Volume <i>V</i> = &radic;(det <i>G</i>) = <b>' + fx(R.volume, 2) + ' &Aring;&sup3;</b></p></div>');
  }

  // ---- step 3: conventional cubic cell -------------------------------------------------
  function step3(R, P) {
    var C = R.conv;
    if (!C) { set('c2s-s3', '<p class="c2s-stop">' + R.stop + '</p>'); return; }
    var html;
    if (C.key === 'P') {
      html = '<p>Here <i>G</i> is already <i>a</i>&sup2; times the identity: the three edges are equal (' + fx(R.cif.cell[0]) + ' &Aring;) and at right angles ' +
        '(largest off-diagonal entry ' + fx(Math.max(Math.abs(R.G[0][1]), Math.abs(R.G[0][2]), Math.abs(R.G[1][2])), 4) + ' &Aring;&sup2;). The cell in the file <b>is</b> the cube, with ' +
        '<i>a</i><sub>c</sub> = ' + fx(R.a) + ' &Aring;, and <i>M</i> is the identity. Whether further lattice points sit inside it (a centred cube) is decided from the atoms in Step 4.</p>';
    } else {
      var Mt = C.M, Gc = C.Gc, ap = R.cif.cell[0];
      html = '<p>The three edges are equal (' + fx(ap) + ' &Aring;) but the angles are ' + fx(R.cif.cell[3], 3) + '&deg;, not 90&deg;. ' +
        'Edges at 60&deg; are exactly the three shortest lattice vectors of a <b>face-centred cube</b>: ' +
        '<b>a</b><sub>1</sub> = &frac12;<i>a</i><sub>c</sub>(0, 1, 1), <b>a</b><sub>2</sub> = &frac12;<i>a</i><sub>c</sub>(1, 0, 1), <b>a</b><sub>3</sub> = &frac12;<i>a</i><sub>c</sub>(1, 1, 0), ' +
        'each of length <i>a</i><sub>c</sub>/&radic;2 and at 60&deg; to the others. The cube edges are then ' +
        '<b>c</b><sub>1</sub> = &minus;<b>a</b><sub>1</sub>+<b>a</b><sub>2</sub>+<b>a</b><sub>3</sub>, <b>c</b><sub>2</sub> = <b>a</b><sub>1</sub>&minus;<b>a</b><sub>2</sub>+<b>a</b><sub>3</sub>, ' +
        '<b>c</b><sub>3</sub> = <b>a</b><sub>1</sub>+<b>a</b><sub>2</sub>&minus;<b>a</b><sub>3</sub>, which is the matrix <i>M</i> below. Check with the numbers:</p>' +
        '<div class="c2s-eq"><i>M</i> = ' + mat(Mt, 0) + '&emsp; <i>G</i><sub>c</sub> = <i>M G M</i><sup>T</sup> = ' + mat(Gc, 3) + ' &Aring;&sup2;</div>' +
        '<div class="c2s-work"><p>The diagonal entries agree and the off-diagonal entries vanish (largest relative deviation ' + C.deviation.toExponential(1) + ', from the rounding in the file), so the lattice is cubic with</p>' +
        '<p><i>a</i><sub>c</sub> = &radic;<i>G</i><sub>c,11</sub> = &radic;' + fx(Gc[0][0], 3) + ' = <b>' + fx(R.a) + ' &Aring;</b>, and indeed ' + fx(ap) + ' &times; &radic;2 = ' + fx(ap * Math.SQRT2) + ' &Aring;.</p>' +
        '<p>Volume check: det <i>M</i> = ' + Math.round(la.det3(Mt)) + ', so the cube holds ' + R.pointsPerCell + ' lattice points and <i>V</i><sub>c</sub> = ' + R.pointsPerCell + ' &times; ' + fx(R.volume, 2) +
        ' = ' + fx(R.pointsPerCell * R.volume, 1) + ' &Aring;&sup3; = <i>a</i><sub>c</sub>&sup3; = ' + fx(Math.pow(R.a, 3), 1) + ' &Aring;&sup3;.</p></div>' +
        '<p>Re-expressed in the cube, the ' + R.cif.atoms.length + ' atoms of the file become ' + R.C.els.length + ' (each appears at its four lattice-equivalent positions).</p>';
    }
    if (P) html += pyLine('conventional cell edge ' + fx(P.a_conv) + ' &Aring; (transformation ' + P.cubic_transform + '); spglib standard cell ' + fx(P.spglib.a) + ' &Aring;.');
    set('c2s-s3', html);
  }

  // ---- step 4: centring -------------------------------------------------------------------
  function step4(R, P) {
    var T = R.centringTest;
    function cells(tst) {
      return tst.I.map(function (x) { return x.r.mapped + ' / ' + x.r.of; }).concat(tst.F.map(function (x) { return x.r.mapped + ' / ' + x.r.of; }));
    }
    var a = cells(T.withH), b = cells(T.withoutH);
    var head = ['I: + (&frac12;, &frac12;, &frac12;)', 'F: + (0, &frac12;, &frac12;)', 'F: + (&frac12;, 0, &frac12;)', 'F: + (&frac12;, &frac12;, 0)'];
    var html = '<div class="table-wrap"><table class="data-table" id="c2s-centring"><thead><tr><td>Atoms used</td>' + head.map(function (h) { return '<td>' + h + '</td>'; }).join('') +
      '</tr></thead><tbody><tr><td class="dt-label">all ' + R.C.els.length + '</td>' + a.map(function (x) { return '<td class="dt-value">' + x + '</td>'; }).join('') +
      '</tr><tr><td class="dt-label">without H</td>' + b.map(function (x) { return '<td class="dt-value">' + x + '</td>'; }).join('') + '</tr></tbody></table></div>';
    var name = { F: 'face-centred (F)', I: 'body-centred (I)', P: 'primitive (P)' }[R.centring];
    html += '<p>Each entry counts the atoms <i>j</i> that have an atom of the same element within ' + CS.TOL + ' &Aring; of <b>x</b><sub><i>j</i></sub> + <b>t</b>. ' +
      'A translation is a symmetry only if every atom passes. Result: the lattice is <b>' + name + '</b>' +
      (R.symmetryWithH ? '.' : ', found on the framework without hydrogen.') + '</p>';
    if (R.conv.key !== 'P') html += '<p class="sm">For this file the F translations hold for every atom automatically, because they are combinations of the file\'s own cell vectors (Step 3): the 60&deg; cell already says the cube is face-centred.</p>';
    if (!R.symmetryWithH) html += '<div class="callout warn" data-kind="Hydrogen breaks the symmetry in this file">With every atom, (&frac12;, &frac12;, &frac12;) maps only ' + a[0] +
      ' atoms; the ones that fail are hydrogen atoms whose positions in this file do not follow the framework. Without hydrogen all ' + R.framework.els.length +
      ' atoms pass. The framework symmetry is used from here on, as spglib does for this file.</div>';
    if (P) html += pyLine('centring ' + P.centring + ', found ' + (P.symmetry_found_with === 'with_H' ? 'with' : 'without') + ' hydrogen; spglib uses hydrogen: ' + (P.spglib.used_hydrogen ? 'yes' : 'no') + '.');
    set('c2s-s4', html);
  }

  // ---- step 5: point group --------------------------------------------------------------------
  function step5(R, P) {
    var tag = R.symmetryWithH ? 'withH' : 'withoutH', rows = '';
    CS.OPS.forEach(function (o) {
      var r = R.pgTest[tag][o.key], okk = r.mapped === r.of;
      rows += '<tr><td class="dt-label">' + o.label + '</td><td class="dt-note">' + o.text + '</td><td class="dt-note">' + mat(o.R, 0, 'c2s-small') + '</td>' +
        '<td class="dt-value">' + r.mapped + ' / ' + r.of + '</td><td class="dt-note">' + (okk && r.t ? '(' + r.t.map(fr).join(', ') + ')' : '&mdash;') + '</td>' +
        '<td class="dt-note">' + (okk ? '<b>yes</b>' : 'no') + '</td></tr>';
    });
    var html = '<div class="table-wrap"><table class="data-table" id="c2s-pg"><thead><tr><td>Operation</td><td>Acts as</td><td><i>R</i></td><td>Atoms mapped (best <b>t</b>)</td><td><b>t</b> found</td><td>Symmetry?</td></tr></thead><tbody>' + rows + '</tbody></table></div>';
    html += '<p>Decision: a 3-fold axis is required for a cubic crystal. With inversion and a 4-fold axis the point group is <b>m-3m</b> (48 operations); ' +
      'with the 3-fold axis and the &minus;4 axis but no inversion it is <b>-43m</b> (24 operations). Here: <b>' + R.pointGroup + '</b>.</p>';
    if (R.pointGroup === '-43m') html += '<p>Without inversion the eight {111} planes split into two sets of four that are not related by symmetry, {111}<sub>+</sub> (<i>hkl</i> &gt; 0) and {111}<sub>&minus;</sub> (<i>hkl</i> &lt; 0). The same holds for every family with no zero index. If the two halves grew at different rates the crystal could become tetrahedral; BFDH gives them equal distances (Step 8), and the tetrahedral shapes are explored on the <a href="morphology.html">Morphology</a> page.</p>';
    if (P) html += pyLine('point group ' + P.point_group + ' by the same search; spglib: ' + P.spglib.spacegroup + ' (No. ' + P.spglib.number + ').');
    set('c2s-s5', html);
  }

  // ---- step 6: structure factors and space group --------------------------------------------------
  function step6(R, P) {
    var cen = R.centring, rows = '';
    R.sfTable.forEach(function (x) {
      var S = x.S;
      rows += '<tr><td class="dt-label">' + hkl(x.h) + '</td><td class="dt-note">' + S.terms.map(function (t) { return t < 0 ? '−' + (-t) : String(t); }).join(' + ').replace(/\+ −/g, '− ') + ' = <b>' + S.value + '</b></td>' +
        '<td class="dt-note">' + (x.allowed ? 'allowed' : '<b>absent</b>') + '</td><td class="dt-value">' + fx(x.F.ratio, 5) + '</td></tr>';
    });
    var cs = cen === 'F' ? '<i>S</i>(<b>h</b>) = 1 + e<sup>i&pi;(<i>k</i>+<i>l</i>)</sup> + e<sup>i&pi;(<i>h</i>+<i>l</i>)</sup> + e<sup>i&pi;(<i>h</i>+<i>k</i>)</sup>'
      : cen === 'I' ? '<i>S</i>(<b>h</b>) = 1 + e<sup>i&pi;(<i>h</i>+<i>k</i>+<i>l</i>)</sup>' : '<i>S</i>(<b>h</b>) = 1';
    var html = '<p class="c2s-eq">For this lattice, ' + cs + '. Each term is +1 or &minus;1, so <i>S</i> is ' +
      (cen === 'F' ? '4 when <i>h</i>, <i>k</i>, <i>l</i> are all even or all odd, and 0 otherwise.' : cen === 'I' ? '2 when <i>h</i> + <i>k</i> + <i>l</i> is even, and 0 otherwise.' : 'always 1.') + '</p>' +
      '<div class="table-wrap"><table class="data-table" id="c2s-sf"><thead><tr><td>(<i>hkl</i>)</td><td><i>S</i>(<b>h</b>), term by term</td><td>By centring</td>' +
      '<td>|<i>F</i>(<i>hkl</i>)| / &Sigma;<i>Z</i>, from the ' + R.framework.els.length + ' atoms</td></tr></thead><tbody>' + rows + '</tbody></table></div>' +
      '<p>Every reflection the centring forbids comes out as exactly zero from the atoms; the allowed ones do not (&Sigma;<i>Z</i> = ' + fx(R.framework.els.reduce(function (s, e) { return s + (CS.Z[e] || 6); }, 0), 0) + ', with <i>Z</i> the atomic number of each atom as its weight).</p>';
    var sg = R.sg;
    if (sg.reasons.length) {
      html += '<p>Centring ' + cen + ' with point group ' + R.pointGroup + ' leaves ' + (sg.reasons.length + 1) + ' possible space groups. The others contain glide planes, and each glide forbids one more reflection:</p><ul class="c2s-list">' +
        sg.reasons.map(function (x) {
          return '<li><b>' + x.sg + '</b> (No. ' + x.n + '): ' + x.cond + '. From the atoms |<i>F</i>' + hkl(x.hkl) + '|/&Sigma;<i>Z</i> = ' + fx(x.ratio, 4) + (x.ruledOut ? ', not zero, so ' + x.sg + ' is ruled out.' : ', zero, so ' + x.sg + ' remains possible.') + '</li>';
        }).join('') + '</ul>';
    }
    html += '<p><b>Space group: ' + (sg.sg ? sg.sg + ' (No. ' + sg.n + ')' : 'not decided here') + '.</b> For these groups the centring is the only rule that removes faces, so the first allowed order of (<i>hkl</i>) follows from the centring alone.</p>';
    if (P) html += pyLine('|<i>F</i>|/&Sigma;<i>Z</i> for (100), (110), (111), (200): ' + ['100', '110', '111', '200'].map(function (k) { return fx(P.structure_factor[k], 5); }).join(', ') + '; spglib: <b>' + P.spglib.spacegroup + '</b>.');
    set('c2s-s6', html);
  }

  // ---- lattice-plane picture (step 7) ---------------------------------------------------------------
  function latticePicture(R, which) {
    var host = el('c2s-planes-fig');
    if (!host) return;
    host.innerHTML = '';
    var cen = R.centring, W = 300, H = 300, pad = 30, s = (W - 2 * pad) / 2;   // two cells across
    var pts = [];
    for (var i = 0; i <= 2; i++) for (var j = 0; j <= 2; j++) pts.push([i, j, 0]);
    if (cen === 'I') for (i = 0; i < 2; i++) for (j = 0; j < 2; j++) pts.push([i + .5, j + .5, .5]);
    if (cen === 'F') {
      for (i = 0; i < 2; i++) for (j = 0; j < 2; j++) pts.push([i + .5, j + .5, 0]);
      for (i = 0; i <= 2; i++) for (j = 0; j < 2; j++) { pts.push([i, j + .5, .5]); pts.push([j + .5, i, .5]); }
    }
    var svg = document.createElementNS(SVGNS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H); svg.setAttribute('class', 'c2s-svg c2s-flat');
    svg.setAttribute('role', 'img');
    host.appendChild(svg);
    var X = function (x) { return pad + x * s; }, Y = function (y) { return H - pad - y * s; };
    // the planes: lines h x + k y = m for the projection, m stepping by 1/2
    var h = which === '110' ? [1, 1] : [1, 0];
    var vals = {};
    pts.forEach(function (p) { vals[(((h[0] * p[0] + h[1] * p[1]) % 1) + 1) % 1] = 1; });
    var layers = Object.keys(vals).length;                 // distinct layers per repeat
    for (var m = -2; m <= 4; m += 0.5) {
      var own = Math.abs(m - Math.round(m)) < 1e-9, extra = !own && layers > 1;
      if (!own && !extra) continue;
      var x1, y1, x2, y2;
      if (which === '110') { x1 = m; y1 = 0; x2 = m - 2; y2 = 2; if (x1 > 2) { y1 = x1 - 2; x1 = 2; } if (x2 < 0) { y2 = m; x2 = 0; } if (y1 > 2 || y2 < 0 || m <= 0 || m >= 4) continue; }
      else { if (m < 0 || m > 2) continue; x1 = m; y1 = 0; x2 = m; y2 = 2; }
      node('line', { x1: X(x1), y1: Y(y1), x2: X(x2), y2: Y(y2), style: 'stroke:' + (own ? 'var(--linker)' : 'var(--node)') + ';stroke-width:' + (own ? 1.6 : 1.4) + (own ? '' : ';stroke-dasharray:5 4') }, svg);
    }
    node('rect', { x: X(0), y: Y(2), width: 2 * s, height: 2 * s, style: 'fill:none;stroke:var(--border-strong);stroke-width:1' }, svg);
    node('line', { x1: X(1), y1: Y(0), x2: X(1), y2: Y(2), style: 'stroke:var(--border-strong);stroke-width:.7' }, svg);
    node('line', { x1: X(0), y1: Y(1), x2: X(2), y2: Y(1), style: 'stroke:var(--border-strong);stroke-width:.7' }, svg);
    pts.forEach(function (p) {
      node('circle', { cx: X(p[0]), cy: Y(p[1]), r: 5, style: p[2] ? 'fill:var(--surface-0);stroke:var(--text);stroke-width:1.5' : 'fill:var(--text)' }, svg);
    });
    var lab = node('text', { x: W / 2, y: 16, 'text-anchor': 'middle', style: 'font-size:12px;fill:var(--text)' }, svg);
    lab.textContent = (which === '110' ? '(110)' : '(100)') + ' planes, viewed down [001]';
    var d = which === '110' ? R.a / Math.SQRT2 : R.a;
    set('c2s-planes-cap', 'Filled dots: lattice points at height 0; open dots: at height &frac12;<i>a</i>. Two cells of edge <i>a</i> = ' + fx(R.a, 3) + ' &Aring; are shown. ' +
      'Blue lines: the planes (' + (which === '110' ? '110' : '100') + ') with spacing <i>d</i> = ' + fx(d, 3) + ' &Aring;. ' +
      (layers > 1 ? 'Red dashed lines: an identical layer of lattice points lies exactly half-way, so the true repeat is <i>d</i>/2 = <b>' + fx(d / 2, 3) + ' &Aring;</b>. That is why (' + (which === '110' ? '110' : '100') + ') is absent and its first allowed order is (' + (which === '110' ? '220' : '200') + ').'
        : 'No lattice point lies between two blue planes, so the repeat is <i>d</i> itself and (' + (which === '110' ? '110' : '100') + ') is allowed.'));
  }

  // ---- step 7: families -----------------------------------------------------------------------------
  function step7(R, P, showAll) {
    var F = R.families, n = showAll ? F.length : 12, rows = '';
    F.slice(0, n).forEach(function (f, i) {
      var first = f.n === 1 ? hkl(f.hkl) + ' allowed' : hkl(f.hkl) + ' absent, ' + hkl(f.hkl.map(function (x) { return x * f.n; })) + ' allowed';
      rows += '<tr><td class="dt-value">' + (i + 1) + '</td><td class="dt-label">' + famLabel(f.label) + '</td><td class="dt-value">' + f.multiplicity + '</td>' +
        '<td class="dt-value">' + f.sumSq + '</td><td class="dt-value">' + fx(R.a, 3) + ' / &radic;' + f.sumSq + ' = ' + fx(f.d, 3) + '</td>' +
        '<td class="dt-note">' + first + '</td><td class="dt-value">' + f.n + '</td><td class="dt-value"><b>' + fx(f.dEff, 3) + '</b></td></tr>';
    });
    var html = '<div class="table-wrap"><table class="data-table" id="c2s-fams"><thead><tr><td>#</td><td>Family</td><td>Planes</td><td><i>h</i>&sup2;+<i>k</i>&sup2;+<i>l</i>&sup2;</td>' +
      '<td><i>d</i> = <i>a</i>/&radic;(&hellip;) (&Aring;)</td><td>First allowed order</td><td><i>n</i></td><td><i>d</i><sub>eff</sub> = <i>d</i>/<i>n</i> (&Aring;)</td></tr></thead><tbody>' + rows + '</tbody></table></div>' +
      '<p class="sm">' + (showAll ? 'All ' : 'The 12 widest-spaced of ') + F.length + ' families with indices up to 6 are listed' +
      (showAll ? '.' : '; <button type="button" class="mini" id="c2s-showall">show all ' + F.length + '</button>') + ' Every one of them is used in Step 9.</p>';
    if (P) html += pyLine('the widest families and <i>d</i><sub>eff</sub>: ' + P.families.map(function (f) { return famLabel(f.family) + ' ' + fx(f.d_eff, 3); }).join(', ') + ' &Aring;.');
    set('c2s-s7', html);
    var b = el('c2s-showall');
    if (b) b.addEventListener('click', function () { step7(R, P, true); });
  }

  // ---- step 8: BFDH distances ---------------------------------------------------------------------------
  function step8(R, P) {
    var F = R.families, f0 = F[0], rows = '';
    F.slice(0, 8).forEach(function (f) {
      var num = f.n * f.n * f.sumSq, den = f0.n * f0.n * f0.sumSq;
      rows += '<tr><td class="dt-label">' + famLabel(f.label) + '</td><td class="dt-value">' + fx(R.dmax, 3) + ' / ' + fx(f.dEff, 3) + '</td><td class="dt-value"><b>' + fx(f.R, 4) + '</b></td>' +
        '<td class="dt-note">' + surd(num, den) + '</td></tr>';
    });
    var html = '<p>The widest spacing is <i>d</i><sub>eff,max</sub> = ' + fx(R.dmax, 3) + ' &Aring;, for ' + famLabel(f0.label) + '. Dividing by it puts that family at distance 1:</p>' +
      '<div class="table-wrap"><table class="data-table" id="c2s-rates"><thead><tr><td>Family</td><td><i>d</i><sub>eff,max</sub> / <i>d</i><sub>eff</sub></td><td><i>R</i><sub><i>f</i></sub></td><td>Exact value</td></tr></thead><tbody>' + rows + '</tbody></table></div>' +
      '<p>The exact values follow because every <i>d</i><sub>eff</sub> is <i>a</i>/(<i>n</i>&radic;(<i>h</i>&sup2;+<i>k</i>&sup2;+<i>l</i>&sup2;)): the cell edge <i>a</i> cancels, so <i>R</i><sub><i>f</i></sub>&sup2; is a ratio of whole numbers, ' +
      '<i>R</i><sub><i>f</i></sub>&sup2; = <i>n</i><sub><i>f</i></sub>&sup2;(<i>h</i>&sup2;+<i>k</i>&sup2;+<i>l</i>&sup2;)<sub><i>f</i></sub> / <i>n</i><sub>0</sub>&sup2;(<i>h</i>&sup2;+<i>k</i>&sup2;+<i>l</i>&sup2;)<sub>0</sub>. ' +
      'So the BFDH shape depends only on the centring and the point group, not on the size of the cell or on the atoms.</p>';
    if (P) html += pyLine('BFDH distances ' + Object.keys(P.bfdh_rates).slice(0, 4).map(function (k) { return famLabel(k) + ' ' + fx(P.bfdh_rates[k], 4); }).join(', ') + '.');
    set('c2s-s8', html);
  }

  // ---- step 9: building the shape -----------------------------------------------------------------------
  var growView = null, finalView = null;
  function frames(R) {
    var S = R.shape, out = [], skipped = 0, first = -1, lead = S.planes[0].tag, leadEnd = 0;
    S.planes.forEach(function (p, i) { if (p.tag === lead) leadEnd = i; });
    S.snapshots.forEach(function (sn, i) {
      // the first picture is the whole first family, once it encloses a closed shape
      var bounded = !sn.faces.some(function (f) { return f.tag === 'bound'; });
      if (!bounded || i < leadEnd) return;
      if (first < 0) { first = i; out.push({ i: i, plane: sn.plane, faces: sn.faces, first: true, before: i + 1 }); skipped = 0; return; }
      if (sn.changed) { out.push({ i: i, plane: sn.plane, faces: sn.faces, skipped: skipped }); skipped = 0; } else skipped++;
    });
    out.after = skipped;
    return out;
  }
  function drawFrame(R) {
    var Fs = R.frames, k = Math.max(0, Math.min(state.frame, Fs.length - 1)), f = Fs[k];
    var sc = 0; R.shape.faces.forEach(function (x) { x.pts.forEach(function (p) { sc = Math.max(sc, la.norm(p)); }); });
    Fs.forEach(function (fr0) { fr0.faces.forEach(function (x) { x.pts.forEach(function (p) { sc = Math.max(sc, la.norm(p)); }); }); });
    growView.draw = function () {
      drawShape(growView, f.faces, { scale: sc, label: 'the shape after ' + (f.i + 1) + ' planes',
        highlight: function (x) { return !f.first && x.hkl && x.hkl.join() === f.plane.hkl.join() && x.tag === f.plane.tag; } });
    };
    growView.draw();
    var nm = M ? M.name({ faces: f.faces.map(function (x) { return { tag: x.tag, poly: x.pts, area: CS.polygonArea(x.pts) }; }), V: uniq(f.faces) }) : '';
    var txt;
    if (f.first) {
      var fam = f.plane.family;
      txt = '<b>Start.</b> The ' + f.before + ' planes ' + (f.before === fam.multiplicity ? 'of the nearest family, ' : 'up to and including the nearest family, ') + famLabel(fam.label) + ' at <i>R</i> = ' + fx(fam.R, 4) + ', already enclose a closed shape: <b>' + nm + '</b>, ' + f.faces.length + ' faces.';
    } else {
      txt = '<b>Cut ' + k + '.</b> Plane ' + hkl(f.plane.hkl) + ' of ' + famLabel(f.plane.tag) + ', at distance <i>R</i> = ' + fx(f.plane.d, 4) + ', slices off a corner: the new face is outlined in orange. ' +
        (f.skipped ? f.skipped + ' plane' + (f.skipped > 1 ? 's' : '') + ' before it missed the shape and changed nothing. ' : '') + 'Now: <b>' + nm + '</b>, ' + f.faces.length + ' faces.';
    }
    if (k === Fs.length - 1) txt += ' The remaining <b>' + Fs.after + '</b> planes all lie outside this shape (Step 10 shows by how much), so this is the final crystal.';
    set('c2s-grow-txt', txt);
    var sl = el('c2s-grow-slider'); if (sl) { sl.max = Fs.length - 1; sl.value = k; }
    set('c2s-grow-count', (k + 1) + ' / ' + Fs.length);
  }
  function uniq(faces) {
    var V = [];
    faces.forEach(function (f) { f.pts.forEach(function (p) { if (!V.some(function (q) { return la.norm(la.sub(p, q)) < 1e-7; })) V.push(p); }); });
    return V;
  }
  function step9(R) {
    R.frames = frames(R);
    state.frame = 0;
    var host = el('c2s-grow-view');
    if (host) { growView = View(host, { yaw: 2.2, pitch: 0.38 }); drawFrame(R); }
    // worked vertex
    var W = R.worked, html = '';
    if (W) {
      var nm = ['x', 'y', 'z'];
      var eqs = W.planes.map(function (p, i) {
        var terms = p.hkl.map(function (c, j) { return c === 0 ? '' : (c > 0 ? ' + ' : ' − ') + (Math.abs(c) === 1 ? '' : Math.abs(c)) + '<i>' + nm[j] + '</i>'; }).join('').replace(/^ \+ /, '').replace(/^ − /, '−');
        return '<p>' + hkl(p.hkl) + ': ' + terms + ' = <i>R</i>|<b>h</b>| = ' + fx(p.d, 4) + ' &times; ' + fx(la.norm(p.hkl), 4) + ' = ' + fx(W.rhs[i], 4) + '</p>';
      }).join('');
      html += '<p>One corner of the final shape, worked by hand. It lies on the three planes</p><div class="c2s-work">' + eqs + '</div>' +
        '<div class="c2s-eq"><i>N</i> = ' + mat(W.N, 0) + ', &ensp; <b>r</b> = ' + mat(W.rhs.map(function (x) { return [x]; }), 4) + ', &ensp; det <i>N</i> = ' + fx(W.D, 0) + '</div>' +
        '<div class="c2s-work">' + W.cols.map(function (c, i) {
          return '<p><i>' + nm[i] + '</i> = det <i>N</i><sub>' + nm[i] + '</sub> / det <i>N</i> = ' + fx(c.det, 4) + ' / ' + fx(W.D, 0) + ' = <b>' + fx(W.x[i], 4) + '</b>&emsp;(<i>N</i><sub>' + nm[i] + '</sub> is <i>N</i> with column ' + (i + 1) + ' replaced by <b>r</b>)</p>';
        }).join('') + '</div>' +
        '<p>So the corner is at ' + vec(W.x) + '. It must also satisfy every other plane: of all ' + R.shape.planes.length + ' planes, the largest value of <b>n</b>&middot;<b>x</b> &minus; <i>R</i> at this point is ' +
        fx(Math.max.apply(null, R.shape.planes.map(function (p) { return la.dot(p.n, W.x) - p.d; })), 6) + ' (zero or below means inside), and ' + W.nOn + ' planes pass exactly through it.</p>';
    }
    set('c2s-s9', html);
  }

  // ---- step 10: which faces survive ---------------------------------------------------------------------
  function step10(R, P) {
    var rows = '';
    R.families.slice(0, 14).forEach(function (f) {
      var st = f.present ? '<b>face</b>, ' + f.faceCount + ' polygons, ' + fx(100 * f.areaFraction, 1) + '% of the area'
        : f.touches ? '<b>touches</b> the shape at corners only, zero area' : 'misses by ' + fx(f.R - f.reach, 4);
      rows += '<tr><td class="dt-label">' + famLabel(f.label) + '</td><td class="dt-value">' + fx(f.R, 4) + '</td><td class="dt-value">' + fx(f.reach, 4) + '</td><td class="dt-note">' + st + '</td></tr>';
    });
    var absent = R.families.filter(function (f) { return !f.present; });
    var minm = Math.min.apply(null, absent.filter(function (f) { return !f.touches; }).map(function (f) { return f.R - f.reach; }));
    var html = '<div class="table-wrap"><table class="data-table" id="c2s-survive"><thead><tr><td>Family</td><td>Its distance <i>R</i><sub><i>f</i></sub></td><td>Reach of the shape <i>h</i><sub><i>P</i></sub>(<b>n</b><sub><i>f</i></sub>)</td><td>Result</td></tr></thead><tbody>' + rows + '</tbody></table></div>' +
      '<p>Of the ' + R.families.length + ' families, ' + R.families.filter(function (f) { return f.present; }).length + ' carry faces. For the other ' + absent.length + ', the smallest gap between the plane and the shape is ' + fx(minm, 4) +
      (absent.some(function (f) { return f.touches; }) ? ', apart from ' + absent.filter(function (f) { return f.touches; }).map(function (f) { return famLabel(f.label); }).join(', ') + ', which touches exactly.' : '.') + '</p>';
    var t = R.families.filter(function (f) { return f.touches; });
    if (t.length) html += '<div class="callout warn" data-kind="A shape exactly on a boundary">The ' + t.map(function (f) { return famLabel(f.label); }).join(', ') + ' planes pass exactly through corners of the shape (<i>R</i> = ' + fx(t[0].R, 4) +
      ' = <i>h</i><sub><i>P</i></sub>). Any growth rate for these faces slightly slower than BFDH would make them appear as small faces at those corners. For a cubic I-centred lattice this happens for every cell size, because <i>R</i><sub>100</sub>/<i>R</i><sub>110</sub> = &radic;2 exactly.</div>';
    if (P) html += pyLine((P.other_families_checked + 10) + ' families with SciPy half-space intersection on the ten widest; the narrower ' + P.other_families_checked + ' miss that shape by at least ' + fx(P.smallest_margin_other_families, 4) + '.');
    set('c2s-s10', html);
  }

  // ---- step 11: measuring ---------------------------------------------------------------------------------------
  function step11(R, P) {
    var S = R.shape, I = S.info, A = R.totalArea, html = '';
    var present = R.families.filter(function (f) { return f.present; });
    present.forEach(function (F) {
      // the member with the largest index sum, e.g. (100), (111), (11-1), (110)
      var f = S.faces.filter(function (x) { return x.tag === F.label; }).sort(function (a, b) {
        var sa = a.hkl[0] + a.hkl[1] + a.hkl[2], sb = b.hkl[0] + b.hkl[1] + b.hkl[2];
        return (sb - sa) || (b.hkl[0] - a.hkl[0]) || (b.hkl[1] - a.hkl[1]);
      })[0];
      var p = f.pts, terms = [];
      var tot = [0, 0, 0];
      for (var t = 1; t + 1 < p.length; t++) { var c = la.cross(la.sub(p[t], p[0]), la.sub(p[t + 1], p[0])); tot = la.add(tot, c); }
      html += '<p>A ' + famLabel(F.label) + ' face, ' + hkl(f.hkl) + ', is a polygon with ' + p.length + ' corners:</p><div class="c2s-work"><p>' + p.map(function (v, i) { return '<b>v</b><sub>' + (i + 1) + '</sub> = ' + vec(v); }).join('<br>') + '</p>' +
        '<p>Area = &frac12;|&Sigma;<sub><i>t</i></sub> (<b>v</b><sub><i>t</i></sub> &minus; <b>v</b><sub>1</sub>) &times; (<b>v</b><sub><i>t</i>+1</sub> &minus; <b>v</b><sub>1</sub>)| = &frac12;|' + vec(tot) + '| = <b>' + fx(f.area, 4) + '</b>, ' +
        'and ' + F.faceCount + ' such faces give ' + fx(f.area * F.faceCount, 4) + '.</p></div>';
    });
    var V = S.faces.reduce(function (s, f) { return s + f.d * f.area / 3; }, 0);
    html += '<div class="c2s-work"><p>Total area <i>A</i> = ' + present.map(function (F) { return fx(F.areaFraction * A, 4); }).join(' + ') + ' = <b>' + fx(A, 4) + '</b>; area fractions ' +
      present.map(function (F) { return famLabel(F.label) + ' ' + fx(F.areaFraction, 4); }).join(', ') + '.</p>' +
      '<p>Volume <i>V</i> = &frac13; &Sigma;<sub><i>f</i></sub> <i>R</i><sub><i>f</i></sub> <i>A</i><sub><i>f</i></sub> (a pyramid from the centre to each face) = ' +
      present.map(function (F) { return '&frac13; &times; ' + fx(F.R, 4) + ' &times; ' + fx(F.areaFraction * A, 4); }).join(' + ') + ' = <b>' + fx(V, 4) + '</b></p>' +
      '<p>Sphericity &Psi; = &pi;<sup>1/3</sup>(6<i>V</i>)<sup>2/3</sup>/<i>A</i> = ' + fx(Math.pow(Math.PI, 1 / 3), 4) + ' &times; (6 &times; ' + fx(V, 4) + ')<sup>2/3</sup> / ' + fx(A, 4) + ' = <b>' + fx(I.sphericity, 4) + '</b> (a sphere has 1, a cube 0.806).</p>' +
      '<p>Counts: ' + I.faces + ' faces, ' + I.vertices + ' corners, ' + (I.faces + I.vertices - 2) + ' edges (Euler: <i>F</i> + <i>V</i> &minus; <i>E</i> = 2).</p></div>';
    var why = '';
    var b = {}; present.forEach(function (F) { b[F.base] = 1; });
    var bk = Object.keys(b).sort().join(' ');
    if (bk === '{100} {111}') {
      var hex = S.faces.filter(function (f) { return /111/.test(f.tag); })[0].pts.length;
      why = 'Only {100} and {111} faces are present. The {111} faces are ' + (hex === 6 ? 'hexagons, so the corners of an <b>octahedron</b> have been cut off by small {100} squares' : 'triangles, so the corners of a <b>cube</b> have been cut off') + '.';
      var r100 = R.rates['{100}'], r111 = R.rates['{111}'] || R.rates['{111}+'];
      if (hex === 6 && Math.abs(r100 / r111 - 2 / Math.sqrt(3)) < 1e-9) {
        // closed-form check: at R100/R111 = 2/sqrt3 every edge has the same length e
        var sq = S.faces.filter(function (f) { return f.tag === '{100}'; })[0].pts, e = la.norm(la.sub(sq[1], sq[0]));
        why += ' A closed-form check by hand: with <i>R</i><sub>100</sub>/<i>R</i><sub>111</sub> = 2/&radic;3 every edge has the same length, <i>e</i> = ' + fx(e, 4) +
          ', so this is the regular (Archimedean) truncated octahedron. Its six squares have area 6<i>e</i>&sup2; and its eight hexagons 8 &times; (3&radic;3/2)<i>e</i>&sup2; = 12&radic;3 <i>e</i>&sup2;, ' +
          'so the {100} fraction is 6/(6 + 12&radic;3) = ' + fx(6 / (6 + 12 * Math.sqrt(3)), 4) + ' and the total area is (6 + 12&radic;3) &times; ' + fx(e * e, 4) + ' = ' + fx((6 + 12 * Math.sqrt(3)) * e * e, 4) +
          ', the same as the sums above. Its volume is 8&radic;2 <i>e</i>&sup3; = ' + fx(8 * Math.SQRT2 * e * e * e, 4) + '.';
      }
    } else if (bk === '{110}') {
      var rh = S.faces[0].pts, d1 = la.norm(la.sub(rh[2], rh[0])), d2 = la.norm(la.sub(rh[3], rh[1]));
      why = 'Only the twelve {110} faces are present, each a rhombus. A closed-form check by hand: the diagonals of each rhombus are ' + fx(Math.max(d1, d2), 4) + ' and ' + fx(Math.min(d1, d2), 4) +
        ' (ratio ' + fx(Math.max(d1, d2) / Math.min(d1, d2), 4) + ' = &radic;2), so each face has area &frac12; &times; ' + fx(d1, 4) + ' &times; ' + fx(d2, 4) + ' = ' + fx(d1 * d2 / 2, 4) +
        ' and twelve give ' + fx(6 * d1 * d2, 4) + '; the volume of a rhombic dodecahedron with face distance 1 is 4&radic;2 = ' + fx(4 * Math.SQRT2, 4) + '.';
    } else if (bk === '{100}') why = 'Only the six {100} faces are present.';
    else if (bk === '{111}') why = 'Only the {111} faces are present.';
    html += '<p>Name: <b>' + S.name + '</b>. ' + why + '</p>';
    if (P) html += pyLine(P.shape.name + ', ' + P.shape.n_faces + ' faces, ' + P.shape.n_vertices + ' corners, &Psi; = ' + fx(P.shape.sphericity, 4) + ', area fractions ' +
      Object.keys(P.shape.face_area_fraction).sort().map(function (k) { return famLabel(k) + ' ' + fx(P.shape.face_area_fraction[k], 4); }).join(', ') + '.');
    set('c2s-s11', html);
    var host = el('c2s-final-view');
    if (host) {
      finalView = View(host, { yaw: 2.2, pitch: 0.38 });
      finalView.draw = function () { drawShape(finalView, S.faces, { labels: true, minLabelArea: 0.05, label: 'final BFDH shape: ' + S.name }); };
      finalView.draw();
    }
  }

  // ---- unit cell picture (steps 1-3) ---------------------------------------------------------------------------
  var cellView = null;
  function cellPicture(R) {
    var host = el('c2s-cell-view');
    if (!host || !R.conv) return;
    cellView = View(host, { yaw: 0.5, pitch: 0.3 });
    var a = R.a, half = [a / 2, a / 2, a / 2], Minv = la.inv3(R.conv.M);
    var prim = R.conv.key === 'P' ? null : Minv.map(function (r) { return la.scale(r, a); });
    var metals = { Zn: 1, Cu: 1, Zr: 1, Mg: 1, Co: 1, Ni: 1, Fe: 1, Cr: 1, Al: 1, Cd: 1, Mn: 1, Ti: 1 };
    cellView.draw = function () {
      var W = 360, H = 320, s = cellView.svg(W, H, 'unit cell'), k = 0.5 * Math.min(W, H) / a;
      function P(p) { var q = cellView.rot(la.sub(p, half)); return [W / 2 + k * q[0], H / 2 - k * q[2], q[1]]; }
      var items = [];
      R.C.X.forEach(function (x, i) {
        var e = R.C.els[i], p = P(la.scale(x, a)), m = metals[e];
        if (e === 'H') return;
        items.push({ z: p[2], f: function () { node('circle', { cx: p[0].toFixed(1), cy: p[1].toFixed(1), r: m ? 3.6 : 1.5, style: m ? 'fill:var(--node);stroke:var(--surface-0);stroke-width:.8' : 'fill:var(--muted, #64748b);fill-opacity:.55' }, s); } });
      });
      items.sort(function (u, v) { return v.z - u.z; }).forEach(function (it) { it.f(); });
      var E = [];
      [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1]].forEach(function (u) {
        [0, 1, 2].forEach(function (ax) { if (!u[ax]) { var v = u.slice(); v[ax] = 1; E.push([la.scale(u, a), la.scale(v, a), 'cube']); } });
      });
      if (prim) {
        var o = [0, 0, 0], p1 = prim[0], p2 = prim[1], p3 = prim[2];
        var C8 = [o, p1, p2, p3, la.add(p1, p2), la.add(p1, p3), la.add(p2, p3), la.add(la.add(p1, p2), p3)];
        [[0, 1], [0, 2], [0, 3], [1, 4], [1, 5], [2, 4], [2, 6], [3, 5], [3, 6], [4, 7], [5, 7], [6, 7]].forEach(function (e) { E.push([C8[e[0]], C8[e[1]], 'prim']); });
      }
      E.forEach(function (e) {
        var p = P(e[0]), q = P(e[1]);
        node('line', { x1: p[0].toFixed(1), y1: p[1].toFixed(1), x2: q[0].toFixed(1), y2: q[1].toFixed(1),
          style: e[2] === 'cube' ? 'stroke:var(--linker);stroke-width:1.4' : 'stroke:var(--warn, #d97706);stroke-width:1.6;stroke-dasharray:5 3' }, s);
      });
    };
    cellView.draw();
    set('c2s-cell-cap', 'Blue: the conventional cube, edge ' + fx(a, 3) + ' &Aring;. ' + (prim ? 'Orange dashed: the cell actually stored in the file (edges ' + fx(R.cif.cell[0], 3) + ' &Aring; at ' + fx(R.cif.cell[3], 1) + '&deg;), drawn from the same corner; four of them fill the cube. ' : 'The file stores this cube directly. ') +
      'Red: metal atoms; grey: the other non-hydrogen atoms, all ' + R.C.els.length + ' atoms placed from the file\'s fractional coordinates. Drag to rotate.');
  }

  // ---- step 12: the morphology map ---------------------------------------------------------------------------------
  var mapView = null, mapState = { x: 1.4142, y: 0.866 };
  function mapFamilies() {
    return CS.families('P', 'm-3m', 1, 1).filter(function (f) { return f.sumSq <= 3; });   // {100}, {110}, {111}
  }
  function mapShape(x, y) {
    var F = mapFamilies(), r = { '{100}': 1, '{110}': x, '{111}': y };
    var S = CS.build(F, r);
    var tot = S.faces.reduce(function (s, f) { return s + f.area; }, 0), fr0 = { '{100}': 0, '{110}': 0, '{111}': 0 };
    S.faces.forEach(function (f) { fr0[f.tag] += f.area / tot; });
    S.fr = fr0;
    return S;
  }
  function parseRGB(s, fb) { var m = /rgba?\((\d+)[, ]+(\d+)[, ]+(\d+)/.exec(s || ''); return m ? [+m[1], +m[2], +m[3]] : fb; }
  var mapCache = null;
  function drawMap(R) {
    var host = el('c2s-map');
    if (!host) return;
    var W = 380, H = 360, padL = 46, padB = 40, padT = 12, padR = 12, x0 = 0.4, x1 = 2.2, y0 = 0.3, y1 = 2.1, N = 46;
    var X = function (x) { return padL + (x - x0) / (x1 - x0) * (W - padL - padR); };
    var Y = function (y) { return H - padB - (y - y0) / (y1 - y0) * (H - padB - padT); };
    var pal = window.PAL || {};
    var c100 = parseRGB(pal.linker, [29, 78, 216]), c111 = parseRGB(pal.node, [185, 28, 28]), c110 = parseRGB(pal.good, [4, 120, 87]);
    var bg = parseRGB(pal.surface, [255, 255, 255]);
    if (!mapCache) {
      mapCache = [];
      for (var i = 0; i < N; i++) for (var j = 0; j < N; j++) {
        var x = x0 + (i + 0.5) / N * (x1 - x0), y = y0 + (j + 0.5) / N * (y1 - y0), S = mapShape(x, y);
        mapCache.push({ x: x, y: y, fr: S.fr });
      }
    }
    host.innerHTML = '';
    var svg = document.createElementNS(SVGNS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H); svg.setAttribute('class', 'c2s-svg c2s-flat');
    svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', 'morphology map of a cubic crystal');
    host.appendChild(svg);
    var cw = (W - padL - padR) / N, ch = (H - padB - padT) / N;
    mapCache.forEach(function (c) {
      var f = c.fr, rgb = [0, 1, 2].map(function (k) { return Math.round(0.58 * bg[k] + 0.42 * (f['{100}'] * c100[k] + f['{111}'] * c111[k] + f['{110}'] * c110[k])); });
      node('rect', { x: (X(c.x) - cw / 2).toFixed(2), y: (Y(c.y) - ch / 2).toFixed(2), width: (cw + 0.6).toFixed(2), height: (ch + 0.6).toFixed(2),
        style: 'fill:rgb(' + rgb.join(',') + ')' }, svg);
    });
    var r2 = Math.SQRT2, r3 = Math.sqrt(3), r32 = Math.sqrt(1.5);
    // exact region boundaries (derived in the text): cube, cuboctahedron line, octahedron, rhombic dodecahedron
    var lines = [[[r2, r3], [x1, r3]], [[r2, r3], [r2, y1]],
                 [[r2, 2 / r3], [x1, 2 / r3]],
                 [[1 / r2, 1 / r3], [x1, 1 / r3]], [[x0, x0 / r32], [1 / r2, 1 / r3]],
                 [[1 / r2, r32 / r2], [1 / r2, y1]], [[x0, r32 * x0], [1 / r2, r32 / r2]]];
    lines.forEach(function (L) { node('line', { x1: X(L[0][0]), y1: Y(L[0][1]), x2: X(L[1][0]), y2: Y(L[1][1]), style: 'stroke:var(--text);stroke-width:1.1' }, svg); });
    [['cube', 1.8, 1.95], ['octahedron', 1.65, 0.42], ['rhombic dodecahedron', 0.43, 2.0, 'start'], ['truncated octahedron', 1.8, 0.72], ['truncated cube', 1.8, 1.45], ['cuboctahedron (line)', 1.83, 2 / r3 + 0.06]].forEach(function (t) {
      var e = node('text', { x: X(t[1]), y: Y(t[2]), 'text-anchor': t[3] || 'middle', style: 'font-size:10.5px;fill:var(--text);paint-order:stroke;stroke:var(--surface-0);stroke-width:3px' }, svg);
      e.textContent = t[0];
    });
    // axes
    node('line', { x1: X(x0), y1: Y(y0), x2: X(x1), y2: Y(y0), style: 'stroke:var(--text);stroke-width:1' }, svg);
    node('line', { x1: X(x0), y1: Y(y0), x2: X(x0), y2: Y(y1), style: 'stroke:var(--text);stroke-width:1' }, svg);
    [[0.5, '0.5'], [1 / r2, '1/√2'], [1, '1'], [r2, '√2'], [2, '2']].forEach(function (t) {
      node('line', { x1: X(t[0]), y1: Y(y0), x2: X(t[0]), y2: Y(y0) + 4, style: 'stroke:var(--text)' }, svg);
      var e = node('text', { x: X(t[0]), y: Y(y0) + 15, 'text-anchor': 'middle', style: 'font-size:10px;fill:var(--text)' }, svg); e.textContent = t[1];
    });
    [[1 / r3, '1/√3'], [1, '1'], [2 / r3, '2/√3'], [r3, '√3'], [2, '2']].forEach(function (t) {
      node('line', { x1: X(x0) - 4, y1: Y(t[0]), x2: X(x0), y2: Y(t[0]), style: 'stroke:var(--text)' }, svg);
      var e = node('text', { x: X(x0) - 6, y: Y(t[0]) + 3.5, 'text-anchor': 'end', style: 'font-size:10px;fill:var(--text)' }, svg); e.textContent = t[1];
    });
    var ax = node('text', { x: (X(x0) + X(x1)) / 2, y: H - 6, 'text-anchor': 'middle', style: 'font-size:11px;fill:var(--text)' }, svg); ax.textContent = 'x = R110 / R100';
    var ay = node('text', { x: 11, y: (Y(y0) + Y(y1)) / 2, 'text-anchor': 'middle', transform: 'rotate(-90 11 ' + (Y(y0) + Y(y1)) / 2 + ')', style: 'font-size:11px;fill:var(--text)' }, svg); ay.textContent = 'y = R111 / R100';
    // this structure's BFDH point
    if (R && R.rates && R.rates['{100}']) {
      var bx = R.rates['{110}'] / R.rates['{100}'], by = (R.rates['{111}'] || R.rates['{111}+']) / R.rates['{100}'];
      if (bx >= x0 && bx <= x1 && by >= y0 && by <= y1) {
        node('rect', { x: X(bx) - 5, y: Y(by) - 5, width: 10, height: 10, transform: 'rotate(45 ' + X(bx) + ' ' + Y(by) + ')', style: 'fill:var(--surface-0);stroke:var(--text);stroke-width:2' }, svg);
        var tb = node('text', { x: X(bx) - 9, y: Y(by) - 8, 'text-anchor': 'end', style: 'font-size:10.5px;fill:var(--text);paint-order:stroke;stroke:var(--surface-0);stroke-width:3px' }, svg);
        tb.textContent = 'BFDH ' + state.name;
      }
    }
    node('circle', { cx: X(mapState.x), cy: Y(mapState.y), r: 6, style: 'fill:var(--warn, #d97706);stroke:var(--surface-0);stroke-width:2' }, svg);
    function pick(e) {
      var rc = svg.getBoundingClientRect(), sx = (e.clientX - rc.left) / rc.width * W, sy = (e.clientY - rc.top) / rc.height * H;
      mapState.x = Math.max(x0, Math.min(x1, x0 + (sx - padL) / (W - padL - padR) * (x1 - x0)));
      mapState.y = Math.max(y0, Math.min(y1, y0 + (H - padB - sy) / (H - padB - padT) * (y1 - y0)));
      drawMap(R); mapPreview();
    }
    var down = false;
    svg.addEventListener('pointerdown', function (e) { down = true; pick(e); });
    svg.addEventListener('pointermove', function (e) { if (down) pick(e); });
    svg.addEventListener('pointerup', function () { down = false; });
  }
  function mapPreview() {
    var host = el('c2s-map-view');
    if (!host) return;
    if (!mapView) mapView = View(host, { yaw: 0.62, pitch: 0.38 });
    var S = mapShape(mapState.x, mapState.y);
    mapView.draw = function () { drawShape(mapView, S.faces, { label: 'shape at the chosen point: ' + S.name }); };
    mapView.draw();
    set('c2s-map-txt', '<i>x</i> = ' + fx(mapState.x, 3) + ', <i>y</i> = ' + fx(mapState.y, 3) + ': <b>' + S.name + '</b>; area {100} ' + fx(S.fr['{100}'], 3) + ', {110} ' + fx(S.fr['{110}'], 3) + ', {111} ' + fx(S.fr['{111}'], 3) + '.');
  }

  // ---- summary line at the top ---------------------------------------------------------------------------------------
  function summary(R) {
    if (R.stop) { set('c2s-summary', '<p class="c2s-stop">' + R.stop + '</p>'); return; }
    var lead = R.families[0];
    set('c2s-summary', '<div class="c2s-chain">' + [
      ['CIF', R.cif.atoms.length + ' atoms, ' + fx(R.cif.cell[0], 2) + ' &Aring;, ' + fx(R.cif.cell[3], 0) + '&deg;'],
      ['Lattice', 'cubic, <i>a</i> = ' + fx(R.a, 3) + ' &Aring;'],
      ['Symmetry', R.sg.sg || (R.centring + ' ' + R.pointGroup)],
      ['Widest planes', famLabel(lead.label) + ', <i>d</i><sub>eff</sub> = ' + fx(lead.dEff, 2) + ' &Aring;'],
      ['Shape', R.shape.name]
    ].map(function (c) { return '<div class="c2s-box"><div class="c2s-k">' + c[0] + '</div><div class="c2s-v">' + c[1] + '</div></div>'; }).join('<div class="c2s-arrow" aria-hidden="true">&rarr;</div>') + '</div>' +
      '<p class="sm">Computed in ' + R.ms + ' ms in this browser by <code>mof_cif_shape.js</code>.</p>');
  }

  // ---- run everything ---------------------------------------------------------------------------------------------------
  function render() {
    var R;
    try { R = CS.run(state.text, { snapshots: true }); }
    catch (e) { set('c2s-summary', '<p class="c2s-stop">This file could not be read: ' + e.message + '</p>'); return; }
    state.R = R;
    var P = py(state.name);
    summary(R); step1(R); step2(R); step3(R, P); cellPicture(R);
    var later = ['c2s-s4', 'c2s-s5', 'c2s-s6', 'c2s-s7', 'c2s-s8', 'c2s-s9', 'c2s-s10', 'c2s-s11'];
    if (R.stop) { later.forEach(function (id) { set(id, '<p class="c2s-stop">Not reached: ' + R.stop + '</p>'); }); return; }
    step4(R, P); step5(R, P); step6(R, P); latticePicture(R, state.planes || '100'); step7(R, P); step8(R, P); step9(R); step10(R, P); step11(R, P);
    mapState.x = R.rates['{110}'] / R.rates['{100}'];
    mapState.y = (R.rates['{111}'] || R.rates['{111}+']) / R.rates['{100}'];
    drawMap(R); mapPreview();
  }

  function choose(name) {
    state.name = name; state.bundled = true;
    state.text = (window.DEFAULT_CIFS || {})[name];
    document.querySelectorAll('#c2s-structs .struct-tab').forEach(function (b) { b.classList.toggle('active', b.getAttribute('data-name') === name); });
    render();
  }

  function init() {
    if (!el('c2s-summary') || !CS) return;
    var bar = el('c2s-structs');
    STRUCTS.forEach(function (n) {
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'struct-tab'; b.textContent = n; b.setAttribute('data-name', n);
      b.addEventListener('click', function () { choose(n); });
      bar.appendChild(b);
    });
    var inp = el('c2s-file');
    if (inp) inp.addEventListener('change', function () {
      var f = inp.files && inp.files[0];
      if (!f) return;
      var rd = new FileReader();
      rd.onload = function () {
        state.name = f.name; state.bundled = false; state.text = String(rd.result);
        document.querySelectorAll('#c2s-structs .struct-tab').forEach(function (b) { b.classList.remove('active'); });
        render();
      };
      rd.readAsText(f);
    });
    ['100', '110'].forEach(function (w) {
      var b = el('c2s-planes-' + w);
      if (b) b.addEventListener('click', function () {
        state.planes = w;
        ['100', '110'].forEach(function (q) { var x = el('c2s-planes-' + q); if (x) x.classList.toggle('active', q === w); });
        latticePicture(state.R, w);
      });
    });
    var sl = el('c2s-grow-slider');
    if (sl) sl.addEventListener('input', function () { state.frame = +sl.value; drawFrame(state.R); });
    var play = el('c2s-grow-play');
    if (play) play.addEventListener('click', function () {
      if (state.timer) { clearInterval(state.timer); state.timer = null; play.textContent = 'Play'; return; }
      if (state.frame >= state.R.frames.length - 1) state.frame = 0;
      play.textContent = 'Pause';
      drawFrame(state.R);
      state.timer = setInterval(function () {
        if (state.frame >= state.R.frames.length - 1) { clearInterval(state.timer); state.timer = null; play.textContent = 'Play'; return; }
        state.frame++; drawFrame(state.R);
      }, 900);
    });
    [['c2s-preset-bfdh', null], ['c2s-preset-cube', [2, 2]], ['c2s-preset-oct', [2, 0.45]], ['c2s-preset-rd', [0.55, 2]], ['c2s-preset-cubo', [2, 2 / Math.sqrt(3)]]].forEach(function (p) {
      var b = el(p[0]);
      if (b) b.addEventListener('click', function () {
        var R = state.R;
        if (p[1]) { mapState.x = p[1][0]; mapState.y = p[1][1]; }
        else { mapState.x = R.rates['{110}'] / R.rates['{100}']; mapState.y = (R.rates['{111}'] || R.rates['{111}+']) / R.rates['{100}']; }
        drawMap(R); mapPreview();
      });
    });
    window.addEventListener('themechange', function () { mapCache = null; if (state.R) render(); });
    choose('MOF-5');
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
  window.CIF_SHAPE_PAGE = { state: state, choose: choose, mapShape: mapShape, surd: surd };
})();
