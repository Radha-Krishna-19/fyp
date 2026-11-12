// test_cif_to_shape.js — the CIF to Shape page (cif_to_shape.html).
// 1. The browser engine mof_cif_shape.js, run on each bundled CIF, gives the same numbers as the
//    independent Python implementation code/morphology/run_cif_to_shape.py (cif_to_shape.json),
//    the same space group as spglib, and the same BFDH shape as results/phase1_results.json.
// 2. The exact boundaries of the morphology map hold on both sides of every line.
// 3. The page renders every step for every structure, with no blank panel.
const path = require('path'), fs = require('fs');
const { JSDOM } = require('jsdom');
const SITE = path.join(__dirname, '..');
const RES = path.join(SITE, '..', 'code', 'morphology', 'results');
let fails = 0;
const ok = (c, m) => { console.log((c ? 'PASS  ' : 'FAIL  ') + m); if (!c) fails++; };
const near = (a, b, t) => Math.abs(a - b) <= t;

global.window = global;
require(path.join(SITE, 'mof_morphology.js'));
const CS = require(path.join(SITE, 'mof_cif_shape.js'));
const PY = JSON.parse(fs.readFileSync(path.join(RES, 'cif_to_shape.json'), 'utf8'));
const P1 = JSON.parse(fs.readFileSync(path.join(RES, 'phase1_results.json'), 'utf8'));
const FILES = { 'MOF-5': 'MOF5.cif', 'HKUST-1': 'HKUST-1.cif', 'UiO-66': 'UiO-66.cif', 'ZIF-8': 'ZIF-8.cif' };

