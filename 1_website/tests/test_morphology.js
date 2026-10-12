// test_morphology.js — the browser morphology engine (mof_morphology.js) and
// the page it drives (morphology.html).
//
// Two things are checked. First, that the JavaScript engine agrees with the
// independent Python implementation (2_python/morphology/), number by number,
// using the Python package's saved output. Two implementations written from
// one specification that disagree means one of them is wrong. Second, that the
// page actually fills its tables and draws a shape, because this site's usual
// failure is a silently blank panel.
const path = require('path');
const fs = require('fs');
const { JSDOM } = require('jsdom');
const SITE = path.join(__dirname, '..');
const M = require(path.join(SITE, 'mof_morphology.js'));

let fails = 0;
const ok = (c, m) => { console.log((c ? 'PASS  ' : 'FAIL  ') + m); if (!c) fails++; };
const near = (a, b, tol) => Math.abs(a - b) <= tol;
const r3 = Math.sqrt(3);

// ---- 1. exact geometry -------------------------------------------------
const cube = M.shape({ '{100}': 1 }, 'm-3m');
ok(cube.name === 'cube' && cube.info.faces === 6 && cube.info.vertices === 8, 'cube: 6 faces, 8 vertices');
ok(near(cube.info.volume, 8, 1e-9), 'cube [-1,1]^3 has volume 8');
ok(near(cube.info.gyration[0][0], 1 / 3, 1e-9), 'cube gyration diagonal is exactly 1/3');
ok(near(cube.info.sphericity, 0.8060, 5e-4), `cube sphericity ${cube.info.sphericity.toFixed(4)} (0.8060)`);
ok(near(cube.info.Q4, 0.7638, 5e-4) && near(cube.info.Q6, 0.3536, 5e-4), 'cube Q4 = 0.764, Q6 = 0.354');
const octa = M.shape({ '{111}': 1 }, 'm-3m');
ok(octa.name === 'octahedron' && near(octa.info.sphericity, 0.8456, 5e-4), 'octahedron, sphericity 0.8456');
ok(near(octa.info.Q4, 0.5092, 5e-4) && near(octa.info.Q6, 0.6285, 5e-4), 'octahedron Q4 = 0.509, Q6 = 0.629');
ok(cube.info.kappa2 < 1e-12 && octa.info.kappa2 < 1e-12, 'kappa^2 = 0 for cube and octahedron');

// ---- 2. systematic absences -----------------------------------------------
ok(!M.allowed([1, 0, 0], 'F') && M.allowed([2, 0, 0], 'F') && M.allowed([1, 1, 1], 'F'), 'F-centring: (100) absent, (200) and (111) allowed');
ok(!M.allowed([1, 1, 1], 'I') && M.allowed([1, 1, 0], 'I'), 'I-centring: (111) absent, (110) allowed');
ok(M.dEff([1, 0, 0], 'F', 1).n === 2 && near(M.dEff([1, 1, 1], 'F', 1).dEff, 1 / r3, 1e-12), 'F: d_eff(100) = a/2, d_eff(111) = a/sqrt3');

// ---- 3. thresholds of the cube-octahedron family --------------------------
ok(M.shape({ '{100}': 1, '{111}': r3 * 1.001 }, 'm-3m').name === 'cube', 'cube for t >= sqrt3');
ok(M.shape({ '{100}': 1, '{111}': 2 / r3 }, 'm-3m').name === 'cuboctahedron', 'cuboctahedron at t = 2/sqrt3');
ok(M.shape({ '{100}': 1, '{111}': 0.999 / r3 }, 'm-3m').name === 'octahedron', 'octahedron for t <= 1/sqrt3');

