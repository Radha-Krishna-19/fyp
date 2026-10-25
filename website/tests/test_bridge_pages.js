// Checks the three pages added on 2026-10-16 (Hybrid, Spectrum to Shape, Mistakes) against their data files.
const fs = require('fs'), path = require('path');
const { JSDOM } = require('jsdom');
const SITE = path.join(__dirname, '..');
const ROOT = path.join(SITE, '..');
let fails = 0;
const ok = (c, m) => { console.log((c ? 'PASS  ' : 'FAIL  ') + m); if (!c) fails++; };
const doc = f => new JSDOM(fs.readFileSync(path.join(SITE, f), 'utf8')).window.document;

// ---- Spectrum <-> Shape (relation.html): every number equals the notebook's result files
const RES = path.join(ROOT, 'code/spectrum_shape_relation/results');
const R1 = JSON.parse(fs.readFileSync(path.join(RES, '01_box_particles_MOF5.json'), 'utf8'));
const R2 = JSON.parse(fs.readFileSync(path.join(RES, '02_predicted_crystal_shapes_MOF5.json'), 'utf8'));
const R3 = JSON.parse(fs.readFileSync(path.join(RES, '03_core_mof_spectrum_vs_bfdh_shape.json'), 'utf8'));
const B = doc('relation.html');
R1.shapes.forEach(r => {
  const row = B.querySelector(`#rel-boxes-table tr[data-shape="${r.label}"]`);
  ok(!!row, `relation: box row ${r.label}`);
  if (!row) return;
  const c = row.querySelectorAll('td');
  ok(c[4].textContent.startsWith(r.width_mean.toFixed(3)), `relation: ${r.label} width ${r.width_mean.toFixed(3)}`);
  ok(Number(c[3].textContent) === r.diameter, `relation: ${r.label} diameter`);
  ok(c[6].textContent.startsWith((r.excess_over_trend >= 0 ? '+' : '-') + Math.abs(r.excess_over_trend).toFixed(3)), `relation: ${r.label} difference from trend`);
});
R2.shapes.forEach(r => {
  const row = B.querySelector(`#rel-predicted-table tr[data-shape="${r.shape}|${r.target_blocks}"]`);
  ok(!!row && row.querySelectorAll('td')[4].textContent.startsWith(r.width_mean.toFixed(3)), `relation: ${r.shape} at ${r.target_blocks} width`);
});
Object.entries(R3.tests).forEach(([sub, tests]) => Object.entries(tests).forEach(([k, v]) => {
  if (!('partial_p' in v)) return;
  const row = B.querySelector(`#rel-core-table tr[data-test="${sub}|${k}"]`);
  ok(!!row && row.querySelectorAll('td')[3].textContent.startsWith((v.spearman >= 0 ? '+' : '-') + Math.abs(v.spearman).toFixed(3)), `relation: ${sub} / ${k} raw rho`);
}));
ok(R1.check_against_code_19 && R1.check_against_code_19.largest_width_difference === 0, 'relation data: notebook run equals code_19 exactly');
ok(/Produced by:/.test(B.body.textContent) && /Spectrum_Shape_Relation\.ipynb/.test(B.body.textContent), 'relation: names the notebook that produced it');
ok(['01_box_particles_MOF5.png', '02_predicted_crystal_shapes_MOF5.png', '03_core_mof_spectrum_vs_bfdh_shape.png']
   .every(f => fs.existsSync(path.join(SITE, 'figures/relation', f))), 'relation: all three figures exist');
const BR = doc('bridge.html');
ok(/Why We Want to Change the Shape/.test(BR.body.textContent), 'bridge: purpose section present');
ok(/not computed adsorption|has not computed adsorption/.test(BR.body.textContent), 'bridge: states adsorption was not computed');
ok(!!BR.querySelector('a[href="relation.html"]'), 'bridge: links to the relation page');

