/* =====================================================================
   test_real_band_numbers.js — every number the real-MOF section states must
   be derivable from 3_notebooks/real_results.json and results.json.

   WHY A SEPARATE SUITE
   The other suites check that pages render and that engines agree. This one
   checks that the PROSE is true. The section that this replaces asserted "no
   overlap at all" and "a gap of 0.25" in hand-written HTML, and those
   sentences stayed on the site after the data that supported them had been
   superseded — because nothing was comparing the sentence to the file.

   Every assertion here recomputes the statistic from the raw spectra and
   compares it to what real_band_data.js ships. If someone regenerates the
   data and forgets to update the page, or edits the page without regenerating
   the data, this fails.
   ===================================================================== */
'use strict';

const fs = require('fs');
const path = require('path');

const SITE = path.join(__dirname, '..');
const ROOT = path.join(SITE, '..');

let failures = 0, checks = 0;
function ok(cond, msg) {
  checks++;
  if (cond) { console.log('PASS  ' + msg); }
  else { failures++; console.log('FAIL  ' + msg); }
}
function close(a, b, tol, msg) {
  ok(Math.abs(a - b) <= tol, `${msg} (page ${a}, data ${b})`);
}

// ---- load the raw spectra -------------------------------------------------
// NOTE: both notebook outputs contain bare `NaN` tokens. Python's json.dump
// emits those by default and Python's json.load reads them back, but NaN is
// not valid JSON and JSON.parse rejects it — so these files cannot be consumed
// by any non-Python reader without this substitution. The NaN sits in the r2
// array at q = 0, where the through-origin fit is against a flat line and R²
// is genuinely undefined, so null is the honest replacement rather than a
// workaround. Flagged in 3_notebooks/README.md.
function readSpectra(p) {
  const raw = fs.readFileSync(p, 'utf8');
  return JSON.parse(raw.replace(/\bNaN\b/g, 'null').replace(/\b-?Infinity\b/g, 'null'));
}
const real = readSpectra(path.join(ROOT, '3_notebooks', 'real_results.json'));
const hmof = readSpectra(path.join(ROOT, '3_notebooks', 'results.json'));

// ---- load what the site ships --------------------------------------------
const src = fs.readFileSync(path.join(SITE, 'real_band_data.js'), 'utf8');
const sandbox = { window: {} };
new Function('window', src)(sandbox.window);
const S = sandbox.window.REAL_BAND_STATS;
const D = sandbox.window.REAL_BAND_DATA;

const rW = Object.keys(real).map(k => real[k].width);
const hW = Object.keys(hmof).map(k => hmof[k].width);
const mean = a => a.reduce((x, y) => x + y, 0) / a.length;
const sd = a => { const m = mean(a); return Math.sqrt(a.reduce((s, v) => s + (v - m) ** 2, 0) / (a.length - 1)); };

// ---- counts ---------------------------------------------------------------
ok(Object.keys(D).length === Object.keys(real).length,
   `every spectrum in real_results.json is shipped (${Object.keys(D).length}/${Object.keys(real).length})`);
ok(S.n === rW.length, `stated n matches the data (${S.n})`);
ok(S.n_hmof === hW.length, `stated hMOF n matches the data (${S.n_hmof})`);

// ---- the band itself ------------------------------------------------------
close(S.w_min, Math.min(...rW), 5e-4, 'real minimum Δα');
close(S.w_max, Math.max(...rW), 5e-4, 'real maximum Δα');
close(S.w_mean, mean(rW), 5e-4, 'real mean Δα');
close(S.w_sd, sd(rW), 5e-4, 'real sd of Δα');
close(S.h_min, Math.min(...hW), 5e-4, 'hMOF minimum Δα');
close(S.h_max, Math.max(...hW), 5e-4, 'hMOF maximum Δα');
close(S.h_mean, mean(hW), 5e-4, 'hMOF mean Δα');
close(S.mean_diff, mean(rW) - mean(hW), 5e-4, 'stated difference of means');

