// band_page.js
// Section 15b — the multifractal band across 77 real frameworks.
//
// This section reports two corrections and one retraction:
//
//   1. THE SHAPE WAS WRONG.  A multifractal spectrum f(alpha) must be an
//      inverted parabola peaking at q=0, where f(alpha_0)=D_0. Ours sloped
//      downhill. Cause: the paper defines tau = ln P_q / ln(r/r_N), a fit
//      THROUGH THE ORIGIN, but the code used a free-intercept least-squares
//      slope. At q=0 every term is pr_i^0=1, so P_0=|I| is constant in r; a
//      flat line has slope 0, forcing tau(0)=0 and f(alpha_0)=0 -- deleting
//      the peak. Fixed in the notebook via tau_mode="paper".
//
//   2. THE BAND IS CONFOUNDED BY GRAPH SIZE.  Delta-alpha correlates with pore
//      diameter (r=-0.33) but that vanishes once graph size is controlled for
//      (partial r=+0.06), while size survives controlling for pore diameter
//      (+0.38). Pore size adds R^2 = +0.002 over size alone. So Delta-alpha
//      is tracking supercell size, which is set by MIN_CELL_LENGTH and the
//      MAX_ATOMS cap -- computational parameters, not chemistry.
//
// band_data.js now carries spectra computed with the CORRECTED tau: all 77 are
// proper inverted parabolas peaking at q = 0. The size-confound finding is
// independent of the tau fix and, on the corrected data, is stronger still.