// ---- Hybrid page equals hybrid_results.json
const H = JSON.parse(fs.readFileSync(path.join(ROOT, 'code/morphology/results/hybrid_results.json'), 'utf8'));
const HD = doc('hybrid.html');
Object.keys(H).forEach(m => {
  const row = HD.querySelector(`#hy-table tr[data-mof="${m}"]`);
  ok(!!row, `hybrid: row ${m}`);
  if (!row) return;
  const c = row.querySelectorAll('td');
  ['0', '0.25', '0.5', '0.75', '1'].forEach((w, i) => ok(c[1 + i].textContent === H[m].shapes[w].name, `hybrid: ${m} w=${w} ${H[m].shapes[w].name}`));
});
ok(/no best weight|Why no best weight/i.test(HD.body.textContent), 'hybrid: refuses to give a best weight');

// ---- Mistakes page: every entry has all six rows, and the key admissions are there
const L = doc('lessons.html');
const tabs = [...L.querySelectorAll('table.lesson')];
ok(tabs.length === 22, `lessons: 22 entries: 9 spectrum, 8 morphology, 5 audit (found ${tabs.length})`);
const need = ['In simple words', 'Why we chose it', 'Why it was wrong', 'The technical reason', 'How we fixed it', 'Where to see it'];
ok(tabs.every(t => need.every((n, i) => t.querySelectorAll('tr')[i].querySelector('td').textContent === n)), 'lessons: every entry has the six rows in order');
['l-tau', 'l-classes', 'l-size', 'm-hydrogen', 'm-never', 'm-trustuff'].forEach(id => ok(!!L.getElementById(id), `lessons: entry ${id}`));

// ---- How We Got Here (journey.html): ten stages, six rows each, every mistake link resolves
const J = doc('journey.html');
const jt = [...J.querySelectorAll('table.journey')];
ok(jt.length === 11, `journey: 11 stages (found ${jt.length})`);
ok(jt.every(t => t.querySelectorAll('tr').length === 7 && t.querySelector('td').textContent === 'Purpose of this step'), 'journey: every stage has the seven rows, starting with its purpose');
const LL = doc('lessons.html');
const links = [...J.querySelectorAll('a[href^="lessons.html#"]')].map(a => a.getAttribute('href').split('#')[1]);
ok(links.length >= 15 && links.every(id => !!LL.getElementById(id)), `journey: all ${links.length} mistake links point to real entries`);
ok([...J.querySelectorAll('a[href^="#j"]')].every(a => !!J.getElementById(a.getAttribute('href').slice(1))), 'journey: stage index links resolve');

ok(J.querySelectorAll('#j-papers-table tbody tr').length >= 12, 'journey: purpose of each paper');
ok(J.querySelectorAll('#j-notebooks-table tbody tr').length >= 8, 'journey: purpose of each notebook');
ok(J.querySelectorAll('#j-decisions-table tbody tr').length >= 10, 'journey: each key decision defended');

// ---- Learn 2 (learn_energy.html): every newly defined term is actually taught on the page
const LE = doc('learn_energy.html');
const leText = LE.body.textContent.toLowerCase();
['surface energy', 'cleavage energy', 'termination', 'slab', 'vacuum', 'stoichiometric', 'symmetric slab', 'relaxation',
 'force field', 'lennard-jones', 'dft', 'chgnet', 'modulator', 'overfitting', 'hold-out', 'spearman', 'permutation',
 'bootstrap', 'partial correlation', 'torus', 'finite particle', 'taxicab', 'spglib', 'pymatgen', 'ev/']
  .forEach(t => ok(leText.includes(t), `learn 2: teaches "${t}"`));
ok([...LE.querySelectorAll('img')].every(i => fs.existsSync(path.join(SITE, i.getAttribute('src')))), 'learn 2: every figure exists');
ok(/make_learn_energy_figures\.py/.test(LE.body.textContent), 'learn 2: names the script that drew its figures');

// ---- Team page agrees with the dataset
const T = doc('team.html').body.textContent;
ok(/134 records/.test(T) && !/104 records/.test(T), 'team: dataset size is 134 records, not the old 104');
console.log(fails ? `\n${fails} FAILURES` : '\nAll bridge-page tests passed.');
process.exit(fails ? 1 : 0);
