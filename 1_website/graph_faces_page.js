/* =====================================================================
   graph_faces_page.js — fills the tables on graph_faces.html from
   phase3_data.js (the output of 2_python/morphology/run_phase3.py).
   ===================================================================== */
(function () {
  'use strict';
  var ORDER = ['MOF-5', 'HKUST-1', 'UiO-66', 'ZIF-8'];
  var FAM = ['{100}', '{110}', '{111}', '{111}+', '{111}-', '{211}', '{211}+', '{211}-', '{221}', '{310}', '{311}', '{311}+', '{311}-'];
  var CLS = { F: '--good', S: '--warn', K: '--bad' };
  var SEEN = { 'MOF-5': 'cubes (Cubillas 2012)', 'HKUST-1': 'octahedra; cube to octahedron with salt (Liu 2016)',
               'UiO-66': 'octahedra (Ceballos 2022; UiO-67: Chen 2020)', 'ZIF-8': 'rhombic dodecahedra (Pan 2011; Liu 2020)' };
  var BFDH = { 'MOF-5': 'truncated octahedron', 'HKUST-1': 'truncated octahedron', 'UiO-66': 'truncated octahedron', 'ZIF-8': 'rhombic dodecahedron' };

  function fam(t) { return t.replace(/\+$/, '<sub>+</sub>').replace(/-$/, '<sub>&minus;</sub>'); }
  function wrap(id, head, body) {
    return '<div class="table-wrap"><table class="data-table" id="' + id + '"><thead><tr>' +
      head.map(function (h) { return '<td>' + h + '</td>'; }).join('') + '</tr></thead><tbody>' + body + '</tbody></table></div>';
  }
  function major(rec) {
    var fr = rec.face_area_fraction, keys = Object.keys(fr).filter(function (k) { return fr[k] > 0.01; })
      .sort(function (a, b) { return fr[b] - fr[a]; });
    return keys.map(function (k) { return fam(k) + ' ' + Math.round(100 * fr[k]) + '%'; }).join(', ');
  }

  function netTable(P) {
    var body = ORDER.map(function (n) {
      var r = P[n], q = r.quotient, g = r.net;
      return '<tr><td class="dt-label">' + n + '</td><td class="dt-note">' + r.spacegroup + '</td>' +
        '<td class="dt-value">' + q.blocks + ' / ' + q.links + '</td>' +
        '<td class="dt-note">nodes ' + q.node_degrees.join(', ') + '; linkers ' + q.linker_degrees.join(', ') + '</td>' +
        '<td class="dt-value">' + g.vertices + ' / ' + g.links + '</td><td class="dt-value">' + g.vertex_degrees.join(', ') + '</td></tr>';
    }).join('');
    return wrap('gf-net', ['Structure', 'Space group', 'Quotient blocks / links', 'Block degrees', 'Net vertices / links', 'Net degrees'], body);
  }

  function faceTable(P, name) {
    var r = P[name], rows = FAM.filter(function (f) { return r.faces[f]; }).map(function (f) {
      var v = r.faces[f];
      return '<tr><td class="dt-label">' + fam(f) + '</td><td class="dt-value">' + v.d_eff.toFixed(2) + '</td>' +
        '<td class="dt-value">' + v.E_att.toFixed(3) + '</td><td class="dt-value">' + (1000 * v.gamma).toFixed(2) + '</td>' +
        '<td class="dt-note" style="color:var(' + CLS[v.cls] + ');font-weight:650">' + v.cls + '</td><td class="dt-value">' + v.rank + '</td></tr>';
    }).join('');
    return '<h3 class="sub-head">' + name + '</h3>' + wrap('gf-faces-' + name.replace(/[^A-Za-z0-9]/g, ''),
      ['Face family', '<i>d</i><sub>eff</sub> (&Aring;)', '<i>E</i><sub>att</sub> (links per new unit)', '&gamma; (links per 1000 &Aring;&sup2;)', 'Class', 'Slice rank'], rows);
  }

  function shapeTable(P) {
    var body = ORDER.map(function (n) {
      var a = P[n].shape_attachment, w = P[n].shape_wulff_broken_bond;
      return '<tr><td class="dt-label">' + n + '</td><td class="dt-note">' + BFDH[n] + '</td>' +
        '<td class="dt-note"><b>' + a.name_major_faces + '</b><br><span class="sm">' + major(a) + '</span></td>' +
        '<td class="dt-note"><b>' + w.name_major_faces + '</b><br><span class="sm">' + major(w) + '</span></td>' +
        '<td class="dt-note">' + SEEN[n] + '</td></tr>';
    }).join('');
    return wrap('gf-shapes', ['Structure', 'Phase 1: BFDH (lattice only)', 'Phase 3: attachment energy', 'Phase 3: broken-bond Wulff', 'Seen in experiments'], body);
  }

  function init() {
    var P = window.PHASE3, t;
    if (!P) return;
    if ((t = document.getElementById('gf-net-table'))) t.innerHTML = netTable(P);
    if ((t = document.getElementById('gf-face-tables'))) t.innerHTML = ORDER.map(function (n) { return faceTable(P, n); }).join('');
    if ((t = document.getElementById('gf-shape-table'))) t.innerHTML = shapeTable(P);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