// ---- the overlap claim, which is the headline -----------------------------
const oLo = Math.max(Math.min(...rW), Math.min(...hW));
const oHi = Math.min(Math.max(...rW), Math.max(...hW));
close(S.overlap_lo, oLo, 5e-4, 'overlap lower bound');
close(S.overlap_hi, oHi, 5e-4, 'overlap upper bound');
ok(oHi > oLo, 'the two ranges genuinely overlap — the headline claim is true of the data');
close(S.overlap_frac_real, rW.filter(v => v >= oLo && v <= oHi).length / rW.length, 5e-4,
      'fraction of the real set inside the overlap');

// ---- the withdrawal must remain justified by the data ---------------------
const rN = Object.keys(real).map(k => real[k].N);
const hN = Object.keys(hmof).map(k => hmof[k].N);
ok(Math.min(...hN) === S.hN_min && Math.max(...hN) === S.hN_max,
   `stated hMOF size range matches the data (${S.hN_min}–${S.hN_max})`);
const OLD_MAX_N = 972;   // the largest of the four withdrawn structures
ok(hN.every(n => n > OLD_MAX_N),
   'no hMOF is as small as the largest withdrawn structure — the size mismatch was real');
ok(S.n_size_matched === rN.filter(n => n >= Math.min(...hN)).length,
   `stated size-matched count is correct (${S.n_size_matched}/${rW.length})`);

// correlation of width with atom count, which is the reason the old claim fell
function corr(a, b) {
  const ma = mean(a), mb = mean(b);
  let n = 0, da = 0, db = 0;
  for (let i = 0; i < a.length; i++) {
    n += (a[i] - ma) * (b[i] - mb); da += (a[i] - ma) ** 2; db += (b[i] - mb) ** 2;
  }
  return n / Math.sqrt(da * db);
}
close(S.r_width_atoms_hmof, corr(hW, hN), 2e-3, 'stated Δα–atoms correlation (hMOF)');
close(S.r_width_atoms_real, corr(rW, rN), 2e-3, 'stated Δα–atoms correlation (real)');
ok(S.r_width_atoms_hmof > 0.5,
   `Δα really does rise with graph size (r=${S.r_width_atoms_hmof}) — the withdrawal stands`);

// ---- the rendered page must not contain the retracted sentences ----------
const results = fs.readFileSync(path.join(SITE, 'results.html'), 'utf8');
[['no overlap at all', 'the retracted "no overlap" sentence'],
 ['gap of 0.25', 'the retracted gap figure'],
 ['1.66', 'the withdrawn lower bound stated as current']].forEach(([needle, what]) => {
  const i = results.indexOf(needle);
  if (i === -1) { ok(true, `results.html does not present ${what}`); return; }
  const context = results.slice(Math.max(0, i - 400), i + 200);
  ok(/[Ww]ithdraw|previously|superseded|retract|earlier/.test(context),
     `results.html mentions ${what} only inside a withdrawal`);
});
// The strongest wording lives in real_band_page.js, which renders at runtime.
// The static HTML must carry the disclosure too, so that a reader with
// JavaScript disabled is not shown a page that quietly omits the retraction.
ok(/withdraw/i.test(results),
   'results.html discloses the withdrawal in its static markup, not only via JavaScript');
ok(/withdrawn/i.test(fs.readFileSync(path.join(SITE, 'real_band_page.js'), 'utf8')),
   'the rendered section states the withdrawal explicitly');

// ---- and the per-structure rows must match the source --------------------
let drift = 0;
Object.keys(D).forEach(k => {
  if (!(k in real)) { drift++; return; }
  if (Math.abs(D[k].width - real[k].width) > 5e-4) drift++;
  if (D[k].N !== real[k].N) drift++;
});
ok(drift === 0, `no shipped structure has drifted from real_results.json (${drift} mismatches)`);

console.log(`\n${checks - failures}/${checks} checks passed.`);
if (failures) { console.log('REAL-BAND NUMBER CHECKS FAILED'); process.exit(1); }
console.log('ALL REAL-BAND NUMBER CHECKS PASSED');