// ---- 4. agreement with the Python implementation -------------------------
const PY = path.join(SITE, '..', '2_python', 'morphology', 'results', 'phase1_results.json');
if (!fs.existsSync(PY)) { ok(false, 'Python results file present: ' + PY); }
else {
  const R = JSON.parse(fs.readFileSync(PY, 'utf8'));
  // the JSON rounds ratios to 4 decimals; the exact cuboctahedron point 2/sqrt3 must be restored
  const exact = t => Math.abs(t - 2 / r3) < 1e-3 ? 2 / r3 : t;
  R['MOF-5'].morph_series.points.forEach(p => {
    const S = M.shape({ '{100}': 1, '{111}': exact(p.ratio) }, 'm-3m');
    ok(S.name === p.name && S.info.faces === p.n_faces && near(S.info.sphericity, p.sphericity, 2e-4) &&
       near(S.info.Q4, p.Q4, 2e-3) && near(S.info.Q6, p.Q6, 2e-3),
       `MOF-5 t=${p.ratio}: JS "${S.name}" matches Python "${p.name}"`);
  });
  R['ZIF-8'].morph_series.points.forEach(p => {
    const S = M.shape({ '{100}': 1, '{110}': exact(p.ratio) }, 'm-3m');
    ok(S.name === p.name && near(S.info.sphericity, p.sphericity, 2e-4), `ZIF-8 R110/R100=${p.ratio}: JS matches Python ("${p.name}")`);
  });
  R['UiO-66'].tetrahedral_series.forEach(p => {
    const S = M.shape({ '{111}+': p.ratio, '{111}-': 1, '{100}': 1.155 }, '-43m');
    const pyName = p.name.replace('trunc. octahedron', 'truncated octahedron');
    ok(S.name === pyName && near(S.info.sphericity, p.sphericity, 2e-4) && near(S.info.Q3, p.Q3, 2e-3),
       `UiO-66 tetrahedral ${p.ratio}: JS matches Python ("${p.name}", Q3 ${p.Q3})`);
  });
  ['MOF-5', 'HKUST-1', 'UiO-66', 'ZIF-8'].forEach(n => {
    const s = M.STRUCTURES[n], S = M.shape(M.bfdhRates(s.centring, s.a, s.pointGroup), s.pointGroup);
    ok(S.name === R[n].bfdh.name && near(S.info.sphericity, R[n].bfdh.sphericity, 2e-4), `${n} BFDH: ${S.name} (Python ${R[n].bfdh.name})`);
    ok(s.spacegroup === R[n].spacegroup && near(s.a, R[n].a, 1e-3), `${n} input symmetry matches spglib output (${s.spacegroup}, a=${s.a})`);
  });
  const G = R.graph_rule;
  ['pcu', 'fcu'].forEach((net, i) => {
    const mof = i ? 'UiO-66' : 'MOF-5', c = G[mof].attachment_numbers;
    ok(M.attachmentNumber(net, [1, 0, 0]) === c['{100}'] && M.attachmentNumber(net, [1, 1, 0]) === c['{110}'] &&
       M.attachmentNumber(net, [1, 1, 1]) === c['{111}'], `${net} attachment numbers agree (${c['{100}']}, ${c['{110}']}, ${c['{111}']})`);
    G[mof].beta_series.filter(b => b.beta > 0).forEach(b => {
      ok(M.shape(M.graphRates(net, b.beta), 'm-3m').name === b.name, `${net} beta=${b.beta}: ${b.name}`);
    });
  });
}
ok(M.attachmentNumber('fcu', [1, 1, 0]) === 5 && M.attachmentNumber('fcu', [1, 0, 0]) === 4 &&
   M.attachmentNumber('fcu', [1, 1, 1]) === 3, 'fcu reproduces Chen et al. (Matter 2020): 5, 4, 3');

// ---- 5. the page ------------------------------------------------------------
const html = fs.readFileSync(path.join(SITE, 'morphology.html'), 'utf8');
const body = html.replace(/<script src="[a-zA-Z0-9_./]+\.js"><\/script>/g, '')
  .replace(/^[\s\S]*<body>/, '').replace(/<\/body>[\s\S]*$/, '');
const dom = new JSDOM(`<!DOCTYPE html><html><body>${body}</body></html>`, { runScripts: 'outside-only', pretendToBeVisual: true });
const W = dom.window;
W.eval(fs.readFileSync(path.join(SITE, 'mof_morphology.js'), 'utf8'));
W.eval(fs.readFileSync(path.join(SITE, 'morphology_page.js'), 'utf8'));
// jsdom leaves readyState at "loading", so the page waits for DOMContentLoaded
if (W.document.readyState === 'loading') W.document.dispatchEvent(new W.Event('DOMContentLoaded', { bubbles: true }));
const D = W.document;

ok(/<script src="mof_morphology\.js"><\/script>/.test(html) && /<script src="morphology_page\.js"><\/script>/.test(html), 'page loads both morphology scripts');
const rowsOf = id => D.querySelectorAll(`#${id} tbody tr`).length;
ok(rowsOf('morph-bfdh') === 4, 'BFDH table has one row per structure');
ok(/rhombic dodecahedron/.test(D.getElementById('morph-bfdh').textContent), 'BFDH table names ZIF-8 a rhombic dodecahedron');
ok(rowsOf('morph-thresholds') === 6 && /cuboctahedron/.test(D.getElementById('morph-thresholds').textContent), 'threshold table computed');
ok(rowsOf('morph-attach') === 2 && /cube/.test(D.getElementById('morph-attach').textContent) &&
   /octahedron/.test(D.getElementById('morph-attach').textContent), 'attachment table: pcu cube, fcu octahedron');

const polys = () => D.querySelectorAll('#morph-view svg polygon').length;
const nameNow = () => (D.getElementById('morph-name') || {}).textContent;
ok(polys() > 0, `explorer draws a shape (${polys()} visible faces)`);
ok(nameNow() === 'truncated octahedron', `explorer starts at the BFDH shape of MOF-5 (${nameNow()})`);
const click = label => [...D.querySelectorAll('#morph-presets .mode-btn')].find(b => b.textContent === label).click();
click('Cube'); ok(nameNow() === 'cube', 'preset Cube gives a cube');
click('Octahedron'); ok(nameNow() === 'octahedron', 'preset Octahedron gives an octahedron');
click('Tetrahedron'); ok(nameNow() === 'tetrahedron', 'preset Tetrahedron switches to UiO-66 and gives a tetrahedron');
click('Graph rule'); ok(nameNow() === 'octahedron', 'graph rule on UiO-66 gives an octahedron');
[...D.querySelectorAll('#morph-structs .mode-btn')].find(b => b.textContent === 'MOF-5').click();
click('Graph rule'); ok(nameNow() === 'cube', 'graph rule on MOF-5 gives a cube');
[...D.querySelectorAll('#morph-structs .mode-btn')].find(b => b.textContent === 'ZIF-8').click();
click('BFDH (lattice only)'); ok(nameNow() === 'rhombic dodecahedron', 'BFDH on ZIF-8 gives a rhombic dodecahedron');
const slider = D.getElementById('morph-in-r110');
slider.value = Math.log(3); slider.dispatchEvent(new W.Event('input'));
ok(nameNow() !== 'rhombic dodecahedron', `moving the R110 slider changes the shape (${nameNow()})`);

console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
