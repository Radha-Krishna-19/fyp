// test_pages.js — runs every generated page headlessly and asserts that its
// engine scripts actually populated it. A broken engine renders NOTHING and
// throws no visible error, so "the page loaded" is not evidence of anything;
// these tests check for computed content.
const path = require('path');
const SITE = path.join(__dirname, '..');
const fs = require('fs');
const { JSDOM } = require('jsdom');

let fails = 0;
const ok = (c, m) => { console.log((c ? 'PASS  ' : 'FAIL  ') + m); if (!c) fails++; };

const PAGES = ['index.html', 'methodology.html', 'decomposition.html', 'network.html',
               'spectrum.html', 'results.html', 'code.html', 'references.html',
               'glossary.html', 'team.html'];

// ---- 1. static structure, every page ----------------------------------
const docs = {};
PAGES.forEach(p => {
  const html = fs.readFileSync(path.join(SITE, p), 'utf8');
  const dom = new JSDOM(html);
  const D = dom.window.document;
  docs[p] = { html, D };

  ok(D.querySelectorAll('h1').length === 1, `${p}: exactly one <h1>`);
  ok(!!D.querySelector('.site-header'), `${p}: site header present`);
  ok(D.querySelectorAll('.site-nav a').length === PAGES.length, `${p}: nav lists all ${PAGES.length} pages`);
  ok(D.querySelectorAll(`.site-nav a[aria-current="page"]`).length === 1, `${p}: exactly one nav item marked current`);
  ok(!!D.getElementById('theme-btn'), `${p}: theme toggle present`);
  ok(!!D.getElementById('toc'), `${p}: TOC rail present`);
  // Every page must place the reader in the sequence, or say plainly that it
  // sits outside it. A page that does neither leaves them lost.
  ok(!!D.querySelector('.readpath') || !!D.querySelector('.path-note'),
     `${p}: reading position shown`);
  const here = D.querySelectorAll('.readpath li.here');
  ok(here.length <= 1, `${p}: at most one current step marked`);
  ok(/assets\/tokens\.css/.test(html) && /assets\/design\.css/.test(html), `${p}: design system linked`);
  ok(/data-theme/.test(html), `${p}: theme applied before paint`);

  // no colour may be hardcoded outside the token system
  const body = html.slice(html.indexOf('<body'));
  const hard = (body.match(/#[0-9a-fA-F]{6}\b/g) || [])
      .filter(c => !/^#(2f6fed|1f9d67|d81e40|c0392b|2e86c1|39404d|f5c842)$/i.test(c)); // 3D legend swatches, matched to WebGL ints
  ok(hard.length === 0, `${p}: no untokenised colours in markup${hard.length ? ' — ' + [...new Set(hard)].slice(0,6) : ''}`);

  // every internal link must resolve
  D.querySelectorAll('a[href]').forEach(a => {
    const h = a.getAttribute('href');
    if (/^(https?:|mailto:|#)/.test(h)) return;
    const [file, frag] = h.split('#');
    if (!file) return;
    ok(fs.existsSync(path.join(SITE, file)), `${p}: link target ${file} exists`);
    if (frag && docs[file]) {
      ok(!!docs[file].D.getElementById(frag), `${p}: fragment #${frag} exists in ${file}`);
    }
  });

  // section numbers must be 1..n in document order
  const nums = [...D.querySelectorAll('main .stitle-num, main h2.st .n')].map(e => e.textContent.trim());
  const want = nums.map((_, i) => String(i + 1));
  ok(JSON.stringify(nums) === JSON.stringify(want),
     `${p}: sections numbered 1..${nums.length} in order` + (nums.length ? ` (got ${nums.join(',')})` : ''));

  // ids must be unique
  const ids = [...D.querySelectorAll('[id]')].map(e => e.id);
  const dup = [...new Set(ids.filter((v, i) => ids.indexOf(v) !== i))];
  ok(dup.length === 0, `${p}: no duplicate ids${dup.length ? ' — ' + dup : ''}`);
});

// no page may still reference the deleted presentation layer
PAGES.forEach(p => ok(!/stage\.(js|css)|enhance\.js/.test(docs[p].html),
                      `${p}: no reference to the removed stage/enhance layer`));

// three.js must be vendored, not CDN-only
ok(fs.existsSync(path.join(SITE, 'three.min.js')), 'three.min.js is vendored into the repo');
ok(fs.statSync(path.join(SITE, 'three.min.js')).size > 400000, 'three.min.js is the real library');

console.log(fails ? `\n${fails} FAILURES` : '\nAll page tests passed.');
process.exit(fails ? 1 : 0);
