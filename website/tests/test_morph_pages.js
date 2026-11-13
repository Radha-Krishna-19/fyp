// test_morph_pages.js — the three morphology teaching pages added in October 2026:
// learn_shape.html (concepts), morph_math.html (Phase 2 proofs with live checks) and
// graph_faces.html (Phase 3 results). Checks that every figure exists, that every
// live check on the Mathematics page holds, and that the Phase 3 tables show exactly
// the numbers the Python code wrote.
const path = require('path'), fs = require('fs');
const { JSDOM } = require('jsdom');
const SITE = path.join(__dirname, '..');
let fails = 0;
const ok = (c, m) => { console.log((c ? 'PASS  ' : 'FAIL  ') + m); if (!c) fails++; };

function load(page, scripts) {
  const html = fs.readFileSync(path.join(SITE, page), 'utf8');
  const body = html.replace(/<script src="[a-zA-Z0-9_./]+\.js"><\/script>/g, '').replace(/^[\s\S]*<body>/, '').replace(/<\/body>[\s\S]*$/, '');
  const dom = new JSDOM(`<!DOCTYPE html><html><body>${body}</body></html>`, { runScripts: 'outside-only' });
  scripts.forEach(s => dom.window.eval(fs.readFileSync(path.join(SITE, s), 'utf8')));
  if (dom.window.document.readyState === 'loading') dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
  return { html, D: dom.window.document };
}

// ---- every image on the morphology pages exists, and has alt text --------------------
['learn_shape.html', 'morph_math.html', 'morphology.html', 'graph_faces.html', 'surface_energy.html', 'deform.html', 'experiment.html'].forEach(p => {
  const D = new JSDOM(fs.readFileSync(path.join(SITE, p), 'utf8')).window.document;
  const imgs = [...D.querySelectorAll('main img')];
  imgs.forEach(i => {
    ok(fs.existsSync(path.join(SITE, i.getAttribute('src'))), `${p}: image ${i.getAttribute('src')} exists`);
    ok((i.getAttribute('alt') || '').length > 30, `${p}: image ${i.getAttribute('src')} has descriptive alt text`);
  });
  if (p === 'learn_shape.html') ok(imgs.length >= 14, `learn_shape.html teaches with pictures (${imgs.length} figures)`);
});

// ---- the Mathematics page: all live checks hold ---------------------------------------
const MM = load('morph_math.html', ['mof_morphology.js', 'mof_deform.js', 'morph_math_page.js']);
const rows = [...MM.D.querySelectorAll('#math-checks-table tbody tr')];
ok(rows.length >= 16, `morph_math.html: ${rows.length} live checks rendered`);
rows.forEach(r => ok(r.children[2].textContent === 'holds', `Proposition ${r.children[0].textContent}: ${r.children[2].textContent}`));
['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16'].forEach(n =>
  ok(new RegExp('Proposition ' + n + '\\b').test(MM.html), `morph_math.html states Proposition ${n}`));
