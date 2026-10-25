/* =====================================================================
   morphology_page.js — drives morphology.html.

   Fills three tables and the shape explorer from mof_morphology.js when the
   page loads. Nothing on this page is typed in as a result: the only inputs
   are the lattice centring, point group and cell edge of each structure
   (from spglib in Python, listed in MORPH.STRUCTURES).

   The 3D view is drawn as SVG, not WebGL: a convex polytope needs only its
   front-facing faces, drawn back to front, so SVG is enough and it works
   on every device, with no graphics driver and no network.
   ===================================================================== */
(function () {
  'use strict';
  var M = window.MORPH;
  var SVGNS = 'http://www.w3.org/2000/svg';
  // face colours: CSS variables only, so the view follows the site theme
  var FILL = { '{100}': 'var(--linker)', '{111}': 'var(--node)', '{111}+': 'var(--node)',
               '{111}-': 'var(--node-line)', '{110}': 'var(--good)' };

  function el(tag, attrs, html) {
    var e = document.createElement(tag);
    for (var k in (attrs || {})) e.setAttribute(k, attrs[k]);
    if (html !== undefined) e.innerHTML = html;
    return e;
  }
  function f3(x) { return (Math.abs(x) < 5e-4 ? 0 : x).toFixed(3); }
  function famHTML(t) { return t.replace('{', '{').replace('+', '<sub>+</sub>').replace(/-$/, '<sub>&minus;</sub>'); }

  // ---- tables computed at load ------------------------------------------
  function bfdhTable(host) {
    var rows = '';
    Object.keys(M.STRUCTURES).forEach(function (name) {
      var s = M.STRUCTURES[name];
      var fams = M.familyList('m-3m').map(function (F) {
        var e = M.dEff(F.hkl, s.centring, s.a);
        return { label: F.base, d: e.dEff, n: e.n };
      }).sort(function (a, b) { return b.d - a.d; });
      var S = M.shape(M.bfdhRates(s.centring, s.a, s.pointGroup), s.pointGroup);
      rows += '<tr><td class="dt-label">' + name + '</td>' +
        '<td class="dt-note">' + s.spacegroup + ' (' + s.number + ')</td>' +
        '<td class="dt-value">' + s.a.toFixed(3) + '</td>' +
        '<td class="dt-note">' + fams.map(function (F) {
          return F.label + ' ' + F.d.toFixed(2) + (F.n > 1 ? ' (n=' + F.n + ')' : '');
        }).join(', ') + '</td>' +
        '<td class="dt-note">' + S.name + '</td>' +
        '<td class="dt-value">' + S.info.sphericity.toFixed(3) + '</td></tr>';
    });
    host.innerHTML = '<div class="table-wrap"><table class="data-table" id="morph-bfdh"><thead><tr><td>Structure</td><td>Space group</td>' +
      '<td><i>a</i> (&Aring;)</td><td><i>d</i><sub>eff</sub> (&Aring;), largest first</td>' +
      '<td>BFDH shape</td><td>&Psi;</td></tr></thead><tbody>' + rows + '</tbody></table></div>' +
      '<p class="sm">n is the order of the first allowed reflection: n = 2 means the family\'s own reflection is forbidden by centring.</p>';
  }

  function thresholdTable(host) {
    var r3 = Math.sqrt(3), rows = '';
    [[3, 'above &radic;3'], [1.6, ''], [2 / r3, '2/&radic;3'], [1.0, ''], [0.8, ''], [0.98 / r3, 'below 1/&radic;3']].forEach(function (p) {
      var S = M.shape({ '{100}': 1, '{111}': p[0] }, 'm-3m'), I = S.info;
      rows += '<tr><td class="dt-value">' + p[0].toFixed(3) + (p[1] ? ' <span class="sm">(' + p[1] + ')</span>' : '') + '</td>' +
        '<td class="dt-note">' + S.name + '</td><td class="dt-value">' + I.faces + '</td><td class="dt-value">' + I.vertices + '</td>' +
        '<td class="dt-value">' + f3(I.sphericity) + '</td><td class="dt-value">' + f3(I.kappa2) + '</td>' +
        '<td class="dt-value">' + f3(I.Q4) + '</td><td class="dt-value">' + f3(I.Q6) + '</td></tr>';
    });
    host.innerHTML = '<div class="table-wrap"><table class="data-table" id="morph-thresholds"><thead><tr><td><i>t</i> = <i>R</i><sub>111</sub>/<i>R</i><sub>100</sub></td>' +
      '<td>Shape</td><td>Faces</td><td>Vertices</td><td>&Psi;</td><td>&kappa;&sup2;</td><td><i>Q</i><sub>4</sub></td><td><i>Q</i><sub>6</sub></td></tr></thead><tbody>' +
      rows + '</tbody></table></div>';
  }

  function attachTable(host) {
    var rows = '';
    [['pcu', 'MOF-5'], ['fcu', 'UiO-66 / UiO-67']].forEach(function (p) {
      var c = [[1, 0, 0], [1, 1, 0], [1, 1, 1]].map(function (f) { return M.attachmentNumber(p[0], f); });
      var S = M.shape(M.graphRates(p[0], 0.6), 'm-3m');
      rows += '<tr><td class="dt-label">' + p[0] + ' (' + p[1] + ')</td><td class="dt-value">' + c[0] + '</td><td class="dt-value">' +
        c[1] + '</td><td class="dt-value">' + c[2] + '</td><td class="dt-note">' + S.name + '</td></tr>';
    });
    host.innerHTML = '<div class="table-wrap"><table class="data-table" id="morph-attach"><thead><tr><td>Node net</td><td><i>c</i><sub>100</sub></td>' +
      '<td><i>c</i><sub>110</sub></td><td><i>c</i><sub>111</sub></td><td>Shape for &beta; = 0.6</td></tr></thead><tbody>' + rows + '</tbody></table></div>';
  }

  // ---- the explorer ------------------------------------------------------
  var state = { struct: 'MOF-5', r100: 1, r110: 1.633, r111p: 1, r111m: 1, linked: true, yaw: 0.75, pitch: 0.42 };

  var SLIDERS = [
    { key: 'r111p', label: 'R<sub>111</sub> / R<sub>100</sub>', min: 0.3, max: 3.2 },
    { key: 'r111m', label: 'R<sub>111&minus;</sub> / R<sub>100</sub> (second half of {111})', min: 0.3, max: 3.2, tetra: true },
    { key: 'r110', label: 'R<sub>110</sub> / R<sub>100</sub>', min: 0.4, max: 3.2 }
  ];

  function rates() {
    var s = M.STRUCTURES[state.struct], r = { '{100}': 1, '{110}': state.r110 };
    if (s.pointGroup === '-43m' && !state.linked) { r['{111}+'] = state.r111p; r['{111}-'] = state.r111m; }
    else r['{111}'] = state.r111p;
    return r;
  }

  function current() { return M.shape(rates(), M.STRUCTURES[state.struct].pointGroup); }

  function rotate(v) {
    var cy = Math.cos(state.yaw), sy = Math.sin(state.yaw), cp = Math.cos(state.pitch), sp = Math.sin(state.pitch);
    var x = cy * v[0] - sy * v[1], y = sy * v[0] + cy * v[1], z = v[2];
    return [x, cp * y - sp * z, sp * y + cp * z];        // screen: x right, z up, y into the page
  }

  function draw(S) {
    var host = document.getElementById('morph-view');
    if (!host) return;
    host.innerHTML = '';
    var W = 360, H = 320, R = 0;
    S.V.forEach(function (v) { R = Math.max(R, Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])); });
    var k = 0.42 * Math.min(W, H) / (R || 1);
    var svg = document.createElementNS(SVGNS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    svg.setAttribute('class', 'morph-svg');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'Crystal shape: ' + S.name);
    svg.style.cssText = 'width:100%;max-width:420px;height:auto;display:block;margin:6px auto;cursor:grab;touch-action:none';
    var faces = S.faces.map(function (f) {
      var n = rotate(f.n), pts = f.poly.map(rotate);
      var depth = pts.reduce(function (s, p) { return s + p[1]; }, 0) / pts.length;
      return { f: f, n: n, pts: pts, depth: depth };
    }).filter(function (F) { return F.n[1] < 0; })          // faces turned towards the viewer
      .sort(function (a, b) { return b.depth - a.depth; });
    faces.forEach(function (F) {
      var light = 0.55 + 0.45 * Math.max(0, -F.n[1] * 0.75 + F.n[2] * 0.45 + F.n[0] * 0.2);
      var poly = document.createElementNS(SVGNS, 'polygon');
      poly.setAttribute('points', F.pts.map(function (p) { return (W / 2 + k * p[0]).toFixed(1) + ',' + (H / 2 - k * p[2]).toFixed(1); }).join(' '));
      poly.setAttribute('style', 'fill:' + (FILL[F.f.tag] || 'var(--accent2)') + ';fill-opacity:' + light.toFixed(2) +
        ';stroke:var(--text);stroke-width:0.8;stroke-linejoin:round');
      var title = document.createElementNS(SVGNS, 'title');
      title.textContent = F.f.tag + ' face';
      poly.appendChild(title);
      svg.appendChild(poly);
    });
    // drag to rotate
    var drag = null;
    svg.addEventListener('pointerdown', function (e) { drag = [e.clientX, e.clientY]; svg.setPointerCapture && svg.setPointerCapture(e.pointerId); });
    svg.addEventListener('pointermove', function (e) {
      if (!drag) return;
      state.yaw += (e.clientX - drag[0]) * 0.01; state.pitch = Math.max(-1.4, Math.min(1.4, state.pitch + (e.clientY - drag[1]) * 0.01));
      drag = [e.clientX, e.clientY]; draw(S);
    });
    svg.addEventListener('pointerup', function () { drag = null; });
    host.appendChild(svg);
    var legend = el('div', { class: 'legend sm', style: 'text-align:center' });
    var seen = {};
    S.faces.forEach(function (f) { seen[f.tag] = true; });
    legend.innerHTML = Object.keys(seen).sort().map(function (t) {
      return '<span style="display:inline-block;margin:0 8px"><span style="display:inline-block;width:11px;height:11px;border-radius:2px;vertical-align:-1px;background:' +
        (FILL[t] || 'var(--accent2)') + '"></span> ' + famHTML(t) + '</span>';
    }).join('') + ' &middot; drag to rotate';
    host.appendChild(legend);
  }

  function readout(S) {
    var host = document.getElementById('morph-readout'), I = S.info;
    if (!host) return;
    var fr = Object.keys(I.fraction).sort().map(function (t) { return famHTML(t) + ' ' + (100 * I.fraction[t]).toFixed(0) + '%'; }).join(', ');
    host.innerHTML = '<p class="sd" style="text-align:center;margin:4px 0 10px"><b id="morph-name">' + S.name + '</b></p>' +
      '<div class="table-wrap"><table class="data-table" id="morph-numbers"><tbody>' +
      '<tr><td class="dt-label">Faces / vertices</td><td class="dt-value">' + I.faces + ' / ' + I.vertices + '</td>' +
      '<td class="dt-label">Face area</td><td class="dt-note">' + fr + '</td></tr>' +
      '<tr><td class="dt-label">Sphericity &Psi;</td><td class="dt-value">' + f3(I.sphericity) + '</td>' +
      '<td class="dt-label">Asphericity &kappa;&sup2;</td><td class="dt-value">' + f3(I.kappa2) + '</td></tr>' +
      '<tr><td class="dt-label"><i>Q</i><sub>4</sub> / <i>Q</i><sub>6</sub></td><td class="dt-value">' + f3(I.Q4) + ' / ' + f3(I.Q6) + '</td>' +
      '<td class="dt-label"><i>Q</i><sub>3</sub> (non-zero only without inversion)</td><td class="dt-value">' + f3(I.Q3) + '</td></tr>' +
      '</tbody></table></div>';
  }

  function update() { var S = current(); draw(S); readout(S); syncSliders(); }

  function syncSliders() {
    var tetra = M.STRUCTURES[state.struct].pointGroup === '-43m';
    SLIDERS.forEach(function (s) {
      var row = document.getElementById('morph-row-' + s.key);
      if (!row) return;
      if (s.tetra) row.style.display = (tetra && !state.linked) ? '' : 'none';
      row.querySelector('input').value = Math.log(state[s.key]);
      row.querySelector('output').textContent = state[s.key].toFixed(3);
    });
    var tog = document.getElementById('morph-split');
    if (tog) { tog.parentNode.style.display = tetra ? '' : 'none'; tog.checked = !state.linked; }
  }

  var PRESETS = [
    ['BFDH (lattice only)', function () {
      var s = M.STRUCTURES[state.struct], r = M.bfdhRates(s.centring, s.a, s.pointGroup);
      state.linked = true; state.r110 = r['{110}'] / r['{100}'];
      state.r111p = state.r111m = (r['{111}'] || r['{111}+']) / r['{100}'];
    }],
    ['Cube', function () { state.linked = true; state.r111p = state.r111m = 3; state.r110 = 3; }],
    ['Cuboctahedron', function () { state.linked = true; state.r111p = state.r111m = 2 / Math.sqrt(3); state.r110 = 3; }],
    ['Octahedron', function () { state.linked = true; state.r111p = state.r111m = 0.55; state.r110 = 3; }],
    ['Rhombic dodecahedron', function () { state.linked = true; state.r111p = state.r111m = 3; state.r110 = 0.6; }],
    ['Tetrahedron', function () {
      if (M.STRUCTURES[state.struct].pointGroup !== '-43m') state.struct = 'UiO-66';
      state.linked = false; state.r111p = 0.3; state.r111m = 1; state.r110 = 3;
      state.yaw = -0.8; state.pitch = 0.6;          // shows three of the four faces
    }],
    ['Graph rule', function () {
      var net = M.STRUCTURES[state.struct].net;
      if (net !== 'pcu' && net !== 'fcu') { state.struct = 'MOF-5'; net = 'pcu'; }
      var r = M.graphRates(net, 0.6);
      state.linked = true; state.r110 = r['{110}'] / r['{100}']; state.r111p = state.r111m = r['{111}'] / r['{100}'];
    }]
  ];

  function buildExplorer() {
    var structs = document.getElementById('morph-structs'), presets = document.getElementById('morph-presets'),
        sliders = document.getElementById('morph-sliders');
    if (!structs || !presets || !sliders) return;
    Object.keys(M.STRUCTURES).forEach(function (name) {
      var s = M.STRUCTURES[name];
      var b = el('button', { type: 'button', class: 'mode-btn', 'data-struct': name, title: s.spacegroup + ', ' + s.net + ' net' }, name);
      b.addEventListener('click', function () {
        state.struct = name; if (M.STRUCTURES[name].pointGroup !== '-43m') state.linked = true;
        structs.querySelectorAll('.mode-btn').forEach(function (x) { x.classList.toggle('active', x === b); });
        update();
      });
      if (name === state.struct) b.classList.add('active');
      structs.appendChild(b);
    });
    PRESETS.forEach(function (p) {
      var b = el('button', { type: 'button', class: 'mode-btn' }, p[0]);
      b.addEventListener('click', function () {
        p[1]();
        structs.querySelectorAll('.mode-btn').forEach(function (x) { x.classList.toggle('active', x.getAttribute('data-struct') === state.struct); });
        update();
      });
      presets.appendChild(b);
    });
    SLIDERS.forEach(function (s) {
      var row = el('div', { id: 'morph-row-' + s.key, class: 'toolbar' });
      row.innerHTML = '<label class="lbl" for="morph-in-' + s.key + '" style="min-width:250px">' + s.label + '</label>' +
        '<input id="morph-in-' + s.key + '" type="range" min="' + Math.log(s.min) + '" max="' + Math.log(s.max) + '" step="0.005" style="flex:1;min-width:140px">' +
        '<output style="min-width:52px;font-variant-numeric:tabular-nums"></output>';
      row.querySelector('input').addEventListener('input', function (e) {
        state[s.key] = Math.exp(parseFloat(e.target.value));
        if (s.key === 'r111p' && state.linked) state.r111m = state.r111p;
        update();
      });
      sliders.appendChild(row);
    });
    var tog = el('div', { class: 'toolbar' });
    tog.innerHTML = '<label class="sm"><input id="morph-split" type="checkbox"> Let the two halves of {111} grow at different rates (allowed only without an inversion centre, -43m)</label>';
    sliders.appendChild(tog);
    document.getElementById('morph-split').addEventListener('change', function (e) {
      state.linked = !e.target.checked; if (state.linked) state.r111m = state.r111p; update();
    });
    PRESETS[0][1]();
    update();
  }

  function init() {
    if (!M) return;
    var t;
    if ((t = document.getElementById('morph-bfdh-table'))) bfdhTable(t);
    if ((t = document.getElementById('morph-threshold-table'))) thresholdTable(t);
    if ((t = document.getElementById('morph-attach-table'))) attachTable(t);
    buildExplorer();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
