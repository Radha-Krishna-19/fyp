/* =====================================================================
   palette.js — one palette for CSS, SVG and canvas.

   THE PROBLEM THIS SOLVES
   About half of this site is drawn, not laid out: the 3D viewer, the
   network graph, the Laplacian spectra, the multifractal curves, the band
   chart. Canvas drawing takes a colour STRING — `ctx.strokeStyle = '#555'`
   — and a string cannot follow a CSS variable. So when the site gained a
   dark theme, every chart kept its light-theme colours: dark grey axes and
   near-black labels on a near-black background, which is unreadable.

   HOW IT WORKS
   tokens.css exposes each token through a helper class (`.tok-node` sets
   `color: var(--node)`). This module renders a hidden probe element, reads
   the resolved `color` back with getComputedStyle, and caches the result.
   That gives the drawing code real rgb() strings for whichever theme is
   active, from the same single definition the CSS uses.

   USAGE
       PAL.node          -> "rgb(185, 28, 28)"   (light)  /  "rgb(248,113,113)" (dark)
       PAL.series(3)     -> a categorical colour, stable across themes
       PAL.alpha(c, .3)  -> the same colour at 30% opacity
       window.addEventListener('themechange', redrawEverything)

   The cache is rebuilt on 'themechange', which site.js fires when the
   toggle is used, so charts repaint in the new palette instead of being
   stuck in the palette they were first drawn in.
   ===================================================================== */
(function (global) {
  'use strict';

  var TOKENS = ['node', 'linker', 'text', 'text3', 'border', 'grid',
                'surface', 'good', 'warn', 'bad', 'accent2', 'brand'];

  var cache = {};

  function read() {
    cache = {};
    var probe = document.createElement('span');
    probe.style.cssText = 'position:absolute;left:-9999px;top:0;width:0;height:0';
    document.body.appendChild(probe);
    TOKENS.forEach(function (t) {
      probe.className = 'tok-' + t;
      // getComputedStyle resolves var() for us and always returns an
      // rgb()/rgba() string, which is exactly what canvas wants.
      cache[t] = getComputedStyle(probe).color || '#888';
    });
    probe.remove();

    // The categorical series used by every multi-line chart. Ordered so that
    // adjacent series stay distinguishable in the two most common forms of
    // colour-vision deficiency, and so that none of them is the axis grey.
    cache.seriesList = [cache.linker, cache.node, cache.good,
                        cache.accent2, cache.warn, cache.text3];
    return cache;
  }

  function ensure() {
    if (!cache.text) read();
    return cache;
  }

  var PAL = {
    /* Convert any resolved colour to the same hue at a given opacity.
       Used for fills under curves and for confidence bands. */
    alpha: function (c, a) {
      var m = /rgba?\(([^)]+)\)/.exec(c || '');
      if (!m) return c;
      var p = m[1].split(',').map(function (x) { return x.trim(); });
      return 'rgba(' + p[0] + ',' + p[1] + ',' + p[2] + ',' + a + ')';
    },
    series: function (i) {
      var c = ensure();
      return c.seriesList[((i % c.seriesList.length) + c.seriesList.length) % c.seriesList.length];
    },
    isDark: function () {
      return document.documentElement.getAttribute('data-theme') === 'dark';
    },
    refresh: read
  };

  // Expose each token as a live getter, so `PAL.node` is always the value for
  // the theme in force right now rather than the one at first paint.
  TOKENS.forEach(function (t) {
    Object.defineProperty(PAL, t, { get: function () { return ensure()[t]; } });
  });

  // Charts register here; every one of them repaints on a theme change.
  var redrawers = [];
  PAL.onTheme = function (fn) {
    redrawers.push(fn);
  };
  global.addEventListener('themechange', function () {
    read();
    redrawers.forEach(function (fn) {
      try { fn(); } catch (e) { /* one broken chart must not stop the rest */ }
    });
  });

  global.PAL = PAL;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', read);
  } else {
    read();
  }
})(window);
