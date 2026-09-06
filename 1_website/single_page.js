// single_page.js
// Behaviour that only exists because the whole project is now one page:
// the sticky section nav, and the source-code browser grid.

(function () {
  'use strict';

  // ---------------- sticky nav: highlight the section you are in ----------------
  function initNav() {
    const links = Array.prototype.slice.call(document.querySelectorAll('.sticky-nav a[href^="#"]'));
    const targets = links
      .map(a => ({ a, el: document.getElementById(a.getAttribute('href').slice(1)) }))
      .filter(t => t.el);
    if (!targets.length) return;

    links.forEach(a => a.addEventListener('click', e => {
      const el = document.getElementById(a.getAttribute('href').slice(1));
      if (!el) return;
      e.preventDefault();
      const top = el.getBoundingClientRect().top + window.pageYOffset - 62;
      window.scrollTo({ top, behavior: 'smooth' });
    }));

    let ticking = false;
    function mark() {
      ticking = false;
      const y = window.pageYOffset + 90;
      let cur = targets[0];
      targets.forEach(t => { if (t.el.offsetTop <= y) cur = t; });
      links.forEach(a => a.classList.remove('here'));
      if (cur) cur.a.classList.add('here');
    }
    window.addEventListener('scroll', () => {
      if (!ticking) { ticking = true; requestAnimationFrame(mark); }
    }, { passive: true });
    mark();
  }

  // ---------------- source-code browser ----------------
  const OURS = ['code_09_network_analysis.py', 'code_10_multifractal_spectrum.py',
                'code_11_nmfa_paper.py', 'band_page.js'];

  function initCodeGrid() {
    const grid = document.getElementById('code-grid');
    if (!grid || !window.CODE_SOURCES) return;
    const names = Object.keys(window.CODE_SOURCES);

    function render(filter) {
      const shown = names.filter(n => {
        const d = window.CODE_SOURCES[n];
        if (filter === 'py') return d.lang === 'python';
        if (filter === 'js') return d.lang === 'javascript';
        if (filter === 'ours') return OURS.indexOf(n) !== -1;
        return true;
      });
      grid.innerHTML = shown.map(n => {
        const d = window.CODE_SOURCES[n];
        const ours = OURS.indexOf(n) !== -1;
        const lines = d.src.split('\n').length;
        return '<div class="codecard" data-code="' + n + '">' +
          '<span class="ct' + (ours ? ' ours' : '') + '">' + (ours ? 'OUR WORK' : d.tag || 'JS') + '</span>' +
          '<div class="cf">' + n + '</div>' +
          '<div class="cd">' + (d.desc || '') + '</div>' +
          '<div class="cd" style="color:var(--muted2);margin-top:5px;">' + lines + ' lines · click to read</div>' +
          '</div>';
      }).join('');
    }

    const btns = { all: 'cs-all', py: 'cs-py', ours: 'cs-ours', js: 'cs-js' };
    Object.keys(btns).forEach(k => {
      const b = document.getElementById(btns[k]);
      if (!b) return;
      b.addEventListener('click', () => {
        Object.keys(btns).forEach(j => {
          const o = document.getElementById(btns[j]); if (o) o.classList.remove('active');
        });
        b.classList.add('active');
        render(k);
      });
    });
    render('all');
  }

  // ---------------- make every filename mentioned anywhere clickable ----------------
  // The implementation map and the old file lists use plain text / links; turning
  // them into code-viewer triggers means a filename is clickable wherever it appears.
  function wireFilenames() {
    if (!window.CODE_SOURCES) return;
    document.querySelectorAll('.filemap .f').forEach(td => {
      const name = td.textContent.trim();
      if (window.CODE_SOURCES[name]) td.setAttribute('data-code', name);
    });
    document.querySelectorAll('.file-group a, .codecard, td.f').forEach(el => {
      const t = (el.textContent || '').trim();
      const m = t.match(/([A-Za-z0-9_.-]+\.(?:py|js))/);
      if (m && window.CODE_SOURCES[m[1]] && !el.hasAttribute('data-code')) {
        el.setAttribute('data-code', m[1]);
      }
    });
    // code chips inside the walkthrough already carry the filename as text
    document.addEventListener('click', e => {
      const chip = e.target.closest('.code-chip');
      if (!chip) return;
      const m = (chip.textContent || '').match(/([A-Za-z0-9_.-]+\.(?:py|js))/);
      if (m && window.CODE_SOURCES[m[1]]) { e.preventDefault(); window.CodeViewer.open(m[1]); }
    });
    // and make them look clickable
    const style = document.createElement('style');
    style.textContent = '.code-chip{cursor:pointer;} .code-chip:hover{filter:brightness(1.25);}';
    document.head.appendChild(style);
  }

  function boot() { initNav(); initCodeGrid(); wireFilenames(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