// ---- 1. engine against Python -----------------------------------------------------------
Object.keys(FILES).forEach(n => {
  const py = PY[n], R = CS.run(fs.readFileSync(path.join(SITE, FILES[n]), 'utf8'), { snapshots: true });
  ok(R.cif.atoms.length === py.n_atoms, `${n}: ${R.cif.atoms.length} atoms read, Python ${py.n_atoms}`);
  ok(near(R.volume, py.volume, 0.05), `${n}: cell volume ${R.volume.toFixed(2)} = ${py.volume}`);
  ok(R.conv.key === py.cubic_transform && near(R.a, py.a_conv, 1e-3), `${n}: cubic cell via ${R.conv.key}, a = ${R.a.toFixed(4)} (Python ${py.a_conv})`);
  ok(R.C.els.length === py.n_atoms_conventional, `${n}: ${R.C.els.length} atoms in the conventional cell`);
  ['with_H', 'without_H'].forEach(tag => {
    const js = tag === 'with_H' ? R.centringTest.withH : R.centringTest.withoutH;
    const same = ['I', 'F'].every(k => js[k].every((x, i) => x.r.mapped === py.centring_test[tag][k][i][0] && x.r.of === py.centring_test[tag][k][i][1]));
    ok(same, `${n}: centring counts ${tag} equal Python`);
    const pj = tag === 'with_H' ? R.pgTest.withH : R.pgTest.withoutH;
    const ops = Object.keys(py.point_group_test[tag]);
    // the full count is reported only when the operation fails; when it holds both must say "all"
    ok(ops.every(o => (pj[o].mapped === pj[o].of) === (py.point_group_test[tag][o].mapped === py.point_group_test[tag][o].of)),
       `${n}: the same operations hold ${tag} (${ops.filter(o => pj[o].mapped === pj[o].of).join(', ')})`);
  });
  ok(R.centring === py.centring, `${n}: centring ${R.centring}`);
  ok(R.symmetryWithH === (py.symmetry_found_with === 'with_H'), `${n}: symmetry found ${R.symmetryWithH ? 'with' : 'without'} hydrogen`);
  ok(R.pointGroup === py.point_group, `${n}: point group ${R.pointGroup}`);
  ok(R.sg.sg === py.spglib.spacegroup, `${n}: space group ${R.sg.sg} equals spglib ${py.spglib.spacegroup}`);
  Object.keys(py.structure_factor).forEach(k => {
    const h = k.split('').map(Number), F = R.sfOf(h);
    ok(near(F.ratio, py.structure_factor[k].ratio, 2e-4), `${n}: |F(${k})|/sum Z ${F.ratio.toFixed(5)} = ${py.structure_factor[k].ratio}`);
  });
  // every reflection that the centring forbids is zero from the atoms
  ok(R.sfTable.every(x => x.allowed || x.F.ratio < 1e-9), `${n}: every centring-forbidden reflection is exactly zero`);
  py.families.forEach(f => {
    const j = R.families.find(F => F.label === f.family);
    ok(j && j.n === f.n && near(j.dEff, f.d_eff, 2e-3) && j.multiplicity === f.multiplicity,
       `${n}: ${f.family} n=${f.n} d_eff=${f.d_eff} x${f.multiplicity}`);
  });
  Object.keys(py.bfdh_rates).forEach(k => ok(near(R.rates[k], py.bfdh_rates[k], 1e-4), `${n}: R${k} = ${py.bfdh_rates[k]}`));
  const S = R.shape;
  ok(S.bounded, `${n}: shape is closed`);
  ok(S.name === py.shape.name && S.name === P1[n].bfdh.name, `${n}: shape "${S.name}" (Python "${py.shape.name}", Phase 1 "${P1[n].bfdh.name}")`);
  ok(S.info.faces === py.shape.n_faces && S.info.vertices === py.shape.n_vertices, `${n}: ${S.info.faces} faces, ${S.info.vertices} corners`);
  ok(near(S.info.sphericity, py.shape.sphericity, 2e-4), `${n}: sphericity ${S.info.sphericity.toFixed(4)}`);
  // the engine puts the leading family at distance 1, as does SciPy in Python
  ok(near(S.info.volume, py.shape.volume, 2e-3) && near(R.totalArea, py.shape.area, 2e-3), `${n}: volume ${S.info.volume.toFixed(4)}, area ${R.totalArea.toFixed(4)}`);
  Object.keys(py.shape.face_area_fraction).forEach(k => {
    const F = R.families.find(x => x.label === k);
    ok(F && near(F.areaFraction, py.shape.face_area_fraction[k], 2e-4), `${n}: area fraction ${k} ${F && F.areaFraction.toFixed(4)}`);
  });
  // the worked corner lies on its three planes and inside every other
  const W = R.worked;
  ok(W && W.planes.every((p, i) => near(p.hkl[0] * W.x[0] + p.hkl[1] * W.x[1] + p.hkl[2] * W.x[2], W.rhs[i], 1e-9)), `${n}: worked corner solves its three plane equations`);
  ok(W && Math.max(...S.planes.map(p => CS.la.dot(p.n, W.x) - p.d)) < 1e-9, `${n}: worked corner is inside all ${S.planes.length} planes`);
  // no absent family reaches the shape
  ok(R.families.filter(F => !F.present).every(F => F.R - F.reach > -1e-9), `${n}: every absent family lies outside the shape`);
  // the volume formula used on the page equals the polytope volume
  const V = S.faces.reduce((s, f) => s + f.d * f.area / 3, 0);
  ok(near(V, S.info.volume, 1e-9), `${n}: V = (1/3) sum R_f A_f`);
});
ok(CS.run(fs.readFileSync(path.join(SITE, 'ZIF-8.cif'), 'utf8')).families.find(F => F.label === '{100}').touches,
   'ZIF-8: {100} touches the rhombic dodecahedron exactly at its corners');

// a non-cubic cell stops at Step 3 with a message
{
  const t = fs.readFileSync(path.join(SITE, 'MOF5.cif'), 'utf8').replace(/(_cell_length_c\s+)[0-9.]+/, '$130.0');
  const R = CS.run(t);
  ok(!!R.stop && !R.shape, 'a stretched (tetragonal) cell stops at Step 3 with a message');
}

// ---- 2. the exact map boundaries -------------------------------------------------------------
const fam3 = CS.families('P', 'm-3m', 1, 1).filter(f => f.sumSq <= 3);
const shapeAt = (x, y) => CS.build(fam3, { '{100}': 1, '{110}': x, '{111}': y });
const r2 = Math.SQRT2, r3 = Math.sqrt(3), r32 = Math.sqrt(1.5), e = 1e-3;
[[2, r3 + e, 'cube'], [2, r3 - e, 'truncated cube'], [r2 + e, 2, 'cube'], [r2 - e, 2, null],
 [2, 2 / r3, 'cuboctahedron'], [2, 2 / r3 + 0.05, 'truncated cube'], [2, 2 / r3 - 0.05, 'truncated octahedron'],
 [2, 1 / r3 - e, 'octahedron'], [2, 1 / r3 + e, 'truncated octahedron'], [r32 * 0.5 + e, 0.5, 'octahedron'], [r32 * 0.5 - e, 0.5, null],
 [0.6, r32 * 0.6 + e, 'rhombic dodecahedron'], [0.6, r32 * 0.6 - e, null], [1 / r2 - e, 2, 'rhombic dodecahedron'], [1 / r2 + e, 2, null]].forEach(c => {
  const S = shapeAt(c[0], c[1]);
  ok(c[2] ? S.name === c[2] : !/^(cube|octahedron|rhombic dodecahedron)$/.test(S.name),
     `map at x=${c[0].toFixed(4)}, y=${c[1].toFixed(4)}: ${S.name}${c[2] ? '' : ' (not pure)'}`);
});

