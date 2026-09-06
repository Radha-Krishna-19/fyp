/* =====================================================================
   glossary.js — defines every term at the point it first appears.

   THE PROBLEM
   A reader who does not know what a "labelled quotient graph" is cannot pick
   it up from a sentence that uses the phrase in passing. Putting the
   definitions in an appendix does not help either, because nobody breaks
   their reading to go and find one. The definition has to be where the word
   is, the first time the word is used.

   WHAT THIS DOES
   1. Scans the prose of each page for every term in glossary-data.js.
   2. Marks the FIRST occurrence on that page and attaches its definition,
      shown on hover or tap. Later occurrences are left alone — marking every
      instance would make the page unreadable.
   3. Builds the notation panel listing the symbols that page actually uses.
   4. Renders the full A-Z on glossary.html.

   WHY MARK ONLY THE FIRST
   Underlining "graph" forty times turns the page into a minefield of dotted
   lines. The first occurrence is where a reader who does not know the word
   will stop; after that they either know it or have decided to read on.

   SAFETY
   The scan walks text nodes only, and skips headings, code, tables, existing
   links and anything already marked. Rewriting innerHTML with a regex would
   corrupt attributes and break event handlers — this touches nothing but the
   text it is replacing.
   ===================================================================== */
(function () {
  'use strict';

  if (!window.GLOSSARY) return;

  /* Longest first: "eigenvector centrality" must be matched before
     "centrality", or the shorter term steals the match. */
  var ENTRIES = window.GLOSSARY.slice().sort(function (a, b) {
    return b.term.length - a.term.length;
  });

  var BY_KEY = {};
  ENTRIES.forEach(function (e) {
    BY_KEY[e.term.toLowerCase()] = e;
    (e.aka || []).forEach(function (a) { BY_KEY[a.toLowerCase()] = e; });
  });

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  /* -------------------------------------------------------------------
     Which elements must never be touched. Marking a term inside a heading
     wrecks the type; inside code it would be plain wrong; inside an existing
     link it would nest two interactive elements.
     ------------------------------------------------------------------- */
  var SKIP = /^(H1|H2|H3|H4|H5|H6|CODE|PRE|A|BUTTON|SCRIPT|STYLE|TEXTAREA|INPUT|SVG|CANVAS|DFN|TH|SELECT|OPTION)$/;

  function collectTextNodes(root) {
    var out = [];
    var walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        if (!n.nodeValue || n.nodeValue.trim().length < 3) return NodeFilter.FILTER_REJECT;
        for (var p = n.parentNode; p && p !== root; p = p.parentNode) {
          if (SKIP.test(p.nodeName)) return NodeFilter.FILTER_REJECT;
          if (p.classList && (p.classList.contains('no-gloss') ||
                              p.classList.contains('toc') ||
                              p.classList.contains('site-nav'))) {
            return NodeFilter.FILTER_REJECT;
          }
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var n;
    while ((n = walk.nextNode())) out.push(n);
    return out;
  }

  function makeDfn(entry, matchedText) {
    var d = document.createElement('dfn');
    d.className = 'gloss';
    d.setAttribute('tabindex', '0');
    d.setAttribute('role', 'button');
    d.setAttribute('aria-label', 'Definition of ' + entry.term);
    d.textContent = matchedText;

    var pop = document.createElement('span');
    pop.className = 'gloss-pop';
    pop.setAttribute('role', 'tooltip');
    pop.innerHTML =
      '<b>' + escapeHtml(entry.term) + '</b>' +
      '<span class="gloss-short">' + escapeHtml(entry.short) + '</span>' +
      (entry.long ? '<span class="gloss-long">' + entry.long + '</span>' : '') +
      '<a class="gloss-more" href="glossary.html#' + slug(entry.term) + '">Full entry &rarr;</a>';
    d.appendChild(pop);
    return d;
  }

  function slug(t) {
    return t.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  }

  /* -------------------------------------------------------------------
     Mark the first occurrence of each term in the page's main content.
     ------------------------------------------------------------------- */
  function annotate() {
    var main = document.querySelector('main');
    if (!main) return [];

    var done = {};          // term key -> already marked on this page
    var used = [];          // entries actually found, for the notation panel
    var nodes = collectTextNodes(main);

    ENTRIES.forEach(function (entry) {
      var forms = [entry.term].concat(entry.aka || []);
      // Word-boundary match, case-insensitive. \b fails on symbols such as
      // "Δα", so those fall back to a plain indexOf on the exact form.
      for (var f = 0; f < forms.length; f++) {
        if (done[entry.term]) break;
        var form = forms[f];
        var isWordy = /^[a-z0-9 ()'’.-]+$/i.test(form);
        var re = isWordy
          ? new RegExp('\\b(' + form.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')\\b', 'i')
          : null;

        for (var i = 0; i < nodes.length; i++) {
          var node = nodes[i];
          if (!node.parentNode) continue;         // already replaced
          var text = node.nodeValue, idx = -1, matched = form;

          if (re) {
            var m = re.exec(text);
            if (m) { idx = m.index; matched = m[1]; }
          } else {
            idx = text.indexOf(form);
          }
          if (idx < 0) continue;

          var before = document.createTextNode(text.slice(0, idx));
          var after = document.createTextNode(text.slice(idx + matched.length));
          var dfn = makeDfn(entry, matched);
          var parent = node.parentNode;
          parent.insertBefore(before, node);
          parent.insertBefore(dfn, node);
          parent.insertBefore(after, node);
          parent.removeChild(node);

          // The tail is still scannable for other terms.
          nodes[i] = after;
          done[entry.term] = true;
          used.push(entry);
          break;
        }
      }
    });
    return used;
  }

  /* -------------------------------------------------------------------
     Keep the popover on screen. A definition that opens off the right edge
     of the viewport is worse than no definition.
     ------------------------------------------------------------------- */
  function keepInView(dfn) {
    var pop = dfn.querySelector('.gloss-pop');
    if (!pop) return;
    pop.style.left = '';
    pop.style.right = '';
    var r = pop.getBoundingClientRect();
    var pad = 12;
    if (r.right > window.innerWidth - pad) {
      pop.style.left = 'auto';
      pop.style.right = '0';
    } else if (r.left < pad) {
      pop.style.left = '0';
      pop.style.right = 'auto';
    }
  }

  /* -------------------------------------------------------------------
     The notation panel: the symbols and terms THIS page uses, in reading
     order, so a reader can check one without leaving the page.
     ------------------------------------------------------------------- */
  function notation(used) {
    var host = document.getElementById('notation');
    if (!host || !used.length) { if (host) host.remove(); return; }

    var order = ['Chemistry', 'Graph theory', 'Fractals', 'Statistics'];
    var groups = {};
    used.forEach(function (e) { (groups[e.group] = groups[e.group] || []).push(e); });

    var html = '<div class="notation-head">Terms and symbols on this page' +
               '<span>hover any underlined term in the text for its definition</span></div>' +
               '<div class="notation-grid">';
    order.forEach(function (g) {
      if (!groups[g]) return;
      html += '<div class="notation-col"><h4>' + g + '</h4><dl>';
      groups[g].forEach(function (e) {
        html += '<dt>' + escapeHtml(e.term) + '</dt><dd>' + escapeHtml(e.short) + '</dd>';
      });
      html += '</dl></div>';
    });
    html += '</div>';
    host.innerHTML = html;
    host.classList.add('notation');
  }

  /* -------------------------------------------------------------------
     The full A-Z, rendered on glossary.html only.
     ------------------------------------------------------------------- */
  function fullGlossary() {
    var host = document.getElementById('glossary-full');
    if (!host) return;

    var order = ['Chemistry', 'Graph theory', 'Fractals', 'Statistics'];
    var groups = {};
    window.GLOSSARY.forEach(function (e) { (groups[e.group] = groups[e.group] || []).push(e); });

    var html = '';
    order.forEach(function (g) {
      if (!groups[g]) return;
      html += '<h2 class="section-title" id="' + slug(g) + '" data-toc="' + g + '">' +
              '<span class="stitle-num">0</span>' + g + '</h2>';
      groups[g].forEach(function (e) {
        var needs = (e.needs || []).filter(function (n) { return BY_KEY[n.toLowerCase()]; });
        html += '<div class="gloss-entry" id="' + slug(e.term) + '">' +
          '<h3>' + escapeHtml(e.term) +
            ((e.aka && e.aka.length) ? ' <span class="gloss-aka">also: ' +
              e.aka.map(escapeHtml).join(', ') + '</span>' : '') +
          '</h3>' +
          '<p class="gloss-short">' + escapeHtml(e.short) + '</p>' +
          (e.long ? '<p class="gloss-long">' + e.long + '</p>' : '') +
          (needs.length
            ? '<p class="gloss-needs">Understand first: ' + needs.map(function (n) {
                return '<a href="#' + slug(BY_KEY[n.toLowerCase()].term) + '">' +
                       escapeHtml(BY_KEY[n.toLowerCase()].term) + '</a>';
              }).join(' &middot; ') + '</p>'
            : '<p class="gloss-needs">No prerequisites &mdash; start here.</p>') +
          '</div>';
      });
    });
    host.innerHTML = html;
    // Number the generated headings the way build_site.py numbers the others.
    var n = 0;
    host.querySelectorAll('.stitle-num').forEach(function (s) { s.textContent = ++n; });
  }

  function boot() {
    try {
      var used = annotate();
      notation(used);
      fullGlossary();

      document.querySelectorAll('dfn.gloss').forEach(function (d) {
        d.addEventListener('mouseenter', function () { keepInView(d); });
        d.addEventListener('focus', function () { keepInView(d); });
        // Tap-to-open on touch, where there is no hover.
        d.addEventListener('click', function (ev) {
          if (ev.target.closest('.gloss-more')) return;   // let the link work
          ev.preventDefault();
          var open = d.classList.contains('open');
          document.querySelectorAll('dfn.gloss.open').forEach(function (o) {
            o.classList.remove('open');
          });
          if (!open) { d.classList.add('open'); keepInView(d); }
        });
      });
      document.addEventListener('click', function (ev) {
        if (!ev.target.closest('dfn.gloss')) {
          document.querySelectorAll('dfn.gloss.open').forEach(function (o) {
            o.classList.remove('open');
          });
        }
      });
      document.addEventListener('keydown', function (ev) {
        if (ev.key === 'Escape') {
          document.querySelectorAll('dfn.gloss.open').forEach(function (o) {
            o.classList.remove('open');
          });
        }
      });
    } catch (e) {
      if (window.console) console.warn('glossary:', e);
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

  window.MOFGlossary = { entries: ENTRIES, slug: slug };
})();
