/* Click a face of a 3D crystal drawing to see what it is. Shared by the Morphology, Cell Deform
   and CIF to Shape pages. No dependencies.

   FaceCard.show(host, html)  shows a small card in the corner of host (a positioned container);
   FaceCard.wire(svg, host, describe)  makes every <polygon data-face="i"> in svg clickable:
   a press and release without dragging calls describe(i) and shows the HTML it returns. */
(function (global) {
  'use strict';
  function card(host) {
    var c = host.querySelector(':scope > .face-card');
    if (!c) {
      if (global.getComputedStyle && getComputedStyle(host).position === 'static') host.style.position = 'relative';
      c = document.createElement('div');
      c.className = 'face-card'; c.setAttribute('role', 'dialog'); c.setAttribute('aria-label', 'The selected face');
      host.appendChild(c);
    }
    return c;
  }
  function show(host, html) {
    var c = card(host);
    c.innerHTML = '<button type="button" class="close" aria-label="Close">×</button>' + html;
    c.style.display = 'block';
    c.querySelector('.close').addEventListener('click', function (e) { e.stopPropagation(); c.style.display = 'none'; });
  }
  function hide(host) { var c = host.querySelector(':scope > .face-card'); if (c) c.style.display = 'none'; }
  function wire(svg, host, describe) {
    var start = null;
    svg.addEventListener('pointerdown', function (e) { start = [e.clientX, e.clientY]; });
    svg.addEventListener('pointerup', function (e) {
      if (!start) return;
      var moved = Math.abs(e.clientX - start[0]) + Math.abs(e.clientY - start[1]);
      start = null;
      if (moved > 5) return;
      var t = e.target, i = t && t.getAttribute ? t.getAttribute('data-face') : null;
      if (i === null || i === undefined) {
        // the pointer may be captured by the svg: find the face under the pointer instead
        var el = document.elementFromPoint ? document.elementFromPoint(e.clientX, e.clientY) : null;
        i = el && el.getAttribute ? el.getAttribute('data-face') : null;
      }
      if (i === null || i === undefined) { hide(host); return; }
      var html = describe(+i);
      if (html) show(host, html);
    });
    svg.querySelectorAll('polygon[data-face]').forEach(function (p) { p.style.cursor = 'pointer'; });
  }
  // a short description of a face: its family, its normal, its area and the family's share of the surface
  function area(poly) {                       // polygon area in 3D (Newell's method)
    var n = [0, 0, 0];
    for (var i = 0; i < poly.length; i++) {
      var a = poly[i], b = poly[(i + 1) % poly.length];
      n[0] += (a[1] - b[1]) * (a[2] + b[2]); n[1] += (a[2] - b[2]) * (a[0] + b[0]); n[2] += (a[0] - b[0]) * (a[1] + b[1]);
    }
    return Math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]) / 2;
  }
  function describe(o) {
    // o: { family (html), index (html, optional), normal [x,y,z], faceShare, familyShare, count, extra: [[label, value]] }
    var rows = [['This face', (100 * o.faceShare).toFixed(1) + ' % of the surface'],
                ['Its family', (100 * o.familyShare).toFixed(1) + ' % in ' + o.count + ' face' + (o.count === 1 ? '' : 's')],
                ['Outward normal', o.normal.map(function (x) { return (Math.abs(x) < 5e-4 ? 0 : x).toFixed(3); }).join(', ')]].concat(o.extra || []);
    return '<div class="head"><b>Face ' + (o.index || '') + '</b> <span class="sub">of family ' + o.family + '</span></div>' +
      '<table>' + rows.map(function (r) { return '<tr><td>' + r[0] + '</td><td>' + r[1] + '</td></tr>'; }).join('') + '</table>' +
      (o.note ? '<p class="sub">' + o.note + '</p>' : '');
  }
  // Drag-to-turn for a picture that is redrawn on every move. The handlers sit on the host element,
  // which persists; a handler on the picture itself would be lost with the first redraw, and the drag
  // would stop after one frame. onTurn(dx, dy) receives the pointer movement in pixels.
  function drag(host, onTurn) {
    if (host._dragWired) { host._onTurn = onTurn; return; }
    host._dragWired = true; host._onTurn = onTurn;
    host.style.touchAction = 'none';
    var last = null;
    host.addEventListener('pointerdown', function (e) {
      if (!e.target.closest || !e.target.closest('svg')) return;
      last = [e.clientX, e.clientY];
      try { host.setPointerCapture(e.pointerId); } catch (x) { /* not supported */ }
    });
    host.addEventListener('pointermove', function (e) {
      if (!last) return;
      var dx = e.clientX - last[0], dy = e.clientY - last[1];
      if (!dx && !dy) return;
      last = [e.clientX, e.clientY];
      host._onTurn(dx, dy);
    });
    function end() { last = null; }
    host.addEventListener('pointerup', end);
    host.addEventListener('pointercancel', end);
    host.addEventListener('lostpointercapture', end);
  }
  // A click (press and release without moving) on a face of the current picture opens its card.
  // Wired once on the host, so it keeps working after the picture is redrawn.
  function wireHost(host, describe) {
    host._describe = describe;
    if (host._clickWired) return;
    host._clickWired = true;
    var start = null;
    host.addEventListener('pointerdown', function (e) { start = [e.clientX, e.clientY]; });
    host.addEventListener('pointerup', function (e) {
      if (!start) return;
      var moved = Math.abs(e.clientX - start[0]) + Math.abs(e.clientY - start[1]);
      start = null;
      if (moved > 5) return;
      if (e.target.closest && e.target.closest('.face-card')) return;
      var el = document.elementFromPoint ? document.elementFromPoint(e.clientX, e.clientY) : e.target;
      if (!el || !el.getAttribute) el = e.target;
      var i = el && el.getAttribute ? el.getAttribute('data-face') : null;
      if (i === null || i === undefined) { hide(host); return; }
      var html = host._describe(+i);
      if (html) show(host, html);
    });
  }
  global.FaceCard = { show: show, hide: hide, wire: wire, wireHost: wireHost, drag: drag, area: area, describe: describe };
})(typeof window !== 'undefined' ? window : this);
