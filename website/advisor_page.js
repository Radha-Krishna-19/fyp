/* The Shape Advisor page: for each MOF with a structure, the predicted shape, what laboratories saw,
   how to steer the shape, and what each shape exposes to a gas. All numbers come from
   website/advisor_data.js (generated from code/morphology/results/*.json); the shapes are redrawn here
   with the same engines as the other pages (mof_morphology.js for cubic Wulff shapes,
   mof_general_shape.js for other lattices). */
(function () {
  'use strict';
  var A = window.ADVISOR, M = window.MORPH, GS = window.GENSHAPE;
  if (!A) return;
  var SVGNS = 'http://www.w3.org/2000/svg';
  var state = { mof: null, R: [[1, 0, 0], [0, 1, 0], [0, 0, 1]] };
  function el(id) { return document.getElementById(id); }
  function set(id, h) { var e = el(id); if (e) e.innerHTML = h; }
  function fx(x, d) { return (x === null || x === undefined || isNaN(x)) ? '&mdash;' : (+x).toFixed(d); }
  function pct(x, d) { return (x === null || x === undefined) ? '&mdash;' : (100 * x).toFixed(d === undefined ? 0 : d) + ' %'; }
  function fam(k) { return '{' + String(k).replace(/-(\d)/g, '<span style="text-decoration:overline">$1</span>') + '}'; }
  var COL = { '100': 'var(--linker)', '111': 'var(--node)', '110': 'var(--good)' };
  function colourOf(tag) { var k = String(tag).replace(/[{}+-]/g, ''); return COL[k] || 'var(--accent2)'; }
  var NAMES = { '100': 'cube', '110': 'rhombic dodecahedron', '111': 'octahedron' };
  var KIND = { measured: 'published structure', built: 'built from ZIF-8 (Zn replaced by Co)', 'stand-in': 'close stand-in structure', none: 'no structure file' };

  // ---- the shape of one MOF ----
  function shapeFaces(mof) {
    var p = A.predictions[mof];
    if (p.uff) {
      var g = {};
      Object.keys(p.uff.gamma).forEach(function (k) {
        var f = k.replace(/[{}+-]/g, '');
        if (f === '100' || f === '110' || f === '111') g[f] = Math.min(p.uff.gamma[k], g[f] === undefined ? 1e9 : g[f]);
      });
      var S = M.shape({ '{100}': g['100'], '{110}': g['110'], '{111}': g['111'] }, 'm-3m');
      return { faces: S.faces.map(function (f) { return { n: f.n, pts: f.poly, tag: f.tag }; }), how: 'Wulff shape from unrelaxed bond-count surface energies with UFF van der Waals terms' };
    }
    if (A.cifs[mof] && GS) {
      var R = GS.run(A.cifs[mof]);
      return { faces: R.faces.map(function (f) { return { n: f.n, pts: f.pts, tag: f.tag }; }), how: 'BFDH shape (any lattice)' };
    }
    return null;
  }
  function rot(v) { var R = state.R; return [R[0][0] * v[0] + R[0][1] * v[1] + R[0][2] * v[2], R[1][0] * v[0] + R[1][1] * v[1] + R[1][2] * v[2], R[2][0] * v[0] + R[2][1] * v[1] + R[2][2] * v[2]]; }
  function draw() {
    var host = el('adv-view'); if (!host) return;
    var sh = state.shape; host.querySelectorAll('svg, p.adv-none').forEach(function (s) { s.remove(); });
    if (!sh) { host.insertAdjacentHTML('afterbegin', '<p class="sm adv-none">No structure file, so no shape.</p>'); return; }
    var W = 340, H = 300, all = [];
    sh.faces.forEach(function (f) { f.pts.forEach(function (p) { all.push(p); }); });
    var m = Math.max.apply(null, all.map(function (p) { return Math.sqrt(p[0] * p[0] + p[1] * p[1] + p[2] * p[2]); }));
    var k = 0.42 * Math.min(W, H) / m;
    var svg = document.createElementNS(SVGNS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H); svg.setAttribute('class', 'adv-svg');
    svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', 'Predicted crystal shape of ' + state.mof + '; drag to turn, click a face');
    var L = [0.35, -0.55, 0.75], ln = Math.sqrt(L[0] * L[0] + L[1] * L[1] + L[2] * L[2]);
    sh.faces.map(function (f, i) {
      var n = rot(f.n), pts = f.pts.map(rot);
      return { i: i, f: f, n: n, pts: pts, depth: pts.reduce(function (s, p) { return s + p[1]; }, 0) / pts.length };
    }).filter(function (F) { return F.n[1] < 1e-9; }).sort(function (a, b) { return b.depth - a.depth; }).forEach(function (F) {
      var lam = Math.max(0, (F.n[0] * L[0] + F.n[1] * L[1] + F.n[2] * L[2]) / ln);
      var pts = F.pts.map(function (p) { return (W / 2 + k * p[0]).toFixed(1) + ',' + (H / 2 - k * p[2]).toFixed(1); }).join(' ');
      var base = document.createElementNS(SVGNS, 'polygon');
      base.setAttribute('points', pts); base.setAttribute('style', 'fill:' + colourOf(F.f.tag) + ';stroke:none');
      svg.appendChild(base);
      var top = document.createElementNS(SVGNS, 'polygon');
      top.setAttribute('points', pts); top.setAttribute('data-face', F.i);
      top.setAttribute('style', 'cursor:pointer;fill:#fff;fill-opacity:' + (0.05 + 0.35 * lam).toFixed(3) + ';stroke:var(--text);stroke-width:1.1;stroke-linejoin:round');
      svg.appendChild(top);
    });
    host.insertBefore(svg, host.firstChild);
    if (window.FaceCard) FaceCard.wire(svg, host, describeFace);
    var dragging = null;
    svg.addEventListener('pointerdown', function (e) { dragging = [e.clientX, e.clientY]; try { svg.setPointerCapture(e.pointerId); } catch (x) { /* jsdom */ } });
    svg.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      var dx = (e.clientX - dragging[0]) * 0.01, dy = (e.clientY - dragging[1]) * 0.01;
      if (Math.abs(dx) + Math.abs(dy) < 0.02) return;
      dragging = [e.clientX, e.clientY];
      var cz = Math.cos(dx), sz = Math.sin(dx), cx = Math.cos(dy), sx = Math.sin(dy);
      var Rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], Rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]];
      state.R = mul(Rx, mul(Rz, state.R)); draw();
    });
    svg.addEventListener('pointerup', function () { dragging = null; });
  }
  function mul(a, b) { var r = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]; for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) for (var q = 0; q < 3; q++) r[i][j] += a[i][q] * b[q][j]; return r; }
  function describeFace(i) {
    var f = state.shape.faces[i]; if (!f) return null;
    var key = String(f.tag).replace(/[{}+-]/g, ''), ad = A.adsorption[state.mof], face = ad && ad.faces[key];
    var extra = [];
    if (face) {
      extra.push(['Open to CO<sub>2</sub> at its likely termination', pct(face.CO2.open_fraction, 1)]);
      extra.push(['Open to N<sub>2</sub>', pct(face.N2.open_fraction, 1)]);
      extra.push(['Largest opening', fx(face.CO2.largest_opening_A, 1) + ' &Aring;']);
    }
    var areas = state.shape.faces.map(function (g) { return FaceCard.area(g.pts); }), tot = areas.reduce(function (a, b) { return a + b; }, 0), fa = 0, cnt = 0;
    state.shape.faces.forEach(function (g, j) { if (g.tag === f.tag) { fa += areas[j]; cnt++; } });
    return FaceCard.describe({ family: fam(key), normal: f.n, faceShare: areas[i] / tot, familyShare: fa / tot, count: cnt, extra: extra });
  }

  // ---- the text and tables for one MOF ----
  function render() {
    var mof = state.mof, p = A.predictions[mof], pm = A.per_mof[mof], st = A.steering[mof], ad = A.adsorption[mof];
    document.querySelectorAll('#adv-mofs .struct-tab').forEach(function (b) { b.classList.toggle('active', b.getAttribute('data-mof') === mof); });
    state.shape = p.file ? shapeFaces(mof) : null;
    if (window.FaceCard) FaceCard.hide(el('adv-view'));
    draw();
    // summary
    var h = '<p class="adv-head"><b>' + mof + '</b> <span class="sm">(' + KIND[p.structure] + ')</span></p>';
    if (p.uff) h += '<p>Predicted from the structure alone: <b>' + p.uff.shape + '</b>, mostly ' + fam(p.uff.dominant_face) + ' faces (' + state.shape.how + ').</p>';
    else if (p.bfdh) h += '<p>Predicted from the structure alone: <b>' + (p.bfdh.habit === 'rod' ? 'a rod' : p.bfdh.habit) + '</b>' +
      (p.bfdh.long_axis_uvw ? ' along [' + p.bfdh.long_axis_uvw.join('') + ']' : '') + ' (BFDH; this lattice has no energy model here).</p>';
    else h += '<p>No structure file is available, so nothing is predicted.</p>';
    if (pm) {
      var lab = Object.keys(pm.lab_faces).map(function (k) { return pm.lab_faces[k] + ' &times; ' + fam(k); }).join(', ');
      var hab = Object.keys(pm.lab_habits).map(function (k) { return pm.lab_habits[k] + ' ' + k; }).join(', ');
      h += '<p>Laboratory records: <b>' + pm.records + '</b>' + (lab ? '; dominant face reported: ' + lab : '') + (hab ? '; overall form: ' + hab : '') + '.</p>';
      var agree = [];
      if (pm.uff_face_correct !== null && pm.on_map) agree.push('main face right in ' + pm.uff_face_correct + ' of ' + pm.on_map + ' records');
      if (pm.habit_scored) agree.push('compact / rod / plate right in ' + pm.habit_correct + ' of ' + pm.habit_scored);
      if (agree.length) h += '<p>Agreement: ' + agree.join('; ') + '.</p>';
    }
    if (mof === 'IRMOF-8') h += '<p class="c2s-stop">The IRMOF-8 file keeps only P2<sub>1</sub>/c symmetry because of how its naphthalene linkers are ordered; an ideal Fm-3m framework would cancel different planes. Treat its prediction with caution.</p>';
    if (p.structure === 'stand-in') h += '<p class="c2s-stop">Scored with a stand-in structure (' + (mof === 'MIL-53(Fe)' ? 'MIL-53(Cr)' : 'UiO-66') + '). Reported separately and not counted in the main score.</p>';
    set('adv-summary', h);
    // steering
    if (st) {
      function pc(x) { return x === null || x === undefined ? 'not reached' : x === 0 ? 'already' : x < 1 ? fx(x, 1) + ' %' : fx(x, 0) + ' %'; }
      var rows = '', evid = [];
      ['100', '110', '111'].forEach(function (F) {
        var s = st.steering[F], ev = [];
        Object.keys(st.lab_evidence).forEach(function (c) {
          var e = st.lab_evidence[c];
          if (c !== 'none' && e.faces[F]) ev.push(c.replace(/_/g, ' ') + ' (' + e.faces[F] + ' of ' + Object.values(e.faces).reduce(function (a, b) { return a + b; }, 0) + ' records; ' + e.papers.join(', ') + ')' + (e.faces[F] < 3 ? ' <span class="sm">(fewer than 3 records: an example, not an established effect)</span>' : ''));
        });
        rows += '<tr><td class="dt-label">' + fam(F) + ' &rarr; ' + NAMES[F] + '</td><td class="dt-value">' + pc(s.lower_by_percent_to_dominate) + '</td><td class="dt-value">' + pc(s.lower_by_percent_for_pure_shape) + '</td></tr>';
        evid.push('<li>' + fam(F) + ': ' + (ev.join('; ') || 'no record with an additive gave this face') + '</li>');
      });
      var none = st.lab_evidence.none;
      set('adv-steer', '<div class="table-wrap"><table class="data-table" id="adv-steer-table"><thead><tr><td>Face and its pure shape</td><td>Energy cut to become the main face</td><td>Energy cut for the pure shape</td></tr></thead><tbody>' + rows +
        '</tbody></table></div><p class="sd">Additive types in the laboratory records of ' + mof + ' that gave each face' + (none ? ' (without an additive: ' + Object.keys(none.faces).map(function (k) { return none.faces[k] + ' &times; ' + fam(k); }).join(', ') + ')' : '') + ':</p><ul class="sd" id="adv-steer-evidence">' + evid.join('') + '</ul>' +
        '<p class="sm">An additive that binds one face lowers its surface energy (Gibbs: d&gamma; = &minus;&Gamma; d&mu;). The percentages are relative to unrelaxed bond-count surface energies without solvent: they rank how hard each change is, not binding energies.</p>');
    } else set('adv-steer', '<p class="sm">Steering needs the cubic surface-energy map; ' + (p.file ? 'this lattice is not cubic.' : 'there is no structure file.') + '</p>');
    // gas access
    if (ad) {
      var fr = Object.keys(ad.faces).map(function (k) {
        var f = ad.faces[k];
        return '<tr><td class="dt-label">' + fam(k) + '</td><td class="dt-value">' + pct(f.CO2.open_fraction, 1) + '</td><td class="dt-value">' + pct(f.N2.open_fraction, 1) +
          '</td><td class="dt-value">' + fx(f.CO2.largest_opening_A, 1) + '</td><td class="dt-value">' + pct(f.CO2.open_fraction_range_over_positions[0], 0) + '&ndash;' + pct(f.CO2.open_fraction_range_over_positions[1], 0) + '</td></tr>';
      }).join('');
      var sr = Object.keys(ad.shapes).map(function (k) {
        var s = ad.shapes[k];
        return '<tr><td class="dt-label">' + k.replace(/_/g, ' ') + '</td><td class="dt-value">' + fx(s.sphericity, 3) + '</td><td class="dt-value">' + (s.open_surface_CO2 === undefined ? '&mdash;' : pct(s.open_surface_CO2, 1)) +
          '</td><td class="dt-value">' + fx(s.diffusion_length_per_V13, 3) + '</td><td class="dt-value">' + fx(s.relative_fill_time, 2) + '</td><td class="dt-value">' + fx(s.relative_initial_uptake_CO2, 2) + '</td></tr>';
      }).join('');
      set('adv-gas', '<div class="table-wrap"><table class="data-table" id="adv-face-table"><thead><tr><td>Face</td><td>Open to CO<sub>2</sub></td><td>Open to N<sub>2</sub></td><td>Largest opening (&Aring;)</td><td>Range over terminations (CO<sub>2</sub>)</td></tr></thead><tbody>' + fr +
        '</tbody></table></div><div class="table-wrap"><table class="data-table" id="adv-shape-table"><thead><tr><td>Shape</td><td>Sphericity</td><td>Open surface (CO<sub>2</sub>)</td><td>Diffusion length L / V<sup>1/3</sup></td><td>Fill time (relative)</td><td>Initial uptake (relative)</td></tr></thead><tbody>' + sr +
        '</tbody></table></div><p class="sm">Bulk open fraction from random 3D points: ' + pct(ad.bulk_open_fraction_3D.CO2, 1) + ' (CO<sub>2</sub>); largest cavity ' + fx(ad.largest_cavity_3D_A, 1) + ' &Aring;. The first row of the second table is the reference (1.00).</p>');
    } else set('adv-gas', '<p class="sm">Not computed for ' + (p.structure === 'stand-in' ? 'stand-in structures.' : 'MOFs without a structure file.') + '</p>');
  }

  function overall() {
    var fs = A.face_scores;
    set('adv-nrec', String(A.n_records));
    function row(key, label) {
      return '<tr><td class="dt-label">' + label + '</td>' + fs[key].map(function (s) { return '<td class="dt-value">' + s.correct + ' / ' + s.n + (s.n ? ' <span class="sm">(' + Math.round(100 * s.accuracy) + ' %; ' + Math.round(100 * s.ci95[0]) + '&ndash;' + Math.round(100 * s.ci95[1]) + ')</span>' : '') + '</td>'; }).join('') + '</tr>';
    }
    var head = fs['measured_and_built/all'].map(function (s) { return '<td>' + s.model + '</td>'; }).join('');
    set('adv-score', '<div class="table-wrap"><table class="data-table" id="adv-score-table"><thead><tr><td>Records</td>' + head + '</tr></thead><tbody>' +
      row('measured_and_built/additive_free', 'No additive') + row('measured_and_built/with_additive', 'With an additive') + row('measured_and_built/all', 'All') + '</tbody></table></div>');
    var eu = A.evidence_units['uff/additive_free'], nf = A.evidence_units['uff/all/new_four_only'], ea = A.evidence_units['uff/all'];
    set('adv-units', 'The structure-only model gives <b>one prediction per MOF</b>, so its records are not independent. On the records without an additive, the ' +
      eu.records + ' records come from <b>' + eu.mofs + ' MOFs</b> and ' + eu.papers + ' papers, and the prediction is right for <b>' + eu.mofs_right_by_majority + ' of ' + eu.mofs +
      ' MOFs</b> (' + Object.keys(eu.per_mof).map(function (m) { var v = eu.per_mof[m]; return m + ' ' + v.correct + '/' + v.n; }).join(', ') +
      '). Resampling whole papers gives a 95 % interval of ' + Math.round(100 * eu.paper_bootstrap_ci95[0]) + '&ndash;' + Math.round(100 * eu.paper_bootstrap_ci95[1]) +
      ' %. Over all records, with and without additives, it is right for ' + ea.mofs_right_by_majority + ' of ' + ea.mofs + ' MOFs. The energy model was fixed on the four demonstration MOFs; the MOFs added later are the clean test. Of these, ' +
      nf.mofs.join(' and ') + ' have face records: the prediction is right in ' + nf.correct + ' of ' + nf.records + (nf.records - nf.correct === nf.wrong_with_additive ? ', and every wrong one was grown with an additive.' : '; ' + nf.wrong_with_additive + ' of the wrong ones were grown with an additive.'));
    set('adv-judgement', 'Records counted as additive-free by judgement: ' + A.judgement_calls.map(function (j) { return j.record + ' (' + (j.additive ? j.additive + ', amount &ldquo;' + j.amount + '&rdquo;' : 'no additive recorded') + ')'; }).join('; ') + '.');
    var hs = A.habit_scores;
    set('adv-habit', 'Compact, rod or plate, structure only: <b>' + hs.measured_and_built.correct + ' of ' + hs.measured_and_built.n + '</b> records; always guessing "compact" gets ' +
      hs['measured_and_built/baseline_always_compact'].correct + ' of ' + hs['measured_and_built/baseline_always_compact'].n + '. Where the structure predicts a rod (Mg-MOF-74), ' +
      hs['measured_and_built/where_bfdh_predicts_non_compact'].correct + ' of ' + hs['measured_and_built/where_bfdh_predicts_non_compact'].n + ' laboratory crystals are elongated.');
    var ds = A.dataset_summary, t = [];
    Object.keys(ds).forEach(function (k) { var d = ds[k]; t.push('<b>' + k + '</b>: ' + d.files + ' files, ' + Object.keys(d.habits).map(function (h) { return d.habits[h] + ' ' + (h === 'equant' ? 'compact' : h); }).join(', ') + (d.errors ? ', ' + d.errors + ' unreadable' : '') + '; ' + d.p1_files + ' stored without symmetry'); });
    set('adv-dataset', t.join('<br>'));
  }

  function init() {
    var bar = el('adv-mofs'); if (!bar) return;
    A.order.forEach(function (m) {
      var b = document.createElement('button'); b.type = 'button'; b.className = 'struct-tab'; b.setAttribute('data-mof', m);
      b.textContent = m + (A.predictions[m].structure === 'stand-in' ? ' *' : A.predictions[m].structure === 'none' ? ' (no file)' : '');
      b.addEventListener('click', function () { state.mof = m; state.R = [[0.94, -0.34, 0], [0.2, 0.55, -0.81], [0.28, 0.77, 0.58]]; render(); });
      bar.appendChild(b);
    });
    overall();
    state.mof = 'HKUST-1'; state.R = [[0.94, -0.34, 0], [0.2, 0.55, -0.81], [0.28, 0.77, 0.58]]; render();
  }
  window.ADVISOR_PAGE = { render: render, state: state, select: function (m) { state.mof = m; render(); } };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
