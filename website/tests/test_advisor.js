// test_advisor.js: the MOF Shape Advisor page (advisor.html).
// 1. advisor_data.js equals the result files it is built from (no number edited by hand).
// 2. The cubic shapes drawn by mof_morphology.js have the dominant face and face shares that
//    the Python benchmark and steering scripts report.
// 3. The page renders every MOF with no blank panel, and its tables show the result-file numbers.
const path = require('path'), fs = require('fs');
const { JSDOM } = require('jsdom');
const SITE = path.join(__dirname, '..');
const RES = path.join(SITE, '..', 'code', 'morphology', 'results');
let fails = 0;
const ok = (c, m) => { console.log((c ? 'PASS  ' : 'FAIL  ') + m); if (!c) fails++; };
const J = f => JSON.parse(fs.readFileSync(path.join(RES, f), 'utf8'));
const BENCH = J('benchmark_mofs.json'), STEER = J('shape_steering.json'), ADS = J('shape_adsorption.json'), DS = J('dataset_shapes.json');

// ---- 1. data file against the result files ----------------------------------------------
const W = {}; new Function('window', fs.readFileSync(path.join(SITE, 'advisor_data.js'), 'utf8'))(W);
const A = W.ADVISOR;
ok(JSON.stringify(A.face_scores) === JSON.stringify(BENCH.face_scores), 'face scores equal benchmark_mofs.json');
ok(JSON.stringify(A.habit_scores) === JSON.stringify(BENCH.habit_scores), 'habit scores equal benchmark_mofs.json');
ok(A.n_records === BENCH.n_records, `record count ${A.n_records}`);
ok(JSON.stringify(A.steering) === JSON.stringify(STEER.mofs), 'steering equals shape_steering.json');
Object.keys(ADS.mofs || {}).forEach(m => ok(JSON.stringify(A.adsorption[m]) === JSON.stringify(ADS.mofs[m]), `adsorption ${m} equals shape_adsorption.json`));

// ---- 2. JS Wulff shapes against Python face shares --------------------------------------
global.window = global;
const M = require(path.join(SITE, 'mof_morphology.js'));
Object.keys(STEER.mofs).forEach(m => {
  const g = STEER.mofs[m].gamma_uff;
  const S = M.shape({ '{100}': g['100'], '{110}': g['110'], '{111}': g['111'] }, 'm-3m');
  const area = {}; let tot = 0;
  S.faces.forEach(f => { area[f.tag] = (area[f.tag] || 0) + f.area; tot += f.area; });
  const py = STEER.mofs[m].shares;
  const worst = Math.max(...['100', '110', '111'].map(k => Math.abs((area['{' + k + '}'] || 0) / tot - py[k])));
  ok(worst < 2e-3, `${m}: JS face shares equal Python within ${worst.toExponential(1)}`);
});

// ---- 3. the page ---------------------------------------------------------------------------
const html = fs.readFileSync(path.join(SITE, 'advisor.html'), 'utf8');
const body = html.replace(/<script src="[a-zA-Z0-9_./]+\.js"><\/script>/g, '').replace(/^[\s\S]*<body>/, '').replace(/<\/body>[\s\S]*$/, '');
const dom = new JSDOM(`<!DOCTYPE html><html><body>${body}</body></html>`, { runScripts: 'outside-only' });
['face_card.js', 'mof_morphology.js', 'mof_cif_shape.js', 'mof_general_shape.js', 'advisor_data.js', 'advisor_page.js'].forEach(s =>
  dom.window.eval(fs.readFileSync(path.join(SITE, s), 'utf8')));
if (dom.window.document.readyState === 'loading') dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
const D = dom.window.document, P = dom.window.ADVISOR_PAGE;
ok(D.querySelectorAll('#adv-mofs .struct-tab').length === A.order.length, `${A.order.length} MOF buttons`);
ok(D.getElementById('adv-nrec').textContent === String(BENCH.n_records), 'record count shown');
const sc = D.querySelectorAll('#adv-score-table tbody tr');
ok(sc.length === 3, 'score table has three rows');
const af = BENCH.face_scores['measured_and_built/additive_free'];
ok(sc[0].querySelectorAll('td')[2].textContent.startsWith(af[1].correct + ' / ' + af[1].n), `UFF additive-free ${af[1].correct}/${af[1].n} shown`);
const EU = BENCH.evidence_units['uff/additive_free'];
ok(D.getElementById('adv-units').textContent.includes(`right for ${EU.mofs_right_by_majority} of ${EU.mofs} MOFs`), `evidence units: ${EU.mofs_right_by_majority} of ${EU.mofs} MOFs`);
ok(D.getElementById('adv-dataset').textContent.includes('77 files'), 'dataset summary shown');
A.order.forEach(m => {
  P.select(m);
  const p = A.predictions[m];
  const svg = D.querySelector('#adv-view svg');
  if (p.file) ok(!!svg && svg.querySelectorAll('polygon[data-face]').length >= 3, `${m}: shape drawn`);
  else ok(!svg, `${m}: no file, no shape`);
  ok(D.getElementById('adv-summary').textContent.length > 40, `${m}: summary written`);
  if (STEER.mofs[m]) {
    const rows = D.querySelectorAll('#adv-steer-table tbody tr');
    const s = STEER.mofs[m].steering['100'].lower_by_percent_for_pure_shape;
    ok(rows.length === 3 && rows[0].querySelectorAll('td')[2].textContent === (s === 0 ? 'already' : s < 1 ? s.toFixed(1) + ' %' : s.toFixed(0) + ' %'), `${m}: steering {100} pure shape ${s} %`);
  }
  if (A.adsorption[m]) {
    const r = D.querySelector('#adv-face-table tbody tr');
    const k = Object.keys(A.adsorption[m].faces)[0];
    ok(!!r && r.querySelectorAll('td')[1].textContent === (100 * A.adsorption[m].faces[k].CO2.open_fraction).toFixed(1) + ' %', `${m}: open fraction of {${k}} shown`);
  }
});
P.select('HKUST-1');
const poly = D.querySelector('#adv-view polygon[data-face]');
['pointerdown', 'pointerup'].forEach(t => poly.dispatchEvent(new dom.window.MouseEvent(t, { bubbles: true, clientX: 10, clientY: 10 })));
ok(/Open to CO/.test(D.getElementById('adv-view').textContent), 'face card shows the open fraction');
console.log(fails ? `\n${fails} failure(s)` : '\nall advisor checks passed');
process.exit(fails ? 1 : 0);
