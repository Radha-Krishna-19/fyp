// enhance.js
// Presentation layer: reading progress, scroll reveal, section anchors,
// back-to-top, and keyboard navigation.
//
// DESIGN CONSTRAINTS (all deliberate):
//   1. NO external dependencies. The site must work from a USB stick with no
//      internet, in front of a panel, with no CDN reachable.
//   2. Animation uses ONLY `transform` and `opacity`. Those two properties are
//      composited on the GPU and never trigger layout or paint, so scrolling
//      stays smooth even with several live 3D canvases on the page. Animating
//      anything else (height, top, margin) would cause reflow and stutter.
//   3. Every observer DISCONNECTS once it has done its job. An earlier version
//      of this site exhausted the browser's WebGL contexts by leaving work
//      running; nothing here is allowed to accumulate.
//   4. `prefers-reduced-motion` is honoured. If the viewer's OS asks for reduced
//      motion, everything appears instantly with no transition.

(function () {
  'use strict';

  // Respect the OS-level accessibility setting. Some people get motion sickness
  // from scroll animation, and a panel member's laptop may well have it on.
  const REDUCED = window.matchMedia &&
                  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ------------------------------------------------------------------
  // 1. READING PROGRESS BAR
  // A thin bar across the top showing how far through the document you are.
  // On a page this long (18 sections) it gives a sense of scale that a plain
  // scrollbar does not, because the sticky nav hides part of the scrollbar.
  // ------------------------------------------------------------------
  function progressBar() {
    const bar = document.createElement('div');
    bar.className = 'read-progress';
    bar.innerHTML = '<i></i>';
    document.body.appendChild(bar);
    const fill = bar.querySelector('i');

    let ticking = false;
    function update() {
      ticking = false;
      // scrollHeight - innerHeight is the total scrollable distance. Guard
      // against division by zero on a page shorter than the viewport.
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const pct = max > 0 ? (window.pageYOffset / max) * 100 : 0;
      // scaleX rather than width: transforms are GPU-composited, width is not.
      fill.style.transform = 'scaleX(' + (pct / 100) + ')';
    }
    // rAF-throttled: the scroll event can fire far more often than the display
    // refreshes, and doing work per event rather than per frame wastes time.
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });   // passive: we never preventDefault, so the browser
                             // can scroll without waiting for this handler
    update();
  }

  // ------------------------------------------------------------------
  // 2. SCROLL REVEAL
  // Sections fade and rise slightly as they enter the viewport. Purely
  // presentational, but it gives the page a sense of pace and stops an
  // 18-section document feeling like an undifferentiated wall.
  // ------------------------------------------------------------------
  function scrollReveal() {
    if (REDUCED || !('IntersectionObserver' in window)) return;

    // Reveal at the level of blocks, not whole sections: a section can be taller
    // than the viewport, and animating it as one unit would mean the bottom half
    // appears already-revealed.
    const targets = document.querySelectorAll(
      '.panel, figure.fig, .callout, .negbox, table.data-table, table.tbl'
    );

    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add('revealed');
        // Stop observing once revealed. Without this the observer keeps firing
        // for the life of the page, for every element, forever.
        io.unobserve(e.target);
      });
    }, {
      // Trigger slightly BEFORE the element reaches the viewport edge, so the
      // animation is finishing as it becomes properly visible rather than
      // starting then.
      rootMargin: '0px 0px -60px 0px',
      threshold: 0.05
    });

    targets.forEach(function (t) {
      t.classList.add('reveal');
      io.observe(t);
    });
  }

  // ------------------------------------------------------------------
  // 3. SECTION ANCHOR LINKS
  // A ¶ appears on hover beside each heading; clicking copies a direct link.
  // Useful when someone asks "where did you show that?" and you want to send
  // them straight to it.
  // ------------------------------------------------------------------
  function anchorLinks() {
    document.querySelectorAll('h2[id], h2.st[id], h2.section-title[id]').forEach(function (h) {
      if (!h.id || h.querySelector('.anchor')) return;
      const a = document.createElement('a');
      a.className = 'anchor';
      a.href = '#' + h.id;
      a.title = 'Copy link to this section';
      a.textContent = '¶';
      a.addEventListener('click', function (ev) {
        ev.preventDefault();
        const url = location.href.split('#')[0] + '#' + h.id;
        // Update the address bar without adding a history entry, so the back
        // button still does what the reader expects.
        history.replaceState(null, '', '#' + h.id);
        h.scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth', block: 'start' });
        // Clipboard is best-effort: it fails on file:// in some browsers, and a
        // failed copy must not break the scroll that already happened.
        if (navigator.clipboard) {
          navigator.clipboard.writeText(url).then(function () {
            a.classList.add('copied');
            setTimeout(function () { a.classList.remove('copied'); }, 1200);
          }, function () { /* clipboard blocked — the scroll still worked */ });
        }
      });
      h.appendChild(a);
    });
  }

  // ------------------------------------------------------------------
  // 4. BACK TO TOP
  // Appears once you are well down the page. On a document this long, scrolling
  // back by hand to reach the navigation is genuinely annoying.
  // ------------------------------------------------------------------
  function backToTop() {
    const btn = document.createElement('button');
    btn.className = 'to-top';
    btn.setAttribute('aria-label', 'Back to top');
    btn.innerHTML = '↑';
    btn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: REDUCED ? 'auto' : 'smooth' });
    });
    document.body.appendChild(btn);

    let ticking = false;
    window.addEventListener('scroll', function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        ticking = false;
        // 600px ≈ most of one screen. Showing it sooner would put a floating
        // button over content the reader has barely started.
        btn.classList.toggle('show', window.pageYOffset > 600);
      });
    }, { passive: true });
  }

  // ------------------------------------------------------------------
  // 5. KEYBOARD NAVIGATION
  // J / K (or the arrow keys with Alt) jump between sections. Handy when
  // presenting: you can move section to section without hunting with a mouse.
  // ------------------------------------------------------------------
  function keyboardNav() {
    const heads = Array.prototype.slice.call(
      document.querySelectorAll('h2.st[id], h2.section-title[id]')
    );
    if (!heads.length) return;

    document.addEventListener('keydown', function (e) {
      // Never hijack keys while the reader is typing in a field, and leave
      // browser shortcuts (Ctrl/Cmd combinations) alone.
      const tag = (e.target.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'textarea' || e.metaKey || e.ctrlKey) return;

      const k = e.key.toLowerCase();
      const next = (k === 'j') || (e.altKey && e.key === 'ArrowDown');
      const prev = (k === 'k') || (e.altKey && e.key === 'ArrowUp');
      if (!next && !prev) return;
      e.preventDefault();

      // Which section are we currently in? The one whose top is nearest above
      // the reading line (100px down, roughly under the sticky nav).
      const y = window.pageYOffset + 100;
      let idx = 0;
      heads.forEach(function (h, i) { if (h.offsetTop <= y + 5) idx = i; });

      const target = heads[Math.max(0, Math.min(heads.length - 1, idx + (next ? 1 : -1)))];
      window.scrollTo({
        top: target.offsetTop - 62,          // 62px clears the sticky nav
        behavior: REDUCED ? 'auto' : 'smooth'
      });
    });
  }

  // ------------------------------------------------------------------
  function boot() {
    try { progressBar(); } catch (e) { /* presentation only — never break the page */ }
    try { scrollReveal(); } catch (e) {}
    try { anchorLinks(); } catch (e) {}
    try { backToTop(); } catch (e) {}
    try { keyboardNav(); } catch (e) {}
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  window.MOFEnhance = { reduced: REDUCED };
})();
