// The any-lattice engine (mof_general_shape.js) against the Python reference
// (code/morphology/run_general_shape.py -> results/general_shape.json), number by number.
const fs = require('fs'), path = require('path');
global.window = global;
require('../mof_cif_shape.js');
const G = require('../mof_general_shape.js');
const ROOT = path.join(__dirname, '..', '..');
const PY = JSON.parse(fs.readFileSync(path.join(ROOT, 'code/morphology/results/general_shape.json'), 'utf8'));
const DIR = path.join(ROOT, 'data/structures/general_lattice');
let pass = 0, fail = 0;
function ok(cond, msg) { if (cond) pass++; else { fail++; console.log('FAIL', msg); } }
function near(a, b, tol, msg) { ok(Math.abs(a - b) <= tol, msg + ': ' + a + ' vs ' + b); }
const base = {};
for (const key of Object.keys(PY)) {
  const P = PY[key], file = P.file, st = P.stretch;
  const text = fs.readFileSync(path.join(DIR, file), 'utf8');
  if (!base[file]) base[file] = G.run(text);
  const R = G.run(text, { base: base[file], stretch: st });
  ok(R.nAtoms === P.n_atoms, key + ' atoms ' + R.nAtoms + ' vs ' + P.n_atoms);
  ok(R.keptOps === P.operations, key + ' operations ' + R.keptOps + ' vs ' + P.operations);
  ok(R.bounded, key + ' bounded');
  ok(R.habit === P.habit, key + ' habit ' + R.habit + ' vs ' + P.habit);
  near(R.bOverA, P.b_over_a, 2e-3, key + ' b/a');
  near(R.cOverB, P.c_over_b, 2e-3, key + ' c/b');
  near(R.sphericity, P.sphericity, 2e-3, key + ' sphericity');
  P.families.slice(0, 12).forEach((F, i) => near(R.families[i].dEff, F.d_eff, 1e-3, key + ' d_eff #' + i));
  P.families.forEach(F => {
    const J = R.families.find(x => x.label === F.label);
    if (F.area_fraction > 0.005) { ok(!!J, key + ' family ' + F.label + ' present in JS'); if (J) near(J.areaFraction, F.area_fraction, 2e-3, key + ' area ' + F.label); }
  });
  if (P.habit === 'rod' || P.habit === 'lath') ok(JSON.stringify(R.longAxisUVW) === JSON.stringify(P.long_axis_uvw), key + ' long axis ' + R.longAxisUVW + ' vs ' + P.long_axis_uvw);
  if (P.habit === 'plate' || P.habit === 'lath') ok(JSON.stringify(R.flatFaceHKL) === JSON.stringify(P.flat_face_hkl), key + ' flat face ' + R.flatFaceHKL + ' vs ' + P.flat_face_hkl);
}
// the operation parser
const op = G.parseOp('-x+y, 1/2-x, z+0.25');
ok(JSON.stringify(op.R) === JSON.stringify([[-1, 1, 0], [-1, 0, 0], [0, 0, 1]]) && Math.abs(op.t[1] - 0.5) < 1e-12 && Math.abs(op.t[2] - 0.25) < 1e-12, 'parseOp');
console.log('general shape: ' + pass + ' passed, ' + fail + ' failed');
if (fail) process.exit(1);
