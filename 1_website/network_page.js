// network_page.js
// Logic for the network-analysis sections of index.html. Draws the block graph, the Laplacian
// spectrum, the centrality tables and the defect simulation. Uses only canvas
// 2D -- no charting library, no WebGL, so this page has zero interaction with
// the 3D contexts used elsewhere in the project.

(function () {
  'use strict';

  const NODE_C = '#d81e40', LINK_C = '#2e86c1', GHOST = '#c9ccd4';
  const LIT = {
    'HKUST-1': { node: 4, linker: 3, net: 'tbo', sbu: 'Cu paddlewheel' },
    'UiO-66':  { node: 12, linker: 2, net: 'fcu', sbu: 'Zr₆O₄(OH)₄ cluster' },
    'MOF-5':   { node: 6, linker: 2, net: 'pcu', sbu: 'Zn₄O cluster' },
    'ZIF-8':   { node: 4, linker: 2, net: 'sod', sbu: 'single Zn' },
  };

  let structures = {};   // name -> DATA
  let current = null;
  let mode = 'periodic'; // 'periodic' | 'naive'
  let defectId = null;   // block id removed, or null
  let render3d = null;   // the 3D renderer instance for the molecular view
  let colour3d = 'degree';   // 'degree' | 'centrality' | 'role'
  let highlightTop = false;  // spotlight the highest-degree blocks in 3D

  // Blue -> yellow -> red ramp, used to colour blocks by a normalised measure.
  function ramp(t) {
    t = Math.max(0, Math.min(1, t));
    let r, g, b;
    if (t < 0.5) { const u = t / 0.5; r = 46 + u * (245 - 46); g = 134 + u * (200 - 134); b = 193 + u * (66 - 193); }
    else { const u = (t - 0.5) / 0.5; r = 245 + u * (216 - 245); g = 200 + u * (30 - 200); b = 66 + u * (64 - 66); }
    return (Math.round(r) << 16) | (Math.round(g) << 8) | Math.round(b);
  }

  // Build the {blockId: colour} map the 3D renderer consumes, from whichever
  // measure is currently selected. This is what makes the 2D graph and the 3D
  // crystal show the SAME quantity.
  function blockColours(G, deg, cent) {
    const map = {};
    const maxD = Math.max.apply(null, deg) || 1;
    const minD = Math.min.apply(null, deg);
    const topDeg = maxD;
    G.blocks.forEach((b, i) => {
      if (highlightTop) {
        map[b.id] = deg[i] === topDeg ? 0x1f9d67 : 0x39404d;   // spotlight vs dimmed
      } else if (colour3d === 'degree') {
        map[b.id] = ramp(maxD === minD ? 0.5 : (deg[i] - minD) / (maxD - minD));
      } else if (colour3d === 'centrality') {
        map[b.id] = ramp(cent[i]);
      } else {
        map[b.id] = b.type === 'metal' ? 0xc0392b : 0x2e86c1;
      }
    });
    return map;
  }

  function legend3d(G, deg) {
    const el = document.getElementById('c3d-legend');
    if (!el) return;
    const maxD = Math.max.apply(null, deg) || 1, minD = Math.min.apply(null, deg);
    const top = deg.filter(v => v === maxD).length;
    if (highlightTop) {
      el.innerHTML = '<span><i style="background:#1f9d67"></i><b>highest degree (' + maxD + ')</b> — ' + top +
        ' block' + (top === 1 ? '' : 's') + ', all tied</span>' +
        '<span><i style="background:#39404d"></i>everything else</span>' +
        '<span style="color:var(--muted2)">every highlighted block is identical to the others — that is the point</span>';
    } else if (colour3d === 'role') {
      el.innerHTML = '<span><i style="background:#c0392b"></i>node (inorganic)</span>' +
        '<span><i style="background:#2e86c1"></i>linker (organic)</span>';
    } else {
      const lo = colour3d === 'degree' ? minD : '0.00';
      const hi = colour3d === 'degree' ? maxD : '1.00';
      el.innerHTML = '<span><i style="background:#2e86c1"></i>' + lo + '</span>' +
        '<span style="width:130px;height:12px;border-radius:3px;display:inline-block;background:linear-gradient(90deg,#2e86c1,#f5c842,#d81e40)"></span>' +
        '<span><i style="background:#d81e40"></i>' + hi + '</span>' +
        '<span style="color:var(--muted2)">' + (colour3d === 'degree' ? 'coordination number' : 'eigenvector centrality') + '</span>';
    }
  }

  // ---------------- force-directed layout ----------------
  function layout(G, w, h, iters) {
    const n = G.n;
    const pos = [];
    for (let i = 0; i < n; i++) {
      const a = (2 * Math.PI * i) / n;
      pos.push([w / 2 + (w / 3) * Math.cos(a) + (Math.random() - 0.5) * 8,
                h / 2 + (h / 3) * Math.sin(a) + (Math.random() - 0.5) * 8]);
    }
    if (n < 2) return pos;
    const k = Math.sqrt((w * h) / n) * 0.62;
    iters = iters || 320;
    for (let it = 0; it < iters; it++) {
      const disp = pos.map(() => [0, 0]);
      for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
          let dx = pos[i][0] - pos[j][0], dy = pos[i][1] - pos[j][1];
          let d = Math.hypot(dx, dy) || 0.01;
          const rep = (k * k) / d;
          dx /= d; dy /= d;
          disp[i][0] += dx * rep; disp[i][1] += dy * rep;
          disp[j][0] -= dx * rep; disp[j][1] -= dy * rep;
        }
      }
      G.edges.forEach(e => {
        let dx = pos[e.i][0] - pos[e.j][0], dy = pos[e.i][1] - pos[e.j][1];
        let d = Math.hypot(dx, dy) || 0.01;
        const att = (d * d) / k;
        dx /= d; dy /= d;
        disp[e.i][0] -= dx * att; disp[e.i][1] -= dy * att;
        disp[e.j][0] += dx * att; disp[e.j][1] += dy * att;
      });
      const temp = k * (1 - it / iters) * 0.14;
      for (let i = 0; i < n; i++) {
        const d = Math.hypot(disp[i][0], disp[i][1]) || 0.01;
        pos[i][0] += (disp[i][0] / d) * Math.min(d, temp);
        pos[i][1] += (disp[i][1] / d) * Math.min(d, temp);
        pos[i][0] = Math.max(28, Math.min(w - 28, pos[i][0]));
        pos[i][1] = Math.max(28, Math.min(h - 28, pos[i][1]));
      }
    }
    return pos;
  }

  // ---------------- graph canvas ----------------
  let graphState = null;

  function drawGraph(canvas, G, deg, cent, highlight) {
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = canvas.clientWidth, h = canvas.clientHeight;
    canvas.width = w * dpr; canvas.height = h * dpr;
    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    const pos = layout(G, w, h);
    graphState = { pos, G, deg, cent, canvas };

    // edges: self-loops (block bonded to its own periodic image) drawn as arcs
    ctx.strokeStyle = '#aab0bb'; ctx.lineWidth = 1.2;
    G.edges.forEach(e => {
      if (e.i === e.j) {
        ctx.beginPath();
        ctx.arc(pos[e.i][0], pos[e.i][1] - 15, 13, 0, Math.PI * 2);
        ctx.stroke();
      } else {
        ctx.beginPath();
        ctx.moveTo(pos[e.i][0], pos[e.i][1]);
        ctx.lineTo(pos[e.j][0], pos[e.j][1]);
        ctx.stroke();
      }
    });

    const maxDeg = Math.max.apply(null, deg) || 1;
    G.blocks.forEach((b, i) => {
      const r = 6 + 12 * (deg[i] / maxDeg);
      ctx.beginPath();
      ctx.arc(pos[i][0], pos[i][1], r, 0, Math.PI * 2);
      ctx.fillStyle = b.type === 'metal' ? NODE_C : LINK_C;
      if (highlight && highlight.has(b.id)) { ctx.fillStyle = '#1f9d67'; }
      ctx.fill();
      if (r > 11) {
        ctx.fillStyle = '#fff';
        ctx.font = '600 10px system-ui';
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(String(deg[i]), pos[i][0], pos[i][1]);
      }
    });
  }

  function wireHover(canvas, tip) {
    canvas.addEventListener('mousemove', ev => {
      if (!graphState) return;
      const rect = canvas.getBoundingClientRect();
      const mx = ev.clientX - rect.left, my = ev.clientY - rect.top;
      let best = -1, bestD = 1e9;
      graphState.pos.forEach((p, i) => {
        const d = Math.hypot(p[0] - mx, p[1] - my);
        if (d < bestD) { bestD = d; best = i; }
      });
      if (best < 0 || bestD > 22) { tip.style.display = 'none'; return; }
      const b = graphState.G.blocks[best];
      const comp = Object.entries(b.composition).map(([e, n]) => e + n).join(' ');
      tip.innerHTML = '<b>' + (b.type === 'metal' ? 'Node' : 'Linker') + ' block #' + b.id + '</b><br>' +
        comp + '<br>coordination number: <b>' + graphState.deg[best] + '</b><br>' +
        'eigenvector centrality: ' + graphState.cent[best].toFixed(3);
      tip.style.display = 'block';
      tip.style.left = Math.min(mx + 14, canvas.clientWidth - 180) + 'px';
      tip.style.top = (my + 14) + 'px';
    });
    canvas.addEventListener('mouseleave', () => { tip.style.display = 'none'; });
  }

  // ---------------- spectrum chart ----------------
  function drawSpectrum(canvas, series) {
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = canvas.clientWidth, h = canvas.clientHeight;
    canvas.width = w * dpr; canvas.height = h * dpr;
    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    const pad = { l: 46, r: 12, t: 14, b: 34 };
    const maxY = Math.max.apply(null, series.map(s => Math.max.apply(null, s.values))) || 1;

    ctx.strokeStyle = '#e2e6f0'; ctx.lineWidth = 1;
    ctx.fillStyle = '#7c8296'; ctx.font = '11px system-ui'; ctx.textAlign = 'right';
    for (let g = 0; g <= 4; g++) {
      const y = pad.t + (h - pad.t - pad.b) * (1 - g / 4);
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
      ctx.fillText(((maxY * g) / 4).toFixed(1), pad.l - 7, y + 4);
    }
    ctx.textAlign = 'center';
    ctx.fillText('eigenvalue index (normalised)', (pad.l + w - pad.r) / 2, h - 8);
    ctx.save(); ctx.translate(13, (pad.t + h - pad.b) / 2); ctx.rotate(-Math.PI / 2);
    ctx.fillText('Laplacian λ', 0, 0); ctx.restore();

    series.forEach(s => {
      ctx.strokeStyle = s.color; ctx.fillStyle = s.color; ctx.lineWidth = 2;
      ctx.beginPath();
      s.values.forEach((v, i) => {
        const x = pad.l + (w - pad.l - pad.r) * (s.values.length > 1 ? i / (s.values.length - 1) : 0.5);
        const y = pad.t + (h - pad.t - pad.b) * (1 - v / maxY);
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.stroke();
      s.values.forEach((v, i) => {
        const x = pad.l + (w - pad.l - pad.r) * (s.values.length > 1 ? i / (s.values.length - 1) : 0.5);
        const y = pad.t + (h - pad.t - pad.b) * (1 - v / maxY);
        ctx.beginPath(); ctx.arc(x, y, 2.6, 0, Math.PI * 2); ctx.fill();
      });
    });
  }

  // ---------------- multifractal spectrum (Section 5) ----------------
  let mfCache = {};

  function mfAnalyse(name) {
    if (!mfCache[name]) {
      mfCache[name] = window.MOFMultifractal.analyse(structures[name], { nTrials: 24, seed: 0 });
    }
    return mfCache[name];
  }

  function drawCurve(canvas, series, xlabel, ylabel, title) {
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = canvas.clientWidth, h = canvas.clientHeight;
    canvas.width = w * dpr; canvas.height = h * dpr;
    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    const pad = { l: 52, r: 14, t: 24, b: 40 };
    const all = series.filter(s => s.x.length);
    if (!all.length) { ctx.fillStyle = '#7c8296'; ctx.font = '13px system-ui'; ctx.textAlign = 'center';
      ctx.fillText('spectrum undefined for this structure', w / 2, h / 2); return; }
    const xs = [].concat.apply([], all.map(s => s.x)).filter(isFinite);
    const ys = [].concat.apply([], all.map(s => s.y)).filter(isFinite);
    let x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs);
    let y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
    if (x1 - x0 < 1e-6) { x0 -= 0.05; x1 += 0.05; }
    if (y1 - y0 < 1e-6) { y0 -= 0.05; y1 += 0.05; }
    const X = v => pad.l + (w - pad.l - pad.r) * ((v - x0) / (x1 - x0));
    const Y = v => pad.t + (h - pad.t - pad.b) * (1 - (v - y0) / (y1 - y0));

    ctx.strokeStyle = '#e2e6f0'; ctx.fillStyle = '#7c8296'; ctx.font = '11px system-ui';
    for (let g = 0; g <= 4; g++) {
      const yy = pad.t + (h - pad.t - pad.b) * (1 - g / 4);
      ctx.beginPath(); ctx.moveTo(pad.l, yy); ctx.lineTo(w - pad.r, yy); ctx.stroke();
      ctx.textAlign = 'right'; ctx.fillText((y0 + (y1 - y0) * g / 4).toFixed(2), pad.l - 7, yy + 4);
      const xx = pad.l + (w - pad.l - pad.r) * (g / 4);
      ctx.textAlign = 'center'; ctx.fillText((x0 + (x1 - x0) * g / 4).toFixed(2), xx, h - 22);
    }
    ctx.textAlign = 'center'; ctx.fillStyle = '#5c6478';
    ctx.fillText(xlabel, (pad.l + w - pad.r) / 2, h - 6);
    ctx.save(); ctx.translate(14, (pad.t + h - pad.b) / 2); ctx.rotate(-Math.PI / 2);
    ctx.fillText(ylabel, 0, 0); ctx.restore();
    if (title) { ctx.font = '600 12px system-ui'; ctx.fillStyle = '#1a2033'; ctx.fillText(title, w / 2, 15); }

    series.forEach(s => {
      ctx.strokeStyle = s.color; ctx.fillStyle = s.color; ctx.lineWidth = s.bar ? 9 : 2;
      if (s.bar) {
        ctx.beginPath(); ctx.moveTo(X(s.x[0]), Y(s.y[0])); ctx.lineTo(X(s.x[1]), Y(s.y[1])); ctx.stroke();
        ctx.font = '600 11px system-ui'; ctx.textAlign = 'left';
        ctx.fillText(s.label, X(s.x[1]) + 8, Y(s.y[1]) + 4);
      } else {
        ctx.beginPath();
        let started = false;
        s.x.forEach((xv, i) => {
          if (!isFinite(xv) || !isFinite(s.y[i])) return;
          if (!started) { ctx.moveTo(X(xv), Y(s.y[i])); started = true; } else ctx.lineTo(X(xv), Y(s.y[i]));
        });
        ctx.stroke();
        s.x.forEach((xv, i) => {
          if (!isFinite(xv) || !isFinite(s.y[i])) return;
          ctx.beginPath(); ctx.arc(X(xv), Y(s.y[i]), 2.4, 0, Math.PI * 2); ctx.fill();
        });
      }
    });
  }

  const MF_COLS = { 'HKUST-1': '#d81e40', 'UiO-66': '#1f9d67', 'MOF-5': '#e0873a', 'ZIF-8': '#8a56c9' };

  function renderMultifractal() {
    if (!window.MOFMultifractal) return;
    const r = mfAnalyse(current);
    const cc = r.ok ? window.MOFMultifractal.cleanCurve(r.alpha, r.fAlpha) : { a: [], f: [] };
    drawCurve(document.getElementById('mf-curve-canvas'),
      [{ x: cc.a, y: cc.f, color: MF_COLS[current] || '#2f6fed' }],
      'α(q)', 'f(α)', current + ' — multifractal spectrum');

    // comparison: each structure's alpha interval as a horizontal bar
    const names = Object.keys(structures);
    const bars = [];
    names.forEach((n, i) => {
      const rr = mfAnalyse(n);
      if (!rr.ok) return;
      bars.push({ x: [rr.alphaMin, rr.alphaMax], y: [i, i], color: MF_COLS[n] || '#666', bar: true, label: n });
    });
    drawCurve(document.getElementById('mf-compare-canvas'), bars,
      'α  (singularity strength)', 'structure', 'α range per structure');

    // table
    let rows = '';
    names.forEach(n => {
      const rr = mfAnalyse(n);
      const metal = metalOf(structures[n]);
      rows += '<tr><td class="dt-label"><span style="color:' + (MF_COLS[n] || '#666') + '">●</span> ' + n +
        '</td><td class="dt-value">' + metal + '</td>' +
        '<td class="dt-value">' + rr.supercellN + '³ → ' + rr.K + '</td>' +
        '<td class="dt-value">' + rr.influential.length + '</td>' +
        '<td class="dt-value">' + (rr.ok ? rr.alphaMin.toFixed(2) + ' – ' + rr.alphaMax.toFixed(2) : 'undefined') + '</td>' +
        '<td class="dt-value">' + (rr.ok ? (rr.alphaMax - rr.alphaMin).toFixed(2) : '—') + '</td>' +
        '<td class="dt-value">' + (isFinite(rr.asymmetry) ? rr.asymmetry.toFixed(2) : 'n/a') + '</td></tr>';
    });
    document.getElementById('mf-table').innerHTML =
      '<table class="data-table"><thead><tr><td>Structure</td><td>Metal</td><td>Supercell → blocks</td>' +
      '<td>Influential</td><td>α range</td><td>Width</td><td>Asymmetry A</td></tr></thead><tbody>' +
      rows + '</tbody></table>';

    // verdict: does the Zr framework separate from the others?
    const zr = names.filter(n => metalOf(structures[n]) === 'Zr').map(mfAnalyse).filter(x => x.ok);
    const others = names.filter(n => metalOf(structures[n]) !== 'Zr').map(mfAnalyse).filter(x => x.ok);
    const el = document.getElementById('mf-verdict');
    if (zr.length && others.length) {
      const zrLo = Math.min.apply(null, zr.map(x => x.alphaMin));
      const otHi = Math.max.apply(null, others.map(x => x.alphaMax));
      const sep = zrLo > otHi;
      el.className = sep ? 'verdict ok' : 'verdict';
      el.innerHTML = sep
        ? '<b>The zirconium framework occupies its own region of α.</b> UiO-66 spans α ≈ ' +
          zrLo.toFixed(2) + '–' + Math.max.apply(null, zr.map(x => x.alphaMax)).toFixed(2) +
          ', entirely above every Cu/Zn framework here (which top out at α ≈ ' + otHi.toFixed(2) +
          '). That separation is the mechanism the brief is aiming at — but it rests on <b>one</b> Zr structure, ' +
          'so it demonstrates that the method can separate families, not that Zr-MOFs as a class occupy this band. ' +
          'Establishing that needs many structures per metal.'
        : '<b>The α ranges overlap here</b>, so on these four structures the spectrum alone does not separate the metals. ' +
          'With more structures per family the picture may sharpen — or it may show the descriptor needs pairing with another.';
    }

    // the fixes table
    document.getElementById('mf-fixes').innerHTML =
      '<table class="data-table"><thead><tr><td>#</td><td>Defect in the first implementation</td>' +
      '<td>Consequence</td><td>Correction</td></tr></thead><tbody>' +
      [['1', 'The spectrum was computed on the induced subgraph of only the influential nodes',
        'In a MOF the high-degree blocks are metal nodes, and metal nodes are never bonded to each other — they connect <i>through</i> linkers. That subgraph has <b>zero edges</b> for HKUST-1 and ZIF-8, so no distances exist and the spectrum is undefined.',
        'Box-cover the <b>full</b> block graph, which supplies the geometry, and read the measure only <i>at</i> the influential nodes.'],
       ['2', 'Bonds found with a plain distance matrix on raw coordinates',
        'Any bond crossing a unit-cell boundary is missed. A MOF is infinite.',
        'Periodic minimum-image bond search across all 27 neighbouring cells.'],
       ['3', 'All metal atoms merged into a single block',
        'HKUST-1\'s six separate paddlewheels became one giant hub joined to everything — the star-shaped graph seen earlier.',
        'Split node atoms into connected components first, giving the real separate SBUs.'],
       ['4', 'Block graph built without lattice translations',
        'Blocks joined by bonds in different directions collapsed to one edge; coordination numbers came out wrong.',
        'Labelled quotient graph — literature-correct coordination numbers (Section 1).'],
       ['5', 'Only 5 box-covering trials',
        'The covering is randomised, so the spectrum was not reproducible: the same structure gave different answers per random seed.',
        'More trials, and a stability check that reports the residual spread as pure algorithmic noise.'],
       ['6', 'Primitive cell used directly',
        'UiO-66\'s cell has 7 blocks and a graph diameter of 2 — there is no range of radii to fit a power law across, so the result is noise.',
        'Expand to a supercell until the graph is large enough to scale over (exact, because every edge carries its translation).']
      ].map(r => '<tr><td class="dt-value">' + r[0] + '</td><td class="dt-label">' + r[1] +
        '</td><td class="dt-note">' + r[2] + '</td><td class="dt-note" style="color:#0d6b47">' + r[3] + '</td></tr>').join('') +
      '</tbody></table>';
  }

  // ---------------- Section 6: the published box-growing method ----------------
  let paperCache = {};
  function paperAnalyse(name) {
    if (!paperCache[name]) paperCache[name] = window.MOFMultifractal.analysePaper(structures[name]);
    return paperCache[name];
  }

  function renderPaper() {
    if (!window.MOFMultifractal || !window.MOFMultifractal.analysePaper) return;
    const names = Object.keys(structures);
    let rows = '', maxW = -1, maxName = '';
    names.forEach(n => {
      const r = paperAnalyse(n);
      const a = r.nmfa, b = r.inmfa;
      if (a.width > maxW) { maxW = a.width; maxName = n; }
      rows += '<tr><td class="dt-label">' + n + '</td>' +
        '<td class="dt-value">' + metalOf(structures[n]) + '</td>' +
        '<td class="dt-value">' + r.K + '</td>' +
        '<td class="dt-value">' + a.dNet + '</td>' +
        '<td class="dt-value">' + (isFinite(a.alpha0) ? a.alpha0.toFixed(2) : '—') + '</td>' +
        '<td class="dt-value">' + (isFinite(a.width) ? a.width.toFixed(2) : '—') + '</td>' +
        '<td class="dt-value" style="color:#d64545">' + (isFinite(b.width) ? b.width.toFixed(3) : '—') + '</td>' +
        '<td class="dt-value">' + b.distinctCurves + '</td></tr>';
    });
    document.getElementById('paper-table').innerHTML =
      '<table class="data-table"><thead><tr><td>Structure</td><td>Metal</td><td>Blocks</td>' +
      '<td>Radius d</td><td>NMFA α₀</td><td>NMFA width w</td><td>iNMFA width</td>' +
      '<td>Distinct growth curves among influential nodes</td></tr></thead><tbody>' +
      rows + '</tbody></table>';

    const el = document.getElementById('paper-verdict');
    el.className = 'verdict';
    el.innerHTML =
      '<b>A perfect crystal is a degenerate case for iNMFA — and the reason is symmetry, not a bug.</b> ' +
      'Look at the last column: the influential blocks of every structure share <b>one single growth curve</b>. ' +
      'They are symmetry-equivalent copies of each other, so every <code>M<sub>i</sub>(r)</code> is identical, ' +
      'every measure <code>u<sub>i</sub>(r)</code> is identical, τ(q) comes out exactly linear in q, and the ' +
      'spectrum collapses to a single point — width <b>0.000</b>. The published method was designed for social ' +
      'and biological networks, where every node genuinely differs. ' +
      '<br><br><b>NMFA over all blocks does work</b>, because node and linker blocks differ from each other: ' +
      'widths run from ' + names.map(n => paperAnalyse(n).nmfa.width).filter(isFinite).sort((a,b)=>a-b)[0].toFixed(2) +
      ' to ' + maxW.toFixed(2) + ' (widest: <b>' + maxName + '</b>). That is a usable heterogeneity measure. ' +
      'And introducing a defect breaks the symmetry, which is what makes the influential-node variant informative again.';
  }

  // ---------------- family fingerprint scatter ----------------
  function drawScatter(canvas, points) {
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = canvas.clientWidth, h = canvas.clientHeight;
    canvas.width = w * dpr; canvas.height = h * dpr;
    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    const pad = { l: 50, r: 18, t: 16, b: 38 };
    const xs = points.map(p => p.x), ys = points.map(p => p.y);
    const xMax = Math.max.apply(null, xs) * 1.15 || 1;
    const yMax = Math.max.apply(null, ys) * 1.15 || 1;

    ctx.strokeStyle = '#e2e6f0'; ctx.fillStyle = '#7c8296'; ctx.font = '11px system-ui';
    for (let g = 0; g <= 4; g++) {
      const y = pad.t + (h - pad.t - pad.b) * (1 - g / 4);
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
      ctx.textAlign = 'right'; ctx.fillText(((yMax * g) / 4).toFixed(1), pad.l - 7, y + 4);
      const x = pad.l + (w - pad.l - pad.r) * (g / 4);
      ctx.textAlign = 'center'; ctx.fillText(((xMax * g) / 4).toFixed(1), x, h - 20);
    }
    ctx.textAlign = 'center';
    ctx.fillText('λ₂  (algebraic connectivity)', (pad.l + w - pad.r) / 2, h - 6);
    ctx.save(); ctx.translate(14, (pad.t + h - pad.b) / 2); ctx.rotate(-Math.PI / 2);
    ctx.fillText('λ max', 0, 0); ctx.restore();

    points.forEach(p => {
      const x = pad.l + (w - pad.l - pad.r) * (p.x / xMax);
      const y = pad.t + (h - pad.t - pad.b) * (1 - p.y / yMax);
      ctx.beginPath(); ctx.arc(x, y, 9, 0, Math.PI * 2);
      ctx.fillStyle = p.color; ctx.fill();
      ctx.fillStyle = '#1a2033'; ctx.font = '600 11.5px system-ui'; ctx.textAlign = 'left';
      ctx.fillText(p.label + ' (' + p.metal + ')', x + 13, y + 4);
    });
  }

  // ---------------- rendering the whole page for one structure ----------------
  function render() {
    const DATA = structures[current];
    const opts = defectId !== null ? { excludeBlocks: [defectId] } : {};
    const G = mode === 'naive' ? MOFNetwork.buildNaiveGraph(DATA)
                               : MOFNetwork.buildQuotientGraph(DATA, opts);
    const deg = MOFNetwork.degrees(G);
    const cent = MOFNetwork.eigenvectorCentrality(G);
    const btw = MOFNetwork.betweenness(G).normalised;
    const spec = MOFNetwork.laplacianSpectrum(G);
    const lit = LIT[current];

    drawGraph(document.getElementById('graph-canvas'), G, deg,
              cent, defectId !== null ? new Set() : null);

    // ---- the same blocks, in the real crystal ----
    if (render3d) {
      const opts = defectId !== null ? { excludeBlocks: [defectId] } : {};
      render3d.load(DATA, {
        colorMode: 'block', blockColorStyle: 'custom',
        blockColors: blockColours(G, deg, cent),
        showBonds: true, showCell: true, netOnly: false,
      });
      legend3d(G, deg);
    }

    // --- validation table ---
    const nodeCN = [], linkCN = [];
    G.blocks.forEach((b, i) => (b.type === 'metal' ? nodeCN : linkCN).push(deg[i]));
    const uNode = Array.from(new Set(nodeCN)).sort((a, b) => a - b);
    const uLink = Array.from(new Set(linkCN)).sort((a, b) => a - b);
    const nodeOK = uNode.length === 1 && uNode[0] === lit.node;
    const linkOK = uLink.length === 1 && uLink[0] === lit.linker;

    document.getElementById('validation').innerHTML =
      '<table class="data-table"><thead><tr><td>Quantity</td><td>Computed</td><td>Published</td><td>Match</td></tr></thead><tbody>' +
      row('Node coordination (' + lit.sbu + ')', uNode.join(', '), lit.node, nodeOK && mode === 'periodic') +
      row('Linker coordination', uLink.join(', '), lit.linker, linkOK && mode === 'periodic') +
      row('Underlying net', '—', lit.net, null) +
      '<tr><td class="dt-label">Blocks / edges</td><td class="dt-value">' + G.n + ' / ' + G.edges.length +
      '</td><td class="dt-note" colspan="2">' +
      (mode === 'naive'
        ? '<b style="color:#a8382c">Naive graph: periodic translations discarded</b>'
        : 'Labelled quotient graph (translations preserved)') + '</td></tr>' +
      '</tbody></table>';

    // --- centrality table ---
    const distinct = MOFNetwork.distinctCount(cent);
    const order = cent.map((v, i) => i).sort((a, b) => cent[b] - cent[a]);
    let rows = '';
    order.slice(0, 8).forEach(i => {
      const b = G.blocks[i];
      rows += '<tr><td class="dt-label">#' + b.id + ' <span style="color:' +
        (b.type === 'metal' ? NODE_C : LINK_C) + '">●</span> ' +
        (b.type === 'metal' ? 'node' : 'linker') + '</td>' +
        '<td class="dt-value">' + deg[i] + '</td>' +
        '<td class="dt-value">' + cent[i].toFixed(3) + '</td>' +
        '<td class="dt-value">' + btw[i].toFixed(3) + '</td></tr>';
    });
    document.getElementById('centrality').innerHTML =
      '<table class="data-table"><thead><tr><td>Block</td><td>Degree</td><td>Eigenvector</td><td>Betweenness</td></tr></thead><tbody>' +
      rows + '</tbody></table>';

    const degen = distinct <= 2;
    document.getElementById('degeneracy').className = degen ? 'verdict' : 'verdict ok';
    document.getElementById('degeneracy').innerHTML = degen
      ? '<b>Only ' + distinct + ' distinct centrality values across ' + G.n + ' blocks — ranking is not meaningful here.</b> ' +
        'This is not a bug: in a defect-free crystal every symmetry-equivalent block is genuinely identical, so no ordering among them can exist. ' +
        'Any "top-k most influential" list computed on a perfect cell is really just reporting the sort order of tied values. ' +
        'Use the defect simulation below to break the symmetry and make influence a real quantity.'
      : '<b>' + distinct + ' distinct centrality values across ' + G.n + ' blocks — ranking is now meaningful.</b> ' +
        'Removing a linker broke the symmetry, so blocks are no longer interchangeable and centrality genuinely separates them.';

    // --- spectrum ---
    drawSpectrum(document.getElementById('spectrum-canvas'),
      [{ values: spec, color: NODE_C }]);
    const ss = document.getElementById('spectrum-stats');
    if (ss) ss.innerHTML =
      '<b>λ₂ = ' + (spec[1] || 0).toFixed(3) + '</b> (algebraic connectivity — how hard the framework is to cut) &nbsp;·&nbsp; ' +
      '<b>λ<sub>max</sub> = ' + (spec[spec.length - 1] || 0).toFixed(2) + '</b> (scales with the highest coordination number) &nbsp;·&nbsp; ' +
      spec.length + ' eigenvalues';

    document.querySelectorAll('.struct-tab').forEach(b =>
      b.classList.toggle('active', b.dataset.name === current));
    document.getElementById('btn-periodic').classList.toggle('active', mode === 'periodic');
    document.getElementById('btn-naive').classList.toggle('active', mode === 'naive');
  }

  function row(label, computed, published, ok) {
    const badge = ok === null ? '' :
      (ok ? '<b style="color:#1f9d67">✓ matches</b>' : '<b style="color:#d64545">✗ differs</b>');
    return '<tr><td class="dt-label">' + label + '</td><td class="dt-value">' + computed +
      '</td><td class="dt-value">' + published + '</td><td class="dt-note">' + badge + '</td></tr>';
  }

  // --- defect simulation panel ---
  function renderDefect() {
    const DATA = structures[current];
    const perfect = MOFNetwork.analyse(DATA);
    const linkers = DATA.blocks.filter(b => b.type === 'linker');
    if (!linkers.length) { document.getElementById('defect-result').innerHTML = ''; return; }
    const d = MOFNetwork.analyse(DATA, { excludeBlocks: [linkers[0].id] });
    const changed = d.distinctCentrality > perfect.distinctCentrality;
    document.getElementById('defect-result').innerHTML =
      '<table class="data-table"><thead><tr><td></td><td>Perfect crystal</td><td>One linker removed</td><td>Effect</td></tr></thead><tbody>' +
      '<tr><td class="dt-label">Distinct centrality values</td><td class="dt-value">' + perfect.distinctCentrality +
      '</td><td class="dt-value" style="color:#1f9d67">' + d.distinctCentrality + '</td><td class="dt-note">' +
      (changed ? 'symmetry broken — blocks become distinguishable' : 'still symmetric — remaining blocks are all equivalent') + '</td></tr>' +
      '<tr><td class="dt-label">λ₂ (algebraic connectivity)</td><td class="dt-value">' + perfect.lambda2.toFixed(3) +
      '</td><td class="dt-value">' + d.lambda2.toFixed(3) + '</td><td class="dt-note">' +
      (d.lambda2 < perfect.lambda2 ? 'framework became easier to cut — quantifies the weakening' : 'unchanged') + '</td></tr>' +
      '<tr><td class="dt-label">Blocks / edges</td><td class="dt-value">' + perfect.nBlocks + ' / ' + perfect.nEdges +
      '</td><td class="dt-value">' + d.nBlocks + ' / ' + d.nEdges + '</td><td class="dt-note">the removed linker and its bonds</td></tr>' +
      '</tbody></table>';
  }

  // --- cross-structure fingerprint ---
  function renderFingerprint() {
    const cols = { 'HKUST-1': '#d81e40', 'UiO-66': '#1f9d67', 'MOF-5': '#e0873a', 'ZIF-8': '#8a56c9' };
    const series = [], points = [], rows = [];
    Object.keys(structures).forEach(name => {
      const r = MOFNetwork.analyse(structures[name]);
      const metal = metalOf(structures[name]);
      series.push({ values: r.spectrum, color: cols[name] || '#666' });
      points.push({ x: r.lambda2, y: r.lambdaMax, label: name, metal, color: cols[name] || '#666' });
      rows.push('<tr><td class="dt-label"><span style="color:' + (cols[name] || '#666') + '">●</span> ' + name +
        '</td><td class="dt-value">' + metal + '</td><td class="dt-value">' + r.nodeCN.join(',') +
        '</td><td class="dt-value">' + r.lambda2.toFixed(3) + '</td><td class="dt-value">' + r.lambdaMax.toFixed(2) +
        '</td><td class="dt-note">' + (LIT[name] ? LIT[name].net : '') + '</td></tr>');
    });
    drawSpectrum(document.getElementById('all-spectrum-canvas'), series);
    drawScatter(document.getElementById('scatter-canvas'), points);
    document.getElementById('fingerprint-table').innerHTML =
      '<table class="data-table"><thead><tr><td>Structure</td><td>Metal</td><td>Node c.n.</td><td>λ₂</td><td>λmax</td><td>Net</td></tr></thead><tbody>' +
      rows.join('') + '</tbody></table>';
  }

  function metalOf(DATA) {
    const M = (window.MOFDecompose && MOFDecompose.METALS) || new Set();
    const found = new Set();
    DATA.atoms.forEach(a => { if (M.has(a.el)) found.add(a.el); });
    return Array.from(found).join(',') || '—';
  }

  // ---------------- boot ----------------
  document.addEventListener('DOMContentLoaded', function () {
    const names = Object.keys(window.DEFAULT_CIFS);
    names.forEach(name => {
      const p = MOFDecompose.parseCIF(window.DEFAULT_CIFS[name]);
      p.atoms.cellPar = p.cellPar;
      structures[name] = MOFDecompose.buildMetalOxoVariant(p.atoms, p.cellMatrix);
    });
    current = names.indexOf('HKUST-1') >= 0 ? 'HKUST-1' : names[0];

    const tabs = document.getElementById('net-struct-tabs');
    names.forEach(name => {
      const b = document.createElement('button');
      b.className = 'struct-tab'; b.dataset.name = name; b.textContent = name;
      b.addEventListener('click', () => { current = name; defectId = null; render(); renderDefect();
        try { renderMultifractal(); } catch (e) {}
        try { renderPaper(); } catch (e) {} });
      tabs.appendChild(b);
    });

    document.getElementById('btn-periodic').addEventListener('click', () => { mode = 'periodic'; render(); });
    document.getElementById('btn-naive').addEventListener('click', () => { mode = 'naive'; render(); });
    document.getElementById('btn-defect').addEventListener('click', () => {
      const linkers = structures[current].blocks.filter(b => b.type === 'linker');
      defectId = defectId === null && linkers.length ? linkers[0].id : null;
      document.getElementById('btn-defect').classList.toggle('active', defectId !== null);
      document.getElementById('btn-defect').textContent =
        defectId !== null ? '✓ Defect applied — restore linker' : 'Remove one linker (simulate a defect)';
      render();
    });

    // 3D molecular view (guarded: if three.js failed to load, the rest of the
    // page still works and the panel explains itself)
    const wrap3d = document.getElementById('mol3d-wrap');
    if (window.THREE && wrap3d) {
      render3d = window.MOFRender.create();
      render3d.init(document.getElementById('mol3d-canvas'), wrap3d,
                    document.getElementById('mol3d-labels'), document.getElementById('mol3d-tip'));
    } else if (wrap3d) {
      wrap3d.innerHTML = '<div style="color:#ffb4a8;font:13px/1.6 system-ui;padding:22px;text-align:center">' +
        '<b>3D library not loaded.</b><br>Save <code>three.min.js</code> into this folder, or connect to the internet.<br>' +
        'The graph analysis on the left works either way.</div>';
    }

    function setColour(mode3, top) {
      colour3d = mode3; highlightTop = top;
      ['c3d-degree', 'c3d-central', 'c3d-role', 'c3d-top'].forEach(id => {
        const b = document.getElementById(id); if (b) b.classList.remove('active');
      });
      const activeId = top ? 'c3d-top' : (mode3 === 'degree' ? 'c3d-degree' : mode3 === 'centrality' ? 'c3d-central' : 'c3d-role');
      const ab = document.getElementById(activeId); if (ab) ab.classList.add('active');
      render();
    }
    const bind = (id, m, t) => { const b = document.getElementById(id); if (b) b.addEventListener('click', () => setColour(m, t)); };
    bind('c3d-degree', 'degree', false);
    bind('c3d-central', 'centrality', false);
    bind('c3d-role', 'role', false);
    bind('c3d-top', colour3d, true);

    wireHover(document.getElementById('graph-canvas'), document.getElementById('graph-tip'));
    render(); renderDefect(); renderFingerprint();
    try { renderMultifractal(); } catch (e) {}
    try { renderPaper(); } catch (e) {}
    window.addEventListener('resize', () => { render(); renderFingerprint(); });
  });
})();
