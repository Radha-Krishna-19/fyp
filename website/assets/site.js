/* =====================================================================
   site.js — site chrome. Deliberately small.

   WHAT IT DOES
     1. theme()     dark / light, remembered, applied before first paint
     2. toc()       builds the in-page table of contents and tracks position
     3. progress()  the 2px reading indicator under the header
     4. reveal()    one fade-and-rise the first time a block is seen
     5. anchors()   copyable deep links on every heading
     6. tables()    wraps wide tables so they scroll instead of overflowing

   WHAT IT DELIBERATELY DOES NOT DO
   No parallax, no cursor effects, no animated backgrounds, no count-up
   numbers, no page transitions. An earlier version had all of those. They
   made a document that a professor has to grade look like a product launch,
   and they cost frames on a page that already runs several WebGL canvases.
   The only continuously-updating element left is the reading progress bar,
   which earns its keep by being genuinely useful on a long page.

   PERFORMANCE
   Scroll work is throttled through requestAnimationFrame, never run directly
   in the scroll handler. Every IntersectionObserver stops observing an
   element once it has fired, so observers do not accumulate.
   ===================================================================== */
(function () {
  'use strict';

  var REDUCED = window.matchMedia &&
                window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* -------------------------------------------------------------------
     rAF throttle. A scroll event can fire well over 100 times a second;
     the screen only redraws 60. Coalescing to one callback per frame is
     the difference between smooth and janky on a long document.
     ------------------------------------------------------------------- */
  function onScroll(fn) {
    var queued = false;
    function handler() {
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () { queued = false; fn(); });
    }
    window.addEventListener('scroll', handler, { passive: true });
    window.addEventListener('resize', handler, { passive: true });
    fn();
  }

  /* ===================================================================
     1 · THEME
     The <head> of every page runs a two-line inline script that applies
     the stored theme BEFORE the first paint — otherwise a dark-mode user
     sees a white flash on every navigation. This function only wires up
     the toggle and keeps the button label honest.
     =================================================================== */
  function theme() {
    var btn = document.getElementById('theme-btn');
    if (!btn) return;

    var SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5 5l1.4 1.4M17.6 17.6L19 19M19 5l-1.4 1.4M6.4 17.6L5 19"/></svg>';
    var MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 14.2A8.2 8.2 0 1 1 9.8 4a6.6 6.6 0 0 0 10.2 10.2z"/></svg>';

    function paint() {
      var dark = document.documentElement.getAttribute('data-theme') === 'dark';
      btn.innerHTML = dark ? SUN : MOON;
      btn.setAttribute('title', dark ? 'Switch to light theme' : 'Switch to dark theme');
      btn.setAttribute('aria-label', btn.getAttribute('title'));
      // Canvases are painted from JS and cannot react to a CSS variable, so
      // they are told to repaint themselves with the new palette.
      window.dispatchEvent(new CustomEvent('themechange', { detail: { dark: dark } }));
    }
    btn.addEventListener('click', function () {
      var dark = document.documentElement.getAttribute('data-theme') === 'dark';
      var next = dark ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('mof-theme', next); } catch (e) { /* private mode */ }
      paint();
    });
    paint();
  }

  /* ===================================================================
     2 · TABLE OF CONTENTS
     Built from the page's own <h2 id> elements, so it can never drift out
     of sync with the content the way a hand-written list does. An earlier
     hand-maintained navigation ended up reading "1 3 2 3 4 5 6 10 11".
     =================================================================== */
  function toc() {
    var rail = document.getElementById('toc');
    if (!rail) return;
    var heads = [].slice.call(document.querySelectorAll('main h2[id]'));
    if (heads.length < 2) { rail.remove(); return; }

    var html = '<div class="toc-title">On this page</div>';
    heads.forEach(function (h) {
      // Strip the section number span so the rail reads as plain titles.
      var label = (h.getAttribute('data-toc') || h.textContent || '')
                    .replace(/^\s*\d+\s*/, '').trim();
      html += '<a href="#' + h.id + '">' + label + '</a>';
    });
    rail.innerHTML = html;

    var links = [].slice.call(rail.querySelectorAll('a'));
    onScroll(function () {
      // The "current" section is the last heading whose top has passed the
      // reading line (a third of the way down the viewport).
      var line = window.innerHeight * 0.33, current = 0;
      heads.forEach(function (h, i) {
        if (h.getBoundingClientRect().top <= line) current = i;
      });
      links.forEach(function (a, i) { a.classList.toggle('active', i === current); });
    });
  }

  /* =================================================================== */
  function progress() {
    var bar = document.createElement('div');
    bar.className = 'read-progress';
    bar.innerHTML = '<i></i>';
    bar.setAttribute('aria-hidden', 'true');
    document.body.appendChild(bar);
    var fill = bar.firstChild;
    onScroll(function () {
      var max = document.documentElement.scrollHeight - window.innerHeight;
      fill.style.transform = 'scaleX(' + (max > 0 ? window.pageYOffset / max : 0) + ')';
    });
  }

  /* ===================================================================
     4 · REVEAL
     8px and a fade, once. Staggered by at most three steps so a row of
     cards arrives as a group rather than a queue.
     =================================================================== */
  function reveal() {
    if (REDUCED || !('IntersectionObserver' in window)) return;
    // Headings are included so their rule can draw itself, and .keynums so the
    // strip can wipe in cell by cell. Individual .keynum children are NOT
    // observed: staggering them is the parent's job in CSS, and observing
    // twenty small elements costs more than observing four containers.
    var targets = document.querySelectorAll(
      'main h2.section-title, main h2.st, ' +
      'main .panel, main figure.fig, main .callout, main .negbox, ' +
      'main .table-wrap, main .keynums, main .part, main .lim-card, main .demo-card'
    );
    if (!targets.length) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e, i) {
        if (!e.isIntersecting) return;
        // Stagger within the batch, capped at four steps. A row of six cards
        // arriving one-by-one over 600ms reads as slow; three or four steps
        // reads as a group settling.
        if (!e.target.classList.contains('keynums')) {
          e.target.style.transitionDelay = Math.min(i, 3) * 70 + 'ms';
        }
        e.target.classList.add('revealed');
        io.unobserve(e.target);          // fire once, then stop watching
      });
    }, { rootMargin: '0px 0px -60px 0px', threshold: 0.03 });
    [].forEach.call(targets, function (t) { t.classList.add('reveal'); io.observe(t); });
  }

  /* =================================================================== */
  function anchors() {
    document.querySelectorAll('main h2[id], main h3[id]').forEach(function (h) {
      if (h.querySelector('.anchor')) return;
      var a = document.createElement('a');
      a.className = 'anchor';
      a.href = '#' + h.id;
      a.textContent = '#';
      a.title = 'Copy a link to this section';
      a.addEventListener('click', function (ev) {
        ev.preventDefault();
        history.replaceState(null, '', '#' + h.id);
        h.scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth', block: 'start' });
        if (navigator.clipboard) {
          navigator.clipboard
            .writeText(location.href.split('#')[0] + '#' + h.id)
            .then(function () {
              a.classList.add('copied');
              setTimeout(function () { a.classList.remove('copied'); }, 1200);
            }, function () { /* clipboard denied — the link still works */ });
        }
      });
      h.appendChild(a);
    });
  }

  /* ===================================================================
     6 · TABLES
     Several tables here are genuinely wide (the 77-framework listing has
     eight columns). Unwrapped they force the whole page to scroll
     sideways, which breaks the layout on a laptop. Wrapping each one in
     its own scroll container confines the overflow to the table.
     =================================================================== */
  function tables() {
    document.querySelectorAll('main table').forEach(function (t) {
      if (t.closest('.table-wrap')) return;
      var w = document.createElement('div');
      w.className = 'table-wrap';
      t.parentNode.insertBefore(w, t);
      w.appendChild(t);
    });
  }

  function boot() {
    [theme, tables, toc, progress, reveal, anchors].forEach(function (fn) {
      try { fn(); } catch (e) {
        // Chrome is presentation. A failure here must never take down the
        // computational parts of the page below it.
        if (window.console) console.warn('site.js:', fn.name, e);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
