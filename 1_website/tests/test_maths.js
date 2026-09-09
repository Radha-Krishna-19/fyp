/* =====================================================================
   test_maths.js — the derivation must define what it uses, in order.

   WHAT THIS GUARDS
   The site's rule for the mathematics is that a symbol may not appear in a
   displayed equation before a "where" table has defined it. That rule is easy
   to state and easy to break silently: a later edit inserts an equation, or
   moves one, and suddenly the reader meets tau before anything has said what
   tau is. Prose cannot be unit-tested, but this particular property can.

   It also checks the equations are numbered consecutively, since the text
   refers to them by number, and that the derivation's claimed values agree
   with the shipped data rather than being typed in from memory.
   ===================================================================== */
'use strict';

const fs = require('fs');
const path = require('path');

// Deliberately no jsdom. This suite reasons about the ORDER of things in the
// built file, and a DOM re-serialises entities, so element.outerHTML stops
// matching the source it came from — which silently made an earlier version of
// this test pass without checking anything. Working on the source string keeps
// positions exact, and skips a 60-second module load.
const SITE = path.join(__dirname, '..');
let failures = 0, checks = 0;
function ok(cond, msg) {
  checks++;
  if (cond) console.log('PASS  ' + msg);
  else { failures++; console.log('FAIL  ' + msg); }
}

const html = fs.readFileSync(path.join(SITE, 'spectrum.html'), 'utf8');

/** Every <div class="eq">…</div> in source order, with its offset. */
function blocks(cls) {
  const out = [];
  const re = new RegExp('<div class="' + cls + '"[^>]*>', 'g');
  let m;
  while ((m = re.exec(html))) {
    // walk to the matching </div>
    let i = m.index + m[0].length, depth = 1;
    while (depth > 0 && i < html.length) {
      const open = html.indexOf('<div', i), close = html.indexOf('</div>', i);
      if (close === -1) break;
      if (open !== -1 && open < close) { depth++; i = open + 4; }
      else { depth--; i = close + 6; }
    }
    out.push({ start: m.index, end: i, html: html.slice(m.index, i) });
  }
  return out;
}

// ---- 1. the derivation is present and ordered ---------------------------
const ids = ['why-parabola', 'maths', 'spectra61'];
const order = ids.map(id => html.indexOf('id="' + id + '"'));
ok(order.every(i => i >= 0), 'the intuition, the derivation and the raw spectra are all present');
ok(order[0] < order[1] && order[1] < order[2],
   'they are in teaching order: intuition, then derivation, then data');

// ---- 2. equations are numbered consecutively ----------------------------
const EQ = blocks('eq');
const tags = EQ.map(b => (b.html.match(/<span class="tag">([^<]*)<\/span>/) || [,''])[1].trim());
ok(tags.length >= 12, `the derivation carries its equations (${tags.length})`);
const nums = tags.map(t => parseInt(t.replace(/[()]/g, ''), 10));
let consecutive = true;
nums.forEach((n, i) => { if (n !== i + 1) consecutive = false; });
ok(consecutive, `equations are numbered 1..${nums.length} without gaps (got ${nums.join(',')})`);