(function () {
  'use strict';

  let sortKey = 'width', showN = 40;

  function fmt(v, n) { return (v === null || v === undefined || isNaN(v)) ? '—' : (+v).toFixed(n === undefined ? 3 : n); }

  function cleanCurve(alpha, f) {
    const pts = [];
    for (let i = 0; i < alpha.length; i++) {
      if (isFinite(alpha[i]) && isFinite(f[i])) pts.push([alpha[i], f[i]]);
    }
    pts.sort((a, b) => a[0] - b[0]);
    const a = [], y = [];
    pts.forEach(pt => {
      if (a.length && Math.abs(pt[0] - a[a.length - 1]) < 1e-12) y[y.length - 1] = (y[y.length - 1] + pt[1]) / 2;
      else { a.push(pt[0]); y.push(pt[1]); }
    });
    return { a, f: y };
  }


  // ------------------------------------------------- the f(alpha) spectra
  // Draws every curve and marks q = 0 on each. If the data came from the
  // corrected tau, the q=0 marks sit at the APEX of each curve. If they sit at
  // the bottom-right instead, the data predates the tau fix -- which the page
  // detects and says out loud rather than quietly drawing the wrong shape.
  function tauIsFixed() {
    const D = window.BAND_DATA;
    const k = Object.keys(D)[0]; if (!k) return false;
    const q = D[k].q, f = D[k].f_alpha;
    let i0 = 0, best = Infinity, pk = 0, mx = -Infinity;
    q.forEach((v, i) => { if (Math.abs(v) < best) { best = Math.abs(v); i0 = i; } });
    f.forEach((v, i) => { if (isFinite(v) && v > mx) { mx = v; pk = i; } });
    return pk === i0;
  }

  function drawSpectra(canvas) {
    const D = window.BAND_DATA;
    if (!canvas || !D) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const W = canvas.clientWidth || 700, H = canvas.clientHeight || 380;
    canvas.width = W * dpr; canvas.height = H * dpr;
    const g = canvas.getContext('2d'); if (!g) return;
    g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);

    const names = Object.keys(D).sort((a, b) => D[b].width - D[a].width);
    let amin = Infinity, amax = -Infinity, fmin = Infinity, fmax = -Infinity;
    names.forEach(n => {
      D[n].alpha.forEach(v => { if (isFinite(v)) { amin = Math.min(amin, v); amax = Math.max(amax, v); } });
      D[n].f_alpha.forEach(v => { if (isFinite(v)) { fmin = Math.min(fmin, v); fmax = Math.max(fmax, v); } });
    });
    const padL = 56, padR = 16, padT = 16, padB = 42;
    const pw = W - padL - padR, ph = H - padT - padB;
    const X = a => padL + ((a - amin) / (amax - amin || 1)) * pw;
    const Y = f => padT + ph - ((f - fmin) / (fmax - fmin || 1)) * ph;

    g.strokeStyle = PAL.alpha(PAL.text, .06); g.lineWidth = 1;
    for (let k = 0; k <= 4; k++) {
      const y = padT + (ph * k) / 4;
      g.beginPath(); g.moveTo(padL, y); g.lineTo(padL + pw, y); g.stroke();
    }
    g.strokeStyle = PAL.text3; g.lineWidth = 1.1;
    g.beginPath(); g.moveTo(padL, padT); g.lineTo(padL, padT + ph); g.lineTo(padL + pw, padT + ph); g.stroke();
    g.fillStyle = PAL.text3; g.font = '11px system-ui,sans-serif'; g.textAlign = 'center';
    g.fillText('α  (local scaling exponent)', padL + pw / 2, H - 10);
    for (let k = 0; k <= 4; k++) {
      const a = amin + ((amax - amin) * k) / 4;
      g.fillText(a.toFixed(2), X(a), padT + ph + 15);
    }
    g.textAlign = 'right';
    for (let k = 0; k <= 4; k++) {
      const f = fmin + ((fmax - fmin) * k) / 4;
      g.fillText(f.toFixed(1), padL - 6, padT + ph - (ph * k) / 4 + 4);
    }
    g.save(); g.translate(15, padT + ph / 2); g.rotate(-Math.PI / 2);
    g.textAlign = 'center'; g.fillText('f(α)', 0, 0); g.restore();

    // curves, coloured by width so the spread is legible
    const ws = names.map(n => D[n].width);
    const wmin = Math.min.apply(null, ws), wmax = Math.max.apply(null, ws);
    names.forEach(n => {
      const d = D[n], t = (d.width - wmin) / (wmax - wmin || 1);
      g.beginPath();
      let started = false, i0 = 0, best = Infinity;
      d.alpha.forEach((a, i) => {
        const f = d.f_alpha[i];
        if (!isFinite(a) || !isFinite(f)) return;
        if (!started) { g.moveTo(X(a), Y(f)); started = true; } else g.lineTo(X(a), Y(f));
        if (Math.abs(d.q[i]) < best) { best = Math.abs(d.q[i]); i0 = i; }
      });
      g.strokeStyle = 'rgba(' + Math.round(40 + 200 * t) + ',' + Math.round(100 + 40 * (1 - t)) + ',' + Math.round(190 - 110 * t) + ',0.5)';
      g.lineWidth = 1.1; g.stroke();
      // mark q = 0
      const a0 = d.alpha[i0], f0 = d.f_alpha[i0];
      if (isFinite(a0) && isFinite(f0)) {
        g.beginPath(); g.arc(X(a0), Y(f0), 2.6, 0, Math.PI * 2);
        g.fillStyle = PAL.text; g.fill();
      }
    });
    g.textAlign = 'left'; g.font = '10.5px system-ui,sans-serif'; g.fillStyle = PAL.text;
    g.fillText('● = q = 0', padL + 10, padT + 14);
    g.fillText(tauIsFixed() ? '   (at the apex — τ is correct)'
                            : '   (NOT at the apex — data predates the τ fix)',
               padL + 60, padT + 14);
  }

  // ---------------------------------------------------------- the band chart
  function drawBand(canvas) {
    const D = window.BAND_DATA, S = window.BAND_STATS;
    if (!canvas || !D) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const W = canvas.clientWidth || 700, H = canvas.clientHeight || 300;
    canvas.width = W * dpr; canvas.height = H * dpr;
    const g = canvas.getContext('2d'); if (!g) return;
    g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);

    const names = Object.keys(D).sort((a, b) => D[a].width - D[b].width);
    const ws = names.map(n => D[n].width);
    const wmax = Math.max.apply(null, ws) * 1.06;
    const padL = 52, padR = 16, padT = 16, padB = 40;
    const pw = W - padL - padR, ph = H - padT - padB;
    const X = i => padL + (i / (names.length - 1 || 1)) * pw;
    const Y = w => padT + ph - (w / wmax) * ph;

    // band region
    g.fillStyle = PAL.alpha(PAL.accent2, .16);
    g.fillRect(padL, Y(S.band_hi), pw, Y(S.band_lo) - Y(S.band_hi));
    g.strokeStyle = PAL.alpha(PAL.accent2, .6); g.setLineDash([5, 4]); g.lineWidth = 1.2;
    g.strokeRect(padL, Y(S.band_hi), pw, Y(S.band_lo) - Y(S.band_hi));
    g.setLineDash([]);
    g.fillStyle = PAL.accent2; g.font = '600 11px system-ui,sans-serif'; g.textAlign = 'left';
    g.fillText('band (interquartile) ' + fmt(S.band_lo, 2) + ' – ' + fmt(S.band_hi, 2),
               padL + 8, Y(S.band_hi) - 6);

    // axes
    g.strokeStyle = PAL.text3; g.lineWidth = 1.1;
    g.beginPath(); g.moveTo(padL, padT); g.lineTo(padL, padT + ph); g.lineTo(padL + pw, padT + ph); g.stroke();
    g.fillStyle = PAL.text3; g.font = '11px system-ui,sans-serif'; g.textAlign = 'right';
    for (let k = 0; k <= 4; k++) {
      const v = (wmax * k) / 4;
      g.fillText(v.toFixed(2), padL - 6, Y(v) + 4);
      g.strokeStyle = PAL.alpha(PAL.text, .06); g.beginPath(); g.moveTo(padL, Y(v)); g.lineTo(padL + pw, Y(v)); g.stroke();
    }
    g.textAlign = 'center'; g.fillStyle = PAL.text3;
    g.fillText('77 frameworks, sorted by Δα', padL + pw / 2, H - 10);
    g.save(); g.translate(14, padT + ph / 2); g.rotate(-Math.PI / 2);
    g.fillText('Δα', 0, 0); g.restore();

    // points, coloured by graph size — the confound made visible
    const Ns = names.map(n => D[n].N);
    const nmin = Math.min.apply(null, Ns), nmax = Math.max.apply(null, Ns);
    names.forEach((n, i) => {
      const t = (D[n].N - nmin) / (nmax - nmin || 1);
      g.beginPath(); g.arc(X(i), Y(D[n].width), 3.6, 0, Math.PI * 2);
      g.fillStyle = 'rgb(' + Math.round(40 + 200 * t) + ',' + Math.round(90 + 60 * (1 - t)) + ',' + Math.round(190 - 120 * t) + ')';
      g.fill();
    });
    g.textAlign = 'right'; g.font = '10px system-ui,sans-serif'; g.fillStyle = PAL.text3;
    g.fillText('dot colour = supercell size (blue small → red large)', padL + pw, padT + 12);
  }

  // ------------------------------------------------- the confound bar chart
  function drawConfound(canvas) {
    const S = window.BAND_STATS;
    if (!canvas || !S) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const W = canvas.clientWidth || 640, H = canvas.clientHeight || 250;
    canvas.width = W * dpr; canvas.height = H * dpr;
    const g = canvas.getContext('2d'); if (!g) return;
    g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);

    const bars = [
      { l: 'pore size (LCD)\nraw', v: S.r_lcd, c: PAL.brand },
      { l: 'pore size (LCD)\ncontrolling for size', v: S.p_lcd_given_size, c: PAL.brand },
      { l: 'graph size\nraw', v: S.r_size, c: PAL.node },
      { l: 'graph size\ncontrolling for LCD', v: S.p_size_given_lcd, c: PAL.node },
    ];
    const padL = 54, padB = 52, padT = 18;
    const pw = W - padL - 16, ph = H - padB - padT;
    const zero = padT + ph / 2, scale = ph / 2 / 0.6;
    g.strokeStyle = PAL.text3; g.lineWidth = 1.1;
    g.beginPath(); g.moveTo(padL, zero); g.lineTo(padL + pw, zero); g.stroke();
    g.fillStyle = PAL.text3; g.font = '11px system-ui,sans-serif'; g.textAlign = 'right';
    [-0.5, -0.25, 0, 0.25, 0.5].forEach(v => {
      g.fillText(v.toFixed(2), padL - 6, zero - v * scale + 4);
      g.strokeStyle = PAL.alpha(PAL.text, .06);
      g.beginPath(); g.moveTo(padL, zero - v * scale); g.lineTo(padL + pw, zero - v * scale); g.stroke();
    });
    const bw = pw / bars.length * 0.56;
    bars.forEach((b, i) => {
      const cx = padL + (i + 0.5) * (pw / bars.length);
      const h = b.v * scale;
      g.fillStyle = b.c;
      g.fillRect(cx - bw / 2, h >= 0 ? zero - h : zero, bw, Math.abs(h));
      g.fillStyle = PAL.text; g.font = '700 11px system-ui,sans-serif'; g.textAlign = 'center';
      g.fillText((b.v >= 0 ? '+' : '') + b.v.toFixed(2), cx, h >= 0 ? zero - h - 6 : zero - h + 14);
      g.fillStyle = PAL.text; g.font = '10px system-ui,sans-serif';
      b.l.split('\n').forEach((ln, k) => g.fillText(ln, cx, padT + ph + 16 + k * 12));
    });
    g.fillStyle = PAL.text3; g.font = '11px system-ui,sans-serif'; g.textAlign = 'left';
    g.save(); g.translate(14, padT + ph / 2); g.rotate(-Math.PI / 2);
    g.textAlign = 'center'; g.fillText('correlation with Δα', 0, 0); g.restore();
  }

  // ------------------------------------------------------------------- UI
  function render() {
    const D = window.BAND_DATA, S = window.BAND_STATS;
    const host = document.getElementById('band-body');
    if (!host || !D || !S) return;

    const names = Object.keys(D).sort((a, b) =>
      sortKey === 'width' ? D[b].width - D[a].width :
      sortKey === 'lcd' ? D[b].lcd - D[a].lcd : D[b].N - D[a].N);

    const rows = names.slice(0, showN).map(n => {
      const d = D[n];
      const inb = d.width >= S.band_lo && d.width <= S.band_hi;
      return '<tr><td>' + n + '</td>' +
        '<td class="r">' + d.N.toLocaleString() + '</td>' +
        '<td class="r">' + d.diameter + '</td>' +
        '<td class="r">' + fmt(d.pld, 2) + '</td>' +
        '<td class="r">' + fmt(d.lcd, 2) + '</td>' +
        '<td class="r"><b>' + fmt(d.width) + '</b> <span class="sd">± ' + fmt(d.width_sd) + '</span></td>' +
        '<td>' + (inb ? '<span class="pill in">in band</span>' : '<span class="pill out">outside</span>') + '</td></tr>';
    }).join('');

    host.innerHTML =
      '<div class="negbox"><b>These spectra come from the corrected τ.</b> ' +
        'All ' + S.parabolic + ' of ' + S.n + ' frameworks are proper inverted parabolas peaking at ' +
        'q = 0, which is what a multifractal spectrum must do. What the band <i>means</i> is a ' +
        'separate question, answered below.</div>' +

      '<h4 class="bh">1 · The spectra — ' + S.n + ' curves, ● marks q = 0</h4>' +
      '<canvas id="spec-canvas" style="width:100%;height:380px;display:block"></canvas>' +
      '<p class="cap">' + (tauIsFixed()
        ? 'Every curve peaks at its q = 0 marker, which is what a multifractal spectrum must do — '
          + 'f(α₀) = D₀ is the apex. τ is being computed as the paper defines it.'
        : '<b>These curves predate the τ fix.</b> The q = 0 markers sit at the bottom right rather '
          + 'than at the apex, because a free-intercept fit forces τ(0) = 0 and therefore f(α₀) = 0. '
          + 'Re-running <span class="code-chip">mof_band_analysis.ipynb</span> regenerates '
          + '<code>results.json</code> with the corrected definition, and these become proper '
          + 'inverted parabolas.') + '</p>' +

      '<h4 class="bh">2 · The Δα band across ' + S.n + ' frameworks</h4>' +
      '<canvas id="band-canvas" style="width:100%;height:300px;display:block"></canvas>' +
      '<p class="cap">Each dot is one framework. The shaded region is the interquartile band, ' +
        'Δα ' + fmt(S.band_lo, 2) + '–' + fmt(S.band_hi, 2) + '. <b>Dot colour is supercell size</b> — ' +
        'note how strongly colour tracks height. That is the problem, and the next panel measures it.</p>' +

      '<h4 class="bh">3 · Does the band mean pore architecture? No.</h4>' +
      '<canvas id="conf-canvas" style="width:100%;height:250px;display:block"></canvas>' +
      '<p class="cap">Δα correlates with pore diameter at <b>r = ' + fmt(S.r_lcd, 2) + '</b>, which ' +
        'looks like a real structural result. But controlling for graph size collapses it to ' +
        '<b>' + fmt(S.p_lcd_given_size, 2) + '</b>, while graph size <i>survives</i> controlling for pore ' +
        'diameter at <b>+' + fmt(S.p_size_given_lcd, 2) + '</b>. In a linear model, graph size alone gives ' +
        'R² = ' + fmt(S.r2_size, 2) + '; adding pore diameter takes it to ' + fmt(S.r2_both, 2) + ' — ' +
        '<b>pore size buys +' + fmt(S.r2_both - S.r2_size, 3) + '</b>.</p>' +

      '<div class="negbox"><b>Withdrawn: “the band groups MOFs by pore architecture.”</b> ' +
        'On 8 frameworks that reading was plausible. On 77 it does not hold — Δα is tracking ' +
        'how many atoms are in the supercell, and supercell size is set by <code>MIN_CELL_LENGTH</code> ' +
        'and the <code>MAX_ATOMS</code> cap, which are computational parameters rather than chemistry. ' +
        'Two routes make the question answerable: compare only frameworks of comparable graph size, ' +
        'or normalise the fit window so Δα stops growing with the graph, then re-test.</div>' +

      '<div class="band-controls">' +
        '<button class="mini' + (sortKey === 'width' ? ' active' : '') + '" id="bs-w">sort by Δα</button>' +
        '<button class="mini' + (sortKey === 'lcd' ? ' active' : '') + '" id="bs-l">sort by pore size</button>' +
        '<button class="mini' + (sortKey === 'size' ? ' active' : '') + '" id="bs-n">sort by graph size</button>' +
        '<button class="mini" id="bs-more">' + (showN >= names.length ? 'show fewer' : 'show all ' + names.length) + '</button>' +
      '</div>' +
      '<table class="tbl band-tbl"><thead><tr><th>Framework</th><th class="r">Atoms</th>' +
        '<th class="r">Diam</th><th class="r">PLD Å</th><th class="r">LCD Å</th>' +
        '<th class="r">Δα</th><th>Band</th></tr></thead><tbody>' + rows + '</tbody></table>' +
      '<p class="cap">Showing ' + Math.min(showN, names.length) + ' of ' + names.length + '.</p>';

    drawSpectra(document.getElementById('spec-canvas'));
    drawBand(document.getElementById('band-canvas'));
    drawConfound(document.getElementById('conf-canvas'));
    if (!render._r) {
      render._r = true;
      window.addEventListener('resize', () => {
        drawSpectra(document.getElementById('spec-canvas'));
    drawBand(document.getElementById('band-canvas'));
        drawConfound(document.getElementById('conf-canvas'));
      });
    }
    const b = (id, fn) => { const e = document.getElementById(id); if (e) e.addEventListener('click', fn); };
    b('bs-w', () => { sortKey = 'width'; render(); });
    b('bs-l', () => { sortKey = 'lcd'; render(); });
    b('bs-n', () => { sortKey = 'size'; render(); });
    b('bs-more', () => { showN = showN >= Object.keys(D).length ? 40 : 999; render(); });
  }

  function boot() {
    if (!document.getElementById('band-body') || !window.BAND_DATA) return;
    try { render(); } catch (e) { console.error('band section failed', e); }
    // Repaint the three canvases when the theme changes (see palette.js).
    if (window.PAL && PAL.onTheme) PAL.onTheme(function () {
      try { render(); } catch (e) {}
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

  window.MOFBand = { render, cleanCurve, tauIsFixed };
})();
