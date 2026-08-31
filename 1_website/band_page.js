// band_page.js
// Section 15b — the multifractal band across eight real frameworks.
//
// TWO different things get called "the band", and only one of them works as a
// membership test. This section shows both, and says which is which:
//
//   1. The Delta-alpha band (1-D).  Spectrum WIDTH only. The six grouped
//      frameworks span 0.835-0.941; the two outliers sit at 0.375 and 0.203.
//      The gap between the groups is 0.46 against a measured noise floor of
//      0.105 -- about 4x the noise. This separation is real.
//
//   2. The f(alpha) envelope (2-D).  Shade between the highest and lowest
//      curve and ask whether a candidate falls inside. MEASURED HERE: this
//      does NOT discriminate. Held out, ZIF-8 (a member) scores 0.0% while
//      UMCM-1 (a non-member) scores 44.7% -- the non-member scores far HIGHER.
//      The reason is visible in the plot: the narrow curves sit inside the
//      wide group's alpha range but far below it in f, so an envelope test
//      is dominated by alpha position rather than by width.
//
// Reporting 2 as a negative result rather than hiding it is the point. The
// hold-out buttons below let anyone reproduce it.

(function () {
  'use strict';

  const IN_BAND = ['Co-MOF-74', 'ZIF-8', 'Mg-MOF-74', 'Zn-MOF-74',
                   'HKUST-1 (Cu-BTC)', 'Ni-MOF-74'];
  const FAMILY_74 = ['Ni-MOF-74', 'Co-MOF-74', 'Mg-MOF-74', 'Zn-MOF-74'];
  const NOISE_FLOOR = 0.105;   // measured spread across the isomorphic MOF-74 graphs

  const COLOR = {
    'Co-MOF-74': '#e06c3b', 'Ni-MOF-74': '#e0993b', 'Mg-MOF-74': '#c9873b',
    'Zn-MOF-74': '#b5623b', 'HKUST-1 (Cu-BTC)': '#c94f7c', 'ZIF-8': '#8a56c9',
    'IRMOF-1 (MOF-5)': '#1f9d67', 'UMCM-1': '#2f7fd1',
  };

  let held = null;

  // ------------------------------------------------------------- band maths
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

  function interp(grid, a, f) {
    return grid.map(x => {
      if (x < a[0] || x > a[a.length - 1]) return NaN;
      let i = 0;
      while (i < a.length - 2 && a[i + 1] < x) i++;
      const t = (x - a[i]) / (a[i + 1] - a[i] || 1);
      return f[i] + t * (f[i + 1] - f[i]);
    });
  }

  function buildBand(names, nGrid) {
    const D = window.BAND_DATA;
    const curves = names.filter(n => D[n]).map(n => cleanCurve(D[n].alpha, D[n].f_alpha));
    if (curves.length < 2) return null;
    const lo = Math.min.apply(null, curves.map(c => c.a[0]));
    const hi = Math.max.apply(null, curves.map(c => c.a[c.a.length - 1]));
    nGrid = nGrid || 200;
    const grid = [];
    for (let i = 0; i < nGrid; i++) grid.push(lo + ((hi - lo) * i) / (nGrid - 1));
    const stack = curves.map(c => interp(grid, c.a, c.f));
    const lower = [], upper = [];
    grid.forEach((_x, i) => {
      const v = stack.map(s => s[i]).filter(isFinite);
      lower.push(v.length ? Math.min.apply(null, v) : NaN);
      upper.push(v.length ? Math.max.apply(null, v) : NaN);
    });
    return { grid, lower, upper, n: curves.length };
  }

  function scoreAgainst(band, name) {
    const D = window.BAND_DATA[name];
    if (!band || !D) return null;
    const c = cleanCurve(D.alpha, D.f_alpha);
    const fi = interp(band.grid, c.a, c.f);
    let inside = 0, tot = 0;
    for (let i = 0; i < band.grid.length; i++) {
      if (!isFinite(fi[i]) || !isFinite(band.lower[i]) || !isFinite(band.upper[i])) continue;
      tot++;
      if (fi[i] >= band.lower[i] - 1e-9 && fi[i] <= band.upper[i] + 1e-9) inside++;
    }
    return { pct: tot ? (100 * inside) / tot : null, n: tot };
  }

  // 1-D test: is the width inside the band members' width range (+/- noise)?
  function widthTest(name, members) {
    const D = window.BAND_DATA;
    const w = members.filter(n => n !== name).map(n => D[n].width);
    if (!w.length) return null;
    const lo = Math.min.apply(null, w), hi = Math.max.apply(null, w);
    const v = D[name].width;
    return { lo, hi, v, inside: v >= lo - NOISE_FLOOR && v <= hi + NOISE_FLOOR,
             margin: v < lo ? lo - v : (v > hi ? v - hi : 0) };
  }

  // --------------------------------------------------------- the width axis
  function drawWidthAxis(canvas) {
    const D = window.BAND_DATA;
    if (!canvas || !D) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const W = canvas.clientWidth || 680, H = 168;
    canvas.width = W * dpr; canvas.height = H * dpr;
    const g = canvas.getContext('2d');
    if (!g) return;
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, W, H);

    const padL = 22, padR = 22, y = 104;
    const pw = W - padL - padR;
    const lo = 0, hi = 1.05;
    const X = v => padL + ((v - lo) / (hi - lo)) * pw;

    const members = IN_BAND.filter(n => n !== held);
    const ws = members.map(n => D[n].width);
    const bLo = Math.min.apply(null, ws), bHi = Math.max.apply(null, ws);

    // the band
    g.fillStyle = 'rgba(138,86,201,0.20)';
    g.fillRect(X(bLo), y - 34, X(bHi) - X(bLo), 68);
    g.strokeStyle = 'rgba(138,86,201,0.75)'; g.lineWidth = 1.3; g.setLineDash([5, 4]);
    g.strokeRect(X(bLo), y - 34, X(bHi) - X(bLo), 68);
    g.setLineDash([]);
    g.fillStyle = '#6b3fa8'; g.font = '600 11px system-ui,sans-serif'; g.textAlign = 'center';
    g.fillText('the band  ' + bLo.toFixed(3) + ' – ' + bHi.toFixed(3),
               (X(bLo) + X(bHi)) / 2, y - 42);

    // axis
    g.strokeStyle = '#888'; g.lineWidth = 1.2;
    g.beginPath(); g.moveTo(padL, y); g.lineTo(padL + pw, y); g.stroke();
    g.fillStyle = '#555'; g.font = '11px system-ui,sans-serif';
    for (let v = 0; v <= 1.0001; v += 0.2) {
      g.beginPath(); g.moveTo(X(v), y); g.lineTo(X(v), y + 5); g.stroke();
      g.fillText(v.toFixed(1), X(v), y + 18);
    }
    g.fillText('Δα  (spectrum width)', padL + pw / 2, y + 38);

    // markers, dodged vertically when they collide
    const pts = Object.keys(D).map(n => ({ n, x: X(D[n].width), w: D[n].width }))
                              .sort((a, b) => a.x - b.x);
    let lastX = -999, lane = 0;
    pts.forEach(pt => {
      lane = (pt.x - lastX < 46) ? lane + 1 : 0;
      lastX = pt.x;
      const yy = y - 8 - (lane % 3) * 15;
      g.beginPath(); g.arc(pt.x, y, held === pt.n ? 7 : 5, 0, Math.PI * 2);
      g.fillStyle = COLOR[pt.n] || '#888'; g.fill();
      if (held === pt.n) { g.strokeStyle = '#222'; g.lineWidth = 2; g.stroke(); }
      g.save();
      g.font = (held === pt.n ? '700 ' : '') + '10px system-ui,sans-serif';
      g.fillStyle = '#33384a'; g.textAlign = 'center';
      const short = pt.n.replace(' (Cu-BTC)', '').replace(' (MOF-5)', '');
      g.fillText(short, pt.x, yy);
      g.restore();
    });

    // the gap
    const gapLo = 0.375, gapHi = 0.835;
    g.strokeStyle = '#b02a2a'; g.lineWidth = 1.4;
    g.beginPath(); g.moveTo(X(gapLo), y + 52); g.lineTo(X(gapHi), y + 52); g.stroke();
    [gapLo, gapHi].forEach(v => {
      g.beginPath(); g.moveTo(X(v), y + 47); g.lineTo(X(v), y + 57); g.stroke();
    });
    g.fillStyle = '#b02a2a'; g.font = '600 10.5px system-ui,sans-serif';
    g.fillText('gap 0.46  ≈ 4× the 0.105 noise floor', (X(gapLo) + X(gapHi)) / 2, y + 66);
  }

  // ------------------------------------------------------------ the curves
  function drawCurves(canvas) {
    const D = window.BAND_DATA;
    if (!canvas || !D) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const W = canvas.clientWidth || 680, H = canvas.clientHeight || 400;
    canvas.width = W * dpr; canvas.height = H * dpr;
    const g = canvas.getContext('2d');
    if (!g) return;
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, W, H);

    const names = Object.keys(D);
    let amin = Infinity, amax = -Infinity, fmin = Infinity, fmax = -Infinity;
    names.forEach(n => {
      D[n].alpha.forEach(v => { if (isFinite(v)) { amin = Math.min(amin, v); amax = Math.max(amax, v); } });
      D[n].f_alpha.forEach(v => { if (isFinite(v)) { fmin = Math.min(fmin, v); fmax = Math.max(fmax, v); } });
    });
    const padL = 54, padR = 150, padT = 14, padB = 42;
    const pw = W - padL - padR, ph = H - padT - padB;
    const ax = a => padL + ((a - amin) / (amax - amin || 1)) * pw;
    const ay = f => padT + ph - ((f - fmin) / (fmax - fmin || 1)) * ph;

    g.strokeStyle = 'rgba(0,0,0,0.07)'; g.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const yy = padT + (ph * i) / 4;
      g.beginPath(); g.moveTo(padL, yy); g.lineTo(padL + pw, yy); g.stroke();
    }
    g.strokeStyle = '#666'; g.lineWidth = 1.2;
    g.beginPath(); g.moveTo(padL, padT); g.lineTo(padL, padT + ph); g.lineTo(padL + pw, padT + ph); g.stroke();
    g.fillStyle = '#555'; g.font = '11px system-ui,sans-serif'; g.textAlign = 'center';
    g.fillText('α', padL + pw / 2, H - 10);
    for (let i = 0; i <= 4; i++) {
      const a = amin + ((amax - amin) * i) / 4;
      g.fillText(a.toFixed(2), ax(a), padT + ph + 15);
    }
    g.save(); g.translate(13, padT + ph / 2); g.rotate(-Math.PI / 2);
    g.fillText('f(α)', 0, 0); g.restore();
    g.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
      const f = fmin + ((fmax - fmin) * i) / 4;
      g.fillText(f.toFixed(1), padL - 6, padT + ph - (ph * i) / 4 + 4);
    }

    const band = buildBand(IN_BAND.filter(n => n !== held));
    if (band) {
      g.beginPath();
      let started = false;
      band.grid.forEach((x, i) => {
        if (!isFinite(band.upper[i])) return;
        if (!started) { g.moveTo(ax(x), ay(band.upper[i])); started = true; }
        else g.lineTo(ax(x), ay(band.upper[i]));
      });
      for (let i = band.grid.length - 1; i >= 0; i--) {
        if (!isFinite(band.lower[i])) continue;
        g.lineTo(ax(band.grid[i]), ay(band.lower[i]));
      }
      g.closePath();
      g.fillStyle = 'rgba(138,86,201,0.15)'; g.fill();
      g.strokeStyle = 'rgba(138,86,201,0.5)'; g.lineWidth = 1.1; g.setLineDash([5, 4]);
      g.stroke(); g.setLineDash([]);
    }

    names.forEach(n => {
      const c = cleanCurve(D[n].alpha, D[n].f_alpha);
      const isHeld = n === held, outside = !IN_BAND.includes(n);
      g.beginPath();
      c.a.forEach((a, i) => (i ? g.lineTo(ax(a), ay(c.f[i])) : g.moveTo(ax(a), ay(c.f[i]))));
      g.strokeStyle = COLOR[n] || '#888';
      g.lineWidth = isHeld ? 3.2 : (outside ? 2.6 : 1.7);
      g.setLineDash(outside && !isHeld ? [7, 4] : []);
      g.globalAlpha = isHeld ? 1 : (held ? 0.4 : 0.9);
      g.stroke(); g.setLineDash([]); g.globalAlpha = 1;
    });

    // legend
    g.textAlign = 'left'; g.font = '10.5px system-ui,sans-serif';
    Object.keys(D).sort((a, b) => D[b].width - D[a].width).forEach((n, i) => {
      const yy = padT + 12 + i * 16;
      g.strokeStyle = COLOR[n]; g.lineWidth = 2.4;
      g.setLineDash(IN_BAND.includes(n) ? [] : [6, 3]);
      g.beginPath(); g.moveTo(padL + pw + 12, yy); g.lineTo(padL + pw + 32, yy); g.stroke();
      g.setLineDash([]);
      g.fillStyle = held === n ? '#111' : '#444';
      g.font = (held === n ? '700 ' : '') + '10.5px system-ui,sans-serif';
      g.fillText(n.replace(' (Cu-BTC)', '').replace(' (MOF-5)', '') + '  ' + D[n].width.toFixed(2),
                 padL + pw + 37, yy + 3.5);
    });
  }

  // ------------------------------------------------------------------- UI
  function render() {
    const D = window.BAND_DATA;
    const host = document.getElementById('band-body');
    if (!host || !D) return;

    const names = Object.keys(D).sort((a, b) => D[b].width - D[a].width);
    const envBand = buildBand(IN_BAND.filter(n => n !== held));

    const rows = names.map(n => {
      const d = D[n];
      const inb = IN_BAND.includes(n);
      const wt = held === n ? widthTest(n, IN_BAND) : null;
      const es = held === n ? scoreAgainst(envBand, n) : null;
      return '<tr' + (held === n ? ' class="heldrow"' : '') + '>' +
        '<td><span class="swatch" style="background:' + (COLOR[n] || '#888') + '"></span>' + n + '</td>' +
        '<td>' + d.metal + '</td>' +
        '<td>' + d.chemistry + '</td>' +
        '<td class="r">' + d.N.toLocaleString() + '</td>' +
        '<td class="r">' + d.diameter + '</td>' +
        '<td class="r"><b>' + d.width.toFixed(3) + '</b> <span class="sd">± ' + d.width_sd.toFixed(3) + '</span></td>' +
        '<td>' + (inb ? '<span class="pill in">in band</span>' : '<span class="pill out">outside</span>') + '</td>' +
        '<td class="r">' + (wt ? (wt.inside ? '<b class="ok">inside</b>' : '<b class="no">outside by ' + wt.margin.toFixed(2) + '</b>') : '—') + '</td>' +
        '<td class="r">' + (es && es.pct !== null ? es.pct.toFixed(1) + '%' : '—') + '</td>' +
        '<td><button class="mini" data-hold="' + n + '">' + (held === n ? 'restore' : 'hold out') + '</button></td>' +
        '</tr>';
    }).join('');

    host.innerHTML =
      '<h4 class="bh">1 · The Δα band — this is the result that holds</h4>' +
      '<canvas id="band-axis" style="width:100%;height:168px;display:block"></canvas>' +
      '<p class="cap">Each dot is one framework, placed by its spectrum width Δα. Six cluster ' +
        'between 0.835 and 0.941; two sit far below at 0.375 and 0.203. The gap between the ' +
        'groups is <b>0.46</b>, about <b>four times</b> the 0.105 noise floor measured on ' +
        'structures that are provably identical — so the split is a property of the frameworks, ' +
        'not of the estimator.</p>' +

      '<h4 class="bh">2 · The f(α) curves — and why the envelope is <i>not</i> a valid test</h4>' +
      '<canvas id="band-canvas" style="width:100%;height:400px;display:block"></canvas>' +
      '<p class="cap">Shaded = the envelope of the six band members. Dashed curves are the two ' +
        'outliers. Note their shape: they are <b>short arcs sitting inside the wide group\'s α ' +
        'range but far below it in f(α)</b>. That geometry is exactly why an envelope test fails ' +
        'here — it is dominated by where a curve sits in α, not by how wide it is.</p>' +

      '<div class="negbox">' +
        '<b>Measured negative result.</b> Press <i>hold out</i> on any row: the framework is ' +
        'removed from the band, the band is rebuilt from the rest, and its curve is scored ' +
        'against it. Hold out <b>ZIF-8</b> (a genuine member) and it scores <b>0.0%</b> inside. ' +
        'Hold out <b>UMCM-1</b> (a non-member) and it scores <b>44.7%</b> — far <b>higher</b>. ' +
        'The 2-D envelope therefore cannot be used to decide membership on this data, and we ' +
        'report that rather than quoting it as though it worked. The 1-D Δα test in the ' +
        '“held-out Δα” column does separate them correctly.' +
      '</div>' +

      '<table class="tbl band-tbl"><thead><tr>' +
        '<th>Framework</th><th>Metal</th><th>Binding</th><th class="r">Atoms</th>' +
        '<th class="r">Diam</th><th class="r">Δα</th><th>Group</th>' +
        '<th class="r">Held-out Δα test</th><th class="r">Envelope score</th><th></th>' +
      '</tr></thead><tbody>' + rows + '</tbody></table>' +
      (held ? '<p class="cap"><button class="mini" id="bd-reset">Clear hold-out (' + held + ')</button></p>' : '');

    drawWidthAxis(document.getElementById('band-axis'));
    drawCurves(document.getElementById('band-canvas'));

    if (!render._resize) {
      render._resize = true;
      window.addEventListener('resize', () => {
        drawWidthAxis(document.getElementById('band-axis'));
        drawCurves(document.getElementById('band-canvas'));
      });
    }
    host.querySelectorAll('[data-hold]').forEach(b => b.addEventListener('click', () => {
      const n = b.getAttribute('data-hold');
      held = (held === n) ? null : n;
      render();
    }));
    const rst = document.getElementById('bd-reset');
    if (rst) rst.addEventListener('click', () => { held = null; render(); });
  }

  function boot() {
    if (!document.getElementById('band-body') || !window.BAND_DATA) return;
    try { render(); } catch (e) { console.error('band section failed', e); }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

  window.MOFBand = { render, buildBand, scoreAgainst, widthTest, cleanCurve,
                     IN_BAND, FAMILY_74, NOISE_FLOOR };
})();