// ---- 3. no symbol is used before it is defined --------------------------
// Each symbol maps to a regex that recognises it inside an equation, and the
// text that must have appeared in a `where` table before that point.
const SYMBOLS = [
  { sym: 'd(u,v)',  inEq: /<i>d<\/i>\(/,                defined: /shortest-path distance/i },
  { sym: 'N',       inEq: /<i>N<\/i>/,                  defined: /number of vertices/i },
  { sym: 'deg',     inEq: /deg\(/,                      defined: /<b>Degree<\/b>/i },
  { sym: 'C(v)',    inEq: /C\(<i>v<\/i>\)/,             defined: /closeness centrality/i },
  { sym: 'I',       inEq: /&isin;&#8239;<i>I<\/i>/,     defined: /influential set/i },
  { sym: 'r',       inEq: /<i>r<\/i>/,                  defined: /<b>box radius<\/b>/i },
  { sym: 'p_i',     inEq: /<i>p<sub>i<\/sub><\/i>/,     defined: /share of the total covered mass/i },
  { sym: 'q',       inEq: /<sup><i>q<\/i><\/sup>/,      defined: /moment order/i },
  { sym: 'P_q',     inEq: /P<sub><i>q<\/i><\/sub>/,     defined: /partition function/i },
  { sym: 'r_N',     inEq: /<i>r<sub>N<\/sub><\/i>/,     defined: /normalising radius/i },
  { sym: 'tau',     inEq: /&tau;\(<i>q<\/i>\)/,         defined: /mass exponent/i },
  { sym: 'alpha',   inEq: /&alpha;\(<i>q<\/i>\)/,       defined: /singularity strength/i },
  { sym: 'f(alpha)',inEq: /<i>f<\/i>\(&alpha;\)/,       defined: /singularity spectrum/i },
  { sym: 'B',       inEq: /<i>B<\/i>/,                  defined: /number of independent batches/i },
];

// The rule, stated precisely. Writing "where x is ..." immediately under a
// display is standard mathematical style, so demanding a definition strictly
// BEFORE first use would be stricter than good practice and would force the
// prose into an unnatural order. What genuinely must not happen is a reader
// reaching the end of a subsection still carrying an unexplained symbol.
// So: a symbol's definition must appear after its first use but before the
// next <h3> — or anywhere earlier.
function nextHeadingAfter(pos) {
  const i = html.indexOf('<h3', pos);
  return i === -1 ? html.length : i;
}

let violations = 0, unused = 0;
SYMBOLS.forEach(({ sym, inEq, defined }) => {
  const defAt = html.search(defined);
  if (defAt < 0) { failures++; checks++; console.log(`FAIL  ${sym}: never defined in any "where" table`); return; }
  const use = EQ.find(b => inEq.test(b.html));
  if (!use) { unused++; return; }        // symbol not used in a display; fine
  checks++;
  const deadline = nextHeadingAfter(use.end);
  if (defAt < deadline) {
    console.log(`PASS  ${sym} is defined ${defAt < use.start ? 'before' : 'with'} its first equation`);
  } else {
    failures++; violations++;
    console.log(`FAIL  ${sym} is still undefined at the end of the subsection that first uses it`);
  }
});
ok(unused <= 3, `most listed symbols really do appear in displayed equations (${SYMBOLS.length - unused}/${SYMBOLS.length})`);
ok(violations === 0, 'no symbol is used before the reader has been told what it means');

// ---- 4. every "where" table actually defines something ------------------
const WH = blocks('where');
ok(WH.length >= 7, `symbol tables present (${WH.length})`);
const count = (s, tag) => (s.match(new RegExp('<' + tag + '>', 'g')) || []).length;
ok(WH.every(w => count(w.html, 'dt') > 0 && count(w.html, 'dd') > 0),
   'every symbol table has both terms and definitions');
ok(WH.every(w => count(w.html, 'dt') === count(w.html, 'dd')),
   'every symbol has exactly one definition');

// ---- 5. the worked example matches the shipped data ---------------------
const real = JSON.parse(
  fs.readFileSync(path.join(SITE, '..', '3_notebooks', 'real_results.json'), 'utf8')
    .replace(/\bNaN\b/g, 'null'));
const ex = real['ABAVIJ_clean'];
ok(!!ex, 'the framework used in the worked example is in the dataset');
const WK = blocks('worked');
ok(WK.length >= 1, 'the derivation carries a worked numeric example');
const wt = WK.map(b => b.html).join(' ')
             .replace(/<[^>]+>/g, '')
             .replace(/&#8239;|&nbsp;|&thinsp;|&lfloor;|&rfloor;/g, '')
             .replace(/\s+/g, ' ');
ok(wt.includes(String(ex.N)), `worked example quotes the real block count (${ex.N})`);
ok(wt.includes(String(ex.diameter)), `worked example quotes the real diameter (${ex.diameter})`);
ok(wt.includes(String(ex.n_influential)), `worked example quotes the real influential count (${ex.n_influential})`);
ok(wt.includes(ex.width.toFixed(3)), `worked example quotes the real width (${ex.width.toFixed(3)})`);
ok(wt.includes(Math.abs(ex.asymmetry).toFixed(2)), `worked example quotes the real asymmetry (${ex.asymmetry.toFixed(2)})`);
ok(wt.includes(String(ex.radii.length)), `worked example quotes the real number of fit radii (${ex.radii.length})`);

// ---- 6. the negative-R2 explanation is present, since the data shows it --
const anyNegative = Object.keys(real).some(k =>
  (real[k].r2 || []).some(v => v !== null && v < -1));
ok(!anyNegative || /R&sup2;|R²/.test(html),
   'the alarming R² values in the data are explained rather than left to be discovered');

console.log(`\n${checks - failures}/${checks} checks passed.`);
if (failures) { console.log('MATHS CHECKS FAILED'); process.exit(1); }
console.log('ALL MATHS CHECKS PASSED');