// ---- 3. the page ------------------------------------------------------------------------------
const html = fs.readFileSync(path.join(SITE, 'cif_to_shape.html'), 'utf8');
const data = fs.readFileSync(path.join(SITE, 'cif_shape_data.js'), 'utf8');
const Wd = {}; new Function('window', data)(Wd);
Object.keys(FILES).forEach(n => ok(Wd.CIF_SHAPE_PY[n].shape.name === PY[n].shape.name && Wd.CIF_SHAPE_PY[n].a_conv === PY[n].a_conv,
  `cif_shape_data.js ${n} equals cif_to_shape.json`));
const body = html.replace(/<script src="[a-zA-Z0-9_./]+\.js"><\/script>/g, '').replace(/^[\s\S]*<body>/, '').replace(/<\/body>[\s\S]*$/, '');
const dom = new JSDOM(`<!DOCTYPE html><html><body>${body}</body></html>`, { runScripts: 'outside-only' });
['default_cif_data.js', 'mof_morphology.js', 'mof_cif_shape.js', 'mof_general_shape.js', 'general_shape_data.js', 'cif_shape_data.js', 'cif_shape_page.js'].forEach(s =>
  dom.window.eval(fs.readFileSync(path.join(SITE, s), 'utf8')));
if (dom.window.document.readyState === 'loading') dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
const D = dom.window.document;
ok(D.querySelectorAll('#c2s-structs .struct-tab').length === 4, 'four structure buttons');
Object.keys(FILES).forEach(n => {
  dom.window.CIF_SHAPE_PAGE.choose(n);
  ['c2s-summary', 'c2s-s1', 'c2s-s2', 'c2s-s3', 'c2s-s4', 'c2s-s5', 'c2s-s6', 'c2s-s7', 'c2s-s8', 'c2s-s9', 'c2s-s10', 'c2s-s11'].forEach(id => {
    const t = (D.getElementById(id) || { textContent: '' }).textContent;
    ok(t.length > 80 && !/could not be read|Not reached|NaN|undefined/.test(t), `${n}: ${id} filled (${t.length} characters)`);
  });
  const sum = D.getElementById('c2s-summary').textContent;
  ok(sum.includes(PY[n].spglib.spacegroup) && sum.includes(PY[n].shape.name), `${n}: summary names ${PY[n].spglib.spacegroup} and ${PY[n].shape.name}`);
  ok(D.querySelectorAll('.c2s-py').length >= 8, `${n}: Python check lines shown under the steps (${D.querySelectorAll('.c2s-py').length})`);
  ok(D.querySelectorAll('#c2s-fams tbody tr').length === 12, `${n}: family table shows 12 rows`);
  ok(D.querySelectorAll('#c2s-grow-view polygon').length >= 2, `${n}: the growing shape is drawn`);
  ok(D.querySelectorAll('#c2s-final-view polygon').length > 3, `${n}: the final shape is drawn`);
  ok(D.querySelectorAll('#c2s-cell-view line').length >= 12, `${n}: the unit cell is drawn`);
  ok(D.querySelectorAll('#c2s-planes-fig circle').length >= 9, `${n}: the lattice-plane picture is drawn`);
  ok(D.querySelectorAll('#c2s-map rect').length > 1000, `${n}: the morphology map is drawn`);
  const fr = dom.window.CIF_SHAPE_PAGE.state.R.frames;
  // ZIF-8: the twelve {110} planes alone give the final shape, so there is one frame
  ok(fr[0].first && (n === 'ZIF-8' ? fr.length === 1 : fr.length >= 7), `${n}: ${fr.length} frames in the plane-by-plane build`);
});
// UiO-66 (-43m) passes through a tetrahedron on the way; MOF-5 (m-3m) passes through an octahedron
dom.window.CIF_SHAPE_PAGE.choose('UiO-66');
ok(/tetrahedron/.test(D.getElementById('c2s-grow-txt').textContent), 'UiO-66: the first frame of the build is a tetrahedron');
dom.window.CIF_SHAPE_PAGE.choose('MOF-5');
ok(/octahedron/.test(D.getElementById('c2s-grow-txt').textContent), 'MOF-5: the first frame of the build is an octahedron');
dom.window.CIF_SHAPE_PAGE.choose('ZIF-8');
{ const rows = [...D.querySelectorAll('#c2s-explain-txt tbody tr')].map(r => r.textContent);
  ok(rows.length === 3, 'ZIF-8: the five-box explanation lists {100}, {110}, {111}');
  ok(/\{100\}.*cancelled/.test(rows[0]) && /\{110\}.*allowed/.test(rows[1]) && /\{111\}.*cancelled/.test(rows[2]), 'ZIF-8: body-centring cancels {100} and {111}, keeps {110}');
  ok(D.querySelectorAll('#c2s-explain-view circle').length >= 9, 'ZIF-8: the centring model is drawn (8 corners and the body centre)'); }
