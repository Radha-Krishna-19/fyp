/* =====================================================================
   deform_page.js - the live "change the cell" explorer on deform.html.
   Uses DEFORM (mof_deform.js) and MORPH (mof_morphology.js). Nothing here is typed in:
   the inputs are the centring, point group and edge of each structure (MORPH.STRUCTURES),
   and the slider values.  The view is SVG (front-facing faces, painted back to front).
   ===================================================================== */
(function () {
  'use strict';
  var M = window.MORPH, D = window.DEFORM, SVGNS = 'http://www.w3.org/2000/svg';
  var FILL = { '{100}': 'var(--linker)', '{111}': 'var(--node)', '{110}': 'var(--good)' };
  var state = { struct: 'MOF-5', la: 1, lb: 1, lc: 1, yaw: 0.75, pitch: 0.42 };

  function el(tag, attrs, html) { var e = document.createElement(tag); for (var k in (attrs || {})) e.setAttribute(k, attrs[k]); if (html !== undefined) e.innerHTML = html; return e; }
  function f3(x) { return (Math.abs(x) < 5e-4 ? 0 : x).toFixed(3); }

  function current() {
    var s = M.STRUCTURES[state.struct], a = s.a;
    return D.bfdhShape(s.centring, s.pointGroup, [a * state.la, a * state.lb, a * state.lc]);
  }
  function rotate(v) {
    var cy = Math.cos(state.yaw), sy = Math.sin(state.yaw), cp = Math.cos(state.pitch), sp = Math.sin(state.pitch);
    var x = cy * v[0] - sy * v[1], y = sy * v[0] + cy * v[1], z = v[2];
    return [x, cp * y - sp * z, sp * y + cp * z];
  }

  function draw(S) {
    var host = document.getElementById('df-view'); if (!host) return;
    host.innerHTML = '';
    var W = 360, H = 320, R = 0;
    S.V.forEach(function (v) { R = Math.max(R, Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])); });
    var k = 0.42 * Math.min(W, H) / (R || 1);
    var svg = document.createElementNS(SVGNS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H); svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'Crystal shape: ' + S.name);
    svg.style.cssText = 'width:100%;max-width:420px;height:auto;display:block;margin:6px auto;cursor:grab;touch-action:none';
    S.faces.map(function (f) {
      var n = rotate(f.n), pts = f.poly.map(rotate);
      return { f: f, n: n, pts: pts, depth: pts.reduce(function (s, p) { return s + p[1]; }, 0) / pts.length };
    }).filter(function (F) { return F.n[1] < 0; }).sort(function (a, b) { return b.depth - a.depth; }).forEach(function (F) {
      var light = 0.55 + 0.45 * Math.max(0, -F.n[1] * 0.75 + F.n[2] * 0.45 + F.n[0] * 0.2);
      var poly = document.createElementNS(SVGNS, 'polygon');
      poly.setAttribute('points', F.pts.map(function (p) { return (W / 2 + k * p[0]).toFixed(1) + ',' + (H / 2 - k * p[2]).toFixed(1); }).join(' '));
      poly.setAttribute('style', 'fill:' + (FILL[F.f.tag] || 'var(--accent2)') + ';fill-opacity:' + light.toFixed(2) + ';stroke:var(--text);stroke-width:0.8;stroke-linejoin:round');
      svg.appendChild(poly);
    });
    var drag = null;
    svg.addEventListener('pointerdown', function (e) { drag = [e.clientX, e.clientY]; svg.setPointerCapture && svg.setPointerCapture(e.pointerId); });
    svg.addEventListener('pointermove', function (e) {
      if (!drag) return;
      state.yaw += (e.clientX - drag[0]) * 0.01; state.pitch = Math.max(-1.4, Math.min(1.4, state.pitch + (e.clientY - drag[1]) * 0.01));
      drag = [e.clientX, e.clientY]; draw(S);
    });
    svg.addEventListener('pointerup', function () { drag = null; });
    host.appendChild(svg);
    host.appendChild(el('div', { class: 'legend sm', style: 'text-align:center' }, 'blue {100} &middot; red {111} &middot; green {110} &middot; other families purple &middot; drag to rotate'));
  }

  function readout(S) {
    var host = document.getElementById('df-readout'); if (!host) return;
    var h = D.habit(S), I = S.info, hw = h.halfWidths, s = M.STRUCTURES[state.struct];
    host.innerHTML = '<p class="sd" style="text-align:center;margin:4px 0 10px"><b id="df-name">' + h.type + ' &middot; ' + S.name + '</b></p>' +
      '<div class="table-wrap"><table class="data-table" id="df-numbers"><tbody>' +
      '<tr><td class="dt-label">Cell edges (&Aring;)</td><td class="dt-value">' + (s.a * state.la).toFixed(2) + ' &times; ' + (s.a * state.lb).toFixed(2) + ' &times; ' + (s.a * state.lc).toFixed(2) + '</td>' +
      '<td class="dt-label">Symmetry operations (point group)</td><td class="dt-value">' + S.operations + '</td></tr>' +
      '<tr><td class="dt-label">Half-widths x : y : z</td><td class="dt-value">' + (hw[0] / hw[0]).toFixed(3) + ' : ' + (hw[1] / hw[0]).toFixed(3) + ' : ' + (hw[2] / hw[0]).toFixed(3) + '</td>' +
      '<td class="dt-label">Zingg ratios b/a, c/b</td><td class="dt-value">' + f3(h.ba) + ', ' + f3(h.cb) + '</td></tr>' +
      '<tr><td class="dt-label">Faces / vertices</td><td class="dt-value">' + I.faces + ' / ' + I.vertices + '</td>' +
      '<td class="dt-label">&Psi; / &kappa;&sup2;</td><td class="dt-value">' + f3(I.sphericity) + ' / ' + f3(I.kappa2) + '</td></tr>' +
      '</tbody></table></div>';
  }

  function sync() {
    ['la', 'lb', 'lc'].forEach(function (key) {
      var row = document.getElementById('df-row-' + key); if (!row) return;
      row.querySelector('input').value = Math.log(state[key]);
      row.querySelector('output').textContent = state[key].toFixed(2) + '×  (' + (M.STRUCTURES[state.struct].a * state[key]).toFixed(2) + ' Å)';
    });
  }
  function update() { var S = current(); draw(S); readout(S); sync(); }

  var PRESETS = [
    ['Real cell', function () { state.la = state.lb = state.lc = 1; }],
    ['Plate: c × 2.5', function () { state.la = state.lb = 1; state.lc = 2.5; }],
    ['Rod: c × 0.3', function () { state.la = state.lb = 1; state.lc = 0.3; }],
    ['Lath: all different', function () { state.la = 1; state.lb = 0.6; state.lc = 2.2; }]
  ];

  function build() {
    var structs = document.getElementById('df-structs'), presets = document.getElementById('df-presets'), sliders = document.getElementById('df-sliders');
    if (!structs || !presets || !sliders) return;
    Object.keys(M.STRUCTURES).forEach(function (name) {
      var b = el('button', { type: 'button', class: 'mode-btn', 'data-struct': name, title: M.STRUCTURES[name].spacegroup }, name);
      b.addEventListener('click', function () { state.struct = name; structs.querySelectorAll('.mode-btn').forEach(function (x) { x.classList.toggle('active', x === b); }); update(); });
      if (name === state.struct) b.classList.add('active');
      structs.appendChild(b);
    });
    PRESETS.forEach(function (p) {
      var b = el('button', { type: 'button', class: 'mode-btn' }, p[0]);
      b.addEventListener('click', function () { p[1](); update(); });
      presets.appendChild(b);
    });
    [['la', '<i>a</i> (scale of the first edge)'], ['lb', '<i>b</i> (second edge)'], ['lc', '<i>c</i> (third edge)']].forEach(function (s) {
      var row = el('div', { id: 'df-row-' + s[0], class: 'toolbar' });
      row.innerHTML = '<label class="lbl" for="df-in-' + s[0] + '" style="min-width:220px">' + s[1] + '</label>' +
        '<input id="df-in-' + s[0] + '" type="range" min="' + Math.log(0.2) + '" max="' + Math.log(3) + '" step="0.005" style="flex:1;min-width:140px">' +
        '<output style="min-width:130px;font-variant-numeric:tabular-nums"></output>';
      row.querySelector('input').addEventListener('input', function (e) { state[s[0]] = Math.exp(parseFloat(e.target.value)); update(); });
      sliders.appendChild(row);
    });
    update();
  }
  function init() { if (M && D) build(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
