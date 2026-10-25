// run_all_tests.js: runs every test_*.js suite in this folder and stops at the first failure.
// Usage:  npm install   (once, installs jsdom)   then   npm test
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const suites = fs.readdirSync(__dirname).filter(f => /^test_.*\.js$/.test(f)).sort();
let failed = 0;
for (const f of suites) {
  const t0 = Date.now();
  const r = spawnSync(process.execPath, [path.join(__dirname, f)], { encoding: 'utf8' });
  const ok = r.status === 0;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${f}  (${((Date.now() - t0) / 1000).toFixed(1)} s)`);
  if (!ok) {
    failed += 1;
    console.log((r.stdout || '').split('\n').slice(-15).join('\n'));
    console.log(r.stderr || '');
  }
}
console.log(`\n${suites.length - failed} of ${suites.length} suites passed`);
process.exit(failed ? 1 : 0);