ok((MM.html.match(/&#8718;|∎/g) || []).length >= 16, 'every proposition has a proof ending in a box');

// ---- the Graph Faces page shows exactly the Python numbers ------------------------------
const PY = JSON.parse(fs.readFileSync(path.join(SITE, '..', 'code', 'morphology', 'results', 'phase3_results.json'), 'utf8'));
const data = fs.readFileSync(path.join(SITE, 'phase3_data.js'), 'utf8');
const W = {}; new Function('window', data)(W);
['MOF-5', 'HKUST-1', 'UiO-66', 'ZIF-8'].forEach(n => {
  Object.keys(PY[n].faces).forEach(f => {
    const a = PY[n].faces[f], b = W.PHASE3[n].faces[f];
    ok(b && a.E_att === b.E_att && a.gamma === b.gamma && a.cls === b.cls, `phase3_data.js ${n} ${f} equals the Python output`);
  });
});
const GF = load('graph_faces.html', ['phase3_data.js', 'graph_faces_page.js']);
ok(GF.D.querySelectorAll('#gf-net tbody tr').length === 4, 'graph_faces.html: net table has four structures');
ok(GF.D.querySelectorAll('#gf-face-tables table').length === 4, 'graph_faces.html: one face table per structure');
const shapes = GF.D.getElementById('gf-shapes').textContent;
ok(/rhombic dodecahedron/.test(shapes) && /cube/.test(shapes), 'graph_faces.html: shape table names the ZIF-8 dodecahedron and the MOF-5 cube');
// the headline claims on the page must agree with the data
ok(PY['ZIF-8'].shape_attachment.name_major_faces === 'rhombic dodecahedron', 'ZIF-8 attachment shape is a rhombic dodecahedron');
ok(PY['MOF-5'].shape_wulff_broken_bond.name_major_faces === 'cube', 'MOF-5 broken-bond Wulff shape is a cube');
const slow = n => Object.entries(PY[n].shape_attachment.face_area_fraction).sort((a, b) => b[1] - a[1])[0][0].replace(/[+-]$/, '');
ok(slow('MOF-5') === '{100}' && slow('HKUST-1') === '{111}' && slow('UiO-66') === '{111}' && slow('ZIF-8') === '{110}',
   `dominant faces from the graph: MOF-5 ${slow('MOF-5')}, HKUST-1 ${slow('HKUST-1')}, UiO-66 ${slow('UiO-66')}, ZIF-8 ${slow('ZIF-8')}`);

// ---- the Surface Energy page shows exactly the Python numbers (Phase 4) ----------------
const P4 = JSON.parse(fs.readFileSync(path.join(SITE, '..', 'code', 'morphology', 'results', 'phase4_results.json'), 'utf8'));
const SE = load('surface_energy.html', []);
let n4 = 0;
SE.D.querySelectorAll('tr[data-face]').forEach(tr => {
  const [m, f] = tr.getAttribute('data-face').split('|');
  ok(P4[m].faces[f] && Number(tr.getAttribute('data-gamma')) === P4[m].faces[f].gamma, `surface_energy.html ${m} ${f} gamma equals the Python output`); n4++;
});
ok(n4 === Object.values(P4).reduce((a, r) => a + Object.keys(r.faces).length, 0), `surface_energy.html lists every face (${n4})`);
ok(/cube/.test(SE.D.querySelector('tr[data-shape="MOF-5"]').textContent) && /rhombic dodecahedron/.test(SE.D.querySelector('tr[data-shape="ZIF-8"]').textContent), 'surface_energy.html: MOF-5 cube and ZIF-8 dodecahedron named');
const low = m => Object.entries(P4[m].faces).sort((a, b) => a[1].gamma - b[1].gamma)[0][0];
ok(low('MOF-5') === '{100}' && low('HKUST-1') === '{111}' && /^\{111\}/.test(low('UiO-66')) && low('ZIF-8') === '{110}', 'lowest-energy faces: MOF-5 {100}, HKUST-1 {111}, UiO-66 {111}, ZIF-8 {110}');

// ---- the Cell Deform page: live explorer agrees with the Python results ----------------------
const DF = JSON.parse(fs.readFileSync(path.join(SITE, '..', 'code', 'morphology', 'results', 'deform_results.json'), 'utf8'));
const DM = load('deform.html', ['face_card.js', 'mof_morphology.js', 'mof_deform.js', 'deform_page.js']);
ok(DM.D.querySelectorAll('#df-view svg polygon').length > 3, 'deform.html: explorer draws a crystal');
ok(/equant/.test(DM.D.getElementById('df-name').textContent), 'deform.html: the real cell is equant');
const CEN = { 'MOF-5': ['F', 'm-3m', 25.866], 'HKUST-1': ['F', 'm-3m', 26.297], 'UiO-66': ['F', '-43m', 20.518], 'ZIF-8': ['I', '-43m', 16.991] };
const DEF = require(path.join(SITE, 'mof_deform.js'));
let nd = 0, bd = 0;
Object.keys(CEN).forEach(m => DF[m].c_stretch.forEach(r => {
  const [c, pg, a] = CEN[m], S = DEF.bfdhShape(c, pg, [a, a, a * r.lc]), h = DEF.habit(S); nd++;
  if (!(h.type === r.habit && S.name === r.name && Math.abs(S.info.sphericity - r.sphericity) < 2e-4)) bd++;
}));
ok(bd === 0, `JavaScript deformed-cell shapes equal the Python output in all ${nd} stretched cases (habit, name, sphericity)`);
DM.D.querySelectorAll('tr[data-case]').forEach(tr => {
  const [m, lc] = tr.getAttribute('data-case').split('|'), r = DF[m].c_stretch.find(x => x.lc === Number(lc));
  ok(r && r.habit === tr.getAttribute('data-habit'), `deform.html table ${m} c x ${lc} habit equals the Python output`);
});
ok(DF['MOF-5'].c_stretch.some(r => r.habit === 'plate') && DF['MOF-5'].c_stretch.some(r => r.habit === 'rod'), 'a plate and a rod are both reached from the MOF-5 cell');

// ---- the Experiment page shows exactly the Python numbers (CHGNet, fragments, bond cost, CoRE) ----
const RES = path.join(SITE, '..', 'code', 'morphology', 'results');
const rj = f => JSON.parse(fs.readFileSync(path.join(RES, f), 'utf8'));
const CC = rj('chgnet_cleavage_results.json'), PC = rj('slab_pieces.json'), BSJ = rj('bond_sensitivity.json'), CO = rj('core_results.json');
const EX = load('experiment.html', []);
let ncl = 0;
EX.D.querySelectorAll('tr[data-gamma-cl]').forEach(tr => {
  const [m, f] = tr.getAttribute('data-gamma-cl').split('|');
  ok(Number(tr.getAttribute('data-gamma')) === CC[m].all_slabs.faces_info[f].gamma_cleavage_J_m2, `experiment.html ${m} ${f} cleavage gamma equals the Python output`); ncl++;
});
ok(ncl === Object.values(CC).reduce((a, v) => a + Object.keys(v.all_slabs.faces_info).length, 0), `experiment.html lists every CHGNet cleavage energy (${ncl})`);
Object.keys(CC).forEach(m => {
  const tr = EX.D.querySelector(`tr[data-cl-shape="${m}"]`);
  ok(tr && tr.textContent.includes(CC[m].all_slabs.shapes['1'].name), `experiment.html ${m} CHGNet Wulff shape named as in the Python output`);
});
EX.D.querySelectorAll('tr[data-sym]').forEach(tr => {
  const [m, f] = tr.getAttribute('data-sym').split('|');
  ok(Number(tr.getAttribute('data-gamma')) === CC[m].symmetric_slab_gammas[f][0].gamma_J_m2, `experiment.html ${m} ${f} symmetric-slab gamma equals the Python output`);
});
Object.keys(PC).forEach(m => {
  const tr = EX.D.querySelector(`tr[data-frag="${m}"]`);
  ok(tr && Number(tr.getAttribute('data-n')) === PC[m].length && Number(tr.getAttribute('data-cut')) === PC[m].filter(x => x.small_initial.length).length,
     `experiment.html ${m} fragment counts equal the Python output`);
});
Object.keys(BSJ).forEach(m => {
  const tr = EX.D.querySelector(`tr[data-bs="${m}"]`);
  ok(tr && ['1.0', '0.5', '0.25'].every(f => tr.textContent.includes(BSJ[m].by_factor[f].shape)), `experiment.html ${m} bond-cost shapes equal the Python output`);
});
ok(BSJ['MOF-5'].by_factor['1.0'].shape === 'cube' && BSJ['MOF-5'].by_factor['0.25'].shape !== 'cube', 'the MOF-5 UFF cube depends on the metal-ligand bond cost');
ok(Object.keys(CO).every(c => EX.D.querySelector(`tr[data-core="${c}"]`)), `experiment.html lists all ${Object.keys(CO).length} CoRE MOF structures`);
ok(new Set(Object.values(CO).map(v => v.crystal_system)).size >= 5, 'the CoRE MOF set spans at least five crystal systems');
ok(EX.D.querySelectorAll('tr[data-cmp]').length >= 20, 'experiment.html comparison table has every method row');
ok(EX.D.querySelector('img[src="figures/morph/methods_vs_experiment.png"]') && fs.existsSync(path.join(SITE, 'figures', 'morph', 'methods_vs_experiment.png')), 'experiment.html figure exists');

console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
