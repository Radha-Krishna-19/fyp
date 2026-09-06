// test_glossary.js — the glossary must actually define things, in the right
// order, without corrupting the pages it annotates.
const path = require('path');
const SITE = path.join(__dirname, '..');
const fs = require('fs');
const { JSDOM } = require('jsdom');

let fails = 0;
const ok = (c, m) => { console.log((c ? 'PASS  ' : 'FAIL  ') + m); if (!c) fails++; };

// ---- 1. the data itself -------------------------------------------------
const sandbox = { window: {} };
new Function('window', fs.readFileSync(path.join(SITE, 'assets/glossary-data.js'), 'utf8'))(sandbox.window);
const G = sandbox.window.GLOSSARY;

ok(Array.isArray(G) && G.length >= 40, `glossary has ${G.length} entries`);

const byKey = {};
G.forEach(e => { byKey[e.term.toLowerCase()] = e; (e.aka || []).forEach(a => byKey[a.toLowerCase()] = e); });

G.forEach(e => {
  ok(!!e.short && e.short.length > 20, `"${e.term}" has a short definition`);
  ok(!!e.group, `"${e.term}" is grouped`);
});

// No definition may be circular: a term must not be defined using itself.
G.forEach(e => {
  const body = (e.short + ' ' + (e.long || '')).toLowerCase();
  const bare = e.term.toLowerCase();
  // Allow the term inside its own long-form prose (natural), but the SHORT
  // definition is the one a reader sees first and must stand alone.
  const circular = new RegExp('^[^.]*\\b' + bare.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b')
                     .test(e.short.toLowerCase());
  ok(!circular, `"${e.term}" short definition is not circular`);
});

// Every prerequisite must exist, and must not create a cycle.
G.forEach(e => (e.needs || []).forEach(n =>
  ok(!!byKey[n.toLowerCase()], `"${e.term}" prerequisite "${n}" is itself defined`)));

function reachable(term, seen) {
  seen = seen || new Set();
  if (seen.has(term)) return true;              // cycle
  seen.add(term);
  const e = byKey[term.toLowerCase()];
  if (!e) return false;
  return (e.needs || []).some(n => reachable(n, new Set(seen)));
}
G.forEach(e => ok(!(e.needs || []).some(n => reachable(n, new Set([e.term]))),
                  `"${e.term}" prerequisites contain no cycle`));

// ---- 2. annotation on a real page ---------------------------------------
function annotated(page) {
  const html = fs.readFileSync(path.join(SITE, page), 'utf8');
  const dom = new JSDOM(html, { runScripts: 'outside-only', pretendToBeVisual: true });
  const W = dom.window;
  W.IntersectionObserver = class { observe(){} unobserve(){} disconnect(){} };
  W.requestAnimationFrame = fn => setTimeout(fn, 0);
  ['assets/glossary-data.js', 'assets/glossary.js'].forEach(f =>
    W.eval(fs.readFileSync(path.join(SITE, f), 'utf8')));
  W.document.dispatchEvent(new W.Event('DOMContentLoaded', { bubbles: true }));
  return W.document;
}

const D = annotated('network.html');
const marks = [...D.querySelectorAll('dfn.gloss')];
ok(marks.length >= 8, `network.html: ${marks.length} terms marked in the prose`);

// each term marked at most ONCE per page
const terms = marks.map(m => m.getAttribute('aria-label'));
ok(new Set(terms).size === terms.length, 'each term is marked only once per page');

// never inside a heading, code block, link or table header
['h1','h2','h3','h4','code','pre','a','th'].forEach(sel =>
  ok(D.querySelectorAll(`${sel} dfn.gloss`).length === 0,
     `no definition marked inside <${sel}>`));

// every mark carries a usable popover
ok(marks.every(m => m.querySelector('.gloss-pop b') && m.querySelector('.gloss-short')),
   'every marked term carries its definition');
ok(marks.every(m => m.textContent.trim().length > 0), 'no marked term lost its text');

// the notation panel lists what the page uses
const notation = D.getElementById('notation');
ok(!!notation && /notation-grid/.test(notation.innerHTML), 'network.html: notation panel built');
ok(notation.querySelectorAll('dt').length >= 8, 'notation panel lists the page terms');

// ---- 3. the full A-Z ------------------------------------------------------
const GD = annotated('glossary.html');
const entries = GD.querySelectorAll('.gloss-entry');
ok(entries.length === G.length, `glossary.html renders all ${G.length} entries (got ${entries.length})`);
ok(GD.querySelectorAll('.gloss-entry h3').length === G.length, 'every entry has a heading');
ok(/No prerequisites/.test(GD.body.innerHTML), 'entry-level prerequisites are shown');
const nums = [...GD.querySelectorAll('#glossary-full .stitle-num')].map(e => e.textContent);
ok(nums.join(',') === nums.map((_, i) => i + 1).join(','), 'glossary sections numbered in order');

// ---- 4. glossary is loaded everywhere ------------------------------------
['index.html','methodology.html','decomposition.html','network.html','spectrum.html',
 'results.html','code.html','references.html','glossary.html','team.html'].forEach(p => {
  const h = fs.readFileSync(path.join(SITE, p), 'utf8');
  ok(/assets\/glossary\.js/.test(h) && /assets\/glossary-data\.js/.test(h),
     `${p}: glossary loaded`);
});

console.log(fails ? `\n${fails} FAILURES` : '\nAll glossary tests passed.');
process.exit(fails ? 1 : 0);
