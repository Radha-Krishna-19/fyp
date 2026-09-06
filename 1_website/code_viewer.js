// code_viewer.js
// In-page source browser. Clicking any filename anywhere on the site opens the
// real source with line numbers, without leaving the page and without needing a
// web server — the sources are embedded by code_sources.js.

(function () {
  'use strict';

  function esc(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // Deliberately light-touch highlighting: comments, strings, keywords, numbers.
  // Anything cleverer risks mangling the code, which would defeat the purpose.
  function highlight(src, lang) {
    const kw = lang === 'python'
      ? ['def','class','return','if','elif','else','for','while','in','not','and','or','import','from','as','with','try','except','raise','lambda','None','True','False','yield','assert','global','pass','continue','break']
      : ['function','return','if','else','for','while','const','let','var','new','this','typeof','instanceof','try','catch','throw','class','extends','null','undefined','true','false','break','continue','of','in','delete','void'];
    const kwRe = new RegExp('\\b(' + kw.join('|') + ')\\b', 'g');
    const out = [];
    const lines = src.split('\n');
    for (const raw of lines) {
      let line = esc(raw);
      const isComment = lang === 'python'
        ? /^\s*#/.test(raw)
        : /^\s*(\/\/|\*|\/\*)/.test(raw);
      if (isComment) { out.push('<span class="cv-cm">' + line + '</span>'); continue; }
      line = line
        .replace(/(&quot;|&#39;|'|")((?:(?!\1).)*)\1/g, '<span class="cv-st">$&</span>')
        .replace(kwRe, '<span class="cv-kw">$1</span>')
        .replace(/\b(\d+\.?\d*)\b/g, '<span class="cv-nu">$1</span>');
      if (lang === 'python') line = line.replace(/(#.*)$/, '<span class="cv-cm">$1</span>');
      else line = line.replace(/(\/\/.*)$/, '<span class="cv-cm">$1</span>');
      out.push(line);
    }
    return out;
  }

  let overlay = null;

  function build() {
    if (overlay) return overlay;
    overlay = document.createElement('div');
    overlay.className = 'cv-overlay';
    overlay.innerHTML =
      '<div class="cv-box">' +
        '<div class="cv-head">' +
          '<span class="cv-name" id="cv-name"></span>' +
          '<span class="cv-meta" id="cv-meta"></span>' +
          '<span style="flex:1"></span>' +
          '<button class="cv-btn" id="cv-copy">Copy</button>' +
          '<button class="cv-btn" id="cv-close">Close ✕</button>' +
        '</div>' +
        '<div class="cv-body"><table class="cv-tbl"><tbody id="cv-lines"></tbody></table></div>' +
      '</div>';
    document.body.appendChild(overlay);
    overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
    overlay.querySelector('#cv-close').addEventListener('click', close);
    overlay.querySelector('#cv-copy').addEventListener('click', function () {
      const f = overlay.dataset.file;
      const src = (window.CODE_SOURCES || {})[f];
      if (!src) return;
      const btn = this;
      const done = () => { btn.textContent = 'Copied ✓'; setTimeout(() => { btn.textContent = 'Copy'; }, 1400); };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(src.src).then(done, () => { btn.textContent = 'Copy failed'; });
      } else {
        const ta = document.createElement('textarea');
        ta.value = src.src; document.body.appendChild(ta); ta.select();
        try { document.execCommand('copy'); done(); } catch (e) { btn.textContent = 'Copy failed'; }
        document.body.removeChild(ta);
      }
    });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
    return overlay;
  }

  function close() { if (overlay) overlay.classList.remove('open'); }

  function open(file) {
    const data = (window.CODE_SOURCES || {})[file];
    const o = build();
    o.dataset.file = file;
    if (!data) {
      o.querySelector('#cv-name').textContent = file;
      o.querySelector('#cv-meta').textContent = '';
      o.querySelector('#cv-lines').innerHTML =
        '<tr><td class="cv-ln"></td><td class="cv-src">Source not embedded for this file. ' +
        'It is on disk in the project folder.</td></tr>';
      o.classList.add('open');
      return;
    }
    o.querySelector('#cv-name').textContent = file;
    o.querySelector('#cv-meta').textContent =
      data.desc + '  ·  ' + data.src.split('\n').length + ' lines';
    const lines = highlight(data.src, data.lang);
    o.querySelector('#cv-lines').innerHTML = lines.map((l, i) =>
      '<tr><td class="cv-ln">' + (i + 1) + '</td><td class="cv-src">' + (l || '&nbsp;') + '</td></tr>'
    ).join('');
    o.querySelector('.cv-body').scrollTop = 0;
    o.classList.add('open');
  }

  // Any element carrying data-code="filename" opens the viewer. Also upgrades
  // plain links that point at a source file, so existing markup keeps working.
  function wire() {
    document.addEventListener('click', e => {
      const el = e.target.closest('[data-code]');
      if (el) { e.preventDefault(); open(el.getAttribute('data-code')); return; }
      const a = e.target.closest('a[href]');
      if (!a) return;
      const href = a.getAttribute('href') || '';
      const m = href.match(/([A-Za-z0-9_.-]+\.(?:py|js))$/);
      if (m && window.CODE_SOURCES && window.CODE_SOURCES[m[1]]) {
        e.preventDefault();
        open(m[1]);
      }
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', wire);
  else wire();

  window.CodeViewer = { open, close };
})();
