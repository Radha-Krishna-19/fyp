// Run the any-lattice BFDH engine (website/mof_general_shape.js) on every CIF in a folder and
// write one line per file. Used for the RASPA2 survey quoted on the CIF to Shape page.
//   node code/morphology/survey_general_lattice.js <folder with .cif files> [output.json]
// The RASPA2 library: https://github.com/iRASPA/RASPA2, folder structures/mofs/cif
// (commit 6498ab1eec9c8e0f063dcd0d71dd7add372c529b for the numbers on the page).
const fs = require('fs'), path = require('path'), crypto = require('crypto');
global.window = global;
require(path.join(__dirname, '..', '..', 'website', 'mof_cif_shape.js'));
const G = require(path.join(__dirname, '..', '..', 'website', 'mof_general_shape.js'));
const dir = process.argv[2], out = process.argv[3] || path.join(__dirname, 'results', 'general_survey_raspa2.json');
if (!dir) { console.log('usage: node survey_general_lattice.js <cif folder> [output.json]'); process.exit(1); }
const files = fs.readdirSync(dir).filter(f => f.endsWith('.cif') && !/primitive/.test(f)).sort();
const res = {};
for (const f of files) {
  const text = fs.readFileSync(path.join(dir, f), 'utf8');
  const sha256 = crypto.createHash('sha256').update(fs.readFileSync(path.join(dir, f))).digest('hex');
  let r;
  try {
    const R = G.run(text);
    r = { sha256, kind: /^COF/.test(f) ? 'COF' : 'MOF', atoms: R.nAtoms, operations: R.symOps.length, lattice_rotations: R.symmetry.rotations,
          habit: R.habit, b_over_a: +R.bOverA.toFixed(4), c_over_b: +R.cOverB.toFixed(4), long_axis_uvw: R.longAxisUVW, flat_face_hkl: R.flatFaceHKL,
          few_operations: R.symOps.length <= 2 && R.symmetry.rotations > 2 };
  } catch (e) { r = { sha256, kind: /^COF/.test(f) ? 'COF' : 'MOF', error: String(e.message) }; }
  res[f] = r;
  console.log(f.padEnd(30), r.error ? 'ERROR ' + r.error : [r.habit, r.b_over_a, r.c_over_b, 'ops ' + r.operations + '/' + r.lattice_rotations, r.few_operations ? 'FEW OPERATIONS' : ''].join(' '));
}
fs.writeFileSync(out, JSON.stringify(res, null, 1));
const tally = {};
for (const r of Object.values(res)) { const k = r.kind + ' ' + (r.error ? 'error' : r.habit + (r.few_operations ? ' (few operations)' : '')); tally[k] = (tally[k] || 0) + 1; }
console.log(tally);