dom.window.CIF_SHAPE_PAGE.choose('MOF-5');
{ const rows = [...D.querySelectorAll('#c2s-explain-txt tbody tr')].map(r => r.textContent);
  ok(/\{100\}.*cancelled/.test(rows[0]) && /\{110\}.*cancelled/.test(rows[1]) && /\{111\}.*allowed/.test(rows[2]), 'MOF-5: face-centring cancels {100} and {110}, keeps {111}'); }
ok(dom.window.CIF_SHAPE_PAGE.surd(4, 3) === '2/√3' && dom.window.CIF_SHAPE_PAGE.surd(4, 2) === '√2' && dom.window.CIF_SHAPE_PAGE.surd(8, 3) === '2√2/√3',
   'exact surd forms: 2/sqrt3, sqrt2, 2sqrt2/sqrt3');

// ---- 4. the any-lattice section ---------------------------------------------------------------
{ const pg = dom.window.CIF_SHAPE_PAGE, head = () => D.getElementById('c2s-any-result').textContent;
  const flush = () => pg.anyRun();
  pg.anyChoose('MgMOF-74', dom.window.GENERAL_CIFS['MgMOF-74']); flush();
  ok(/Rod/.test(head()) && /\[001\]/.test(head()), 'Any lattice: Mg-MOF-74 is a rod along [001] (' + head().slice(0, 60) + ')');
  ok(D.querySelectorAll('#c2s-any-view svg polygon').length > 10, 'Any lattice: the 3D crystal is drawn');
  ok(D.querySelectorAll('#c2s-any-table tbody tr').length >= 10, 'Any lattice: the face table is filled');
  ok(/Python check/.test(D.getElementById('c2s-any-txt').textContent), 'Any lattice: the Python check line is shown for a bundled file');
  pg.anyChoose('MIL-88A-dry', dom.window.GENERAL_CIFS['MIL-88A-dry']); flush();
  ok(/Compact/.test(head()), 'Any lattice: MIL-88A dry is compact');
  pg.anyChoose('MOF5', dom.window.GENERAL_CIFS['MOF5']); pg.anySetStretch([1, 1, 2.5]); flush();
  ok(/Plate/.test(head()) && /\(001\)/.test(head()), 'Any lattice: MOF-5 with c x 2.5 is a plate on (001)');
  ok(/Python check/.test(D.getElementById('c2s-any-txt').textContent), 'Any lattice: the stretched cell has its Python check');
  pg.anySetStretch([1, 1, 0.25]); flush();
  ok(/Rod/.test(head()), 'Any lattice: MOF-5 with c x 1/4 is a rod');
  // a non-cubic file at the top of the page: the cubic steps stop and point to the section
  pg.state.name = 'MIL-47.cif'; pg.state.bundled = false; pg.state.text = dom.window.GENERAL_CIFS['MIL-47'];
  pg.anyChoose(null, pg.state.text); flush();
  ok(/Rod/.test(head()), 'Any lattice: a non-cubic file chosen at the top is shown as a rod');
}

console.log(fails ? `\n${fails} FAILURES` : '\nAll CIF to Shape tests passed.');
process.exit(fails ? 1 : 0);
